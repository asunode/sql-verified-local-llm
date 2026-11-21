"""Datasheet olgularını `donanim` veritabanına yükler (rol `donanim`, tek işlem, tekrar çalıştırılabilir).

Kullanım: python -m pinsecim.yukle [--pdf veri/kaynak/esp32-c6_datasheet_en.pdf] [--csv veri/dogrulanmis]

Akış: SHA-256 denetimi → çıkarma A ve B → karşılaştırmalar (kararı olmayan fark varsa dur) → şema
(sql/001_sema.sql) → bu kaynağın eski satırları silinir, yenileri yazılır → CSV dışa aktarım.
Aynı kaynak yeniden yüklenince satırlar ve CSV'ler aynı çıkar.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from . import cikar_a, cikar_b, kart_verisi, karsilastir, kural_verisi, olgular
from . import baglanti
from .kararlar import FARK_KARARLARI, GORSEL_DENETIM, GORSEL_DENETIM_TARIHI, KAYNAK
from .pdfoku import sayfa_metni, sayfa_sayisi, sha256

KOK = Path(__file__).resolve().parents[2]
SEMA = KOK / "sql" / "001_sema.sql"
SEMA_KURAL = KOK / "sql" / "002_kurallar.sql"
SEMA_TANIM = KOK / "sql" / "003_arayuz_tanim.sql"
SEMA_SOZLUK = KOK / "sql" / "004_istek_sozlugu.sql"
SEMA_ISTISNA = KOK / "sql" / "005_sayi_istisnasi.sql"
SEMA_PIN = KOK / "sql" / "006_pin_tercihleri.sql"
SEMA_SORU = KOK / "sql" / "007_soru_mesaj.sql"
SEMA_SAYI = KOK / "sql" / "008_sayi_es_ad.sql"
SEMA_ES_AD_HARF = KOK / "sql" / "009_es_ad_harf.sql"
SEMA_KART = KOK / "sql" / "010_kart.sql"
SEMA_KART_KONU = KOK / "sql" / "011_kart_konu.sql"
SEMA_ORTAK_HAT = KOK / "sql" / "012_ortak_hat.sql"
SEMA_KART_ATAMA = KOK / "sql" / "013_kart_atama.sql"
SEMA_DESTEKLENMEYEN = KOK / "sql" / "014_desteklenmeyen.sql"
SEMA_SORU_SOZCUGU = KOK / "sql" / "015_soru_sozcugu.sql"
SEMA_SAYI_DISI = KOK / "sql" / "016_sayi_disi_sozcuk.sql"
KURAL_TABLOLARI = ["kural", "arayuz_sinyal", "arayuz_tanimi", "cevre_adet", "sayi_sozcugu", "baglam_sozcugu",
                   "pin_bahsi_deseni", "soru_konusu", "durum_mesaji", "arayuz_es_adi", "desteklenmeyen_ozellik", "soru_sozcugu",
                   "sayi_disi_sozcuk"]   # tek kaynaklı; tümü yeniden yazılır
KART_TABLOLARI = ["kart_parca", "kart_pin", "kart", "modul_pin"]   # kart verisi (Adım 10b); silme sırası, tümü yeniden yazılır
OLGU_TABLOLARI = ["flash_pin", "strapping_kombinasyon", "gpio_kisit", "cevre_birim_sinyal", "gpio_islev", "pin",
                  "cip", "paket", "ham_metin", "dogrulama"]   # silme sırası (çocuktan ebeveyne)
DSN = baglanti.dsn("donanim", "pinsecim_yukle")


class YuklemeHatasi(Exception):
    pass


def hazirla(pdf: Path) -> dict:
    """Veritabanına dokunmadan: SHA, çıkarma, karşılaştırma, satırlar."""
    ozet = sha256(pdf)
    if ozet != KAYNAK["sha256"]:
        raise YuklemeHatasi(f"SHA-256 tutmuyor: {ozet} (beklenen {KAYNAK['sha256']})")
    a, b = cikar_a.hepsi(pdf), cikar_b.hepsi(pdf)
    farklar = karsilastir.a_b_farklari(a, b) + karsilastir.a_ic_farklari(a) + karsilastir.renk_metin_farklari(a)
    eksik = [f.anahtar for f in farklar if f.anahtar not in FARK_KARARLARI]
    if eksik:
        raise YuklemeHatasi("Kararı olmayan farklar: " + "; ".join(eksik))
    return {"a": a, "b": b, "farklar": farklar, "satirlar": olgular.satirlar(a, farklar),
            "sayfa_sayisi": sayfa_sayisi(pdf)}


def _dogrulama_satirlari(h: dict) -> list[dict]:
    bugun = dt.date.today().isoformat()
    fark_sayisi: dict[str, int] = {}
    for f in h["farklar"]:
        for parca in (f.kaynak_a, f.kaynak_b):
            fark_sayisi[parca] = fark_sayisi.get(parca, 0) + 1
    satirlar = []
    b = h["b"]
    # A–B: pin overview, IO MUX, LP IO MUX, analog ↔ Consolidated
    ab = [(t, ref, s) for t, ref, s in [
        ("pin", "Table 2-1", 16), ("pin", "Table 2-1", 17), ("pin", "Table 2-2", 17), ("pin", "Table 2-2", 18),
        ("gpio_islev", "Table 2-4", 20), ("gpio_islev", "Table 2-5", 21), ("gpio_islev", "Table 2-7", 22),
        ("gpio_islev", "Table 2-9", 23), ("pin", "Table 7-1", 79), ("pin", "Table 7-2", 80)]]
    ab_farki = [f for f in h["farklar"] if f.tur == "A-B"]
    for tablo, ref, sayfa in ab:
        satirlar.append({"tablo": tablo, "referans": ref, "sayfa": sayfa, "yontem": "A-B karsilastirma",
                         "sonuc": "fark var, karara baglandi" if ab_farki else "uyumlu",
                         "ayrinti": f"Consolidated Pin Overview ile alan alan; QFN40 {len(b['QFN40'])}, "
                                    f"QFN32 {len(b['QFN32'])} pin; {len(ab_farki)} fark", "tarih": bugun})
    ic = {"cevre_birim_sinyal": [("Table 2-10", 26), ("Table 2-11", 27)], "pin": [("Figure 2-1", 14), ("Figure 2-2", 15)],
          "gpio_kisit": [("2.3.5", 25), ("Table 3-1", 33)]}
    for tablo, refler in ic.items():
        for ref, sayfa in refler:
            ilgili = [f for f in h["farklar"] if f.tur in ("A-ic", "renk-metin")
                      and (ref in f.kaynak_a or ref in f.kaynak_b)]
            satirlar.append({"tablo": tablo, "referans": ref, "sayfa": sayfa, "yontem": "A ic capraz denetim",
                             "sonuc": "fark var, karara baglandi" if ilgili else "uyumlu",
                             "ayrinti": "; ".join(f"{f.paket} pin {f.pin_no} {f.alan}: {f.a} ≠ {f.b}" for f in ilgili)
                                        or None, "tarih": bugun})
    for sayfa, (tablolar, ref, ayrinti) in sorted(GORSEL_DENETIM.items()):
        for tablo in tablolar:
            satirlar.append({"tablo": tablo, "referans": ref, "sayfa": sayfa, "yontem": "gorsel denetim",
                             "sonuc": "fark var, karara baglandi" if "fark" in ayrinti else "uyumlu",
                             "ayrinti": ayrinti, "tarih": GORSEL_DENETIM_TARIHI})
    return satirlar


def yukle(pdf: Path, csv_dizini: Path | None = None, dsn: str = DSN) -> dict[str, int]:
    h = hazirla(pdf)
    t = h["satirlar"]
    with psycopg.connect(dsn) as b:          # çıkışta commit; hata olursa rollback
        with b.transaction():
            b.execute(SEMA.read_text(encoding="utf-8"))
            b.execute(SEMA_KART.read_text(encoding="utf-8"))
            b.execute(SEMA_KART_ATAMA.read_text(encoding="utf-8"))
            for tablo in KART_TABLOLARI:                # cip satırlarına bağlı; çip olguları silinmeden önce
                b.execute(f"DELETE FROM {tablo}")
            k = b.execute(
                """INSERT INTO kaynak (belge, surum, yayin_tarihi, sha256, dosya_yolu, url, indirme_zamani, sayfa_sayisi)
                   VALUES (%(belge)s, %(surum)s, %(yayin_tarihi)s, %(sha256)s, %(dosya_yolu)s, %(url)s, %(indirme_zamani)s, %(n)s)
                   ON CONFLICT (sha256) DO UPDATE SET belge = EXCLUDED.belge, surum = EXCLUDED.surum,
                       yayin_tarihi = EXCLUDED.yayin_tarihi, dosya_yolu = EXCLUDED.dosya_yolu, url = EXCLUDED.url,
                       indirme_zamani = EXCLUDED.indirme_zamani, sayfa_sayisi = EXCLUDED.sayfa_sayisi
                   RETURNING id""", {**KAYNAK, "n": h["sayfa_sayisi"]}).fetchone()[0]
            for tablo in OLGU_TABLOLARI:
                b.execute(f"DELETE FROM {tablo} WHERE kaynak_id = %s", (k,))

            for s in range(1, h["sayfa_sayisi"] + 1):
                b.execute("INSERT INTO ham_metin (kaynak_id, sayfa, metin) VALUES (%s, %s, %s)", (k, s, sayfa_metni(pdf, s)))
            paket_id = {}
            for p in t["paket"]:
                paket_id[p["ad"]] = b.execute(
                    "INSERT INTO paket (aile, ad, boyut, kaynak_id, sayfa, referans) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                    (p["aile"], p["ad"], p["boyut"], k, p["sayfa"], p["referans"])).fetchone()[0]

            def ekle(tablo: str, satir: dict) -> None:
                d = dict(satir)
                if "paket" in d:
                    d["paket_id"] = paket_id[d.pop("paket")] if d["paket"] is not None else d.pop("paket")
                if "not" in d:
                    d["not_"] = d.pop("not")
                if "pin_degerleri" in d:
                    d["pin_degerleri"] = Jsonb(d["pin_degerleri"])
                d["kaynak_id"] = k
                sutunlar = list(d)
                b.execute(f"INSERT INTO {tablo} ({', '.join(sutunlar)}) VALUES ({', '.join('%s' for _ in sutunlar)})",
                          [d[c] for c in sutunlar])

            for tablo in ("cip", "pin", "gpio_islev", "cevre_birim_sinyal", "gpio_kisit", "strapping_kombinasyon",
                          "flash_pin"):
                for satir in t[tablo]:
                    ekle(tablo, satir)
            for satir in _dogrulama_satirlari(h):
                ekle("dogrulama", satir)
            kurallari_yaz(b, k, pdf)
            kart_yaz(b)
        sayilar = {tablo: b.execute(f"SELECT count(*) FROM {tablo} WHERE kaynak_id = %s", (k,)).fetchone()[0]
                   for tablo in reversed(OLGU_TABLOLARI)}
        sayilar.update({tablo: b.execute(f"SELECT count(*) FROM {tablo}").fetchone()[0]
                        for tablo in reversed(KURAL_TABLOLARI + ["yorum"] + KART_TABLOLARI)})
        if csv_dizini is not None:
            disa_aktar(b, csv_dizini)
    return sayilar


def _bosluksuz(metin: str) -> str:
    return " ".join(metin.split())


def kurallari_yaz(b: psycopg.Connection, k: int, pdf: Path) -> None:
    """Adım 3 tabloları: adetler (dayanak sayfa metninde aranır), arayüzler, sabit sinyaller, kurallar, yorumlar."""
    b.execute(SEMA_KURAL.read_text(encoding="utf-8"))
    b.execute(SEMA_TANIM.read_text(encoding="utf-8"))
    b.execute(SEMA_SOZLUK.read_text(encoding="utf-8"))
    b.execute(SEMA_ISTISNA.read_text(encoding="utf-8"))
    b.execute(SEMA_PIN.read_text(encoding="utf-8"))
    b.execute(SEMA_SORU.read_text(encoding="utf-8"))
    b.execute(SEMA_SAYI.read_text(encoding="utf-8"))
    b.execute(SEMA_ES_AD_HARF.read_text(encoding="utf-8"))
    b.execute(SEMA_KART_KONU.read_text(encoding="utf-8"))
    b.execute(SEMA_ORTAK_HAT.read_text(encoding="utf-8"))
    b.execute(SEMA_DESTEKLENMEYEN.read_text(encoding="utf-8"))
    b.execute(SEMA_SORU_SOZCUGU.read_text(encoding="utf-8"))
    b.execute(SEMA_SAYI_DISI.read_text(encoding="utf-8"))
    for tablo in KURAL_TABLOLARI:
        b.execute(f"DELETE FROM {tablo}")
    b.execute("DELETE FROM yorum WHERE kaynak_id = %s", (k,))
    aile = olgular.AILE
    for ad, adet, dayanak, sayfa, ref, not_ in kural_verisi.ADETLER:
        if dayanak.startswith("sayim:"):
            sayi = b.execute("SELECT count(*) FROM gpio_islev WHERE kaynak_id = %s AND grup = 'LP_IO_MUX' "
                             "AND islev_no = 0", (k,)).fetchone()[0]
            if sayi != adet:
                raise YuklemeHatasi(f"{ad}: sayım {sayi}, beklenen {adet}")
        elif _bosluksuz(dayanak) not in _bosluksuz(sayfa_metni(pdf, sayfa)):
            raise YuklemeHatasi(f"{ad}: dayanak ifadesi s. {sayfa} metninde yok: {dayanak!r}")
        b.execute("INSERT INTO cevre_adet (aile, ad, adet, dayanak, kaynak_id, sayfa, referans, not_) "
                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (aile, ad, adet, _bosluksuz(dayanak), k, sayfa, ref, not_))
    adc = b.execute("SELECT count(*) FROM gpio_islev WHERE kaynak_id = %s AND grup = 'ANALOG' "
                    "AND islev_adi LIKE 'ADC1\\_CH%%'", (k,)).fetchone()[0]
    if adc != dict((a[0], a[1]) for a in kural_verisi.ADETLER)["ADC"]:
        raise YuklemeHatasi(f"ADC adedi Table 2-9'daki ADC1_CH sayısıyla ({adc}) tutmuyor")
    for r in kural_verisi.arayuz_satirlari():
        b.execute("INSERT INTO arayuz_tanimi (aile, arayuz, sinyaller, sinyal_kaynagi, yonlendirme, cevre_birim, adet_adi, "
                  "adet_baglam_dusumu, tanim, paylasimli_hat, ortak_hat_secim, kaynak_id, sayfa, referans, not_) "
                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                  (aile, r["arayuz"], r["sinyaller"], r["sinyal_kaynagi"], r["yonlendirme"], r["cevre_birim"],
                   r["adet_adi"], r["adet_baglam_dusumu"], r["tanim"], r["paylasimli_hat"], r["ortak_hat_secim"], k,
                   r["sayfa"], r["referans"], r["not"]))
    for (arayuz, sinyal), (grup, desen, sayfa, ref) in kural_verisi.SABIT_SINYALLER.items():
        b.execute("INSERT INTO arayuz_sinyal (aile, arayuz, sinyal, sabit_grup, islev_deseni, kaynak_id, sayfa, referans) "
                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (aile, arayuz, sinyal, grup, desen, k, sayfa, ref))
    for sira, (kod, kat, tur, baglam, seviye, mesaj, aciklama, sayfa, ref) in enumerate(kural_verisi.KURALLAR, 1):
        tek, dogru, yanlis = (seviye, None, None) if baglam is None else (None, *seviye)
        b.execute("INSERT INTO kural (kod, kategori, kisit_turu, baglam_anahtari, seviye, seviye_dogru, seviye_yanlis, "
                  "mesaj, mesaj_tr, aciklama, kaynak_id, sayfa, referans, veren, sira) "
                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                  (kod, kat, tur, baglam, tek, dogru, yanlis, mesaj, kural_verisi.KURAL_MESAJ_TR[kod], aciklama,
                   k if sayfa else None, sayfa, ref, kural_verisi.VEREN, sira))
    adim6 = {*kural_verisi._BIRLER, "on", "yirmi"}
    for ifade, (deger, basamak) in kural_verisi.SAYI_BASAMAKLARI.items():
        b.execute("INSERT INTO sayi_sozcugu (ifade, deger, basamak, kaynak) VALUES (%s,%s,%s,%s)",
                  (ifade, deger, basamak, kural_verisi.SOZLUK_KAYNAGI if ifade in adim6 else kural_verisi.SAYI_KAYNAGI_10A))
    for ifade, deger in kural_verisi.SAYI_SOZCUKLERI.items():
        b.execute("INSERT INTO sayi_sozcugu (ifade, deger, kaynak) VALUES (%s,%s,%s)", (ifade, deger, kural_verisi.SOZLUK_KAYNAGI))
    for ifade, deger in kural_verisi.SAYI_EKLERI.items():
        b.execute("INSERT INTO sayi_sozcugu (ifade, deger, kaynak) VALUES (%s,%s,%s)", (ifade, deger, kural_verisi.SAYI_KAYNAGI_10A))
    for ifade in kural_verisi.SAYI_ISTISNALARI:
        b.execute("INSERT INTO sayi_sozcugu (ifade, deger, kaynak) VALUES (%s,NULL,%s)", (ifade, kural_verisi.ISTISNA_KAYNAGI))
    for ifade in kural_verisi.SAYI_ISTISNALARI_10A:
        b.execute("INSERT INTO sayi_sozcugu (ifade, deger, kaynak) VALUES (%s,NULL,%s)", (ifade, kural_verisi.SAYI_KAYNAGI_10A))
    for es_ad, arayuz, *harf in kural_verisi.ARAYUZ_ES_ADLARI:
        b.execute("INSERT INTO arayuz_es_adi (es_ad, arayuz, harf_duyarli, kaynak) VALUES (%s,%s,%s,%s)",
                  (es_ad, arayuz, bool(harf and harf[0]), kural_verisi.ES_AD_KAYNAGI))
    liste = "\n".join(sayfa_metni(pdf, sf) for sf in kural_verisi.DESTEKLENMEYEN_SAYFALAR)
    for terim, aciklama, adlar, harfli in kural_verisi.DESTEKLENMEYEN_OZELLIKLER:
        for ad in [*adlar, *harfli]:                 # "bu listede yok": ad çevre birimi listelerinde geçmemeli
            m = re.search(rf"(?<![A-Za-z0-9]){re.escape(ad)}(?![A-Za-z0-9])", liste, 0 if ad in harfli else re.I)
            if m:
                raise YuklemeHatasi(f"desteklenmeyen özellik adı '{ad}' çevre birimi listesinde geçiyor: {m.group()!r}")
        b.execute("INSERT INTO desteklenmeyen_ozellik (aile, terim, es_adlar, harf_duyarli_adlar, aciklama_tr, kaynak_id, "
                  "sayfa, referans) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                  (aile, terim, adlar, harfli, aciklama, k, kural_verisi.DESTEKLENMEYEN_SAYFALAR[0],
                   kural_verisi.DESTEKLENMEYEN_REFERANS))
    sayfa, baslik = kural_verisi.ELEKTRIKSEL_BOLUM
    if baslik not in sayfa_metni(pdf, sayfa):
        raise YuklemeHatasi(f"cevap.elektriksel_yok: s. {sayfa} metninde '{baslik}' yok")
    for sozcuk, harf in kural_verisi.SORU_SOZCUKLERI:
        b.execute("INSERT INTO soru_sozcugu (sozcuk, tur, harf_duyarli, kaynak) VALUES (%s,'elektriksel',%s,%s)",
                  (sozcuk, harf, kural_verisi.SORU_SOZCUGU_KAYNAGI))
    for sozcuk, tur, bicim, harf in kural_verisi.SAYI_DISI_SOZCUKLER:
        b.execute("INSERT INTO sayi_disi_sozcuk (sozcuk, tur, bicim, harf_duyarli, kaynak) VALUES (%s,%s,%s,%s,%s)",
                  (sozcuk, tur, bicim, harf, kural_verisi.SAYI_DISI_KAYNAGI))
    for tur, anahtar, desen in kural_verisi.BAGLAM_SOZCUKLERI:
        b.execute("INSERT INTO baglam_sozcugu (tur, anahtar, desen, kaynak) VALUES (%s,%s,%s,%s)",
                  (tur, anahtar, desen, kural_verisi.SOZLUK_KAYNAGI))
    for tur, desen, aciklama in kural_verisi.PIN_BAHSI_DESENLERI:
        b.execute("INSERT INTO pin_bahsi_deseni (tur, desen, aciklama, kaynak) VALUES (%s,%s,%s,%s)",
                  (tur, desen, aciklama, kural_verisi.PIN_BAHSI_KAYNAGI))
    for sira, (konu, tanim, tur, gereken, tablolar) in enumerate(kural_verisi.SORU_KONULARI, 1):
        b.execute("INSERT INTO soru_konusu (konu, model_tanimi, cevap_turu, gereken, tablolar, sira, kaynak) "
                  "VALUES (%s,%s,%s,%s,%s,%s,%s)", (konu, tanim, tur, gereken, tablolar, sira, kural_verisi.SORU_KAYNAGI))
    for satirlar, kaynak in ((kural_verisi.DURUM_MESAJLARI, kural_verisi.MESAJ_KAYNAGI),
                             (kural_verisi.DURUM_MESAJLARI_10B, kural_verisi.MESAJ_KAYNAGI_10B),
                             (kural_verisi.DURUM_MESAJLARI_11A, kural_verisi.MESAJ_KAYNAGI_11A)):
        for anahtar, mesaj, ne, ornek, tanim in satirlar:
            b.execute("INSERT INTO durum_mesaji (anahtar, mesaj_tr, ne_yazmali_tr, ornek_tr, model_tanimi, kaynak) "
                      "VALUES (%s,%s,%s,%s,%s,%s)", (anahtar, mesaj, ne, ornek, tanim, kaynak))
    for y in kural_verisi.YORUMLAR:
        b.execute("INSERT INTO yorum (olgu_tablo, olgu_anahtar, yorum, deger, gerekce, kaynaklar, veren, tarih, kaynak_id) "
                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                  (y["olgu_tablo"], Jsonb(y["olgu_anahtar"]), y["yorum"], Jsonb(y["deger"]), y["gerekce"],
                   y["kaynaklar"], y["veren"], y["tarih"], k))


def kart_yaz(b: psycopg.Connection) -> None:
    """Adım 10b kart verisi: kart kaynakları (SHA-256 dosyayla denetlenir), kartlar, modül pinleri, kart pinleri, kart
    üstü parçalar. Tablolar yukle() başında boşaltıldı."""
    kid = {}
    for kisa, kay in kart_verisi.KAYNAKLAR.items():
        if sha256(KOK / kay["dosya_yolu"]) != kay["sha256"]:
            raise YuklemeHatasi(f"{kisa}: {kay['dosya_yolu']} SHA-256 tutmuyor")
        kid[kisa] = b.execute(
            """INSERT INTO kaynak (belge, surum, yayin_tarihi, sha256, dosya_yolu, url, indirme_zamani, sayfa_sayisi,
                                   kaynak_turu)
               VALUES (%(belge)s, %(surum)s, %(yayin_tarihi)s, %(sha256)s, %(dosya_yolu)s, %(url)s, %(indirme_zamani)s,
                       %(sayfa_sayisi)s, %(kaynak_turu)s)
               ON CONFLICT (sha256) DO UPDATE SET belge = EXCLUDED.belge, surum = EXCLUDED.surum,
                   yayin_tarihi = EXCLUDED.yayin_tarihi, dosya_yolu = EXCLUDED.dosya_yolu, url = EXCLUDED.url,
                   indirme_zamani = EXCLUDED.indirme_zamani, sayfa_sayisi = EXCLUDED.sayfa_sayisi,
                   kaynak_turu = EXCLUDED.kaynak_turu
               RETURNING id""", kay).fetchone()[0]
    kart_id = {}
    for kisa, ad, surum, uretici, cip, modul, (kay, sayfa, ref), durum, not_ in kart_verisi.KARTLAR:
        kart_id[kisa] = b.execute(
            "INSERT INTO kart (kisa_ad, ad, surum, uretici, cip_id, modul, kaynak_id, sayfa, referans, dogrulama_durumu, "
            "not_) VALUES (%s,%s,%s,%s,(SELECT id FROM cip WHERE ad = %s),%s,%s,%s,%s,%s,%s) RETURNING id",
            (kisa, ad, surum, uretici, cip, modul, kid[kay], sayfa, ref, durum, not_)).fetchone()[0]
    for modul, no, ad, gpio, (kay, sayfa, ref), teyit, durum in kart_verisi.MODUL_PINLERI:
        b.execute("INSERT INTO modul_pin (modul, pin_no, pin_adi, gpio_no, kaynak_id, sayfa, referans, teyit_kaynak_id, "
                  "dogrulama_durumu) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                  (modul, no, ad, gpio, kid[kay], sayfa, ref, kid[teyit], durum))
    for kart, kon, sira, etiket, gpio, (kay, sayfa, ref), durum, not_, tur in kart_verisi.KART_PINLERI:
        b.execute("INSERT INTO kart_pin (kart_id, konnektor, sira, etiket, gpio_no, kaynak_id, sayfa, referans, "
                  "dogrulama_durumu, not_, tur) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                  (kart_id[kart], kon, sira, etiket, gpio, kid[kay], sayfa, ref, durum, not_, tur))
    for kart, tur, ad, gpio, bag, seviye, aciklama, (kay, sayfa, ref), durum, not_ in kart_verisi.KART_PARCALARI:
        b.execute("INSERT INTO kart_parca (kart_id, tur, ad, gpio_no, baglanti, aktif_seviye, aciklama, kaynak_id, sayfa, "
                  "referans, dogrulama_durumu, not_) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                  (kart_id[kart], tur, ad, gpio, bag, seviye, aciklama, kid[kay], sayfa, ref, durum, not_))


# CSV: yapay kimlikler yerine doğal anahtarlar (paket adı, kaynak SHA'sının başı); sıralı, tarihsiz.
CSV_SORGULARI = {
    "kaynak": "SELECT belge, surum, yayin_tarihi, sha256, dosya_yolu, url, indirme_zamani, sayfa_sayisi, kaynak_turu FROM kaynak ORDER BY sha256",
    "kart": "SELECT x.kisa_ad, x.ad, x.surum, x.uretici, c.ad AS cip, x.modul, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans, x.dogrulama_durumu, x.not_ FROM kart x JOIN cip c ON c.id = x.cip_id JOIN kaynak k ON k.id = x.kaynak_id ORDER BY x.kisa_ad",
    "modul_pin": "SELECT x.modul, x.pin_no, x.pin_adi, x.gpio_no, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans, left(t.sha256, 12) AS teyit_kaynak, x.dogrulama_durumu FROM modul_pin x JOIN kaynak k ON k.id = x.kaynak_id LEFT JOIN kaynak t ON t.id = x.teyit_kaynak_id ORDER BY x.modul, x.pin_no",
    "kart_pin": "SELECT c.kisa_ad AS kart, x.konnektor, x.sira, x.etiket, x.gpio_no, x.tur, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans, x.dogrulama_durumu, x.not_ FROM kart_pin x JOIN kart c ON c.id = x.kart_id JOIN kaynak k ON k.id = x.kaynak_id ORDER BY c.kisa_ad, x.konnektor, x.sira",
    "kart_parca": "SELECT c.kisa_ad AS kart, x.tur, x.ad, x.gpio_no, x.baglanti, x.aktif_seviye, x.aciklama, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans, x.dogrulama_durumu, x.not_ FROM kart_parca x JOIN kart c ON c.id = x.kart_id JOIN kaynak k ON k.id = x.kaynak_id ORDER BY c.kisa_ad, x.tur, x.ad",
    "paket": "SELECT p.aile, p.ad, p.boyut, left(k.sha256, 12) AS kaynak, p.sayfa, p.referans FROM paket p JOIN kaynak k ON k.id = p.kaynak_id ORDER BY p.aile, p.ad",
    "cip": "SELECT c.ad, c.aile, p.ad AS paket, c.gomulu_flash, c.sicaklik, c.revizyon, c.dipnot, left(k.sha256, 12) AS kaynak, c.sayfa, c.referans FROM cip c JOIN paket p ON p.id = c.paket_id JOIN kaynak k ON k.id = c.kaynak_id ORDER BY c.ad",
    "pin": "SELECT p.aile, p.ad AS paket, x.pin_no, x.pin_adi, x.pin_turu, x.gpio_no, x.guc, x.reset_ayar, x.reset_sonrasi_ayar, array_to_string(x.islev_kumeleri, '|') AS islev_kumeleri, array_to_string(x.varsayilan_kume, '|') AS varsayilan_kume, x.varsayilan_surme_ma, x.dipnot, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans, x.belirsiz, x.not_ FROM pin x JOIN paket p ON p.id = x.paket_id JOIN kaynak k ON k.id = x.kaynak_id ORDER BY p.aile, p.ad, x.pin_no",
    "gpio_islev": "SELECT x.aile, x.gpio_no, p.ad AS paket, x.grup, x.islev_no, x.islev_adi, x.tip, x.varsayilan, x.tablo_adi, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans, x.belirsiz, x.not_ FROM gpio_islev x LEFT JOIN paket p ON p.id = x.paket_id JOIN kaynak k ON k.id = x.kaynak_id ORDER BY x.aile, x.gpio_no, p.ad NULLS FIRST, x.grup, x.islev_no",
    "cevre_birim_sinyal": "SELECT p.ad AS paket, x.pin_no, x.cevre_birim, x.hucre, x.sinyal, x.gpio_no, x.oncelik, x.yonlendirme, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans, x.belirsiz, x.not_ FROM cevre_birim_sinyal x JOIN paket p ON p.id = x.paket_id JOIN kaynak k ON k.id = x.kaynak_id ORDER BY p.ad, x.pin_no, x.cevre_birim",
    "gpio_kisit": "SELECT x.aile, x.gpio_no, p.ad AS paket, x.kisit_turu, x.oncelik, x.aciklama, x.varsayilan_durum, x.kaynak_turu, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans, x.belirsiz, x.not_ FROM gpio_kisit x LEFT JOIN paket p ON p.id = x.paket_id JOIN kaynak k ON k.id = x.kaynak_id ORDER BY x.aile, x.gpio_no, p.ad NULLS FIRST, x.kisit_turu",
    "strapping_kombinasyon": "SELECT x.aile, x.islev, x.sonuc, x.pin_degerleri::text AS pin_degerleri, x.varsayilan, x.dipnot, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans FROM strapping_kombinasyon x JOIN kaynak k ON k.id = x.kaynak_id ORDER BY x.aile, x.islev, x.sonuc",
    "flash_pin": "SELECT p.ad AS paket, x.pin_no, x.pin_adi, x.gpio_no, x.tek_spi, x.cift_spi, x.dortlu_spi, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans FROM flash_pin x JOIN paket p ON p.id = x.paket_id JOIN kaynak k ON k.id = x.kaynak_id ORDER BY p.ad, x.pin_no",
    "cevre_adet": "SELECT x.aile, x.ad, x.adet, x.dayanak, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans, x.not_ FROM cevre_adet x JOIN kaynak k ON k.id = x.kaynak_id ORDER BY x.aile, x.ad",
    "arayuz_tanimi": "SELECT x.aile, x.arayuz, array_to_string(x.sinyaller, '|') AS sinyaller, x.sinyal_kaynagi, x.yonlendirme, x.cevre_birim, x.adet_adi, x.adet_baglam_dusumu, x.tanim, x.paylasimli_hat, x.ortak_hat_secim, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans, x.not_ FROM arayuz_tanimi x JOIN kaynak k ON k.id = x.kaynak_id ORDER BY x.aile, x.arayuz",
    "arayuz_sinyal": "SELECT x.aile, x.arayuz, x.sinyal, x.sabit_grup, x.islev_deseni, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans FROM arayuz_sinyal x JOIN kaynak k ON k.id = x.kaynak_id ORDER BY x.aile, x.arayuz, x.sinyal",
    "kural": "SELECT x.sira, x.kod, x.kategori, x.kisit_turu, x.baglam_anahtari, x.seviye, x.seviye_dogru, x.seviye_yanlis, x.mesaj, x.mesaj_tr, x.aciklama, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans, x.veren FROM kural x LEFT JOIN kaynak k ON k.id = x.kaynak_id ORDER BY x.sira",
    "sayi_sozcugu": "SELECT ifade, deger, basamak, kaynak FROM sayi_sozcugu ORDER BY deger NULLS LAST, ifade",
    "arayuz_es_adi": "SELECT es_ad, arayuz, harf_duyarli, kaynak FROM arayuz_es_adi ORDER BY arayuz, es_ad",
    "desteklenmeyen_ozellik": "SELECT x.aile, x.terim, array_to_string(x.es_adlar, '|') AS es_adlar, array_to_string(x.harf_duyarli_adlar, '|') AS harf_duyarli_adlar, x.aciklama_tr, left(k.sha256, 12) AS kaynak, x.sayfa, x.referans FROM desteklenmeyen_ozellik x JOIN kaynak k ON k.id = x.kaynak_id ORDER BY x.terim",
    "soru_sozcugu": "SELECT sozcuk, tur, harf_duyarli, kaynak FROM soru_sozcugu ORDER BY tur, sozcuk",
    "sayi_disi_sozcuk": "SELECT sozcuk, tur, bicim, harf_duyarli, kaynak FROM sayi_disi_sozcuk ORDER BY tur, sozcuk",
    "baglam_sozcugu": "SELECT tur, anahtar, desen, kaynak FROM baglam_sozcugu ORDER BY tur, anahtar NULLS FIRST, desen",
    "pin_bahsi_deseni": "SELECT tur, desen, aciklama, kaynak FROM pin_bahsi_deseni ORDER BY tur, desen",
    "soru_konusu": "SELECT sira, konu, model_tanimi, cevap_turu, gereken, tablolar, kaynak FROM soru_konusu ORDER BY sira",
    "durum_mesaji": "SELECT anahtar, mesaj_tr, ne_yazmali_tr, ornek_tr, model_tanimi, kaynak FROM durum_mesaji ORDER BY anahtar",
    "yorum": "SELECT x.olgu_tablo, x.olgu_anahtar::text AS olgu_anahtar, x.yorum, x.deger::text AS deger, array_to_string(x.gerekce, ' | ') AS gerekce, array_to_string(x.kaynaklar, ' | ') AS kaynaklar, x.veren, x.tarih, left(k.sha256, 12) AS kaynak FROM yorum x JOIN kaynak k ON k.id = x.kaynak_id ORDER BY x.olgu_tablo, x.olgu_anahtar::text",
    "dogrulama": "SELECT x.tablo, x.referans, x.sayfa, x.yontem, x.sonuc, x.ayrinti, left(k.sha256, 12) AS kaynak FROM dogrulama x JOIN kaynak k ON k.id = x.kaynak_id ORDER BY x.yontem, x.sayfa, x.referans, x.tablo",
}


def disa_aktar(b: psycopg.Connection, dizin: Path) -> None:
    dizin.mkdir(parents=True, exist_ok=True)
    for ad, sorgu in CSV_SORGULARI.items():
        with b.cursor() as c:
            c.execute(sorgu)
            with open(dizin / f"{ad}.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, lineterminator="\n")
                w.writerow([d.name for d in c.description])
                for satir in c:
                    w.writerow(["" if v is None else v for v in satir])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pdf", type=Path, default=KOK / KAYNAK["dosya_yolu"])
    ap.add_argument("--csv", type=Path, default=KOK / "veri" / "dogrulanmis")
    a = ap.parse_args(argv)
    try:
        sayilar = yukle(a.pdf, a.csv)
    except YuklemeHatasi as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1
    print(json.dumps(sayilar, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

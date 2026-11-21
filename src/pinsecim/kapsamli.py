"""Adım 8: kapsamlı set (v3) ile A + atayıcı ölçümü (K-6). Ham sayılar; yorum yok.

Kullanım:
    python -m pinsecim.kapsamli kos --set YOL --sha HEX --ham YOL [--tekrar 15]
    python -m pinsecim.kapsamli rapor --set YOL --sha HEX --ham YOL --sonuc YOL --dondurma YOL --tarih T
                                      [--cli-goster X34,X35]
    python -m pinsecim.kapsamli yeniden-ata --set YOL --sha HEX --eski-ham YOL --ham YOL

Koşular (en_cok_tur 3, sınır açık):
1. a_atayici  her istek uçtan uca varsayılan akışla: Çağrı A (model) → kod atayıcı → denetim. Komut satırının
              kullanıcıya göstereceği metin de kaydedilir. Yanında hakem: setteki her 'tamam' kabul seçeneğinin
              ihtiyaçlarıyla atayıcı.
2. tekrar     ilk N isteğin yalnız Çağrı A'sı yeniden; ham yanıtlar karşılaştırılır.

yeniden-ata (Adım 9b): model çalıştırılmaz. Eski ham kayıttaki Çağrı A turlarının ham yanıtları sırayla geri verilir,
Çağrı A denetimi, atayıcı, denetim, CLI metni ve hakem yeni kodla yeniden üretilir. Her istekte turların mesajları,
son yanıt ve durum eskisiyle birebir aynı olmalı; değilse durur. Çağrı A kaydı ve süresi eskisinden alınır; tekrar
satırları olduğu gibi kopyalanır.

Set biçimi doğrulama setleriyle aynı ("kabul" listesi); ek alanlar `kategori`, `cift`. Adım 9 (v4): kabul
seçeneklerinde `pin_tercihleri` [{arayuz, sinyal (null = belirtilmemiş), gpio}] ve `kullanilmayacak` [gpio] (yoksa boş),
istekte `beklenen_sonuc` (Web AI'ın beklentisi). Hakem tercih ve yasaklarla çalışır.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import statistics
import time
import traceback
from collections import Counter
from pathlib import Path

from asu_llmcore import IzYazici, OllamaIstemcisi, OllamaYaniti, kayit

from . import cagrilar, hat, pinveri
from . import sozluk as sozluk_mod
from .__main__ import yazdir
from .denetim import Denetleyici
from .dogrulama import (KOK, _istatistik, _sha, a_eslesen, atayici_kos, cikarim_dogru, hakem_sec, ham_oku,
                        hat_kaydi, pin_ozeti, set_oku, verilen_metni)

TEKRAR_ADET = 15


# ------------------------------------------------------------------ koşu
def kos(set_yolu: Path, sha: str, ham: Path, tekrar: int = TEKRAR_ADET, uzerine: bool = False,
        istemci=None) -> Path:
    if ham.exists() and not uzerine:
        raise SystemExit(f"{ham} var; üzerine yazmak için --uzerine")
    ham.unlink(missing_ok=True)
    veri = pinveri.yukle()
    sozluk = sozluk_mod.yukle()
    denetleyici = Denetleyici(veri)
    varsayilan, istekler = set_oku(set_yolu, sha)
    ayar = cagrilar.ayar(onbellek_siniri=True)
    istemci = istemci or OllamaIstemcisi(ayar)
    iz = IzYazici(ham)
    ortak = {"set": set_yolu.name, "set_sha": _sha(set_yolu),
             "istemler": {p.name: _sha(p)[:12] for p in sorted(cagrilar.ISTEMLER.glob("*.txt"))}}

    def baglam_of(i):
        return {**varsayilan, **i["baglam"]}

    for i in istekler:                                                   # Koşu 1: A + atayıcı
        try:
            h = hat.calistir(i["metin"], i["paket"], baglam_of(i), veri, istemci, iz=None, sozluk=sozluk)
            tampon = io.StringIO()
            with contextlib.redirect_stdout(tampon):
                yazdir(h, veri)
            beklenen = [{"kabul_no": k, **atayici_kos(veri, denetleyici, i["paket"], baglam_of(i), sec["ihtiyaclar"],
                                                      sec.get("pin_tercihleri"), sec.get("kullanilmayacak"))}
                        for k, sec in enumerate(i["kabul"]) if sec["durum"] == "tamam" and sec["ihtiyaclar"]]
            iz.yaz({"kosu": "a_atayici", "id": i["id"], **ortak, "zaman": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    **hat_kaydi(h, ayar), "yazilim_hatasi": [i_.kod for i_ in h.yazilim_hatasi],
                    "cli": tampon.getvalue(), "beklenenle": beklenen})
            print("a_atayici", i["id"], h.a_durumu, (h.atama or {}).get("durum", "-"), h.sure_sn, flush=True)
        except Exception:
            iz.yaz({"kosu": "a_atayici", "id": i["id"], **ortak, "hata": traceback.format_exc()})
            print("a_atayici", i["id"], "HATA", flush=True)

    for i in istekler[:tekrar]:                                          # Koşu 2: Çağrı A tekrarı
        try:
            t0 = time.monotonic()
            a = cagrilar.ihtiyac_cikar(istemci, veri, i["metin"], sozluk, baglam_of(i))
            sure = round(time.monotonic() - t0, 2)
            iz.yaz({"kosu": "tekrar", "id": i["id"], **ortak, "zaman": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "cagri_a": kayit(a, ayar), "sure_sn": {"cagri_a": sure}})
            print("tekrar", i["id"], sure, flush=True)
        except Exception:
            iz.yaz({"kosu": "tekrar", "id": i["id"], **ortak, "hata": traceback.format_exc()})
            print("tekrar", i["id"], "HATA", flush=True)
    return ham


# ------------------------------------------------------------------ kayıttan yeniden atama
class KayitIstemcisi:
    """Kayıttaki Çağrı A turlarının ham yanıtlarını sırayla döner; model çalışmaz."""

    def __init__(self, turlar: list[dict]):
        self.hamlar = [t["ham"] for t in turlar]

    def uret(self, mesajlar, sema=None, sabit_onek=None):
        ham = self.hamlar.pop(0)
        try:
            return OllamaYaniti(ham=ham, json=json.loads(ham), model="kayit")
        except json.JSONDecodeError as e:
            return OllamaYaniti(ham=ham, json_hatasi=str(e), model="kayit")


def yeniden_ata(set_yolu: Path, sha: str, eski_ham: Path, ham: Path, uzerine: bool = False) -> Path:
    if ham.exists() and not uzerine:
        raise SystemExit(f"{ham} var; üzerine yazmak için --uzerine")
    ham.unlink(missing_ok=True)
    veri = pinveri.yukle()
    sozluk = sozluk_mod.yukle()
    denetleyici = Denetleyici(veri)
    varsayilan, istekler = set_oku(set_yolu, sha)
    bilgi = {i["id"]: i for i in istekler}
    ayar = cagrilar.ayar(onbellek_siniri=True)
    iz = IzYazici(ham)
    for satir in eski_ham.read_text(encoding="utf-8").splitlines():
        r = json.loads(satir)
        if r["kosu"] != "a_atayici" or "hata" in r:
            iz.yaz(r)
            continue
        i, eski_a = bilgi[r["id"]], r["cagri_a"]
        h = hat.calistir(r["metin"], r["paket"], r["baglam"], veri, KayitIstemcisi(eski_a["turlar"]), iz=None,
                         sozluk=sozluk)
        ayni = (h.cagri_a.durum.value == eski_a["durum"] and h.cagri_a.yanit == eski_a["yanit"]
                and [t.mesajlar for t in h.cagri_a.turlar] == [t["mesajlar"] for t in eski_a["turlar"]])
        if not ayni:
            raise SystemExit(f"{r['id']}: kayıttan yeniden üretilen Çağrı A eskisinden farklı")
        h.sure_sn = {"cagri_a": r["sure_sn"]["cagri_a"], **({"atayici": h.sure_sn["atayici"]} if "atayici" in h.sure_sn
                                                             else {}),
                     "toplam": round(r["sure_sn"]["cagri_a"] + h.sure_sn.get("atayici", 0), 3)}
        tampon = io.StringIO()
        with contextlib.redirect_stdout(tampon):
            yazdir(h, veri)
        baglam = {**varsayilan, **i["baglam"]}
        beklenen = [{"kabul_no": k, **atayici_kos(veri, denetleyici, i["paket"], baglam, sec["ihtiyaclar"],
                                                  sec.get("pin_tercihleri"), sec.get("kullanilmayacak"))}
                    for k, sec in enumerate(i["kabul"]) if sec["durum"] == "tamam" and sec["ihtiyaclar"]]
        iz.yaz({**r, **hat_kaydi(h, ayar), "cagri_a": eski_a, "yazilim_hatasi": [x.kod for x in h.yazilim_hatasi],
                "cli": tampon.getvalue(), "beklenenle": beklenen,
                "yeniden_atama": {"zaman": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "eski_ham": eski_ham.name}})
        print("yeniden_ata", r["id"], (h.atama or {}).get("durum", "-"), flush=True)
    return ham


# ------------------------------------------------------------------ puanlama
def karar(r: dict) -> str | None:
    """Atayıcının kararı; atamaya gelmediyse None."""
    return (r.get("gosterilen_atama") or {}).get("durum")


def hakem(r: dict, kabul_no: int | None) -> dict | None:
    """A doğruysa eşleşen kabul seçeneğiyle atayıcı ('tamam' + ihtiyaç değilse hakem yok), değilse ilk 'tamam'
    seçeneğiyle; 'tamam' seçeneği yoksa None."""
    return hakem_sec(r.get("beklenenle") or [], kabul_no)


def hakem_karari(r: dict, kabul_no: int | None) -> str | None:
    h = hakem(r, kabul_no)
    return h["atama"]["durum"] if h else None


def tur_dogru_mu(tur: dict, kabul: list[dict]) -> bool | None:
    """Bir turun yanıtı (denetimden geçmemiş olsa da) kabul listesine uyuyor mu; JSON yoksa None."""
    if not tur.get("json"):
        return None
    return a_eslesen({"durum": "GECTI", "yanit": tur["json"]}, kabul) is not None


def beklenen_metni(kabul: list[dict]) -> str:
    return " | ".join(f"{s['durum']} [{' '.join(sorted(s['ihtiyaclar'])) if s['ihtiyaclar'] is not None else 'null'}]"
                      + pin_ozeti(s.get("pin_tercihleri") or [], s.get("kullanilmayacak") or []) for s in kabul)


def beklenen_sonuc(istek: dict) -> str | None:
    """Web AI'ın beklentisi (istekte ya da ilk kabul seçeneğinde `beklenen_sonuc`); sözlükse `durum` alanı."""
    b = istek.get("beklenen_sonuc", (istek["kabul"][0] if istek["kabul"] else {}).get("beklenen_sonuc"))
    return b.get("durum") if isinstance(b, dict) else b


def hakem_sonucu(r: dict, istek: dict) -> str:
    """İlk kabul seçeneğiyle hakemin sonucu; seçenek 'tamam' + ihtiyaç değilse onun durumu ('pin_gerekmiyor')."""
    h = hakem_sec(r.get("beklenenle") or [], 0)
    if h is not None:
        return h["atama"]["durum"]
    s = istek["kabul"][0]
    return "pin_gerekmiyor" if s["durum"] == "tamam" else s["durum"]


MATRIS = re.compile(r"\d\s*[x×]\s*\d|matris", re.IGNORECASE)


def rapor_satirlari(set_yolu: Path, sha: str, ham: Path, cli_goster: tuple[str, ...] = ()) -> list[str]:
    _, istekler = set_oku(set_yolu, sha)
    bilgi = {i["id"]: i for i in istekler}
    sira = [i["id"] for i in istekler]
    satirlar = ham_oku(ham)

    def yer(kosu, i):
        return f"`{ham.name}:{satirlar[(kosu, i)][0]}`" if (kosu, i) in satirlar else "-"

    def tamam(kosu, i):
        return (kosu, i) in satirlar and "hata" not in satirlar[(kosu, i)][1]

    hatalar = [(k, i, r["hata"].strip().splitlines()[-1], no) for (k, i), (no, r) in satirlar.items() if "hata" in r]
    kos1 = {i: satirlar[("a_atayici", i)][1] for i in sira if tamam("a_atayici", i)}
    tek = {i: satirlar[("tekrar", i)][1] for i in sira if tamam("tekrar", i)}
    kat = {i: bilgi[i].get("kategori") or "-" for i in sira}

    a_es = {i: a_eslesen(r["cagri_a"], bilgi[i]["kabul"]) for i, r in kos1.items()}
    a_dogru = {i: a_es[i] is not None for i in kos1}
    a_yanlis = [i for i in kos1 if not a_dogru[i]]
    kararlar = {i: karar(r) for i, r in kos1.items()}
    hakemler = {i: hakem_karari(r, a_es[i]) for i, r in kos1.items()}
    uctan_uca = {i: a_dogru[i] and kararlar[i] == hakemler[i] for i in kos1}
    sans = [i for i in a_yanlis if kararlar[i] == hakemler[i]]
    hakemli = [i for i in kos1 if hakemler[i] is not None and kararlar[i] is not None]
    karar_uyusmaz = [i for i in hakemli if kararlar[i] != hakemler[i]]
    yazilim = {i: r.get("yazilim_hatasi") or [] for i, r in kos1.items()}
    cik = {i: cikarim_dogru(r["cagri_a"], bilgi[i]["kabul"]) for i, r in kos1.items()}
    a_tur = Counter(r["cagri_a"]["gecti_turu"] if r["cagri_a"]["durum"] == "GECTI" else r["cagri_a"]["durum"]
                    for r in kos1.values())
    k_dag = Counter(kararlar[i] or ("pin gerekmiyor" if r["a_durumu"] == "tamam" else "atamaya gelmedi")
                    for i, r in kos1.items())

    # Adım 9: pin bahisleri, tercihler, beklenen_sonuc, esnek dayanak
    def kod_say(r, kod):                                              # (ihlal, turlar boyunca) ve son turun uyarıları
        return (sum(x["kod"] == kod for t in r["cagri_a"]["turlar"] for x in t["ihlaller"])
                + sum(u["kod"] == kod for u in r["cagri_a"]["uyarilar"]))
    pin_kod = {k: {i: kod_say(r, k) for i, r in kos1.items()} for k in
               ("PIN_BAHSI_ATLANDI", "PIN_UYDURMA", "BELIRSIZ_PIN_TERCIHI", "BELIRSIZ_PIN_BAHSI", "TERCIH_IHTIYACSIZ")}
    tercihli = {i: r for i, r in kos1.items() if r.get("istek") and (r["istek"].get("pin_tercihleri")
                                                                        or r["istek"].get("kullanilmayacak"))}
    uygulandi = {}
    for i, r in tercihli.items():
        if kararlar[i] != "atandi":
            continue
        ist, ata = r["istek"], r["gosterilen_atama"]["atamalar"]
        arayuz = {n["id"]: n["arayuz"] for n in ist["ihtiyaclar"]}
        kullanan = {a["gpio"]: (arayuz[a["ihtiyac_id"]], a["sinyal"]) for a in ata}
        karsilanan: set[int] = set()                  # bir pin tek tercihi karşılar (Adım 9b)
        tercih_ok = True
        for t in ist["pin_tercihleri"]:
            ok = (kullanan.get(t["gpio"], (None,))[0] == t["arayuz"] and t["gpio"] not in karsilanan
                  and (not t["sinyal"] or kullanan[t["gpio"]][1] == t["sinyal"]))
            tercih_ok &= ok
            karsilanan.add(t["gpio"])
        uygulandi[i] = (tercih_ok, not set(ist.get("kullanilmayacak", [])) & set(kullanan))
    tu = [i for i in sira if kararlar.get(i) == "tercih_uygulanamadi"]
    esnek = {i: [u["mesaj"] for u in r["cagri_a"]["uyarilar"] if u["kod"] == "ESNEK_DAYANAK"] for i, r in kos1.items()}
    bek = {i: beklenen_sonuc(bilgi[i]) for i in sira}
    hk_sonuc = {i: hakem_sonucu(r, bilgi[i]) for i, r in kos1.items()}
    bek_var = [i for i in kos1 if bek[i] is not None]
    bek_uyusmaz = [i for i in bek_var if str(bek[i]) != hk_sonuc[i]]

    # SAYI_UYUSMAZ: işaretlenen her turun yanıtı kabule uyuyor muydu (uyuyorsa yanlış alarm), son yanıt doğru mu
    sayi = {}
    for i, r in kos1.items():
        turlar = [t for t in r["cagri_a"]["turlar"] if any(x["kod"] == "SAYI_UYUSMAZ" for x in t["ihlaller"])]
        if turlar:
            sayi[i] = [(t["no"], tur_dogru_mu(t, bilgi[i]["kabul"])) for t in turlar]
    yanlis_alarm = sum(1 for v in sayi.values() for _, d in v if d)
    gercek = sum(1 for v in sayi.values() for _, d in v if d is False)
    baglam_uy = {i: [u["mesaj"] for u in r["cagri_a"]["uyarilar"] if u["kod"] == "BAGLAM_CELISKI"]
                 for i, r in kos1.items()}

    # durum kullanımı
    durumlar = ("tamam", "desteklenmiyor", "emin_degilim")
    verilen_durum = {i: (r["cagri_a"]["yanit"] or {}).get("durum", r["cagri_a"]["durum"]) for i, r in kos1.items()}
    kabul_durum = {i: {s["durum"] for s in bilgi[i]["kabul"]} for i in sira}

    a_sure = [r["sure_sn"]["cagri_a"] for r in kos1.values()]
    atay_sure = [r["sure_sn"]["atayici"] for r in kos1.values() if "atayici" in r["sure_sn"]]
    top_sure = [r["sure_sn"]["toplam"] for r in kos1.values()]
    uzunluk = {i: len(bilgi[i]["metin"]) for i in kos1}
    ilk_tur = [i for i in kos1 if kos1[i]["cagri_a"]["gecti_turu"] == 1]

    def korelasyon(ids):
        try:
            return f"{statistics.correlation([uzunluk[i] for i in ids], [kos1[i]['sure_sn']['cagri_a'] for i in ids]):.2f}"
        except statistics.StatisticsError:                               # 2'den az nokta ya da sabit girdi
            return "-"

    # tekrar
    tek_ayni = {i: [t["ham"] for t in kos1[i]["cagri_a"]["turlar"]] == [t["ham"] for t in tek[i]["cagri_a"]["turlar"]]
                for i in tek if i in kos1}

    n = len(istekler)
    md = ["| Ölçüt | Değer |", "|---|---|",
          f"| Çağrı A doğru | {len(kos1) - len(a_yanlis)}/{n} |",
          f"| Çağrı A geçtiği tur (1 / 2 / 3); BILGI_YOK; KULLANICIYA; JSON_GECERSIZ | {a_tur.get(1, 0)} / "
          f"{a_tur.get(2, 0)} / {a_tur.get(3, 0)}; {a_tur.get('BILGI_YOK', 0)}; {a_tur.get('KULLANICIYA', 0)}; "
          f"{a_tur.get('JSON_GECERSIZ', 0)} |",
          f"| SAYI_UYUSMAZ (işaretlenen tur / istek) | {sum(len(v) for v in sayi.values())} / {len(sayi)} |",
          f"| SAYI_UYUSMAZ işaretlenen tur: yanıt kabule uyuyordu (yanlış alarm) / uymuyordu (gerçek yakalama) | "
          f"{yanlis_alarm} / {gercek} |",
          f"| SAYI_UYUSMAZ tetiklenen isteklerde son A doğru | {sum(a_dogru[i] for i in sayi)}/{len(sayi)} |",
          f"| BAGLAM_CELISKI (uyarı / istek) | {sum(len(v) for v in baglam_uy.values())} / "
          f"{sum(1 for v in baglam_uy.values() if v)} |",
          f"| model_cikarimi örneği / doğru | {sum(c[0] for c in cik.values())} / {sum(c[1] for c in cik.values())} |",
          f"| Atayıcı kararı: atandi / tercih_uygulanamadi / mumkun_degil / pin gerekmiyor / atamaya gelmedi | "
          f"{k_dag.get('atandi', 0)} / {k_dag.get('tercih_uygulanamadi', 0)} / {k_dag.get('mumkun_degil', 0)} / "
          f"{k_dag.get('pin gerekmiyor', 0)} / {k_dag.get('atamaya gelmedi', 0)} |",
          f"| PIN_BAHSI_ATLANDI / PIN_UYDURMA / belirsiz pin uyarısı (sayı) | "
          f"{sum(pin_kod['PIN_BAHSI_ATLANDI'].values())} / {sum(pin_kod['PIN_UYDURMA'].values())} / "
          f"{sum(pin_kod['BELIRSIZ_PIN_BAHSI'].values())} |",
          f"| Atandı + tercih/yasak: tercihler uygulandı / yasaklar kullanılmadı | "
          f"{sum(v[0] for v in uygulandi.values())}/{len(uygulandi)} / {sum(v[1] for v in uygulandi.values())}/"
          f"{len(uygulandi)} |",
          f"| Hakem (ilk kabul seçeneği) beklenen_sonuc ile aynı | {len(bek_var) - len(bek_uyusmaz)}/{len(bek_var)} |",
          f"| Esnek dayanak devreye giren istek | {sum(1 for v in esnek.values() if v)} |",
          f"| Atayıcı sonucunda denetim hatası (yazılım hatası), istek | {sum(1 for v in yazilim.values() if v)} |",
          f"| Atayıcı kararı hakemle aynı (ikisi de var) | {len(hakemli) - len(karar_uyusmaz)}/{len(hakemli)} |",
          f"| Uçtan uca doğru (A doğru ve karar hakemle aynı) | {sum(uctan_uca.values())}/{n} |",
          f"| A yanlış, nihai karar yine hakemle aynı | {len(sans)}/{len(a_yanlis)} |",
          f"| Tekrar: Çağrı A ham aynı | {sum(tek_ayni.values())}/{len(tek_ayni)} |",
          f"| Süre A (sn) | {_istatistik(a_sure)} |",
          f"| Süre atayıcı (sn) | {_istatistik(atay_sure)} |",
          f"| Süre toplam (sn) | {_istatistik(top_sure)} |",
          f"| Metin uzunluğu ile A süresi korelasyonu (Pearson r): tümü; A 1. turda geçenler | {korelasyon(list(kos1))}; "
          f"{korelasyon(ilk_tur)} |", ""]

    md += ["### Kategori bazında", "", "| Kategori | İstek | A doğru | Uçtan uca doğru |", "|---|---|---|---|"]
    for k in dict.fromkeys(kat[i] for i in sira):
        ids = [i for i in sira if kat[i] == k]
        md.append(f"| {k} | {len(ids)} | {sum(a_dogru.get(i, False) for i in ids)}/{len(ids)} | "
                  f"{sum(uctan_uca.get(i, False) for i in ids)}/{len(ids)} |")

    md += ["", "### Çift tutarlılığı (aynı `cift` değerindeki isteklerin Çağrı A çoklu kümesi)", ""]
    ciftler: dict = {}
    for i in sira:
        c = bilgi[i].get("cift")
        if c is not None:
            ciftler.setdefault(str(c), []).append(i)
    if ciftler:
        ayni_say = 0
        md += ["| Çift | İstekler | Çağrı A (durum [çoklu küme]) | Aynı | A doğru |", "|---|---|---|---|---|"]
        for c, ids in ciftler.items():
            kumeler = [verilen_metni(kos1[i]["cagri_a"]) if i in kos1 else "HATA" for i in ids]
            ayni = len(set(kumeler)) == 1 and "HATA" not in kumeler
            ayni_say += ayni
            md.append(f"| {c} | {', '.join(ids)} | {' / '.join(kumeler)} | {'evet' if ayni else 'HAYIR'} | "
                      f"{' / '.join('✓' if a_dogru.get(i) else '✗' for i in ids)} |")
        md += ["", f"Aynı: {ayni_say}/{len(ciftler)} çift."]
    else:
        md.append("Sette `cift` değeri yok.")

    md += ["", "### Çağrı A yanlışları", ""]
    if a_yanlis:
        md += ["| İstek | Kategori | Beklenen (kabul) | Verilen | İz |", "|---|---|---|---|---|"]
        md += [f"| {i} | {kat[i]} | {beklenen_metni(bilgi[i]['kabul'])} | {verilen_metni(kos1[i]['cagri_a'])}"
               + (f" desteklenmeyen: {kos1[i]['cagri_a']['yanit']['desteklenmeyenler']}"
                  if (kos1[i]["cagri_a"]["yanit"] or {}).get("desteklenmeyenler") else "")
               + f" | {yer('a_atayici', i)} |" for i in a_yanlis]
    else:
        md.append("Yok.")

    md += ["", "### SAYI_UYUSMAZ tetiklenen istekler", ""]
    if sayi:
        md += ["| İstek | İşaretlenen tur: yanıt kabule uyuyor mu | A geçtiği tur | Son A doğru | İz |",
               "|---|---|---|---|---|"]
        md += [f"| {i} | {', '.join(f'{no}: ' + ('-' if d is None else 'evet' if d else 'hayır') for no, d in v)} | "
               f"{kos1[i]['cagri_a']['gecti_turu'] or kos1[i]['cagri_a']['durum']} | {'✓' if a_dogru[i] else '✗'} | "
               f"{yer('a_atayici', i)} |" for i, v in sayi.items()]
    else:
        md.append("Yok.")

    md += ["", "### BAGLAM_CELISKI tetiklenen istekler", ""]
    tetik = [i for i in sira if baglam_uy.get(i)]
    if tetik:
        md += ["| İstek | Uyarı | İz |", "|---|---|---|"]
        md += [f"| {i} | {' / '.join(baglam_uy[i])} | {yer('a_atayici', i)} |" for i in tetik]
    else:
        md.append("Yok.")

    # Adım 10a: düzeltme turlarının dökümü ve diger_ifadeler
    md += ["", "### Düzeltme turları: tetikleyen hata kodu ve ifade (Adım 10a)", ""]
    tur_satir = []
    for i in sira:
        for t in (kos1[i]["cagri_a"]["turlar"][:-1] if i in kos1 else []):
            for x in t["ihlaller"]:
                if x.get("seviye", "hata") == "hata":
                    tur_satir.append(f"| {i} | {t['no']} | {x['kod']} | `{x['alan']}` | {x['mesaj'][:160]} | "
                                     f"{yer('a_atayici', i)} |")
    md += (["| İstek | Tur | Kod | Alan | İleti | İz |", "|---|---|---|---|---|---|", *tur_satir]
           if tur_satir else ["Yok."])
    md += ["", "### diger_ifadeler: ihtiyaç izi uyarısı alan öğeler (Adım 10a)", ""]
    diger_satir = []
    for i in sira:
        if i not in kos1:
            continue
        y = kos1[i]["cagri_a"].get("yanit") or {}
        uyari = {u["alan"]: u["mesaj"] for u in kos1[i]["cagri_a"]["uyarilar"] if u["kod"] == "DIGER_IHTIYAC_IZI"}
        for no, d in enumerate(y.get("diger_ifadeler", [])):
            if f"diger_ifadeler/{no}" in uyari:
                diger_satir.append(f"| {i} | «{d}» | {uyari[f'diger_ifadeler/{no}']} | {'✓' if a_dogru[i] else '✗'} | "
                                   f"{yer('a_atayici', i)} |")
    toplam_diger = sum(len((r["cagri_a"].get("yanit") or {}).get("diger_ifadeler", [])) for r in kos1.values())
    md.append(f"diger_ifadeler öğesi: {toplam_diger}; uyarı alan: {len(diger_satir)}.")
    if diger_satir:
        md += ["", "| İstek | Öğe | Uyarı | A doğru | İz |", "|---|---|---|---|---|", *diger_satir]

    yeni_uy = [(i, u) for i in sira if i in kos1 for u in kos1[i]["cagri_a"]["uyarilar"]
               if u["kod"] in ("DIGER_PIN_TERCIH_IZI", "DIGER_IHTIYAC_IZI", "SAYI_YARIM", "KAPSANMAYAN_CUMLE",
                                "SPI_ADET_IZI")]
    md += ["", "### Uyarılar: DIGER_PIN_TERCIH_IZI, DIGER_IHTIYAC_IZI, SAYI_YARIM, KAPSANMAYAN_CUMLE, SPI_ADET_IZI "
           "(son tur; Adım 10a–12)", ""]
    md += (["| İstek | Kod | Alan | İleti | A doğru | İz |", "|---|---|---|---|---|---|",
            *(f"| {i} | {u['kod']} | `{u['alan']}` | {u['mesaj']} | {'✓' if a_dogru[i] else '✗'} | {yer('a_atayici', i)} |"
              for i, u in yeni_uy)] if yeni_uy else ["Yok."])
    md += ["", "### Çağrı A durumu: setin kabul ettiği ve modelin verdiği", "",
           "| Durum | Kabul listesinde olan istek | Model verdi | Verdi ve doğru |", "|---|---|---|---|"]
    for d in durumlar:
        md.append(f"| {d} | {sum(d in kabul_durum[i] for i in sira)} | {sum(v == d for v in verilen_durum.values())} | "
                  f"{sum(v == d and a_dogru[i] for i, v in verilen_durum.items())} |")
    diger = Counter(v for v in verilen_durum.values() if v not in durumlar)
    if diger:
        md.append(f"| (diğer: {', '.join(f'{k} {v}' for k, v in diger.items())}) | - | {sum(diger.values())} | - |")
    tamam_disi = [i for i in kos1 if verilen_durum[i] != "tamam" or kabul_durum[i] != {"tamam"}]
    md += ["", "| İstek | Kabul durumları | Verilen | A doğru | İz |", "|---|---|---|---|---|",
           *(f"| {i} | {', '.join(sorted(kabul_durum[i]))} | {verilen_durum[i]} | {'✓' if a_dogru[i] else '✗'} | "
             f"{yer('a_atayici', i)} |" for i in tamam_disi)] if tamam_disi else ["", "Tamam dışı durum yok."]

    md += ["", "### Pin bahisleri (Çağrı A; turlar boyunca ihlal + son turun uyarıları)", "",
           "| Kod | Sayı | İstek |", "|---|---|---|"]
    md += [f"| {k} | {sum(v.values())} | {', '.join(i for i in sira if v.get(i)) or '-'} |" for k, v in pin_kod.items()]
    md += ["", "### Tercih ya da yasak içeren istekler (Çağrı A'nın verdiği)", ""]
    if tercihli:
        md += ["| İstek | A doğru | Çağrı A | Karar | Atandıysa: tercihler uygulandı / yasaklar kullanılmadı | İz |",
               "|---|---|---|---|---|---|"]
        md += [f"| {i} | {'✓' if a_dogru[i] else '✗'} | {verilen_metni(kos1[i]['cagri_a'])} | {kararlar[i] or '-'} | "
               + (f"{'evet' if uygulandi[i][0] else 'HAYIR'} / {'evet' if uygulandi[i][1] else 'HAYIR'}" if i in uygulandi
                  else "-") + f" | {yer('a_atayici', i)} |" for i in sira if i in tercihli]
    else:
        md.append("Yok.")
    md += ["", "### tercih_uygulanamadi: kullanıcıya gösterilen neden, öneri, alternatif", ""]
    if tu:
        md += ["| İstek | Tercih | Neden | Öneri | Alternatif atama | İz |", "|---|---|---|---|---|---|"]
        for i in tu:
            ay = kos1[i]["atayici"]
            for x in ay["tercih_sorunlari"]:
                t = x["tercih"]
                md.append(f"| {i} | {t['arayuz']}{' ' + t['sinyal'] if t['sinyal'] else ''} → GPIO{t['gpio']} | "
                          f"{x['neden']} | {x['oneri']} | {'var' if ay.get('alternatif') else 'yok'} | "
                          f"{yer('a_atayici', i)} |")
    else:
        md.append("Yok.")
    md += ["", "### Hakemin sonucu (ilk kabul seçeneğiyle) ve beklenen_sonuc", ""]
    if bek_var:
        md += [f"Uyuşan {len(bek_var) - len(bek_uyusmaz)}/{len(bek_var)}.", ""]
        if bek_uyusmaz:
            md += ["| İstek | beklenen_sonuc | Hakem | Hakemin nedeni / tercih sorunları | İz |", "|---|---|---|---|---|"]
            for i in bek_uyusmaz:
                h = hakem_sec(kos1[i].get("beklenenle") or [], 0) or {}
                neden = h.get("neden") or "; ".join(f"GPIO{x['tercih']['gpio']}: {x['neden']}"
                                                    for x in h.get("tercih_sorunlari", [])) or "-"
                md.append(f"| {i} | {bek[i]} | {hk_sonuc[i]} | {neden} | {yer('a_atayici', i)} |")
    else:
        md.append("Sette beklenen_sonuc yok.")
    md += ["", "### Esnek dayanak devreye giren istekler", ""]
    es = [i for i in sira if esnek.get(i)]
    md += (["| İstek | A doğru | Dayanak (model → metindeki parça) | İz |", "|---|---|---|---|",
            *(f"| {i} | {'✓' if a_dogru[i] else '✗'} | {' / '.join(esnek[i])} | {yer('a_atayici', i)} |" for i in es)]
           if es else ["Yok."])
    md += ["", "### v3 örüntülerinin karşılıkları: matris cihaz (metinde 'RxC' ya da 'matris') ve dayanak hatası", ""]
    mat = [i for i in sira if MATRIS.search(bilgi[i]["metin"])]
    day = [i for i in sira if i in kos1 and any(x["kod"] == "DAYANAK_YOK" for t in kos1[i]["cagri_a"]["turlar"]
                                                for x in t["ihlaller"])]
    md += ["| Örüntü | İstek | A doğru | A tur | Çağrı A | İz |", "|---|---|---|---|---|---|"]
    md += [f"| {ad} | {i} | {'✓' if a_dogru[i] else '✗'} | {kos1[i]['cagri_a']['gecti_turu'] or kos1[i]['cagri_a']['durum']} | "
           f"{verilen_metni(kos1[i]['cagri_a'])} | {yer('a_atayici', i)} |"
           for ad, ids in (("matris", mat), ("DAYANAK_YOK (herhangi bir turda)", day)) for i in ids if i in kos1]
    if not mat and not day:
        md.append("| - | - | - | - | - | - |")

    md += ["", "### Atayıcı kararı hakemden farklı", ""]
    if karar_uyusmaz:
        md += ["| İstek | A doğru | Karar | Hakem | Atayıcının nedeni | Hakemin nedeni | İz |", "|---|---|---|---|---|---|---|"]
        md += [f"| {i} | {'✓' if a_dogru[i] else '✗'} | {kararlar[i]} | {hakemler[i]} | "
               f"{(kos1[i]['atayici'] or {}).get('neden') or '-'} | {hakem(kos1[i], a_es[i])['neden'] or '-'} | "
               f"{yer('a_atayici', i)} |" for i in karar_uyusmaz]
    else:
        md.append("Yok.")

    md += ["", "### A yanlış, nihai karar hakemle aynı", ""]
    md += (["| İstek | Karar | Hakem | İz |", "|---|---|---|---|",
            *(f"| {i} | {kararlar[i] or '-'} | {hakemler[i] or '-'} | {yer('a_atayici', i)} |" for i in sans)]
           if sans else ["Yok."])

    md += ["", "### Yazılım hatası (atayıcının atamasında denetim hatası)", ""]
    yh = [i for i in sira if yazilim.get(i)]
    md += (["| İstek | Kodlar | İz |", "|---|---|---|",
            *(f"| {i} | {', '.join(yazilim[i])} | {yer('a_atayici', i)} |" for i in yh)] if yh else ["Yok."])

    md += ["", "### Tekrarlanabilirlik (ilk istekler, yalnız Çağrı A)", "",
           "| İstek | A ham aynı | İz (Koşu 1 / tekrar) |", "|---|---|---|"]
    md += [f"| {i} | {'=' if tek_ayni[i] else '≠'} | {yer('a_atayici', i)} / {yer('tekrar', i)} |" for i in tek_ayni]
    md += ["", f"A ham aynı {sum(tek_ayni.values())}/{len(tek_ayni)}."]

    md += ["", "### Pipeline hataları", ""]
    md += (["| Koşu | İstek | Son satır | İz |", "|---|---|---|---|",
            *(f"| {k} | {i} | `{s}` | `{ham.name}:{no}` |" for k, i, s, no in hatalar)] if hatalar else ["Yok."])

    md += ["", "### İstek ayrıntısı", "",
           "| İstek | Kategori | Çift | Paket | Karakter | A doğru | A tur | Çağrı A | Karar | Hakem | Uçtan uca | "
           "süre A sn | İz |", "|---" * 13 + "|"]
    for i in sira:
        r = kos1.get(i)
        if r is None:
            md.append(f"| {i} | {kat[i]} | {bilgi[i].get('cift') or '-'} | {bilgi[i]['paket']} | "
                      f"{len(bilgi[i]['metin'])} | HATA |" + " - |" * 6 + f" {yer('a_atayici', i)} |")
            continue
        md.append(f"| {i} | {kat[i]} | {bilgi[i].get('cift') or '-'} | {bilgi[i]['paket']} | {uzunluk[i]} | "
                  f"{'✓' if a_dogru[i] else '✗'} | {r['cagri_a']['gecti_turu'] or r['cagri_a']['durum']} | "
                  f"{verilen_metni(r['cagri_a'])} | {kararlar[i] or '-'} | {hakemler[i] or '-'} | "
                  f"{'✓' if uctan_uca[i] else '✗'} | {r['sure_sn']['cagri_a']} | {yer('a_atayici', i)} |")

    for i in cli_goster:
        md += ["", f"### Komut satırı çıktısı: {i} ({yer('a_atayici', i)})", ""]
        md += ["```", kos1[i]["cli"].rstrip(), "```"] if i in kos1 else ["Kayıt yok."]
    return md


TANIMLAR = [
    "Tanımlar:",
    "- Çağrı A doğru: modelin durumu kabul seçeneklerinden birininkiyle aynı ve o seçeneğin ihtiyaclar'ı null değilse "
    "arayüz çoklu kümesi (kalemler adet kadar çoğaltılmış) birebir.",
    "- Karar: atayıcının, Çağrı A'nın ihtiyaçlarıyla verdiği `durum` (atandi / mumkun_degil); A atamaya ihtiyaç "
    "göndermediyse yok.",
    "- Hakem: setteki beklenen ihtiyaçlarla atayıcı. A doğruysa eşleşen kabul seçeneği (seçenek 'tamam' + ihtiyaç "
    "değilse hakem yok), değilse ilk 'tamam' seçeneği; 'tamam' seçeneği yoksa hakem yok.",
    "- Verilen: Çağrı A'nın durumu [çoklu küme]; döngü geçmediyse (KULLANICIYA, JSON_GECERSIZ) o durum ve parantezde son "
    "turun yanıtı.",
    "- Uçtan uca doğru: A doğru ve karar hakemle aynı (ikisi de yoksa aynı sayılır).",
    "- SAYI_UYUSMAZ yanlış alarm: işaretlenen turun yanıtı kabul listesine uyuyordu; gerçek yakalama: uymuyordu.",
    "- Süre: ortalama / ortanca / en uzun, saniye. Karakter: istek metninin uzunluğu.",
    "- Adım 9: Çağrı A doğruluğuna pin tercihleri (beklenende sinyal null ise yalnız arayüz + GPIO) ve kullanılmayacak "
    "pinler de girer; seçenekte alan yoksa boş beklenir. Hakem tercih ve yasaklarla çalışır. beklenen_sonuc ilk kabul "
    "seçeneğinin hakemiyle kıyaslanır (seçenek 'tamam' + ihtiyaç değilse onun durumu, boş 'tamam' = pin_gerekmiyor).",
]


def rapor(set_yolu: Path, sha: str, ham: Path, sonuc: Path, dondurma_yolu: Path, tarih: str,
          cli_goster: tuple[str, ...] = ()) -> Path:
    _, istekler = set_oku(set_yolu, sha)
    ilk = json.loads(ham.read_text(encoding="utf-8").splitlines()[0])
    md = [f"# Kapsamlı ölçüm (A + atayıcı) — {tarih}", "",
          f"Set `{set_yolu.relative_to(KOK)}` (SHA-256 `{_sha(set_yolu)}`), {len(istekler)} istek. Model "
          f"{cagrilar.MODEL}, CPU, temperature 0, seed 42, num_ctx 8192, think kapalı, sınır açık, en_cok_tur "
          f"{cagrilar.EN_COK_TUR}. Atamayı kod atayıcı yapar (K-6); Çağrı B çalışmadı. İstemler: "
          + ", ".join(f"{k} {v}" for k, v in ilk["istemler"].items())
          + f". Ham iz: `{ham.name}` (satır numaraları aşağıda). Dondurma: `{dondurma_yolu.name}`.", "", *TANIMLAR, "",
          "## Özet", "", *rapor_satirlari(set_yolu, sha, ham, cli_goster)]
    sonuc.write_text("\n".join(md) + "\n", encoding="utf-8")
    return sonuc


def main() -> None:
    ap = argparse.ArgumentParser()
    alt = ap.add_subparsers(dest="komut", required=True)
    k = alt.add_parser("kos")
    k.add_argument("--uzerine", action="store_true")
    k.add_argument("--tekrar", type=int, default=TEKRAR_ADET, help="Çağrı A'sı yeniden koşacak ilk istek sayısı")
    r = alt.add_parser("rapor")
    for x in (k, r):
        x.add_argument("--set", type=Path, required=True)
        x.add_argument("--sha", required=True, help="setin beklenen SHA-256'sı; tutmazsa durur")
        x.add_argument("--ham", type=Path, required=True)
    r.add_argument("--sonuc", type=Path, required=True)
    r.add_argument("--dondurma", type=Path, required=True)
    r.add_argument("--tarih", required=True)
    r.add_argument("--cli-goster", default="", help="komut satırı çıktısı rapora eklenecek istekler (virgülle)")
    y = alt.add_parser("yeniden-ata")
    y.add_argument("--set", type=Path, required=True)
    y.add_argument("--sha", required=True)
    y.add_argument("--eski-ham", type=Path, required=True)
    y.add_argument("--ham", type=Path, required=True)
    y.add_argument("--uzerine", action="store_true")
    a = ap.parse_args()
    if a.komut == "yeniden-ata":
        print(yeniden_ata(a.set.resolve(), a.sha, a.eski_ham.resolve(), a.ham.resolve(), a.uzerine))
    elif a.komut == "kos":
        print(kos(a.set.resolve(), a.sha, a.ham.resolve(), a.tekrar, a.uzerine))
    else:
        print(rapor(a.set.resolve(), a.sha, a.ham.resolve(), a.sonuc.resolve(), a.dondurma, a.tarih,
                    tuple(x for x in a.cli_goster.split(",") if x)))


if __name__ == "__main__":
    main()

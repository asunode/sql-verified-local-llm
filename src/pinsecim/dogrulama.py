"""Adım 5: görülmemiş doğrulama setiyle ölçüm; Adım 6: gerileme koşusu. Ham sayılar; yorum yok.

Kullanım:
    python -m pinsecim.dogrulama dondurma --asama once|sonra [--ad v2] [--tarih T] [--set YOL] [--not "…"]
    python -m pinsecim.dogrulama kos                            # dört koşu → doc/olcum/<tarih>_dogrulama_ham.jsonl
    python -m pinsecim.dogrulama rapor                          # ham JSONL'den → doc/olcum/<tarih>_dogrulama_sonuc.md
    python -m pinsecim.dogrulama kos --set YOL --sha HEX --ham YOL --kosular model,atayici,tekrar
    python -m pinsecim.dogrulama rapor --set YOL --sha HEX --ham YOL --sonuc YOL --dondurma YOL
    python -m pinsecim.dogrulama gerileme --surum r0            # geliştirme + v1, model ve atayıcı → *_gerileme_r0.*

Koşular (en_cok_tur 3, sınır açık):
1. model     30 istek uçtan uca (A + B); kod atayıcı A'nın ihtiyaçlarıyla kıyas için yanında.
2. atayici   A'nın ihtiyaçlarıyla ve setteki beklenen ihtiyaçlarla (kabul seçeneklerinin her biri); hakem ikincisi.
3. tablosuz  Koşu 1'in A ihtiyaçlarıyla Çağrı B; pin tablosu, sabit pin kuralları, adet sınırları ve notlar
             verilmez (istemler/atama_sistem_tablosuz.txt). Şema, denetleyici, döngü aynı.
4. tekrar    Koşu 1'in ilk 10 isteği yeniden uçtan uca; ham yanıtlar karşılaştırılır.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import statistics
import subprocess
import time
import traceback
from collections import Counter
from pathlib import Path

from asu_llmcore import Durum, IzYazici, OllamaIstemcisi, PgOkuyucu, calistir, kayit

from . import cagrilar, hat, pinveri, semalar
from . import baglanti
from . import sozluk as sozluk_mod
from .atayici import Atayici
from .denetim import Denetleyici

KOK = Path(__file__).resolve().parents[2]
SET = KOK / "setler" / "dogrulama" / "dogrulama_seti_v1.json"
SET_SHA = "12211f6eccea718a80d8cce76813ae85a710a4048995334f4f8090677f393908"
OLCUM = KOK / "doc" / "olcum"
TARIH = "2026-11-20"
HAM = OLCUM / f"{TARIH}_dogrulama_ham.jsonl"
SONUC = OLCUM / f"{TARIH}_dogrulama_sonuc.md"
DONDURMA = OLCUM / f"{TARIH}_dogrulama_dondurma.md"
TEKRAR_ADET = 10

DONMUS_DOSYALAR = ["src/pinsecim/istemler/atama_sistem.txt", "src/pinsecim/istemler/ihtiyac_sistem.txt",
                   "src/pinsecim/semalar.py", "src/pinsecim/cagrilar.py", "src/pinsecim/hat.py",
                   "src/pinsecim/denetim.py", "src/pinsecim/atayici.py", "src/pinsecim/pinveri.py",
                   "src/pinsecim/sozluk.py", "src/pinsecim/kural_verisi.py",
                   "setler/dogrulama/dogrulama_seti_v1.json", "setler/gelistirme/gelistirme_seti.json",
                   "testler/veri/denetim_vakalari.json"]
KURAL_TABLOLARI = ["kural", "cevre_adet", "arayuz_tanimi", "arayuz_sinyal", "yorum", "sayi_sozcugu", "baglam_sozcugu",
                   "pin_bahsi_deseni", "soru_konusu", "durum_mesaji", "arayuz_es_adi", "kart", "modul_pin", "kart_pin",
                   "kart_parca"]   # özet: satırlar id'siz, içeriğe göre sıralı


def _sha(yol: Path) -> str:
    return hashlib.sha256(yol.read_bytes()).hexdigest()


# ------------------------------------------------------------------ dondurma
def dondurma_ozeti(ek_dosyalar: tuple[str, ...] = ()) -> dict:
    tablolar = {}
    with PgOkuyucu("donanim_okur", baglanti.VERITABANI, uygulama_adi="pinsecim_dogrulama", **baglanti.adres()) as db:
        for t in KURAL_TABLOLARI:
            satirlar = db.sorgu(f"SELECT to_jsonb(t) - 'id' AS s FROM {t} t ORDER BY (to_jsonb(t) - 'id')::text")
            metin = "\n".join(json.dumps(r["s"], sort_keys=True, ensure_ascii=False, default=str) for r in satirlar)
            tablolar[t] = {"satir": len(satirlar), "sha256": hashlib.sha256(metin.encode()).hexdigest()}
    commit = {ad: subprocess.run(["git", "-C", str(yol), "rev-parse", "--short", "HEAD"], capture_output=True,
                                 text=True, check=True).stdout.strip()
              for ad, yol in (("localllm_ass1", KOK), ("asu_llmcore", KOK.parent / "asu_llmcore"))}
    return {"zaman": time.strftime("%Y-%m-%d %H:%M:%S %z"),
            "dosyalar": {d: _sha(KOK / d) for d in [*DONMUS_DOSYALAR, *ek_dosyalar]}, "tablolar": tablolar, "commit": commit}


def commit_farki(depo: str, once: str, sonra: str) -> list[str]:
    """İki commit arasında değişen dosyalar."""
    if once == sonra:
        return []
    yol = KOK if depo == "localllm_ass1" else KOK.parent / "asu_llmcore"
    return subprocess.run(["git", "-C", str(yol), "diff", "--name-only", once, sonra], capture_output=True, text=True,
                          check=True).stdout.split()


def dondurma(asama: str, ad: str = "dogrulama", tarih: str = TARIH, ek_dosyalar: tuple[str, ...] = (),
             not_: str | None = None) -> Path:
    """Öncesi/sonrası kaydı. Sonrası, öncesindeki ek dosyaları ve notu kendisi okur."""
    once_yol = OLCUM / f"{tarih}_{ad}_dondurma_once.json"
    if asama == "sonra":
        o_ = json.loads(once_yol.read_text(encoding="utf-8"))
        ek_dosyalar = tuple(o_.get("ek_dosyalar", ()))
    o = dondurma_ozeti(ek_dosyalar)
    if asama == "once":
        o.update({"ek_dosyalar": list(ek_dosyalar), "not": not_})
    json_yol = OLCUM / f"{tarih}_{ad}_dondurma_{asama}.json"
    if json_yol.exists():
        raise SystemExit(f"{json_yol} var; eski kayıt değiştirilmez")
    json_yol.write_text(json.dumps(o, ensure_ascii=False, indent=1), encoding="utf-8")
    once = json.loads(once_yol.read_text(encoding="utf-8"))
    sonra_yol = OLCUM / f"{tarih}_{ad}_dondurma_sonra.json"
    sonra = json.loads(sonra_yol.read_text(encoding="utf-8")) if sonra_yol.exists() else None

    def hucre(a, b):
        return "-" if b is None else "aynı" if a == b else "FARKLI"

    md = [f"# Ölçüm dondurma kaydı ({ad}) — {tarih}", "",
          f"Öncesi: {once['zaman']}" + (f" · sonrası: {sonra['zaman']}" if sonra else "") + ". Ham: "
          f"`{tarih}_{ad}_dondurma_once.json`" + (f", `{tarih}_{ad}_dondurma_sonra.json`" if sonra else "") + ".", "",
          *([f"Değişiklik: {once['not']}", ""] if once.get("not") else []),
          "## Dosyalar (SHA-256)", "", "| Dosya | Öncesi | Sonrası |", "|---|---|---|"]
    for d, s in once["dosyalar"].items():
        b = sonra["dosyalar"].get(d) if sonra else None
        md.append(f"| `{d}` | `{s}` | {hucre(s, b)} |")
    md += ["", "## Kural tabloları (satır sayısı, satırların SHA-256'sı)", "", "| Tablo | Satır | SHA-256 | Sonrası |",
           "|---|---|---|---|"]
    for t, v in once["tablolar"].items():
        b = sonra["tablolar"].get(t) if sonra else None
        md.append(f"| `{t}` | {v['satir']} | `{v['sha256']}` | {hucre(v, b)} |")
    md += ["", "## Commit", "", "| Depo | Öncesi | Sonrası | Arada değişen dosyalar |", "|---|---|---|---|"]
    commit_ayni = True
    for r, c in once["commit"].items():
        if not sonra:
            md.append(f"| {r} | `{c}` | - | - |")
            continue
        arada = commit_farki(r, c, sonra["commit"][r])
        commit_ayni &= all(d.startswith("doc/") for d in arada)      # ölçüm kaydı commit'leri yalnız doc/ altında
        md.append(f"| {r} | `{c}` | `{sonra['commit'][r]}` | {', '.join(f'`{d}`' for d in arada) or '-'} |")
    if sonra:
        ayni = once["dosyalar"] == sonra["dosyalar"] and once["tablolar"] == sonra["tablolar"] and commit_ayni
        md += ["", "Commit farkı yalnız `doc/` altındaysa aynı sayılır (dondurma ve ölçüm kayıtları)."]
        md += ["", f"Sonuç: öncesi ve sonrası {'aynı' if ayni else 'FARKLI'}."]
    yol = OLCUM / f"{tarih}_{ad}_dondurma.md"
    yol.write_text("\n".join(md) + "\n", encoding="utf-8")
    return yol


# ------------------------------------------------------------------ tablosuz Çağrı B
def tablosuz_mesaji(istek: dict, veri: pinveri.PinVerisi) -> str:
    s = [f"Package: {istek['paket']}",
         "Board context: " + "; ".join(f"{cagrilar.BAGLAM_ACIKLAMA[k]}: {'yes' if v else 'no'}"
                                       for k, v in istek["baglam"].items()),
         "", "Needs (id: interface, signals):"]
    for n in istek["ihtiyaclar"]:
        s.append(f"{n['id']}: {n['arayuz']}, signals {', '.join(veri.arayuzler[n['arayuz']]['sinyaller'])}")
    return "\n".join(s)


def tablosuz_ata(istemci, veri: pinveri.PinVerisi, istek: dict):
    sistem = cagrilar._istem("atama_sistem_tablosuz.txt")
    mesaj = tablosuz_mesaji(istek, veri)
    sinyaller = sorted({s for n in istek["ihtiyaclar"] for s in veri.arayuzler[n["arayuz"]]["sinyaller"]})
    sema = semalar.model_atama_semasi([n["id"] for n in istek["ihtiyaclar"]], sinyaller,
                                      sorted(veri.paket_gpio[istek["paket"]]))
    return calistir(istemci, lambda: [{"role": "system", "content": sistem}, {"role": "user", "content": mesaj}],
                    sema, Denetleyici(veri).icin(istek), cagrilar.EN_COK_TUR,
                    bilgi_yok_mu=lambda y: y["durum"] == "bilgi_yok", sabit_onek=sistem)


# ------------------------------------------------------------------ koşular
def set_oku(yol: Path = SET, sha: str | None = SET_SHA) -> tuple[dict, list[dict]]:
    """Set → (varsayılan bağlam, istekler). Geliştirme setinin `beklenen` (+ `alternatifler`) alanı `kabul` listesine
    çevrilir; puanlama iki sette aynı işler."""
    if sha is not None and _sha(yol) != sha:
        raise SystemExit(f"{yol.name} SHA-256 tutmuyor: {_sha(yol)}")
    d = json.loads(yol.read_text(encoding="utf-8"))
    istekler = []
    for i in d["istekler"]:
        if "kabul" not in i:
            b = i["beklenen"]
            i = {**i, "kabul": [{"durum": b["durum"], "ihtiyaclar": b["ihtiyaclar"]},
                                *({"durum": b["durum"], "ihtiyaclar": a} for a in b.get("alternatifler", []))]}
        istekler.append(i)
    return d["varsayilan_baglam"], istekler


def _ihlaller(liste) -> list[dict]:
    return [dataclasses.asdict(i) for i in liste]


def hat_kaydi(h: hat.HatSonucu, ayar) -> dict:
    return {"metin": h.metin, "paket": h.paket, "baglam": h.baglam, "atayan": h.atayan, "a_durumu": h.a_durumu,
            "cagri_a": kayit(h.cagri_a, ayar), "istek": h.istek,
            "cagri_b": kayit(h.cagri_b, ayar) if h.cagri_b else None, "atayici": h.atayici,
            "gosterilen_atama": h.atama, "ihlaller": _ihlaller(h.ihlaller),
            "alternatif_ihlaller": _ihlaller(h.alternatif_ihlaller), "sure_sn": h.sure_sn}


def atayici_kos(veri, denetleyici, paket, baglam, ihtiyaclar: list[str], tercihler: list[dict] | None = None,
                yasaklar: list[int] | None = None) -> dict:
    """Atayıcı, verilen ihtiyaçlar (ve Adım 9'dan beri pin tercihleri, kullanılmayacak pinler) ile."""
    istek = {"paket": paket, "baglam": baglam, "ihtiyaclar": cagrilar.kimlik_ver([{"arayuz": a} for a in ihtiyaclar])}
    if tercihler or yasaklar:
        istek |= {"pin_tercihleri": [{"arayuz": t["arayuz"], "sinyal": t.get("sinyal") or "", "gpio": t["gpio"]}
                                     for t in tercihler or []], "kullanilmayacak": sorted(set(yasaklar or []))}
    r = Atayici(veri).ata(istek)
    kayit_ = {"istek": istek, "atama": r.atama, "neden": r.neden, "uyarilar": _ihlaller(denetleyici.denetle(istek, r.atama))}
    if r.tercih_sorunlari or r.alternatif:
        kayit_ |= {"tercih_sorunlari": r.tercih_sorunlari, "alternatif": r.alternatif}
    return kayit_


TUM_KOSULAR = ("model", "atayici", "tablosuz", "tekrar")


def kos(uzerine: bool = False, set_yolu: Path = SET, sha: str | None = SET_SHA, ham: Path = HAM,
        kosular: tuple[str, ...] = TUM_KOSULAR, ek: dict | None = None) -> Path:
    if ham.exists() and not uzerine:
        raise SystemExit(f"{ham} var; üzerine yazmak için --uzerine")
    ham.unlink(missing_ok=True)
    veri = pinveri.yukle()
    sozluk = sozluk_mod.yukle()
    denetleyici = Denetleyici(veri)
    varsayilan, istekler = set_oku(set_yolu, sha)
    ayar = cagrilar.ayar(onbellek_siniri=True)
    istemci = OllamaIstemcisi(ayar)
    iz = IzYazici(ham)
    ortak = {**(ek or {}), "set": set_yolu.name, "set_sha": _sha(set_yolu),
             "istemler": {p.name: _sha(p)[:12] for p in sorted(cagrilar.ISTEMLER.glob("*.txt"))}}

    def baglam_of(i):
        return {**varsayilan, **i["baglam"]}

    k1: dict[str, hat.HatSonucu] = {}
    for i in istekler:                                                   # Koşu 1: model
        try:
            h = hat.calistir(i["metin"], i["paket"], baglam_of(i), veri, istemci, model_ata=True, iz=None,
                             sozluk=sozluk)
            k1[i["id"]] = h
            iz.yaz({"kosu": "model", "id": i["id"], **ortak, "zaman": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    **hat_kaydi(h, ayar)})
            print("model", i["id"], h.a_durumu, h.cagri_b.durum.value if h.cagri_b else "-", h.sure_sn, flush=True)
        except Exception:
            iz.yaz({"kosu": "model", "id": i["id"], **ortak, "hata": traceback.format_exc()})
            print("model", i["id"], "HATA", flush=True)

    if "atayici" in kosular:
        for i in istekler:                                               # Koşu 2: atayıcı
            try:
                h = k1.get(i["id"])
                a_ile = None
                if h is not None and h.istek is not None:
                    a_ile = atayici_kos(veri, denetleyici, i["paket"], baglam_of(i),
                                        [n["arayuz"] for n in h.istek["ihtiyaclar"]])
                beklenen = [{"kabul_no": k, **atayici_kos(veri, denetleyici, i["paket"], baglam_of(i), sec["ihtiyaclar"])}
                            for k, sec in enumerate(i["kabul"]) if sec["durum"] == "tamam" and sec["ihtiyaclar"]]
                iz.yaz({"kosu": "atayici", "id": i["id"], **ortak, "a_ihtiyaclariyla": a_ile, "beklenenle": beklenen})
            except Exception:
                iz.yaz({"kosu": "atayici", "id": i["id"], **ortak, "hata": traceback.format_exc()})
                print("atayici", i["id"], "HATA", flush=True)

    if "tablosuz" in kosular:
        for i in istekler:                                               # Koşu 3: tablosuz
            h = k1.get(i["id"])
            if h is None or h.istek is None:
                iz.yaz({"kosu": "tablosuz", "id": i["id"], **ortak, "atlandi": "Koşu 1'de Çağrı B'ye gelmedi"})
                continue
            try:
                t0 = time.monotonic()
                s = tablosuz_ata(istemci, veri, h.istek)
                sure = round(time.monotonic() - t0, 2)
                ihl = denetleyici.denetle(h.istek, s.yanit) if s.yanit and s.yanit.get("durum") in (
                    "atandi", "mumkun_degil", "bilgi_yok") else []
                iz.yaz({"kosu": "tablosuz", "id": i["id"], **ortak, "zaman": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        "istek": h.istek, "kullanici_mesaji": tablosuz_mesaji(h.istek, veri), "cagri_b": kayit(s, ayar),
                        "ihlaller": _ihlaller(ihl), "sure_sn": {"cagri_b": sure}})
                print("tablosuz", i["id"], s.durum.value, sure, flush=True)
            except Exception:
                iz.yaz({"kosu": "tablosuz", "id": i["id"], **ortak, "hata": traceback.format_exc()})
                print("tablosuz", i["id"], "HATA", flush=True)

    if "tekrar" in kosular:
        for i in istekler[:TEKRAR_ADET]:                                 # Koşu 4: tekrar
            try:
                h = hat.calistir(i["metin"], i["paket"], baglam_of(i), veri, istemci, model_ata=True, kiyas=False,
                                 iz=None, sozluk=sozluk)
                iz.yaz({"kosu": "tekrar", "id": i["id"], **ortak, "zaman": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        **hat_kaydi(h, ayar)})
                print("tekrar", i["id"], h.sure_sn, flush=True)
            except Exception:
                iz.yaz({"kosu": "tekrar", "id": i["id"], **ortak, "hata": traceback.format_exc()})
                print("tekrar", i["id"], "HATA", flush=True)
    return ham


# ------------------------------------------------------------------ puanlama
def a_kalemleri(cagri_a: dict) -> list[str]:
    """Çağrı A'nın kalemleri adet kadar çoğaltılmış arayüz listesi (Adım 5 izlerinde adet yok: 1)."""
    return [n["arayuz"] for n in cagrilar.genislet((cagri_a["yanit"] or {}).get("ihtiyaclar", []))]


def tercihler_tutar(verilen: list[dict], beklenen: list[dict]) -> bool:
    """Pin tercihleri birebir mi: her beklenen tercih ayrı bir verilen tercihle aynı arayüz ve GPIO'da; beklenende
    sinyal null ise sinyale bakılmaz, değilse sinyal de aynı. Sayılar eşit olmalı."""
    if len(verilen) != len(beklenen):
        return False
    kalan = list(verilen)
    for b in beklenen:
        m = next((v for v in kalan if v["arayuz"] == b["arayuz"] and v["gpio"] == b["gpio"]
                  and (b.get("sinyal") is None or (v.get("sinyal") or None) == b["sinyal"])), None)
        if m is None:
            return False
        kalan.remove(m)
    return True


def a_eslesen(cagri_a: dict, kabul: list[dict]) -> int | None:
    """Kabul listesinde eşleşen seçeneğin sırası: durum aynı; ihtiyaclar null değilse çoklu küme birebir; pin
    tercihleri ve kullanılmayacak pinler birebir (seçenekte alan yoksa boş beklenir; Adım 9)."""
    y = cagri_a["yanit"]
    if cagri_a["durum"] not in ("GECTI", "BILGI_YOK") or not y:
        return None
    bulunan = Counter(a_kalemleri(cagri_a))
    tercih = y.get("pin_tercihleri", [])
    yasak = {p["gpio"] for p in y.get("kullanilmayacak_pinler", [])}
    for k, sec in enumerate(kabul):
        if (y["durum"] == sec["durum"] and (sec["ihtiyaclar"] is None or bulunan == Counter(sec["ihtiyaclar"]))
                and tercihler_tutar(tercih, sec.get("pin_tercihleri") or [])
                and yasak == set(sec.get("kullanilmayacak") or [])):
            return k
    return None


def cikarim_dogru(cagri_a: dict, kabul: list[dict]) -> tuple[int, int]:
    """(model_cikarimi örnekleri, bunlardan doğru olanlar). Örnek düzeyinde (kalem × adet): en çok örtüşen kabul
    seçeneğinin çoklu kümesinden önce istekte_acik örnekler düşülür; kalan kümede karşılığı olan çıkarım doğru."""
    kalemler = (cagri_a["yanit"] or {}).get("ihtiyaclar", [])
    cik = [n["arayuz"] for n in cagrilar.genislet([k for k in kalemler if k["kaynak"] == "model_cikarimi"])]
    if not cik:
        return 0, 0
    bulunan = Counter(a_kalemleri(cagri_a))
    secenekler = [Counter(s["ihtiyaclar"]) for s in kabul if s["ihtiyaclar"]]
    if not secenekler:
        return len(cik), 0
    kalan = max(secenekler, key=lambda c: sum((c & bulunan).values()))
    kalan = kalan - Counter(n["arayuz"] for n in cagrilar.genislet([k for k in kalemler if k["kaynak"] == "istekte_acik"]))
    dogru = 0
    for a in cik:
        if kalan[a] > 0:
            kalan[a] -= 1
            dogru += 1
    return len(cik), dogru


def hakem_sec(beklenenle: list[dict], kabul_no: int | None) -> dict | None:
    """Hakem kaydı: A doğruysa eşleşen kabul seçeneğininki; o seçenek 'tamam' + ihtiyaç değilse (desteklenmiyor,
    emin_degilim, pin gerekmiyor) hakem yok. A yanlışsa ilk 'tamam' seçeneğininki."""
    if not beklenenle:
        return None
    if kabul_no is None:
        return beklenenle[0]
    return next((x for x in beklenenle if x["kabul_no"] == kabul_no), None)


def pin_ozeti(tercihler: list[dict], yasaklar: list[int]) -> str:
    """' tercih [I2C SDA→6, SPI→19] yasak [2]'; ikisi de boşsa ''."""
    s = ""
    if tercihler:
        s += " tercih [" + ", ".join(sorted(f"{t['arayuz']}{' ' + t['sinyal'] if t.get('sinyal') else ''}→{t['gpio']}"
                                            for t in tercihler)) + "]"
    if yasaklar:
        s += f" yasak [{', '.join(str(g) for g in sorted(yasaklar))}]"
    return s


def verilen_metni(cagri_a: dict) -> str:
    """Çağrı A'nın verdiği: durum [çoklu küme]. Döngü geçmediyse (KULLANICIYA, JSON_GECERSIZ) önce o durum, son turun
    yanıtı parantezde."""
    y = cagri_a["yanit"]
    ozet = f"{y['durum']} [{' '.join(sorted(a_kalemleri(cagri_a))) or '-'}]" + pin_ozeti(
        y.get("pin_tercihleri", []), [p["gpio"] for p in y.get("kullanilmayacak_pinler", [])]) if y else None
    if cagri_a["durum"] in ("GECTI", "BILGI_YOK"):
        return ozet or cagri_a["durum"]
    return cagri_a["durum"] + (f" (son tur: {ozet})" if ozet else "")


GELMEDI = "B'ye gelmedi"
PIN_GEREKMIYOR = "pin gerekmiyor"


def b_ozeti(cagri_b: dict | None, r: dict | None = None) -> str:
    if cagri_b is None:
        if r is not None and r.get("a_durumu") == "tamam" and not (r["cagri_a"]["yanit"] or {}).get("ihtiyaclar"):
            return PIN_GEREKMIYOR
        return GELMEDI
    return f"{cagri_b['gecti_turu']}. turda geçti" if cagri_b["durum"] == "GECTI" else cagri_b["durum"]


def karar(cagri_b: dict | None) -> str | None:
    return (cagri_b["yanit"] or {}).get("durum") if cagri_b else None


def uyari_say(ihlaller: list[dict]) -> int:
    return sum(i["seviye"] == "uyari" for i in ihlaller)


def _istatistik(x: list[float]) -> str:
    return f"{statistics.mean(x):.1f} / {statistics.median(x):.1f} / {max(x):.1f}" if x else "-"


def ham_oku(ham: Path) -> dict[tuple[str, str], tuple[int, dict]]:
    satirlar = {}
    for no, s in enumerate(ham.read_text(encoding="utf-8").splitlines(), 1):
        r = json.loads(s)
        satirlar[(r["kosu"], r["id"])] = (no, r)
    return satirlar


def model_ozeti(ham: Path, kabul: dict[str, list[dict]]) -> dict[str, tuple]:
    """Bir ham dosyanın model koşusu: id → (A doğru, B özeti, karar). Önceki koşuyla kıyas için."""
    sonuc = {}
    for (k, i), (_, r) in ham_oku(ham).items():
        if k == "model" and "hata" not in r and i in kabul:
            sonuc[i] = (a_eslesen(r["cagri_a"], kabul[i]) is not None, b_ozeti(r["cagri_b"], r), karar(r["cagri_b"]))
    return sonuc


def v0_ozeti(yol: Path) -> dict[str, tuple]:
    """Adım 4 geliştirme seti v0 sonucu (JSON): id → (A doğru, B özeti, karar)."""
    sonuc = {}
    for s in json.loads(yol.read_text(encoding="utf-8"))["satirlar"]:
        b = (GELMEDI if s["b_sonuc"] is None else f"{s['b_gecti_turu']}. turda geçti" if s["b_sonuc"] == "GECTI"
             else s["b_sonuc"])
        sonuc[s["id"]] = (s["a_dogru"], b, s["model_karar"])
    return sonuc


def rapor_satirlari(set_yolu: Path, sha: str | None, ham: Path, onceki: dict[str, tuple] | None = None,
                    onceki_adi: str = "") -> list[str]:
    """Ham JSONL'den sonuç bölümleri (başlıksız markdown satırları). Koşmayan koşuların bölümleri yazılmaz."""
    varsayilan, istekler = set_oku(set_yolu, sha)
    kabul = {i["id"]: i["kabul"] for i in istekler}
    sira = [i["id"] for i in istekler]
    satirlar = ham_oku(ham)

    def yer(kosu, i):
        return f"`{ham.name}:{satirlar[(kosu, i)][0]}`" if (kosu, i) in satirlar else "-"

    def tamam(kosu, i, atla=()):
        return (kosu, i) in satirlar and not ({"hata", *atla} & satirlar[(kosu, i)][1].keys())

    hatalar = [(k, i, r["hata"].strip().splitlines()[-1], no) for (k, i), (no, r) in satirlar.items() if "hata" in r]
    model = {i: satirlar[("model", i)][1] for i in sira if tamam("model", i)}
    ata = {i: satirlar[("atayici", i)][1] for i in sira if tamam("atayici", i)}
    tsz = {i: satirlar[("tablosuz", i)][1] for i in sira if tamam("tablosuz", i, ("atlandi",))}
    tek = {i: satirlar[("tekrar", i)][1] for i in sira if tamam("tekrar", i)}
    tablosuz_var = any(k == "tablosuz" for k, _ in satirlar)

    # ---- A
    a_es = {i: a_eslesen(r["cagri_a"], kabul[i]) for i, r in model.items()}
    a_yanlis = [i for i in model if a_es[i] is None]
    cik = {i: cikarim_dogru(r["cagri_a"], kabul[i]) for i, r in model.items()}
    a_tur = Counter(r["cagri_a"]["gecti_turu"] if r["cagri_a"]["durum"] == "GECTI" else r["cagri_a"]["durum"]
                    for r in model.values())
    sayi = {i: sum(x["kod"] == "SAYI_UYUSMAZ" for t in r["cagri_a"]["turlar"] for x in t["ihlaller"])
            for i, r in model.items()}
    baglam_uy = {i: [u["mesaj"] for u in r["cagri_a"]["uyarilar"] if u["kod"] == "BAGLAM_CELISKI"]
                 for i, r in model.items()}

    def verilen(r):
        y = r["cagri_a"]["yanit"]
        return verilen_metni(r["cagri_a"]) + (
            f" desteklenmeyen: {y['desteklenmeyenler']}" if y.get("desteklenmeyenler") else "")

    def beklenen(i):
        return " | ".join(f"{s['durum']} [{' '.join(sorted(s['ihtiyaclar'])) if s['ihtiyaclar'] is not None else 'null'}]"
                          for s in kabul[i])

    # ---- hakem
    def hakem(i) -> dict | None:
        return hakem_sec(ata.get(i, {}).get("beklenenle") or [], a_es.get(i))

    def b_dagilim(kayitlar: dict) -> Counter:
        return Counter(b_ozeti(r["cagri_b"], r) for r in kayitlar.values())

    def duzeltme(kayitlar):
        sonuc = []
        for i, r in kayitlar.items():
            b = r["cagri_b"]
            if b and b["durum"] == "GECTI" and b["gecti_turu"] > 1:
                sonuc.append((i, b["gecti_turu"], [[x["kod"] for x in t["ihlaller"]] for t in b["turlar"]]))
        return sonuc

    def uyusma(kayitlar, kosu):
        n, ayni, liste = 0, 0, []
        for i, r in kayitlar.items():
            b = r["cagri_b"]
            if b is None:
                continue
            h = hakem(i)
            m = karar(b)
            if h is None:
                liste.append((i, m, "hakem yok (beklenen 'tamam' değil)", "", yer(kosu, i)))
                continue
            n += 1
            if m == h["atama"]["durum"]:
                ayni += 1
            else:
                liste.append((i, m, h["atama"]["durum"], h["neden"] or "", yer(kosu, i)))
        return ayni, n, liste

    def uyari_farki(kayitlar):
        fark = {}
        for i, r in kayitlar.items():
            b = r["cagri_b"]
            a = (ata.get(i) or {}).get("a_ihtiyaclariyla")
            if b and karar(b) == "atandi" and b["durum"] == "GECTI" and a and a["atama"]["durum"] == "atandi":
                fark[i] = (uyari_say(r["ihlaller"]), uyari_say(a["uyarilar"]))
        return fark

    def ayni_ihtiyacla(kayitlar):     # aynı (A'nın) ihtiyaçlarla atayıcının kararıyla
        cift = [(karar(r["cagri_b"]), ata[i]["a_ihtiyaclariyla"]["atama"]["durum"]) for i, r in kayitlar.items()
                if r.get("cagri_b") and (ata.get(i) or {}).get("a_ihtiyaclariyla")]
        return sum(x == y for x, y in cift), len(cift)

    ata_kayit = {i: r["a_ihtiyaclariyla"] for i, r in ata.items() if r["a_ihtiyaclariyla"]}
    ata_ayni = sum(1 for i, a in ata_kayit.items() if hakem(i) and a["atama"]["durum"] == hakem(i)["atama"]["durum"])
    ata_n = sum(1 for i in ata_kayit if hakem(i))
    ata_liste = [(i, a["atama"]["durum"], hakem(i)["atama"]["durum"], hakem(i)["neden"] or "", yer("atayici", i))
                 for i, a in ata_kayit.items() if hakem(i) and a["atama"]["durum"] != hakem(i)["atama"]["durum"]]

    m_dag, t_dag = b_dagilim(model), b_dagilim(tsz)
    t_atlanan = sum(1 for i in sira if ("tablosuz", i) in satirlar and "atlandi" in satirlar[("tablosuz", i)][1])
    m_uy, t_uy = uyusma(model, "model"), uyusma(tsz, "tablosuz")
    m_fark, t_fark = uyari_farki(model), uyari_farki(tsz)
    m_duz, t_duz = duzeltme(model), duzeltme(tsz)
    m_ai, t_ai = ayni_ihtiyacla(model), ayni_ihtiyacla(tsz)

    a_sure = [r["sure_sn"]["cagri_a"] for r in model.values()]
    b_sure = [r["sure_sn"]["cagri_b"] for r in model.values() if "cagri_b" in r["sure_sn"]]
    t_sure = [r["sure_sn"]["cagri_b"] for r in tsz.values() if r.get("cagri_b")]
    top_sure = [r["sure_sn"]["toplam"] for r in model.values()]
    atay_sure = [r["sure_sn"]["atayici"] for r in model.values() if "atayici" in r["sure_sn"]]

    sutunlar = ["Koşu 1 model", "Koşu 2 atayıcı (A ihtiyaçlarıyla)"] + (["Koşu 3 tablosuz"] if tablosuz_var else [])

    def satir(ad, *hucreler):
        return f"| {ad} | " + " | ".join(hucreler[:len(sutunlar)]) + " |"

    md = ["| Ölçüt | " + " | ".join(sutunlar) + " |", "|---" * (len(sutunlar) + 1) + "|",
          satir("Çağrı A doğru", f"{len(model) - len(a_yanlis)}/{len(istekler)}", "(Koşu 1'in A'sı)", "(Koşu 1'in A'sı)"),
          satir("Çağrı A geçtiği tur (1 / 2 / 3); BILGI_YOK; KULLANICIYA; JSON_GECERSIZ",
                f"{a_tur.get(1, 0)} / {a_tur.get(2, 0)} / {a_tur.get(3, 0)}; {a_tur.get('BILGI_YOK', 0)}; "
                f"{a_tur.get('KULLANICIYA', 0)}; {a_tur.get('JSON_GECERSIZ', 0)}", "-", "-"),
          satir("SAYI_UYUSMAZ (ihlal / istek)", f"{sum(sayi.values())} / {sum(1 for v in sayi.values() if v)}", "-", "-"),
          satir("Bağlam uyarısı BAGLAM_CELISKI (uyarı / istek)",
                f"{sum(len(v) for v in baglam_uy.values())} / {sum(1 for v in baglam_uy.values() if v)}", "-", "-"),
          satir("model_cikarimi örneği / doğru", f"{sum(c[0] for c in cik.values())} / {sum(c[1] for c in cik.values())}",
                "-", "-")]
    for anahtar, ad in (("1. turda geçti", "B 1. turda geçti"), ("2. turda geçti", "B 2. turda geçti"),
                        ("3. turda geçti", "B 3. turda geçti"), ("KULLANICIYA", "KULLANICIYA"),
                        ("JSON_GECERSIZ", "JSON_GECERSIZ"), ("BILGI_YOK", "BILGI_YOK (bilgi_yok)")):
        md.append(satir(ad, str(m_dag.get(anahtar, 0)), "-", str(t_dag.get(anahtar, 0))))
    md += [satir("Çağrı A durdurduğu için B'ye gelmeyen", str(m_dag.get(GELMEDI, 0)), "-", str(t_atlanan)),
           satir("Pin gerekmiyor (tamam + boş ihtiyaç)", str(m_dag.get(PIN_GEREKMIYOR, 0)), "-", "-"),
           satir("Mümkün/imkânsız kararı hakemle aynı", f"{m_uy[0]}/{m_uy[1]}", f"{ata_ayni}/{ata_n}", f"{t_uy[0]}/{t_uy[1]}"),
           satir("Kararı aynı (A'nın) ihtiyaçlarla atayıcıyla aynı", f"{m_ai[0]}/{m_ai[1]}", "-", f"{t_ai[0]}/{t_ai[1]}"),
           satir("Uyarı farkı toplamı (model − atayıcı), istek sayısı",
                 f"{sum(a - b for a, b in m_fark.values())} ({len(m_fark)} istek)", "-",
                 f"{sum(a - b for a, b in t_fark.values())} ({len(t_fark)} istek)"),
           satir("Süre A", _istatistik(a_sure), "-", "-"),
           satir("Süre B", _istatistik(b_sure), _istatistik(atay_sure), _istatistik(t_sure)),
           satir("Süre toplam (A + B + atayıcı kıyası)", _istatistik(top_sure), "-", "-"), ""]

    if onceki is not None:
        md += [f"### {onceki_adi}'e göre değişen istekler (A doğru · B · karar)", ""]
        degisen = []
        for i in sira:
            if i in model and i in onceki:
                simdi = (a_es[i] is not None, b_ozeti(model[i]["cagri_b"], model[i]), karar(model[i]["cagri_b"]))
                if simdi != onceki[i]:
                    o = onceki[i]
                    degisen.append(f"| {i} | {'✓' if o[0] else '✗'} · {o[1]} · {o[2] or '-'} | "
                                   f"{'✓' if simdi[0] else '✗'} · {simdi[1]} · {simdi[2] or '-'} | {yer('model', i)} |")
        md += (["| İstek | Önce | Şimdi | İz |", "|---|---|---|---|", *degisen] if degisen else ["Yok."]) + [""]

    md += ["### Çağrı A yanlışları (Koşu 1)", ""]
    if a_yanlis:
        md += ["| İstek | Beklenen (kabul) | Verilen | İz |", "|---|---|---|---|"]
        md += [f"| {i} | {beklenen(i)} | {verilen(model[i])} | {yer('model', i)} |" for i in a_yanlis]
    else:
        md.append("Yok.")
    md += ["", "### SAYI_UYUSMAZ ve bağlam uyarısı tetiklenen istekler", ""]
    tetik = [i for i in sira if sayi.get(i) or baglam_uy.get(i)]
    if tetik:
        md += ["| İstek | SAYI_UYUSMAZ (turlar boyunca) | A geçtiği tur | Bağlam uyarıları | İz |", "|---|---|---|---|---|"]
        md += [f"| {i} | {sayi[i]} | {model[i]['cagri_a']['gecti_turu'] or model[i]['cagri_a']['durum']} | "
               f"{' / '.join(baglam_uy[i]) or '-'} | {yer('model', i)} |" for i in tetik]
    else:
        md.append("Yok.")
    md += ["", "### model_cikarimi örnekleri (Koşu 1)", "", "| İstek | Örnek | Doğru |", "|---|---|---|"]
    md += [f"| {i} | {c[0]} | {c[1]} |" for i, c in cik.items() if c[0]]

    for baslik, liste, kosu in (("Koşu 1 model", m_duz, "model"), ("Koşu 3 tablosuz", t_duz, "tablosuz")):
        if kosu == "tablosuz" and not tablosuz_var:
            continue
        md += ["", f"### Düzeltme turu: 1. turda hata alıp sonra geçenler — {baslik}", ""]
        if liste:
            md += ["| İstek | Geçtiği tur | Turların hata kodları | İz |", "|---|---|---|---|"]
            md += [f"| {i} | {t} | {' → '.join(','.join(k) or '-' for k in kod)} | {yer(kosu, i)} |" for i, t, kod in liste]
        else:
            md.append("Yok.")
    for baslik, liste in (("Koşu 1 model", m_uy[2]), ("Koşu 2 atayıcı (A ihtiyaçlarıyla)", ata_liste),
                          *((("Koşu 3 tablosuz", t_uy[2]),) if tablosuz_var else ())):
        md += ["", f"### Mümkün/imkânsız uyuşmazlıkları — {baslik}", ""]
        if liste:
            md += ["| İstek | Karar | Hakem | Hakemin nedeni | İz |", "|---|---|---|---|---|"]
            md += [f"| {i} | {m or '-'} | {h} | {n} | {y} |" for i, m, h, n, y in liste]
        else:
            md.append("Yok.")

    md += ["", "### Çağrı B KULLANICIYA: hakemin kararı — Koşu 1 model", ""]
    kul = [i for i in sira if i in model and (model[i]["cagri_b"] or {}).get("durum") == "KULLANICIYA"]
    if kul:
        md += ["| İstek | Son turdaki karar | Son turun hata kodları | Hakem | Hakemin nedeni | İz |", "|---|---|---|---|---|---|"]
        for i in kul:
            b, h = model[i]["cagri_b"], hakem(i)
            kodlar = ",".join(x["kod"] for x in b["turlar"][-1]["ihlaller"]) if b["turlar"] else ""
            md.append(f"| {i} | {karar(b) or '-'} | {kodlar or '-'} | {h['atama']['durum'] if h else 'hakem yok'} | "
                      f"{(h['neden'] or '') if h else ''} | {yer('model', i)} |")
    else:
        md.append("Yok.")

    md += ["", "### Uyarı sayısı (istek başına; model / atayıcı → fark)", "",
           "| İstek | Koşu 1 model |" + (" Koşu 3 tablosuz |" if tablosuz_var else ""),
           "|---|---|" + ("---|" if tablosuz_var else "")]
    for i in sira:
        if i in m_fark or i in t_fark:
            hc = lambda f: f"{f[i][0]} / {f[i][1]} → {f[i][0] - f[i][1]}" if i in f else "-"   # noqa: E731
            md.append(f"| {i} | {hc(m_fark)} |" + (f" {hc(t_fark)} |" if tablosuz_var else ""))

    if tablosuz_var:
        ilk, ilk_istek = Counter(), Counter()
        for r in tsz.values():
            b = r.get("cagri_b")
            if b and b["turlar"]:
                kodlar = [x["kod"] for x in b["turlar"][0]["ihlaller"]]
                if b["turlar"][0]["durum"] == "JSON_GECERSIZ":
                    kodlar.append("(JSON_GECERSIZ)")
                ilk.update(kodlar)
                ilk_istek.update(set(kodlar))
        md += ["", "### Tablosuz model: ilk turdaki hata kodları", "",
               f"B çalışan {sum(t_dag.values())} istek; 1. turda hatasız geçen {t_dag.get('1. turda geçti', 0)}.", "",
               "| Kod | İhlal sayısı | İstek sayısı |", "|---|---|---|"]
        md += [f"| {k} | {v} | {ilk_istek[k]} |" for k, v in ilk.most_common()] or ["| - | 0 | 0 |"]

    if tek:
        md += ["", f"### Tekrarlanabilirlik (Koşu 1'in ilk {TEKRAR_ADET} isteği yeniden)", "",
               "| İstek | A ham aynı | B ham aynı | İz (Koşu 1 / tekrar) |", "|---|---|---|---|"]
        a_ayni = a_n = b_ayni = b_n = 0
        for i in sira[:TEKRAR_ADET]:
            if i not in tek or i not in model:
                md.append(f"| {i} | - | - | {yer('model', i)} / {yer('tekrar', i)} |")
                continue
            ha = [t["ham"] for t in model[i]["cagri_a"]["turlar"]] == [t["ham"] for t in tek[i]["cagri_a"]["turlar"]]
            mb_, tb_ = model[i]["cagri_b"], tek[i]["cagri_b"]
            hb = None if mb_ is None and tb_ is None else (mb_ is not None and tb_ is not None and
                                                           [t["ham"] for t in mb_["turlar"]] == [t["ham"] for t in tb_["turlar"]])
            a_n += 1
            a_ayni += ha
            if hb is not None:
                b_n += 1
                b_ayni += hb
            md.append(f"| {i} | {'=' if ha else '≠'} | {'-' if hb is None else '=' if hb else '≠'} | "
                      f"{yer('model', i)} / {yer('tekrar', i)} |")
        md += ["", f"A ham aynı {a_ayni}/{a_n}; B ham aynı {b_ayni}/{b_n} (B'nin çalıştığı istekler)."]

    md += ["", "### Pipeline hataları", ""]
    if hatalar:
        md += ["| Koşu | İstek | Son satır | İz |", "|---|---|---|---|"]
        md += [f"| {k} | {i} | `{s}` | `{ham.name}:{no}` |" for k, i, s, no in hatalar]
    else:
        md.append("Yok.")

    md += ["", "### İstek ayrıntısı", "",
           "| İstek | Paket | A doğru | A durumu | A ihtiyaçlar | B (model) | karar |"
           + (" B (tablosuz) | karar |" if tablosuz_var else "") + " hakem | süre A / B sn | İz (model) |",
           "|---" * (10 + (2 if tablosuz_var else 0)) + "|"]
    paket = {i["id"]: i["paket"] for i in istekler}
    for i in sira:
        r = model.get(i)
        if r is None:
            md.append(f"| {i} | {paket[i]} | HATA |" + " |" * (8 + (2 if tablosuz_var else 0)) + f" {yer('model', i)} |")
            continue
        t = tsz.get(i, {})
        h = hakem(i)
        tsz_hucre = (f" {b_ozeti(t['cagri_b']) if t.get('cagri_b') else '-'} | {karar(t.get('cagri_b')) or '-'} |"
                     if tablosuz_var else "")
        md.append(f"| {i} | {paket[i]} | {'✓' if a_es[i] is not None else '✗'} | {r['a_durumu']} | "
                  f"{' '.join(sorted(a_kalemleri(r['cagri_a']))) or '-'} | {b_ozeti(r['cagri_b'], r)} | "
                  f"{karar(r['cagri_b']) or '-'} |{tsz_hucre} {h['atama']['durum'] if h else '-'} | "
                  f"{r['sure_sn']['cagri_a']} / {r['sure_sn'].get('cagri_b', '-')} | {yer('model', i)} |")
    return md


def rapor(set_yolu: Path = SET, sha: str | None = SET_SHA, ham: Path = HAM, sonuc: Path = SONUC,
          dondurma_yolu: Path = DONDURMA, tarih: str = TARIH) -> Path:
    """Sonuç belgesi (varsayılan: Adım 5, doğrulama seti v1, dört koşu)."""
    _, istekler = set_oku(set_yolu, sha)
    ilk = json.loads(ham.read_text(encoding="utf-8").splitlines()[0])
    md = [f"# Doğrulama ölçümü — {tarih}", "",
          f"Set `{set_yolu.relative_to(KOK)}` (SHA-256 `{_sha(set_yolu)}`), {len(istekler)} istek. Model "
          f"{cagrilar.MODEL}, CPU, temperature 0, seed 42, num_ctx 8192, think kapalı, sınır açık, en_cok_tur "
          f"{cagrilar.EN_COK_TUR}. İstemler: " + ", ".join(f"{k} {v}" for k, v in ilk["istemler"].items())
          + f". Ham iz: `{ham.name}` (satır numaraları aşağıda). Dondurma: `{dondurma_yolu.name}`.", "", *TANIMLAR, "",
          "## Özet", "", *rapor_satirlari(set_yolu, sha, ham)]
    sonuc.write_text("\n".join(md) + "\n", encoding="utf-8")
    return sonuc


TANIMLAR = [
    "Tanımlar:",
    "- Çağrı A doğru: modelin durumu kabul seçeneklerinden birininkiyle aynı ve o seçeneğin ihtiyaclar'ı null değilse "
    "arayüz çoklu kümesi (kalemler adet kadar çoğaltılmış) birebir.",
    "- model_cikarimi doğru: örnek düzeyinde; en çok örtüşen kabul seçeneğinin çoklu kümesinden istekte_acik örnekler "
    "düşülür, kalan kümede karşılığı olan çıkarım örneği doğru.",
    "- Hakem: setteki beklenen ihtiyaçlarla kod atayıcı. A doğruysa eşleşen kabul seçeneği (seçenek 'tamam' + ihtiyaç "
    "değilse hakem yok), değilse ilk 'tamam' seçeneği.",
    "- Karar: Çağrı B'nin son turundaki `durum` (atandi / mumkun_degil / bilgi_yok).",
    "- Uyarı farkı: model atamasının uyarı sayısı eksi aynı ihtiyaçlarla atayıcının uyarı sayısı; yalnız ikisi de "
    "`atandi` ve B denetimden geçtiyse.",
    "- Süre: ortalama / ortanca / en uzun, saniye.",
]

GELISTIRME = KOK / "setler" / "gelistirme" / "gelistirme_seti.json"
GELISTIRME_SHA = "b5434c6d17ea5ef2bdf17c3968e5a5cba350babd45cf976883179131d0666f38"
V0 = OLCUM / f"{TARIH}_gelistirme_v0.json"


def gerileme(surum: str, uzerine: bool = False, yalniz_rapor: bool = False) -> Path:
    """Adım 6 gerileme koşusu: geliştirme seti (20) ve doğrulama seti v1 (30; görülmüş set, T-26) uçtan uca, model ve
    atayıcı koşuları. Önceki sonuçla kıyas: geliştirme v0 (Adım 4), v1 Adım 5."""
    setler = [("Geliştirme seti", GELISTIRME, GELISTIRME_SHA, "gelistirme", v0_ozeti(V0), "Adım 4 v0"),
              ("Doğrulama seti v1 — görülmüş set (T-26)", SET, SET_SHA, "dogrulama_v1",
               model_ozeti(HAM, {i["id"]: i["kabul"] for i in set_oku()[1]}), "Adım 5")]
    md = [f"# Gerileme koşusu {surum} — {TARIH}", ""]
    for baslik, yol, sha, ad, onceki, onceki_adi in setler:
        ham = OLCUM / f"{TARIH}_gerileme_{surum}_{ad}.jsonl"
        if not yalniz_rapor:
            kos(uzerine, yol, sha, ham, ("model", "atayici"), ek={"olcum": f"gerileme_{surum}"})
        ilk = json.loads(ham.read_text(encoding="utf-8").splitlines()[0])
        md += [f"## {baslik}", "",
               f"`{yol.relative_to(KOK)}` (SHA-256 `{sha[:12]}…`). Ham iz: `{ham.name}`. İstemler: "
               + ", ".join(f"{k} {v}" for k, v in ilk["istemler"].items()) + ".", "",
               *rapor_satirlari(yol, sha, ham, onceki, onceki_adi), ""]
    md[2:2] = [f"Model {cagrilar.MODEL}, CPU, temperature 0, seed 42, num_ctx 8192, think kapalı, sınır açık, en_cok_tur "
               f"{cagrilar.EN_COK_TUR}. Koşular: model (A + B) ve atayıcı; tablosuz ve tekrar yok.", "", *TANIMLAR, ""]
    yol = OLCUM / f"{TARIH}_gerileme_{surum}.md"
    yol.write_text("\n".join(md) + "\n", encoding="utf-8")
    return yol


def main() -> None:
    ap = argparse.ArgumentParser()
    alt = ap.add_subparsers(dest="komut", required=True)
    d = alt.add_parser("dondurma")
    d.add_argument("--asama", required=True, choices=["once", "sonra"])
    d.add_argument("--ad", default="dogrulama", help="kayıt adı: dogrulama (Adım 5) ya da v2 (Adım 6 sonrası)")
    d.add_argument("--tarih", default=TARIH, help="kayıt dosyalarının tarih öneki")
    d.add_argument("--set", action="append", default=[], help="ayrıca dondurulacak set dosyası (proje köküne göre)")
    d.add_argument("--not", dest="not_", help="öncesi kaydına: neyin neden değiştiği (bir satır)")
    k = alt.add_parser("kos")
    k.add_argument("--uzerine", action="store_true")
    r = alt.add_parser("rapor")
    for x in (k, r):
        x.add_argument("--set", type=Path, default=SET, help="set dosyası (varsayılan v1)")
        x.add_argument("--sha", default=SET_SHA, help="setin beklenen SHA-256'sı; tutmazsa durur")
        x.add_argument("--ham", type=Path, default=HAM, help="ham JSONL")
    k.add_argument("--kosular", default=",".join(TUM_KOSULAR), help="virgülle: model,atayici,tablosuz,tekrar")
    r.add_argument("--sonuc", type=Path, default=SONUC)
    r.add_argument("--dondurma", type=Path, default=DONDURMA)
    r.add_argument("--tarih", default=TARIH)
    g = alt.add_parser("gerileme")
    g.add_argument("--surum", required=True)
    g.add_argument("--uzerine", action="store_true")
    g.add_argument("--yalniz-rapor", action="store_true", help="koşmadan, var olan ham dosyalardan raporu yeniden yaz")
    a = ap.parse_args()
    if a.komut == "dondurma":
        print(dondurma(a.asama, a.ad, a.tarih, tuple(a.set), a.not_))
    elif a.komut == "kos":
        kosular = tuple(a.kosular.split(","))
        if not set(kosular) <= set(TUM_KOSULAR) or "model" not in kosular:
            raise SystemExit(f"--kosular: {TUM_KOSULAR} içinden, 'model' dahil")
        print(kos(a.uzerine, a.set.resolve(), a.sha, a.ham.resolve(), kosular))
    elif a.komut == "rapor":
        print(rapor(a.set.resolve(), a.sha, a.ham.resolve(), a.sonuc.resolve(), a.dondurma, a.tarih))
    else:
        print(gerileme(a.surum, a.uzerine, a.yalniz_rapor))


if __name__ == "__main__":
    main()

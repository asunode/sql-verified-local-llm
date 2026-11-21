"""Adım 4 ölçümleri: önbellek sınırı ölçümü ve geliştirme seti koşusu. Ham sayılar; puan ya da yorum yok.

Kullanım:
    python -m pinsecim.olcum onbellek                 # ilk 10 istek, üç koşu → doc/olcum/<tarih>_onbellek.{json,md}
    python -m pinsecim.olcum gelistirme --surum v0    # 20 istek → doc/olcum/<tarih>_gelistirme_v0.{json,md}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from collections import Counter
from pathlib import Path

from asu_llmcore import Durum, OllamaIstemcisi

from . import cagrilar, hat, pinveri

KOK = Path(__file__).resolve().parents[2]
SET = KOK / "setler" / "gelistirme" / "gelistirme_seti.json"
OLCUM = KOK / "doc" / "olcum"


def set_oku() -> tuple[dict, list[dict]]:
    d = json.loads(SET.read_text(encoding="utf-8"))
    return d["varsayilan_baglam"], d["istekler"]


def istem_ozeti() -> dict:
    return {ad: hashlib.sha256((cagrilar.ISTEMLER / ad).read_bytes()).hexdigest()[:12]
            for ad in sorted(p.name for p in cagrilar.ISTEMLER.glob("*.txt"))}


def hamlar(h: hat.HatSonucu) -> dict:
    return {"a": [t.ham for t in h.cagri_a.turlar], "b": [t.ham for t in h.cagri_b.turlar] if h.cagri_b else None}


def _kos(veri, istek: dict, varsayilan: dict, istemci) -> hat.HatSonucu:
    return hat.calistir(istek["metin"], istek["paket"], {**varsayilan, **istek["baglam"]}, veri, istemci,
                        model_ata=True, iz=None)


# ------------------------------------------------------------------ önbellek
def onbellek() -> Path:
    veri = pinveri.yukle()
    varsayilan, istekler = set_oku()
    hedef, dolgu = istekler[:10], istekler[10:20]
    acik = OllamaIstemcisi(cagrilar.ayar(onbellek_siniri=True))
    kapali = OllamaIstemcisi(cagrilar.ayar(onbellek_siniri=False))
    kayit = {"baslangic": time.strftime("%Y-%m-%d %H:%M:%S %z"), "istemler": istem_ozeti(), "kosular": {}}
    for ad, istemci, araya in (("kosu1", acik, False), ("kosu2", acik, False), ("kosu3", kapali, True)):
        sonuclar = []
        for i, istek in enumerate(hedef):
            ara = None
            if araya:   # her hedef istekten önce farklı bir istek (dolgu i), aynı istemciyle
                d = _kos(veri, dolgu[i], varsayilan, istemci)
                ara = {"id": dolgu[i]["id"], **hamlar(d)}
            h = _kos(veri, istek, varsayilan, istemci)
            sonuclar.append({"id": istek["id"], "araya_giren": ara, **hamlar(h), "sure_sn": h.sure_sn})
            print(ad, istek["id"], h.sure_sn, flush=True)
        kayit["kosular"][ad] = sonuclar
    kayit["bitis"] = time.strftime("%Y-%m-%d %H:%M:%S %z")
    k1, k2, k3 = (kayit["kosular"][k] for k in ("kosu1", "kosu2", "kosu3"))

    def say(c1, c2, alan):
        cift = [(a[alan], b[alan]) for a, b in zip(c1, c2) if a[alan] is not None or b[alan] is not None]
        return sum(x == y for x, y in cift), len(cift)

    ozet = {f"{alan}_{ad}": say(k1, k, alan) for alan in ("a", "b") for ad, k in (("k1_k2_ayni", k2), ("k1_k3_ayni", k3))}
    kayit["ozet"] = ozet
    tarih = time.strftime("%Y-%m-%d")
    (OLCUM / f"{tarih}_onbellek.json").write_text(json.dumps(kayit, ensure_ascii=False, indent=1), encoding="utf-8")
    satir = []
    for (a, b, c) in zip(k1, k2, k3):
        satir.append(f"| {a['id']} | {len(a['a'])} | {'=' if a['a'] == b['a'] else '≠'} | {'=' if a['a'] == c['a'] else '≠'} | "
                     f"{len(a['b']) if a['b'] else '-'} | {'-' if a['b'] is None and b['b'] is None else '=' if a['b'] == b['b'] else '≠'} | "
                     f"{'-' if a['b'] is None and c['b'] is None else '=' if a['b'] == c['b'] else '≠'} | {c['araya_giren']['id']} |")
    md = [f"# Önbellek sınırı ölçümü — {tarih}", "",
          f"Model {cagrilar.MODEL}, yalnız CPU, temperature 0, seed 42, num_ctx 8192, think kapalı; en_cok_tur {cagrilar.EN_COK_TUR}. "
          f"İstemler: {', '.join(f'{k} {v}' for k, v in kayit['istemler'].items())}. Ham veri: `{tarih}_onbellek.json`. "
          f"Koşu: {kayit['baslangic']} – {kayit['bitis']}.", "",
          "- Koşu 1: sınır açık, G01–G10 sırayla.", "- Koşu 2: sınır açık, aynı sıra.",
          "- Koşu 3: sınır kapalı; her hedef istekten hemen önce farklı bir istek (G11–G20'den biri) uçtan uca çalıştırıldı.",
          "- Karşılaştırma: bir çağrının bütün turlarının ham yanıt metinleri birebir aynıysa `=`.", "",
          "| Çağrı | Koşu 1 = Koşu 2 | Koşu 3'te Koşu 1'den farklı |", "|---|---|---|",
          f"| A (ihtiyaç) | {ozet['a_k1_k2_ayni'][0]}/{ozet['a_k1_k2_ayni'][1]} | {ozet['a_k1_k3_ayni'][1] - ozet['a_k1_k3_ayni'][0]}/{ozet['a_k1_k3_ayni'][1]} |",
          f"| B (atama) | {ozet['b_k1_k2_ayni'][0]}/{ozet['b_k1_k2_ayni'][1]} | {ozet['b_k1_k3_ayni'][1] - ozet['b_k1_k3_ayni'][0]}/{ozet['b_k1_k3_ayni'][1]} |",
          "", "B satırı: yalnız Çağrı B'nin en az bir koşuda çalıştığı istekler (A 'tamam' değilse B çalışmaz).", "",
          "| İstek | A tur (K1) | A K1=K2 | A K1=K3 | B tur (K1) | B K1=K2 | B K1=K3 | K3'te araya giren |",
          "|---|---|---|---|---|---|---|---|", *satir]
    yol = OLCUM / f"{tarih}_onbellek.md"
    yol.write_text("\n".join(md) + "\n", encoding="utf-8")
    return yol


# ------------------------------------------------------------------ geliştirme seti
def a_dogru_mu(h: hat.HatSonucu, beklenen: dict) -> bool:
    if h.cagri_a.durum is not Durum.GECTI or h.cagri_a.yanit["durum"] != beklenen["durum"]:
        return False
    bulunan = Counter(n["arayuz"] for n in cagrilar.genislet(h.cagri_a.yanit["ihtiyaclar"]))
    return any(bulunan == Counter(k) for k in [beklenen["ihtiyaclar"], *beklenen.get("alternatifler", [])])


def gelistirme(surum: str) -> Path:
    veri = pinveri.yukle()
    varsayilan, istekler = set_oku()
    istemci = OllamaIstemcisi(cagrilar.ayar(onbellek_siniri=True))
    satirlar = []
    for istek in istekler:
        h = hat.calistir(istek["metin"], istek["paket"], {**varsayilan, **istek["baglam"]}, veri, istemci,
                         model_ata=True, ek={"olcum": f"gelistirme_{surum}", "id": istek["id"]})
        b = h.cagri_b
        model_karar = (b.turlar[-1].json or {}).get("durum") if b else None
        atayici_karar = h.atayici["atama"]["durum"] if h.atayici else None
        satirlar.append({
            "id": istek["id"], "a_dogru": a_dogru_mu(h, istek["beklenen"]), "a_durumu": h.a_durumu,
            "a_tur": h.cagri_a.tur_sayisi,
            "a_ihtiyaclar": sorted(n["arayuz"] for n in cagrilar.genislet((h.cagri_a.yanit or {}).get("ihtiyaclar", []))),
            "a_model_cikarimi": sum(n["kaynak"] == "model_cikarimi" for n in (h.cagri_a.yanit or {}).get("ihtiyaclar", [])),
            "beklenen": istek["beklenen"],
            "b_sonuc": b.durum.value if b else None, "b_gecti_turu": b.gecti_turu if b else None,
            "b_tur": b.tur_sayisi if b else None, "model_karar": model_karar,
            "atayici_karar": atayici_karar, "atayici_neden": h.atayici["neden"] if h.atayici else None,
            "karar_ayni": (model_karar == atayici_karar) if b else None,
            "model_uyari": sum(i.seviye == "uyari" for i in h.ihlaller) if b else None,
            "model_hata": sum(i.seviye == "hata" for i in h.ihlaller) if b else None,
            "atayici_uyari": sum(i["seviye"] == "uyari" for i in h.atayici["uyarilar"]) if h.atayici else None,
            "sure_sn": h.sure_sn,
            "b_hata_kodlari": [[i.kod for i in t.ihlaller] for t in b.turlar] if b else None,
        })
        print(surum, istek["id"], satirlar[-1]["a_dogru"], satirlar[-1]["b_sonuc"], satirlar[-1]["b_gecti_turu"],
              h.sure_sn, flush=True)
    tarih = time.strftime("%Y-%m-%d")
    kayit = {"surum": surum, "istemler": istem_ozeti(), "zaman": time.strftime("%Y-%m-%d %H:%M:%S %z"), "satirlar": satirlar}
    (OLCUM / f"{tarih}_gelistirme_{surum}.json").write_text(json.dumps(kayit, ensure_ascii=False, indent=1), encoding="utf-8")

    b_olan = [s for s in satirlar if s["b_sonuc"]]
    turlar = Counter(s["b_gecti_turu"] if s["b_sonuc"] == "GECTI" else s["b_sonuc"] for s in b_olan)
    sureler = [s["sure_sn"]["toplam"] for s in satirlar]
    md = [f"# Geliştirme seti koşusu {surum} — {tarih}", "",
          f"İstemler: {', '.join(f'{k} {v}' for k, v in kayit['istemler'].items())}. Sınır açık, en_cok_tur {cagrilar.EN_COK_TUR}. "
          f"Ham veri: `{tarih}_gelistirme_{surum}.json`; izler `doc/olcum/iz/`.", "",
          f"- Çağrı A doğru: {sum(s['a_dogru'] for s in satirlar)}/{len(satirlar)}",
          f"- Çağrı B çalışan: {len(b_olan)}; sonuç: " + ", ".join(f"{k if isinstance(k, str) else f'{k}. turda geçti'}: {v}" for k, v in sorted(turlar.items(), key=str)),
          f"- Model–atayıcı mümkün/imkânsız kararı aynı: {sum(bool(s['karar_ayni']) for s in b_olan)}/{len(b_olan)}",
          f"- Süre (sn): ortalama {statistics.mean(sureler):.1f}, en uzun {max(sureler):.1f}", "",
          "| İstek | A doğru | A durumu | A ihtiyaçlar | B sonucu | B tur | model kararı | atayıcı kararı | aynı | uyarı (model/atayıcı) | süre sn |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in satirlar:
        md.append(f"| {s['id']} | {'✓' if s['a_dogru'] else '✗'} | {s['a_durumu']} | {' '.join(s['a_ihtiyaclar']) or '-'} | "
                  f"{s['b_sonuc'] or '-'} | {s['b_gecti_turu'] or s['b_tur'] or '-'} | {s['model_karar'] or '-'} | "
                  f"{s['atayici_karar'] or '-'} | {'-' if s['karar_ayni'] is None else '✓' if s['karar_ayni'] else '✗'} | "
                  f"{'-' if s['model_uyari'] is None else s['model_uyari']}/{'-' if s['atayici_uyari'] is None else s['atayici_uyari']} | "
                  f"{s['sure_sn']['toplam']} |")
    yol = OLCUM / f"{tarih}_gelistirme_{surum}.md"
    yol.write_text("\n".join(md) + "\n", encoding="utf-8")
    return yol


def main() -> None:
    ap = argparse.ArgumentParser()
    alt = ap.add_subparsers(dest="komut", required=True)
    alt.add_parser("onbellek")
    g = alt.add_parser("gelistirme")
    g.add_argument("--surum", required=True)
    a = ap.parse_args()
    print(onbellek() if a.komut == "onbellek" else gelistirme(a.surum))


if __name__ == "__main__":
    main()

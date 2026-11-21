"""Adım 11: v5 biçimli set (kart, soru, bağlam bayrakları) ile tam hat ölçümü. Ham sayılar; uyarı ve mesaj beklentileri
elle puanlanır (setin `beklenen` metni).

Kullanım:
    python -m pinsecim.tamolcum kos --set YOL --sha HEX --ham YOL
    python -m pinsecim.tamolcum rapor --set YOL --sha HEX --ham YOL --sonuc YOL --dondurma YOL --tarih T

kos: her istek bir kez, varsayılan akışla (Çağrı A → cevaplayıcı → kod atayıcı → denetim); `--kart` verilmişse paket
karttan, atama kart düzeyinde. Setin `tekrar` listesindeki istekler ikinci kez aynı akışla koşulur (kosu "tekrar").
Kayıtta komut satırı metni, soru cevapları ve durum bildirimi de var.

Çağrı A doğru: kabul seçeneklerinden biriyle durum, ihtiyaç çoklu kümesi, pin tercihleri ve kullanılmayacak pinler
aynı (dogrulama.a_eslesen) ve o seçeneğin `sorular` listesiyle soru sayısı ve konular eşleşiyor (seçenekte alan yoksa
soru beklenmez); `eksik_icerir` kodları eksik içinde. Karar: atayıcının durumu; A pin ihtiyacı göndermediyse
pin_gerekmiyor, A tamam değilse atama_yok.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import time
import traceback
from collections import Counter
from pathlib import Path

from asu_llmcore import IzYazici, OllamaIstemcisi

from . import cagrilar, hat, kart as kart_mod, pinveri
from . import sozluk as sozluk_mod
from .__main__ import yazdir
from .dogrulama import KOK, _istatistik, _sha, a_eslesen, hat_kaydi, verilen_metni


def set_oku(yol: Path, sha: str) -> dict:
    if _sha(yol) != sha:
        raise SystemExit(f"{yol.name} SHA-256 tutmuyor: {_sha(yol)}")
    return json.loads(yol.read_text(encoding="utf-8"))


def _calistir(i: dict, varsayilan: dict, veri, istemci, sozluk, kartlar) -> tuple[hat.HatSonucu, str]:
    kart = kartlar.bul(i["kart"]) if i.get("kart") else None
    paket = kart["paket"] if kart else i["paket"]
    h = hat.calistir(i["metin"], paket, {**varsayilan, **i["baglam"]}, veri, istemci, iz=None, sozluk=sozluk,
                     kart=kart, kartlar=kartlar if kart else None)
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        yazdir(h, veri)
    return h, tampon.getvalue()


def kos(set_yolu: Path, sha: str, ham: Path, uzerine: bool = False, istemci=None) -> Path:
    if ham.exists() and not uzerine:
        raise SystemExit(f"{ham} var; üzerine yazmak için --uzerine")
    ham.unlink(missing_ok=True)
    d = set_oku(set_yolu, sha)
    veri, sozluk, kartlar = pinveri.yukle(), sozluk_mod.yukle(), kart_mod.yukle()
    ayar = cagrilar.ayar(onbellek_siniri=True)
    istemci = istemci or OllamaIstemcisi(ayar)
    iz = IzYazici(ham)
    ortak = {"set": set_yolu.name, "set_sha": _sha(set_yolu),
             "istemler": {p.name: _sha(p)[:12] for p in sorted(cagrilar.ISTEMLER.glob("*.txt"))}}
    bilgi = {i["id"]: i for i in d["istekler"]}
    for kosu, ids in (("a_atayici", [i["id"] for i in d["istekler"]]), ("tekrar", d.get("tekrar", []))):
        for k in ids:
            i = bilgi[k]
            try:
                h, cli = _calistir(i, d["varsayilan_baglam"], veri, istemci, sozluk, kartlar)
                iz.yaz({"kosu": kosu, "id": k, **ortak, "zaman": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        "kart": i.get("kart"), **hat_kaydi(h, ayar), "cevaplar": h.cevaplar, "bildirim": h.bildirim,
                        "pin_gerekmiyor": h.pin_gerekmiyor, "yazilim_hatasi": [x.kod for x in h.yazilim_hatasi],
                        "cli": cli})
                print(kosu, k, h.a_durumu, (h.atama or {}).get("durum", "-"), h.sure_sn, flush=True)
            except Exception:
                iz.yaz({"kosu": kosu, "id": k, **ortak, "hata": traceback.format_exc()})
                print(kosu, k, "HATA", flush=True)
    return ham


# ------------------------------------------------------------------ puanlama
def sorular_tutar(y: dict, sec: dict) -> bool:
    """Soru sayısı seçenektekiyle aynı ve her soru, kabul edilen konulardan birine bire bir eşlenebiliyor."""
    konular = [q["konu"] for q in y.get("sorular", [])]
    beklenen = sec.get("sorular") or []
    if len(konular) != len(beklenen):
        return False
    kalan = list(beklenen)
    for k in konular:                                   # küçük listeler: açgözlü eşleme yeterli
        j = next((n for n, izin in enumerate(kalan) if k in izin), None)
        if j is None:
            return False
        kalan.pop(j)
    return True


def a_dogru(r: dict, kabul: list[dict]) -> bool:
    y = r["cagri_a"].get("yanit")
    if y is None:
        return False
    for k, sec in enumerate(kabul):
        if a_eslesen(r["cagri_a"], [sec]) == 0 and sorular_tutar(y, sec) \
                and set(sec.get("eksik_icerir") or []) <= set(y.get("eksik", [])):
            return True
    return False


def karar(r: dict) -> str:
    if r["a_durumu"] != "tamam":
        return "atama_yok"
    if r.get("pin_gerekmiyor") or r.get("gosterilen_atama") is None:
        return "pin_gerekmiyor"
    return r["gosterilen_atama"]["durum"]


def karar_dogru(r: dict, beklenen) -> bool:
    return karar(r) in (beklenen if isinstance(beklenen, list) else [beklenen])


def ham_oku(ham: Path) -> dict[str, dict[str, tuple[int, dict]]]:
    kayit: dict[str, dict[str, tuple[int, dict]]] = {"a_atayici": {}, "tekrar": {}}
    for no, satir in enumerate(ham.read_text(encoding="utf-8").splitlines(), 1):
        r = json.loads(satir)
        kayit[r["kosu"]].setdefault(r["id"], (no, r))
    return kayit


def rapor(set_yolu: Path, sha: str, ham: Path, sonuc: Path, dondurma: Path, tarih: str) -> Path:
    d = set_oku(set_yolu, sha)
    kayit = ham_oku(ham)
    k1 = kayit["a_atayici"]

    def yer(kosu, i):
        return f"`{ham.name}:{kayit[kosu][i][0]}`"

    satirlar, sureler, kat = [], [], Counter()
    kat_dogru, kat_karar = Counter(), Counter()
    for i in d["istekler"]:
        no, r = k1[i["id"]]
        if "hata" in r:
            satirlar.append(f"| {i['id']} | {i['kategori']} | HATA | - | - | - | - | {yer('a_atayici', i['id'])} |")
            continue
        ad, kd = a_dogru(r, i["kabul"]), karar_dogru(r, i["beklenen_sonuc"])
        kat[i["kategori"]] += 1
        kat_dogru[i["kategori"]] += ad
        kat_karar[i["kategori"]] += kd
        sureler.append(r["sure_sn"]["toplam"])
        y = r["cagri_a"].get("yanit") or {}
        sor = ", ".join(q["konu"] for q in y.get("sorular", [])) or "-"
        bek = i["beklenen_sonuc"]
        satirlar.append(f"| {i['id']} | {i['kategori']} | {r['cagri_a']['tur_sayisi']} | {verilen_metni(r['cagri_a'])} "
                        f"| {sor} | {'✓' if ad else '✗'} | {karar(r)} ({'/'.join(bek) if isinstance(bek, list) else bek})"
                        f" {'✓' if kd else '✗'} | {yer('a_atayici', i['id'])} |")
    tum = sum(kat.values())
    md = [f"# v5 ölçümü (tam hat: soru, kart, atama) — {tarih}", "",
          f"Set `{set_yolu.relative_to(KOK) if set_yolu.is_relative_to(KOK) else set_yolu}` (SHA-256 `{sha}`), {len(d['istekler'])} istek. Model gemma4:12b-it-qat, "
          "CPU, temperature 0, seed 42, num_ctx 8192, think kapalı, sınır açık, en_cok_tur 3. Atamayı kod atayıcı yapar "
          "(K-6). İstemler: " + ", ".join(f"{k} {v}" for k, v in next(iter(k1.values()))[1]["istemler"].items())
          + f". Ham iz: `{ham.name}`. Dondurma: `{dondurma.name}`.", "",
          "Otomatik sütunlar setin yapılı `kabul` ve `beklenen_sonuc` alanlarıyla hesaplandı (tanım modül "
          "belgesinde). Uyarı ve mesaj beklentileri `beklenen` metnine göre elle puanlanır (Adım 11 raporu).", "",
          "## Özet", "", "| Ölçüt | Değer |", "|---|---|",
          f"| Çağrı A doğru (otomatik) | {sum(kat_dogru.values())}/{tum} |",
          f"| Karar beklenenle aynı | {sum(kat_karar.values())}/{tum} |",
          f"| Süre toplam (sn): ortalama / ortanca / en uzun | {_istatistik(sureler)} |",
          "", "| Kategori | İstek | A doğru | Karar doğru |", "|---|---|---|---|",
          *(f"| {k} | {kat[k]} | {kat_dogru[k]}/{kat[k]} | {kat_karar[k]}/{kat[k]} |" for k in kat), "",
          "## İstekler", "", "| İstek | Kategori | A tur | Verilen | Soru konuları | A doğru | Karar (beklenen) | İz |",
          "|---|---|---|---|---|---|---|---|", *satirlar, "", "## Tekrar", ""]
    for i in d.get("tekrar", []):
        if i not in kayit["tekrar"]:
            md.append(f"- {i}: tekrar kaydı yok")
            continue
        a, b = k1[i][1], kayit["tekrar"][i][1]
        ham_ayni = [x["ham"] for x in a["cagri_a"]["turlar"]] == [x["ham"] for x in b["cagri_a"]["turlar"]]
        cli_ayni = a["cli"].rsplit("\nSüre:", 1)[0] == b["cli"].rsplit("\nSüre:", 1)[0]
        md.append(f"- {i}: Çağrı A ham yanıtları {'aynı' if ham_ayni else 'FARKLI'}; komut satırı çıktısı (süre satırı "
                  f"dışında) {'aynı' if cli_ayni else 'FARKLI'} ({yer('a_atayici', i)}, {yer('tekrar', i)})")
    md += ["", "## Komut satırı çıktıları", ""]
    for i in d["istekler"]:
        r = k1[i["id"]][1]
        md += [f"### {i['id']} `{i['bayraklar']}`", "", f"Beklenen: {i['beklenen']}", "", "```",
               (r.get("cli") or r.get("hata", "")).rstrip("\n"), "```", ""]
    sonuc.write_text("\n".join(md), encoding="utf-8")
    return sonuc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m pinsecim.tamolcum")
    alt = ap.add_subparsers(dest="komut", required=True)
    k = alt.add_parser("kos")
    r = alt.add_parser("rapor")
    for p in (k, r):
        p.add_argument("--set", type=Path, required=True)
        p.add_argument("--sha", required=True)
        p.add_argument("--ham", type=Path, required=True)
    k.add_argument("--uzerine", action="store_true")
    r.add_argument("--sonuc", type=Path, required=True)
    r.add_argument("--dondurma", type=Path, required=True)
    r.add_argument("--tarih", required=True)
    a = ap.parse_args(argv)
    if a.komut == "kos":
        print(kos(a.set, a.sha, a.ham, a.uzerine))
    else:
        print(rapor(a.set.resolve(), a.sha, a.ham, a.sonuc, a.dondurma, a.tarih))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

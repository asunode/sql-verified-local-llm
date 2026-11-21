"""Adım 11: KAPSANMAYAN_CUMLE kuralını ölçüm izlerine modelsiz uygular (yanlış alarm oranı için). Her isteğin ilk
a_atayici kaydında Çağrı A'nın son turunun yanıtı denetlenir; uyarı alan cümleler listelenir. Adım 11a: izde kayıtlı
DESTEKLENMEYEN_OZELLIK hataları da (bütün turlar) listelenir. Adım 12: SPI_ADET_IZI da son yanıta modelsiz uygulanır.

    python -m pinsecim.kapsam HAM.jsonl [HAM.jsonl ...] [--cikti YOL]
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from . import cagrilar, semalar, sozluk as sozluk_mod


def uygula(ham: Path, sozluk) -> list[dict]:
    sonuc, gorulen = [], set()
    for satir_no, satir in enumerate(ham.read_text(encoding="utf-8").splitlines(), 1):
        r = json.loads(satir)
        if r.get("kosu", "a_atayici") != "a_atayici" or r.get("id") in gorulen:
            continue
        gorulen.add(r.get("id"))
        turlar = r["cagri_a"].get("turlar") or []
        y = turlar[-1].get("json") if turlar else None
        cumle = len(list(cagrilar.CUMLE.finditer(r["metin"])))
        kayit = {"id": r.get("id", str(satir_no)), "satir": satir_no, "metin": r["metin"], "cumle": cumle,
                 "uyarilar": [], "spi": [], "yanit_yok": y is None, "a_durumu": r.get("a_durumu"),
                 "desteklenmeyen": [(t["no"], i["mesaj"].split("'")[1]) for t in turlar for i in t.get("ihlaller", [])
                                    if i["kod"] == "DESTEKLENMEYEN_OZELLIK"]}
        if y is not None:
            d = cagrilar.ihtiyac_denetleyici(r["metin"], list(semalar.ARAYUZLER), sozluk)
            ihl = d(copy.deepcopy(y))
            kayit["uyarilar"] = [i.mesaj for i in ihl if i.kod == "KAPSANMAYAN_CUMLE"]
            kayit["spi"] = [i.mesaj for i in ihl if i.kod == "SPI_ADET_IZI"]
            kayit["spi_adet"] = [(n["dayanak"], n["adet"]) for n in y["ihtiyaclar"] if n["arayuz"] == "SPI"]
            kayit["durum"] = y.get("durum")
        sonuc.append(kayit)
    return sonuc


def metin(hamlar: list[Path], sozluk) -> str:
    md = ["# KAPSANMAYAN_CUMLE ve SPI_ADET_IZI: ölçüm izlerine modelsiz uygulama", "",
          "Her isteğin Çağrı A son tur yanıtı (ilk a_atayici kaydı) yeni kuralla denetlendi. Uyarı tur açmaz, kararı "
          "değiştirmez.", ""]
    for ham in hamlar:
        k = uygula(ham, sozluk)
        uyarili = [x for x in k if x["uyarilar"]]
        md += [f"## `{ham.name}`", "",
               f"İstek {len(k)}, cümle {sum(x['cumle'] for x in k)}; uyarı alan istek {len(uyarili)}, cümle "
               f"{sum(len(x['uyarilar']) for x in k)}." + (f" Yanıtı olmayan istek: {sum(x['yanit_yok'] for x in k)}."
                                                          if any(x["yanit_yok"] for x in k) else ""), ""]
        if uyarili:
            md += ["| İstek | Durum | Uyarı alan cümle | İz |", "|---|---|---|---|"]
            for x in uyarili:
                for u in x["uyarilar"]:
                    md.append(f"| {x['id']} | {x.get('durum')} | {u.split('» hiçbir')[0]}» | `{ham.name}:{x['satir']}` |")
            md.append("")
        ds = [x for x in k if x["desteklenmeyen"]]
        md += [f"DESTEKLENMEYEN_OZELLIK (izde kayıtlı, bütün turlar): {len(ds)} istek.", ""]
        if ds:
            md += ["| İstek | Tur: ad | Son durum | İz |", "|---|---|---|---|",
                   *(f"| {x['id']} | {', '.join(f'{t}: {a}' for t, a in x['desteklenmeyen'])} | "
                     f"{x['a_durumu']} / {x.get('durum')} | `{ham.name}:{x['satir']}` |" for x in ds), ""]
        spi = [x for x in k if x["spi_adet"]]
        md += [f"SPI_ADET_IZI (son yanıt): SPI ihtiyacı olan istek {len(spi)}, uyarı alan "
               f"{sum(bool(x['spi']) for x in k)}.", ""]
        if spi:
            md += ["| İstek | SPI ihtiyaçları (dayanak ×adet) | Uyarı | İz |", "|---|---|---|---|",
                   *(f"| {x['id']} | {'; '.join(f'«{d}» ×{n}' for d, n in x['spi_adet'])} | "
                     f"{' / '.join(x['spi']) or '-'} | `{ham.name}:{x['satir']}` |" for x in spi), ""]
    return "\n".join(md)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m pinsecim.kapsam")
    ap.add_argument("hamlar", nargs="+", type=Path)
    ap.add_argument("--cikti", type=Path)
    a = ap.parse_args(argv)
    md = metin(a.hamlar, sozluk_mod.yukle())
    if a.cikti:
        a.cikti.write_text(md + "\n", encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

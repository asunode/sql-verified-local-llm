"""A–B karşılaştırması ve A'nın kendi tabloları arasındaki çapraz denetimler.

A (1–3. bölüm tabloları) ve B (Consolidated Pin Overview) aynı pin için aynı alanları ayrı ayrı verir.
Her fark `Fark` olarak döner; kararlar `kararlar.py`'de, gerekçeleri doc/dogrulama/ fark raporunda.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

ALANLAR = ["pin_adi", "pin_turu", "guc", "reset_ayar", "reset_sonrasi_ayar",
           "analog_0", "analog_1", "lp_0", "lp_1",
           "iomux_0", "iomux_0_tip", "iomux_1", "iomux_1_tip", "iomux_2", "iomux_2_tip"]


@dataclass(frozen=True)
class Fark:
    tur: str            # "A-B" | "A-ic"
    paket: str
    pin_no: int | None
    alan: str
    a: str
    b: str
    kaynak_a: str
    kaynak_b: str

    @property
    def anahtar(self) -> str:
        return f"{self.tur}|{self.paket}|{self.pin_no}|{self.alan}"


def a_gorunumu(a: dict) -> dict[str, dict[int, dict]]:
    """A'nın tablolarını B ile aynı biçimde pin satırlarına toplar (paket → pin no → alanlar)."""
    lp = {r["pin_no"]: r for r in a["lp_iomux"]}
    sonuc: dict[str, dict[int, dict]] = {}
    for paket, satirlar in a["pin_overview"].items():
        iomux = {r["pin_no"]: r for r in a["iomux"][paket]}
        analog = {r["pin_no"][paket]: r for r in a["analog"] if r["pin_no"][paket] is not None}
        pinler = {}
        for s in satirlar:
            no = s["pin_no"]
            g = {k: s[k] for k in ("pin_adi", "pin_turu", "guc", "reset_ayar", "reset_sonrasi_ayar")}
            g.update({f: "" for f in ALANLAR if f not in g})
            kalin, renkler, kaynaklar = set(), set(), [f"{s['referans']} s.{s['sayfa']}"]
            if no in iomux:
                r = iomux[no]
                kaynaklar.append(f"{r['referans']} s.{r['sayfa']}")
                renkler.add(r["gpio_renk"])
                for f in r["islevler"]:
                    g[f"iomux_{f['no']}"], g[f"iomux_{f['no']}_tip"] = f["ad"], f["tip"]
                    renkler.add(f["renk"])
                    if f["kalin"]:
                        kalin.add(f"iomux_{f['no']}")
            if no in lp:
                r = lp[no]
                kaynaklar.append(f"{r['referans']} s.{r['sayfa']}")
                renkler.add(r["lp_renk"])
                for f in r["islevler"]:
                    g[f"lp_{f['no']}"] = f["ad"]
                    renkler.add(f["renk"])
                    if f["kalin"]:
                        kalin.add(f"lp_{f['no']}")
            if no in analog:
                r = analog[no]
                kaynaklar.append(f"{r['referans']} s.{r['sayfa']}")
                renkler.add(r["gpio_renk"])
                for f in r["islevler"]:
                    g[f"analog_{f['no']}"] = f["ad"]
                    renkler.add(f["renk"])
                    if f["kalin"]:
                        kalin.add(f"analog_{f['no']}")
            renkler.discard(None)
            g["kalin"] = sorted(kalin)
            g["renk"] = ",".join(sorted(renkler)) or ""
            g["gpio_no"] = iomux[no]["gpio_no"] if no in iomux else None
            g["kaynak"] = "; ".join(dict.fromkeys(kaynaklar))
            pinler[no] = g
        sonuc[paket] = pinler
    return sonuc


def b_gorunumu(b: dict) -> dict[str, dict[int, dict]]:
    sonuc = {}
    for paket, satirlar in b.items():
        pinler = {}
        for s in satirlar:
            g = {f: s[f] for f in ALANLAR}
            g["kalin"] = sorted(f for f, v in s["kalin"].items() if v and f in ALANLAR and f.split("_")[0] in ("iomux", "lp", "analog") and not f.endswith("_tip"))
            g["renk"] = s["satir_renk"] or ""
            m = re.fullmatch(r"GPIO(\d+)", s["iomux_1"])
            g["gpio_no"] = int(m[1]) if m else None
            g["kaynak"] = f"{s['referans']} s.{s['sayfa']}"
            pinler[s["pin_no"]] = g
        sonuc[paket] = pinler
    return sonuc


def a_b_farklari(a: dict, b: dict) -> list[Fark]:
    ga, gb = a_gorunumu(a), b_gorunumu(b)
    farklar = []
    for paket in sorted(set(ga) | set(gb)):
        pa, pb = ga.get(paket, {}), gb.get(paket, {})
        for no in sorted(set(pa) | set(pb)):
            ra, rb = pa.get(no), pb.get(no)
            if ra is None or rb is None:
                farklar.append(Fark("A-B", paket, no, "satir", "var" if ra else "yok", "var" if rb else "yok",
                                    ra["kaynak"] if ra else "", rb["kaynak"] if rb else ""))
                continue
            for alan in ALANLAR + ["gpio_no", "kalin", "renk"]:
                va, vb = ra[alan], rb[alan]
                if alan == "kalin":
                    va, vb = ",".join(va), ",".join(vb)
                if str(va if va is not None else "") != str(vb if vb is not None else ""):
                    farklar.append(Fark("A-B", paket, no, alan, str(va), str(vb), ra["kaynak"], rb["kaynak"]))
    return farklar


def a_ic_farklari(a: dict) -> list[Fark]:
    """A'nın kendi tabloları arasındaki çapraz denetimler."""
    farklar = []
    # 1. Pin düzeni şekli (s. 14–15) ↔ pin overview (Table 2-1/2-2)
    for paket, satirlar in a["pin_overview"].items():
        sekil = a["pin_duzeni"][paket]
        tablo = {s["pin_no"]: s["pin_adi"] for s in satirlar}
        for no in sorted(set(sekil) | set(tablo)):
            if sekil.get(no) != tablo.get(no):
                farklar.append(Fark("A-ic", paket, no, "pin_duzeni", str(tablo.get(no)), str(sekil.get(no)),
                                    satirlar[0]["referans"], f"Figure 2-{1 if paket == 'QFN40' else 2}"))
    # 2. Çevre birimi tablosu (2-10/2-11): GPIO matrisi hücresindeki GPIO, pinin GPIO'su olmalı;
    #    P1 sabit sinyali pinin IO MUX / LP IO MUX / analog işlevlerinden biri olmalı;
    #    P2–P4 önceliği 2.3.5 metnindeki listelerle uyuşmalı.
    ga = a_gorunumu(a)
    liste = {}
    for r in a["oncelik_listeleri"]:
        liste[r["gpio_no"]] = max(liste.get(r["gpio_no"], "P2"), r["oncelik"])
    for paket, hucreler in a["cevre_birim"].items():
        for h in hucreler:
            pin = ga[paket][h["pin_no"]]
            islevler = {pin[f] for f in ALANLAR if f.split("_")[0] in ("iomux", "lp", "analog") and not f.endswith("_tip")} - {""}
            m = re.fullmatch(r"GPIO(\d+)", h["deger"])
            yer = f"{h['referans']} s.{h['sayfa']} {h['cevre_birim']}"
            if h["oncelik"] is None:
                farklar.append(Fark("A-ic", paket, h["pin_no"], f"cevre:{h['cevre_birim']}:bicim", h["hucre"], "",
                                    yer, "beklenen biçim 'DEĞER (Pn)'"))
            elif m:
                if int(m[1]) != pin["gpio_no"]:
                    farklar.append(Fark("A-ic", paket, h["pin_no"], f"cevre:{h['cevre_birim']}:gpio", h["deger"],
                                        f"GPIO{pin['gpio_no']}", yer, pin["kaynak"]))
                beklenen = liste.get(int(m[1]), "P2")
                if h["oncelik"] != beklenen:
                    farklar.append(Fark("A-ic", paket, h["pin_no"], f"cevre:{h['cevre_birim']}:oncelik",
                                        h["oncelik"], beklenen, yer, "2.3.5 s.25"))
            elif h["oncelik"] == "P1" and h["deger"] not in islevler:
                farklar.append(Fark("A-ic", paket, h["pin_no"], f"cevre:{h['cevre_birim']}:sabit", h["deger"],
                                    ",".join(sorted(islevler)), yer, pin["kaynak"]))
    return farklar


def renk_metin_farklari(a: dict) -> list[Fark]:
    """Renkli vurgu (kırmızı/sarı, Table 2-4/2-5/2-7/2-9) ile metin kısıtları (2.3.5 listeleri, Table 3-1) uyuşuyor mu.

    Renkli olup metinde geçmeyen GPIO "renkten gelen" bilgidir; metinde olup hiçbir yerde renkli olmayan da raporlanır.
    """
    f0 = {f["ad"]: r["gpio_no"] for r in a["iomux"]["QFN40"] for f in r["islevler"] if f["no"] == 0}
    metin = {r["gpio_no"] for r in a["oncelik_listeleri"]}
    metin |= {int(r["pin_adi"][4:]) if r["pin_adi"].startswith("GPIO") else f0[r["pin_adi"]] for r in a["strapping"]}
    renkli: dict[int, set[str]] = {}
    for paket, satirlar in a["iomux"].items():
        for r in satirlar:
            hucreler = [r["gpio_renk"]] + [f["renk"] for f in r["islevler"]]
            if any(hucreler):
                renkli.setdefault(r["gpio_no"], set()).add(f"{r['referans']} s.{r['sayfa']}")
    gpio40 = {r["pin_no"]: r["gpio_no"] for r in a["iomux"]["QFN40"]}
    for r in a["lp_iomux"]:
        if r["lp_renk"] or any(f["renk"] for f in r["islevler"]):
            renkli.setdefault(gpio40[r["pin_no"]], set()).add(f"{r['referans']} s.{r['sayfa']}")
    for r in a["analog"]:
        if r["gpio_renk"] or any(f["renk"] for f in r["islevler"]):
            renkli.setdefault(r["gpio_no"], set()).add(f"{r['referans']} s.{r['sayfa']}")
    farklar = []
    for g in sorted(set(renkli) - metin):
        farklar.append(Fark("renk-metin", "*", None, f"GPIO{g}", "renkli", "metinde yok",
                            ", ".join(sorted(renkli[g])), "2.3.5 s.25; Table 3-1 s.33"))
    for g in sorted(metin - set(renkli)):
        farklar.append(Fark("renk-metin", "*", None, f"GPIO{g}", "renksiz", "metinde var",
                            "Table 2-4/2-5/2-7/2-9", "2.3.5 s.25; Table 3-1 s.33"))
    return farklar

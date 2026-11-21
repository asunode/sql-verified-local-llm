"""Çıkarma A: datasheet'in 1–3. bölümlerindeki pin tabloları (çizgili tablo hücreleriyle).

Her kayıt kaynağını (`sayfa`, `referans`) taşır. Değerler datasheet'te yazdığı gibidir; yorum yapılmaz.
Hücre renkleri (`renk`) ve kalınlık (`kalin`) ayrıca saklanır; anlamları 2.3.4 (s. 24) ve tablo dipnotlarındadır.
"""

from __future__ import annotations

import re
from pathlib import Path

from .pdfoku import Hucre, sayfa_metni, tablolar

GPIO = re.compile(r"^GPIO(\d+)$")
HUCRE_ONCELIK = re.compile(r"^(?P<deger>\S+) \((?P<oncelik>P[1-4])\)$")


def _bas(hucre: Hucre) -> str:
    """Başlık hücresi: sonda kalan dipnot rakamlarını at (ör. "UART0 2" → "UART0")."""
    return re.sub(r"(\s+\d+(,\s*\d+)*)+$", "", hucre.metin).strip()


def _veri_satirlari(izgara: list[list[Hucre]]) -> list[list[Hucre]]:
    """Başlık satırlarını atla: ilk hücresi pin numarası (ya da tabloya özgü veri) olan satırlar."""
    return [s for s in izgara if s and re.fullmatch(r"\d+", s[0].metin)]


def _renk(h: Hucre) -> str | None:
    return h.renk


def cipler(pdf: Path) -> list[dict]:
    """Table 1-1 (s. 13)."""
    izgara = tablolar(pdf, 13)[0]
    sonuc = []
    for s in izgara[1:]:
        paket = re.match(r"^(QFN\d+) \((.+)\)$", s[3].metin)
        sonuc.append({"ad": s[0].metin, "gomulu_flash": s[1].metin, "dipnot_flash": s[1].ust_simge,
                      "sicaklik": s[2].metin, "paket": paket[1], "paket_boyut": paket[2],
                      "revizyon": s[4].metin, "sayfa": 13, "referans": "Table 1-1"})
    return sonuc


def pin_duzeni(pdf: Path) -> dict[str, dict[int, str]]:
    """Figure 2-1 (s. 14) ve Figure 2-2 (s. 15): pin no → pin adı (şekildeki etiketler)."""
    sonuc = {}
    for sayfa, paket in ((14, "QFN40"), (15, "QFN32")):
        metin = sayfa_metni(pdf, sayfa)
        # Çip adı etiketi pin değildir; yanındaki boşlukla bir pin numarasına eşlenmesin.
        govde = metin.split("Figure 2-", 1)[0].split("\n", 1)[1].replace("ESP32-C6", " " * 8)
        ciftler = {}
        for m in re.finditer(r"(?<![\w-])(\d{1,2}) ([A-Z][A-Z0-9_+\-]*)(?![\w])|([A-Z][A-Z0-9_+\-]*) +(\d{1,2})(?![\w])", govde):
            no, ad = (m[1], m[2]) if m[1] else (m[4], m[3])
            ciftler[int(no)] = ad
        # Köşedeki döndürülmüş etiket: numara bir satırda, ad (boş satırlardan sonra) altında tek başına.
        for m in re.finditer(r"^ +(\d{1,2}) *\n(?: *\n)* +([A-Z][A-Z0-9_+\-]*) *$", govde, re.M):
            ciftler.setdefault(int(m[1]), m[2])
        sonuc[paket] = ciftler
    return sonuc


PIN_OVERVIEW = {"QFN40": ((16, 17), "Table 2-1"), "QFN32": ((17, 18), "Table 2-2")}


def pin_overview(pdf: Path) -> dict[str, list[dict]]:
    """Table 2-1 (s. 16–17) ve Table 2-2 (s. 17–18)."""
    sonuc = {}
    for paket, (sayfalar, ref) in PIN_OVERVIEW.items():
        satirlar = []
        for sayfa in sayfalar:
            for izgara in tablolar(pdf, sayfa):
                # s. 17'de iki tablo var: Table 2-1'in sonu (pin 18–41) ve Table 2-2'nin başı (pin 1–15).
                veri = _veri_satirlari(izgara)
                if not veri:
                    continue
                ilk = int(veri[0][0].metin)
                bu_tablo = (paket == "QFN40" and (sayfa == 16 or ilk > 15)) or \
                           (paket == "QFN32" and (sayfa == 18 or (sayfa == 17 and ilk == 1)))
                if not bu_tablo:
                    continue
                for s in veri:
                    kumeler = {"IO MUX": s[6], "LP IO MUX": s[7], "Analog": s[8]}
                    satirlar.append({
                        "paket": paket, "pin_no": int(s[0].metin), "pin_adi": s[1].metin, "pin_turu": s[2].metin,
                        "guc": s[3].metin, "reset_ayar": s[4].metin, "reset_sonrasi_ayar": s[5].metin,
                        "dipnot": ",".join(x for x in (s[4].ust_simge, s[5].ust_simge) if x),
                        "islev_kumeleri": [k for k, h in kumeler.items() if h.metin],
                        "varsayilan_kume": [k for k, h in kumeler.items() if h.metin and h.kalin],
                        "sayfa": sayfa, "referans": ref,
                    })
        sonuc[paket] = satirlar
    return sonuc


IOMUX = {"QFN40": (20, "Table 2-4"), "QFN32": (21, "Table 2-5")}


def iomux(pdf: Path) -> dict[str, list[dict]]:
    """Table 2-4 (s. 20), Table 2-5 (s. 21): IO MUX işlevleri F0–F2."""
    sonuc = {}
    for paket, (sayfa, ref) in IOMUX.items():
        satirlar = []
        for s in _veri_satirlari(tablolar(pdf, sayfa)[0]):
            islevler = []
            for n in range(3):
                ad, tip = s[2 + 2 * n], s[3 + 2 * n]
                if ad.metin:
                    islevler.append({"no": n, "ad": ad.metin, "tip": tip.metin, "kalin": ad.kalin, "renk": _renk(ad)})
            satirlar.append({"paket": paket, "pin_no": int(s[0].metin), "gpio_adi": s[1].metin,
                             "gpio_no": int(GPIO.match(s[1].metin)[1]), "gpio_renk": _renk(s[1]),
                             "islevler": islevler, "sayfa": sayfa, "referans": ref})
        sonuc[paket] = satirlar
    return sonuc


def lp_iomux(pdf: Path) -> list[dict]:
    """Table 2-7 (s. 22). Pakete göre ayrılmaz; yalnız pin no verir."""
    izgara = [t for t in tablolar(pdf, 22) if _bas(t[0][0]) == "Pin"][0]
    sonuc = []
    for s in _veri_satirlari(izgara):
        sonuc.append({"pin_no": int(s[0].metin), "lp_adi": s[1].metin, "lp_renk": _renk(s[1]),
                      "islevler": [{"no": n, "ad": h.metin, "kalin": h.kalin, "renk": _renk(h)}
                                   for n, h in enumerate(s[2:4]) if h.metin],
                      "sayfa": 22, "referans": "Table 2-7"})
    return sonuc


def analog(pdf: Path) -> list[dict]:
    """Table 2-9 (s. 23): her iki paketin pin numarasıyla."""
    izgara = [t for t in tablolar(pdf, 23) if _bas(t[0][0]) == "QFN40"][0]
    sonuc = []
    for s in _veri_satirlari(izgara):
        sonuc.append({"pin_no": {"QFN40": int(s[0].metin), "QFN32": int(s[1].metin) if s[1].metin.isdigit() else None},
                      "qfn32_hucre": s[1].metin, "gpio_adi": s[2].metin, "gpio_no": int(GPIO.match(s[2].metin)[1]),
                      "gpio_renk": _renk(s[2]),
                      "islevler": [{"no": n, "ad": h.metin, "kalin": h.kalin, "renk": _renk(h)}
                                   for n, h in enumerate(s[3:5]) if h.metin],
                      "sayfa": 23, "referans": "Table 2-9"})
    return sonuc


CEVRE = {"QFN40": (26, "Table 2-10"), "QFN32": (27, "Table 2-11")}


def cevre_birim(pdf: Path) -> dict[str, list[dict]]:
    """Table 2-10 (s. 26), Table 2-11 (s. 27): pin × çevre birimi hücreleri, öncelik P1–P4."""
    sonuc = {}
    for paket, (sayfa, ref) in CEVRE.items():
        izgara = tablolar(pdf, sayfa)[0]
        basliklar = [_bas(h) for h in izgara[0]]
        hucreler = []
        for s in _veri_satirlari(izgara):
            for baslik, h in zip(basliklar[2:], s[2:]):
                if not h.metin:
                    continue
                m = HUCRE_ONCELIK.match(h.metin)
                hucreler.append({"paket": paket, "pin_no": int(s[0].metin), "pin_adi": s[1].metin,
                                 "cevre_birim": baslik, "hucre": h.metin,
                                 "deger": m["deger"] if m else h.metin, "oncelik": m["oncelik"] if m else None,
                                 "renk": _renk(h), "sayfa": sayfa, "referans": ref})
        sonuc[paket] = hucreler
    return sonuc


def flash(pdf: Path) -> list[dict]:
    """Table 2-16 (s. 32): yalnız QFN40."""
    izgara = tablolar(pdf, 32)[0]
    return [{"paket": "QFN40", "pin_no": int(s[0].metin), "pin_adi": s[1].metin, "tek_spi": s[2].metin,
             "cift_spi": s[3].metin, "dortlu_spi": s[4].metin, "sayfa": 32, "referans": "Table 2-16"}
            for s in _veri_satirlari(izgara)]


def strapping(pdf: Path) -> list[dict]:
    """Table 3-1 (s. 33): strapping pinlerinin varsayılan yapılandırması."""
    izgara = tablolar(pdf, 33)[0]
    return [{"pin_adi": s[0].metin, "varsayilan": s[1].metin, "bit": s[2].metin, "sayfa": 33,
             "referans": "Table 3-1"} for s in izgara[1:]]


def boot_modu(pdf: Path) -> list[dict]:
    """Table 3-3 (s. 34)."""
    izgara = [t for t in tablolar(pdf, 34) if _bas(t[0][0]) == "Boot Mode"][0]
    sonuc, gorulen = [], set()
    for s in izgara[1:]:
        anahtar = (s[0].metin, s[1].metin, s[2].metin)
        if anahtar in gorulen:      # pdfplumber birleşik hücreyi iki satır olarak verebiliyor
            continue
        gorulen.add(anahtar)
        sonuc.append({"mod": s[0].metin, "dipnot": s[0].ust_simge, "GPIO8": s[1].metin, "GPIO9": s[2].metin,
                      "varsayilan": s[0].kalin, "sayfa": 34, "referans": "Table 3-3"})
    return sonuc


def oncelik_listeleri(pdf: Path) -> list[dict]:
    """2.3.5 (s. 25) metnindeki P3/P4 GPIO listeleri: "* GPIO4, GPIO5, …: Strapping pins." biçimi."""
    metin = " ".join(sayfa_metni(pdf, 25).split())
    p3 = metin.split("Priority 3 (P3)", 1)[1].split("Priority 4 (P4)", 1)[0]
    p4 = metin.split("Priority 4 (P4)", 1)[1].split("If a peripheral interface does not have priority 2", 1)[0]
    sonuc = []
    for oncelik, govde in (("P3", p3), ("P4", p4)):
        for m in re.finditer(r"\* ((?:GPIO\d+, )*GPIO\d+) : (.+?)(?= \* |$)", govde):
            for g in re.findall(r"GPIO(\d+)", m[1]):
                sonuc.append({"gpio_no": int(g), "oncelik": oncelik, "aciklama": m[2].strip(), "sayfa": 25,
                              "referans": "2.3.5"})
    return sonuc


def hepsi(pdf: Path) -> dict:
    return {
        "cipler": cipler(pdf), "pin_duzeni": pin_duzeni(pdf), "pin_overview": pin_overview(pdf),
        "iomux": iomux(pdf), "lp_iomux": lp_iomux(pdf), "analog": analog(pdf), "cevre_birim": cevre_birim(pdf),
        "flash": flash(pdf), "strapping": strapping(pdf), "boot_modu": boot_modu(pdf),
        "oncelik_listeleri": oncelik_listeleri(pdf),
    }

"""PDF'ten düşük düzey okuma: sayfa metni, çizgili tablo hücreleri, kelimeler; renk ve kalınlık bilgisiyle.

Çıkarma A çizgili tabloları (`tablolar`), çıkarma B kelime konumlarını (`kelimeler`) kullanır; iki yol
birbirinden bağımsız algoritmalardır, ortak olan yalnız karakter okumasıdır.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pdfplumber

# Datasheet'teki vurgu dolguları (pdfplumber non_stroking_color, RGB). 2.3.4 s. 24: kırmızı = flash için
# ayrılmış, sarı = önemli işlev (strapping, USB, JTAG, UART0, VDD_SPI). Açık tonlar yatay sayfalarda (s. 26–27, 79–80).
RENKLER = {
    (0.898, 0.125, 0.102): "kirmizi",
    (0.98, 0.825, 0.82): "kirmizi",
    (0.831, 0.726, 0.0): "sari",
    (0.966, 0.945, 0.8): "sari",
}
KALIN_YAZI = "Medium"          # MaisonNeue-Medium: datasheet'te "bold"
# Dipnot işaretleri aynı boyutta ama satır tabanından ~3.8 pt yukarıda yazılmış rakamlar/virgüller.
UST_SIMGE_YUKSEKLIK = 2.5
UST_SIMGE_KARAKTER = set("0123456789,-–")
SATIR_TOLERANSI = 4.5


@dataclass(frozen=True)
class Hucre:
    metin: str
    renk: str | None = None      # "kirmizi" | "sari" | None
    kalin: bool = False
    ust_simge: str = ""          # ayıklanan dipnot işaretleri


@dataclass(frozen=True)
class Kelime:
    metin: str
    x0: float
    x1: float
    ust: float
    alt: float
    kalin: bool
    renk: str | None
    boyut: float


def sha256(yol: Path) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


@lru_cache(maxsize=4)
def _pdf(yol: str) -> pdfplumber.PDF:
    return pdfplumber.open(yol)


def sayfa_sayisi(yol: Path) -> int:
    return len(_pdf(str(yol)).pages)


def sayfa_metni(yol: Path, sayfa: int) -> str:
    """pdftotext -layout ile sayfanın düz metni (ham_metin tablosu için)."""
    return subprocess.run(["pdftotext", "-f", str(sayfa), "-l", str(sayfa), "-layout", str(yol), "-"],
                          capture_output=True, text=True, check=True).stdout


def _renk_adi(renk) -> str | None:
    if isinstance(renk, (tuple, list)) and len(renk) == 3:
        return RENKLER.get(tuple(round(float(c), 3) for c in renk))
    return None


def _dolgular(sayfa) -> list[tuple[tuple[float, float, float, float], str]]:
    sonuc = []
    for r in sayfa.rects:
        ad = _renk_adi(r.get("non_stroking_color")) if r.get("fill") else None
        if ad:
            sonuc.append(((r["x0"], r["top"], r["x1"], r["bottom"]), ad))
    return sonuc


def _renk(dolgular, x: float, y: float) -> str | None:
    for (x0, t, x1, b), ad in dolgular:
        if x0 - 0.5 <= x <= x1 + 0.5 and t - 0.5 <= y <= b + 0.5:
            return ad
    return None


def _satirlar(karakterler, tolerans: float = SATIR_TOLERANSI) -> list[list[dict]]:
    satirlar: list[list[dict]] = []
    for c in sorted(karakterler, key=lambda c: (c["top"], c["x0"])):
        if satirlar and abs(c["top"] - satirlar[-1][0]["top"]) <= tolerans:
            satirlar[-1].append(c)
        else:
            satirlar.append([c])
    return satirlar


def _ust_simge_ayir(karakterler) -> tuple[list[dict], list[dict]]:
    """(normal, üst simge): satır tabanından belirgin yukarıda duran rakam/virgül/tire üst simgedir."""
    normal, ust = [], []
    for satir in _satirlar(karakterler):
        taban = max(c["bottom"] for c in satir)
        for c in satir:
            yukarda = taban - c["bottom"] >= UST_SIMGE_YUKSEKLIK
            (ust if yukarda and c["text"] in UST_SIMGE_KARAKTER else normal).append(c)
    return normal, ust


def _birlestir(karakterler, bosluk: float = 1.2) -> str:
    """Karakterleri satır satır, aralarındaki boşluğa göre kelimelere ayırarak birleştirir."""
    parcalar = []
    for satir in _satirlar(karakterler):
        satir.sort(key=lambda c: c["x0"])
        metin, onceki = "", None
        for c in satir:
            if onceki is not None and c["x0"] - onceki["x1"] > bosluk:
                metin += " "
            metin += c["text"]
            onceki = c
        parcalar.append(metin.strip())
    return " ".join(p for p in parcalar if p)


def tablolar(yol: Path, sayfa_no: int) -> list[list[list[Hucre]]]:
    """Sayfadaki çizgili tablolar: tablo → satır → hücre. Birleşik hücrelerin devamı Hucre("")."""
    sayfa = _pdf(str(yol)).pages[sayfa_no - 1]
    dolgular = _dolgular(sayfa)
    karakterler = [c for c in sayfa.chars if c.get("upright", True)]
    sonuc = []
    for t in sayfa.find_tables():
        izgara = []
        for satir in t.rows:
            hucreler = []
            for kutu in satir.cells:
                if kutu is None:
                    hucreler.append(Hucre(""))
                    continue
                x0, top, x1, bottom = kutu
                icindeki = [c for c in karakterler
                            if x0 <= (c["x0"] + c["x1"]) / 2 <= x1 and top <= (c["top"] + c["bottom"]) / 2 <= bottom]
                normal, ust = _ust_simge_ayir(icindeki)
                metin = _birlestir(normal)
                kalin = bool(normal) and all(KALIN_YAZI in c["fontname"] for c in normal if c["text"].strip())
                hucreler.append(Hucre(metin, _renk(dolgular, (x0 + x1) / 2, (top + bottom) / 2), kalin,
                                      _birlestir(ust)))
            izgara.append(hucreler)
        sonuc.append(izgara)
    return sonuc


def kelimeler(yol: Path, sayfa_no: int) -> list[Kelime]:
    """Sayfadaki yatay kelimeler (çizgi bilgisi kullanılmaz). Dipnot işaretleri ayrı kelime olarak kalır."""
    sayfa = _pdf(str(yol)).pages[sayfa_no - 1]
    dolgular = _dolgular(sayfa)
    sonuc = []
    for w in sayfa.extract_words(extra_attrs=["fontname", "size"], x_tolerance=1.2, keep_blank_chars=False):
        if not w.get("upright", True):
            continue
        sonuc.append(Kelime(w["text"], w["x0"], w["x1"], w["top"], w["bottom"], KALIN_YAZI in w["fontname"],
                            _renk(dolgular, (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2), w["size"]))
    return sonuc

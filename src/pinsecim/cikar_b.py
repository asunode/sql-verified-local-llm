"""Çıkarma B: ESP32-C6 Consolidated Pin Overview (Table 7-1 s. 79, Table 7-2 s. 80), çıkarma A'dan bağımsız.

Çizgi ya da tablo algılama kullanılmaz: kelimeler, ortalarının ikinci başlık satırındaki sütun başlıklarının
sol kenarlarına göre düştüğü sütuna yerleştirilir. Bu tabloda vurgu satır düzeyindedir (bütün satır renkli).
"""

from __future__ import annotations

import re
from pathlib import Path

from .pdfoku import Kelime, kelimeler

SAYFALAR = {"QFN40": (79, "Table 7-1"), "QFN32": (80, "Table 7-2")}
SUTUNLAR = ["pin_no", "pin_adi", "pin_turu", "guc", "reset_ayar", "reset_sonrasi_ayar",
            "analog_0", "analog_1", "lp_0", "lp_1", "iomux_0", "iomux_0_tip", "iomux_1", "iomux_1_tip",
            "iomux_2", "iomux_2_tip"]
# İkinci başlık satırı: No. Name Type Power At Reset After Reset 0 1 0 1 0 Type 1 Type 2 Type
BASLIK = ["No.", "Name", "Type", "Power", "At", "After", "0", "1", "0", "1", "0", "Type", "1", "Type", "2", "Type"]
SOL_PAY = 6.0          # hücre metni başlığın sol kenarından biraz önce başlayabilir (ortalanmış kısa değerler)


def _satirlar(ks: list[Kelime], tolerans: float = 3.0) -> list[list[Kelime]]:
    satirlar: list[list[Kelime]] = []
    for k in sorted(ks, key=lambda k: (k.ust, k.x0)):
        if satirlar and abs(k.ust - satirlar[-1][0].ust) <= tolerans:
            satirlar[-1].append(k)
        else:
            satirlar.append([k])
    return [sorted(s, key=lambda k: k.x0) for s in satirlar]


def _sutun_kenarlari(satirlar: list[list[Kelime]]) -> tuple[list[float], float]:
    for s in satirlar:
        metinler = [k.metin for k in s if k.metin != "Reset"]
        if metinler == BASLIK:
            return [k.x0 for k in s if k.metin != "Reset"], s[0].alt
    raise ValueError("Consolidated tablo başlık satırı bulunamadı")


def tablo(pdf: Path, paket: str) -> list[dict]:
    sayfa, ref = SAYFALAR[paket]
    satirlar = _satirlar(kelimeler(pdf, sayfa))
    kenarlar, baslik_alt = _sutun_kenarlari(satirlar)
    sinirlar = [x - SOL_PAY for x in kenarlar[1:]] + [float("inf")]
    sonuc = []
    for s in satirlar:
        if s[0].ust <= baslik_alt or not re.fullmatch(r"\d+", s[0].metin) or s[0].x0 > kenarlar[1] - SOL_PAY:
            continue
        hucreler: dict[str, list[Kelime]] = {ad: [] for ad in SUTUNLAR}
        for k in s:
            orta = (k.x0 + k.x1) / 2
            i = next(i for i, sinir in enumerate(sinirlar) if orta < sinir)
            hucreler[SUTUNLAR[i]].append(k)
        if not hucreler["pin_adi"]:
            continue
        kayit = {ad: " ".join(k.metin for k in ks) for ad, ks in hucreler.items()}
        kayit["pin_no"] = int(kayit["pin_no"])
        kayit["kalin"] = {ad: all(k.kalin for k in ks) for ad, ks in hucreler.items() if ks}
        renkler = {k.renk for k in s if k.renk}
        kayit["satir_renk"] = renkler.pop() if len(renkler) == 1 else (",".join(sorted(renkler)) or None)
        kayit.update({"paket": paket, "sayfa": sayfa, "referans": ref})
        sonuc.append(kayit)
    return sonuc


def hepsi(pdf: Path) -> dict[str, list[dict]]:
    return {paket: tablo(pdf, paket) for paket in SAYFALAR}

"""Kaynak belgeleri resmî adreslerinden indirir ve SHA-256'larını doğrular (yayın kopyası: PDF'ler depoda yok).

Kullanım (proje kökünden):
    python veri/kaynak/indir.py            # eksik ya da bozuk olanları indirir
    python veri/kaynak/indir.py --denetle  # yalnız var olanları doğrular, indirmez

Sayfa metni (`ham_metin` tablosu) ayrıca saklanmaz; `python -m pinsecim.yukle` onu PDF'ten yerelde yeniden üretir.
Belge sürümü yayıncıda değişmişse SHA tutmaz: indirilen dosya `<ad>.indirilen` olarak bırakılır, betik hata verir.
Bu durumda doğru sürüm elle bulunmalıdır (README, "Kaynak belgeler").
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

DIZIN = Path(__file__).resolve().parent

KAYNAKLAR = [   # (dosya, adres, SHA-256, açıklama); ayrıntı KAYNAKLAR.md
    ("esp32-c6_datasheet_en.pdf",
     "https://documentation.espressif.com/esp32-c6_datasheet_en.pdf",
     "c9bf7ece109859a93be2b4d780370478655a7830c0c171cea6670caf8ab3c339", "ESP32-C6 Series Datasheet v1.6"),
    ("esp32-c6-wroom-1_wroom-1u_datasheet_en.pdf",
     "https://documentation.espressif.com/esp32-c6-wroom-1_wroom-1u_datasheet_en.pdf",
     "163020762fa6d499e0c611c5a13e78ad9d4720b421c6bc5e14e16fc748862b73", "ESP32-C6-WROOM-1/1U Datasheet v1.4"),
    ("nanoESP32-C6_v1.0_sematik.pdf",
     "https://raw.githubusercontent.com/wuxx/nanoESP32-C6/master/hardware/nanoESP32C6.pdf",
     "a2ca1ca2112cf86c636f11a0bc3066a680c24204666f30e12422666a16f18239", "nanoESP32-C6 v1.0 şematiği (MuseLab)"),
    ("esp32-c6-supermini_sematik_tarama.pdf",
     "https://mischianti.org/wp-content/uploads/2026/04/esp32-c6-supermini-board-schematic.pdf",
     "248cabd39c6cc97c8b99500843a1cb86cc17005c2e59a0e10f746b5622db2b8a", "ESP32-C6 Super Mini şematik taraması (topluluk)"),
]


def sha256(yol: Path) -> str:
    h = hashlib.sha256()
    with yol.open("rb") as f:
        for parca in iter(lambda: f.read(1 << 16), b""):
            h.update(parca)
    return h.hexdigest()


def indir(adres: str, hedef: Path) -> None:
    istek = urllib.request.Request(adres, headers={"User-Agent": "Mozilla/5.0 (sql-verified-local-llm kaynak indirici)"})
    with urllib.request.urlopen(istek, timeout=120) as y, hedef.open("wb") as f:
        while parca := y.read(1 << 16):
            f.write(parca)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python veri/kaynak/indir.py")
    ap.add_argument("--denetle", action="store_true", help="indirmeden yalnız doğrula")
    a = ap.parse_args(argv)
    hata = 0
    for dosya, adres, beklenen, aciklama in KAYNAKLAR:
        yol = DIZIN / dosya
        if yol.exists() and sha256(yol) == beklenen:
            print(f"tamam    {dosya}")
            continue
        if a.denetle:
            print(f"{'BOZUK' if yol.exists() else 'YOK':8} {dosya}  ({aciklama})")
            hata += 1
            continue
        gecici = yol.with_name(yol.name + ".indirilen")
        try:
            indir(adres, gecici)
        except OSError as e:
            print(f"İNEMEDİ  {dosya}  {adres}: {e}")
            print("         Elle indirip bu klasöre aynı adla koyun (README, 'Kaynak belgeler').")
            hata += 1
            continue
        bulunan = sha256(gecici)
        if bulunan != beklenen:
            print(f"SHA FARKLI {dosya}: {bulunan} (beklenen {beklenen}); dosya {gecici.name} olarak bırakıldı")
            hata += 1
            continue
        gecici.replace(yol)
        print(f"indirildi {dosya}")
    if not hata:
        print("Bütün kaynaklar doğrulandı. Sayfa metni için: python -m pinsecim.yukle")
    return 1 if hata else 0


if __name__ == "__main__":
    sys.exit(main())

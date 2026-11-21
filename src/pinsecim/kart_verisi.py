"""Kart düzeyi veri (Adım 10b): kaynaklar, kartlar, modül pinleri, kart pinleri, kart üstü parçalar.

Her satır bir kaynak kısa adı (K2, W1, S2, E1), sayfa, referans ve doğrulama durumu taşır. Kaynak dosyaları ve
SHA-256'ları `veri/kaynak/KAYNAKLAR.md`'de; dosyalar değiştirilmez. Değerler Adım 10 raporundaki okumadan
(`doc/raporlar/adim10_rapor.md`, "Kart kaynakları") ve WROOM-1 Table 3-1'den (Adım 10a raporu) alındı.
"""

from __future__ import annotations

KB, DG = "kaynak_belge", "dogrulanmadi"

KAYNAKLAR = {   # kısa ad → kaynak satırı
    "K2": {"belge": "nanoESP32-C6 şematiği (MuseLab)", "surum": "v1.0", "yayin_tarihi": "2023-04-25",
           "sha256": "a2ca1ca2112cf86c636f11a0bc3066a680c24204666f30e12422666a16f18239",
           "dosya_yolu": "veri/kaynak/nanoESP32-C6_v1.0_sematik.pdf",
           "url": "https://github.com/wuxx/nanoESP32-C6/blob/master/hardware/nanoESP32C6.pdf",
           "indirme_zamani": "2026-11-21 10:56:46+03:00", "sayfa_sayisi": 1, "kaynak_turu": "uretici_semasi"},
    "W1": {"belge": "ESP32-C6-WROOM-1 & ESP32-C6-WROOM-1U Datasheet", "surum": "v1.4", "yayin_tarihi": "2025-12-10",
           "sha256": "163020762fa6d499e0c611c5a13e78ad9d4720b421c6bc5e14e16fc748862b73",
           "dosya_yolu": "veri/kaynak/esp32-c6-wroom-1_wroom-1u_datasheet_en.pdf",
           "url": "https://documentation.espressif.com/esp32-c6-wroom-1_wroom-1u_datasheet_en.pdf",
           "indirme_zamani": "2026-11-21 13:06:34+03:00", "sayfa_sayisi": 52, "kaynak_turu": "uretici_belgesi"},
    "S2": {"belge": "ESP32-C6 Super Mini şematik taraması (topluluk)", "surum": "tarama-2026-04-13",
           "yayin_tarihi": "2026-04-13",
           "sha256": "248cabd39c6cc97c8b99500843a1cb86cc17005c2e59a0e10f746b5622db2b8a",
           "dosya_yolu": "veri/kaynak/esp32-c6-supermini_sematik_tarama.pdf",
           "url": "https://mischianti.org/wp-content/uploads/2026/04/esp32-c6-supermini-board-schematic.pdf",
           "indirme_zamani": "2026-11-21 10:56:46+03:00", "sayfa_sayisi": 1, "kaynak_turu": "topluluk"},
    "E1": {"belge": "Kullanıcı envanteri (Sinan)", "surum": "2026-11-21", "yayin_tarihi": "2026-11-21",
           # kısaltılmış kamu sürümü (yayın kopyası); özgün envanterin SHA-256'sı b393f118a13f… (yayımlanmadı)
           "sha256": "82c739f095c55a03685086aa2cd27fd21c495c952159b95525df3270f5f500b7",
           "dosya_yolu": "veri/kaynak/kullanici_envanteri_2026-11-21_kamu.md",
           "url": "yerel: veri/kaynak/kullanici_envanteri_2026-11-21_kamu.md",
           "indirme_zamani": "2026-11-21 00:00:00+03:00", "sayfa_sayisi": 1, "kaynak_turu": "kullanici_envanteri"},
}

V02_NOTU = "v1.0 şematiğinden aktarıldı; sürüm farkı doğrulanmadı"
NANO_SEMA = ("K2", 1, "nanoESP32-C6 v1.0 şematiği")
SM_SEMA = ("S2", 1, "Super Mini şematik taraması")

# (kisa_ad, ad, sürüm, üretici, çip, modül, (kaynak, sayfa, referans), durum, not)
KARTLAR = [
    ("nanoESP32-C6-v1.0", "nanoESP32-C6", "v1.0", "MuseLab", "ESP32-C6", "ESP32-C6-WROOM-1",
     ("K2", 1, "başlık bloğu; U1 ESP32-C6-WROOM-1"), KB,
     "Modülün flash sürümü (N4/N8/N16) şematikte yok."),
    ("nanoESP32-C6-v0.2", "nanoESP32-C6", "v0.2", "MuseLab", "ESP32-C6", "ESP32-C6-WROOM-1",
     ("E1", 1, "envanter satırı 1"), DG,
     "Sürüm kullanıcı envanterinden; v0.2 şematiği üretici deposunda (git geçmişi dahil) bulunamadı. Kart verileri "
     + V02_NOTU + ". 'v0.2' ESP32-C6 çip revizyonu (v0.0/v0.1/v0.2) da olabilir; doğrulanmadı."),
    ("SuperMini", "ESP32-C6 Super Mini", None, None, "ESP32-C6FH4", None,
     ("S2", 1, "U1 ESP32-C6FH4"), DG,
     "Üretici bulunamadı (çok satıcılı); sürümler arasında parça farkı olabilir (S4). Envanter (E1): ESP32-C6FH4, "
     "4 MB dahili flash."),
]

# ESP32-C6-WROOM-1 Table 3-1 (W1 s. 11); K2'deki modül sembolüyle aynı (Adım 10a karşılaştırması).
_MODUL = ["GND", "3V3", "EN", "IO4", "IO5", "IO6", "IO7", "IO0", "IO1", "IO8", "IO10", "IO11", "IO12", "IO13", "IO9",
          "IO18", "IO19", "IO20", "IO21", "IO22", "IO23", "NC", "IO15", "RXD0", "TXD0", "IO3", "IO2", "GND", "EPAD"]


def _modul_gpio(ad: str) -> int | None:
    return int(ad[2:]) if ad.startswith("IO") else {"RXD0": 17, "TXD0": 16}.get(ad)


MODUL_PINLERI = [("ESP32-C6-WROOM-1", no, ad, _modul_gpio(ad), ("W1", 11, "Table 3-1 Pin Definitions"), "K2", KB)
                 for no, ad in enumerate(_MODUL, 1)]

# Kart pinleri: (konnektör, sıra, etiket, GPIO)
_NANO_PINLERI = [
    *[("J1", i, e, g) for i, (e, g) in enumerate(
        [("GND", None), ("3V3", None), ("CHIP_PU", None), ("GPIO4", 4), ("GPIO5", 5), ("GPIO6", 6), ("GPIO7", 7),
         ("GPIO0", 0), ("GPIO1", 1), ("GPIO8", 8), ("GPIO10", 10), ("GPIO11", 11), ("GPIO12", 12), ("GPIO13", 13),
         ("5V", None)], 1)],
    *[("J6", i, e, g) for i, (e, g) in enumerate(
        [("GND", None), ("GPIO2", 2), ("GPIO3", 3), ("TXD0", 16), ("RXD0", 17), ("GPIO15", 15), ("GPIO23", 23),
         ("GPIO22", 22), ("GPIO21", 21), ("GPIO20", 20), ("GPIO19", 19), ("GPIO18", 18), ("GPIO9", 9), ("GND", None),
         ("5V", None)], 1)],
]
_SM_PINLERI = [
    *[("H1", i, e, g) for i, (e, g) in enumerate(
        [("GPIO7", 7), ("GPIO6", 6), ("GPIO5", 5), ("GPIO4", 4), ("GPIO3", 3), ("GPIO2", 2), ("GPIO1", 1), ("GPIO0", 0),
         ("U0RXD", 17), ("U0TXD", 16)], 1)],
    *[("H2", i, e, g) for i, (e, g) in enumerate(
        [("VBUS", None), ("GND", None), ("3V3", None), ("GPIO20", 20), ("GPIO19", 19), ("GPIO18", 18), ("GPIO15", 15),
         ("GPIO14", 14), ("GPIO9", 9), ("GPIO8", 8)], 1)],
    *[("PED", i, e, g) for i, (e, g) in enumerate(
        [("GPIO21", 21), ("GPIO22", 22), ("GPIO23", 23), ("GPIO12", 12), ("GPIO13", 13)], 1)],
]

# (kart, konnektör, sıra, etiket, GPIO, (kaynak, sayfa, referans), durum, not, tür); tür ped: lehim pedi (Adım 10c)
KART_PINLERI = [
    *[("nanoESP32-C6-v1.0", k, s, e, g, (*NANO_SEMA[:2], f"{k} konnektörü"), KB, None, "konnektor")
      for k, s, e, g in _NANO_PINLERI],
    *[("nanoESP32-C6-v0.2", k, s, e, g, (*NANO_SEMA[:2], f"{k} konnektörü"), DG, V02_NOTU, "konnektor")
      for k, s, e, g in _NANO_PINLERI],
    *[("SuperMini", k, s, e, g, (*SM_SEMA[:2], "Microbit Pads (NC)" if k == "PED" else f"{k} başlığı"), DG, None,
       "ped" if k == "PED" else "konnektor") for k, s, e, g in _SM_PINLERI],
]

# Kart üstü parçalar: (tür, ad, GPIO, bağlantı, aktif seviye, açıklama, (kaynak, sayfa, referans), durum, not)
_NANO_PARCALAR = [
    ("ws2812", "D2", 8, "GPIO8 → Q2 BSS138 seviye çevirici → DIN; DIN tarafı 10K ile 5V'a, GPIO8 tarafı 10K ile 3V3'e",
     None, "WS2812B RGB LED", NANO_SEMA, KB, None),
    ("led", "D3", None, "3V3 → R8 10K → LED", None, "kırmızı güç LED'i",
     NANO_SEMA, DG, "Şematikte soluk (gri) çizili; takılı olup olmadığı belli değil."),
    ("buton", "S1", 9, "GPIO9 → GND (basınca)", "dusuk", "BOOT butonu", NANO_SEMA, KB, None),
    ("buton", "S2", None, "CHIP_PU → GND (basınca)", "dusuk", "RST butonu", NANO_SEMA, KB, None),
    ("usb", "J5", None, "USB-C D-/D+ → 22R → GPIO12 (D-) / GPIO13 (D+)", None, "yerel USB Serial/JTAG",
     NANO_SEMA, KB, None),
    ("usb_uart", "U2", None, "J4 USB-C → CH343P; CH343 RXD ← TXD0 (GPIO16), TXD → RXD0 (GPIO17); DTR/RTS → Q1 → "
     "CHIP_PU ve GPIO9 (otomatik indirme)", None, "CH343P USB-UART köprüsü", NANO_SEMA, KB, None),
]
_SM_PARCALAR = [
    ("ws2812", "LED1", 8, "GPIO8 (net RGB_CTRL) → DIN; VDD 3V3", None, "WS2812B RGB LED (0807)", SM_SEMA, DG, None),
    ("led", "PD2", 15, "GPIO15 → PR9 1K → LED → GND", "yuksek", "mavi durum LED'i", SM_SEMA, DG, None),
    ("led", "PD4", None, "TP4054 CHRG çıkışı; GPIO'ya bağlı değil", None, "yeşil şarj LED'i", SM_SEMA, DG, None),
    ("buton", "BOOT", 9, "GPIO9, 10K ile 3V3'e çekili; basınca GND", "dusuk", "BOOT butonu", SM_SEMA, DG, None),
    ("buton", "RST", None, "CHIP_EN, 10K ile 3V3'e çekili; basınca GND", "dusuk", "RST butonu", SM_SEMA, DG, None),
    ("usb", "USB-C", None, "D-/D+ → 22R → GPIO12 / GPIO13; USB-UART köprüsü yok", None, "yerel USB Serial/JTAG",
     SM_SEMA, DG, None),
    ("sarj", "TP4054", None, "BAT pedi", None, "Li-ion şarj entegresi", SM_SEMA, DG,
     "S2 TP4054 gösteriyor; S3 (espboards.dev) LTH7R diyor: çelişki."),
    ("flash", "dahili flash", None, "ESP32-C6FH4 paket içi", None, "4 MB dahili flash", ("E1", 1, "envanter satırı 2"),
     DG, "Kullanıcı envanterinden; kart üstünden doğrulanmadı."),
]
KART_PARCALARI = [
    *[("nanoESP32-C6-v1.0", *p) for p in _NANO_PARCALAR],
    *[("nanoESP32-C6-v0.2", *p[:7], DG, ((p[8] + " ") if p[8] else "") + V02_NOTU + ".") for p in _NANO_PARCALAR],
    ("nanoESP32-C6-v0.2", "flash", "modül flash'ı", None, "ESP32-C6-WROOM-1 içinde, çip dışında (W1 Fig. 8-1)", None,
     "16 MB (N16)", ("E1", 1, "envanter satırı 1"), DG, "Kullanıcı envanterinden; kart üstünden doğrulanmadı."),
    *[("SuperMini", *p) for p in _SM_PARCALAR],
]

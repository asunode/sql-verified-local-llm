"""Doğrulama kararları: A–B ve A iç farkları için karar, ayrıca görsel denetim kaydı.

Her farkın kararı burada; gerekçesi doc/dogrulama/2026-11-20_fark_raporu.md'de. Kararı olmayan bir fark
varsa yükleyici durur.
"""

KAYNAK = {
    "belge": "ESP32-C6 Series Datasheet",
    "surum": "v1.6",
    "yayin_tarihi": "2026-11-10",
    "sha256": "c9bf7ece109859a93be2b4d780370478655a7830c0c171cea6670caf8ab3c339",
    "dosya_yolu": "veri/kaynak/esp32-c6_datasheet_en.pdf",
    "url": "https://www.espressif.com/sites/default/files/documentation/esp32-c6_datasheet_en.pdf",
    "indirme_zamani": "2026-11-20 07:56:04+03:00",
}
AILE = "ESP32-C6"

# anahtar: Fark.anahtar → karar. "belirsiz": satır belgedeki gibi girer, belirsiz işaretlenir.
FARK_KARARLARI = {
    "A-ic|QFN32|9|cevre:SPI2:gpio": {
        "karar": "belgedeki gibi (GPIO1), belirsiz",
        "belirsiz": True,
        "not": "Table 2-11 s.27, pin 9 (GPIO3) SPI2 hücresi 'GPIO1 (P2)' yazıyor (görüntüde doğrulandı). Aynı "
               "satırın diğer GPIO matrisi hücreleri ve Table 2-10'daki aynı hücre GPIO3. Belge kendi içinde tutarsız.",
    },
}

# Görsel denetim: sayfa → (veritabanı tabloları, belgedeki referanslar, sonuç ayrıntısı). Tarih: denetim günü.
GORSEL_DENETIM_TARIHI = "2026-11-20"
GORSEL_DENETIM: dict[int, tuple[list[str], str, str]] = {
    13: (["cip", "paket"], "Table 1-1", "3 varyant, paket, gömülü flash, sıcaklık, revizyon görüntüyle aynı"),
    14: (["pin"], "Figure 2-1", "41 pin etiketi Table 2-1 ile aynı"),
    15: (["pin"], "Figure 2-2", "33 pin etiketi Table 2-2 ile aynı (pin 9 etiketi döndürülmüş)"),
    16: (["pin"], "Table 2-1", "pin 1–17: ad, tür, güç, reset ayarları, işlev kümeleri ve kalın küme aynı"),
    17: (["pin"], "Table 2-1, Table 2-2", "Table 2-1 pin 18–41, Table 2-2 pin 1–15 aynı; dipnot 5 ve 6 işaretleri"),
    18: (["pin"], "Table 2-2", "pin 16–33 aynı; dipnot 3–6 metni pin.dipnot ve varsayilan_surme_ma'ya işlendi"),
    20: (["gpio_islev", "gpio_kisit"], "Table 2-4", "30 GPIO, F0–F2, türler, kalın varsayılanlar ve sarı/kırmızı vurgular aynı"),
    21: (["gpio_islev", "gpio_kisit"], "Table 2-5", "22 GPIO, F0–F2, türler, kalın varsayılanlar ve vurgular aynı"),
    22: (["gpio_islev"], "Table 2-7", "LP_GPIO0–7, F0–F1 aynı; LP_GPIO4/5 sarı"),
    23: (["gpio_islev"], "Table 2-9", "10 satır, iki paketin pin numaraları, F0–F1 ve vurgular aynı"),
    25: (["gpio_kisit"], "2.3.5", "P3/P4 GPIO listeleri aynı"),
    26: (["cevre_birim_sinyal"], "Table 2-10", "18 sütun × 41 satır; 387 dolu hücre aynı"),
    27: (["cevre_birim_sinyal"], "Table 2-11", "17 sütun × 33 satır; 269 dolu hücre aynı; fark: pin 9 SPI2 'GPIO1 (P2)' "
                                               "belgede de böyle yazıyor (belirsiz, fark raporu)"),
    32: (["flash_pin"], "Table 2-16", "6 satır, üç SPI modu aynı"),
    33: (["gpio_kisit"], "Table 3-1", "5 strapping pini ve varsayılanları aynı"),
    34: (["strapping_kombinasyon"], "Table 3-3", "3 kombinasyon; SPI boot mode varsayılan (kalın)"),
    36: (["gpio_kisit"], "3.4", "GPIO15: dahili pull direnci yok notu aynı"),
    79: (["pin", "gpio_islev"], "Table 7-1", "çıkarma B kaynağı; A ile alan alan aynı, satır vurguları aynı"),
    80: (["pin", "gpio_islev"], "Table 7-2", "çıkarma B kaynağı; A ile alan alan aynı, satır vurguları aynı"),
}

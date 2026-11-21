"""Adım 3 verisi: datasheet adetleri, arayüz tanımları, sabit pin bağları, kurallar, yorumlar.

Yükleyici bunları veritabanına yazar; denetleyici ve atayıcı veritabanından okur. Adetlerin `dayanak`
ifadesi yüklemede kaynak sayfanın metninde aranır; bulunmazsa yükleme durur.
"""

from .semalar import ARAYUZLER, PILOT_KAYNAGI

# ad, adet, dayanak (sayfadaki ifade; "sayim:" ile başlarsa olgu tablosundan sayılır), sayfa, referans, not
ADETLER = [
    ("UART", 2, "It consists of two UARTs in the main system", 50, "4.2.1.1", None),
    ("LP_UART", 1, "and one\nlow-power LP UART", 50, "4.2.1.1", None),
    ("I2C", 1, "Two I2C controllers: one in the main system and one in the low-power system", 51, "4.2.1.3",
     "Genel I2C: ana sistemdeki."),
    ("LP_I2C", 1, "Two I2C controllers: one in the main system and one in the low-power system", 51, "4.2.1.3",
     "LP I2C: düşük güç sistemindeki."),
    ("SPI2", 1, "SPI0 and SPI1 are reserved for system use, and only SPI2 is available for users", 50, "4.2.1.2", None),
    ("SPI2_CS", 6, "Provides six FSPICS… pins for connection with six independent SPI slaves", 51, "4.2.1.2",
     "Adım 10c (L-1): SPI ×N tek SPI2 hattı, ayrı CS; en çok altı cihaz."),
    ("RMT", 4, "Four channels for sending and receiving infrared remote control signals", 56, "4.2.1.11",
     "Adım 10c (L-5): RMT_TX ve RMT_RX aynı dört kanalı paylaşır; her kanal ayrı gönderip alabilir (aynı bölüm)."),
    ("I2S", 1, "– I2S", 4, "Features (Peripherals)",
     "Belge sayı vermiyor; özellik listesinde ve 4.2.1.4'te (s. 52) tekil 'The I2S Controller'. "
     "4.2.1.4: ayrı TX ve RX birimleri aynı denetleyicide."),
    ("TWAI", 2, "Two TWAI® controllers", 4, "Features (Peripherals)", None),
    ("LED_PWM", 6, "Six independent PWM generators", 55, "4.2.1.9", "s. 4: 'LED PWM controller, up to 6 channels'."),
    ("ADC", 7, "Analog voltage sampling from up to seven pins", 57, "4.2.2.1",
     "s. 4: 'up to 7 channels'; Table 2-9'da ADC1_CH0–CH6."),
    ("LP_GPIO", 8, "sayim:gpio_islev LP_IO_MUX islev_no=0", 22, "Table 2-7", "LP_GPIO0–LP_GPIO7."),
]

# arayüz → (yönlendirme, Table 2-10/2-11 sütunu, adet adı, bağlam düşümü, sayfa, referans, not)
ARAYUZ_YONLENDIRME = {
    "GPIO_OUT": ("GPIO_MATRISI", None, None, None, 19, "2.3.1",
                 "GPIO matrisi pine hemen her çevre birimi sinyalini verir; paketteki her GPIO."),
    "GPIO_IN": ("GPIO_MATRISI", None, None, None, 19, "2.3.1",
                "GPIO matrisi pine hemen her çevre birimi sinyalini verir; paketteki her GPIO."),
    "UART": ("GPIO_MATRISI", "UART1", "UART", "uart0_konsol", 26, "Table 2-10/2-11 (UART1), 2.3.5",
             "UART1'in P1 pini yok, her GPIO'ya atanabilir (2.3.5). UART0 da GPIO matrisiyle her pine gider "
             "(Table 2-10 dipnot 2)."),
    "I2C": ("GPIO_MATRISI", "I2C", "I2C", None, 26, "Table 2-10/2-11 (I2C)", None),
    "SPI": ("GPIO_MATRISI", "SPI2", "SPI2_CS", None, 26, "Table 2-10/2-11 (SPI2)",
            "SPI2 sinyalleri sabit pinlerine bakılmaksızın her GPIO'ya gider (Table 2-10/2-11 dipnot 2). SPI ×N: tek "
            "hat, ayrı CS (Adım 10c, L-1)."),
    "ADC": ("SABIT", None, "ADC", None, 23, "Table 2-9", None),
    "PWM": ("GPIO_MATRISI", "LED PWM", "LED_PWM", None, 26, "Table 2-10/2-11 (LED PWM)", None),
    "I2S_OUT": ("GPIO_MATRISI", "I2S", "I2S", None, 26, "Table 2-10/2-11 (I2S)",
                "I2S_OUT ve I2S_IN aynı I2S denetleyicisini paylaşır (adet I2S)."),
    "I2S_IN": ("GPIO_MATRISI", "I2S", "I2S", None, 26, "Table 2-10/2-11 (I2S)",
               "I2S_OUT ve I2S_IN aynı I2S denetleyicisini paylaşır (adet I2S)."),
    "TWAI": ("GPIO_MATRISI", "TWAI", "TWAI", None, 26, "Table 2-10/2-11 (TWAI)", None),
    "WAKE": ("SABIT", None, "LP_GPIO", None, 22, "2.3.2, Table 2-7",
             "Deep-sleep'te IO MUX çalışmaz; LP IO MUX pinleri (LP GPIO) kullanılır."),
    "LP_I2C": ("SABIT", None, "LP_I2C", None, 22, "Table 2-7", None),
    "LP_UART": ("SABIT", None, "LP_UART", None, 22, "Table 2-7", None),
    "RMT_TX": ("GPIO_MATRISI", "RMT", "RMT", None, 26, "Table 2-10/2-11 (RMT), 4.2.1.11",
               "Adım 10c (L-5): RMT sinyalleri tabloda P2/P3 öncelikli GPIO'lara GPIO matrisiyle gider."),
    "RMT_RX": ("GPIO_MATRISI", "RMT", "RMT", None, 26, "Table 2-10/2-11 (RMT), 4.2.1.11",
               "Adım 10c (L-5): alma da aynı bölümde açıkça var (Independent transmission and reception)."),
}
# Aynı hatta birden çok cihaz (L-1): arayüz → seçim sinyali (ilk örnek bütün sinyalleri, sonrakiler yalnız bunu alır).
# "adres" (Adım 11a): cihazlar hat üzerinde adresle ayrılır; sonraki örnekler pin almaz ve birim sayısına girmez (I2C).
ORTAK_HAT_SECIM = {"SPI": "CS", "I2C": "adres", "LP_I2C": "adres"}

# (arayüz, sinyal) → (grup, işlev deseni, sayfa, referans)
SABIT_SINYALLER = {
    ("ADC", "AIN"): ("ANALOG", "ADC1_CH%", 23, "Table 2-9"),
    ("WAKE", "IN"): ("LP_IO_MUX", "LP_GPIO%", 22, "Table 2-7"),
    ("LP_I2C", "SDA"): ("LP_IO_MUX", "LP_I2C_SDA", 22, "Table 2-7"),
    ("LP_I2C", "SCL"): ("LP_IO_MUX", "LP_I2C_SCL", 22, "Table 2-7"),
    ("LP_UART", "TX"): ("LP_IO_MUX", "LP_UART_TXD", 22, "Table 2-7"),
    ("LP_UART", "RX"): ("LP_IO_MUX", "LP_UART_RXD", 22, "Table 2-7"),
}

# Arayüzlerin isteme giren kısa tanımı (pilot tanımı; İngilizce, model istemine girer).
ARAYUZ_TANIMLARI = {
    "GPIO_OUT": "One digital output line switched by software: lamp, relay, transistor, enable or reset line. "
                "A device that needs several output lines needs one per line. A matrix device (keypad, LED matrix) "
                "with R rows and C columns uses R + C lines in total, not R x C.",
    "GPIO_IN": "One digital input line read by software: button, switch, end stop, interrupt or status line. "
               "A device that needs several input lines needs one per line. A matrix device (keypad, LED matrix) "
               "with R rows and C columns uses R + C lines in total, not R x C.",
    "UART": "Asynchronous serial port with TX and RX, for one serial device.",
    "I2C": "General I2C bus (SDA, SCL). One bus serves several I2C devices with different addresses.",
    "SPI": "General SPI bus (SCLK, MOSI, MISO, CS) for one SPI device.",
    "ADC": "One analog input channel: reads a voltage, such as an analog sensor output or a variable resistor.",
    "PWM": "One PWM output channel: brightness, speed or position control, tone generation.",
    "I2S_OUT": "I2S digital audio output (BCLK, WS, DOUT), to a DAC or amplifier.",
    "I2S_IN": "I2S digital audio input (BCLK, WS, DIN), from a digital microphone or ADC.",
    "TWAI": "CAN bus controller (TWAI) with TX and RX, connected through a CAN transceiver.",
    "WAKE": "One input whose purpose is to wake the chip from deep sleep: any wake-up button, switch or sensor "
            "signal, also when the words 'deep sleep' are not used.",
    "LP_I2C": "Low-power I2C bus (LP I2C), usable while the main system sleeps.",
    "LP_UART": "Low-power UART (LP UART), usable while the main system sleeps.",
    "RMT_TX": "One RMT transmit channel: addressable LED strip (WS2812, NeoPixel) data line or infrared transmitter.",
    "RMT_RX": "One RMT receive channel: infrared remote control receiver.",
}

# Tek kalemi birden çok cihazın paylaştığı hatlar: dayanaktaki sayı cihaz sayısıdır, adet değil (SAYI_UYUSMAZ uygulanmaz).
PAYLASIMLI_HAT = {"I2C", "LP_I2C"}

# Dayanaktaki sayı ifadeleri (SAYI_UYUSMAZ). Küçük harf. Basamaklı sözcükler Türkçe sayı dizilişiyle birleştirilir
# (Adım 10a: "on altı", "onaltı", "iki yüz elli"); öbürleri kendi başına, çok sözcüklüler en uzun eşleşmeyle okunur.
_BIRLER = ["bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
_ONLAR = ["on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
SAYI_BASAMAKLARI = {  # ifade → (değer, basamak)
    **{s: (n, "birler") for n, s in enumerate(_BIRLER, 1)}, **{s: (10 * n, "onlar") for n, s in enumerate(_ONLAR, 1)},
    "yüz": (100, "yuz"), "bin": (1000, "bin"),
}
SAYI_SOZCUKLERI = {"tek": 1, "çift": 2, "bir çift": 2, "düzine": 12, "bir düzine": 12, "yarım düzine": 6}
SAYI_EKLERI = {"sıfır": 0}            # Adım 10a; basamaksız
# Sayı olmayan ifadeler (deger NULL): içindeki sayı sözcüğü bu bağlamda sayı değildir.
SAYI_ISTISNALARI = ["çift yönlü"]
ISTISNA_KAYNAGI = "pilot tanımı (Web AI, Adım 7), 2026-11-21"
SAYI_ISTISNALARI_10A = ["bir de", "bir şey", "bir şeyi", "bir şeyler"]
SAYI_KAYNAGI_10A = "pilot tanımı (DAI, Adım 10a; Web AI görevi: Türkçe sayı kuralı), 2026-11-21"

# Arayüz eş adları (küçük harf): cevaplayıcı ve diger_ifadeler uyarısı için. Kart bağlamı sözlüğüyle çakışan ad yok
# ("seri port", "programlama portu" bilerek alınmadı; test_es_ad_baglam_cakismasi). Küçük harf, harfe duyarlılar hariç.
ARAYUZ_ES_ADLARI = [   # (eş ad, arayüz[, harfe duyarlı]); harfe duyarlı ad metinde birebir aranır (Adım 10b)
    ("CAN", "TWAI", True), ("can bus", "TWAI"), ("analog", "ADC"), ("analog giriş", "ADC"), ("iic", "I2C"), ("i²c", "I2C"),
    ("dijital giriş", "GPIO_IN"), ("dijital çıkış", "GPIO_OUT"), ("seri haberleşme", "UART"),
    ("ws2812", "RMT_TX"), ("neopixel", "RMT_TX"), ("adreslenebilir led", "RMT_TX"),   # Adım 10c (L-5)
]
ES_AD_KAYNAGI = "pilot tanımı (Web AI görevi, DAI; Adım 10a), 2026-11-21"

# Desteklenmeyen özellikler (Adım 11a): datasheet v1.6'nın çevre birimi listelerinde (Features > Peripherals s. 4;
# 4.2 Peripherals s. 50–57) bulunmayanlar. (terim, açıklama, eş adlar (harfe duyarsız), harfe duyarlı adlar). Yükleyici
# her adın o sayfalarda geçmediğini denetler. Şüpheliler alınmadı: "paralel" (PARLIO var), "SDIO" (SDIO slave var),
# "LCD" ve "kamera"/"kamera modülü" (SPI/I2C ile bağlanan ekran ve kameralar var), "analog çıkış" (PWM ile yapılır),
# "dokunmatik", "dokunmatik sensör/buton", "kapasitif dokunmatik" (dış dokunmatik modüller dijital çıkış verir),
# "USB" (USB Serial/JTAG var), "Bluetooth Classic" (pin ataması değil).
DESTEKLENMEYEN_OZELLIKLER = [
    ("Ethernet MAC", "Ethernet MAC ve RMII/MII arayüzü yok.", ["ethernet"], ["RMII", "MII"]),
    ("DAC", "Dijital-analog dönüştürücü (DAC) yok.", ["dijital-analog dönüştürücü", "dijital analog dönüştürücü"],
     ["DAC"]),
    ("Dokunmatik sensör (touch)", "Çipte dokunmatik (touch) sensör pini yok.",
     ["touch sensor", "touch pin", "dokunmatik pin"], []),
    ("USB OTG / USB host", "USB OTG ve USB host denetleyicisi yok (yalnız USB Serial/JTAG).",
     ["usb host", "usb otg"], ["OTG"]),
    ("Kamera arayüzü", "Kamera (DVP/MIPI CSI) arayüzü yok.", ["kamera arayüzü", "camera interface", "mipi csi"],
     ["DVP"]),
    ("SD/MMC host", "SD/MMC host denetleyicisi yok (yalnız SDIO slave).", ["sdmmc", "sd/mmc host", "sd host"], []),
]
DESTEKLENMEYEN_SAYFALAR = (4, *range(50, 58))
DESTEKLENMEYEN_REFERANS = "Features (Peripherals) s. 4; 4.2 Peripherals s. 50–57: bu listede yok"

# Bağlam ifadeleri: konu (ifadede geçen desen → bağlam anahtarı) ve olumsuzluk (ifadede geçerse değer "hayır").
BAGLAM_SOZCUKLERI = [
    ("konu", "usb_serial_jtag", "usb"),
    ("konu", "uart0_konsol", "uart0"), ("konu", "uart0_konsol", "konsol"),
    ("konu", "jtag_pinleri", "jtag"),
    ("konu", "harici_flash_beslemesi", "flash"),
    *[("olumsuz", None, d) for d in ("mayacağ", "meyeceğ", "mayacak", "meyecek", "mıyor", "miyor", "muyor", "müyor",
                                     "madan", "meden", "olmayacak", "yok", "değil", "kapalı", "devre dışı", "istemiyorum")],
]

# Metindeki GPIO bahsi desenleri (tur, desen, açıklama). Metin Türkçe küçük harfe çevrilir, "ı" → "i"; 1. grup numara.
PIN_BAHSI_DESENLERI = [
    ("gpio", r"\b(?:gpio|io)[\s_-]?(\d{1,2})(?!\d)", "GPIO5, gpio5, gpıo11, GPIO 5, IO4"),
    ("liste_devami", r"\s*(?:,\s*(?:ve\s+|veya\s+)?|\s+(?:ve|veya|ile)\s+)(\d{1,2})"
                     r"(?=\s*(?:$|[,.;:)'’]|ve\b|veya\b|ile\b|pin))",
     "bir bahsin ardından virgül, 've', 'veya', 'ile' ile gelen çıplak sayı: GPIO19, 18, 20 ve 21; sayıdan sonra "
     "ad gelirse ('GPIO5, 3 LED') bahis değil"),
    ("belirsiz", r"\b(\d{1,2})\s*numarali\s+pin", "5 numaralı pin"),
    ("belirsiz", r"\bpin\s*(?:no\.?\s*)?(\d{1,2})(?!\d)", "pin 5, pin no 5"),
    ("belirsiz", r"\b(\d{1,2})\.\s*pin", "5. pin"),
]
PIN_BAHSI_KAYNAGI = "pilot tanımı (DAI, Adım 9; Web AI görevi), 2026-11-21"

VEREN = "Web AI — datasheet P3/P4 sınıflarına dayanarak"
KART_KURALI = "kart verisi (Adım 10c; Web AI görevi)"
PILOT = "pilot tanımı (Web AI), 2026-11-20"
SOZLUK_KAYNAGI = "pilot tanımı (DAI, Adım 6), 2026-11-20"

# kod, kategori, kisit_turu, bağlam, seviye | (dogru, yanlis), mesaj, açıklama, sayfa, referans
KURALLAR = [
    ("GECERSIZ_GPIO", "yapisal", None, None, "hata",
     "GPIO{gpio} does not exist on this chip (valid: GPIO0-GPIO30). [{kaynak}]",
     "Çipte olmayan GPIO no; o GPIO için başka pin kuralı işletilmez.", 20, "Table 2-4/2-5"),
    ("PIN_PAKETTE_YOK", "pin", "bu_pakette_yok", None, "hata",
     "GPIO{gpio} has no pin on the {paket} package. [{kaynak}]",
     "GPIO bu pakette yok; o GPIO için başka pin kuralı işletilmez.", 20, "Table 2-4/2-5"),
    ("PIN_FLASH", "pin", "flash", None, "hata",
     "GPIO{gpio} is connected to the SPI flash (P4, not recommended); do not use it. [{kaynak}]",
     "Flash pini (P4).", 25, "2.3.5 (P4), 2.3.4, 2.6"),
    ("PIN_VDD_SPI", "pin", "vdd_spi", "harici_flash_beslemesi", ("uyari", "hata"),
     "GPIO{gpio} is the VDD_SPI flash supply pin (P3); usable as GPIO only if the flash has an external supply. [{kaynak}]",
     "VDD_SPI: flash harici beslemeli değilse hata, beslemeliyse uyarı.", 25, "2.3.5 (P3), 2.3.4"),
    ("PIN_USB", "pin", "usb_serial_jtag", "usb_serial_jtag", ("hata", "uyari"),
     "GPIO{gpio} is USB_D-/USB_D+ of the USB Serial/JTAG controller (P3). [{kaynak}]",
     "USB Serial/JTAG kullanılıyorsa hata, kullanılmıyorsa uyarı.", 25, "2.3.5 (P3), 2.3.4"),
    ("PIN_UART0", "pin", "uart0", "uart0_konsol", ("hata", "uyari"),
     "GPIO{gpio} is a UART0 console pin (P3). [{kaynak}]",
     "UART0 konsolsa hata, değilse uyarı.", 25, "2.3.5 (P3), 2.3.4"),
    ("PIN_JTAG", "pin", "jtag", "jtag_pinleri", ("hata", "uyari"),
     "GPIO{gpio} is a JTAG pin (P3). [{kaynak}]",
     "JTAG pinleri kullanılıyorsa hata, kullanılmıyorsa uyarı.", 25, "2.3.5 (P3), 2.3.4"),
    ("PIN_STRAPPING", "pin", "strapping", None, "uyari",
     "GPIO{gpio} is a strapping pin (P3); its level at reset selects boot options. [{kaynak}]",
     "Strapping pini: uyarı.", 25, "2.3.5 (P3), Table 3-1"),
    ("CAKISMA", "yapisal", None, None, "hata",
     "GPIO{gpio} is assigned to more than one signal ({sinyal}).",
     "Aynı GPIO birden fazla sinyalde; aynı ihtiyacın aynı sinyali iki kez atanırsa da.", None, PILOT),
    ("EKSIK_SINYAL", "yapisal", None, None, "hata",
     "Need '{ihtiyac}' ({arayuz}) has no GPIO for signal {sinyal}.",
     "İhtiyacın sinyallerinden biri atanmamış.", None, PILOT),
    ("BILINMEYEN", "yapisal", None, None, "hata",
     "{sinyal}",
     "İstekte olmayan ihtiyaç kimliği ya da arayüzün sözlüğünde olmayan sinyal adı.", None, PILOT),
    ("SABIT_PIN", "yapisal", None, None, "hata",
     "Signal {sinyal} of need '{ihtiyac}' ({arayuz}) is fixed to {izinli}; GPIO{gpio} is not allowed. [{kaynak}]",
     "Sabit pin isteyen sinyal başka pine atanmış.", 22, "Table 2-7, Table 2-9 (arayuz_sinyal)"),
    ("ADET_ASIMI", "adet", None, None, "hata",
     "{arayuz}: {sayi} needs but only {adet} available. [{kaynak}]",
     "Durum 'atandi' ama bir arayüzün ihtiyaç sayısı adet sınırını aşıyor.", None, "cevre_adet (adet başına sayfa)"),
    ("YANLIS_RET", "yapisal", None, None, "hata",
     "Status is 'mumkun_degil' but a valid assignment exists, e.g. {ornek}.",
     "Durum 'mumkun_degil' ama kod atayıcı geçerli bir atama buluyor.", None, PILOT),
    ("YASAK_PIN", "yapisal", None, None, "hata",
     "GPIO{gpio} must not be used: the user excluded it.",
     "Kullanıcının kullanılmayacak dediği pin atamada (K-7).", None, PILOT),
    ("TERCIH_UYGULANMADI", "yapisal", None, None, "hata",
     "The user wants {arayuz}{sinyal} on GPIO{gpio}, but the assignment does not use it there.",
     "Uygulanan bir pin tercihi atamada yok (K-7).", None, PILOT),
    ("BELIRSIZ_KAYNAK", "yapisal", None, None, "uyari",
     "GPIO{gpio} for {arayuz} relies on an ambiguous datasheet cell with no interpretation; it was ignored. [{kaynak}]",
     "Belirsiz olgu satırı yorumsuz: yok sayıldı.", None, "dogrulama kuralı (Adım 3)"),
    # Kart düzeyi (Adım 10c): yalnız istekte kart varsa (--kart).
    ("KART_PIN_YOK", "yapisal", None, None, "hata",
     "GPIO{gpio} is not brought out on board {kart} (neither a header pin nor a pad).",
     "Kartın konnektörüne ya da pedine çıkmayan GPIO atanamaz.", None, KART_KURALI),
    ("KART_PED", "yapisal", None, None, "uyari",
     "GPIO{gpio} ({etiket}) is only on a pad of board {kart}, not on a header. [{kaynak}]",
     "Ped pini yalnız konnektör pinleri yetmezse kullanılır; kullanılırsa uyarı.", None, KART_KURALI),
    ("KART_PARCA", "yapisal", None, None, "uyari",
     "GPIO{gpio} ({etiket}) is connected to the on-board {parca} of board {kart}. [{kaynak}]",
     "Kart üstü parçaya bağlı pin son çare; kullanılırsa (tercih dahil) uyarı.", None, KART_KURALI),
    ("KART_UART_KOPRU", "yapisal", None, None, "uyari",
     "GPIO{gpio} ({etiket}) is a UART0 pin; on board {kart} the USB-UART bridge {parca} is connected to UART0. [{kaynak}]",
     "Kartta USB-UART köprüsü varsa UART0 pinine atamada uyarı.", None, KART_KURALI),
]

YORUMLAR = [
    {
        "olgu_tablo": "cevre_birim_sinyal",
        "olgu_anahtar": {"paket": "QFN32", "pin_no": 9, "cevre_birim": "SPI2"},
        "yorum": "SPI2 sinyalleri GPIO matrisiyle GPIO3'e gider.",
        "deger": {"gpio_no": 3},
        "gerekce": [
            "Aynı satırın (Table 2-11, pin 9) diğer GPIO matrisi hücreleri GPIO3 (P2).",
            "Table 2-10'da (QFN40) aynı pinin SPI2 hücresi GPIO3 (P2).",
            "2.3.5'teki P2 tanımı: GPIO matrisi hücresi o pinin GPIO'sudur.",
        ],
        "kaynaklar": ["Table 2-11 s. 27", "Table 2-10 s. 26", "2.3.5 s. 25"],
        "veren": "Web AI",
        "tarih": "2026-11-20",
    },
]


def arayuz_satirlari() -> list[dict]:
    satirlar = []
    for arayuz, sinyaller in ARAYUZLER.items():
        yon, sutun, adet, dusum, sayfa, ref, not_ = ARAYUZ_YONLENDIRME[arayuz]
        satirlar.append({"arayuz": arayuz, "sinyaller": sinyaller, "sinyal_kaynagi": PILOT_KAYNAGI,
                         "yonlendirme": yon, "cevre_birim": sutun, "adet_adi": adet, "adet_baglam_dusumu": dusum,
                         "tanim": ARAYUZ_TANIMLARI[arayuz], "paylasimli_hat": arayuz in PAYLASIMLI_HAT,
                         "ortak_hat_secim": ORTAK_HAT_SECIM.get(arayuz), "sayfa": sayfa, "referans": ref, "not": not_})
    return satirlar


# Kullanıcıya gösterilen Türkçe mesajlar (kural.mesaj_tr); yer tutucular İngilizce mesajla aynı.
KURAL_MESAJ_TR = {
    "GECERSIZ_GPIO": "GPIO{gpio} bu çipte yok (geçerli: GPIO0–GPIO30). [{kaynak}]",
    "PIN_PAKETTE_YOK": "GPIO{gpio}: {paket} paketinde pini yok. [{kaynak}]",
    "PIN_FLASH": "GPIO{gpio}: SPI flash'a bağlı (P4, önerilmez); kullanılmamalı. [{kaynak}]",
    "PIN_VDD_SPI": "GPIO{gpio}: flash besleme pini VDD_SPI (P3); yalnız flash harici beslenirse GPIO olarak "
                   "kullanılabilir. [{kaynak}]",
    "PIN_USB": "GPIO{gpio}: USB Serial/JTAG denetleyicisinin USB_D-/USB_D+ pini (P3). [{kaynak}]",
    "PIN_UART0": "GPIO{gpio}: UART0 konsol pini (P3). [{kaynak}]",
    "PIN_JTAG": "GPIO{gpio}: JTAG pini (P3). [{kaynak}]",
    "PIN_STRAPPING": "GPIO{gpio}: strapping pini (P3); reset anındaki seviyesi açılış seçeneklerini belirler. [{kaynak}]",
    "KART_PIN_YOK": "GPIO{gpio}: {kart} kartında konnektöre ya da pede çıkmıyor; atanamaz.",
    "KART_PED": "GPIO{gpio} ({etiket}): {kart} kartında konnektörde değil, yalnız pedde; bağlantı için lehim gerekir. "
                "[{kaynak}]",
    "KART_PARCA": "GPIO{gpio} ({etiket}): kart üstü {parca} bu pine bağlı. [{kaynak}]",
    "KART_UART_KOPRU": "GPIO{gpio} ({etiket}): UART0 pini; {kart} kartında {parca} USB-UART köprüsü UART0'a bağlı. "
                       "[{kaynak}]",
    "CAKISMA": "GPIO{gpio} birden çok sinyale atanmış ({sinyal}).",
    "EKSIK_SINYAL": "'{ihtiyac}' ({arayuz}) ihtiyacının {sinyal} sinyaline GPIO atanmamış.",
    "BILINMEYEN": "{sinyal}",
    "SABIT_PIN": "'{ihtiyac}' ({arayuz}) {sinyal} sinyali yalnız {izinli} olabilir; GPIO{gpio} olamaz. [{kaynak}]",
    "ADET_ASIMI": "{arayuz}: {sayi} ihtiyaç var, kullanılabilir {adet}. [{kaynak}]",
    "YANLIS_RET": "Durum 'mumkun_degil' ama geçerli bir atama var, örneğin {ornek}.",
    "YASAK_PIN": "GPIO{gpio} kullanılmamalı: kullanıcı dışarıda bıraktı.",
    "TERCIH_UYGULANMADI": "Kullanıcı {arayuz}{sinyal} için GPIO{gpio} istiyor; atamada orada değil.",
    "BELIRSIZ_KAYNAK": "GPIO{gpio} ({arayuz}) datasheet'te yorumu olmayan belirsiz bir hücreye dayanıyor; yok sayıldı. "
                       "[{kaynak}]",
}


# Soru konuları (Adım 10, K-8): konu, modele giden tanım, cevap türü, gereken bilgi, cevabı veren tablolar.
SORU_KONULARI = [
    ("pin_islevi", "what functions a given GPIO has", "tablo", "gpio", "gpio_islev (Table 2-4…2-9)"),
    ("pin_kisiti", "restrictions or special roles of a given GPIO (strapping, flash, USB, JTAG, UART0 console)",
     "tablo", "gpio", "gpio_kisit, kural (2.3.5, Table 3-1)"),
    ("arayuz_pinleri", "which GPIOs a given interface (I2C, SPI, UART, ADC, …) can use", "tablo", "arayuz",
     "arayuz_tanimi, arayuz_sinyal, gpio_islev, cevre_birim_sinyal, kural"),
    ("paket_pinleri", "which GPIOs the chip package has or which of them can be used", "tablo", None,
     "pin, gpio_kisit, kural"),
    ("kart_led", "LEDs on a development board", "kart", None, "kart, kart_pin, kart_parca, modul_pin"),
    ("kart_buton", "buttons on a development board", "kart", None, "kart, kart_pin, kart_parca, modul_pin"),
    ("kart_pin_cikisi", "the header pins or pin labels of a development board", "kart", None,
     "kart, kart_pin, kart_parca, modul_pin"),
    ("diger", "any other question", "tabloda_yok", None, None),
]
SORU_KAYNAGI = "pilot tanımı (Web AI görevi, DAI; Adım 10), 2026-11-21"

# Kullanıcı mesajları: anahtar, mesaj, ne yazmalı, örnek, modele giden tanım (yalnız eksik.*).
DURUM_MESAJLARI = [
    ("durum.desteklenmiyor", "İstekte bu çipin desteklenen arayüzleriyle yapılamayan bir işlev var.",
     "Desteklenmeyen kısmı çıkar ya da desteklenen bir arayüzle (I2C, SPI, UART, ADC, PWM, TWAI, I2S, dijital "
     "giriş/çıkış) yapılacak biçimde yaz.", "Ekranı paralel değil SPI ile bağlayacağım.", None),
    ("durum.emin_degilim", "İstek, hangi pin arayüzlerinin gerektiğine karar vermeye yetmedi.",
     "Karta ne bağlanacağını, kaç tane olduğunu ve nasıl bağlanacağını yaz.", "Bir BME280 sensörünü I2C ile okuyacağım.",
     None),
    ("durum.KULLANICIYA", "Çıkarım, düzeltme turları içinde denetimden geçmedi; karar size kaldı.",
     "Her cihazı ayrı ve kısa cümlelerle yazıp yeniden dene.", None, None),
    ("durum.JSON_GECERSIZ", "Model şemaya uyan bir yanıt veremedi.", "İsteği yeniden dene; sürerse bildir.", None, None),
    ("eksik.cihaz_belirsiz", "Karta ne bağlanacağı belli değil.",
     "Bağlanacak cihazı ya da işlevi yaz (sensör, röle, ekran, buton …).", "İki röle ve bir buton bağlayacağım.",
     "the description does not say which device or function is connected"),
    ("eksik.arayuz_belirsiz", "Cihaz belli ama hangi arayüzle bağlanacağı belli değil.",
     "Bağlantı türünü yaz: I2C, SPI, UART, analog giriş, dijital giriş ya da çıkış.",
     "OLED ekranı I2C ile bağlayacağım.",
     "a device is named but its interface cannot be decided from the description or common knowledge"),
    ("eksik.adet_belirsiz", "Kaç tane bağlanacağı belli değil.", "Her cihazdan kaç tane olduğunu yaz.",
     "Dört LED süreceğim.", "the number of devices or lines cannot be decided"),
    ("eksik.celiskili", "İstekteki bilgiler birbiriyle çelişiyor.", "Çelişen kısmı düzeltip isteği yeniden yaz.", None,
     "parts of the description contradict each other"),
    ("cevap.tabloda_yok", "Bu konu veritabanındaki tablolarda yok; cevap verilmedi.", None, None, None),
    ("cevap.gpio_eksik", "Soruda GPIO numarası yok; hangi pin sorulduğu belli değil.",
     "Soruyu GPIO numarasıyla yaz.", "GPIO8'in işlevleri neler?", None),
    ("cevap.arayuz_eksik", "Soruda arayüz adı yok; hangi arayüzün pinleri sorulduğu belli değil.",
     "Soruyu arayüz adıyla yaz (I2C, SPI, UART, ADC, PWM, TWAI, I2S, LP_I2C, LP_UART).",
     "UART hangi pinlere çıkabilir?", None),
]
MESAJ_KAYNAGI = "pilot tanımı (DAI, Adım 10; Web AI önerisi), 2026-11-21"
# Adım 10b: kart soruları ve kartlı atama notu.
DURUM_MESAJLARI_10B = [
    ("cevap.kart_eksik", "Soru bir geliştirme kartıyla ilgili ama --kart verilmedi; hangi kart olduğu belli değil.",
     "Komutu --kart seçeneğiyle, yukarıdaki kartlardan biriyle yeniden çalıştır.", "--kart {kart}", None),
    ("cevap.kart_gorev_yok", "Kart verisi LED'lere görev (watchdog, durum, hata göstergesi vb.) atamaz; görevi "
     "yazılımda sen belirlersin. Aşağıda LED'lerin hangi GPIO'dan sürüldüğü var.", None, None, None),
]
MESAJ_KAYNAGI_10B = "pilot tanımı (DAI, Adım 10b; Web AI görevi), 2026-11-21"
# Adım 11a: elektriksel değer soruları. Bölüm numarası ve adı yükleyicide sayfa metniyle denetlenir.
ELEKTRIKSEL_BOLUM = (64, "5 Electrical Characteristics")
DURUM_MESAJLARI_11A = [
    ("cevap.elektriksel_yok", "Elektriksel değerler (akım, gerilim) yapılı tablolarda yok; ESP32-C6 Datasheet v1.6, "
     "Bölüm 5 (Electrical Characteristics), s. 64.", None, None, None),
]
MESAJ_KAYNAGI_11A = "pilot tanımı (DAI, Adım 11a; Web AI görevi), 2026-11-21"
# (sözcük, harfe duyarlı): harfe duyarlılar birim kısaltmaları.
SORU_SOZCUKLERI = [
    ("akım", False), ("gerilim", False), ("voltaj", False), ("volt", False), ("amper", False), ("miliamper", False),
    ("güç tüketimi", False), ("mA", True), ("µA", True), ("uA", True), ("V", True), ("mV", True), ("mW", True),
]
SORU_SOZCUGU_KAYNAGI = MESAJ_KAYNAGI_11A

# Adım 12, SPI_ADET_IZI: sayıdan sonra gelince sayıyı cihaz sayısı olmaktan çıkaran sözcükler (sözcük, tür, biçim, harfe
# duyarlı). Birimler: ölçü, para, süre; harfe duyarlılar kısaltma. 'hat': sayı hattı sayıyor ("bir SPI hattına").
# "16x2" tek sözcük olduğundan sayı sayılmaz; "16 x 2" ve ondalık ("3,3 V") kodda ayıklanır.
SAYI_DISI_SOZCUKLER = [
    *((b, "birim", "tam", True) for b in ("V", "mV", "kV", "A", "mA", "µA", "uA", "W", "mW", "kW", "Hz", "kHz",
                                          "MHz", "GHz", "TL", "USD", "EUR", "mm", "cm", "m", "km", "g", "kg", "ms",
                                          "µs", "us", "s", "dk", "sn", "Ω", "kΩ", "k", "K", "F", "µF", "uF", "nF",
                                          "pF", "mAh", "Ah", "dB", "bit", "kbit", "kB", "MB", "GB", "bps", "baud")),
    *((b, "birim", "onek", False) for b in ("volt", "amper", "miliamper", "watt", "hertz", "lira", "dolar", "avro",
                                            "euro", "kuruş", "milimetre", "santim", "santimetre", "metre", "kilometre",
                                            "gram", "kilogram", "saniye", "milisaniye", "dakika", "saat", "derece",
                                            "ohm", "yüzde", "kanal", "bayt", "byte")),
    ("hat", "hat", "tam", False), ("hatt", "hat", "onek", False), ("hatl", "hat", "onek", False),
    ("veri yolu", "hat", "onek", False), ("bus", "hat", "tam", False),
]
SAYI_DISI_KAYNAGI = "pilot tanımı (DAI, Adım 12; Web AI görevi), 2026-11-21"

# Pin seçimi raporu

- Tarih: 2026-11-21 18:25:11 +0300
- Kart: SuperMini (ESP32-C6 Super Mini)
- Paket: QFN32
- Bağlam: usb_serial_jtag=evet, uart0_konsol=evet, jtag_pinleri=hayır, harici_flash_beslemesi=hayır
- Model: gemma4:12b-it-qat, CPU (num_gpu 0), temperature 0, seed 42, num_ctx 8192, think kapalı
- İstemler: ihtiyac_sistem.txt 3ff741e27c2e, atama_sistem.txt f09040e1f110
- Dondurma kaydı: `2026-11-21_adim10c_dondurma` (istemler aynı; dondurulan dosyaların hepsi aynı)

## Kaynaklar

| Belge | Sürüm | Tür | SHA-256 (baş) |
|---|---|---|---|
| ESP32-C6 Series Datasheet | v1.6 | uretici_belgesi | `c9bf7ece1098` |
| nanoESP32-C6 şematiği (MuseLab) | v1.0 | uretici_semasi | `a2ca1ca2112c` |
| ESP32-C6-WROOM-1 & ESP32-C6-WROOM-1U Datasheet | v1.4 | uretici_belgesi | `163020762fa6` |
| ESP32-C6 Super Mini şematik taraması (topluluk) | tarama-2026-04-13 | topluluk | `248cabd39c6c` |
| Kullanıcı envanteri (Sinan) | 2026-11-21 | kullanici_envanteri | `b393f118a13f` |

## Komut satırı çıktısı

```
İstek: İki basınç dönüştürücüsünü aynı SPI hattından okuyacağım ve on iki vantilatörü ayrı ayrı açıp kapatacağım.
Kart: SuperMini · Paket: QFN32 · bağlam: usb_serial_jtag=evet, uart0_konsol=evet, jtag_pinleri=hayır, harici_flash_beslemesi=hayır

1) İhtiyaçlar (model, 2. turda geçti):
   - SPI       ×2  «İki basınç dönüştürücüsünü aynı SPI hattından okuyacağım»
   - GPIO_OUT  ×12 «on iki vantilatörü ayrı ayrı açıp kapatacağım»  [model çıkarımı — kontrol edin]

3) Atama (kod atayıcı):
   Kart düzeyi: SuperMini; adaylar karta çıkan pinler (17 konnektör pini, 5 ped). Ped: GPIO21–GPIO23; kart üstü parça pini: GPIO8, GPIO9.
   Sonuç: atandı
   İhtiyaç      Sinyal GPIO           Pinin durumu
   spi_1        SCLK   GPIO0 (H1-8)   serbest
   spi_1        MOSI   GPIO1 (H1-7)   serbest
   spi_1        MISO   GPIO2 (H1-6)   serbest
   spi_1        CS     GPIO3 (H1-5)   serbest
   spi_2        CS     GPIO14 (H2-8)  serbest
   gpio_out_1   OUT    GPIO18 (H2-6)  serbest
   gpio_out_2   OUT    GPIO19 (H2-5)  serbest
   gpio_out_3   OUT    GPIO20 (H2-4)  serbest
   gpio_out_4   OUT    GPIO21 (PED-1) serbest
   gpio_out_5   OUT    GPIO22 (PED-2) serbest
   gpio_out_6   OUT    GPIO23 (PED-3) serbest
   gpio_out_7   OUT    GPIO4 (H1-4)   uyarı (PIN_JTAG, PIN_STRAPPING)
   gpio_out_8   OUT    GPIO5 (H1-3)   uyarı (PIN_JTAG, PIN_STRAPPING)
   gpio_out_9   OUT    GPIO6 (H1-2)   uyarı (PIN_JTAG)
   gpio_out_10  OUT    GPIO7 (H1-1)   uyarı (PIN_JTAG)
   gpio_out_11  OUT    GPIO8 (H2-10)  uyarı (PIN_STRAPPING)
   gpio_out_12  OUT    GPIO9 (H2-9)   uyarı (PIN_STRAPPING)
   SPI ortak hat: spi_2 yalnız CS alır; SCLK, MOSI, MISO spi_1 ile ortak.
   Not: kart verisi doğrulanmadı: kart satırı (ESP32-C6 Super Mini şematik taraması (topluluk) tarama-2026-04-13, U1 ESP32-C6FH4, s. 1 (topluluk)); H1-1 (GPIO7), H1-2 (GPIO6), H1-3 (GPIO5), H1-4 (GPIO4), H1-5 (GPIO3), H1-6 (GPIO2), H1-7 (GPIO1), H1-8 (GPIO0), H2-4 (GPIO20), H2-5 (GPIO19), H2-6 (GPIO18), H2-8 (GPIO14), H2-9 (GPIO9), H2-10 (GPIO8), PED-1 (GPIO21), PED-2 (GPIO22), PED-3 (GPIO23), BOOT BOOT butonu, LED1 WS2812B RGB LED (0807).

4) Uyarılar (kaynak köşeli parantezde):
   [KART_PED] GPIO21 (PED-1): SuperMini kartında konnektörde değil, yalnız pedde; bağlantı için lehim gerekir. [ESP32-C6 Super Mini şematik taraması (topluluk) tarama-2026-04-13, Microbit Pads (NC), s. 1 (topluluk)]
   [KART_PED] GPIO22 (PED-2): SuperMini kartında konnektörde değil, yalnız pedde; bağlantı için lehim gerekir. [ESP32-C6 Super Mini şematik taraması (topluluk) tarama-2026-04-13, Microbit Pads (NC), s. 1 (topluluk)]
   [KART_PED] GPIO23 (PED-3): SuperMini kartında konnektörde değil, yalnız pedde; bağlantı için lehim gerekir. [ESP32-C6 Super Mini şematik taraması (topluluk) tarama-2026-04-13, Microbit Pads (NC), s. 1 (topluluk)]
   [PIN_JTAG] GPIO4: JTAG pini (P3). [ESP32-C6 Datasheet v1.6, 2.3.5 p.25]
   [PIN_STRAPPING] GPIO4: strapping pini (P3); reset anındaki seviyesi açılış seçeneklerini belirler. [ESP32-C6 Datasheet v1.6, Table 3-1 p.33]
   [PIN_JTAG] GPIO5: JTAG pini (P3). [ESP32-C6 Datasheet v1.6, 2.3.5 p.25]
   [PIN_STRAPPING] GPIO5: strapping pini (P3); reset anındaki seviyesi açılış seçeneklerini belirler. [ESP32-C6 Datasheet v1.6, Table 3-1 p.33]
   [PIN_JTAG] GPIO6: JTAG pini (P3). [ESP32-C6 Datasheet v1.6, 2.3.5 p.25]
   [PIN_JTAG] GPIO7: JTAG pini (P3). [ESP32-C6 Datasheet v1.6, 2.3.5 p.25]
   [PIN_STRAPPING] GPIO8: strapping pini (P3); reset anındaki seviyesi açılış seçeneklerini belirler. [ESP32-C6 Datasheet v1.6, Table 3-1 p.33]
   [KART_PARCA] GPIO8 (H2-10): kart üstü LED1 WS2812B RGB LED (0807) bu pine bağlı. [ESP32-C6 Super Mini şematik taraması (topluluk) tarama-2026-04-13, Super Mini şematik taraması, s. 1 (topluluk)]
   [PIN_STRAPPING] GPIO9: strapping pini (P3); reset anındaki seviyesi açılış seçeneklerini belirler. [ESP32-C6 Datasheet v1.6, Table 3-1 p.33]
   [KART_PARCA] GPIO9 (H2-9): kart üstü BOOT BOOT butonu bu pine bağlı. [ESP32-C6 Super Mini şematik taraması (topluluk) tarama-2026-04-13, Super Mini şematik taraması, s. 1 (topluluk)]

Süre: 83.38 sn (cagri_a 83.38, atayici 0.002)
```

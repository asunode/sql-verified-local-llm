**Spot kontrol — ESP32-C6 Datasheet v1.6**  
Sinan için elle karşılaştırma listesi. Satırlar `veri/dogrulanmis/*.csv` dosyalarından rastgele seçildi (tohum 20261120), her biri farklı bir belge tablosundan. PDF: `veri/kaynak/esp32-c6_datasheet_en.pdf` (v1.6). Sayfa numarası basılı numara, PDF sayfasıyla aynı.  
Sonuç sütununa: ✓ (aynı) ya da PDF'te gördüğünüz değer.  
  
|  |  |  |  |  |  |  |  
| - | - | - | - | - | - | - |  
| **#** |  **Veritabanı tablosu** |  **Veritabanındaki değer** |  **Sayfa** |  **Belge tablosu** |  **PDF'te nereye bakılacak** |  **Sonuç** |  
| 1 |  `pin` |  QFN40 pin 12 = MTCK; At Reset `(boş)`, After Reset `IE, WPU`; kalın küme `IO MUX` |  16 |  Table 2-1 |  Table 2-1 satırı Pin No. 12: Pin Settings ve Pin Function Sets sütunları |    ✓ (aynı) |  
| 2 |  `gpio_islev` |  QFN32 GPIO20 IO MUX F2 = FSPICS4, tür O/T |  21 |  Table 2-5 |  Table 2-5, IO MUX/GPIO Name = GPIO20 satırı, F2 ve yanındaki Type sütunu |     ✓ (aynı) |  
| 3 |  `gpio_islev` |  LP_GPIO6 (GPIO6) LP IO MUX F1 = LP_I2C_SDA |  22 |  Table 2-7 |  Table 2-7, LP IO Name = LP_GPIO6 satırı, F1 sütunu |  ✓ (aynı) |  
| 4 |  `gpio_islev` |  GPIO2 analog F1 = ADC1_CH2 |  23 |  Table 2-9 |  Table 2-9, Analog IO Name = GPIO2 satırı, F1 sütunu |  ✓ (aynı) |  
| 5 |  `cevre_birim_sinyal` |  QFN40 pin 15, RMT = `GPIO9 (P3)` |  26 |  Table 2-10 |  Table 2-10 (yatay sayfa), Pin No. 15 satırı, RMT sütunu |  ✓ (aynı) |  
| 6 |  `cevre_birim_sinyal` |  QFN32 pin 9, LP UART = `LP_UART_CTSN (P1)` (LP_IO_MUX_SABIT) |  27 |  Table 2-11 |  Table 2-11 (yatay sayfa), Pin No. 9 satırı, LP UART sütunu |    ✓ (aynı) |  
| 7 |  `gpio_kisit` |  GPIO9 strapping, varsayılan `Weak pull-up (bit değeri 1)` |  33 |  Table 3-1 |  Table 3-1: Strapping Pin sütununda bu pin (MTMS = GPIO4, MTDI = GPIO5), Default Configuration ve Bit Value |    ✓ (aynı) |  
| 8 |  `flash_pin` |  QFN40 pin 20 SPICS0: Single `CS#`, Dual `CS#`, Quad `CS#` |  32 |  Table 2-16 |  Table 2-16, QFN40 Pin No. 20 satırı |    ✓ (aynı) |  
  
   

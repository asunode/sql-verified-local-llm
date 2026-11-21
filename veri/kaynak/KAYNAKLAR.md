# Kaynak belgeler

**Yayın kopyası notu:** Üçüncü taraf PDF'ler (datasheet, WROOM-1, MuseLab şematiği, Super Mini taraması) bu depoda yok. `python veri/kaynak/indir.py` her belgeyi aşağıdaki resmî adresinden indirir ve SHA-256'yı doğrular. Sayfa metni (`ham_metin` tablosu) yükleyici (`python -m pinsecim.yukle`) tarafından yerelde PDF'ten yeniden üretilir. Aşağıdaki tablolar dosyalar burada dururken yazıldı.

Bu klasördeki belgeler değiştirilmez. Yeni sürüm gelirse ayrı dosya adıyla eklenir ve buraya yeni bir kayıt yazılır. Tablolara giren her bilgi bu kayıtlardaki belge, sürüm ve sayfa ile kaynaklanır.

## ESP32-C6 Series Datasheet

| Alan | Değer |
|---|---|
| Dosya | `esp32-c6_datasheet_en.pdf` |
| Belge adı | ESP32-C6 Series Datasheet (kapsadığı çipler: ESP32-C6, ESP32-C6FH4, ESP32-C6FH8) |
| Sürüm | **v1.6** (kapak sayfası "Datasheet Version 1.6"; her sayfanın altında "ESP32-C6 Series Datasheet v1.6") |
| Yayın tarihi | **2026-11-10** (s. 85, Revision History, v1.6 satırı). PDF meta verisi: CreationDate 2026-11-11 04:59:42 +03 |
| Dil | İngilizce |
| İndirme adresi | `https://www.espressif.com/sites/default/files/documentation/esp32-c6_datasheet_en.pdf` → yönlendirme sonrası `https://documentation.espressif.com/esp32-c6_datasheet_en.pdf` (HTTP 200, `application/pdf`) |
| İndirme zamanı | 2026-11-20 07:56 +03:00 |
| SHA-256 | `c9bf7ece109859a93be2b4d780370478655a7830c0c171cea6670caf8ab3c339` |
| Boyut | 1 003 247 bayt |
| Sayfa sayısı | **87** (pdfinfo). Basılı sayfa numarası PDF sayfa numarasıyla aynı (s. 14, 16, 19, 32, 33'te denetlendi) |

### Pin bilgisi taşıyan bölümler

Sayfalar basılı numaradır (PDF sayfasıyla aynı).

| Konu | Bölüm / tablo | Sayfa |
|---|---|---|
| Pin düzeni QFN40 | 2.1 Pin Layout, Figure 2-1 ESP32-C6 Pin Layout (QFN40, Top View) | 14 |
| Pin düzeni QFN32 | 2.1 Pin Layout, Figure 2-2 ESP32-C6 Pin Layout (QFN32, Top View) | 15 |
| Pin tanımları (genel bakış) | 2.2 Pin Overview: Table 2-1 QFN40 Pin Overview (s. 16), Table 2-2 QFN32 Pin Overview (s. 17, devamı s. 18) | 16–18 |
| IO MUX işlevleri | 2.3 IO Pins (19), 2.3.1 IO MUX Pin Functions: Table 2-3 Peripheral Signals Routed via IO MUX (19), Table 2-4 QFN40 IO MUX Pin Functions (20), Table 2-5 QFN32 IO MUX Pin Functions (21) | 19–21 |
| LP işlevleri | 2.3.2 LP IO MUX Functions: Table 2-6 LP Peripheral Signals Routed via LP IO MUX, Table 2-7 LP IO MUX Functions | 22 |
| Analog işlevler | 2.3.3 Analog Functions: Table 2-8 Analog Signals Routed to Analog Functions, Table 2-9 Analog Functions | 23 |
| GPIO kısıtları | 2.3.4 Restrictions for GPIOs and LP GPIOs (flash pinleri, strapping, USB_D+/-, JTAG, UART0, VDD_SPI) | 24 |
| Çevre birimi pin ataması | 2.3.5 Peripheral Pin Assignment (öncelik P1–P4 ve P3/P4 GPIO listeleri, s. 25): Table 2-10 QFN40 Peripheral Pin Assignment (26), Table 2-11 QFN32 Peripheral Pin Assignment (27) | 25–27 |
| Analog pinler | 2.4 Analog Pins: Table 2-12 Analog Pins | 28 |
| Güç pinleri | 2.5 Power Supply, 2.5.1 Power Pins: Table 2-13 Power Pins, Table 2-14 Voltage Regulators (29); 2.5.2 Power Scheme (29–30); 2.5.3 Chip Power-up and Reset (30–31) | 29–31 |
| Flash pinleri | 2.6 Pin Mapping Between Chip and Flash: Table 2-16 Pin Mapping Between QFN40 Chip and Flash | 32 |
| PSRAM | Belgede PSRAM geçmiyor ("psram" araması 0 sonuç); ESP32-C6 PSRAM arayüzü sunmuyor | — |
| Strapping pinleri | 3 Boot Configurations: Table 3-1 Default Configuration of Strapping Pins (33), Table 3-2 Timing Parameters (34); 3.1 Chip Boot Mode Control, Table 3-3 (34); 3.2 SDIO Sampling and Driving Clock Edge Control, Table 3-4 (35); 3.3 ROM Messages Printing Control, Table 3-5, 3-6 (35–36) | 33–36 |
| USB / JTAG | 3.4 JTAG Signal Source Control, Table 3-7 (36); 4.2.1.6 USB Serial/JTAG Controller (53); USB_D+/- kısıtı 2.3.4 (24) | 24, 36, 53 |
| IO MUX ve GPIO matrisi (işlevsel açıklama) | 4.1.3.1 IO MUX and GPIO Matrix | 41 |
| Toplu pin tablosu ("consolidated pin overview") | ESP32-C6 Consolidated Pin Overview: Table 7-1 QFN40 Pin Overview (79), Table 7-2 QFN32 Pin Overview (80); yatay sayfa | 79–80 |
| Kılıf | 7 Packaging: Figure 7-1 QFN40 (5×5 mm), Figure 7-2 QFN32 (5×5 mm) | 78 |

### Çıkarma adımı için notlar (bu adımda çıkarma yapılmadı)

- Pin tablolarında bazı işlevler **kırmızı ya da sarı vurgulu** (2.3.4, s. 24: kırmızı = flash için ayrılmış, sarı = strapping/USB/JTAG/UART0/VDD_SPI). `pdftotext` rengi taşımaz; bu bilgi ya renkli çıkarmayla ya da 2.3.4 ve 2.3.5'teki metin listelerinden (P3/P4 GPIO listeleri, s. 25) alınmalı.
- Table 2-16 yalnız QFN40 için. 2.6 metnine göre (s. 32) paket içi flash'lı varyantlarda (QFN32) flash pinleri dışarı çıkarılmıyor; tablo yalnız başvuru içindir.
- Toplu pin tabloları (s. 79–80) yatay ve çok sütunlu; metin çıkarmada sütun kayması beklenir. Ana bölümlerdeki tablolarla çapraz denetim için uygun.

## Kart kaynakları (Adım 10b)

Kaynak türü (`kaynak.kaynak_turu`): `uretici_belgesi`, `uretici_semasi`, `uretici_sayfasi`, `satici`, `topluluk`, `kullanici_envanteri`. Yukarıdaki ESP32-C6 datasheet'i `uretici_belgesi`. Yalnız satıcı, topluluk ya da kullanıcı envanterine dayanan satır `dogrulanmadi` sayılır.

### K2 — nanoESP32-C6 v1.0 şematiği

| Alan | Değer |
|---|---|
| Dosya | `nanoESP32-C6_v1.0_sematik.pdf` (depodaki adı `hardware/nanoESP32C6.pdf`) |
| Belge adı | nanoESP32-C6 şematiği (MuseLab); başlık bloğunda "nanoESP32-C6 v1.0" |
| Tür | `uretici_semasi` |
| Sürüm | v1.0 |
| Yayın tarihi | 2023-04-25 (PDF CreationDate; Altium Designer). Depoya ekleniş: commit `b6296ad`, 2023-04-27 |
| İndirme adresi | `https://github.com/wuxx/nanoESP32-C6/blob/master/hardware/nanoESP32C6.pdf` (depo klonuyla da aynı SHA) |
| İndirme zamanı | 2026-11-21 10:56 +03:00 |
| SHA-256 | `a2ca1ca2112cf86c636f11a0bc3066a680c24204666f30e12422666a16f18239` |
| Boyut | 247 001 bayt |
| Sayfa sayısı | 1 |
| Not | Deponun bütün geçmişinde (12 commit, tek dal, etiket yok) başka şematik yok; v0.2 şematiği bulunamadı (Adım 10b). Depodaki ürün fotoğrafının (doc/nanoESP32-C6-2.jpg) arka yüzünde "nanoESP32-C6 v1.0" yazıyor |

### W1 — ESP32-C6-WROOM-1 & WROOM-1U Datasheet

| Alan | Değer |
|---|---|
| Dosya | `esp32-c6-wroom-1_wroom-1u_datasheet_en.pdf` |
| Belge adı | ESP32-C6-WROOM-1 & ESP32-C6-WROOM-1U Datasheet (Espressif) |
| Tür | `uretici_belgesi` |
| Sürüm | v1.4 |
| Yayın tarihi | 2025-12-10 (Revision History, v1.4 satırı, s. 50; PDF CreationDate aynı gün) |
| İndirme adresi | `https://www.espressif.com/sites/default/files/documentation/esp32-c6-wroom-1_wroom-1u_datasheet_en.pdf` → yönlendirme sonrası `https://documentation.espressif.com/esp32-c6-wroom-1_wroom-1u_datasheet_en.pdf` (HTTP 200, `application/pdf`) |
| İndirme zamanı | 2026-11-21 13:06 +03:00 |
| SHA-256 | `163020762fa6d499e0c611c5a13e78ad9d4720b421c6bc5e14e16fc748862b73` |
| Boyut | 938 372 bayt |
| Sayfa sayısı | 52 |
| Kullanılan bölümler | Table 3-1 Pin Definitions (s. 11), Table 1-1 Series Comparison (s. 4), Figure 8-1 Module Schematics (s. 38), Table 4-1/4-3 strapping (s. 12–13) |
| Not | Table 1-1'de N4/N8/N16 var; kapak ve §1.2 metni "up to 8 MB" diyor (belge içi tutarsızlık) |

### S2 — ESP32-C6 Super Mini şematik taraması

| Alan | Değer |
|---|---|
| Dosya | `esp32-c6-supermini_sematik_tarama.pdf` |
| Belge adı | ESP32-C6 Super Mini şematiği, taranmış tek sayfa; üretici ve sürüm yazmıyor |
| Tür | `topluluk` (mischianti.org yazısının bağladığı dosya) |
| Sürüm | yok ("tarama-2026-04-13" adıyla kaydedildi) |
| Yayın tarihi | 2026-04-13 (PDF CreationDate) |
| İndirme adresi | `https://mischianti.org/wp-content/uploads/2026/04/esp32-c6-supermini-board-schematic.pdf` |
| İndirme zamanı | 2026-11-21 10:56 +03:00 |
| SHA-256 | `248cabd39c6cc97c8b99500843a1cb86cc17005c2e59a0e10f746b5622db2b8a` |
| Boyut | 337 120 bayt |
| Sayfa sayısı | 1 |

### E1 — Kullanıcı envanteri

| Alan | Değer |
|---|---|
| Dosya | `kullanici_envanteri_2026-11-21_kamu.md` (**kısaltılmış kamu sürümü**) |
| Belge adı | Sinan'ın kart envanteri; yalnız kart verisinin kullandığı alanlar (kart modeli, sürüm notu, flash), satır sırası korundu |
| Tür | `kullanici_envanteri` |
| Sürüm / tarih | 2026-11-21 |
| SHA-256 | `82c739f095c55a03685086aa2cd27fd21c495c952159b95525df3270f5f500b7` |
| Özgün | `kullanici_envanteri_2026-11-21.md`, SHA-256 `b393f118a13ffaad29d58dca1d96a219a2b4edbda156144f02cc3b93bcba0a87` (Adım 10b görev metninden aynen; kişisel kurulum bilgisi içerdiği için yayımlanmadı). `doc/` altındaki eski belgelerde geçen `b393f118a13f` özgün dosyayı gösterir |
| Not | Kart üstünden doğrulanmadı. "v0.2" ifadesi kart sürümü olarak verildi; ESP32-C6 çip revizyonları da v0.0/v0.1/v0.2 (datasheet Table 1-1), esptool çıktısındaki "revision v0.2" ile karışmış olabilir (doğrulanmadı) |

K3 (`uelectronics.com` satıcı şematiği) HTTP 403 verdi, okunamadı; kaydedilmedi.

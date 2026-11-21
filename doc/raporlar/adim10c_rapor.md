# Adım 10c raporu: kart düzeyi atama, SPI çoklu CS, RMT, rapor dosyası (2026-11-21)

Adım 10b raporu kabul edildi. Bu adım pilotu bitirme yönündeki son geliştirme adımı; sonrası Adım 11 (v5 ölçümü) ve Adım 12 (kapanış raporu).

İstem dosyası değişmedi (`ihtiyac_sistem.txt` 3ff741e27c2e). Modele giden arayüz listesine iki satır eklendi (RMT_TX, RMT_RX; aşağıda).

Commit'ler:
- `1abac04`: SPI çoklu CS, RMT, küçük düzeltmeler
- `c651b06`: kart düzeyi atama
- `1704450`: `--rapor`
- `e9bab31`: dondurma öncesi
- `8f5f6de`: ölçüm, dondurma sonrası, sınav cümlesi, örnek rapor
- rapor ve belgeler commit'i (WORKLOG)

## Kart atama (kural, örnek çıktı: iki kartta birer set dışı istek)

### Kural

`--kart` verildiğinde hat, kartın atama bilgisini isteğe ekler (`istek["kart"]`, `kart.atama_bilgisi`):
- konnektör ve ped pinleri, etiketleriyle ("J1-4", "PED-2");
- GPIO'ya bağlı kart üstü parçalar (LED, WS2812, buton);
- USB-UART köprüleri;
- her satırda doğrulama durumu ve kaynak.

Atayıcı ve denetleyici aynı bilgiyi kullanır. Denetleyici atayıcının sonucunu da denetlediği için iki taraf tutarlı kalır.

1. **Aday pinler:** çip kurallarından geçen adaylar ile karta çıkan GPIO'ların kesişimi. Atayıcı üç aşamada arar:
   - (1) konnektör pinleri, kart üstü parçaya bağlı olmayanlar;
   - (2) yetmezse pedler de;
   - (3) o da yetmezse parçaya bağlı pinler de.

   İlk çözüm bulunan aşamanın sonucu verilir. Her aşamanın içinde çip düzeyindeki "en az uyarılı pin" araması aynen çalışır.
2. **Dışarı çıkmayan GPIO atanmaz.** Denetleyicide KART_PIN_YOK (hata), atayıcıda aday dışı.
   - Gerçek iki kartta da çip kurallarından geçip karta çıkmayan GPIO yok: nanoESP32-C6'da GPIO14 pakette yok, GPIO24–30 flash; Super Mini bütün QFN32 GPIO'larını konnektöre ya da pede çıkarıyor. Bu yüzden kural sahte bir kart bilgisiyle sınandı.
3. **Ped:** yalnız konnektör pinleri yetmezse kullanılır; kullanılırsa KART_PED uyarısı ("yalnız pedde; bağlantı için lehim gerekir").
4. **Kart üstü parçaya bağlı pin** (nanoESP32-C6: GPIO8 D2 WS2812B, GPIO9 S1 BOOT; Super Mini: GPIO8 LED1 WS2812B, GPIO9 BOOT, GPIO15 PD2 mavi LED):
   - Son çare olarak kullanılır; kullanılırsa parçayı adıyla anan KART_PARCA uyarısı verilir ("kart üstü D2 WS2812B RGB LED bu pine bağlı").
   - Kullanıcının tercihi bu pine düşerse K-7 geçerli: tercih uygulanır (kilit her aşamada yerinde kalır) ve aynı uyarı verilir.
   - Tercih bir kural ihlaline takılırsa mevcut neden + öneri + ALTERNATİF akışı çalışır.
5. **Tercih karta çıkmayan bir pine düşerse:** KART_PIN_YOK nedeni ("GPIO21: … kartında konnektöre ya da pede çıkmıyor."), öneri ("Kartta çıkan bir pin seç: …") ve kart içinde alternatif atama verilir.
6. **USB ve UART0** mevcut bağlam kurallarıyla çalışır.
   - Kartta USB-UART köprüsü varsa (nanoESP32-C6: U2 CH343P), UART0 pinine yapılan atamada KART_UART_KOPRU uyarısı verilir.
   - UART0 konsolken o pine düşen tercih reddedilir; ret nedenine de "Kartta U2 CH343P USB-UART köprüsü UART0'a bağlı." eklenir.
7. **Çıktı:**
   - Pin adının yanında kart etiketi yazılır: "GPIO4 (J1-4)".
   - "3) Atama" altında kart düzeyi özeti çıkar ("Kart düzeyi: SuperMini; adaylar karta çıkan pinler (17 konnektör pini, 5 ped). Ped: …; kart üstü parça pini: …").
   - Atamada `dogrulanmadi` kart satırı kullanıldıysa not düşülür: "Not: kart verisi doğrulanmadı: kart satırı (…); H1-8 (GPIO0), …".
   - Adım 10b'deki `not.kart_atama` ("atama çip düzeyinde") kaldırıldı.
8. **`--kart` yoksa** atama çip düzeyinde kalır. Ölçüm kartsız yapıldı.

Kurallar kural tablosunda (`kural_verisi.KURALLAR`, kategori `yapisal`, kaynak "kart verisi (Adım 10c)"): KART_PIN_YOK (hata), KART_PED, KART_PARCA, KART_UART_KOPRU (uyarı). Ped bilgisi `kart_pin.tur` (konnektor / ped) sütununda (`sql/013`).

Testler (`testler/test_10c.py`):
- aşamalar konnektör → ped → parça ve kart önekli `mumkun_degil`;
- dışarı çıkmayan pine tercih ve atama;
- tercihin parça pinine düşmesi;
- nanoESP32-C6'da UART0 köprü uyarısı ve ret nedeni;
- gerçek Super Mini'de 10 çıkışın parça ve ped pinlerine dokunmaması.

### Örnek çıktılar

Set dışı iki istek (kendi cümlelerim; setlerde yok), birer kez.

**nanoESP32-C6 v0.2** (`--kart "nanoESP32-C6 (v0.2)"`): «Bir NeoPixel halkası, bir kızılötesi alıcı ve üç peltier sürücüsü bağlayacağım.»

```
İstek: Bir NeoPixel halkası, bir kızılötesi alıcı ve üç peltier sürücüsü bağlayacağım.
Kart: nanoESP32-C6-v0.2 · Paket: QFN40 · bağlam: usb_serial_jtag=evet, uart0_konsol=evet, jtag_pinleri=hayır, harici_flash_beslemesi=hayır

1) İhtiyaçlar (model, 1. turda geçti):
   - RMT_TX    ×1  «Bir NeoPixel halkası»  [model çıkarımı — kontrol edin]
   - RMT_RX    ×1  «bir kızılötesi alıcı»  [model çıkarımı — kontrol edin]
   - GPIO_OUT  ×3  «üç peltier sürücüsü»  [model çıkarımı — kontrol edin]

3) Atama (kod atayıcı):
   Kart düzeyi: nanoESP32-C6-v0.2; adaylar karta çıkan pinler (23 konnektör pini). Ped: kullanılmadı; kart üstü parça pini: kullanılmadı.
   Sonuç: atandı
   İhtiyaç      Sinyal GPIO           Pinin durumu
   rmt_tx_1     OUT    GPIO0 (J1-8)   serbest
   rmt_rx_1     IN     GPIO1 (J1-9)   serbest
   gpio_out_1   OUT    GPIO2 (J6-2)   serbest
   gpio_out_2   OUT    GPIO3 (J6-3)   serbest
   gpio_out_3   OUT    GPIO10 (J1-11) serbest
   Not: kart verisi doğrulanmadı: kart satırı (Kullanıcı envanteri (Sinan) 2026-11-21, envanter satırı 1, s. 1 (kullanici_envanteri)); J1-8 (GPIO0), J1-9 (GPIO1), J1-11 (GPIO10), J6-2 (GPIO2), J6-3 (GPIO3).

4) Uyarı yok.
```

- Model NeoPixel için RMT_TX, kızılötesi alıcı için RMT_RX çıkardı (yeni eş adlar modele gitmez; yalnız arayüz tanımları).
- Bütün pinler 1. aşamada konnektörden; WS2812B (GPIO8) ve BOOT (GPIO9) kullanılmadı.
- v0.2 satırları `dogrulanmadi` olduğu için not çıktı.

**Super Mini** (`--kart SuperMini --rapor …`): «İki basınç dönüştürücüsünü aynı SPI hattından okuyacağım ve on iki vantilatörü ayrı ayrı açıp kapatacağım.»

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
```

- Model 1. turda "aynı SPI hattından" için SPI ×1 verdi. SAYI_UYUSMAZ ("iki" = 2) yakaladı, 2. turda SPI ×2. Atayıcı bunu tek hat ve iki CS olarak atadı (T-68).
- 4 + 1 + 12 = 17 sinyal. Konnektörde parçasız ve bağlamca kullanılabilir 12 GPIO var (GPIO0–7, 14, 18–20; GPIO16/17 UART0 konsol). Pedlerde 3 (GPIO21–23; PED-4/5 = GPIO12/13 USB). 15 yetmediği için aşama 3'e geçildi ve parça pinleri GPIO8 (WS2812B) ile GPIO9 (BOOT) uyarılı kullanıldı. Mavi LED pini GPIO15 gerekmedi.
- Tablodaki "Pinin durumu" sütunu yalnız çip kurallarının durumunu gösterir: ped satırları "serbest" görünür, KART_PED uyarısı yalnız 4) bölümünde. Bu bir gösterim eksiği; açık kalanlarda.
- Parça adı iki kez geçiyor ("BOOT BOOT butonu": ad + açıklama). Kozmetik; açık kalanlarda.

## SPI çoklu CS

- **Kural (L-1):** Çağrı A'nın SPI ×N çıktısı atayıcıda tek SPI2 hattı olarak yorumlanır: SCLK, MOSI ve MISO ilk SPI ihtiyacında, her cihazın ayrı CS'i var. İstem değişmedi.
  - Veritabanı: `arayuz_tanimi.ortak_hat_secim` (`sql/012`); SPI için "CS".
  - Yuva hesabı `PinVerisi.yuva_sinyalleri`: ilk örnek bütün sinyaller, sonrakiler yalnız seçim sinyali.
- **CS sınırı, kaynaklı:** ESP32-C6 Datasheet v1.6, 4.2.1.2 SPI Controller, s. 51: "Provides six FSPICS… pins for connection with six independent SPI slaves".
  - Yeni `cevre_adet` satırı `SPI2_CS` = 6; SPI'nin `adet_adi` `SPI2` → `SPI2_CS`. `SPI2` satırı (yalnız SPI2 kullanıcıya açık) duruyor.
- **Taşma:** N > 6 ise `mumkun_degil`: "SPI ×7: tek hatta her cihaz ayrı CS ister; 7 CS gerekiyor, en çok 6 var (SPI2_CS; ESP32-C6 Datasheet v1.6, 4.2.1.2 p.51)".
- **Denetleyici:**
  - İkinci ve sonraki SPI örneklerinde yalnız CS zorunlu (EKSIK_SINYAL buna göre).
  - Bir atama (ör. Çağrı B) ikinci örneğe ortak sinyali ilk örnekle aynı pinden verirse CAKISMA sayılmaz.
- **Tercih:** "SPI SCLK → GPIO21" iki SPI cihazında ortak saate uygulanır (test edildi).
- **Komut satırı:** "SPI ortak hat: spi_2 yalnız CS alır; SCLK, MOSI, MISO spi_1 ile ortak." satırı.
- **Sınır:** Çağrı B'nin atama istemi (`--model-ata`) ortak hattı bilmiyor; o yol değişmedi.
- **Önceki davranış:** SPI ×2 her zaman `mumkun_degil`'di (SPI2 adedi 1, ADET_ASIMI). Görülmüş setlerde kabul listesinde SPI ×N olan istek yok.

## RMT_TX (kaynak, kural, istem farkı)

**Kaynak:**
- ESP32-C6 Datasheet v1.6, 4.2.1.11 Remote Control Peripheral, s. 56:
  > Four channels for sending and receiving infrared remote control signals; Independent transmission and reception capabilities for each channel
- Table 2-10/2-11 (s. 26–27) RMT sütunu: RMT sinyalleri P2/P3 öncelikli GPIO'lara gidiyor. Veritabanında `cevre_birim_sinyal` RMT satırları zaten vardı.
- Belge alma yeteneğini açıkça yazdığı için görev koşuluna göre RMT_RX de eklendi.

**Kural:**
- RMT_TX (OUT) ve RMT_RX (IN): `yonlendirme` GPIO_MATRISI, `cevre_birim` RMT. Adaylar RMT sütunundaki GPIO'lar, sonra çip pin kuralları.
  - QFN32: GPIO0–9, 12–23.
  - QFN40: GPIO0–13, 15–30 (flash pinleri pin kuralıyla elenir).
- Yeni `cevre_adet` satırı `RMT` = 4. RMT_TX ve RMT_RX aynı dört kanalı paylaşır; 5 RMT örneği `mumkun_degil`.
- Teknik başvuru kılavuzu okunmadı; kanalların TX/RX dağılımı (C6'da kanal başına sabit yön olabilir) doğrulanmadı.
- Eş adlar (`arayuz_es_adi`, cevaplayıcı ve DIGER_IHTIYAC_IZI için): "ws2812", "neopixel", "adreslenebilir led" → RMT_TX.

**İstem farkı** (modele giden sistem metni; istem dosyası aynı):

```
+- RMT_TX: OUT; One RMT transmit channel: addressable LED strip (WS2812, NeoPixel) data line or infrared transmitter.
+- RMT_RX: IN; One RMT receive channel: infrared remote control receiver.
```

- Arayüz listesinin sonuna (LP_UART'tan sonra) eklendi; mevcut satırların sırası ve metni aynı.
- JSON şemasında `arayuz` enum'larına (ihtiyaçlar ve pin tercihleri) iki ad eklendi; tercih sinyal enum'una yeni sinyal adı girmedi (OUT, IN zaten vardı).
- Kural ve örnek metinlerine dokunulmadı.

## Küçük düzeltmeler

1. **SAYI_YARIM** yalnız dayanaktaki sayı değeri metindeki tam değerden farklıysa verilir. "Bir çift" ile "çift" (2 = 2) artık uyarmıyor (X17 türü); "On iki zil" içinde "iki zil" (2 ≠ 12) uyarmaya devam ediyor.
2. **`cevap.kart_eksik` örneği** pakete uyan ilk kartla üretiliyor: `durum_mesaji.ornek_tr` artık "--kart {kart}" şablonu. QFN40 → "--kart nanoESP32-C6-v0.2", QFN32 → "--kart SuperMini".
3. **`cevap.kart_verisi_yok`** satırı ve kullanılmayan `not.kart_atama` satırı kaldırıldı (`durum_mesaji` 15 → 13 satır).
4. **Y29'daki eski konum uyarısı** (DIGER_PIN_TERCIH_IZI, GPIO2) kodda olduğu gibi kaldı. Bu ölçümde çıkmadı: model Y29'da GPIO3'ü artık pin_tercihleri'ne yazıyor, GPIO2 tercihsiz bir ihtiyacın cümlesinde kalmıyor (Ölçüm). Davranış kapanış raporunda bilinen davranış olarak yazılacak.

Testler: `test_10c.py` (SAYI_YARIM, kart_eksik örneği, mesajın kaldırılması).

## Rapor dosyası (örnek)

`--rapor YOL`:
- Komut satırı çıktısı değişmeden ekrana basılır; aynı metin Markdown dosyasına kod bloğu içinde yazılır.
- Dosyanın başında: tarih, kart / paket / bağlam, model ve ayarları (gemma4:12b-it-qat, num_gpu 0, temperature 0, seed 42, num_ctx 8192, think kapalı), istem dosyalarının SHA-256 başları, istemleri eşleşen en son dondurma kaydı (o kayıttan sonra değişen dondurulmuş dosyalar varsa adlarıyla), veritabanındaki kaynak listesi (belge, sürüm, tür, SHA-256 başı).
- Modül `src/pinsecim/rapor.py`.
- Test: dosyadaki kod bloğu ekran çıktısıyla bayt bayt aynı; üst bilgi alanları var.

Örnek: `doc/raporlar/adim10c_ornek_rapor.md` (yukarıdaki Super Mini isteği). Kod bloğu ekran çıktısıyla aynı (diff ile denetlendi). Dondurma satırı: "`2026-11-21_adim10c_dondurma` (istemler aynı; dondurulan dosyaların hepsi aynı)". Kaynak tablosunda beş belge (datasheet, nanoESP32-C6 şematiği, WROOM-1, Super Mini taraması, kullanıcı envanteri).

## Ölçüm (önce/sonra, kayan çıktılar)

- Dondurma `doc/olcum/2026-11-21_adim10c_dondurma.md`: öncesi `e9bab31`, sonrası aynı.
- Koşu: kartsız (setler çip düzeyi), tekrar yok. Sonuçlar `doc/olcum/2026-11-21_adim10c_v4_sonuc.md` ve `doc/olcum/2026-11-21_adim10c_v3_sonuc.md`, ham `…_adim10c_{v4,v3}_ham.jsonl`.
- Testler: proje 299 geçti, çekirdek 19 geçti (ölçümden önce).

| Ölçüt | 10b | 10c | Kabul |
|---|---|---|---|
| v4 Çağrı A doğru | 35/36 (Y29) | **36/36** | ≥ 35/36: karşılandı |
| v4 uçtan uca | 35/36 | 36/36 | |
| v4 tur 1 / 2 / 3 | 31 / 5 / 0 | 31 / 5 / 0 | |
| v3 Çağrı A doğru (resmî) | 43/45 (X34, X35) | **42/45** (X24, X34, X35) | ≥ 43/45: **karşılanmadı** |
| v3 uçtan uca | 43/45 | 42/45 | |
| v3 tur 1 / 2 / 3 | 35 / 9 / 1 | 34 / 10 / 1 | |
| Atayıcı kararı değişen istek | — | 0 / 81 | |
| Yazılım hatası (atayıcı sonucunda denetim hatası) | 0 | 0 | |

**v3 kabul ölçütü karşılanmadı.** Tek yeni yanlış X24, «Bir WS2812 LED şerit süreceğim.»:
- 10b'de model GPIO_OUT ×1 veriyordu; 10c'de RMT_TX ×1 veriyor. İkisinde de atama atandi, GPIO0.
- Setin kabul listesi: tamam [GPIO_OUT], emin_degilim, desteklenmiyor. RMT_TX liste yazıldığında yoktu.
- Görevin kendisi WS2812'yi RMT_TX olarak tanımlıyor (eş ad ve arayüz tanımı). Bu yüzden çıktı teknik olarak daha doğru: WS2812 zamanlaması RMT ister, düz GPIO_OUT yetmez.
- Set ve kabul listesi değiştirilmedi (kural). X24'ün kabul listesine RMT_TX eklenip eklenmeyeceği Web AI hükmüdür. Eklenirse v3 resmî 43/45 olur (X34/X35 10a hükmüyle zaten doğru sayılıyor).

### Kayan Çağrı A çıktıları (son tur ham yanıtı 10b'den farklı olanlar)

Sistem metnindeki iki satır v4'te 5, v3'te 8 isteğin son yanıtını, 1 isteğin (X08) yalnız ara turunu değiştirdi. Kalan 67 isteğin ilk ve son turunun ham yanıtı 10b ile bayt bayt aynı.

| Set | İstek | Ne kaydı | Karar değişti mi | Kontrol | Sonuç |
|---|---|---|---|---|---|
| v4 | Y02 | tercih dayanakları "GPIO10" → "GPIO10'da" (ve 11) | hayır (atandi) | gerek yok | doğru, aynı |
| v4 | Y06 | tercih dayanağı "GPIO10'a bağlayacağım" → "GPIO10'a" | hayır (tercih_uygulanamadi) | gerek yok | doğru, aynı |
| v4 | Y10, Y11 | tercih dayanağı "GPIO14'te olacak" → "GPIO14" | hayır | gerek yok | doğru, aynı |
| v4 | Y29 | GPIO3 diger_pin_bahisleri → pin_tercihleri; GPIO2 bahis olarak kaldı | evet: atama GPIO0 → GPIO3 | — | **düzeldi** (10a'dan beri yanlıştı); DIGER_PIN_TERCIH_IZI uyarıları kalktı |
| v3 | X04 | "iki LED" kaynağı model_cikarimi → istekte_acik | hayır | denetlenmiyor | kabulde kaynak yok; yanlış etiket, zararsız |
| v3 | X07 | "Başta SD kart da düşünmüştüm ama vazgeçtim." diger_ifadeler'den düştü (hiçbir listede yok) | hayır | **kaçtı**: cümlenin bir listede olması denetlenmiyor | sonuç doğru (cümle olumsuz); kayıp sessiz |
| v3 | X08 | 1. turda CAN cümlesi baglam_ifadeleri'nde | hayır | BAGLAM_KONUSUZ yakaladı, 2. tur diger_ifadeler | doğru, +1 tur |
| v3 | X11 | "debug için değil" artık hiçbir listede değil (10b'de 1. tur bağlam, 2. tur diger) | hayır | BAGLAM_KONUSUZ turu gerekmedi; düşme denetlenmiyor | doğru, −1 tur; kayıp sessiz (ifade ihtiyaç dayanağının içinde) |
| v3 | X15 | 1. tur dayanak "4'lü röle modülü" (sözcük içinde biter) | hayır | DAYANAK_SINIRI yakaladı, 2. tur "modülünü" | doğru, +1 tur |
| v3 | X24 | GPIO_OUT → RMT_TX | hayır (atandi, GPIO0) | arayüz geçerli, denetlenecek bir şey yok | resmî puanda yanlış (yukarıda) |
| v3 | X27 | 1. tur UART0 cümlesi diger_ifadeler'de | hayır | DIGER_BAGLAM yakaladı, 2. tur baglam_ifadeleri | doğru, +1 tur |
| v3 | X31 | "Altı analog sensör" kaynağı model_cikarimi → istekte_acik | hayır (mumkun_degil) | denetlenmiyor | zararsız |
| v3 | X43 | 10b'de 1. tur 3 BAGLAM_KONUSUZ; 10c'de 1. turda doğru diger_ifadeler | hayır | gerek kalmadı | doğru, −1 tur |

Özet: karar değişen tek istek Y29 (düzeldi). Bir istek resmî puanda yanlışa döndü (X24; çıktı daha doğru). Ara turlarda 3 yeni hata kontrolce yakalandı (X08, X15, X27). İki isteğin konusuz cümlesi sessizce düştü (X07, X11); ikisi de sonucu etkilemiyor ama denetimde boşluk.

### SPI ×N ve RMT

- **SPI ×N:** v4 ve v3'te hiçbir istekte Çağrı A SPI ×2 ya da üstü vermedi (10b'de de). Atayıcı kararı SPI ×N yüzünden değişen istek yok.
- **RMT:** RMT_TX yalnız X24'te çıktı. RMT_RX hiçbir istekte çıkmadı.

### Sınav cümlesi

- Üç biçim birer kez (`doc/dogrulama/bagimsiz_sinav.md`, "Adım 10c sistemiyle").
- Sistem metni değiştiği halde Çağrı A ham yanıtı 10a/10b ile birebir aynı (dcf38030…).
- Çıktıdaki tek fark kartsız biçimde: `cevap.kart_eksik` örneği «--kart SuperMini» yerine «--kart nanoESP32-C6-v0.2» (küçük düzeltme 2).

## Açık kalanlar

### Pilot sonu bilinen sınırlar

1. **Y29 eski konum uyarısı:** DIGER_PIN_TERCIH_IZI, bir cümlede eski ve yeni konum geçerse eski konum için de uyarır (10b'de GPIO2 yanlış alarmı). 10c ölçümünde model yanıtı değiştiği için çıkmadı; davranış kodda duruyor.
2. **L-2:** I2S tek denetleyici; tam çift yönlü kullanım modellenmedi.
3. **Çağrı B ortak SPI hattını bilmiyor.** `--model-ata` yolunda SPI ×N için B her cihaza ayrı hat vermeye çalışır; denetleyici ortak sinyali kabul eder ama B'ye öğretilmedi.
4. **RMT kanal yönü:** RMT_TX ve RMT_RX dört kanalı ortak sayıyor. C6'da kanalların sabit TX/RX ayrımı olabilir; teknik başvuru kılavuzu okunmadı. Örneğin 3 TX + 2 RX bugün "5 > 4" diye reddedilir, ama 4 TX'in olup olmadığı doğrulanmadı.
5. **Kart verisi doğrulanmamış:** nanoESP32-C6 v0.2 (v1.0 şematiğinden aktarılmış; "v0.2" çip revizyonu olabilir, Sinan'ın kart arkası kontrolü bekliyor) ve Super Mini (topluluk taraması). Her kartlı çıktıda not düşülüyor.
6. **nanoESP32-C6 J5 USB:** GPIO12/13 kartın USB konnektörüne bağlı, ama `kart_parca`'da bir girdi yok. Bugün USB bağlamı (usb_serial_jtag=evet) bu pinleri zaten eliyor; `--no-usb` ile seçilebilirler ve kart uyarısı çıkmaz.
7. **Konusuz cümlenin düşmesi denetlenmiyor** (X07, X11): model bir cümleyi hiçbir listeye yazmazsa ses çıkmıyor.
8. **"can" sözcük sorunları:** eş ad harfe duyarlı (T-65) ama "CAN" büyük harfle yazılmış Türkçe bir sözcükte hâlâ eşleşir.
9. **DAYANAK_SINIRI ve BAGLAM_KONUSUZ turları:** küçük sistem metni değişiklikleri bile ara turları kaydırıyor (X08, X15, X27, X22). Sonuç doğru kalıyor, süre uzuyor.
10. **İletiler kodda:** atayıcının mumkun_degil ve SPI taşma iletileri, kart özeti, ortak hat satırı `atayici.py` ve `__main__.py`'de duruyor, `durum_mesaji` tablosunda değil.
11. **Kaynak etiketi (model_cikarimi / istekte_acik) denetlenmiyor:** X04 ve X31'de yanlış etiket; karar etkilenmiyor.

### Sonraki tur

1. X24 kabul listesi: RMT_TX'in kabul edilip edilmeyeceği (Web AI hükmü).
2. Atama tablosunun "Pinin durumu" sütununa kart uyarıları (KART_PED, KART_PARCA) eklenmesi; bugün yalnız 4) bölümünde.
3. Kart parça adının tekrarı ("BOOT BOOT butonu"): ad ile açıklama aynı başlıyorsa tek yazılması.
4. Teknik başvuru kılavuzundan RMT kanal yönleri; gerekirse RMT_TX / RMT_RX ayrı adetler.
5. Çağrı B'ye ortak hat bilgisi (istemde değil, isteğin yuva listesinde; istem değişmez kuralı korunarak).
6. Cümle kapsama denetimi: her cümle ya bir ihtiyaç / tercih dayanağında ya da bir listede olmalı (X07, X11 türü).
7. nanoESP32-C6 J5 USB'nin `kart_parca`'ya eklenmesi (kaynak: K2 şematiği).
8. Kodda duran iletilerin `durum_mesaji`'na taşınması.

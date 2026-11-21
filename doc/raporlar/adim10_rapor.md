# Adım 10 raporu — soru ayrımı, kart kaynakları (2026-11-21)

Karar K-8 (Sinan; Web AI netleştirmesi): soruyu model yalnız ayırır ve kapalı bir konu listesine bağlar, cevabı kod veritabanından üretir. Kart verisi bu adımda yüklenmedi; yalnız kaynakları araştırıldı (yükleme Adım 10b).

Commit'ler: `2c62781` (CLI izi), `62f1a2a` (sınav kaydı, K-8, L-5, DEVAM), `7867d5e` (tablolar), `b9686dd` (soru ayrımı), `f83c622` (dondurma öncesi), ölçüm ve rapor commit'leri (WORKLOG).

## Kart kaynakları

Kaynak türleri: üretici şematiği / üretici sayfası / satıcı sayfası / topluluk. Yalnız satıcı ya da topluluk kaynağına dayanan satır **doğrulanmadı** sayıldı. İndirilen PDF'ler depoya konmadı (kaynak onayı Adım 10b'de); SHA-256 aşağıda.

| Kısa ad | Adres | Tür | Not |
|---|---|---|---|
| K1 | https://github.com/wuxx/nanoESP32-C6 (README) | üretici sayfası (MuseLab GitHub deposu) | Çince README; ayrı ürün sayfası bulunamadı |
| K2 | https://github.com/wuxx/nanoESP32-C6/blob/master/hardware/nanoESP32C6.pdf | üretici şematiği | "nanoESP32-C6 v1.0", Altium, 2023-04-25, 1 sayfa; SHA-256 `a2ca1ca2112cf86c636f11a0bc3066a680c24204666f30e12422666a16f18239` |
| K3 | https://uelectronics.com/wp-content/uploads/2023/11/nanoESP32C6-Esquematico.pdf | satıcı sayfası | HTTP 403; **okunamadı** |
| S1 | https://mischianti.org/esp32-c6-supermini-high-resolution-pinout-datasheet-schema-and-specs/ | topluluk | pin çıkış görseli dosya adı "MakerGO"; okuyucu yorumlarında sürüm farkı iddiası |
| S2 | https://mischianti.org/wp-content/uploads/2026/04/esp32-c6-supermini-board-schematic.pdf | topluluk (S1'in bağladığı tarama) | tek sayfa taranmış şematik, üretici ve sürüm yazmıyor, 2026-04-13; SHA-256 `248cabd39c6cc97c8b99500843a1cb86cc17005c2e59a0e10f746b5622db2b8a` |
| S3 | https://www.espboards.dev/esp32/esp32-c6-super-mini/ | topluluk | "by Generic"; pin tablosu |
| S4 | https://esp32.co.uk/esp32-c6-supermini-pinout-safe-gpios/ | topluluk | "several vendors"; sürüm farkları uyarısı |

Super Mini için üretici, resmî ürün sayfası ve üretici şematiği **bulunamadı** (S4: "There is no single official Espressif ESP32-C6 SuperMini specification").

### nanoESP32-C6 (MuseLab)

| Bilgi | Değer | Kaynak | Durum |
|---|---|---|---|
| Üretici | MuseLab | K1 | kaynak_belge |
| Sürüm | v1.0 (başka sürüm bulunamadı) | K2 başlığı | kaynak_belge |
| Çip / modül | **ESP32-C6-WROOM-1 modülü** (U1); çıplak çip değil | K2 | kaynak_belge |
| Modül içindeki çip ve flash | modül datasheet'i okunmadı; QFN40 olduğu ve flash boyutu bulunamadı | — | doğrulanmadı |
| Modül → GPIO | modül pin adı IOn = net adı GPIOn: 1 GND, 2 3V3, 3 EN, 4 IO4, 5 IO5, 6 IO6, 7 IO7, 8 IO0, 9 IO1, 10 IO8, 11 IO10, 12 IO11, 13 IO12, 14 IO13, 15 IO9, 16 IO18, 17 IO19, 18 IO20, 19 IO21, 20 IO22, 21 IO23, 22 NC, 23 IO15, 24 RXD0, 25 TXD0, 26 IO3, 27 IO2, 28 GND, 29 EPAD | K2 | kaynak_belge (şematik); modül datasheet'iyle karşılaştırılmadı |
| WS2812 | D2 WS2812B, DIN ← Q2 BSS138 seviye çevirici ← **GPIO8**; VDD 3V3; DIN tarafı 10K ile 5V'a, GPIO8 tarafı 10K ile 3V3'e çekili | K2; K1 "RGB LED" | kaynak_belge |
| Güç LED'i | D3 kırmızı, 3V3 → R8 10K; şematikte soluk (gri) çizili, takılmamış olabilir | K2 | doğrulanmadı (takılı mı belli değil) |
| Kullanıcı LED'i | şematikte yok | K2 | kaynak_belge |
| Butonlar | S1 → **GPIO9** (GND'ye; BOOT), S2 → **CHIP_PU** (RST) | K2 | kaynak_belge |
| Otomatik indirme | CH343P DTR/RTS → Q1 (LMBT3904 ×2) → CHIP_PU ve GPIO9 | K2 | kaynak_belge |
| USB | iki USB-C: J5 → 22R → ESP32C6_USB_N/P → IO12/IO13 (**GPIO12/13, yerel USB Serial/JTAG**); J4 → **CH343P** (U2) USB-UART: CH343 RXD ← TXD0, TXD → RXD0 | K2; K1 | kaynak_belge |
| UART0 | TXD0 = GPIO16, RXD0 = GPIO17 (şematikte J6 yanında yan etiket) | K2 | kaynak_belge |
| Besleme | iki konnektörün VBUS'ı → F1 sigorta → AMS1117-3.3 | K2 | kaynak_belge |
| Pin çıkışı J1 (15) | 1 GND, 2 3V3, 3 CHIP_PU, 4 GPIO4, 5 GPIO5, 6 GPIO6, 7 GPIO7, 8 GPIO0, 9 GPIO1, 10 GPIO8, 11 GPIO10, 12 GPIO11, 13 GPIO12, 14 GPIO13, 15 5V | K2 | kaynak_belge |
| Pin çıkışı J6 (15) | 1 GND, 2 GPIO2, 3 GPIO3, 4 TXD0, 5 RXD0, 6 GPIO15, 7 GPIO23, 8 GPIO22, 9 GPIO21, 10 GPIO20, 11 GPIO19, 12 GPIO18, 13 GPIO9, 14 GND, 15 5V | K2 | kaynak_belge |
| Kart üstündeki etiket yazıları (silkscreen) | bulunamadı (şematikte net adları var, kart üstü yazı yok) | — | doğrulanmadı |

GPIO14 ve flash pinleri (GPIO24–30) dışarı çıkmıyor; veritabanında QFN40'ta GPIO14 olmamasıyla uyumlu.

### ESP32-C6 Super Mini

| Bilgi | Değer | Kaynak | Durum |
|---|---|---|---|
| Üretici | bulunamadı (çok satıcılı; S1 görsel adı "MakerGO", S3 "Generic") | S1, S3, S4 | doğrulanmadı |
| Çip | U1 **ESP32-C6FH4** (QFN32, gömülü 4 MB flash; veritabanındaki `cip` satırıyla uyumlu); modül yok | S2 | doğrulanmadı |
| Şematikteki çip pinleri | pin 14 GPIO8, 15 GPIO9, 16 GPIO12 (USBD_N), 17 GPIO13 (USBD_P), 19 GPIO15, 21 U0TXD, 22 U0RXD, 23–28 GPIO18…23: datasheet `pin` tablosuyla (QFN32) aynı | S2 + veritabanı | çip sembolü tutarlı; kart bağlantısı doğrulanmadı |
| WS2812 | LED1 WS2812B (0807), DIN ← **GPIO8** (net RGB_CTRL), VDD 3V3 | S2; metinde S1, S3, S4 | doğrulanmadı |
| Durum LED'i | PD2 mavi: **GPIO15** → PR9 1K → LED → GND, yani **aktif yüksek** | S2; metinde S1, S3, S4 (seviye yazmıyor) | doğrulanmadı |
| Şarj LED'i | PD4 yeşil, TP4054 CHRG çıkışı; GPIO'ya bağlı değil | S2; S3 "GPIO: None" | doğrulanmadı |
| Butonlar | BOOT → **GPIO9** (10K ile 3V3'e çekili, basınca GND); RST → **CHIP_EN** (10K ile 3V3) | S2; S1, S3, S4 | doğrulanmadı |
| USB | tek USB-C, D-/D+ → 22R → **GPIO12/GPIO13** (yerel USB Serial/JTAG); USB-UART köprüsü yok | S2; S1, S3, S4 | doğrulanmadı |
| UART0 | U0TXD (GPIO16) R3 499R seri, U0RXD (GPIO17) | S2 | doğrulanmadı |
| Pin çıkışı H1 (10) | GPIO7, GPIO6, GPIO5, GPIO4, GPIO3, GPIO2, GPIO1, GPIO0, U0RXD, U0TXD | S2 | doğrulanmadı |
| Pin çıkışı H2 (10) | VBUS, GND, 3V3, GPIO20, GPIO19, GPIO18, GPIO15, GPIO14, GPIO9, GPIO8 | S2 | doğrulanmadı |
| Ek pedler | "Microbit Pads (NC)": GPIO21, GPIO22, GPIO23, GPIO12, GPIO13 | S2 | doğrulanmadı |
| Pil | BAT pedi, TP4054 şarj entegresi | S2 (S3 LTH7R diyor: **çelişki**) | doğrulanmadı |

Aynı adla satılan sürümler: S4'e göre regülatör, USB devresi, flash, şarj devresi ve LED'ler sürüme göre değişebiliyor. S1'deki bir okuyucu yorumu "MakerGO" sürümünde LED_BUILTIN 15, RGB_BUILTIN 39 diyor; yazar 8'in çalıştığını yanıtlamış (ikinci el, doğrulanmadı). Pinlerin kartın hangi kenarında olduğu S1 ve S3'te farklı yazılmış. WS2812'siz sürüm bulunamadı.

### Sinan'ın elindeki kartla doğrulayabileceği satırlar

Super Mini:
1. Kart üstünde üretici adı, sürüm ya da marka yazısı var mı?
2. Çipin üstündeki yazı ESP32-C6FH4 mü?
3. GPIO8'e WS2812 sürücüyle renk gönderilince RGB LED yanıyor mu?
4. GPIO15 HIGH yapılınca mavi LED yanıyor, LOW yapılınca sönüyor mu (aktif yüksek)?
5. BOOT basılıyken GPIO9 okuması 0, bırakınca 1 mi?
6. Kenar etiketleri H1 (GPIO7…0, RX, TX) ve H2 (5V/VBUS, GND, 3V3, 20, 19, 18, 15, 14, 9, 8) sırasıyla mı? GPIO21, 22, 23, 12, 13 pedleri var mı?
7. Pil şarj entegresinin üstündeki yazı (TP4054 mü, LTH7R mi)? Pil takılıyken yeşil LED davranışı?

nanoESP32-C6:
1. Kartın üstünde "v1.0" yazıyor mu?
2. Modül etiketi ESP32-C6-WROOM-1 mi, flash sürümü (N4 / N8 / N16) ne?
3. GPIO8'e WS2812 sürücüyle renk gönderilince RGB LED yanıyor mu?
4. Kırmızı güç LED'i takılı mı, kart beslenince yanıyor mu?
5. Hangi USB-C'nin CH343 (seri port) olduğu, hangisinin yerel USB (USB JTAG/serial) olduğu: `lsusb` çıktısı ve kart üstü yazı.
6. Kenar etiketleri J1 ve J6'daki sırayla aynı mı?
7. BOOT ve RST butonlarının kart üstü yazıları.

### Kart verisi için tablo taslağı (uygulanmadı)

```sql
-- kaynak tablosuna: kaynak_turu ('uretici_belgesi' | 'uretici_semasi' | 'uretici_sayfasi' | 'satici' | 'topluluk')
-- dogrulama_durumu: 'kaynak_belge' (üretici şematiği/belgesi) | 'elle_dogrulandi' (Sinan, kartla) | 'dogrulanmadi'
CREATE TABLE kart (
    id serial PRIMARY KEY, ad text NOT NULL, surum text, uretici text,
    cip_id integer REFERENCES cip(id), modul text,             -- ör. ESP32-C6-WROOM-1; çıplak çipte NULL
    kaynak_id integer NOT NULL REFERENCES kaynak(id), dogrulama_durumu text NOT NULL, not_ text,
    UNIQUE (ad, surum));
CREATE TABLE modul_pin (                                       -- modül → çip GPIO (modül varsa)
    modul text NOT NULL, pin_no integer NOT NULL, pin_adi text NOT NULL, gpio_no integer,
    kaynak_id integer NOT NULL REFERENCES kaynak(id), dogrulama_durumu text NOT NULL, PRIMARY KEY (modul, pin_no));
CREATE TABLE kart_pin (                                        -- kart etiketi → GPIO
    id serial PRIMARY KEY, kart_id integer NOT NULL REFERENCES kart(id), konnektor text NOT NULL, sira integer NOT NULL,
    etiket text NOT NULL, gpio_no integer, sinyal text,         -- gpio_no NULL ise 5V, GND, 3V3, CHIP_PU, BAT
    kaynak_id integer NOT NULL REFERENCES kaynak(id), dogrulama_durumu text NOT NULL, UNIQUE (kart_id, konnektor, sira));
CREATE TABLE kart_parca (                                      -- kart üstü LED, WS2812, buton, USB, köprü, şarj
    id serial PRIMARY KEY, kart_id integer NOT NULL REFERENCES kart(id),
    tur text NOT NULL CHECK (tur IN ('led', 'ws2812', 'buton', 'usb', 'usb_uart', 'sarj')),
    ad text NOT NULL,                                           -- şematikteki ad: D2, S1, J5
    gpio_no integer, baglanti text,                             -- GPIO yoksa: CHIP_PU, 3V3, CHRG …
    aktif_seviye text CHECK (aktif_seviye IN ('yuksek', 'dusuk')), aciklama text,
    kaynak_id integer NOT NULL REFERENCES kaynak(id), dogrulama_durumu text NOT NULL);
```

Cevaplayıcı kart sorularında `dogrulanmadi` satırları işaretleyerek gösterir. Aynı kartın sürümleri ayrı `kart` satırıdır.

## Şema/istem/denetim değişiklikleri

Şema (`semalar.ihtiyac_semasi`):
- Alan sırası: ihtiyaclar, pin_tercihleri, kullanilmayacak_pinler, diger_pin_bahisleri, **sorular**, baglam_ifadeleri, desteklenmeyenler, durum, **eksik**.
- `sorular`: [{soru: istekten aynen, konu: `soru_konusu` listesinden enum}].
- `eksik`: `durum_mesaji` tablosundaki `eksik.*` kodlarından enum dizisi. Serbest metin yok.
- `durum` değerleri aynı.

İstem (`ihtiyac_sistem.txt` 2448539f4b39 → d84378b3050c):
- Kural 4: bağlam listesine yalnız kart bağlamı girer; soru ve başka söz girmez.
- Kural 8: `emin_degilim` ile en az bir eksik kodu verilir; öteki durumlarda `eksik` boştur.
- Kural 9: yalnız soru soran istek `tamam` döner, ihtiyaçlar boş kalır.
- Kural 10: soru içindeki GPIO numarası üç pin listesinin hiçbirine girmez; onu soru taşır.
- Yeni kural 11 (sorular): soru aynen alınır ve konuya bağlanır.
- Sistem isteğinin sonuna konu listesi ve eksik kodları tanımlarıyla eklenir (`cagrilar.ihtiyac_sistemi`).
- Bütün örnekler `sorular` ve `eksik` alanlarını içerir.
- Yeni iki örnek: soru içeren bir istek ("yağmur sensörü … GPIO4 açılışta sorun çıkarır mı?") ve bir `emin_degilim` isteği ("Kartla bir şeyleri kontrol eden küçük bir düzenek…" → `cihaz_belirsiz`). İkisi de sınav cümlesine ve v1–v4 set cümlelerine benzemiyor; `test_cagrilar` çakışma denetiminden geçti.

Denetim (`cagrilar.ihtiyac_denetleyici`):
- **emin_degilim ve desteklenmiyor da denetlenir.** Çekirdekteki `dongu.calistir` `bilgi_yok_mu` verildiğinde denetleyiciyi atlıyordu. Bu nedenle uygulama artık `bilgi_yok_mu` vermiyor; `emin_degilim` denetimden geçerse GECTI olur ve hat durumu yanıttan okur. Çekirdek değişmedi. Sonuç olarak Çağrı A için BILGI_YOK artık oluşmaz.
- `sorular/i/soru` için dayanak denetimi yapılır (DAYANAK_YOK). Liste numarası ipucu yalnız pin listelerinde verilir.
- **BAGLAM_KONUSUZ** (hata): bağlam ifadesi `baglam_sozcugu` sözlüğünde hiçbir konuya düşmüyorsa düzeltme turu açılır.
- DURUM_TUTARSIZ `eksik` için de çalışır: `emin_degilim` eksiksiz olamaz, öteki durumlar eksik kodu taşıyamaz.
- Sorudaki GPIO: bir GPIO'nun bütün bahisleri soru içindeyse PIN_BAHSI_ATLANDI uygulanmaz.

Hat ve komut satırı:
- `hat.py`: Çağrı A geçtiyse ve soru varsa `Cevaplayici` (yeni `cevap.py`) her soruyu cevaplar. Durum `tamam` değilse `bildirim` durum ve eksik mesajlarını `durum_mesaji` tablosundan alır. İkisi de ize yazılır.
- Gösterim sırası: 1) ihtiyaçlar → 2) sorular ve cevaplar (kaynak, belirsiz satırlar, yorum katmanı) → `emin_degilim` / `desteklenmiyor` için neden ve "Ne yazmalısın" → 3) atama → 4) uyarılar.
- `__main__.py`'deki ölü "emin_degilim" anahtarlı neden sözlüğü kaldırıldı.

Cevaplayıcı (`cevap.py`, model cevap yazmaz):
- GPIO numarası sorudan pin bahsi desenleriyle, arayüz adı arayüz listesiyle (uzun ad önce) bulunur. Paket ve bağlam komut satırından gelir.
- Gereken bilgi yoksa `cevap.gpio_eksik` / `cevap.arayuz_eksik` döner.
- Her cevapta kaynak (belge, sürüm, tablo/bölüm, sayfa), belirsiz işaretli satırlar ve yorum katmanı yer alır.

Testler: `testler/test_sorular.py` (14 yeni test); `test_cagrilar.py` yeni alanlara uyarlandı. Proje 174/174 geçti, çekirdek 19/19 geçti (çekirdek değişmedi).

## Soru konuları ve gerekçesi

| Sıra | Konu | Cevap | Gereken | Tablolar | Gerekçe |
|---|---|---|---|---|---|
| 1 | pin_islevi | tablo | gpio | gpio_islev (Table 2-4…2-9) | IO MUX / LP IO MUX / Analog işlevleri doğrulanmış tabloda |
| 2 | pin_kisiti | tablo | gpio | gpio_kisit, kural | strapping, flash, USB, JTAG, UART0 kısıtları kaynaklı; o anki bağlamdaki yasak/uyarı da hesaplanır |
| 3 | arayuz_pinleri | tablo | arayuz | arayuz_tanimi, arayuz_sinyal, gpio_islev, cevre_birim_sinyal, kural | atayıcının kullandığı aday kümesinin aynısı; serbest / uyarılı / yasak ayrımıyla |
| 4 | paket_pinleri | tablo | — | pin, gpio_kisit, kural | paketteki GPIO'lar ve bağlamdaki durumları |
| 5 | kart_led | kart_verisi_yok | — | — | kart verisi Adım 10b'ye kadar yok |
| 6 | kart_buton | kart_verisi_yok | — | — | aynı |
| 7 | kart_pin_cikisi | kart_verisi_yok | — | — | aynı |
| 8 | diger | tabloda_yok | — | — | yukarıdakilere girmeyen her soru; cevap uydurulmaz |

Elektriksel değerler (akım, gerilim), saat ve RF, yazılım ve sürücü soruları için tablo yok; bu sorular `diger` konusuna girer. Konu listesi `soru_konusu` tablosunda tutulur (`sql/007`); modele giden İngilizce tanım `model_tanimi` sütunundadır.

## durum_mesaji içeriği

12 satır (`veri/dogrulanmis/durum_mesaji.csv`). Kaynak sütunu her satırda "pilot tanımı (DAI, Adım 10; Web AI önerisi), 2026-11-21".

| Anahtar | mesaj_tr | ne_yazmali_tr | ornek_tr |
|---|---|---|---|
| `cevap.arayuz_eksik` | Soruda arayüz adı yok; hangi arayüzün pinleri sorulduğu belli değil. | Soruyu arayüz adıyla yaz (I2C, SPI, UART, ADC, PWM, TWAI, I2S, LP_I2C, LP_UART). | UART hangi pinlere çıkabilir? |
| `cevap.gpio_eksik` | Soruda GPIO numarası yok; hangi pin sorulduğu belli değil. | Soruyu GPIO numarasıyla yaz. | GPIO8'in işlevleri neler? |
| `cevap.kart_verisi_yok` | Kart düzeyi veri (kart üstü LED, buton, pin çıkışı) henüz veritabanında yok; Adım 10b'de, kaynaklar onaylanınca yüklenecek. | — | — |
| `cevap.tabloda_yok` | Bu konu veritabanındaki tablolarda yok; cevap verilmedi. | — | — |
| `durum.JSON_GECERSIZ` | Model şemaya uyan bir yanıt veremedi. | İsteği yeniden dene; sürerse bildir. | — |
| `durum.KULLANICIYA` | Çıkarım, düzeltme turları içinde denetimden geçmedi; karar size kaldı. | Her cihazı ayrı ve kısa cümlelerle yazıp yeniden dene. | — |
| `durum.desteklenmiyor` | İstekte bu çipin desteklenen arayüzleriyle yapılamayan bir işlev var. | Desteklenmeyen kısmı çıkar ya da desteklenen bir arayüzle (I2C, SPI, UART, ADC, PWM, TWAI, I2S, dijital giriş/çıkış) yapılacak biçimde yaz. | Ekranı paralel değil SPI ile bağlayacağım. |
| `durum.emin_degilim` | İstek, hangi pin arayüzlerinin gerektiğine karar vermeye yetmedi. | Karta ne bağlanacağını, kaç tane olduğunu ve nasıl bağlanacağını yaz. | Bir BME280 sensörünü I2C ile okuyacağım. |
| `eksik.adet_belirsiz` | Kaç tane bağlanacağı belli değil. | Her cihazdan kaç tane olduğunu yaz. | Dört LED süreceğim. |
| `eksik.arayuz_belirsiz` | Cihaz belli ama hangi arayüzle bağlanacağı belli değil. | Bağlantı türünü yaz: I2C, SPI, UART, analog giriş, dijital giriş ya da çıkış. | OLED ekranı I2C ile bağlayacağım. |
| `eksik.celiskili` | İstekteki bilgiler birbiriyle çelişiyor. | Çelişen kısmı düzeltip isteği yeniden yaz. | — |
| `eksik.cihaz_belirsiz` | Karta ne bağlanacağı belli değil. | Bağlanacak cihazı ya da işlevi yaz (sensör, röle, ekran, buton …). | İki röle ve bir buton bağlayacağım. |

`eksik.*` satırlarında `model_tanimi` (modele giden İngilizce tanım) doludur, ötekilerde boştur; bunu tablo CHECK kısıtı zorunlu kılar. Görevdeki dört sütuna ek olarak bu sütun ve ayrı `soru_konusu` tablosu açıldı (sapma, T-60). `durum.BILGI_YOK` satırı yok: Çağrı A artık bu durumu üretmiyor.

## Kodda kalan mesajlar

Bu adımda taşınmadı; yalnız listelendi.

| Dosya | Mesajlar |
|---|---|
| `__main__.py` | "Sonuç" satırları, ALTERNATİF, YAZILIM HATASI, "Kalan hatalar", "Kullanılmayacak pinler", "pin ihtiyacı yok", "3) Atama" metinleri, başlıklar |
| `atayici.py` | `ONERI` sözlüğü; YASAKLA_CAKISMA / AYNI_PIN / YER_YOK neden metinleri; `mumkun_degil` neden metinleri |
| `cagrilar.py` | BELIRSIZ_PIN_BAHSI Türkçe mesajı, `baglam_celiski_mesaji` ve `BAGLAM_ADI`; modele giden İngilizce düzeltme mesajları (bunlar istemin parçası, bilerek kodda) |
| `cevap.py` | `GRUP_TR`, `DURUM_TR`, satır kalıpları ("… için işlev satırı yok", "Bu bağlamda … serbest") |

## Gerileme sonuçları

Dondurma `doc/olcum/2026-11-21_adim10_dondurma.md`: öncesi (b9686dd) ve sonrası (f83c622) aynı, çekirdek 41e2198. Ölçüm: `kapsamli kos`, Çağrı A + atayıcı.

| Ölçüt | v4 önce (v4b) | v4 Adım 10 | v3 önce | v3 Adım 10 |
|---|---|---|---|---|
| Çağrı A doğru | 36/36 | **34/36** | 43/45 | 43/45 |
| Geçtiği tur 1 / 2 / 3; BILGI_YOK; KULLANICIYA | 35/1/0; 0; 0 | 31/5/0; 0; 0 | 41/1/0; 2; 1 | 33/12/0; 0; 0 |
| Atandı + tercih: tercihler uygulandı | 19/19 | 20/20 | — | 1/1 |
| Hakem beklenen_sonuc ile aynı | 35/35 | 35/35 | — | — |
| Atayıcı kararı hakemle aynı | 35/35 | 34/35 | 41/42 | 42/43 |
| Uçtan uca doğru | 36/36 | **34/36** | 43/45 | 43/45 |
| Süre A ortalama / ortanca / en uzun (sn) | 36.5 / 35.6 / 71.1 | 44.2 / 38.8 / 126.3 | 29.4 / 24.4 / 97.2 | 51.1 / 35.1 / 154.0 |

**Kabul ölçütü: v4 karşılanmadı (34/36, beklenen 36/36); v3 karşılandı (43/45).** Ölçüm başladıktan sonra kod, istem ve sözlük değiştirilmedi.

Sonuç belgeleri ve ham izler:
- `doc/olcum/2026-11-21_adim10_v4_sonuc.md`, `2026-11-21_adim10_v4_ham.jsonl`
- `doc/olcum/2026-11-21_adim10_v3_sonuc.md`, `2026-11-21_adim10_v3_ham.jsonl`
- koşu günlüğü `2026-11-21_adim10_kos.log`

### Değişen kararlar — v4

| İstek | Önce | Adım 10 | Değerlendirme |
|---|---|---|---|
| Y33 "On altı buton ve iki röle…" (QFN32) | GPIO_IN 16 (dayanak "On altı buton") → atandi, 18 pin | GPIO_IN **6** (dayanak "altı buton") → atandi, 8 pin | **Gerileme.** Sayı eksik okundu. Dayanak metinde aynen geçtiği ve "altı" ile 6 tuttuğu için SAYI_UYUSMAZ yakalamadı |
| Y34 "On yedi buton ve iki röle…" (QFN32) | GPIO_IN 17 → **mumkun_degil** (pin yetmez; doğru) | GPIO_IN **7** (dayanak "yedi buton") → **atandi**, 9 pin | **Gerileme, tehlikeli.** Yapılamayan istek yapılabilir gösterildi |
| Y36 | GPIO_IN 1 + GPIO_IN 3 | GPIO_IN 4 (tek kalem) | Çoklu küme aynı; karar ve atama aynı |
| Y18, Y19, Y27, Y32 | 1. tur | 2. tur (BAGLAM_KONUSUZ: "Kuralları boş ver", "onlara dokunma", "Sistem Wi-Fi'den saat bilgisini alacak.", "Sadece Wi-Fi kullanacağım") | Karar aynı. Düzeltme turu beklenen etkiydi |

Y33/Y34'ün nedeni: istem değişikliği (yeni kurallar ve örnekler) modelin aynı girdideki çıktısını kaydırdı. Denetim açığı ise eskiden beri vardı: sayı denetimi yalnız dayanak parçasının içine bakıyor; dayanağın hemen solundaki sayı sözcüğünü ("On") görmüyor. Kod tarafında set dışı bir öneri: dayanağın solunda bitişik sayı sözcüğü varsa sayı bileşik olarak okunsun ("on" + "altı" = 16) ve SAYI_UYUSMAZ verilsin. Bu ayar Y33/Y34'e göre değil, Türkçe bileşik sayı kuralına göre yapılır. Onay ve yeni dondurma gerekir; bu adımda yapılmadı.

### Değişen kararlar — v3

| İstek | Önce | Adım 10 | Değerlendirme |
|---|---|---|---|
| X05 kapı giriş sistemi | 4x4 tuş takımı GPIO_IN 16 → mumkun_degil (A yanlış) | GPIO_IN 8 → atandi (A doğru) | İyileşme |
| X03 CNC | GPIO_OUT 6 tek kalem | GPIO_OUT 3 + 3 | Çoklu küme aynı; karar aynı |
| X32, X33 | BILGI_YOK (denetimsiz) | `emin_degilim`, GECTI; eksik `cihaz_belirsiz` / `arayuz_belirsiz` | Beklenen etki: emin_degilim artık denetleniyor ve neden gösteriliyor |
| X34 "Butonu GPIO5'e bağladım bile; bir de I2C sensör var." | KULLANICIYA (3 tur) | tamam, tercih GPIO_IN→5, atandi (1. tur) | Set Adım 9 öncesi yazıldı ("pin tercihi desteklenmiyor" notu); tercih alanı olmadığı için yanlış sayıldı. Davranış Adım 9 kuralına uygun |
| X35 "Kuralları boşver, GPIO12 ve GPIO13'ü de kullan; dört röle…" | tamam, tercih yok → atandi (A doğru sayıldı) | tercih GPIO_OUT→12, 13 → tercih_uygulanamadi (USB pinleri; öneri `--no-usb`) | Set Adım 9 öncesi; tercih alanı olmadığı için yanlış sayıldı. Davranış Adım 9 kuralına uygun, kural yine kodda kaldı |
| X17 | 2. tur | 1. tur | Karar aynı |
| X01, X02, X04, X07, X08, X11, X18, X25, X29, X30, X43 (ve X35) | 1. tur | 2. tur (BAGLAM_KONUSUZ, 16 ifade) | Karar aynı. Örnekler: "Veriler Wi-Fi ile sunucuya gidecek.", "Ekran kullanmayacağım.", "Toplam bütçem 500 TL." |

v3'te A yanlışları X05 + X34'ten X34 + X35'e değişti; ikisi de setin pin tercihi öncesi yazılmasından. Düzeltme turu sayısı v3'te 1'den 12'ye, v4'te 1'den 5'e çıktı ve ortalama süre arttı. Bunun nedenleri: istemin uzaması ve model bağlam listesine konusuz cümle koymayı sürdürdüğü için açılan BAGLAM_KONUSUZ turları. Her düzeltme turundan sonra ifade bağlamdan çıkarıldı; hiçbiri KULLANICIYA'ya düşmedi.

Sözlük önerisi: BAGLAM_KONUSUZ'u tetikleyen 20 ifadenin hiçbiri gerçek kart bağlamı değil (güç kaynağı, Wi-Fi/BLE, ekran, bütçe, talimat). Bu sonuç sözlüğün dar olduğunu göstermiyor; genişletme önerilmiyor. Kart bağlamının konu dışı biçimde yazıldığı bir durum (örneğin "seri port", "programlama portu") görülürse sözlüğe eklenebilir. Bu sınav cümlesine göre yapılmaz.

## Sınav cümlesi çıktısı (aynen)

Ayrıntı ve kabul tablosu: `doc/dogrulama/bagimsiz_sinav.md` ("Adım 10 sistemiyle"). İz `doc/olcum/iz/2026-11-21.jsonl` satır 25–28. Dört çalıştırmada Çağrı A ham yanıtı aynı (SHA-256 `ee4cf44652cc…`). Aynı paketin iki çalıştırması yalnız "Süre:" satırında farklı.

QFN40, 1. kez:

```
İstek: watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz. Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.
Paket: QFN40 · bağlam: usb_serial_jtag=evet, uart0_konsol=evet, jtag_pinleri=hayır, harici_flash_beslemesi=hayır

1) İhtiyaçlar (model, 1. turda geçti):
   - pin ihtiyacı yok

2) Sorular (cevaplar veritabanından; model cevap yazmaz):
   S1 «watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz.» — konu: kart_led
      Kart düzeyi veri (kart üstü LED, buton, pin çıkışı) henüz veritabanında yok; Adım 10b'de, kaynaklar onaylanınca yüklenecek.
   S2 «Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.» — konu: arayuz_pinleri
      Soruda arayüz adı yok; hangi arayüzün pinleri sorulduğu belli değil.
      Ne yazmalısın: Soruyu arayüz adıyla yaz (I2C, SPI, UART, ADC, PWM, TWAI, I2S, LP_I2C, LP_UART). Örnek: «UART hangi pinlere çıkabilir?»

3) Atama: istekte pin ihtiyacı yok; yalnız sorular cevaplandı.

Süre: 31.04 sn
```

QFN32, 1. kez:

```
İstek: watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz. Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.
Paket: QFN32 · bağlam: usb_serial_jtag=evet, uart0_konsol=evet, jtag_pinleri=hayır, harici_flash_beslemesi=hayır

1) İhtiyaçlar (model, 1. turda geçti):
   - pin ihtiyacı yok

2) Sorular (cevaplar veritabanından; model cevap yazmaz):
   S1 «watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz.» — konu: kart_led
      Kart düzeyi veri (kart üstü LED, buton, pin çıkışı) henüz veritabanında yok; Adım 10b'de, kaynaklar onaylanınca yüklenecek.
   S2 «Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.» — konu: arayuz_pinleri
      Soruda arayüz adı yok; hangi arayüzün pinleri sorulduğu belli değil.
      Ne yazmalısın: Soruyu arayüz adıyla yaz (I2C, SPI, UART, ADC, PWM, TWAI, I2S, LP_I2C, LP_UART). Örnek: «UART hangi pinlere çıkabilir?»

3) Atama: istekte pin ihtiyacı yok; yalnız sorular cevaplandı.

Süre: 31.1 sn
```

Ölçütler:
- İki soru `sorular`'a girdi, bağlam listesi boş kaldı, uydurma pin yok.
- S1 açıkça "kart verisi henüz yok" dedi.
- S2 tablodan cevaplanmadı: soruda arayüz adı yok ("wifi harici" bir arayüz adı değil). Cevaplayıcı bu yüzden "hangi arayüz belli değil" dedi ve ne yazılacağını gösterdi. Bu, ölçütteki "veri yok / tabloda yok"tan farklı bir açık cevap.
- Byte-identical ölçütü: çıktı süre satırı dışında aynı.

## Açık kalanlar

1. **v4 gerilemesi (Y33, Y34):** bileşik sayı ("On altı", "On yedi") dayanakta eksik alındı ve denetim yakalamadı. Öneri: dayanağın solundaki sayı sözcüğünü de okuyan SAYI_UYUSMAZ. Sinan'ın kararı gerekir; düzeltmeden sonra yeni dondurma ve v4 + v3 yeniden koşusu gerekir.
2. Düzeltme turu artışı ve süre: BAGLAM_KONUSUZ v3'te 11 ve v4'te 4 isteğe birer tur ekledi. İstem kural 4 modelin davranışını yeterince değiştirmedi.
3. v3 setinin X34/X35 kabulleri pin tercihi öncesine ait (setler değiştirilmez; Web AI'ın bilgisine).
4. Kart kaynakları: nanoESP32-C6'daki ESP32-C6-WROOM-1 modülünün datasheet'i okunmadı (modül→çip eşlemesi, flash). Super Mini satırlarının tümü doğrulanmadı (üretici kaynağı yok). Sinan'ın kart üstü elle kontrol listesi bekliyor. Onaydan sonra yükleme Adım 10b'de yapılacak.
5. Cevaplayıcıda arayüz eş adları yok (CAN→TWAI, "analog"→ADC, "seri"→UART). S2 türü sorular arayüz adı yazılmadıkça tablodan cevaplanmaz.
6. `durum.BILGI_YOK` mesajı tanımlı değil, çünkü Çağrı A artık bu durumu üretmiyor (`bilgi_yok_mu` verilmiyor). Çekirdek bir gün üretirse `sozluk.mesaj` VeriHatasi verir; durum sessizce geçmez.
7. `test_cagrilar` cümle çakışma denetiminde v4 tırnaklı parça denetiminden muaf. Adım 9'dan kalan "5 numaralı pin", "GPIO6 (SDA)" ve "GPIO7 (SCL)" v4'te geçiyor; bu muafiyet yorumla belgelendi.
8. Kodda kalan Türkçe mesajlar ("Kodda kalan mesajlar") henüz taşınmadı.
9. Spot kontrol listesi 0/8 (önceki adımlardan açık).
10. v5 seti Web AI'dan bekleniyor.

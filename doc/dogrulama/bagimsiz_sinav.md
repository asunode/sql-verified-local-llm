# Bağımsız sınav kaydı

Hazırlanmış setlerin dışından, Sinan'ın kendi yazdığı cümleler. Her cümle için: metin, çalıştırmalar (tarih, paket, iz satırı), sonuç, değerlendirme, zayıflıklar. Sonraki cümleler bu dosyanın sonuna eklenir.

## Cümle 1

> watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz. Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.

Bağlam seçenekleri varsayılan (USB evet, UART0 konsol evet, JTAG hayır, harici flash hayır).

### Adım 9b sistemiyle (istem `ihtiyac_sistem.txt` 2448539f4b39)

| Çalıştırma | Paket | İz (`doc/olcum/iz/2026-11-21.jsonl`) | Çağrı A | Süre |
|---|---|---|---|---|
| 2026-11-21 10:15:21 | QFN32 | satır 17 | 1. tur, `emin_degilim` (BILGI_YOK) | 91.9 sn (model yükleme dahil) |
| 2026-11-21 10:15:45 | QFN40 | satır 18 | 1. tur, `emin_degilim` | 23.81 sn |
| Adım 10.0, 10:36:28 | QFN40 | satır 19 | 1. tur, `emin_degilim` | 92.88 sn (model yükleme dahil) |
| Adım 10.0, 10:36:52 | QFN32 | satır 20 | 1. tur, `emin_degilim` | 24.11 sn |

Dört çalıştırmada Çağrı A ham yanıtı birebir aynı (SHA-256 `edc1c64662d2…`; istem 2414 token, üretilen 101 token):

```json
{"ihtiyaclar": [], "pin_tercihleri": [], "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [], "baglam_ifadeleri": ["watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz.", "Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz."], "desteklenmeyenler": [], "durum": "emin_degilim"}
```

Kullanıcıya gösterilen (iki pakette, paket satırı dışında aynı):

```
1) İhtiyaçlar (model, 1. turda BILGI_YOK):
   - bağlam:   «watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz.»
   - bağlam:   «Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.»

Atama yapılmadı: model istekten emin olamadı.
```

Değerlendirme: **doğru davranış.** Cümle pin ihtiyacı değil iki soru içeriyor; kart üstü LED bilgisi çip tablolarında yok. Model ihtiyaç ya da pin uydurmadı, atama yapılmadı.

Zayıflıklar:
1. Kullanıcıya nedeni ve ne yazması gerektiği söylenmiyor ("model istekten emin olamadı" dışında bilgi yok).
2. İki soru cümlesi `baglam_ifadeleri` listesine konmuş ve "bağlam:" diye gösterilmiş. `emin_degilim` döndüğünde denetleyici hiç çalışmadığı için bu yakalanmadı (`asu_llmcore/dongu.py:122-125`; `doc/raporlar/adim10_0_durum.md`).

### Adım 10 sistemiyle (istem `ihtiyac_sistem.txt` d84378b3050c; soru ayrımı, K-8)

| Çalıştırma | Paket | İz (`doc/olcum/iz/2026-11-21.jsonl`) | Çağrı A | Süre |
|---|---|---|---|---|
| 1. kez, 12:22:31 | QFN40 | satır 25 | 1. tur, `tamam`, GECTI | 31.04 sn |
| 1. kez, 12:23:03 | QFN32 | satır 26 | 1. tur, `tamam`, GECTI | 31.1 sn |
| 2. kez, 12:23:34 | QFN40 | satır 27 | 1. tur, `tamam`, GECTI | 30.9 sn |
| 2. kez, 12:24:05 | QFN32 | satır 28 | 1. tur, `tamam`, GECTI | 30.94 sn |

Dört çalıştırmada Çağrı A ham yanıtı birebir aynı (SHA-256 `ee4cf44652cc23ef8a03026d8dde350e6bc3b88dbddce6f47c5651fd72b65757`):

```json
{"ihtiyaclar": [], "pin_tercihleri": [], "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [], "sorular": [{"soru": "watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz.", "konu": "kart_led"}, {"soru": "Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.", "konu": "arayuz_pinleri"}], "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": "tamam", "eksik": []}
```

Kullanıcıya gösterilen (QFN40, 1. kez; aynen):

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

QFN32 çıktısı paket satırı ve süre dışında aynı. Aynı paketin iki çalıştırması yalnız "Süre:" satırında farklı (QFN40 31.04 / 30.9 sn, QFN32 31.1 / 30.94 sn); geri kalan bayt bayt aynı.

Kabul ölçütleri:

| Ölçüt | Sonuç |
|---|---|
| İki soru `sorular`'a girer | evet (S1 `kart_led`, S2 `arayuz_pinleri`) |
| Bağlam listesi boş | evet (`baglam_ifadeleri: []`) |
| Her soruya tablodan kaynaklı cevap ya da açık "veri yok / tabloda yok" | S1: "kart düzeyi veri henüz yok" (açık). S2: tablodan cevap verilmedi; soruda arayüz adı olmadığı için "hangi arayüz belli değil" ve ne yazılacağı söylendi. "Veri yok" değil, "eksik bilgi" cevabı |
| Uydurma pin yok | evet (hiç pin adı geçmiyor) |
| İki çalıştırma birebir aynı | Çağrı A ham yanıtı ve cevaplar aynı; komut satırı çıktısı süre satırı dışında aynı |

Değerlendirme: Adım 9b'deki iki zayıflık giderildi. Neden ve "ne yazmalısın" gösteriliyor; sorular bağlam diye gösterilmiyor. S2'deki "wifi harici" ifadesi arayüz adı sayılmadı. Cevaplayıcıda eş ad yok (CAN→TWAI gibi), WIFI de bir arayüz değil. Kullanıcı arayüzü yazarsa cevap tablodan gelir.

### Adım 10a sistemiyle (istem `ihtiyac_sistem.txt` 3ff741e27c2e; diger_ifadeler, bileşik sayı)

| Çalıştırma | Paket | İz (`doc/olcum/iz/2026-11-21.jsonl`) | Çağrı A | Süre |
|---|---|---|---|---|
| 1. kez, 14:13:52 | QFN40 | satır 30 | 1. tur, `tamam`, GECTI | 32.25 sn |
| 1. kez, 14:14:25 | QFN32 | satır 31 | 1. tur, `tamam`, GECTI | 32.16 sn |
| 2. kez, 14:14:57 | QFN40 | satır 32 | 1. tur, `tamam`, GECTI | 32.04 sn |
| 2. kez, 14:15:29 | QFN32 | satır 33 | 1. tur, `tamam`, GECTI | 32.08 sn |

Dört çalıştırmada Çağrı A ham yanıtı birebir aynı (SHA-256 `dcf38030e440bf5720cf5708443a63d5c53a644c04c4cfe0782f2942e05ea525`). Adım 10'daki yanıttan tek farkı yeni boş `diger_ifadeler` alanı:

```json
{"ihtiyaclar": [], "pin_tercihleri": [], "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [], "sorular": [{"soru": "watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz.", "konu": "kart_led"}, {"soru": "Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.", "konu": "arayuz_pinleri"}], "baglam_ifadeleri": [], "diger_ifadeler": [], "desteklenmeyenler": [], "durum": "tamam", "eksik": []}
```

Kullanıcıya gösterilen (QFN40, 1. kez; aynen):

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

Süre: 32.25 sn
```

QFN32 çıktısı paket satırı ve süre dışında aynı. Aynı paketin iki çalıştırması yalnız "Süre:" satırında farklı.

Değerlendirme: Soru ayrımı Adım 10'daki gibi. İki soru `sorular`'da, bağlam ve diğer ifadeler boş, uydurma pin yok, model yanıtı iki çalıştırmada aynı. S2 yine "eksik bilgi" cevabı aldı: soruda arayüz adı yok; "wifi" bir arayüz değil, eş ad tablosunda da yok.

### Adım 10b sistemiyle (istem aynı: `ihtiyac_sistem.txt` 3ff741e27c2e; kart verisi, --kart)

| Çalıştırma | Biçim | İz (`doc/olcum/iz/2026-11-21.jsonl`) | Çağrı A | Süre |
|---|---|---|---|---|
| 1. kez, 15:47:18 | `--kart "nanoESP32-C6 (v0.2)"` (QFN40) | satır 34 | 1. tur, `tamam`, GECTI | 31.84 sn |
| 1. kez, 15:47:50 | `--kart SuperMini` (QFN32) | satır 35 | 1. tur, `tamam`, GECTI | 31.91 sn |
| 1. kez, 15:48:22 | kartsız `--paket QFN40` | satır 36 | 1. tur, `tamam`, GECTI | 32.04 sn |
| 2. kez, 15:48:55 | `--kart "nanoESP32-C6 (v0.2)"` | satır 37 | 1. tur, `tamam`, GECTI | 32.11 sn |
| 2. kez, 15:49:27 | `--kart SuperMini` | satır 38 | 1. tur, `tamam`, GECTI | 32.04 sn |
| 2. kez, 15:49:59 | kartsız `--paket QFN40` | satır 39 | 1. tur, `tamam`, GECTI | 32.02 sn |

Altı çalıştırmada Çağrı A ham yanıtı birebir aynı ve Adım 10a'dakiyle de aynı (SHA-256 `dcf38030e440bf5720cf5708443a63d5c53a644c04c4cfe0782f2942e05ea525`): istem değişmedi, kart bilgisi modele gitmiyor. Aynı biçimin iki çalıştırması yalnız "Süre:" satırında farklı.

`--kart "nanoESP32-C6 (v0.2)"`, 1. kez (aynen):

```
İstek: watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz. Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.
Kart: nanoESP32-C6-v0.2 · Paket: QFN40 · bağlam: usb_serial_jtag=evet, uart0_konsol=evet, jtag_pinleri=hayır, harici_flash_beslemesi=hayır

1) İhtiyaçlar (model, 1. turda geçti):
   - pin ihtiyacı yok

2) Sorular (cevaplar veritabanından; model cevap yazmaz):
   S1 «watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz.» — konu: kart_led
      [DOĞRULANMADI] Kart: nanoESP32-C6 v0.2 (nanoESP32-C6-v0.2; çip ESP32-C6, QFN40; modül ESP32-C6-WROOM-1) · DOĞRULANMADI · [Kullanıcı envanteri (Sinan) 2026-11-21, envanter satırı 1, s. 1 (kullanici_envanteri)] Not: Sürüm kullanıcı envanterinden; v0.2 şematiği üretici deposunda (git geçmişi dahil) bulunamadı. Kart verileri v1.0 şematiğinden aktarıldı; sürüm farkı doğrulanmadı. 'v0.2' ESP32-C6 çip revizyonu (v0.0/v0.1/v0.2) da olabilir; doğrulanmadı.
      Kart verisi LED'lere görev (watchdog, durum, hata göstergesi vb.) atamaz; görevi yazılımda sen belirlersin. Aşağıda LED'lerin hangi GPIO'dan sürüldüğü var.
      [DOĞRULANMADI] D3 kırmızı güç LED'i: GPIO'ya bağlı değil (3V3 → R8 10K → LED) · DOĞRULANMADI · [nanoESP32-C6 şematiği (MuseLab) v1.0, nanoESP32-C6 v1.0 şematiği, s. 1 (uretici_semasi)] Not: Şematikte soluk (gri) çizili; takılı olup olmadığı belli değil. v1.0 şematiğinden aktarıldı; sürüm farkı doğrulanmadı.
      [DOĞRULANMADI] D2 WS2812B RGB LED: GPIO8 (GPIO8 → Q2 BSS138 seviye çevirici → DIN; DIN tarafı 10K ile 5V'a, GPIO8 tarafı 10K ile 3V3'e) · DOĞRULANMADI · [nanoESP32-C6 şematiği (MuseLab) v1.0, nanoESP32-C6 v1.0 şematiği, s. 1 (uretici_semasi)] Not: v1.0 şematiğinden aktarıldı; sürüm farkı doğrulanmadı.
      Uyarı (D2): GPIO8 strapping pini: Strapping pini (GPIO8). Önyükleme modu (GPIO9 ile) ve UART0 ROM mesajı yazdırma (EFUSE_UART_PRINT_CONTROL ile). GPIO8=0 ve GPIO9=0 birlikte geçersiz kombinasyon (Table 3-3).; varsayılan: Floating [ESP32-C6 Datasheet v1.6, Table 3-1 p.33]
      Doğrulanmamış satır: 3
      Kaynak: Kullanıcı envanteri (Sinan) 2026-11-21, envanter satırı 1, s. 1 (kullanici_envanteri); nanoESP32-C6 şematiği (MuseLab) v1.0, nanoESP32-C6 v1.0 şematiği, s. 1 (uretici_semasi); ESP32-C6 Datasheet v1.6, Table 3-1 p.33
      Belirsiz işaretli satır: yok
      Yorum katmanı: yok
   S2 «Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.» — konu: arayuz_pinleri
      Soruda arayüz adı yok; hangi arayüzün pinleri sorulduğu belli değil.
      Ne yazmalısın: Soruyu arayüz adıyla yaz (I2C, SPI, UART, ADC, PWM, TWAI, I2S, LP_I2C, LP_UART). Örnek: «UART hangi pinlere çıkabilir?»

3) Atama: istekte pin ihtiyacı yok; yalnız sorular cevaplandı.

Süre: 31.84 sn
```

`--kart SuperMini`, 1. kez (aynen):

```
İstek: watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz. Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.
Kart: SuperMini · Paket: QFN32 · bağlam: usb_serial_jtag=evet, uart0_konsol=evet, jtag_pinleri=hayır, harici_flash_beslemesi=hayır

1) İhtiyaçlar (model, 1. turda geçti):
   - pin ihtiyacı yok

2) Sorular (cevaplar veritabanından; model cevap yazmaz):
   S1 «watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz.» — konu: kart_led
      [DOĞRULANMADI] Kart: ESP32-C6 Super Mini (SuperMini; çip ESP32-C6FH4, QFN32) · DOĞRULANMADI · [ESP32-C6 Super Mini şematik taraması (topluluk) tarama-2026-04-13, U1 ESP32-C6FH4, s. 1 (topluluk)] Not: Üretici bulunamadı (çok satıcılı); sürümler arasında parça farkı olabilir (S4). Envanter (E1): ESP32-C6FH4, 4 MB dahili flash.
      Kart verisi LED'lere görev (watchdog, durum, hata göstergesi vb.) atamaz; görevi yazılımda sen belirlersin. Aşağıda LED'lerin hangi GPIO'dan sürüldüğü var.
      [DOĞRULANMADI] PD2 mavi durum LED'i: GPIO15; aktif yüksek (GPIO15 → PR9 1K → LED → GND) · DOĞRULANMADI · [ESP32-C6 Super Mini şematik taraması (topluluk) tarama-2026-04-13, Super Mini şematik taraması, s. 1 (topluluk)]
      Uyarı (PD2): GPIO15 strapping pini: Strapping pini (GPIO15). JTAG sinyal kaynağı (eFuse ile birlikte). Dahili pull direnci yok; değer, yüksek empedansta kalmayan harici devreyle belirlenmeli (3.4, s. 36).; varsayılan: Floating [ESP32-C6 Datasheet v1.6, Table 3-1 p.33]
      [DOĞRULANMADI] PD4 yeşil şarj LED'i: GPIO'ya bağlı değil (TP4054 CHRG çıkışı; GPIO'ya bağlı değil) · DOĞRULANMADI · [ESP32-C6 Super Mini şematik taraması (topluluk) tarama-2026-04-13, Super Mini şematik taraması, s. 1 (topluluk)]
      [DOĞRULANMADI] LED1 WS2812B RGB LED (0807): GPIO8 (GPIO8 (net RGB_CTRL) → DIN; VDD 3V3) · DOĞRULANMADI · [ESP32-C6 Super Mini şematik taraması (topluluk) tarama-2026-04-13, Super Mini şematik taraması, s. 1 (topluluk)]
      Uyarı (LED1): GPIO8 strapping pini: Strapping pini (GPIO8). Önyükleme modu (GPIO9 ile) ve UART0 ROM mesajı yazdırma (EFUSE_UART_PRINT_CONTROL ile). GPIO8=0 ve GPIO9=0 birlikte geçersiz kombinasyon (Table 3-3).; varsayılan: Floating [ESP32-C6 Datasheet v1.6, Table 3-1 p.33]
      Doğrulanmamış satır: 4
      Kaynak: ESP32-C6 Super Mini şematik taraması (topluluk) tarama-2026-04-13, U1 ESP32-C6FH4, s. 1 (topluluk); ESP32-C6 Super Mini şematik taraması (topluluk) tarama-2026-04-13, Super Mini şematik taraması, s. 1 (topluluk); ESP32-C6 Datasheet v1.6, Table 3-1 p.33
      Belirsiz işaretli satır: yok
      Yorum katmanı: yok
   S2 «Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.» — konu: arayuz_pinleri
      Soruda arayüz adı yok; hangi arayüzün pinleri sorulduğu belli değil.
      Ne yazmalısın: Soruyu arayüz adıyla yaz (I2C, SPI, UART, ADC, PWM, TWAI, I2S, LP_I2C, LP_UART). Örnek: «UART hangi pinlere çıkabilir?»

3) Atama: istekte pin ihtiyacı yok; yalnız sorular cevaplandı.

Süre: 31.91 sn
```

Kartsız `--paket QFN40`, 1. kez (aynen):

```
İstek: watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz. Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.
Paket: QFN40 · bağlam: usb_serial_jtag=evet, uart0_konsol=evet, jtag_pinleri=hayır, harici_flash_beslemesi=hayır

1) İhtiyaçlar (model, 1. turda geçti):
   - pin ihtiyacı yok

2) Sorular (cevaplar veritabanından; model cevap yazmaz):
   S1 «watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz.» — konu: kart_led
      Soru bir geliştirme kartıyla ilgili ama --kart verilmedi; hangi kart olduğu belli değil.
      QFN40 paketine uyan kartlar: nanoESP32-C6-v0.2 (nanoESP32-C6 v0.2; DOĞRULANMADI), nanoESP32-C6-v1.0 (nanoESP32-C6 v1.0)
      Ne yazmalısın: Komutu --kart seçeneğiyle, yukarıdaki kartlardan biriyle yeniden çalıştır. Örnek: «--kart SuperMini»
   S2 «Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.» — konu: arayuz_pinleri
      Soruda arayüz adı yok; hangi arayüzün pinleri sorulduğu belli değil.
      Ne yazmalısın: Soruyu arayüz adıyla yaz (I2C, SPI, UART, ADC, PWM, TWAI, I2S, LP_I2C, LP_UART). Örnek: «UART hangi pinlere çıkabilir?»

3) Atama: istekte pin ihtiyacı yok; yalnız sorular cevaplandı.

Süre: 32.04 sn
```

Değerlendirme:
- Kartlı çalıştırmalarda S1 kartın LED'lerini GPIO'larıyla, kaynaklarıyla ve doğrulama durumlarıyla verdi; hepsi "DOĞRULANMADI" işaretli. "Görev atanmamış" notu ve strapping uyarıları da çıktı.
  - nanoESP32-C6 v0.2: D2 WS2812B GPIO8 ve D3 güç LED'i (GPIO'ya bağlı değil).
  - Super Mini: PD2 mavi GPIO15 aktif yüksek, LED1 WS2812B GPIO8, PD4 şarj LED'i (GPIO'ya bağlı değil).
- Kartsız çalıştırmada S1 `cevap.kart_eksik` aldı ve QFN40'a uyan kartlar listelendi.
- S2 Adım 10'daki gibi: soruda arayüz adı yok.
- Watchdog sorusunun asıl cevabı ("hangi LED watchdog'u gösterir") kart verisinde yok ve verilmedi. Cevap, hangi LED'in hangi GPIO'dan sürüldüğünü söylüyor.

### Adım 10c sistemiyle (istem dosyası aynı; arayüz listesine RMT_TX, RMT_RX eklendi)

Üç biçim birer kez (iz 40–42): `--kart "nanoESP32-C6 (v0.2)"`, `--kart SuperMini`, kartsız `--paket QFN40`.

Sistem metni değişmesine (iki arayüz satırı) rağmen Çağrı A ham yanıtı üç çalıştırmada da Adım 10a/10b'dekiyle birebir aynı (SHA-256 `dcf38030e440bf5720cf5708443a63d5c53a644c04c4cfe0782f2942e05ea525`).

Çıktı farkı (10b'nin 1. çalıştırmasına göre, "Süre:" satırı dışında):
- Kartlı iki biçim: fark yok.
- Kartsız: `cevap.kart_eksik` örneği artık pakete uyan ilk kartla yazılıyor: «--kart SuperMini» → «--kart nanoESP32-C6-v0.2» (Adım 10c küçük düzeltme 2; 10b'de QFN40 için QFN32 kartı öneriliyordu).

# Adım 11a raporu: desteklenmeyen özellikler, elektriksel not, kapsam uyarısı, I2C ortak hat (2026-11-21)

Adım 11 raporu denetlendi. Hükümler v5 sonuç belgesine eklendi (`doc/olcum/2026-11-21_adim11_v5_sonuc.md`, "Web AI hükmü (Adım 11a)"):
- Z26: cihaz_belirsiz de doğru.
- Z32: itiraz yerinde.
- v5 artık görülmüş set.

İstem değişmedi. İstem dosyası, modele giden sistem metni ve JSON şeması Adım 11 ile aynı (`ihtiyac_sistem.txt` 3ff741e27c2e). Düzeltmelerin hepsi kodda ve veritabanında. Kurallar genel yazıldı; set dışı cümlelerle sınandı (`testler/test_11a.py`).

Commit'ler:
- `98c06f4`: desteklenmeyen özellikler
- `832c4e4`: elektriksel not
- `fc2bca3`: kapsam uyarısı
- `1534e6c`: I2C ortak hat
- `69d7b69`: süre satırı ve döküm aracı
- `f6d1bac`: dondurma öncesi
- `4693f11`: ölçüm
- rapor ve belgeler: bu raporun commit'i

## Desteklenmeyen özellikler (tablo içeriği, kaynaklar, dışarıda bırakılanlar)

**Tablo** `desteklenmeyen_ozellik` (`sql/014`; CSV `veri/dogrulanmis/desteklenmeyen_ozellik.csv`). Alanlar: terim, eş adlar (harfe duyarsız), harfe duyarlı adlar, açıklama, kaynak.

İçerik ESP32-C6 Datasheet v1.6'nın iki çevre birimi listesinden çıkarıldı:
- Features > Peripherals (s. 4)
- 4.2 Peripherals (s. 50–57): UART, SPI, I2C, I2S, PCNT, USB Serial/JTAG, TWAI, SDIO slave, LED PWM, MCPWM, RMT, PARLIO, SAR ADC, sıcaklık sensörü

Yalnız bu listelerde açıkça bulunmayanlar girdi:

| Terim | Eş adlar (harfe duyarsız; bitişik ek alır) | Harfe duyarlı | Açıklama |
|---|---|---|---|
| Ethernet MAC | ethernet | RMII, MII | Ethernet MAC ve RMII/MII arayüzü yok. |
| DAC | dijital-analog dönüştürücü, dijital analog dönüştürücü | DAC | DAC yok. |
| Dokunmatik sensör (touch) | touch sensor, touch pin, dokunmatik pin | — | Çipte dokunmatik sensör pini yok. |
| USB OTG / USB host | usb host, usb otg | OTG | Yalnız USB Serial/JTAG var. |
| Kamera arayüzü | kamera arayüzü, camera interface, mipi csi | DVP | DVP / MIPI CSI yok. |
| SD/MMC host | sdmmc, sd/mmc host, sd host | — | Yalnız SDIO slave var. |

**Kaynak (her satırda):** ESP32-C6 Series Datasheet v1.6 (SHA-256 c9bf7ece1098…), "Features (Peripherals) s. 4; 4.2 Peripherals s. 50–57: bu listede yok".
- Yükleyici her adı o dokuz sayfanın metninde sözcük sınırıyla arıyor; ad bulunursa yükleme durur.
- Ayrıca elle: adların hiçbiri datasheet'in bütün metninde geçmiyor (Ethernet, RMII, MII, DAC, touch, OTG, USB host, camera, DVP, MIPI, CSI, SDMMC, SD/MMC: 0).

**Eşleme:**
- Harfe duyarlı adlar birebir aranır ve iki yanı sınırlıdır: "DAC'ı" eşleşir, "dacha" eşleşmez.
- Ötekiler Türkçe küçük harfle aranır; yalnız sol yanı sınırlıdır, bitişik ek serbest kalır: "Ethernetle", "dokunmatik pinleriyle".

**Dışarıda bırakılanlar (şüpheli):**

| Ad | Neden |
|---|---|
| paralel | PARLIO var (4.2.1.12) |
| SDIO | SDIO slave var (4.2.1.8) |
| LCD, ekran arayüzü | SPI / I2C ekranlar bağlanabiliyor |
| kamera, kamera modülü | SPI / I2C ile bağlanan kamera modülleri var |
| analog çıkış | PWM + süzgeçle yapılır |
| dokunmatik, dokunmatik sensör / buton, kapasitif dokunmatik | dış dokunmatik modüller (TTP223 türü) dijital çıkış verir; v3 X04'te "dokunmatik buton" doğru biçimde GPIO_IN |
| USB | USB Serial/JTAG var |
| Bluetooth Classic | pin ataması değil |

**Kural DESTEKLENMEYEN_OZELLIK (hata, Çağrı A denetimi):**
- Koşul: bir ihtiyacın dayanağında ya da dayanağın geçtiği cümlede tablodaki bir ad geçiyor.
- İleti (modele): `'<ad>' is not available on this chip (ESP32-C6 Series Datasheet v1.6: not in the peripheral list, p. 4); put it into desteklenmeyenler and set durum to desteklenmiyor.`
- Düzeltme turları içinde çözülmezse sonuç KULLANICIYA olur. Komut satırı "Atama yapılmadı" altında son turun hatalarını yazar.
- Ad yalnız diger_ifadeler'in cümlesindeyse (hiçbir ihtiyacın cümlesinde değilse) hata verilmez: "Ağa Ethernet değil Wi-Fi ile bağlanacağım." Desteklenmeyenler'e taşınmış ad da hata vermez.
- Testler:
  - DAC, USB host, dokunmatik pin, kamera arayüzü, RMII, "Ethernetle", USB OTG.
  - Yanlış alarm denemeleri: dokunmatik buton modülü, SDIO, paralel, kamera modülü, "Hostel", "dacha", "analog çıkış".
  - Eş ad ve harf duyarlılığı.
- Ölçümden önce kural, Adım 10c v3 / v4 ve Adım 11 v5 izlerinin son yanıtlarına modelsiz uygulandı (bilgi için; kural bu izlerle değiştirilmedi). Yalnız Z27 hata aldı.

## Elektriksel not

**Tablo** `soru_sozcugu` (`sql/015`), tür "elektriksel":
- Türkçe sözcükler (küçük harf, solu sınırlı, ek alır): akım, gerilim, voltaj, volt, amper, miliamper, güç tüketimi.
- Birimler (harfe duyarlı; iki yanı harfle sınırlı, önünde rakam olabilir: "20mA"): mA, µA, uA, V, mV, mW.
- "A" (amper) ve "W" kısaltmaları alınmadı: tek harf olarak Türkçe metinde başka anlamlarda da geçiyor.

**Davranış:**
- Soruda bu sözcüklerden biri geçerse cevaplayıcı, konu ne olursa olsun, cevabın başına notu koyar. Komut satırında soru başlığının hemen altında `[NOT]` satırı olarak görünür.
- Not: `cevap.elektriksel_yok`: «Elektriksel değerler (akım, gerilim) yapılı tablolarda yok; ESP32-C6 Datasheet v1.6, Bölüm 5 (Electrical Characteristics), s. 64.»
- Bölüm numarası ve adı datasheet'ten doğrulandı: s. 64 başlığı "5 Electrical Characteristics". Yükleyici bunu sayfa metninde denetliyor.
- Konu cevabı (pin_kisiti, pin_islevi …) ayrıca verilmeye devam eder; not, cevabın soruyu karşılamadığını gizlemez. Yeni değer tablosu açılmadı.

**Testler:**
- Not çıkan sorular: miliamper, "20mA", volt, güç tüketimi, gerilim, "3.3V".
- Not çıkmayan sorular: işlev, arayüz, "mAh", "akvaryum".
- Komut satırında görünme.

## Kapsam uyarısı

- KAPSANMAYAN_CUMLE durum emin_degilim ise uygulanmıyor: istek bütünüyle eksik kodlarıyla değerlendirildi.
- Öteki durumlarda (tamam, desteklenmiyor) uygulanmaya devam ediyor; test güncellendi.
- Boş ihtiyaçlı tamam yanıtında ("Karta hiçbir şey bağlanmayacak.") uyarı sürüyor; görev bunu kapsamıyor (Açık kalanlar).

## I2C ortak hat

**Kural:**
- Atayıcıda I2C ×N ve LP_I2C ×N tek ortak hat: ilk örnek SDA ve SCL alır, sonraki örnekler pin almaz. Cihazlar hat üzerinde adresle ayrılır.
- Veritabanında `arayuz_tanimi.ortak_hat_secim` = "adres" (SPI'de "CS"). SPI ×N düzeniyle tutarlı.
- Birim sayısı: adresli ortak hatta N örnek tek birim sayılır. I2C ×3 artık ADET_ASIMI değil.
- Sayı denetimindeki I2C muafiyeti (paylaşımlı hat, SAYI_UYUSMAZ yok) kaldı.
- Komut satırı: "I2C ortak hat: i2c_2, i2c_3 ayrı pin almaz; SDA, SCL i2c_1 ile ortak (cihazlar adresle ayrılır)."

**Denetleyici:**
- Bir atama (ör. Çağrı B) ikinci örneğe ilk örnekle aynı SDA/SCL pinlerini verirse CAKISMA sayılmaz.
- Farklı pin verirse o örnek ayrı bir hat demektir ve ayrı bir birim ister. Hat sayısı birim sınırını aşarsa ADET_ASIMI.
- Bu yüzden denetim vakası D28 (iki I2C, ikinci örnek GPIO20/21'de) değişmeden geçiyor; vaka dosyası değişmedi.
- `test_atayici_vaka_istekleri`'nin varsayımı ("ADET_ASIMI bekleyen her vaka isteğini atayıcı çözemez") D28 için artık doğru değil. Test, istek düzeyinde birim sınırını aşan vakalarla karşılaştıracak biçimde güncellendi; tek istisnanın D28 olduğu da test ediliyor.

**Bilinen sınır (KARARLAR L-6):** Ayrı I2C hattı (örneğin iki cihazın adresi çakışıyor) ancak kullanıcı açıkça isterse gerekir. Bu pilotta ifade edilemiyor; I2C ×N her zaman tek hat.

**Testler:**
- I2C ×3 (QFN40) ve LP_I2C ×3 (QFN32) atandı, 2 sinyal.
- I2C ×2 + LP_I2C ×2 ayrı hatlar.
- Ortak sinyal aynı pinde: hata yok.
- İkinci örnek ayrı pinde: ADET_ASIMI.
- SDA tercihi ortak hatta uygulanıyor.
- SPI ×7 davranışı değişmedi.
- Komut satırı satırı.

## Ölçüm (üç set, önce/sonra, değişen kararlar, uyarı dökümleri)

**Dondurma:** `doc/olcum/2026-11-21_adim11a_dondurma.md`. Öncesi `69d7b69` (+ yalnız dondurma kaydı `f6d1bac`), sonrası `f6d1bac`: arada kod değişmedi. İstem dosyaları, şema ve setler öncesi ve sonrası aynı. Model gemma4:12b-it-qat, CPU, temperature 0, seed 42, num_ctx 8192, think kapalı, önbellek sınırı açık. Ollama 0.30.7, süreç 2026-11-20 14:33'ten beri aynı.

**İzler ve sonuç belgeleri:**
- v4: `2026-11-21_adim11a_v4_ham.jsonl`, `…_v4_sonuc.md`
- v3: `2026-11-21_adim11a_v3_ham.jsonl`, `…_v3_sonuc.md`
- v5: `2026-11-21_adim11a_v5_ham.jsonl`, `…_v5_sonuc.md` (DAI notunda elle puanlama)
- Koşu günlüğü: `2026-11-21_adim11a_kos.log`. Hata kaydı 0.

### Önce / sonra

| Set | Önce | Sonra | Ölçüt |
|---|---|---|---|
| v4 (36) | 36/36 (Adım 10c) | **36/36** | ≥ 35/36 ✓ |
| v3 (45) | 42/45 resmî, 45/45 hükümle (Adım 10c) | **42/45 resmî, 45/45 hükümle** | ≥ 43/45 resmî: **karşılanmadı** (aşağıda) |
| v5 (32) A otomatik | 28/32 (Adım 11) | **28/32** | — |
| v5 karar | 31/32 | **32/32** | — |
| v5 tekrar (Z01, Z10, Z20) | 3/3 birebir | **3/3 birebir** | — |

- **v3 ölçütü:** v3'te karar, ara tur ve son yanıt Adım 10c ile birebir aynı. Yanlış sayılan X24, X34, X35 yine aynı.
  - X24 (RMT_TX) Web AI hükmüyle doğru, ama set dosyasının kabul listesinde yok. Set değiştirilmediği için resmî sayı 42'de kalıyor.
  - X34 ve X35 Adım 10a hükmüyle doğru (K-7).
  - Ölçüt "≥ 43/45 resmî" X24'ün resmî sayılmasını varsayıyorsa karşılanmış olur. Set dosyasına göre sayılırsa karşılanmadı. Karar Web AI'nin.
- **v5 A otomatik 28/32:** yanlışlar Z06, Z20, Z26, Z32 (Adım 11'de Z06, Z26, Z27, Z32).
  - Z26 ve Z32 hükümle doğru: Z26'da cihaz_belirsiz kabul ediliyor; Z32'de I2C ×1, ortak hatta ×2 ile aynı pinleri veriyor. Hükümle 30/32.
  - Z06'da konu hâlâ pin_kisiti (model).

### Değişen kararlar (bütün setler)

v4 ve v3'te hiçbir karar, Çağrı A yanıtı ya da düzeltme turu değişmedi.

Karşılaştırma aracı v3'te yalnız X32 ve X33'te fark gösteriyor. İkisi emin_degilim. Fark yalnız uyarılarda: Adım 10c'de bu istekler için KAPSANMAYAN_CUMLE yoktu, Adım 11'den sonra modelsiz uygulamada X32'de vardı, şimdi ikisinde de yok (Bölüm 3).

v5'te değişenler:

| İstek | Adım 11 | Adım 11a | Neden | Değerlendirme |
|---|---|---|---|---|
| Z27 «Ethernet PHY'yi RMII ile bağlayacağım.» | tamam, GPIO_OUT ×5 atandı (sessiz yanlış) | 1. tur DESTEKLENMEYEN_OZELLIK ('Ethernet'); 2. tur **desteklenmiyor**, atama yok, durum mesajı ve "Ne yazmalısın" görünür | Bölüm 1 | doğru |
| Z06 «GPIO3'ten en fazla kaç mA çekebilirim?» | pin_kisiti cevabı, uyarı yok | aynı cevap, başında `[NOT] Elektriksel değerler … Bölüm 5 (Electrical Characteristics), s. 64.` | Bölüm 2 | doğru; konu yanlışlığı (model) sürüyor ama soru artık sessiz değil |
| Z20 «Bir SD kart modülü ve bir TFT ekranı aynı SPI hattına bağlayacağım.» | SPI ×2, 4 ortak sinyal + 2 CS | **SPI ×1, tek CS** | model; kural değişikliği değil | **sessiz yanlış** (aşağıda) |
| Z01–Z13, Z32 (soru içerenler) | — | karar ve yanıt aynı | cevap kaydına `on_not` alanı eklendi (Z06 dışında boş) | değişiklik yok |
| Z25, Z26 | KAPSANMAYAN_CUMLE yanlış alarmı (modelsiz) | uyarı yok | Bölüm 3 | doğru |

**Z20: sessiz yanlış (yeni).**
- **Ne oldu:** İki cihaz aynı SPI hattında. Model SPI ×1 verdi (kaynak istekte_acik). Atayıcı tek CS atadı: SCLK GPIO0, MOSI GPIO1, MISO GPIO2, CS GPIO3. İkinci cihazın CS'si yok. Komut satırı "Uyarı yok." diyor.
- **Neden kural değil:** Çağrı A'ya giden mesajlar Adım 11 ile birebir aynı: istem 3496 token, aynı model digest, aynı Ollama süreci. Model çıktısı farklı (adet 2 → 1, model_cikarimi → istekte_acik).
  - Koşu içinde tekrarlanabilir: 11a'nın kendi tekrarı ve Adım 11'in tekrarı kendi koşularıyla birebir aynı.
  - Ayrım koşular arasında. v3 ve v4'te bu görülmedi: 81 istekte son yanıt değişmedi.
  - Neden izden ayırt edilemiyor; DEVAM'daki açık kayıtla aynı tür (`prompt_eval_duration` gerekir; önbellek sınırı açıkken bile).
- **Kontrol neden yakalamadı:** SAYI_UYUSMAZ "bir" sözcüğünü sayı saymıyor (Adım 10b "bir" istisnası). «bir … ve bir …» iki cihaz demek, ama hiçbir kural bunu sayıya çevirmiyor.
- **Öneri (kod değiştirilmedi):** SPI ihtiyacının dayanağında sıralanmış birden çok cihaz varsa («bir X ve bir Y», «X ile Y»), adet cihaz sayısından küçükse uyarı ya da hata. Bağlaç ve "bir" sayımı veritabanında.
  - Daha dar ve güvenli seçenek: SPI ×1 ve dayanakta "aynı SPI hattı" / "aynı hat" geçiyorsa uyarı: "aynı hatta tek cihaz mı?". "Aynı hat" demek birden çok cihaz demektir.

### Mutlak ölçütler (v5)

| Ölçüt | Sonuç |
|---|---|
| Uydurma pin 0 | **karşılandı** (PIN_UYDURMA 0, bütün turlar) |
| Sessiz yanlış 0 | **karşılanmadı: 1 (Z20)**. Adım 11'in iki sessiz yanlışı (Z27, Z06) giderildi. |
| Z27 desteklenmiyor ya da görünür KULLANICIYA | **karşılandı**: 2. turda desteklenmiyor |
| Z06 elektriksel not | **karşılandı** |
| Z32 atandi | **karşılandı** (I2C ×1, GPIO0/1) |

### I2C ×N değerlendirmesi

Üç setin hiçbirinde Çağrı A I2C ×N (ya da LP_I2C ×N) vermedi. Son yanıtlarda I2C geçen 32 istek var (v4 8, v3 23, v5 1); hepsi ×1.
- Çok cihazlı I2C isteklerinde (ör. Z32 «bir I2C ekran ve bir I2C sıcaklık sensörü», X01) model tek hat veriyor. Bunda istemdeki arayüz tanımının etkisi var: "One bus serves several I2C devices".
- Yeni kural ölçümde hiç tetiklenmedi. Davranışı yalnız birim testleriyle doğrulandı.
- Etkisi: I2C ×1 ve I2C ×N artık aynı pinleri ve aynı kararı veriyor. Z32 türü set beklentisi (×2) yalnız Çağrı A puanlamasında fark yaratıyor.
- Yanlış alarm: yok. Tetiklenmediği için olamaz.

### DESTEKLENMEYEN_OZELLIK dökümü (bütün turlar)

| Set | İstek | Tur: ad | Son durum | Değerlendirme |
|---|---|---|---|---|
| v4 | — | — | — | 0 istek |
| v3 | — | — | — | 0 istek |
| v5 | Z27 | 1: Ethernet | desteklenmiyor | doğru |

Yanlış alarm 0. Hiçbir sette "dokunmatik buton", "SD kart", "SDIO", "paralel", "kamera modülü" türü dışarıda bırakılan sözcüklerde hata çıkmadı. Kaynak: `doc/dogrulama/kapsam_uyarisi_11a.md`.

### KAPSANMAYAN_CUMLE dökümü (son yanıtlar, modelsiz yeniden uygulama)

| Set | İstek / cümle | Uyarı alan | Değerlendirme |
|---|---|---|---|
| v4 | 36 / 38 | 0 | — |
| v3 | 45 / 61 | X01 «Seranın kontrol kartını tasarlıyorum.», X07 «Başta SD kart da düşünmüştüm ama vazgeçtim.» | ikisi doğru (Adım 11'de de) |
| v5 | 32 / 37 | 0 | — |

Adım 11'deki üç yanlış alarm (X32, Z25, Z26; hepsi emin_degilim) kalktı. Doğru uyarılar (X01, X07) duruyor.

### Elektriksel not dökümü

- v5'te not yalnız Z06'da çıktı. 14 sorudan başka hiçbirinde birim ya da elektriksel sözcük yok; yanlış alarm 0.
- v3 ve v4 isteklerinde soru yok.

### Süre

| Set | Toplam süre ortalama / ortanca / en uzun (sn) |
|---|---|
| v4 | 51.0 / 41.2 / 144.3 |
| v3 | 53.0 / 41.0 / 162.2 |
| v5 | 31.4 / 28.0 / 72.7 (Z27 2 tur, 59.1) |

v5 süre satırı artık doğru biçimde (Bölüm 5).

## Açık kalanlar

### Pilot sonu bilinen sınırlar (güncel)

1. **Koşular arası belirlenimsizlik (yeni, Z20):** aynı girdi, aynı model ve aynı Ollama süreci farklı koşularda farklı Çağrı A çıktısı verebiliyor; koşu içi tekrar aynı. Nedeni izden ayırt edilemiyor.
2. **Çok cihazlı SPI'de adet denetimi yok (yeni, Z20):** «bir X ve bir Y» sayıya çevrilmiyor; SPI ×1 iki cihaza tek CS verir, uyarı çıkmaz.
3. **L-6: ayrı I2C hattı ifade edilemiyor (yeni):** I2C ×N her zaman tek hat. Adres çakışması gibi nedenlerle ikinci hat gerekirse kullanıcı bunu bu pilotta isteyemez.
4. **Dayanağın cümle içi kapsamı:** dayanak cümlenin bir kısmını kapsıyorsa kalan kısım denetlenmiyor (Z27'deki «Ethernet PHY'yi» türü). Z27 artık desteklenmeyen sözlüğüyle yakalanıyor; sözlükte olmayan bir ad aynı yoldan sessiz geçebilir.
5. **Desteklenmeyen sözlüğü kapalı liste:** yalnız datasheet'te açıkça olmayan 6 özellik. Şüpheliler (paralel, LCD, kamera modülü, analog çıkış, dokunmatik buton) bilerek dışarıda. Bunlar model ve kullanıcıya kalıyor.
6. **Elektriksel değer yok:** not kaynak bölümü gösteriyor, değer vermiyor. "V" birimi tek harf; "V" ile biten bir model adı ya da "V" yazılmış bir başlık notu yanlış tetikleyebilir (ölçümde görülmedi).
7. **Boş ihtiyaçlı tamam'da KAPSANMAYAN_CUMLE** sürüyor ("Karta hiçbir şey bağlanmayacak." türü; görev kapsamı dışında bırakıldı).
8. **Z06 türü konu yanlışlığı:** model elektriksel soruyu pin_kisiti olarak ayırırsa konu cevabı yine kısıt tablosundan gelir; not cevabın soruyu karşılamadığını gösteriyor, ama konu denetlenmiyor.
9. **model_cikarimi + sayısız dayanak + adet > 1 uyarısı yok** (Adım 11 önerisi 2; Z27 artık başka yoldan yakalanıyor).
10. **adet_belirsiz denetimi yok** ("birkaç", "bazı"; Adım 11 önerisi 4; Z26 hükümle doğru sayıldı).
11. **cevap.arayuz_eksik'in "ne yazmalısın" listesinde RMT_TX / RMT_RX yok** (veritabanı mesajı).
12. Adım 10c listesinden sürenler:
    - Y29 eski konum uyarısı
    - L-2 tek I2S
    - Çağrı B ortak hat bilmiyor (SPI ve artık I2C; `--model-ata` yolu)
    - RMT kanal yönü (TRM okunmadı)
    - doğrulanmamış kart verisi (v0.2, Super Mini)
    - nanoESP32-C6 J5 USB parça girdisi
    - DAYANAK_SINIRI / BAGLAM_KONUSUZ ara turları
    - kodda duran iletiler (atayıcı mumkun_degil, SPI taşma, ortak hat satırları, I2C ortak hat satırı da eklendi)
    - kaynak etiketi denetimsiz
    - "can" sözcüğü

### Sonraki tur

1. Z20 türü: SPI dayanağında cihaz sayımı ya da "aynı hat" uyarısı (veritabanında bağlaç / sözcük listesi).
2. Koşular arası belirlenimsizlik: çekirdek izine `prompt_eval_duration` ve önbellek isabeti; aynı girdinin iki ayrı Ollama oturumunda karşılaştırılması.
3. Çağrı B'ye ortak hat bilgisi (SPI ve I2C; yuva listesinde, istem değişmeden).
4. Atama tablosunun "Pinin durumu" sütununa kart uyarıları (KART_PED, KART_PARCA).
5. Kart parça adı tekrarı ("BOOT BOOT butonu").
6. Teknik başvuru kılavuzundan RMT kanal yönleri.
7. nanoESP32-C6 J5 USB'nin `kart_parca`'ya eklenmesi.
8. Kodda duran iletilerin `durum_mesaji`'na taşınması (I2C ortak hat satırı dahil).
9. cevap.arayuz_eksik listesine RMT_TX / RMT_RX.
10. adet_belirsiz denetimi; model_cikarimi adet uyarısı.
11. Ayrı I2C hattı gerekiyorsa (L-6) bağlam bayrağı ya da açık ifade; Web AI / Sinan kararı.

Adım 12'ye (kapanış raporu) geçilmedi.

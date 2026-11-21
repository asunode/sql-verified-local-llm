# Adım 11 raporu: kapsam uyarısı ve v5 ölçümü (2026-11-21)

Adım 10c raporu kabul edildi. X24 hükmü `doc/olcum/2026-11-21_adim10c_v3_sonuc.md` sonuna eklendi: resmî sonuç 42/45, hükümle 45/45.

İstem ve sistem metni Adım 10c ile aynı (`ihtiyac_sistem.txt` 3ff741e27c2e). Bu adımda değişen tek davranış yeni bir uyarı. v5 ölçümünden sonra kod değiştirilmedi; aşağıdaki düzeltmeler yalnız öneri.

Commit'ler:
- `fa48856`: X24 hükmü
- `69e5238`: KAPSANMAYAN_CUMLE, modelsiz uygulayıcı, testler
- `6be9b71`: modelsiz uygulama (v3, v4)
- `2139ae7`: `pinsecim.tamolcum` (kartlı, sorulu tam hat ölçümü)
- `894cf2d`: v5 seti
- `e527cb6`: dondurma öncesi
- `93d28ce`: v5 ölçümü, dondurma sonrası, modelsiz uygulama (v3, v4, v5)
- rapor ve belgeler commit'i (WORKLOG)

## Kapsam uyarısı (kural, modelsiz uygulama sonuçları)

**Kural (KAPSANMAYAN_CUMLE, uyarı):**
- İstek ". ! ?" ile cümlelere bölünür (Çağrı A denetimindeki `CUMLE` deseni). Harf ya da rakam içermeyen parçalar atlanır.
- Bir cümle şu dayanakların hiçbiriyle karakter aralığı olarak örtüşmüyorsa uyarı verilir: ihtiyaçlar, pin_tercihleri, kullanilmayacak_pinler, diger_pin_bahisleri, sorular, baglam_ifadeleri, diger_ifadeler, desteklenmeyenler.
- İleti: «…» hiçbir şekilde değerlendirilmedi; pin ihtiyacı içeriyorsa ayrı ve açık bir cümleyle yaz.
- Tur açmaz, kararı değiştirmez. Komut satırında "1) İhtiyaçlar" altında `[UYARI]` satırı olarak görünür. Kapsamlı ölçüm raporunun son tur uyarıları tablosuna da girer.
- Kod: `cagrilar.ihtiyac_denetleyici` içinde `kapsanmayan_cumleler`.
- Testler (`testler/test_11.py`, set dışı cümleler): kapsanmayan cümle, diger_ifadeler'deki cümle, dayanağın cümlenin bir parçası olması, sessiz kaybolan ihtiyaç cümlesi, soru / bağlam / desteklenmeyen kapsaması, pin listesi dayanağı, emin_degilim, noktalama uçları, tur açmama, komut satırında görünme.
- Adım 11'den önceki dört testte yeni uyarı ayıklandı (o testler başka kodları sınıyor). `test_tamam_bos_ihtiyac_gecerli` artık uyarıyı açıkça bekliyor.

**Modelsiz uygulama** (`python -m pinsecim.kapsam`, sonuç `doc/dogrulama/kapsam_uyarisi.md`). Her isteğin Çağrı A son tur yanıtı yeniden denetlendi; v5'te uyarı ölçüm sırasında da çalışıyordu.

| İz | İstek | Cümle | Uyarı alan cümle |
|---|---|---|---|
| Adım 10c v4 | 36 | 38 | 0 |
| Adım 10c v3 | 45 | 61 | 3: X01, X07, X32 |
| Adım 11 v5 | 32 | 37 | 2: Z25, Z26 |

| İstek | Cümle | Durum | Değerlendirme |
|---|---|---|---|
| X01 | «Seranın kontrol kartını tasarlıyorum.» | tamam | doğru yakalama: bağlam dışı cümle hiçbir listeye girmemiş |
| X07 | «Başta SD kart da düşünmüştüm ama vazgeçtim.» | tamam | doğru yakalama (Adım 10c'de sessiz düşen cümle) |
| X32 | «Birkaç sensör ve bazı çıkışlar bağlayacağım.» | emin_degilim | yanlış alarm: istek emin_degilim + eksik ile değerlendirildi |
| Z25 | «Bahçem için bir şeyler yapmak istiyorum.» | emin_degilim | yanlış alarm (aynı tür) |
| Z26 | «Birkaç sensör bağlayacağım.» | emin_degilim | yanlış alarm (aynı tür) |

Özet:
- 5 uyarının 2'si doğru, 3'ü yanlış alarm. Yanlış alarmların hepsi aynı türden: emin_degilim yanıtında dayanak taşıyan alan yok, istek bütünüyle eksik kodlarıyla değerlendiriliyor. Kullanıcı aynı ekranda hem "Atama yapılmadı … ne yazmalısın" hem "hiçbir şekilde değerlendirilmedi" görüyor; iki ileti çelişiyor.
- Aynı tür: boş ihtiyaçlı tamam yanıtı ("Karta hiçbir şey bağlanmayacak.", eski birim testi) da uyarı alıyor. v3, v4 ve v5'te bu durum gerçek bir istekte çıkmadı.
- Kuralın yakalayamadığı: bir dayanak cümlenin herhangi bir parçasına değiyorsa cümlenin kalanı kapsanmış sayılıyor. Z27'de dayanak «RMII ile bağlayacağım», «Ethernet PHY'yi» hiçbir yerde değil; uyarı çıkmadı (Yanlışların analizi).

## v5 sonuç tablosu

- Set `setler/dogrulama/test_seti_v5.json` (SHA-256 `e3f6aed3…`). İstek metni, bayraklar ve beklenen metni Web AI tablosundan birebir alındı. Yapılı `kabul` ve `beklenen_sonuc` alanları beklenen metninin aktarımı.
- Ölçüm `doc/olcum/2026-11-21_adim11_v5_sonuc.md`: otomatik tablo ve her isteğin komut satırı çıktısı. Ham iz `2026-11-21_adim11_v5_ham.jsonl`.
- Dondurma `2026-11-21_adim11_dondurma.md`: öncesi `e527cb6`, sonrası aynı.
- Akış varsayılan: Çağrı A → cevaplayıcı → kod atayıcı. `--kart` verilen isteklerde atama kart düzeyinde.
- Süre: ortalama 33.4, ortanca 27.6, en uzun 125.1 sn (Z01, ilk istek). Sonuç belgesindeki süre satırı bozuk (DAI notu orada).

Sütunlar:
- **A:** ihtiyaç kümesi, sorular ve konu, durum, eksik, tercihler.
- **Karar:** atayıcının sonucu ya da pin_gerekmiyor / atama yok.
- **Uyarı ve mesaj:** beklenen metnindeki uyarı ve mesajlar komut satırı çıktısında var mı (elle).

| İstek | Verilen (A) | A | Karar | Uyarı ve mesaj |
|---|---|---|---|---|
| Z01 | soru pin_islevi | ✓ | pin_gerekmiyor ✓ | ✓ IO MUX işlevleri, Table 2-4 s. 20 |
| Z02 | soru pin_kisiti; tercih yok | ✓ | pin_gerekmiyor ✓ | ✓ strapping, Table 3-1 s. 33 |
| Z03 | soru arayuz_pinleri | ✓ | pin_gerekmiyor ✓ | ✓ CAN → TWAI TX/RX pinleri, kaynaklı |
| Z04 | soru arayuz_pinleri | ✓ | pin_gerekmiyor ✓ | ✓ ADC AIN (QFN32 7 pin) |
| Z05 | soru paket_pinleri | ✓ | pin_gerekmiyor ✓ | ✓ 30 GPIO, Table 2-1 |
| Z06 | soru **pin_kisiti** (beklenen diger) | ✗ | pin_gerekmiyor ✓ | ✗ tabloda_yok iletisi yok; uydurma değer yok, GPIO3 hatası yok |
| Z07 | soru arayuz_pinleri | ✓ | pin_gerekmiyor ✓ | ✓ cevap.arayuz_eksik + ne yazmalı |
| Z08 | soru pin_islevi | ✓ | pin_gerekmiyor ✓ | ✓ cevap.gpio_eksik + ne yazmalı |
| Z09 | GPIO_OUT, GPIO_IN; soru pin_kisiti | ✓ | atandi ✓ | ✓ GPIO15 tercih değil, strapping cevabı |
| Z10 | GPIO_IN ×2; soru kart_led | ✓ | atandi ✓ | ✓ PD2 GPIO15 [DOĞRULANMADI], görev notu; atama H1-8/H1-7, parça ve ped yok |
| Z11 | soru kart_buton | ✓ | pin_gerekmiyor ✓ | ✓ BOOT GPIO9 [DOĞRULANMADI] |
| Z12 | soru kart_pin_cikisi | ✓ | pin_gerekmiyor ✓ | ✓ J1 ve J6, "kaynak belgede", doğrulanmamış satır 0 |
| Z13 | soru kart_led | ✓ | pin_gerekmiyor ✓ | ✓ cevap.kart_eksik, liste ve örnek SuperMini |
| Z14 | GPIO_IN ×4, GPIO_OUT ×4 | ✓ | atandi ✓ | ✓ 8 konnektör pini, ped ve parça yok |
| Z15 | RMT_TX, RMT_RX | ✓ | atandi ✓ | ✓ GPIO0/GPIO1; GPIO8 kullanılmadı |
| Z16 | GPIO_IN, tercih 22 | ✓ | atandi ✓ | ✓ tercih uygulandı + KART_PED |
| Z17 | GPIO_IN, tercih 8 | ✓ | atandi ✓ | ✓ uygulandı + KART_PARCA (D2 WS2812B) + PIN_STRAPPING |
| Z18 | PWM ×2 | ✓ | atandi ✓ | ✓ "kart verisi doğrulanmadı" notu |
| Z19 | GPIO_OUT, ADC, tercih 15 | ✓ | atandi ✓ | ✓ uygulandı + KART_PARCA (PD2) + PIN_STRAPPING |
| Z20 | SPI ×2 | ✓ | atandi ✓ | ✓ tek hat, ortak SCLK/MOSI/MISO, 2 CS |
| Z21 | SPI ×7 | ✓ | mumkun_degil ✓ | ✓ "7 CS gerekiyor, en çok 6 var (… 4.2.1.2 p.51)" |
| Z22 | SPI ×2 + ×1 | ✓ | atandi ✓ | ✓ tek hat, 3 CS; bağlam boş, BAGLAM_CELISKI / DIGER_BAGLAM yok |
| Z23 | GPIO_OUT ×25 | ✓ | mumkun_degil ✓ | ✓ "Toplam 25 sinyal … uygun pin sayısı 19" |
| Z24 | GPIO_IN ×14 | ✓ | atandi ✓ | ✓ (12 serbest + 2 uyarılı pin, uyarılarıyla) |
| Z25 | emin_degilim [cihaz_belirsiz] | ✓ | atama yok ✓ | ✓ neden + ne yazmalı; fazladan KAPSANMAYAN_CUMLE (yanlış alarm) |
| Z26 | emin_degilim [cihaz_belirsiz] | ✗ | atama yok ✓ | kısmen: neden + ne yazmalı var, adet_belirsiz yok; fazladan KAPSANMAYAN_CUMLE |
| Z27 | **tamam GPIO_OUT ×5** (beklenen desteklenmiyor) | ✗ | **atandi** ✗ | ✗ durum mesajı yok; yalnız "[model çıkarımı — kontrol edin]" işareti |
| Z28 | ADC ×2; iki diger ifade | ✓ | atandi ✓ | ✓ DIGER_IHTIYAC_IZI yok, bağlam boş (1. turda BAGLAM_KONUSUZ ×2, 2. turda düzeldi) |
| Z29 | GPIO_OUT ×3; bağlam USB | ✓ | atandi ✓ | ✓ BAGLAM_CELISKI ("--no-usb verildi; komut satırı esas alındı") |
| Z30 | GPIO_OUT, tercih 24 | ✓ | tercih_uygulanamadi ✓ | ✓ neden (flash, 2.3.5 s. 25) + öneri + ALTERNATİF |
| Z31 | GPIO_OUT; ikinci cümle diger | ✓ | atandi ✓ | ✓ diger_ifadeler'de |
| Z32 | **I2C ×1**; soru pin_kisiti | ✗ | atandi ✓ | ✓ GPIO6/7 tercih değil, JTAG uyarılı cevap (hakem itirazı 1) |

**Toplam:**
- Çağrı A 28/32 (Z06, Z26, Z27, Z32). Z32 itirazı kabul edilirse 29/32.
- Karar 31/32 (Z27).
- Beklenen uyarı ve mesajların hepsi var: 29/32 (Z06, Z26, Z27 eksik).
- 31 istek 1. turda, Z28 2. turda geçti. Çağrı A'da KULLANICIYA ve JSON_GECERSIZ yok.

## Kategori özeti

| Kategori | İstekler | A | Karar | Uyarı ve mesaj |
|---|---|---|---|---|
| soru | Z01–Z08 | 7/8 | 8/8 | 7/8 (Z06) |
| karışık | Z09, Z10, Z32 | 2/3 (Z32, itirazlı) | 3/3 | 3/3 |
| kart | Z11–Z14, Z16–Z19 | 8/8 | 8/8 | 8/8 |
| SPI | Z20–Z22 | 3/3 | 3/3 | 3/3 |
| RMT | Z15 | 1/1 | 1/1 | 1/1 |
| sayı | Z23, Z24 | 2/2 | 2/2 | 2/2 |
| emin_degilim | Z25, Z26 | 1/2 (Z26) | 2/2 | 1/2 (Z26); ikisinde fazladan uyarı |
| desteklenmiyor | Z27 | 0/1 | 0/1 | 0/1 |
| bağlam ve diğer | Z28–Z31 | 4/4 | 4/4 | 4/4 |

## Mutlak ölçütler

| Ölçüt | Sonuç |
|---|---|
| Uydurma pin: 0 | **karşılandı.** Bütün turlarda PIN_UYDURMA 0. Çıktılardaki her GPIO ya metinde, ya veritabanı tablosunda ya da atayıcının atamasında. Z06'da akım değeri uydurulmadı. |
| Model cevap metni yazmaz | **karşılandı.** Şemada soru öğesi yalnız `soru` ve `konu` taşıyor (ham izde başka alan yok). 14 sorunun bütün cevapları veritabanından, kaynaklı ya da `cevap.*` durum mesajı. |
| Sessiz yanlış: 0 | **karşılanmadı: 2.** Z27 (ağır: desteklenmeyen arayüze pin atandı) ve Z06 (hafif: yanlış konu, soru cevapsız kaldı, uyarı yok). Z26 kullanıcıya gösterildi; Z32 set beklentisine itiraz. |

## Yanlışların analizi

**Z27 «Ethernet PHY'yi RMII ile bağlayacağım.»: sessiz yanlış (ağır)**
- **Ne oldu:** Model durumu `tamam` verdi, «RMII ile bağlayacağım» dayanağıyla GPIO_OUT ×5 (model_cikarimi). Atayıcı GPIO0–3 ve GPIO10'a atadı.
  - ESP32-C6'da Ethernet MAC / RMII yok: Datasheet v1.6'nın çevre birimleri listesinde Ethernet geçmiyor. Bu yüzden beklenen `desteklenmiyor`.
  - RMII 5 değil 7–9 hat ister ve 50 MHz saat gerektirir; düz GPIO ile yapılamaz.
- **Kontrol:** yakalamadı.
  - SAYI_UYUSMAZ: dayanakta sayı yok.
  - DAYANAK: dayanak metinde birebir var.
  - KAPSANMAYAN_CUMLE: cümle dayanakla örtüşüyor.
- **Uyarı:** yalnız her model çıkarımında görülen "[model çıkarımı — kontrol edin]" işareti. Kullanıcı Ethernet'in desteklenmediğini öğrenmiyor, atanmış 5 pin görüyor.
- **Kök neden:** model (desteklenmeyen arayüzü uydurma bir GPIO sayısına çevirdi) ve kod (desteklenmeyen arayüz adlarına karşı denetim yok).
- **Öneri:**
  - (a) Veritabanında desteklenmeyen arayüz sözlüğü (RMII, Ethernet, MII, DVP / kamera, MIPI, SDIO host, USB host / OTG …). Metinde geçer ve durum `tamam` ise Çağrı A'ya hata: "move it to desteklenmeyenler". Sözlük genel; set cümlesi istem örneği olmaz.
  - (b) model_cikarimi ihtiyacında adet > 1 ve dayanakta sayı yoksa kullanıcıya uyarı: "adet modelin tahmini". 4×4 tuş takımı gibi meşru durumlar olduğu için hata değil.
  - (c) KAPSANMAYAN_CUMLE'nin cümle içi kapsamaya genişletilmesi (Açık kalanlar).

**Z06 «GPIO3'ten en fazla kaç mA çekebilirim?»: sessiz yanlış (hafif)**
- **Ne oldu:** Model soruyu `pin_kisiti` konusuyla ayırdı (beklenen `diger`). Cevaplayıcı GPIO3'ün kısıt tablosuna baktı: "GPIO3: kısıt tablosunda satırı yok. Bu bağlamda GPIO3 serbest (kural ihlali yok)."
  - Akım sorusu cevaplanmadı. "Tabloda yok" iletisi (`cevap.tabloda_yok`) çıkmadı.
  - Değer uydurulmadı. GPIO3 bahsi soru içinde kaldı; tercih ya da bahis hatası yok.
- **Kontrol:** yakalamadı; konu seçimi denetlenmiyor (konu kapalı listede ve geçerli).
- **Uyarı:** yok. Kullanıcı cevabın sorusuna uymadığını kendisi fark etmeli.
- **Kök neden:** model (konu) ve kod (cevaplayıcı sorunun neyi sorduğunu denetlemiyor).
- **Öneri:** pin_kisiti / pin_islevi cevabında soru metninde birim ya da nicelik sözcüğü (mA, A, V, MHz, °C, "kaç", "en fazla") geçiyorsa cevaba `cevap.tabloda_yok` eki: "Sorudaki nicelik kısıt tablosunda yok". Birim listesi veritabanında.

**Z26 «Birkaç sensör bağlayacağım.»: yanlış, kullanıcıya gösterildi**
- **Ne oldu:** emin_degilim doğru, eksik [cihaz_belirsiz]. Beklenen eksik listesinde adet_belirsiz vardı ("birkaç").
- **Kontrol / uyarı:** yanlış, kullanıcıya emin_degilim bildirimiyle gösterildi: "Karta ne bağlanacağı belli değil." ve ne yazmalı örneği. Atama yok, zarar yok. Ama ileti adet belirsizliğini söylemiyor. Fazladan KAPSANMAYAN_CUMLE (yanlış alarm) da çıktı.
- **Kök neden:** model.
- **Öneri:** belirsiz nicelik sözcükleri ("birkaç", "bazı", "birçok", "bir sürü") veritabanında. Metinde geçer ve durum emin_degilim ise eksik içinde adet_belirsiz yoksa Çağrı A'ya hata (DURUM_TUTARSIZ türü).

**Z32 «Bir I2C ekran ve bir I2C sıcaklık sensörü kullanacağım. GPIO6 ve GPIO7 I2C için uygun mu?»: set beklentisi**
- **Ne oldu:** Model I2C ×1 verdi (dayanak iki cihazı kapsıyor), beklenen I2C ×2. Soru pin_kisiti, GPIO6/7 tercih değil, atama atandi (GPIO0/1).
- **Kontrol:** paylaşımlı hatta sayı denetlenmiyor (bilerek).
- **Kök neden:** set beklentisi. Bu sistemde I2C ×2 iki I2C denetleyicisi demek ve atayıcı mumkun_degil verir. Modelin ×1'i, beklenen kararı (atandi) üreten tek yanıt (hakem itirazı 1).

## Hakem itirazları

1. **Z32: "I2C ×2 (paylaşımlı hat) … atandi" bu sistemde birlikte olamaz.**
   - Atayıcı I2C ×2'yi iki ayrı I2C birimi sayar: "I2C için 2 birim gerekiyor, çipte en çok 1 kullanılabilir (I2C; ESP32-C6 Datasheet v1.6, 4.2.1.3 p.51)". Belge: "Two I2C controllers: one in the main system and one in the low-power system"; ana sistemde bir tane.
   - Ortak hat (T-68) yalnız SPI için var (`ortak_hat_secim` SPI → CS). I2C'de aynı hattaki cihazlar adresle ayrılır, ayrı seçim pini yoktur.
   - Model I2C ×1 verdi ve karar beklenen gibi atandi.
   - Seçenekler: (a) Z32 kabulüne I2C ×1 eklenir; (b) I2C ×N tek hat olarak modellenir (atayıcıda seçim sinyali olmayan ortak hat; kod değişikliği). Karar Sinan'ın.
2. **Z06 (itiraz değil, not):** Akım bilgisi kaynak belgede var: Datasheet v1.6, 5.4 DC Characteristics (Table 5-4, s. 65), I_OH yüksek seviye kaynak akımı 40 mA (VDD = 3.3 V). Ama yapılı tablolarda yok. "tabloda_yok" beklentisi tablolara göre doğru. Tabloya eklenmesi ayrı bir karar.

Başka beklenti datasheet ya da kart verisiyle çelişmiyor. Kontrol edilenler:
- Z10, Z11, Z19: Super Mini GPIO15 PD2, GPIO9 BOOT, GPIO8 LED1; hepsi `dogrulanmadi`.
- Z12: nanoESP32-C6 v1.0 konnektörleri J1 ve J6, `kaynak_belge`.
- Z13: QFN32'ye uyan tek kart SuperMini.
- Z17: v1.0'da GPIO8 D2.
- Z23 / Z24: QFN40 varsayılan bağlamda 19 uygun pin.
- Z30: GPIO24 flash pini.

## Tekrarlanabilirlik

Z01, Z10 ve Z20 ikinci kez koşuldu (iz satırları 33–35). Üçünde de Çağrı A ham yanıtları birebir aynı; komut satırı çıktısı da "Süre:" satırı dışında aynı (soru cevapları, kart düzeyi atama ve ortak hat satırı dahil).

İlk istek Z01 125 sn sürdü (model belleğe yükleniyor ve önbellek ısınıyor), tekrarı 24.7 sn. Ham yanıt yine aynı.

## Açık kalanlar

**Bu ölçümden çıkan öneriler (kod değiştirilmedi):**
1. Desteklenmeyen arayüz sözlüğü ve denetimi (Z27). Pilotun en ağır açığı: model desteklenmeyen bir arayüzü GPIO'ya çevirince hiçbir denetim durdurmuyor.
2. model_cikarimi + sayısız dayanak + adet > 1 için kullanıcı uyarısı (Z27 türü).
3. Sorudaki nicelik ya da birim tabloda yoksa cevaba "tabloda yok" eki (Z06).
4. Belirsiz nicelik sözcüklerinde adet_belirsiz denetimi (Z26).
5. KAPSANMAYAN_CUMLE: emin_degilim'de (ve boş ihtiyaçlı tamam'da) ya verilmesin ya da ileti emin_degilim bildirimiyle çelişmesin (X32, Z25, Z26 yanlış alarmları). İkinci olarak cümle içi kapsama: dayanak cümlenin yalnız bir ucuna değiyorsa kalan kısım için ayrı uyarı (Z27'deki «Ethernet PHY'yi»).
6. I2C ×N tek hat (Z32; hakem itirazı 1'in kararına bağlı).
7. `tamolcum.rapor` süre satırı biçim hatası (sonuç belgesinde DAI notu).
8. cevap.arayuz_eksik'in "ne yazmalısın" listesinde RMT_TX / RMT_RX yok (Z07 çıktısı); liste kodda değil veritabanı mesajında sabit.

**Önceki adımlardan süren (Adım 10c raporu "pilot sonu bilinen sınırlar"):** Y29 eski konum uyarısı, L-2 tek I2S, Çağrı B'nin ortak SPI hattını bilmemesi, RMT kanal yönü (TRM), doğrulanmamış kart verisi (v0.2, Super Mini), nanoESP32-C6 J5 USB'nin parça girdisi, DAYANAK_SINIRI / BAGLAM_KONUSUZ ara turları (v5'te Z28), kodda duran iletiler, kaynak etiketi denetimsiz, kart parça adı tekrarı ("BOOT BOOT butonu", Z11'de de görüldü), tablo "Pinin durumu" sütununda kart uyarıları yok.

Adım 12'ye (kapanış raporu) geçilmedi.

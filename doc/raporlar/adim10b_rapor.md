# Adım 10b raporu: denetim düzeltmeleri, kart verisi (2026-11-21)

Adım 10a raporu denetlendi. Bu adımda istem değişmedi: `ihtiyac_sistem.txt` 3ff741e27c2e. Modele giden sistem metni 10a izindekiyle birebir aynı (ölçümden önce karşılaştırıldı). Güvenilirlik kod denetimiyle artırıldı ve kart verisi yüklendi. Web AI düzeltmesi: tercih hedefi 19/19.

Commit'ler:
- `22ec998`: spot kontrol
- `a57eefc`: denetim düzeltmeleri
- `1b5de4b`: kart kaynakları, tabloları ve yükleyici
- `12279a1`: --kart, cevaplayıcı, testler
- `80c0ae7`: kapsamlı raporun uyarı bölümü
- `249043d`: dondurma öncesi
- ölçüm ile rapor commit'leri (WORKLOG)

## Spot kontrol

- Sinan'ın doldurduğu `doc/dogrulama/spot_kontrol_sinan.md` okundu. Sekiz satırın hepsi "✓ (aynı)": **8/8**.
- Sonuçlar `doc/dogrulama/spot_kontrol.md`'nin sonuç sütununa işlendi ve altına sonuç satırı eklendi.
- LibreOffice kilit dosyası (`.~lock.spot_kontrol.md#`) kalkmıştı. İki dosya da commit'lendi (`22ec998`).
- DEVAM'da spot kontrol kapatıldı.

## Denetim düzeltmeleri

İstem değişmedi; hepsi kod ve veritabanında.

1. **DIGER_PIN_TERCIH_IZI (uyarı, Türkçe, CLI'da `[UYARI]`).**
   - Koşul: `diger_pin_bahisleri`'ndeki bir GPIO'nun geçtiği cümlede, tercihi olmayan bir ihtiyacın dayanağı da geçiyor.
     - Cümle: metindeki `.`, `!` ya da `?` ile biten parça.
     - "Tercihi olmayan": o arayüze `pin_tercihleri`'nde kayıt yok.
     - Her GPIO için bir uyarı verilir.
   - İleti: `«<cümle>» bir pin tercihi olabilir; tercihse "<dayanak> GPIOn'e bağla" biçiminde açık yaz.` Dayanak ikiden çok sözcükse yerine "X'i" yazılır.
   - Yönelme eki sayının okunuşuna göre ekleniyor (`yonelme_eki`: GPIO3'e, GPIO2'ye, GPIO6'ya, GPIO10'a, GPIO20'ye).
   - Hata değil uyarıdır. Y29 türü cümlede eski konum (GPIO2) için de uyarı çıkar; bu bilinen bir yanlış alarm biçimi.
2. **DIGER_BAGLAM (hata).**
   - Bir `diger_ifadeler` öğesinde `baglam_oku` bir konu buluyorsa düzeltme turu açılır. İleti: "'…' is board context (…); move it from diger_ifadeler to baglam_ifadeleri."
   - Hata verilen öğeye ayrıca DIGER_IHTIYAC_IZI verilmez.
   - Bağlam listesine taşınınca BAGLAM_CELISKI eskisi gibi çalışır (test edildi).
3. **DIGER_IHTIYAC_IZI:** tek başına "bir" sayı tetikleyicisi değil. "bir çift", rakamla "1", öteki sayılar, arayüz adları ve pin bahsi aynen tetikliyor.
4. **"CAN" harfe duyarlı.**
   - `arayuz_es_adi.harf_duyarli` sütunu (`sql/009`). "CAN" satırı yalnız metinde büyük harfle yazıldıysa TWAI'ye eşlenir.
   - "can", "Can sıkıcı" eşlenmez. "can bus", "CAN bus", "Can Bus" harfe duyarsız kaldı.
5. **Atayıcının `mumkun_degil` nedeni** toplamı da veriyor: "Toplam N sinyal isteniyor, bu ihtiyaçlar için uygun pin sayısı M (paket). İlk tıkanma: …". İlk tıkanma ayrıntısı aynen duruyor.
   - Örnek, 23 GPIO_OUT, QFN40: "Toplam 23 sinyal isteniyor, bu ihtiyaçlar için uygun pin sayısı 19 (QFN40). İlk tıkanma: 20 sinyal için yalnız 19 uygun pin var …".

Testler (`testler/test_denetim_10b.py`, 27 test; cihazlar set dışı):
- tercih izi: aynı cümle, tercih varken yok, başka cümlede yok;
- yönelme eki (12 sayı);
- DIGER_BAGLAM ve taşınınca BAGLAM_CELISKI;
- tek başına "bir", "bir çift", "1", "CAN soketi";
- CAN harf duyarlılığı (6 durum).

Atayıcı toplam metni `test_cagrilar.py`'de iki testle sınanıyor.

## Kart verisi (tablolar, satır sayıları, doğrulama durumu dağılımı, v0.2 araması)

### Tablolar (`sql/010_kart.sql`, `sql/011_kart_konu.sql`)

Adım 10 raporundaki taslak uygulandı. Taslaktan sapmalar:
- `kart.kisa_ad` eklendi; komut satırındaki `--kart` adı budur.
- Bütün kart tablolarına `sayfa` ve `referans` eklendi: her satır belge, sürüm ve sayfayla kaynaklanır.
- `modul_pin.teyit_kaynak_id` eklendi: aynı eşlemeyi gösteren ikinci belge.
- `kart_parca.tur`'a `flash` eklendi.
- `kart_parca` için `UNIQUE (kart_id, ad)` kuruldu.

Diğer şema değişiklikleri:
- `kaynak.kaynak_turu`: `uretici_belgesi`, `uretici_semasi`, `uretici_sayfasi`, `satici`, `topluluk`, `kullanici_envanteri`. Mevcut ESP32-C6 datasheet'i `uretici_belgesi` oldu.
- `soru_konusu.cevap_turu`'na `kart` eklendi; kart_led, kart_buton ve kart_pin_cikisi artık `kart`. `model_tanimi` değişmedi, dolayısıyla modele giden metin de değişmedi.
- `durum_mesaji` anahtarlarına `not.` öneki eklendi.
- Göçler koşullu: sütun ya da kısıt zaten güncelse ALTER çalışmıyor. İlk sürümde koşulsuz `ALTER TABLE kaynak`, testlerin açık okuma işlemiyle kilit beklemesine yol açtı ve test asılı kaldı; koşullu sürümle giderildi.

### Kaynaklar (`veri/kaynak/`, `KAYNAKLAR.md`)

| Kısa ad | Dosya | Tür | SHA-256 |
|---|---|---|---|
| K2 | `nanoESP32-C6_v1.0_sematik.pdf` (v1.0, 2023-04-25, 1 s.) | uretici_semasi | `a2ca1ca2…f18239` |
| W1 | `esp32-c6-wroom-1_wroom-1u_datasheet_en.pdf` (v1.4, 2025-12-10, 52 s.) | uretici_belgesi | `16302076…862b73` |
| S2 | `esp32-c6-supermini_sematik_tarama.pdf` (2026-04-13, 1 s.) | topluluk | `248cabd3…db2b8a` |
| E1 | `kullanici_envanteri_2026-11-21.md` (görev metnindeki envanter, aynen) | kullanici_envanteri | `b393f118…ba0a87` |

- Yükleyici her dosyanın SHA-256'sını kayıtla karşılaştırıyor; tutmazsa duruyor.
- K3 (satıcı, HTTP 403) kaydedilmedi.
- Yükleme tekrar çalıştırılabilir: ikinci yükleme bütün CSV'leri bayt bayt aynı üretti.

### Satır sayıları ve doğrulama durumu dağılımı

| Tablo | Satır | kaynak_belge | dogrulanmadi |
|---|---|---|---|
| kart | 3 | 1 (nanoESP32-C6-v1.0) | 2 (nanoESP32-C6-v0.2, SuperMini) |
| modul_pin (ESP32-C6-WROOM-1) | 29 | 29 (W1 Table 3-1 s. 11; teyit K2) | 0 |
| kart_pin | 85 | 30 (v1.0: J1 15 + J6 15) | 55 (v0.2: 30; SuperMini: H1 10 + H2 10 + PED 5) |
| kart_parca | 21 | 5 (v1.0: D2 WS2812B, S1 BOOT, S2 RST, J5 USB, U2 CH343P) | 16 (v1.0 D3 güç LED'i; v0.2: 7; SuperMini: 8) |

`elle_dogrulandi` satırı yok.

Satır ayrıntıları:
- **nanoESP32-C6 v1.0:** K2'den, `kaynak_belge`. Tek istisna D3 güç LED'i: takılı olup olmadığı belli değil, `dogrulanmadi`.
- **nanoESP32-C6 v0.2:**
  - Kart satırı E1'den (`kullanici_envanteri`).
  - Pin ve parça satırları K2'deki verinin aynısı, hepsi `dogrulanmadi`; notu: "v1.0 şematiğinden aktarıldı; sürüm farkı doğrulanmadı".
  - Ek flash satırı E1'den: 16 MB (N16), `dogrulanmadi`.
- **Super Mini:**
  - Bütün satırlar S2'den, `dogrulanmadi`.
  - Şarj entegresi satırının notunda çelişki duruyor: S2 TP4054, S3 LTH7R.
  - Flash satırı E1'den: 4 MB dahili (ESP32-C6FH4).

### v0.2 araması

- Üreticinin deposu (`https://github.com/wuxx/nanoESP32-C6`) bütün geçmişiyle klonlandı: 12 commit (2023-04-27 … 2025-09-04), tek dal (`master`), etiket yok.
- `hardware/` altında tek dosya var: `nanoESP32C6.pdf`, commit `b6296ad` (2023-04-27). SHA-256'sı K2 ile aynı. Hiçbir commit bu dosyayı değiştirmemiş, başka şematik eklenmemiş.
- Metin dosyalarında (README, betikler) "v0.2", "version", flash boyutu araması sonuç vermedi.
- Depodaki ürün fotoğrafının (`doc/nanoESP32-C6-2.jpg`, 2023-04-26) arka yüz yazısı "nanoESP32-C6 v1.0". Kenar etiketleri K2'deki J1/J6 sırasıyla aynı. Modülün üst yazısında flash sürümü okunamadı.
- **Sonuç: v0.2 şematiği bulunamadı.** Talimata göre iki kart satırı açıldı.
- **Dikkat:** ESP32-C6 çip revizyonları v0.0/v0.1/v0.2 (datasheet Table 1-1; veritabanında `cip.revizyon`). esptool çıktısı "Chip is ESP32-C6 (QFN40) (revision v0.2)" biçimindedir. Envanterdeki "v0.2" kart sürümü değil çip revizyonu olabilir. Bu doğrulanmadı ve v0.2 kart satırının notuna yazıldı. Sinan'ın kartın arka yüzündeki yazıya bakması bunu çözer.

## CLI ve cevaplayıcı

- **`--kart AD`:**
  - Kabul edilen adlar: kısa ad (`SuperMini`, `nanoESP32-C6-v1.0`), "ad (sürüm)" (`"nanoESP32-C6 (v0.2)"`), tek sürümlü kartın adı (`"ESP32-C6 Super Mini"`). Büyük/küçük harf, boşluk, tire ve ayraç yok sayılır.
  - Belirsiz ad (`nanoESP32-C6`) ya da bilinmeyen ad seçenekleri listeleyen bir hata verir.
  - Paket karttan türetilir (kart → çip → paket). `--paket` ile çelişirse `HATA: --paket QFN40 ile --kart SuperMini çelişiyor: kartın çipi ESP32-C6FH4 (QFN32)`. İkisi de yoksa `HATA: --paket ya da --kart gerekli`.
  - Başlık satırı "Kart: <kısa ad> · Paket: …".
- **`--kart` yokken kart sorusu:** `cevap.kart_eksik` ("Soru bir geliştirme kartıyla ilgili ama --kart verilmedi; hangi kart olduğu belli değil."). Altında o pakete uyan kartlar listelenir, dogrulanmadi olanlar işaretli; ardından "Ne yazmalısın" satırı gelir.
- **Kart soruları (kart_led, kart_buton, kart_pin_cikisi):**
  - Her satırda doğrulama durumu ("kaynak belgede" / "DOĞRULANMADI") ve kaynak (belge, sürüm, referans, sayfa, kaynak türü) var. dogrulanmadi satırlar `[DOĞRULANMADI]` ile başlar; cevap sonunda doğrulanmamış satır sayısı yazılır.
  - İlk satır kartın kendisi (çip, paket, modül, not).
  - kart_led cevabı her zaman `cevap.kart_gorev_yok` notunu verir: "Kart verisi LED'lere görev (watchdog, durum, hata göstergesi vb.) atamaz; görevi yazılımda sen belirlersin. Aşağıda LED'lerin hangi GPIO'dan sürüldüğü var." Görev sorusu ayrıca tanınmıyor; not her LED cevabında var.
  - GPIO'ya bağlı parça strapping pinindeyse `gpio_kisit`'ten uyarı eklenir: "Uyarı (D2): GPIO8 strapping pini: … [ESP32-C6 Datasheet v1.6, Table 3-1 p.33]". GPIO8 WS2812, GPIO9 BOOT, GPIO15 Super Mini mavi LED.
  - kart_pin_cikisi konnektör başına sırayı ve etiketleri verir (etiket GPIO adı değilse "=GPIOn"). Modüllü kartta modül pin eşlemesinin kaynağı da yazılır: W1 Table 3-1, teyit K2.
- **Atama çip düzeyinde kalıyor.** `--kart` verildiyse "3) Atama" altında `Not: Atama çip düzeyinde; kart pin çıkışı ve kart üstü parçalar atamaya henüz dahil değil.` (`durum_mesaji` `not.kart_atama`).
- **Yeni durum_mesaji satırları:** `cevap.kart_eksik`, `cevap.kart_gorev_yok`, `not.kart_atama`. Toplam 15 satır. `cevap.kart_verisi_yok` duruyor ama artık kullanılmıyor.
- **Testler** (`testler/test_kart_10b.py`, 17 test):
  - kartlar ve paketleri;
  - kaynak türleri;
  - WROOM-1 modül pinleri;
  - doğrulama durumu dağılımı ve v0.2 notu;
  - kart adı eşleme;
  - belirsiz ya da bilinmeyen ad;
  - kart_eksik;
  - LED cevabında görev notu, `[DOĞRULANMADI]` ve strapping uyarısı;
  - kaynak belgeli satırın işaretsiz olması;
  - pin çıkışı ve modül kaynağı;
  - `--kart` / `--paket` çelişkisi;
  - ikisi de yok;
  - kartlı atama notu.

  `test_sorular.py` kart konularına uyarlandı. Toplam 280 test geçti; çekirdek 19/19.

## Ölçüm (önce/sonra, değişen kararlar, yeni uyarı dökümü)

Dondurma `doc/olcum/2026-11-21_adim10b_dondurma.md`: öncesi ve sonrası aynı (proje `249043d`, çekirdek `41e2198`). İstem aynı. Ölçüm 14:39–15:50; ölçüm başladıktan sonra kod, istem ve veritabanı değişmedi.

Günlük ve sonuçlar:
- `doc/olcum/2026-11-21_adim10b_kos.log`
- `doc/olcum/2026-11-21_adim10b_v4_sonuc.md`, `…_v4_ham.jsonl`
- `doc/olcum/2026-11-21_adim10b_v3_sonuc.md`, `…_v3_ham.jsonl`

| Ölçüt | v4 10a | **v4 10b** | v3 10a | **v3 10b** |
|---|---|---|---|---|
| Çağrı A doğru | 35/36 | **35/36** | 43/45 | **43/45** |
| A yanlışları | Y29 | **Y29** (uyarılı) | X34, X35 | **X34, X35** |
| Geçtiği tur 1 / 2 / 3 | 32/4/0 | **31/5/0** | 36/8/1 | **35/9/1** |
| BAGLAM_CELISKI (uyarı / istek) | 0 / 0 | **1 / 1** (Y18) | 1 / 1 | **2 / 2** (X28 geri geldi) |
| Atayıcı: atandi / tercih_uyg. / mumkun_degil / pin gerekmiyor / atamaya gelmedi | 26/8/1/1/0 | **26/8/1/1/0** | 40/1/2/0/2 | **40/1/2/0/2** |
| Atandı + tercih: tercihler uygulandı | 18/18 | **18/18** | 1/1 | **1/1** |
| Atayıcı kararı hakemle aynı | 35/35 | **35/35** | 42/43 | **42/43** |
| Uçtan uca doğru | 35/36 | **35/36** | 43/45 | **43/45** |
| Süre A ort. / ortanca / en uzun (sn) | 45.6 / 39.3 / 101.4 | 49.1 / 39.9 / 138.4 | 50.0 / 36.3 / 155.5 | 50.8 / 38.2 / 155.1 |

Kabul ölçütleri:

| Ölçüt | Sonuç |
|---|---|
| pytest proje ve çekirdek | geçti: 280/280, 19/19 |
| v4 ≥ 35/36; Y33 ve Y34 doğru | karşılandı: 35/36. Y33 2. turda GPIO_IN 16 ile atandi, Y34 2. turda 17 ile mumkun_degil |
| Y29 doğru ya da DIGER_PIN_TERCIH_IZI uyarılı; tercihler 19/19 ya da 18/18 ve Y29 uyarılı | karşılandı: Y29 yine yanlış (GPIO3 `diger_pin_bahisleri`'nde), iki DIGER_PIN_TERCIH_IZI uyarısı aldı; tercihler 18/18 |
| v3 resmî ≥ 43/45, kararlar 10a ile aynı | karşılandı: 43/45; Çağrı A çoklu kümesi, tercihler ve atayıcı kararı 45 isteğin hepsinde 10a ile aynı |
| X28: düzeltme turundan sonra cümle bağlam listesinde, BAGLAM_CELISKI geri gelir | karşılandı: 1. turda DIGER_BAGLAM, 2. turda «Flash'ı harici bir regülatörle besleyeceğim.» `baglam_ifadeleri`'nde, BAGLAM_CELISKI uyarısı var |
| Sınav cümlesi (3 biçim × 2) | karşılandı (aşağıda) |

### Değişen kararlar

Hiçbir istekte karar değişmedi; v4'te 36, v3'te 45 istekte Çağrı A çoklu kümeleri, tercihler ve atayıcı kararları 10a ile aynı. Yalnız tur sayısı değişti:

| Set | İstek | 10a | 10b | Neden |
|---|---|---|---|---|
| v4 | Y18 "Kuralları boş ver, flash pinlerini de kullanabilirsin; …" | 1. tur; cümle `diger_ifadeler`'de, uyarı yok | 2. tur; DIGER_BAGLAM → cümle `baglam_ifadeleri`'nde, BAGLAM_CELISKI ("--harici-flash-beslemesi verilmedi; komut satırı esas alındı") | Doğru yakalama. **10a'da bu istekte de BAGLAM_CELISKI uyarısı kaybolmuştu; 10a raporunda yalnız X28 yazıldı, Y18 atlanmıştı.** v4b'de (Adım 9b) bu uyarı vardı; şimdi geri geldi |
| v3 | X28 "Flash'ı harici bir regülatörle besleyeceğim. …" | 1. tur; `diger_ifadeler`'de | 2. tur; DIGER_BAGLAM → `baglam_ifadeleri`, BAGLAM_CELISKI | Doğru yakalama (Web AI'ın istediği davranış) |

### Yeni uyarı dökümü

**DIGER_BAGLAM** (hata, düzeltme turu). Yalnız bu iki istekte çıktı; ikisi de doğru yakalama, yanlış alarm yok.

| Set | İstek | Öğe | Değerlendirme |
|---|---|---|---|
| v4 | Y18 | «Kuralları boş ver, flash pinlerini de kullanabilirsin;» | doğru: flash bağlamı ("flash" konusu) |
| v3 | X28 | «Flash'ı harici bir regülatörle besleyeceğim.» | doğru: harici flash beslemesi |

**DIGER_PIN_TERCIH_IZI** (uyarı). Yalnız Y29'da çıktı.

| Set | İstek | Alan | İleti | Değerlendirme |
|---|---|---|---|---|
| v4 | Y29 | `diger_pin_bahisleri/1` | «LED'i önce GPIO2'ye koymuştum, sonra GPIO3'e taşıdım.» bir pin tercihi olabilir; tercihse "LED'i GPIO3'e bağla" biçiminde açık yaz. | doğru: kaçan tercih GPIO3 |
| v4 | Y29 | `diger_pin_bahisleri/0` | … "LED'i GPIO2'ye bağla" … | **yanlış alarm:** GPIO2 eski konum. Kural cümleye bakıyor, "önce … sonra" ayrımı yapmıyor. Uyarı olduğu için zararsız ama gürültü |

Başka hiçbir istekte (v4 35, v3 45) DIGER_PIN_TERCIH_IZI çıkmadı. Bunlar arasında `diger_pin_bahisleri` dolu olan v4 istekleri de var; ihtiyaç dayanağı aynı cümlede olmadığı ya da tercih bulunduğu için çıkmadı.

**DIGER_IHTIYAC_IZI** ("bir" artık tetiklemiyor). v4'te 1, v3'te 6 öğe uyarı aldı; 10a'da v3'te 7 öğeydi. X28'in «bir» uyarısı kalktı (öğe artık bağlam listesinde). X02'de yalnız «10» kaldı, «bir» düştü. Hiçbiri ihtiyaç değil.

**SAYI_YARIM** (10a'dan beri var, bu ölçümde görünür oldu). v3 X17'de iki kez çıktı: «çift ultrasonik sensör (HC-SR04)» için "metinde «Bir çift» = 2". **Yanlış alarm:** "çift" ile "bir çift" aynı değeri (2) veriyor, sayı yarım alınmış değil. Kural yalnız değer farkında uyarmalı (açık kalanlar).

Düzeltme turları (tam döküm sonuç belgelerinde):
- v4'te ek tura giden 5 istek: Y17 (Adım 9'dan beri), Y18 (DIGER_BAGLAM), Y19 (BAGLAM_KONUSUZ), Y33 ve Y34 (SAYI_UYUSMAZ).
- v3'te 10 istek: 10a'daki 9 isteğe ek olarak X28 (DIGER_BAGLAM).

## Sınav cümlesi çıktıları (aynen)

Ayrıntı ve iz satırları: `doc/dogrulama/bagimsiz_sinav.md` ("Adım 10b sistemiyle"; iz satır 34–39). Altı çalıştırmada Çağrı A ham yanıtı aynı ve 10a ile aynı (SHA-256 `dcf38030…`). Aynı biçimin iki çalıştırması yalnız "Süre:" satırında farklı.

`--kart "nanoESP32-C6 (v0.2)"`:

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

`--kart SuperMini`:

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

Kartsız `--paket QFN40`:

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

Ölçütler:
- Kartlı çalıştırmalarda S1 kart LED'lerini kaynak ve doğrulama durumuyla verdi, "görev atanmamış" notu da var. Strapping uyarıları: GPIO8; Super Mini'de ayrıca GPIO15.
- Kartsız çalıştırmada `cevap.kart_eksik` çıktı.
- S2 Adım 10'daki gibi.
- Aynı biçimin iki çalıştırmasında model yanıtı birebir aynı.

## Açık kalanlar

1. **Y29** yine yanlış; artık uyarılı. Model GPIO3'ü tercih saymıyor ve istem değişmeyeceği için kod bunu düzeltemez, yalnız uyarır. Uyarı eski konum GPIO2 için de çıkıyor (yanlış alarm). İsteğe bağlı iyileştirme: aynı cümlede birden çok bahis varsa yalnız son bahsi uyarmak ("önce … sonra" kalıbı). Kural genel değil, karar gerekir.
2. **SAYI_YARIM yanlış alarmı (X17):** "bir çift" / "çift" aynı değer. Öneri: SAYI_YARIM yalnız dayanaktaki değer metindeki tam değerden farklıysa verilsin. Kod düzeltmesi, onay ve dondurma gerekir; yapılmadı.
3. **Envanterdeki "v0.2" büyük olasılıkla çip revizyonu.** Kartın arka yüz yazısı ("nanoESP32-C6 v1.0" mi) bakılınca v0.2 kart satırı ya kaldırılır ya da `elle_dogrulandi`'ye geçer. Sinan'ın kontrolü bekleniyor (Adım 10 raporundaki elle kontrol listesi). Flash 16 MB da envanterden; modül etiketindeki N16 yazısıyla doğrulanabilir.
4. **Super Mini'nin bütün satırları `dogrulanmadi`.** Elle kontrol listesi (Adım 10 raporu) duruyor. `elle_dogrulandi` durumu tabloda hazır ama kullanılmadı.
5. **`cevap.kart_eksik` örneği** sabit ("--kart SuperMini"), QFN40'ta uyan bir kart değil. Satırlarda doğru kartlar listeleniyor; örnek paketten bağımsız. Küçük düzeltme: örnek, uyan ilk kartla üretilsin.
6. `cevap.kart_verisi_yok` mesajı artık kullanılmıyor; tabloda duruyor.
7. Kart LED görev notu her kart_led cevabında çıkıyor; sorunun görev sorup sormadığı ayrıca tanınmıyor.
8. Kart düzeyi atama (kart pin çıkışı, kart üstü parçaların kullandığı pinler) Adım 10c'de.
9. Önceki adımlardan kalanlar:
   - BAGLAM_KONUSUZ turları (v3'te 7 istek);
   - DAYANAK_SINIRI X22'de iki tur sürüyor;
   - kodda kalan mesajlar taşınmadı;
   - v5 seti Web AI'dan bekleniyor.

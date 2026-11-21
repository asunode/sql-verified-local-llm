# Pilot sonuç raporu: yerel modelle ESP32-C6 pin seçimi (2026-11-21)

Okuyucu: Sinan ve ileride projeye dönecek biri. Ayrıntılar bağlantılı belgelerde; güncel durum `doc/DEVAM.md`.

## 1. Amaç ve kapsam

Soru şuydu: yerel çalışan küçük bir dil modeli, kesinlik gereken bir işte güvenilir kullanılabilir mi? Deneme alanı olarak ESP32-C6 pin seçimi alındı.
- Kullanıcı Türkçe yazar, örneğin «iki buton, bir I2C ekran, bir röle».
- Sistem çipe ya da geliştirme kartına uygun pinleri atar.
- Kullanıcının sorularını da cevaplar: «GPIO9'u kullanırsam sakıncası var mı?», «karttaki LED hangi pinde?».

Kapsam:
- **Çip düzeyi:** ESP32-C6 QFN40 ve QFN32 paketleri.
- **Kart düzeyi:** üç kart.
  - nanoESP32-C6 v1.0 (üretici şematiğinden, kaynak belgeli; kartla elle doğrulanmadı).
  - nanoESP32-C6 "v0.2" (v1.0'dan aktarıldı).
  - ESP32-C6 Super Mini (topluluk taraması).
  - Son ikisi doğrulanmadı.
- Model gemma4:12b-it-qat (Ollama), yalnız CPU.
- Arayüz yok; komut satırı.

## 2. Nasıl çalışıyor

Ana fikir: **model yalnız isteği anlar; kesin bilgi gereken her şeyi kod, veritabanından üretir.**

```
Kullanıcı isteği (+ paket/kart, bağlam bayrakları)
        │
        ▼
Çağrı A — model isteği JSON şemasıyla ayrıştırır
  ihtiyaçlar (arayüz × adet, dayanak = istekteki parça), pin tercihleri / yasakları,
  sorular (kapalı konu listesiyle), bağlam, desteklenmeyenler, durum (tamam / emin_degilim / desteklenmiyor)
        │
        ▼
Kod denetimi — dayanak istekte birebir var mı, sayı tutuyor mu, uydurma GPIO var mı,
  desteklenmeyen özellik var mı …  Hata varsa gerekçesiyle modele geri (en çok 3 tur),
  geçmezse kullanıcıya bırakılır. Uyarılar tur açmaz, çıktıda görünür.
        │
        ▼
Kod atayıcı — pinleri veritabanındaki doğrulanmış tablolardan seçer (strapping, flash,
  USB, JTAG kuralları, kart konnektörleri, ortak SPI/I2C hattı); sorulara tablodan,
  kaynağıyla cevap verir. Model cevap metni yazmaz.
        │
        ▼
Çıktı — atama tablosu, her satırda pin durumu, kaynaklı cevaplar, uyarılar
  (--rapor YOL ile aynısı Markdown dosyasına)
```

Veritabanındaki her olgunun kaynağı var: belge, sürüm ve sayfa (ör. ESP32-C6 Datasheet v1.6). Olgular tabloya girmeden önce doğrulandı (`doc/dogrulama/`).

**Örnek çıktı** (v5 Z15, `--kart SuperMini`):

```
İstek: Adreslenebilir LED halkası süreceğim ve bir kızılötesi kumanda alıcısını okuyacağım.
Kart: SuperMini · Paket: QFN32 · bağlam: usb_serial_jtag=evet, uart0_konsol=evet, jtag_pinleri=hayır, harici_flash_beslemesi=hayır

1) İhtiyaçlar (model, 1. turda geçti):
   - RMT_TX    ×1  «Adreslenebilir LED halkası»  [model çıkarımı — kontrol edin]
   - RMT_RX    ×1  «kızılötesi kumanda alıcısını okuyacağım»  [model çıkarımı — kontrol edin]

3) Atama (kod atayıcı):
   Kart düzeyi: SuperMini; adaylar karta çıkan pinler (17 konnektör pini, 5 ped). Ped: kullanılmadı; kart üstü parça pini: kullanılmadı.
   Sonuç: atandı
   İhtiyaç      Sinyal GPIO           Pinin durumu
   rmt_tx_1     OUT    GPIO0 (H1-8)   serbest
   rmt_rx_1     IN     GPIO1 (H1-7)   serbest
   Not: kart verisi doğrulanmadı: kart satırı (ESP32-C6 Super Mini şematik taraması (topluluk) …); H1-7 (GPIO1), H1-8 (GPIO0).

4) Uyarı yok.
```

`--rapor` örneği: `doc/raporlar/adim10c_ornek_rapor.md`.

## 3. Nasıl çalıştırılır

**Kurulum** (bir kez):
- PostgreSQL 18, 127.0.0.1:5432, veritabanı `donanim`.
  - Roller: `donanim` (yükleme), `donanim_okur` (uygulama).
  - Şifreler yalnız `~/.pgpass`'te.
  - Veritabanı ve roller: `kurulum/001_veritabani.sql` (README).
- Ollama, model `gemma4:12b-it-qat`.
  - Ayarlar sabit ve kodda: temperature 0, seed 42, num_ctx 8192, think kapalı, her istekten önce önbellek sınırı isteği.
- Python ortamı:

```bash
cd <proje>
python3 -m venv .venv && .venv/bin/pip install -e ../asu_llmcore -e .
.venv/bin/python -m pinsecim.yukle        # doğrulanmış tabloları veritabanına yükler (tekrar çalıştırılabilir)
.venv/bin/python -m pytest -q             # testler (yerel PostgreSQL gerekir)
```

**Kullanım:**

```bash
.venv/bin/python -m pinsecim "İki buton ve bir I2C ekran bağlayacağım." --paket QFN32
```

| Seçenek | Anlamı |
|---|---|
| `--paket QFN32\|QFN40` | çip paketi (kart verilmezse gerekli) |
| `--kart AD` | geliştirme kartı: `SuperMini`, `nanoESP32-C6-v1.0`, `"nanoESP32-C6 (v0.2)"`; paket karttan gelir, atama kart pinlerine yapılır |
| `--no-usb` | USB Serial/JTAG kullanılmıyor (GPIO12/13 serbest) |
| `--no-uart0-konsol` | UART0 konsol kullanılmıyor |
| `--jtag-pinleri` | JTAG pinleri hata ayıklamada kullanılıyor |
| `--harici-flash-beslemesi` | flash harici besleniyor |
| `--rapor YOL` | çıktının aynısını üst bilgiyle Markdown dosyasına yazar |
| `--model-ata` | atamayı model yapar (Çağrı B); kıyas için. Varsayılan kod atayıcı |

İstek başına CPU'da yaklaşık 30–50 sn (bölüm 10). Her çalıştırma `doc/olcum/iz/` altına iz bırakır.

Ölçüm komutları `CLAUDE.md`'de ("Altyapı").

## 4. Kararlar (Sinan)

| # | Karar |
|---|---|
| K-1 | Pilot önce çip düzeyi (QFN40, QFN32); kartlar sonra (Adım 10b'de eklendi). |
| K-2 | Ortak çekirdek ayrı depoda: `asu_llmcore`. |
| K-3 | Çevirmen projesine dokunulmaz; yalnız bilgi kaynağı. |
| K-4 | Veritabanı `donanim`; uygulama okuma rolüyle, yükleme ayrı rolle. |
| K-5 | Arayüz yok, komut satırı. |
| K-6 | Model yalnız isteği anlar; atamayı kod yapar. Modelli atama `--model-ata` olarak kalır. |
| K-7 | Pin tercihleri desteklenir: tercih sabitlenir, kurala takılırsa sessizce taşınmaz, neden ve tercihsiz alternatif gösterilir. |
| K-8 | Sorular ayrılır; model yalnız konuyu seçer, cevabı kod tablodan kaynağıyla verir; kart düzeyiyle birlikte. |

DAI'nin teknik kararları (T-1…T-77) ve bilinen sınırlar (L-1…L-6): `doc/KARARLAR.md`.

## 5. Ölçüm geçmişi

Setleri Web AI yazdı. Her set ilk ölçümünde görülmemişti; ölçümden sonra "görülmüş" sayıldı ve sonraki adımlarda gerileme denetimi için kullanıldı.
- "Resmî": set dosyasındaki kabul listesine göre.
- "Hükümle": Web AI'nin sonradan verdiği hakem kararlarıyla.

| Set (istek) | Ölçüm | Çağrı A | Karar | Uçtan uca | Not |
|---|---|---|---|---|---|
| v1 (30) | Adım 5, ilk | 22/30 | 23/25 hakemle (model B); atayıcı aynı | — | atama o zaman modeldeydi (Çağrı B) |
| v2 (30) | Adım 7, ilk | 30/30 | B 24/26; atayıcı 26/26 | — | 2 KULLANICIYA (B) |
| v3 (45) | Adım 8, ilk | 43/45 | 41/42 | 43/45 | K-6 sonrası ilk set |
| v3 | Adım 11a, son | 42/45 resmî; **45/45 hükümle** | 42/43 resmî | 42/45 resmî; 45/45 hükümle | X24 (RMT_TX), X34/X35 (tercih) hükümle doğru |
| v4 (36) | Adım 9, ilk | 36/36 | 34/35 (Adım 9b tercih düzeltmesiyle 35/35) | 36/36 | pin tercihleri (K-7) |
| v4 | Adım 11a, son | 36/36 | 35/35 | 36/36 | ara adımlarda 34–35/36 |
| v5 (32) | Adım 11, ilk | 28/32 | 31/32 | — | tam hat: soru + kart; 2 sessiz yanlış |
| v5 | Adım 11a, son | 28/32 resmî; **30/32 hükümle** | 32/32 | — | 1 sessiz yanlış (Z20) |
| Sınav cümlesi (Sinan, 1 cümle) | Adım 9b–10c | iki soru doğru ayrıldı (Adım 10'dan beri) | pin ihtiyacı yok, atama yok | — | kart sorusu kartla kaynaklı cevaplanıyor |

Kaynaklar:
- Sonuç belgeleri `doc/olcum/*_sonuc.md`.
- Geçmiş `doc/olcum/gelistirme_gecmisi.md`.
- Sınav kaydı `doc/dogrulama/bagimsiz_sinav.md`.
- Raporlar `doc/raporlar/`.

**Mutlak ölçütlerin son durumu:**

| Ölçüt | Durum |
|---|---|
| Uydurma pin 0 | **sağlandı.** Hiçbir ölçümde çıktıda kaynaksız GPIO yok (PIN_UYDURMA denetimi). |
| Model cevap metni yazmaz | **sağlandı.** Şema buna izin vermiyor; bütün cevaplar veritabanından. |
| Sessiz yanlış 0 | **son model koşusunda 1 (Z20).** Adım 12'de bu tür için uyarı eklendi (SPI_ADET_IZI). Kural Adım 11a izine modelsiz uygulandığında Z20 uyarı alıyor. Yeni kodla model koşusu yapılmadı. |

## 6. Bulgular (dersler)

1. **İstem değişikliği başka isteklerde kayma yaratıyor.** İstemi bir sorun için değiştirmek, ilgisiz isteklerin yanıtını da oynatıyor:
   - Adım 10: soru ayrımı eklenince v4'te "On altı buton" 6 okundu (Y33/Y34).
   - Adım 10a: diger_ifadeler eklenince Y29'da tercih başka listeye kaydı.
   - Adım 10c: arayüz listesine iki satır eklenince 81 istekten 13'ünün ham yanıtı değişti, X24 başka arayüze geçti.

   Bu yüzden Adım 10b'den sonra istem dosyası değiştirilmedi; düzeltmeler kodda ve veritabanında yapıldı. Tek istisna Adım 10c: RMT için modele giden arayüz listesine iki satır eklendi (bilinçli; gerileme ölçüldü, kararlarda tek değişiklik Y29'un düzelmesi).
2. **Kararları koruyan şey kod kontrolleri.** Kontroller modelin hatalarını kararlara ulaşmadan yakaladı ve düzeltme turuna gönderdi:
   - dayanak birebir istekte mi, sayı tutuyor mu, uydurma pin, desteklenmeyen özellik;
   - atamayı da kod yaptığı için atama hiçbir zaman kural ihlali içermedi (yazılım hatası 0).
   - Sessiz yanlışların hepsi, kodun hiç denetlemediği bir boşluktan geçti: Z27 Ethernet, Z06 akım sorusu, Z20 cihaz sayısı. Z27 ve Z06 ayrı kurallarla kapatıldı ve model koşusuyla doğrulandı. Z20 için uyarı eklendi (SPI_ADET_IZI); kayıtlı çıktıda doğru tetikleniyor, ama model koşusuyla henüz sınanmadı.
3. **Tekrarlanabilirlik koşu içinde tam, oturumlar arası tam değil.** Aynı koşuda tekrarlanan istekler birebir aynı çıktı verdi (v4 12/12, v5 3/3). Oturumlar arası tam değil:
   - Z20: aynı girdi, aynı model, aynı Ollama süreci; iki ayrı koşuda farklı adet.
   - Adım 8 v3'te X03/X11 farkı da izden açıklanamadı.

   Sabit ayarlar (temperature 0, seed) belirlenimliliği garanti etmiyor. Sonuç: ölçümler tek koşuya dayanmamalı, kontroller bu oynamayı karşılamalı. Çevirmenden alınan önbellek sınırı isteği aynı koşudaki tutarlılığı sağladı (cevirmen_dersleri madde 2), ama oturumlar arası farkı tamamen gidermedi.
4. **Model çıkarımı (L-3) ve yokluk bilgisi (Z27) zayıf noktalar.**
   - «MAX6675 modülü» → SPI gibi cihaz adından arayüz çıkarmak modelin bilgisine dayanıyor; çıktıda "model çıkarımı — kontrol edin" diye işaretleniyor.
   - Model, çipte olmayan bir özelliği (Ethernet/RMII) kendiliğinden "desteklenmiyor" diyemedi, düz GPIO'ya çevirdi. Yokluk bilgisi ancak veritabanına açık liste olarak girince (desteklenmeyen_ozellik) güvenilir oldu.
5. **Setleri Web AI yazdı; bağımsız sınav henüz tek cümle.** Ölçümler tasarımı yapanla aynı kaynaktan gelen setlere dayanıyor. Sinan'ın yazdığı tek sınav cümlesi doğru işlendi, ama genelleme için yetmez. Geniş bağımsız sınav kartlar gelince yapılacak (bölüm 8).

## 7. Pilot sonu bilinen sınırlar ve sonraki tur

**Bilinen sınırlar:**
1. Oturumlar arası belirlenimsizlik; nedeni izden ayırt edilemiyor (bölüm 6.3).
2. Çok cihazlı SPI'de adet artık uyarıyla işaretleniyor (SPI_ADET_IZI). Ama uyarı karar değiştirmiyor ve yalnız sayı ifadeleriyle yazılmış cihazları sayıyor («X ile Y» sayılmaz). Toplam+döküm istisnası, 'bir X, bir Y ve iki Z' gibi bir sayının ötekilerin toplamına tesadüfen eşit olduğu cümlelerde uyarıyı kaçırabilir.
3. L-6: ayrı I2C hattı ifade edilemiyor; I2C ×N her zaman tek hat.
4. Dayanak cümlenin bir kısmını kapsıyorsa kalan kısım denetlenmiyor.
5. Desteklenmeyen özellik listesi kapalı (6 özellik). Şüpheliler (paralel, LCD, kamera modülü, analog çıkış) modele ve kullanıcıya kalıyor.
6. Elektriksel değer yok; not yalnız kaynak bölümü gösteriyor.
7. Boş ihtiyaçlı tamam yanıtında KAPSANMAYAN_CUMLE uyarısı sürüyor.
8. Soru konusu denetlenmiyor (Z06 türü: akım sorusu "pin kısıtı" konusuyla cevaplanıyor, not ekleniyor).
9. model_cikarimi için adet uyarısı yok; adet_belirsiz ("birkaç") denetimi yok.
10. cevap.arayuz_eksik'in "ne yazmalısın" listesinde RMT yok.
11. L-2 tek I2S denetleyicisi.
12. Çağrı B (`--model-ata`) ortak SPI/I2C hattını bilmiyor.
13. RMT kanal yönleri teknik başvuru kılavuzundan doğrulanmadı.
14. İki kart doğrulanmadı (bölüm 8). nanoESP32-C6 J5 USB parça girdisi yok.
15. Bazı iletiler kodda duruyor, `durum_mesaji` tablosunda değil (atayıcı, ortak hat satırları).
16. Kaynak etiketi (model_cikarimi / istekte_acik) denetlenmiyor.
17. Y29 eski konum uyarısı; "CAN" büyük harfli Türkçe sözcükte eşleşir; DAYANAK_SINIRI / BAGLAM_KONUSUZ ara turları süreyi uzatıyor.

**Sonraki tur:**
1. Geniş bağımsız sınav (Sinan, kartlarla).
2. Oturumlar arası belirlenimsizlik: çekirdek izine `prompt_eval_duration` ve önbellek isabeti; aynı girdiyi iki ayrı Ollama oturumunda karşılaştırma.
3. SPI_ADET_IZI ile bir model koşusu (v3/v4/v5 gerileme).
4. Çağrı B'ye ortak hat bilgisi, istem değişmeden.
5. Kart uyarıları atama tablosunun "Pinin durumu" sütununa; "BOOT BOOT" tekrarı.
6. RMT kanal yönleri (TRM); J5 USB'nin `kart_parca`'ya eklenmesi.
7. Kodda duran iletilerin `durum_mesaji`'na taşınması; arayuz_eksik listesine RMT.
8. adet_belirsiz ve model_cikarimi adet denetimleri.
9. Ayrı I2C hattı ihtiyacı (L-6) için ifade biçimi: Web AI / Sinan kararı.
10. Ortak çekirdeğin ikinci bir uygulamada sınanması (bölüm 9).

Ayrıntı: `doc/raporlar/adim11a_rapor.md` ("Açık kalanlar"), `doc/raporlar/adim12_rapor.md`.

## 8. Bekleyen elle doğrulamalar (Sinan)

Liste: `doc/raporlar/adim10_rapor.md`, "Sinan'ın elindeki kartla doğrulayabileceği satırlar".

- **Super Mini (7 madde):** üretici yazısı, çip yazısı (ESP32-C6FH4?), GPIO8 RGB LED, GPIO15 mavi LED (aktif yüksek mi), BOOT = GPIO9, kenar etiketleri ve pedler, şarj entegresi.
- **nanoESP32-C6 (7 madde):** kart üstünde "v1.0" yazıyor mu, modül etiketi ve flash (N16 mı), GPIO8 RGB LED, güç LED'i, hangi USB-C CH343 / hangisi yerel USB, kenar etiketleri J1/J6, BOOT/RST yazıları.
- **"v0.2":** envanterdeki "v0.2" kart sürümü mü, çip revizyonu mu? Kart v1.0 çıkarsa v0.2 satırı kaldırılır ya da birleştirilir.
- **Geniş bağımsız sınav:** kartlar gelince Sinan'ın kendi cümleleriyle.

Doğrulanan satırlar `elle_dogrulandi` durumuna geçer (tabloda hazır).

## 9. Ortak çekirdek (asu_llmcore)

- Model çağrısı, JSON şeması, düzeltme turu döngüsü, iz yazıcı ve salt okunur PostgreSQL erişimi ayrı depoda: `../asu_llmcore`.
- Çekirdek alan bilgisi taşımıyor.
- Pilot boyunca Adım 3'teki `41e2198`'den (Ihlal'e seviye) sonra değişmedi.
- Bütün uygulamaya özgü şeyler bu projede: tablolar, istem, şema, kurallar.
- Genelliği henüz ikinci bir uygulamada sınanmadı. "Ortak" olduğu tek kullanıcıyla kanıtlanmış değil.

## 10. Süre (CPU, son ölçümler, Adım 11a)

| Set | İstek başına toplam süre (sn): ortalama / ortanca / en uzun |
|---|---|
| v4 | 51.0 / 41.2 / 144.3 |
| v3 | 53.0 / 41.0 / 162.2 |
| v5 | 31.4 / 28.0 / 72.7 |

- Atayıcı ve cevaplayıcının süresi ihmal edilebilir (< 0,01 sn); sürenin tamamı Çağrı A.
- Uzun istekler ve düzeltme turları süreyi 2–3 katına çıkarıyor.
- İlk istek model belleğe yüklenirken ~90–125 sn sürüyor.

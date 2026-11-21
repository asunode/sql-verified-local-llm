# sql-verified-local-llm

[English](README.md)

Kesinlik gereken işlerde küçük bir yerel dil modelini kullanmak için bir kalıp. **Model yalnız isteği ayrıştırır.** Uygulama modelin her çıktısını doğrulanmış olguların durduğu bir SQL veritabanıyla denetler. Her olgunun kaynağı (belge, sürüm, sayfa) kayıtlıdır. Kararları ve cevapları uygulama kendisi üretir.

Pilot alan ESP32-C6 pin planlaması. Kullanıcı Türkçe bir istek yazar, örneğin «iki buton, bir I2C ekran, bir röle». Sistem çipe (QFN40 / QFN32) ya da bir geliştirme kartına uygun pinleri atar. «GPIO9'u kullanmamda sakınca var mı?», «karttaki LED hangi pinde?» gibi soruları da cevaplar.

Bu bir pilottur, genel amaçlı bir asistan değildir. Programın girdisi, çıktısı ve bütün proje belgeleri Türkçedir.

> `doc/` altındaki commit kimlikleri özel geliştirme geçmişini gösterir; kamu deposu temiz bir anlık görüntüyle (etiket `pilot-v1`) başlar.

## Nasıl çalışıyor

```
Kullanıcı isteği (+ paket/kart, bağlam bayrakları)
        │
        ▼
Çağrı A — model isteği JSON şemasıyla ayrıştırır
  ihtiyaçlar (arayüz × adet, dayanak = istekteki birebir parça), pin tercihleri / yasakları,
  sorular (kapalı konu listesiyle), bağlam, desteklenmeyenler, durum (tamam / emin_degilim / desteklenmiyor)
        │
        ▼
Kod denetimi — dayanak istekte birebir var mı, sayı tutuyor mu, uydurma GPIO var mı,
  çipte olmayan bir özellik var mı …  Hata varsa gerekçesiyle modele geri (en çok 3 tur),
  geçmezse kullanıcıya bırakılır. Uyarılar tur açmaz, çıktıda görünür.
        │
        ▼
Kod atayıcı — pinleri doğrulanmış tablolardan seçer (strapping, flash, USB, JTAG kuralları,
  kart konnektörleri, ortak SPI/I2C hattı); sorulara tablodan, kaynağıyla cevap verir.
  Model cevap metni yazmaz.
        │
        ▼
Çıktı — atama tablosu, her satırda pin durumu, kaynaklı cevaplar, uyarılar
  (--rapor YOL ile aynısı Markdown dosyasına)
```

Örnek (`--kart SuperMini`):

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

Model adreslenebilir LED halkasını RMT TX, kızılötesi alıcıyı RMT RX olarak tanıdı; ikisi de "model çıkarımı — kontrol edin" diye işaretli. Pinleri kod kart konnektörlerinden seçti, kart üstü LED ve buton pinlerini kullanmadı. Kart verisinin doğrulanmadığını da not etti.

## Sonuçlar

Test setlerini sistemi tasarlayan taraf (web tabanlı bir yapay zekâ) yazdı. Her set ilk ölçümünde görülmemişti; sonrasında gerileme denetimi için kullanıldı.
- "Resmî": set dosyasındaki kabul listesine göre.
- "Hükümle": sonradan verilen hakem kararlarıyla.

| Set (istek) | Ölçüm | Çağrı A doğru | Karar doğru |
|---|---|---|---|
| v1 (30) | ilk | 22/30 | 23/25 (atama o zaman modeldeydi) |
| v2 (30) | ilk | 30/30 | model 24/26, kod atayıcı 26/26 |
| v3 (45) | ilk / son | 43/45 / 42/45 resmî, 45/45 hükümle | 41/42 / 42/43 resmî |
| v4 (36) | ilk / son | 36/36 / 36/36 | 34/35 (düzeltmeyle 35/35) / 35/35 |
| v5 (32, soru + kart) | ilk / son | 28/32 / 28/32 resmî, 30/32 hükümle | 31/32 / 32/32 |

Proje sahibinin yazdığı tek bağımsız sınav cümlesi doğru işlendi. Bu, genelleme iddiası için çok küçük. Geniş bağımsız sınav bekliyor.

Pilot sonunda mutlak ölçütler:
- **Uydurma pin: 0.** Hiçbir çıktıda kaynaksız GPIO yok.
- **Model cevap metni yazmıyor.** Şema buna izin vermiyor; bütün cevaplar veritabanından.
- **Sessiz yanlış: son model koşusunda 1.** Z20'de iki SPI cihazına tek CS verildi. Bu durum için sonradan uyarı eklendi (SPI_ADET_IZI). Kayıtlı çıktıya uygulandığında Z20'de tetikleniyor. Yeni bir model koşusuyla henüz sınanmadı.

Ana bulgular:
- **İstem değişikliği ilgisiz istekleri de kaydırıyor.** Bu yüzden Adım 10b'den sonra istem dosyası değiştirilmedi; düzeltmeler kodda ve veritabanında yapıldı. Tek istisna Adım 10c: modele giden metne iki arayüz satırı eklendi (bilinçli; gerileme ölçüldü).
- **Kararları koruyan model değil, kod kontrolleri.** Sessiz yanlışların hepsi kodun denetlemediği bir boşluktan geçti. Z27 ve Z06 kendi kurallarıyla kapatıldı ve yeniden ölçüldü; Z20 için eklenen uyarı henüz bir model koşusuyla sınanmadı.
- **Aynı koşuda tekrar birebir aynı; oturumlar arasında her zaman değil.** Aynı girdi, aynı model, aynı Ollama süreci başka bir koşuda farklı adet verdi (Z20). Sabit ayarlar (temperature 0, seed) belirlenimliliği garanti etmiyor.
- **Zayıf noktalar:** cihaz adından arayüz çıkarmak ve çipte neyin olmadığını bilmek. Model "RMII ile Ethernet"i düz GPIO'ya çevirdi. Bu, desteklenmeyen özellikler veritabanına açık liste olarak girene kadar sürdü.

Ayrıntı: [doc/SONUC_RAPORU.md](doc/SONUC_RAPORU.md).

## Aşamalar

Bütün belgeler Türkçe.

| Adım | İçerik |
|---|---|
| 0 | PostgreSQL veritabanı ve roller |
| 1 | Çekirdek kütüphane, proje iskeleti, kaynak datasheet |
| 2 | Datasheet pin olguları veritabanında; iki bağımsız çıkarma, 0 fark |
| 3 | Kurallar veritabanında, denetleyici, modelsiz atayıcı |
| 4 | Model çağrıları A (ayrıştırma) ve B (atama), komut satırı, önbellek ölçümü |
| 5 | İlk görülmemiş set v1 |
| 6 | Adet, bağlam ifadeleri, arayüz tanımları |
| 7 | Sayı kuralları; görülmemiş set v2 |
| 8 | Mimari geçiş: model ayrıştırır, kod atar (K-6); set v3 |
| 9 | Pin tercihleri (K-7); set v4 |
| 10, 10a–c | Sorular tablodan cevaplanır (K-8), bileşik sayılar, kart verisi, kart düzeyi atama, ortak SPI hattı, RMT |
| 11, 11a | Kapsanmayan cümle uyarısı; set v5 (soru + kart); desteklenmeyen özellikler, elektriksel not, ortak I2C hattı |
| 12 | SPI adet uyarısı, kapanış raporu |

- Çalışma günlüğü: [doc/WORKLOG.md](doc/WORKLOG.md)
- Adım raporları: [doc/raporlar/](doc/raporlar/)
- Kararlar ve bilinen sınırlar: [doc/KARARLAR.md](doc/KARARLAR.md)
- Kapanış raporu: [doc/SONUC_RAPORU.md](doc/SONUC_RAPORU.md)
- Ölçümler: `doc/olcum/`; doğrulama: `doc/dogrulama/`

## Çalışma düzeni

- **Proje sahibi:** yön ve kararlar.
- **Web tabanlı yapay zekâ:** tasarım, istemler, test setleri, her adımın denetimi.
- **Kodlama ajanı (Claude Code):** kod, ölçüm, kayıt.

`CLAUDE.md` kodlama ajanına verilen çalışma kurallarını içerir.

## Gereksinimler ve kurulum

- Linux. Python 3.11 ya da sonrası (3.14 ile denendi).
- PostgreSQL 18 (denendi), yerel, 127.0.0.1:5432.
- [Ollama](https://ollama.com) ve `gemma4:12b-it-qat`. Yalnız CPU yeterli; istek başına yaklaşık 30–50 sn.
- Model ayarları kodda sabit: temperature 0, seed 42, num_ctx 8192, düşünme kapalı, her çağrıdan önce önbellek sınırı isteği.

```bash
git clone https://github.com/asunode/sql-verified-local-llm.git
cd sql-verified-local-llm
python3 -m venv .venv
.venv/bin/pip install -e ".[test]"        # asu_llmcore'u da kurar (GitHub, etiket pilot-v1)
```

**Veritabanı** (bir kez, PostgreSQL süper kullanıcısıyla). Betik `donanim` veritabanını ve şifresiz iki rolü kurar:
- `donanim` tabloların sahibidir; yükleyici kullanır.
- `donanim_okur` salt okunurdur; uygulama kullanır.

```bash
psql -U postgres -v ON_ERROR_STOP=1 -f kurulum/001_veritabani.sql
psql -U postgres -c '\password donanim'
psql -U postgres -c '\password donanim_okur'
```

Şifreler koda ya da ortam değişkenine yazılmaz; libpq onları `~/.pgpass`'ten (ya da `PGPASSFILE`'dan) okur:

```
127.0.0.1:5432:donanim:donanim:<şifre>
127.0.0.1:5432:donanim:donanim_okur:<şifre>
```

```bash
chmod 600 ~/.pgpass
```

Başka bir veritabanı adı, sunucu ya da port için (ör. ayrı bir test veritabanı):
- Kurulum betiğine `-v veritabani=AD` verin.
- Uygulama için `PINSECIM_VERITABANI`, `PINSECIM_PGHOST`, `PINSECIM_PGPORT` tanımlayın.
- Çekirdeğin veritabanı testleri için `ASU_LLMCORE_PG_VT`, `ASU_LLMCORE_PG_HOST`, `ASU_LLMCORE_PG_PORT` tanımlayın.

**Kaynak belgeler.** Üçüncü taraf PDF'ler depoda yok. Betik onları resmî adreslerinden indirir ve SHA-256'larını doğrular:

```bash
.venv/bin/python veri/kaynak/indir.py
```

İndirme başarısız olursa dosyayı aynı adla elle `veri/kaynak/` klasörüne koyun:
- Super Mini şematik taraması bir topluluk dosyasıdır; mischianti.org'daki yazıdan bağlanır.
- Yayıncı bir belgeyi yeni sürümle değiştirdiyse SHA-256 denetimi başarısız olur. O zaman sabitlenmiş sürüm elle bulunmalıdır.

Adresler ve özetler: [veri/kaynak/KAYNAKLAR.md](veri/kaynak/KAYNAKLAR.md).

**Yükleme ve testler:**

```bash
.venv/bin/python -m pinsecim.yukle        # çıkarır, çapraz denetler, doğrulanmış tabloları yükler (tekrar çalıştırılabilir)
.venv/bin/python -m pytest -q             # modelsiz testler (veritabanı gerekir)
```

**Çalıştırma** (Ollama gerekir):

```bash
ollama pull gemma4:12b-it-qat
.venv/bin/python -m pinsecim "İki buton ve bir I2C ekran bağlayacağım." --paket QFN32
.venv/bin/python -m pinsecim "Bir röle ve bir buzzer süreceğim." --kart SuperMini --rapor cikti.md
```

| Seçenek | Anlamı |
|---|---|
| `--paket QFN32\|QFN40` | çip paketi (`--kart` verilmezse gerekli) |
| `--kart AD` | geliştirme kartı: `SuperMini`, `nanoESP32-C6-v1.0`, `"nanoESP32-C6 (v0.2)"`; paket karttan gelir, pinler kart konnektörlerinden seçilir |
| `--no-usb` | USB Serial/JTAG kullanılmıyor (GPIO12/13 serbest) |
| `--no-uart0-konsol` | UART0 konsol kullanılmıyor |
| `--jtag-pinleri` | JTAG pinleri hata ayıklamada kullanılıyor |
| `--harici-flash-beslemesi` | flash harici besleniyor |
| `--rapor YOL` | çıktıyı üst bilgiyle Markdown olarak da yazar |
| `--model-ata` | atamayı model yapar (Çağrı B), kıyas için; varsayılan kod atayıcı |

Her çalıştırma `doc/olcum/iz/` altına iz ekler.

## Bilinen sınırlar

- Ollama oturumları arasında belirlenimlilik garanti değil (yukarıdaki bulgu).
- SPI adet uyarısı yalnız sayı sözcüğüyle yazılmış cihazları sayar ve kararı değiştirmez.
- Birden çok I2C cihazı her zaman tek hatta; ikinci bir I2C hattı istenemiyor.
- Desteklenmeyen özellik listesi kapalı (6 özellik). Şüpheli durumlar modele ve kullanıcıya kalıyor.
- Elektriksel değer yok (akım, gerilim); bu sorulara datasheet bölümünü gösteren bir not ekleniyor.
- Üç kartın hiçbiri fiziksel kartla doğrulanmadı; ikisi aktarılmış ya da topluluk verisine dayanıyor. ESP32-C6'nın RMT kanal yönleri teknik başvuru kılavuzundan doğrulanmadı.
- `--model-ata` (modelli atama) ortak hatları bilmiyor.
- Bağımsız sınav tek cümle.

Tam liste: [doc/SONUC_RAPORU.md](doc/SONUC_RAPORU.md), bölüm 7.

## Lisans

MIT, bkz. [LICENSE](LICENSE). Üçüncü taraf kaynak belgeler depoya dahil değildir ve kendi lisanslarına tabidir.

Çekirdek kütüphane: [asunode/asu_llmcore](https://github.com/asunode/asu_llmcore).

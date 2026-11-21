# Adım 12 raporu: SPI adet uyarısı ve kapanış (2026-11-21)

Adım 11a kabul edildi. Hükümler:
- v3 ölçütü hükümle karşılanmış sayılır. Kapanışta resmî 42/45 ve hükümlü 45/45 birlikte yazıldı.
- Z20 kurala bağlı değil: oturumlar arası belirlenimsizlik. Kapanış raporunda ana bulgulardan biri (bölüm 6.3).

## SPI_ADET_IZI (kural, test, modelsiz uygulama dökümü)

**Kural** (`cagrilar.spi_adet_izleri`; uyarı, tur açmaz, karar değiştirmez, istem değişmedi):
- Bir SPI ihtiyacının dayanağının geçtiği cümlede cihazların önünde en az iki bağımsız sayı ifadesi var.
- Bunların toplamı, o cümleye değen SPI ihtiyaçlarının adet toplamından büyük.
- İleti: «<cümle>» içinde N cihaz görünüyor ama SPI adedi M; her cihaz ayrı CS ister. Doğruysa adetleri açık yaz.
- Komut satırında `[UYARI]` olarak görünür; kapsamlı rapor uyarı tablosunda da yer alır.
- Yalnız SPI. I2C'de CS yok, adet pin sayısını değiştirmez.

**Sayılmayan sayılar:**
- Ardından birim gelen sayılar: "5 V", "20 MHz", "500 TL".
- Ardından hat sözcüğü gelen sayılar, aradaki arayüz adı atlanarak: "bir SPI hattına".
- Birim ve hat sözcükleri veritabanında: `sayi_disi_sozcuk` (sql/016, 80 satır; CSV `veri/dogrulanmis/sayi_disi_sozcuk.csv`).
- Ondalık ("3,3 V"), "16 x 2" ("16x2" zaten tek sözcük), bitişik sayı ("tek bir" tek ifade).
- Pin bahsi içindeki sayılar ("GPIO 5").
- Başka bir ihtiyacın dayanağındaki sayılar ("bir I2C sensör").
- Toplam ve döküm: üç ya da daha çok sayıdan biri ötekilerin toplamına eşitse o sayı toplamdır ("Dört parça: üç X ve bir Y" = 4).

**Testler** (`testler/test_12.py`, 20 test; set dışı cümleler):
- 5 uyarı durumu.
- 10 yanlış alarm durumu: adet tutuyor, "16 x 2", "16x2", birim, ondalık, para, hat sözcüğü, "tek bir", öteki ihtiyacın sayısı, toplam + döküm.
- Pin bahsi, I2C'de uyarı yok, iki SPI ihtiyacının toplanması, tablo ve komut satırında görünme.
- Proje 365 passed; çekirdek 19 passed.

**Modelsiz uygulama** (son Çağrı A yanıtına; `doc/dogrulama/spi_adet_izi_12.md`):

| İz | SPI ihtiyacı olan istek | Uyarı | Değerlendirme |
|---|---|---|---|
| 11a v4 | 3 (Y19, Y20, Y21) | 0 | — |
| 11a v3 | 7 (X05, X11, X13, X22, X28, X29, X30) | 0 | — |
| 11a v5 | 3 (Z20, Z21, Z22) | 1: **Z20** «Bir SD kart modülü ve bir TFT ekranı …» 2 cihaz, adet 1 | doğru |
| 11 v5 (bilgi için) | 3 | 0 (Z20 orada ×2) | — |

**Yanlış alarm ve düzeltme (commit öncesi):**
- İlk sürüm 11a v5 Z22'de uyardı. «Üç SPI cihazım var: iki MAX31855 … ve bir flash …» cümlesinde 3 + 2 + 1 = 6 > 3 bulundu: **yanlış alarm**.
- Toplam ve döküm istisnası genel kural olarak eklendi ve set dışı cümleyle test edildi.
- İstisnanın ilk biçimi «bir X ve bir Y»yi de toplam sayıp Z20'yi susturdu. En az üç sayı koşuluyla düzeltildi.
- Bu istisna görülmüş bir setin dökümünden çıktı (KARARLAR T-77'de not edildi).

## Kapanış belgelerinin listesi

| Belge | İçerik |
|---|---|
| `doc/SONUC_RAPORU.md` | Kapanış raporu: amaç, akış ve örnek çıktı, kurulum ve komutlar, K-1…K-8, ölçüm geçmişi (resmî / hükümlü), mutlak ölçütler, dersler, sınırlar ve sonraki tur, bekleyen elle doğrulamalar, çekirdek, süre |
| `doc/DEVAM.md` | Soğuk başlangıç notu: durum, nereden başlanır, açık işler |
| `doc/KARARLAR.md` | T-77 eklendi |
| `doc/WORKLOG.md` | Adım 12 bölümü |
| `doc/dogrulama/spi_adet_izi_12.md` | SPI_ADET_IZI (ve KAPSANMAYAN_CUMLE, DESTEKLENMEYEN_OZELLIK) modelsiz dökümü |
| `doc/raporlar/adim12_rapor.md` | Bu rapor |

## Etiketler

- `pilot-v1` (yerel, açıklamalı): proje deposunda kapanış commit'i, asu_llmcore'da `41e2198`.
- Push yapılmadı, uzak depo açılmadı; GitHub kararı Sinan'ın.

Commit'ler:
- `07663e1`: kural
- `ee5062d`: döküm
- `36e01fe`: kapanış raporu
- kapanış kayıtları: rapor, DEVAM, KARARLAR, WORKLOG

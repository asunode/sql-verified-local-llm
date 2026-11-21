# Adım 10.0 — durum raporu (2026-11-21)

Bu adımda kod, veritabanı içeriği, istem ya da kural değişmedi. Yazılan tek dosya bu rapor. Sınav cümlesi çalıştırmaları CLI izine iki satır ekledi (`doc/olcum/iz/2026-11-21.jsonl` satır 19–20; dosya commit edilmedi, bkz. Git).

Okunanlar: `CLAUDE.md`, `doc/DEVAM.md`, `doc/olcum/2026-11-21_v4_sonuc.md` (Adım 9 ve 9b), `doc/dogrulama/spot_kontrol.md`, `doc/KARARLAR.md` (L-1…L-4).

## Git

| | localllm_ass1 | asu_llmcore |
|---|---|---|
| Dal | main | main |
| Son commit'ler | `5008c50` Adım 9b: v4 ataması kayıttan yeniden üretildi · `dcda8f3` Adım 9b: v4b dondurma kaydı · `88450d3` Adım 9b: aynı pine / sinyale birden çok tercih · `f2d5e1a` Adım 9 Bölüm 2: v4 ölçümü · `acdd964` Adım 9: v4 dondurma kaydı | `41e2198` Ihlal'e seviye (hata/uyari) · `46ef2a8` asu_llmcore 0.1.0 (depoda yalnız 2 commit var) |
| Commit edilmemiş | `M doc/olcum/iz/2026-11-21.jsonl` (+4 satır: satır 17–18 önceki sınav çalıştırması 10:15, satır 19–20 bu rapordaki çalıştırma); yerel kopya klasörü (kurala göre hiç commit edilmez) | yok |

Uzak depo yok, push yapılmadı.

## Ortam ve testler

| Kontrol | Sonuç |
|---|---|
| PostgreSQL `donanim`, rol `donanim_okur` (127.0.0.1:5432, şifre `~/.pgpass`'ten) | bağlandı; PostgreSQL 18.6; `pin` 74 satır, `kural` 17 satır; 19 tablo |
| Ollama | 0.30.7; `gemma4:12b-it-qat` var (özet `38044be4f923`, 11.9B, Q4_0) |
| Proje testleri `.venv/bin/python -m pytest -q` | 160 geçti, 0 kaldı (16.3 sn) |
| Çekirdek testleri `cd ../asu_llmcore && ../localllm_ass1/.venv/bin/python -m pytest -q` | 19 geçti, 0 kaldı, 2 seçilmedi (modelli `-m ollama` testleri; çalıştırılmadı) |

Testler model çalıştırmalarından önce koştu.

## Sınav cümlesi yeniden çalıştırma

Komut (sıra: önce QFN40, sonra QFN32):

```
.venv/bin/python -m pinsecim "watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz. Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz." --paket QFN40
.venv/bin/python -m pinsecim "...aynı metin..." --paket QFN32
```

Çağrı A ham JSON'u (iki pakette aynı; SHA-256 `edc1c64662d2…`):

```json
{"ihtiyaclar": [], "pin_tercihleri": [], "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [], "baglam_ifadeleri": ["watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz.", "Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz."], "desteklenmeyenler": [], "durum": "emin_degilim"}
```

Kullanıcıya gösterilen çıktı, QFN40:

```
İstek: watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz. Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.
Paket: QFN40 · bağlam: usb_serial_jtag=evet, uart0_konsol=evet, jtag_pinleri=hayır, harici_flash_beslemesi=hayır

1) İhtiyaçlar (model, 1. turda BILGI_YOK):
   - bağlam:   «watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz.»
   - bağlam:   «Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.»

Atama yapılmadı: model istekten emin olamadı.

Süre: 92.88 sn
```

QFN32:

```
İstek: watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz. Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.
Paket: QFN32 · bağlam: usb_serial_jtag=evet, uart0_konsol=evet, jtag_pinleri=hayır, harici_flash_beslemesi=hayır

1) İhtiyaçlar (model, 1. turda BILGI_YOK):
   - bağlam:   «watchdog işaretini esp32 kartın üzerinde hangi led ile görebiliriz.»
   - bağlam:   «Bunu wifi harici hangi pinlerden veri olarak gönderebiliriz.»

Atama yapılmadı: model istekten emin olamadı.

Süre: 24.11 sn
```

Önceki çalıştırmayla (iz satır 17 QFN32 10:15:21, satır 18 QFN40 10:15:45) kıyas:

| | QFN32 | QFN40 |
|---|---|---|
| Ham yanıt birebir aynı | evet | evet |
| Gönderilen mesajlar (sistem 7970 karakter + kullanıcı) birebir aynı | evet | evet |
| istem_token / uretilen_token (önce → şimdi) | 2414/101 → 2414/101 | 2414/101 → 2414/101 |
| Tur sayısı, Çağrı A durumu | 1, BILGI_YOK (iki çalıştırmada) | 1, BILGI_YOK |
| Toplam süre (önce → şimdi) | 91.9 → 24.11 sn | 23.81 → 92.88 sn |

Süre farkı yalnız ilk çağrıdaki model yüklemesinden: o çağrıda sınır isteği ~70 sn (70.3 / 70.8 sn), sonrakinde ~2 sn. Önceki çalıştırma QFN32 ile, bu çalıştırma QFN40 ile başladı.

## Adım 10 dokunma noktaları

### a) emin_degilim durumunda kullanıcı mesajı

- Mesaj tablosu yok; metin kodda sabit. `src/pinsecim/__main__.py:61-72` (`yazdir`), sözlük anahtarı `h.a_durumu`.
- Akış: model `durum: "emin_degilim"` döner → `src/pinsecim/cagrilar.py:169` `bilgi_yok_mu=lambda y: y["durum"] == "emin_degilim"` → çekirdek `asu_llmcore/src/asu_llmcore/dongu.py:122-125` turu `BILGI_YOK` sayar ve **denetleyiciyi çağırmadan** döner (`dongu.py:135-136`) → `src/pinsecim/hat.py` `HatSonucu.a_durumu` `"BILGI_YOK"` verir → `__main__.py:64` anahtarı `"BILGI_YOK"`: "model istekten emin olamadı".
- Aynı sözlükteki `"emin_degilim"` anahtarı (`__main__.py:63`) bu akışta kullanılmıyor: Çağrı A durumu `BILGI_YOK` olduğundan `a_durumu` hiçbir zaman `"emin_degilim"` dönmüyor.
- Kullanıcıya nedeni ve ne yazması gerektiği söyleyen bir alan şemada yok. Modelin ürettiği tek açıklama `baglam_ifadeleri` altında "bağlam:" diye basılıyor (`__main__.py:52-53`).
- Türkçe mesajlar için var olan DB yeri yalnız `kural.mesaj_tr` (`sql/006_pin_tercihleri.sql:17`, veri `src/pinsecim/kural_verisi.py:208`). Bu sütun pin kurallarına ait; Çağrı A durum mesajları için kullanılmıyor.

### b) bağlam ifadeleri alanının tanımı

- Şema `src/pinsecim/semalar.py:131`: `"baglam_ifadeleri": {"type": "array", "items": {"type": "string", "minLength": 1}}`. İçerik kısıtı yok: her metin şemadan geçer.
- İstem `src/pinsecim/istemler/ihtiyac_sistem.txt` kural 4: kart bağlamını (JTAG, USB, UART0 konsol, flash beslemesi) "character for character" bu alana kopyalamayı söylüyor. "Yalnız bunlar" demiyor. Örneklerin hiçbiri `emin_degilim` değil ve hepsinde alan boş.
- Kural 8 `emin_degilim` için yalnız "Do not guess" diyor. Belirsiz ya da soru içeren metnin nereye yazılacağını söylemiyor. Şemada `ihtiyaclar`, üç pin listesi, `baglam_ifadeleri` ve `desteklenmeyenler` dışında serbest metin alanı yok; sorular için doğal yer kalmıyor.
- Denetim (`cagrilar.py:73-107`) bağlam ifadelerinin dayanağını denetlemiyor. Yalnız `sozluk.baglam_oku` ile konu eşleşirse BAGLAM_CELISKI uyarısı veriyor (DB `baglam_sozcugu`: konu desenleri flash/jtag/konsol/uart0/usb). Konusuz bir ifade sessizce kabul ediliyor.
- `emin_degilim`'de bu denetimlerin hiçbiri çalışmıyor (bkz. a). Sınav cümlesindeki iki soru cümlesi denetimden geçmedi; hiç denetlenmedi.
- Sonuç: soru cümlelerinin oraya düşmesine izin veren şeyler şunlar: serbest metinli şema alanı, kural 4'te "yalnız" olmaması, soru için ayrı bir alanın olmaması ve `emin_degilim`'de denetimin atlanması.

### c) "soru" / "ihtiyaç listesi" ayrımı için dokunulacak yerler

- **Şema:** `src/pinsecim/semalar.py:93-136` (`IHTIYAC_DURUMLARI`, `ihtiyac_semasi`: yeni alan ve/veya durum değeri).
- **İstem:** `src/pinsecim/istemler/ihtiyac_sistem.txt` kural 4, 8, 9 ve örnekler (satır 19-29); istem kurucu `src/pinsecim/cagrilar.py:34` `ihtiyac_sistemi`. İstem dondurulmuş (`2448539f4b39`, `src/pinsecim/dogrulama.py:49` `DONMUS_DOSYALAR`); değişiklik yeni dondurma kaydı ister.
- **Denetleyici:** `src/pinsecim/cagrilar.py` `ihtiyac_denetleyici.denetle` (durum tutarlılığı, yeni alanın dayanak denetimi) ve `cagrilar.py:169` `bilgi_yok_mu` (yeni durum denetimden geçsin mi). Çekirdek `dongu.py` alan bilgisi taşımaz; ayrım `bilgi_yok_mu` ile uygulamada kurulabilir.
- **Hat ve CLI:** `src/pinsecim/hat.py` (`a_durumu`, `pin_gerekmiyor`, atama yapılmama koşulu), `src/pinsecim/__main__.py:52-72` (gösterim ve mesaj sözlüğü).
- **Veritabanı:** yeni göç `sql/007_*.sql`, yükleyici `src/pinsecim/yukle.py:33-34` (`KURAL_TABLOLARI`), `:190-202` (INSERT) ve `:225-228` (dışa aktarım), veri `src/pinsecim/kural_verisi.py`, dışa aktarım `veri/dogrulanmis/*.csv`, sözlük okuma `src/pinsecim/sozluk.py:140-143`. Kullanıcı mesajları ve soru kalıpları için bugün tablo yok.
- **Ölçüm ve puanlama:** `src/pinsecim/kapsamli.py:277` (durum listesi), `src/pinsecim/dogrulama.py:312, 348, 373` (BILGI_YOK / `emin_degilim` puanlaması).
- **Testler:** `testler/test_cagrilar.py`.

### Tasarım önerisi (en fazla 5 madde)

1. Şemaya `sorular` listesi ekle (metinden birebir kopya, dayanak denetimli); `baglam_ifadeleri` için istemde "yalnız kart bağlamı" kısıtı ve bir denetim (konusu `baglam_sozcugu`'nda eşleşmeyen ifade = hata) ekle.
2. `emin_degilim` yanında modelin kısa bir `eksik` alanı doldursun ya da kullanıcı mesajı koddan, durum ve kalıpla eşlenen bir DB tablosundan (`durum_mesaji`: anahtar, mesaj_tr, ne yazmalı) gelsin. Model metni yerine tablo, ilke 2 ile uyumlu.
3. `emin_degilim`'de de şema dışı denetim koşsun (dayanak, bağlam). `bilgi_yok_mu` denetimden sonra değerlendirilsin; bu çekirdekte değil, uygulama tarafında bir denetleyici sarmalıyla yapılabilir.
4. `__main__.py:63` ölü `"emin_degilim"` anahtarını kaldır ya da a_durumu'nu modelin `durum` değerine bağla; kullanıcıya "ne yazmalı" satırı ekle.
5. Ölçüm için soru içeren ve içermeyen belirsiz istekleri ayrı kategori yap (setler Web AI'dan; `beklenen_sonuc` alanına `soru` / `emin_degilim` ayrımı).

## Açık işler

- **DEVAM.md "Açık işler"** (`doc/DEVAM.md`):
  - Spot kontrol sonuçlanmadı.
  - G09 `desteklenmiyor` ama listesi dolu; V23 Çağrı B KULLANICIYA.
  - L-1…L-3.
  - v3: X05 (4x4 tuş takımı → GPIO_IN ×16), X34 (dayanakta "de" atlandı).
  - v2: W13 ve W19 Çağrı B KULLANICIYA.
  - Kart düzeyi sonraki tur.
- **DEVAM.md "Sıradaki iş":**
  - v4 sonuçlarının Sinan / Web AI değerlendirmesi.
  - Çağrı A denetimi aynı GPIO'nun iki listede birden olmasına ses çıkarmıyor.
  - Tekrarlanabilirlik için izde `prompt_eval_duration` eksik (çekirdek `Tur`).
- **Spot kontrol** (`doc/dogrulama/spot_kontrol.md`): 8 satır, sonuç sütunu 8'inde de boş. Sinan doldurmadı; sonuçlanan satır 0/8.
- **Kart düzeyi:**
  - Depoda ve veritabanında kart bilgisi yok. Tablolar yalnız çip düzeyinde (datasheet v1.6): `cip`, `paket`, `pin`, `gpio_islev`, `gpio_kisit`, `flash_pin` vb.
  - Super Mini (WS2812 GPIO8, durum LED'i GPIO15) ve nanoESP32-C6 (LED pini doğrulanmadı) bilgisi kayıtlarda geçmiyor. Kaynak belge `veri/kaynak/KAYNAKLAR.md`'de yok.
  - WS2812 / RMT arayüzü yok: `arayuz_tanimi`'nde 13 arayüz var (ADC, GPIO_IN, GPIO_OUT, I2C, I2S_IN, I2S_OUT, LP_I2C, LP_UART, PWM, SPI, TWAI, UART, WAKE). RMT sinyalleri yalnız datasheet tablosu `cevre_birim_sinyal`'de var.
- **Bilinen sınırlar** (`doc/KARARLAR.md:128-131`):
  - L-1: aynı SPI hattında ayrı CS'li çoklu cihaz ifade edilemiyor.
  - L-2: I2S_OUT ve I2S_IN tek denetleyici; tam çift yön modellenmedi.
  - L-3: cihaz adından arayüz çıkarımı model bilgisi (`model_cikarimi`).
  - L-4: çözüldü (T-39).

## FARK listesi

1. **Bağımsız sınav kaydı:**
   - Önceki çalıştırma (2026-11-21 10:15, önce QFN32 sonra QFN40) `doc/` belgelerinde, WORKLOG'da ve DEVAM'da yok.
   - Tek kaydı, commit edilmemiş CLI izi (`doc/olcum/iz/2026-11-21.jsonl` satır 17–18).
   - "Kullanıcıya neden söylenmiyor" ve "soru cümleleri bağlam ifadelerinde" zayıflıkları açık işler listesinde yok.
2. **Kod denetimleri:**
   - Özetteki listede yer almayan denetimler de var: ARAYUZ_BILINMEYEN, DURUM_TUTARSIZ, BELIRSIZ_PIN_TERCIHI, TERCIH_IHTIYACSIZ, TERCIH_SINYAL, PIN_UYDURMA (`cagrilar.py:73-150`).
   - Daha önemlisi: `emin_degilim` dönünce şema dışında hiçbir denetim çalışmıyor (`asu_llmcore/dongu.py:122-125`). Sınav cümlesinin bağlam ifadeleri hiç denetlenmedi.
3. **Çağrı A çıktıları:** özette `desteklenmeyenler` listesi yok; şemada var (`semalar.py:132`) ve `desteklenmiyor` durumu ona bağlı.
4. **RMT/WS2812:** KARARLAR'da bilinen sınır olarak kayıtlı değil (L kaydı yok). Bu yalnız bu adımda, arayüz listesinden çıkarılarak görüldü.
5. **Kart düzeyi bilgisi** (Super Mini GPIO8 / GPIO15, nanoESP32-C6): kayıtlarda hiç geçmiyor; kaynağı ve doğrulaması yok. DEVAM yalnız "kart düzeyi sonraki tur" diyor.
6. **v4 tercih sayısı:** 19/19, Adım 9b düzeltmesinden sonraki değer; ilk v4 raporunda 20/20'ydi (`doc/olcum/2026-11-21_v4_sonuc.md` baştaki eski–yeni tablosu). Özetle uyumlu, not olarak yazıldı.

Özetin geri kalanı kayıtlarla aynı: commit'ler (`88450d3`, `dcda8f3`, `5008c50`; çekirdek `41e2198`); K-6 / K-7 ve `--model-ata`; v1 A 22/30; v2 A 30/30 ve atayıcı 26/26; v3 uçtan uca 43/45 (X05, X34); v4 36/36 ve beklenen sonuçla 35/35; sınav cümlesinde iki pakette `emin_degilim`, uydurma yok; L-1…L-3.

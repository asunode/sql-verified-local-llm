# WORKLOG

## Adım 0 — 2026-11-20 (kurulum oturumu)

- PostgreSQL: `donanim` veritabanı, `donanim` (sahip) ve `donanim_okur` (salt okunur) rolleri, şifreler `~/.pgpass`'te. pg_hba değişmedi. Kayıt: yerel altyapı defteri (yayımlanmadı).

## Adım 1 — 2026-11-20

- **A. Çevirmen incelemesi** (salt okunur): `doc/cevirmen_dersleri.md`. Ollama ayarları, önbellek tutarsızlığı ve sınır isteği çözümü, JSON gözden geçirme, kod koruması, okuma rolüyle PostgreSQL, ölçüm kayıtları.
- **B. Çekirdek** `../asu_llmcore` (paket `asu_llmcore` 0.1.0, src düzeni; bağımlılıklar `psycopg[binary]`, `jsonschema`):
  - `ollama.py`: `OllamaAyar` (değiştirilemez), `OllamaIstemcisi.uret(mesajlar, sema, sabit_onek)` → `OllamaYaniti` (ham, json, süre, token, digest); her istekten önce önbellek sınırı.
  - `pg.py`: `PgOkuyucu(rol, veritabani).sorgu(sql, parametreler)` → sözlük listesi; salt okunur oturum.
  - `dongu.py`: `calistir(...)` → `Sonuc` (GECTI / BILGI_YOK / KULLANICIYA / JSON_GECERSIZ, tur izi).
  - `iz.py`: `kayit(sonuc, ayar, **ek)`, `IzYazici(yol).yaz(...)` (JSONL).
  - Testler: 16 birim/PG testi geçti; gerçek Ollama 2/2 geçti (aynı istek iki kez ve araya başka istek girince birebir aynı). Çıktı: `doc/olcum/2026-11-20_cekirdek_entegrasyon.txt`.
- **C. İskelet**: `.venv` (Python 3.14.4), `asu_llmcore` ve `pinsecim` düzenlenebilir kurulu; `src/pinsecim/`, `veri/kaynak/`, `setler/gelistirme/`, `doc/olcum/`, `testler/`; `CLAUDE.md`, `doc/KARARLAR.md` (K-1…K-5, teknik T-1…T-8).
- **D. Kaynak**: ESP32-C6 Series Datasheet v1.6 (2026-11-10), 87 sayfa, SHA-256 `c9bf7ece…c339`; pin bölümleri ve sayfaları `veri/kaynak/KAYNAKLAR.md`. Çıkarma yapılmadı.
- Notlar:
  - PG testleri ve Adım 0'ın yetki sınaması kasıtlı retler ürettiği için sunucu günlüğünde `donanim_okur@donanim` ERROR satırları var. Yerel durum betiği bunları gerçek hata sayar (altyapı defteri, yayımlanmadı).
  - Önceden var olan boş yerel klasörlere dokunulmadı.

## Adım 2 — 2026-11-20

- KARARLAR: T-1…T-8 Web AI denetiminden geçti; T-9 (pilot ölçümleri `en_cok_tur=3`) eklendi.
- Kaynak SHA-256 yeniden doğrulandı (`c9bf7ece…c339`).
- Şema `sql/001_sema.sql` (rol `donanim`, public): `kaynak`, `ham_metin`, `paket`, `cip`, `pin`, `gpio_islev`, `cevre_birim_sinyal`, `gpio_kisit`, `strapping_kombinasyon`, `flash_pin`, `dogrulama`. Her olgu satırında `kaynak_id`, `sayfa`, `referans`.
- Çıkarma A (`src/pinsecim/cikar_a.py`, çizgili tablo hücreleri + renk + kalın) ve B (`cikar_b.py`, Consolidated Pin Overview, kelime konumları) bağımsız. Karşılaştırma `karsilastir.py`: A–B 0 fark; A iç denetimleri 1 fark (Table 2-11 pin 9 SPI2 `GPIO1 (P2)`, belgede de böyle; belirsiz işaretli); renk ↔ metin 0 fark (renkten gelen kayıt yok).
- Görsel denetim: s. 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 25, 26, 27, 32, 33, 34, 36, 79, 80 (`dogrulama` tablosunda).
- Yükleyici `src/pinsecim/yukle.py` (tek işlem, tekrar çalıştırılabilir), CSV `veri/dogrulanmis/`. `donanim_okur` yeni tabloları ve sequence'ları okuyabiliyor, yazamıyor (varsayılan yetkiler).
- Satırlar: paket 2, cip 3, pin 74 (QFN40 41 / QFN32 33; GPIO 30 / 22), gpio_islev 154, cevre_birim_sinyal 656, gpio_kisit 30, strapping_kombinasyon 3, flash_pin 6, ham_metin 87, dogrulama 40.
- Testler `testler/test_veri.py`: 9 test + iskelet testi, 10/10 geçti.
- Belgeler: `doc/dogrulama/2026-11-20_fark_raporu.md`, `doc/dogrulama/spot_kontrol.md` (Sinan için 8 satır, sonuç sütunu boş).
- Yeni bağımlılık: `pdfplumber` (venv'e kuruldu, pyproject'e eklendi).

## Adım 3 — 2026-11-20

- Çekirdek (`asu_llmcore` `41e2198`): `Ihlal.seviye` (hata | uyari, varsayılan hata); döngü yalnız hataları geri gönderir, uyarılar `Tur.uyarilar` / `Sonuc.uyarilar` ve izde. 3 yeni test (uyarı-yalnız, hata+uyarı, geçersiz seviye); çekirdek 19/19.
- Şemalar `src/pinsecim/semalar.py` (pilot sözlüğü, istek ve atama JSON şemaları).
- `sql/002_kurallar.sql`: `cevre_adet` 10, `arayuz_tanimi` 13, `arayuz_sinyal` 6, `kural` 15, `yorum` 1. Veri `src/pinsecim/kural_verisi.py`; yükleyici aynı işlemde yazar, adetlerin dayanak ifadesini sayfa metninde arar.
- Adetler: UART 2 (s. 50), LP UART 1 (s. 50), I2C 1 ve LP I2C 1 (s. 51), SPI2 1 (s. 50), I2S 1 (s. 4, tekil ifade), TWAI 2 (s. 4), LED PWM 6 (s. 55), ADC 7 (s. 57; Table 2-9 ile denetlendi), LP GPIO 8 (Table 2-7 sayımı).
- Yorum: Table 2-11 QFN32 pin 9 SPI2 → GPIO3 (Web AI).
- `src/pinsecim/pinveri.py` (veri, donanim_okur; ulaşılamazsa VeriHatasi), `denetim.py` (denetleyici), `atayici.py` (geri izlemeli, eşleştirme budamalı, en az uyarılı).
- Testler `testler/test_denetim.py`: 35/35 vaka; atayıcı vaka isteklerinde çözdüğü her atama sıfır hata, çözemedikleri tam olarak ADET_ASIMI vakalarının istekleri; 200 rastgele istek (tohum 20261120): 144 çözüm (30'u uyarılı), hepsi sıfır hata, 56 mumkun_degil (32 adet, 24 pin). Proje toplam 57/57.
- Not: ilk atayıcı sürümü budama zayıf olduğu için rastgele testte takıldı (test 600 sn'de durduruldu); alt sınırlı budamayla 200 istek 0,07 sn.
- Vaka dosyası değiştirilmedi (SHA-256 testte sabit). Yerel bir kopyası depoya eklenmedi.

## Adım 4 — 2026-11-20

- KARARLAR: L-1…L-3 (Web AI) eklendi; teknik T-18…T-24.
- `arayuz_tanimi.tanim` sütunu (`sql/003_arayuz_tanim.sql`), İngilizce tek satırlık tanımlar `kural_verisi.ARAYUZ_TANIMLARI`; CSV yeniden dışa aktarıldı.
- İstemler `src/pinsecim/istemler/ihtiyac_sistem.txt` (Çağrı A, 3 yeni Türkçe örnek, setten değil) ve `atama_sistem.txt` (Çağrı B). Şemalar `semalar.ihtiyac_semasi`, `semalar.model_atama_semasi`.
- Kod: `cagrilar.py` (A ve B, çekirdek döngüsü, en_cok_tur 3, sınır açık), `hat.py` (uçtan uca + iz `doc/olcum/iz/<tarih>.jsonl`), `__main__.py` (CLI), `olcum.py` (önbellek ve geliştirme koşuları).
- v0 öncesi düzeltme: Çağrı B "atandi" tanımı (T-23).
- Önbellek ölçümü (G01–G10): A K1=K2 10/10, K3 farklı 0/10; B K1=K2 8/8, K3 farklı 1/8 (G07, yalnız gerekçe metni). `doc/olcum/2026-11-20_onbellek.md`.
- Geliştirme seti v0: A 20/20; B 18/18 1. turda; model–atayıcı 18/18 aynı; ort. 66,7 sn, en uzun 173,2 sn. Revizyon 0/3 (`doc/olcum/gelistirme_gecmisi.md`).
- Örnek CLI çıktısı `doc/olcum/2026-11-20_ornek_cli.txt`.
- Testler `testler/test_cagrilar.py` 9 (modelsiz); proje 66/66.
- Çekirdek değişmedi. Geliştirme seti dosyası değiştirilmeden depoya eklendi; yerel kopya klasörü eklenmedi.

## Adım 4b — 2026-11-20 (ara kayıt)

- Gün kapanışı: Adım 0–4 bitti; devam notu `doc/DEVAM.md`, CLAUDE.md başına ona işaret eden satır. Kod değişmedi. Sıradaki: Adım 5 (görülmemiş setle ölçüm).

## Adım 5 — 2026-11-20

- Doğrulama seti `setler/dogrulama/dogrulama_seti_v1.json` SHA-256 doğrulandı (`12211f6e…3908`), içeriğine bakılmadan betiğe verildi.
- Dondurma: `doc/olcum/2026-11-20_dogrulama_dondurma.md`. 11 dosya, 5 kural tablosu, iki commit; öncesi ve sonrası aynı.
- Yeni: `src/pinsecim/dogrulama.py` (dondurma, kos, rapor), `src/pinsecim/istemler/atama_sistem_tablosuz.txt`. İstem, şema, kural, denetleyici, atayıcı değişmedi. KARARLAR T-25…T-27 (T-26/T-27 Adım 6'da T-28/T-29 oldu).
- Koşular (en_cok_tur 3, sınır açık), ham `doc/olcum/2026-11-20_dogrulama_ham.jsonl` (100 satır), sonuç `doc/olcum/2026-11-20_dogrulama_sonuc.md`:
  - Model: A 22/30; B 23 ilk turda, 2 üçüncü turda; A durdurduğu için B'ye gelmeyen 5; hakemle 23/25; aynı ihtiyaçlarla atayıcıyla 25/25; uyarı farkı 0.
  - Atayıcı (A ihtiyaçlarıyla): hakemle 23/25.
  - Tablosuz: B 14/5/5 (1./2./3. tur), KULLANICIYA 1; hakemle 22/25; uyarı farkı +39 (21 istek).
  - Tekrar: A 10/10, B 9/9 birebir. Pipeline hatası yok.
- Süre (ort./ortanca/en uzun): A 39,1/28,2/87,7 sn; B 90,5/52,4/470,9 sn; tablosuz B 141,4/55,1/589,4 sn.
- Testler 66/66 (ölçümden sonra).

## Adım 6 — 2026-11-20

- KARARLAR: Web AI T-26 (v1 görülmüş set), T-27 (komut satırı bağlamı esas); Adım 5'in DAI kararları T-28/T-29'a taşındı. DAI kararları T-30…T-38, bilinen sınır L-4.
- F1: şemada `adet` (≥1); kod kalemleri çoğaltıp kimlik verir (`cagrilar.genislet`). SAYI_UYUSMAZ (hata, geri gönderilir): dayanaktaki sayı ifadesi adetle tutmazsa; I2C/LP_I2C muaf (`arayuz_tanimi.paylasimli_hat`). Sayı sözlüğü `sayi_sozcugu` (26 satır), ayrıştırıcı `src/pinsecim/sozluk.py`.
- F2: şemada `baglam_ifadeleri`; desteklenmiyor'a yol açmaz. BAGLAM_CELISKI uyarısı, CLI `[UYARI]` satırı. Anahtar sözcükler `baglam_sozcugu` (21 satır: konu + olumsuzluk).
- F3: `tamam` + boş liste geçerli; Çağrı B çalışmaz, CLI "Bu istek için pin ataması gerekmiyor."
- F4: WAKE, GPIO_IN/OUT, PWM tanımları (`kural_verisi.py`, `arayuz_tanimi.csv`).
- Şema/DB: `sql/004_istek_sozlugu.sql`; yükleyici iki tabloyu ve CSV'lerini (`veri/dogrulanmis/sayi_sozcugu.csv`, `baglam_sozcugu.csv`) yazar.
- `dogrulama.py`: `gerileme` alt komutu, set yolu/SHA parametreli koşu ve rapor, `dondurma --ad`. Adım 5 raporu yeni kodla yeniden üretildi: sayılar aynı (dosyanın üzerine yazılmadı).
- Testler 66 → 114 (`testler/test_sozluk.py` 36 ayrıştırıcı + 6 bağlam durumu; F1–F3 birim ve uçtan uca; istem örneği parçalarının setlerde geçmediği testi genişletildi).
- Gerileme (en_cok_tur 3, sınır açık; model + atayıcı; tablosuz yok), `doc/olcum/2026-11-20_gerileme_r{0,1,2}.md`:
  - r0: geliştirme A 19/20, v1 (görülmüş) A 28/30; SAYI_UYUSMAZ 1 + 3 istek; BAGLAM_CELISKI 0.
  - r1 (istem + Çağrı A geri bildirim metinleri): geliştirme 19/20, v1 30/30.
  - r2 (istem): geliştirme 19/20 (G09 `desteklenmiyor` ama listesi dolu), v1 30/30; B 23/1/2 + 1 KULLANICIYA; hakemle 26/27; SAYI_UYUSMAZ 2 istek; BAGLAM_CELISKI 0.
  - Ayrıntı `doc/olcum/gelistirme_gecmisi.md`. 2/2 revizyon kullanıldı.
- Çağrı B denetleyicisi, atayıcı, pin kuralları, setler ve vaka dosyası değişmedi; çevirmene dokunulmadı.
- v2 dondurma (`--ad v2 --asama once`): `doc/olcum/2026-11-20_v2_dondurma.md`; 13 dosya, 7 kural tablosu; proje `561eb23`, çekirdek `41e2198`. ihtiyac_sistem.txt `164fa748b37b`, atama_sistem.txt `f09040e1f110`. v2 ölçümü bu kayıtla yapılır.

## Adım 7 — 2026-11-21

Bölüm 1 (v2 açılmadan):
- KARARLAR: Web AI T-39 (L-4: model_cikarimi kalemde adet dayanaktaki sayının tam katı olabilir; istekte_acik eşit), T-40 ("çift yönlü" sayı değil). DAI T-41…T-44. L-4 çözüldü.
- `cagrilar.adet_tutar`; SAYI_UYUSMAZ mesajı kaynağa göre (r1 ipucu kaldırıldı). İstem dosyaları değişmedi.
- `sql/005_sayi_istisnasi.sql`: `sayi_sozcugu.deger` NULL = sayı değil; "çift yönlü" satırı (27 satır). Ayrıştırıcı istisnayı tüketir.
- `dogrulama.py`: `kos`/`rapor` için `--set --sha --ham --kosular --sonuc --dondurma --tarih`; `dondurma` için `--tarih --set --not`, üzerine yazmaz; rapora KULLANICIYA–hakem bölümü. Adım 5 raporu yeniden üretildi, ana sayılar aynı.
- Testler 114 → 128 (kat kuralı 9, "çift yönlü" 5 + DB).
- Duman testi (kendi cümlelerim, model): "İki enkoder … dört LED" → GPIO_IN ×4 + GPIO_OUT ×4, B 1. turda; "Çift yönlü dönen bir fan…" → PWM + GPIO_OUT, SAYI_UYUSMAZ yok; "JTAG ile hata ayıklayacağım; … BMP388 … I2C" → I2C + BAGLAM_CELISKI uyarısı. Üçünde atayıcıyla karar aynı.
- `dondurma` sonrası: commit farkı `git diff --name-only` ile okunur; yalnız `doc/` altındaysa aynı sayılır (dondurma kaydı ayrı commit'lendiği için).
- v2 dondurma (yeni): `doc/olcum/2026-11-21_v2_dondurma.md`; 14 dosya (v2 seti dahil), 7 kural tablosu; proje `84edee4`, çekirdek `41e2198`. Eski 2026-11-20 kaydı değişmedi.

Bölüm 2 (v2 ölçümü, kod/istem/şema/kural/sözlük değişmedi):
- Set SHA `aff56f72…dcc9` doğrulandı. Koşular: model (30), atayıcı (A ihtiyaçlarıyla + hakem), tekrar (ilk 10); arka planda, sınır açık, en_cok_tur 3; ham 70 satır `doc/olcum/2026-11-21_v2_ham.jsonl`, günlük `2026-11-21_v2_kos.log`.
- Dondurma sonrası: öncesiyle aynı (dosyalar, 7 tablo; proje commit farkı yalnız `doc/`, çekirdek `41e2198`).
- Sonuç `doc/olcum/2026-11-21_v2_sonuc.md`: A 30/30 (30 istek 1. turda), SAYI_UYUSMAZ 0, BAGLAM_CELISKI 1 (W09); B 23/1/0 + 2 KULLANICIYA (W13, W19; hakem ikisinde mumkun_degil, model son turda CAKISMA'lı atandi); karar hakemle 24/26, atayıcı (A ihtiyaçlarıyla) hakemle 26/26; model_cikarimi 59/61 (W28 0/2); tekrar A 10/10, B 7/7 birebir; pipeline hatası yok.

## Adım 8 — 2026-11-21

Bölüm 1 (v3 açılmadan; istem dosyaları değişmedi):
- KARARLAR: K-6 (Sinan: model yalnız isteği anlar, atamayı kod atayıcı yapar; `--model-ata` kalır). DAI T-45…T-48.
- Varsayılan akış A → atayıcı (`hat.calistir(model_ata=False)`); `--atayici` kaldırıldı, `--model-ata` eklendi. v1/v2 ölçüm kodu `model_ata=True` ile eski davranışta.
- Atayıcının `mumkun_degil` nedeni Türkçe ("19 sinyal için yalnız 18 uygun pin var (QFN32; 7 GPIO_IN, …)", "ADC için 9 birim gerekiyor, çipte en çok 7 kullanılabilir (…)").
- Denetleyici atayıcının atamasını da denetler; hata → CLI'de "YAZILIM HATASI", izde `yazilim_hatasi`. İze `atayan` eklendi.
- `pinsecim.kapsamli` (kos/rapor): A + atayıcı + hakem, tekrar (yalnız A), kategori, çift tutarlılığı, SAYI_UYUSMAZ yanlış alarm / gerçek yakalama, durum kullanımı, uzunluk–süre, uçtan uca, şans eseri doğru, CLI metni.
- Testler 128 → 133 (varsayılan akış, Türkçe neden ×2, yazılım hatası, kapsamlı kos+rapor sahte modelle).
- Duman testi (kendi cümlelerim, model, A → atayıcı): "Bir nem sensörünü I2C ile okuyup iki rölenin …" (QFN32) → I2C + GPIO_OUT ×2, atandı; "Toprak nemini ölçen dokuz analog prob …" (QFN32) → ADC ×9, karşılanamıyor, neden ADC 9 > 7 (4.2.2.1 p.57); "Bahçe kapısı için bir CAN alıcı-vericisi ve bir uyandırma düğmesi …; USB'yi kullanmayacağım." (QFN40) → TWAI + WAKE, atandı, BAGLAM_CELISKI uyarısı.
- v3 seti (`setler/dogrulama/kapsamli_set_v3.json`) SHA-256 doğrulandı (2497ff34…8967); açılmadı.
- v3 dondurma: `doc/olcum/2026-11-21_v3_dondurma.md`; 17 dosya (v3 seti, kapsamli.py, __main__.py, dogrulama.py dahil), 7 kural tablosu; proje `70330c4`, çekirdek `41e2198`. İstem, şema, cagrilar.py, sozluk.py ve tablolar v2 kaydıyla aynı.

Bölüm 2 (v3 ölçümü; kod/istem/şema/kural/sözlük değişmedi):
- Set SHA `2497ff34…8967` doğrulandı. Koşular: a_atayici (45, hakemle), tekrar (ilk 15, yalnız A); arka planda, sınır açık, en_cok_tur 3; ham 60 satır `doc/olcum/2026-11-21_v3_ham.jsonl`, günlük `2026-11-21_v3_kos.log`.
- Dondurma sonrası: öncesiyle aynı (17 dosya, 7 tablo; proje commit farkı yalnız `doc/`, çekirdek `41e2198`).
- Sonuç `doc/olcum/2026-11-21_v3_sonuc.md`: A 43/45 (tur 41/1/0, BILGI_YOK 2, KULLANICIYA 1); SAYI_UYUSMAZ 0; BAGLAM_CELISKI 1 (X28); atayıcı 39 atandi / 3 mumkun_degil; yazılım hatası 0; karar hakemle 41/42; uçtan uca 42/45 (betik); çift 4/4; tekrar A ham 13/15 (X03, X11: yalnız dayanak metni farklı, çoklu küme aynı).
- Yanlışlar: X05 (4x4 tuş takımı → GPIO_IN ×16; atayıcı mumkun_degil, hakem atandi), X34 (A KULLANICIYA: dayanak "bir I2C sensör var", metinde "bir de I2C sensör var"; 3 tur DAYANAK_YOK).
- Ölçümden sonra fark edilen betik hataları (düzeltilmedi, Bölüm 2 sınırı): (1) `kapsamli.hakem`: A, 'tamam' olmayan bir kabul seçeneğiyle eşleşince hakem yok sayılmalıydı; ilk 'tamam' seçeneğine düşüyor. X33 (emin_degilim, kabulde var) bu yüzden uçtan uca ✗; doğru sayımla uçtan uca 43/45, "belirsiz" 2/2. (2) Yanlışlar tablosunun "Verilen" sütunu A'nın durumu KULLANICIYA iken son turun yanıtını gösteriyor (X34 "tamam [GPIO_IN I2C]"); durum ayrıntı tablosunda KULLANICIYA.

## Adım 8b — 2026-11-21

- Puanlama düzeltmesi (yalnız rapor kodu, T-49): `dogrulama.hakem_sec` (A 'tamam' dışı kabul seçeneğiyle eşleşince hakem yok), `dogrulama.verilen_metni` (A KULLANICIYA / JSON_GECERSIZ ise o durum + son turun yanıtı); `kapsamli` ikisini kullanır. Model yeniden çalıştırılmadı.
- Testler 133 → 135 (hakem seçimi, KULLANICIYA'da verilen).
- Dondurma kaydına göre: yalnız `kapsamli.py` (9927c812 → 5039a3a5) ve `dogrulama.py` (a2e792a5 → c52f47a6) değişti; istemler, şema, cagrilar, hat, atayıcı, denetleyici, sözlük, setler ve 7 tablo aynı. Dondurma kaydı değiştirilmedi.
- Sınama: v1 (Adım 5), v2 (Adım 7) sonuçları ve r0–r2 gerileme raporları eski ve yeni kodla üretilip kıyaslandı: sayılar aynı; değişen yalnız tanım satırı, r0 V01 "verilen" (KULLANICIYA (son tur: …)) ve r1 V28 hakem sütunu (atandi → -). Commit'li belgeler değiştirilmedi.
- v3 sonucu yeniden üretildi, başına not ve eski–yeni tablo: uçtan uca 42/45 → 43/45, `belirsiz` 1/2 → 2/2, X33 hakem atandi → yok, X34 verilen → KULLANICIYA (son tur: tamam [GPIO_IN I2C]).

## Adım 9 — 2026-11-21

Bölüm 1 (v4 açılmadan):
- KARARLAR: K-7 (Sinan: pin tercihleri). DAI T-50…T-57.
- `sql/006_pin_tercihleri.sql`: `pin_bahsi_deseni` (5 desen: gpio, liste_devami, belirsiz ×3), `kural.mesaj_tr`. Kurallara YASAK_PIN ve TERCIH_UYGULANMADI (17 kural). Matris cihaz tanımı GPIO_IN / GPIO_OUT tanımlarına. DB yeniden yüklendi; CSV'ler güncel.
- Çağrı A şeması: `pin_tercihleri`, `kullanilmayacak_pinler`, `diger_pin_bahisleri`. Denetimler: PIN_BAHSI_ATLANDI, PIN_UYDURMA, BELIRSIZ_PIN_TERCIHI, TERCIH_IHTIYACSIZ, TERCIH_SINYAL; uyarılar BELIRSIZ_PIN_BAHSI (Türkçe), ESNEK_DAYANAK.
- Esnek dayanak (`sozluk.dayanak_bul`), gerçek parça kaydedilir, sayı denetimi onun üzerinden. Kesme işaretli ek sözcüğün parçası (duman testinde "13'e" → "13 ve 18'e" eşleşmesi görüldü, düzeltildi).
- İstem kural 10 + bir örnek; listede çıplak sayının dayanağı ipucu (istem ve DAYANAK_YOK geri bildirimi). İstem–set çakışma testi geliştirme + v1–v3 + arayüz tanımları: geçti.
- Atayıcı: tercih ön denetimi, kilitleme, YER_YOK, `tercih_uygulanamadi` + alternatif; `mumkun_degil` tercihten bağımsız. Denetleyici alternatifi denetler. CLI: pin listeleri, [tercih] işareti, neden + öneri, ALTERNATİF tablo, Türkçe uyarılar.
- Puanlama (`dogrulama.a_eslesen`) pin tercihleri ve yasaklarla; hakem tercih/yasaklarla; `kapsamli` v4 bölümleri. v1, v2, v3 raporları yeni kodla: sayılar aynı.
- Tekrarlanabilirlik incelemesi (X03, X11): `doc/olcum/2026-11-21_v3_tekrar_inceleme.md`. Girdi farkı yok (sınır isteği gitti, mesajlar, model özeti, önceki istek ve yanıtı aynı); ayrışma dayanak uzunluğunda; net yazılım hatası yok. `istem_token` açıklaması (çekirdek) bu Ollama sürümüyle uyuşmuyor olabilir.
- Testler 135 → 155.
- Duman testi (kendi cümlelerim, son istemle): BMP280 I2C GPIO20 (SDA) / GPIO21 (SCL) + iki buton (QFN40) → atandı, tercihler uygulandı; "Üç LED'i GPIO12, 13 ve 18'e" (QFN40, USB açık) → tercih_uygulanamadı, GPIO12/13 PIN_USB + "--no-usb" önerisi, ALTERNATİF (GPIO18 tercihli); servo PWM + analog sıcaklık, "GPIO0 ve GPIO1'e hiçbir şey bağlanmasın" (QFN32) → atandı, ADC GPIO2; "Bir röleyi 5 numaralı pine" → belirsiz pin uyarısı, 1. turda BELIRSIZ_PIN_TERCIHI, 2. turda geçti.
- v4 seti SHA-256 doğrulandı (3c449e7c…df07); açılmadı.
- v4 dondurma: `doc/olcum/2026-11-21_v4_dondurma.md`; 19 dosya (v3 ve v4 setleri, sql/006, kapsamli.py, __main__.py, dogrulama.py dahil), 8 kural tablosu; proje `8e393e9`, çekirdek `41e2198`.

Bölüm 2 (v4 ölçümü; kod/istem/şema/kural/sözlük değişmedi):
- Set SHA `3c449e7c…df07` doğrulandı. Koşular: a_atayici (36, hakemle), tekrar (ilk 12, yalnız A); arka planda, sınır açık, en_cok_tur 3; ham 48 satır `doc/olcum/2026-11-21_v4_ham.jsonl`, günlük `2026-11-21_v4_kos.log`.
- Dondurma sonrası: öncesiyle aynı (19 dosya, 8 tablo; proje commit farkı yalnız `doc/`, çekirdek `41e2198`).
- Sonuç `doc/olcum/2026-11-21_v4_sonuc.md`: A 36/36 (tur 35/1/0); atayıcı 27 atandi / 7 tercih_uygulanamadi / 1 mumkun_degil / 1 pin gerekmiyor; PIN_BAHSI_ATLANDI 0, PIN_UYDURMA 0, belirsiz pin uyarısı 1 (Y17; BELIRSIZ_PIN_TERCIHI 1. turda, 2. turda geçti); esnek dayanak 1 (Y01: «bir I2C sensör var» → «bir de I2C sensör var»); matris Y23, Y24 doğru; hakem–beklenen_sonuc 34/35 (Y13); yazılım hatası 0; uçtan uca 36/36; tekrar A 12/12.
- Ölçümden sonra bulunan hatalar (düzeltilmedi, Bölüm 2 sınırı): (1) Atayıcı `_tercih_on_denetimi` birebir aynı tercihi tekrar sayıp atlıyor (`if t in gecerli: continue`). Y13 "İki buton da GPIO20'ye bağlı olsun": Çağrı A iki GPIO_IN → GPIO20 tercihi verdi (doğru), atayıcı birini uyguladı, ikinci butonu GPIO0'a koyup "atandı (pin tercihleri uygulandı)" dedi; beklenen tercih_uygulanamadi (aynı pine iki tercih). Hakem aynı kodu kullandığı için o da atandi; uçtan uca 36/36 bu yüzden Y13'ü doğru sayıyor. (2) Ölçüm betiğinin "tercihler uygulandı" denetimi tercih edilen pinin aynı arayüzce kullanılmasına bakıyor, tercih sayısına bakmıyor; Y13 "evet" sayıldı (doğru sayımla 19/20).

## Adım 9b — 2026-11-21

- Tercih eşleme düzeltmesi (T-58): atayıcı aynı iki tercihi AYNI_PIN sayar; FAZLA_TERCIH arayüz toplamına da bakar; denetleyici TERCIH_UYGULANMADI ve ölçüm "tercihler uygulandı" sayımında bir pin tek tercihi karşılar. İstem, şema, Çağrı A denetimi, kurallar ve sözlük değişmedi.
- Taranan tekilleştirme noktaları: atayıcı ön denetimi (hata, düzeltildi), denetleyici tercih denetimi (aynı kör nokta, düzeltildi), ölçüm sayımı (düzeltildi), FAZLA_TERCIH karışık grup (düzeltildi), `hat.py` kullanılmayacak kümesi (zararsız), Çağrı A'da aynı GPIO iki listede (raporlandı, değişmedi).
- `kapsamli yeniden-ata`: kayıttan, model çalışmadan.
- Testler 155 → 160 (iki ihtiyaç aynı GPIO, tercih + yasak aynı GPIO, aynı sinyale iki GPIO + karışık SPI, denetleyici aynı pine iki tercih, yeniden-ata).
- v1, v2, v3 raporları yeni kodla: Adım 9 koduyla üretilenle birebir aynı.
- v4b dondurma: `doc/olcum/2026-11-21_v4b_dondurma.md`; v4 kaydına göre değişen yalnız atayici.py, denetim.py, kapsamli.py (T-58); proje `88450d3`, çekirdek `41e2198`. Eski v4 kaydı değişmedi.
- v4 yeniden atama (model çalışmadı): `kapsamli yeniden-ata` → `doc/olcum/2026-11-21_v4b_ham.jsonl` (48 satır; 36 istekte Çağrı A mesajları, yanıtı ve durumu eskisiyle aynı; tekrar satırları kopya). Dondurma v4b sonrası: öncesiyle aynı.
- Değişen istek: yalnız Y13 (karar atandi → tercih_uygulanamadi, AYNI_PIN; hakem atandi → tercih_uygulanamadi). Sayılar: atayıcı 27/7/1/1/0 → 26/8/1/1/0; tercihler uygulandı 20/20 → 19/19; hakem–beklenen_sonuc 34/35 → 35/35; A 36/36, uçtan uca 36/36, tekrar 12/12 aynı.
- `doc/olcum/2026-11-21_v4_sonuc.md` yeniden üretildi; başına not ve eski–yeni tablo.

## Adım 10 — 2026-11-21 (K-8: soru ayrımı, kart kaynakları)

Bölüm 0:
- CLI izi commit'lendi (`2c62781`).
- `doc/dogrulama/bagimsiz_sinav.md`: cümle 1, dört çalıştırma, değerlendirme, iki zayıflık.
- KARARLAR K-8, L-5; DEVAM açık işleri (`62f1a2a`).

Bölüm 1 (yalnız araştırma, DB'ye yazılmadı):
- nanoESP32-C6: MuseLab GitHub deposu ve şematik v1.0 (SHA-256 a2ca1ca2…). Kart ESP32-C6-WROOM-1 modülü kullanıyor; WS2812B GPIO8; BOOT GPIO9; native USB GPIO12/13; CH343P TXD0/RXD0.
- Super Mini: üretici kaynağı yok; topluluk şematik taraması (SHA-256 248cabd3…). Satırların tümü doğrulanmadı.
- Elle kontrol listesi ve `kart` / `kart_pin` / `kart_parca` taslağı: `doc/raporlar/adim10_rapor.md`.

Bölüm 2:
- `sql/007` (`soru_konusu` 8, `durum_mesaji` 12), yükleyici, CSV'ler, dondurma tablo listesi (`7867d5e`).
- Şema: `sorular` + `eksik`. İstem kural 4, 8, 9, 10, 11 ve iki yeni örnek. Konu ve eksik listeleri sistem isteğinde.
- Denetim: emin_degilim/desteklenmiyor denetleniyor (T-59), soru dayanağı, BAGLAM_KONUSUZ, eksik tutarlılığı, sorudaki GPIO.
- `cevap.py` (T-61). `hat.py`: cevaplar + bildirim.
- CLI: ihtiyaçlar → sorular/cevaplar → neden/ne yazmalısın → atama → uyarılar; ölü "emin_degilim" anahtarı kaldırıldı.
- Testler 160 → 174; çekirdek 19/19, değişmedi (`b9686dd`).
- Dondurma öncesi `doc/olcum/2026-11-21_adim10_dondurma.md` (`f83c622`); sonrası: aynı.

Ölçüm (kod/istem/şema/kural/sözlük değişmedi):
- v4 (36): A 34/36, uçtan uca 34/36. **Kabul ölçütü (36/36) karşılanmadı.**
  - Y33 "On altı buton" → GPIO_IN 6.
  - Y34 "On yedi buton" → GPIO_IN 7 ve atandi; doğrusu mumkun_degil.
  - Dayanak "altı buton" / "yedi buton" metinde aynen geçtiği için SAYI_UYUSMAZ yakalamadı.
  - Tercihler 19/19 korundu; Y34 atandığı için sayım 20/20.
  - Tur 31/5/0.
- v3 (45): A 43/45, uçtan uca 43/45 (ölçüt karşılandı).
  - X05 düzeldi (4x4 tuş takımı 8 hat).
  - X32/X33 BILGI_YOK → emin_degilim + eksik.
  - X34/X35 pin tercihi yakalandı; set tercih öncesi yazıldığı için yanlış sayıldı.
  - Tur 33/12/0; BAGLAM_KONUSUZ 16 ifade.
- Sonuçlar: `doc/olcum/2026-11-21_adim10_v4_sonuc.md`, `2026-11-21_adim10_v3_sonuc.md`.
- Sınav cümlesi 2 paket × 2 kez (iz satır 25–28):
  - İki soru `sorular`'da (kart_led, arayuz_pinleri), bağlam boş, uydurma pin yok.
  - Çağrı A ham yanıtı dört çalıştırmada aynı (ee4cf446…).
  - Çıktı süre satırı dışında aynı.
  - S2 arayüz adı içermediği için "eksik bilgi" cevabı aldı.
- Rapor `doc/raporlar/adim10_rapor.md`. KARARLAR T-59…T-61.

## Adım 10a — 2026-11-21 (bileşik sayı, diger_ifadeler, eş adlar)

- Durum: başlangıçta yalnız yerel kopya klasörü commit dışıydı (kural). Adım sırasında `doc/dogrulama/.~lock.spot_kontrol.md#` (LibreOffice kilidi) belirdi; dokunulmadı.
- `sql/008`: `sayi_sozcugu.basamak`, deger ≥ 0, `arayuz_es_adi` (9 eş ad). Sayı sözlüğü 27 → 32 satır ("on bir"…"on dokuz" kaldırıldı; otuz–doksan, yüz, bin, sıfır ve 4 istisna eklendi). DB yeniden yüklendi (`43c932b`).
- `sozluk.sayi_araliklari` (Türkçe diziliş, bitişik yazım, konumlu); `arayuz_adlari` (eş adlarla); cevaplayıcı eş adları kullanıyor.
- Denetim: DAYANAK_SINIRI, tam sayıyla SAYI_UYUSMAZ, SAYI_YARIM, diger_ifadeler dayanağı, DIGER_IHTIYAC_IZI, BAGLAM_KONUSUZ iletisi diger_ifadeler'e yönlendiriyor. Şema diger_ifadeler; istem kural 4 ve bir örnek; CLI bölümü; `kapsamli rapor` tur dökümü ve diger_ifadeler bölümü (`38301c8`).
- Testler 174 → 235 (`test_sayi_10a.py` 61); çekirdek 19/19, değişmedi.
- Duman testi (kendi cümlem): "Yirmi üç spot…" → GPIO_OUT ×23, ikinci cümle diger_ifadeler'de.
- v3 sonucuna Web AI hükmü. WROOM-1 datasheet v1.4 okundu (SHA-256 16302076…): modül pinleri K2 ile birebir; çip ESP32-C6 QFN40, harici QSPI flash; flash sürümü bulunamadı.
- Dondurma `2026-11-21_adim10a_dondurma.md` (öncesi `97055e6`; sonrası aynı).
- Ölçüm (kod/istem/sözlük değişmedi):
  - v4 A 35/36. Y33/Y34 2. turda SAYI_UYUSMAZ ile düzeldi (Y33 16 atandi, Y34 mumkun_degil). Y29 yeni yanlış: GPIO3 tercihi diger_pin_bahisleri'ne kaydı, atama GPIO0. Tercihler 18/18. Tur 32/4/0.
  - v3 A 43/45 (X34/X35). Karar değişikliği yok. Tur 36/8/1; BAGLAM_KONUSUZ 16 → 9 ifade; X45 gerçek yakalama ("iki buton" → "On iki"); X22 DAYANAK_SINIRI 2 tur.
  - diger_ifadeler uyarısı 8 öğe, ihtiyaç kaybı yok. X28: flash bağlam cümlesi diger_ifadeler'e düştü, BAGLAM_CELISKI uyarısı kayboldu (karar aynı).
  - Sınav cümlesi 2 paket × 2 (iz 30–33): soru ayrımı aynı, ham yanıt dört çalıştırmada aynı (dcf38030…).
- Rapor `doc/raporlar/adim10a_rapor.md`. KARARLAR T-62…T-64.

## Adım 10b — 2026-11-21 (denetim düzeltmeleri, kart verisi; istem aynı)

- Spot kontrol: `spot_kontrol_sinan.md` 8/8 ✓; `spot_kontrol.md`'ye işlendi; kilit kalkmıştı, iki dosya commit'lendi (`22ec998`); DEVAM'da kapandı.
- Denetim (`a57eefc`): DIGER_PIN_TERCIH_IZI, DIGER_BAGLAM, "bir" DIGER_IHTIYAC_IZI dışı, CAN harfe duyarlı (sql/009), atayıcı neden metninde toplam. Testler +27 (`test_denetim_10b.py`) +1.
- Kart verisi (`1b5de4b`):
  - Üretici deposu git geçmişiyle tarandı: tek şematik v1.0, v0.2 yok; ürün fotoğrafında "v1.0".
  - Kaynaklar K2, W1, S2, E1 `veri/kaynak/`'a kopyalandı, KAYNAKLAR.md'ye eklendi; K3 kaydedilmedi.
  - sql/010–011, `kart_verisi.py`, yükleyici. Satırlar: kart 3, modul_pin 29, kart_pin 85, kart_parca 21. Yeniden yükleme CSV'leri aynı üretti.
  - İlk sürümde koşulsuz `ALTER TABLE kaynak` test bağlantısının açık işlemiyle kilit bekledi (pytest asıldı, durduruldu); göçler koşullu yapıldı.
- CLI ve cevaplayıcı (`12279a1`): --kart (paket karttan, çelişkide hata), cevap.kart_eksik, kart soruları (kaynak, doğrulama durumu, strapping uyarısı, görev notu), kartlı atama notu. Testler +17 (`test_kart_10b.py`); toplam 280; çekirdek 19/19.
- Kapsamlı rapora son tur uyarıları bölümü. İstem ve sistem metni 10a iziyle birebir aynı (ölçüm öncesi denetlendi).
- Dondurma `2026-11-21_adim10b_dondurma.md` (öncesi `249043d`, sonrası aynı).
- Ölçüm:
  - v4 A 35/36 (Y29 yanlış, DIGER_PIN_TERCIH_IZI uyarılı; GPIO2 uyarısı yanlış alarm), tercihler 18/18, Y33/Y34 doğru.
  - v3 43/45 (X34/X35). Kararlar 10a ile 81 isteğin hepsinde aynı.
  - DIGER_BAGLAM X28 ve Y18'de doğru yakalama; ikisinde BAGLAM_CELISKI geri geldi. Y18'deki kayıp 10a raporunda atlanmıştı.
  - SAYI_YARIM X17'de yanlış alarm ("bir çift" / "çift").
- Sınav cümlesi 3 biçim × 2 (iz 34–39): ham yanıt altısında ve 10a ile aynı; kartlı S1 LED'leri kaynaklı ve DOĞRULANMADI işaretli, görev notu var; kartsız kart_eksik; S2 aynı.
- Rapor `doc/raporlar/adim10b_rapor.md`. KARARLAR T-65, T-66.

## Adım 10c — 2026-11-21 (kart düzeyi atama, SPI çoklu CS, RMT, --rapor)

- SPI çoklu CS ve RMT (`1abac04`):
  - L-1: `arayuz_tanimi.ortak_hat_secim` (sql/012), `PinVerisi.yuva_sinyalleri`, SPI2_CS = 6 (s. 51), taşma iletisi kaynaklı.
  - L-5: RMT_TX / RMT_RX (GPIO matrisi, RMT 4 kanal s. 56), eş adlar ws2812 / neopixel / adreslenebilir led.
  - Sistem metninde yalnız iki arayüz satırı; istem dosyası 3ff741e27c2e aynı.
  - Küçük düzeltmeler: SAYI_YARIM değer farkında; kart_eksik örneği ilk uyan kart; `cevap.kart_verisi_yok` ve `not.kart_atama` kaldırıldı.
- Kart düzeyi atama (`c651b06`):
  - Aşamalar konnektör → ped → parça; KART_PIN_YOK / KART_PED / KART_PARCA / KART_UART_KOPRU.
  - `kart_pin.tur` (sql/013, koşullu); etiketli pin, kart özeti, doğrulanmamış kart notu.
- `--rapor YOL` (`1704450`): `rapor.py`.
- Testler 280 → 299 (`test_10c.py`); çekirdek 19/19.
- Dondurma `2026-11-21_adim10c_dondurma.md` (öncesi `e9bab31`, sonrası aynı).
- Ölçüm (`8f5f6de`; kartsız):
  - v4 A 36/36: Y29 düzeldi (GPIO3 pin_tercihleri'nde, atama GPIO3).
  - v3 A 42/45 (X24, X34, X35): **ölçüt (≥ 43/45) karşılanmadı.** X24 WS2812 artık RMT_TX, kabul listesinde yok; atama aynı (GPIO0).
  - Atayıcı kararı 81 istekten yalnız Y29'da değişti. Son ham yanıtı değişen 13 istek (v4 5, v3 8), ara turu değişen 1 (X08).
  - Ara turda yakalanan: X08 BAGLAM_KONUSUZ, X15 DAYANAK_SINIRI, X27 DIGER_BAGLAM. Sessiz düşen konusuz cümle: X07, X11.
  - SPI ×N çıkmadı; RMT_TX yalnız X24.
- Sınav cümlesi 3 biçim (iz 40–42): ham yanıt dcf38030… (10a/10b ile aynı); kartsız örnek «--kart nanoESP32-C6-v0.2».
- Set dışı örnekler: nanoESP32-C6 v0.2 (NeoPixel → RMT_TX, IR alıcı → RMT_RX, 1. aşama); Super Mini (SPI ×2 tek hat, 12 çıkış, aşama 3, ped ve parça uyarıları). `--rapor` örneği `doc/raporlar/adim10c_ornek_rapor.md`.
- Rapor `doc/raporlar/adim10c_rapor.md`. KARARLAR T-67…T-70; L-1 ve L-5 çözüldü.

## Adım 11 — 2026-11-21 (kapsam uyarısı, v5 ölçümü)

- Adım 10c kabul. X24 hükmü 10c v3 sonucuna eklendi (`fa48856`): resmî 42/45, hükümle 45/45.
- KAPSANMAYAN_CUMLE (`69e5238`): cagrilar, CLI `[UYARI]`, kapsamlı rapor tablosu; `pinsecim.kapsam`; `test_11.py`. Eski 4 testte uyarı ayıklandı. Testler 299 → 310; çekirdek 19/19.
- Modelsiz uygulama: 10c v4 0/38 cümle, v3 3/61 (X01 ve X07 doğru, X32 yanlış alarm), v5 2/37 (Z25, Z26 yanlış alarm; emin_degilim). `doc/dogrulama/kapsam_uyarisi.md`.
- `pinsecim.tamolcum` (`2139ae7`), v5 seti (`894cf2d`, SHA e3f6aed3…), dondurma `2026-11-21_adim11_dondurma.md` (öncesi `e527cb6`, sonrası aynı).
- v5 ölçümü (`93d28ce`):
  - A 28/32 (Z06 konu, Z26 eksik, Z27, Z32 I2C ×1); karar 31/32 (Z27); beklenen uyarı ve mesajlar 29/32. Tekrar 3/3 birebir.
  - Mutlak ölçütler: uydurma pin 0 ✓; model cevap yazmıyor ✓; sessiz yanlış **2**: Z27 (Ethernet RMII → GPIO_OUT ×5 atandı) ve Z06 (akım sorusu pin_kisiti ile cevapsız).
  - Hakem itirazı: Z32 (I2C ×2 bu sistemde mumkun_degil; kabul ya da I2C ortak hat). Not: Z06 akım bilgisi datasheet Table 5-4 s. 65'te var, tabloda yok.
  - Sonuç belgesindeki süre satırı rapor üreticisi hatasıyla bozuk; doğru değerler DAI notunda. Ölçümden sonra kod değişmedi.
- Rapor `doc/raporlar/adim11_rapor.md`. KARARLAR T-71, T-72.


## Adım 11a — 2026-11-21 (desteklenmeyen özellikler, elektriksel not, kapsam, I2C ortak hat)

- Web AI hükmü v5 sonucuna (`3ff6718`): Z26 doğru, Z32 itirazı yerinde, v5 görülmüş set. İstem değişmedi.
- `desteklenmeyen_ozellik` + DESTEKLENMEYEN_OZELLIK hatası (`98c06f4`; sql/014, 6 özellik, yükleyici yokluk denetimi).
- `soru_sozcugu` + `cevap.elektriksel_yok` notu (`832c4e4`; sql/015, Bölüm 5 s. 64 denetli).
- KAPSANMAYAN_CUMLE emin_degilim'de yok (`fc2bca3`).
- I2C / LP_I2C ×N tek ortak hat, ayrı hat = ADET_ASIMI (`1534e6c`). D28 değişmeden geçiyor; `test_atayici_vaka_istekleri` istek düzeyi taşmaya göre güncellendi.
- tamolcum süre satırı düzeltildi; kapsam dökümüne DESTEKLENMEYEN_OZELLIK (`69d7b69`).
- Testler 310 → 345 (`test_11a.py`); çekirdek 19/19.
- Dondurma `2026-11-21_adim11a_dondurma.md` (öncesi `69d7b69`, sonrası `f6d1bac`, arada yalnız dondurma kaydı).
- Ölçüm (`4693f11`):
  - v4 36/36; v3 42/45 resmî, 45/45 hükümle. Kararlar 10c ile birebir. **v3 ölçütü (≥ 43/45 resmî) set dosyasına göre karşılanmadı** (X24 kabul listesinde yok).
  - v5 A 28/32 (hükümle 30/32), karar 32/32, tekrar 3/3.
  - Z27 desteklenmiyor (2. tur); Z06 `[NOT]`; Z32 atandi.
  - Uydurma pin 0. **Sessiz yanlış 1: Z20** (SPI ×1, iki cihaza tek CS). Girdi Adım 11 ile aynı, çıktı farklı (koşular arası belirlenimsizlik).
  - DESTEKLENMEYEN_OZELLIK yalnız Z27 (doğru); KAPSANMAYAN_CUMLE yalnız X01, X07 (doğru). I2C ×N hiçbir sette çıkmadı. `doc/dogrulama/kapsam_uyarisi_11a.md`.
- Rapor `doc/raporlar/adim11a_rapor.md`. KARARLAR T-73…T-76, L-6.

## Adım 12 — 2026-11-21 (SPI adet uyarısı, kapanış)

- Adım 11a kabul. Hükümler: v3 ölçütü hükümle karşılanmış sayılır (resmî 42/45 ve hükümlü 45/45 birlikte yazılır); Z20 kurala bağlı değil, oturumlar arası belirlenimsizlik (ana bulgu).
- SPI_ADET_IZI (`07663e1`): cagrilar, `sayi_disi_sozcuk` (sql/016, 80 satır), CLI `[UYARI]`, kapsamlı rapor uyarı tablosu, `pinsecim.kapsam` dökümü; `test_12.py`. Testler 345 → 365; çekirdek 19/19.
- Modelsiz uygulama (`ee5062d`, `doc/dogrulama/spi_adet_izi_12.md`): 11a v4 SPI'li 3 istek 0 uyarı, v3 7 / 0, v5 3 / 1 (Z20, doğru); 11 v5 3 / 0 (Z20 orada ×2).
  - İlk sürüm Z22'de («Üç SPI cihazım var: iki … ve bir …») yanlış alarm verdi (6 > 3). Toplam + döküm istisnası eklendi.
  - Bu istisnanın ilk biçimi «bir X ve bir Y»yi de toplam sayıyordu; en az üç sayı koşuluyla düzeltildi. İkisi de commit öncesi.
- Kapanış raporu `doc/SONUC_RAPORU.md` (`36e01fe`).
- DEVAM soğuk başlangıç notu olarak yeniden yazıldı. KARARLAR T-77. Rapor `doc/raporlar/adim12_rapor.md`.
- Etiket `pilot-v1`: proje kapanış commit'inde, asu_llmcore `41e2198`. Push yok.

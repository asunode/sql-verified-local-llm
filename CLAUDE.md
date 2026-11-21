Güncel durum için önce doc/DEVAM.md

# localllm_ass1 — DAI pin ataması pilotu

Bu proje, yerel modeli kesinlik gereken işlerde güvenilir çalıştırma yaklaşımını sınıyor. İlk pilot: ESP32-C6 pin seçimi. Yerel model pin ataması önerir, kod öneriyi doğrulanmış tablolarla denetler.

## İlkeler

1. Model veritabanına kendisi erişmez. Gereken bilgiyi uygulama seçer ve isteme koyar.
2. Kesin bilgi, kaynağıyla birlikte (belge, sürüm, sayfa) yapılı tablolarda durur ve tabloya girmeden önce doğrulanır.
3. Model öneriyi JSON şemasıyla verir (Ollama `format`). Şemada "bilgi yok / emin değilim" seçeneği vardır.
4. Kod öneriyi denetler. Hata varsa gerekçesiyle modele geri gönderir, en çok 2 tur. Yine geçmezse kullanıcıya bırakır.
5. Tek iş, tek çağrı. Ayarlar sabittir.
6. Hiçbir test setine göre ayar yapılmaz. Ölçüm, görülmemiş setle yapılır.
7. Ortak çekirdek ayrı bir kütüphanededir. Uygulamaya özgü olan yalnız tablolar, istem şablonu ve denetim kurallarıdır. Kurallar mümkün olduğunca veritabanında durur.

**Test seti kuralı:** Görülmemiş doğrulama seti ölçüm adımında verilir. Ondan önce hiçbir ayar (istem, şema, kural, eşik, model ayarı) onunla yapılmaz. `setler/gelistirme/` geliştirme içindir; doğrulama seti geldiğinde ayrı klasöre birebir kaydedilir ve ölçümden önce açılıp incelenmez.

## Klasörler

| Yol | İçerik |
|---|---|
| `<proje>` | Bu proje |
| `src/pinsecim/` | Uygulama paketi: tablolar için sorgular, istem şablonu, JSON şeması, denetim kuralları |
| `sql/` | Veritabanı göç dosyaları |
| `veri/dogrulanmis/` | Veritabanındaki doğrulanmış tabloların CSV dışa aktarımı (diff ile izlenir) |
| `doc/dogrulama/` | Fark raporları, spot kontrol listeleri |
| `veri/kaynak/` | Kaynak belgeler (PDF) ve `KAYNAKLAR.md` (sürüm, tarih, SHA-256, sayfa). Belgeler değiştirilmez |
| `setler/gelistirme/` | Geliştirme vakaları |
| `doc/` | `KARARLAR.md`, `WORKLOG.md`, `cevirmen_dersleri.md` |
| `doc/olcum/` | Ölçüm izleri (JSONL), ham çıktılar ve sonuç belgeleri |
| `testler/` | Uygulamanın pytest testleri |
| `../asu_llmcore` | Ortak çekirdek (ayrı git deposu). Alan bilgisi taşımaz: içinde ESP, pin ya da çeviriye dair satır olmaz |
| `cevirmen` (ayrı, yayımlanmamış bir proje) | **Salt okunur bilgi kaynağı.** Hiçbir dosyası değiştirilmez, kopyalanmaz, taşınmaz, çekirdeğe bağlanmaz |

## Altyapı

- Ollama yerelde, model `gemma4:12b-it-qat`, yalnız CPU (GPU yok). Ayarlar sabit: temperature 0, seed 42, think kapalı, num_ctx 8192. Çekirdek her asıl istekten önce önbellek sınırı isteği gönderir (bkz. `doc/cevirmen_dersleri.md` madde 2).
- PostgreSQL 18, 127.0.0.1:5432, veritabanı `donanim`. Uygulama okuma rolü `donanim_okur`, yükleme rolü `donanim`. Şifreler yalnız `~/.pgpass`'te; koda, belgeye ya da çıktıya yazılmaz. Kurulum: `kurulum/001_veritabani.sql`.
- Ortam: `.venv` (asu_llmcore `pip install -e ../asu_llmcore`, pinsecim `pip install -e .`).
- Veri yükleme: `.venv/bin/python -m pinsecim.yukle` (rol `donanim`, tek işlem, tekrar çalıştırılabilir; şema `sql/001_sema.sql`, dışa aktarım `veri/dogrulanmis/*.csv`). Doğrulama belgeleri `doc/dogrulama/`.
- Pin seçimi: `.venv/bin/python -m pinsecim "istek" --paket QFN32|QFN40 [--no-usb] [--no-uart0-konsol] [--jtag-pinleri] [--harici-flash-beslemesi] [--model-ata]` (varsayılan: model isteği anlar, kod atayıcı atar — K-6; `--model-ata` atamayı Çağrı B'ye yaptırır; Ollama gemma4:12b-it-qat, CPU; iz `doc/olcum/iz/`).
- Ölçüm: `.venv/bin/python -m pinsecim.olcum onbellek` ve `... olcum gelistirme --surum vN` (sonuç `doc/olcum/`; geçmiş `doc/olcum/gelistirme_gecmisi.md`); doğrulama setleri `... -m pinsecim.dogrulama dondurma|kos|rapor`; kapsamlı set (A + atayıcı) `... -m pinsecim.kapsamli kos|rapor`.
- Testler: `.venv/bin/python -m pytest` (proje; yerel PostgreSQL gerekir); çekirdekte `cd ../asu_llmcore && ../localllm_ass1/.venv/bin/python -m pytest` (gerçek Ollama için `-m ollama -s`).

## Roller

- **Sinan:** kararlar.
- **Web AI:** tasarım, istemler, test setleri.
- **DAI:** kod, ölçüm, kayıt.

## Çalışma kuralları

- Her adım `doc/WORKLOG.md`'ye işlenir; kararlar `doc/KARARLAR.md`'ye.
- Arayüz yok; pilot komut satırından çalışır.
- Git yalnız yerel; uzak depo ve push yok.

# Çevirmenden dersler

Kaynak: `cevirmen` (ayrı, yayımlanmamış bir proje) (PolyglotDesk), salt okunur incelendi 2026-11-20 (son commit `605b0ed`). Hiçbir dosyası değiştirilmedi, kopyalanmadı, çekirdeğe bağlanmadı. Satır numaraları bu commit'e göredir.

Her maddede: çevirmende nerede, ne öğrenildi, çekirdeğe (`asu_llmcore`) nasıl taşındı ya da neden taşınmadı.

## 1. Ollama çağrısı ve ayarlar

- **Nerede:** `cevirmen/ollama.py:12-14` (`BAGLAM = 8192`, `TOHUM = 42`), `:73-77` (`temperature 0`, `seed`, `num_ctx`, yalnız CPU'da `num_gpu 0`), `:86-100` (`/api/chat`, `think: False`, `keep_alive`, şema verilirse `format`). Varsayılan model ve CPU seçimi `cevirmen/ayarlar.py:7-13`. Uygulama QtNetwork ile akışlı istek atıyor (`ollama.py:8-9`, `:165-237`); ölçüm betikleri ise standart kütüphaneyle akışsız istek atıyor (`doc/olcum/tutarlilik.py:46-59`, `urllib.request`).
- **Ders:** Ayarlar kodda sabit, kullanıcıya açık değil. `think: False` gemma4'te şart; yoksa model yanıttan önce uzun süre düşünüyor (`ollama.py:91`). `num_ctx` değişirse Ollama modeli yeniden yüklüyor (`ollama.py:11`).
- **Çekirdekte:** `asu_llmcore/ollama.py` → `OllamaAyar` (`frozen=True` dataclass: değiştirilemez), aynı varsayılanlar (temperature 0, seed 42, num_ctx 8192, think False). HTTP için çevirmenin ölçüm betiklerindeki gibi **urllib** (ek bağımlılık yok). Akış yok: pilot komut satırında çalışıyor, ara çıktı gösterilmiyor; tek parça yanıt token sayılarını ve süre alanlarını doğrudan veriyor. QtNetwork taşınmadı (arayüz yok).

## 2. Prompt önbelleğinin yarattığı tutarsızlık ve çözüm (en önemli ders)

- **Nerede:** inceleme `doc/olcum/tutarlilik-inceleme.md` (ölçüm betiği `doc/olcum/tutarlilik.py`, ham veri `tutarlilik-ham.json`); çözüm `cevirmen/istem.py:57-61` (`sinir_istemi() = ORTAK + "\n\n#"`), `cevirmen/ollama.py:57-61` (`onbellek_sinirda` bayrağı), `:102-107` (`sinir()`: tek token, `num_predict 1`), `cevirmen/cevirici.py:154-166` (bayrak düşükse önce sınır isteği), `cevirmen/arayuz.py:277` (önden yükleme de sınır istemiyle).
- **Sorun:** Aynı metin, aynı ayarlarla (temperature 0, seed 42) bir önceki isteğe göre farklı çeviri verdi (4 metnin 1'inde; "I will still send" ↔ "nevertheless, I will send"). Neden: Ollama tek yuvalı istem önbelleğini bir önceki istekle ortak başlangıçtan sürdürüyor; gemma'nın kayan pencere dikkati yüzünden yalnız kayıtlı ara noktalardan (ölçümde 597, 598, 610, 614, 615, 621. token) devam edebiliyor. Devam noktası değişince istemin kalanı farklı parti bölünmesiyle işleniyor, kayan nokta sonuçları çok az değişiyor ve olasılığı çok yakın iki token arasında seçim değişebiliyor. Seed bunu gidermiyor; Ollama'da önbelleği kapatan ayar yok.
- **Çözüm:** Asıl istekten hemen önce "sınır isteği": sistem istemi = istemin sabit başlangıcı + `"\n\n#"`, kullanıcı mesajı ".", tek token. Böylece asıl istek önbelleği her koşulda aynı noktadan sürdürüyor. Ölçümde 16/16 koşu aynı çıktı; maliyet ~2 s/istek (çoğu Ollama'nın her istekteki ~1.2 s sabit yükü). Çevirmen seçenek C'yi uyguladı: sınır yalnız önbelleği başka türden bir istek değiştirdiyse gönderiliyor (hız için).
- **Çekirdekte:** `OllamaIstemcisi.uret()` her asıl istekten önce sınır isteği gönderiyor (`OllamaAyar.onbellek_siniri=True`, varsayılan). Çevirmenin **seçenek B**'si (her istekte sınır) seçildi, C değil: denetle-geri gönder döngüsünde her turun mesaj geçmişi farklı, uygulama farklı işler arasında geçiş yapabilir; "hangi istek önbelleği bozdu" takibi alana ve çağrı sırasına bağlı kalırdı. Pilotta kesinlik hızdan önemli. Sabit başlangıç uygulamadan `sabit_onek` olarak gelebilir (ilk sistem mesajının başı olmak zorunda, değilse `ValueError`); verilmezse ilk sistem mesajının tamamı kullanılıyor, bu da aynı sistem istemli her isteği aynı noktaya getiriyor. Gerçek Ollama testi: aynı istek iki kez ve araya farklı bir istek girdikten sonra birebir aynı yanıt (`tests/test_ollama_entegrasyon.py`).

## 3. JSON karar dönen gözden geçirme turu

- **Nerede:** şema `cevirmen/istem.py:108-128` (`DENETIM_SEMASI`: `has_errors`, `errors[{type, draft_text, corrected_text, reason}]`, `bold`); istek `cevirmen/detayli.py:216-221` (`bicim=DENETIM_SEMASI` → `format`); kararın çözülmesi `cevirmen/denetim.py:64-71` (`karari_coz`: ayrıştırılamazsa "geçersiz yanıt"); uygulanması `denetim.py:120-144`.
- **Ders:** Model metni yeniden yazmıyor; yalnız yapılı bir karar veriyor ("hata yok" ya da düzeltme listesi). Her düzeltme taslaktan birebir alınmış bir parça; kararı kod uyguluyor. Yanıt okunamazsa taslak olduğu gibi kalıyor. Gözden geçirme tek tur: hata bulunursa modele geri gönderilmiyor, kod uyguluyor ya da reddediyor. Şemada "bilgi yok" seçeneği yok; `format` şemayı zorlasa da kod yine ayrıştırma hatasını ele alıyor.
- **Çekirdekte:** `asu_llmcore/dongu.py` → `calistir()`. Farklar: (a) yanıt `jsonschema` (Draft 2020-12) ile ayrıca doğrulanıyor, uymayan yanıt `JSON_GECERSIZ` sayılıp gerekçesiyle geri gönderiliyor; (b) denetleyici ihlal listesi (`Ihlal(kod, mesaj, alan)`) döndürüyor ve ihlaller modele geri gönderiliyor, en çok `en_cok_tur` (varsayılan 2) çağrı; (c) "bilgi yok" uygulamanın `bilgi_yok_mu` işleviyle tanınıyor, yeniden denenmiyor. Çevirmenin hata türleri ve `draft_text/corrected_text` yapısı alana özgü olduğu için taşınmadı.

## 4. Kod koruması (zararlı değişikliği geri alma)

- **Nerede:** `cevirmen/denetim.py:80-117` (`guvenlik`: biçim düzeltmesi kelime değiştiriyorsa, unvan değişikliği, yan yana tekrar, fazladan olumsuzluk, İngilizceye Türkçe ek, çevrilmemiş kaynak kelime, karşılığı olmayan yeni kelime → geri al), `:120-144` (`uygula`: her düzeltme ayrı ayrı denenir; `uygulanan`, `geri_alinan`, `uygulanmayan` listeleri neden ile tutulur), veritabanı destekli karşılık denetimi `cevirmen/detayli.py:223-240`.
- **Ders:** Modelin önerisi doğrudan kabul edilmiyor; kod her öneriyi kurallarla denetliyor ve reddedilenleri **nedeniyle** kaydediyor. Kural kaynağı mümkünse veritabanı (`bilgi.siklik`, `karsilik_var_mi`). Veritabanına ulaşılamazsa o denetim atlanıyor (`detayli.py:234-235`), ama bu durum kayda geçmiyor.
- **Çekirdekte:** Genel mekanizma taşındı, kuralların kendisi taşınmadı. Kurallar uygulamanın `denetleyici` işlevinde ve mümkün olduğunca veritabanında duracak (ilke 7). Çekirdek, her turun ihlallerini izde nedenleriyle saklıyor. Bir fark: çevirmen reddedilen düzeltmeyi sessizce geri alıp taslağı koruyor; pilotta reddedilen öneri gerekçesiyle modele dönüyor, geçmezse kullanıcıya kalıyor (ilke 4). Ders: denetimin bir kısmı atlanırsa (veritabanı yok vb.) bu, sonuçta görünür olmalı. Pilotta veritabanı hatası döngüyü durdurur (`PgHatasi`), sessizce atlanmaz.

## 5. PostgreSQL okuma ve okuma rolüyle bağlanma

- **Nerede:** bağlantı `cevirmen/bilgi.py:30-48` (`make_conninfo`: `connect_timeout=3`, `application_name`, `statement_timeout=10000`; şifre kodda yok, libpq `~/.pgpass`'ten okuyor), `:117-130` (`baglan`, anlaşılır hata iletisi); okuma rolü `veritabani/okur_rol.sh:75-76` (`ALTER ROLE … SET default_transaction_read_only = on`, yalnız bir veritabanına `CONNECT`); yetkiler yükleme sırasında `veritabani/yukle.py:506-509` (`GRANT USAGE/SELECT/EXECUTE`). Sürücü psycopg 3 (`requirements.txt`).
- **Ders:** Uygulama yükleme rolünü değil, ayrı bir okuma rolünü kullanıyor; salt okunurluk rol düzeyinde. Sorgular parametreli. Bilgi istem bloğuna kaynağıyla birlikte giriyor (`Kayit.kaynak`, `lisans`; `bilgi.py:92-100`).
- **Çekirdekte:** `asu_llmcore/pg.py` → `PgOkuyucu(rol, veritabani)`; psycopg 3, aynı zaman aşımları. Ek güvence: oturum `-c default_transaction_read_only=on` ile açılıyor ve psycopg `read_only=True`, yani rol ayarına bağımlı değil. `PGPASSWORD` tanımlıysa bağlanmıyor (şifrenin tek kaynağı `.pgpass`). Sonuç `dict_row` ile sözlük listesi. `donanim_okur` rolüne `default_transaction_read_only` rol ayarı verilmedi (Adım 0); salt okunurluğu oturum sağlıyor, yazma yasağını rol yetkileri sağlıyor (testte ikisi ayrı ayrı gösterildi).

## 6. Ölçüm kayıtlarının tutuluşu

- **Nerede:** `doc/olcum/bench_detayli_v3.py:68-102` (her test için ham çıktı, süreler, karar, uygulanan/geri alınan düzeltmeler, modele giden kayıtlar; her testten sonra tüm JSON yeniden yazılıyor), `doc/olcum/tutarlilik.py:46-59` (istek başına süre, `prompt_eval_count`, `eval_count`, önbellekten gelen token, Ollama günlüğünden `cached n_tokens`); sonuç belgeleri `*-sonuc.md` "puan/yorum yok" kuralıyla (`doc/WORKLOG.md:119`). Test seti disiplini: doğrulama setleri birebir kaydediliyor, "hiçbir ayarı bu metinlere göre yapma" (`doc/design.md:115`, `:138`); istem örnekleri test setlerindeki cümleleri içermiyor (`cevirmen/istem.py:7`).
- **Ders:** Ham veri ile yorum ayrı. Her koşunun ayarları kaydın başında. Model digest'i kaydedilmiyor: model güncellenirse eski ölçümlerle karşılaştırma belirsizleşir. Kayıt tek bir büyük JSON; yarıda kesilen koşuda her test sonrası tam yeniden yazma gerekiyor.
- **Çekirdekte:** `asu_llmcore/iz.py` → `IzYazici` (JSONL, çalıştırma başına bir satır, yalnız ekleme; yarıda kesilse de önceki satırlar sağlam) ve `kayit(sonuc, ayar, **ek)`: ayarların tamamı, durum, kaçıncı turda geçtiği ve her turun istemi, ham yanıtı, ayrıştırılmış JSON'u, ihlalleri, süresi, sınır süresi, token sayıları, **model digest**'i. Ölçüm raporu (puan, yorum) çekirdekte değil, uygulamanın ölçüm adımında. Test seti disiplini CLAUDE.md'ye kural olarak yazıldı.

## Taşınmayanlar (özet)

| Çevirmende | Neden taşınmadı |
|---|---|
| QtNetwork akışlı istemci, sinyaller (`ollama.py:52-237`) | Arayüz yok; pilot komut satırında, akışsız |
| Seçenek C (sınırı yalnız gerektiğinde gönderme) | Her istekte sınır daha kesin; döngüde turların geçmişi farklı (madde 2) |
| Denetim kuralları, hata türleri, kalın yazı düzeltmesi (`denetim.py`, `bicim.py`) | Alana özgü; pilotun kuralları kendi denetleyicisinde ve veritabanında |
| Bilgi arama mantığı (`bilgi.py:133+`) | Alana özgü; pilotta bilgiyi uygulama seçip isteme koyacak (ilke 1) |
| Ayar dosyası (`ayarlar.py`) | İlke 5: ayarlar sabit, kodda |

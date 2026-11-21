# Devam notu — 2026-11-21 (pilot sonu)

Soğuk başlangıç: önce `doc/SONUC_RAPORU.md` (pilotun özeti: nasıl çalışıyor, ölçümler, dersler, sınırlar), sonra bu dosya ve `CLAUDE.md`. Ayrıntı `doc/WORKLOG.md`, kararlar `doc/KARARLAR.md`.

## Durum

Pilot (Adım 0–12) kapandı; iki depoda yerel etiket `pilot-v1`. Uzak depo yok; GitHub kararı Sinan'ın.

- Akış: Çağrı A (model isteği anlar) → kod denetimi ve düzeltme turu → kod atayıcı ve cevaplayıcı (veritabanından, kaynaklı) → çıktı (`--rapor` ile dosya). K-6, K-7, K-8.
- İstem dosyası Adım 10b'den beri aynı (T-65); modele giden metin Adım 10c'de iki arayüz satırıyla (RMT_TX, RMT_RX) değişti. İstem dosyaları: atama_sistem.txt `f09040e1f110`, ihtiyac_sistem.txt `3ff741e27c2e`. Son dondurma kaydı `doc/olcum/2026-11-21_adim11a_dondurma.md`.
- Son model ölçümü Adım 11a: v4 36/36; v3 42/45 resmî, 45/45 hükümle; v5 A 28/32 (30/32 hükümle), karar 32/32; uydurma pin 0; sessiz yanlış 1 (Z20).
- Adım 12'de SPI_ADET_IZI eklendi; yeni kodla model koşusu yapılmadı.
- Testler: proje 365, çekirdek 19 (modelsiz). Çekirdek `asu_llmcore` `41e2198` (pilot boyunca değişmedi).
- Bütün setler görülmüş: geliştirme, v1–v5. Yeni ölçüm için yeni görülmemiş set gerekir (CLAUDE.md test seti kuralı).

| Adım | Sonuç | Commit |
|---|---|---|
| 0 | PostgreSQL: `donanim` veritabanı, `donanim` / `donanim_okur` rolleri, `.pgpass`, yerel altyapı kaydı (yayımlanmadı) | — (git dışı) |
| 1 | Çekirdek kütüphane, proje iskeleti, çevirmen dersleri, datasheet v1.6 kaynağı | proje `030bc7b`, çekirdek `46ef2a8` |
| 2 | Datasheet pin olguları DB'de; A/B çıkarma 0 fark, görsel denetim, yükleyici | proje `d578611` |
| 3 | Kurallar DB'de, denetleyici (35/35 vaka), modelsiz atayıcı, yorum katmanı; çekirdeğe `Ihlal.seviye` | proje `94c71d4`, çekirdek `41e2198` |
| 4 | Model çağrıları A (ihtiyaç) ve B (atama), CLI, önbellek ölçümü; geliştirme seti v0: A 20/20, B 18/18 1. turda, atayıcıyla 18/18 aynı | proje `289bd87` (ara kayıt `87e6f38`) |
| 5 | Görülmemiş set v1 (30 istek) ölçüldü: A 22/30; B model 23 ilk turda + 2 üçüncü turda; mümkün/imkânsız hakemle 23/25 (tablosuz 22/25); tekrar 10/10 ve 9/9 birebir. `doc/olcum/2026-11-20_dogrulama_sonuc.md` | proje `1d897e8` |
| 6 | Çağrı A: `adet` + SAYI_UYUSMAZ, `baglam_ifadeleri` + BAGLAM_CELISKI uyarısı (T-27), `tamam` + boş liste = pin gerekmiyor, arayüz tanımları; sözlük tabloları DB'de. Gerileme r0→r2 (2/2 revizyon): geliştirme A 19/20, v1 (görülmüş) A 30/30. v2 dondurma `doc/olcum/2026-11-20_v2_dondurma.md` | proje: Adım 6 commit'leri (WORKLOG) |
| 7 | L-4 tam kat kuralı (T-39), "çift yönlü" istisnası (T-40), CLI set/SHA seçenekleri; v2 dondurma `doc/olcum/2026-11-21_v2_dondurma.md` (öncesi = sonrası). Görülmemiş v2 (30): A 30/30; B 23/1/0 + 2 KULLANICIYA (W13, W19); karar hakemle 24/26, atayıcı 26/26; tekrar 10/10 ve 7/7. `doc/olcum/2026-11-21_v2_sonuc.md` | proje `be8614c`, `84edee4`, `9e8613e` + v2 sonuç commit'i |
| 8 | K-6 mimari geçiş (A → atayıcı), Türkçe neden, yazılım hatası denetimi, `pinsecim.kapsamli`. Kapsamlı set v3 (45): A 43/45; atayıcı kararı hakemle 41/42; uçtan uca 43/45 (Adım 8b puanlama düzeltmesiyle; önce 42/45); çift 4/4; tekrar A 13/15 ham aynı; yazılım hatası 0. `doc/olcum/2026-11-21_v3_sonuc.md`, dondurma `2026-11-21_v3_dondurma.md` | proje `70330c4`, `5428b10`, `a2b01e3`; 8b düzeltme commit'i (WORKLOG) |
| 9 | K-7 pin tercihleri: Çağrı A'da üç pin listesi + bahis denetimleri (desenler DB'de), esnek dayanak, matris tanımı, Türkçe kural mesajları, atayıcıda tercih kilidi / tercih_uygulanamadi / alternatif. Test seti v4 (36): A 36/36; atayıcı 27 atandı / 7 tercih_uygulanamadı / 1 mümkün değil / 1 pin gerekmiyor; hakem–beklenen_sonuc 35/35 (Adım 9b düzeltmesiyle; önce 34/35, Y13); atayıcı 26 / 8 / 1 / 1; tekrar 12/12. `doc/olcum/2026-11-21_v4_sonuc.md`, dondurma `2026-11-21_v4_dondurma.md` | proje `8e393e9`, `acdd964`, `f2d5e1a`; 9b `88450d3`, `dcda8f3` + sonuç commit'i |
| 10 | K-8 soru ayrımı: şemada `sorular` + `eksik`, `soru_konusu` / `durum_mesaji` tabloları (sql/007), kod cevaplayıcı (kaynaklı), emin_degilim denetimi, BAGLAM_KONUSUZ. Kart kaynakları araştırıldı (yüklenmedi). Gerileme: v4 A 34/36 (Y33/Y34 bileşik sayı, **ölçüt karşılanmadı**), v3 43/45. Sınav cümlesi: sorular ayrıldı, bağlam boş. `doc/raporlar/adim10_rapor.md` | proje `2c62781`, `62f1a2a`, `7867d5e`, `b9686dd`, `f83c622` + sonuç/rapor commit'leri |
| 10a | Bileşik sayı kuralı (basamak, SAYI_UYUSMAZ tam sayıyla, SAYI_YARIM), DAYANAK_SINIRI, `diger_ifadeler` + DIGER_IHTIYAC_IZI, `arayuz_es_adi` (sql/008), v3 hükmü, WROOM-1 karşılaştırması. v4 A 35/36 (Y33/Y34 düzeldi; Y29 tercih kaydı), v3 43/45 (X34/X35). `doc/raporlar/adim10a_rapor.md` | proje `43c932b`, `38301c8`, `97055e6` + sonuç/rapor commit'leri |
| 10b | Spot kontrol 8/8 ✓. Denetim: DIGER_PIN_TERCIH_IZI, DIGER_BAGLAM, "bir" istisnası, CAN harfe duyarlı, atayıcı toplamlı neden. Kart verisi (sql/010–011; K2, W1, S2, E1): nanoESP32-C6 v1.0 / v0.2, Super Mini; --kart, kart soruları. v4 35/36 (Y29 uyarılı), v3 43/45, kararlar 10a ile aynı. `doc/raporlar/adim10b_rapor.md` | proje `22ec998`, `a57eefc`, `1b5de4b`, `12279a1`, `249043d` + sonuç/rapor commit'leri |
| 10c | Kart düzeyi atama (konnektör → ped → parça, KART_* kuralları, sql/013), SPI ×N tek hat (SPI2_CS 6, sql/012), RMT_TX/RMT_RX, `--rapor`, SAYI_YARIM düzeltmesi. v4 36/36 (Y29 düzeldi), v3 42/45 (X24 RMT_TX kabulde yok; **ölçüt karşılanmadı**, Web AI hükmü bekliyor). `doc/raporlar/adim10c_rapor.md` | proje `1abac04`, `c651b06`, `1704450`, `e9bab31`, `8f5f6de` + rapor commit'i |
| 11 | KAPSANMAYAN_CUMLE uyarısı (T-71), `pinsecim.tamolcum`, v5 seti (32). v5: A 28/32, karar 31/32, tekrar 3/3; uydurma pin 0, model cevap yazmıyor; **sessiz yanlış 2** (Z27 Ethernet RMII atandı, Z06). Hakem itirazı Z32. `doc/raporlar/adim11_rapor.md` | proje `fa48856`, `69e5238`, `6be9b71`, `2139ae7`, `894cf2d`, `e527cb6`, `93d28ce` + rapor commit'i |
| 11a | desteklenmeyen_ozellik + DESTEKLENMEYEN_OZELLIK (T-73), elektriksel not (T-74), KAPSANMAYAN_CUMLE emin_degilim'de yok (T-75), I2C ×N ortak hat (T-76, L-6). v4 36/36, v3 42/45 resmî / 45/45 hükümle (**resmî ölçüt karşılanmadı**), v5 A 28/32, karar 32/32; Z27 desteklenmiyor, Z06 not; **sessiz yanlış 1 (Z20, koşular arası fark)**. `doc/raporlar/adim11a_rapor.md` | proje `3ff6718`, `98c06f4`, `832c4e4`, `fc2bca3`, `1534e6c`, `69d7b69`, `f6d1bac`, `4693f11` + rapor commit'i |
| 12 | SPI_ADET_IZI uyarısı (T-77, sql/016; modelsiz uygulamada yalnız 11a Z20), kapanış raporu `doc/SONUC_RAPORU.md`, etiket `pilot-v1` (iki depo). `doc/raporlar/adim12_rapor.md` | proje `07663e1`, `ee5062d`, `36e01fe` + kapanış commit'i |

## Nasıl çalıştırılır

```bash
cd <proje> && source .venv/bin/activate
python -m pinsecim.yukle                  # doğrulanmış tabloları yükler (rol donanim; tekrar çalıştırılabilir)
python -m pytest -q                       # proje testleri, modelsiz (PostgreSQL gerekir; test_yukleyici DB'yi yeniden yükler)
cd ../asu_llmcore && python -m pytest -m ollama -s   # çekirdeğin modelli testleri (Ollama gerekir); modelsizler: python -m pytest
python -m pinsecim "İki buton ve bir I2C ekran bağlayacağım." --paket QFN32
python -m pinsecim "..." --kart SuperMini --rapor cikti.md
python -m pinsecim "..." --paket QFN40 --no-usb --jtag-pinleri --model-ata     # atamayı model yapar (Çağrı B)
```

Ölçüm araçları:
- `pinsecim.kapsamli kos|rapor` (v3/v4 biçimi)
- `pinsecim.tamolcum kos|rapor` (v5 biçimi: soru, kart, bayrak)
- `pinsecim.dogrulama dondurma --asama once|sonra`
- `pinsecim.kapsam HAM…` (KAPSANMAYAN_CUMLE, SPI_ADET_IZI ve DESTEKLENMEYEN_OZELLIK modelsiz dökümü)

Komut ayrıntıları önceki adımların WORKLOG kayıtlarında. Model ölçümü sürerken `pytest` çalıştırma (yükleyici testi DB'yi yeniden yazar).

## Sonraki tur: nereden başlanır

1. Sinan'ın kararları:
   - GitHub (uzak depo) açılsın mı;
   - sonraki tur kapsamı (`doc/SONUC_RAPORU.md` bölüm 7 "Sonraki tur").
2. Elle doğrulamalar (Sinan, `doc/raporlar/adim10_rapor.md` "Sinan'ın elindeki kartla doğrulayabileceği satırlar"):
   - Super Mini 7 madde;
   - nanoESP32-C6 7 madde (v1.0 mı, "v0.2" çip revizyonu mu, modül N16 mı);
   - doğrulanan satırlar `elle_dogrulandi`'ye.
3. Geniş bağımsız sınav (Sinan, kartlarla): `doc/dogrulama/bagimsiz_sinav.md`'ye eklenir.
4. Teknik ilk işler:
   - SPI_ADET_IZI ile v3/v4/v5 gerileme koşusu;
   - oturumlar arası belirlenimsizlik için çekirdek izine `prompt_eval_duration` ve aynı girdinin iki Ollama oturumunda karşılaştırılması.

## Açık işler

Güncel liste: `doc/SONUC_RAPORU.md` bölüm 7 (bilinen sınırlar 1–17, sonraki tur 1–10). Önemli olanlar:
- oturumlar arası belirlenimsizlik (Z20; Adım 8 X03/X11);
- L-6 ayrı I2C hattı;
- Çağrı B ortak hat bilmiyor;
- RMT kanal yönleri (TRM);
- iki kart doğrulanmadı;
- kodda duran iletiler.

Kapananların geçmişi WORKLOG'da.

## Dikkat notları

- Datasheet Table 2-11 QFN32 pin 9 SPI2 hücresi belgede "GPIO1 (P2)" yazıyor; DB'de belirsiz işaretli, yorum katmanı (Web AI) GPIO3 okuyor. `doc/dogrulama/2026-11-20_fark_raporu.md`, KARARLAR T-13.
- Önbellek sınırı açık: gemma'da önbellek önceki isteğe göre yanıtı değiştirebiliyor (`doc/cevirmen_dersleri.md` madde 2). Ölçüm: `doc/olcum/2026-11-20_onbellek.md` (sınır kapalıyken B'de 1/8 ham fark).
- PostgreSQL sunucu günlüğündeki `donanim_okur@donanim` ERROR satırları kasıtlı (yetki ret testleri); yerel durum betiği bunları hata sayar (altyapı defteri, yayımlanmadı).
- Şifreler yalnız `~/.pgpass`'te. `cevirmen` (ayrı, yayımlanmamış bir proje) salt okunur. Push yok.

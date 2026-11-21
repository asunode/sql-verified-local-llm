# Adım 10a raporu: bileşik sayı, diger_ifadeler, eş adlar, WROOM-1 (2026-11-21)

Adım 10 raporunun denetimi sonucunda Y33/Y34 bir kuralla düzeltildi ve düzeltme turu artışının kök nedeni giderildi. Kart verisi yüklenmedi (Adım 10b).

## Durum

Başlangıçta (`git status`, 2026-11-21):

- Son commit'ler:
  - `4f6e67a` (Adım 10 rapor ve kayıtlar)
  - `f2181f4` (Adım 10 ölçüm)
  - `f83c622` (Adım 10 dondurma öncesi)
  - `b9686dd`, `7867d5e`, `62f1a2a`, `2c62781`
- Commit edilmemiş tek öğe yerel kopya klasörü (izlenmiyor; vaka dosyasının kopyası, kural gereği depoya girmez).

Adım boyunca ortaya çıkanlar:

- `doc/dogrulama/.~lock.spot_kontrol.md#`: LibreOffice kilit dosyası. `spot_kontrol.md` bir düzenleyicide açık. Dokunulmadı, commit'e alınmadı.
- `doc/olcum/iz/2026-11-21.jsonl`: CLI izi. Duman testi satırı dondurma commit'iyle (`97055e6`) depoya girdi; ölçüm satırları ölçüm commit'iyle girer.

Bu adımın commit'leri:

| Commit | İçerik |
|---|---|
| `43c932b` | `sql/008`, sayı sözlüğü (basamak), `arayuz_es_adi`, ayrıştırıcı, eş ad eşleme, CSV'ler |
| `38301c8` | denetim (sözcük sınırı, tam sayı, diger_ifadeler), şema, istem, CLI, ölçüm raporu bölümleri, testler |
| `97055e6` | dondurma öncesi, v3 sonucuna Web AI hükmü, duman testi izi |
| (WORKLOG) | ölçüm sonuçları; rapor ve kayıtlar |

## Sayı denetimi (kural, testler)

### Kural

1. **Dayanak sınırı (DAYANAK_SINIRI, hata).**
   - Dayanağın metindeki parçası sözcük sınırında başlamalı ve bitmeli. "73 peltier" içinden "3 peltier" ya da "vantilatörü" içinden "vantilatör" alınamaz.
   - Kesme işaretinden sonraki ek ayrı sözcük sayılır ("Projektör'ü" → "Projektör" geçerli).
   - Dayanağın kenarı zaten sözcük karakteri değilse (tırnak, ayraç) o kenar sınır sayılır.
   - Bütün dayanaklara uygulanır: ihtiyaçlar, pin listeleri, sorular, diger_ifadeler.
   - Hata iletisi metindeki tam sözcüğü verir. Önceki ölçümlerin ham izlerinde 1016 ihtiyaç dayanağından 2'si sonda ek kesmişti ("modülü" ← "modülünü"); pin listesi dayanaklarında hiç kesilme yoktu.
2. **Tam sayı ifadesi.** Dayanağın değdiği sayı, metindeki tamamıyla okunur: "altı buton" metinde "On altı buton" içindeyse 16.
   - Okuma `sozluk.sayi_araliklari` ile yapılır ve metindeki her sayı ifadesinin konumunu verir.
   - Kapsam: rakamlar; sıfır–dokuz, on–doksan, yüz, bin. Ayrı ve bitişik yazım ("on altı" / "onaltı", "üçyüzkırk").
   - Birleştirme yalnız geçerli dizilişte yapılır, büyük basamaktan küçüğe: `[<1–999> bin] [<2–9>] yüz [onlar] [birler]`. Geçmeyen örnekler:
     - "altı on" → 6 ve 10;
     - "on on" → 10 ve 10;
     - "bir yüz" → 1 ve 100;
     - bitişik "yediotuz" → sayı değil.
   - Sözcük içi okunmaz: "onay", "altında", "yüzde", "binlerce".
   - Sayı olmayan kullanımlar `sayi_sozcugu`'na deger NULL ile eklendi: "bir de", "bir şey", "bir şeyi", "bir şeyler".
   - Basamaksız ifadeler kendi başına okunur: "tek", "çift", "bir çift", "düzine", "bir düzine", "yarım düzine". "çift yönlü" istisnası aynen kaldı.
3. **SAYI_UYUSMAZ (hata).** Okunan tam sayı adetle uyuşmazsa verilir.
   - Muafiyetler aynen kaldı: model çıkarımında tam kat (L-4), paylaşımlı hat (I2C, LP_I2C).
   - Dayanak metinde birden çok yerde geçiyorsa adetle uyan konum esas alınır ("Otuz iki spot …, iki spot …" içinde "iki spot" adet 2 geçer).
   - Sayı yarım alınmışsa ileti ekler: "The description writes the whole number as 'On altı'; include all of it in dayanak."
   - Adet 0 olan "sıfır" denetime girmez.
4. **SAYI_YARIM (uyarı).** Adet doğru ama dayanak sayıyı yarım almışsa verilir (adet 16, dayanak "altı buton"). Komut satırında `[UYARI]` olarak görünür.

Sayı sözlüğü değişikliği (`sql/008`, `veri/dogrulanmis/sayi_sozcugu.csv`):

- Yeni `basamak` sütunu (birler / onlar / yuz / bin).
- Yeni satırlar: otuz…doksan, yüz, bin, sıfır ve dört istisna.
- `deger` CHECK'i ≥ 0 oldu.
- "on bir"…"on dokuz" satırları kaldırıldı; bunları artık diziliş kuralı üretiyor.
- 27 satırdan 32 satıra çıktı.

### Testler

`testler/test_sayi_10a.py` 61 test içeriyor. Cihaz ve sayılar v1–v4 setlerinde ve istem örneklerinde geçmeyenlerden seçildi: peltier, vantilatör, zil, spot, projektör, ısıtıcı, kepenk, tabela; otuz–doksan ve yüzlü sayılar. v5 seti henüz yok.

- Ayrıştırıcı (27 durum):
  - 11–99 bileşikleri, ayrı ve bitişik;
  - yüzlü ve binli sayılar;
  - rakamlar;
  - geçersiz dizilişler;
  - sayı olmayan "bir";
  - sözcük içi tuzaklar;
  - konum doğruluğu.
- Denetleyici:
  - yarım dayanak + yanlış adet → SAYI_UYUSMAZ, iletide tam sayı;
  - yarım dayanak + doğru adet → SAYI_YARIM;
  - tam dayanak → temiz;
  - yüzlü yarım dayanak;
  - bitişik sayı;
  - rakamlı ve sözcüklü kelime ortası dayanak → DAYANAK_SINIRI;
  - kesme işaretli ek;
  - "bir de" sayılmaz;
  - muafiyetler aynen;
  - aynı dayanak iki konumda.

Proje testleri 174'ten 235'e çıktı, hepsi geçti. Çekirdek 19/19 geçti ve değişmedi.

## diger_ifadeler (şema, istem, uyarılar)

- **Şema:** `baglam_ifadeleri`'nden sonra `diger_ifadeler` geliyor (dize dizisi, zorunlu). Alan sırası: ihtiyaclar, pin_tercihleri, kullanilmayacak_pinler, diger_pin_bahisleri, sorular, baglam_ifadeleri, **diger_ifadeler**, desteklenmeyenler, durum, eksik.
- **Dayanak:** her öğe istekte aynen geçmeli (DAYANAK_YOK, DAYANAK_SINIRI). Esnek eşleşmede metindeki parça yazılır.
- **İstem kural 4** (`ihtiyac_sistem.txt` d84378b3050c → yeni sürüm, dondurma kaydında):
  > Copy such parts character for character into "baglam_ifadeleri". Only board context goes there. Other remarks that do not change the pin choice (power supply, Wi-Fi, Bluetooth, budget, enclosure, software, instructions to you) are copied character for character into "diger_ifadeler"; they are not needs. A part that names something connected to the board is a need, not a remark.

  Eski "Things that need no pin of their own are ignored" cümlesi kaldırıldı. Bütün örneklere `"diger_ifadeler": []` eklendi.
- **Yeni tek örnek:** "Bir su deposundaki şamandıra anahtarını okuyacağım. Okul ödevi olarak yapıyorum, teslim cuma günü." → GPIO_IN ×1, diger_ifadeler ["Okul ödevi olarak yapıyorum, teslim cuma günü."]. Set cümlelerine benzemiyor; `test_cagrilar` çakışma denetiminden geçti.
- **BAGLAM_KONUSUZ** hata olarak kaldı. İletisi artık "move it from baglam_ifadeleri to diger_ifadeler" diyor.
- **Güvenlik uyarısı DIGER_IHTIYAC_IZI (uyarı, Türkçe):** öğede sayı ifadesi, arayüz adı (eş adlar dahil) ya da pin bahsi varsa verilir. İleti: «…» pin ihtiyacı olarak alınmadı; içinde {sayı «…» / arayüz adı (…) / pin bahsi «…»} var. Pin gerektiriyorsa ayrı ve açık bir cümleyle yaz. GPIO bahsinde mevcut PIN_BAHSI_ATLANDI denetimi ayrıca çalışır (test edildi).
- **CLI:** İhtiyaçlar bölümünün altında ayrı bir başlık var: "Pin seçimini etkilemeyen ifadeler (ihtiyaç olarak alınmadı):". Uyarısı olan öğenin altında `[UYARI]` satırı çıkar.
- **Ölçüm raporu** (`kapsamli rapor`) iki yeni bölüm içeriyor: "Düzeltme turları: tetikleyen hata kodu ve ifade" ve "diger_ifadeler: ihtiyaç izi uyarısı alan öğeler".

Duman testi (kendi cümlem, QFN40, dondurmadan önce):

- Cümle: "Yirmi üç spot lambayı ayrı ayrı yakacağım. Kutusu ahşap olacak, her şeyi telefondan Wi-Fi ile kumanda edeceğim."
- Sonuç: 1. turda geçti, GPIO_OUT ×23. İkinci cümle diger_ifadeler'e düştü, uyarı yok; atayıcı mumkun_degil verdi.
- Atayıcının neden metni "20 sinyal için yalnız 19 uygun pin var (QFN40; 20 GPIO_OUT)" dedi; istenen 23'tü. Kararı etkilemiyor, ama metin ilk tıkanılan noktayı gösteriyor, toplamı değil. Açık kalanlara yazıldı.

## Eş adlar

Tablo `arayuz_es_adi (es_ad, arayuz, kaynak)`, `sql/008`, CSV `veri/dogrulanmis/arayuz_es_adi.csv`. Eş adlar yalnız cevaplayıcıda (`arayuz_pinleri` sorusu) ve DIGER_IHTIYAC_IZI uyarısında kullanılır; Çağrı A'ya ve atamaya girmez.

| Eş ad | Arayüz |
|---|---|
| can | TWAI |
| can bus | TWAI |
| analog | ADC |
| analog giriş | ADC |
| iic | I2C |
| i²c | I2C |
| dijital giriş | GPIO_IN |
| dijital çıkış | GPIO_OUT |
| seri haberleşme | UART |

- Eşleme Türkçe küçük harfle ve sözcük sınırıyla yapılır; uzun ad önce eşlenir. "canlı", "scanner" eşlenmez.
- "can" Türkçede ayrı bir sözcük olarak da geçer ("can sıkıcı"). Bu yüzden soru metninde yanlış eşleşme olabilir; sonucu yalnız cevaplayıcının hangi arayüzü cevapladığı ve uyarı metni olur.
- Kart bağlamı sözlüğüyle çakışan ad alınmadı ("seri port", "programlama portu").
- `test_es_ad_baglam_cakismasi` her eş ad için şunları sınar: `baglam_oku` boş dönüyor, hiçbir konu deseni ("usb", "jtag", "uart0", "konsol", "flash") eş adın içinde geçmiyor, iki yasak ad tabloda yok, hedefler arayüz listesinde.
- Cevaplayıcı testi: "CAN hangi pinlere çıkabilir?" (QFN32) → TWAI, kaynaklı cevap.

## v3 hükmü

`doc/olcum/2026-11-21_adim10_v3_sonuc.md` sonuna "Web AI hükmü" bölümü eklendi (set değişmedi):

- X34 ve X35'teki davranış K-7'ye uygun. Setin beklentileri pin tercihi öncesine ait.
- Resmî sonuç 43/45; K-7'ye göre 45/45.
- X05'teki iyileşme model bilgisine dayanıyor (L-3).

Aynı bölüm Adım 10a v3 sonuç belgesine de eklendi (`doc/olcum/2026-11-21_adim10a_v3_sonuc.md`).

## WROOM-1 karşılaştırması

Kaynak: **ESP32-C6-WROOM-1 & WROOM-1U Datasheet v1.4** (Espressif).

- URL: https://www.espressif.com/sites/default/files/documentation/esp32-c6-wroom-1_wroom-1u_datasheet_en.pdf. Yönlendirme: https://documentation.espressif.com/esp32-c6-wroom-1_wroom-1u_datasheet_en.pdf.
- Sürüm notu tarihi 2025-12-10; PDF oluşturma tarihi aynı. 52 sayfa, 938 372 bayt.
- SHA-256 `163020762fa6d499e0c611c5a13e78ad9d4720b421c6bc5e14e16fc748862b73`.
- İndirme 2026-11-21. Dosya depoya konmadı (kaynak onayı Adım 10b'de).
- Tür: üretici belgesi.

| Bilgi | Datasheet | Sayfa |
|---|---|---|
| İçteki çip ve paket | **ESP32-C6, QFN40** (modül şematiğinde U1 "ESP32-C6-QFN40") | Fig. 8-1, s. 38 |
| Flash | çip dışında **QSPI flash** (U2), SPICS0 / SPICLK / SPID / SPIQ / SPIWP / SPIHD ve VDD_SPI hatlarına bağlı | Fig. 2-1 s. 9; Fig. 8-1 s. 38 |
| Flash seçenekleri | Table 1-1: N4 (4 MB), N8 (8 MB), N16 (16 MB), hepsi Quad SPI. Aynı belgenin kapağı ve §1.2 metni "up to 8 MB" ve "two versions" diyor; v1.4 sürüm notunda N16 eklenmiş. **Belge içi tutarsızlık** | s. 1, 3–4, 50 |
| Modül pinleri | 29 pin (Table 3-1) | s. 11 |
| Modülün içinde kullanılan pinler | flash hatları (çipin SPICS0/SPIQ/SPIWP/SPIHD/SPICLK/SPID pinleri; veritabanında QFN40 için GPIO24–26, 28–30, `flash_pin`) ve 40 MHz kristal (XTAL_P/N). Bunlar modül pinine çıkmıyor | Fig. 8-1 |
| Dışarı çıkmayan GPIO | GPIO14 yok (QFN40'ta pini yok, veritabanıyla uyumlu); flash GPIO'ları çıkmıyor | Table 3-1 |
| Strapping | GPIO8 ve GPIO9 açılış kipi (GPIO9 iç zayıf pull-up; indirme kipi GPIO8=1, GPIO9=0); MTMS/MTDI SDIO; GPIO15 JTAG kaynağı | Tables 4-1, 4-3, s. 12–13 |

Modül pin → GPIO eşlemesi (Table 3-1): 1 GND, 2 3V3, 3 EN, 4 IO4 (GPIO4), 5 IO5, 6 IO6, 7 IO7, 8 IO0, 9 IO1, 10 IO8, 11 IO10, 12 IO11, 13 IO12 (USB_D-), 14 IO13 (USB_D+), 15 IO9, 16 IO18, 17 IO19, 18 IO20, 19 IO21, 20 IO22, 21 IO23, 22 NC, 23 IO15, 24 RXD0 (GPIO17), 25 TXD0 (GPIO16), 26 IO3, 27 IO2, 28 GND, 29 EPAD (GND).

**K2 (nanoESP32-C6 v1.0 şematiği) ile karşılaştırma:**

- 29 pinin hepsinde modül pin numarası ve adı Adım 10 raporundaki K2 listesiyle birebir aynı. Fark yok.
- K2'de TXD0 = GPIO16 ve RXD0 = GPIO17 yan etiketleri datasheet'teki U0TXD/GPIO16, U0RXD/GPIO17 ile uyumlu.
- K2'deki EN → CHIP_PU bağlantısı datasheet'teki EN (çipi açar) ile uyumlu.
- K2'de GPIO8 10K ile 3V3'e çekili ve WS2812'yi sürüyor. Datasheet'e göre GPIO8 strapping pini ve indirme kipinde 1 olmalı; çekme direnci bu koşulu karşılıyor.
- K2'de S1 → GPIO9 (BOOT) bağlantısı datasheet'teki açılış kipi tablosuyla uyumlu.
- K2'de modülün flash sürümü (N4 / N8 / N16) yazmıyor: **bulunamadı**.
- Sonuç: Adım 10 raporundaki "modül → GPIO" satırı artık iki kaynakla destekleniyor (K2 + WROOM-1 datasheet), `kaynak_belge`. "Modül içindeki çip" satırı da kaynaklı: ESP32-C6 QFN40 ve harici QSPI flash. Flash boyutu doğrulanmadı.

## Ölçüm (önce/sonra tablosu, değişen kararlar, tur dökümü)

Dondurma `doc/olcum/2026-11-21_adim10a_dondurma.md`: öncesi ve sonrası aynı (proje `97055e6`, çekirdek `41e2198`). Ölçüm başladıktan sonra kod, istem ve sözlük değişmedi.

Koşu: `kapsamlı kos`, Çağrı A + atayıcı, 13:08–14:15. Günlük `doc/olcum/2026-11-21_adim10a_kos.log`. Sonuçlar ve ham izler:
- `doc/olcum/2026-11-21_adim10a_v4_sonuc.md`, `2026-11-21_adim10a_v4_ham.jsonl`
- `doc/olcum/2026-11-21_adim10a_v3_sonuc.md`, `2026-11-21_adim10a_v3_ham.jsonl`

| Ölçüt | v4 Adım 9b (v4b) | v4 Adım 10 | **v4 Adım 10a** | v3 Adım 9 | v3 Adım 10 | **v3 Adım 10a** |
|---|---|---|---|---|---|---|
| Çağrı A doğru | 36/36 | 34/36 | **35/36** | 43/45 | 43/45 | **43/45** |
| A yanlışları | — | Y33, Y34 | **Y29** | X05, X34 | X34, X35 | **X34, X35** |
| Geçtiği tur 1 / 2 / 3 | 35/1/0 | 31/5/0 | **32/4/0** | 41/1/0 (+2 BILGI_YOK, 1 KULLANICIYA) | 33/12/0 | **36/8/1** |
| Atayıcı: atandi / tercih_uyg. / mumkun_degil / pin gerekmiyor | 26/8/1/1 | 27/8/0/1 | **26/8/1/1** | 39/–/3/0 | 40/1/2/0 | **40/1/2/0** |
| Atandı + tercih: tercihler uygulandı | 19/19 | 20/20 | **18/18** | — | 1/1 | **1/1** |
| Atayıcı kararı hakemle aynı | 35/35 | 34/35 | **35/35** | 41/42 | 42/43 | **42/43** |
| Uçtan uca doğru | 36/36 | 34/36 | **35/36** | 43/45 | 43/45 | **43/45** |
| Süre A ort. / ortanca / en uzun (sn) | 36.5 / 35.6 / 71.1 | 44.2 / 38.8 / 126.3 | 45.6 / 39.3 / 101.4 | 29.4 / 24.4 / 97.2 | 51.1 / 35.1 / 154.0 | 50.0 / 36.3 / 155.5 |

Kabul ölçütleri:

| Ölçüt | Sonuç |
|---|---|
| pytest proje ve çekirdek | geçti: 235/235, 19/19 |
| v4 36/36 | **karşılanmadı: 35/36.** Y33 ve Y34 düzeldi; Y29 yeni yanlış (aşağıda) |
| Y33 GPIO_IN 16 ile atanır | evet: 2. turda "On altı buton" 16, atandi, 18 pin |
| Y34 mumkun_degil | evet: 2. turda "On yedi buton" 17, mumkun_degil |
| Tercihler 20/20 | **karşılanmadı: 18/18.** Y34 artık atanmadığı için ulaşılabilecek en yüksek değer 19/19 (v4b ile aynı); Y29'daki tercih kaybolduğu için 18 |
| v3 resmî ≥ 43/45, A yanlışları yalnız X34/X35 | karşılandı |
| Sınav cümlesi: soru ayrımı Adım 10'daki gibi, aynı paketin iki çalıştırmasında model yanıtı aynı | karşılandı (`bagimsiz_sinav.md`, iz satır 30–33) |
| Düzeltme turları Adım 9 düzeyine yakın | kısmen. v4: 2. tura kalan istek 1'den 5'e çıkmıştı, şimdi 4; ikisi amaçlı SAYI_UYUSMAZ, biri Adım 9'dan beri var. v3: 1'den 12'ye çıkmıştı, şimdi 9 (+1 istek 3. turda); BAGLAM_KONUSUZ yedi istekte sürüyor |
| diger_ifadeler'e kaçan ihtiyaç yüzünden karar değişikliği | **yok.** Uyarı alan 8 öğenin hiçbiri ihtiyaç değil; bu isteklerin hepsinde A doğru. Bağlam bilgisi kaybı var (X28, aşağıda) |

### Değişen kararlar: v4 (v4b → Adım 10a)

| İstek | v4b | Adım 10a | Değerlendirme |
|---|---|---|---|
| Y29 "LED'i önce GPIO2'ye koymuştum, sonra GPIO3'e taşıdım." | GPIO_OUT, tercih GPIO3 → atandi GPIO3 | GPIO_OUT; GPIO2 ve GPIO3 ikisi de `diger_pin_bahisleri` → tercih yok, atandi **GPIO0** | **Gerileme.** Model GPIO3'ü tercih değil "başka bahis" saydı. Kod bunu yakalayamaz: üç listeden hangisine gireceği anlam kararıdır, iki liste de geçerli. İstem değişikliğinin modelin çıktısını kaydırmasından; diger_ifadeler'le ilgisi yok (`diger_ifadeler` boş) |
| Y33 | GPIO_IN 16, atandi | 1. tur "altı buton" 6 → SAYI_UYUSMAZ ("'on altı' = 16 … include all of it") → 2. tur "On altı buton" 16, atandi | Düzeldi (Adım 10'da 6 ile atanmıştı) |
| Y34 | GPIO_IN 17, mumkun_degil | 1. tur "yedi buton" 7 → SAYI_UYUSMAZ → 2. tur 17, mumkun_degil | Düzeldi (Adım 10'da 7 ile atandi) |
| Y36 | GPIO_IN 1 + 3 | GPIO_IN 4 tek kalem | Çoklu küme ve karar aynı |
| Y19 | 1. tur | 2. tur (BAGLAM_KONUSUZ: "GPIO0 ve GPIO1'e 32 kHz kristal bağlı") | Karar aynı; ifade 2. turda diger_ifadeler'e geçti ve uyarı aldı (aşağıda) |

### Değişen kararlar: v3 (Adım 10 → Adım 10a)

Karar değişikliği yok: Çağrı A çoklu kümeleri, tercihler ve atayıcı kararları her istekte aynı. Tur değişiklikleri:
- X03 aynı çoklu küme, gruplama farklı.
- 1. tura inenler: X01, X04, X07, X08, X18, X35 (BAGLAM_KONUSUZ artık yok).
- 2. ya da 3. tura çıkanlar: X16, X22, X45 (dökümde).
- X32/X33 `emin_degilim` ve eksik kodları aynı.

Adım 9 → 10a arasında v3'te değişen kararlar Adım 10 raporundaki gibi:
- X05 düzeldi.
- X32/X33 `emin_degilim` oldu.
- X34/X35'te tercih yakalandı (resmî puanda yanlış, Web AI hükmüne göre doğru).

### Tur dökümü: 2. ve 3. turu tetikleyen hatalar

| Set | İstek | Tur | Kod | İfade / ayrıntı |
|---|---|---|---|---|
| v4 | Y17 | 1 | BELIRSIZ_PIN_TERCIHI | "5 numaralı pin" tercih yapılmış (Adım 9'dan beri aynı) |
| v4 | Y19 | 1 | BAGLAM_KONUSUZ | "GPIO0 ve GPIO1'e 32 kHz kristal bağlı" |
| v4 | Y33 | 1 | SAYI_UYUSMAZ | "altı buton" adet 6; metinde "On altı" = 16 |
| v4 | Y34 | 1 | SAYI_UYUSMAZ | "yedi buton" adet 7; metinde "On yedi" = 17 |
| v3 | X02 | 1 | BAGLAM_KONUSUZ | "Cihaz pille çalışacak" |
| v3 | X11 | 1 | BAGLAM_KONUSUZ | "debug için değil" |
| v3 | X16 | 1 | BAGLAM_KONUSUZ | "İki kat var" |
| v3 | X22 | 1, 2 | DAYANAK_SINIRI | "MAX6675 termokupl modülü" ← "modülünü"; 3. turda düzeldi |
| v3 | X25 | 1 | BAGLAM_KONUSUZ | "Ekran kullanmayacağım." |
| v3 | X29 | 1 | BAGLAM_KONUSUZ | "Endüstriyel kart:" |
| v3 | X30 | 1 | BAGLAM_KONUSUZ | "Endüstriyel kart:" |
| v3 | X43 | 1 | BAGLAM_KONUSUZ ×3 | "Kutuyu 3D yazıcıda basacağım", "yazılımı Python ile değil C ile yazacağım.", "Güç için 18650 pil." |
| v3 | X45 | 1 | SAYI_UYUSMAZ | "iki buton" adet 2; metinde "On iki" = 12. Gerçek yakalama: Adım 10'da 1. turda doğruydu, bu kez model sayıyı yarım aldı ve kural düzeltti |

Toplam: v4'te 4 istek ek tura gitti (2 amaçlı yakalama, 1 eski), v3'te 9 istek. BAGLAM_KONUSUZ v3'te 16 ifadeden 9'a, v4'te 4'ten 1'e indi. Model ilk turda konusuz cümleyi hâlâ bağlam listesine koyabiliyor; düzeltme iletisinden sonra cümleyi diger_ifadeler'e taşıyor (hepsi 2. turda geçti). DAYANAK_SINIRI yeni bir tur kaynağı: X22'de iki tur sürdü.

### diger_ifadeler: uyarı alan öğeler

v4'te 5 öğeden 1'i, v3'te 19 öğeden 7'si uyarı aldı. Hiçbiri pin ihtiyacı değil; bu isteklerin hepsinde Çağrı A doğru.

| Set | İstek | Öğe | Uyarının nedeni | İhtiyaç kaybı? |
|---|---|---|---|---|
| v4 | Y19 | «GPIO0 ve GPIO1'e 32 kHz kristal bağlı» | sayı «32», pin bahsi GPIO0, GPIO1 | yok. GPIO0/1 `kullanilmayacak_pinler`'de (kabul); kristal bağlamı pilotta bağlam anahtarı değil |
| v3 | X01 | «Kutunun içinde 12 V adaptör olacak, kartı da 5 V'tan besleyeceğim.» | sayı «12», «5» | yok (güç kaynağı) |
| v3 | X02 | «her 10 dakikada derin uykudan bir zamanlayıcıyla uyanacak.» | sayı «10», «bir» | yok. Zamanlayıcıyla uyanma pin istemez; kabul de WAKE beklemiyor |
| v3 | X08 | «CAN modülünü ileride ekleyeceğim, şu an yok.» | arayüz adı (TWAI) | yok. "Şu an yok": kabul TWAI beklemiyor |
| v3 | X16 | «İki kat var» | sayı «İki» | yok |
| v3 | X28 | «Flash'ı harici bir regülatörle besleyeceğim.» | sayı «bir» | ihtiyaç kaybı yok, ama **bağlam bilgisi kaybı var** (aşağıda) |
| v3 | X43 | «Güç için 18650 pil.» | sayı «18650» | yok |
| v3 | X43 | «Toplam bütçem 500 TL.» | sayı «500» | yok |

**X28 bulgusu:** "Flash'ı harici bir regülatörle besleyeceğim." gerçek kart bağlamı (`harici_flash_beslemesi`).
- Adım 10'da model bu cümleyi `baglam_ifadeleri`'ne koyuyordu. Komut satırında `--harici-flash-beslemesi` verilmediği için BAGLAM_CELISKI uyarısı çıkıyordu.
- Adım 10a'da model cümleyi `diger_ifadeler`'e koydu. Denetim bunu hata saymadı, BAGLAM_CELISKI uyarısı kayboldu. Kullanıcı yalnız DIGER_IHTIYAC_IZI uyarısını görüyor ("bir" sayısı yüzünden) ve bu uyarı asıl sorunu söylemiyor.
- Karar değişmedi: bağlamı komut satırı belirler, flash pinleri yine kullanılmadı. Kaybolan şey, "metin ile komut satırı çelişiyor" uyarısı.
- Öneri (kod, set dışı): `diger_ifadeler` öğesinde `baglam_oku` bir konu buluyorsa hata versin ("this is board context; put it into baglam_ifadeleri"). BAGLAM_KONUSUZ'un tersidir. Onay ve yeni dondurma gerekir; yapılmadı.

## Açık kalanlar

1. **v4 Y29 gerilemesi:** tercih GPIO3, `diger_pin_bahisleri`'ne kaydı ve atama GPIO0'a yapıldı. Kod denetimi bunu ayırt edemez (iki liste de geçerli). İstem değişikliğinin modelin çıktısını kaydırmasından. Ele almak için seçenekler:
   - (a) istem kural 10'a "taşındı / şimdi … de" gibi güncel konumun tercih olduğunu söyleyen genel bir cümle (Y29'a göre değil, düzeltme kalıbına göre);
   - (b) aynı cümlede iki GPIO bahsi olup ikisi de `diger_pin_bahisleri`'ndeyse ve ihtiyaç tercihsizse kullanıcıya görünür uyarı.
   Karar Sinan / Web AI'da.
2. **X28 bağlam kaybı:** diger_ifadeler'deki kart bağlamı cümlesi için hata önerisi (yukarıda).
3. **Tercihler ölçütü:** görevdeki 20/20, Adım 10'da Y34'ün yanlışlıkla atanmasından gelen sayıydı. Doğru hedef 19/19; bu ölçümde 18/18 (Y29).
4. **BAGLAM_KONUSUZ** v3'te yedi istekte, v4'te bir istekte sürüyor. Kalan ifadelerin çoğu kısa parçalar ("debug için değil", "Endüstriyel kart:", "İki kat var"). Sözlüğü genişletmek çözüm değil (hiçbiri kart bağlamı değil); istem örneği eklemek ise "en fazla bir örnek" sınırını aşar.
5. **DAYANAK_SINIRI** X22'de iki tur sürdü (model "modülü"nü iki kez tekrarladı). İleti tam sözcüğü veriyor; üçüncü turda düzeldi.
6. **DIGER_IHTIYAC_IZI** "bir" sözcüğüne de uyarı veriyor (X02, X28: "bir zamanlayıcıyla", "bir regülatörle"). Kural gereği; gürültü kabul edilebilir mi, Sinan karar versin.
7. **"can" eş adı** Türkçe "can" sözcüğüyle karışabilir (yalnız cevaplayıcı ve uyarı).
8. Atayıcının `mumkun_degil` neden metni ilk tıkanılan sinyal sayısını veriyor, toplam ihtiyacı değil (duman testi: 23 istendi, metin "20 sinyal için yalnız 19 uygun pin").
9. WROOM-1: nanoESP32-C6'daki modülün flash sürümü bulunamadı. Datasheet v1.4'te flash seçenekleri belge içinde tutarsız ("up to 8 MB" ve N16).
10. Önceki adımlardan kalanlar:
    - Super Mini satırları doğrulanmadı.
    - Sinan'ın kart üstü elle kontrol listesi bekliyor.
    - Spot kontrol 0/8; `spot_kontrol.md` şu an bir düzenleyicide açık.
    - Kodda kalan mesajlar taşınmadı.
    - v5 seti Web AI'dan bekleniyor.

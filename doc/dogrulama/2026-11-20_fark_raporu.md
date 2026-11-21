# Fark raporu — ESP32-C6 Datasheet v1.6 (2026-11-20)

Kaynak: `veri/kaynak/esp32-c6_datasheet_en.pdf`, ESP32-C6 Series Datasheet v1.6 (2026-11-10), SHA-256 `c9bf7ece…c339` (yükleme öncesi yeniden doğrulandı). Sayfa numaraları basılı numaradır, PDF sayfasıyla aynı.

Kod: `src/pinsecim/cikar_a.py` (A), `cikar_b.py` (B), `karsilastir.py` (karşılaştırmalar), `kararlar.py` (kararlar). Model kullanılmadı.

## Yöntem

| Çıkarma | Kaynak | Yöntem |
|---|---|---|
| A | Table 1-1 (s. 13), Figure 2-1/2-2 (s. 14–15), Table 2-1/2-2 (s. 16–18), 2-4/2-5 (s. 20–21), 2-7 (s. 22), 2-9 (s. 23), 2.3.5 metni (s. 25), 2-10/2-11 (s. 26–27), 2-16 (s. 32), 3-1 (s. 33), 3-3 (s. 34) | pdfplumber çizgili tablo hücreleri; dipnot işaretleri satır tabanından yükseklikle ayıklanır; hücre dolgu rengi ve kalın yazı (MaisonNeue-Medium) ayrıca okunur. Şekiller ve 2.3.5 listeleri `pdftotext -layout` metninden |
| B | Consolidated Pin Overview, Table 7-1 (s. 79), Table 7-2 (s. 80) | Tablo/çizgi algılama yok: kelimeler, ortaları ikinci başlık satırının sütun kenarlarına göre sütunlara yerleştirilir; satır rengi kelimelerin altındaki dolgudan |

## 1. A–B karşılaştırması: 0 fark

Her paket ve her pin için şu alanlar karşılaştırıldı: pin adı, pin türü, güç, reset ayarı, reset sonrası ayarı, analog F0–F1, LP IO MUX F0–F1, IO MUX F0–F2 ve türleri, GPIO numarası (A: Table 2-4/2-5 GPIO adı; B: IO MUX F1), kalın (varsayılan) işlevler, vurgu rengi (A: pinin 2-4/2-5/2-7/2-9 hücrelerindeki renkler; B: satır rengi).

- QFN40: 41 pin × 18 alan; QFN32: 33 pin × 18 alan. Fark yok.
- Karşılaştırmanın boşta çalışmadığı testle gösterildi: B'de tek hücre bozulunca tam o fark çıkıyor (`testler/test_veri.py::test_karsilastirma_bos_degil`).
- Paket başına GPIO: QFN40 30, QFN32 22. Table 2-4/2-5, Table 7-1/7-2, Table 2-1/2-2'deki IO pin sayısı ve s. 1'deki "30 or 22 GPIOs" aynı.
- Pin sayısı: QFN40 41, QFN32 33. Şekil, Table 2-1/2-2 ve Table 7-1/7-2 aynı.

## 2. A iç çapraz denetimleri: 1 fark

Denetimler: şekil etiketleri ↔ Table 2-1/2-2; Table 2-10/2-11'deki GPIO matrisi hücresinin GPIO'su ↔ pinin GPIO'su (Table 2-4/2-5); P1 sabit sinyal ↔ pinin IO MUX / LP IO MUX / analog işlevleri; P2–P4 önceliği ↔ 2.3.5 listeleri (s. 25).

### A-ic|QFN32|9|cevre:SPI2:gpio

| | |
|---|---|
| Nerede | Table 2-11 QFN32 Peripheral Pin Assignment, s. 27; pin 9 (GPIO3), sütun SPI2 |
| A (tablo hücresi) | `GPIO1 (P2)` |
| Beklenen (çapraz) | `GPIO3`: pin 9'un GPIO'su (Table 2-5 s. 21, Table 2-2, Table 7-2); aynı satırın diğer 10 GPIO matrisi hücresi `GPIO3 (P2)`; Table 2-10 s. 26'da aynı pinin SPI2 hücresi `GPIO3 (P2)` |
| Görüntü | s. 27, 200 dpi'da açıldı: hücrede gerçekten `GPIO1 (P2)` yazıyor (çıkarma hatası değil) |
| Karar | **Belgedeki gibi girildi (`hucre = 'GPIO1 (P2)'`, `gpio_no = 1`), `belirsiz = true`**, not alanında açıklamayla |
| Gerekçe | Kural: belgede yazmayanı tabloya koyma. Belge kendi içinde tutarsız; büyük olasılıkla yazım hatası, ama bunu düzeltmek belgede yazmayan bir bilgiyi eklemek olur. Satır işaretli kalır; Adım 3'teki kurallar belirsiz satırları ayrıca ele almalı. |

## 3. Renk ↔ metin: 0 fark

Kırmızı/sarı vurgulu her GPIO (Table 2-4/2-5/2-7/2-9) 2.3.5 listelerinde ya da Table 3-1'de geçiyor; metinde geçen her GPIO en az bir tabloda vurgulu. Bu yüzden **renkten gelen kayıt yok**: `gpio_kisit` satırlarının hepsi `kaynak_turu = 'metin'`.

Görsel denetimde görülen ama ayrı satıra dönüştürülmeyen renk ayrıntıları (bilgi metinde zaten var):

- Table 2-4/2-5: sarı = strapping pinlerinin GPIO adı (GPIO4, 5, 8, 9, 15), JTAG F0 (MTMS, MTDI, MTCK, MTDO), UART0 F0 (U0TXD, U0RXD); kırmızı = flash F0 (SPICS0, SPIQ, SPIWP, SPIHD, SPICLK, SPID).
- Table 2-9: sarı = USB_D-, USB_D+, VDD_SPI. Table 2-7: sarı = LP_GPIO4, LP_GPIO5.
- Table 7-1/7-2: vurgu satır düzeyinde (açık ton), strapping pinlerinde ayrıca "At Reset" hücresi koyu sarı (2.3.4'teki notla uyumlu).
- Table 2-10/2-11: hücre renkleri önceliği gösteriyor (yeşil P1, mavi P2, sarı P3, kırmızı P4) ve hücre metnindeki "(Pn)" ile aynı.

## 4. Belirsiz işaretli kayıtlar

| Tablo | Satır | Neden |
|---|---|---|
| `cevre_birim_sinyal` | QFN32, pin 9, SPI2, `GPIO1 (P2)` | Madde 2 |

## 5. Türetilen alanlar (belgede doğrudan o hücrede yazmayan ama başka tablodan bağlanan)

Bunlar belirsiz sayılmadı; bağlantı belgedeki başka bir tablodan geliyor ve not alanında yazıyor:

- `gpio_islev` LP IO MUX satırlarının `gpio_no`'su: Table 2-7 yalnız pin no (6–13) veriyor; GPIO no aynı pin no üzerinden Table 2-4/2-5'ten (iki pakette de pin 6–13 aynı GPIO).
- Strapping satırlarında MTMS → GPIO4, MTDI → GPIO5: Table 2-4 F0 adlarından.
- `cevre_birim_sinyal.yonlendirme`: P1 sinyal pinin IO MUX işlevlerindeyse `IO_MUX_SABIT`, LP IO MUX işlevlerindeyse `LP_IO_MUX_SABIT`, analog işlevlerindeyse `ANALOG_SABIT`; `GPIOn (P2–P4)` hücreleri `GPIO_MATRISI` (2.3.5 tanımı).
- `gpio_kisit` `bu_pakette_yok`: iki paketin IO MUX tablolarının farkı (QFN40'ta GPIO14 yok; QFN32'de GPIO10, 11, 24–30 yok).
- `pin.varsayilan_surme_ma`: Table 2-1/2-2 dipnot 3 (GPIO12/13 40 mA, diğerleri 20 mA); yalnız GPIO'su olan pinlere yazıldı.

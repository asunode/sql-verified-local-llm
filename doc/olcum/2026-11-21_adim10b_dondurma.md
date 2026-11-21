# Ölçüm dondurma kaydı (adim10b) — 2026-11-21

Öncesi: 2026-11-21 14:38:53 +0300 · sonrası: 2026-11-21 15:50:30 +0300. Ham: `2026-11-21_adim10b_dondurma_once.json`, `2026-11-21_adim10b_dondurma_sonra.json`.

Değişiklik: Adım 10b: adim10a kaydından (97055e6) sonra; İSTEM DEĞİŞMEDİ (ihtiyac_sistem.txt 3ff741e27c2e, sistem metni 10a iziyle birebir). Değişen: cagrilar.py (DIGER_PIN_TERCIH_IZI uyarısı, DIGER_BAGLAM hatası, tek başına 'bir' DIGER_IHTIYAC_IZI dışı, yonelme_eki), sozluk.py (harfe duyarlı eş ad), atayici.py (mumkun_degil nedeninde toplam), hat.py ve __main__.py (--kart, kart notu), cevap.py (kart soruları), yeni kart.py ve kart_verisi.py, kural_verisi.py (CAN harfe duyarlı, kart konuları cevap_turu 'kart', 3 mesaj), yukle.py (kart tabloları ve kaynakları), sql 009–011, kapsamli.py (uyarı bölümü), dogrulama.py (tablo listesi). Gerileme: v4 ve v3 yeniden koşulacak.

## Dosyalar (SHA-256)

| Dosya | Öncesi | Sonrası |
|---|---|---|
| `src/pinsecim/istemler/atama_sistem.txt` | `f09040e1f110af265f4f47e90193cf868b6cca5c504ccabe8741fe38b6bbfce6` | aynı |
| `src/pinsecim/istemler/ihtiyac_sistem.txt` | `3ff741e27c2e7b41c548d21d6dfc3e029af5b7ed9d785803875e474164f0775a` | aynı |
| `src/pinsecim/semalar.py` | `5d148ad28822df2ef48c27f432267ce0d238086a262dd0a5971f9f3a906af55f` | aynı |
| `src/pinsecim/cagrilar.py` | `f99e4bfab56471402e307a8200f9e96af656a5cb93a9bd789611c90034e3bca6` | aynı |
| `src/pinsecim/hat.py` | `34d5afd40edd164f9f22d1c5d0894562fba31ce30271b54726c70b1651094eeb` | aynı |
| `src/pinsecim/denetim.py` | `60158f712538d5bc20476906eb71b7e8169398aaea3b33ae481976362f41a13f` | aynı |
| `src/pinsecim/atayici.py` | `93938bdb2456796045b9646a67229649d1e6c8e4c8b3779eceeff7e0211c852e` | aynı |
| `src/pinsecim/pinveri.py` | `c9af6a9e3fec674af087d279dc970a0774e70f75295446fca957c7c5bba38bc8` | aynı |
| `src/pinsecim/sozluk.py` | `462cba27199dc0cec9b115c86fe9ca3e6eb915c7c481798fec98e3832ea99f33` | aynı |
| `src/pinsecim/kural_verisi.py` | `00258827e67bdc65d697bc192d0c8a8b121e1722ba7bf28fb7e2569152b2dd08` | aynı |
| `setler/dogrulama/dogrulama_seti_v1.json` | `12211f6eccea718a80d8cce76813ae85a710a4048995334f4f8090677f393908` | aynı |
| `setler/gelistirme/gelistirme_seti.json` | `b5434c6d17ea5ef2bdf17c3968e5a5cba350babd45cf976883179131d0666f38` | aynı |
| `testler/veri/denetim_vakalari.json` | `0a1422c966583a9896698aabf85425851a745323eb57d3e3c47876e0c602b727` | aynı |
| `src/pinsecim/cevap.py` | `9a3257ca5085e0bb2eadd2b2299ca4fc7980ae6521b5fe5d0a802aaa495095d2` | aynı |
| `src/pinsecim/__main__.py` | `d1834bd0309384a47fc8d1761149501829d3bc98a4389b1f4a66f4536a116260` | aynı |
| `src/pinsecim/kapsamli.py` | `67be9f6d9343a1494639af0b33e57491e1594f8ba8b98928e26887360cfa601a` | aynı |
| `src/pinsecim/dogrulama.py` | `d8bb6ab73913a375bb64b807ecc0f62f959be70d3c76874c56ce90a0bb82e65a` | aynı |
| `src/pinsecim/yukle.py` | `44ebb0c264319e9f1ba4e9c3e9f6b7a49f91a6314aa3a4c6276b6e0521b4e417` | aynı |
| `src/pinsecim/kart.py` | `eefaadb774414bf5ca5a67efc5fa7c0a103ff202bf654780b01f4f7d043e0d53` | aynı |
| `src/pinsecim/kart_verisi.py` | `d5906536fc4332e36f74ef74c04c3b4a90f37069e3db1460fef6b195d126dcc7` | aynı |
| `sql/008_sayi_es_ad.sql` | `af0789e457f4b555bf47d18977720390906128015ee1257963b7fad90021129b` | aynı |
| `sql/009_es_ad_harf.sql` | `f44b345c2645f8b695279e90571862d1bd1f39da3e1146791da784ac81ce82a1` | aynı |
| `sql/010_kart.sql` | `45927e1826ab7d9018ffed4bbcad3655a022cfa15be35042546dd2683e47ea66` | aynı |
| `sql/011_kart_konu.sql` | `0d136a987e6bfdbb1a062d62100d10ec9c3d16b9a99951c8542dcb4e8d73c555` | aynı |
| `setler/dogrulama/kapsamli_set_v3.json` | `2497ff34e7d8c97d772b6cf696343d6daf37fed80675d7bc8f5594a6741d8967` | aynı |
| `setler/dogrulama/test_seti_v4.json` | `3c449e7cf9cc89b2fa612f6c4a15fb00d69d000462840816831738d60c69df07` | aynı |

## Kural tabloları (satır sayısı, satırların SHA-256'sı)

| Tablo | Satır | SHA-256 | Sonrası |
|---|---|---|---|
| `kural` | 17 | `2af81694b0086f990550d2c21a6eaafd7ee649ef272f09532cfc0b6963c6d203` | aynı |
| `cevre_adet` | 10 | `4b5b11e6f6e00d1a86f6a4f698bdec1aadb798e6505c31d5a1b0554dc2f6280d` | aynı |
| `arayuz_tanimi` | 13 | `2148d7a09705b570956e488ce8c770ac666928023a3159dd848fa85f4d379310` | aynı |
| `arayuz_sinyal` | 6 | `857c002a27612b7fb8c6addf8bc2a4e76809aea8d8fe8633ab646b8a7d58c7a6` | aynı |
| `yorum` | 1 | `7f226c6475d6a48aab97d1abb3bd128e483f719857370301d84a1aad0738f751` | aynı |
| `sayi_sozcugu` | 32 | `fd46c900561a4c3bf274d44ced7b7c0366fbdc6cbc8e853c11d0bffa4b6df00c` | aynı |
| `baglam_sozcugu` | 21 | `90f1c7e9b23dad3cd5d8b04329938b43a8c8bd18b72291a23685e94c8d8f7cc9` | aynı |
| `pin_bahsi_deseni` | 5 | `856b0320fec3e37097d9aff5ee233da9554f276ce80163ee7e4fdaa657ebaee4` | aynı |
| `soru_konusu` | 8 | `f9058bac247444fae76f20c9bae5353ee726a39578b7ebb636d9f0bed0f175c8` | aynı |
| `durum_mesaji` | 15 | `3f8f76103c9c6527d03c9c406ed4c6fc0498f0ed0f842fe4f7e9e4b1396b1d5b` | aynı |
| `arayuz_es_adi` | 9 | `beff51a11e61612ea922ee0b89c418e439a45d1491674697bfd45ab5ebb6aedc` | aynı |
| `kart` | 3 | `16b13d0d9e823e00a290772e0b2abaf6fef28803c62bc79ae389d7083208119c` | aynı |
| `modul_pin` | 29 | `ad7e691882f7f947b2ed1dd1efff5a32f69bd5694cef417323e2f07012f896f6` | aynı |
| `kart_pin` | 85 | `d5722c44df46428b522c3214ec6cd2070e6f21aaef7e790e7ce3b30fbb0bed6b` | aynı |
| `kart_parca` | 21 | `0fa5936d3d88c068df6ab6d5d921c7f64c24a453869ab80a985f2a8f438cf428` | aynı |

## Commit

| Depo | Öncesi | Sonrası | Arada değişen dosyalar |
|---|---|---|---|
| localllm_ass1 | `80c0ae7` | `249043d` | `doc/olcum/2026-11-21_adim10b_dondurma.md`, `doc/olcum/2026-11-21_adim10b_dondurma_once.json` |
| asu_llmcore | `41e2198` | `41e2198` | - |

Commit farkı yalnız `doc/` altındaysa aynı sayılır (dondurma ve ölçüm kayıtları).

Sonuç: öncesi ve sonrası aynı.

# Ölçüm dondurma kaydı (adim10c) — 2026-11-21

Öncesi: 2026-11-21 17:13:19 +0300 · sonrası: 2026-11-21 18:25:41 +0300. Ham: `2026-11-21_adim10c_dondurma_once.json`, `2026-11-21_adim10c_dondurma_sonra.json`.

Değişiklik: Adım 10c: adim10b kaydından (249043d) sonra. İstem dosyası aynı (ihtiyac_sistem.txt 3ff741e27c2e); modele giden arayüz listesine iki satır (RMT_TX, RMT_RX) ve JSON şemasının arayüz enum'una iki ad eklendi (L-5). Değişen: semalar.py (RMT_TX/RMT_RX), kural_verisi.py (RMT ve SPI2_CS adetleri, SPI adet_adi SPI2_CS, ortak_hat_secim, RMT eş adları, kart kuralları, mesajlar), pinveri.py (yuva_sinyalleri, ortak_hat_secim), atayici.py (ortak hat, kart aşamaları, SPI taşma iletisi), denetim.py (ortak hat, kart kuralları), cagrilar.py (SAYI_YARIM değer farkı), cevap.py (kart_eksik örneği), hat.py ve __main__.py (kart düzeyi atama, --rapor), kart.py (atama_bilgisi), kart_verisi.py (kart_pin.tur), yeni rapor.py, sql 012–013, yukle.py. Gerileme: v4 ve v3 kartsız yeniden koşulacak.

## Dosyalar (SHA-256)

| Dosya | Öncesi | Sonrası |
|---|---|---|
| `src/pinsecim/istemler/atama_sistem.txt` | `f09040e1f110af265f4f47e90193cf868b6cca5c504ccabe8741fe38b6bbfce6` | aynı |
| `src/pinsecim/istemler/ihtiyac_sistem.txt` | `3ff741e27c2e7b41c548d21d6dfc3e029af5b7ed9d785803875e474164f0775a` | aynı |
| `src/pinsecim/semalar.py` | `0b32f58616bb3b15a6f6467d9571b43997b6fe9d7d6f936592e606014444f9fb` | aynı |
| `src/pinsecim/cagrilar.py` | `4a38f0a28374b60973e165d1baa8fc3b31422ee5d5775d4906457cfd060c3ee8` | aynı |
| `src/pinsecim/hat.py` | `fa01432245bc79a5a022d86e56337149f7a8a801d90c1d5a08b3e8e17469f5ff` | aynı |
| `src/pinsecim/denetim.py` | `06478b9a42b69571a0745bc39601d47d027fa213959ca315ecadf85c3cd714e8` | aynı |
| `src/pinsecim/atayici.py` | `077c4c5660bce527de1328f7ab10ad6e6ab80847b7b0d7460e634a1d3132d2fe` | aynı |
| `src/pinsecim/pinveri.py` | `779a3ccc6d0d1987b1b75fb242963b54adee202174c68061c0f334468f49e76d` | aynı |
| `src/pinsecim/sozluk.py` | `462cba27199dc0cec9b115c86fe9ca3e6eb915c7c481798fec98e3832ea99f33` | aynı |
| `src/pinsecim/kural_verisi.py` | `5701c0adce288a2eb146421660237580b35e3054eb83ed94235a05c135b4f443` | aynı |
| `setler/dogrulama/dogrulama_seti_v1.json` | `12211f6eccea718a80d8cce76813ae85a710a4048995334f4f8090677f393908` | aynı |
| `setler/gelistirme/gelistirme_seti.json` | `b5434c6d17ea5ef2bdf17c3968e5a5cba350babd45cf976883179131d0666f38` | aynı |
| `testler/veri/denetim_vakalari.json` | `0a1422c966583a9896698aabf85425851a745323eb57d3e3c47876e0c602b727` | aynı |
| `src/pinsecim/cevap.py` | `30648ee036caa397c6d4a98b4a46907998493462e7035019c46e7b1ac86ee081` | aynı |
| `src/pinsecim/__main__.py` | `65af61110f49b5da668904dc4e51022cff71538d796c1c1dd8fbbd32cff7fd54` | aynı |
| `src/pinsecim/kapsamli.py` | `67be9f6d9343a1494639af0b33e57491e1594f8ba8b98928e26887360cfa601a` | aynı |
| `src/pinsecim/dogrulama.py` | `d8bb6ab73913a375bb64b807ecc0f62f959be70d3c76874c56ce90a0bb82e65a` | aynı |
| `src/pinsecim/yukle.py` | `2ab48b0eccff619d2715c9cc3ce803ae893c257688a377848363df89f81128c5` | aynı |
| `src/pinsecim/kart.py` | `0b908e58fbc01f06743426d11577c815067c66d057e5c1f9bdfe90678a555b3d` | aynı |
| `src/pinsecim/kart_verisi.py` | `4e56a2d08b356cfa726a41bfed28fe5cc74ee9596f39f9b8b0e68f5e6a8c868c` | aynı |
| `src/pinsecim/rapor.py` | `97437c8e586ae7bb5339a73f8fe51b0aca946c70e1777d3ef7056c2cb7742ca6` | aynı |
| `sql/008_sayi_es_ad.sql` | `af0789e457f4b555bf47d18977720390906128015ee1257963b7fad90021129b` | aynı |
| `sql/009_es_ad_harf.sql` | `f44b345c2645f8b695279e90571862d1bd1f39da3e1146791da784ac81ce82a1` | aynı |
| `sql/010_kart.sql` | `45927e1826ab7d9018ffed4bbcad3655a022cfa15be35042546dd2683e47ea66` | aynı |
| `sql/011_kart_konu.sql` | `0d136a987e6bfdbb1a062d62100d10ec9c3d16b9a99951c8542dcb4e8d73c555` | aynı |
| `sql/012_ortak_hat.sql` | `4041cfeefd96373dcb8c69b197962cf0ef539266d2c9ada830c4ef8a52b3b132` | aynı |
| `sql/013_kart_atama.sql` | `2892a6e9d11c6b1687f31b52daf4fecf4435730051ce41f82c31442654a97787` | aynı |
| `setler/dogrulama/kapsamli_set_v3.json` | `2497ff34e7d8c97d772b6cf696343d6daf37fed80675d7bc8f5594a6741d8967` | aynı |
| `setler/dogrulama/test_seti_v4.json` | `3c449e7cf9cc89b2fa612f6c4a15fb00d69d000462840816831738d60c69df07` | aynı |

## Kural tabloları (satır sayısı, satırların SHA-256'sı)

| Tablo | Satır | SHA-256 | Sonrası |
|---|---|---|---|
| `kural` | 21 | `5012900cf279c27f587736f6a0bb22a5d72d0928bc9863c02b2d63e4ce45461f` | aynı |
| `cevre_adet` | 12 | `aa26a41c1c5bfa6ec2503181f0ee6cdc15e3a07ab475a7dfa36d1981e8cdd786` | aynı |
| `arayuz_tanimi` | 15 | `49f737ce9af87ce647a5f8b0c53b83f4fa32ce0558a68f411bc62da3286c82b3` | aynı |
| `arayuz_sinyal` | 6 | `857c002a27612b7fb8c6addf8bc2a4e76809aea8d8fe8633ab646b8a7d58c7a6` | aynı |
| `yorum` | 1 | `7f226c6475d6a48aab97d1abb3bd128e483f719857370301d84a1aad0738f751` | aynı |
| `sayi_sozcugu` | 32 | `fd46c900561a4c3bf274d44ced7b7c0366fbdc6cbc8e853c11d0bffa4b6df00c` | aynı |
| `baglam_sozcugu` | 21 | `90f1c7e9b23dad3cd5d8b04329938b43a8c8bd18b72291a23685e94c8d8f7cc9` | aynı |
| `pin_bahsi_deseni` | 5 | `856b0320fec3e37097d9aff5ee233da9554f276ce80163ee7e4fdaa657ebaee4` | aynı |
| `soru_konusu` | 8 | `f9058bac247444fae76f20c9bae5353ee726a39578b7ebb636d9f0bed0f175c8` | aynı |
| `durum_mesaji` | 13 | `97973536321c770abfc2a431a6de250d0e3dcf6f88f5ba38975ec668904d1198` | aynı |
| `arayuz_es_adi` | 12 | `1d6f18093d1197e2cf165708b155eceab0f9d19a16ca0b349b2b62b075ddc641` | aynı |
| `kart` | 3 | `270c3f3ca685df837083685104e37b71bddcfdf4b9756f3ebb7eeee6b96d8029` | aynı |
| `modul_pin` | 29 | `ad7e691882f7f947b2ed1dd1efff5a32f69bd5694cef417323e2f07012f896f6` | aynı |
| `kart_pin` | 85 | `b3253ce1aa53c2aea24f552874d626ec1650d33281eeaee857b27aebb7d8d7f7` | aynı |
| `kart_parca` | 21 | `85708c456d800879c86f400dae44bac986a76f397f03ed2a5ed925dd1361e971` | aynı |

## Commit

| Depo | Öncesi | Sonrası | Arada değişen dosyalar |
|---|---|---|---|
| localllm_ass1 | `1704450` | `e9bab31` | `doc/olcum/2026-11-21_adim10c_dondurma.md`, `doc/olcum/2026-11-21_adim10c_dondurma_once.json` |
| asu_llmcore | `41e2198` | `41e2198` | - |

Commit farkı yalnız `doc/` altındaysa aynı sayılır (dondurma ve ölçüm kayıtları).

Sonuç: öncesi ve sonrası aynı.

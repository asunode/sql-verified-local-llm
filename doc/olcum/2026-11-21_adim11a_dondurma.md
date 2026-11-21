# Ölçüm dondurma kaydı (adim11a) — 2026-11-21

Öncesi: 2026-11-21 20:31:39 +0300 · sonrası: 2026-11-21 22:00:44 +0300. Ham: `2026-11-21_adim11a_dondurma_once.json`, `2026-11-21_adim11a_dondurma_sonra.json`.

Değişiklik: Adım 11a: adim11 kaydından (e527cb6) sonra. İstem ve sistem metni aynı. Değişen: cagrilar.py (DESTEKLENMEYEN_OZELLIK hata, KAPSANMAYAN_CUMLE emin_degilim'de yok), sozluk.py (desteklenmeyen_ozellik, soru_sozcugu), cevap.py ve __main__.py (elektriksel not, I2C ortak hat satırı), pinveri.py/denetim.py/atayici.py (I2C ×N tek hat), kural_verisi.py, yukle.py, sql 014–015, tamolcum.py (süre satırı), kapsam.py.

## Dosyalar (SHA-256)

| Dosya | Öncesi | Sonrası |
|---|---|---|
| `src/pinsecim/istemler/atama_sistem.txt` | `f09040e1f110af265f4f47e90193cf868b6cca5c504ccabe8741fe38b6bbfce6` | aynı |
| `src/pinsecim/istemler/ihtiyac_sistem.txt` | `3ff741e27c2e7b41c548d21d6dfc3e029af5b7ed9d785803875e474164f0775a` | aynı |
| `src/pinsecim/semalar.py` | `0b32f58616bb3b15a6f6467d9571b43997b6fe9d7d6f936592e606014444f9fb` | aynı |
| `src/pinsecim/cagrilar.py` | `54c80572f0537fcb244d0c307093d8b91686d2720fb24cddc9b2725a2b9d4405` | aynı |
| `src/pinsecim/hat.py` | `fa01432245bc79a5a022d86e56337149f7a8a801d90c1d5a08b3e8e17469f5ff` | aynı |
| `src/pinsecim/denetim.py` | `d1085990c1c32f44c145b63e6096487c3180c5b57f04524a985f274125089a12` | aynı |
| `src/pinsecim/atayici.py` | `adb06d8504b992575f1980e2bd3dc3bf56cb43654e4384f5351d34e8d240ad6f` | aynı |
| `src/pinsecim/pinveri.py` | `ff6387f8a274519608e5c41f39b76416bad78a4d38beca1d36225a257b20ff0f` | aynı |
| `src/pinsecim/sozluk.py` | `44993bd651f2e8de17dbcf6392f18c18d45c9e92b20f87ec1ca50ed385486629` | aynı |
| `src/pinsecim/kural_verisi.py` | `1804c44231e25e9b01f84d04b81f068d4fda76ba835bc3a8690c9b767a4250c8` | aynı |
| `setler/dogrulama/dogrulama_seti_v1.json` | `12211f6eccea718a80d8cce76813ae85a710a4048995334f4f8090677f393908` | aynı |
| `setler/gelistirme/gelistirme_seti.json` | `b5434c6d17ea5ef2bdf17c3968e5a5cba350babd45cf976883179131d0666f38` | aynı |
| `testler/veri/denetim_vakalari.json` | `0a1422c966583a9896698aabf85425851a745323eb57d3e3c47876e0c602b727` | aynı |
| `setler/dogrulama/test_seti_v5.json` | `e3f6aed3782e0effa84ad2bef90402badf0ef60551996b5f5384b6f3d264315e` | aynı |

## Kural tabloları (satır sayısı, satırların SHA-256'sı)

| Tablo | Satır | SHA-256 | Sonrası |
|---|---|---|---|
| `kural` | 21 | `5012900cf279c27f587736f6a0bb22a5d72d0928bc9863c02b2d63e4ce45461f` | aynı |
| `cevre_adet` | 12 | `aa26a41c1c5bfa6ec2503181f0ee6cdc15e3a07ab475a7dfa36d1981e8cdd786` | aynı |
| `arayuz_tanimi` | 15 | `5b96a35b2f00f397da5f704dff0f25f8c6c0c7589858b2d8879eda9a4ea75123` | aynı |
| `arayuz_sinyal` | 6 | `857c002a27612b7fb8c6addf8bc2a4e76809aea8d8fe8633ab646b8a7d58c7a6` | aynı |
| `yorum` | 1 | `7f226c6475d6a48aab97d1abb3bd128e483f719857370301d84a1aad0738f751` | aynı |
| `sayi_sozcugu` | 32 | `fd46c900561a4c3bf274d44ced7b7c0366fbdc6cbc8e853c11d0bffa4b6df00c` | aynı |
| `baglam_sozcugu` | 21 | `90f1c7e9b23dad3cd5d8b04329938b43a8c8bd18b72291a23685e94c8d8f7cc9` | aynı |
| `pin_bahsi_deseni` | 5 | `856b0320fec3e37097d9aff5ee233da9554f276ce80163ee7e4fdaa657ebaee4` | aynı |
| `soru_konusu` | 8 | `f9058bac247444fae76f20c9bae5353ee726a39578b7ebb636d9f0bed0f175c8` | aynı |
| `durum_mesaji` | 14 | `1684f30f1a9b8631920a3d9075edc9619520a99274d057e76d2afb73789ace6e` | aynı |
| `arayuz_es_adi` | 12 | `1d6f18093d1197e2cf165708b155eceab0f9d19a16ca0b349b2b62b075ddc641` | aynı |
| `kart` | 3 | `edeb67f5168bb5592101ebb396e11df3337c1247993625c2ae8b5f4e5ed4d86d` | aynı |
| `modul_pin` | 29 | `ad7e691882f7f947b2ed1dd1efff5a32f69bd5694cef417323e2f07012f896f6` | aynı |
| `kart_pin` | 85 | `1be58f89af106bc1f709419332f5f2b6d37d7043dda863074a3f70ceeb1927fe` | aynı |
| `kart_parca` | 21 | `bc7bf48b61f48701de8c9fc51c1800f94bf722d4567470d1f4e68f261a737974` | aynı |

## Commit

| Depo | Öncesi | Sonrası | Arada değişen dosyalar |
|---|---|---|---|
| localllm_ass1 | `69d7b69` | `f6d1bac` | `doc/olcum/2026-11-21_adim11a_dondurma.md`, `doc/olcum/2026-11-21_adim11a_dondurma_once.json` |
| asu_llmcore | `41e2198` | `41e2198` | - |

Commit farkı yalnız `doc/` altındaysa aynı sayılır (dondurma ve ölçüm kayıtları).

Sonuç: öncesi ve sonrası aynı.

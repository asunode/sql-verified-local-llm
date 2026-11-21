# Ölçüm dondurma kaydı (v4b) — 2026-11-21

Öncesi: 2026-11-21 09:28:53 +0300 · sonrası: 2026-11-21 09:29:25 +0300. Ham: `2026-11-21_v4b_dondurma_once.json`, `2026-11-21_v4b_dondurma_sonra.json`.

Değişiklik: 2026-11-21 v4 kaydından (8e393e9) sonra yalnız tercih eşleme düzeltmesi (T-58): atayici.py (aynı iki tercih AYNI_PIN, FAZLA_TERCIH arayüz toplamı), denetim.py (bir pin tek tercihi karşılar), kapsamli.py (aynı sayım; yeniden-ata komutu). İstem, şema, cagrilar.py, sozluk.py, kurallar ve tablolar v4 kaydıyla aynı. v4 Çağrı A çıktıları kayıttan geri verilerek atama yeniden üretilecek.

## Dosyalar (SHA-256)

| Dosya | Öncesi | Sonrası |
|---|---|---|
| `src/pinsecim/istemler/atama_sistem.txt` | `f09040e1f110af265f4f47e90193cf868b6cca5c504ccabe8741fe38b6bbfce6` | aynı |
| `src/pinsecim/istemler/ihtiyac_sistem.txt` | `2448539f4b39f296828427c67785388b8058782e2547bb63e14377218207c164` | aynı |
| `src/pinsecim/semalar.py` | `bd05406e8af7d2f45fbc0a4ed7c147e98739aae29332ef66e951bc0247d786ce` | aynı |
| `src/pinsecim/cagrilar.py` | `e1dfbd477ce82629fb88f6f1f8e611b684972e57146b1e334f591e3547b1d4b0` | aynı |
| `src/pinsecim/hat.py` | `20bb8fa41aebdcd0d3d8c662ac453a0d14f68f8d94f6219531d5a49d039073b7` | aynı |
| `src/pinsecim/denetim.py` | `60158f712538d5bc20476906eb71b7e8169398aaea3b33ae481976362f41a13f` | aynı |
| `src/pinsecim/atayici.py` | `a351da512a26e6d0505b31c4ff26b4cd27fc953ef9db705c9af338a18761122c` | aynı |
| `src/pinsecim/pinveri.py` | `6c115b1ef5e4e6393ed2f9b79653d1599d58d253bc21ae02b38ecc5ef1ba7c57` | aynı |
| `src/pinsecim/sozluk.py` | `914af6c5fc393c66baaba8f373a98f80ecbffd8fb28ca3ee85c8049b9bb3a8d6` | aynı |
| `src/pinsecim/kural_verisi.py` | `6a33a258b0174bd718317369dee2cbce1069f3fd66de2a0e62ae0a248a8fc007` | aynı |
| `setler/dogrulama/dogrulama_seti_v1.json` | `12211f6eccea718a80d8cce76813ae85a710a4048995334f4f8090677f393908` | aynı |
| `setler/gelistirme/gelistirme_seti.json` | `b5434c6d17ea5ef2bdf17c3968e5a5cba350babd45cf976883179131d0666f38` | aynı |
| `testler/veri/denetim_vakalari.json` | `0a1422c966583a9896698aabf85425851a745323eb57d3e3c47876e0c602b727` | aynı |
| `src/pinsecim/kapsamli.py` | `975736f497ad7b1fec17cd04d5c665b907124dd545bb590ac40ff38415b179f3` | aynı |
| `src/pinsecim/__main__.py` | `9fb5fcbd9c09d86f4cb3555b2b4b7965680bdd8c8e364d62c33c354b07bff1c1` | aynı |
| `src/pinsecim/dogrulama.py` | `2ef72cedb3b320b114f94015b2b38296b41d100eb5d8841f457318e2ed1df2d6` | aynı |
| `sql/006_pin_tercihleri.sql` | `2e3cc8ff4172c17a5bd19a5363d3be3e800242bda66f21b190383b93fb9de151` | aynı |
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
| `sayi_sozcugu` | 27 | `d796bb6a9e9d1a62790f0cdde5cb7fa35af2a4382000cdf8bd5a79bbd8eb22ae` | aynı |
| `baglam_sozcugu` | 21 | `90f1c7e9b23dad3cd5d8b04329938b43a8c8bd18b72291a23685e94c8d8f7cc9` | aynı |
| `pin_bahsi_deseni` | 5 | `856b0320fec3e37097d9aff5ee233da9554f276ce80163ee7e4fdaa657ebaee4` | aynı |

## Commit

| Depo | Öncesi | Sonrası | Arada değişen dosyalar |
|---|---|---|---|
| localllm_ass1 | `88450d3` | `dcda8f3` | `doc/WORKLOG.md`, `doc/olcum/2026-11-21_v4b_dondurma.md`, `doc/olcum/2026-11-21_v4b_dondurma_once.json` |
| asu_llmcore | `41e2198` | `41e2198` | - |

Commit farkı yalnız `doc/` altındaysa aynı sayılır (dondurma ve ölçüm kayıtları).

Sonuç: öncesi ve sonrası aynı.

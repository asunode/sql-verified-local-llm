# Ölçüm dondurma kaydı (adim10a) — 2026-11-21

Öncesi: 2026-11-21 13:08:17 +0300 · sonrası: 2026-11-21 14:15:45 +0300. Ham: `2026-11-21_adim10a_dondurma_once.json`, `2026-11-21_adim10a_dondurma_sonra.json`.

Değişiklik: Adım 10a: adim10 kaydından (f83c622) sonra. Değişen: sozluk.py (Türkçe bileşik sayı ayrıştırıcı, arayüz eş adları), cagrilar.py (dayanak sözcük sınırı DAYANAK_SINIRI, tam sayıyla SAYI_UYUSMAZ, SAYI_YARIM uyarısı, diger_ifadeler dayanağı ve DIGER_IHTIYAC_IZI uyarısı, BAGLAM_KONUSUZ iletisi), semalar.py (diger_ifadeler), ihtiyac_sistem.txt (kural 4, bir örnek, örneklere alan), __main__.py (diger_ifadeler bölümü), cevap.py (eş adlar), kural_verisi.py/yukle.py/sql 008 (sayi_sozcugu.basamak, otuz–doksan, yüz, bin, sıfır, 'bir de/şey' istisnaları; on bir–on dokuz satırları kaldırıldı; arayuz_es_adi), kapsamli.py (tur dökümü, diger_ifadeler bölümü), dogrulama.py (tablo listesi). atayici.py, denetim.py, hat.py, pinveri.py, atama istemi aynı. Gerileme: v4 ve v3 yeniden koşulacak.

## Dosyalar (SHA-256)

| Dosya | Öncesi | Sonrası |
|---|---|---|
| `src/pinsecim/istemler/atama_sistem.txt` | `f09040e1f110af265f4f47e90193cf868b6cca5c504ccabe8741fe38b6bbfce6` | aynı |
| `src/pinsecim/istemler/ihtiyac_sistem.txt` | `3ff741e27c2e7b41c548d21d6dfc3e029af5b7ed9d785803875e474164f0775a` | aynı |
| `src/pinsecim/semalar.py` | `5d148ad28822df2ef48c27f432267ce0d238086a262dd0a5971f9f3a906af55f` | aynı |
| `src/pinsecim/cagrilar.py` | `466ae5267c65408539da70bcf3b30203bb7a7e498122bdd6632b38c580655739` | aynı |
| `src/pinsecim/hat.py` | `71e00885a2c1b59cd443be2dec4a432ae6142db3c1b0e3b6c237dba16e3de1d9` | aynı |
| `src/pinsecim/denetim.py` | `60158f712538d5bc20476906eb71b7e8169398aaea3b33ae481976362f41a13f` | aynı |
| `src/pinsecim/atayici.py` | `a351da512a26e6d0505b31c4ff26b4cd27fc953ef9db705c9af338a18761122c` | aynı |
| `src/pinsecim/pinveri.py` | `c9af6a9e3fec674af087d279dc970a0774e70f75295446fca957c7c5bba38bc8` | aynı |
| `src/pinsecim/sozluk.py` | `2bcfc1818d3c0f271bf24605df452d51a15b60503a1357f82cd92f730dffd856` | aynı |
| `src/pinsecim/kural_verisi.py` | `8daaff2653f95a439f90bb47b0f5a3b10cd4b6c51edca5333f81517657841348` | aynı |
| `setler/dogrulama/dogrulama_seti_v1.json` | `12211f6eccea718a80d8cce76813ae85a710a4048995334f4f8090677f393908` | aynı |
| `setler/gelistirme/gelistirme_seti.json` | `b5434c6d17ea5ef2bdf17c3968e5a5cba350babd45cf976883179131d0666f38` | aynı |
| `testler/veri/denetim_vakalari.json` | `0a1422c966583a9896698aabf85425851a745323eb57d3e3c47876e0c602b727` | aynı |
| `src/pinsecim/cevap.py` | `0d64c6338fd4a881196db6c0d69e23af3c8500419b436d6413fec95395665bd9` | aynı |
| `src/pinsecim/__main__.py` | `18fb73510803fcfaeb286c01d993b3fa4eea4fbd9c5cd19e0c4d63386804635d` | aynı |
| `src/pinsecim/kapsamli.py` | `bcca9d8e9456608dd3b3c6577f2e3d53b390362f043c2d43622f5cfc85130e55` | aynı |
| `src/pinsecim/dogrulama.py` | `0294dea3903c3ee428511d258a49e37bc3f780001f1b9e7b7b8192e2c7bcbb58` | aynı |
| `src/pinsecim/yukle.py` | `01648d8c97f96eb29c8dae909b4d974f09141fcfc8e17281babc9aad79d50974` | aynı |
| `sql/008_sayi_es_ad.sql` | `af0789e457f4b555bf47d18977720390906128015ee1257963b7fad90021129b` | aynı |
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
| `soru_konusu` | 8 | `9976083de60ef50386c1816f7962e0408adae20e5827922b4aa5b75ce539f8bc` | aynı |
| `durum_mesaji` | 12 | `b21051a3c13597cb224b1e1df75fcc1e4779d0b61bd5f6391a6bcd47165cbb7a` | aynı |
| `arayuz_es_adi` | 9 | `39c71d3a4c6e419e6bc2f22ec5e22cb842601d5e4e5cacc879fc1df8b64ab4ce` | aynı |

## Commit

| Depo | Öncesi | Sonrası | Arada değişen dosyalar |
|---|---|---|---|
| localllm_ass1 | `38301c8` | `97055e6` | `doc/olcum/2026-11-21_adim10_v3_sonuc.md`, `doc/olcum/2026-11-21_adim10a_dondurma.md`, `doc/olcum/2026-11-21_adim10a_dondurma_once.json`, `doc/olcum/iz/2026-11-21.jsonl` |
| asu_llmcore | `41e2198` | `41e2198` | - |

Commit farkı yalnız `doc/` altındaysa aynı sayılır (dondurma ve ölçüm kayıtları).

Sonuç: öncesi ve sonrası aynı.

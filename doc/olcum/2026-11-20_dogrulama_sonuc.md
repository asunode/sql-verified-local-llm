# Doğrulama ölçümü — 2026-11-20

Set `setler/dogrulama/dogrulama_seti_v1.json` (SHA-256 `12211f6eccea718a80d8cce76813ae85a710a4048995334f4f8090677f393908`), 30 istek. Model gemma4:12b-it-qat, CPU, temperature 0, seed 42, num_ctx 8192, think kapalı, sınır açık, en_cok_tur 3. İstemler: atama_sistem.txt f09040e1f110, atama_sistem_tablosuz.txt 873d3d28306d, ihtiyac_sistem.txt a091cdfe0aa4. Ham iz: `2026-11-20_dogrulama_ham.jsonl` (satır numaraları aşağıda). Dondurma: `2026-11-20_dogrulama_dondurma.md`.

Tanımlar:
- Çağrı A doğru: modelin durumu kabul seçeneklerinden birininkiyle aynı ve o seçeneğin ihtiyaclar'ı null değilse arayüz çoklu kümesi birebir.
- model_cikarimi doğru: kalem düzeyinde; en çok örtüşen kabul seçeneğinin çoklu kümesinden istekte_acik kalemler düşülür, kalan kümede karşılığı olan çıkarım kalemi doğru.
- Hakem: setteki beklenen ihtiyaçlarla kod atayıcı. A doğruysa eşleşen kabul seçeneği, değilse ilk 'tamam' seçeneği.
- Karar: Çağrı B'nin son turundaki `durum` (atandi / mumkun_degil / bilgi_yok).
- Uyarı farkı: model (ya da tablosuz) atamasının uyarı sayısı eksi aynı ihtiyaçlarla atayıcının uyarı sayısı; yalnız ikisi de `atandi` ve B denetimden geçtiyse.
- Süre: ortalama / ortanca / en uzun, saniye.

## Özet

| Ölçüt | Koşu 1 model | Koşu 2 atayıcı (A ihtiyaçlarıyla) | Koşu 3 tablosuz |
|---|---|---|---|
| Çağrı A doğru | 22/30 | (Koşu 1'in A'sı) | (Koşu 1'in A'sı) |
| model_cikarimi kalemi / doğru | 67 / 63 | - | - |
| B 1. turda geçti | 23 | - | 14 |
| B 2. turda geçti | 0 | - | 5 |
| B 3. turda geçti | 2 | - | 5 |
| KULLANICIYA | 0 | - | 1 |
| JSON_GECERSIZ | 0 | - | 0 |
| BILGI_YOK (bilgi_yok) | 0 | - | 0 |
| Çağrı A durdurduğu için B'ye gelmeyen | 5 | 5 | 5 |
| Mümkün/imkânsız kararı hakemle aynı | 23/25 | 23/25 | 22/25 |
| Kararı aynı (A'nın) ihtiyaçlarla atayıcıyla aynı | 25/25 | - | 24/25 |
| Uyarı farkı toplamı (model − atayıcı), istek sayısı | 0 (21 istek) | - | 39 (21 istek) |
| Süre A | 39.1 / 28.2 / 87.7 | - | - |
| Süre B | 90.5 / 52.4 / 470.9 | 0.0 / 0.0 / 0.0 | 141.4 / 55.1 / 589.4 |
| Süre toplam (A + B + atayıcı kıyası) | 114.5 / 66.7 / 558.2 | - | - |

## Çağrı A yanlışları (Koşu 1)

| İstek | Beklenen (kabul) | Verilen | İz |
|---|---|---|---|
| V04 | tamam [GPIO_IN GPIO_IN] | tamam [GPIO_IN] | `2026-11-20_dogrulama_ham.jsonl:4` |
| V12 | tamam [ADC ADC ADC ADC ADC LP_I2C WAKE WAKE] | tamam [ADC ADC ADC ADC ADC GPIO_IN GPIO_IN LP_I2C] | `2026-11-20_dogrulama_ham.jsonl:12` |
| V13 | tamam [ADC ADC ADC ADC LP_I2C WAKE WAKE] | tamam [ADC ADC ADC ADC GPIO_IN GPIO_IN LP_I2C] | `2026-11-20_dogrulama_ham.jsonl:13` |
| V15 | tamam [ADC ADC ADC ADC ADC] | desteklenmiyor [ADC ADC ADC ADC ADC] desteklenmeyen: ['JTAG pinleriyle hata ayıklama'] | `2026-11-20_dogrulama_ham.jsonl:15` |
| V16 | tamam [ADC ADC ADC ADC] | desteklenmiyor [ADC ADC ADC ADC] desteklenmeyen: ['JTAG pinleriyle hata ayıklama'] | `2026-11-20_dogrulama_ham.jsonl:16` |
| V23 | tamam [GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT] | tamam [GPIO_IN GPIO_OUT] | `2026-11-20_dogrulama_ham.jsonl:23` |
| V24 | tamam [GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT] | tamam [GPIO_IN GPIO_OUT] | `2026-11-20_dogrulama_ham.jsonl:24` |
| V30 | tamam [] | emin_degilim [-] | `2026-11-20_dogrulama_ham.jsonl:30` |

## model_cikarimi kalemleri (Koşu 1)

| İstek | Kalem | Doğru |
|---|---|---|
| V02 | 2 | 2 |
| V03 | 1 | 1 |
| V04 | 1 | 1 |
| V05 | 2 | 2 |
| V07 | 12 | 12 |
| V08 | 1 | 1 |
| V12 | 2 | 0 |
| V13 | 2 | 0 |
| V19 | 7 | 7 |
| V20 | 8 | 8 |
| V21 | 8 | 8 |
| V22 | 8 | 8 |
| V23 | 1 | 1 |
| V24 | 1 | 1 |
| V26 | 2 | 2 |
| V27 | 1 | 1 |
| V28 | 1 | 1 |
| V29 | 7 | 7 |

## Düzeltme turu: 1. turda hata alıp sonra geçenler — Koşu 1 model

| İstek | Geçtiği tur | Turların hata kodları | İz |
|---|---|---|---|
| V14 | 3 | CAKISMA,CAKISMA → CAKISMA,CAKISMA → - | `2026-11-20_dogrulama_ham.jsonl:14` |
| V20 | 3 | CAKISMA → PIN_FLASH → - | `2026-11-20_dogrulama_ham.jsonl:20` |

## Düzeltme turu: 1. turda hata alıp sonra geçenler — Koşu 3 tablosuz

| İstek | Geçtiği tur | Turların hata kodları | İz |
|---|---|---|---|
| V08 | 3 | PIN_UART0 → PIN_UART0 → - | `2026-11-20_dogrulama_ham.jsonl:68` |
| V09 | 2 | SABIT_PIN,SABIT_PIN → - | `2026-11-20_dogrulama_ham.jsonl:69` |
| V12 | 2 | SABIT_PIN,SABIT_PIN → - | `2026-11-20_dogrulama_ham.jsonl:72` |
| V14 | 3 | SABIT_PIN,SABIT_PIN → SABIT_PIN,SABIT_PIN → - | `2026-11-20_dogrulama_ham.jsonl:74` |
| V17 | 2 | ADET_ASIMI → - | `2026-11-20_dogrulama_ham.jsonl:77` |
| V19 | 3 | PIN_USB,PIN_USB,PIN_UART0,PIN_UART0 → PIN_FLASH,PIN_FLASH,PIN_FLASH,PIN_VDD_SPI,PIN_FLASH → - | `2026-11-20_dogrulama_ham.jsonl:79` |
| V21 | 3 | PIN_USB,PIN_USB,PIN_UART0,PIN_UART0,PIN_FLASH → PIN_FLASH,PIN_FLASH,PIN_FLASH → - | `2026-11-20_dogrulama_ham.jsonl:81` |
| V22 | 3 | PIN_UART0,PIN_UART0,PIN_FLASH → PIN_FLASH,PIN_FLASH,PIN_VDD_SPI → - | `2026-11-20_dogrulama_ham.jsonl:82` |
| V25 | 2 | SABIT_PIN,SABIT_PIN → - | `2026-11-20_dogrulama_ham.jsonl:85` |
| V29 | 2 | ADET_ASIMI → - | `2026-11-20_dogrulama_ham.jsonl:89` |

## Mümkün/imkânsız uyuşmazlıkları — Koşu 1 model

| İstek | Karar | Hakem | Hakemin nedeni | İz |
|---|---|---|---|---|
| V12 | atandi | mumkun_degil | PIN: ADC(adc_1), ADC(adc_2), ADC(adc_3), ADC(adc_4), ADC(adc_5), LP_I2C(lp_i2c_1), WAKE(wake_1), WAKE(wake_2) için 9 sinyale yalnız 8 uygun pin var (GPIO0, GPIO1, GPIO2, GPIO3, GPIO4, GPIO5, GPIO6, GPIO7; QFN32) | `2026-11-20_dogrulama_ham.jsonl:12` |
| V23 | atandi | mumkun_degil | PIN: GPIO_IN(gpio_in_1), GPIO_IN(gpio_in_2), GPIO_IN(gpio_in_3), GPIO_IN(gpio_in_4), GPIO_IN(gpio_in_5), GPIO_IN(gpio_in_6), GPIO_IN(gpio_in_7), GPIO_IN(gpio_in_8), GPIO_IN(gpio_in_9), GPIO_OUT(gpio_out_1), GPIO_OUT(gpio_out_10), GPIO_OUT(gpio_out_2), GPIO_OUT(gpio_out_3), GPIO_OUT(gpio_out_4), GPIO_OUT(gpio_out_5), GPIO_OUT(gpio_out_6), GPIO_OUT(gpio_out_7), GPIO_OUT(gpio_out_8), GPIO_OUT(gpio_out_9) için 19 sinyale yalnız 18 uygun pin var (GPIO0, GPIO1, GPIO2, GPIO3, GPIO4, GPIO5, GPIO6, GPIO7, GPIO8, GPIO9, GPIO14, GPIO15, GPIO18, GPIO19, GPIO20, GPIO21, GPIO22, GPIO23; QFN32) | `2026-11-20_dogrulama_ham.jsonl:23` |

## Mümkün/imkânsız uyuşmazlıkları — Koşu 2 atayıcı (A ihtiyaçlarıyla)

| İstek | Karar | Hakem | Hakemin nedeni | İz |
|---|---|---|---|---|
| V12 | atandi | mumkun_degil | PIN: ADC(adc_1), ADC(adc_2), ADC(adc_3), ADC(adc_4), ADC(adc_5), LP_I2C(lp_i2c_1), WAKE(wake_1), WAKE(wake_2) için 9 sinyale yalnız 8 uygun pin var (GPIO0, GPIO1, GPIO2, GPIO3, GPIO4, GPIO5, GPIO6, GPIO7; QFN32) | `2026-11-20_dogrulama_ham.jsonl:42` |
| V23 | atandi | mumkun_degil | PIN: GPIO_IN(gpio_in_1), GPIO_IN(gpio_in_2), GPIO_IN(gpio_in_3), GPIO_IN(gpio_in_4), GPIO_IN(gpio_in_5), GPIO_IN(gpio_in_6), GPIO_IN(gpio_in_7), GPIO_IN(gpio_in_8), GPIO_IN(gpio_in_9), GPIO_OUT(gpio_out_1), GPIO_OUT(gpio_out_10), GPIO_OUT(gpio_out_2), GPIO_OUT(gpio_out_3), GPIO_OUT(gpio_out_4), GPIO_OUT(gpio_out_5), GPIO_OUT(gpio_out_6), GPIO_OUT(gpio_out_7), GPIO_OUT(gpio_out_8), GPIO_OUT(gpio_out_9) için 19 sinyale yalnız 18 uygun pin var (GPIO0, GPIO1, GPIO2, GPIO3, GPIO4, GPIO5, GPIO6, GPIO7, GPIO8, GPIO9, GPIO14, GPIO15, GPIO18, GPIO19, GPIO20, GPIO21, GPIO22, GPIO23; QFN32) | `2026-11-20_dogrulama_ham.jsonl:53` |

## Mümkün/imkânsız uyuşmazlıkları — Koşu 3 tablosuz

| İstek | Karar | Hakem | Hakemin nedeni | İz |
|---|---|---|---|---|
| V12 | atandi | mumkun_degil | PIN: ADC(adc_1), ADC(adc_2), ADC(adc_3), ADC(adc_4), ADC(adc_5), LP_I2C(lp_i2c_1), WAKE(wake_1), WAKE(wake_2) için 9 sinyale yalnız 8 uygun pin var (GPIO0, GPIO1, GPIO2, GPIO3, GPIO4, GPIO5, GPIO6, GPIO7; QFN32) | `2026-11-20_dogrulama_ham.jsonl:72` |
| V20 | atandi | mumkun_degil | PIN: GPIO_IN(gpio_in_1), GPIO_IN(gpio_in_2), GPIO_IN(gpio_in_3), GPIO_OUT(gpio_out_1), GPIO_OUT(gpio_out_2), GPIO_OUT(gpio_out_3), GPIO_OUT(gpio_out_4), GPIO_OUT(gpio_out_5), I2C(i2c_1), PWM(pwm_1), PWM(pwm_2), PWM(pwm_3), PWM(pwm_4), SPI(spi_1), UART(uart_1) için 20 sinyale yalnız 19 uygun pin var (GPIO0, GPIO1, GPIO2, GPIO3, GPIO4, GPIO5, GPIO6, GPIO7, GPIO8, GPIO9, GPIO10, GPIO11, GPIO15, GPIO18, GPIO19, GPIO20, GPIO21, GPIO22, GPIO23; QFN40) | `2026-11-20_dogrulama_ham.jsonl:80` |
| V23 | atandi | mumkun_degil | PIN: GPIO_IN(gpio_in_1), GPIO_IN(gpio_in_2), GPIO_IN(gpio_in_3), GPIO_IN(gpio_in_4), GPIO_IN(gpio_in_5), GPIO_IN(gpio_in_6), GPIO_IN(gpio_in_7), GPIO_IN(gpio_in_8), GPIO_IN(gpio_in_9), GPIO_OUT(gpio_out_1), GPIO_OUT(gpio_out_10), GPIO_OUT(gpio_out_2), GPIO_OUT(gpio_out_3), GPIO_OUT(gpio_out_4), GPIO_OUT(gpio_out_5), GPIO_OUT(gpio_out_6), GPIO_OUT(gpio_out_7), GPIO_OUT(gpio_out_8), GPIO_OUT(gpio_out_9) için 19 sinyale yalnız 18 uygun pin var (GPIO0, GPIO1, GPIO2, GPIO3, GPIO4, GPIO5, GPIO6, GPIO7, GPIO8, GPIO9, GPIO14, GPIO15, GPIO18, GPIO19, GPIO20, GPIO21, GPIO22, GPIO23; QFN32) | `2026-11-20_dogrulama_ham.jsonl:83` |

## Uyarı sayısı (istek başına; model / atayıcı → fark)

| İstek | Koşu 1 model | Koşu 3 tablosuz |
|---|---|---|
| V01 | 0 / 0 → 0 | 2 / 0 → 2 |
| V02 | 0 / 0 → 0 | 0 / 0 → 0 |
| V03 | 0 / 0 → 0 | 3 / 0 → 3 |
| V04 | 0 / 0 → 0 | 0 / 0 → 0 |
| V05 | 0 / 0 → 0 | 0 / 0 → 0 |
| V06 | 0 / 0 → 0 | 4 / 0 → 4 |
| V07 | 0 / 0 → 0 | 8 / 0 → 8 |
| V08 | 0 / 0 → 0 | 4 / 0 → 4 |
| V09 | 0 / 0 → 0 | 0 / 0 → 0 |
| V12 | 4 / 4 → 0 | 7 / 4 → 3 |
| V13 | 2 / 2 → 0 | 6 / 2 → 4 |
| V18 | 2 / 2 → 0 | 8 / 2 → 6 |
| V19 | 9 / 9 → 0 | 9 / 9 → 0 |
| V21 | 10 / 10 → 0 | 10 / 10 → 0 |
| V22 | 10 / 10 → 0 | 11 / 10 → 1 |
| V23 | 0 / 0 → 0 | 0 / 0 → 0 |
| V24 | 0 / 0 → 0 | 0 / 0 → 0 |
| V25 | 2 / 2 → 0 | 6 / 2 → 4 |
| V26 | 0 / 0 → 0 | 0 / 0 → 0 |
| V27 | 0 / 0 → 0 | 0 / 0 → 0 |
| V28 | 0 / 0 → 0 | 0 / 0 → 0 |

## Tablosuz model: ilk turdaki hata kodları

B çalışan 25 istek; 1. turda hatasız geçen 14.

| Kod | İhlal sayısı | İstek sayısı |
|---|---|---|
| PIN_UART0 | 9 | 5 |
| SABIT_PIN | 8 | 4 |
| PIN_USB | 6 | 3 |
| PIN_FLASH | 3 | 3 |
| ADET_ASIMI | 2 | 2 |

## Tekrarlanabilirlik (Koşu 1'in ilk 10 isteği yeniden)

| İstek | A ham aynı | B ham aynı | İz (Koşu 1 / tekrar) |
|---|---|---|---|
| V01 | = | = | `2026-11-20_dogrulama_ham.jsonl:1` / `2026-11-20_dogrulama_ham.jsonl:91` |
| V02 | = | = | `2026-11-20_dogrulama_ham.jsonl:2` / `2026-11-20_dogrulama_ham.jsonl:92` |
| V03 | = | = | `2026-11-20_dogrulama_ham.jsonl:3` / `2026-11-20_dogrulama_ham.jsonl:93` |
| V04 | = | = | `2026-11-20_dogrulama_ham.jsonl:4` / `2026-11-20_dogrulama_ham.jsonl:94` |
| V05 | = | = | `2026-11-20_dogrulama_ham.jsonl:5` / `2026-11-20_dogrulama_ham.jsonl:95` |
| V06 | = | = | `2026-11-20_dogrulama_ham.jsonl:6` / `2026-11-20_dogrulama_ham.jsonl:96` |
| V07 | = | = | `2026-11-20_dogrulama_ham.jsonl:7` / `2026-11-20_dogrulama_ham.jsonl:97` |
| V08 | = | = | `2026-11-20_dogrulama_ham.jsonl:8` / `2026-11-20_dogrulama_ham.jsonl:98` |
| V09 | = | = | `2026-11-20_dogrulama_ham.jsonl:9` / `2026-11-20_dogrulama_ham.jsonl:99` |
| V10 | = | - | `2026-11-20_dogrulama_ham.jsonl:10` / `2026-11-20_dogrulama_ham.jsonl:100` |

A ham aynı 10/10; B ham aynı 9/9 (B'nin çalıştığı istekler).

## Pipeline hataları

Yok.

## İstek ayrıntısı

| İstek | Paket | A doğru | A durumu | A ihtiyaçlar | B (model) | karar | B (tablosuz) | karar | hakem | süre A / B sn | İz (model) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| V01 | QFN32 | ✓ | tamam | I2C SPI | 1. turda geçti | atandi | 1. turda geçti | atandi | atandi | 67.57 / 65.96 | `2026-11-20_dogrulama_ham.jsonl:1` |
| V02 | QFN32 | ✓ | tamam | GPIO_IN GPIO_OUT | 1. turda geçti | atandi | 1. turda geçti | atandi | atandi | 20.56 / 30.42 | `2026-11-20_dogrulama_ham.jsonl:2` |
| V03 | QFN40 | ✓ | tamam | GPIO_OUT UART | 1. turda geçti | atandi | 1. turda geçti | atandi | atandi | 20.31 / 38.73 | `2026-11-20_dogrulama_ham.jsonl:3` |
| V04 | QFN32 | ✗ | tamam | GPIO_IN | 1. turda geçti | atandi | 1. turda geçti | atandi | atandi | 14.83 / 24.79 | `2026-11-20_dogrulama_ham.jsonl:4` |
| V05 | QFN40 | ✓ | tamam | ADC ADC GPIO_IN | 1. turda geçti | atandi | 1. turda geçti | atandi | atandi | 24.53 / 40.68 | `2026-11-20_dogrulama_ham.jsonl:5` |
| V06 | QFN40 | ✓ | tamam | PWM PWM PWM PWM PWM PWM | 1. turda geçti | atandi | 1. turda geçti | atandi | atandi | 43.07 / 52.37 | `2026-11-20_dogrulama_ham.jsonl:6` |
| V07 | QFN40 | ✓ | tamam | GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN GPIO_IN | 1. turda geçti | atandi | 1. turda geçti | atandi | atandi | 73.19 / 90.26 | `2026-11-20_dogrulama_ham.jsonl:7` |
| V08 | QFN32 | ✓ | tamam | GPIO_OUT SPI | 1. turda geçti | atandi | 3. turda geçti | atandi | atandi | 20.9 / 68.1 | `2026-11-20_dogrulama_ham.jsonl:8` |
| V09 | QFN40 | ✓ | tamam | WAKE WAKE | 1. turda geçti | atandi | 2. turda geçti | atandi | atandi | 20.83 / 34.88 | `2026-11-20_dogrulama_ham.jsonl:9` |
| V10 | QFN32 | ✓ | desteklenmiyor | I2C | B'ye gelmedi | - | - | - | - | 16.21 / - | `2026-11-20_dogrulama_ham.jsonl:10` |
| V11 | QFN40 | ✓ | desteklenmiyor | TWAI | B'ye gelmedi | - | - | - | - | 15.01 / - | `2026-11-20_dogrulama_ham.jsonl:11` |
| V12 | QFN32 | ✗ | tamam | ADC ADC ADC ADC ADC GPIO_IN GPIO_IN LP_I2C | 1. turda geçti | atandi | 2. turda geçti | atandi | mumkun_degil | 54.04 / 70.25 | `2026-11-20_dogrulama_ham.jsonl:12` |
| V13 | QFN32 | ✗ | tamam | ADC ADC ADC ADC GPIO_IN GPIO_IN LP_I2C | 1. turda geçti | atandi | 1. turda geçti | atandi | atandi | 48.31 / 64.81 | `2026-11-20_dogrulama_ham.jsonl:13` |
| V14 | QFN40 | ✓ | tamam | ADC ADC ADC ADC ADC ADC ADC LP_UART | 3. turda geçti | mumkun_degil | 3. turda geçti | mumkun_degil | mumkun_degil | 50.54 / 262.62 | `2026-11-20_dogrulama_ham.jsonl:14` |
| V15 | QFN40 | ✗ | desteklenmiyor | ADC ADC ADC ADC ADC | B'ye gelmedi | - | - | - | mumkun_degil | 37.29 / - | `2026-11-20_dogrulama_ham.jsonl:15` |
| V16 | QFN40 | ✗ | desteklenmiyor | ADC ADC ADC ADC | B'ye gelmedi | - | - | - | atandi | 31.79 / - | `2026-11-20_dogrulama_ham.jsonl:16` |
| V17 | QFN32 | ✓ | tamam | UART UART | 1. turda geçti | mumkun_degil | 2. turda geçti | mumkun_degil | mumkun_degil | 19.75 / 34.17 | `2026-11-20_dogrulama_ham.jsonl:17` |
| V18 | QFN32 | ✓ | tamam | I2C SPI TWAI TWAI UART | 1. turda geçti | atandi | 1. turda geçti | atandi | atandi | 34.29 / 105.51 | `2026-11-20_dogrulama_ham.jsonl:18` |
| V19 | QFN40 | ✓ | tamam | GPIO_IN GPIO_IN GPIO_IN GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT I2C PWM PWM PWM PWM SPI UART | 1. turda geçti | atandi | 3. turda geçti | atandi | atandi | 82.27 / 174.83 | `2026-11-20_dogrulama_ham.jsonl:19` |
| V20 | QFN40 | ✓ | tamam | GPIO_IN GPIO_IN GPIO_IN GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT I2C PWM PWM PWM PWM SPI UART | 3. turda geçti | mumkun_degil | KULLANICIYA | atandi | mumkun_degil | 87.37 / 470.86 | `2026-11-20_dogrulama_ham.jsonl:20` |
| V21 | QFN40 | ✓ | tamam | GPIO_IN GPIO_IN GPIO_IN GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT I2C PWM PWM PWM PWM SPI UART | 1. turda geçti | atandi | 3. turda geçti | atandi | atandi | 87.74 / 182.39 | `2026-11-20_dogrulama_ham.jsonl:21` |
| V22 | QFN40 | ✓ | tamam | GPIO_IN GPIO_IN GPIO_IN GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT I2C PWM PWM PWM PWM SPI UART | 1. turda geçti | atandi | 3. turda geçti | atandi | atandi | 87.55 / 181.76 | `2026-11-20_dogrulama_ham.jsonl:22` |
| V23 | QFN32 | ✗ | tamam | GPIO_IN GPIO_OUT | 1. turda geçti | atandi | 1. turda geçti | atandi | mumkun_degil | 19.18 / 43.42 | `2026-11-20_dogrulama_ham.jsonl:23` |
| V24 | QFN32 | ✗ | tamam | GPIO_IN GPIO_OUT | 1. turda geçti | atandi | 1. turda geçti | atandi | atandi | 19.04 / 30.44 | `2026-11-20_dogrulama_ham.jsonl:24` |
| V25 | QFN40 | ✓ | tamam | I2C LP_I2C | 1. turda geçti | atandi | 2. turda geçti | atandi | atandi | 50.26 / 56.97 | `2026-11-20_dogrulama_ham.jsonl:25` |
| V26 | QFN32 | ✓ | tamam | GPIO_IN I2S_IN | 1. turda geçti | atandi | 1. turda geçti | atandi | atandi | 21.45 / 41.15 | `2026-11-20_dogrulama_ham.jsonl:26` |
| V27 | QFN40 | ✓ | tamam | ADC I2S_OUT | 1. turda geçti | atandi | 1. turda geçti | atandi | atandi | 22.19 / 45.92 | `2026-11-20_dogrulama_ham.jsonl:27` |
| V28 | QFN32 | ✓ | tamam | GPIO_IN | 1. turda geçti | atandi | 1. turda geçti | atandi | atandi | 15.17 / 24.53 | `2026-11-20_dogrulama_ham.jsonl:28` |
| V29 | QFN40 | ✓ | tamam | PWM PWM PWM PWM PWM PWM PWM | 1. turda geçti | mumkun_degil | 2. turda geçti | mumkun_degil | mumkun_degil | 45.06 / 26.11 | `2026-11-20_dogrulama_ham.jsonl:29` |
| V30 | QFN32 | ✗ | BILGI_YOK | - | B'ye gelmedi | - | - | - | - | 22.1 / - | `2026-11-20_dogrulama_ham.jsonl:30` |

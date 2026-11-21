# Geliştirme seti koşusu v0 — 2026-11-20

İstemler: atama_sistem.txt f09040e1f110, ihtiyac_sistem.txt a091cdfe0aa4. Sınır açık, en_cok_tur 3. Ham veri: `2026-11-20_gelistirme_v0.json`; izler `doc/olcum/iz/`.

- Çağrı A doğru: 20/20
- Çağrı B çalışan: 18; sonuç: 1. turda geçti: 18
- Model–atayıcı mümkün/imkânsız kararı aynı: 18/18
- Süre (sn): ortalama 66.7, en uzun 173.2

| İstek | A doğru | A durumu | A ihtiyaçlar | B sonucu | B tur | model kararı | atayıcı kararı | aynı | uyarı (model/atayıcı) | süre sn |
|---|---|---|---|---|---|---|---|---|---|---|
| G01 | ✓ | tamam | I2C SPI | GECTI | 1 | atandi | atandi | ✓ | 0/0 | 72.19 |
| G02 | ✓ | tamam | ADC ADC PWM | GECTI | 1 | atandi | atandi | ✓ | 0/0 | 68.52 |
| G03 | ✓ | tamam | UART WAKE | GECTI | 1 | atandi | atandi | ✓ | 0/0 | 60.4 |
| G04 | ✓ | tamam | GPIO_IN GPIO_IN I2S_IN | GECTI | 1 | atandi | atandi | ✓ | 0/0 | 75.11 |
| G05 | ✓ | tamam | GPIO_IN GPIO_IN GPIO_OUT GPIO_OUT GPIO_OUT GPIO_OUT | GECTI | 1 | atandi | atandi | ✓ | 0/0 | 97.41 |
| G06 | ✓ | tamam | TWAI TWAI UART | GECTI | 1 | atandi | atandi | ✓ | 0/0 | 78.0 |
| G07 | ✓ | tamam | TWAI TWAI TWAI | GECTI | 1 | mumkun_degil | mumkun_degil | ✓ | 0/0 | 50.14 |
| G08 | ✓ | tamam | ADC ADC ADC ADC ADC ADC ADC ADC | GECTI | 1 | mumkun_degil | mumkun_degil | ✓ | 0/0 | 76.4 |
| G09 | ✓ | desteklenmiyor | - | - | - | - | - | - | -/- | 10.44 |
| G10 | ✓ | desteklenmiyor | - | - | - | - | - | - | -/- | 10.09 |
| G11 | ✓ | tamam | I2C | GECTI | 1 | atandi | atandi | ✓ | 0/0 | 44.43 |
| G12 | ✓ | tamam | GPIO_OUT GPIO_OUT SPI | GECTI | 1 | atandi | atandi | ✓ | 0/0 | 79.19 |
| G13 | ✓ | tamam | PWM PWM PWM PWM PWM PWM | GECTI | 1 | atandi | atandi | ✓ | 0/0 | 91.39 |
| G14 | ✓ | tamam | PWM PWM PWM PWM PWM PWM PWM | GECTI | 1 | mumkun_degil | mumkun_degil | ✓ | 0/0 | 67.06 |
| G15 | ✓ | tamam | LP_I2C | GECTI | 1 | atandi | atandi | ✓ | 2/2 | 51.47 |
| G16 | ✓ | tamam | GPIO_IN GPIO_IN GPIO_OUT | GECTI | 1 | atandi | atandi | ✓ | 0/0 | 58.14 |
| G17 | ✓ | tamam | ADC ADC ADC ADC I2C PWM PWM SPI UART | GECTI | 1 | atandi | atandi | ✓ | 5/5 | 173.24 |
| G18 | ✓ | tamam | UART UART | GECTI | 1 | atandi | atandi | ✓ | 0/0 | 60.1 |
| G19 | ✓ | tamam | ADC | GECTI | 1 | atandi | atandi | ✓ | 0/0 | 42.15 |
| G20 | ✓ | tamam | GPIO_IN SPI | GECTI | 1 | atandi | atandi | ✓ | 0/0 | 68.92 |

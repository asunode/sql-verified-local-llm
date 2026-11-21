-- 002_kurallar.sql — pilot sözlüğü, datasheet adetleri, denetim kuralları ve yorum katmanı.
-- Olgu tabloları (001) değişmez. Kural verisi burada, kural mantığı kodda (src/pinsecim/denetim.py).
-- Tekrar çalıştırılabilir (IF NOT EXISTS).

-- Çevre birimi adetleri (datasheet'ten, sayfasıyla). dayanak: sayfadaki ifade ya da sayım yöntemi.
CREATE TABLE IF NOT EXISTS cevre_adet (
    id          serial PRIMARY KEY,
    aile        text NOT NULL,
    ad          text NOT NULL,                 -- UART, LP_UART, I2C, LP_I2C, SPI2, I2S, TWAI, LED_PWM, ADC, LP_GPIO
    adet        integer NOT NULL CHECK (adet >= 0),
    dayanak     text NOT NULL,
    kaynak_id   integer NOT NULL REFERENCES kaynak(id),
    sayfa       integer NOT NULL,
    referans    text NOT NULL,
    not_        text,
    UNIQUE (aile, ad)
);

-- Pilot arayüzleri. Sinyaller pilot tanımı; yönlendirme, sütun ve adet datasheet'ten.
CREATE TABLE IF NOT EXISTS arayuz_tanimi (
    id                 serial PRIMARY KEY,
    aile               text NOT NULL,
    arayuz             text NOT NULL,
    sinyaller          text[] NOT NULL,
    sinyal_kaynagi     text NOT NULL,          -- "pilot tanımı (Web AI), 2026-11-20"
    yonlendirme        text NOT NULL CHECK (yonlendirme IN ('GPIO_MATRISI', 'SABIT')),
    cevre_birim        text,                   -- Table 2-10/2-11 sütunu; NULL + GPIO_MATRISI: paketteki her GPIO
    adet_adi           text,                   -- cevre_adet.ad; NULL: adet sınırı yok
    adet_baglam_dusumu text,                   -- bu bağlam anahtarı true ise kullanılabilir adet 1 eksilir
    kaynak_id          integer NOT NULL REFERENCES kaynak(id),
    sayfa              integer NOT NULL,       -- yönlendirmenin kaynağı
    referans           text NOT NULL,
    not_               text,
    UNIQUE (aile, arayuz)
);

-- Sabit pin isteyen sinyaller: hangi olgu işlevine bağlı (gpio_islev.grup + islev_adi deseni).
CREATE TABLE IF NOT EXISTS arayuz_sinyal (
    id            serial PRIMARY KEY,
    aile          text NOT NULL,
    arayuz        text NOT NULL,
    sinyal        text NOT NULL,
    sabit_grup    text NOT NULL CHECK (sabit_grup IN ('IO_MUX', 'LP_IO_MUX', 'ANALOG')),
    islev_deseni  text NOT NULL,               -- LIKE deseni: 'ADC1_CH%', 'LP_GPIO%', 'LP_I2C_SDA'
    kaynak_id     integer NOT NULL REFERENCES kaynak(id),
    sayfa         integer NOT NULL,
    referans      text NOT NULL,
    UNIQUE (aile, arayuz, sinyal)
);

-- Denetim kuralları. kategori: pin (gpio_kisit türüne bağlı), yapisal, adet.
-- Seviye: baglam_anahtari NULL ise `seviye`; değilse bağlam true → seviye_dogru, false → seviye_yanlis.
CREATE TABLE IF NOT EXISTS kural (
    id               serial PRIMARY KEY,
    kod              text NOT NULL UNIQUE,
    kategori         text NOT NULL CHECK (kategori IN ('pin', 'yapisal', 'adet')),
    kisit_turu       text,                     -- gpio_kisit.kisit_turu (pin kuralları)
    baglam_anahtari  text,
    seviye           text CHECK (seviye IN ('hata', 'uyari')),
    seviye_dogru     text CHECK (seviye_dogru IN ('hata', 'uyari')),
    seviye_yanlis    text CHECK (seviye_yanlis IN ('hata', 'uyari')),
    mesaj            text NOT NULL,            -- İngilizce şablon: {gpio}, {sinyal}, {ihtiyac}, {arayuz}, {adet}, {kaynak}
    aciklama         text NOT NULL,
    kaynak_id        integer REFERENCES kaynak(id),
    sayfa            integer,
    referans         text NOT NULL,            -- datasheet bölümü ya da "pilot tanımı"
    veren            text NOT NULL,
    sira             integer NOT NULL,
    CHECK ((baglam_anahtari IS NULL AND seviye IS NOT NULL AND seviye_dogru IS NULL AND seviye_yanlis IS NULL)
        OR (baglam_anahtari IS NOT NULL AND seviye IS NULL AND seviye_dogru IS NOT NULL AND seviye_yanlis IS NOT NULL))
);

-- Olgu satırına bağlı yorum. Olgu satırı değişmez; bağ doğal anahtarla (yeniden yüklemede kimlik değişir).
CREATE TABLE IF NOT EXISTS yorum (
    id            serial PRIMARY KEY,
    olgu_tablo    text NOT NULL,
    olgu_anahtar  jsonb NOT NULL,              -- ör. {"paket": "QFN32", "pin_no": 9, "cevre_birim": "SPI2"}
    yorum         text NOT NULL,
    deger         jsonb NOT NULL,              -- makinenin kullanacağı yorum: {"gpio_no": 3}
    gerekce       text[] NOT NULL,
    kaynaklar     text[] NOT NULL,
    veren         text NOT NULL,
    tarih         date NOT NULL,
    kaynak_id     integer NOT NULL REFERENCES kaynak(id),
    UNIQUE (olgu_tablo, olgu_anahtar)
);

-- 004_istek_sozlugu.sql — Çağrı A'nın kod denetimi için istek sözlüğü (pilot tanımı, Türkçe).
-- sayi_sozcugu: dayanaktaki sayı ifadeleri (SAYI_UYUSMAZ). baglam_sozcugu: bağlam ifadelerinin konusu ve olumsuzluğu.
-- arayuz_tanimi.paylasimli_hat: tek kalemi birden çok cihazın paylaştığı hat; dayanaktaki sayı cihaz sayısıdır, adet değil.

CREATE TABLE IF NOT EXISTS sayi_sozcugu (
    id      serial PRIMARY KEY,
    ifade   text NOT NULL UNIQUE,                  -- küçük harf, sözcükler tek boşlukla
    deger   integer NOT NULL CHECK (deger >= 1),
    kaynak  text NOT NULL
);

CREATE TABLE IF NOT EXISTS baglam_sozcugu (
    id       serial PRIMARY KEY,
    tur      text NOT NULL CHECK (tur IN ('konu', 'olumsuz')),
    anahtar  text,                                  -- konu: bağlam anahtarı (usb_serial_jtag …); olumsuz: NULL
    desen    text NOT NULL,                         -- küçük harf; ifadenin içinde alt dize olarak aranır
    kaynak   text NOT NULL,
    UNIQUE (tur, desen),
    CHECK ((tur = 'konu') = (anahtar IS NOT NULL))
);

ALTER TABLE arayuz_tanimi ADD COLUMN IF NOT EXISTS paylasimli_hat boolean NOT NULL DEFAULT false;

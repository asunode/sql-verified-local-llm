-- 016_sayi_disi_sozcuk.sql — sayıdan sonra gelince o sayıyı cihaz sayısı olmaktan çıkaran sözcükler (Adım 12,
-- SPI_ADET_IZI). tur 'birim': ölçü ya da para birimi ("5 V", "500 TL"); tur 'hat': sayı hattı sayıyor, cihazı değil
-- ("bir SPI hattına"). bicim 'tam': sözcük birebir; 'onek': sözcük bu önekle başlıyor (Türkçe ek: "hattına").
-- harf_duyarli sözcük birebir harfle karşılaştırılır; öteki Türkçe küçük harfle.

CREATE TABLE IF NOT EXISTS sayi_disi_sozcuk (
    id            serial PRIMARY KEY,
    sozcuk        text NOT NULL,
    tur           text NOT NULL CHECK (tur IN ('birim', 'hat')),
    bicim         text NOT NULL CHECK (bicim IN ('tam', 'onek')),
    harf_duyarli  boolean NOT NULL DEFAULT false,
    kaynak        text NOT NULL,
    UNIQUE (sozcuk, tur)
);

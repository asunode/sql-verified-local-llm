-- 015_soru_sozcugu.sql — soru sözcükleri (Adım 11a). tur 'elektriksel': soruda geçerse cevaplayıcı, konu ne olursa
-- olsun, cevabın başına cevap.elektriksel_yok notunu koyar (elektriksel değerler yapılı tablolarda yok). harf_duyarli
-- sözcük (birim: mA, V …) birebir ve iki yanı harfle sınırlı aranır (önünde rakam olabilir: "20mA"); öteki sözcükler
-- Türkçe küçük harfle, solu sınırlı, bitişik ek serbest ("akımı").

CREATE TABLE IF NOT EXISTS soru_sozcugu (
    id            serial PRIMARY KEY,
    sozcuk        text NOT NULL UNIQUE,
    tur           text NOT NULL CHECK (tur IN ('elektriksel')),
    harf_duyarli  boolean NOT NULL DEFAULT false,
    kaynak        text NOT NULL
);

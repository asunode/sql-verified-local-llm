-- 008_sayi_es_ad.sql — bileşik sayı okuma ve arayüz eş adları (Adım 10a).
-- sayi_sozcugu.basamak: Türkçe sayı dizilişine giren tek sözcükler (birler: bir…dokuz, onlar: on…doksan, yuz, bin).
--   Bunlar büyük basamaktan küçüğe birleştirilir ("on altı" = 16, "iki yüz elli" = 250; bitişik "onaltı" da), "altı on"
--   birleşmez. basamak NULL olan satır kendi başına okunur ("düzine", "bir çift"); deger NULL: sayı değil ("bir de").
-- arayuz_es_adi: cevaplayıcının ve diger_ifadeler uyarısının tanıdığı arayüz eş adları (küçük harf). Kart bağlamı
--   sözlüğüyle çakışan ad girmez ("seri port", "programlama portu").

ALTER TABLE sayi_sozcugu ADD COLUMN IF NOT EXISTS basamak text CHECK (basamak IN ('birler', 'onlar', 'yuz', 'bin'));

CREATE TABLE IF NOT EXISTS arayuz_es_adi (
    id      serial PRIMARY KEY,
    es_ad   text NOT NULL UNIQUE,
    arayuz  text NOT NULL,
    kaynak  text NOT NULL
);

-- "sıfır" (0) da sayı sözcüğüdür; adet denetimi 0'ı kullanmaz.
ALTER TABLE sayi_sozcugu DROP CONSTRAINT IF EXISTS sayi_sozcugu_deger_check;
ALTER TABLE sayi_sozcugu ADD CONSTRAINT sayi_sozcugu_deger_check CHECK (deger >= 0);

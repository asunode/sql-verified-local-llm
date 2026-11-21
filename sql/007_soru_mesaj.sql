-- 007_soru_mesaj.sql — soru konuları ve kullanıcı mesajları (Adım 10, K-8).
-- soru_konusu: Çağrı A'nın sorulara bağladığı kapalı konu listesi. model_tanimi modele giden İngilizce tanımdır;
--   cevap_turu cevabın nereden geldiğini söyler (tablo: veritabanından; kart_verisi_yok: Adım 10b'ye kadar veri yok;
--   tabloda_yok: bu konu tablolarda yok). gereken: cevaplayıcının sorudan çıkarması gereken bilgi (gpio, arayuz) ya da NULL.
-- durum_mesaji: kullanıcıya gösterilen Türkçe mesajlar. Anahtar önekleri: durum.<Çağrı A durumu>, eksik.<neden kodu>,
--   cevap.<cevaplayıcı durumu>. model_tanimi yalnız eksik.* satırlarında dolu: modele giden İngilizce tanım.

CREATE TABLE IF NOT EXISTS soru_konusu (
    id           serial PRIMARY KEY,
    konu         text NOT NULL UNIQUE,
    model_tanimi text NOT NULL,
    cevap_turu   text NOT NULL CHECK (cevap_turu IN ('tablo', 'kart_verisi_yok', 'tabloda_yok')),
    gereken      text CHECK (gereken IN ('gpio', 'arayuz')),
    tablolar     text,
    sira         integer NOT NULL UNIQUE,
    kaynak       text NOT NULL
);

CREATE TABLE IF NOT EXISTS durum_mesaji (
    id            serial PRIMARY KEY,
    anahtar       text NOT NULL UNIQUE CHECK (anahtar ~ '^(durum|eksik|cevap)\.[A-Za-z_]+$'),
    mesaj_tr      text NOT NULL,
    ne_yazmali_tr text,
    ornek_tr      text,
    model_tanimi  text,
    kaynak        text NOT NULL,
    CHECK ((anahtar LIKE 'eksik.%') = (model_tanimi IS NOT NULL))
);

-- 010_kart.sql — kart düzeyi veri (Adım 10b). Taslak: doc/raporlar/adim10_rapor.md "Kart verisi için tablo taslağı".
-- kaynak.kaynak_turu: belgenin türü. Yalnız satici / topluluk / kullanici_envanteri kaynaklı satır dogrulanmadi sayılır.
-- dogrulama_durumu: kaynak_belge (üretici şematiği/belgesi) | elle_dogrulandi (Sinan, kartla) | dogrulanmadi.
-- Aynı kartın sürümleri ayrı kart satırıdır; kisa_ad komut satırındaki --kart adıdır.
-- modul_pin: modül pini → çip GPIO'su (modüllü kartlar); teyit_kaynak_id aynı eşlemeyi gösteren ikinci belge.
-- kart_pin: kart konnektöründeki sıra → etiket (şematikteki net adı) ve GPIO; gpio_no NULL: 5V, GND, 3V3, CHIP_PU …
-- kart_parca: kart üstü LED, WS2812, buton, USB, USB-UART köprüsü, şarj, flash.

-- ALTER yalnız sütun yoksa çalışır: varken kilit istemez (testlerin açık okuma işlemleriyle beklemesin).
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'kaynak' AND column_name = 'kaynak_turu') THEN
        ALTER TABLE kaynak ADD COLUMN kaynak_turu text NOT NULL DEFAULT 'uretici_belgesi'
            CHECK (kaynak_turu IN ('uretici_belgesi', 'uretici_semasi', 'uretici_sayfasi', 'satici', 'topluluk',
                                   'kullanici_envanteri'));
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS kart (
    id               serial PRIMARY KEY,
    kisa_ad          text NOT NULL UNIQUE,
    ad               text NOT NULL,
    surum            text,
    uretici          text,
    cip_id           integer NOT NULL REFERENCES cip(id),
    modul            text,                                   -- ör. ESP32-C6-WROOM-1; çıplak çipte NULL
    kaynak_id        integer NOT NULL REFERENCES kaynak(id),
    sayfa            integer,
    referans         text,
    dogrulama_durumu text NOT NULL CHECK (dogrulama_durumu IN ('kaynak_belge', 'elle_dogrulandi', 'dogrulanmadi')),
    not_             text,
    UNIQUE NULLS NOT DISTINCT (ad, surum)
);

CREATE TABLE IF NOT EXISTS modul_pin (
    modul            text NOT NULL,
    pin_no           integer NOT NULL,
    pin_adi          text NOT NULL,
    gpio_no          integer,
    kaynak_id        integer NOT NULL REFERENCES kaynak(id),
    sayfa            integer,
    referans         text,
    teyit_kaynak_id  integer REFERENCES kaynak(id),
    dogrulama_durumu text NOT NULL CHECK (dogrulama_durumu IN ('kaynak_belge', 'elle_dogrulandi', 'dogrulanmadi')),
    PRIMARY KEY (modul, pin_no)
);

CREATE TABLE IF NOT EXISTS kart_pin (
    id               serial PRIMARY KEY,
    kart_id          integer NOT NULL REFERENCES kart(id),
    konnektor        text NOT NULL,
    sira             integer NOT NULL,
    etiket           text NOT NULL,
    gpio_no          integer,
    kaynak_id        integer NOT NULL REFERENCES kaynak(id),
    sayfa            integer,
    referans         text,
    dogrulama_durumu text NOT NULL CHECK (dogrulama_durumu IN ('kaynak_belge', 'elle_dogrulandi', 'dogrulanmadi')),
    not_             text,
    UNIQUE (kart_id, konnektor, sira)
);

CREATE TABLE IF NOT EXISTS kart_parca (
    id               serial PRIMARY KEY,
    kart_id          integer NOT NULL REFERENCES kart(id),
    tur              text NOT NULL CHECK (tur IN ('led', 'ws2812', 'buton', 'usb', 'usb_uart', 'sarj', 'flash')),
    ad               text NOT NULL,                          -- şematikteki ad: D2, S1, J5
    gpio_no          integer,
    baglanti         text,                                   -- GPIO yoksa ya da ek ayrıntı: CHIP_PU, 3V3, CHRG …
    aktif_seviye     text CHECK (aktif_seviye IN ('yuksek', 'dusuk')),
    aciklama         text NOT NULL,
    kaynak_id        integer NOT NULL REFERENCES kaynak(id),
    sayfa            integer,
    referans         text,
    dogrulama_durumu text NOT NULL CHECK (dogrulama_durumu IN ('kaynak_belge', 'elle_dogrulandi', 'dogrulanmadi')),
    not_             text,
    UNIQUE (kart_id, ad)
);

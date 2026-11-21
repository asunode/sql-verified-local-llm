-- 001_sema.sql — donanım olgu tabloları (public şeması, sahip: donanim).
-- Yalnız OLGU: kaynak belge ne diyorsa o. Politika (yasak/uyarı) burada yok.
-- Her olgu satırı kaynağını taşır: kaynak_id, sayfa (basılı sayfa = PDF sayfası), referans ("Table 2-4", "2.3.5").
-- Tablolar çip ailesi ve paketle genel: başka çipler ve kartlar aynı tablolara girer.
-- Tekrar çalıştırılabilir (IF NOT EXISTS). donanim_okur'un SELECT yetkisi varsayılan yetkilerden gelir (Adım 0).

CREATE TABLE IF NOT EXISTS kaynak (
    id              serial PRIMARY KEY,
    belge           text NOT NULL,
    surum           text NOT NULL,
    yayin_tarihi    date NOT NULL,
    sha256          char(64) NOT NULL UNIQUE,
    dosya_yolu      text NOT NULL,
    url             text NOT NULL,
    indirme_zamani  timestamptz NOT NULL,
    sayfa_sayisi    integer NOT NULL CHECK (sayfa_sayisi > 0)
);

-- Kaynak belgenin sayfa başına düz metni (pdftotext -layout); tüm sayfalar.
CREATE TABLE IF NOT EXISTS ham_metin (
    kaynak_id   integer NOT NULL REFERENCES kaynak(id),
    sayfa       integer NOT NULL CHECK (sayfa > 0),
    metin       text NOT NULL,
    PRIMARY KEY (kaynak_id, sayfa)
);

CREATE TABLE IF NOT EXISTS paket (
    id          serial PRIMARY KEY,
    aile        text NOT NULL,                 -- çip ailesi, ör. ESP32-C6
    ad          text NOT NULL,                 -- QFN40, QFN32
    boyut       text,
    kaynak_id   integer NOT NULL REFERENCES kaynak(id),
    sayfa       integer NOT NULL,
    referans    text NOT NULL,
    UNIQUE (aile, ad)
);

-- Çip varyantı (sipariş kodu) ve paketi (Table 1-1).
CREATE TABLE IF NOT EXISTS cip (
    id              serial PRIMARY KEY,
    ad              text NOT NULL UNIQUE,      -- ESP32-C6, ESP32-C6FH4 …
    aile            text NOT NULL,
    paket_id        integer NOT NULL REFERENCES paket(id),
    gomulu_flash    text NOT NULL,             -- belgedeki gibi ("—", "4 MB (Quad SPI)")
    sicaklik        text,
    revizyon        text,
    dipnot          text,
    kaynak_id       integer NOT NULL REFERENCES kaynak(id),
    sayfa           integer NOT NULL,
    referans        text NOT NULL
);

-- Paketin fiziksel pinleri (Table 2-1 / 2-2).
CREATE TABLE IF NOT EXISTS pin (
    id                  serial PRIMARY KEY,
    paket_id            integer NOT NULL REFERENCES paket(id),
    pin_no              integer NOT NULL,
    pin_adi             text NOT NULL,
    pin_turu            text NOT NULL,         -- IO, Analog, Power, Power/IO (belgedeki gibi)
    gpio_no             integer,               -- IO MUX tablosundaki GPIO adı (Table 2-4 / 2-5); yoksa NULL
    guc                 text,                  -- "Pin Providing Power"
    reset_ayar          text,                  -- "At Reset" (IE, WPU, USB_PU …)
    reset_sonrasi_ayar  text,                  -- "After Reset"
    islev_kumeleri      text[] NOT NULL DEFAULT '{}',   -- IO MUX / LP IO MUX / Analog
    varsayilan_kume     text[] NOT NULL DEFAULT '{}',   -- kalın yazılan küme (varsayılan boot modunda varsayılan işlev)
    varsayilan_surme_ma integer,               -- dipnot 3: GPIO12/13 40 mA, diğerleri 20 mA (yalnız GPIO'su olan pinler)
    dipnot              text,
    kaynak_id           integer NOT NULL REFERENCES kaynak(id),
    sayfa               integer NOT NULL,
    referans            text NOT NULL,
    belirsiz            boolean NOT NULL DEFAULT false,
    not_                text,
    UNIQUE (paket_id, pin_no)
);

-- GPIO'nun önceden tanımlı işlevleri: IO MUX F0–F2 (Table 2-4/2-5, pakete göre), LP IO MUX F0–F1 (Table 2-7),
-- analog F0–F1 (Table 2-9). paket_id NULL: tablo pakete göre ayrılmıyor.
CREATE TABLE IF NOT EXISTS gpio_islev (
    id          serial PRIMARY KEY,
    aile        text NOT NULL,
    gpio_no     integer NOT NULL,
    paket_id    integer REFERENCES paket(id),
    grup        text NOT NULL CHECK (grup IN ('IO_MUX', 'LP_IO_MUX', 'ANALOG')),
    islev_no    integer NOT NULL CHECK (islev_no >= 0),
    islev_adi   text NOT NULL,
    tip         text,                          -- IO MUX türü: I/O/T, I1, O/T … (yalnız IO_MUX)
    varsayilan  boolean NOT NULL DEFAULT false, -- belgede kalın: varsayılan boot modunda varsayılan işlev
    tablo_adi   text,                          -- tablodaki IO adı (GPIO4, LP_GPIO4 …)
    kaynak_id   integer NOT NULL REFERENCES kaynak(id),
    sayfa       integer NOT NULL,
    referans    text NOT NULL,
    belirsiz    boolean NOT NULL DEFAULT false,
    not_        text
);
CREATE UNIQUE INDEX IF NOT EXISTS gpio_islev_tekil
    ON gpio_islev (aile, gpio_no, COALESCE(paket_id, 0), grup, islev_no);

-- Çevre birimi pin ataması (Table 2-10 / 2-11): her dolu hücre bir satır.
CREATE TABLE IF NOT EXISTS cevre_birim_sinyal (
    id           serial PRIMARY KEY,
    paket_id     integer NOT NULL REFERENCES paket(id),
    pin_no       integer NOT NULL,
    cevre_birim  text NOT NULL,                -- tablo sütunu: UART0, SPI2, ADC …
    hucre        text NOT NULL,                -- hücre metni olduğu gibi: "GPIO4 (P3)", "MTMS (P1)"
    sinyal       text,                         -- P1 sabit sinyal adı; GPIO matrisi hücresinde NULL
    gpio_no      integer,                      -- hücredeki GPIO (matris) ya da pinin GPIO'su (sabit)
    oncelik      text NOT NULL CHECK (oncelik IN ('P1', 'P2', 'P3', 'P4')),
    yonlendirme  text NOT NULL CHECK (yonlendirme IN ('IO_MUX_SABIT', 'LP_IO_MUX_SABIT', 'ANALOG_SABIT', 'GPIO_MATRISI')),
    kaynak_id    integer NOT NULL REFERENCES kaynak(id),
    sayfa        integer NOT NULL,
    referans     text NOT NULL,
    belirsiz     boolean NOT NULL DEFAULT false,
    not_         text,
    UNIQUE (paket_id, pin_no, cevre_birim)
);

-- GPIO kısıtları: datasheet'in saydığı önemli işlevler ve paket farkları. Politika değil, olgu.
CREATE TABLE IF NOT EXISTS gpio_kisit (
    id                serial PRIMARY KEY,
    aile              text NOT NULL,
    gpio_no           integer NOT NULL,
    paket_id          integer REFERENCES paket(id),    -- NULL: GPIO'nun bulunduğu tüm paketler
    kisit_turu        text NOT NULL CHECK (kisit_turu IN ('strapping', 'flash', 'usb_serial_jtag', 'jtag', 'uart0',
                                                          'vdd_spi', 'bu_pakette_yok')),
    oncelik           text CHECK (oncelik IN ('P3', 'P4')),   -- 2.3.5'teki çevre birimi önceliği
    aciklama          text NOT NULL,           -- kısa, kendi sözümüzle
    varsayilan_durum  text,                    -- ör. strapping varsayılanı (Table 3-1)
    kaynak_turu       text NOT NULL DEFAULT 'metin' CHECK (kaynak_turu IN ('metin', 'renk')),
    kaynak_id         integer NOT NULL REFERENCES kaynak(id),
    sayfa             integer NOT NULL,
    referans          text NOT NULL,
    belirsiz          boolean NOT NULL DEFAULT false,
    not_              text
);
CREATE UNIQUE INDEX IF NOT EXISTS gpio_kisit_tekil
    ON gpio_kisit (aile, gpio_no, COALESCE(paket_id, 0), kisit_turu);

-- Strapping pin değer kombinasyonları (Table 3-3).
CREATE TABLE IF NOT EXISTS strapping_kombinasyon (
    id            serial PRIMARY KEY,
    aile          text NOT NULL,
    islev         text NOT NULL,               -- boot_modu
    sonuc         text NOT NULL,               -- belgedeki satır adı
    pin_degerleri jsonb NOT NULL,              -- {"GPIO8": "Any value", "GPIO9": "1"}
    varsayilan    boolean NOT NULL DEFAULT false,
    dipnot        text,
    kaynak_id     integer NOT NULL REFERENCES kaynak(id),
    sayfa         integer NOT NULL,
    referans      text NOT NULL,
    UNIQUE (aile, islev, sonuc)
);

-- Çip ile harici flash arasındaki pin eşlemesi (Table 2-16).
CREATE TABLE IF NOT EXISTS flash_pin (
    id          serial PRIMARY KEY,
    paket_id    integer NOT NULL REFERENCES paket(id),
    pin_no      integer NOT NULL,
    pin_adi     text NOT NULL,
    gpio_no     integer,
    tek_spi     text,
    cift_spi    text,
    dortlu_spi  text,
    kaynak_id   integer NOT NULL REFERENCES kaynak(id),
    sayfa       integer NOT NULL,
    referans    text NOT NULL,
    UNIQUE (paket_id, pin_no)
);

-- Doğrulama kaydı: hangi tablo/sayfa, hangi yöntemle, sonuç.
CREATE TABLE IF NOT EXISTS dogrulama (
    id          serial PRIMARY KEY,
    kaynak_id   integer NOT NULL REFERENCES kaynak(id),
    tablo       text NOT NULL,                 -- veritabanı tablosu
    referans    text NOT NULL,                 -- belgedeki tablo/bölüm
    sayfa       integer NOT NULL,
    yontem      text NOT NULL CHECK (yontem IN ('A-B karsilastirma', 'A ic capraz denetim', 'gorsel denetim', 'sayim')),
    sonuc       text NOT NULL CHECK (sonuc IN ('uyumlu', 'fark var, karara baglandi')),
    ayrinti     text,
    tarih       date NOT NULL
);

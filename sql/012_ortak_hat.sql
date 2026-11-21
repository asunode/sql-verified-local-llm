-- 012_ortak_hat.sql — aynı hatta birden çok cihaz (L-1, Adım 10c). arayuz_tanimi.ortak_hat_secim: bu arayüzün birden
-- çok örneği tek hattı paylaşır; ilk örnek bütün sinyalleri alır, sonrakiler yalnız bu seçim sinyalini (SPI: CS).
-- Sınır, arayüzün adet satırından gelir (SPI2_CS: altı FSPICS pini). ALTER yalnız sütun yoksa çalışır.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'arayuz_tanimi' AND column_name = 'ortak_hat_secim') THEN
        ALTER TABLE arayuz_tanimi ADD COLUMN ortak_hat_secim text;
    END IF;
END $$;

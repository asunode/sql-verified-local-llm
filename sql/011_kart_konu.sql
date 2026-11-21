-- 011_kart_konu.sql — kart soruları veritabanından cevaplanır (Adım 10b): soru_konusu.cevap_turu'na 'kart';
-- durum_mesaji anahtarlarına 'not.' öneki (atama çıktısına düşülen notlar). Kısıtlar yalnız eskiyse değiştirilir.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'soru_konusu_cevap_turu_check'
                   AND pg_get_constraintdef(oid) LIKE '%''kart''%') THEN
        ALTER TABLE soru_konusu DROP CONSTRAINT IF EXISTS soru_konusu_cevap_turu_check;
        ALTER TABLE soru_konusu ADD CONSTRAINT soru_konusu_cevap_turu_check
            CHECK (cevap_turu IN ('tablo', 'kart', 'kart_verisi_yok', 'tabloda_yok'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'durum_mesaji_anahtar_check'
                   AND pg_get_constraintdef(oid) LIKE '%|not)%') THEN
        ALTER TABLE durum_mesaji DROP CONSTRAINT IF EXISTS durum_mesaji_anahtar_check;
        ALTER TABLE durum_mesaji ADD CONSTRAINT durum_mesaji_anahtar_check
            CHECK (anahtar ~ '^(durum|eksik|cevap|not)\.[A-Za-z_]+$');
    END IF;
END $$;

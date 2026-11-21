-- 013_kart_atama.sql — kart düzeyi atama (Adım 10c). kart_pin.tur: konnektor (başlık pini) | ped (lehim pedi; yalnız
-- konnektör pinleri yetmezse kullanılır). ALTER yalnız sütun yoksa çalışır.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'kart_pin' AND column_name = 'tur') THEN
        ALTER TABLE kart_pin ADD COLUMN tur text NOT NULL DEFAULT 'konnektor' CHECK (tur IN ('konnektor', 'ped'));
    END IF;
END $$;

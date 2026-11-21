-- 005_sayi_istisnasi.sql — sayı sözlüğünde istisna: deger NULL olan ifade sayı değildir ("çift yönlü").
-- Ayrıştırıcı en uzun eşleşmeyle ifadeyi tüketir ve sayı üretmez; içindeki sözcük ("çift") ayrıca sayılmaz.

ALTER TABLE sayi_sozcugu ALTER COLUMN deger DROP NOT NULL;

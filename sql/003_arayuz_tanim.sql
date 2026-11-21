-- 003_arayuz_tanim.sql — arayüzlerin isteme giren kısa tanımı (pilot tanımı, İngilizce).
ALTER TABLE arayuz_tanimi ADD COLUMN IF NOT EXISTS tanim text;

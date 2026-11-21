-- 009_es_ad_harf.sql — harfe duyarlı arayüz eş adı (Adım 10b): "CAN" yalnız büyük harfle yazıldıysa TWAI'dir
-- (Türkçe "can" sözcüğüyle karışmasın). harf_duyarli satırı metinde birebir aynı harflerle aranır.

ALTER TABLE arayuz_es_adi ADD COLUMN IF NOT EXISTS harf_duyarli boolean NOT NULL DEFAULT false;

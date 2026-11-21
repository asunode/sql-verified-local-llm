-- 006_pin_tercihleri.sql — pin bahisleri ve Türkçe kural mesajları (Adım 9, K-7).
-- pin_bahsi_deseni: metindeki GPIO bahislerini bulan düzenli ifadeler. Desenler Türkçe küçük harfe çevrilmiş ve
--   "ı" → "i" yapılmış metne uygulanır; 1. yakalama grubu GPIO numarasıdır.
--   gpio: GPIO bahsi ("GPIO5", "gpıo11", "IO4"). liste_devami: bir bahsin hemen ardından gelen çıplak sayı
--   ("GPIO19, 18, 20 ve 21"); bir önceki bahsin bittiği yerden eşlenir. belirsiz: GPIO numarası olmayan pin bahsi
--   ("5 numaralı pin", "pin 5"); kullanıcıya uyarı, tercihe bağlanamaz.
-- kural.mesaj_tr: kullanıcıya gösterilen Türkçe mesaj; modele giden İngilizce `mesaj` aynı kalır.

CREATE TABLE IF NOT EXISTS pin_bahsi_deseni (
    id        serial PRIMARY KEY,
    tur       text NOT NULL CHECK (tur IN ('gpio', 'liste_devami', 'belirsiz')),
    desen     text NOT NULL UNIQUE,
    aciklama  text NOT NULL,
    kaynak    text NOT NULL
);

ALTER TABLE kural ADD COLUMN IF NOT EXISTS mesaj_tr text;

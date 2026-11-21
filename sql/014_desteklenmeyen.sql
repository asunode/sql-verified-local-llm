-- 014_desteklenmeyen.sql — desteklenmeyen özellikler (Adım 11a). Datasheet'in çevre birimi listelerinde bulunmayan
-- özellikler; Çağrı A denetimi (DESTEKLENMEYEN_OZELLIK) bir ihtiyacın dayanağında ya da dayanağın cümlesinde bu adları
-- arar. es_adlar harfe duyarsız (küçük harf), harf_duyarli_adlar metinde birebir aranır. Kaynak: listelendiği bölüm ve
-- "bu listede yok".

CREATE TABLE IF NOT EXISTS desteklenmeyen_ozellik (
    id                  serial PRIMARY KEY,
    aile                text NOT NULL,
    terim               text NOT NULL UNIQUE,
    es_adlar            text[] NOT NULL,
    harf_duyarli_adlar  text[] NOT NULL DEFAULT '{}',
    aciklama_tr         text NOT NULL,
    kaynak_id           integer NOT NULL REFERENCES kaynak(id),
    sayfa               integer NOT NULL,
    referans            text NOT NULL
);

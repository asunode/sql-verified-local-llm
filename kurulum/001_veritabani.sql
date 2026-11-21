-- 001_veritabani.sql — veritabanı ve iki rol (şifresiz). Süper kullanıcıyla bir kez çalıştırılır:
--     psql -U postgres -v ON_ERROR_STOP=1 -f kurulum/001_veritabani.sql
--     psql -U postgres -v ON_ERROR_STOP=1 -v veritabani=donanim_test -f kurulum/001_veritabani.sql   # ayrı ad
-- Roller: donanim (tabloların sahibi; yükleyici yazar), donanim_okur (uygulama; yalnız SELECT).
-- Şifreler bu dosyada yok: psql'de \password donanim ve \password donanim_okur ile verilir, ~/.pgpass'e yazılır
-- (README). Tablolar burada değil, yükleyicide kurulur (python -m pinsecim.yukle; sql/0*.sql).

\if :{?veritabani}
\else
\set veritabani donanim
\endif

SELECT 'CREATE ROLE donanim LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'donanim') \gexec
SELECT 'CREATE ROLE donanim_okur LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'donanim_okur') \gexec

-- Sıralama C.UTF-8 (builtin): CSV dışa aktarımlarının sırası yerel ayara bağlı kalmasın (PostgreSQL 17+).
CREATE DATABASE :"veritabani" OWNER donanim ENCODING 'UTF8' LOCALE_PROVIDER builtin BUILTIN_LOCALE 'C.UTF-8'
    LOCALE 'C.UTF-8' TEMPLATE template0;
REVOKE ALL ON DATABASE :"veritabani" FROM PUBLIC;              -- bağlanma ve geçici tablo yalnız iki role
GRANT CONNECT ON DATABASE :"veritabani" TO donanim_okur;

\connect :"veritabani"
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO donanim_okur;
ALTER DEFAULT PRIVILEGES FOR ROLE donanim IN SCHEMA public GRANT SELECT ON TABLES TO donanim_okur;
ALTER DEFAULT PRIVILEGES FOR ROLE donanim IN SCHEMA public GRANT SELECT ON SEQUENCES TO donanim_okur;

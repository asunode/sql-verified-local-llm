"""Veritabanı bağlantı ayarları (yayın kopyası). Varsayılan: 127.0.0.1:5432, veritabanı `donanim`; roller `donanim`
(yükleme) ve `donanim_okur` (uygulama). Ortam değişkenleriyle değiştirilebilir (ör. ayrı bir test veritabanı):
PINSECIM_PGHOST, PINSECIM_PGPORT, PINSECIM_VERITABANI. Şifre koda ya da ortama yazılmaz: libpq ~/.pgpass'ten (ya da
PGPASSFILE'dan) okur.
"""

from __future__ import annotations

import os
from pathlib import Path

HOST = os.environ.get("PINSECIM_PGHOST", "127.0.0.1")
PORT = int(os.environ.get("PINSECIM_PGPORT", "5432"))
VERITABANI = os.environ.get("PINSECIM_VERITABANI", "donanim")
SIFRE_DOSYASI = os.environ.get("PGPASSFILE") or str(Path.home() / ".pgpass")


def adres() -> dict:
    """PgOkuyucu'ya verilecek host ve port."""
    return {"host": HOST, "port": PORT}


def dsn(rol: str, uygulama: str | None = None) -> str:
    """psycopg bağlantı dizesi (şifresiz; şifre dosyasından)."""
    ek = f" application_name={uygulama}" if uygulama else ""
    return f"host={HOST} port={PORT} dbname={VERITABANI} user={rol} passfile={SIFRE_DOSYASI}{ek}"

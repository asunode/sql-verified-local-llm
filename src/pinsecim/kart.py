"""Kart düzeyi veri okuması (Adım 10b; veritabanından, donanim_okur): kartlar, kart pinleri, kart üstü parçalar, modül
pinleri. Komut satırındaki --kart adını kart satırına eşler; paket karttan (çip → paket) türetilir.
Tablolar `sql/010_kart.sql`; veri `kart_verisi.py`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from asu_llmcore import PgHatasi, PgOkuyucu

from . import baglanti as baglanti_ayari
from .pinveri import VeriHatasi

DURUM_ETIKETI = {"kaynak_belge": "kaynak belgede", "elle_dogrulandi": "elle doğrulandı",
                 "dogrulanmadi": "DOĞRULANMADI"}


class KartHatasi(VeriHatasi):
    """--kart adı bulunamadı, birden çok karta uyuyor ya da --paket ile çelişiyor."""


def kaynak_metni(r: dict) -> str:
    """Kart satırının kaynağı: belge, sürüm, referans, sayfa ve kaynak türü."""
    yer = ", ".join(x for x in (r.get("referans"), f"s. {r['sayfa']}" if r.get("sayfa") else None) if x)
    return f"{r['kaynak_belge']} {r['kaynak_surum']}" + (f", {yer}" if yer else "") + f" ({r['kaynak_turu']})"


def _anahtar(ad: str) -> str:
    return re.sub(r"[\s()_\-]", "", ad.lower())


@dataclass(frozen=True)
class KartVerisi:
    kartlar: list[dict]
    pinler: list[dict]
    parcalar: list[dict]
    modul_pinleri: list[dict]

    def bul(self, ad: str) -> dict:
        """--kart adı → kart satırı. Kısa ad ("SuperMini", "nanoESP32-C6-v0.2"), "ad (sürüm)" ya da tek sürümlü kartın
        adı kabul edilir; büyük/küçük harf, boşluk, tire ve ayraç yok sayılır."""
        a = _anahtar(ad)
        for k in self.kartlar:
            if a in (_anahtar(k["kisa_ad"]), _anahtar(k["ad"] + (k["surum"] or ""))):
                return k
        adla = [k for k in self.kartlar if _anahtar(k["ad"]) == a]
        if len(adla) == 1:
            return adla[0]
        liste = ", ".join(k["kisa_ad"] for k in (adla or self.kartlar))
        raise KartHatasi(f"'{ad}' {'birden çok karta uyuyor' if adla else 'adlı kart yok'}; seçenekler: {liste}")

    def pakete_uyan(self, paket: str) -> list[dict]:
        return [k for k in self.kartlar if k["paket"] == paket]

    def pinleri(self, kart: dict) -> list[dict]:
        return [p for p in self.pinler if p["kart_id"] == kart["id"]]

    def parcalari(self, kart: dict, turler: tuple[str, ...]) -> list[dict]:
        return [p for p in self.parcalar if p["kart_id"] == kart["id"] and p["tur"] in turler]

    def atama_bilgisi(self, kart: dict) -> dict:
        """Kart düzeyi atama için isteğe giren kart bilgisi (JSON'a yazılabilir; Adım 10c): konnektör ve ped pinleri
        (etiket "J1-4"), GPIO'ya bağlı kart üstü parçalar, USB-UART köprüleri; her satırda doğrulama durumu ve kaynak."""
        def kay(r):
            return {"durum": r["dogrulama_durumu"], "kaynak": kaynak_metni(r)}
        return {
            "kisa_ad": kart["kisa_ad"], **kay(kart),
            "pinler": [{"gpio": p["gpio_no"], "etiket": f"{p['konnektor']}-{p['sira']}", "tur": p["tur"], **kay(p)}
                       for p in self.pinleri(kart) if p["gpio_no"] is not None],
            "parcalar": [{"gpio": p["gpio_no"], "ad": p["ad"], "aciklama": p["aciklama"], "tur": p["tur"], **kay(p)}
                         for p in self.parcalari(kart, ("led", "ws2812", "buton")) if p["gpio_no"] is not None],
            "usb_uart": [{"ad": p["ad"], "aciklama": p["aciklama"], **kay(p)} for p in self.parcalari(kart, ("usb_uart",))],
        }

    def modul_kaynagi(self, modul: str) -> dict | None:
        return next((m for m in self.modul_pinleri if m["modul"] == modul), None)


_KAYNAK = "k.belge AS kaynak_belge, k.surum AS kaynak_surum, k.kaynak_turu"
SORGULAR = {
    "kart": f"SELECT x.id, x.kisa_ad, x.ad, x.surum, x.uretici, c.ad AS cip, p.ad AS paket, x.modul, x.sayfa, x.referans, "
            f"x.dogrulama_durumu, x.not_, {_KAYNAK} FROM kart x JOIN cip c ON c.id = x.cip_id "
            f"JOIN paket p ON p.id = c.paket_id JOIN kaynak k ON k.id = x.kaynak_id ORDER BY x.kisa_ad",
    "pin": f"SELECT x.kart_id, x.konnektor, x.sira, x.etiket, x.gpio_no, x.tur, x.sayfa, x.referans, x.dogrulama_durumu, "
           f"x.not_, {_KAYNAK} FROM kart_pin x JOIN kaynak k ON k.id = x.kaynak_id ORDER BY x.kart_id, x.konnektor, x.sira",
    "parca": f"SELECT x.kart_id, x.tur, x.ad, x.gpio_no, x.baglanti, x.aktif_seviye, x.aciklama, x.sayfa, x.referans, "
             f"x.dogrulama_durumu, x.not_, {_KAYNAK} FROM kart_parca x JOIN kaynak k ON k.id = x.kaynak_id "
             f"ORDER BY x.kart_id, x.tur, x.ad",
    "modul": f"SELECT x.modul, x.pin_no, x.pin_adi, x.gpio_no, x.sayfa, x.referans, x.dogrulama_durumu, {_KAYNAK}, "
             f"t.belge AS teyit_belge, t.surum AS teyit_surum FROM modul_pin x JOIN kaynak k ON k.id = x.kaynak_id "
             f"LEFT JOIN kaynak t ON t.id = x.teyit_kaynak_id ORDER BY x.modul, x.pin_no",
}


def yukle(rol: str = "donanim_okur", veritabani: str = baglanti_ayari.VERITABANI, **baglanti) -> KartVerisi:
    try:
        with PgOkuyucu(rol, veritabani, uygulama_adi="pinsecim_kart", **{**baglanti_ayari.adres(), **baglanti}) as db:
            r = {ad: db.sorgu(sql) for ad, sql in SORGULAR.items()}
    except PgHatasi as e:
        raise VeriHatasi(f"kart verisi okunamadı: {e}") from e
    if not r["kart"]:
        raise VeriHatasi("kart verisi eksik: kart tablosu boş")
    return KartVerisi(kartlar=r["kart"], pinler=r["pin"], parcalar=r["parca"], modul_pinleri=r["modul"])

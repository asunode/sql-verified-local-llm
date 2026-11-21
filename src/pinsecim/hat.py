"""Uçtan uca: Türkçe istek → (Çağrı A) ihtiyaçlar → kod atayıcı atama → denetim, iz (K-6).

Modelli atama (Çağrı B) yalnız `model_ata` ile çalışır; atayıcı o zaman kıyas için yanında koşar.
Çağrı A desteklenmiyor ya da emin_degilim dönerse (ya da geçmezse) atama yapılmaz. 'tamam' ve boş ihtiyaç
listesi: pin gerekmiyor, Çağrı B ve atayıcı çalışmaz. Kalemler adet kadar çoğaltılıp kimlik alır.
Atayıcının sonucu da denetlenir; orada çıkan hata yazılım hatasıdır (`yazilim_hatasi`).
Çağrı A'nın pin tercihleri ve kullanılmayacak pinleri isteğe girer (K-7). Atayıcı tercih_uygulanamadi derse asıl atama
yoktur; alternatif atama, uygulanan tercihlerle denetlenir (`alternatif_ihlaller`).
Çağrı A geçtiyse ayırdığı sorular, durumdan bağımsız, veritabanından cevaplanır (`cevaplar`, K-8). Atama yalnız
'tamam' ve dolu ihtiyaç listesiyle yapılır. 'tamam' dışındaki durumda kullanıcı mesajı (neden, ne yazmalı) ve
emin_degilim'in eksik kodlarının açıklamaları `durum_mesaji` tablosundan gelir (`bildirim`).
Kart (Adım 10b–10c): verilirse kart soruları o kartın verisiyle cevaplanır; atama kart düzeyindedir: isteğe kartın pin
ve parça bilgisi girer (`istek["kart"]`), atayıcı ve denetleyici onu kullanır; özet `atayici["kart_ozeti"]`.
"""

from __future__ import annotations

import dataclasses
import time
from pathlib import Path

from asu_llmcore import Durum, IzYazici, OllamaIstemcisi, Sonuc, kayit

from . import cagrilar, sozluk as sozluk_mod
from .atayici import Atayici
from .cevap import Cevaplayici
from .denetim import Denetleyici
from . import kart as kart_mod
from .kart import KartVerisi
from .pinveri import PinVerisi
from .sozluk import IstekSozlugu

KOK = Path(__file__).resolve().parents[2]
IZ_DIZINI = KOK / "doc" / "olcum" / "iz"


@dataclasses.dataclass
class HatSonucu:
    metin: str
    paket: str
    baglam: dict
    cagri_a: Sonuc
    istek: dict | None = None             # kimlikli ihtiyaçlarla atama isteği
    cagri_b: Sonuc | None = None
    atayici: dict | None = None           # kod atayıcı: {"atama", "neden", "uyarilar"}
    atama: dict | None = None             # gösterilen atama (model ya da atayıcı)
    ihlaller: list = dataclasses.field(default_factory=list)   # gösterilen atamanın denetimi
    alternatif_ihlaller: list = dataclasses.field(default_factory=list)   # tercih_uygulanamadi: alternatifin denetimi
    sure_sn: dict = dataclasses.field(default_factory=dict)
    atayan: str = "atayici"
    cevaplar: list = dataclasses.field(default_factory=list)     # soruların veritabanı cevapları (K-8)
    bildirim: dict | None = None          # 'tamam' değilse: {"durum": mesaj, "eksik": [mesaj, …]} (durum_mesaji)
    kart: dict | None = None              # --kart satırı (Adım 10b); atama kart düzeyinde (Adım 10c)

    @property
    def a_durumu(self) -> str:
        if self.cagri_a.durum is not Durum.GECTI:
            return self.cagri_a.durum.value
        return self.cagri_a.yanit["durum"]

    @property
    def pin_gerekmiyor(self) -> bool:
        return self.a_durumu == "tamam" and not self.cagri_a.yanit["ihtiyaclar"]

    @property
    def yazilim_hatasi(self) -> list:
        """Atayıcının atamasında (ya da alternatifinde) denetleyicinin bulduğu hatalar (sıfır beklenir)."""
        if self.atayan != "atayici":
            return []
        return [i for i in self.ihlaller + self.alternatif_ihlaller if i.seviye == "hata"]


def calistir(metin: str, paket: str, baglam: dict, veri: PinVerisi, istemci: OllamaIstemcisi | None = None,
             model_ata: bool = False, kiyas: bool = True, iz: Path | None = IZ_DIZINI, ek: dict | None = None,
             sozluk: IstekSozlugu | None = None, kart: dict | None = None,
             kartlar: KartVerisi | None = None) -> HatSonucu:
    """`model_ata`: atamayı Çağrı B yapar; `kiyas` (yalnız onunla anlamlı): atayıcı yanında koşar."""
    istemci = istemci or OllamaIstemcisi(cagrilar.ayar())
    sozluk = sozluk or sozluk_mod.yukle()
    t0 = time.monotonic()
    a = cagrilar.ihtiyac_cikar(istemci, veri, metin, sozluk, baglam)
    h = HatSonucu(metin, paket, baglam, a, sure_sn={"cagri_a": round(time.monotonic() - t0, 2)}, kart=kart)
    if kart is not None and kartlar is None:
        kartlar = kart_mod.yukle()
    if a.durum is Durum.GECTI and a.yanit.get("sorular"):
        cevaplayici = Cevaplayici(veri, sozluk, kartlar)
        h.cevaplar = [cevaplayici.cevapla(q, paket, baglam, kart) for q in a.yanit["sorular"]]
    if h.a_durumu != "tamam":
        h.bildirim = {"durum": _mesaj(sozluk, f"durum.{h.a_durumu}"),
                      "eksik": [_mesaj(sozluk, f"eksik.{e}") for e in (a.yanit or {}).get("eksik", [])
                                if a.durum is Durum.GECTI]}
    if a.durum is Durum.GECTI and a.yanit["durum"] == "tamam" and a.yanit["ihtiyaclar"]:
        h.istek = {"paket": paket, "baglam": baglam,
                   "ihtiyaclar": cagrilar.kimlik_ver(cagrilar.genislet(a.yanit["ihtiyaclar"])),
                   "pin_tercihleri": [{"arayuz": t["arayuz"], "sinyal": t["sinyal"], "gpio": t["gpio"]}
                                      for t in a.yanit.get("pin_tercihleri", [])],
                   "kullanilmayacak": sorted({p["gpio"] for p in a.yanit.get("kullanilmayacak_pinler", [])})}
        if kart is not None:                             # kart düzeyi atama (Adım 10c)
            h.istek["kart"] = kartlar.atama_bilgisi(kart)
        denetleyici = Denetleyici(veri)
        if model_ata:
            t1 = time.monotonic()
            h.cagri_b = cagrilar.pin_ata(istemci, veri, h.istek)
            h.sure_sn["cagri_b"] = round(time.monotonic() - t1, 2)
            h.atama, h.atayan = h.cagri_b.yanit, "model"
        if not model_ata or kiyas:
            t1 = time.monotonic()
            r = Atayici(veri).ata(h.istek)
            h.atayici = {"atama": r.atama, "neden": r.neden,
                         "uyarilar": [dataclasses.asdict(i) for i in denetleyici.denetle(h.istek, r.atama)],
                         "tercih_sorunlari": r.tercih_sorunlari, "uygulanan_tercihler": r.uygulanan_tercihler,
                         "alternatif": r.alternatif, "kart_ozeti": r.kart_ozeti}
            if r.alternatif is not None:
                h.alternatif_ihlaller = denetleyici.denetle({**h.istek, "pin_tercihleri": r.uygulanan_tercihler},
                                                            r.alternatif)
            h.sure_sn["atayici"] = round(time.monotonic() - t1, 3)
        if not model_ata:
            h.atama = h.atayici["atama"]
        if h.atama is not None and h.atama.get("durum") in ("atandi", "mumkun_degil", "bilgi_yok",
                                                            "tercih_uygulanamadi"):
            h.ihlaller = denetleyici.denetle(h.istek, h.atama)
    h.sure_sn["toplam"] = round(time.monotonic() - t0, 2)
    if iz is not None:
        iz_yaz(h, iz, ek)
    return h


def _mesaj(sozluk: IstekSozlugu, anahtar: str) -> dict:
    m = sozluk.mesaj(anahtar)
    return {"anahtar": anahtar, "mesaj": m["mesaj_tr"], "ne_yazmali": m["ne_yazmali_tr"], "ornek": m["ornek_tr"]}


def iz_yaz(h: HatSonucu, dizin: Path, ek: dict | None = None) -> Path:
    yol = dizin / f"{time.strftime('%Y-%m-%d')}.jsonl"
    ayar = cagrilar.ayar()
    IzYazici(yol).yaz({
        **(ek or {}), "zaman": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "metin": h.metin, "paket": h.paket,
        **({"kart": h.kart["kisa_ad"]} if h.kart else {}),
        "baglam": h.baglam, "atayan": h.atayan, "a_durumu": h.a_durumu,
        "cagri_a": kayit(h.cagri_a, ayar), "istek": h.istek,
        "cagri_b": kayit(h.cagri_b, ayar) if h.cagri_b else None, "atayici": h.atayici,
        "gosterilen_atama": h.atama, "ihlaller": [dataclasses.asdict(i) for i in h.ihlaller],
        "alternatif_ihlaller": [dataclasses.asdict(i) for i in h.alternatif_ihlaller],
        "yazilim_hatasi": [i.kod for i in h.yazilim_hatasi], "cevaplar": h.cevaplar, "bildirim": h.bildirim,
        "sure_sn": h.sure_sn,
    })
    return yol

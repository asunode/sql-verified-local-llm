"""Denetleyici ve atayıcının ortak verisi: olgular, kurallar, arayüzler, yorumlar (veritabanından, donanim_okur).

Ham satırlar `PinVerisi`'nde tutulur, türetilmiş yapılar onlardan kurulur. `yorumsuz()` aynı veriyi yorum
katmanı olmadan verir (belirsiz satırların yok sayıldığı durum).
"""

from __future__ import annotations

import dataclasses
import fnmatch
from dataclasses import dataclass, field

from asu_llmcore import PgHatasi, PgOkuyucu

from . import baglanti as baglanti_ayari
from .kararlar import AILE, KAYNAK


ADRES = "adres"                                   # ortak_hat_secim: cihazlar adresle ayrılır (I2C; Adım 11a)

class VeriHatasi(Exception):
    """Denetim verisi okunamadı (veritabanı yok, tablo boş vb.). Denetim sessizce atlanmaz."""


def kaynak_metni(referans: str | None, sayfa: int | None) -> str:
    belge = f"{KAYNAK['belge'].replace(' Series', '')} {KAYNAK['surum']}"
    if not referans:
        return belge
    return f"{belge}, {referans}" + (f" p.{sayfa}" if sayfa else "")


@dataclass(frozen=True)
class Kural:
    kod: str
    kategori: str
    kisit_turu: str | None
    baglam_anahtari: str | None
    seviye: str | None
    seviye_dogru: str | None
    seviye_yanlis: str | None
    mesaj: str
    mesaj_tr: str
    sayfa: int | None
    referans: str

    def seviye_icin(self, baglam: dict) -> str:
        if self.baglam_anahtari is None:
            return self.seviye
        return self.seviye_dogru if baglam[self.baglam_anahtari] else self.seviye_yanlis


@dataclass(frozen=True)
class Kaynakli:
    """Olgudan türeyen bir GPIO bilgisi ve kaynağı."""
    gpio: int
    sayfa: int
    referans: str


@dataclass
class PinVerisi:
    pin_satirlari: list[dict]
    kisit_satirlari: list[dict]
    islev_satirlari: list[dict]
    cevre_satirlari: list[dict]
    kurallar: dict[str, Kural]
    arayuzler: dict[str, dict]
    sabit_sinyaller: dict[tuple[str, str], dict]
    adetler: dict[str, dict]
    yorumlar: list[dict]
    # türetilmiş
    paket_gpio: dict[str, set[int]] = field(init=False)
    cip_gpio: set[int] = field(init=False)
    sutun: dict[tuple[str, str], dict[int, Kaynakli]] = field(init=False)
    belirsiz_yok_sayilan: dict[tuple[str, str], dict[int, Kaynakli]] = field(init=False)
    kullanilan_yorumlar: list[dict] = field(init=False)

    def __post_init__(self) -> None:
        self.paket_gpio = {}
        for r in self.pin_satirlari:
            if r["gpio_no"] is not None:
                self.paket_gpio.setdefault(r["paket"], set()).add(r["gpio_no"])
        if not self.paket_gpio:
            raise VeriHatasi("pin tablosunda GPIO yok")
        self.cip_gpio = set().union(*self.paket_gpio.values())
        pin_gpio = {(r["paket"], r["pin_no"]): r["gpio_no"] for r in self.pin_satirlari}
        yorum = {(y["olgu_tablo"], tuple(sorted(y["olgu_anahtar"].items()))): y for y in self.yorumlar}
        self.sutun, self.belirsiz_yok_sayilan, self.kullanilan_yorumlar = {}, {}, []
        for r in self.cevre_satirlari:
            anahtar = (r["paket"], r["cevre_birim"])
            gpio, sayfa, ref = r["gpio_no"], r["sayfa"], r["referans"]
            if r["belirsiz"]:
                y = yorum.get(("cevre_birim_sinyal", tuple(sorted(
                    {"paket": r["paket"], "pin_no": r["pin_no"], "cevre_birim": r["cevre_birim"]}.items()))))
                if y is None:
                    g = pin_gpio[(r["paket"], r["pin_no"])]
                    self.belirsiz_yok_sayilan.setdefault(anahtar, {})[g] = Kaynakli(g, sayfa, ref)
                    continue
                gpio = y["deger"]["gpio_no"]
                ref = f"{ref} (yorum: {y['veren']})"
                self.kullanilan_yorumlar.append(y)
            self.sutun.setdefault(anahtar, {})[gpio] = Kaynakli(gpio, sayfa, ref)

    def yorumsuz(self) -> "PinVerisi":
        alanlar = {f.name: getattr(self, f.name) for f in dataclasses.fields(self) if f.init}
        return PinVerisi(**{**alanlar, "yorumlar": []})

    # --- sorgular ---
    def kisitlar(self, paket: str, gpio: int) -> list[dict]:
        return [k for k in self.kisit_satirlari if k["gpio_no"] == gpio and k["paket"] in (None, paket)]

    def sabit_izinli(self, paket: str, arayuz: str, sinyal: str) -> dict[int, Kaynakli] | None:
        """Sabit pinli sinyal için izinli GPIO'lar (paketteki), değilse None."""
        s = self.sabit_sinyaller.get((arayuz, sinyal))
        if s is None:
            return None
        izinli = {}
        for r in self.islev_satirlari:
            if r["grup"] == s["sabit_grup"] and r["paket"] in (None, paket) \
                    and fnmatch.fnmatchcase(r["islev_adi"], s["islev_deseni"].replace("%", "*")) \
                    and r["gpio_no"] in self.paket_gpio[paket]:
                izinli[r["gpio_no"]] = Kaynakli(r["gpio_no"], r["sayfa"], r["referans"])
        return izinli

    def sabit_islev_adlari(self, paket: str, arayuz: str, sinyal: str) -> dict[int, str]:
        s = self.sabit_sinyaller[(arayuz, sinyal)]
        return {r["gpio_no"]: r["islev_adi"] for r in self.islev_satirlari
                if r["grup"] == s["sabit_grup"] and r["paket"] in (None, paket)
                and fnmatch.fnmatchcase(r["islev_adi"], s["islev_deseni"].replace("%", "*"))}

    def aday_gpio(self, paket: str, arayuz: str, sinyal: str) -> set[int]:
        """Sinyalin gidebileceği GPIO'lar (pin kuralları uygulanmadan)."""
        sabit = self.sabit_izinli(paket, arayuz, sinyal)
        if sabit is not None:
            return set(sabit)
        sutun = self.arayuzler[arayuz]["cevre_birim"]
        if sutun is None:
            return set(self.paket_gpio[paket])
        return set(self.sutun.get((paket, sutun), {})) & self.paket_gpio[paket]

    def yuva_sinyalleri(self, ihtiyaclar: list[dict]) -> list[tuple[str, str, str]]:
        """Atanacak (ihtiyaç kimliği, arayüz, sinyal) yuvaları. Ortak hatlı arayüzde (L-1, `ortak_hat_secim`) ilk örnek
        bütün sinyalleri, sonraki örnekler yalnız seçim sinyalini alır: SPI ×3 → SCLK, MOSI, MISO, CS + CS + CS.
        Seçim "adres" ise (I2C, Adım 11a) sonraki örnekler hiç yuva almaz: I2C ×3 → SDA, SCL."""
        gorulen, sonuc = set(), []
        for n in ihtiyaclar:
            a = self.arayuzler[n["arayuz"]]
            secim = a.get("ortak_hat_secim")
            if secim and n["arayuz"] in gorulen:
                sinyaller = [] if secim == ADRES else [secim]
            else:
                sinyaller = a["sinyaller"]
            gorulen.add(n["arayuz"])
            sonuc += [(n["id"], n["arayuz"], s) for s in sinyaller]
        return sonuc

    def adet_siniri(self, arayuz: str, baglam: dict) -> tuple[str, int, dict] | None:
        a = self.arayuzler[arayuz]
        if a["adet_adi"] is None:
            return None
        adet = self.adetler[a["adet_adi"]]
        sinir = adet["adet"] - (1 if a["adet_baglam_dusumu"] and baglam[a["adet_baglam_dusumu"]] else 0)
        return a["adet_adi"], sinir, adet


SORGULAR = {
    "pin": "SELECT p.ad AS paket, x.pin_no, x.gpio_no, x.sayfa, x.referans, x.belirsiz FROM pin x "
           "JOIN paket p ON p.id = x.paket_id WHERE p.aile = %(aile)s",
    "kisit": "SELECT x.gpio_no, p.ad AS paket, x.kisit_turu, x.aciklama, x.varsayilan_durum, x.belirsiz, x.sayfa, "
             "x.referans FROM gpio_kisit x "
             "LEFT JOIN paket p ON p.id = x.paket_id WHERE x.aile = %(aile)s",
    "islev": "SELECT x.gpio_no, p.ad AS paket, x.grup, x.islev_no, x.islev_adi, x.sayfa, x.referans, x.belirsiz "
             "FROM gpio_islev x LEFT JOIN paket p ON p.id = x.paket_id WHERE x.aile = %(aile)s",
    "cevre": "SELECT p.ad AS paket, x.pin_no, x.cevre_birim, x.gpio_no, x.oncelik, x.yonlendirme, x.belirsiz, x.sayfa, "
             "x.referans FROM cevre_birim_sinyal x JOIN paket p ON p.id = x.paket_id WHERE p.aile = %(aile)s",
    "kural": "SELECT kod, kategori, kisit_turu, baglam_anahtari, seviye, seviye_dogru, seviye_yanlis, mesaj, mesaj_tr, sayfa, "
             "referans FROM kural ORDER BY sira",
    "arayuz": "SELECT arayuz, sinyaller, yonlendirme, cevre_birim, adet_adi, adet_baglam_dusumu, tanim, ortak_hat_secim, "
              "sayfa, referans "
              "FROM arayuz_tanimi WHERE aile = %(aile)s",
    "sabit": "SELECT arayuz, sinyal, sabit_grup, islev_deseni, sayfa, referans FROM arayuz_sinyal WHERE aile = %(aile)s",
    "adet": "SELECT ad, adet, sayfa, referans FROM cevre_adet WHERE aile = %(aile)s",
    "yorum": "SELECT olgu_tablo, olgu_anahtar, yorum, deger, veren FROM yorum",
}


def yukle(rol: str = "donanim_okur", veritabani: str = baglanti_ayari.VERITABANI, aile: str = AILE, **baglanti) -> PinVerisi:
    """Veritabanından okur; ulaşılamazsa ya da tablo boşsa VeriHatasi."""
    try:
        with PgOkuyucu(rol, veritabani, uygulama_adi="pinsecim_denetim", **{**baglanti_ayari.adres(), **baglanti}) as db:
            r = {ad: db.sorgu(sql, {"aile": aile}) for ad, sql in SORGULAR.items()}
    except PgHatasi as e:
        raise VeriHatasi(f"denetim verisi okunamadı: {e}") from e
    for ad in ("pin", "kisit", "islev", "cevre", "kural", "arayuz", "sabit", "adet"):
        if not r[ad]:
            raise VeriHatasi(f"denetim verisi eksik: {ad} boş")
    return PinVerisi(
        pin_satirlari=r["pin"], kisit_satirlari=r["kisit"], islev_satirlari=r["islev"], cevre_satirlari=r["cevre"],
        kurallar={k["kod"]: Kural(**k) for k in r["kural"]},
        arayuzler={a["arayuz"]: a for a in r["arayuz"]},
        sabit_sinyaller={(s["arayuz"], s["sinyal"]): s for s in r["sabit"]},
        adetler={a["ad"]: a for a in r["adet"]},
        yorumlar=r["yorum"],
    )

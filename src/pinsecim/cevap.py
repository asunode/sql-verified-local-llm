"""Soru cevaplayıcı (K-8): Çağrı A'nın ayırdığı soruyu, konusuna göre veritabanından cevaplar. Model cevap yazmaz.

Sorudaki GPIO numarası pin bahsi desenleriyle (sozluk.pin_bahisleri), arayüz adı arayüz listesi ve eş adlarla bulunur; paket ve
bağlam komut satırından gelir. Gereken bilgi soruda yoksa cevap uydurulmaz, ne eksik olduğu söylenir. Her cevapta
kaynak (belge, sürüm, tablo/bölüm, sayfa), belirsiz işaretli satırlar ve yorum katmanı yer alır; yoksa "yok" yazılır.
Kart konuları (Adım 10b) kart tablolarından cevaplanır: --kart verilmediyse cevap.kart_eksik ve o pakete uyan kartlar;
verildiyse her satırda kaynak ve doğrulama durumu, strapping pinindeki parçaya gpio_kisit'ten uyarı. Kart verisi LED'lere
görev atamaz; kart_led cevabı bunu söyler.
"""

from __future__ import annotations

from .cagrilar import gpio_durumlari
from . import kart as kart_mod
from .denetim import pin_ihlalleri, turkce
from .pinveri import PinVerisi, kaynak_metni
from .sozluk import IstekSozlugu

GRUP_TR = {"IO_MUX": "IO MUX", "LP_IO_MUX": "LP IO MUX", "ANALOG": "Analog"}
DURUM_TR = {"FREE": "serbest", "WARNING": "uyarılı", "FORBIDDEN": "yasak"}


def arayuz_bul(veri: PinVerisi, sozluk: IstekSozlugu, soru: str) -> list[str]:
    """Soruda adı ya da eş adı (`arayuz_es_adi`: CAN → TWAI, analog → ADC …) geçen arayüzler; sozluk.arayuz_adlari."""
    return sozluk.arayuz_adlari(soru, list(veri.arayuzler))


def _gpio_listesi(gpiolar) -> str:
    return ", ".join(f"GPIO{g}" for g in sorted(gpiolar)) or "yok"


KART_PARCA_TURLERI = {"kart_led": ("led", "ws2812"), "kart_buton": ("buton",)}


class Cevaplayici:
    def __init__(self, veri: PinVerisi, sozluk: IstekSozlugu, kartlar: kart_mod.KartVerisi | None = None):
        self.veri, self.sozluk, self._kartlar = veri, sozluk, kartlar
        self.konular = {k["konu"]: k for k in sozluk.soru_konulari}

    @property
    def kartlar(self) -> kart_mod.KartVerisi:
        if self._kartlar is None:                       # yalnız kart sorusu geldiğinde okunur
            self._kartlar = kart_mod.yukle()
        return self._kartlar

    def cevapla(self, soru: dict, paket: str, baglam: dict, kart: dict | None = None) -> dict:
        """{"soru", "konu", "durum": cevap | eksik_bilgi | kart_eksik | tabloda_yok, "parametre",
        "satirlar", "kaynaklar", "belirsiz", "yorumlar", "dogrulanmadi", "mesaj", "on_not"}. Adım 11a: soruda
        elektriksel değer sözcüğü (`soru_sozcugu`) geçerse, konu ne olursa olsun, `on_not` = cevap.elektriksel_yok;
        konu cevabı ayrıca verilir."""
        c = self._cevapla(soru, paket, baglam, kart)
        sozcukler = self.sozluk.soru_sozcukleri_bul(soru["soru"], "elektriksel")
        c["on_not"] = {**self._mesaj("cevap.elektriksel_yok"), "sozcukler": sozcukler} if sozcukler else None
        return c

    def _cevapla(self, soru: dict, paket: str, baglam: dict, kart: dict | None = None) -> dict:
        k = self.konular[soru["konu"]]
        c = {"soru": soru["soru"], "konu": soru["konu"], "durum": "cevap", "parametre": {"paket": paket},
             "satirlar": [], "kaynaklar": [], "belirsiz": [], "yorumlar": [], "dogrulanmadi": [], "mesaj": None}
        if k["cevap_turu"] == "kart":
            return self._kart(c, paket, kart)
        if k["cevap_turu"] != "tablo":
            c["durum"] = k["cevap_turu"]
            c["mesaj"] = self._mesaj(f"cevap.{k['cevap_turu']}")
            return c
        if k["gereken"] == "gpio":
            gpiolar = sorted({b.gpio for b in self.sozluk.pin_bahisleri(soru["soru"]) if b.tur != "belirsiz"})
            if not gpiolar:
                return {**c, "durum": "eksik_bilgi", "mesaj": self._mesaj("cevap.gpio_eksik")}
            c["parametre"]["gpio"] = gpiolar
            for g in gpiolar:
                (self._pin_islevi if k["konu"] == "pin_islevi" else self._pin_kisiti)(c, g, paket, baglam)
        elif k["gereken"] == "arayuz":
            arayuzler = arayuz_bul(self.veri, self.sozluk, soru["soru"])
            if not arayuzler:
                return {**c, "durum": "eksik_bilgi", "mesaj": self._mesaj("cevap.arayuz_eksik")}
            c["parametre"]["arayuz"] = arayuzler
            for a in arayuzler:
                self._arayuz_pinleri(c, a, paket, baglam)
        else:
            self._paket_pinleri(c, paket, baglam)
        c["kaynaklar"] = list(dict.fromkeys(c["kaynaklar"]))
        return c

    # ------------------------------------------------------------------ kart soruları (Adım 10b)
    def _kart(self, c: dict, paket: str, kart: dict | None) -> dict:
        if kart is None:
            uyan = self.kartlar.pakete_uyan(paket)
            c["satirlar"] = [f"{paket} paketine uyan kartlar: " + (", ".join(
                f"{x['kisa_ad']} ({x['ad']}{' ' + x['surum'] if x['surum'] else ''}"
                + ("; DOĞRULANMADI" if x["dogrulama_durumu"] == "dogrulanmadi" else "") + ")" for x in uyan) or "yok")]
            m = self._mesaj("cevap.kart_eksik")
            m["ornek"] = m["ornek"].format(kart=uyan[0]["kisa_ad"]) if uyan else None   # pakete uyan ilk kart (Adım 10c)
            return {**c, "durum": "kart_eksik", "mesaj": m}
        c["parametre"]["kart"] = kart["kisa_ad"]
        self._satir(c, f"Kart: {kart['ad']}{' ' + kart['surum'] if kart['surum'] else ''} ({kart['kisa_ad']}; çip "
                       f"{kart['cip']}, {kart['paket']}" + (f"; modül {kart['modul']}" if kart["modul"] else "") + ")",
                    kart)
        if c["konu"] == "kart_led":
            c["satirlar"].append(self._mesaj("cevap.kart_gorev_yok")["mesaj"])
        if c["konu"] in KART_PARCA_TURLERI:
            parcalar = self.kartlar.parcalari(kart, KART_PARCA_TURLERI[c["konu"]])
            for p in parcalar:
                gpio = f"GPIO{p['gpio_no']}" if p["gpio_no"] is not None else "GPIO'ya bağlı değil"
                seviye = {"yuksek": "; aktif yüksek", "dusuk": "; aktif düşük"}.get(p["aktif_seviye"], "")
                self._satir(c, f"{p['ad']} {p['aciklama']}: {gpio}{seviye} ({p['baglanti']})", p)
                if p["gpio_no"] is not None:
                    self._strapping(c, p["gpio_no"], kart["paket"], p["ad"])
            if not parcalar:
                c["satirlar"].append("Bu kartta bu türde parça kaydı yok.")
        else:                                           # kart_pin_cikisi
            pinler = self.kartlar.pinleri(kart)
            for kon in dict.fromkeys(p["konnektor"] for p in pinler):
                grup = [p for p in pinler if p["konnektor"] == kon]
                self._satir(c, f"{kon} ({grup[0]['referans']}): " + ", ".join(
                    f"{p['sira']} {p['etiket']}" + (f"=GPIO{p['gpio_no']}" if p["gpio_no"] is not None
                                                     and p["etiket"] != f"GPIO{p['gpio_no']}" else "") for p in grup),
                            grup[0])
            if kart["modul"]:
                m = self.kartlar.modul_kaynagi(kart["modul"])
                if m is not None:
                    c["satirlar"].append(f"Modül pin → GPIO eşlemesi: {kart['modul']} "
                                         f"[{kart_mod.kaynak_metni(m)}; teyit: {m['teyit_belge']} {m['teyit_surum']}]")
                    c["kaynaklar"].append(kart_mod.kaynak_metni(m))
        c["kaynaklar"] = list(dict.fromkeys(c["kaynaklar"]))
        return c

    def _satir(self, c: dict, metin: str, r: dict) -> None:
        """Kart satırı: doğrulama durumu ve kaynak her satırda; dogrulanmadi satır ayrıca listelenir."""
        durum = kart_mod.DURUM_ETIKETI[r["dogrulama_durumu"]]
        not_ = f" Not: {r['not_']}" if r.get("not_") else ""
        c["satirlar"].append(f"{'[DOĞRULANMADI] ' if r['dogrulama_durumu'] == 'dogrulanmadi' else ''}{metin} · {durum} · "
                             f"[{kart_mod.kaynak_metni(r)}]{not_}")
        c["kaynaklar"].append(kart_mod.kaynak_metni(r))
        if r["dogrulama_durumu"] == "dogrulanmadi":
            c["dogrulanmadi"].append(metin)

    def _strapping(self, c: dict, g: int, paket: str, parca: str) -> None:
        for k in self.veri.kisitlar(paket, g):
            if k["kisit_turu"] == "strapping":
                ek = f"; varsayılan: {k['varsayilan_durum']}" if k["varsayilan_durum"] else ""
                c["satirlar"].append(f"Uyarı ({parca}): GPIO{g} strapping pini: {k['aciklama']}{ek} "
                                     f"[{kaynak_metni(k['referans'], k['sayfa'])}]")
                c["kaynaklar"].append(kaynak_metni(k["referans"], k["sayfa"]))

    def _mesaj(self, anahtar: str) -> dict:
        m = self.sozluk.mesaj(anahtar)
        return {"anahtar": anahtar, "mesaj": m["mesaj_tr"], "ne_yazmali": m["ne_yazmali_tr"], "ornek": m["ornek_tr"]}

    def _pakette_degil(self, c: dict, g: int, paket: str, baglam: dict) -> bool:
        if g in self.veri.paket_gpio[paket]:
            return False
        for i in pin_ihlalleri(self.veri, paket, g, baglam):      # GECERSIZ_GPIO ya da PIN_PAKETTE_YOK, kaynaklı
            c["satirlar"].append(turkce(i))
        return True

    def _pin_islevi(self, c: dict, g: int, paket: str, baglam: dict) -> None:
        if self._pakette_degil(c, g, paket, baglam):
            return
        satirlar = [r for r in self.veri.islev_satirlari if r["gpio_no"] == g and r["paket"] in (None, paket)]
        for grup in GRUP_TR:
            rs = sorted((r for r in satirlar if r["grup"] == grup), key=lambda r: r["islev_no"])
            if not rs:
                continue
            c["satirlar"].append(f"GPIO{g} {GRUP_TR[grup]}: " + ", ".join(
                f"F{r['islev_no']} {r['islev_adi']}" + (" (belirsiz)" if r["belirsiz"] else "") for r in rs))
            c["kaynaklar"] += [kaynak_metni(r["referans"], r["sayfa"]) for r in rs]
            c["belirsiz"] += [f"GPIO{g} {GRUP_TR[grup]} F{r['islev_no']} {r['islev_adi']} "
                              f"[{kaynak_metni(r['referans'], r['sayfa'])}]" for r in rs if r["belirsiz"]]
        if not satirlar:
            c["satirlar"].append(f"GPIO{g} için işlev satırı yok.")

    def _pin_kisiti(self, c: dict, g: int, paket: str, baglam: dict) -> None:
        if self._pakette_degil(c, g, paket, baglam):
            return
        kisitlar = [k for k in self.veri.kisitlar(paket, g) if k["kisit_turu"] != "bu_pakette_yok"]
        for k in kisitlar:
            ek = f"; varsayılan: {k['varsayilan_durum']}" if k["varsayilan_durum"] else ""
            c["satirlar"].append(f"GPIO{g} {k['kisit_turu']}: {k['aciklama']}{ek}"
                                 + (" (belirsiz)" if k["belirsiz"] else ""))
            c["kaynaklar"].append(kaynak_metni(k["referans"], k["sayfa"]))
            if k["belirsiz"]:
                c["belirsiz"].append(f"GPIO{g} {k['kisit_turu']} [{kaynak_metni(k['referans'], k['sayfa'])}]")
        if not kisitlar:
            c["satirlar"].append(f"GPIO{g}: kısıt tablosunda satırı yok.")
        ihl = pin_ihlalleri(self.veri, paket, g, baglam)
        if ihl:
            c["satirlar"] += [f"Bu bağlamda {'yasak' if i.seviye == 'hata' else 'uyarı'}: {turkce(i)}" for i in ihl]
        else:
            c["satirlar"].append(f"Bu bağlamda GPIO{g} serbest (kural ihlali yok).")

    def _durumlu(self, gpiolar, durumlar: dict) -> list[str]:
        satirlar = []
        for d in ("FREE", "WARNING", "FORBIDDEN"):
            gs = sorted(g for g in gpiolar if durumlar[g][0] == d)
            if gs:
                satirlar.append(f"{DURUM_TR[d]}: " + ", ".join(
                    f"GPIO{g}" + (f" ({', '.join(i.kod for i in durumlar[g][1])})" if durumlar[g][1] else "")
                    for g in gs))
        return satirlar

    def _kural_kaynaklari(self, c: dict, gpiolar, durumlar: dict) -> None:
        for kod in sorted({i.kod for g in gpiolar for i in durumlar[g][1]}):
            kural = self.veri.kurallar[kod]
            c["kaynaklar"].append(f"{kod}: " + kaynak_metni(kural.referans, kural.sayfa))

    def _arayuz_pinleri(self, c: dict, ad: str, paket: str, baglam: dict) -> None:
        v, a = self.veri, self.veri.arayuzler[ad]
        durumlar = gpio_durumlari(v, paket, baglam)
        c["kaynaklar"].append(f"{ad} tanımı: " + kaynak_metni(a["referans"], a["sayfa"]))
        tum = set()
        for s in a["sinyaller"]:
            aday = v.aday_gpio(paket, ad, s)
            tum |= aday
            c["satirlar"].append(f"{ad} {s} ({paket}, {len(aday)} pin) — " + "; ".join(self._durumlu(aday, durumlar)))
            sabit = v.sabit_izinli(paket, ad, s)
            if sabit is not None:
                c["kaynaklar"] += [f"{ad} {s} sabit pin: " + kaynak_metni(k.referans, k.sayfa) for k in sabit.values()]
        sutun = a["cevre_birim"]
        if sutun is not None:
            c["kaynaklar"] += [f"{sutun} sütunu: " + kaynak_metni(k.referans, k.sayfa)
                               for k in v.sutun.get((paket, sutun), {}).values()]
            c["belirsiz"] += [f"{sutun} GPIO{g}: belirsiz hücre, yorumu yok; yok sayıldı "
                              f"[{kaynak_metni(k.referans, k.sayfa)}]"
                              for g, k in sorted(v.belirsiz_yok_sayilan.get((paket, sutun), {}).items())]
            c["yorumlar"] += [f"{y['yorum']} (veren: {y['veren']})" for y in v.kullanilan_yorumlar
                              if y["olgu_anahtar"].get("paket") == paket and y["olgu_anahtar"].get("cevre_birim") == sutun]
        adet = v.adet_siniri(ad, baglam)
        if adet is not None:
            adet_adi, sinir, satir = adet
            c["satirlar"].append(f"{ad}: bu bağlamda en çok {sinir} örnek ({adet_adi}).")
            c["kaynaklar"].append(f"{adet_adi} adedi: " + kaynak_metni(satir["referans"], satir["sayfa"]))
        self._kural_kaynaklari(c, tum, durumlar)

    def _paket_pinleri(self, c: dict, paket: str, baglam: dict) -> None:
        v = self.veri
        durumlar = gpio_durumlari(v, paket, baglam)
        gpiolar = sorted(v.paket_gpio[paket])
        c["satirlar"].append(f"{paket} paketinde {len(gpiolar)} GPIO var: {_gpio_listesi(gpiolar)}.")
        c["satirlar"].append("Bu bağlamdaki durumları — " + "; ".join(self._durumlu(gpiolar, durumlar)))
        pinler = [r for r in v.pin_satirlari if r["paket"] == paket and r["gpio_no"] is not None]
        c["kaynaklar"] += [kaynak_metni(r["referans"], r["sayfa"]) for r in pinler]
        c["belirsiz"] += [f"{paket} pin {r['pin_no']} (GPIO{r['gpio_no']}) [{kaynak_metni(r['referans'], r['sayfa'])}]"
                          for r in pinler if r["belirsiz"]]
        self._kural_kaynaklari(c, gpiolar, durumlar)

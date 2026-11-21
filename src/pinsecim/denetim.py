"""Pin atama denetleyicisi: istek + atama → Ihlal listesi (hata ve uyarı).

Kural verisi (kodlar, seviyeler, bağlam koşulları, mesaj şablonları) ve olgular veritabanından gelir
(`pinveri.yukle`, rol donanim_okur); burada yalnız mantık var. Veritabanına ulaşılamazsa `VeriHatasi`.

Çekirdeğin döngüsüne verilecek biçim: `Denetleyici(veri).icin(istek)` → `atama -> list[Ihlal]`.
İhlaller `PinIhlali`dir: `mesaj` modele giden İngilizce geri bildirim, `mesaj_tr` kullanıcıya gösterilen Türkçe metin.
İstekte `pin_tercihleri` / `kullanilmayacak` varsa (K-7) atandı atamada YASAK_PIN ve TERCIH_UYGULANMADI da denetlenir.
Ortak hat (L-1): SPI'nin ikinci ve sonraki örneklerinde yalnız CS zorunlu; ortak sinyal verilirse ilk örnekle aynı pin olur.
İstekte kart varsa (Adım 10c) kart kuralları: KART_PIN_YOK (hata), KART_PED, KART_PARCA, KART_UART_KOPRU (uyarı).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from asu_llmcore import Ihlal

from .pinveri import ADRES, PinVerisi, kaynak_metni, yukle

KISIT_KURALI = {"bu_pakette_yok": "PIN_PAKETTE_YOK", "flash": "PIN_FLASH", "vdd_spi": "PIN_VDD_SPI",
                "usb_serial_jtag": "PIN_USB", "uart0": "PIN_UART0", "jtag": "PIN_JTAG", "strapping": "PIN_STRAPPING"}


@dataclass(frozen=True)
class PinIhlali(Ihlal):
    mesaj_tr: str = ""


def turkce(i: Ihlal) -> str:
    """Kullanıcıya gösterilecek metin: Türkçe mesaj varsa o, yoksa İngilizce."""
    return getattr(i, "mesaj_tr", "") or i.mesaj


def _ihlal(veri: PinVerisi, kod: str, baglam: dict, alan: str = "", seviye: str | None = None, **degerler) -> PinIhlali:
    k = veri.kurallar[kod]
    return PinIhlali(kod, k.mesaj.format(**degerler), alan, seviye or k.seviye_icin(baglam),
                     k.mesaj_tr.format(**degerler))


def pin_ihlalleri(veri: PinVerisi, paket: str, gpio: int, baglam: dict, alan: str = "") -> list[Ihlal]:
    """Bir GPIO'nun kendisinden doğan ihlaller (hangi arayüzle kullanılırsa kullanılsın)."""
    if gpio not in veri.cip_gpio:
        return [_ihlal(veri, "GECERSIZ_GPIO", baglam, alan, gpio=gpio,
                       kaynak=kaynak_metni(veri.kurallar["GECERSIZ_GPIO"].referans, veri.kurallar["GECERSIZ_GPIO"].sayfa))]
    kisitlar = veri.kisitlar(paket, gpio)
    if gpio not in veri.paket_gpio[paket]:
        k = next(k for k in kisitlar if k["kisit_turu"] == "bu_pakette_yok")
        return [_ihlal(veri, "PIN_PAKETTE_YOK", baglam, alan, gpio=gpio, paket=paket,
                       kaynak=kaynak_metni(k["referans"], k["sayfa"]))]
    sonuc = []
    for k in sorted(kisitlar, key=lambda k: list(KISIT_KURALI).index(k["kisit_turu"])):
        kod = KISIT_KURALI[k["kisit_turu"]]
        if kod != "PIN_PAKETTE_YOK":
            sonuc.append(_ihlal(veri, kod, baglam, alan, gpio=gpio, kaynak=kaynak_metni(k["referans"], k["sayfa"])))
    return sonuc


class Denetleyici:
    def __init__(self, veri: PinVerisi | None = None):
        self.veri = veri if veri is not None else yukle()

    def icin(self, istek: dict):
        """Çekirdeğin döngüsü için tek argümanlı denetleyici."""
        return lambda atama: self.denetle(istek, atama)

    def denetle(self, istek: dict, atama: dict) -> list[Ihlal]:
        v, paket, baglam = self.veri, istek["paket"], istek["baglam"]
        durum = atama["durum"]
        if durum in ("bilgi_yok", "tercih_uygulanamadi"):     # tercih_uygulanamadi: atama yok, alternatif ayrı denetlenir
            return []
        if durum == "mumkun_degil":
            from .atayici import Atayici
            bulunan = Atayici(v).ata(istek)
            if bulunan.atama["durum"] != "atandi":
                return []
            ornek = ", ".join(f"{a['ihtiyac_id']}.{a['sinyal']}=GPIO{a['gpio']}" for a in bulunan.atama["atamalar"][:6])
            return [_ihlal(v, "YANLIS_RET", baglam, "durum", ornek=ornek)]

        ihtiyaclar = {n["id"]: n["arayuz"] for n in istek["ihtiyaclar"]}
        yuvalar = v.yuva_sinyalleri(istek["ihtiyaclar"])
        gerekli = {(nid, s) for nid, _, s in yuvalar}
        sonraki: list[tuple[str, str, str, int]] = []   # ortak hatta sonraki örneğe verilen ortak sinyaller
        ilk = {}                                         # ortak hat (L-1): arayüz → ilk örneğin kimliği
        for nid, a, _ in yuvalar:
            ilk.setdefault(a, nid)
        ihlaller: list[Ihlal] = []
        atanan: dict[tuple[str, str], int] = {}
        gpio_sinyal: dict[int, list[str]] = {}
        for i, a in enumerate(atama["atamalar"]):
            nid, sinyal, gpio, alan = a["ihtiyac_id"], a["sinyal"], a["gpio"], f"atamalar/{i}"
            if nid not in ihtiyaclar:
                ihlaller.append(_ihlal(v, "BILINMEYEN", baglam, f"{alan}/ihtiyac_id",
                                       sinyal=f"Need id '{nid}' is not in the request."))
                continue
            arayuz = ihtiyaclar[nid]
            sinyaller = v.arayuzler[arayuz]["sinyaller"]
            if sinyal not in sinyaller:
                ihlaller.append(_ihlal(v, "BILINMEYEN", baglam, f"{alan}/sinyal",
                                       sinyal=f"'{sinyal}' is not a signal of {arayuz} ({', '.join(sinyaller)})."))
                continue
            if (nid, sinyal) in atanan:
                ihlaller.append(_ihlal(v, "CAKISMA", baglam, f"{alan}/sinyal", gpio=gpio,
                                       sinyal=f"{nid}.{sinyal} assigned twice"))
                continue
            atanan[(nid, sinyal)] = gpio
            if (nid, sinyal) not in gerekli:
                sonraki.append((nid, arayuz, sinyal, gpio))
                if atanan.get((ilk[arayuz], sinyal)) == gpio:
                    continue                             # sonraki örneğin ortak sinyali ilk örnekle aynı pinde (L-1)
            gpio_sinyal.setdefault(gpio, []).append(f"{nid}.{sinyal}")

            pin = pin_ihlalleri(v, paket, gpio, baglam, f"{alan}/gpio")
            ihlaller += pin
            if any(p.kod in ("GECERSIZ_GPIO", "PIN_PAKETTE_YOK") for p in pin):
                continue
            if istek.get("kart"):
                ihlaller += kart_ihlalleri(v, istek["kart"], gpio, baglam, f"{alan}/gpio",
                                           uart0=any(p.kod == "PIN_UART0" for p in pin))
            izinli = v.sabit_izinli(paket, arayuz, sinyal)
            if izinli is not None and gpio not in izinli:
                adlar = v.sabit_islev_adlari(paket, arayuz, sinyal)
                yer = ", ".join(f"GPIO{g} ({adlar[g]})" for g in sorted(izinli))
                s = v.sabit_sinyaller[(arayuz, sinyal)]
                ihlaller.append(_ihlal(v, "SABIT_PIN", baglam, f"{alan}/gpio", gpio=gpio, sinyal=sinyal,
                                       ihtiyac=nid, arayuz=arayuz, izinli=yer,
                                       kaynak=kaynak_metni(s["referans"], s["sayfa"])))
            sutun = v.arayuzler[arayuz]["cevre_birim"]
            yok_sayilan = v.belirsiz_yok_sayilan.get((paket, sutun), {}) if sutun else {}
            if gpio in yok_sayilan:
                k = yok_sayilan[gpio]
                ihlaller.append(_ihlal(v, "BELIRSIZ_KAYNAK", baglam, f"{alan}/gpio", gpio=gpio, arayuz=arayuz,
                                       kaynak=kaynak_metni(k.referans, k.sayfa)))

        for gpio, kullananlar in gpio_sinyal.items():
            if len(kullananlar) > 1:
                ihlaller.append(_ihlal(v, "CAKISMA", baglam, "atamalar", gpio=gpio, sinyal=", ".join(kullananlar)))
        for nid, arayuz, sinyal in yuvalar:
            if (nid, sinyal) not in atanan:
                ihlaller.append(_ihlal(v, "EKSIK_SINYAL", baglam, "atamalar", ihtiyac=nid, arayuz=arayuz, sinyal=sinyal))
        ihlaller += adet_ihlalleri(v, istek)
        ihlaller += ayri_hat_ihlalleri(v, istek, atanan, ilk, sonraki)
        ihlaller += tercih_ihlalleri(v, istek, atama)
        return ihlaller


def kart_ihlalleri(veri: PinVerisi, kart: dict, gpio: int, baglam: dict, alan: str, uart0: bool) -> list[Ihlal]:
    """Kart düzeyi (Adım 10c): pin kartta çıkmıyorsa hata; pedde ise, kart üstü parçaya bağlıysa ya da UART0 pini olup
    kartta USB-UART köprüsü varsa uyarı. Kart verisi isteğe kart.atama_bilgisi ile girer."""
    pin = next((p for p in kart["pinler"] if p["gpio"] == gpio), None)
    if pin is None:
        return [_ihlal(veri, "KART_PIN_YOK", baglam, alan, gpio=gpio, kart=kart["kisa_ad"])]
    ortak = {"gpio": gpio, "etiket": pin["etiket"], "kart": kart["kisa_ad"]}
    sonuc = []
    if pin["tur"] == "ped":
        sonuc.append(_ihlal(veri, "KART_PED", baglam, alan, kaynak=pin["kaynak"], **ortak))
    for p in kart["parcalar"]:
        if p["gpio"] == gpio:
            sonuc.append(_ihlal(veri, "KART_PARCA", baglam, alan, parca=f"{p['ad']} {p['aciklama']}", kaynak=p["kaynak"],
                                **ortak))
    if uart0:
        for k in kart["usb_uart"]:
            sonuc.append(_ihlal(veri, "KART_UART_KOPRU", baglam, alan, parca=f"{k['ad']} {k['aciklama']}",
                                kaynak=k["kaynak"], **ortak))
    return sonuc


def tercih_ihlalleri(veri: PinVerisi, istek: dict, atama: dict) -> list[Ihlal]:
    """K-7: kullanılmayacak pin atamada olmamalı; her pin tercihi, istenen arayüzün (ve verildiyse sinyalin) bir
    sinyaline atanmış olmalı."""
    baglam = istek["baglam"]
    arayuz = {n["id"]: n["arayuz"] for n in istek["ihtiyaclar"]}
    kullanan = {a["gpio"]: (arayuz.get(a["ihtiyac_id"]), a["sinyal"]) for a in atama["atamalar"]}
    sonuc = [_ihlal(veri, "YASAK_PIN", baglam, "atamalar", gpio=g)
             for g in sorted(set(istek.get("kullanilmayacak", ())) & set(kullanan))]
    karsilanan: set[int] = set()                     # bir pin tek tercihi karşılar (aynı pine iki tercih)
    for t in istek.get("pin_tercihleri", ()):
        a, s = kullanan.get(t["gpio"], (None, None))
        if a != t["arayuz"] or (t["sinyal"] and s != t["sinyal"]) or t["gpio"] in karsilanan:
            sonuc.append(_ihlal(veri, "TERCIH_UYGULANMADI", baglam, "atamalar", gpio=t["gpio"], arayuz=t["arayuz"],
                                sinyal=f" {t['sinyal']}" if t["sinyal"] else ""))
        else:
            karsilanan.add(t["gpio"])
    return sonuc


def adet_asimlari(veri: PinVerisi, istek: dict) -> list[tuple[str, list[str], int, dict]]:
    """(adet adı, arayüzler, sınır, adet satırı) — ihtiyaç sayısı sınırı aşan gruplar."""
    sayac: Counter = Counter()
    arayuzler: dict[str, list[str]] = {}
    sinirlar = {}
    adresli = set()
    for n in istek["ihtiyaclar"]:
        s = veri.adet_siniri(n["arayuz"], istek["baglam"])
        if s is None:
            continue
        if veri.arayuzler[n["arayuz"]].get("ortak_hat_secim") == ADRES:   # I2C ×N tek hat: bir birim (Adım 11a)
            if n["arayuz"] in adresli:
                continue
            adresli.add(n["arayuz"])
        ad, sinir, satir = s
        sayac[ad] += 1
        arayuzler.setdefault(ad, [])
        if n["arayuz"] not in arayuzler[ad]:
            arayuzler[ad].append(n["arayuz"])
        sinirlar[ad] = (sinir, satir)
    return [(ad, arayuzler[ad], sinirlar[ad][0], {**sinirlar[ad][1], "sayi": sayac[ad]})
            for ad in sayac if sayac[ad] > sinirlar[ad][0]]


def ayri_hat_ihlalleri(veri: PinVerisi, istek: dict, atanan: dict, ilk: dict, sonraki: list) -> list[Ihlal]:
    """Adım 11a: adresle paylaşılan hatta (I2C ×N) sonraki bir örneğin sinyali ilk örnekten farklı pindeyse o örnek ayrı
    bir hat demektir ve ayrı bir birim ister; hat sayısı birim sınırını aşarsa ADET_ASIMI."""
    hatlar: dict[str, set[str]] = {}
    for nid, arayuz, sinyal, gpio in sonraki:
        if veri.arayuzler[arayuz].get("ortak_hat_secim") == ADRES and atanan.get((ilk[arayuz], sinyal)) != gpio:
            hatlar.setdefault(arayuz, set()).add(nid)
    sonuc = []
    for arayuz, ayri in hatlar.items():
        s = veri.adet_siniri(arayuz, istek["baglam"])
        if s is not None and 1 + len(ayri) > s[1]:
            sonuc.append(_ihlal(veri, "ADET_ASIMI", istek["baglam"], "durum", arayuz=arayuz, sayi=1 + len(ayri),
                                adet=s[1], kaynak=kaynak_metni(s[2]["referans"], s[2]["sayfa"])))
    return sonuc


def adet_ihlalleri(veri: PinVerisi, istek: dict) -> list[Ihlal]:
    sonuc = []
    for ad, arayuzler, sinir, satir in adet_asimlari(veri, istek):
        sonuc.append(_ihlal(veri, "ADET_ASIMI", istek["baglam"], "durum", arayuz="/".join(arayuzler),
                            sayi=satir["sayi"], adet=sinir, kaynak=kaynak_metni(satir["referans"], satir["sayfa"])))
    return sonuc

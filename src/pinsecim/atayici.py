"""Modelsiz kod atayıcı: deterministik geri izlemeli arama.

Her (ihtiyaç, sinyal) bir yuvadır; yuvaya ayrı bir GPIO verilir. Adaylar: sinyalin gidebileceği GPIO'lar
(sabit pin ya da Table 2-10/2-11 sütunu) eksi hata üreten pinler eksi kullanıcının kullanılmayacak dediği pinler.
Önce uyarısız pinler denenir; çözüm yoksa uyarılı pin sınırı birer birer artırılır (k = alt sınır, alt sınır + 1, …),
böylece en az uyarılı çözüm bulunur. Arama iki parçalı eşleştirmeyle budanır: kalan yuvalar kalan pinlerle
eşleşemiyorsa ya da yalnız uyarısız pinlerle eşleşemeyen yuva sayısı kalan uyarı hakkını aşıyorsa dal kesilir.

Pin tercihleri (K-7): her tercih önce kurallarla denetlenir (pakette yok, flash, bağlama göre USB/UART0/JTAG/VDD_SPI,
sabit pin ya da arayüzün gidemediği pin, aynı pine iki tercih, kullanılmayacak pinle çakışma, sinyalden fazla tercih).
Geçen tercihler kilitlenir: tercih edilen GPIO, eşleşen arayüzün (verildiyse o sinyalin) bir yuvasına sabitlenir,
kalan atama çevresine yapılır. Sinyali verilmemiş çoklu tercihte (bir SPI'ye dört GPIO) sinyaller bu pinler içinde
dağıtılır. Uyarılı pindeki tercih uygulanır. Kilitli tercihlerle çözüm yoksa tercihleri birer birer deneyerek
çözümü bozanlar bulunur. Sonuç: atandi (tüm tercihler uygulandı) | tercih_uygulanamadi (her sorunlu tercih için neden
ve öneri; sorunlu tercihler olmadan alternatif atama) | mumkun_degil (tercihlerden bağımsız olarak pin ya da adet yetmez).

Kart düzeyi (Adım 10c; istekte "kart" varsa): adaylar kartın konnektör ve pedlerine çıkan GPIO'larla sınırlı; önce
konnektör pinleri (kart üstü parçaya bağlı olmayanlar), yetmezse pedler, en son parçaya bağlı pinler denenir. Çıkmayan
pine tercih KART_PIN_YOK (neden, öneri, alternatif); parça pinine düşen tercih uygulanır (denetleyici uyarır).

Aynı hatta birden çok cihaz (L-1, Adım 10c): ortak hatlı arayüzün (SPI) ilk örneği bütün sinyalleri, sonrakiler yalnız
seçim sinyalini (CS) alır; örnek sayısı adet satırıyla sınırlı (SPI2_CS: altı).

Görevleri: varsayılan akışta atama (K-6), ölçümde hakem, YANLIS_RET kuralının hakemi.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .denetim import adet_asimlari, pin_ihlalleri, turkce
from .pinveri import ADRES, PinVerisi, kaynak_metni, yukle

ONERI = {   # kurala takılan tercih için çözüm önerisi
    "GECERSIZ_GPIO": "GPIO0–GPIO30 arasından bir pin seç.",
    "PIN_PAKETTE_YOK": "Bu paketteki bir GPIO seç.",
    "PIN_FLASH": "Flash pinleri kullanılamaz; başka bir pin seç.",
    "PIN_VDD_SPI": "Flash harici besleniyorsa --harici-flash-beslemesi ver; değilse başka bir pin seç.",
    "PIN_USB": "USB Serial/JTAG'ı kullanmayacaksan --no-usb ver; kullanacaksan başka bir pin seç.",
    "PIN_UART0": "UART0'ı konsol olarak kullanmayacaksan --no-uart0-konsol ver; kullanacaksan başka bir pin seç.",
    "PIN_JTAG": "JTAG pinleriyle hata ayıklamayacaksan --jtag-pinleri verme; ayıklayacaksan başka bir pin seç.",
}


def pin_listesi(gpiolar) -> str:
    """GPIO0–GPIO6, GPIO10 biçiminde kısa liste."""
    g = sorted(set(gpiolar))
    parcalar, i = [], 0
    while i < len(g):
        j = i
        while j + 1 < len(g) and g[j + 1] == g[j] + 1:
            j += 1
        if j == i:
            parcalar.append(f"GPIO{g[i]}")
        elif j == i + 1:
            parcalar.append(f"GPIO{g[i]}, GPIO{g[j]}")
        else:
            parcalar.append(f"GPIO{g[i]}–GPIO{g[j]}")
        i = j + 1
    return ", ".join(parcalar) or "yok"


def tercih_adi(t: dict) -> str:
    return f"{t['arayuz']}{' ' + t['sinyal'] if t.get('sinyal') else ''} → GPIO{t['gpio']}"


@dataclass
class AtamaSonucu:
    atama: dict                       # {"durum": "atandi"|"tercih_uygulanamadi"|"mumkun_degil", "atamalar": [...]}
    neden: str | None = None          # mumkun_degil ise: hangi arayüz, hangi kısıt (Türkçe, kullanıcıya gösterilir)
    uyarili_pin: list[int] = field(default_factory=list)
    tercih_sorunlari: list[dict] = field(default_factory=list)   # {"tercih", "kod", "neden", "oneri"}
    uygulanan_tercihler: list[dict] = field(default_factory=list)
    alternatif: dict | None = None    # tercih_uygulanamadi: sorunlu tercihler olmadan atama (alternatif)
    kart_ozeti: dict | None = None    # kart düzeyi atama (Adım 10c): aşama, konnektör/ped sayısı, kullanılan ped/parça


def _eslesme(yuvalar: list[int], adaylar: list[list[int]], dolu: set[int]) -> dict[int, int]:
    """Yuva → GPIO en büyük eşleşmesi (artırma yollarıyla). Sıra deterministik."""
    eslesen: dict[int, int] = {}      # gpio → yuva

    def artir(y: int, gorulen: set[int]) -> bool:
        for g in adaylar[y]:
            if g in dolu or g in gorulen:
                continue
            gorulen.add(g)
            if g not in eslesen or artir(eslesen[g], gorulen):
                eslesen[g] = y
                return True
        return False

    for y in yuvalar:
        artir(y, set())
    return {y: g for g, y in eslesen.items()}


class Atayici:
    def __init__(self, veri: PinVerisi | None = None):
        self.veri = veri if veri is not None else yukle()

    def adaylar(self, istek: dict, arayuz: str, sinyal: str) -> tuple[list[int], set[int]]:
        """(sıralı adaylar: önce uyarısız, sonra uyarılı; uyarılı küme). Hata üreten ve kullanılmayacak pin yok."""
        v, paket, baglam = self.veri, istek["paket"], istek["baglam"]
        yasak = set(istek.get("kullanilmayacak", ()))
        temiz, uyarili = [], []
        for g in sorted(v.aday_gpio(paket, arayuz, sinyal) - yasak):
            ihl = pin_ihlalleri(v, paket, g, baglam)
            if any(i.seviye == "hata" for i in ihl):
                continue
            (uyarili if ihl else temiz).append(g)
        return temiz + uyarili, set(uyarili)

    def ata(self, istek: dict) -> AtamaSonucu:
        v = self.veri
        bilinmeyen = sorted({n["arayuz"] for n in istek["ihtiyaclar"]} - set(v.arayuzler))
        if bilinmeyen:
            raise ValueError(f"bilinmeyen arayüz: {bilinmeyen}")
        asim = adet_asimlari(v, istek)
        if asim:
            ad, arayuzler, sinir, satir = asim[0]
            secim = v.arayuzler[arayuzler[0]].get("ortak_hat_secim")
            if secim and secim != ADRES:                 # L-1: ortak hatta her cihaz ayrı seçim sinyali ister
                neden = (f"{arayuzler[0]} ×{satir['sayi']}: tek hatta her cihaz ayrı {secim} ister; {satir['sayi']} "
                         f"{secim} gerekiyor, en çok {sinir} var")
            else:
                neden = f"{'/'.join(arayuzler)} için {satir['sayi']} birim gerekiyor, çipte en çok {sinir} kullanılabilir"
            return AtamaSonucu({"durum": "mumkun_degil", "atamalar": []},
                               f"{neden} ({ad}; {kaynak_metni(satir['referans'], satir['sayfa'])})")

        yasak = sorted(set(istek.get("kullanilmayacak", ())))
        yasak_notu = f" Kullanılmayacak pinler hariç tutuldu: {pin_listesi(yasak)}." if yasak else ""
        yuva_bilgi: list[tuple[str, str, str]] = []
        adaylar: list[list[int]] = []
        uyarili: set[int] = set()
        for nid, arayuz, sinyal in v.yuva_sinyalleri(istek["ihtiyaclar"]):      # SPI ×N: tek hat, ayrı CS (L-1)
            a, u = self.adaylar(istek, arayuz, sinyal)
            yuva_bilgi.append((nid, arayuz, sinyal))
            adaylar.append(a)
            uyarili |= u
        kart = istek.get("kart")
        gecerli, sorunlar = self._tercih_on_denetimi(istek, yuva_bilgi, adaylar)
        if kart is None:
            return self._asama(istek, yuva_bilgi, adaylar, uyarili, gecerli, sorunlar, yasak_notu, True)
        # Kart düzeyi (Adım 10c): önce konnektör pinleri (parçasız), sonra pedler, en son kart üstü parçaya bağlı pinler.
        # Geçen tercihlerin pini her aşamada kendi yuvalarında kalır (K-7; parça pinindeki tercih uyarıyla uygulanır).
        kon = {p["gpio"] for p in kart["pinler"] if p["tur"] == "konnektor"}
        ped = {p["gpio"] for p in kart["pinler"] if p["tur"] == "ped"} - kon
        parca = {p["gpio"] for p in kart["parcalar"]} & (kon | ped)
        asamalar = [("konnektor", kon - parca)] + ([("ped", (kon | ped) - parca)] if ped - parca else []) \
            + ([("parca", kon | ped)] if parca else [])
        kilitli = {t["gpio"] for t in gecerli}
        for k, (asama, izinli) in enumerate(asamalar):
            ad = [[g for g in a if g in izinli or g in kilitli] for a in adaylar]
            r = self._asama(istek, yuva_bilgi, ad, uyarili, list(gecerli), list(sorunlar), yasak_notu,
                            k == len(asamalar) - 1)
            if r is None:
                continue
            if r.atama["durum"] == "mumkun_degil":
                r.neden = f"{kart['kisa_ad']} kartının konnektör ve pedlerine çıkan pinlerle: {r.neden}"
            kullanilan = {x["gpio"] for x in (r.atama["atamalar"] or (r.alternatif or {}).get("atamalar", []))}
            r.kart_ozeti = {"kart": kart["kisa_ad"], "asama": asama, "konnektor": len(kon), "ped": len(ped),
                            "kullanilan_ped": sorted(kullanilan & ped), "kullanilan_parca": sorted(kullanilan & parca)}
            return r
        raise AssertionError("son aşama her zaman sonuç döner")

    def _asama(self, istek, yuva_bilgi, adaylar, uyarili, gecerli, sorunlar, yasak_notu, son: bool) -> AtamaSonucu | None:
        """Verilen adaylarla atama. son=False iken çözüm yoksa ya da bir tercih yer bulamıyorsa None (sonraki kart
        aşaması denenir); son=True iken her zaman sonuç."""
        bos = [i for i, a in enumerate(adaylar) if not a]
        if bos and not son:
            return None
        if bos:
            nid, arayuz, sinyal = yuva_bilgi[bos[0]]
            return AtamaSonucu({"durum": "mumkun_degil", "atamalar": []},
                               f"{arayuz} ({nid}) {sinyal} sinyali için {istek['paket']} paketinde kullanılabilecek "
                               f"pin yok.{yasak_notu}".rstrip("."))

        tum = list(range(len(adaylar)))
        eslesme = _eslesme(tum, adaylar, set())
        if len(eslesme) < len(tum) and not son:
            return None
        if len(eslesme) < len(tum):
            birlesim = set().union(*adaylar)
            toplam = (f"Toplam {len(tum)} sinyal isteniyor, bu ihtiyaçlar için uygun pin sayısı {len(birlesim)} "
                      f"({istek['paket']}). İlk tıkanma: ")
            return AtamaSonucu({"durum": "mumkun_degil", "atamalar": []},
                               toplam + self._yetersizlik(istek, yuva_bilgi, adaylar, eslesme) + yasak_notu.rstrip("."))

        secim = self._coz(adaylar, uyarili, yuva_bilgi, gecerli)
        if secim is None and not son:
            return None
        if secim is None:                                    # kilitli tercihlerle çözüm yok: bozanları bul
            for t in list(gecerli):
                if self._coz(adaylar, uyarili, yuva_bilgi, [t]) is None:
                    gecerli.remove(t)
                    sorunlar.append(self._yer_yok(istek, t, yuva_bilgi, adaylar, tek=True))
            while (secim := self._coz(adaylar, uyarili, yuva_bilgi, gecerli)) is None:
                sorunlar.append(self._yer_yok(istek, gecerli.pop(), yuva_bilgi, adaylar, tek=False))

        def atama_listesi(sec):
            return [{"ihtiyac_id": nid, "sinyal": s, "gpio": sec[i]} for i, (nid, _, s) in enumerate(yuva_bilgi)]

        uy = sorted(g for g in secim.values() if g in uyarili)
        if sorunlar:
            return AtamaSonucu({"durum": "tercih_uygulanamadi", "atamalar": []}, uyarili_pin=uy,
                               tercih_sorunlari=sorunlar, uygulanan_tercihler=gecerli,
                               alternatif={"durum": "atandi", "atamalar": atama_listesi(secim)})
        return AtamaSonucu({"durum": "atandi", "atamalar": atama_listesi(secim)}, uyarili_pin=uy,
                           uygulanan_tercihler=gecerli)

    # ------------------------------------------------------------------ tercihler
    @staticmethod
    def _eslesen_yuvalar(t: dict, yuva_bilgi) -> list[int]:
        return [y for y, (_, a, s) in enumerate(yuva_bilgi) if a == t["arayuz"] and (not t.get("sinyal") or s == t["sinyal"])]

    def _tercih_on_denetimi(self, istek: dict, yuva_bilgi, adaylar) -> tuple[list[dict], list[dict]]:
        v, paket, baglam = self.veri, istek["paket"], istek["baglam"]
        yasak = set(istek.get("kullanilmayacak", ()))
        gecerli, sorunlar, goruldu = [], [], {}
        kart = istek.get("kart")
        cikan = {p["gpio"] for p in kart["pinler"]} if kart else set()

        def sorun(t, kod, neden, oneri):
            sorunlar.append({"tercih": t, "kod": kod, "neden": neden, "oneri": oneri})

        for t in istek.get("pin_tercihleri", ()):
            t = {"arayuz": t["arayuz"], "sinyal": t.get("sinyal") or "", "gpio": t["gpio"]}
            g = t["gpio"]
            if t["arayuz"] not in {a for _, a, _ in yuva_bilgi}:
                sorun(t, "IHTIYAC_YOK", f"İhtiyaçlarda {t['arayuz']} yok.", "Tercihi ilgili ihtiyaçla birlikte yaz.")
                continue
            if t["sinyal"] and t["sinyal"] not in v.arayuzler[t["arayuz"]]["sinyaller"]:
                sorun(t, "SINYAL_YOK", f"{t['sinyal']}, {t['arayuz']} arayüzünün sinyali değil.",
                      f"Sinyallerden birini yaz: {', '.join(v.arayuzler[t['arayuz']]['sinyaller'])}.")
                continue
            if g in yasak:
                sorun(t, "YASAKLA_CAKISMA", f"GPIO{g} hem tercih edildi hem kullanılmayacak denildi.",
                      "İkisinden birini kaldır.")
                continue
            if g in goruldu:                                  # birebir aynı tercih de: iki ihtiyaç tek pine istenmiş
                sorun(t, "AYNI_PIN", f"GPIO{g} iki tercihte birden: {tercih_adi(goruldu[g])} ve {tercih_adi(t)}; "
                      "bir pin tek sinyale atanır.", "Her ihtiyaca ayrı bir pin yaz.")
                continue
            hatalar = [i for i in pin_ihlalleri(v, paket, g, baglam) if i.seviye == "hata"]
            if hatalar:
                ek = (f" Kartta {', '.join(k['ad'] + ' ' + k['aciklama'] for k in kart['usb_uart'])} UART0'a bağlı."
                      if kart and kart["usb_uart"] and hatalar[0].kod == "PIN_UART0" else "")
                sorun(t, hatalar[0].kod, turkce(hatalar[0]) + ek, ONERI.get(hatalar[0].kod, "Başka bir pin seç."))
                continue
            if kart and g not in cikan:
                uygun = sorted(x for x in cikan if not any(i.seviye == "hata" for i in pin_ihlalleri(v, paket, x, baglam)))
                sorun(t, "KART_PIN_YOK", f"GPIO{g}: {kart['kisa_ad']} kartında konnektöre ya da pede çıkmıyor.",
                      f"Kartta çıkan bir pin seç: {pin_listesi(uygun)}.")
                continue
            sinyaller = [t["sinyal"]] if t["sinyal"] else v.arayuzler[t["arayuz"]]["sinyaller"]
            gidebilir = set().union(*(v.aday_gpio(paket, t["arayuz"], s) for s in sinyaller))
            if g not in gidebilir:
                uygun = {x for x in gidebilir if not any(i.seviye == "hata" for i in pin_ihlalleri(v, paket, x, baglam))}
                ne = f"{t['arayuz']}{' ' + t['sinyal'] if t['sinyal'] else ''}"
                kaynak = ""
                for s in sinyaller:
                    sabit = v.sabit_sinyaller.get((t["arayuz"], s))
                    if sabit:
                        kaynak = f" [{kaynak_metni(sabit['referans'], sabit['sayfa'])}]"
                sorun(t, "SABIT_PIN", f"{ne}: GPIO{g} olamaz; yalnız {pin_listesi(gidebilir)}.{kaynak}",
                      f"{ne} için şu pinlerden birini seç: {pin_listesi(uygun)}.")
                continue
            yuvalar = self._eslesen_yuvalar(t, yuva_bilgi)
            ayni_grup = [x for x in gecerli if x["arayuz"] == t["arayuz"] and x["sinyal"] == t["sinyal"]]
            ayni_arayuz = [x for x in gecerli if x["arayuz"] == t["arayuz"]]
            arayuz_yuvasi = sum(1 for _, a, _ in yuva_bilgi if a == t["arayuz"])
            if len(ayni_grup) >= len(yuvalar) or len(ayni_arayuz) >= arayuz_yuvasi:
                fazla = (f"{t['arayuz']}{' ' + t['sinyal'] if t['sinyal'] else ''} için {len(ayni_grup) + 1} pin "
                         f"tercihi var, {len(yuvalar)} sinyal var." if len(ayni_grup) >= len(yuvalar) else
                         f"{t['arayuz']} için {len(ayni_arayuz) + 1} pin tercihi var, {arayuz_yuvasi} sinyal var.")
                sorun(t, "FAZLA_TERCIH", fazla, "Fazla pini kaldır.")
                continue
            goruldu[g] = t
            gecerli.append(t)
        return gecerli, sorunlar

    def _yer_yok(self, istek, t, yuva_bilgi, adaylar, tek: bool) -> dict:
        """Kilitlenince çözümü bozan tercih: o pini isteyebilecek sabit pinli ihtiyaçlar varsa adlarıyla."""
        sabit = Counter(a for a, _ in sorted({(a, nid) for y, (nid, a, s) in enumerate(yuva_bilgi)
                                              if a != t["arayuz"] and t["gpio"] in adaylar[y]
                                              and self.veri.arayuzler[a]["yonlendirme"] == "SABIT"}))
        sabitler = [f"{n} {a}" for a, n in sorted(sabit.items())]
        neden = (f"GPIO{t['gpio']} {t['arayuz']} için ayrılırsa kalan ihtiyaçlara yetecek uygun pin kalmıyor"
                 if tek else f"GPIO{t['gpio']} öteki tercihlerle birlikte uygulanınca kalan ihtiyaçlara yetecek uygun "
                 "pin kalmıyor")
        if sabitler:
            neden += f"; bu pine sabit pinli {', '.join(sabitler)} de muhtaç"
        return {"tercih": t, "kod": "YER_YOK", "neden": neden + ".",
                "oneri": "Başka bir pin seç ya da bu tercihi kaldır."}

    def _coz(self, adaylar, uyarili, yuva_bilgi, tercihler: list[dict]) -> dict[int, int] | None:
        """Tercihleri yuvalara kilitleyip kalanını en az uyarılı çöz; çözüm yoksa None. Tercih → yuva seçimi
        geri izlemeyle; eşdeğer yuvalardan (aynı arayüz, sinyal, adaylar) yalnız ilki denenir."""
        kilit: dict[int, int] = {}

        def yerlestir(k: int) -> dict[int, int] | None:
            if k == len(tercihler):
                pinler = set(kilit.values())
                ad = [[kilit[y]] if y in kilit else [g for g in a if g not in pinler] for y, a in enumerate(adaylar)]
                return self._serbest(ad, uyarili)
            t, denenen = tercihler[k], set()
            for y in self._eslesen_yuvalar(t, yuva_bilgi):
                anahtar = (yuva_bilgi[y][1], yuva_bilgi[y][2], tuple(adaylar[y]))
                if y in kilit or t["gpio"] not in adaylar[y] or anahtar in denenen:
                    continue
                denenen.add(anahtar)
                kilit[y] = t["gpio"]
                sonuc = yerlestir(k + 1)
                if sonuc is not None:
                    return sonuc
                del kilit[y]
            return None

        return yerlestir(0)

    def _serbest(self, adaylar, uyarili) -> dict[int, int] | None:
        tum = list(range(len(adaylar)))
        if len(_eslesme(tum, adaylar, set())) < len(tum):
            return None
        temiz = [[g for g in a if g not in uyarili] for a in adaylar]
        alt_sinir = len(tum) - len(_eslesme(tum, temiz, set()))   # en az bu kadar uyarılı pin gerekir
        for k in range(alt_sinir, len(tum) + 1):
            secim = self._ara(adaylar, temiz, uyarili, k)
            if secim is not None:
                return secim
        raise AssertionError("eşleşme var ama arama çözüm bulamadı")   # eşleşme varsa k = yuva sayısında bulunur

    def _ara(self, adaylar: list[list[int]], temiz: list[list[int]], uyarili: set[int], k: int) -> dict[int, int] | None:
        secim: dict[int, int] = {}
        dolu: set[int] = set()

        def adim(uyari_sayisi: int) -> bool:
            kalan = [i for i in range(len(adaylar)) if i not in secim]
            if not kalan:
                return True
            if len(_eslesme(kalan, adaylar, dolu)) < len(kalan):
                return False
            # kalan yuvalar için gereken en az uyarılı pin (yalnız temiz pinlerle eşleşemeyenler)
            if uyari_sayisi + len(kalan) - len(_eslesme(kalan, temiz, dolu)) > k:
                return False
            # en az adayı kalan yuva önce (eşitlikte sıra)
            y = min(kalan, key=lambda i: (sum(g not in dolu for g in adaylar[i]), i))
            for g in adaylar[y]:
                if g in dolu:
                    continue
                ek = g in uyarili
                if uyari_sayisi + ek > k:
                    continue
                secim[y], _ = g, dolu.add(g)
                if adim(uyari_sayisi + ek):
                    return True
                del secim[y]
                dolu.discard(g)
            return False

        return dict(secim) if adim(0) else None

    @staticmethod
    def _yetersizlik(istek, yuva_bilgi, adaylar, eslesme) -> str:
        """Eşleşmeyen bir yuvadan alternatif yollarla ulaşılan yuvalar ve pinler (Hall koşulunu bozan küme)."""
        gpio_yuva = {g: y for y, g in eslesme.items()}
        bas = next(i for i in range(len(adaylar)) if i not in eslesme)
        yuvalar, pinler, kuyruk = {bas}, set(), [bas]
        while kuyruk:
            y = kuyruk.pop()
            for g in adaylar[y]:
                if g not in pinler:
                    pinler.add(g)
                    if g in gpio_yuva and gpio_yuva[g] not in yuvalar:
                        yuvalar.add(gpio_yuva[g])
                        kuyruk.append(gpio_yuva[g])
        ihtiyac = Counter(a for a, _ in sorted({yuva_bilgi[y][1::-1] for y in yuvalar}))   # arayüz → ihtiyaç sayısı
        kimler = ", ".join(f"{n} {a}" for a, n in sorted(ihtiyac.items()))
        return (f"{len(yuvalar)} sinyal için yalnız {len(pinler)} uygun pin var ({istek['paket']}; {kimler}). "
                f"Uygun pinler: {', '.join(f'GPIO{g}' for g in sorted(pinler))}")

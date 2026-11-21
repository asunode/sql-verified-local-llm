"""Model çağrıları: A (Türkçe istekten ihtiyaç listesi) ve B (pin atama). İkisi de çekirdeğin döngüsüyle.

İstem düzeni: sistem mesajı sabit talimatla başlar (istemler/*.txt) ve `sabit_onek` olarak verilir; değişen
veri (istek, pin tablosu, ihtiyaçlar) ondan sonra, kullanıcı mesajında gelir. Çağrı A'nın sistem mesajına
arayüz listesi veritabanından eklenir; bu liste istekten istekte değişmez.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from asu_llmcore import Ihlal, OllamaAyar, Sonuc, calistir

from . import semalar
from .denetim import Denetleyici, pin_ihlalleri
from .pinveri import PinVerisi
from .sozluk import IstekSozlugu, dayanak_bul

ISTEMLER = Path(__file__).resolve().parent / "istemler"
EN_COK_TUR = 3                       # T-9: pilot ölçümleri en_cok_tur=3 ile
MODEL = "gemma4:12b-it-qat"


def ayar(onbellek_siniri: bool = True) -> OllamaAyar:
    return OllamaAyar(model=MODEL, num_gpu=0, onbellek_siniri=onbellek_siniri)


def _istem(ad: str) -> str:
    return (ISTEMLER / ad).read_text(encoding="utf-8").strip()


# ------------------------------------------------------------------ Çağrı A
def ihtiyac_sistemi(veri: PinVerisi, sozluk: IstekSozlugu) -> str:
    """Sabit talimat + arayüz listesi, soru konuları ve eksik kodları (veritabanından; istekten istekte değişmez)."""
    satirlar = [_istem("ihtiyac_sistem.txt"), "", "Interfaces (name: signals; meaning):"]
    for ad in semalar.ARAYUZLER:
        a = veri.arayuzler[ad]
        satirlar.append(f"- {ad}: {', '.join(a['sinyaller'])}; {a['tanim']}")
    satirlar += ["", "Question topics (konu: meaning):"]
    satirlar += [f"- {k['konu']}: {k['model_tanimi']}" for k in sozluk.soru_konulari]
    satirlar += ["", "Missing-information codes (eksik: meaning):"]
    satirlar += [f"- {e}: {sozluk.mesaj('eksik.' + e)['model_tanimi']}" for e in sozluk.eksik_kodlari]
    return "\n".join(satirlar)


SOZCUK_KARAKTERI = re.compile(r"\w")
CUMLE = re.compile(r"[^.!?]+[.!?]*")


def yonelme_eki(n: int) -> str:
    """Sayının okunuşuna göre yönelme eki: GPIO3'e, GPIO2'ye, GPIO6'ya, GPIO10'a, GPIO20'ye."""
    birler = {0: "'a", 1: "'e", 2: "'ye", 3: "'e", 4: "'e", 5: "'e", 6: "'ya", 7: "'ye", 8: "'e", 9: "'a"}
    onlar = {10: "'a", 20: "'ye", 30: "'a", 40: "'a", 50: "'ye", 60: "'a", 70: "'e", 80: "'e", 90: "'a"}
    return birler[n % 10] if n % 10 or n == 0 else onlar.get(n % 100, "'e")


def sinirda(metin: str, bas: int, son: int) -> bool:
    """metin[bas:son] sözcük sınırında mı başlayıp bitiyor ("16 buton" içinden "6 buton" değil). Parçanın kenarı zaten
    sözcük karakteri değilse (tırnak, ayraç) o kenar sınır sayılır; kesme işaretinden sonraki ek ayrı sözcüktür."""
    def kenar(i: int, j: int) -> bool:
        return not (0 <= j < len(metin) and SOZCUK_KARAKTERI.match(metin[i]) and SOZCUK_KARAKTERI.match(metin[j]))
    return son > bas and kenar(bas, bas - 1) and kenar(son - 1, son)


def adet_tutar(n: dict, sayilar: set[int]) -> bool:
    """Adet dayanaktaki sayılardan birine eşit mi; model_cikarimi kalemde tam katı da olur (cihaz başına birden çok
    hat, L-4 kararı). istekte_acik kalemde eşitlik katı."""
    if n["kaynak"] == "model_cikarimi":
        return any(n["adet"] % d == 0 for d in sayilar)
    return n["adet"] in sayilar


def ihtiyac_denetleyici(metin: str, arayuzler: list[str], sozluk: IstekSozlugu, baglam: dict | None = None):
    """Kod denetimi: dayanak istekte mi (birebir ya da esnek eşleşme; esnekse metindeki gerçek parçayla değiştirilir),
    arayüz listede mi, adet dayanaktaki sayıyla uyumlu mu, durum alanlarla tutarlı mı, metindeki her GPIO bahsi pin
    listelerinden birinde mi ve listelerde metinde olmayan GPIO var mı (K-7); soruların metni istekte mi, bağlam ifadesinin
    konusu bağlam sözlüğünde mi, eksik kodları durumla tutarlı mı (K-8). Adım 10a: dayanak sözcük sınırında mı; adet,
    dayanağın değdiği sayının metindeki tamamıyla ("altı buton" → "On altı" = 16) uyumlu mu; diger_ifadeler'in metni
    istekte mi. Uyarılar: model çıkarımı; esnek dayanak; belirsiz pin bahsi; bağlam ifadesi komut satırı bağlamıyla
    çelişiyor (T-27); dayanak sayının bir kısmını içeriyor; diger_ifadeler öğesinde sayı, arayüz adı ya da pin bahsi var.
    Adım 10b: diger_ifadeler öğesi kart bağlamıysa hata (DIGER_BAGLAM); diger_pin_bahisleri'ndeki GPIO, tercihsiz bir
    ihtiyacın dayanağıyla aynı cümledeyse uyarı (DIGER_PIN_TERCIH_IZI). Adım 11: hiçbir dayanakla örtüşmeyen cümle
    uyarısı (KAPSANMAYAN_CUMLE). Adım 11a: bir ihtiyacın dayanağında ya da dayanağın cümlesinde desteklenmeyen özellik
    adı (DESTEKLENMEYEN_OZELLIK, hata). Adım 12: SPI dayanağının cümlesinde cihaz sayısı adetten büyük (SPI_ADET_IZI,
    uyarı).
    """
    bahisler = sozluk.pin_bahisleri(metin)
    metin_sayilari = sozluk.sayi_araliklari(metin)
    gpio_bahsi = {b.gpio: b for b in bahisler if b.tur != "belirsiz"}
    belirsiz = [b for b in bahisler if b.tur == "belirsiz"]

    def dayanak_denetle(n: dict, alan: str, ihlaller: list[Ihlal], anahtar: str = "dayanak") -> list[tuple[int, int]]:
        """Dayanağın metinde sözcük sınırındaki konumları (bas, son); geçmiyorsa ya da hiçbir konumu sınırda değilse
        boş liste ve hata."""
        gercek = dayanak_bul(metin, n[anahtar])
        if gercek is None:
            ipucu = (" For a GPIO number in a list, the number alone as written is enough."
                     if alan.startswith(tuple(semalar.PIN_LISTELERI)) else "")
            ihlaller.append(Ihlal("DAYANAK_YOK", f"{anahtar} '{n[anahtar]}' does not occur verbatim in the "
                                  "description; copy one continuous part with the exact characters and do not "
                                  f"leave out any word.{ipucu}", f"{alan}/{anahtar}"))
            return []
        if gercek != n[anahtar]:
            ihlaller.append(Ihlal("ESNEK_DAYANAK", f"«{n[anahtar]}» → «{gercek}»", f"{alan}/{anahtar}", "uyari"))
            n[anahtar] = gercek
        konumlar = [(b, b + len(gercek)) for b in _konumlar(metin, gercek)]
        sinirdaki = [(b, e) for b, e in konumlar if sinirda(metin, b, e)]
        if not sinirdaki:
            b, e = konumlar[0]
            while b > 0 and SOZCUK_KARAKTERI.match(metin[b - 1]):
                b -= 1
            while e < len(metin) and SOZCUK_KARAKTERI.match(metin[e]):
                e += 1
            ihlaller.append(Ihlal("DAYANAK_SINIRI", f"{anahtar} '{gercek}' starts or ends inside a word of the "
                                  f"description ('{metin[b:e]}'); copy whole words.", f"{alan}/{anahtar}"))
        return sinirdaki

    def sayi_denetle(n: dict, alan: str, konumlar: list[tuple[int, int]], ihlaller: list[Ihlal]) -> None:
        """Dayanağın değdiği sayı ifadeleri metindeki tamamlarıyla okunur ("altı buton", metinde "On altı buton" → 16).
        Bir konumda adet uyuyorsa o konum esas alınır; hiçbirinde uymuyorsa SAYI_UYUSMAZ. Paylaşımlı hatta sayı
        cihaz sayısıdır, denetlenmez."""
        if n["arayuz"] in sozluk.paylasimli:
            return
        sonuclar = []                                   # (uyuyor mu, sayı ifadeleri, yarım alınanlar)
        for bas, son in konumlar:
            ortusen = [x for x in metin_sayilari if x.bas < son and bas < x.son and x.deger > 0]
            if ortusen:
                sonuclar.append((adet_tutar(n, {x.deger for x in ortusen}), ortusen,
                                 [x for x in ortusen if x.bas < bas or x.son > son]))
        if not sonuclar:
            return
        uyan = next((x for x in sonuclar if x[0]), None)
        if uyan is None:
            _, ortusen, yarim = sonuclar[0]
            ifadeler = ", ".join(f"'{x.ifade}' = {x.deger}" for x in ortusen)
            istenen = ("equal to the count in dayanak, or a whole multiple of it when each device needs several "
                       "lines" if n["kaynak"] == "model_cikarimi" else "equal to the count in dayanak")
            ek = (" The description writes the whole number as " + ", ".join(f"'{metin[x.bas:x.son]}'" for x in yarim)
                  + "; include all of it in dayanak." if yarim else "")
            ihlaller.append(Ihlal("SAYI_UYUSMAZ", f"dayanak '{n['dayanak']}' gives the count {ifadeler}, but adet "
                                  f"is {n['adet']}. Make adet {istenen}.{ek}", f"{alan}/adet"))
        else:                                           # Adım 10c: yalnız dayanaktaki değer tam değerden farklıysa
            dayanakta = {x.deger for x in sozluk.sayi_araliklari(n["dayanak"])}
            farkli = [x for x in uyan[2] if x.deger not in dayanakta]      # "çift" / "Bir çift" aynı: uyarı yok
            if farkli:
                ihlaller.append(Ihlal("SAYI_YARIM", f"«{n['dayanak']}» sayının yalnız bir kısmını içeriyor; metinde "
                                      + ", ".join(f"«{metin[x.bas:x.son]}» = {x.deger}" for x in farkli)
                                      + f" yazıyor (adet {n['adet']} buna uygun).", f"{alan}/dayanak", "uyari"))

    def diger_uyarisi(ifade: str, alan: str) -> Ihlal | None:
        """diger_ifadeler öğesi ihtiyaç izi taşıyorsa kullanıcıya görünür uyarı: sayı, arayüz adı (eş adlar dahil) ya da
        pin bahsi."""
        nedenler = [f"sayı «{ifade[x.bas:x.son]}»" for x in sozluk.sayi_araliklari(ifade)
                    if x.ifade != "bir"]                            # tek başına "bir" tetiklemez (Adım 10b)
        nedenler += [f"arayüz adı ({a})" for a in sozluk.arayuz_adlari(ifade, arayuzler)]
        nedenler += [f"pin bahsi «{b.metin}»" for b in sozluk.pin_bahisleri(ifade)]
        if not nedenler:
            return None
        return Ihlal("DIGER_IHTIYAC_IZI", f"«{ifade}» pin ihtiyacı olarak alınmadı; içinde {', '.join(nedenler)} var. "
                     "Pin gerektiriyorsa ayrı ve açık bir cümleyle yaz.", alan, "uyari")

    def denetle(y: dict) -> list[Ihlal]:
        ihlaller = []
        for i, n in enumerate(y["ihtiyaclar"]):
            if n["arayuz"] not in arayuzler:
                ihlaller.append(Ihlal("ARAYUZ_BILINMEYEN", f"'{n['arayuz']}' is not in the interface list.",
                                      f"ihtiyaclar/{i}/arayuz"))
            konumlar = dayanak_denetle(n, f"ihtiyaclar/{i}", ihlaller)
            sayi_denetle(n, f"ihtiyaclar/{i}", konumlar, ihlaller)
            if n["kaynak"] == "model_cikarimi":
                ihlaller.append(Ihlal("MODEL_CIKARIMI", f"{n['arayuz']} was inferred by the model from "
                                      f"'{n['dayanak']}'.", f"ihtiyaclar/{i}", "uyari"))
        ihlaller += desteklenmeyen_izleri(y)
        for i, q in enumerate(y.get("sorular", [])):
            dayanak_denetle(q, f"sorular/{i}", ihlaller, "soru")
        ihlaller += pin_listesi_ihlalleri(y, dayanak_denetle)
        for i, ifade in enumerate(y["baglam_ifadeleri"]):
            if not sozluk.baglam_oku(ifade):
                ihlaller.append(Ihlal("BAGLAM_KONUSUZ", f"'{ifade}' is not board context (JTAG debugging, USB, UART0 "
                                      "console, flash power supply); move it from baglam_ifadeleri to diger_ifadeler. "
                                      "A question goes into sorular.", f"baglam_ifadeleri/{i}"))
        for i, ifade in enumerate(y.get("diger_ifadeler", [])):
            q = {"ifade": ifade}
            if dayanak_denetle(q, f"diger_ifadeler/{i}", ihlaller, "ifade"):
                y["diger_ifadeler"][i] = q["ifade"]
                if sozluk.baglam_oku(q["ifade"]):
                    ihlaller.append(Ihlal("DIGER_BAGLAM", f"'{q['ifade']}' is board context (JTAG debugging, USB, "
                                          "UART0 console, flash power supply); move it from diger_ifadeler to "
                                          "baglam_ifadeleri.", f"diger_ifadeler/{i}"))
                    continue
                uyari = diger_uyarisi(q["ifade"], f"diger_ifadeler/{i}")
                if uyari is not None:
                    ihlaller.append(uyari)
        d = y["durum"]
        if d == "emin_degilim" and not y.get("eksik"):
            ihlaller.append(Ihlal("DURUM_TUTARSIZ", "With durum 'emin_degilim', give the reasons in eksik.", "eksik"))
        if d != "emin_degilim" and y.get("eksik"):
            ihlaller.append(Ihlal("DURUM_TUTARSIZ", "eksik must be empty unless durum is 'emin_degilim'.", "eksik"))
        if d == "tamam" and y["desteklenmeyenler"]:          # tamam + boş ihtiyaç listesi geçerli: pin gerekmiyor
            ihlaller.append(Ihlal("DURUM_TUTARSIZ", "With durum 'tamam', desteklenmeyenler must be empty.", "durum"))
        if d == "desteklenmiyor" and not y["desteklenmeyenler"]:
            ihlaller.append(Ihlal("DURUM_TUTARSIZ", "With durum 'desteklenmiyor', list the unsupported parts in "
                                  "desteklenmeyenler.", "durum"))
        ihlaller += kapsanmayan_cumleler(y)
        ihlaller += spi_adet_izleri(y)
        if baglam is not None:
            for i, ifade in enumerate(y["baglam_ifadeleri"]):
                for anahtar, deger in sozluk.baglam_oku(ifade).items():
                    if anahtar in baglam and baglam[anahtar] != deger:
                        ihlaller.append(Ihlal("BAGLAM_CELISKI", baglam_celiski_mesaji(ifade, anahtar, deger,
                                                                                        baglam[anahtar]),
                                              f"baglam_ifadeleri/{i}", "uyari"))
        return ihlaller

    def pin_listesi_ihlalleri(y: dict, dayanak_denetle) -> list[Ihlal]:
        ihlaller = []
        listede: dict[int, str] = {}
        ihtiyac_arayuzleri = {n["arayuz"] for n in y["ihtiyaclar"]}
        for liste in semalar.PIN_LISTELERI:
            for i, p in enumerate(y.get(liste, [])):
                alan = f"{liste}/{i}"
                dayanak_denetle(p, alan, ihlaller)
                listede.setdefault(p["gpio"], alan)
                if p["gpio"] in gpio_bahsi:
                    continue
                b = next((b for b in belirsiz if b.gpio == p["gpio"]), None)
                if b is not None and liste == "pin_tercihleri":
                    ihlaller.append(Ihlal("BELIRSIZ_PIN_TERCIHI", f"'{b.metin}' is not a GPIO number; do not use it "
                                          "as a pin preference.", f"{alan}/gpio"))
                else:
                    ihlaller.append(Ihlal("PIN_UYDURMA", f"GPIO{p['gpio']} is not written in the description; list "
                                          "only GPIO numbers that occur in it.", f"{alan}/gpio"))
            if liste == "pin_tercihleri":
                for i, p in enumerate(y.get(liste, [])):
                    if p["arayuz"] not in ihtiyac_arayuzleri:
                        ihlaller.append(Ihlal("TERCIH_IHTIYACSIZ", f"pin_tercihleri entry for {p['arayuz']} on "
                                              f"GPIO{p['gpio']}, but ihtiyaclar has no {p['arayuz']} entry.",
                                              f"{liste}/{i}/arayuz"))
                    elif p["sinyal"] and p["sinyal"] not in semalar.ARAYUZLER[p["arayuz"]]:
                        ihlaller.append(Ihlal("TERCIH_SINYAL", f"'{p['sinyal']}' is not a signal of {p['arayuz']} "
                                              f"({', '.join(semalar.ARAYUZLER[p['arayuz']])}); use one of them or "
                                              "\"\".", f"{liste}/{i}/sinyal"))
        # Sorunun içindeki GPIO bahsi listelere girmez, soru taşır (K-8); GPIO soru dışında da geçiyorsa listede olmalı.
        soru_araliklari = [(m, m + len(q["soru"])) for q in y.get("sorular", []) for m in _konumlar(metin, q["soru"])]
        soru_disi = {x.gpio for x in bahisler if x.tur != "belirsiz"
                     and not any(bas <= x.bas < son for bas, son in soru_araliklari)}
        for g, b in sorted(gpio_bahsi.items()):
            if g not in listede and g in soru_disi:
                ihlaller.append(Ihlal("PIN_BAHSI_ATLANDI", f"GPIO{g} is mentioned in the description ('{b.metin}') "
                                      "but is in none of pin_tercihleri, kullanilmayacak_pinler, diger_pin_bahisleri.",
                                      "pin_tercihleri"))
        for b in belirsiz:
            ihlaller.append(Ihlal("BELIRSIZ_PIN_BAHSI", f"'{b.metin}' belirsiz; GPIO numarasıyla yaz.", "", "uyari"))
        ihlaller += diger_pin_tercih_izleri(y)
        return ihlaller

    def desteklenmeyen_izleri(y: dict) -> list[Ihlal]:
        """Adım 11a: ihtiyaç dayanağının geçtiği cümlede (dayanak dahil) `desteklenmeyen_ozellik` adı varsa hata. Ad
        yalnız diger_ifadeler'in cümlesindeyse ("Ethernet değil Wi-Fi kullanacağım") hata yok."""
        cumleler = [(m.start(), m.end()) for m in CUMLE.finditer(metin)]
        sonuc, gorulen = [], set()
        for i, n in enumerate(y["ihtiyaclar"]):
            for b in _konumlar(metin, n["dayanak"]):
                e = b + len(n["dayanak"])
                cb = min((c for c, d in cumleler if c <= b < d), default=0)
                cs = max((d for c, d in cumleler if c < e <= d), default=len(metin))
                for r, ad in sozluk.desteklenmeyen_bul(metin[cb:cs]):
                    if r["terim"] not in gorulen:
                        gorulen.add(r["terim"])
                        sonuc.append(Ihlal("DESTEKLENMEYEN_OZELLIK", f"'{ad}' is not available on this chip "
                                           f"({r['belge']} {r['surum']}: not in the peripheral list, p. {r['sayfa']}); "
                                           "put it into desteklenmeyenler and set durum to desteklenmiyor.",
                                           f"ihtiyaclar/{i}/dayanak"))
        return sonuc

    def kapsanmayan_cumleler(y: dict) -> list[Ihlal]:
        """Adım 11: istek ". ! ?" ile cümlelere bölünür; hiçbir dayanakla (ihtiyaç, üç pin listesi, soru, bağlam ve diğer
        ifadeler, desteklenmeyenler) örtüşmeyen cümle uyarı alır. Tur açmaz, kararı değiştirmez. Adım 11a: durum
        emin_degilim ise uygulanmaz (istek bütünüyle eksik kodlarıyla değerlendirildi)."""
        if y["durum"] == "emin_degilim":
            return []
        parcalar = [n["dayanak"] for n in y["ihtiyaclar"]]
        parcalar += [p["dayanak"] for liste in semalar.PIN_LISTELERI for p in y.get(liste, [])]
        parcalar += [q["soru"] for q in y.get("sorular", [])]
        parcalar += [*y["baglam_ifadeleri"], *y.get("diger_ifadeler", []), *y["desteklenmeyenler"]]
        araliklar = [(b, b + len(x)) for x in parcalar for b in _konumlar(metin, x)]
        sonuc = []
        for no, m in enumerate(CUMLE.finditer(metin)):
            cumle = m.group().strip()
            if SOZCUK_KARAKTERI.search(cumle) and not any(b < m.end() and m.start() < e for b, e in araliklar):
                sonuc.append(Ihlal("KAPSANMAYAN_CUMLE", f"«{cumle}» hiçbir şekilde değerlendirilmedi; pin ihtiyacı "
                                   "içeriyorsa ayrı ve açık bir cümleyle yaz.", f"cumle/{no}", "uyari"))
        return sonuc

    def cihaz_sayisi_mi(x, haric: list[tuple[int, int]]) -> bool:
        """Sayı ifadesi bir cihazın önünde mi: başka bir ihtiyacın dayanağında ya da pin bahsinde değil, ardından başka
        bir sayı gelmiyor, ondalık ya da "16 x 2" parçası değil, ardından birim gelmiyor, (arayüz adı atlanarak) ardından
        hat sözcüğü gelmiyor."""
        if any(b < x.son and x.bas < e for b, e in haric):
            return False
        if any(z.bas > x.son and not metin[x.son:z.bas].strip() for z in metin_sayilari):
            return False                                # bitişik sayı bağımsız değil: "tek bir" bir ifade
        sonra, once = metin[x.son:x.son + 40], metin[max(0, x.bas - 6):x.bas]
        if re.match(r"[.,]\d", sonra) or re.search(r"\d[.,]$", once) or re.search(r"\d\s*[x×*]\s*$", once):
            return False
        ss = re.findall(r"\w+|[×*]", sonra)
        if not ss or (len(ss) > 1 and ss[0] in ("x", "×", "*") and ss[1].isdigit()):
            return False
        if sozluk.sayi_disi_mi(ss[0], "birim"):
            return False
        while ss and sozluk.arayuz_adlari(ss[0], arayuzler):
            ss.pop(0)
        return not ss or not any(sozluk.sayi_disi_mi(" ".join(ss[:k]), "hat") for k in (1, 2) if len(ss) >= k)

    def spi_adet_izleri(y: dict) -> list[Ihlal]:
        """Adım 12 (Z20 türü): SPI ihtiyacının dayanağının geçtiği cümlede cihazların önünde birden çok bağımsız sayı
        ifadesi var ("bir X ve bir Y") ve toplamları o cümledeki SPI adetlerinin toplamından büyük: uyarı (her cihaz ayrı
        CS ister). Birim, ondalık, "16 x 2", hat sözcüğü, pin bahsi ve başka ihtiyacın dayanağındaki sayılar sayılmaz;
        üç ya da daha çok sayıdan biri ötekilerin toplamına eşitse toplamdır, döküm ayrıca sayılmaz. Yalnız SPI: I2C'de
        seçim pini yok, adet pin sayısını değiştirmez."""
        cumleler = [(m.start(), m.end()) for m in CUMLE.finditer(metin)]
        haric = [(b, b + len(n["dayanak"])) for n in y["ihtiyaclar"] if n["arayuz"] != "SPI"
                 for b in _konumlar(metin, n["dayanak"])] + [(b.bas, b.son) for b in bahisler]
        araliklar: dict[tuple[int, int], list[int]] = {}
        for i, n in enumerate(y["ihtiyaclar"]):
            if n["arayuz"] != "SPI":
                continue
            for b in _konumlar(metin, n["dayanak"]):
                e = b + len(n["dayanak"])
                cb = min((c for c, d in cumleler if c <= b < d), default=0)
                cs = max((d for c, d in cumleler if c < e <= d), default=len(metin))
                if i not in araliklar.setdefault((cb, cs), []):
                    araliklar[(cb, cs)].append(i)
        sonuc = []
        for (cb, cs), idler in araliklar.items():
            sayilar = [x for x in metin_sayilari if cb <= x.bas and x.son <= cs and cihaz_sayisi_mi(x, haric)]
            cihaz, adet = sum(x.deger for x in sayilar), sum(y["ihtiyaclar"][i]["adet"] for i in idler)
            if len(sayilar) >= 3 and any(2 * x.deger == cihaz for x in sayilar):   # "Üç cihaz: iki X ve bir Y"
                cihaz //= 2
            if len(sayilar) >= 2 and cihaz > adet:
                sonuc.append(Ihlal("SPI_ADET_IZI", f"«{metin[cb:cs].strip()}» içinde {cihaz} cihaz görünüyor ama SPI "
                                   f"adedi {adet}; her cihaz ayrı CS ister. Doğruysa adetleri açık yaz.",
                                   f"ihtiyaclar/{idler[0]}/adet", "uyari"))
        return sonuc

    def diger_pin_tercih_izleri(y: dict) -> list[Ihlal]:
        """Y29 türü: diger_pin_bahisleri'ndeki GPIO'nun geçtiği cümlede, tercihi olmayan bir ihtiyacın dayanağı da
        geçiyor. Uyarı, hata değil ("LED'i GPIO2'den çıkardım" geçerli bir diğer bahis)."""
        tercihli = {t["arayuz"] for t in y.get("pin_tercihleri", [])}
        cumleler = [(m.start(), m.end()) for m in CUMLE.finditer(metin)]
        sonuc, gorulen = [], set()
        for i, p in enumerate(y.get("diger_pin_bahisleri", [])):
            g = p["gpio"]
            if g in gorulen:
                continue
            for b in (x for x in bahisler if x.tur != "belirsiz" and x.gpio == g):
                cb, cs = next(((cb, cs) for cb, cs in cumleler if cb <= b.bas < cs), (0, len(metin)))
                n = next((n for n in y["ihtiyaclar"] if n["arayuz"] not in tercihli
                          and any(cb <= k < cs for k in _konumlar(metin, n["dayanak"]))), None)
                if n is not None:
                    gorulen.add(g)
                    x = n["dayanak"] if len(n["dayanak"].split()) <= 2 else "X'i"
                    sonuc.append(Ihlal("DIGER_PIN_TERCIH_IZI", f"«{metin[cb:cs].strip()}» bir pin tercihi olabilir; "
                                       f"tercihse \"{x} GPIO{g}{yonelme_eki(g)} bağla\" biçiminde açık yaz.",
                                       f"diger_pin_bahisleri/{i}", "uyari"))
                    break
        return sonuc

    return denetle


def _konumlar(metin: str, parca: str) -> list[int]:
    """Parçanın metindeki tüm başlangıç konumları (dayanağı geçmeyen parça için boş)."""
    sonuc, i = [], metin.find(parca)
    while parca and i >= 0:
        sonuc.append(i)
        i = metin.find(parca, i + 1)
    return sonuc


BAGLAM_BAYRAGI = {"usb_serial_jtag": ("--usb", "--no-usb"), "uart0_konsol": ("--uart0-konsol", "--no-uart0-konsol"),
                  "jtag_pinleri": ("--jtag-pinleri", None), "harici_flash_beslemesi": ("--harici-flash-beslemesi", None)}
BAGLAM_ADI = {"usb_serial_jtag": "USB Serial/JTAG kullanımı", "uart0_konsol": "UART0 konsol",
              "jtag_pinleri": "JTAG pinleriyle hata ayıklama", "harici_flash_beslemesi": "flash'ın harici beslenmesi"}


def baglam_celiski_mesaji(ifade: str, anahtar: str, metindeki: bool, komut: bool) -> str:
    """Örnek: Metinde «JTAG ile hata ayıklayacağım» geçiyor (…: evet) ama --jtag-pinleri verilmedi; …"""
    evet, hayir = BAGLAM_BAYRAGI[anahtar]
    if hayir:
        bayrak = f"{evet if komut else hayir} verildi"
    else:
        bayrak = f"{evet} {'verildi' if komut else 'verilmedi'}"
    return (f"Metinde «{ifade}» geçiyor ({BAGLAM_ADI[anahtar]}: {'evet' if metindeki else 'hayır'}) ama {bayrak}; "
            "komut satırı esas alındı.")


def ihtiyac_cikar(istemci, veri: PinVerisi, metin: str, sozluk: IstekSozlugu, baglam: dict | None = None,
                  en_cok_tur: int = EN_COK_TUR) -> Sonuc:
    arayuzler = list(semalar.ARAYUZLER)
    sistem = ihtiyac_sistemi(veri, sozluk)
    # emin_degilim de denetlenir (K-8): bilgi_yok_mu verilmez, çekirdeğin BILGI_YOK kısa yolu (denetimsiz dönüş)
    # kullanılmaz. Denetimden geçen emin_degilim GECTI olur; durum yanıttan okunur (hat.a_durumu). Hata çıkarsa
    # düzeltme turu öteki durumlardaki gibi işler.
    return calistir(istemci, lambda: [{"role": "system", "content": sistem}, {"role": "user", "content": metin}],
                    semalar.ihtiyac_semasi(arayuzler, [k["konu"] for k in sozluk.soru_konulari], sozluk.eksik_kodlari),
                    ihtiyac_denetleyici(metin, arayuzler, sozluk, baglam), en_cok_tur, sabit_onek=sistem)


def genislet(ihtiyaclar: list[dict]) -> list[dict]:
    """Çağrı A kalemlerini adet kadar çoğaltır (adet yoksa 1); Çağrı B, atayıcı ve puanlama bu listeyle çalışır."""
    return [{"arayuz": n["arayuz"]} for n in ihtiyaclar for _ in range(n.get("adet", 1))]


def kimlik_ver(ihtiyaclar: list[dict]) -> list[dict]:
    """Çağrı A'nın ihtiyaçlarına okunur kimlik: adc_1, adc_2, i2c_1 …"""
    sayac: Counter = Counter()
    sonuc = []
    for n in ihtiyaclar:
        sayac[n["arayuz"]] += 1
        sonuc.append({"id": f"{n['arayuz'].lower()}_{sayac[n['arayuz']]}", "arayuz": n["arayuz"]})
    return sonuc


# ------------------------------------------------------------------ Çağrı B
def gpio_durumlari(veri: PinVerisi, paket: str, baglam: dict) -> dict[int, tuple[str, list[Ihlal]]]:
    """Paketteki her GPIO: (FREE | WARNING | FORBIDDEN, ihlaller). Bağlama göre."""
    sonuc = {}
    for g in sorted(veri.paket_gpio[paket]):
        ihl = pin_ihlalleri(veri, paket, g, baglam)
        durum = "FORBIDDEN" if any(i.seviye == "hata" for i in ihl) else "WARNING" if ihl else "FREE"
        sonuc[g] = (durum, ihl)
    return sonuc


BAGLAM_ACIKLAMA = {
    "usb_serial_jtag": "USB Serial/JTAG is used",
    "uart0_konsol": "UART0 is the console",
    "jtag_pinleri": "JTAG pins are used for debugging",
    "harici_flash_beslemesi": "the flash has an external power supply",
}


def atama_mesaji(veri: PinVerisi, istek: dict) -> str:
    paket, baglam = istek["paket"], istek["baglam"]
    s = [f"Package: {paket}",
         "Board context: " + "; ".join(f"{BAGLAM_ACIKLAMA[k]}: {'yes' if v else 'no'}" for k, v in baglam.items()),
         "", "GPIO states:"]
    for g, (durum, ihl) in gpio_durumlari(veri, paket, baglam).items():
        s.append(f"GPIO{g}: {durum}" + (f" ({', '.join(i.kod for i in ihl)})" if ihl else ""))
    arayuzler = list(dict.fromkeys(n["arayuz"] for n in istek["ihtiyaclar"]))
    s += ["", "Needs (id: interface, signals):"]
    for n in istek["ihtiyaclar"]:
        s.append(f"{n['id']}: {n['arayuz']}, signals {', '.join(veri.arayuzler[n['arayuz']]['sinyaller'])}")
    sabit = []
    for a in arayuzler:
        for sinyal in veri.arayuzler[a]["sinyaller"]:
            izinli = veri.sabit_izinli(paket, a, sinyal)
            if izinli is not None:
                adlar = veri.sabit_islev_adlari(paket, a, sinyal)
                sabit.append(f"{a} {sinyal}: only " + ", ".join(f"GPIO{g} ({adlar[g]})" for g in sorted(izinli)))
    matris = []
    for a in arayuzler:
        if veri.arayuzler[a]["yonlendirme"] != "GPIO_MATRISI":
            continue
        adaylar = set()
        for sinyal in veri.arayuzler[a]["sinyaller"]:
            adaylar |= veri.aday_gpio(paket, a, sinyal)
        if adaylar != veri.paket_gpio[paket]:
            matris.append(f"{a}: only " + ", ".join(f"GPIO{g}" for g in sorted(adaylar)))
    s += ["", "Fixed-pin rules:"] + (sabit or ["none for these needs"])
    s += ["Other interfaces can use any GPIO that is not FORBIDDEN."] + matris
    s += ["", "Count limits (needs of the same interface):"]
    for a in arayuzler:
        sinir = veri.adet_siniri(a, baglam)
        if sinir is None:
            continue
        ad, adet, satir = sinir
        paylasan = [b for b in arayuzler if veri.arayuzler[b]["adet_adi"] == ad]
        ek = " (UART0 is the console)" if veri.arayuzler[a]["adet_baglam_dusumu"] and baglam[veri.arayuzler[a]["adet_baglam_dusumu"]] else ""
        istenen = sum(1 for n in istek["ihtiyaclar"] if n["arayuz"] in paylasan)
        s.append(f"{a}: at most {adet}{ek}, requested {istenen}"
                 + (f" (shared by {' and '.join(paylasan)})" if len(paylasan) > 1 else ""))
    notlar = []
    for y in veri.kullanilan_yorumlar:
        k = y["olgu_anahtar"]
        if k["paket"] == paket and any(veri.arayuzler[a]["cevre_birim"] == k["cevre_birim"] for a in arayuzler):
            notlar.append(f"{k['cevre_birim']} on pin {k['pin_no']}: an ambiguous datasheet cell is read as "
                          f"GPIO{y['deger']['gpio_no']} (interpretation: {y['veren']}).")
    if notlar:
        s += ["", "Notes:"] + notlar
    return "\n".join(s)


def pin_ata(istemci, veri: PinVerisi, istek: dict, en_cok_tur: int = EN_COK_TUR) -> Sonuc:
    sistem = _istem("atama_sistem.txt")
    mesaj = atama_mesaji(veri, istek)
    sinyaller = sorted({s for n in istek["ihtiyaclar"] for s in veri.arayuzler[n["arayuz"]]["sinyaller"]})
    sema = semalar.model_atama_semasi([n["id"] for n in istek["ihtiyaclar"]], sinyaller,
                                      sorted(veri.paket_gpio[istek["paket"]]))
    return calistir(istemci, lambda: [{"role": "system", "content": sistem}, {"role": "user", "content": mesaj}],
                    sema, Denetleyici(veri).icin(istek), en_cok_tur,
                    bilgi_yok_mu=lambda y: y["durum"] == "bilgi_yok", sabit_onek=sistem)


"""Çağrı A'nın kod denetimi için istek sözlüğü (veritabanından, donanim_okur): sayı sözcükleri, bağlam sözcükleri,
paylaşımlı hatlar, pin bahsi desenleri, soru konuları ve kullanıcı mesajları. Sayı ayrıştırıcı, bağlam ifadesi okuyucu,
pin bahsi bulucu ve esnek dayanak eşleşmesi burada; tablolar `sql/004_istek_sozlugu.sql`, `sql/006_pin_tercihleri.sql`,
`sql/007_soru_mesaj.sql`, `sql/008_sayi_es_ad.sql`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from asu_llmcore import PgHatasi, PgOkuyucu

from . import baglanti as baglanti_ayari
from .pinveri import AILE, VeriHatasi

SOZCUK = re.compile(r"\w+")


def kucuk(metin: str) -> str:
    """Türkçe küçük harf: I → ı, İ → i."""
    return metin.replace("I", "ı").replace("İ", "i").lower()


def noktasiz(metin: str) -> str:
    """Pin bahsi araması için: Türkçe küçük harf, "ı" → "i" ("GPIO" → "gpıo" → "gpio"). Uzunluk korunur."""
    return kucuk(metin).replace("ı", "i")


ESNEK_ARA = 2                         # esnek dayanakta iki dayanak sözcüğü arasına girebilecek en çok metin sözcüğü
EKLI_SOZCUK = re.compile(r"\w+(?:['’]\w+)*")   # kesme işaretli ek sözcüğün parçası: "13'e", "LED'i" tek sözcük


def dayanak_bul(metin: str, dayanak: str) -> str | None:
    """Dayanağın metindeki gerçek parçası. Birebir geçiyorsa kendisi. Değilse Türkçe küçük harfle, noktalama ve
    boşluk yok sayılarak: dayanak sözcükleri metinde aynı sırayla, art arda iki dayanak sözcüğü arasında en çok
    ESNEK_ARA metin sözcüğüyle geçmeli; dayanakta metinde olmayan sözcük olamaz. Kesme işaretli ek sözcüğün
    parçasıdır ("13'e" ile "13" farklı sözcük). İlk (en soldaki) eşleşmenin
    metindeki parçası döner; yoksa None."""
    if dayanak in metin:
        return dayanak
    d = [x.replace("’", "'") for x in EKLI_SOZCUK.findall(kucuk(dayanak))]
    t = [(m.group().replace("’", "'"), m.start(), m.end()) for m in EKLI_SOZCUK.finditer(kucuk(metin))]
    if not d:
        return None

    def devam(k: int, j: int) -> int | None:        # d[k:] eşleşmesi, d[k-1] metin sözcüğü j'de; son sözcüğün sırası
        if k == len(d):
            return j
        for j2 in range(j + 1, min(j + 2 + ESNEK_ARA, len(t))):
            if t[j2][0] == d[k]:
                son = devam(k + 1, j2)
                if son is not None:
                    return son
        return None

    for i, (sozcuk, bas, _) in enumerate(t):
        if sozcuk == d[0]:
            son = devam(1, i)
            if son is not None:
                return metin[bas:t[son][2]]
    return None


@dataclass(frozen=True)
class PinBahsi:
    gpio: int
    bas: int
    son: int
    metin: str                        # metindeki parça
    tur: str                          # "gpio" | "liste_devami" | "belirsiz"


@dataclass(frozen=True)
class SayiIfadesi:
    bas: int                          # metindeki konum (Türkçe küçük harfe çevrilmiş metinde, uzunluk korunur)
    son: int
    ifade: str                        # küçük harfli metin parçası ("on altı", "16")
    deger: int


BASAMAK_SIRASI = {"birler": 1, "onlar": 2, "yuz": 3, "bin": 4}


def sayi_dizilisi(parcalar: list[tuple[int, str]], j: int = 0) -> tuple[int, int] | None:
    """parcalar[j:]'nin başındaki en uzun geçerli Türkçe sayı dizilişi: (değer, bittiği sıra) ya da None. Büyük basamaktan
    küçüğe: [birler (2–9)] yüz, onlar, birler; bunların önünde isteğe bağlı "<1–999> bin". "on altı" = 16, "iki yüz elli"
    = 250, "bin iki yüz" = 1200; "altı on" yalnız "altı"yı okur. "bir yüz", "bir bin" geçerli değil."""
    toplam, grup, son_sira, bin_var, en_iyi = 0, 0, 9, False, None
    k = j
    while k < len(parcalar):
        deger, basamak = parcalar[k]
        sira = BASAMAK_SIRASI[basamak]
        if basamak == "bin":
            if bin_var or grup == 1:
                break
            toplam, grup, son_sira, bin_var = (grup or 1) * 1000, 0, 9, True
        elif basamak == "yuz":
            if son_sira <= 3 and not (son_sira == 1 and 2 <= grup <= 9):
                break
            grup, son_sira = (grup or 1) * 100, 3
        elif sira >= son_sira:
            break
        else:
            grup, son_sira = grup + deger, sira
        k += 1
        en_iyi = (toplam + grup, k)
    return en_iyi


@dataclass(frozen=True)
class IstekSozlugu:
    sayilar: dict[tuple[str, ...], int | None]    # sözcük dizisi → değer; None: sayı değil (istisna)
    konular: list[tuple[str, str]]                # (desen, bağlam anahtarı)
    olumsuzlar: list[str]
    paylasimli: frozenset[str]                    # paylaşımlı hat arayüzleri
    pin_desenleri: list[tuple[str, str]] = field(default_factory=list)   # (tur, desen)
    soru_konulari: list[dict] = field(default_factory=list)   # soru_konusu satırları, sıralı (Adım 10)
    mesajlar: dict[str, dict] = field(default_factory=dict)   # durum_mesaji: anahtar → satır
    basamaklar: dict[str, tuple[int, str]] = field(default_factory=dict)   # tek sözcük → (değer, basamak) (Adım 10a)
    es_adlar: dict[str, str] = field(default_factory=dict)    # arayüz eş adı (küçük harf) → arayüz (Adım 10a)
    harf_duyarli: frozenset[str] = frozenset()                # metinde birebir aranan eş adlar ("CAN"; Adım 10b)
    desteklenmeyen: list[dict] = field(default_factory=list)  # desteklenmeyen_ozellik satırları (Adım 11a)
    soru_sozcukleri: list[dict] = field(default_factory=list)  # soru_sozcugu satırları (Adım 11a)
    sayi_disi: list[dict] = field(default_factory=list)        # sayi_disi_sozcuk satırları (Adım 12)

    @property
    def eksik_kodlari(self) -> list[str]:
        """emin_degilim neden kodları: durum_mesaji'ndaki eksik.* anahtarlarının sonu, sıralı."""
        return sorted(a.removeprefix("eksik.") for a in self.mesajlar if a.startswith("eksik."))

    def mesaj(self, anahtar: str) -> dict:
        """durum_mesaji satırı; yoksa VeriHatasi (mesaj sessizce atlanmaz)."""
        if anahtar not in self.mesajlar:
            raise VeriHatasi(f"durum_mesaji'nda '{anahtar}' yok")
        return self.mesajlar[anahtar]

    def pin_bahisleri(self, metin: str) -> list[PinBahsi]:
        """Metindeki pin bahisleri, sırayla. GPIO bahsi ("gpio" deseni) ve hemen ardından gelen liste devamları
        ("GPIO19, 18, 20 ve 21") ile GPIO numarası olmayan belirsiz bahisler ("5 numaralı pin")."""
        n = noktasiz(metin)
        desen = {tur: [re.compile(d) for t, d in self.pin_desenleri if t == tur]
                 for tur in ("gpio", "liste_devami", "belirsiz")}
        sonuc = []
        for d in desen["gpio"]:
            for m in d.finditer(n):
                sonuc.append(PinBahsi(int(m.group(1)), m.start(), m.end(), metin[m.start():m.end()], "gpio"))
                son = m.end()
                while True:
                    devam = next((x for x in (d2.match(n, son) for d2 in desen["liste_devami"]) if x), None)
                    if devam is None:
                        break
                    sonuc.append(PinBahsi(int(devam.group(1)), devam.start(1), devam.end(1),
                                          metin[devam.start(1):devam.end(1)], "liste_devami"))
                    son = devam.end()
        tutulan = [(b.bas, b.son) for b in sonuc]
        for d in desen["belirsiz"]:
            for m in d.finditer(n):
                if not any(b < m.end() and m.start() < s for b, s in tutulan):
                    sonuc.append(PinBahsi(int(m.group(1)), m.start(), m.end(), metin[m.start():m.end()], "belirsiz"))
                    tutulan.append((m.start(), m.end()))
        return sorted(set(sonuc), key=lambda b: (b.bas, b.son))

    def gpio_bahisleri(self, metin: str) -> set[int]:
        return {b.gpio for b in self.pin_bahisleri(metin) if b.tur != "belirsiz"}

    def _bitisik(self, sozcuk: str) -> list[tuple[int, str]] | None:
        """Bitişik yazılmış sayı ("onaltı", "ikiyüzelli"): sözcük baştan sona basamaklı sözcüklere bölünür ve tek bir
        geçerli diziliş olmalı; değilse None ("onay", "altında", "altıon")."""
        def bol(i: int) -> list[list[tuple[int, str]]]:
            if i == len(sozcuk):
                return [[]]
            return [[self.basamaklar[sozcuk[i:k]], *kalan] for k in range(len(sozcuk), i, -1)
                    if sozcuk[i:k] in self.basamaklar for kalan in bol(k)]
        for parcalar in bol(0):
            d = sayi_dizilisi(parcalar)
            if d is not None and d[1] == len(parcalar):
                return parcalar
        return None

    def sayi_araliklari(self, metin: str) -> list[SayiIfadesi]:
        """Metindeki sayı ifadeleri, konumlarıyla, sırayla. Yalnız tam sözcük: 'biri', 'onay' sayı değildir; rakam yalnız
        tek başına bir sözcükse ('UART0', 'BME280', '4x4' değil). Basamaklı sözcükler (ayrı ya da bitişik) Türkçe sayı
        dizilişiyle birleştirilir ("on altı" = 16; "altı on" iki ayrı sayı). Basamaksız ifade kendi başına, çok sözcüklü
        ifade en uzun eşleşmeyle okunur; değeri None olan istisna ('çift yönlü', 'bir de') tüketilir, sayı üretmez."""
        k = kucuk(metin)
        sozcukler = [(m.group(), m.start(), m.end()) for m in SOZCUK.finditer(k)]
        ozel = {ifade: d for ifade, d in self.sayilar.items() if not (len(ifade) == 1 and ifade[0] in self.basamaklar)}
        en_uzun = max((len(x) for x in ozel), default=1)
        sonuc: list[SayiIfadesi] = []
        dizi: list[tuple[int, str, int, int]] = []     # art arda basamaklı parçalar: (değer, basamak, baş, son)

        def bosalt() -> None:
            j = 0
            while j < len(dizi):
                d = sayi_dizilisi([(x[0], x[1]) for x in dizi], j)
                if d is None:                                  # olmaz: her basamaklı parça tek başına geçerli
                    j += 1
                    continue
                bas, son = dizi[j][2], dizi[d[1] - 1][3]
                sonuc.append(SayiIfadesi(bas, son, k[bas:son], d[0]))
                j = d[1]
            dizi.clear()

        i = 0
        while i < len(sozcukler):
            sozcuk, bas, son = sozcukler[i]
            if sozcuk.isdigit():
                bosalt()
                sonuc.append(SayiIfadesi(bas, son, sozcuk, int(sozcuk)))
                i += 1
                continue
            for n in range(min(en_uzun, len(sozcukler) - i), 0, -1):
                parca = tuple(x[0] for x in sozcukler[i:i + n])
                if parca in ozel:
                    bosalt()
                    if ozel[parca] is not None:
                        sonuc.append(SayiIfadesi(bas, sozcukler[i + n - 1][2], k[bas:sozcukler[i + n - 1][2]],
                                                 ozel[parca]))
                    i += n
                    break
            else:
                parcalar = self._bitisik(sozcuk)
                if parcalar is None:
                    bosalt()
                else:
                    dizi.extend((d, b, bas, son) for d, b in parcalar)
                i += 1
        bosalt()
        return sonuc

    def sayi_ifadeleri(self, metin: str) -> list[tuple[str, int]]:
        """Metindeki sayı ifadeleri, sırayla: (ifade, değer). Ayrıntı: sayi_araliklari."""
        return [(s.ifade, s.deger) for s in self.sayi_araliklari(metin)]

    def arayuz_adlari(self, metin: str, adlar) -> list[str]:
        """Metinde adı ya da eş adı geçen arayüzler ("LP I2C", "lp_i2c", "I2C", "IIC", "analog giriş"; harfe duyarlı eş ad
        yalnız birebir: "CAN" evet, "can" hayır). Uzun ad önce
        eşlenir; eşlenen parça kısa adın içinde yeniden sayılmaz ("LP I2C" yalnız LP_I2C). Sıra: `adlar` sırası."""
        n = noktasiz(metin)
        adaylar = [(noktasiz(ad).split("_"), ad, False) for ad in adlar]
        adaylar += [(es.split() if es in self.harf_duyarli else noktasiz(es).split(), ad, es in self.harf_duyarli)
                    for es, ad in self.es_adlar.items() if ad in adlar]
        bulunan, tutulan = [], []
        for parcalar, ad, birebir in sorted(adaylar, key=lambda x: len(" ".join(x[0])), reverse=True):
            sinir = "A-Za-z0-9" if birebir else "a-z0-9"
            desen = rf"(?<![{sinir}])" + r"[\s_-]?".join(re.escape(p) for p in parcalar) + rf"(?![{sinir}])"
            for m in re.finditer(desen, metin if birebir else n):
                if not any(b < m.end() and m.start() < s for b, s in tutulan):
                    tutulan.append((m.start(), m.end()))
                    if ad not in bulunan:
                        bulunan.append(ad)
        return sorted(bulunan, key=list(adlar).index)

    def desteklenmeyen_bul(self, metin: str) -> list[tuple[dict, str]]:
        """Metinde adı geçen desteklenmeyen özellikler: (satır, metindeki ad), satır sırasıyla. Ad sözcük sınırında
        aranır. Harfe duyarlı adlar birebir ve iki yanı sınırlı ("DAC'ı" evet, "DACAR" hayır); ötekiler Türkçe küçük harfle,
        yalnız solu sınırlı (bitişik Türkçe ek serbest: "ethernetle", "dokunmatik pinleriyle")."""
        n = noktasiz(metin)
        sonuc = []
        for r in self.desteklenmeyen:
            adaylar = [(noktasiz(a), False) for a in r["es_adlar"]] + [(a, True) for a in r["harf_duyarli_adlar"]]
            for ad, birebir in adaylar:
                desen = (rf"(?<![A-Za-z0-9]){re.escape(ad)}(?![A-Za-z0-9])" if birebir
                         else rf"(?<![a-z0-9çğıöşü]){re.escape(ad)}")
                m = re.search(desen, metin if birebir else n)
                if m:
                    sonuc.append((r, metin[m.start():m.end()]))
                    break
        return sonuc

    def soru_sozcukleri_bul(self, metin: str, tur: str) -> list[str]:
        """Soruda geçen `tur` türündeki soru sözcükleri (metindeki biçimiyle). Harfe duyarlı birim birebir, iki yanı harfle
        sınırlı ("20mA" evet, "mAh" hayır); öteki sözcükler Türkçe küçük harfle, solu sınırlı ("akımı" evet)."""
        n = noktasiz(metin)
        bulunan = []
        for r in (r for r in self.soru_sozcukleri if r["tur"] == tur):
            if r["harf_duyarli"]:
                m = re.search(rf"(?<![A-Za-zµ]){re.escape(r['sozcuk'])}(?![A-Za-z])", metin)
            else:
                m = re.search(rf"(?<![a-z0-9çğıöşü]){re.escape(noktasiz(r['sozcuk']))}", n)
            if m:
                bulunan.append(metin[m.start():m.end()])
        return bulunan

    def sayi_disi_mi(self, sozcuk: str, tur: str) -> bool:
        """Sözcük `sayi_disi_sozcuk`'ta `tur` türünde mi: harfe duyarlı birebir, öteki Türkçe küçük harfle; 'onek'
        biçiminde sözcük önekle başlıyor ("hattına")."""
        n = noktasiz(sozcuk)
        for r in (r for r in self.sayi_disi if r["tur"] == tur):
            s, x = (r["sozcuk"], sozcuk) if r["harf_duyarli"] else (noktasiz(r["sozcuk"]), n)
            if x == s or (r["bicim"] == "onek" and x.startswith(s)):
                return True
        return False

    def baglam_oku(self, ifade: str) -> dict[str, bool]:
        """Bağlam ifadesinin söylediği: {anahtar: değer}. Olumsuzluk deseni geçerse değer False."""
        k = kucuk(ifade)
        deger = not any(o in k for o in self.olumsuzlar)
        return {anahtar: deger for desen, anahtar in self.konular if desen in k}


SORGULAR = {
    "sayi": "SELECT ifade, deger, basamak FROM sayi_sozcugu",
    "es_ad": "SELECT es_ad, arayuz, harf_duyarli FROM arayuz_es_adi",
    "baglam": "SELECT tur, anahtar, desen FROM baglam_sozcugu ORDER BY tur, anahtar, desen",
    "paylasimli": "SELECT arayuz FROM arayuz_tanimi WHERE aile = %(aile)s AND paylasimli_hat",
    "pin": "SELECT tur, desen FROM pin_bahsi_deseni ORDER BY tur, desen",
    "soru": "SELECT konu, model_tanimi, cevap_turu, gereken FROM soru_konusu ORDER BY sira",
    "mesaj": "SELECT anahtar, mesaj_tr, ne_yazmali_tr, ornek_tr, model_tanimi FROM durum_mesaji ORDER BY anahtar",
    "desteklenmeyen": "SELECT x.terim, x.es_adlar, x.harf_duyarli_adlar, x.aciklama_tr, x.sayfa, x.referans, k.belge, "
                      "k.surum FROM desteklenmeyen_ozellik x JOIN kaynak k ON k.id = x.kaynak_id "
                      "WHERE x.aile = %(aile)s ORDER BY x.id",
    "soru_sozcugu": "SELECT sozcuk, tur, harf_duyarli FROM soru_sozcugu ORDER BY id",
    "sayi_disi": "SELECT sozcuk, tur, bicim, harf_duyarli FROM sayi_disi_sozcuk ORDER BY id",
}


def yukle(rol: str = "donanim_okur", veritabani: str = baglanti_ayari.VERITABANI, aile: str = AILE, **baglanti) -> IstekSozlugu:
    try:
        with PgOkuyucu(rol, veritabani, uygulama_adi="pinsecim_sozluk", **{**baglanti_ayari.adres(), **baglanti}) as db:
            r = {ad: db.sorgu(sql, {"aile": aile}) for ad, sql in SORGULAR.items()}
    except PgHatasi as e:
        raise VeriHatasi(f"istek sözlüğü okunamadı: {e}") from e
    if not r["sayi"] or not r["baglam"] or not r["pin"] or not r["soru"] or not r["mesaj"]:
        raise VeriHatasi("istek sözlüğü eksik: sayi_sozcugu, baglam_sozcugu, pin_bahsi_deseni, soru_konusu ya da "
                         "durum_mesaji boş")
    return IstekSozlugu(
        sayilar={tuple(s["ifade"].split()): s["deger"] for s in r["sayi"]},
        basamaklar={s["ifade"]: (s["deger"], s["basamak"]) for s in r["sayi"] if s["basamak"]},
        es_adlar={s["es_ad"]: s["arayuz"] for s in r["es_ad"]},
        harf_duyarli=frozenset(s["es_ad"] for s in r["es_ad"] if s["harf_duyarli"]),
        konular=[(s["desen"], s["anahtar"]) for s in r["baglam"] if s["tur"] == "konu"],
        olumsuzlar=[s["desen"] for s in r["baglam"] if s["tur"] == "olumsuz"],
        paylasimli=frozenset(s["arayuz"] for s in r["paylasimli"]),
        pin_desenleri=[(s["tur"], s["desen"]) for s in r["pin"]],
        soru_konulari=r["soru"],
        mesajlar={m["anahtar"]: m for m in r["mesaj"]},
        desteklenmeyen=r["desteklenmeyen"],
        soru_sozcukleri=r["soru_sozcugu"],
        sayi_disi=r["sayi_disi"],
    )

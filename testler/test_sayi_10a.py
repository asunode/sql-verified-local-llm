"""Adım 10a: bileşik sayı okuma (Türkçe sayı kuralı), dayanağın sözcük sınırı, diger_ifadeler ve arayüz eş adları.

Cihaz ve sayılar v1–v4 setlerinde ve istem örneklerinde geçmeyenlerden seçildi (peltier, vantilatör, zil, spot,
projektör, ısıtıcı, kepenk, tabela; otuz–doksan, yüzlü sayılar).
"""

from __future__ import annotations

import json

import pytest

from asu_llmcore import OllamaYaniti

from pinsecim import cagrilar, hat, pinveri, semalar, sozluk as sozluk_mod
from pinsecim.__main__ import yazdir
from pinsecim.cevap import Cevaplayici

BAGLAM = {"usb_serial_jtag": True, "uart0_konsol": True, "jtag_pinleri": False, "harici_flash_beslemesi": False}


@pytest.fixture(scope="module")
def s():
    return sozluk_mod.yukle()


@pytest.fixture(scope="module")
def veri():
    return pinveri.yukle()


def degerler(s, metin):
    return [x.deger for x in s.sayi_araliklari(metin)]


# ------------------------------------------------------------------ sayı ayrıştırıcı
@pytest.mark.parametrize("metin, beklenen", [
    # 11–99 bileşikleri, ayrı ve bitişik
    ("otuz iki spot", [32]), ("kırk yedi tabela", [47]), ("yetmiş üç peltier", [73]), ("doksan vantilatör", [90]),
    ("Seksen dört kepenk", [84]), ("otuziki spot", [32]), ("kırkyedi tabela", [47]), ("on beş zil", [15]),
    # yüzlü ve binli
    ("yüz on iki spot", [112]), ("üç yüz kırk projektör", [340]), ("üçyüzkırk projektör", [340]),
    ("iki bin üç yüz", [2300]), ("bin kepenk", [1000]),
    # rakam
    ("73 peltier", [73]), ("Kapıda 112 spot", [112]),
    # geçersiz diziliş: büyükten küçüğe değil, birleşmez
    ("yedi otuz spot", [7, 30]), ("on on zil", [10, 10]), ("bir yüz ısıtıcı", [1, 100]), ("yediotuz spot", []),
    # sayı olmayan "bir"
    ("bir de zil var", []), ("bir şey bağlanacak", []), ("bir şeyler yapacağım", []), ("bir zil", [1]),
    # sözcük içi değil
    ("onayla", []), ("altında", []), ("yüzde", []), ("binlerce", []),
])
def test_sayi_dizilisi(s, metin, beklenen):
    assert degerler(s, metin) == beklenen


def test_sayi_konumlari(s):
    metin = "Toplam Otuz iki spot ve 7 zil."
    a = s.sayi_araliklari(metin)
    assert [(metin[x.bas:x.son], x.deger) for x in a] == [("Otuz iki", 32), ("7", 7)]


# ------------------------------------------------------------------ denetleyici
def denetle(s, metin, *kalemler, diger=None, baglam_ifadeleri=None):
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), s)
    y = {"ihtiyaclar": [{"arayuz": a, "dayanak": da, "adet": n, "kaynak": k} for a, da, n, k in kalemler],
         "baglam_ifadeleri": baglam_ifadeleri or [], "diger_ifadeler": diger or [], "desteklenmeyenler": [],
         "durum": "tamam"}
    return d(y), y


def hatalar(ihl):
    return [i.kod for i in ihl if i.seviye == "hata"]


def test_yarim_dayanak_yanlis_adet_hata(s):
    ihl, _ = denetle(s, "Otuz iki spot lambayı yakacağım.", ("GPIO_OUT", "iki spot lambayı yakacağım", 2, "model_cikarimi"))
    h = [i for i in ihl if i.kod == "SAYI_UYUSMAZ"]
    assert len(h) == 1 and "'otuz iki' = 32" in h[0].mesaj and "'Otuz iki'" in h[0].mesaj


def test_yarim_dayanak_dogru_adet_uyari(s):
    ihl, _ = denetle(s, "Otuz iki spot lambayı yakacağım.", ("GPIO_OUT", "iki spot lambayı yakacağım", 32, "model_cikarimi"))
    assert hatalar(ihl) == [] and [i.kod for i in ihl if i.kod == "SAYI_YARIM"] == ["SAYI_YARIM"]


def test_tam_dayanak_gecer(s):
    ihl, _ = denetle(s, "Otuz iki spot lambayı yakacağım.", ("GPIO_OUT", "Otuz iki spot lambayı", 32, "model_cikarimi"))
    assert hatalar(ihl) == [] and not any(i.kod == "SAYI_YARIM" for i in ihl)


def test_yuzlu_yarim_dayanak(s):
    ihl, _ = denetle(s, "Yüz yirmi tabela ışığı var.", ("GPIO_OUT", "yirmi tabela ışığı", 20, "istekte_acik"))
    assert hatalar(ihl) == ["SAYI_UYUSMAZ"]


def test_bitisik_sayi(s):
    ihl, _ = denetle(s, "Kırkyedi kepenk motoru.", ("GPIO_OUT", "Kırkyedi kepenk motoru", 47, "istekte_acik"))
    assert hatalar(ihl) == []
    ihl, _ = denetle(s, "Kırkyedi kepenk motoru.", ("GPIO_OUT", "Kırkyedi kepenk motoru", 7, "istekte_acik"))
    assert hatalar(ihl) == ["SAYI_UYUSMAZ"]


def test_rakamli_kelime_ortasi_dayanak(s):
    ihl, _ = denetle(s, "Salonda 73 peltier var.", ("GPIO_OUT", "3 peltier", 3, "istekte_acik"))
    assert hatalar(ihl) == ["DAYANAK_SINIRI"] and "'73 peltier'" in ihl[0].mesaj


def test_kelime_ortasi_dayanak_sozcuk(s):
    ihl, _ = denetle(s, "Onbeş zil çalacak.", ("GPIO_OUT", "beş zil", 5, "istekte_acik"))
    assert "DAYANAK_SINIRI" in hatalar(ihl)
    ihl, _ = denetle(s, "Üç vantilatörü süreceğim.", ("PWM", "vantilatör", 3, "model_cikarimi"))
    assert hatalar(ihl) == ["DAYANAK_SINIRI"]                               # ek kesilmiş: "vantilatörü"


def test_kesme_isaretli_ek_sinirdir(s):
    ihl, _ = denetle(s, "Projektör'ü ve iki zili süreceğim.", ("GPIO_OUT", "Projektör", 1, "model_cikarimi"))
    assert hatalar(ihl) == []


def test_bir_de_sayi_degil(s):
    ihl, _ = denetle(s, "Üç spot yakacağım, bir de zil süreceğim.", ("GPIO_OUT", "bir de zil süreceğim", 2, "istekte_acik"))
    assert hatalar(ihl) == []                       # Adım 10a öncesi "bir" = 1 sayılıp SAYI_UYUSMAZ verirdi


def test_muafiyetler_aynen(s):
    ihl, _ = denetle(s, "Otuz iki sıcaklık sensörü I2C ile okunacak.", ("I2C", "iki sıcaklık sensörü I2C ile", 1, "istekte_acik"))
    assert hatalar(ihl) == []                       # paylaşımlı hat: sayı cihaz sayısı
    ihl, _ = denetle(s, "Kırk iki peltier sürücüsü.", ("GPIO_OUT", "Kırk iki peltier sürücüsü", 84, "model_cikarimi"))
    assert hatalar(ihl) == []                       # model çıkarımında tam kat (L-4)


def test_ayni_dayanak_iki_konumda(s):
    metin = "Otuz iki spot ışığı salonda, iki spot ışığı kapıda."
    ihl, _ = denetle(s, metin, ("GPIO_OUT", "iki spot ışığı", 2, "istekte_acik"))
    assert hatalar(ihl) == [] and not any(i.kod == "SAYI_YARIM" for i in ihl)   # ikinci konum tam


# ------------------------------------------------------------------ diger_ifadeler
def test_diger_ifadeler_dayanak(s):
    ihl, _ = denetle(s, "Bir zil çalacak. Kasası ahşap olacak.", ("GPIO_OUT", "Bir zil çalacak", 1, "model_cikarimi"),
                     diger=["Kasası metal olacak."])
    assert ("DAYANAK_YOK") in hatalar(ihl)
    ihl, _ = denetle(s, "Bir zil çalacak. Kasası ahşap olacak.", ("GPIO_OUT", "Bir zil çalacak", 1, "model_cikarimi"),
                     diger=["Kasası ahşap olacak."])
    assert hatalar(ihl) == [] and not any(i.kod == "DIGER_IHTIYAC_IZI" for i in ihl)


@pytest.mark.parametrize("ifade, neden", [
    ("Kırk tabela ışığı da olabilir.", "sayı «Kırk»"),
    ("Ileride UART ile bağlarım.", "arayüz adı (UART)"),
    ("Ileride IIC ile bağlarım.", "arayüz adı (I2C)"),
    ("Projektör eskiden GPIO3'teydi.", "pin bahsi «GPIO3»"),
])
def test_diger_ifade_ihtiyac_izi_uyarisi(s, ifade, neden):
    metin = f"Bir zil çalacak. {ifade}"
    ihl, _ = denetle(s, metin, ("GPIO_OUT", "Bir zil çalacak", 1, "model_cikarimi"), diger=[ifade])
    u = [i for i in ihl if i.kod == "DIGER_IHTIYAC_IZI"]
    assert len(u) == 1 and u[0].seviye == "uyari" and neden in u[0].mesaj and u[0].alan == "diger_ifadeler/0"


def test_diger_ifadedeki_gpio_pin_listesine_de_girmeli(s):
    metin = "Bir zil çalacak. Projektör eskiden GPIO3'teydi."
    ihl, _ = denetle(s, metin, ("GPIO_OUT", "Bir zil çalacak", 1, "model_cikarimi"), diger=["Projektör eskiden GPIO3'teydi."])
    assert "PIN_BAHSI_ATLANDI" in hatalar(ihl)       # mevcut pin bahsi denetimi çalışmaya devam eder


def test_baglam_konusuz_diger_ifadelere_yonlendirir(s):
    ihl, _ = denetle(s, "Bir zil çalacak. Kasası ahşap olacak.", ("GPIO_OUT", "Bir zil çalacak", 1, "model_cikarimi"),
                     baglam_ifadeleri=["Kasası ahşap olacak."])
    h = [i for i in ihl if i.kod == "BAGLAM_KONUSUZ"]
    assert len(h) == 1 and "diger_ifadeler" in h[0].mesaj


def test_istem_kural_4_ve_ornekler(s):
    metin = (cagrilar.ISTEMLER / "ihtiyac_sistem.txt").read_text(encoding="utf-8")
    assert '"diger_ifadeler"' in metin.split("Examples")[0]
    assert metin.count('"diger_ifadeler": [') == metin.count("Answer: {")


class Sahte:
    def __init__(self, yanitlar):
        self.yanitlar = list(yanitlar)

    def uret(self, mesajlar, sema=None, sabit_onek=None):
        j = self.yanitlar.pop(0)
        return OllamaYaniti(ham=json.dumps(j, ensure_ascii=False), json=j, model="sahte")


def test_cli_diger_ifadeler_bolumu(veri, s, capsys):
    metin = "Bir peltier süreceğim. Kırk lira bütçem var."
    y = {"ihtiyaclar": [{"arayuz": "GPIO_OUT", "dayanak": "Bir peltier süreceğim", "adet": 1, "kaynak": "model_cikarimi"}],
         "pin_tercihleri": [], "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [], "sorular": [],
         "baglam_ifadeleri": [], "diger_ifadeler": ["Kırk lira bütçem var."], "desteklenmeyenler": [], "durum": "tamam",
         "eksik": []}
    h = hat.calistir(metin, "QFN40", BAGLAM, veri, Sahte([y]), iz=None, sozluk=s)
    assert h.atama["durum"] == "atandi"
    yazdir(h, veri)
    cikti = capsys.readouterr().out
    assert "Pin seçimini etkilemeyen ifadeler (ihtiyaç olarak alınmadı):" in cikti
    assert "«Kırk lira bütçem var.»" in cikti and "sayı «Kırk»" in cikti
    assert cikti.index("1) İhtiyaçlar") < cikti.index("Pin seçimini etkilemeyen") < cikti.index("3) Atama")


# ------------------------------------------------------------------ eş adlar
@pytest.mark.parametrize("metin, beklenen", [
    ("CAN hattı hangi pinlerde?", ["TWAI"]), ("analog giriş pinleri", ["ADC"]), ("analog okuma", ["ADC"]),
    ("IIC pinleri", ["I2C"]), ("I²C pinleri", ["I2C"]), ("dijital giriş", ["GPIO_IN"]), ("dijital çıkış", ["GPIO_OUT"]),
    ("seri haberleşme pinleri", ["UART"]), ("LP I2C ve IIC", ["I2C", "LP_I2C"]),
    ("canlı yayın", []), ("scanner", []),
])
def test_es_adlar(s, metin, beklenen):
    assert s.arayuz_adlari(metin, list(semalar.ARAYUZLER)) == beklenen


def test_es_ad_baglam_cakismasi(s):
    desenler = [d for d, _ in s.konular]
    for es in s.es_adlar:
        assert s.baglam_oku(es) == {}, es
        assert not any(es in d for d in desenler), es
    assert "seri port" not in s.es_adlar and "programlama portu" not in s.es_adlar
    assert set(s.es_adlar.values()) <= set(semalar.ARAYUZLER)


def test_cevaplayici_es_adla(veri, s):
    c = Cevaplayici(veri, s).cevapla({"soru": "CAN hangi pinlere çıkabilir?", "konu": "arayuz_pinleri"}, "QFN32", BAGLAM)
    assert c["durum"] == "cevap" and c["parametre"]["arayuz"] == ["TWAI"] and c["kaynaklar"]

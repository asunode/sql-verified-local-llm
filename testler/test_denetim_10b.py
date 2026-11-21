"""Adım 10b denetim düzeltmeleri: DIGER_PIN_TERCIH_IZI, DIGER_BAGLAM, tek başına "bir", harfe duyarlı "CAN",
atayıcının toplamlı mumkun_degil nedeni (test_cagrilar). Cihazlar v1–v4 setlerinde geçmeyenlerden."""

from __future__ import annotations

import pytest

from pinsecim import cagrilar, semalar, sozluk as sozluk_mod


@pytest.fixture(scope="module")
def s():
    return sozluk_mod.yukle()


def denetle(s, metin, ihtiyaclar, diger_pin=(), tercih=(), diger=(), baglam=None):
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), s, baglam)
    y = {"ihtiyaclar": [{"arayuz": a, "dayanak": da, "adet": 1, "kaynak": "model_cikarimi"} for a, da in ihtiyaclar],
         "pin_tercihleri": [{"arayuz": a, "sinyal": "", "gpio": g, "dayanak": da} for a, g, da in tercih],
         "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [{"gpio": g, "dayanak": da} for g, da in diger_pin],
         "sorular": [], "baglam_ifadeleri": [], "diger_ifadeler": list(diger), "desteklenmeyenler": [], "durum": "tamam",
         "eksik": []}
    return d(y), y


def kod(ihl, k):
    return [i for i in ihl if i.kod == k]


# ------------------------------------------------------------------ DIGER_PIN_TERCIH_IZI
def test_tercih_izi_ayni_cumlede_tercihsiz_ihtiyac(s):
    metin = "Zili önce GPIO4'e takmıştım, şimdi GPIO5'te duruyor."
    ihl, _ = denetle(s, metin, [("GPIO_OUT", "Zili")], diger_pin=[(4, "GPIO4"), (5, "GPIO5")])
    u = kod(ihl, "DIGER_PIN_TERCIH_IZI")
    assert [i.seviye for i in u] == ["uyari", "uyari"] and [i.alan for i in u] == ["diger_pin_bahisleri/0",
                                                                                  "diger_pin_bahisleri/1"]
    assert "bir pin tercihi olabilir" in u[1].mesaj and '"Zili GPIO5\'e bağla"' in u[1].mesaj
    assert not [i for i in ihl if i.seviye == "hata"]


def test_tercih_izi_tercih_varsa_yok(s):
    metin = "Zili önce GPIO4'e takmıştım, şimdi GPIO5'te duruyor."
    ihl, _ = denetle(s, metin, [("GPIO_OUT", "Zili")], diger_pin=[(4, "GPIO4")], tercih=[("GPIO_OUT", 5, "GPIO5'te")])
    assert kod(ihl, "DIGER_PIN_TERCIH_IZI") == []


def test_tercih_izi_baska_cumlede_yok(s):
    metin = "Bir peltier süreceğim. Eski kartta GPIO10 kullanılıyordu."
    ihl, _ = denetle(s, metin, [("GPIO_OUT", "Bir peltier süreceğim")], diger_pin=[(10, "GPIO10")])
    assert kod(ihl, "DIGER_PIN_TERCIH_IZI") == []


@pytest.mark.parametrize("n, ek", [(0, "'a"), (1, "'e"), (2, "'ye"), (3, "'e"), (6, "'ya"), (7, "'ye"), (9, "'a"),
                                   (10, "'a"), (12, "'ye"), (20, "'ye"), (23, "'e"), (30, "'a")])
def test_yonelme_eki(n, ek):
    assert cagrilar.yonelme_eki(n) == ek


# ------------------------------------------------------------------ DIGER_BAGLAM
def test_diger_ifadede_kart_baglami_hata(s):
    metin = "Bir peltier süreceğim. Flash'ı ayrı bir kaynaktan besleyeceğim."
    ihl, _ = denetle(s, metin, [("GPIO_OUT", "Bir peltier süreceğim")],
                     diger=["Flash'ı ayrı bir kaynaktan besleyeceğim."])
    h = kod(ihl, "DIGER_BAGLAM")
    assert len(h) == 1 and h[0].seviye == "hata" and "baglam_ifadeleri" in h[0].mesaj
    assert kod(ihl, "DIGER_IHTIYAC_IZI") == []                    # hata verilen öğeye ayrıca uyarı yok


def test_baglama_tasininca_celiski_calisir(s):
    metin = "Bir peltier süreceğim. Flash'ı ayrı bir kaynaktan besleyeceğim."
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), s, {"usb_serial_jtag": True, "uart0_konsol": True,
                                                                         "jtag_pinleri": False,
                                                                         "harici_flash_beslemesi": False})
    y = {"ihtiyaclar": [{"arayuz": "GPIO_OUT", "dayanak": "Bir peltier süreceğim", "adet": 1, "kaynak": "model_cikarimi"}],
         "pin_tercihleri": [], "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [], "sorular": [],
         "baglam_ifadeleri": ["Flash'ı ayrı bir kaynaktan besleyeceğim."], "diger_ifadeler": [],
         "desteklenmeyenler": [], "durum": "tamam", "eksik": []}
    ihl = d(y)
    assert [i.kod for i in ihl if i.seviye == "hata"] == [] and kod(ihl, "BAGLAM_CELISKI")


# ------------------------------------------------------------------ tek başına "bir"
def test_tek_basina_bir_uyari_vermez(s):
    metin = "Bir peltier süreceğim. Kasayı bir marangoza yaptıracağım."
    ihl, _ = denetle(s, metin, [("GPIO_OUT", "Bir peltier süreceğim")], diger=["Kasayı bir marangoza yaptıracağım."])
    assert kod(ihl, "DIGER_IHTIYAC_IZI") == []


@pytest.mark.parametrize("ifade, neden", [
    ("Kasaya bir çift menteşe takılacak.", "sayı «bir çift»"),
    ("Kasada 1 menteşe var.", "sayı «1»"),
    ("Kasada bir CAN soketi olacak.", "arayüz adı (TWAI)"),
])
def test_bir_disindakiler_aynen(s, ifade, neden):
    metin = f"Bir peltier süreceğim. {ifade}"
    ihl, _ = denetle(s, metin, [("GPIO_OUT", "Bir peltier süreceğim")], diger=[ifade])
    u = kod(ihl, "DIGER_IHTIYAC_IZI")
    assert len(u) == 1 and neden in u[0].mesaj and "«bir»" not in u[0].mesaj


# ------------------------------------------------------------------ harfe duyarlı "CAN"
@pytest.mark.parametrize("metin, beklenen", [
    ("CAN hattı", ["TWAI"]), ("can hattı", []), ("Can sıkıcı bir iş", []), ("can bus", ["TWAI"]),
    ("CAN bus", ["TWAI"]), ("Can Bus", ["TWAI"]),
])
def test_can_harf_duyarli(s, metin, beklenen):
    assert s.arayuz_adlari(metin, list(semalar.ARAYUZLER)) == beklenen

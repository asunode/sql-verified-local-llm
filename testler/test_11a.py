"""Adım 11a: DESTEKLENMEYEN_OZELLIK, elektriksel not, KAPSANMAYAN_CUMLE emin_degilim'de yok, I2C ortak hat, rapor süre
satırı. Cümleler v1–v5 setlerinde geçmeyenlerden."""

from __future__ import annotations

import pytest

from pinsecim import cagrilar, semalar, sozluk as sozluk_mod


@pytest.fixture(scope="module")
def s():
    return sozluk_mod.yukle()


def yanit(ihtiyaclar=(), sorular=(), baglam=(), diger=(), desteklenmeyen=(), durum="tamam", eksik=()):
    return {"ihtiyaclar": [{"arayuz": a, "dayanak": da, "adet": n, "kaynak": "model_cikarimi"} for a, da, n in ihtiyaclar],
            "pin_tercihleri": [], "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [],
            "sorular": [{"soru": q, "konu": k} for q, k in sorular], "baglam_ifadeleri": list(baglam),
            "diger_ifadeler": list(diger), "desteklenmeyenler": list(desteklenmeyen), "durum": durum,
            "eksik": list(eksik)}


def kodlar(s, metin, y, kod):
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), s, None)
    return [i for i in d(y) if i.kod == kod]


# ------------------------------------------------------------------ DESTEKLENMEYEN_OZELLIK
@pytest.mark.parametrize("metin, dayanak, ad", [
    ("Bir DAC çıkışıyla sinüs dalgası üreteceğim.", "Bir DAC çıkışıyla", "DAC"),
    ("Klavyeyi USB host olarak okuyacağım.", "Klavyeyi", "USB host"),
    ("Dokunmatik pinleriyle üç tuş yapacağım.", "üç tuş", "Dokunmatik pin"),
    ("OV2640'ı kamera arayüzüne bağlayacağım.", "OV2640'ı", "kamera arayüzü"),
    ("LAN8720 modülünü RMII üzerinden bağlayacağım.", "LAN8720 modülünü", "RMII"),
    ("Kartı Ethernetle ağa bağlayacağım.", "Kartı", "Ethernet"),
    ("Telefonu USB OTG ile bağlayacağım.", "Telefonu", "USB OTG"),
])
def test_desteklenmeyen_hata(s, metin, dayanak, ad):
    u = kodlar(s, metin, yanit(ihtiyaclar=[("GPIO_OUT", dayanak, 1)]), "DESTEKLENMEYEN_OZELLIK")
    assert [i.seviye for i in u] == ["hata"] and u[0].alan == "ihtiyaclar/0/dayanak"
    assert u[0].mesaj.startswith(f"'{ad}' is not available on this chip (ESP32-C6 Series Datasheet v1.6: not in the "
                                 "peripheral list, p. 4); put it into desteklenmeyenler and set durum to desteklenmiyor.")


def test_yalniz_diger_ifadede_hata_yok(s):
    metin = "Ağa Ethernet değil Wi-Fi ile bağlanacağım. İki buton okuyacağım."
    y = yanit(ihtiyaclar=[("GPIO_IN", "İki buton", 2)], diger=["Ağa Ethernet değil Wi-Fi ile bağlanacağım."])
    assert kodlar(s, metin, y, "DESTEKLENMEYEN_OZELLIK") == []


def test_desteklenmeyenlere_tasininca_hata_yok(s):
    metin = "Bir DAC ile ses vereceğim."
    y = yanit(desteklenmeyen=["Bir DAC ile ses vereceğim."], durum="desteklenmiyor")
    assert kodlar(s, metin, y, "DESTEKLENMEYEN_OZELLIK") == []


@pytest.mark.parametrize("metin, dayanak", [
    ("Dokunmatik buton modülünü okuyacağım.", "Dokunmatik buton modülünü"),     # dış modül: dijital çıkış
    ("SDIO ile bir Wi-Fi yardımcı işlemcisine bağlanacağım.", "SDIO ile"),       # SDIO slave var
    ("Ekranı paralel bağlayacağım.", "Ekranı"),                                   # PARLIO var
    ("Bir kamera modülünü SPI ile okuyacağım.", "Bir kamera modülünü"),
    ("Hostel tabelasındaki LED'i yakacağım.", "LED'i"),                           # "host" sözcük içinde
    ("Bir dacha projesi için röle süreceğim.", "röle"),                           # "DAC" harfe duyarlı ve sınırlı
    ("Sıcaklığı bir NTC ile ölçeceğim; değeri analog çıkıştan değil ekrandan okuyacağım.", "bir NTC"),
])
def test_yanlis_alarm_yok(s, metin, dayanak):
    assert kodlar(s, metin, yanit(ihtiyaclar=[("ADC", dayanak, 1)]), "DESTEKLENMEYEN_OZELLIK") == []


def test_es_adlar_ve_tablo(s):
    terimler = {r["terim"] for r in s.desteklenmeyen}
    assert {"Ethernet MAC", "DAC", "Dokunmatik sensör (touch)", "USB OTG / USB host", "Kamera arayüzü"} <= terimler
    assert [r["terim"] for r, _ in s.desteklenmeyen_bul("MII ile PHY")] == ["Ethernet MAC"]
    assert s.desteklenmeyen_bul("dvp kamera") == [] and [a for _, a in s.desteklenmeyen_bul("DVP kamera")] == ["DVP"]
    assert all(r["sayfa"] == 4 and "Datasheet" in r["belge"] for r in s.desteklenmeyen)


# ------------------------------------------------------------------ elektriksel not
@pytest.fixture(scope="module")
def cevaplayici(s):
    from pinsecim import cevap, pinveri
    return cevap.Cevaplayici(pinveri.yukle(), s)


BAGLAM = {"usb_serial_jtag": True, "uart0_konsol": True, "jtag_pinleri": False, "harici_flash_beslemesi": False}


@pytest.mark.parametrize("soru, konu, sozcuk", [
    ("GPIO7 kaç miliamper verebilir?", "pin_kisiti", "miliamper"),
    ("GPIO10 20mA LED'i doğrudan sürer mi?", "pin_islevi", "mA"),
    ("ADC girişine en fazla kaç volt uygulayabilirim?", "arayuz_pinleri", "volt"),
    ("Derin uykuda güç tüketimi ne kadar?", "diger", "güç tüketimi"),
    ("GPIO2'nin çıkış gerilimi nedir?", "pin_kisiti", "gerilim"),
    ("GPIO4 3.3V ile mi çalışır?", "pin_kisiti", "V"),
])
def test_elektriksel_not(cevaplayici, soru, konu, sozcuk):
    c = cevaplayici.cevapla({"soru": soru, "konu": konu}, "QFN40", BAGLAM)
    assert c["on_not"]["mesaj"] == ("Elektriksel değerler (akım, gerilim) yapılı tablolarda yok; ESP32-C6 Datasheet "
                                    "v1.6, Bölüm 5 (Electrical Characteristics), s. 64.")
    assert sozcuk in c["on_not"]["sozcukler"]
    assert c["konu"] == konu                                         # konu cevabı ayrıca verilir


@pytest.mark.parametrize("soru, konu", [
    ("GPIO7 hangi işlevlere sahip?", "pin_islevi"),
    ("I2C hangi pinlere çıkabilir?", "arayuz_pinleri"),
    ("Bu kartın mAh değeri ne?", "diger"),                              # "mAh" birim değil
    ("Akvaryum pompası için hangi pin?", "arayuz_pinleri"),             # "akvaryum" "akım" değil
])
def test_elektriksel_not_yok(cevaplayici, soru, konu):
    assert cevaplayici.cevapla({"soru": soru, "konu": konu}, "QFN40", BAGLAM)["on_not"] is None


def test_elektriksel_not_komut_satirinda():
    from pinsecim.__main__ import soru_yazdir
    import contextlib
    import io
    c = {"soru": "GPIO3 kaç mA?", "konu": "pin_kisiti", "mesaj": None, "satirlar": ["GPIO3: satır"],
         "kaynaklar": [], "belirsiz": [], "yorumlar": [], "parametre": {},
         "on_not": {"mesaj": "Elektriksel değerler … yok"}}
    t = io.StringIO()
    with contextlib.redirect_stdout(t):
        soru_yazdir(1, c)
    satirlar = t.getvalue().splitlines()
    assert satirlar[1] == "      [NOT] Elektriksel değerler … yok" and "GPIO3: satır" in satirlar[2]


# ------------------------------------------------------------------ I2C ortak hat
@pytest.fixture(scope="module")
def veri():
    from pinsecim import pinveri
    return pinveri.yukle()


def istek(paket, *arayuzler, **ek):
    return {"paket": paket, "baglam": BAGLAM, "ihtiyaclar": cagrilar.kimlik_ver([{"arayuz": a} for a in arayuzler]), **ek}


def test_i2c_coklu_tek_hat(veri):
    from pinsecim.atayici import Atayici
    from pinsecim.denetim import Denetleyici
    for arayuz, paket in (("I2C", "QFN40"), ("LP_I2C", "QFN32")):
        ist = istek(paket, arayuz, arayuz, arayuz)
        r = Atayici(veri).ata(ist)
        assert r.atama["durum"] == "atandi", r.neden
        assert sorted(a["sinyal"] for a in r.atama["atamalar"]) == ["SCL", "SDA"]
        assert {a["ihtiyac_id"] for a in r.atama["atamalar"]} == {f"{arayuz.lower()}_1"}
        assert [i.kod for i in Denetleyici(veri).denetle(ist, r.atama) if i.seviye == "hata"] == []


def test_i2c_ve_lp_i2c_ayri_hatlar(veri):
    from pinsecim.atayici import Atayici
    r = Atayici(veri).ata(istek("QFN32", "I2C", "I2C", "LP_I2C", "LP_I2C"))
    assert r.atama["durum"] == "atandi" and len(r.atama["atamalar"]) == 4


def test_i2c_ortak_sinyal_ikinci_ornekte_cakisma_degil(veri):
    from pinsecim.denetim import Denetleyici
    ist = istek("QFN40", "I2C", "I2C")
    atama = {"durum": "atandi", "atamalar": [
        {"ihtiyac_id": "i2c_1", "sinyal": "SDA", "gpio": 0}, {"ihtiyac_id": "i2c_1", "sinyal": "SCL", "gpio": 1},
        {"ihtiyac_id": "i2c_2", "sinyal": "SDA", "gpio": 0}, {"ihtiyac_id": "i2c_2", "sinyal": "SCL", "gpio": 1}]}
    kodlar_ = [i.kod for i in Denetleyici(veri).denetle(ist, atama) if i.seviye == "hata"]
    assert "CAKISMA" not in kodlar_ and "EKSIK_SINYAL" not in kodlar_ and "ADET_ASIMI" not in kodlar_


def test_i2c_tercihi_ortak_hatta(veri):
    from pinsecim.atayici import Atayici
    ist = istek("QFN40", "I2C", "I2C", pin_tercihleri=[{"arayuz": "I2C", "sinyal": "SDA", "gpio": 21}],
                kullanilmayacak=[])
    r = Atayici(veri).ata(ist)
    assert r.atama["durum"] == "atandi" and {"ihtiyac_id": "i2c_1", "sinyal": "SDA", "gpio": 21} in r.atama["atamalar"]


def test_spi_davranisi_degismedi(veri):
    from pinsecim.atayici import Atayici
    r = Atayici(veri).ata(istek("QFN40", *["SPI"] * 7))
    assert r.atama["durum"] == "mumkun_degil" and "7 CS gerekiyor, en çok 6 var" in r.neden


def test_i2c_ortak_hat_komut_satiri(monkeypatch, capsys):
    import json

    from asu_llmcore import OllamaYaniti

    from pinsecim import __main__ as cli, hat

    class Sahte:
        def uret(self, mesajlar, sema=None, sabit_onek=None):
            j = {"ihtiyaclar": [{"arayuz": "I2C", "dayanak": "Üç I2C sensörünü", "adet": 3, "kaynak": "istekte_acik"}],
                 "pin_tercihleri": [], "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [], "sorular": [],
                 "baglam_ifadeleri": [], "diger_ifadeler": [], "desteklenmeyenler": [], "durum": "tamam", "eksik": []}
            return OllamaYaniti(ham=json.dumps(j, ensure_ascii=False), json=j, model="sahte")

    asil = hat.calistir
    monkeypatch.setattr(cli.hat, "calistir", lambda *a, **k: asil(*a, **{**k, "istemci": Sahte(), "iz": None}))
    assert cli.main(["Üç I2C sensörünü okuyacağım.", "--paket", "QFN32"]) == 0
    cikti = capsys.readouterr().out
    assert "Sonuç: atandı" in cikti
    assert "I2C ortak hat: i2c_2, i2c_3 ayrı pin almaz; SDA, SCL i2c_1 ile ortak (cihazlar adresle ayrılır)." in cikti


def test_i2c_ikinci_ornek_ayri_hat_adet_asimi(veri):
    from pinsecim.denetim import Denetleyici
    ist = istek("QFN32", "I2C", "I2C")
    atama = {"durum": "atandi", "atamalar": [
        {"ihtiyac_id": "i2c_1", "sinyal": "SDA", "gpio": 0}, {"ihtiyac_id": "i2c_1", "sinyal": "SCL", "gpio": 1},
        {"ihtiyac_id": "i2c_2", "sinyal": "SDA", "gpio": 2}, {"ihtiyac_id": "i2c_2", "sinyal": "SCL", "gpio": 3}]}
    u = [i for i in Denetleyici(veri).denetle(ist, atama) if i.kod == "ADET_ASIMI"]
    assert len(u) == 1 and "I2C" in u[0].mesaj

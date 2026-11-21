"""Adım 10b kart verisi: tablolar ve kaynaklar, --kart adı, --kart / --paket çelişkisi, kart_eksik, doğrulama
durumu işareti, görev notu, strapping uyarısı, kartlı atama notu."""

from __future__ import annotations

import json

import pytest

from asu_llmcore import OllamaYaniti

from pinsecim import __main__ as cli, hat, kart as kart_mod, pinveri, sozluk as sozluk_mod
from pinsecim.cevap import Cevaplayici

BAGLAM = {"usb_serial_jtag": True, "uart0_konsol": True, "jtag_pinleri": False, "harici_flash_beslemesi": False}


@pytest.fixture(scope="module")
def K():
    return kart_mod.yukle()


@pytest.fixture(scope="module")
def veri():
    return pinveri.yukle()


@pytest.fixture(scope="module")
def s():
    return sozluk_mod.yukle()


@pytest.fixture(scope="module")
def cev(veri, s, K):
    return Cevaplayici(veri, s, K)


# ------------------------------------------------------------------ tablolar
def test_kartlar_ve_paketleri(K):
    assert {k["kisa_ad"]: (k["paket"], k["dogrulama_durumu"]) for k in K.kartlar} == {
        "nanoESP32-C6-v1.0": ("QFN40", "kaynak_belge"), "nanoESP32-C6-v0.2": ("QFN40", "dogrulanmadi"),
        "SuperMini": ("QFN32", "dogrulanmadi")}
    assert K.bul("SuperMini")["cip"] == "ESP32-C6FH4" and K.bul("nanoESP32-C6-v1.0")["modul"] == "ESP32-C6-WROOM-1"


def test_kaynak_turleri(K):
    turler = {k["kisa_ad"]: k["kaynak_turu"] for k in K.kartlar}
    assert turler == {"nanoESP32-C6-v1.0": "uretici_semasi", "nanoESP32-C6-v0.2": "kullanici_envanteri",
                      "SuperMini": "topluluk"}


def test_modul_pinleri_wroom1(K):
    m = [x for x in K.modul_pinleri if x["modul"] == "ESP32-C6-WROOM-1"]
    assert len(m) == 29 and all(x["dogrulama_durumu"] == "kaynak_belge" for x in m)
    assert {x["pin_no"]: x["gpio_no"] for x in m if x["gpio_no"] is not None}[24] == 17    # RXD0
    assert m[0]["kaynak_belge"].startswith("ESP32-C6-WROOM-1") and m[0]["teyit_belge"].startswith("nanoESP32-C6")


def test_durum_dagilimi(K):
    for kisa, beklenen in (("nanoESP32-C6-v1.0", {"kaynak_belge", "dogrulanmadi"}),     # D3 güç LED'i dogrulanmadi
                           ("nanoESP32-C6-v0.2", {"dogrulanmadi"}), ("SuperMini", {"dogrulanmadi"})):
        k = K.bul(kisa)
        satirlar = K.pinleri(k) + K.parcalari(k, ("led", "ws2812", "buton", "usb", "usb_uart", "sarj", "flash"))
        assert {x["dogrulama_durumu"] for x in satirlar} == beklenen, kisa
    v02 = K.bul("nanoESP32-C6-v0.2")
    assert all("v1.0 şematiğinden aktarıldı; sürüm farkı doğrulanmadı" in x["not_"] for x in K.pinleri(v02))
    assert any(p["aciklama"] == "16 MB (N16)" and p["kaynak_turu"] == "kullanici_envanteri"
               for p in K.parcalari(v02, ("flash",)))
    sarj = K.parcalari(K.bul("SuperMini"), ("sarj",))
    assert len(sarj) == 1 and "LTH7R" in sarj[0]["not_"]


@pytest.mark.parametrize("ad, kisa", [("SuperMini", "SuperMini"), ("supermini", "SuperMini"),
                                      ("ESP32-C6 Super Mini", "SuperMini"), ("nanoESP32-C6 (v0.2)", "nanoESP32-C6-v0.2"),
                                      ("nanoESP32-C6-v1.0", "nanoESP32-C6-v1.0")])
def test_kart_adi(K, ad, kisa):
    assert K.bul(ad)["kisa_ad"] == kisa


def test_kart_adi_belirsiz_ya_da_yok(K):
    with pytest.raises(kart_mod.KartHatasi, match="birden çok karta uyuyor"):
        K.bul("nanoESP32-C6")
    with pytest.raises(kart_mod.KartHatasi, match="adlı kart yok"):
        K.bul("C6-03")


# ------------------------------------------------------------------ cevaplayıcı
def test_kart_eksik_pakete_uyan_kartlar(cev):
    c = cev.cevapla({"soru": "Kartta hangi LED var?", "konu": "kart_led"}, "QFN32", BAGLAM)
    assert c["durum"] == "kart_eksik" and c["mesaj"]["anahtar"] == "cevap.kart_eksik"
    assert c["satirlar"] == ["QFN32 paketine uyan kartlar: SuperMini (ESP32-C6 Super Mini; DOĞRULANMADI)"]


def test_kart_led_gorev_notu_dogrulanmadi_ve_strapping(cev, K):
    k = K.bul("SuperMini")
    c = cev.cevapla({"soru": "Hangi LED durum gösterir?", "konu": "kart_led"}, "QFN32", BAGLAM, k)
    assert c["durum"] == "cevap" and c["parametre"]["kart"] == "SuperMini"
    assert any("LED'lere görev" in x for x in c["satirlar"])
    led = [x for x in c["satirlar"] if x.startswith("[DOĞRULANMADI] PD2")]
    assert len(led) == 1 and "GPIO15; aktif yüksek" in led[0] and "(topluluk)" in led[0]
    assert any(x.startswith("Uyarı (PD2): GPIO15 strapping pini") for x in c["satirlar"])
    assert any(x.startswith("Uyarı (LED1): GPIO8 strapping pini") for x in c["satirlar"])
    assert len(c["dogrulanmadi"]) == 4                      # kart satırı + 3 LED


def test_kaynak_belgeli_satir_isaretsiz(cev, K):
    c = cev.cevapla({"soru": "Butonlar?", "konu": "kart_buton"}, "QFN40", BAGLAM, K.bul("nanoESP32-C6-v1.0"))
    s1 = [x for x in c["satirlar"] if x.startswith("S1 ")]
    assert len(s1) == 1 and "· kaynak belgede ·" in s1[0] and "(uretici_semasi)" in s1[0]
    assert any(x.startswith("Uyarı (S1): GPIO9 strapping pini") for x in c["satirlar"]) and c["dogrulanmadi"] == []


def test_kart_pin_cikisi_modul_kaynagi(cev, K):
    c = cev.cevapla({"soru": "Pinler?", "konu": "kart_pin_cikisi"}, "QFN40", BAGLAM, K.bul("nanoESP32-C6-v0.2"))
    assert any(x.startswith("[DOĞRULANMADI] J6 (J6 konnektörü): 1 GND, 2 GPIO2, 3 GPIO3, 4 TXD0=GPIO16") for x in c["satirlar"])
    assert any("Modül pin → GPIO eşlemesi: ESP32-C6-WROOM-1" in x and "Table 3-1" in x for x in c["satirlar"])


# ------------------------------------------------------------------ komut satırı
class Sahte:
    def __init__(self, yanitlar):
        self.yanitlar = list(yanitlar)

    def uret(self, mesajlar, sema=None, sabit_onek=None):
        j = self.yanitlar.pop(0)
        return OllamaYaniti(ham=json.dumps(j, ensure_ascii=False), json=j, model="sahte")


def test_kart_paket_celiskisi(capsys):
    assert cli.main(["Bir zil.", "--kart", "SuperMini", "--paket", "QFN40"]) == 1
    assert "--paket QFN40 ile --kart SuperMini çelişiyor" in capsys.readouterr().err


def test_kart_ya_da_paket_gerekli(capsys):
    assert cli.main(["Bir zil."]) == 1
    assert "--paket ya da --kart gerekli" in capsys.readouterr().err


def test_kartli_atama_ozeti(veri, s, K, capsys):
    metin = "Bir peltier süreceğim."
    y = {"ihtiyaclar": [{"arayuz": "GPIO_OUT", "dayanak": "Bir peltier süreceğim", "adet": 1, "kaynak": "model_cikarimi"}],
         "pin_tercihleri": [], "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [], "sorular": [],
         "baglam_ifadeleri": [], "diger_ifadeler": [], "desteklenmeyenler": [], "durum": "tamam", "eksik": []}
    k = K.bul("SuperMini")
    h = hat.calistir(metin, k["paket"], BAGLAM, veri, Sahte([y]), iz=None, sozluk=s, kart=k, kartlar=K)
    cli.yazdir(h, veri)
    cikti = capsys.readouterr().out
    assert cikti.startswith("İstek: ") and "Kart: SuperMini · Paket: QFN32" in cikti
    assert "Kart düzeyi: SuperMini; adaylar karta çıkan pinler (17 konnektör pini, 5 ped)." in cikti   # Adım 10c
    assert "GPIO0 (H1-8)" in cikti and "Not: kart verisi doğrulanmadı: kart satırı" in cikti

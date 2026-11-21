"""Adım 10, modelsiz: soru ayrımı (şema alanları, denetim), emin_degilim denetimi, durum mesajları, cevaplayıcı."""

import json

import pytest

from asu_llmcore import Durum, OllamaYaniti
from pinsecim import cagrilar, hat, pinveri, semalar, sozluk as sozluk_mod
from pinsecim.__main__ import yazdir
from pinsecim.cevap import Cevaplayici, arayuz_bul

BAGLAM = {"usb_serial_jtag": True, "uart0_konsol": True, "jtag_pinleri": False, "harici_flash_beslemesi": False}
BOS = {"ihtiyaclar": [], "pin_tercihleri": [], "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [], "sorular": [],
       "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": "tamam", "eksik": []}


@pytest.fixture(scope="module")
def veri():
    return pinveri.yukle()


@pytest.fixture(scope="module")
def sozluk():
    return sozluk_mod.yukle()


@pytest.fixture(scope="module")
def cev(veri, sozluk):
    return Cevaplayici(veri, sozluk)


class Sahte:
    def __init__(self, yanitlar):
        self.yanitlar = list(yanitlar)

    def uret(self, mesajlar, sema=None, sabit_onek=None):
        j = self.yanitlar.pop(0)
        if "ihtiyaclar" in j and "diger_ifadeler" not in j:                 # Adım 10a öncesi biçim
            j = {**j, "diger_ifadeler": []}
        return OllamaYaniti(ham=json.dumps(j, ensure_ascii=False), json=j, model="sahte")


def kodlar(d, y):
    return [(i.kod, i.alan) for i in d(y) if i.seviye == "hata"]


# ------------------------------------------------------------------ veri ve istem
def test_konular_ve_mesajlar_veritabanindan(sozluk):
    assert [k["konu"] for k in sozluk.soru_konulari] == ["pin_islevi", "pin_kisiti", "arayuz_pinleri", "paket_pinleri",
                                                         "kart_led", "kart_buton", "kart_pin_cikisi", "diger"]
    assert {k["konu"]: k["cevap_turu"] for k in sozluk.soru_konulari}["kart_led"] == "kart"          # Adım 10b
    assert sozluk.eksik_kodlari == ["adet_belirsiz", "arayuz_belirsiz", "celiskili", "cihaz_belirsiz"]
    for e in sozluk.eksik_kodlari:
        m = sozluk.mesaj(f"eksik.{e}")
        assert m["mesaj_tr"] and m["ne_yazmali_tr"] and m["model_tanimi"]
    for d in ("desteklenmiyor", "emin_degilim", "KULLANICIYA", "JSON_GECERSIZ"):
        assert sozluk.mesaj(f"durum.{d}")["mesaj_tr"]
    with pytest.raises(pinveri.VeriHatasi):
        sozluk.mesaj("durum.yok_boyle")


def test_istem_konu_ve_eksik_listesi(veri, sozluk):
    sistem = cagrilar.ihtiyac_sistemi(veri, sozluk)
    assert "Question topics (konu: meaning):\n- pin_islevi: what functions a given GPIO has" in sistem
    assert "- cihaz_belirsiz: the description does not say which device or function is connected" in sistem
    for l in cagrilar._istem("ihtiyac_sistem.txt").splitlines():      # her örnek yeni şemaya uyar
        if l.startswith("Answer: {"):
            assert not semalar_ihlali(json.loads(l[8:]), sozluk)


def semalar_ihlali(y, sozluk):
    from asu_llmcore.dongu import sema_ihlalleri
    return sema_ihlalleri(semalar.ihtiyac_semasi(list(semalar.ARAYUZLER), [k["konu"] for k in sozluk.soru_konulari],
                                                 sozluk.eksik_kodlari), y)


# ------------------------------------------------------------------ denetim
def test_soru_dayanak_denetimi(sozluk):
    metin = "Bir röle süreceğim. GPIO5 hangi işlevlere sahip?"
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), sozluk)
    y = {**BOS, "ihtiyaclar": [{"arayuz": "GPIO_OUT", "dayanak": "Bir röle süreceğim", "adet": 1,
                                "kaynak": "model_cikarimi"}],
         "diger_pin_bahisleri": [{"gpio": 5, "dayanak": "GPIO5 hangi işlevlere sahip?"}],
         "sorular": [{"soru": "GPIO5 hangi işlevlere sahip?", "konu": "pin_islevi"}]}
    assert kodlar(d, y) == []
    assert kodlar(d, {**y, "diger_pin_bahisleri": []}) == []          # sorudaki GPIO'yu soru taşır
    kotu = {**y, "diger_pin_bahisleri": [], "sorular": [{"soru": "GPIO5 hangi işlevlere sahiptir?", "konu": "pin_islevi"}]}
    assert kodlar(d, kotu) == [("DAYANAK_YOK", "sorular/0/soru"), ("PIN_BAHSI_ATLANDI", "pin_tercihleri")]
    metin2 = "Butonu GPIO5'e bağlayacağım. GPIO5 hangi işlevlere sahip?"   # soru dışında da geçen GPIO listede olmalı
    d2 = cagrilar.ihtiyac_denetleyici(metin2, list(semalar.ARAYUZLER), sozluk)
    y2 = {**BOS, "ihtiyaclar": [{"arayuz": "GPIO_IN", "dayanak": "Butonu", "adet": 1, "kaynak": "model_cikarimi"}],
          "sorular": [{"soru": "GPIO5 hangi işlevlere sahip?", "konu": "pin_islevi"}]}
    assert kodlar(d2, y2) == [("PIN_BAHSI_ATLANDI", "pin_tercihleri")]


def test_baglam_ifadesi_konusuz_hata(sozluk):
    metin = "JTAG ile hata ayıklayacağım. Kart üstünde kaç LED var?"
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), sozluk)
    y = {**BOS, "baglam_ifadeleri": ["JTAG ile hata ayıklayacağım", "Kart üstünde kaç LED var?"]}
    assert kodlar(d, y) == [("BAGLAM_KONUSUZ", "baglam_ifadeleri/1")]
    y = {**y, "baglam_ifadeleri": ["JTAG ile hata ayıklayacağım"],
         "sorular": [{"soru": "Kart üstünde kaç LED var?", "konu": "kart_led"}]}
    assert kodlar(d, y) == []


def test_eksik_durumla_tutarli(sozluk):
    d = cagrilar.ihtiyac_denetleyici("Bir şey yapacağım.", list(semalar.ARAYUZLER), sozluk)
    assert kodlar(d, {**BOS, "durum": "emin_degilim"}) == [("DURUM_TUTARSIZ", "eksik")]
    assert kodlar(d, {**BOS, "durum": "emin_degilim", "eksik": ["cihaz_belirsiz"]}) == []
    assert kodlar(d, {**BOS, "eksik": ["cihaz_belirsiz"]}) == [("DURUM_TUTARSIZ", "eksik")]


def test_emin_degilim_denetlenir_ve_duzeltilir(veri, sozluk, capsys):
    metin = "Bir şeyler bağlayacağım. Kartta buton var mı?"
    ilk = {**BOS, "baglam_ifadeleri": ["Kartta buton var mı?"], "durum": "emin_degilim", "eksik": ["cihaz_belirsiz"]}
    iyi = {**BOS, "sorular": [{"soru": "Kartta buton var mı?", "konu": "kart_buton"}], "durum": "emin_degilim",
           "eksik": ["cihaz_belirsiz"]}
    h = hat.calistir(metin, "QFN40", BAGLAM, veri, Sahte([ilk, iyi]), iz=None, sozluk=sozluk)
    a = h.cagri_a
    assert a.durum is Durum.GECTI and a.gecti_turu == 2 and a.turlar[0].ihlaller[0].kod == "BAGLAM_KONUSUZ"
    assert h.a_durumu == "emin_degilim" and h.atama is None and h.istek is None
    assert h.bildirim["durum"]["anahtar"] == "durum.emin_degilim"
    assert [e["anahtar"] for e in h.bildirim["eksik"]] == ["eksik.cihaz_belirsiz"]
    assert h.cevaplar[0]["durum"] == "kart_eksik"                   # --kart yok (Adım 10b)
    yazdir(h, veri)
    cikti = capsys.readouterr().out
    i_soru, i_neden = cikti.index("2) Sorular"), cikti.index("Atama yapılmadı:")
    assert i_soru < i_neden and "- bağlam:" not in cikti
    assert "Ne yazmalısın: Bağlanacak cihazı ya da işlevi yaz" in cikti and "--kart verilmedi" in cikti


def test_yalniz_soru_tamam_atama_yok(veri, sozluk, capsys):
    metin = "UART hangi pinlere çıkabilir?"
    y = {**BOS, "sorular": [{"soru": "UART hangi pinlere çıkabilir?", "konu": "arayuz_pinleri"}]}
    h = hat.calistir(metin, "QFN32", BAGLAM, veri, Sahte([y]), iz=None, sozluk=sozluk)
    assert h.a_durumu == "tamam" and h.pin_gerekmiyor and h.atayici is None and h.bildirim is None
    assert h.cevaplar[0]["durum"] == "cevap" and h.cevaplar[0]["parametre"]["arayuz"] == ["UART"]
    yazdir(h, veri)
    cikti = capsys.readouterr().out
    assert "3) Atama: istekte pin ihtiyacı yok; yalnız sorular cevaplandı." in cikti and "Kaynak: " in cikti


def test_soru_ve_ihtiyac_birlikte(veri, sozluk):
    metin = "Bir lamba yakacağım. Paketteki GPIO'lar hangileri?"
    y = {**BOS, "ihtiyaclar": [{"arayuz": "GPIO_OUT", "dayanak": "Bir lamba yakacağım", "adet": 1,
                                "kaynak": "model_cikarimi"}],
         "sorular": [{"soru": "Paketteki GPIO'lar hangileri?", "konu": "paket_pinleri"}]}
    h = hat.calistir(metin, "QFN40", BAGLAM, veri, Sahte([y]), iz=None, sozluk=sozluk)
    assert h.atama["durum"] == "atandi" and h.cevaplar[0]["durum"] == "cevap"


# ------------------------------------------------------------------ cevaplayıcı
def test_arayuz_bul(veri, sozluk):
    assert arayuz_bul(veri, sozluk, "LP I2C hangi pinlerde?") == ["LP_I2C"]
    assert set(arayuz_bul(veri, sozluk, "i2c ve spi pinleri")) == {"I2C", "SPI"}
    assert arayuz_bul(veri, sozluk, "watchdog led") == []


def test_pin_islevi_kaynakli(cev):
    c = cev.cevapla({"soru": "GPIO8 ne işe yarar?", "konu": "pin_islevi"}, "QFN40", BAGLAM)
    assert c["durum"] == "cevap" and c["parametre"]["gpio"] == [8]
    assert any(s.startswith("GPIO8 IO MUX: F0 ") for s in c["satirlar"])
    assert all("Datasheet v1.6" in k for k in c["kaynaklar"]) and c["kaynaklar"]


def test_pin_pakette_yok_ve_gpio_eksik(cev):
    c = cev.cevapla({"soru": "GPIO10 ne işe yarar?", "konu": "pin_islevi"}, "QFN32", BAGLAM)
    assert c["satirlar"] == [s for s in c["satirlar"] if "QFN32 paketinde pini yok" in s] and c["satirlar"]
    c = cev.cevapla({"soru": "Bu pin ne işe yarar?", "konu": "pin_islevi"}, "QFN32", BAGLAM)
    assert c["durum"] == "eksik_bilgi" and c["mesaj"]["anahtar"] == "cevap.gpio_eksik" and not c["satirlar"]


def test_pin_kisiti_baglamla(cev):
    c = cev.cevapla({"soru": "GPIO9 kısıtlı mı?", "konu": "pin_kisiti"}, "QFN40", BAGLAM)
    assert any(s.startswith("GPIO9 strapping:") for s in c["satirlar"])
    assert any(s.startswith("Bu bağlamda uyarı: GPIO9: strapping pini") for s in c["satirlar"])


def test_arayuz_pinleri_yorum_katmani(cev):
    c = cev.cevapla({"soru": "SPI hangi pinlere gider?", "konu": "arayuz_pinleri"}, "QFN32", BAGLAM)
    assert c["yorumlar"] == ["SPI2 sinyalleri GPIO matrisiyle GPIO3'e gider. (veren: Web AI)"]
    c = cev.cevapla({"soru": "ADC hangi pinlerde?", "konu": "arayuz_pinleri"}, "QFN40", BAGLAM)
    assert c["satirlar"][0].startswith("ADC AIN (QFN40, 7 pin)")
    c = cev.cevapla({"soru": "Hangi pinlerden veri gönderebilirim?", "konu": "arayuz_pinleri"}, "QFN40", BAGLAM)
    assert c["durum"] == "eksik_bilgi" and c["mesaj"]["anahtar"] == "cevap.arayuz_eksik"


def test_paket_pinleri_ve_tablosuz_konular(cev, veri):
    c = cev.cevapla({"soru": "Hangi GPIO'lar var?", "konu": "paket_pinleri"}, "QFN32", BAGLAM)
    assert c["satirlar"][0].startswith(f"QFN32 paketinde {len(veri.paket_gpio['QFN32'])} GPIO var:")
    assert "yasak: " in c["satirlar"][1] and "PIN_USB" in c["satirlar"][1]
    c = cev.cevapla({"soru": "x", "konu": "diger"}, "QFN40", BAGLAM)
    assert c["durum"] == "tabloda_yok" and c["mesaj"]["anahtar"] == "cevap.tabloda_yok" and not c["satirlar"]
    for konu in ("kart_led", "kart_pin_cikisi"):                    # Adım 10b: kart yoksa kart_eksik + uyan kartlar
        c = cev.cevapla({"soru": "x", "konu": konu}, "QFN40", BAGLAM)
        assert c["durum"] == "kart_eksik" and c["mesaj"]["anahtar"] == "cevap.kart_eksik"
        assert c["satirlar"][0].startswith("QFN40 paketine uyan kartlar: ")

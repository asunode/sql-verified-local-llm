"""Adım 10c: SPI çoklu CS (L-1), RMT_TX / RMT_RX (L-5), küçük düzeltmeler. Cümle ve cihazlar set dışı."""

from __future__ import annotations

import pytest

from pinsecim import cagrilar, kart as kart_mod, pinveri, semalar, sozluk as sozluk_mod
from pinsecim.atayici import Atayici
from pinsecim.cevap import Cevaplayici
from pinsecim.denetim import Denetleyici

BAGLAM = {"usb_serial_jtag": True, "uart0_konsol": True, "jtag_pinleri": False, "harici_flash_beslemesi": False}


@pytest.fixture(scope="module")
def veri():
    return pinveri.yukle()


@pytest.fixture(scope="module")
def s():
    return sozluk_mod.yukle()


def istek(paket, *arayuzler, **ek):
    return {"paket": paket, "baglam": BAGLAM, "ihtiyaclar": cagrilar.kimlik_ver([{"arayuz": a} for a in arayuzler]), **ek}


def hatalar(veri, ist, atama):
    return [i.kod for i in Denetleyici(veri).denetle(ist, atama) if i.seviye == "hata"]


# ------------------------------------------------------------------ SPI çoklu CS (L-1)
def test_spi_uc_cihaz_tek_hat(veri):
    ist = istek("QFN40", "SPI", "SPI", "SPI", "GPIO_OUT")
    r = Atayici(veri).ata(ist)
    assert r.atama["durum"] == "atandi"
    a = [(x["ihtiyac_id"], x["sinyal"]) for x in r.atama["atamalar"]]
    assert a[:6] == [("spi_1", "SCLK"), ("spi_1", "MOSI"), ("spi_1", "MISO"), ("spi_1", "CS"), ("spi_2", "CS"),
                     ("spi_3", "CS")]
    assert len({x["gpio"] for x in r.atama["atamalar"]}) == 7 and hatalar(veri, ist, r.atama) == []


def test_spi_cs_tasmasi_kaynakli(veri):
    r = Atayici(veri).ata(istek("QFN32", *["SPI"] * 7))
    assert r.atama["durum"] == "mumkun_degil"
    assert r.neden.startswith("SPI ×7: tek hatta her cihaz ayrı CS ister; 7 CS gerekiyor, en çok 6 var (SPI2_CS; ")
    assert "4.2.1.2 p.51" in r.neden
    assert Atayici(veri).ata(istek("QFN32", *["SPI"] * 6)).atama["durum"] == "atandi"


def test_spi_ortak_sinyal_ayni_pinde_cakisma_degil(veri):
    ist = istek("QFN40", "SPI", "SPI")
    atama = {"durum": "atandi", "atamalar": [
        {"ihtiyac_id": "spi_1", "sinyal": s, "gpio": g} for s, g in (("SCLK", 0), ("MOSI", 1), ("MISO", 2), ("CS", 3))
    ] + [{"ihtiyac_id": "spi_2", "sinyal": "SCLK", "gpio": 0}, {"ihtiyac_id": "spi_2", "sinyal": "CS", "gpio": 10}]}
    assert hatalar(veri, ist, atama) == []
    eksik = {**atama, "atamalar": atama["atamalar"][:4]}
    assert hatalar(veri, ist, eksik) == ["EKSIK_SINYAL"]             # spi_2 CS yok


def test_spi_tercih_ortak_saat(veri):
    ist = istek("QFN40", "SPI", "SPI", pin_tercihleri=[{"arayuz": "SPI", "sinyal": "SCLK", "gpio": 21}])
    r = Atayici(veri).ata(ist)
    assert r.atama["durum"] == "atandi"
    assert {(x["ihtiyac_id"], x["sinyal"]): x["gpio"] for x in r.atama["atamalar"]}[("spi_1", "SCLK")] == 21


# ------------------------------------------------------------------ RMT (L-5)
def test_rmt_arayuzleri_ve_istem_listesi(veri, s):
    assert semalar.ARAYUZLER["RMT_TX"] == ["OUT"] and semalar.ARAYUZLER["RMT_RX"] == ["IN"]
    assert list(semalar.ARAYUZLER)[-2:] == ["RMT_TX", "RMT_RX"]                   # liste sonuna eklendi
    sistem = cagrilar.ihtiyac_sistemi(veri, s)
    assert "- RMT_TX: OUT; One RMT transmit channel" in sistem and "- RMT_RX: IN; " in sistem
    a = veri.arayuzler["RMT_TX"]
    assert (a["yonlendirme"], a["cevre_birim"], a["adet_adi"]) == ("GPIO_MATRISI", "RMT", "RMT")
    assert veri.adetler["RMT"]["adet"] == 4 and veri.adetler["RMT"]["sayfa"] == 56


def test_rmt_atama_ve_adet(veri):
    ist = istek("QFN32", "RMT_TX", "RMT_RX", "GPIO_IN")
    r = Atayici(veri).ata(ist)
    assert r.atama["durum"] == "atandi" and hatalar(veri, ist, r.atama) == []
    assert all(x["gpio"] in veri.aday_gpio("QFN32", "RMT_TX", "OUT") for x in r.atama["atamalar"][:1])
    r = Atayici(veri).ata(istek("QFN40", *["RMT_TX"] * 3, *["RMT_RX"] * 2))
    assert r.atama["durum"] == "mumkun_degil" and "en çok 4" in r.neden and "4.2.1.11 p.56" in r.neden


@pytest.mark.parametrize("metin", ["WS2812 şerit", "NeoPixel halka", "adreslenebilir LED şeridi"])
def test_rmt_es_adlari(s, metin):
    assert s.arayuz_adlari(metin, list(semalar.ARAYUZLER)) == ["RMT_TX"]


# ------------------------------------------------------------------ küçük düzeltmeler
def test_sayi_yarim_ayni_degerde_yok(s):
    metin = "Bir çift zil çalacak."
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), s)
    y = {"ihtiyaclar": [{"arayuz": "GPIO_OUT", "dayanak": "çift zil çalacak", "adet": 2, "kaynak": "model_cikarimi"}],
         "baglam_ifadeleri": [], "diger_ifadeler": [], "desteklenmeyenler": [], "durum": "tamam"}
    assert not [i for i in d(y) if i.kod == "SAYI_YARIM"]
    metin = "On iki zil çalacak."
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), s)
    y["ihtiyaclar"][0].update(dayanak="iki zil çalacak", adet=12)
    assert [i.kod for i in d(y) if i.kod == "SAYI_YARIM"] == ["SAYI_YARIM"]


@pytest.mark.parametrize("paket, ornek", [("QFN40", "--kart nanoESP32-C6-v0.2"), ("QFN32", "--kart SuperMini")])
def test_kart_eksik_ornegi_pakete_uyan_kart(veri, s, paket, ornek):
    c = Cevaplayici(veri, s, kart_mod.yukle()).cevapla({"soru": "LED?", "konu": "kart_led"}, paket, BAGLAM)
    assert c["mesaj"]["ornek"] == ornek


def test_kart_verisi_yok_mesaji_kaldirildi(s):
    assert "cevap.kart_verisi_yok" not in s.mesajlar


# ------------------------------------------------------------------ kart düzeyi atama
def sahte_kart(konnektor, ped=(), parca=(), usb_uart=()):
    """Sınama için kart bilgisi (kart.atama_bilgisi biçimi)."""
    k = {"durum": "kaynak_belge", "kaynak": "sınama"}
    return {"kisa_ad": "SINAMA", **k,
            "pinler": [{"gpio": g, "etiket": f"J1-{i}", "tur": "konnektor", **k} for i, g in enumerate(konnektor, 1)]
            + [{"gpio": g, "etiket": f"P-{i}", "tur": "ped", **k} for i, g in enumerate(ped, 1)],
            "parcalar": [{"gpio": g, "ad": f"D{g}", "aciklama": "WS2812B RGB LED", "tur": "ws2812", **k} for g in parca],
            "usb_uart": [{"ad": a, "aciklama": "CH343P USB-UART köprüsü", **k} for a in usb_uart]}


def kodlar(veri, ist, atama):
    return [i.kod for i in Denetleyici(veri).denetle(ist, atama)]


def test_kart_asamalari_konnektor_ped_parca(veri):
    kart = sahte_kart([0, 1, 2, 3, 18, 8], ped=[19], parca=[8])
    for n, asama, ped, parca in ((5, "konnektor", [], []), (6, "ped", [19], []), (7, "parca", [19], [8])):
        ist = istek("QFN40", *["GPIO_OUT"] * n, kart=kart)
        r = Atayici(veri).ata(ist)
        assert r.atama["durum"] == "atandi", n
        assert (r.kart_ozeti["asama"], r.kart_ozeti["kullanilan_ped"], r.kart_ozeti["kullanilan_parca"]) == (asama, ped, parca)
        assert {x["gpio"] for x in r.atama["atamalar"]} <= {0, 1, 2, 3, 18, 8, 19}
        k = kodlar(veri, ist, r.atama)
        assert ("KART_PED" in k) == bool(ped) and ("KART_PARCA" in k) == bool(parca) and "KART_PIN_YOK" not in k
    r = Atayici(veri).ata(istek("QFN40", *["GPIO_OUT"] * 8, kart=kart))
    assert r.atama["durum"] == "mumkun_degil" and r.neden.startswith("SINAMA kartının konnektör ve pedlerine çıkan pinlerle:")


def test_kart_disinda_pin_atanmaz_ve_tercih(veri):
    kart = sahte_kart([0, 1, 2, 3])
    ist = istek("QFN40", "GPIO_OUT", "GPIO_OUT", kart=kart, pin_tercihleri=[{"arayuz": "GPIO_OUT", "sinyal": "", "gpio": 21}])
    r = Atayici(veri).ata(ist)
    assert r.atama["durum"] == "tercih_uygulanamadi" and r.tercih_sorunlari[0]["kod"] == "KART_PIN_YOK"
    assert "Kartta çıkan bir pin seç: GPIO0–GPIO3" in r.tercih_sorunlari[0]["oneri"]
    assert {x["gpio"] for x in r.alternatif["atamalar"]} <= {0, 1, 2, 3}
    disarida = {"durum": "atandi", "atamalar": [{"ihtiyac_id": "gpio_out_1", "sinyal": "OUT", "gpio": 0},
                                                {"ihtiyac_id": "gpio_out_2", "sinyal": "OUT", "gpio": 21}]}
    assert "KART_PIN_YOK" in [i.kod for i in Denetleyici(veri).denetle({**ist, "pin_tercihleri": []}, disarida)
                              if i.seviye == "hata"]


def test_kart_tercih_parca_pinine_duserse_uygulanir(veri):
    kart = sahte_kart([0, 1, 2, 3, 8], parca=[8])
    ist = istek("QFN40", "GPIO_OUT", kart=kart, pin_tercihleri=[{"arayuz": "GPIO_OUT", "sinyal": "", "gpio": 8}])
    r = Atayici(veri).ata(ist)
    assert r.atama["durum"] == "atandi" and r.atama["atamalar"][0]["gpio"] == 8
    u = [i for i in Denetleyici(veri).denetle(ist, r.atama) if i.kod == "KART_PARCA"]
    assert len(u) == 1 and u[0].seviye == "uyari" and "kart üstü D8 WS2812B RGB LED bu pine bağlı" in u[0].mesaj_tr


def test_kart_uart_koprusu_uyarisi(veri):
    k = kart_mod.yukle()
    bilgi = k.atama_bilgisi(k.bul("nanoESP32-C6-v1.0"))
    ist = {**istek("QFN40", "GPIO_IN", kart=bilgi, pin_tercihleri=[{"arayuz": "GPIO_IN", "sinyal": "", "gpio": 16}]),
           "baglam": {**BAGLAM, "uart0_konsol": False}}
    r = Atayici(veri).ata(ist)
    assert r.atama["durum"] == "atandi" and r.atama["atamalar"][0]["gpio"] == 16
    u = [i for i in Denetleyici(veri).denetle(ist, r.atama) if i.kod == "KART_UART_KOPRU"]
    assert len(u) == 1 and "U2 CH343P USB-UART köprüsü" in u[0].mesaj_tr and "(J6-4)" in u[0].mesaj_tr
    ist["baglam"] = BAGLAM                                           # UART0 konsol: tercih hata, köprü nedende
    r = Atayici(veri).ata(ist)
    assert r.atama["durum"] == "tercih_uygulanamadi" and "U2 CH343P USB-UART köprüsü UART0'a bağlı" in \
        r.tercih_sorunlari[0]["neden"]


def test_gercek_kart_parca_pinleri_son_care(veri):
    k = kart_mod.yukle()
    bilgi = k.atama_bilgisi(k.bul("SuperMini"))                       # parça: GPIO8 WS2812, GPIO9 BOOT, GPIO15 LED
    r = Atayici(veri).ata(istek("QFN32", *["GPIO_OUT"] * 10, kart=bilgi))
    assert r.atama["durum"] == "atandi" and r.kart_ozeti["asama"] == "konnektor"
    assert not {x["gpio"] for x in r.atama["atamalar"]} & {8, 9, 15, 21, 22, 23, 12, 13}


# ------------------------------------------------------------------ --rapor
def test_rapor_dosyasi_cikti_ayni(veri, s, tmp_path, monkeypatch, capsys):
    import json

    from asu_llmcore import OllamaYaniti

    from pinsecim import __main__ as cli, hat

    class Sahte:
        def uret(self, mesajlar, sema=None, sabit_onek=None):
            j = {"ihtiyaclar": [{"arayuz": "GPIO_OUT", "dayanak": "Bir peltier süreceğim", "adet": 1,
                                 "kaynak": "model_cikarimi"}], "pin_tercihleri": [], "kullanilmayacak_pinler": [],
                 "diger_pin_bahisleri": [], "sorular": [], "baglam_ifadeleri": [], "diger_ifadeler": [],
                 "desteklenmeyenler": [], "durum": "tamam", "eksik": []}
            return OllamaYaniti(ham=json.dumps(j, ensure_ascii=False), json=j, model="sahte")

    asil = hat.calistir
    monkeypatch.setattr(cli.hat, "calistir", lambda *a, **k: asil(*a, **{**k, "istemci": Sahte(), "iz": None}))
    yol = tmp_path / "r" / "rapor.md"
    assert cli.main(["Bir peltier süreceğim.", "--kart", "SuperMini", "--rapor", str(yol)]) == 0
    cikti = capsys.readouterr().out
    md = yol.read_text(encoding="utf-8")
    assert md.split("## Komut satırı çıktısı\n\n```\n")[1].split("\n```\n")[0] == cikti.rstrip("\n")
    for parca in ("# Pin seçimi raporu", "- Tarih: ", "- Kart: SuperMini (ESP32-C6 Super Mini)", "- Paket: QFN32",
                  "- Bağlam: usb_serial_jtag=evet", "- Model: gemma4:12b-it-qat, CPU (num_gpu 0), temperature 0",
                  "- İstemler: ihtiyac_sistem.txt ", "- Dondurma kaydı: ", "## Kaynaklar"):
        assert parca in md, parca
    assert md.count("| uretici_") >= 3 and "| topluluk |" in md and "| kullanici_envanteri |" in md
    assert "Kart düzeyi: SuperMini" in cikti                           # komut satırı çıktısı kart düzeyinde

"""Adım 12: SPI_ADET_IZI. Cümleler v1–v5 setlerinde ve geliştirme setinde geçmeyenlerden."""

from __future__ import annotations

import pytest

from pinsecim import cagrilar, semalar, sozluk as sozluk_mod


@pytest.fixture(scope="module")
def s():
    return sozluk_mod.yukle()


def yanit(*ihtiyaclar):
    return {"ihtiyaclar": [{"arayuz": a, "dayanak": da, "adet": n, "kaynak": "istekte_acik"} for a, da, n in ihtiyaclar],
            "pin_tercihleri": [], "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [], "sorular": [],
            "baglam_ifadeleri": [], "diger_ifadeler": [], "desteklenmeyenler": [], "durum": "tamam", "eksik": []}


def izler(s, metin, y):
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), s, None)
    return [i for i in d(y) if i.kod == "SPI_ADET_IZI"]


@pytest.mark.parametrize("metin, dayanak, adet, cihaz", [
    ("Bir flaş belleği ve bir ST7735 ekranı ortak SPI hattına takacağım.",
     "Bir flaş belleği ve bir ST7735 ekranı ortak SPI hattına takacağım", 1, 2),
    ("İki MAX31855 ve bir MCP3208 SPI üzerinden okunacak.", "İki MAX31855 ve bir MCP3208", 1, 3),
    ("İki MAX31855 ve bir MCP3208 SPI üzerinden okunacak.", "İki MAX31855 ve bir MCP3208", 2, 3),
    ("SPI ile iki termokupl çevirici, bir de ekran değil bir LoRa modülü bağlanacak.",
     "SPI ile iki termokupl çevirici", 1, 3),
    ("Dört SPI parçası olacak: üç sıcaklık çevirici ve bir ekran.",
     "Dört SPI parçası olacak: üç sıcaklık çevirici ve bir ekran", 2, 4),                     # toplam esas
])
def test_uyari(s, metin, dayanak, adet, cihaz):
    u = izler(s, metin, yanit(("SPI", dayanak, adet)))
    assert len(u) == 1 and u[0].seviye == "uyari" and u[0].alan == "ihtiyaclar/0/adet"
    assert u[0].mesaj.endswith(f"içinde {cihaz} cihaz görünüyor ama SPI adedi {adet}; her cihaz ayrı CS ister. "
                               "Doğruysa adetleri açık yaz.")
    assert u[0].mesaj.startswith(f"«{metin}» içinde")


@pytest.mark.parametrize("metin, dayanak, adet", [
    ("Bir flaş belleği ve bir ST7735 ekranı ortak SPI hattına takacağım.",
     "Bir flaş belleği ve bir ST7735 ekranı", 2),                                  # adet tutuyor
    ("SPI ile bir 16 x 2 karakter ekran süreceğim.", "SPI ile bir 16 x 2 karakter ekran", 1),      # NxM
    ("SPI ile bir 16x2 karakter ekran süreceğim.", "SPI ile bir 16x2 karakter ekran", 1),
    ("Bir SPI ekranı 5 V ile besleyip 20 MHz saatle süreceğim.", "Bir SPI ekranı", 1),           # birim
    ("Bir SPI ekranı 3,3 V ile besleyeceğim.", "Bir SPI ekranı", 1),                           # ondalık
    ("Bir SPI flaş aldım, 500 TL tuttu.", "Bir SPI flaş", 1),                                    # para
    ("Bir SPI hattına bir ekran bağlayacağım.", "Bir SPI hattına bir ekran", 1),                  # hat sözcüğü
    ("Tek bir SPI ekran kullanacağım.", "Tek bir SPI ekran", 1),                                 # tek sayı ifadesi
    ("Bir SPI ekran ve bir I2C sensör bağlayacağım.", "Bir SPI ekran", 1),                        # öteki ihtiyacın sayısı
    ("Dört SPI parçası olacak: üç sıcaklık çevirici ve bir ekran.",
     "Dört SPI parçası olacak: üç sıcaklık çevirici ve bir ekran", 4),                        # toplam ve döküm
])
def test_yanlis_alarm_yok(s, metin, dayanak, adet):
    ihtiyaclar = [("SPI", dayanak, adet)]
    if "I2C sensör" in metin:
        ihtiyaclar.append(("I2C", "bir I2C sensör", 1))
    assert izler(s, metin, yanit(*ihtiyaclar)) == []


def test_pin_bahsi_sayilmaz(s):
    metin = "Bir SPI ekranın CS ucunu GPIO 5 ve GPIO 6 üzerinden deneyeceğim."
    assert izler(s, metin, yanit(("SPI", "Bir SPI ekranın", 1))) == []


def test_i2c_icin_yok(s):
    metin = "Bir nem sensörü ve bir basınç sensörü I2C ile bağlanacak."
    assert izler(s, metin, yanit(("I2C", "Bir nem sensörü ve bir basınç sensörü I2C ile bağlanacak", 1))) == []


def test_iki_spi_ihtiyaci_toplanir(s):
    metin = "Bir flaş belleği ve bir ST7735 ekranı SPI ile bağlayacağım."
    y = yanit(("SPI", "Bir flaş belleği", 1), ("SPI", "bir ST7735 ekranı", 1))
    assert izler(s, metin, y) == []


def test_tablo(s):
    assert s.sayi_disi_mi("V", "birim") and not s.sayi_disi_mi("v", "birim")
    assert s.sayi_disi_mi("Volt", "birim") and s.sayi_disi_mi("hattına", "hat") and s.sayi_disi_mi("veri yolu", "hat")
    assert not s.sayi_disi_mi("ekran", "birim") and not s.sayi_disi_mi("hata", "hat")


def test_komut_satirinda_gorunur(monkeypatch, capsys):
    import json

    from asu_llmcore import OllamaYaniti

    from pinsecim import __main__ as cli, hat

    metin = "Bir flaş belleği ve bir ST7735 ekranı ortak SPI hattına takacağım."

    class Sahte:
        def uret(self, mesajlar, sema=None, sabit_onek=None):
            j = yanit(("SPI", metin.rstrip("."), 1))
            return OllamaYaniti(ham=json.dumps(j, ensure_ascii=False), json=j, model="sahte")

    asil = hat.calistir
    monkeypatch.setattr(cli.hat, "calistir", lambda *a, **k: asil(*a, **{**k, "istemci": Sahte(), "iz": None}))
    assert cli.main([metin, "--paket", "QFN40"]) == 0
    cikti = capsys.readouterr().out
    assert f"[UYARI] «{metin}» içinde 2 cihaz görünüyor ama SPI adedi 1; her cihaz ayrı CS ister." in cikti
    assert "Sonuç: atandı" in cikti and "1. turda geçti" in cikti      # uyarı tur açmaz, kararı değiştirmez

"""Adım 6, F1/F2: istek sözlüğü (veritabanından), sayı ayrıştırıcı ve bağlam ifadesi okuyucu."""

import pytest

from pinsecim import sozluk as sozluk_mod


@pytest.fixture(scope="module")
def s():
    return sozluk_mod.yukle()


@pytest.mark.parametrize("metin, beklenen", [
    # rakamlar
    ("3 sensör", [3]),
    ("12 buton ve 4 LED", [12, 4]),
    # sözcükler bir … yirmi
    ("Bir buton", [1]),
    ("iki röle", [2]),
    ("Üç valf", [3]),
    ("dört motor", [4]),
    ("Beş analog sensör", [5]),
    ("altı LED", [6]),
    ("yedi servo", [7]),
    ("sekiz kanal", [8]),
    ("dokuz buton", [9]),
    ("On röle", [10]),
    ("yirmi giriş", [20]),
    # bileşikler
    ("on bir valf", [11]),
    ("On dokuz lamba", [19]),
    # tek, çift, düzine
    ("tek buton", [1]),
    ("bir çift motor", [2]),
    ("çift sensör", [2]),
    ("Bir düzine buton", [12]),
    ("düzine LED", [12]),
    ("Yarım düzine LED'in", [6]),
    # Türkçe büyük harf (İ, I)
    ("İKİ RÖLE", [2]),
    ("İki eksenli analog bir joystick", [2, 1]),
    # sözcük sınırı tuzakları
    ("Biri normal, biri düşük güç", []),
    ("butonuyla birlikte", []),
    ("onay butonu", []),
    ("ikisi aynı hatta", []),
    ("onlarca sensör", []),
    ("UART0 konsol", []),
    ("BME280 ve SSD1306", []),
    ("HC-SR04 sensörü", []),
    ("altında bir buton", [1]),
    ("tekrar okunacak", []),
    # istisna: "çift yönlü" sayı değil (Adım 7, veritabanında deger NULL)
    ("çift yönlü iletişim", []),
    ("Çift yönlü bir hat", [1]),
    ("ÇİFT YÖNLÜ", []),
    ("bir çift motor, çift yönlü", [2]),
    ("", []),
])
def test_sayi_ifadeleri(s, metin, beklenen):
    assert [d for _, d in s.sayi_ifadeleri(metin)] == beklenen


def test_en_uzun_eslesme_ifadeyi_dondurur(s):
    assert s.sayi_ifadeleri("on bir ve bir çift") == [("on bir", 11), ("bir çift", 2)]


def test_sozluk_veritabanindan(s):
    assert s.sayilar[("yarım", "düzine")] == 6 and s.paylasimli == frozenset({"I2C", "LP_I2C"})
    assert ("jtag", "jtag_pinleri") in s.konular and "mayacağ" in s.olumsuzlar
    assert s.sayilar[("çift", "yönlü")] is None and s.sayilar[("çift",)] == 2


@pytest.mark.parametrize("ifade, beklenen", [
    ("JTAG pinleriyle hata ayıklama yapacağım", {"jtag_pinleri": True}),
    ("USB'yi kullanmayacağım", {"usb_serial_jtag": False}),
    ("UART0 konsol olarak kalsın", {"uart0_konsol": True}),
    ("UART0'ı konsol olarak kullanmıyorum", {"uart0_konsol": False}),
    ("Flash harici beslenecek", {"harici_flash_beslemesi": True}),
    ("Wi-Fi ile gönderilecek", {}),
])
def test_baglam_oku(s, ifade, beklenen):
    assert s.baglam_oku(ifade) == beklenen

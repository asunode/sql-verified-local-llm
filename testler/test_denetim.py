"""Adım 3: denetleyici (35 vaka), kod atayıcı, 200 rastgele istek, belirsiz satır yorumu, şemalar."""

import hashlib
import json
import random
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from asu_llmcore import Ihlal
from pinsecim import pinveri, semalar
from pinsecim.atayici import Atayici
from pinsecim.denetim import Denetleyici, adet_asimlari
from pinsecim.pinveri import VeriHatasi

KOK = Path(__file__).resolve().parents[1]
VAKA_DOSYASI = KOK / "testler" / "veri" / "denetim_vakalari.json"
VAKA_SHA256 = "0a1422c966583a9896698aabf85425851a745323eb57d3e3c47876e0c602b727"   # Web AI'ın teslim ettiği hâli
VAKALAR = json.loads(VAKA_DOSYASI.read_text(encoding="utf-8"))["vakalar"]


@pytest.fixture(scope="module")
def veri():
    return pinveri.yukle()


@pytest.fixture(scope="module")
def denetleyici(veri):
    return Denetleyici(veri)


@pytest.fixture(scope="module")
def atayici(veri):
    return Atayici(veri)


def kodlar(ihlaller: list[Ihlal]) -> tuple[list[str], list[str]]:
    return (sorted({i.kod for i in ihlaller if i.seviye == "hata"}),
            sorted({i.kod for i in ihlaller if i.seviye == "uyari"}))


def test_vaka_dosyasi_degismedi():
    assert hashlib.sha256(VAKA_DOSYASI.read_bytes()).hexdigest() == VAKA_SHA256
    assert len(VAKALAR) == 35


@pytest.mark.parametrize("vaka", VAKALAR, ids=[v["id"] for v in VAKALAR])
def test_vaka(denetleyici, vaka):
    hatalar, uyarilar = kodlar(denetleyici.denetle(vaka["istek"], vaka["atama"]))
    assert hatalar == sorted(vaka["beklenen"]["hatalar"])
    assert uyarilar == sorted(vaka["beklenen"]["uyarilar"])


def test_vakalar_semalara_uyar():
    istek, atama = Draft202012Validator(semalar.istek_semasi(["QFN40", "QFN32"])), Draft202012Validator(semalar.atama_semasi())
    for v in VAKALAR:
        assert not list(istek.iter_errors(v["istek"])), v["id"]
        assert not list(atama.iter_errors(v["atama"])), v["id"]


def test_mesajlar_ingilizce_ve_kaynakli(denetleyici):
    vaka = next(v for v in VAKALAR if v["id"] == "D05")
    (ihlal,) = denetleyici.denetle(vaka["istek"], vaka["atama"])
    assert ihlal.kod == "PIN_FLASH" and "GPIO24" in ihlal.mesaj and "p.25" in ihlal.mesaj and ihlal.alan == "atamalar/0/gpio"


def _istek_anahtari(istek: dict) -> str:
    return json.dumps(istek, sort_keys=True)


def test_atayici_vaka_istekleri(denetleyici, atayici):
    cozumsuz = set()
    for v in VAKALAR:
        r = atayici.ata(v["istek"])
        if r.atama["durum"] == "atandi":
            hatalar, _ = kodlar(denetleyici.denetle(v["istek"], r.atama))
            assert hatalar == [], (v["id"], r.atama)
        else:
            assert r.neden, v["id"]
            cozumsuz.add(_istek_anahtari(v["istek"]))
    # Adım 11a: I2C ×N tek hat. D28'in ADET_ASIMI'si ikinci örneğe ayrı pin verilen atamadan gelir (ayrı hat); istek
    # tek hatla çözülebilir. Atayıcının çözemediği istekler, istek düzeyinde birim sınırı aşılanlardır.
    adet = {_istek_anahtari(v["istek"]) for v in VAKALAR if "ADET_ASIMI" in v["beklenen"]["hatalar"]
            and adet_asimlari(denetleyici.veri, v["istek"])}
    assert cozumsuz == adet
    assert {v["id"] for v in VAKALAR if "ADET_ASIMI" in v["beklenen"]["hatalar"]
            and not adet_asimlari(denetleyici.veri, v["istek"])} == {"D28"}


def test_atayici_deterministik(atayici):
    istek = next(v for v in VAKALAR if v["id"] == "D34")["istek"]
    assert atayici.ata(istek).atama == atayici.ata(json.loads(json.dumps(istek))).atama


def test_atayici_once_uyarisiz_pin(atayici):
    istek = {"paket": "QFN32", "baglam": {"usb_serial_jtag": False, "uart0_konsol": False, "jtag_pinleri": False,
                                          "harici_flash_beslemesi": False},
             "ihtiyaclar": [{"id": "o1", "arayuz": "GPIO_OUT"}]}
    r = atayici.ata(istek)
    assert r.atama["atamalar"][0]["gpio"] == 0 and r.uyarili_pin == []
    # LP I2C yalnız GPIO6/7'ye gider; ikisi de JTAG (uyarı) — uyarılı pin gerekince kullanılır
    istek["ihtiyaclar"] = [{"id": "l1", "arayuz": "LP_I2C"}]
    r = atayici.ata(istek)
    assert [a["gpio"] for a in r.atama["atamalar"]] == [6, 7] and r.uyarili_pin == [6, 7]


def test_atayici_hata_ureten_pini_kullanmaz(atayici):
    istek = {"paket": "QFN40", "baglam": {"usb_serial_jtag": True, "uart0_konsol": True, "jtag_pinleri": True,
                                          "harici_flash_beslemesi": False},
             "ihtiyaclar": [{"id": "l1", "arayuz": "LP_I2C"}]}
    r = atayici.ata(istek)   # GPIO6/7 JTAG ve JTAG pinleri kullanılıyor: hata → çözüm yok
    assert r.atama["durum"] == "mumkun_degil" and "LP_I2C" in r.neden


def _rastgele_istek(rnd: random.Random, n: int) -> dict:
    arayuzler = list(semalar.ARAYUZLER)
    agirlik = [4, 3, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1]          # Adım 10c: RMT_TX, RMT_RX
    return {
        "paket": rnd.choice(["QFN40", "QFN32"]),
        "baglam": {k: rnd.random() < 0.5 for k in semalar.BAGLAM_ANAHTARLARI},
        "ihtiyaclar": [{"id": f"n{i}", "arayuz": a}
                       for i, a in enumerate(rnd.choices(arayuzler, agirlik, k=rnd.randint(1, 7)))],
    }


def test_rastgele_200(denetleyici, atayici):
    rnd = random.Random(20261120)
    cozulen = 0
    for i in range(200):
        istek = _rastgele_istek(rnd, i)
        r = atayici.ata(istek)
        if r.atama["durum"] == "atandi":
            cozulen += 1
            hatalar, _ = kodlar(denetleyici.denetle(istek, r.atama))
            assert hatalar == [], (istek, r.atama)
        else:
            # atayıcının reddi denetleyiciden de geçmeli (YANLIS_RET yok)
            assert kodlar(denetleyici.denetle(istek, r.atama))[0] == []
    assert 0 < cozulen < 200


def test_belirsiz_satir_yorumu(veri):
    vaka = next(v for v in VAKALAR if v["id"] == "D35")
    assert kodlar(Denetleyici(veri).denetle(vaka["istek"], vaka["atama"])) == ([], [])
    assert veri.kullanilan_yorumlar and veri.kullanilan_yorumlar[0]["deger"] == {"gpio_no": 3}
    yorumsuz = veri.yorumsuz()
    assert kodlar(Denetleyici(yorumsuz).denetle(vaka["istek"], vaka["atama"])) == ([], ["BELIRSIZ_KAYNAK"])
    # yorumsuz veride atayıcı QFN32 GPIO3'ü SPI için kullanmaz; yorumluda kullanabilir
    assert 3 not in yorumsuz.aday_gpio("QFN32", "SPI", "SCLK")
    assert 3 in veri.aday_gpio("QFN32", "SPI", "SCLK")


def test_veritabani_yoksa_hata():
    with pytest.raises(VeriHatasi):
        pinveri.yukle(port=1)


def test_veritabanindaki_sozluk_semalarla_ayni(veri):
    assert {a: r["sinyaller"] for a, r in veri.arayuzler.items()} == semalar.ARAYUZLER


def test_cekirdek_dongusune_uyar(denetleyici):
    vaka = next(v for v in VAKALAR if v["id"] == "D11")
    tek_argumanli = denetleyici.icin(vaka["istek"])
    assert kodlar(tek_argumanli(vaka["atama"])) == ([], ["PIN_JTAG", "PIN_STRAPPING"])

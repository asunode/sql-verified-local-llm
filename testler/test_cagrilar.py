"""Adım 4, modelsiz: şemalar, Çağrı A kod denetimi, Çağrı B'nin istem verisi, kimlikler, sahte modelle uçtan uca."""

import hashlib
import json
import re

import pytest
from jsonschema import Draft202012Validator

from asu_llmcore import Durum, OllamaYaniti
from pinsecim import cagrilar, hat, pinveri, semalar, sozluk as sozluk_mod
from pinsecim.__main__ import secenekler, yazdir
from pinsecim.atayici import Atayici, AtamaSonucu
from pinsecim.denetim import Denetleyici

BAGLAM = {"usb_serial_jtag": True, "uart0_konsol": True, "jtag_pinleri": False, "harici_flash_beslemesi": False}


@pytest.fixture(scope="module")
def veri():
    return pinveri.yukle()


@pytest.fixture(scope="module")
def sozluk():
    return sozluk_mod.yukle()


def test_sistem_istemi_sabit_ve_arayuzler_veritabanindan(veri, sozluk):
    sistem = cagrilar.ihtiyac_sistemi(veri, sozluk)
    assert sistem.startswith(cagrilar._istem("ihtiyac_sistem.txt"))
    for ad in semalar.ARAYUZLER:
        assert f"- {ad}: " in sistem and veri.arayuzler[ad]["tanim"] in sistem
    assert cagrilar.ihtiyac_sistemi(veri, sozluk) == sistem


GORULMUS_SETLER = ("setler/gelistirme/gelistirme_seti.json", "setler/dogrulama/dogrulama_seti_v1.json",
                   "setler/dogrulama/dogrulama_seti_v2.json", "setler/dogrulama/kapsamli_set_v3.json",
                   "setler/dogrulama/test_seti_v4.json")


def test_istem_ornekleri_setlerden_degil():                       # Adım 9: v1–v3 ve arayüz tanımları dahil
    from pinsecim import kural_verisi
    kok = cagrilar.ISTEMLER.parents[2]
    metinler = [i["metin"] for s in GORULMUS_SETLER for i in json.loads((kok / s).read_text(encoding="utf-8"))["istekler"]]
    istem = (cagrilar._istem("ihtiyac_sistem.txt") + cagrilar._istem("atama_sistem.txt")
             + " ".join(kural_verisi.ARAYUZ_TANIMLARI.values()))
    for m in metinler:
        for parca in [p.strip() for p in m.replace(";", ".").split(".") if len(p.strip()) > 15]:
            assert parca not in istem, parca
    # kurallardaki çok sözcüklü tırnaklı örnek parçalar da setlerde geçmez. v4 hariç: kural 10'daki "5 numaralı pin"
    # Adım 9'da, v4 açılmadan yazıldı ve v4'te (Y17) geçiyor; Adım 10'da eklenen parçalar v4'le de denetlendi.
    tum = " ".join(sozluk_mod.kucuk(i["metin"]) for s in GORULMUS_SETLER[:-1]
                   for i in json.loads((kok / s).read_text(encoding="utf-8"))["istekler"])
    for parca in re.findall(r'"([^"]+ [^"]+)"', istem):
        assert sozluk_mod.kucuk(parca) not in tum, parca


def kapsamsiz(d):
    """Adım 11'den önceki testler: KAPSANMAYAN_CUMLE uyarısı ayıklanır (test_11'de sınanıyor)."""
    return lambda y: [i for i in d(y) if i.kod != "KAPSANMAYAN_CUMLE"]


def test_ihtiyac_denetleyici(sozluk):
    metin = "Bir sensörü I2C ile okuyacağım ve bir lambayı yakacağım."
    d = kapsamsiz(cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), sozluk))
    iyi = {"ihtiyaclar": [{"arayuz": "I2C", "dayanak": "I2C ile okuyacağım", "adet": 1, "kaynak": "istekte_acik"},
                          {"arayuz": "GPIO_OUT", "dayanak": "bir lambayı yakacağım", "adet": 1, "kaynak": "model_cikarimi"}],
           "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": "tamam"}
    assert [(i.kod, i.seviye) for i in d(iyi)] == [("MODEL_CIKARIMI", "uyari")]
    kotu = {"ihtiyaclar": [{"arayuz": "I2C", "dayanak": "I2C ile okunacak", "adet": 1, "kaynak": "istekte_acik"}],
            "baglam_ifadeleri": [], "desteklenmeyenler": ["kamera"], "durum": "tamam"}
    assert sorted(i.kod for i in d(kotu)) == ["DAYANAK_YOK", "DURUM_TUTARSIZ"]
    assert [i.kod for i in d({"ihtiyaclar": [], "baglam_ifadeleri": [], "desteklenmeyenler": [],
                              "durum": "desteklenmiyor"})] == ["DURUM_TUTARSIZ"]


def test_tamam_bos_ihtiyac_gecerli(sozluk):                      # F3
    d = cagrilar.ihtiyac_denetleyici("Karta hiçbir şey bağlanmayacak.", list(semalar.ARAYUZLER), sozluk)
    ihl = d({"ihtiyaclar": [], "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": "tamam"})
    assert [(i.kod, i.seviye) for i in ihl] == [("KAPSANMAYAN_CUMLE", "uyari")]   # Adım 11: cümle hiçbir listede değil


def test_sayi_uyusmaz(sozluk):                                   # F1
    metin = "Dört röleyi süreceğim, iki sensörü I2C ile okuyacağım, bir de buton var."
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), sozluk)

    def y(*kalemler):
        return {"ihtiyaclar": [{"arayuz": a, "dayanak": da, "adet": n, "kaynak": "istekte_acik"} for a, da, n in kalemler],
                "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": "tamam"}
    assert d(y(("GPIO_OUT", "Dört röleyi süreceğim", 4), ("GPIO_IN", "bir de buton var", 1))) == []
    hata = d(y(("GPIO_OUT", "Dört röleyi süreceğim", 1)))
    assert [(i.kod, i.alan) for i in hata] == [("SAYI_UYUSMAZ", "ihtiyaclar/0/adet")] and "'dört' = 4" in hata[0].mesaj
    assert d(y(("I2C", "iki sensörü I2C ile okuyacağım", 1))) == []          # paylaşımlı hat: sayı cihaz sayısı
    assert d(y(("GPIO_IN", "buton var", 3))) == []                           # dayanakta sayı yok: adet serbest


@pytest.mark.parametrize("kaynak, dayanak, adet, gecer", [                  # L-4 (Web AI, Adım 7)
    ("model_cikarimi", "iki enkoder okuyacağım", 4, True),       # cihaz başına 2 hat: tam kat
    ("model_cikarimi", "iki enkoder okuyacağım", 2, True),       # eşitlik her zaman geçer
    ("model_cikarimi", "iki enkoder okuyacağım", 3, False),      # kat değil
    ("model_cikarimi", "üç step sürücüsü bağlanacak", 6, True),
    ("model_cikarimi", "üç step sürücüsü bağlanacak", 4, False),
    ("model_cikarimi", "bir enkoder okuyacağım", 2, True),        # "bir": her adet 1'in katı
    ("istekte_acik", "iki enkoder okuyacağım", 4, False),         # istekte açık: eşitlik katı
    ("istekte_acik", "iki enkoder okuyacağım", 2, True),
    ("istekte_acik", "bir enkoder okuyacağım", 2, False),
])
def test_sayi_kat_kurali(sozluk, kaynak, dayanak, adet, gecer):
    metin = "Önce bir enkoder okuyacağım, sonra iki enkoder okuyacağım, üç step sürücüsü bağlanacak."
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), sozluk)
    y = {"ihtiyaclar": [{"arayuz": "GPIO_IN", "dayanak": dayanak, "adet": adet, "kaynak": kaynak}],
         "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": "tamam"}
    hatalar = [i for i in d(y) if i.seviye == "hata"]
    assert (hatalar == []) == gecer
    if not gecer:
        assert hatalar[0].kod == "SAYI_UYUSMAZ"
        assert ("whole multiple" in hatalar[0].mesaj) == (kaynak == "model_cikarimi")


def test_cift_yonlu_sayi_degil(sozluk):
    metin = "Çift yönlü bir hattı süreceğim."
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), sozluk)
    y = {"ihtiyaclar": [{"arayuz": "GPIO_OUT", "dayanak": "Çift yönlü bir hattı süreceğim", "adet": 1,
                         "kaynak": "istekte_acik"}], "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": "tamam"}
    assert [i.kod for i in d(y) if i.seviye == "hata"] == []                 # yalnız "bir" = 1 sayılır


def test_baglam_celiskisi_uyari(sozluk):                         # F2, T-27
    metin = "JTAG ile hata ayıklayacağım. UART0 konsol olarak kalsın. Bir buton okuyacağım."
    y = {"ihtiyaclar": [{"arayuz": "GPIO_IN", "dayanak": "Bir buton okuyacağım", "adet": 1, "kaynak": "istekte_acik"}],
         "baglam_ifadeleri": ["JTAG ile hata ayıklayacağım", "UART0 konsol olarak kalsın"], "desteklenmeyenler": [],
         "durum": "tamam"}
    d = kapsamsiz(cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), sozluk, BAGLAM))
    ihl = d(y)
    assert [(i.kod, i.seviye, i.alan) for i in ihl] == [("BAGLAM_CELISKI", "uyari", "baglam_ifadeleri/0")]
    assert "--jtag-pinleri verilmedi" in ihl[0].mesaj
    assert d({**y, "baglam_ifadeleri": ["USB'yi kullanmayacağım"]})[0].mesaj.endswith(
        "ama --usb verildi; komut satırı esas alındı.")
    assert cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), sozluk, {**BAGLAM, "jtag_pinleri": True})(y) == []


def test_genislet():
    assert cagrilar.kimlik_ver(cagrilar.genislet([{"arayuz": "GPIO_OUT", "adet": 3}, {"arayuz": "I2C", "adet": 1}])) == [
        {"id": "gpio_out_1", "arayuz": "GPIO_OUT"}, {"id": "gpio_out_2", "arayuz": "GPIO_OUT"},
        {"id": "gpio_out_3", "arayuz": "GPIO_OUT"}, {"id": "i2c_1", "arayuz": "I2C"}]


def test_kimlik_ver():
    assert cagrilar.kimlik_ver([{"arayuz": "ADC"}, {"arayuz": "I2C"}, {"arayuz": "ADC"}]) == [
        {"id": "adc_1", "arayuz": "ADC"}, {"id": "i2c_1", "arayuz": "I2C"}, {"id": "adc_2", "arayuz": "ADC"}]


def test_atama_mesaji_veritabanindan(veri):
    istek = {"paket": "QFN32", "baglam": BAGLAM,
             "ihtiyaclar": cagrilar.kimlik_ver([{"arayuz": "SPI"}, {"arayuz": "ADC"}, {"arayuz": "UART"}])}
    m = cagrilar.atama_mesaji(veri, istek)
    assert "GPIO12: FORBIDDEN (PIN_USB)" in m and "GPIO4: WARNING (PIN_JTAG, PIN_STRAPPING)" in m and "GPIO0: FREE" in m
    assert "GPIO10" not in m                       # QFN32'de yok
    assert "ADC AIN: only GPIO0 (ADC1_CH0)" in m and "UART: at most 1 (UART0 is the console), requested 1" in m
    assert "read as GPIO3" in m                    # yorum katmanı (Table 2-11 pin 9)
    durumlar = cagrilar.gpio_durumlari(veri, "QFN40", {**BAGLAM, "harici_flash_beslemesi": True})
    assert durumlar[27][0] == "WARNING" and durumlar[24][0] == "FORBIDDEN"


def test_model_semalari_gecerli():
    a = semalar.ihtiyac_semasi(list(semalar.ARAYUZLER), ["pin_islevi", "diger"], ["cihaz_belirsiz"])
    Draft202012Validator.check_schema(a)
    assert list(a["properties"]) == ["ihtiyaclar", "pin_tercihleri", "kullanilmayacak_pinler", "diger_pin_bahisleri",
                                     "sorular", "baglam_ifadeleri", "diger_ifadeler", "desteklenmeyenler", "durum", "eksik"]
    assert a["properties"]["sorular"]["items"]["properties"]["konu"]["enum"] == ["pin_islevi", "diger"]
    assert a["properties"]["eksik"]["items"]["enum"] == ["cihaz_belirsiz"]
    assert a["properties"]["pin_tercihleri"]["items"]["properties"]["sinyal"]["enum"][0] == ""
    assert a["properties"]["ihtiyaclar"]["items"]["properties"]["adet"] == {"type": "integer", "minimum": 1}
    s = semalar.model_atama_semasi(["adc_1"], ["AIN"], [0, 1])
    Draft202012Validator.check_schema(s)
    assert list(s["properties"]) == ["gerekce", "durum", "atamalar"]


class Sahte:
    """Sırayla verilen ham yanıtları döner (sınır isteği yok)."""

    def __init__(self, hamlar):
        self.hamlar = list(hamlar)

    def uret(self, mesajlar, sema=None, sabit_onek=None):
        assert sabit_onek is not None and mesajlar[0]["content"].startswith(sabit_onek)
        ham = self.hamlar.pop(0)
        j = json.loads(ham)
        if "ihtiyaclar" in j and "pin_tercihleri" not in j:                 # Adım 9 öncesi biçimdeki test yanıtları
            j = {"ihtiyaclar": j["ihtiyaclar"], **{k: [] for k in semalar.PIN_LISTELERI},
                 **{k: v for k, v in j.items() if k != "ihtiyaclar"}}
            ham = json.dumps(j, ensure_ascii=False)
        if "ihtiyaclar" in j and "sorular" not in j:                        # Adım 10 öncesi biçim: soru ve eksik yok
            j = {**j, "sorular": [], "eksik": []}
            ham = json.dumps(j, ensure_ascii=False)
        if "ihtiyaclar" in j and "diger_ifadeler" not in j:                 # Adım 10a öncesi biçim: diğer ifadeler yok
            j = {**j, "diger_ifadeler": []}
            ham = json.dumps(j, ensure_ascii=False)
        return OllamaYaniti(ham=ham, json=j, model="sahte")


def test_uctan_uca_sahte_model(veri, sozluk, capsys):
    a = {"ihtiyaclar": [{"arayuz": "ADC", "dayanak": "analog", "adet": 1, "kaynak": "istekte_acik"}],
         "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": "tamam"}
    b_kotu = {"gerekce": "x", "durum": "atandi", "atamalar": [{"ihtiyac_id": "adc_1", "sinyal": "AIN", "gpio": 14}]}
    b_iyi = {"gerekce": "x", "durum": "atandi", "atamalar": [{"ihtiyac_id": "adc_1", "sinyal": "AIN", "gpio": 0}]}
    h = hat.calistir("Bir analog sensör okuyacağım.", "QFN32", BAGLAM, veri,
                     Sahte([json.dumps(a), json.dumps(b_kotu), json.dumps(b_iyi)]), model_ata=True, iz=None,
                     sozluk=sozluk)
    assert h.cagri_b.durum is Durum.GECTI and h.cagri_b.gecti_turu == 2
    assert h.cagri_b.turlar[0].ihlaller[0].kod == "SABIT_PIN" and h.atayici["atama"]["durum"] == "atandi"
    yazdir(h, veri)
    cikti = capsys.readouterr().out
    assert "2. turda denetimden geçti" in cikti and "GPIO0" in cikti


def test_desteklenmiyorsa_atama_yok(veri, sozluk):
    a = {"ihtiyaclar": [], "baglam_ifadeleri": [], "desteklenmeyenler": ["kamera"], "durum": "desteklenmiyor"}
    h = hat.calistir("Bir kamera bağlayacağım.", "QFN40", BAGLAM, veri, Sahte([json.dumps(a)]), iz=None, sozluk=sozluk)
    assert h.a_durumu == "desteklenmiyor" and h.cagri_b is None and h.atama is None


def test_pin_gerekmiyor(veri, sozluk, capsys):                   # F3: B çalışmaz, CLI söyler
    a = {"ihtiyaclar": [], "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": "tamam"}
    h = hat.calistir("Karta hiçbir şey bağlanmayacak.", "QFN32", BAGLAM, veri, Sahte([json.dumps(a)]), iz=None,
                     sozluk=sozluk)
    assert h.pin_gerekmiyor and h.cagri_b is None and h.atayici is None and h.istek is None
    yazdir(h, veri)
    assert "3) Atama: bu istek için pin ataması gerekmiyor." in capsys.readouterr().out


def test_adet_cogaltilir_ve_cli_uyarisi(veri, sozluk, capsys):   # F1 + F2 uçtan uca
    metin = "On röle süreceğim. JTAG ile hata ayıklayacağım."
    a = {"ihtiyaclar": [{"arayuz": "GPIO_OUT", "dayanak": "On röle süreceğim", "adet": 10, "kaynak": "model_cikarimi"}],
         "baglam_ifadeleri": ["JTAG ile hata ayıklayacağım"], "desteklenmeyenler": [], "durum": "tamam"}
    b = {"gerekce": "x", "durum": "atandi",
         "atamalar": [{"ihtiyac_id": f"gpio_out_{k}", "sinyal": "OUT", "gpio": g}
                      for k, g in enumerate([0, 1, 2, 3, 5, 6, 7, 10, 11, 18], 1)]}
    h = hat.calistir(metin, "QFN40", BAGLAM, veri, Sahte([json.dumps(a), json.dumps(b)]), model_ata=True, iz=None,
                     sozluk=sozluk)
    assert [n["id"] for n in h.istek["ihtiyaclar"]] == [f"gpio_out_{k}" for k in range(1, 11)]
    assert [i.kod for i in h.cagri_a.uyarilar] == ["MODEL_CIKARIMI", "BAGLAM_CELISKI"]
    yazdir(h, veri)
    cikti = capsys.readouterr().out
    assert "×10" in cikti and "[UYARI] Metinde «JTAG ile hata ayıklayacağım» geçiyor" in cikti


def test_komut_satiri_secenekleri():
    a = secenekler(["istek", "--paket", "QFN40", "--no-usb", "--jtag-pinleri", "--model-ata"])
    assert (a.usb_serial_jtag, a.uart0_konsol, a.jtag_pinleri, a.harici_flash_beslemesi, a.model_ata) == \
           (False, True, True, False, True)
    assert secenekler(["istek", "--paket", "QFN32"]).model_ata is False
    with pytest.raises(SystemExit):
        secenekler(["istek", "--paket", "QFN32", "--atayici"])       # K-6: kaldırıldı (T-45)


def test_varsayilan_akis_atayici(veri, sozluk, capsys):             # K-6: A → atayıcı, Çağrı B yok
    a = {"ihtiyaclar": [{"arayuz": "ADC", "dayanak": "analog", "adet": 1, "kaynak": "istekte_acik"}],
         "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": "tamam"}
    h = hat.calistir("Bir analog sensör okuyacağım.", "QFN32", BAGLAM, veri, Sahte([json.dumps(a)]), iz=None,
                     sozluk=sozluk)
    assert h.atayan == "atayici" and h.cagri_b is None and h.atama["durum"] == "atandi"
    assert h.atama["atamalar"][0]["gpio"] in range(7) and not h.yazilim_hatasi and "cagri_b" not in h.sure_sn
    yazdir(h, veri)
    cikti = capsys.readouterr().out
    assert "3) Atama (kod atayıcı):" in cikti and "Sonuç: atandı" in cikti and "Kod atayıcıyla" not in cikti


def test_mumkun_degil_nedeni_turkce(veri, sozluk, capsys):
    a = {"ihtiyaclar": [{"arayuz": "ADC", "dayanak": "Dokuz analog sensör", "adet": 9, "kaynak": "istekte_acik"}],
         "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": "tamam"}
    h = hat.calistir("Dokuz analog sensör okuyacağım.", "QFN32", BAGLAM, veri, Sahte([json.dumps(a)]), iz=None,
                     sozluk=sozluk)
    assert h.atama["durum"] == "mumkun_degil" and not h.yazilim_hatasi
    yazdir(h, veri)
    cikti = capsys.readouterr().out
    assert "karşılanamıyor" in cikti and "ADC için 9 birim gerekiyor, çipte en çok 7 kullanılabilir" in cikti


def test_pin_yetersizligi_nedeni(veri):
    istek = {"paket": "QFN32", "baglam": BAGLAM,
             "ihtiyaclar": cagrilar.kimlik_ver([{"arayuz": "ADC"}] * 7 + [{"arayuz": "WAKE"}] * 2)}
    r = Atayici(veri).ata(istek)
    assert r.neden.startswith("Toplam 9 sinyal isteniyor, bu ihtiyaçlar için uygun pin sayısı 8 (QFN32). İlk tıkanma: "
                              "9 sinyal için yalnız 8 uygun pin var (QFN32; 7 ADC, 2 WAKE). Uygun pinler: GPIO0,")


def test_pin_yetersizligi_toplam_ve_ilk_tikanma(veri):      # Adım 10b: toplam ilk tıkanmadan farklı olabilir
    istek = {"paket": "QFN40", "baglam": BAGLAM, "ihtiyaclar": cagrilar.kimlik_ver([{"arayuz": "GPIO_OUT"}] * 23)}
    r = Atayici(veri).ata(istek)
    assert r.neden.startswith("Toplam 23 sinyal isteniyor, bu ihtiyaçlar için uygun pin sayısı 19 (QFN40). İlk tıkanma: ")


def test_atayici_hatasi_yazilim_hatasi(veri, sozluk, capsys, monkeypatch):   # denetleyici atayıcıyı da denetler
    a = {"ihtiyaclar": [{"arayuz": "ADC", "dayanak": "analog", "adet": 1, "kaynak": "istekte_acik"}],
         "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": "tamam"}
    bozuk = AtamaSonucu({"durum": "atandi", "atamalar": [{"ihtiyac_id": "adc_1", "sinyal": "AIN", "gpio": 14}]})
    monkeypatch.setattr(Atayici, "ata", lambda self, istek: bozuk)
    h = hat.calistir("Bir analog sensör okuyacağım.", "QFN32", BAGLAM, veri, Sahte([json.dumps(a)]), iz=None,
                     sozluk=sozluk)
    assert [i.kod for i in h.yazilim_hatasi] == ["SABIT_PIN"]
    yazdir(h, veri)
    assert "YAZILIM HATASI" in capsys.readouterr().out


def test_kapsamli_kos_ve_rapor(veri, sozluk, tmp_path):            # Adım 8 ölçüm betiği, sahte modelle
    from pinsecim import kapsamli

    def a_yaniti(arayuz, dayanak, adet, kaynak="istekte_acik", durum="tamam"):
        return json.dumps({"ihtiyaclar": [{"arayuz": arayuz, "dayanak": dayanak, "adet": adet, "kaynak": kaynak}]
                           if arayuz else [], "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": durum})

    istekler = [
        {"id": "T1", "kategori": "temel", "cift": "c1", "paket": "QFN32", "baglam": {},
         "metin": "İki analog sensör okuyacağım.", "kabul": [{"durum": "tamam", "ihtiyaclar": ["ADC", "ADC"]}]},
        {"id": "T2", "kategori": "temel", "cift": "c1", "paket": "QFN32", "baglam": {},
         "metin": "İki analog giriş okunacak.", "kabul": [{"durum": "tamam", "ihtiyaclar": ["ADC", "ADC"]}]},
        {"id": "T3", "kategori": "sinir", "cift": None, "paket": "QFN32", "baglam": {},
         "metin": "Dokuz analog sensör okuyacağım.", "kabul": [{"durum": "tamam", "ihtiyaclar": ["ADC"] * 9}]},
        {"id": "T4", "kategori": "tercih", "cift": None, "paket": "QFN40", "baglam": {},          # Adım 9 biçimi
         "metin": "Röleyi GPIO12'ye bağla.", "beklenen_sonuc": "tercih_uygulanamadi",
         "kabul": [{"durum": "tamam", "ihtiyaclar": ["GPIO_OUT"],
                    "pin_tercihleri": [{"arayuz": "GPIO_OUT", "sinyal": None, "gpio": 12}]}]},
    ]
    set_yolu = tmp_path / "set.json"
    set_yolu.write_text(json.dumps({"varsayilan_baglam": BAGLAM, "istekler": istekler}, ensure_ascii=False))
    sha = hashlib.sha256(set_yolu.read_bytes()).hexdigest()
    hamlar = [a_yaniti("ADC", "İki analog sensör", 2),
              a_yaniti("ADC", "İki analog giriş", 1),                                   # SAYI_UYUSMAZ, gerçek yakalama
              a_yaniti("ADC", "İki analog giriş", 2),
              a_yaniti("ADC", "Dokuz analog sensör", 9),
              json.dumps(a_yanit([{"arayuz": "GPIO_OUT", "dayanak": "Röleyi", "adet": 1, "kaynak": "model_cikarimi"}],
                                 [{"arayuz": "GPIO_OUT", "sinyal": "", "gpio": 12, "dayanak": "GPIO12'ye bağla"}])),
              a_yaniti("ADC", "İki analog sensör", 2)]                                  # tekrar T1
    ham = tmp_path / "ham.jsonl"
    kapsamli.kos(set_yolu, sha, ham, tekrar=1, istemci=Sahte(hamlar))
    satirlar = [json.loads(s) for s in ham.read_text(encoding="utf-8").splitlines()]
    assert [(r["kosu"], r["id"]) for r in satirlar] == [("a_atayici", "T1"), ("a_atayici", "T2"),
                                                       ("a_atayici", "T3"), ("a_atayici", "T4"), ("tekrar", "T1")]
    assert satirlar[0]["atayan"] == "atayici" and satirlar[0]["cagri_b"] is None
    assert "Sonuç: atandı" in satirlar[0]["cli"] and "karşılanamıyor" in satirlar[2]["cli"]
    md = "\n".join(kapsamli.rapor_satirlari(set_yolu, sha, ham, ("T3",)))
    assert "| Çağrı A doğru | 4/4 |" in md and "| Uçtan uca doğru (A doğru ve karar hakemle aynı) | 4/4 |" in md
    assert "| Hakem (ilk kabul seçeneği) beklenen_sonuc ile aynı | 1/1 |" in md and "--no-usb" in md
    assert "| Çağrı A geçtiği tur (1 / 2 / 3); BILGI_YOK; KULLANICIYA; JSON_GECERSIZ | 3 / 1 / 0; 0; 0; 0 |" in md
    assert "uymuyordu (gerçek yakalama) | 0 / 1 |" in md and "| temel | 2 | 2/2 | 2/2 |" in md
    assert "Aynı: 1/1 çift." in md and "A ham aynı 1/1." in md and "### Komut satırı çıktısı: T3" in md
    assert ("| Atayıcı kararı: atandi / tercih_uygulanamadi / mumkun_degil / pin gerekmiyor / atamaya gelmedi | "
            "2 / 1 / 1 / 0 / 0 |") in md


def test_hakem_tamam_olmayan_kabul_secenegi():                    # Adım 8b: X33 hatası
    from pinsecim.dogrulama import hakem_sec
    beklenenle = [{"kabul_no": 1, "atama": {"durum": "atandi"}}]  # 0: emin_degilim (hakemsiz), 1: tamam
    assert hakem_sec(beklenenle, 0) is None                       # A emin_degilim seçeneğiyle eşleşti
    assert hakem_sec(beklenenle, 1)["kabul_no"] == 1               # A tamam seçeneğiyle eşleşti
    assert hakem_sec(beklenenle, None)["kabul_no"] == 1            # A yanlış: ilk tamam seçeneği
    assert hakem_sec([], None) is None


def test_verilen_kullaniciya():                                   # Adım 8b: X34 hatası
    from pinsecim.dogrulama import verilen_metni
    yanit = {"ihtiyaclar": [{"arayuz": "I2C", "adet": 1}, {"arayuz": "GPIO_IN", "adet": 1}], "durum": "tamam"}
    assert verilen_metni({"durum": "KULLANICIYA", "yanit": yanit}) == "KULLANICIYA (son tur: tamam [GPIO_IN I2C])"
    assert verilen_metni({"durum": "GECTI", "yanit": yanit}) == "tamam [GPIO_IN I2C]"
    assert verilen_metni({"durum": "BILGI_YOK", "yanit": {"ihtiyaclar": [], "durum": "emin_degilim"}}) == "emin_degilim [-]"
    assert verilen_metni({"durum": "JSON_GECERSIZ", "yanit": None}) == "JSON_GECERSIZ"


# ------------------------------------------------------------------ Adım 9: pin tercihleri (K-7)
@pytest.mark.parametrize("metin,beklenen", [
    ("Butonu GPIO5'e bağladım; gpio6, gpıo11, IO4 ve GPIO 7.",
     [(5, "gpio"), (6, "gpio"), (11, "gpio"), (4, "gpio"), (7, "gpio")]),
    ("Ekranı GPIO22, 23, 15 ve 14'e bağla.", [(22, "gpio"), (23, "liste_devami"), (15, "liste_devami"),
                                              (14, "liste_devami")]),
    ("GPIO8, 3 lamba da yakacağım.", [(8, "gpio")]),                           # sayıdan sonra ad: liste devamı değil
    ("Röleyi 4 numaralı pine, sensörü pin 6'ya tak.", [(4, "belirsiz"), (6, "belirsiz")]),
    ("RADIO2 modülü, ESP32-C6, UART0 ve IO MUX.", []),
])
def test_pin_bahisleri(sozluk, metin, beklenen):
    assert [(b.gpio, b.tur) for b in sozluk.pin_bahisleri(metin)] == beklenen


@pytest.mark.parametrize("metin,dayanak,beklenen", [
    ("Kapıyı GPIO3'e bağladım; bir de I2C nem ölçer var.", "bir I2C nem ölçer var", "bir de I2C nem ölçer var"),
    ("Dört adet, mavi LED yakacağım.", "dört mavi LED", "Dört adet, mavi LED"),            # noktalama yok sayılır
    ("Dört adet büyük, parlak mavi LED.", "dört mavi LED", None),                          # araya 3 sözcük: kabul yok
    ("İki fan süreceğim.", "iki büyük fan", None),                                          # dayanakta fazladan sözcük
    ("İKİ FAN SÜRECEĞİM", "iki fan", "İKİ FAN"),                                            # Türkçe küçük harf
    ("Bir röle var.", "Bir röle", "Bir röle"),                                              # birebir
    ("Lambaları GPIO2, 3 ve 9'a bağla.", "3'a", None),                                      # ek sözcüğün parçası
    ("Lambaları GPIO2 ve 9'a bağla.", "lambaları 9'a", "Lambaları GPIO2 ve 9'a"),           # araya 2 sözcük
])
def test_esnek_dayanak(metin, dayanak, beklenen):
    assert sozluk_mod.dayanak_bul(metin, dayanak) == beklenen


def a_yanit(ihtiyaclar, tercih=(), yasak=(), diger=(), durum="tamam"):
    return {"ihtiyaclar": list(ihtiyaclar), "pin_tercihleri": list(tercih), "kullanilmayacak_pinler": list(yasak),
            "diger_pin_bahisleri": list(diger), "baglam_ifadeleri": [], "desteklenmeyenler": [], "durum": durum}


def test_pin_bahsi_denetimleri(sozluk):
    metin = "Rölenin hattını GPIO4'e bağla; GPIO9 kullanılmasın. Eskiden GPIO2'deydi. Sensör 5 numaralı pinde."
    d = kapsamsiz(cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), sozluk))
    role = {"arayuz": "GPIO_OUT", "dayanak": "Rölenin hattını", "adet": 1, "kaynak": "model_cikarimi"}
    tam = a_yanit([role], [{"arayuz": "GPIO_OUT", "sinyal": "", "gpio": 4, "dayanak": "GPIO4'e bağla"}],
                  [{"gpio": 9, "dayanak": "GPIO9 kullanılmasın"}], [{"gpio": 2, "dayanak": "Eskiden GPIO2'deydi"}])
    assert sorted((i.kod, i.seviye) for i in d(tam)) == [("BELIRSIZ_PIN_BAHSI", "uyari"), ("MODEL_CIKARIMI", "uyari")]
    eksik = a_yanit([role], [{"arayuz": "GPIO_OUT", "sinyal": "", "gpio": 4, "dayanak": "GPIO4'e bağla"}])
    assert sorted(i.kod for i in d(eksik) if i.seviye == "hata") == ["PIN_BAHSI_ATLANDI", "PIN_BAHSI_ATLANDI"]
    uydurma = {**tam, "diger_pin_bahisleri": tam["diger_pin_bahisleri"] + [{"gpio": 7, "dayanak": "Eskiden"}]}
    assert [i.kod for i in d(uydurma) if i.seviye == "hata"] == ["PIN_UYDURMA"]
    belirsiz = {**tam, "pin_tercihleri": tam["pin_tercihleri"] + [{"arayuz": "GPIO_OUT", "sinyal": "", "gpio": 5,
                                                                    "dayanak": "5 numaralı pinde"}]}
    assert [i.kod for i in d(belirsiz) if i.seviye == "hata"] == ["BELIRSIZ_PIN_TERCIHI"]
    ihtiyacsiz = {**tam, "pin_tercihleri": [{"arayuz": "I2C", "sinyal": "SDA", "gpio": 4, "dayanak": "GPIO4'e bağla"}]}
    assert [i.kod for i in d(ihtiyacsiz) if i.seviye == "hata"] == ["TERCIH_IHTIYACSIZ"]


def test_esnek_dayanak_denetimde_degistirilir(sozluk):                # sayı denetimi gerçek parça üzerinden
    metin = "Dört adet, mavi LED yakacağım."
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), sozluk)
    y = a_yanit([{"arayuz": "GPIO_OUT", "dayanak": "dört mavi LED", "adet": 3, "kaynak": "model_cikarimi"}])
    kodlar = [i.kod for i in d(y)]
    assert y["ihtiyaclar"][0]["dayanak"] == "Dört adet, mavi LED"
    assert "ESNEK_DAYANAK" in kodlar and "SAYI_UYUSMAZ" in kodlar and "DAYANAK_YOK" not in kodlar


def istek_(paket, arayuzler, tercih=(), yasak=(), baglam=BAGLAM):
    return {"paket": paket, "baglam": baglam, "ihtiyaclar": cagrilar.kimlik_ver([{"arayuz": a} for a in arayuzler]),
            "pin_tercihleri": [{"arayuz": a, "sinyal": s, "gpio": g} for a, s, g in tercih],
            "kullanilmayacak": list(yasak)}


def test_atayici_tercih_uygulanir(veri):
    istek = istek_("QFN40", ["SPI", "GPIO_OUT"], [("SPI", "", g) for g in (22, 23, 18, 19)] + [("GPIO_OUT", "", 9)],
                   yasak=[0, 1])
    r = Atayici(veri).ata(istek)
    assert r.atama["durum"] == "atandi"
    a = {(x["ihtiyac_id"], x["sinyal"]): x["gpio"] for x in r.atama["atamalar"]}
    assert {a[("spi_1", s)] for s in ("SCLK", "MOSI", "MISO", "CS")} == {22, 23, 18, 19}   # sinyaller pinler içinde
    assert a[("gpio_out_1", "OUT")] == 9 and r.uyarili_pin == [9]                         # uyarılı pin: uygulanır
    assert not {0, 1} & set(a.values())
    assert [i.kod for i in Denetleyici(veri).denetle(istek, r.atama)] == ["PIN_STRAPPING"]


def test_atayici_kurala_takilan_tercih(veri):
    r = Atayici(veri).ata(istek_("QFN40", ["GPIO_OUT", "GPIO_OUT", "ADC"], [("GPIO_OUT", "", 12), ("ADC", "", 10)]))
    assert r.atama == {"durum": "tercih_uygulanamadi", "atamalar": []}
    sorun = {x["tercih"]["gpio"]: x for x in r.tercih_sorunlari}
    assert sorun[12]["kod"] == "PIN_USB" and "--no-usb" in sorun[12]["oneri"] and sorun[12]["neden"].startswith("GPIO12:")
    assert sorun[10]["kod"] == "SABIT_PIN" and "GPIO0–GPIO6" in sorun[10]["oneri"]
    assert r.alternatif["durum"] == "atandi" and 12 not in {x["gpio"] for x in r.alternatif["atamalar"]}


def test_atayici_tercih_yer_yok_ve_mumkun_degil(veri):
    r = Atayici(veri).ata(istek_("QFN32", ["ADC"] * 7 + ["GPIO_OUT"], [("GPIO_OUT", "", 3)]))
    assert r.atama["durum"] == "tercih_uygulanamadi" and r.tercih_sorunlari[0]["kod"] == "YER_YOK"
    assert "7 ADC" in r.tercih_sorunlari[0]["neden"]
    r = Atayici(veri).ata(istek_("QFN32", ["ADC"] * 8, [("ADC", "", 0)]))   # tercihten bağımsız: adet yetmez
    assert r.atama["durum"] == "mumkun_degil" and "8 birim" in r.neden and not r.tercih_sorunlari


def test_denetleyici_yasak_ve_tercih(veri):
    istek = istek_("QFN40", ["GPIO_OUT"], [("GPIO_OUT", "", 4)], yasak=[5])
    ihl = Denetleyici(veri).denetle(istek, {"durum": "atandi", "atamalar": [
        {"ihtiyac_id": "gpio_out_1", "sinyal": "OUT", "gpio": 5}]})
    assert sorted(i.kod for i in ihl if i.seviye == "hata") == ["TERCIH_UYGULANMADI", "YASAK_PIN"]
    assert any(i.mesaj_tr.startswith("GPIO5 kullanılmamalı") for i in ihl)


def test_cli_tercih_uygulanamadi(veri, sozluk, capsys):
    metin = "Dört röleyi sürmek için GPIO12'yi de kullan."
    a = a_yanit([{"arayuz": "GPIO_OUT", "dayanak": "Dört röleyi", "adet": 4, "kaynak": "model_cikarimi"}],
                [{"arayuz": "GPIO_OUT", "sinyal": "", "gpio": 12, "dayanak": "GPIO12'yi de kullan"}])
    h = hat.calistir(metin, "QFN40", BAGLAM, veri, Sahte([json.dumps(a, ensure_ascii=False)]), iz=None, sozluk=sozluk)
    assert h.atama["durum"] == "tercih_uygulanamadi" and not h.yazilim_hatasi
    yazdir(h, veri)
    cikti = capsys.readouterr().out
    assert "pin tercihi uygulanamadı" in cikti and "Öneri: USB Serial/JTAG'ı kullanmayacaksan --no-usb ver" in cikti
    assert "ALTERNATİF atama" in cikti and "GPIO12" in cikti


# ------------------------------------------------------------------ Adım 9b: aynı pine / sinyale birden çok tercih
def test_iki_ihtiyac_ayni_gpio(veri):
    r = Atayici(veri).ata(istek_("QFN40", ["GPIO_IN", "GPIO_IN"], [("GPIO_IN", "", 20), ("GPIO_IN", "", 20)]))
    assert r.atama == {"durum": "tercih_uygulanamadi", "atamalar": []}
    assert [x["kod"] for x in r.tercih_sorunlari] == ["AYNI_PIN"] and "GPIO20" in r.tercih_sorunlari[0]["neden"]
    assert r.uygulanan_tercihler == [{"arayuz": "GPIO_IN", "sinyal": "", "gpio": 20}]
    assert sorted(x["gpio"] for x in r.alternatif["atamalar"])[-1] == 20 and len(r.alternatif["atamalar"]) == 2


def test_ayni_gpio_tercih_ve_yasak(veri):
    r = Atayici(veri).ata(istek_("QFN40", ["GPIO_OUT"], [("GPIO_OUT", "", 3)], yasak=[3]))
    assert r.atama["durum"] == "tercih_uygulanamadi" and r.tercih_sorunlari[0]["kod"] == "YASAKLA_CAKISMA"
    assert 3 not in {x["gpio"] for x in r.alternatif["atamalar"]}


def test_ayni_sinyale_iki_gpio(veri):
    r = Atayici(veri).ata(istek_("QFN40", ["UART"], [("UART", "TX", 4), ("UART", "TX", 5)]))
    assert r.atama["durum"] == "tercih_uygulanamadi" and [x["kod"] for x in r.tercih_sorunlari] == ["FAZLA_TERCIH"]
    a = {x["sinyal"]: x["gpio"] for x in r.alternatif["atamalar"]}
    assert a["TX"] == 4
    r = Atayici(veri).ata(istek_("QFN40", ["SPI"], [("SPI", "", g) for g in (18, 19, 20, 21)] + [("SPI", "SCLK", 22)]))
    assert [x["kod"] for x in r.tercih_sorunlari] == ["FAZLA_TERCIH"] and "5 pin tercihi var, 4 sinyal" in \
        r.tercih_sorunlari[0]["neden"]


def test_denetleyici_ayni_pine_iki_tercih(veri):
    istek = istek_("QFN40", ["GPIO_IN", "GPIO_IN"], [("GPIO_IN", "", 20), ("GPIO_IN", "", 20)])
    ihl = Denetleyici(veri).denetle(istek, {"durum": "atandi", "atamalar": [
        {"ihtiyac_id": "gpio_in_1", "sinyal": "IN", "gpio": 20}, {"ihtiyac_id": "gpio_in_2", "sinyal": "IN", "gpio": 0}]})
    assert [i.kod for i in ihl if i.seviye == "hata"] == ["TERCIH_UYGULANMADI"]


def test_kapsamli_yeniden_ata(veri, sozluk, tmp_path):             # Adım 9b: model çalışmadan, aynı Çağrı A ile
    from pinsecim import kapsamli
    test_kapsamli_kos_ve_rapor(veri, sozluk, tmp_path)
    set_yolu, eski = tmp_path / "set.json", tmp_path / "ham.jsonl"
    sha = hashlib.sha256(set_yolu.read_bytes()).hexdigest()
    yeni = kapsamli.yeniden_ata(set_yolu, sha, eski, tmp_path / "yeni.jsonl")
    e = [json.loads(s) for s in eski.read_text(encoding="utf-8").splitlines()]
    n = [json.loads(s) for s in yeni.read_text(encoding="utf-8").splitlines()]
    assert [(r["kosu"], r["id"]) for r in e] == [(r["kosu"], r["id"]) for r in n]
    assert all(a["cagri_a"] == b["cagri_a"] for a, b in zip(e, n))
    assert [r.get("gosterilen_atama") for r in e] == [r.get("gosterilen_atama") for r in n]
    assert "yeniden_atama" in n[0] and "yeniden_atama" not in n[-1]               # tekrar satırı olduğu gibi

"""Adım 11: KAPSANMAYAN_CUMLE (hiçbir dayanakla örtüşmeyen cümle uyarısı). Cümleler v1–v5 setlerinde geçmeyenlerden."""

from __future__ import annotations

import pytest

from pinsecim import cagrilar, semalar, sozluk as sozluk_mod


@pytest.fixture(scope="module")
def s():
    return sozluk_mod.yukle()


def yanit(ihtiyaclar=(), sorular=(), baglam=(), diger=(), desteklenmeyen=(), durum="tamam", eksik=(), tercih=(),
          diger_pin=()):
    return {"ihtiyaclar": [{"arayuz": a, "dayanak": da, "adet": n, "kaynak": "model_cikarimi"} for a, da, n in ihtiyaclar],
            "pin_tercihleri": [{"arayuz": a, "sinyal": "", "gpio": g, "dayanak": da} for a, g, da in tercih],
            "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [{"gpio": g, "dayanak": da} for g, da in diger_pin],
            "sorular": [{"soru": q, "konu": k} for q, k in sorular], "baglam_ifadeleri": list(baglam),
            "diger_ifadeler": list(diger), "desteklenmeyenler": list(desteklenmeyen), "durum": durum,
            "eksik": list(eksik)}


def kapsam(s, metin, y, baglam=None):
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), s, baglam)
    return [i for i in d(y) if i.kod == "KAPSANMAYAN_CUMLE"]


def test_hicbir_listede_olmayan_cumle_uyari(s):
    metin = "Bir fan süreceğim. Kardeşim de lehim yapmayı öğreniyor."
    u = kapsam(s, metin, yanit(ihtiyaclar=[("GPIO_OUT", "Bir fan", 1)]))
    assert [i.seviye for i in u] == ["uyari"] and u[0].alan == "cumle/1"
    assert u[0].mesaj == ("«Kardeşim de lehim yapmayı öğreniyor.» hiçbir şekilde değerlendirilmedi; pin ihtiyacı "
                          "içeriyorsa ayrı ve açık bir cümleyle yaz.")


def test_diger_ifadelerdeki_cumle_uyarmaz(s):
    metin = "Bir fan süreceğim. Kardeşim de lehim yapmayı öğreniyor."
    y = yanit(ihtiyaclar=[("GPIO_OUT", "Bir fan", 1)], diger=["Kardeşim de lehim yapmayı öğreniyor."])
    assert kapsam(s, metin, y) == []


def test_dayanak_cumlenin_bir_parcasiysa_kapsanmis(s):
    metin = "Mutfaktaki aspiratörü, akşamları ve hafta sonları, bir röleyle açıp kapatacağım!"
    assert kapsam(s, metin, yanit(ihtiyaclar=[("GPIO_OUT", "bir röleyle", 1)])) == []


def test_sessiz_kaybolan_ihtiyac_cumlesi(s):
    metin = "İki nem sensörünü ADC ile okuyacağım. Ayrıca bir zil çalacak."
    u = kapsam(s, metin, yanit(ihtiyaclar=[("ADC", "İki nem sensörünü", 2)]))
    assert [i.mesaj.split("»")[0] for i in u] == ["«Ayrıca bir zil çalacak."]


def test_soru_bagalam_desteklenmeyen_kapsar(s):
    metin = ("JTAG ile hata ayıklayacağım. Kamera modülünü DVP ile bağlayacağım. "
             "GPIO10 hangi işlevlere sahip?")
    y = yanit(sorular=[("GPIO10 hangi işlevlere sahip?", "pin_islevi")], baglam=["JTAG ile hata ayıklayacağım."],
              desteklenmeyen=["Kamera modülünü DVP ile"], durum="desteklenmiyor")
    assert kapsam(s, metin, y) == []


def test_pin_listesi_dayanagi_kapsar(s):
    metin = "Bir lamba süreceğim. GPIO21'i başka işe ayırdım."
    y = yanit(ihtiyaclar=[("GPIO_OUT", "Bir lamba", 1)], diger_pin=[(21, "GPIO21'i")])
    assert kapsam(s, metin, y) == []


def test_emin_degilim_uygulanmaz(s):                              # Adım 11a: istek eksik kodlarıyla değerlendirildi
    metin = "Akvaryum için bir şey düşünüyorum. Belki sonra genişletirim."
    assert kapsam(s, metin, yanit(durum="emin_degilim", eksik=["cihaz_belirsiz"])) == []
    u = kapsam(s, metin, yanit(durum="desteklenmiyor", desteklenmeyen=["Akvaryum için"]))
    assert [i.alan for i in u] == ["cumle/1"]                      # öteki durumlarda uygulanır


def test_noktalamasiz_ve_bos_parcalar(s):
    metin = "Bir motor süreceğim...  "
    assert kapsam(s, metin, yanit(ihtiyaclar=[("PWM", "Bir motor", 1)])) == []
    metin = "Bir motor süreceğim ve sonra bakarız"
    assert kapsam(s, metin, yanit(ihtiyaclar=[("PWM", "Bir motor", 1)])) == []


def test_tur_acmaz_karar_degistirmez(s):
    metin = "Bir fan süreceğim. Kardeşim de lehim yapmayı öğreniyor."
    d = cagrilar.ihtiyac_denetleyici(metin, list(semalar.ARAYUZLER), s, None)
    ihl = d(yanit(ihtiyaclar=[("GPIO_OUT", "Bir fan", 1)]))
    assert not [i for i in ihl if i.seviye == "hata"]


def test_komut_satirinda_gorunur(monkeypatch, capsys):
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
    assert cli.main(["Bir peltier süreceğim. Komşum da merak ediyor.", "--paket", "QFN32"]) == 0
    cikti = capsys.readouterr().out
    assert "[UYARI] «Komşum da merak ediyor.» hiçbir şekilde değerlendirilmedi" in cikti
    assert "Sonuç: atandı" in cikti and "1. turda geçti" in cikti


# ------------------------------------------------------------------ tamolcum (sahte model, set dışı istekler)
def test_tamolcum_kos_ve_rapor(tmp_path):
    import hashlib
    import json

    from asu_llmcore import OllamaYaniti

    from pinsecim import tamolcum

    yanitlar = {
        "Bir korna süreceğim.": {"ihtiyaclar": [{"arayuz": "GPIO_OUT", "dayanak": "Bir korna", "adet": 1,
                                                 "kaynak": "model_cikarimi"}], "sorular": []},
        "GPIO2 hangi işlevlere sahip?": {"ihtiyaclar": [], "sorular": [{"soru": "GPIO2 hangi işlevlere sahip?",
                                                                       "konu": "pin_islevi"}]},
    }

    class Sahte:
        def uret(self, mesajlar, sema=None, sabit_onek=None):
            metin = mesajlar[-1]["content"]
            k = next(k for k in yanitlar if k in metin)
            j = {"pin_tercihleri": [], "kullanilmayacak_pinler": [], "diger_pin_bahisleri": [], "baglam_ifadeleri": [],
                 "diger_ifadeler": [], "desteklenmeyenler": [], "durum": "tamam", "eksik": [], **yanitlar[k]}
            return OllamaYaniti(ham=json.dumps(j, ensure_ascii=False), json=j, model="sahte")

    s = {"varsayilan_baglam": {"usb_serial_jtag": True, "uart0_konsol": True, "jtag_pinleri": False,
                               "harici_flash_beslemesi": False}, "tekrar": ["S2"], "istekler": [
        {"id": "S1", "kategori": "kart", "metin": "Bir korna süreceğim.", "bayraklar": "--kart SuperMini",
         "paket": None, "kart": "SuperMini", "baglam": {}, "beklenen": "-",
         "kabul": [{"durum": "tamam", "ihtiyaclar": ["GPIO_OUT"]}], "beklenen_sonuc": "atandi"},
        {"id": "S2", "kategori": "soru", "metin": "GPIO2 hangi işlevlere sahip?", "bayraklar": "--paket QFN40",
         "paket": "QFN40", "kart": None, "baglam": {}, "beklenen": "-",
         "kabul": [{"durum": "tamam", "ihtiyaclar": [], "sorular": [["pin_islevi"]]}],
         "beklenen_sonuc": "pin_gerekmiyor"}]}
    yol = tmp_path / "set.json"
    yol.write_text(json.dumps(s, ensure_ascii=False), encoding="utf-8")
    sha = hashlib.sha256(yol.read_bytes()).hexdigest()
    ham = tamolcum.kos(yol, sha, tmp_path / "ham.jsonl", istemci=Sahte())
    kayit = tamolcum.ham_oku(ham)
    assert set(kayit["a_atayici"]) == {"S1", "S2"} and set(kayit["tekrar"]) == {"S2"}
    r1 = kayit["a_atayici"]["S1"][1]
    assert r1["paket"] == "QFN32" and "Kart düzeyi: SuperMini" in r1["cli"] and tamolcum.karar(r1) == "atandi"
    r2 = kayit["a_atayici"]["S2"][1]
    assert r2["cevaplar"] and tamolcum.karar(r2) == "pin_gerekmiyor" and tamolcum.a_dogru(r2, s["istekler"][1]["kabul"])
    assert not tamolcum.a_dogru(r2, [{"durum": "tamam", "ihtiyaclar": []}])          # soru beklenmiyordu
    md = tamolcum.rapor(yol, sha, ham, tmp_path / "sonuc.md", tmp_path / "d.md", "T").read_text(encoding="utf-8")
    assert "| Çağrı A doğru (otomatik) | 2/2 |" in md and "| Karar beklenenle aynı | 2/2 |" in md
    import re
    assert re.search(r"\| Süre toplam \(sn\): ortalama / ortanca / en uzun \| [\d.]+ / [\d.]+ / [\d.]+ \|", md)   # Adım 11a
    assert "- S2: Çağrı A ham yanıtları aynı; komut satırı çıktısı (süre satırı dışında) aynı" in md

"""Komut satırı: python -m pinsecim "istek metni" (--paket QFN32|QFN40 | --kart AD) [bağlam seçenekleri] [--model-ata]

Varsayılan: model isteği anlar (Çağrı A), atamayı kod atayıcı yapar (K-6). --model-ata: atamayı Çağrı B yapar.
Gösterim sırası: ihtiyaçlar; pin seçimini etkilemeyen ifadeler (Adım 10a); sorular ve veritabanından cevapları
(kaynaklı, K-8); 'tamam' değilse neden ve ne yazılmalı (durum_mesaji); atama; uyarılar.
--rapor YOL (Adım 10c): aynı çıktı, üst bilgiyle Markdown dosyasına da yazılır.
--kart (Adım 10b–10c): paket karttan türetilir (--paket ile çelişirse hata); kart soruları o kartla cevaplanır; atama
kart düzeyindedir: yalnız kartta çıkan pinler, pin adının yanında kart etiketi ("GPIO4 (J1-4)"), kart düzeyi özet ve
doğrulanmamış kart satırı notu.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import sys
from pathlib import Path

from asu_llmcore import Durum, OllamaHatasi

from . import cagrilar, hat, kart as kart_mod, pinveri, rapor
from .atayici import pin_listesi, tercih_adi
from .denetim import turkce
from .pinveri import VeriHatasi

DURUM_TR = {"FREE": "serbest", "WARNING": "uyarı", "FORBIDDEN": "yasak"}


def secenekler(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="python -m pinsecim", description="ESP32-C6 pin ataması (yerel model isteği anlar, kod atar)")
    ap.add_argument("metin", help="Türkçe istek")
    ap.add_argument("--paket", choices=["QFN32", "QFN40"], help="çip paketi; --kart verilirse karttan türetilir")
    ap.add_argument("--kart", help="geliştirme kartı (SuperMini, nanoESP32-C6-v1.0, \"nanoESP32-C6 (v0.2)\" …)")
    ap.add_argument("--usb", dest="usb_serial_jtag", action=argparse.BooleanOptionalAction, default=True,
                    help="USB Serial/JTAG kullanılıyor (varsayılan: evet)")
    ap.add_argument("--uart0-konsol", dest="uart0_konsol", action=argparse.BooleanOptionalAction, default=True,
                    help="UART0 konsol (varsayılan: evet)")
    ap.add_argument("--jtag-pinleri", action="store_true", help="JTAG pinleri hata ayıklamada kullanılıyor")
    ap.add_argument("--harici-flash-beslemesi", action="store_true", help="flash harici besleniyor")
    ap.add_argument("--rapor", type=Path, metavar="YOL",
                    help="komut satırı çıktısının aynısını, üst bilgiyle Markdown olarak bu dosyaya da yaz")
    ap.add_argument("--model-ata", action="store_true",
                    help="atamayı model yapsın (Çağrı B); kod atayıcı kıyas için yanında koşar")
    return ap.parse_args(argv)


def mesaj_ipucu(m: dict, girinti: str) -> None:
    if m.get("ne_yazmali"):
        print(f"{girinti}Ne yazmalısın: {m['ne_yazmali']}" + (f" Örnek: «{m['ornek']}»" if m.get("ornek") else ""))


def soru_yazdir(no: int, c: dict) -> None:
    p = print
    p(f"   S{no} «{c['soru']}» — konu: {c['konu']}")
    if c.get("on_not"):                                 # Adım 11a: elektriksel değer sorusu
        p(f"      [NOT] {c['on_not']['mesaj']}")
    if c["mesaj"] is not None:
        p(f"      {c['mesaj']['mesaj']}")
        for satir in c["satirlar"]:                     # kart_eksik: pakete uyan kartlar
            p(f"      {satir}")
        mesaj_ipucu(c["mesaj"], "      ")
        return
    for satir in c["satirlar"]:
        p(f"      {satir}")
    if c.get("parametre", {}).get("kart"):
        p(f"      Doğrulanmamış satır: {len(c['dogrulanmadi'])}")
    p("      Kaynak: " + ("; ".join(c["kaynaklar"]) or "yok"))
    p("      Belirsiz işaretli satır: " + ("; ".join(c["belirsiz"]) or "yok"))
    p("      Yorum katmanı: " + ("; ".join(c["yorumlar"]) or "yok"))


def yazdir(h: hat.HatSonucu, veri: pinveri.PinVerisi) -> None:
    p = print
    p(f"İstek: {h.metin}")
    p((f"Kart: {h.kart['kisa_ad']} · " if h.kart else "") + f"Paket: {h.paket} · bağlam: "
      + ", ".join(f"{k}={'evet' if v else 'hayır'}" for k, v in h.baglam.items()))
    a = h.cagri_a
    p(f"\n1) İhtiyaçlar (model, {a.tur_sayisi}. turda {'geçti' if a.durum is Durum.GECTI else a.durum.value}):")
    if a.yanit:
        for n in a.yanit.get("ihtiyaclar", []):
            isaret = "  [model çıkarımı — kontrol edin]" if n["kaynak"] == "model_cikarimi" else ""
            p(f"   - {n['arayuz']:<9} ×{n.get('adet', 1):<2} «{n['dayanak']}»{isaret}")
        if a.durum is Durum.GECTI and not a.yanit.get("ihtiyaclar"):
            p("   - pin ihtiyacı yok")
        for t in a.yanit.get("pin_tercihleri", []):
            p(f"   - pin tercihi: {tercih_adi(t)}  «{t['dayanak']}»")
        for t in a.yanit.get("kullanilmayacak_pinler", []):
            p(f"   - kullanılmayacak: GPIO{t['gpio']}  «{t['dayanak']}»")
        for t in a.yanit.get("diger_pin_bahisleri", []):
            p(f"   - başka pin bahsi (atamaya girmez): GPIO{t['gpio']}  «{t['dayanak']}»")
        for d in a.yanit.get("baglam_ifadeleri", []):
            p(f"   - bağlam:   «{d}»")
        for d in a.yanit.get("desteklenmeyenler", []):
            p(f"   - desteklenmiyor: «{d}»")
        for i in a.uyarilar:
            if i.kod in ("BAGLAM_CELISKI", "BELIRSIZ_PIN_BAHSI", "SAYI_YARIM", "DIGER_PIN_TERCIH_IZI",
                         "KAPSANMAYAN_CUMLE", "SPI_ADET_IZI"):
                p(f"   [UYARI] {i.mesaj}")
            elif i.kod == "ESNEK_DAYANAK":
                p(f"   [dayanak metindeki parçayla eşlendi] {i.mesaj}")
        if a.yanit.get("diger_ifadeler"):
            izler = {i.alan: i for i in a.uyarilar if i.kod == "DIGER_IHTIYAC_IZI"}
            p("\n   Pin seçimini etkilemeyen ifadeler (ihtiyaç olarak alınmadı):")
            for no, d in enumerate(a.yanit["diger_ifadeler"]):
                p(f"   - «{d}»")
                if f"diger_ifadeler/{no}" in izler:
                    p(f"     [UYARI] {izler[f'diger_ifadeler/{no}'].mesaj}")
    if h.cevaplar:
        p("\n2) Sorular (cevaplar veritabanından; model cevap yazmaz):")
        for no, c in enumerate(h.cevaplar, 1):
            soru_yazdir(no, c)
    if h.bildirim is not None:
        b = h.bildirim
        p(f"\nAtama yapılmadı: {b['durum']['mesaj']}")
        for e in b["eksik"]:
            p(f"   - {e['mesaj']}")
            mesaj_ipucu(e, "     ")
        if not b["eksik"]:
            mesaj_ipucu(b["durum"], "   ")
        for t in (a.turlar[-1:] if a.durum is not Durum.GECTI else []):
            for i in t.ihlaller:
                p(f"   [{i.kod}] {i.mesaj}")
        p(f"\nSüre: {h.sure_sn['toplam']} sn")
        return
    if h.pin_gerekmiyor:
        p("\n3) Atama: " + ("istekte pin ihtiyacı yok; yalnız sorular cevaplandı." if h.cevaplar
                           else "bu istek için pin ataması gerekmiyor."))
        p(f"\nSüre: {h.sure_sn['toplam']} sn")
        return

    durumlar = cagrilar.gpio_durumlari(veri, h.paket, h.baglam)
    p(f"\n3) Atama ({'kod atayıcı' if h.atayan == 'atayici' else 'model'}):")
    kart = (h.istek or {}).get("kart")
    etiket = {x["gpio"]: x["etiket"] for x in kart["pinler"]} if kart else {}
    ozet = (h.atayici or {}).get("kart_ozeti")
    if ozet:
        p(f"   Kart düzeyi: {ozet['kart']}; adaylar karta çıkan pinler ({ozet['konnektor']} konnektör pini"
          + (f", {ozet['ped']} ped" if ozet["ped"] else "") + "). Ped: "
          + (pin_listesi(ozet["kullanilan_ped"]) if ozet["kullanilan_ped"] else "kullanılmadı")
          + "; kart üstü parça pini: " + (pin_listesi(ozet["kullanilan_parca"]) if ozet["kullanilan_parca"]
                                         else "kullanılmadı") + ".")
    if h.atayan == "model":
        b = h.cagri_b
        sonuc = {Durum.GECTI: f"{b.gecti_turu}. turda denetimden geçti", Durum.BILGI_YOK: "model bilgi yok dedi",
                 Durum.KULLANICIYA: f"{b.tur_sayisi} turda denetimden geçmedi, karar size kaldı",
                 Durum.JSON_GECERSIZ: f"{b.tur_sayisi} turda şemaya uyan yanıt verilemedi"}[b.durum]
        p(f"   Sonuç: {sonuc}; durum = {h.atama.get('durum') if h.atama else '-'}")
        if h.atama and h.atama.get("gerekce"):
            p(f"   Gerekçe: {h.atama['gerekce']}")
    elif h.atama["durum"] == "atandi":
        p("   Sonuç: atandı" + (" (pin tercihleri uygulandı)" if h.istek["pin_tercihleri"] else ""))
    elif h.atama["durum"] == "tercih_uygulanamadi":
        p("   Sonuç: pin tercihi uygulanamadı; tercih başka pine taşınmadı.")
        for x in h.atayici["tercih_sorunlari"]:
            p(f"   - {tercih_adi(x['tercih'])}: {x['neden']}")
            p(f"     Öneri: {x['oneri']}")
    else:
        p("   Sonuç: bu istek bu pakette ve bu bağlamda karşılanamıyor.")
        p(f"   Neden: {h.atayici['neden']}")
    if h.istek.get("kullanilmayacak"):
        p("   Kullanılmayacak pinler atamaya girmedi: " + ", ".join(f"GPIO{g}" for g in h.istek["kullanilmayacak"]))
    tercihli = {t["gpio"] for t in (h.atayici or {}).get("uygulanan_tercihler", [])} if h.atayan == "atayici" else set()

    def tablo(atamalar):
        p(f"   {'İhtiyaç':<12} {'Sinyal':<6} {'GPIO':<{14 if kart else 7}} Pinin durumu")
        for x in atamalar:
            durum, ihl = durumlar.get(x["gpio"], ("?", []))
            ek = f" ({', '.join(i.kod for i in ihl)})" if ihl else ""
            isaret = "  [tercih]" if x["gpio"] in tercihli else ""
            pin = f"GPIO{x['gpio']}" + (f" ({etiket[x['gpio']]})" if x["gpio"] in etiket else "")
            p(f"   {x['ihtiyac_id']:<12} {x['sinyal']:<6} {pin:<{14 if kart else 7}} {DURUM_TR.get(durum, durum)}{ek}"
              f"{isaret}")
        arayuz_ids: dict[str, list[str]] = {}
        for n in h.istek["ihtiyaclar"]:
            arayuz_ids.setdefault(n["arayuz"], []).append(n["id"])
        for a, ids in arayuz_ids.items():                # L-1: ortak hat
            secim = veri.arayuzler[a].get("ortak_hat_secim")
            if secim == pinveri.ADRES and len(ids) > 1:     # I2C ×N (Adım 11a)
                p(f"   {a} ortak hat: {', '.join(ids[1:])} ayrı pin almaz; {', '.join(veri.arayuzler[a]['sinyaller'])} "
                  f"{ids[0]} ile ortak (cihazlar adresle ayrılır).")
            elif secim and len(ids) > 1:
                ortaklar = ", ".join(x for x in veri.arayuzler[a]["sinyaller"] if x != secim)
                p(f"   {a} ortak hat: {', '.join(ids[1:])} yalnız {secim} alır; {ortaklar} {ids[0]} ile ortak.")
        if kart:
            kullanilan = {x["gpio"] for x in atamalar}
            dogrulanmadi = [f"{x['etiket']} (GPIO{x['gpio']})" for x in kart["pinler"]
                            if x["gpio"] in kullanilan and x["durum"] == "dogrulanmadi"]
            dogrulanmadi += [f"{x['ad']} {x['aciklama']}" for x in kart["parcalar"]
                             if x["gpio"] in kullanilan and x["durum"] == "dogrulanmadi"]
            if kart["durum"] == "dogrulanmadi" or dogrulanmadi:
                p("   Not: kart verisi doğrulanmadı: " + "; ".join(
                    (["kart satırı (" + kart["kaynak"] + ")"] if kart["durum"] == "dogrulanmadi" else [])
                    + ([", ".join(dogrulanmadi)] if dogrulanmadi else [])) + ".")

    ihlaller = h.ihlaller
    if h.atama and h.atama.get("atamalar"):
        tablo(h.atama["atamalar"])
    elif h.atayan == "atayici" and h.atayici.get("alternatif"):
        p("\n   ALTERNATİF atama (uygulanamayan tercihler olmadan; isteğiniz bu değil):")
        tablo(h.atayici["alternatif"]["atamalar"])
        ihlaller = h.alternatif_ihlaller
    hatalar = [i for i in ihlaller if i.seviye == "hata"]
    uyarilar = [i for i in ihlaller if i.seviye == "uyari"]
    if h.yazilim_hatasi:
        p("\nYAZILIM HATASI: denetleyici kod atayıcının atamasında hata buldu (olmamalı). Bu atamayı kullanmayın:")
        for i in h.yazilim_hatasi:
            p(f"   [{i.kod}] {turkce(i)}")
    elif hatalar:
        p("\nKalan hatalar:")
        for i in hatalar:
            p(f"   [{i.kod}] {turkce(i)}")
    p("\n4) Uyarılar (kaynak köşeli parantezde):" if uyarilar else "\n4) Uyarı yok.")
    for i in uyarilar:
        p(f"   [{i.kod}] {turkce(i)}")
    if h.atayan == "model" and h.atayici:
        r = h.atayici
        kiyas = "aynı" if (r["atama"]["durum"] == "atandi") == (h.atama.get("durum") == "atandi") else "FARKLI"
        p(f"\nKod atayıcıyla mümkün/imkânsız kararı: {kiyas} (atayıcı: {r['atama']['durum']}"
          + (f"; {r['neden']}" if r["neden"] else "") + ")")
    p(f"\nSüre: {h.sure_sn['toplam']} sn (" + ", ".join(f"{k} {v}" for k, v in h.sure_sn.items() if k != "toplam") + ")")


def main(argv: list[str] | None = None) -> int:
    a = secenekler(argv)
    baglam = {"usb_serial_jtag": a.usb_serial_jtag, "uart0_konsol": a.uart0_konsol, "jtag_pinleri": a.jtag_pinleri,
              "harici_flash_beslemesi": a.harici_flash_beslemesi}
    try:
        kart, kartlar, paket = None, None, a.paket
        if a.kart:
            kartlar = kart_mod.yukle()
            kart = kartlar.bul(a.kart)
            if paket is not None and paket != kart["paket"]:
                raise kart_mod.KartHatasi(f"--paket {paket} ile --kart {kart['kisa_ad']} çelişiyor: kartın çipi "
                                          f"{kart['cip']} ({kart['paket']})")
            paket = kart["paket"]
        elif paket is None:
            raise kart_mod.KartHatasi("--paket ya da --kart gerekli")
        veri = pinveri.yukle()
        h = hat.calistir(a.metin, paket, baglam, veri, model_ata=a.model_ata, kart=kart, kartlar=kartlar)
    except (VeriHatasi, OllamaHatasi) as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1
    if a.rapor is None:
        yazdir(h, veri)
        return 0
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        yazdir(h, veri)
    print(tampon.getvalue(), end="")                     # komut satırı çıktısı aynı
    rapor.yaz(a.rapor, h, tampon.getvalue())
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Çıkarma A'nın sonuçlarından veritabanı satırları (tablo → satır sözlükleri).

Paket ve kaynak kimlikleri burada ad olarak tutulur ("paket": "QFN40"); yükleyici kimliğe çevirir.
"""

from __future__ import annotations

import re

from .karsilastir import Fark, a_gorunumu
from .kararlar import AILE, FARK_KARARLARI

GPIO = re.compile(r"^GPIO(\d+)$")

# Tablo dipnotları (Table 2-1/2-2, s. 18), kendi sözümüzle.
PIN_DIPNOTLARI = {
    "5": "Dipnot 5: EFUSE_DIS_PAD_JTAG=0 (varsayılan) ise IE ve WPU; =1 ise yalnız IE.",
    "6": "Dipnot 6: çıkış etkin.",
}
USB_PU_NOTU = ("Dipnot 4: varsayılan olarak USB işlevi etkin, pull-up USB pull-up direnciyle belirlenir. USB işlevi "
               "kapatılırsa pin sıradan GPIO olur; GPIO13'ün dahili zayıf pull-up'ı resette kapalı, resetten sonra açıktır.")

# 2.3.5 (s. 25) listesindeki açıklama → kısıt türü
LISTE_TURU = {
    "Strapping pins.": "strapping",
    "USB Serial/JTAG interface.": "usb_serial_jtag",
    "JTAG interface.": "jtag",
    "UART0 interface.": "uart0",
}
KISIT_ACIKLAMA = {
    "usb_serial_jtag": "Varsayılan olarak USB Serial/JTAG denetleyicisine bağlı (USB_D-/USB_D+); GPIO olarak "
                       "kullanmak için yeniden yapılandırılmalı.",
    "jtag": "JTAG arayüzü (hata ayıklamada sık kullanılır). Bu pinleri boşaltmak için USB Serial/JTAG kullanılabilir.",
    "uart0": "UART0 arayüzü (hata ayıklamada sık kullanılır).",
    "vdd_spi": "VDD_SPI pini: varsayılan olarak paket dışı flash'ın besleme pini; yalnız flash harici beslenirse "
               "GPIO olarak yeniden yapılandırılabilir.",
    "flash": "SPI0/1 arayüzü; paket dışı flash için önerilir. Flash'a bağlı pinler başka amaçla kullanılmamalı (2.6).",
}
# Bölüm 3 girişi (s. 33): strapping pinlerinin denetlediği önyükleme parametreleri
STRAPPING_ROLLERI = {
    "GPIO8": "Önyükleme modu (GPIO9 ile) ve UART0 ROM mesajı yazdırma (EFUSE_UART_PRINT_CONTROL ile).",
    "GPIO9": "Önyükleme modu (GPIO8 ile).",
    "MTMS": "SDIO örnekleme ve sürme saat kenarı (MTDI ile).",
    "MTDI": "SDIO örnekleme ve sürme saat kenarı (MTMS ile).",
    "GPIO15": "JTAG sinyal kaynağı (eFuse ile birlikte). Dahili pull direnci yok; değer, yüksek empedansta "
              "kalmayan harici devreyle belirlenmeli (3.4, s. 36).",
}


def _kaynak(r: dict) -> dict:
    return {"sayfa": r["sayfa"], "referans": r["referans"]}


def satirlar(a: dict, farklar: list[Fark]) -> dict[str, list[dict]]:
    karar = {f.anahtar: FARK_KARARLARI[f.anahtar] for f in farklar}
    gorunum = a_gorunumu(a)
    t: dict[str, list[dict]] = {k: [] for k in ("paket", "cip", "pin", "gpio_islev", "cevre_birim_sinyal",
                                                "gpio_kisit", "strapping_kombinasyon", "flash_pin")}

    # paket ve çip (Table 1-1)
    for c in a["cipler"]:
        if c["paket"] not in {p["ad"] for p in t["paket"]}:
            t["paket"].append({"aile": AILE, "ad": c["paket"], "boyut": c["paket_boyut"], **_kaynak(c)})
        t["cip"].append({"ad": c["ad"], "aile": AILE, "paket": c["paket"], "gomulu_flash": c["gomulu_flash"],
                         "sicaklik": c["sicaklik"], "revizyon": c["revizyon"],
                         "dipnot": f"Table 1-1 dipnot {c['dipnot_flash']}" if c["dipnot_flash"] else None, **_kaynak(c)})

    # pin (Table 2-1 / 2-2), GPIO no Table 2-4 / 2-5'ten
    for paket, satir in a["pin_overview"].items():
        gpio = {r["pin_no"]: r["gpio_no"] for r in a["iomux"][paket]}
        for s in satir:
            notlar = [PIN_DIPNOTLARI[d] for d in s["dipnot"].split(",") if d in PIN_DIPNOTLARI]
            if "USB_PU" in s["reset_ayar"] + s["reset_sonrasi_ayar"]:
                notlar.append(USB_PU_NOTU)
            g = gpio.get(s["pin_no"])
            t["pin"].append({
                "paket": paket, "pin_no": s["pin_no"], "pin_adi": s["pin_adi"], "pin_turu": s["pin_turu"],
                "gpio_no": g, "guc": s["guc"] or None, "reset_ayar": s["reset_ayar"] or None,
                "reset_sonrasi_ayar": s["reset_sonrasi_ayar"] or None, "islev_kumeleri": s["islev_kumeleri"],
                "varsayilan_kume": s["varsayilan_kume"],
                "varsayilan_surme_ma": None if g is None else (40 if g in (12, 13) else 20),
                "dipnot": " ".join(notlar) or None, **_kaynak(s)})

    # gpio_islev: IO MUX (pakete göre)
    for paket, satir in a["iomux"].items():
        for r in satir:
            for f in r["islevler"]:
                t["gpio_islev"].append({"aile": AILE, "gpio_no": r["gpio_no"], "paket": paket, "grup": "IO_MUX",
                                        "islev_no": f["no"], "islev_adi": f["ad"], "tip": f["tip"],
                                        "varsayilan": f["kalin"], "tablo_adi": r["gpio_adi"], **_kaynak(r)})
    # LP IO MUX: tablo yalnız pin no veriyor (6–13); GPIO no, pin no üzerinden Table 2-4'ten (iki pakette aynı).
    gpio40 = {r["pin_no"]: r["gpio_no"] for r in a["iomux"]["QFN40"]}
    gpio32 = {r["pin_no"]: r["gpio_no"] for r in a["iomux"]["QFN32"]}
    for r in a["lp_iomux"]:
        g = gpio40[r["pin_no"]]
        ayni = gpio32.get(r["pin_no"]) == g
        for f in r["islevler"]:
            t["gpio_islev"].append({
                "aile": AILE, "gpio_no": g, "paket": None, "grup": "LP_IO_MUX", "islev_no": f["no"],
                "islev_adi": f["ad"], "tip": None, "varsayilan": f["kalin"], "tablo_adi": r["lp_adi"],
                "belirsiz": not ayni,
                "not": f"GPIO no, pin {r['pin_no']} üzerinden Table 2-4/2-5'ten" + ("" if ayni else "; paketlerde farklı"),
                **_kaynak(r)})
    for r in a["analog"]:
        for f in r["islevler"]:
            t["gpio_islev"].append({"aile": AILE, "gpio_no": r["gpio_no"], "paket": None, "grup": "ANALOG",
                                    "islev_no": f["no"], "islev_adi": f["ad"], "tip": None, "varsayilan": f["kalin"],
                                    "tablo_adi": r["gpio_adi"],
                                    "not": "QFN32'de pin yok ('—')" if r["pin_no"]["QFN32"] is None else None,
                                    **_kaynak(r)})

    # çevre birimi (Table 2-10 / 2-11)
    for paket, hucreler in a["cevre_birim"].items():
        for h in hucreler:
            pin = gorunum[paket][h["pin_no"]]
            m = GPIO.match(h["deger"])
            fark = karar.get(f"A-ic|{paket}|{h['pin_no']}|cevre:{h['cevre_birim']}:gpio")
            if m:
                yon, sinyal, g = "GPIO_MATRISI", None, int(m[1])
            else:
                sinyal, g = h["deger"], pin["gpio_no"]
                if h["deger"] in (pin["iomux_0"], pin["iomux_1"], pin["iomux_2"]):
                    yon = "IO_MUX_SABIT"
                elif h["deger"] in (pin["lp_0"], pin["lp_1"]):
                    yon = "LP_IO_MUX_SABIT"
                elif h["deger"] in (pin["analog_0"], pin["analog_1"]):
                    yon = "ANALOG_SABIT"
                else:
                    raise ValueError(f"P1 sinyali pinin işlevlerinde yok: {paket} {h}")
            t["cevre_birim_sinyal"].append({
                "paket": paket, "pin_no": h["pin_no"], "cevre_birim": h["cevre_birim"], "hucre": h["hucre"],
                "sinyal": sinyal, "gpio_no": g, "oncelik": h["oncelik"], "yonlendirme": yon,
                "belirsiz": bool(fark and fark["belirsiz"]), "not": fark["not"] if fark else None, **_kaynak(h)})

    # gpio_kisit
    paket_gpio = {p: {r["gpio_no"] for r in s} for p, s in a["iomux"].items()}
    f0_adi = {f["ad"]: r["gpio_no"] for r in a["iomux"]["QFN40"] for f in r["islevler"] if f["no"] == 0}
    oncelik = {}
    for r in a["oncelik_listeleri"]:
        oncelik.setdefault(r["gpio_no"], set()).add(r["oncelik"])
    for r in a["strapping"]:      # Table 3-1; MTMS/MTDI → GPIO4/5 (Table 2-4 F0)
        g = int(GPIO.match(r["pin_adi"])[1]) if GPIO.match(r["pin_adi"]) else f0_adi[r["pin_adi"]]
        varsayilan = r["varsayilan"] + ("" if r["bit"] in ("–", "-") else f" (bit değeri {r['bit']})")
        aciklama = f"Strapping pini ({r['pin_adi']}). {STRAPPING_ROLLERI[r['pin_adi']]}"
        if r["pin_adi"] in ("GPIO8", "GPIO9"):
            aciklama += " GPIO8=0 ve GPIO9=0 birlikte geçersiz kombinasyon (Table 3-3)."
        t["gpio_kisit"].append({"aile": AILE, "gpio_no": g, "paket": None, "kisit_turu": "strapping",
                                "oncelik": "P3" if "P3" in oncelik.get(g, ()) else None, "aciklama": aciklama,
                                "varsayilan_durum": varsayilan,
                                "not": "Önceliği 2.3.5 (s. 25) listesinden.", **_kaynak(r)})
    for r in a["oncelik_listeleri"]:   # 2.3.5 (s. 25)
        tur = LISTE_TURU.get(r["aciklama"])
        if tur == "strapping":
            continue                   # Table 3-1 satırı yukarıda (varsayılan durumla birlikte)
        if tur is None:
            tur = "vdd_spi" if "VDD_SPI" in r["aciklama"] else "flash" if "SPI0/1" in r["aciklama"] else None
        if tur is None:
            raise ValueError(f"2.3.5 listesinde bilinmeyen kalem: {r}")
        t["gpio_kisit"].append({"aile": AILE, "gpio_no": r["gpio_no"], "paket": None, "kisit_turu": tur,
                                "oncelik": r["oncelik"], "aciklama": KISIT_ACIKLAMA[tur], "varsayilan_durum": None,
                                "not": "Kategori açıklaması 2.3.4 (s. 24).", **_kaynak(r)})
    tum = paket_gpio["QFN40"] | paket_gpio["QFN32"]
    for paket, ref, sayfa in (("QFN40", "Table 2-4", 20), ("QFN32", "Table 2-5", 21)):
        for g in sorted(tum - paket_gpio[paket]):
            t["gpio_kisit"].append({
                "aile": AILE, "gpio_no": g, "paket": paket, "kisit_turu": "bu_pakette_yok", "oncelik": None,
                "aciklama": f"GPIO{g} {paket} paketinin IO MUX tablosunda yok; bu pakette pini yok.",
                "varsayilan_durum": None,
                "not": "Diğer paketin tablosunda var." + (" QFN32'de paket içi flash pinleri dışarı çıkarılmıyor "
                                                         "(2.6 s. 32; Table 2-11 dipnot 3)." if paket == "QFN32" and g >= 24 else ""),
                "sayfa": sayfa, "referans": ref})

    # strapping kombinasyonu (Table 3-3)
    for r in a["boot_modu"]:
        t["strapping_kombinasyon"].append({"aile": AILE, "islev": "boot_modu", "sonuc": r["mod"],
                                           "pin_degerleri": {"GPIO8": r["GPIO8"], "GPIO9": r["GPIO9"]},
                                           "varsayilan": r["varsayilan"],
                                           "dipnot": f"Table 3-3 dipnot {r['dipnot']}" if r["dipnot"] else None,
                                           **_kaynak(r)})
    # flash (Table 2-16)
    gpio = {r["pin_no"]: r["gpio_no"] for r in a["iomux"]["QFN40"]}
    for r in a["flash"]:
        t["flash_pin"].append({"paket": r["paket"], "pin_no": r["pin_no"], "pin_adi": r["pin_adi"],
                               "gpio_no": gpio.get(r["pin_no"]), "tek_spi": r["tek_spi"] or None,
                               "cift_spi": r["cift_spi"] or None, "dortlu_spi": r["dortlu_spi"] or None, **_kaynak(r)})
    return t

"""Pilot sözlüğü ve istek/atama JSON şemaları.

Arayüz adları ve sinyal listeleri pilotun tanımıdır (Web AI, 2026-11-20); çipe özgü bilgi (yönlendirme,
adet, sabit pin) burada değil, veritabanında datasheet kaynağıyla durur (`arayuz_tanimi`, `arayuz_sinyal`,
`cevre_adet`). Model şeması Adım 4'te `atama_semasi` üstüne kurulacak.
"""

from __future__ import annotations

PILOT_KAYNAGI = "pilot tanımı (Web AI), 2026-11-20"

# arayüz → sinyaller (sıra anlamlı: atamada bu sırayla beklenir)
ARAYUZLER: dict[str, list[str]] = {
    "GPIO_OUT": ["OUT"],
    "GPIO_IN": ["IN"],
    "UART": ["TX", "RX"],
    "I2C": ["SDA", "SCL"],
    "SPI": ["SCLK", "MOSI", "MISO", "CS"],
    "ADC": ["AIN"],
    "PWM": ["OUT"],
    "I2S_OUT": ["BCLK", "WS", "DOUT"],
    "I2S_IN": ["BCLK", "WS", "DIN"],
    "TWAI": ["TX", "RX"],
    "WAKE": ["IN"],
    "LP_I2C": ["SDA", "SCL"],
    "LP_UART": ["TX", "RX"],
    "RMT_TX": ["OUT"],                # Adım 10c (L-5): WS2812, IR verici
    "RMT_RX": ["IN"],                 # Adım 10c (L-5): IR alıcı
}

# Bağlam anahtarları: kartın/uygulamanın hangi önemli işlevleri kullandığı.
BAGLAM_ANAHTARLARI = ["usb_serial_jtag", "uart0_konsol", "jtag_pinleri", "harici_flash_beslemesi"]
DURUMLAR = ["atandi", "mumkun_degil", "bilgi_yok"]


def istek_semasi(paketler: list[str] | None = None) -> dict:
    paket = {"type": "string"} if paketler is None else {"type": "string", "enum": list(paketler)}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "paket": paket,
            "baglam": {
                "type": "object",
                "properties": {k: {"type": "boolean"} for k in BAGLAM_ANAHTARLARI},
                "required": list(BAGLAM_ANAHTARLARI),
                "additionalProperties": False,
            },
            "ihtiyaclar": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "minLength": 1},
                        "arayuz": {"type": "string", "enum": list(ARAYUZLER)},
                    },
                    "required": ["id", "arayuz"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["paket", "baglam", "ihtiyaclar"],
        "additionalProperties": False,
    }


def atama_semasi() -> dict:
    """Atama biçimi. Sinyal adı ve GPIO serbest bırakılır: sözlük dışı ad (BILINMEYEN) ve çipte olmayan
    GPIO (GECERSIZ_GPIO) şema hatası değil, denetleyicinin gerekçeli ihlalidir."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "durum": {"type": "string", "enum": list(DURUMLAR)},
            "atamalar": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ihtiyac_id": {"type": "string"},
                        "sinyal": {"type": "string"},
                        "gpio": {"type": "integer"},
                    },
                    "required": ["ihtiyac_id", "sinyal", "gpio"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["durum", "atamalar"],
        "additionalProperties": False,
    }


# --- Model şemaları (Adım 4) ---
IHTIYAC_DURUMLARI = ["tamam", "desteklenmiyor", "emin_degilim"]
PIN_LISTELERI = ["pin_tercihleri", "kullanilmayacak_pinler", "diger_pin_bahisleri"]
KAYNAK_TURLERI = ["istekte_acik", "model_cikarimi"]


def _pin_bahsi(ek: dict | None = None) -> dict:
    ozellik = {**(ek or {}), "gpio": {"type": "integer", "minimum": 0}, "dayanak": {"type": "string", "minLength": 1}}
    return {"type": "array", "items": {"type": "object", "properties": ozellik, "required": list(ozellik),
                                       "additionalProperties": False}}


def ihtiyac_semasi(arayuzler: list[str], konular: list[str], eksikler: list[str]) -> dict:
    """Çağrı A çıktısı. Alan sırası üretim sırasıdır: ihtiyaçlar, pin tercihleri, kullanılmayacak pinler, diğer pin
    bahisleri, sorular, bağlam ifadeleri, diğer ifadeler, desteklenmeyenler, durum, en son eksik. Her ihtiyaç bir arayüz
    ve adet (kaç örnek); kod adet kadar çoğaltıp kimlik verir. Pin tercihinde sinyal "" = belirtilmemiş (K-7). Soru:
    istekten birebir metin ve kapalı listeden konu; cevabı kod verir (K-8). diger_ifadeler: pin seçimini etkilemeyen
    cümleler, istekten birebir (Adım 10a). eksik: emin_degilim'in kapalı listeli neden kodları."""
    sinyaller = sorted({s for a in arayuzler for s in ARAYUZLER[a]})
    return {
        "type": "object",
        "properties": {
            "ihtiyaclar": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "arayuz": {"type": "string", "enum": list(arayuzler)},
                        "dayanak": {"type": "string", "minLength": 1},
                        "adet": {"type": "integer", "minimum": 1},
                        "kaynak": {"type": "string", "enum": list(KAYNAK_TURLERI)},
                    },
                    "required": ["arayuz", "dayanak", "adet", "kaynak"],
                    "additionalProperties": False,
                },
            },
            "pin_tercihleri": _pin_bahsi({"arayuz": {"type": "string", "enum": list(arayuzler)},
                                          "sinyal": {"type": "string", "enum": ["", *sinyaller]}}),
            "kullanilmayacak_pinler": _pin_bahsi(),
            "diger_pin_bahisleri": _pin_bahsi(),
            "sorular": {"type": "array", "items": {
                "type": "object",
                "properties": {"soru": {"type": "string", "minLength": 1},
                               "konu": {"type": "string", "enum": list(konular)}},
                "required": ["soru", "konu"], "additionalProperties": False}},
            "baglam_ifadeleri": {"type": "array", "items": {"type": "string", "minLength": 1}},
            "diger_ifadeler": {"type": "array", "items": {"type": "string", "minLength": 1}},
            "desteklenmeyenler": {"type": "array", "items": {"type": "string", "minLength": 1}},
            "durum": {"type": "string", "enum": list(IHTIYAC_DURUMLARI)},
            "eksik": {"type": "array", "items": {"type": "string", "enum": list(eksikler)}},
        },
        "required": ["ihtiyaclar", *PIN_LISTELERI, "sorular", "baglam_ifadeleri", "diger_ifadeler", "desteklenmeyenler",
                     "durum", "eksik"],
        "additionalProperties": False,
    }


def model_atama_semasi(ihtiyac_idleri: list[str], sinyaller: list[str], gpiolar: list[int]) -> dict:
    """Çağrı B çıktısı: Adım 3 atama şeması + gerekçe; kimlik, sinyal ve GPIO bu isteğe göre daraltılır."""
    sema = atama_semasi()
    sema.pop("$schema")
    oge = sema["properties"]["atamalar"]["items"]["properties"]
    oge["ihtiyac_id"] = {"type": "string", "enum": list(ihtiyac_idleri)}
    oge["sinyal"] = {"type": "string", "enum": list(sinyaller)}
    oge["gpio"] = {"type": "integer", "enum": list(gpiolar)}
    return {
        "type": "object",
        "properties": {"gerekce": {"type": "string", "minLength": 1}, **sema["properties"]},
        "required": ["gerekce", *sema["required"]],
        "additionalProperties": False,
    }

"""Adım 2: şema, A–B tutarlılığı, kaynak alanları, yükleyicinin tekrar çalıştırılabilirliği, belgeye dayalı sayımlar."""

import re
from pathlib import Path

import psycopg
import pytest

from pinsecim import cikar_a, cikar_b, karsilastir, yukle
from pinsecim import baglanti
from pinsecim.kararlar import FARK_KARARLARI, KAYNAK
from pinsecim.pdfoku import sayfa_metni

KOK = Path(__file__).resolve().parents[1]
PDF = KOK / KAYNAK["dosya_yolu"]
RAPOR = KOK / "doc" / "dogrulama" / "2026-11-20_fark_raporu.md"
OKUR = baglanti.dsn("donanim_okur")
TABLOLAR = {"kaynak", "ham_metin", "paket", "cip", "pin", "gpio_islev", "cevre_birim_sinyal", "gpio_kisit",
            "strapping_kombinasyon", "flash_pin", "dogrulama"}
OLGU_TABLOLARI = TABLOLAR - {"kaynak"}


@pytest.fixture(scope="module")
def a():
    return cikar_a.hepsi(PDF)


@pytest.fixture(scope="module")
def b():
    return cikar_b.hepsi(PDF)


@pytest.fixture(scope="module")
def db():
    with psycopg.connect(OKUR) as baglanti:
        baglanti.read_only = True
        yield baglanti


def test_sema_kurulu(db):
    tablolar = {r[0] for r in db.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")}
    assert TABLOLAR <= tablolar
    sahip = {r[0] for r in db.execute("SELECT tableowner FROM pg_tables WHERE schemaname = 'public'")}
    assert sahip == {"donanim"}


def test_okur_okuyabilir_yazamaz(db):
    for t in TABLOLAR:
        sel, ins = db.execute("SELECT has_table_privilege('donanim_okur', %s, 'SELECT'), "
                              "has_table_privilege('donanim_okur', %s, 'INSERT')", (t, t)).fetchone()
        assert sel and not ins, t


def test_a_b_farklari_karara_bagli(a, b):
    farklar = karsilastir.a_b_farklari(a, b) + karsilastir.a_ic_farklari(a) + karsilastir.renk_metin_farklari(a)
    rapor = RAPOR.read_text(encoding="utf-8")
    for f in farklar:
        assert f.anahtar in FARK_KARARLARI, f
        assert f.anahtar in rapor, f"fark raporunda yok: {f.anahtar}"
    assert set(FARK_KARARLARI) == {f.anahtar for f in farklar}, "kullanılmayan karar kalmasın"


def test_karsilastirma_bos_degil(a, b):
    """Karşılaştırma gerçekten alanlara bakıyor: B'de tek bir hücreyi bozunca fark çıkmalı."""
    ortak = karsilastir.a_gorunumu(a)["QFN40"][10]
    assert ortak["iomux_0"] == "MTMS" and ortak["lp_1"] == "LP_UART_RXD" and ortak["analog_1"] == "ADC1_CH4"
    bozuk = {p: [dict(r) for r in rs] for p, rs in b.items()}
    bozuk["QFN32"][13]["iomux_2"] = "FSPIXX"          # pin 14 (GPIO8): F2 boş olmalı
    bozuk["QFN40"][9]["satir_renk"] = None             # pin 10 (MTMS): sarı satır
    farklar = {(f.paket, f.pin_no, f.alan) for f in karsilastir.a_b_farklari(a, bozuk)}
    assert farklar == {("QFN32", 14, "iomux_2"), ("QFN40", 10, "renk")}


def test_her_olgu_satirinda_kaynak_ve_sayfa(db):
    for t in OLGU_TABLOLARI:
        bos = db.execute(f"SELECT count(*) FROM {t} WHERE kaynak_id IS NULL OR sayfa IS NULL OR sayfa < 1").fetchone()[0]
        assert bos == 0, t
        if t not in ("ham_metin",):
            ref = db.execute(f"SELECT count(*) FROM {t} WHERE coalesce(referans, '') = ''").fetchone()[0]
            assert ref == 0, t
    assert db.execute("SELECT count(*) FROM ham_metin").fetchone()[0] == \
           db.execute("SELECT sayfa_sayisi FROM kaynak WHERE sha256 = %s", (KAYNAK["sha256"],)).fetchone()[0]


def test_yukleyici_iki_kez_ayni(tmp_path):
    s1 = yukle.yukle(PDF, tmp_path / "bir")
    s2 = yukle.yukle(PDF, tmp_path / "iki")
    assert s1 == s2
    for f in sorted((tmp_path / "bir").glob("*.csv")):
        assert f.read_bytes() == (tmp_path / "iki" / f.name).read_bytes(), f.name
        # depodaki dışa aktarım güncel olmalı
        assert f.read_bytes() == (KOK / "veri" / "dogrulanmis" / f.name).read_bytes(), f.name


def test_gpio_sayilari_belgeyle(a, b, db):
    # s. 1: "30 or 22 GPIOs"
    m = re.search(r"(\d+) or (\d+) GPIOs", sayfa_metni(PDF, 1))
    kapak = {"QFN40": int(m[1]), "QFN32": int(m[2])}
    a_gpio = {p: {r["gpio_no"] for r in rs} for p, rs in a["iomux"].items()}                  # Table 2-4/2-5
    b_gpio = {p: {int(r["iomux_1"][4:]) for r in rs if r["iomux_1"].startswith("GPIO")} for p, rs in b.items()}  # 7-1/7-2
    a_io = {p: sum(r["pin_turu"] in ("IO", "Power/IO") for r in rs) for p, rs in a["pin_overview"].items()}  # 2-1/2-2
    b_io = {p: sum(r["pin_turu"] in ("IO", "Power/IO") for r in rs) for p, rs in b.items()}
    vt = dict(db.execute("SELECT p.ad, count(x.gpio_no) FROM pin x JOIN paket p ON p.id = x.paket_id GROUP BY p.ad"))
    for p in ("QFN40", "QFN32"):
        assert a_gpio[p] == b_gpio[p]
        assert len(a_gpio[p]) == kapak[p] == a_io[p] == b_io[p] == vt[p], p


def test_pin_sayilari_belgeyle(a, b, db):
    vt = dict(db.execute("SELECT p.ad, count(*) FROM pin x JOIN paket p ON p.id = x.paket_id GROUP BY p.ad"))
    for p in ("QFN40", "QFN32"):
        sekil, tablo, toplu = len(a["pin_duzeni"][p]), len(a["pin_overview"][p]), len(b[p])
        assert sekil == tablo == toplu == vt[p], p


def test_belirsiz_kayitlar_karara_bagli(db):
    belirsiz = db.execute("SELECT count(*) FROM cevre_birim_sinyal WHERE belirsiz").fetchone()[0]
    belirsiz += sum(db.execute(f"SELECT count(*) FROM {t} WHERE belirsiz").fetchone()[0]
                    for t in ("pin", "gpio_islev", "gpio_kisit"))
    assert belirsiz == sum(1 for k in FARK_KARARLARI.values() if k["belirsiz"])

"""--rapor YOL (Adım 10c): komut satırı çıktısının aynısını Markdown dosyasına yazar. Başa tarih, kart/paket/bağlam,
model ve istem özeti (istemi eşleşen son dondurma kaydı) ve veritabanındaki kaynak listesi eklenir. Komut satırı
çıktısı değişmez.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from asu_llmcore import PgHatasi, PgOkuyucu

from . import cagrilar
from . import baglanti
from .dogrulama import DONMUS_DOSYALAR, KOK, OLCUM

ISTEMLER = ["src/pinsecim/istemler/ihtiyac_sistem.txt", "src/pinsecim/istemler/atama_sistem.txt"]


def _sha(yol: Path) -> str:
    return hashlib.sha256(yol.read_bytes()).hexdigest()


def dondurma_kimligi() -> str:
    """İstem dosyaları şimdikiyle aynı olan en son dondurma kaydı ve öteki dondurulmuş dosyaların durumu."""
    simdi = {d: _sha(KOK / d) for d in DONMUS_DOSYALAR}
    for yol in sorted(OLCUM.glob("*_dondurma_once.json"), key=lambda y: y.stat().st_mtime, reverse=True):
        kayit = json.loads(yol.read_text(encoding="utf-8"))
        dosyalar = kayit.get("dosyalar", {})
        if all(dosyalar.get(d) == simdi[d] for d in ISTEMLER):
            farkli = [d for d in DONMUS_DOSYALAR if d in dosyalar and dosyalar[d] != simdi[d]]
            ad = yol.name.removesuffix("_once.json")
            return f"`{ad}` (istemler aynı; " + (f"o kayıttan sonra değişen dosya: {', '.join(farkli)})" if farkli
                                                  else "dondurulan dosyaların hepsi aynı)")
    return "istemi eşleşen dondurma kaydı yok"


def kaynaklar() -> list[dict]:
    try:
        with PgOkuyucu("donanim_okur", baglanti.VERITABANI, uygulama_adi="pinsecim_rapor", **baglanti.adres()) as db:
            return db.sorgu("SELECT belge, surum, kaynak_turu, left(sha256, 12) AS sha FROM kaynak ORDER BY id")
    except PgHatasi:
        return []


def metin(h, cikti: str) -> str:
    """Rapor dosyasının içeriği: üst bilgi + komut satırı çıktısı (aynen, kod bloğunda)."""
    ayar = cagrilar.ayar()
    istemler = ", ".join(f"{Path(d).name} {_sha(KOK / d)[:12]}" for d in ISTEMLER)
    kart = (f"{h.kart['kisa_ad']} ({h.kart['ad']}{' ' + h.kart['surum'] if h.kart['surum'] else ''})" if h.kart
            else "yok (çip düzeyi)")
    satirlar = [
        "# Pin seçimi raporu", "",
        f"- Tarih: {time.strftime('%Y-%m-%d %H:%M:%S %z')}",
        f"- Kart: {kart}",
        f"- Paket: {h.paket}",
        "- Bağlam: " + ", ".join(f"{k}={'evet' if v else 'hayır'}" for k, v in h.baglam.items()),
        f"- Model: {ayar.model}, CPU (num_gpu {ayar.num_gpu}), temperature {ayar.temperature}, seed {ayar.seed}, "
        f"num_ctx {ayar.num_ctx}, think {'açık' if ayar.think else 'kapalı'}",
        f"- İstemler: {istemler}",
        f"- Dondurma kaydı: {dondurma_kimligi()}",
        "", "## Kaynaklar", "", "| Belge | Sürüm | Tür | SHA-256 (baş) |", "|---|---|---|---|",
        *(f"| {k['belge']} | {k['surum']} | {k['kaynak_turu']} | `{k['sha']}` |" for k in kaynaklar()),
        "", "## Komut satırı çıktısı", "", "```", cikti.rstrip("\n"), "```", "",
    ]
    return "\n".join(satirlar)


def yaz(yol: Path, h, cikti: str) -> Path:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin(h, cikti), encoding="utf-8")
    return yol

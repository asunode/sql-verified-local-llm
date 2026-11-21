# sql-verified-local-llm

[Türkçe](README.tr.md)

A pattern for using a small local LLM where precision matters. **The model only parses the request.** The application checks every model output against a SQL database of verified facts, each with its source (document, version, page). The application then makes the decisions and writes the answers itself.

The pilot domain is ESP32-C6 pin planning. A user writes a request in Turkish, for example "two buttons, an I2C display, a relay". The system assigns pins for the chip (QFN40 / QFN32) or for a development board, and answers questions such as "is GPIO9 safe to use?" or "which pin is the on-board LED on?".

This is a pilot, not a general-purpose assistant. The program's input and output, and all project documents, are in Turkish.

> Commit references in `doc/` point to the private development history; the public repository starts from a clean snapshot (tag `pilot-v1`).

## How it works

```
User request (+ package/board, context flags)
        │
        ▼
Call A — the model parses the request into a JSON schema
  needs (interface × count, with "dayanak" = the exact span of the request it came from),
  pin preferences / exclusions, questions (closed topic list), context, unsupported parts,
  status (tamam = complete / emin_degilim = unsure / desteklenmiyor = unsupported)
        │
        ▼
Code checks — is the span really in the request, does the count match, any invented GPIO,
  any feature the chip does not have …  Errors go back to the model with the reason
  (at most 3 rounds), otherwise the result is handed to the user. Warnings do not
  start a round; they are shown in the output.
        │
        ▼
Code assigner — picks pins from the verified tables (strapping, flash, USB, JTAG rules,
  board connectors, shared SPI/I2C bus); answers questions from the tables, with sources.
  The model never writes answer text.
        │
        ▼
Output — assignment table with each pin's status, sourced answers, warnings
  (--rapor PATH writes the same as Markdown)
```

Example (`--kart SuperMini`; output is Turkish):

```
İstek: Adreslenebilir LED halkası süreceğim ve bir kızılötesi kumanda alıcısını okuyacağım.
Kart: SuperMini · Paket: QFN32 · bağlam: usb_serial_jtag=evet, uart0_konsol=evet, jtag_pinleri=hayır, harici_flash_beslemesi=hayır

1) İhtiyaçlar (model, 1. turda geçti):
   - RMT_TX    ×1  «Adreslenebilir LED halkası»  [model çıkarımı — kontrol edin]
   - RMT_RX    ×1  «kızılötesi kumanda alıcısını okuyacağım»  [model çıkarımı — kontrol edin]

3) Atama (kod atayıcı):
   Kart düzeyi: SuperMini; adaylar karta çıkan pinler (17 konnektör pini, 5 ped). Ped: kullanılmadı; kart üstü parça pini: kullanılmadı.
   Sonuç: atandı
   İhtiyaç      Sinyal GPIO           Pinin durumu
   rmt_tx_1     OUT    GPIO0 (H1-8)   serbest
   rmt_rx_1     IN     GPIO1 (H1-7)   serbest
   Not: kart verisi doğrulanmadı: kart satırı (ESP32-C6 Super Mini şematik taraması (topluluk) …); H1-7 (GPIO1), H1-8 (GPIO0).

4) Uyarı yok.
```

The model recognised an addressable LED ring as RMT TX and an IR receiver as RMT RX; both are marked "model inference — check". The code chose board pins, avoided the on-board LED and button pins, and noted that the board data is unverified.

## Results

The test sets were written by the side that designed the system (a web-based AI). Each set was unseen at its first measurement and used for regression afterwards.
- "Official" = scored against the acceptance list in the set file.
- "Adjudicated" = after later reviewer rulings.

| Set (requests) | Measurement | Call A correct | Decision correct |
|---|---|---|---|
| v1 (30) | first | 22/30 | 23/25 (assignment then done by the model) |
| v2 (30) | first | 30/30 | model 24/26, code assigner 26/26 |
| v3 (45) | first / last | 43/45 / 42/45 official, 45/45 adjudicated | 41/42 / 42/43 official |
| v4 (36) | first / last | 36/36 / 36/36 | 34/35 (35/35 after a fix) / 35/35 |
| v5 (32, questions + boards) | first / last | 28/32 / 28/32 official, 30/32 adjudicated | 31/32 / 32/32 |

One independent test sentence written by the project owner is handled correctly. That is far too small to claim generalisation. A broader independent test is pending.

Absolute criteria at the end of the pilot:
- **Invented pins: 0.** No output contained a GPIO without a source.
- **The model writes no answer text.** The schema does not allow it; every answer comes from the database.
- **Silent errors: 1 in the last model run.** Z20: two SPI devices got one chip-select. A warning for this case was added afterwards (SPI_ADET_IZI). Applied to the recorded output, it fires on Z20. It has not yet been tested with a new model run.

Main findings:
- **Prompt edits shift unrelated requests.** So after step 10b the prompt file was not changed and fixes went into code and the database; the one exception was step 10c, where two interface lines were added to the text sent to the model (deliberate, regression measured).
- **Decisions are protected by the code checks, not by the model.** Every silent error passed through a gap the code did not check. Z27 and Z06 were closed with their own rules and re-measured; Z20 got a warning that has not yet been tested with a model run.
- **Same-run repeats are identical; across sessions they are not always.** Same input, same model, same Ollama process gave a different count in a different run (Z20). Fixed settings (temperature 0, seed) do not guarantee determinism.
- **Weak points:** inferring an interface from a device name, and knowing what the chip lacks. The model mapped "Ethernet over RMII" to plain GPIOs until an explicit list of unsupported features was put into the database.

Details: [doc/SONUC_RAPORU.md](doc/SONUC_RAPORU.md).

## Stages

All documents are in Turkish.

| Step | Content |
|---|---|
| 0 | PostgreSQL database and roles |
| 1 | Core library, project skeleton, source datasheet |
| 2 | Datasheet pin facts into the database, two independent extractions, 0 differences |
| 3 | Rules in the database, checker, model-free assigner |
| 4 | Model calls A (parse) and B (assign), CLI, cache measurement |
| 5 | First unseen set v1 |
| 6 | Counts, context phrases, interface definitions |
| 7 | Count rules; unseen set v2 |
| 8 | Architecture change: the model parses, the code assigns (K-6); set v3 |
| 9 | Pin preferences (K-7); set v4 |
| 10, 10a–c | Questions answered from tables (K-8), compound numbers, board data, board-level assignment, shared SPI bus, RMT |
| 11, 11a | Uncovered-sentence warning; set v5 (questions + boards); unsupported features, electrical note, shared I2C bus |
| 12 | SPI count warning, closing report |

- Work log: [doc/WORKLOG.md](doc/WORKLOG.md)
- Step reports: [doc/raporlar/](doc/raporlar/)
- Decisions and known limits: [doc/KARARLAR.md](doc/KARARLAR.md)
- Closing report: [doc/SONUC_RAPORU.md](doc/SONUC_RAPORU.md)
- Measurements: `doc/olcum/`; verification: `doc/dogrulama/`

## How the work was organised

- **Project owner:** direction and decisions.
- **Web-based AI:** design, prompts, test sets, review of every step.
- **Coding agent (Claude Code):** code, measurements, records.

`CLAUDE.md` holds the working rules given to the coding agent.

## Requirements and setup

- Linux. Python 3.11 or later (tested with 3.14).
- PostgreSQL 18 (tested), local, 127.0.0.1:5432.
- [Ollama](https://ollama.com) with `gemma4:12b-it-qat`. CPU only is enough; about 30–50 s per request.
- Model settings are fixed in code: temperature 0, seed 42, num_ctx 8192, thinking off, and a cache-boundary request before each call.

```bash
git clone https://github.com/asunode/sql-verified-local-llm.git
cd sql-verified-local-llm
python3 -m venv .venv
.venv/bin/pip install -e ".[test]"        # also installs asu_llmcore (GitHub, tag pilot-v1)
```

**Database** (once, as a PostgreSQL superuser). The script creates the database `donanim` and two roles without passwords:
- `donanim` owns the tables and is used by the loader.
- `donanim_okur` is read-only and is used by the application.

```bash
psql -U postgres -v ON_ERROR_STOP=1 -f kurulum/001_veritabani.sql
psql -U postgres -c '\password donanim'
psql -U postgres -c '\password donanim_okur'
```

Passwords are never written to code or environment variables; libpq reads them from `~/.pgpass` (or `PGPASSFILE`):

```
127.0.0.1:5432:donanim:donanim:<password>
127.0.0.1:5432:donanim:donanim_okur:<password>
```

```bash
chmod 600 ~/.pgpass
```

To use another database name, host or port (e.g. a separate test database):
- Pass `-v veritabani=NAME` to the setup script.
- Set `PINSECIM_VERITABANI`, `PINSECIM_PGHOST`, `PINSECIM_PGPORT` for the application.
- For the core's database tests, set `ASU_LLMCORE_PG_VT`, `ASU_LLMCORE_PG_HOST`, `ASU_LLMCORE_PG_PORT`.

**Source documents.** Third-party PDFs are not in the repository. The script downloads them from their official addresses and checks their SHA-256:

```bash
.venv/bin/python veri/kaynak/indir.py
```

If a download fails, put the file into `veri/kaynak/` by hand under the same name:
- The Super Mini schematic scan is a community file, linked from mischianti.org.
- If a publisher has replaced a document with a newer version, the SHA-256 check fails. The pinned version must then be found by hand.

Addresses and hashes: [veri/kaynak/KAYNAKLAR.md](veri/kaynak/KAYNAKLAR.md).

**Load and test:**

```bash
.venv/bin/python -m pinsecim.yukle        # extracts, cross-checks and loads the verified tables (re-runnable)
.venv/bin/python -m pytest -q             # model-free tests (need the database)
```

**Run** (needs Ollama):

```bash
ollama pull gemma4:12b-it-qat
.venv/bin/python -m pinsecim "İki buton ve bir I2C ekran bağlayacağım." --paket QFN32
.venv/bin/python -m pinsecim "Bir röle ve bir buzzer süreceğim." --kart SuperMini --rapor cikti.md
```

| Option | Meaning |
|---|---|
| `--paket QFN32\|QFN40` | chip package (required without `--kart`) |
| `--kart NAME` | development board: `SuperMini`, `nanoESP32-C6-v1.0`, `"nanoESP32-C6 (v0.2)"`; package comes from the board, pins are chosen from the board's connectors |
| `--no-usb` | USB Serial/JTAG not used (frees GPIO12/13) |
| `--no-uart0-konsol` | UART0 console not used |
| `--jtag-pinleri` | JTAG pins used for debugging |
| `--harici-flash-beslemesi` | flash powered externally |
| `--rapor PATH` | also write the output, with a header, as Markdown |
| `--model-ata` | let the model assign pins (call B), for comparison; default is the code assigner |

Every run appends a trace to `doc/olcum/iz/`.

## Known limits

- Determinism across Ollama sessions is not guaranteed (finding above).
- The SPI count warning only counts devices written with number words. It does not change the decision.
- Several I2C devices always share one bus; a second I2C bus cannot be requested.
- The unsupported-feature list is closed (6 features). Doubtful cases are left to the model and the user.
- No electrical values (current, voltage); questions about them get a note pointing to the datasheet section.
- None of the three boards has been checked against a physical board; two of them rely on transferred or community data. The ESP32-C6's RMT channel directions are not verified against the technical reference manual.
- `--model-ata` (model assignment) does not know about shared buses.
- The independent test is a single sentence.

Full list: [doc/SONUC_RAPORU.md](doc/SONUC_RAPORU.md), section 7.

## License

MIT, see [LICENSE](LICENSE). The third-party source documents are not included and keep their own licenses.

Core library: [asunode/asu_llmcore](https://github.com/asunode/asu_llmcore).

# tw-gov-overseas-trip-kit

[![Version](https://img.shields.io/badge/version-v1.5.0-blue)](https://github.com/Imbad0202/tw-gov-overseas-trip-kit/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Sponsor](https://img.shields.io/badge/sponsor-Buy%20Me%20a%20Coffee-orange?logo=buy-me-a-coffee)](https://buymeacoffee.com/crucify020v)

Document generation toolkit for Taiwan government overseas trip reports, aligned with the **Executive Yuan Overseas Trip Report Processing Guidelines (Appendix I/II)** format, and referencing the **Overseas Travel Expense Reimbursement Rules** (amended 2025-05-13).

> 中文版：[README.md](README.md)

---

## Format Sources

| Regulation | Version | Notes |
|---|---|---|
| Executive Yuan Overseas Trip Report Processing Guidelines | Appendix I/II (2018-06-20) | Primary report format |
| Overseas Travel Expense Reimbursement Rules | Amended 2025-05-13, effective 2026-01-01 (Order 1140101390) | Expense calculation rules |
| Daily Subsistence Allowance Table | Amended 2025-10-31, effective 2026-01-01 (Order 1140103430) | DSA base rates — **not built-in; user-supplied** |

Full legal source list: [docs/sources/README.md](docs/sources/README.md)

---

## Features

- **Per diem calculation**: handles self-paid deduction rules, Taiwan return-day 30% rate, and other scenarios per the reimbursement rules
- **Trip report rendering**: DOCX (editable Word, Appendix I format) trip report and Appendix II review form
- **Pre-trip handbook** (optional): data-driven HTML (daily itinerary / lodging / emergency contacts / notes, all optional); open in a browser or `cmd+P` to print a PDF
- **Finance planning sheet**: Excel travel-expense sheet; the Appendix II review form is rendered separately as DOCX
- **Data validation**: schema validation of required fields and agency-required fields; summary character count 200–300 CJK characters, placeholder rejection

---

## Scope and Limitations

This kit targets the **layer common to all agencies**: the Executive Yuan trip-report Appendix I/II format plus the overseas per-diem reimbursement calculation. It does not target any single agency's customized layout.

**How it works**: you put your **data** into `trip.json` (agency, personnel, itinerary, dates), and the kit **generates** DOCX / XLSX / HTML aligned to that format. The kit **does not read or conform to an individual agency's own template files** (e.g. a university's report template `.odt` or expense form `.doc`).

**Therefore**:

- The report format is a common reference; national colleges and universities with campus funds are excluded from the report guidelines’ definition of schools and must check their own applicable rules; if your agency has a customized layout (logo, header, extra sign-off fields), add those on top of the generated DOCX.
- Per-diem calculation follows the reimbursement rules, but the **fixed layout of an expense report form** (transport schedule table, meals/lodging checkboxes, multi-stage sign-off) is usually agency-specific; the kit outputs a generic worksheet, not a specific agency's form.
- **Pre-trip application / approval forms** (e.g. a campus-fund overseas plan form with principal investigator, unit review, head approval) are agency-specific administrative workflow documents and are **out of scope**.

In short: the kit provides the common base; the customization layer is left to each agency.

---

## Quick start

Python 3.10+ is required. From the cloned repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m tripkit init --directory data/my-trip
python -m tripkit render --trip data/my-trip/trip.json --finance data/my-trip/finance.json --out output/my-trip
```

On Windows use `py -m venv .venv` and `.venv\Scripts\Activate.ps1`, or invoke `.venv\Scripts\python.exe` directly. Installed packages also work outside the checkout.

The default outputs are a handbook, review form and USD planning sheet. Replace the synthetic agency, traveler, dates, itinerary and amounts before use. Example rates and flights are **not official rates or live quotes**. The `data/` and `output/` folders are ignored by Git.

```bash
# Validate both files, including dates and finance inputs
python -m tripkit validate --trip data/my-trip/trip.json --finance data/my-trip/finance.json

# Include the report, which requires a valid summary and all three body sections
python -m tripkit render --trip data/my-trip/trip.json --finance data/my-trip/finance.json --outputs report review finance handbook --out output/full

# Compare candidates from a separate JSON file; does not search or book flights
python -m tripkit flights --input data/my-trip/flight-options.json --out output/flights.html
```

Use `--outputs handbook` for a handbook alone. A report needs `summary` (200–300 Chinese characters) and paragraph arrays at `report_content.purpose`, `process`, and `insights_and_recommendations`. To intentionally generate an unfinished report skeleton, add `--allow-incomplete-report`; the summary is still checked. Review in Word and export ODF/PDF before submission.

Existing files are protected unless `--force` is supplied. Validation errors show field paths and stop rendering before output is written. Every command supports `--help`. The shorter `tripkit` command is also installed.

## Scenario coverage

See the [coverage matrix](docs/情境覆蓋表.md) and [case guidance](docs/延返與個案指引.md) (Traditional Chinese). The toolkit covers one traveler and one trip per finance file:

- Each dated segment represents one day; dates must be ordered and unique, including multi-city travel.
- `reimbursable: false` plus `exclusion_reason` excludes private or non-claim days while retaining their dates and original rates.
- `approved_days` counts calendar days from `approved_start_date` (the first segment by default), including missing days. Set the approval start explicitly for an early private departure. If omitted, it does not restrict reimbursement; approved extensions require an explicit flag.
- Daily rates and `rate_source` are user-supplied. Meal provision and allowances must reflect actual arrangements.
- Long stays retain the existing 30/90-day model; calendar-month boundaries and combinations need manual review.
- `manual_items` contains USD planning amounts only. Currency conversion, actual lodging adjustments, group allocations, eligibility, advances and final TWD reimbursement remain manual.
- Mainland China, Hong Kong and Macau require their separate official rate table. Resident staff and training/research subsidies may use different rules.
- Flight ranking has clock times and +1 flags, not a full dated timezone model. Date-line and multi-day duty windows need manual review.

The mixed synthetic example can be rendered with `--finance examples/04-mixed-scenarios.trip-finance.json`; its expected total is USD 823. Monetary accumulation uses decimal arithmetic. Excel preserves notes, rate sources and exclusion reasons, and is a generated snapshot: edit JSON and regenerate to update amounts.

For development, install `python -m pip install -e ".[dev]"` and run `python -m pytest -q`. CI also builds a wheel and generates all five outputs outside the checkout.

---

## Use as an AI Skill (cross-vendor)

Besides calling it as a Python package, this toolkit is packaged as an AI skill usable across multiple AI tools. The core is a `SKILL.md` with frontmatter; each vendor entry points to the same content:

| Scenario | Entry | How |
|---|---|---|
| claude.ai / cowork | `skill.zip` | Download `tw-gov-overseas-trip-kit-skill-vX.Y.Z.zip` from [Releases](https://github.com/Imbad0202/tw-gov-overseas-trip-kit/releases) and upload it |
| Claude Code | `.claude-plugin/plugin.json` | Load as a plugin after cloning, or `git clone` into `~/.claude/skills/` |
| Codex / Gemini CLIs | `AGENTS.md` / `GEMINI.md` | Clone into your working directory; the agent reads them (both point to `SKILL.md`) |
| Any vendor | clone and go | Clone the repo; each entry file sits at the root |

When using it, have the AI bring in your agency's data (`trip.json`) and fill `per_diem_base` from the current-year official per-diem table (the table is not bundled). For advanced usage see [SKILL.md](SKILL.md).

> **The report body must be filled in by you**: the three body sections of the trip report (Purpose / Process / Reflections & Recommendations) can be supplied through `report_content`; missing sections remain a "heading + writing prompt" skeleton, **not finished content**. Filling only the basic fields and summary yields a hollow report. Use your trip materials (meeting transcripts, notes, visit records) to flesh out the body. **This tool does not record or transcribe; you supply the materials.** If materials contain confidential or others' personal data, handle them per the Executive Yuan's generative-AI guidelines and your agency's rules (see [DISCLAIMER.md](DISCLAIMER.md)).

---

## Disclaimer

This tool generates document templates only. Users bear full responsibility for the accuracy and content of produced documents. Documents must be reviewed and approved per the user's agency procedures before submission.

Full disclaimer: [DISCLAIMER.md](DISCLAIMER.md)
Version & citations: [CITATIONS.md](CITATIONS.md)
Provenance: [PROVENANCE.md](PROVENANCE.md)

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Support This Project

If this tool helped you:

- Hit [Star](https://github.com/Imbad0202/tw-gov-overseas-trip-kit) so more people can find it
- Share with colleagues who handle overseas trip cases, or anyone who needs to produce trip reports
- [Buy Me a Coffee](https://buymeacoffee.com/crucify020v) to support ongoing development
- Found a bug or have a suggestion? Open an [Issue](https://github.com/Imbad0202/tw-gov-overseas-trip-kit/issues)

## Author

**Cheng-I Wu** — [GitHub](https://github.com/Imbad0202) | [Buy Me a Coffee](https://buymeacoffee.com/crucify020v)

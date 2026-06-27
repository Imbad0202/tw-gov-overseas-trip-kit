# tw-gov-overseas-trip-kit

[![Version](https://img.shields.io/badge/version-v1.3.0-blue)](https://github.com/Imbad0202/tw-gov-overseas-trip-kit/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Sponsor](https://img.shields.io/badge/sponsor-Buy%20Me%20a%20Coffee-orange?logo=buy-me-a-coffee)](https://buymeacoffee.com/crucify020v)

Document generation toolkit for Taiwan government overseas trip reports, aligned with the **Executive Yuan Overseas Trip Report Processing Guidelines (Appendix I/II)** format, and referencing the **Overseas Travel Expense Reimbursement Rules** (amended 2025-05-13).

> 中文版：[README.md](README.md)

---

## Format Sources

| Regulation | Version | Notes |
|---|---|---|
| Executive Yuan Overseas Trip Report Processing Guidelines | Appendix I/II (2018-06-20) | Primary report format |
| Overseas Travel Expense Reimbursement Rules | Amended 2025-05-13 (Order 1140101390) | Expense calculation rules |
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

- Most agencies' (including universities') trip reports and review forms inherit the Executive Yuan rules, so the output aligns closely; if your agency has a customized layout (logo, header, extra sign-off fields), add those on top of the generated DOCX.
- Per-diem calculation follows the reimbursement rules, but the **fixed layout of an expense report form** (transport schedule table, meals/lodging checkboxes, multi-stage sign-off) is usually agency-specific; the kit outputs a generic worksheet, not a specific agency's form.
- **Pre-trip application / approval forms** (e.g. a campus-fund overseas plan form with principal investigator, unit review, head approval) are agency-specific administrative workflow documents and are **out of scope**.

In short: the kit provides the common base; the customization layer is left to each agency.

---

## Installation

```bash
pip install -e ".[dev]"
```

Requires Python 3.10+.

---

## Quick Start

```python
# Run from the project root directory (tw-gov-overseas-trip-kit/)
import json, pathlib
from jsonschema import validate
from calc.per_diem import compute_trip_per_diem
from render.render_html import render_html
from render.render_finance_xlsx import render_finance_xlsx

trip = json.loads(pathlib.Path("examples/02-sample-agency.trip.json").read_text(encoding="utf-8"))
fin = json.loads(pathlib.Path("examples/02-sample-agency.trip-finance.json").read_text(encoding="utf-8"))
result = compute_trip_per_diem(fin["per_diem_inputs"]["segments"],
                               fin["per_diem_inputs"].get("manual_items"),
                               approved_days=fin["per_diem_inputs"].get("approved_days"))
render_html(trip, "pre_trip.html")
render_finance_xlsx(fin, "finance.xlsx")
```

See `examples/` for synthetic sample data.

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

> **The report body must be filled in by you**: the three body sections of the trip report (Purpose / Process / Reflections & Recommendations) are generated as a "heading + writing prompt" skeleton, **not finished content**. Filling only the basic fields and summary yields a hollow report. Use your trip materials (meeting transcripts, notes, visit records) to flesh out the body. **This tool does not record or transcribe; you supply the materials.** If materials contain confidential or others' personal data, handle them per the Executive Yuan's generative-AI guidelines and your agency's rules (see [DISCLAIMER.md](DISCLAIMER.md)).

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

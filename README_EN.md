# tw-gov-overseas-trip-kit

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
- **Trip report rendering**: HTML (browser-printable) and DOCX (editable Word format)
- **Finance reimbursement sheet**: Appendix II Excel format
- **Data validation**: schema validation of required fields and agency-required fields; summary character count 200–300 CJK characters, placeholder rejection

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

## Disclaimer

This tool generates document templates only. Users bear full responsibility for the accuracy and content of produced documents. Documents must be reviewed and approved per the user's agency procedures before submission.

Full disclaimer: [DISCLAIMER.md](DISCLAIMER.md)
Version & citations: [CITATIONS.md](CITATIONS.md)
Provenance: [PROVENANCE.md](PROVENANCE.md)

---

## License

MIT License — see [LICENSE](LICENSE)

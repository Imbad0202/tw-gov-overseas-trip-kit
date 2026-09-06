"""tripkit init / validate / render / flights。"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile

from tripkit.resources import resource_text
from tripkit.validation import validate_trip, validate_finance, validate_pair, validate_schema


def _read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}:{exc.lineno}:{exc.colno}: JSON 格式錯誤（{exc.msg}）") from exc


def _destinations(directory, names, force=False):
    paths = [directory / name for name in names]
    for path in paths:
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f"輸出不是一般檔案：{path}")
        if path.exists() and not force:
            raise ValueError(f"檔案已存在：{path}；請換資料夾，或用 --force 明示覆寫")
    return paths


def _warnings(messages):
    for message in dict.fromkeys(messages):
        print(f"提醒：{message}", file=sys.stderr)


def _init(args):
    directory = Path(args.directory)
    sources = {"trip.json": "02-sample-agency.trip.json",
               "finance.json": "02-sample-agency.trip-finance.json",
               "flight-options.json": "03-flight-options.json"}
    paths = _destinations(directory, sources, args.force)
    content = [resource_text("examples", name) for name in sources.values()]
    directory.mkdir(parents=True, exist_ok=True)
    for path, value in zip(paths, content):
        path.write_text(value, encoding="utf-8")
        print(f"已建立 {path}")
    print("這是合成示範：請替換機關、人員、行程、摘要／本文及費用；數額與班機都不是官方查價。")


def _validate_or_render(args):
    if not args.trip and not args.finance:
        raise ValueError("至少提供 --trip 或 --finance")
    trip = _read(args.trip) if args.trip else None
    finance = _read(args.finance) if args.finance else None
    outputs = args.outputs
    if not outputs:
        outputs = (["review", "handbook"] if trip is not None else []) + (["finance"] if finance is not None else [])
    outputs = list(dict.fromkeys(outputs))
    if any(o in outputs for o in ("report", "review", "handbook")) and trip is None:
        raise ValueError("report / review / handbook 需要 --trip")
    if "finance" in outputs and finance is None:
        raise ValueError("finance 輸出需要 --finance")
    warnings = []
    if trip is not None:
        warnings += validate_trip(trip, report="report" in outputs,
                                  allow_incomplete_report=args.allow_incomplete_report)
    if finance is not None:
        warnings += validate_finance(finance)
    if trip is not None and finance is not None:
        warnings += validate_pair(trip, finance)
    _warnings(warnings)
    if args.command == "validate":
        print("資料驗證通過（不代表報支核准或報告內容審核完成）")
        return
    from render.render_docx import render_report_docx, render_review_table_docx
    from render.render_html import render_html
    from render.render_finance_xlsx import render_finance_xlsx
    renderers = {"report": ("report.docx", render_report_docx),
                 "review": ("review_table.docx", render_review_table_docx),
                 "handbook": ("pre_trip.html", render_html),
                 "finance": ("finance.xlsx", render_finance_xlsx)}
    directory = Path(args.out)
    paths = _destinations(directory, [renderers[o][0] for o in outputs], args.force)
    inputs = {Path(p).resolve() for p in (args.trip, args.finance) if p}
    if any(path.resolve() in inputs for path in paths):
        raise ValueError("輸出不可覆蓋輸入資料")
    # 先全數驗證、暫存產檔成功後才寫入目的地；摘要錯誤不留下半套文件。
    with tempfile.TemporaryDirectory(prefix="tripkit-") as temporary:
        for output in outputs:
            name, renderer = renderers[output]
            renderer(finance if output == "finance" else trip, str(Path(temporary) / name))
        directory.mkdir(parents=True, exist_ok=True)
        for path in paths:
            shutil.copyfile(Path(temporary) / path.name, path)
            print(f"已產出 {path}")
    if "report" in outputs:
        print("報告為可編輯 DOCX；請核閱本文後轉 ODF / PDF 送核。")


def _flights(args):
    from calc.flight_rank import rank_candidates, choose_layout, summary_rows
    from render.render_flight_options import render_flight_options
    data = _read(args.input)
    validate_schema(data, "flight-options.schema.json")
    ranked = rank_candidates(data["candidates"], data.get("first_duty_local"), data.get("tz_diff_hours", 0))
    _warnings(["首場公務只帶時刻，休息窗口採最近一次該時刻估計；跨日、多日與換日線請人工核對"]
              if data.get("first_duty_local") else [])
    out = Path(args.out)
    _destinations(out.parent, [out.name], args.force)
    if out.resolve() == Path(args.input).resolve():
        raise ValueError("輸出不可覆蓋輸入資料")
    out.parent.mkdir(parents=True, exist_ok=True)
    render_flight_options({"title": data.get("title", "航班查價比較"), "candidates": ranked,
                           "layout": choose_layout(ranked), "summary_rows": summary_rows(ranked)}, str(out))
    print(f"已產出 {out}（比較底稿；以票務代理報價為準）")


def main(argv=None):
    parser = argparse.ArgumentParser(description="台灣公務國外差旅文件工具（Python 3.10+）")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="建立可直接試跑的合成資料")
    init.add_argument("--directory", default="data/my-trip", help="輸入資料夾（預設 data/my-trip）")
    init.add_argument("--force", action="store_true", help="覆寫既有示範資料")
    init.set_defaults(action=_init)
    for command in ("validate", "render"):
        p = sub.add_parser(command, help="驗證資料" if command == "validate" else "驗證後產生文件")
        p.add_argument("--trip", help="行程 JSON")
        p.add_argument("--finance", help="經費 JSON")
        p.add_argument("--outputs", nargs="+", choices=["report", "review", "handbook", "finance"],
                       help="預設依輸入產審核表／手冊／經費表；report 請明示")
        p.add_argument("--allow-incomplete-report", action="store_true", help="允許缺本文的報告骨架；摘要仍須合格")
        if command == "render":
            p.add_argument("--out", default="output", help="輸出資料夾（預設 output）")
            p.add_argument("--force", action="store_true", help="覆寫既有輸出")
        p.set_defaults(action=_validate_or_render)
    flights = sub.add_parser("flights", help="以獨立候選 JSON 產生航班比較底稿（不查價、不訂位）")
    flights.add_argument("--input", required=True)
    flights.add_argument("--out", default="output/flight_options.html")
    flights.add_argument("--force", action="store_true")
    flights.set_defaults(action=_flights)
    args = parser.parse_args(argv)
    try:
        args.action(args)
    except (ValueError, OSError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 2
    return 0

#!/usr/bin/env python3
"""Install a built wheel into a temporary directory and run the documented journey.

Usage: python scripts/check_wheel.py dist/<wheel>.whl
Dependencies must already be installed in the invoking Python environment.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    wheel = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix="tripkit-wheel-") as tmp:
        root = Path(tmp)
        target = root / "installed"
        subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", "--no-compile",
                        "--target", str(target), str(wheel)], check=True, cwd=root)
        env = {**os.environ, "PYTHONPATH": str(target), "PYTHONNOUSERSITE": "1"}

        def run(*args):
            subprocess.run([sys.executable, "-m", "tripkit", *args], check=True, cwd=root, env=env)

        # cwd 與 PYTHONPATH 均無 checkout，確保不是 editable install 假通過。
        subprocess.run([sys.executable, "-c",
                        "import tripkit, sys; from pathlib import Path; "
                        "assert Path(tripkit.__file__).is_relative_to(Path(sys.argv[1]))",
                        str(target)], check=True, cwd=root, env=env)
        run("init", "--directory", "data/demo")
        run("validate", "--trip", "data/demo/trip.json", "--finance", "data/demo/finance.json",
            "--outputs", "report", "review", "handbook", "finance")
        run("render", "--trip", "data/demo/trip.json", "--finance", "data/demo/finance.json",
            "--outputs", "report", "review", "handbook", "finance", "--out", "result")
        run("flights", "--input", "data/demo/flight-options.json", "--out", "result/flight_options.html")
        expected = {"report.docx", "review_table.docx", "pre_trip.html", "finance.xlsx", "flight_options.html"}
        assert {p.name for p in (root / "result").iterdir()} == expected
        assert all(p.stat().st_size for p in (root / "result").iterdir())
    print("PASS: installed wheel generates all five outputs outside checkout")


if __name__ == "__main__":
    main()

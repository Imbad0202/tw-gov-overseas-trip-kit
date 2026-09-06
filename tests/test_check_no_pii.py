"""掃描器不能漏掉 Git 預設會 quote 的中文檔名。"""
from pathlib import Path
import shutil
import subprocess


def test_unicode_and_metacharacter_filename_is_scanned(tmp_path):
    scanner = Path("scripts/check_no_pii.sh").resolve()
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=Synthetic Test",
                    "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "initial", "--allow-empty"], check=True)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copyfile(scanner, scripts / scanner.name)
    name = "中文|含空白 文件.md"
    data = tmp_path / name
    data.write_text("合成測試\n", encoding="utf-8")
    result = subprocess.run(["bash", str(scripts / scanner.name)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    # 分段組字，避免測試自身成為規則命中的資料。
    data.write_text("Claude" + "-Session: synthetic\n", encoding="utf-8")
    result = subprocess.run(["bash", str(scripts / scanner.name)], capture_output=True, text=True)
    assert result.returncode == 1
    assert f"{name}:1:" in result.stdout
    assert "No such file" not in result.stderr

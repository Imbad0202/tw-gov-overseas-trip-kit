"""Task 12 — public convention files: DISCLAIMER 4-layer, CITATIONS versions, PROVENANCE."""
import pathlib

BASE = pathlib.Path(__file__).parent.parent


def test_disclaimer_four_layers():
    txt = (BASE / "DISCLAIMER.md").read_text(encoding="utf-8")
    assert "自負其責" in txt                    # 第1層 正確性
    assert "人工智慧基本法" in txt              # 第2層
    assert "114" in txt and "12" in txt         # 第2層 AI 基本法日期（民國114年12月）
    assert "生成式 AI 參考指引" in txt          # 第3層
    assert "個人資料保護法" in txt              # 第4層


def test_citations_lock_versions():
    txt = (BASE / "CITATIONS.md").read_text(encoding="utf-8")
    assert "114.05.13" in txt or "114年5月13日" in txt   # 報支要點版本
    assert "1140101390" in txt                            # 報支要點文號
    assert "1140103430" in txt                            # 日支表文號


def test_provenance_from_scratch():
    txt = (BASE / "PROVENANCE.md").read_text(encoding="utf-8")
    assert "from scratch" in txt.lower()

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_probe():
    path = TASK_DIR / "workspace" / "distribution_probe.py"
    spec = importlib.util.spec_from_file_location("distribution_probe_6c2353a2cdee", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_exposes_canonical_morphology_regression_and_repair() -> None:
    probe = _load_probe()
    report = probe.compare_sources(
        before_path=TASK_DIR / "workspace" / "generator_before_review.py",
        after_path=TASK_DIR / "generator.py",
        canonical_path=REPO / "shared" / "data" / "canonical" / "puzzles.jsonl",
        samples_per_band=8,
        seed_base=7331,
    )

    assert report["task_id"] == "6c2353a2cdee"
    assert report["canonical"]["connected_panel_fraction"] == 1.0
    assert report["before"]["connected_panel_fraction"] < 0.5
    assert report["after"]["connected_panel_fraction"] == 1.0
    assert report["after"]["middle_rows_panel_fraction"] == 1.0
    assert report["after"]["all_count_palette_fraction"] == 1.0
    assert set(report["after"]["code_frequencies"]) <= {"1", "2", "3", "4"}

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROBE_PATH = ROOT / "generators" / "b35816e8388b" / "workspace" / "lesson_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("b35816e8388b_lesson_probe", PROBE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_uses_live_declarations_and_covers_every_schedule_start():
    probe = _load_probe()
    report = probe.run_probe(lessons_per_band=3)

    assert report["task_id"] == "b35816e8388b"
    assert report["sampler"]["lessons_per_band"] == 3
    assert set(report["declarations"]["canonical_shortcuts"]) == {
        "fixed_grid_center"
    }
    assert set(report["declarations"]["lesson_competitors"]) == {
        "fixed_grid_center",
        "keep_endpoints",
        "paint_whole_segment",
    }
    assert report["canonical_shortcuts"]["fixed_grid_center"]["fits_all_pairs"]

    for band in ("easy", "medium", "hard"):
        row = report["bands"][band]
        assert row["lessons"] == 3
        assert row["identifiable"] == 3
        assert row["cyclic_start_counts"] == {"0": 1, "1": 1, "2": 1}
        assert row["shortcut_disagreements"]["fixed_grid_center"] > 0
        assert row["unique_inputs"] >= 10

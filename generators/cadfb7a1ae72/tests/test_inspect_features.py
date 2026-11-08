from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_feature_probe_reports_intended_and_rival_matrices_without_mutation():
    generator = _load(TASK_DIR / "generator.py", "cadfb_generator_for_probe_test")
    probe = _load(TASK_DIR / "workspace" / "inspect_features.py", "cadfb_probe_test")
    grid = generator.generate(1234, 3, difficulty="medium")
    before = [row[:] for row in grid]
    report = probe.report_for_grid(grid)
    assert grid == before
    assert report["dimensions"] == [len(grid), len(grid[0])]
    assert len(report["objects"]) == 5
    assert {
        "projection_symmetry_class",
        "enclosed_zero_cells",
    } <= set(report["objects"][0])
    assert report["intended_output"] == generator.rule_mirror(grid)
    assert set(report["rivals"]) == {
        "hole_priority",
        "binary_holes",
        "axis_count",
        "projection_symmetry",
        "enclosed_hole_cells",
        "color_order",
    }
    assert report["rivals"]["binary_holes"]["disagrees"] is True

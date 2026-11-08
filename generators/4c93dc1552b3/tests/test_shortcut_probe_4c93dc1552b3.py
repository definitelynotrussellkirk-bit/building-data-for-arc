from __future__ import annotations

import importlib.util
from pathlib import Path

from reviewer_support import find_root


TASK_ID = "4c93dc1552b3"
ROOT = find_root(__file__)
PROBE = ROOT / "generators" / TASK_ID / "workspace" / "probe_shortcuts.py"


def load_probe():
    spec = importlib.util.spec_from_file_location("shortcut_probe", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_finds_canonical_fitting_wrong_color_rectangle_rival():
    probe = load_probe()
    report = probe.build_report(seed_limit=64)

    rival = report["canonical_rivals"]["all_solid_rectangles_any_color"]
    assert rival["fits_all"] is True
    assert rival["fit_count"] == report["canonical_pair_count"]

    witness = report["selected_witness"]
    assert witness["rival"] == "all_solid_rectangles_any_color"
    assert witness["intended_output"] != witness["rival_output"]
    assert witness["generator_membership"]["self_check_errors"] == []
    assert witness["generator_membership"]["teaching_check_errors"] == []
    assert witness["differing_cells"]
    assert all(cell["input_color"] not in (0, 1, 2) for cell in witness["differing_cells"])

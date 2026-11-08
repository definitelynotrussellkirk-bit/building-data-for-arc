"""Contract tests for the reusable canonical-shortcut witness probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROBE_PATH = HERE.parent / "workspace" / "probe_shortcuts.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location(
        "a9f315ca9cc7_shortcut_probe", PROBE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_probe_checks_actual_declaration_and_finds_generated_witness():
    probe = _load_probe()
    report = probe.build_report(seed=19, max_samples=20)
    assert report["task_id"] == "a9f315ca9cc7"
    assert report["canonical_pair_count"] == 6
    assert report["declared_shortcuts"] == [
        "memorize_public_masks_else_pixel_scale"
    ]
    result = report["shortcuts"]["memorize_public_masks_else_pixel_scale"]
    assert result["fits_all_canonical_pairs"] is True
    witness = result["first_generated_disagreement"]
    assert witness is not None
    assert witness["self_check_errors"] == []
    assert witness["observed_overrides"]["scene_profile"] == "generalized"
    assert witness["intended_python_output"] != witness["shortcut_output"]

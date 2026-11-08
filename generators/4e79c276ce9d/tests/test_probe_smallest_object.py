from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root

TASK_ID = "4e79c276ce9d"
ROOT = find_root(__file__)
PROBE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "probe_smallest_object.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("probe_smallest_object", PROBE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_checks_declared_rivals_axes_and_every_cyclic_rotation():
    probe = _load_probe()
    report = probe.run_probe(seed=441, samples_per_band=8)
    assert report["passed"] is True
    assert report["canonical"]["pair_count"] == 5
    assert report["canonical"]["shortcut_failures"] == []
    assert report["defaults"]["draw_count"] == 24
    assert report["defaults"]["profile_violations"] == []
    assert report["defaults"]["witness_failures"] == []
    assert report["overrides"]["combination_count"] == 48
    assert report["overrides"]["failures"] == []
    assert report["schedule"]["start_count"] == 18
    assert report["schedule"]["rotation_count"] == 72
    assert report["schedule"]["failures"] == []


def test_probe_cli_writes_the_same_structured_report(tmp_path: Path):
    probe = _load_probe()
    output = tmp_path / "probe.json"
    assert probe.main([
        "--seed", "442",
        "--samples-per-band", "2",
        "--out", str(output),
    ]) == 0
    saved = json.loads(output.read_text())
    assert saved["passed"] is True
    assert saved["defaults"]["draw_count"] == 6

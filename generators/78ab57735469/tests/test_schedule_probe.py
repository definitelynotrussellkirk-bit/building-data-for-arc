"""Smoke test for the reusable declared-rival schedule probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import find_root  # noqa: E402

ROOT = find_root(__file__)
PROBE_PATH = ROOT / "generators" / "78ab57735469" / "workspace" / "probe_schedule.py"
SPEC = importlib.util.spec_from_file_location("probe_schedule_78ab", PROBE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROBE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROBE
SPEC.loader.exec_module(PROBE)


def test_probe_checks_declared_shortcuts_and_all_query_rotations():
    report = PROBE.probe(seed=17, starts=4, bands=("easy",))
    assert report["violations"] == []
    assert report["canonical_shortcuts"]["fixed_3x3"]["fits_all_pairs"] is True
    assert report["summary"] == {
        "bands": 1,
        "lesson_starts": 4,
        "lessons_checked": 4,
        "unique_inputs": 7,
        "query_rotations": 16,
        "rival_checks": 48,
        "ambiguous_rotations": 0,
    }

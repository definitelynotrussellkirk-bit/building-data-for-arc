"""Regression tests for the source-bound lawful-minimal-shape evidence tool."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break

TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = TASK_HOME / "workspace" / "lawful_minimal_probe.py"


def load_probe():
    assert SOURCE.is_file(), "lawful-minimal evidence tool has not been implemented"
    spec = importlib.util.spec_from_file_location("lawful_minimal_probe", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_probe_defines_the_exact_linter_shapes_without_narrowing_the_domain():
    probe = load_probe()
    assert set(probe.PROBES) == {"singleton", "short_line", "solid_2x2"}
    for item in probe.PROBES.values():
        grid = item["input"]
        assert len(grid) >= 3 and len(grid[0]) >= 3
        assert item["expected"] == [[4] * sum(value == 4 for row in grid for value in row)]


def test_probe_executes_current_canonical_racket_and_current_self_check():
    probe = load_probe()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        report = probe.build_report(bridge=bridge)
    assert report["status"] == "pass"
    assert report["rule_hash"] == "4571597a8055"
    assert report["summary"] == {"checked": 3, "passed": 3}
    assert all(item["self_check_errors"] == [] for item in report["probes"])
    assert all(item["canonical_matches_expected"] for item in report["probes"])

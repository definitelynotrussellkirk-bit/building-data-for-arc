"""Smoke-test the reusable bounded adversarial probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
PATH = HOME / "workspace" / "parametric" / "adversarial_probe.py"
_SPEC = importlib.util.spec_from_file_location("_probe_8a34b3906f3a", PATH)
assert _SPEC is not None and _SPEC.loader is not None
PROBE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(PROBE)


def test_bounded_probe_covers_minimum_lesson_large_query_and_negative_verifier():
    report = PROBE.run_probe(seed_count=3, racket_seed_count=0)
    assert report["schema"] == "8a34b3906f3a-adversarial-probe-v1"
    assert report["findings"] == []
    assert report["coverage"]["episodes"] == 6
    assert report["coverage"]["minimum_demo_episodes"] == 6
    assert report["coverage"]["maximum_demo_episodes"] == 6
    assert report["coverage"]["query_sizes"] == [21, 23, 25, 30]
    assert set(report["coverage"]["selector_rivals"]) == set(
        PROBE.PROTOTYPE.TEACHING_SELECTOR_RIVALS
    )
    assert report["negative_verifier"]["all_rejected"] is True

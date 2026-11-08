"""The curriculum diagnostic must inspect actual consecutive production calls."""
from __future__ import annotations

import importlib.util

import pytest

from reviewer_support import find_root


def _probe_module():
    path = find_root(__file__) / "generators/9971f3a5882c/workspace/lesson_probe.py"
    spec = importlib.util.spec_from_file_location("lattice_lesson_probe", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _probe_module()


def test_requested_windows_do_not_wrap_or_invent_curriculum_transitions(probe):
    report = probe.run_probe(seed=7331, period=12)
    boundary = next(row for row in report["rotations"]
                    if row["band"] == "default" and row["start"] == 11)
    assert boundary["indices"] == [11, 12, 13, 14]


def test_default_probe_covers_full_joint_profile_period(probe):
    report = probe.run_probe(seed=7331, period=None)
    assert report["profile_schedule_period"] == 60
    assert report["period"] == 60
    assert report["rotations_checked"] == 960
    assert report["coverage_status"] == "complete_profile_period_at_fixed_seed"
    assert report["status"] == "PASS"
    assert report["failures"] == []
    last = next(row for row in report["rotations"]
                if row["band"] == "default" and row["start"] == 59)
    assert last["indices"] == [59, 60, 61, 62]


def test_explicit_short_probe_reports_incomplete_profile_coverage(probe):
    report = probe.run_probe(seed=7331, period=4)
    assert report["coverage_status"] == "partial_profile_period_at_fixed_seed"
    assert report["profile_schedule_period"] == 60
    assert report["period"] == 4

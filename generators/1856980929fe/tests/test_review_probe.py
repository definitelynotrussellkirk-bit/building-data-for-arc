from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


PROBE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "review_probe.py"
SPEC = importlib.util.spec_from_file_location("review_probe_1856980929fe", PROBE_PATH)
assert SPEC and SPEC.loader
probe = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = probe
SPEC.loader.exec_module(probe)


def test_probe_is_source_bound_and_declared_rivals_are_refuted():
    report = probe.analyze(lessons_per_band=4, demos=5)
    assert report["task_id"] == "1856980929fe"
    assert report["generator_sha256"] == probe.generator_sha256()
    assert report["sampler"]["policy"] == "shared seed; five consecutive demos; next index query"
    assert set(report["competitors"]) == {
        "first_two_seeds_only",
        "shared_first_size",
        "single_fan_level",
    }
    assert report["totals"]["lessons"] == 12
    assert report["totals"]["query_discriminating_survivors"] == 0
    assert report["totals"]["invalid_inputs"] == 0
    assert all(row["unique_inputs"] > 0 for row in report["bands"].values())
    assert all(count > 0 for count in report["witness_hits"].values())


def test_probe_uses_sample_offset_even_when_two_inputs_are_identical(monkeypatch):
    fixed = probe.gen.generate(55, 0, difficulty="easy")
    monkeypatch.setattr(probe.gen, "generate", lambda *args, **kwargs: fixed)
    monkeypatch.setattr(probe.gen, "LESSON_COMPETITORS", {})
    monkeypatch.setattr(probe.gen, "SEMANTIC_WITNESSES", {})
    monkeypatch.setattr(
        probe.gen,
        "schedule_profile",
        lambda seed, sample_index, difficulty=None: sample_index % 4,
    )
    report = probe.analyze(lessons_per_band=1, demos=5)
    expected = {"0": 2, "1": 2, "2": 1, "3": 1}
    assert all(row["schedule_profiles"] == expected for row in report["bands"].values())


def test_probe_separates_raw_shortcuts_from_semantic_gate_failures():
    """A declared gate rejection is not an unguarded lesson failure."""
    report = probe.analyze(lessons_per_band=100, demos=5)
    assert report["totals"]["query_discriminating_survivors"] > 0
    assert report["totals"]["guarded_query_discriminating_survivors"] == report["totals"][
        "query_discriminating_survivors"
    ]
    assert report["totals"]["unguarded_query_discriminating_survivors"] == 0

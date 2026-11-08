from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

HOME = Path(__file__).resolve().parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load(HOME / "generator.py", "probe_test_generator")
probe = _load(HOME / "workspace" / "lesson_probe.py", "lesson_probe")


def test_current_schedule_has_no_declared_rival_ambiguity_across_rotations():
    report = probe.audit_schedule(gen, starts=8, seed=1701)
    assert report["passed"] is True
    assert report["counts"]["lessons"] == 24
    assert report["counts"]["rotations"] == 96
    assert report["counts"]["ambiguous_rotations"] == 0
    assert report["counts"]["hook_failures"] == 0
    assert report["counts"]["unique_inputs"] == 33
    assert report["failures"] == []
    for band in ("easy", "medium", "hard"):
        assert set(report["by_band"][band]["profile_counts"]) == {
            "identity_scope",
            "mixed_scope",
        }


def test_probe_retains_a_query_disagreement_when_a_rival_fits_all_demos():
    def generate(seed, sample_index, *, difficulty=None):
        del seed, difficulty
        return [[sample_index % 4]]

    def intended(grid):
        return [row[:] for row in grid]

    def rival(grid):
        return [[9]] if grid == [[3]] else [row[:] for row in grid]

    fake = SimpleNamespace(
        VERSION="fake",
        RULE_HASH="fake-rule",
        generate=generate,
        rule_mirror=intended,
        self_check=lambda grid: [],
        strict_canonical_like=lambda grid: [],
        observe_overrides=lambda grid: {"scene_profile": "one"},
        LESSON_COMPETITORS={"fails_only_on_three": rival},
        lesson_identifiable=lambda demos, query: [],
    )
    report = probe.audit_schedule(
        fake,
        starts=1,
        seed=0,
        difficulties=("easy",),
    )
    assert report["passed"] is False
    assert report["counts"]["ambiguous_rotations"] == 1
    finding = next(row for row in report["failures"] if row["kind"] == "rival_ambiguity")
    assert finding["query_offset"] == 3
    assert finding["rival"] == "fails_only_on_three"
    assert finding["rival_query_output"] == [[9]]

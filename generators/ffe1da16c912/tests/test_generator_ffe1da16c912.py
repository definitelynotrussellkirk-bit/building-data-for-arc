"""Focused semantic and distribution regressions for ffe1da16c912."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest

TASK_ID = "ffe1da16c912"
REPO_ROOT = Path(__file__).resolve().parents[3]
GEN_PATH = REPO_ROOT / "generators" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator", GEN_PATH
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_record():
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise AssertionError("canonical record missing")


def _pair(seed: int, sample_index: int, difficulty: str):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_is_pinned_to_selected_authority():
    assert GEN.RULE_HASH == "c4020b613ba0"


def test_canonical_inputs_are_accepted_and_python_mirror_matches_outputs():
    record = _canonical_record()
    pairs = record["train"] + [record["test"]]
    assert len(pairs) == 3
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        original = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]
        assert grid == original


def test_unknown_overrides_and_unknown_difficulty_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, difficulty="medium", typo_axis=7)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="impossible")


@pytest.mark.parametrize("cell_count", [4, 5, 6])
@pytest.mark.parametrize("match_index", [0, 1, 2])
@pytest.mark.parametrize("transform", ["id", "r1", "r2", "r3", "fh", "fv", "tr", "atr"])
def test_exact_axes_are_observable(cell_count, match_index, transform):
    requested = {
        "cell_count": cell_count,
        "match_index": match_index,
        "transform": transform,
    }
    grid = GEN.generate(901, 17, difficulty="hard", **requested)
    assert GEN.self_check(grid, meta={"overrides": requested}) == []
    assert GEN.observe_overrides(grid) == requested


def test_default_difficulty_bands_have_distinct_observable_complexity():
    observed = {
        band: GEN.observe_overrides(GEN.generate(55, 7, difficulty=band))["cell_count"]
        for band in ("easy", "medium", "hard")
    }
    assert observed == {"easy": 4, "medium": 5, "hard": 6}


def test_generated_inputs_break_count_and_fixed_panel_shortcuts():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = GEN.generate(4000 + sample_index, sample_index, difficulty=band)
            facts = GEN.semantic_observables(grid)
            assert facts["errors"] == []
            assert len(set(facts["prototype_counts"])) == 1
            assert facts["matched_transform_count"] == 1
            assert facts["query_color"] not in facts["prototype_colors"]
            assert GEN.self_check(grid) == []

        demos = [_pair(77_000, i, band) for i in range(3)]
        assert {GEN.observe_overrides(pair["input"])["match_index"] for pair in demos} == {0, 1, 2}
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name
        assert GEN.lesson_identifiable(demos, _pair(77_000, 3, band)) == []


def test_schedule_covers_all_match_transform_profiles():
    observed = {
        GEN.schedule_profile(123, sample_index, "medium")
        for sample_index in range(24)
    }
    assert observed == set(GEN.SCHEDULE_PROFILES)


def test_strongest_canonical_demo_shortcut_fits_train_but_fails_test():
    record = _canonical_record()
    shortcut = GEN.CANONICAL_SHORTCUTS["same_count_leftmost"]
    for pair in record["train"]:
        assert shortcut(pair["input"]) == pair["output"]
    assert shortcut(record["test"]["input"]) != record["test"]["output"]
    assert GEN.rule_mirror(record["test"]["input"]) == record["test"]["output"]


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(1927)
    before = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(42, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second

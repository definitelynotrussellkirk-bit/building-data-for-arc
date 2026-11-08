from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve()
TASK_ID = "5e0575c16ab4"

if (HERE.parent.parent / "generator.py").is_file():
    REPO = HERE.parents[3]
    RUNTIME_ROOT = REPO / "shared" / "runtime"
    GENERATOR_PATH = HERE.parent.parent / "generator.py"
else:
    REPO = HERE.parents[1]
    RUNTIME_ROOT = REPO
    GENERATOR_PATH = REPO / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"

sys.path.insert(0, str(RUNTIME_ROOT))

spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}_generator", GENERATOR_PATH)
assert spec and spec.loader
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def canonical_row() -> dict:
    path = (
        REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
        if (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").is_file()
        else REPO / "data" / "canonical" / "puzzles.jsonl"
    )
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical task missing")


def test_rule_pin_and_python_mirror_match_every_canonical_pair():
    row = canonical_row()
    normalized = " ".join(row["program_solution"].split())
    expected_hash = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert expected_hash == "8cad321146ee"
    assert generator.RULE_HASH == expected_hash

    for pair in row["train"] + [row["test"]]:
        before = [line[:] for line in pair["input"]]
        assert generator.self_check(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before

import random

import pytest
from puzzle_generators import base


def frozen(grid):
    return tuple(tuple(row) for row in grid)


@pytest.mark.parametrize(
    "profile",
    ["canonical", "global_repeat", "blocked_bridge", "count_alignment"],
)
def test_each_profile_override_is_lawful_exact_and_observable(profile):
    grid = generator.generate(
        91,
        17,
        difficulty="hard",
        grid_h=5,
        grid_w=7,
        positive_pairs=2,
        profile=profile,
    )
    assert generator.self_check(grid) == []
    assert generator.observe_overrides(grid) == {
        "grid_h": 5,
        "grid_w": 7,
        "positive_pairs": 2,
        "profile": profile,
    }
    assert generator.rule_mirror(grid) != grid

    facts = generator.semantic_observables(grid)
    expected_branch = {
        "canonical": not facts["negative_branches"],
        "global_repeat": bool(facts["repeated_pair_colors"]),
        "blocked_bridge": bool(facts["blocked_pair_colors"]),
        "count_alignment": bool(facts["vertical_pair_colors"] and facts["triple_colors"]),
    }
    assert expected_branch[profile]


def test_generated_counterexamples_refute_every_declared_canonical_shortcut():
    row = canonical_row()
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        assert all(
            rival(pair["input"]) == pair["output"]
            for pair in row["train"] + [row["test"]]
        ), name

    witnesses = {
        "row_local_pairs": "global_repeat",
        "ignore_blank_guard": "blocked_bridge",
        "connect_vertical_pairs": "count_alignment",
        "row_extremes_for_repeated_color": "count_alignment",
    }
    for rival_name, profile in witnesses.items():
        grid = generator.generate(712, 8, profile=profile)
        truth = generator.rule_mirror(grid)
        assert generator.SEMANTIC_RIVALS[rival_name](grid) != truth


def test_every_four_example_window_contains_all_profiles_and_is_identifiable():
    for start in range(16):
        demos = []
        profiles = []
        for sample_index in range(start, start + generator.EXAMPLES_NEEDED):
            grid = generator.generate(808, sample_index, difficulty="medium")
            profiles.append(generator.semantic_observables(grid)["profile"])
            demos.append({"input": grid, "output": generator.rule_mirror(grid)})
        query_grid = generator.generate(808, start + generator.EXAMPLES_NEEDED, difficulty="medium")
        assert set(profiles) == set(generator.SCHEDULE_PROFILES)
        assert generator.lesson_identifiable(demos, {"input": query_grid}) == []


def test_every_band_has_canonical_profile_anchor_at_each_schedule_cycle():
    for band in ("easy", "medium", "hard"):
        for start in range(0, 20, 4):
            grid = generator.generate(5150, start, difficulty=band)
            facts = generator.semantic_observables(grid)
            assert facts["profile"] == "canonical"
            assert len(grid) in {5, 8}
            assert len(grid[0]) in {7, 8, 9}
            assert facts["positive_pairs"] == 2


def test_exact_overrides_reject_unknown_and_out_of_range_values():
    bad = [
        {"grid_h": 4},
        {"grid_h": 15},
        {"grid_w": 6},
        {"grid_w": 19},
        {"positive_pairs": 0},
        {"positive_pairs": 3},
        {"profile": "unknown"},
        {"bogus": 1},
    ]
    for kwargs in bad:
        with pytest.raises((TypeError, ValueError)):
            generator.generate(0, 0, **kwargs)


def test_default_draw_provenance_matches_observed_axes():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(12):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = generator.generate(17, sample_index, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            observed = generator.observe_overrides(grid)
            drawn = captured[0].recorded_draws()
            assert {axis: drawn[axis] for axis in generator.AXES} == observed


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(12345)
    before = random.getstate()
    first = generator.generate(77, 91, difficulty="hard")
    after = random.getstate()
    second = generator.generate(77, 91, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 99
    assert second[0][0] != 99


def test_negative_controls_are_executable_but_rejected_by_self_check():
    for texture in generator.DEGENERATE_TEXTURES:
        grid = generator.generate(8, 13, difficulty="medium", texture=texture)
        assert generator.self_check(grid)
        output = generator.rule_mirror(grid)
        assert len(output) == len(grid)
        assert all(len(row) == len(grid[0]) for row in output)

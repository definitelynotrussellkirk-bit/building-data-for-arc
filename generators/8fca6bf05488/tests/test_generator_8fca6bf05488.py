from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import sys
from itertools import product
from pathlib import Path

import pytest


HERE = Path(__file__).resolve()
TASK_ID = "8fca6bf05488"

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

from puzzle_generators import base  # noqa: E402


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


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    test = row["test"]
    return row["train"] + (test if isinstance(test, list) else [test])


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def palette_size(grid) -> int:
    return len({value for row in grid for value in row})


def test_rule_pin_and_python_mirror_match_every_canonical_pair():
    row = canonical_row()
    normalized = " ".join(row["program_solution"].split())
    expected_hash = hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert expected_hash == "fe26cc0d2dfe"
    assert generator.RULE_HASH == expected_hash

    for pair in canonical_pairs():
        before = frozen(pair["input"])
        assert generator.self_check(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert frozen(pair["input"]) == before


def test_every_exact_override_combination_is_constructive_and_observable():
    domains = product(
        (6, 12),
        (7, 12),
        (2, 4),
        ("low", "high"),
        ("canonical", "stacked", "bottom_boundary", "repeated_color"),
    )
    for index, (h, w, emitters, palette_kind, profile) in enumerate(domains):
        grid = generator.generate(
            91,
            index,
            difficulty="hard",
            grid_h=h,
            grid_w=w,
            emitters=emitters,
            palette_kind=palette_kind,
            profile=profile,
        )
        assert generator.self_check(grid) == []
        assert generator.observe_overrides(grid) == {
            "grid_h": h,
            "grid_w": w,
            "emitters": emitters,
            "palette_kind": palette_kind,
            "profile": profile,
        }
        assert generator.rule_mirror(grid) != grid


def test_profiles_expose_the_intended_branch_without_overlap():
    expected = {
        "canonical": {"stacked_columns": 0, "bottom_emitters": 0, "repeated_colors": 0},
        "stacked": {"stacked_columns": 1, "bottom_emitters": 0, "repeated_colors": 0},
        "bottom_boundary": {"stacked_columns": 0, "bottom_emitters": 1, "repeated_colors": 0},
        "repeated_color": {"stacked_columns": 0, "bottom_emitters": 0, "repeated_colors": 1},
    }
    for profile, branch in expected.items():
        grid = generator.generate(123, 7, emitters=4, profile=profile)
        facts = generator.semantic_observables(grid)
        assert facts["profile"] == profile
        for key, value in branch.items():
            assert facts[key] == value


def test_generated_profiles_refute_every_canonical_fitting_shortcut():
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name

    witnesses = {
        "topmost_per_column": "stacked",
        "unique_colors_only": "repeated_color",
        "drop_bottom_sources": "bottom_boundary",
    }
    for rival_name, profile in witnesses.items():
        grid = generator.generate(712, 8, profile=profile)
        truth = generator.rule_mirror(grid)
        assert generator.SEMANTIC_RIVALS[rival_name](grid) != truth


def test_every_four_example_window_covers_profiles_and_is_identifiable():
    for start in range(12):
        demos = []
        profiles = []
        for sample_index in range(start, start + generator.EXAMPLES_NEEDED):
            grid = generator.generate(808, sample_index, difficulty="medium")
            profiles.append(generator.semantic_observables(grid)["profile"])
            demos.append({"input": grid, "output": generator.rule_mirror(grid)})
        query = generator.generate(808, start + generator.EXAMPLES_NEEDED, difficulty="medium")
        assert set(profiles) == set(generator.SCHEDULE_PROFILES)
        assert generator.lesson_identifiable(demos, {"input": query}) == []


def test_each_band_has_repeated_canonical_profile_anchors():
    canonical_profiles = {(6, 10, 3), (7, 8, 3), (9, 7, 3)}
    for band in ("easy", "medium", "hard"):
        hits = 0
        for sample_index in range(20):
            grid = generator.generate(5150, sample_index, difficulty=band)
            if generator.semantic_observables(grid)["profile"] == "canonical":
                hits += (len(grid), len(grid[0]), palette_size(grid)) in canonical_profiles
        assert hits >= 5


def test_exact_overrides_reject_unknown_out_of_range_and_bad_types():
    bad = [
        {"grid_h": 5},
        {"grid_h": 13},
        {"grid_w": 6},
        {"grid_w": 13},
        {"emitters": 1},
        {"emitters": 5},
        {"palette_kind": "mixed"},
        {"profile": "unknown"},
        {"emitters": "3"},
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


def test_self_check_rejects_the_short_horizontal_impostor():
    grid = [[0] * 7 for _ in range(6)]
    grid[2][1] = 2
    grid[2][5] = 7
    assert generator.self_check(grid)


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

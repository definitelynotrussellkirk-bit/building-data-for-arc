"""Focused regressions for the left-header row-flood generator repair."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "8862a204ce3a"
ROOT = find_root(__file__)
HOME = next(
    path
    for path in (
        ROOT / "generators" / TASK_ID,
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID,
    )
    if (path / "generator.py").is_file()
)
SPEC = importlib.util.spec_from_file_location(
    "reviewed_8862a204ce3a_tests", HOME / "generator.py"
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical task row missing")


def _reference_output(grid):
    width = len(grid[0])
    return [[row[0]] * width if row[0] else [0] * width for row in grid]


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": _reference_output(grid)}


def test_rule_pin_and_all_canonical_pairs_are_owned():
    expected = hashlib.sha256(
        " ".join(_canonical_program().split()).encode()
    ).hexdigest()[:12]
    assert GEN.RULE_HASH == expected == "067caed98cc7"
    assert len(PAIRS) == 5
    for pair in PAIRS:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert _reference_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_constructive_and_observable(band):
    for scene_profile in GEN.SCENE_PROFILES:
        for row_layout in GEN.ROW_LAYOUTS:
            grid = GEN.generate(
                20261007,
                13,
                difficulty=band,
                scene_profile=scene_profile,
                row_layout=row_layout,
            )
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == {
                "scene_profile": scene_profile,
                "row_layout": row_layout,
            }


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"scene_profile": "missing"},
        {"scene_profile": 3},
        {"row_layout": "diagonal"},
        {"row_layout": True},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


def test_default_schedule_alternates_clean_anchors_and_counterexamples():
    assert GEN.EXAMPLES_NEEDED == 3
    assert tuple(GEN.SCHEDULE_PROFILES) == ("canonical", "contrast")
    for band in ("easy", "medium", "hard"):
        for start in range(10):
            profiles = [
                GEN.schedule_profile(91, start + offset, difficulty=band)
                for offset in range(4)
            ]
            assert profiles.count("canonical") == 2
            assert profiles.count("contrast") == 2

            grids = [GEN.generate(91, start + offset, difficulty=band) for offset in range(4)]
            for offset, grid in enumerate(grids):
                if profiles[offset] == "canonical":
                    assert GEN.strict_canonical_like(grid) == []
                else:
                    assert GEN.SEMANTIC_WITNESSES["zero_header_noise"](grid)
                    assert GEN.SEMANTIC_WITNESSES["marker_row_conflict"](grid)


def test_every_three_demo_window_refutes_declared_shortcuts():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = [
                _pair(GEN.generate(700 + start, start + offset, difficulty=band))
                for offset in range(4)
            ]
            for query_position in range(4):
                query = pairs[query_position]
                demos = [pair for index, pair in enumerate(pairs) if index != query_position]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        rival(copy.deepcopy(pair["input"])) != pair["output"]
                        for pair in demos
                    ), name


def test_semantic_witnesses_are_real_rival_counterexamples():
    grid = GEN.generate(42, 1, difficulty="medium")
    official = GEN.rule_mirror(grid)
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        assert GEN.SEMANTIC_WITNESSES[witness_name](grid)
        assert any(GEN.SEMANTIC_RIVALS[name](grid) != official for name in rival_names)
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(copy.deepcopy(pair["input"])) == pair["output"] for pair in PAIRS), name


def test_self_check_rejects_targeted_impostors():
    grid = GEN.generate(11, 1, scene_profile="broad_6x6_2", row_layout="top")

    blank = [[0 for _ in row] for row in grid]
    assert GEN.self_check(blank)

    stray_colour = copy.deepcopy(grid)
    row = next(r for r in range(len(grid)) if grid[r][0] == 0)
    stray_colour[row][1] = next(c for c in range(1, 10) if c not in {v for line in grid for v in line})
    assert GEN.self_check(stray_colour)

    duplicate_header_colour = copy.deepcopy(grid)
    markers = [r for r in range(len(grid)) if grid[r][0] != 0]
    duplicate_header_colour[markers[1]][0] = duplicate_header_colour[markers[0]][0]
    assert GEN.self_check(duplicate_header_colour)

    missing_marker = copy.deepcopy(grid)
    missing_marker[markers[0]] = [0 for _ in missing_marker[markers[0]]]
    assert GEN.self_check(missing_marker)


def test_determinism_fresh_returns_global_rng_purity_and_rule_input_purity():
    random.seed(123456)
    state = random.getstate()
    first = GEN.generate(314159, 7, difficulty="hard")
    second = GEN.generate(314159, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert random.getstate() == state

    original = copy.deepcopy(first)
    assert GEN.rule_mirror(first) == _reference_output(first)
    assert first == original


def test_difficulty_bands_are_live_and_keep_each_branch_valid():
    for seed in range(8):
        sample_index = seed
        grids = {
            band: GEN.generate(seed, sample_index, difficulty=band)
            for band in ("easy", "medium", "hard")
        }
        assert len({repr(grid) for grid in grids.values()}) == 3
        for grid in grids.values():
            assert GEN.self_check(grid) == []
            if GEN.schedule_profile(seed, sample_index) == "canonical":
                assert GEN.strict_canonical_like(grid) == []
            else:
                assert GEN.SEMANTIC_WITNESSES["zero_header_noise"](grid)
                assert GEN.SEMANTIC_WITNESSES["marker_row_conflict"](grid)


def test_retained_shortcut_counterexample_matches_declared_rivals():
    path = HOME / "counterexamples" / "overwrite_and_clear.json"
    case = json.loads(path.read_text(encoding="utf-8"))
    grid = case["input"]
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == case["observed_overrides"]
    assert GEN.rule_mirror(copy.deepcopy(grid)) == case["official_output"]
    for name, expected in case["rival_outputs"].items():
        assert GEN.LESSON_COMPETITORS[name](copy.deepcopy(grid)) == expected
        assert expected != case["official_output"]

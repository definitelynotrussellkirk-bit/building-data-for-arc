"""Regression tests for the point-reflection generator repair."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
PACKET_ROOT = REPO.parent
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_0da360b839c1", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GEN = load_generator()


def canonical_pairs():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                test = row["test"] if isinstance(row["test"], list) else [row["test"]]
                return [*row["train"], *test]
    raise AssertionError("canonical task missing")


def lesson(seed: int, start: int, difficulty: str):
    demos = []
    for offset in range(GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, start + offset, difficulty=difficulty)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(seed, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty)
    return demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}


def test_rule_hash_and_canonical_examples_are_exact():
    assert GEN.RULE_HASH == "05f942009299"
    for pair in canonical_pairs():
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_every_four_demo_window_is_identifiable_in_every_band():
    expected_profiles = set(GEN.SCHEDULE_PROFILES)
    for difficulty in ("easy", "medium", "hard"):
        for start in range(16):
            demos, query = lesson(1_000 + start, start, difficulty)
            observed = {GEN.observe_overrides(demo["input"])["layout_profile"] for demo in demos}
            assert observed == expected_profiles, (difficulty, start, observed)
            assert GEN.lesson_identifiable(demos, query) == []
            expected_outputs = [demo["output"] for demo in demos]
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != expected
                           for rival, demo, expected in [(rival, d, e) for d, e in zip(demos, expected_outputs)]), (
                    difficulty, start, name
                )


def test_every_exact_override_is_observable_and_composable():
    cases = [
        {"grid_h": 7, "grid_w": 7, "anchor_dr": -1, "anchor_dc": -1,
         "n_cells": 4, "n_colors": 2, "layout_profile": "one_side"},
        {"grid_h": 13, "grid_w": 7, "anchor_dr": 1, "anchor_dc": 1,
         "n_cells": 8, "n_colors": 3, "layout_profile": "split_side"},
        {"grid_h": 7, "grid_w": 13, "anchor_dr": -1, "anchor_dc": 1,
         "n_cells": 8, "n_colors": 2, "layout_profile": "axis_cross"},
        {"grid_h": 13, "grid_w": 13, "anchor_dr": 1, "anchor_dc": -1,
         "n_cells": 8, "n_colors": 3, "layout_profile": "swap_pair"},
    ]
    for difficulty in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = GEN.generate(77 + index, index, difficulty=difficulty, **requested)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == requested
    try:
        GEN.generate(1, 1, typo_axis=3)
    except ValueError as exc:
        assert "unknown override" in str(exc)
    else:
        raise AssertionError("unknown override was accepted")
    try:
        GEN.generate(1, 1, difficulty="impossible")
    except ValueError as exc:
        assert "difficulty" in str(exc)
    else:
        raise AssertionError("invalid difficulty was accepted")


def test_default_schedule_has_exact_canonical_profiles_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        profiles = []
        strict = 0
        for sample_index in range(12):
            grid = GEN.generate(91, sample_index, difficulty=difficulty)
            profiles.append((len(grid), len(grid[0]), len({v for row in grid for v in row})))
            strict += not GEN.strict_canonical_like(grid)
        assert {(7, 7, 4), (8, 8, 4), (9, 9, 4)} <= set(profiles)
        assert strict >= 9


def test_swap_profile_exposes_occupied_destination_shortcut():
    grid = GEN.generate(5, 3, difficulty="medium", layout_profile="swap_pair")
    cells, anchor = GEN.colored_cells_and_anchor(grid)
    ar, ac = anchor
    values = {(r, c): grid[r][c] for r, c in cells}
    pairs = [((r, c), (2 * ar - r, 2 * ac - c)) for r, c in cells
             if (2 * ar - r, 2 * ac - c) in values]
    assert pairs
    assert any(values[a] != values[b] for a, b in pairs)
    assert GEN.CANONICAL_SHORTCUTS["empty_destination_only"](grid) != GEN.rule_mirror(grid)


def test_declared_canonical_shortcuts_fit_all_public_pairs_and_have_generated_counterexamples():
    pairs = canonical_pairs()
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name
        assert any(
            shortcut(GEN.generate(123, i, difficulty=band)) != GEN.rule_mirror(
                GEN.generate(123, i, difficulty=band)
            )
            for band in ("easy", "medium", "hard")
            for i in range(4)
        ), name


def test_self_check_rejects_targeted_malformed_inputs():
    valid = GEN.generate(13, 0, difficulty="easy")
    no_anchor = copy.deepcopy(valid)
    for row in no_anchor:
        for c, value in enumerate(row):
            if value == 9:
                row[c] = 0
    assert GEN.self_check(no_anchor)

    two_anchors = copy.deepcopy(valid)
    two_anchors[0][0] = 9
    assert GEN.self_check(two_anchors)

    bad_cell = copy.deepcopy(valid)
    bad_cell[0][0] = True
    assert GEN.self_check(bad_cell)

    too_small = [row[:6] for row in valid[:6]]
    assert GEN.self_check(too_small)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(24680)
    before = random.getstate()
    first = GEN.generate(44, 7, difficulty="hard")
    other = GEN.generate(45, 8, difficulty="easy")
    second = GEN.generate(44, 7, difficulty="hard")
    after = random.getstate()
    assert before == after
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
    assert second != other

"""Focused regression tests for the hollow-3x3 marker generator repair."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.b1e8f6552b5f import generator as gen


def _canonical_path() -> Path:
    """Find the copied canonical ledger in both supported task-test layouts."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data/canonical/puzzles.jsonl"
        if candidate.is_file():
            return candidate
    raise AssertionError("portable task-test runtime is missing canonical puzzles.jsonl")


def _canonical_row() -> dict:
    with _canonical_path().open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {gen.TASK_ID}")


def _facts(grid) -> dict:
    markers = gen._marker_cells(grid)
    counts = Counter(color for _, _, color in markers)
    h, w = len(grid), len(grid[0])
    return {
        "markers": markers,
        "counts": counts,
        "touches": any(gen._ring_touches_border(r, c, h, w) for r, c, _ in markers),
        "interior": any(gen._ring_is_interior(r, c, h, w) for r, c, _ in markers),
    }


def test_rule_hash_and_every_canonical_pair() -> None:
    row = _canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert gen.RULE_HASH == hashlib.sha256(normalized.encode()).hexdigest()[:12]
    pairs = [*row["train"], *row["test"]]
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen._stamp_prediction(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_override_boundaries_are_observable_in_every_band() -> None:
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_markers"}
    cases = (
        {"grid_h": 7, "grid_w": 7, "n_markers": 2},
        {"grid_h": 7, "grid_w": 13, "n_markers": 4},
        {"grid_h": 13, "grid_w": 7, "n_markers": 4},
        {"grid_h": 13, "grid_w": 13, "n_markers": 2},
        {"grid_h": 10, "grid_w": 11, "n_markers": 3},
    )
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = gen.generate(10_000 + index, 100 + index, difficulty=band, **overrides)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == overrides


def test_unknown_and_out_of_range_overrides_reject_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, texture="warm")
    for overrides in (
        {"grid_h": 6},
        {"grid_h": 14},
        {"grid_w": 6},
        {"grid_w": 14},
        {"n_markers": 1},
        {"n_markers": 5},
    ):
        with pytest.raises((ValueError, AssertionError)):
            gen.generate(2, 0, **overrides)


def test_four_example_schedule_exposes_decisive_profiles_in_every_band() -> None:
    assert gen.EXAMPLES_NEEDED == 4
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "aligned_same_pair",
        "canonical_distinct_pair",
        "mixed_triple",
        "distinct_quad",
    )
    for band in ("easy", "medium", "hard"):
        lesson = [gen.generate(700 + i, i, difficulty=band) for i in range(4)]
        assert [gen.schedule_profile(700 + i, i, band) for i in range(4)] == list(
            gen.SCHEDULE_PROFILES
        )
        assert all(gen.self_check(grid) == [] for grid in lesson)
        first, second, third, fourth = map(_facts, lesson)
        assert len(first["markers"]) == 2 and len(first["counts"]) == 1 and first["touches"]
        assert len(second["markers"]) == 2 and len(second["counts"]) == 2
        assert not second["touches"] and second["interior"]
        assert len(third["markers"]) == 3 and len(third["counts"]) == 2
        assert third["touches"] and third["interior"]
        assert len(fourth["markers"]) == 4 and len(fourth["counts"]) == 4
        assert fourth["interior"]


def test_every_named_rival_is_refuted_by_one_four_demo_lesson() -> None:
    for band in ("easy", "medium", "hard"):
        demos = []
        for index in range(4):
            grid = gen.generate(555, index, difficulty=band)
            demos.append({"input": grid, "output": gen._stamp_prediction(grid)})
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_targeted_impostors_are_rejected() -> None:
    valid = gen.generate(999, 2, difficulty="hard")
    assert gen.self_check(valid) == []
    markers = gen._marker_cells(valid)

    blank = [[0 for _ in row] for row in valid]

    border = copy.deepcopy(valid)
    r, c, color = markers[0]
    border[r][c] = 0
    border[0][c] = color

    overlapping = copy.deepcopy(valid)
    r, c, color = gen._marker_cells(overlapping)[0]
    target = (r, c + 1) if c + 1 < len(overlapping[0]) - 1 else (r, c - 1)
    overlapping[target[0]][target[1]] = next(
        value for value in range(1, 10) if value != color
    )

    too_many = copy.deepcopy(valid)
    occupied = {(r, c) for r, c, _ in gen._marker_cells(too_many)}
    for r in range(1, len(too_many) - 1):
        for c in range(1, len(too_many[0]) - 1):
            if (r, c) not in occupied:
                too_many[r][c] = 9
                occupied.add((r, c))
                if len(occupied) == 5:
                    break
        if len(occupied) == 5:
            break

    invalid_color = copy.deepcopy(valid)
    invalid_color[0][0] = 10

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()

    for impostor in (blank, border, overlapping, too_many, invalid_color, ragged):
        assert gen.self_check(impostor), impostor


def test_absent_feature_recombination_is_distribution_invalid_but_oracle_defined() -> None:
    grid = gen.generate(333, 1, difficulty="medium")
    used = {value for row in grid for value in row}
    replacement = next(color for color in range(1, 10) if color not in used)
    mutated = copy.deepcopy(grid)
    r, c, _ = gen._marker_cells(mutated)[0]
    target = (r, c + 1) if c + 1 < len(mutated[0]) - 1 else (r, c - 1)
    assert mutated[target[0]][target[1]] == 0
    mutated[target[0]][target[1]] = replacement
    assert replacement not in used
    assert gen.self_check(mutated)
    output = gen._stamp_prediction(mutated)
    assert len(output) == len(mutated)
    assert len(output[0]) == len(mutated[0])
    assert any(replacement in row for row in output)


def test_determinism_fresh_returns_rng_purity_and_variation() -> None:
    state = random.getstate()
    first = gen.generate(17, 2, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(17, 2, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second

    seen = {
        json.dumps(gen.generate(seed, seed % 4, difficulty="hard"), separators=(",", ":"))
        for seed in range(80)
    }
    assert len(seen) >= 72


def test_compatible_dimension_overrides_preserve_semantic_schedule() -> None:
    """Exact size controls must not erase a still-feasible teaching profile."""
    cases = (
        (0, 0, "aligned_same_pair", {"grid_h": 7}),
        (0, 1, "canonical_distinct_pair", {"grid_h": 9}),
        (14, 2, "mixed_triple", {"grid_h": 10}),
        (1, 3, "distinct_quad", {"grid_h": 13}),
    )
    for seed, sample_index, profile, overrides in cases:
        grid = gen.generate(
            seed,
            sample_index,
            difficulty="medium",
            **overrides,
        )
        centers = tuple((r, c) for r, c, _ in gen._marker_cells(grid))
        observed = gen.observe_overrides(grid)
        assert all(observed[name] == value for name, value in overrides.items())
        assert gen._layout_ok(
            centers,
            profile=profile,
            h=len(grid),
            w=len(grid[0]),
            strict_profile=True,
        ), (profile, centers)

"""Focused regression tests for the ad6ae79cd803 generator repair."""
from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.ad6ae79cd803 import generator as gen


ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return [
                    pair["input"]
                    for split in ("train", "test")
                    for pair in row[split]
                ]
    raise AssertionError("canonical task row not found")


def _oracle_mirror(grid):
    code = gen._corner_code(grid)
    assert code is not None
    return gen._rotate_grid(gen._crop_without_marker(grid), code)


def test_rule_hash_and_canonical_inputs_are_accepted():
    assert gen.RULE_HASH == "6b203391dc52"
    canonical = _canonical_inputs()
    assert len(canonical) == 4
    for grid in canonical:
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


def test_four_consecutive_samples_cover_every_corner_code():
    for seed in (0, 17, 99991):
        observed = [
            gen.observe_overrides(
                gen.generate(seed, sample_index, difficulty="medium")
            )["corner_code"]
            for sample_index in range(20, 24)
        ]
        assert observed == [0, 1, 2, 3]


def test_exact_override_boundaries_are_observable():
    cases = (
        {"grid_h": 6, "grid_w": 7, "corner_code": 0, "motif_color": 1, "motif_size": 3},
        {"grid_h": 16, "grid_w": 17, "corner_code": 3, "motif_color": 8, "motif_size": 6},
        {"grid_h": 8, "grid_w": 10, "corner_code": 2, "motif_color": 5, "motif_size": 4},
    )
    for band in ("easy", "medium", "hard"):
        for index, expected in enumerate(cases):
            grid = gen.generate(1000 + index, index, difficulty=band, **expected)
            observed = gen.observe_overrides(grid)
            assert observed == expected
            assert gen.self_check(grid, difficulty=band, meta=expected) == []


def test_generated_motifs_are_rotation_unique_and_lawful():
    for band in ("easy", "medium", "hard"):
        for index in range(80):
            grid = gen.generate(20000 + index, index, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            positions = {(r, c) for r, c, _ in gen._motif_cells(grid)}
            assert gen._rotation_unique(positions)


def test_self_check_rejects_targeted_impostors():
    lawful = gen.generate(41, 0, difficulty="medium")
    h, w = len(lawful), len(lawful[0])

    no_marker = copy.deepcopy(lawful)
    mr, mc = next(
        (r, c)
        for r in range(h)
        for c in range(w)
        if no_marker[r][c] == 9
    )
    no_marker[mr][mc] = 0
    assert any("exactly one" in e for e in gen.self_check(no_marker))

    middle_marker = copy.deepcopy(lawful)
    middle_marker[mr][mc] = 0
    middle_marker[h // 2][w // 2] = 9
    assert any("corner" in e for e in gen.self_check(middle_marker))

    multicolor = copy.deepcopy(lawful)
    r, c, color = gen._motif_cells(multicolor)[0]
    multicolor[r][c] = 1 if color != 1 else 2
    assert any("exactly one" in e for e in gen.self_check(multicolor))

    disconnected = copy.deepcopy(lawful)
    r, c, color = gen._motif_cells(disconnected)[0]
    disconnected[r][c] = 0
    placed = False
    for rr in range(1, h - 1):
        for cc in range(1, w - 1):
            if disconnected[rr][cc] == 0 and all(
                abs(rr - ar) + abs(cc - ac) > 1
                for ar, ac, _ in gen._motif_cells(disconnected)
            ):
                disconnected[rr][cc] = color
                placed = True
                break
        if placed:
            break
    assert placed
    assert any("4-connected" in e for e in gen.self_check(disconnected))

    border_touch = copy.deepcopy(lawful)
    for r, c, _ in gen._motif_cells(border_touch):
        border_touch[r][c] = 0
    for offset, (_, _, color) in enumerate(gen._motif_cells(lawful)):
        border_touch[0][1 + offset] = color
    assert any("inside the border" in e for e in gen.self_check(border_touch))


def test_lesson_schedule_is_identifiable():
    demos = []
    for sample_index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(719, sample_index, difficulty="hard")
        demos.append({"input": grid, "output": _oracle_mirror(grid)})
    query_grid = gen.generate(719, gen.EXAMPLES_NEEDED, difficulty="hard")
    query = {"input": query_grid, "output": _oracle_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []

    missing_branch = demos[:-1]
    reasons = gen.lesson_identifiable(missing_branch, query)
    assert any("omit corner code" in reason for reason in reasons)


def test_deterministic_fresh_and_global_rng_pure():
    state_before = random.getstate()
    first = gen.generate(123456, 77, difficulty="easy")
    state_after = random.getstate()
    second = gen.generate(123456, 77, difficulty="easy")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert state_before == state_after

    first[0][0] = 7
    replay = gen.generate(123456, 77, difficulty="easy")
    assert replay == second


def test_invalid_and_unknown_overrides_fail_loudly():
    with pytest.raises(ValueError, match="outside"):
        gen.generate(0, 0, grid_h=5)
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, palette_kind="warm")

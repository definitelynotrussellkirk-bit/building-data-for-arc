"""Focused semantic regressions for generator 28119d6d0e10."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

TASK_ID = "28119d6d0e10"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_rows():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    return rows


def _pairs(row):
    pairs = list(row.get("train", []))
    test = row.get("test", [])
    if isinstance(test, dict):
        pairs.append(test)
    else:
        pairs.extend(test)
    return pairs


def _normalized_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _blank(height=8, width=9):
    return [[0] * width for _ in range(height)]


def test_generator_28119d6d0e10_accepts_all_canonical_pairs_and_matches_rule():
    rows = _canonical_rows()
    assert len(rows) == 1
    pairs = _pairs(rows[0])
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_generator_28119d6d0e10_exact_axes_and_boundaries_are_observable():
    cases = (
        dict(
            grid_h=8,
            grid_w=9,
            n_shapes=2,
            palette_kind="warm",
        ),
        dict(
            grid_h=16,
            grid_w=18,
            n_shapes=4,
            palette_kind="cool",
        ),
    )
    for index, overrides in enumerate(cases):
        grid = GEN.generate(700 + index, 900 + index, difficulty="easy", **overrides)
        assert GEN.self_check(grid, meta={"overrides": overrides}) == []
        observed = GEN.observe_overrides(grid)
        assert observed == overrides

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, texture="tied_sizes")
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(1, 2, grid_h=7)


def test_generator_28119d6d0e10_palette_axis_is_exactly_observable():
    for kind in GEN.PALETTE_KINDS:
        grid = GEN.generate(31, 47, palette_kind=kind)
        assert GEN.observe_overrides(grid)["palette_kind"] == kind
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(53, 71, layout_style="rotate_180")


def test_generator_28119d6d0e10_self_check_rejects_targeted_impostors():
    valid = GEN.generate(101, 203, n_shapes=3)
    info = GEN._analysis(valid)

    duplicate_legend = copy.deepcopy(valid)
    duplicate_legend[0][1] = duplicate_legend[0][0]

    gapped_legend = copy.deepcopy(valid)
    gapped_legend[0][1] = 0

    body_uses_legend = copy.deepcopy(valid)
    for row, col in info["components"][0]["cells"]:
        body_uses_legend[row][col] = info["legend"][0]

    separator_used = copy.deepcopy(valid)
    separator_used[1][0] = 8

    tied_sizes = _blank()
    tied_sizes[0][:3] = [1, 2, 3]
    tied_sizes[2][1] = 4
    tied_sizes[4][1] = tied_sizes[4][2] = 5
    tied_sizes[6][5] = tied_sizes[6][6] = 6

    diagonal_touch = _blank()
    diagonal_touch[0][:2] = [1, 2]
    diagonal_touch[2][2] = 4
    diagonal_touch[3][3] = diagonal_touch[3][4] = 5

    repeated_body_color = _blank()
    repeated_body_color[0][:2] = [1, 2]
    repeated_body_color[2][1] = 4
    repeated_body_color[5][5] = repeated_body_color[5][6] = 4

    impostors = (
        duplicate_legend,
        gapped_legend,
        body_uses_legend,
        separator_used,
        tied_sizes,
        diagonal_touch,
        repeated_body_color,
    )
    assert len(impostors) >= 4
    for grid in impostors:
        assert GEN.self_check(grid), grid


def test_generator_28119d6d0e10_outputs_follow_size_not_position_or_body_color():
    patterns = set()
    body_color_orders = set()
    for seed in range(180):
        grid = GEN.generate(seed, seed * 17 + 3, difficulty="hard", n_shapes=4)
        info = GEN._analysis(grid)
        reading = sorted(info["components"], key=lambda component: component["first"])
        size_rank = {
            component["cells"]: rank
            for rank, component in enumerate(
                sorted(info["components"], key=lambda component: component["size"])
            )
        }
        patterns.add(tuple(size_rank[component["cells"]] for component in reading))
        body_color_orders.add(
            tuple(
                component["size"]
                for component in sorted(
                    info["components"],
                    key=lambda component: next(iter(component["colors"])),
                )
            )
        )
        output = GEN.rule_mirror(grid)
        assert output != grid
        assert output[0] == grid[0]
    assert len(patterns) >= 12
    assert len(body_color_orders) >= 12
    assert any(pattern != tuple(sorted(pattern)) for pattern in patterns)


def test_generator_28119d6d0e10_is_deterministic_fresh_and_rng_pure():
    random.seed(987654321)
    before = random.getstate()
    first = GEN.generate(123, 456, difficulty="medium")
    after = random.getstate()
    second = GEN.generate(123, 456, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_generator_28119d6d0e10_rule_pin_and_active_authorities_are_synced():
    canonical = _canonical_rows()[0]["program_solution"]
    base_path = (
        ROOT
        / "data/base/solutions/banks/56b8d7075625/M156__28119d6d0e10.json"
    )
    target = json.loads(base_path.read_text())["racket_target"]
    assert target["canonicalization_status"] == "preserved_executable_source"
    assert target["target_code"] == canonical
    assert target["raw_code"] != canonical
    assert GEN.RULE_HASH == _normalized_hash(canonical)
    assert GEN.RULE_HASH == "d1af322b3da3"

"""Focused semantic regressions for quadrant-summary generator 31e0316dace3."""
from __future__ import annotations

from collections import Counter, defaultdict
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

from puzzle_generators import base


TASK_ID = "31e0316dace3"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_row() -> dict:
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _decode_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return copy.deepcopy(grid)


def _pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [
        {"input": _decode_grid(pair["input"]), "output": _decode_grid(pair["output"])}
        for pair in [*row["train"], *test]
    ]


def _hash(source: str) -> str:
    normalized = " ".join(source.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def _freeze(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _impostors() -> dict[str, list[list[int]]]:
    valid = GEN.generate(
        91,
        12,
        difficulty="medium",
        half_h=4,
        half_w=4,
        base_cells=2,
        mass_profile="uniform",
        component_pattern="connected",
        empty_quadrant="none",
    )
    analysis = GEN._analysis(valid)
    assert analysis is not None

    multi_color = copy.deepcopy(valid)
    first_color = next(iter(analysis["colors"][0]))
    replacement = next(
        color for color in range(1, 10)
        if color != first_color
        and all(color not in colors for colors in analysis["colors"])
    )
    r0, r1, c0, c1 = GEN._quadrants(len(valid), len(valid[0]))[0]
    zero = next(
        (r, c)
        for r in range(r0, r1)
        for c in range(c0, c1)
        if multi_color[r][c] == 0
    )
    multi_color[zero[0]][zero[1]] = replacement

    duplicate_color = copy.deepcopy(valid)
    second_color = next(iter(analysis["colors"][1]))
    for r, c in analysis["cells"][1]:
        duplicate_color[r][c + len(valid[0]) // 2] = first_color
    assert second_color != first_color

    two_empty = copy.deepcopy(valid)
    for quadrant_index in (0, 1):
        qr0, qr1, qc0, qc1 = GEN._quadrants(
            len(valid), len(valid[0])
        )[quadrant_index]
        for r in range(qr0, qr1):
            for c in range(qc0, qc1):
                two_empty[r][c] = 0

    singleton = copy.deepcopy(valid)
    qr0, qr1, qc0, qc1 = GEN._quadrants(len(valid), len(valid[0]))[2]
    colored = [
        (r, c)
        for r in range(qr0, qr1)
        for c in range(qc0, qc1)
        if singleton[r][c] != 0
    ]
    for r, c in colored[1:]:
        singleton[r][c] = 0

    odd_height = [row[:] for row in valid[:-1]]
    return {
        "multi_color_quadrant": multi_color,
        "duplicate_quadrant_color": duplicate_color,
        "two_empty_quadrants": two_empty,
        "singleton_marker": singleton,
        "odd_height": odd_height,
    }


def test_canonical_pairs_rule_hash_and_pure_mirror() -> None:
    row = _canonical_row()
    pairs = _pairs()
    assert len(row["train"]) == 2
    assert len(pairs) == 3
    assert GEN.RULE_HASH == _hash(row["program_solution"]) == "00eaf58ae429"

    base_record = json.loads(
        (
            ROOT
            / "data/base/solutions/banks/0e5302a13aba/"
            "S5_M1__31e0316dace3.json"
        ).read_text()
    )
    assert _hash(base_record["racket_target"]["target_code"]) == GEN.RULE_HASH

    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_all_axes_are_exact_observable_and_boundaries_work() -> None:
    assert set(GEN.AXES) == {
        "half_h",
        "half_w",
        "base_cells",
        "mass_profile",
        "component_pattern",
        "empty_quadrant",
    }
    boundary_cases = [
        {"half_h": 3},
        {"half_h": 7},
        {"half_w": 3},
        {"half_w": 7},
        {"base_cells": 2},
        {"base_cells": 3},
        *({"mass_profile": value} for value in GEN.MASS_PROFILES),
        *(
            {"component_pattern": value}
            for value in GEN.COMPONENT_PATTERNS
        ),
        *({"empty_quadrant": value} for value in GEN.EMPTY_QUADRANTS),
        {
            "half_h": 3,
            "half_w": 7,
            "base_cells": 3,
            "mass_profile": "zigzag",
            "component_pattern": "split",
            "empty_quadrant": "bottom_left",
        },
    ]
    for band in ("easy", "medium", "hard"):
        for case in boundary_cases:
            for seed in range(5):
                grid = GEN.generate(
                    seed + 300,
                    seed * 19 + 7,
                    difficulty=band,
                    **case,
                )
                observed = GEN.observe_overrides(grid)
                assert GEN.self_check(grid) == []
                for axis, requested in case.items():
                    assert observed[axis] == requested

    invalid = [
        {"half_h": 2},
        {"half_w": 8},
        {"base_cells": 1},
        {"mass_profile": "reverse"},
        {"component_pattern": "three_way"},
        {"empty_quadrant": "center"},
        {"unclaimed_axis": 1},
    ]
    for case in invalid:
        with pytest.raises(ValueError):
            GEN.generate(1, 2, difficulty="easy", **case)


def test_easy_max_dimension_regression_witness() -> None:
    """The baseline rejected declared half_h/half_w=7 in the easy band."""
    grid = GEN.generate(
        17,
        9,
        difficulty="easy",
        half_h=7,
        half_w=7,
    )
    assert (len(grid), len(grid[0])) == (14, 14)
    assert GEN.observe_overrides(grid)["half_h"] == 7
    assert GEN.observe_overrides(grid)["half_w"] == 7


def test_ordinary_keyed_draws_match_returned_grid() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(80):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(
                    seed + 900,
                    seed * 37 + 11,
                    difficulty=band,
                )
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            observed = GEN.observe_overrides(grid)
            draws = captured[0].recorded_draws()
            assert set(draws) >= set(GEN.AXES)
            for axis in GEN.AXES:
                assert draws[axis] == observed[axis]


def test_linked_semantic_census_and_branch_support() -> None:
    for band in ("easy", "medium", "hard"):
        inputs = set()
        outputs = set()
        support = defaultdict(Counter)
        matches = 0
        for seed in range(240):
            grid = GEN.generate(
                seed + 5000,
                seed * 41 + 13,
                difficulty=band,
            )
            output = GEN.rule_mirror(grid)
            observed = GEN.observe_overrides(grid)
            analysis = GEN._analysis(grid)
            assert analysis is not None
            linked = (
                GEN.self_check(grid) == []
                and len(output) == 2
                and all(len(row) == 2 for row in output)
                and output
                == [
                    [
                        0 if not analysis["colors"][0]
                        else next(iter(analysis["colors"][0])),
                        0 if not analysis["colors"][1]
                        else next(iter(analysis["colors"][1])),
                    ],
                    [
                        0 if not analysis["colors"][2]
                        else next(iter(analysis["colors"][2])),
                        0 if not analysis["colors"][3]
                        else next(iter(analysis["colors"][3])),
                    ],
                ]
                and sum(value == 0 for row in output for value in row) <= 1
            )
            matches += int(linked)
            for axis, value in observed.items():
                support[axis][value] += 1
            inputs.add(_freeze(grid))
            outputs.add(_freeze(output))

        assert matches == 240
        assert set(support["mass_profile"]) == set(GEN.MASS_PROFILES)
        assert set(support["component_pattern"]) == set(
            GEN.COMPONENT_PATTERNS
        )
        assert set(support["empty_quadrant"]) == set(GEN.EMPTY_QUADRANTS)
        assert set(support["base_cells"]) == {2, 3}
        assert min(support["half_h"]) >= 3 and max(support["half_h"]) <= 7
        assert min(support["half_w"]) >= 3 and max(support["half_w"]) <= 7
        assert len(inputs) >= 235
        assert len(outputs) >= 180


def test_three_example_schedule_exposes_rule_relevant_variation() -> None:
    for start in range(30):
        observed = [
            GEN.observe_overrides(GEN.generate(29, start + offset))
            for offset in range(3)
        ]
        assert len({item["empty_quadrant"] for item in observed}) == 3
        assert {item["component_pattern"] for item in observed} == {
            "connected",
            "split",
        }
        assert {item["mass_profile"] for item in observed} == set(
            GEN.MASS_PROFILES
        )


def test_shortcut_rebuttals_have_count_matched_color_changes() -> None:
    groups: dict[tuple, set[tuple]] = defaultdict(set)
    component_outputs: dict[str, set[tuple]] = defaultdict(set)
    for seed in range(400):
        grid = GEN.generate(seed + 7000, seed * 29 + 5, difficulty="medium")
        observed = GEN.observe_overrides(grid)
        output = _freeze(GEN.rule_mirror(grid))
        key = (
            observed["half_h"],
            observed["half_w"],
            observed["base_cells"],
            observed["mass_profile"],
            observed["empty_quadrant"],
        )
        groups[key].add(output)
        component_outputs[observed["component_pattern"]].add(output)

    # Same dimensions/count profile can demand different color answers, so a
    # count-only or fixed-position answer cannot solve the generated lessons.
    assert any(len(values) >= 3 for values in groups.values())
    # Both connected and split textures realize many answers, so texture is not
    # an answer label or an oracle shortcut.
    assert all(len(values) >= 60 for values in component_outputs.values())


def test_self_check_rejects_targeted_impostors_but_oracle_can_execute() -> None:
    impostors = _impostors()
    for name, grid in impostors.items():
        errors = GEN.self_check(grid)
        assert errors, name
        # Lesson-grammar rejection and oracle executability are separate facts.
        if name != "odd_height":
            output = GEN.rule_mirror(grid)
            assert len(output) == 2 and all(len(row) == 2 for row in output)


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(20260724)
    state = random.getstate()
    first = GEN.generate(101, 37, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(101, 37, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
    before = copy.deepcopy(second)
    GEN.rule_mirror(second)
    assert second == before

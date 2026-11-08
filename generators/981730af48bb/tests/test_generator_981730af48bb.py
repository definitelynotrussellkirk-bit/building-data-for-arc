from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.981730af48bb.generator"
)
ROOT = find_root(__file__)


def _canonical_record():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def _canonical_pairs():
    return canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)


def _lesson(seed: int, start: int, difficulty: str):
    pairs = []
    for index in range(start, start + gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, index, difficulty=difficulty)
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    return pairs


def test_rule_hash_canonical_acceptance_and_python_mirror():
    row = _canonical_record()
    normalized = " ".join(row["program_solution"].split())
    assert gen.RULE_HASH == hashlib.sha256(normalized.encode()).hexdigest()[:12]
    assert gen.RULE_HASH == "250fc3187c8a"

    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert gen.observe_overrides(source)["span_profile"] == "canonical"
        assert source == pair["input"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 4, "grid_w": 6, "pairs": 2, "span_profile": "short"},
        {"grid_h": 4, "grid_w": 6, "pairs": 4, "span_profile": "wide"},
        {"grid_h": 12, "grid_w": 16, "pairs": 2, "span_profile": "wide"},
        {"grid_h": 12, "grid_w": 16, "pairs": 4, "span_profile": "short"},
    ],
)
def test_boundary_overrides_are_exact_in_every_band(difficulty, overrides):
    grid = gen.generate(812, 37, difficulty=difficulty, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides
    assert gen.rule_mirror(grid) != grid
    assert grid == gen.generate(812, 37, difficulty=difficulty, **overrides)


def test_unknown_invalid_and_legacy_dead_overrides_are_rejected():
    for overrides in (
        {"misspelled_axis": 1},
        {"texture": "warm"},
        {"palette_kind": "cool"},
        {"density": "sparse"},
        {"grid_h": 3},
        {"grid_h": 13},
        {"grid_w": 5},
        {"grid_w": 17},
        {"pairs": 0},
        {"pairs": 1},
        {"pairs": 5},
        {"span_profile": "alternating"},
        {"grid_h": True},
        {"span_profile": 2},
    ):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 2, **overrides)


def test_full_advertised_override_cross_product_is_constructive():
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (4, 8, 12):
            for grid_w in (6, 11, 16):
                for pairs in range(2, 5):
                    for span_profile in gen.SPAN_PROFILES:
                        overrides = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "pairs": pairs,
                            "span_profile": span_profile,
                        }
                        grid = gen.generate(
                            9000 + grid_h + grid_w + pairs,
                            19,
                            difficulty=difficulty,
                            **overrides,
                        )
                        assert gen.self_check(grid) == []
                        assert gen.observe_overrides(grid) == overrides


def test_default_schedule_covers_canonical_profiles_and_teaching_axes_per_band():
    canonical_shapes = {(5, 7), (4, 6), (5, 8)}
    for difficulty in ("easy", "medium", "hard"):
        rows = []
        grids = []
        for index in range(20):
            grid = gen.generate(411, index, difficulty=difficulty)
            grids.append(grid)
            rows.append(gen.observe_overrides(grid))
        assert any(
            (row["grid_h"], row["grid_w"]) in canonical_shapes
            and row["pairs"] == 2
            and len({value for line in grid for value in line if value}) == 2
            for row, grid in zip(rows, grids)
        )
        assert {row["span_profile"] for row in rows} == set(gen.SPAN_PROFILES)
        assert any(
            len({
                cells[1][0] - cells[0][0]
                for line in grid
                if len(cells := [(c, v) for c, v in enumerate(line) if v]) == 2
            }) >= 2
            for grid in grids
        )
        assert all(row["pairs"] >= 2 for row in rows)
        assert all(
            len({value for line in grid for value in line if value}) >= 2
            for grid in grids
        )


def test_canonical_span_override_is_exact_and_canonical_scale():
    assert gen.AXES["pairs"]["valid"] == "2..4"
    assert "canonical" in gen.SPAN_PROFILES
    for pairs in (2, 4):
        grid = gen.generate(
            2026,
            31,
            difficulty="hard",
            grid_h=5,
            grid_w=8,
            pairs=pairs,
            span_profile="canonical",
        )
        observed = gen.observe_overrides(grid)
        assert observed == {
            "grid_h": 5,
            "grid_w": 8,
            "pairs": pairs,
            "span_profile": "canonical",
        }
        spans = []
        for row in grid:
            cells = [c for c, value in enumerate(row) if value]
            if cells:
                spans.append(cells[1] - cells[0])
        assert 2 in spans
        assert 4 in spans


def test_every_three_of_four_consecutive_pairs_refute_named_competitors():
    assert "reuse_first_row_half_span" in gen.LESSON_COMPETITORS
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = _lesson(1301 + start, start, difficulty)
            for query_index in range(len(pairs)):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(
                        rival(copy.deepcopy(pair["input"])) != pair["output"]
                        for pair in demos
                    ), (difficulty, start, query_index, name)


def test_semantic_witnesses_are_generated_counterexamples():
    grids = [gen.generate(42, index, difficulty="medium") for index in range(16)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), witness_name
    for rival_name, rival in gen.SEMANTIC_RIVALS.items():
        assert any(
            rival(copy.deepcopy(grid)) != gen.rule_mirror(grid)
            for grid in grids
        ), rival_name


def test_rule_mirror_places_only_same_color_integer_midpoints():
    grid = gen.generate(
        77,
        3,
        grid_h=8,
        grid_w=11,
        pairs=4,
        span_profile="wide",
    )
    output = gen.rule_mirror(grid)
    for r, row in enumerate(grid):
        endpoints = [(c, value) for c, value in enumerate(row) if value]
        if not endpoints:
            assert all(value == 0 for value in output[r])
            continue
        assert len(endpoints) == 2
        (left, color), (right, same_color) = endpoints
        assert color == same_color
        expected = [0] * len(row)
        expected[(left + right) // 2] = color
        assert output[r] == expected


def test_self_check_rejects_rule_hiding_mutations_and_bad_cells():
    grid = gen.generate(
        77,
        3,
        grid_h=8,
        grid_w=11,
        pairs=4,
        span_profile="wide",
    )
    cases = [
        [],
        [[0]],
        [[True] * 6 for _ in range(4)],
        [[10] * 6 for _ in range(4)],
        [[0] * 6 for _ in range(4)],
    ]
    ragged = copy.deepcopy(grid)
    ragged[0].pop()
    cases.append(ragged)

    mismatched = copy.deepcopy(grid)
    active_row = next(r for r, row in enumerate(mismatched) if any(row))
    cols = [c for c, value in enumerate(mismatched[active_row]) if value]
    mismatched[active_row][cols[1]] = (
        mismatched[active_row][cols[0]] % 9
    ) + 1
    cases.append(mismatched)

    odd_span = copy.deepcopy(grid)
    active_row = next(r for r, row in enumerate(odd_span) if any(row))
    cols = [c for c, value in enumerate(odd_span[active_row]) if value]
    color = odd_span[active_row][cols[0]]
    odd_span[active_row][cols[1]] = 0
    odd_span[active_row][cols[1] - 1] = color
    cases.append(odd_span)

    three_cells = copy.deepcopy(grid)
    active_row = next(r for r, row in enumerate(three_cells) if any(row))
    free = next(c for c, value in enumerate(three_cells[active_row]) if value == 0)
    three_cells[active_row][free] = next(value for value in three_cells[active_row] if value)
    cases.append(three_cells)

    for case in cases:
        assert gen.self_check(case)


def test_replay_is_fresh_deterministic_and_global_rng_pure():
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

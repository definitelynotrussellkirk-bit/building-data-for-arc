from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.bcfefce862fd import generator as gen
from scripts.canonical_profile_gate import (
    canonical_pairs,
    canonical_rule_hash,
)


def _episode(seed: int, start: int, band: str = "medium"):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, start + offset, difficulty=band)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=band)
    return demos, {"input": query_grid, "output": gen.rule_mirror(query_grid)}


def test_bcfefce862fd_rule_hash_and_canonical_pairs():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID)
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_bcfefce862fd_exact_overrides_round_trip_and_unknown_rejects():
    cases = (
        {
            "grid_h": 7,
            "grid_w": 7,
            "rect_height": 3,
            "rect_width": 3,
            "marker_color": 1,
            "diagonal": "main",
            "placement": "interior",
        },
        {
            "grid_h": 10,
            "grid_w": 12,
            "rect_height": 5,
            "rect_width": 5,
            "marker_color": 9,
            "diagonal": "anti",
            "placement": "right",
        },
        {
            "grid_h": 8,
            "grid_w": 11,
            "rect_height": 5,
            "rect_width": 3,
            "marker_color": 6,
            "diagonal": "main",
            "placement": "top",
        },
    )
    for band in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = gen.generate(400 + index, index, difficulty=band, **requested)
            assert gen.observe_overrides(grid) == requested
            assert gen.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __override_contract_unknown_axis__=1)


def test_bcfefce862fd_self_check_rejects_targeted_impostors():
    valid = gen.generate(77, 0, difficulty="medium")
    info = gen.observe_overrides(valid)
    markers = [
        (r, c)
        for r, row in enumerate(valid)
        for c, value in enumerate(row)
        if value != 0
    ]
    assert len(markers) == 2

    blank = [[0 for _ in row] for row in valid]
    assert gen.self_check(blank)

    single = copy.deepcopy(valid)
    r2, c2 = markers[1]
    single[r2][c2] = 0
    assert gen.self_check(single)

    extra = copy.deepcopy(valid)
    extra[0][0] = info["marker_color"]
    assert gen.self_check(extra)

    mismatched = copy.deepcopy(valid)
    mismatched[r2][c2] = 1 if info["marker_color"] != 1 else 2
    assert gen.self_check(mismatched)

    collinear = [[0 for _ in row] for row in valid]
    r1, c1 = markers[0]
    collinear[r1][c1] = info["marker_color"]
    collinear[r1][min(len(valid[0]) - 1, c1 + 2)] = info["marker_color"]
    assert gen.self_check(collinear)

    invalid_color = copy.deepcopy(valid)
    r1, c1 = markers[0]
    invalid_color[r1][c1] = 10
    assert gen.self_check(invalid_color)

    # A 2x2 rectangle is authority-lawful even though ordinary generated
    # lessons use >=3 spans to expose a solid interior and refute outline-only.
    lawful_small = [[4, 0], [0, 4]]
    assert gen.self_check(lawful_small) == []
    assert gen.rule_mirror(lawful_small) == [[4, 4], [4, 4]]
    assert gen.strict_canonical_like(lawful_small)


def test_bcfefce862fd_deterministic_fresh_and_global_rng_pure():
    random.seed(981723)
    before = random.getstate()
    first = gen.generate(123, 9, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(123, 9, difficulty="hard")
    after = random.getstate()
    assert before == middle == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_bcfefce862fd_every_schedule_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(40):
            demos, query = _episode(seed=1701, start=start, band=band)
            assert gen.lesson_identifiable(demos, query) == []


def test_bcfefce862fd_named_rivals_fit_biased_demos_then_die_on_witness():
    seed = 9091
    cases = {
        # sample 0 is 3x3 and sample 3 is 4x4; sample 1 is tall.
        "square_only": ([0, 3], 1),
        # even samples 0 and 2 use low colors 1 and 2; sample 1 uses color 3.
        "low_color_only": ([0, 2], 1),
        # placements 1 and 2 are top/bottom; placement 3 is left.
        "horizontal_edge_only": ([1, 2], 3),
    }
    for name, (demo_indices, witness_index) in cases.items():
        rival = gen.SEMANTIC_RIVALS[name]
        for sample_index in demo_indices:
            grid = gen.generate(seed, sample_index, difficulty="medium")
            assert rival(grid) == gen.rule_mirror(grid)
        witness = gen.generate(seed, witness_index, difficulty="medium")
        assert rival(witness) != gen.rule_mirror(witness)

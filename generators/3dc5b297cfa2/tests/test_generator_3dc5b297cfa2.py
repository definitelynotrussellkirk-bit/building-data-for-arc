from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
for path in (RUNTIME,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

TASK_ID = "3dc5b297cfa2"
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
EXPECTED_RULE_HASH = "69b3b2d19383"


def canonical_pairs(task_id: str) -> list[dict]:
    pairs: list[dict] = []
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != task_id:
                continue
            pairs.extend(row.get("train") or [])
            test = row.get("test") or []
            if isinstance(test, dict):
                test = [test]
            pairs.extend(test)
    return pairs

spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def _shape_cells(grid: list[list[int]]) -> tuple[int, list[tuple[int, int]]]:
    counts: dict[int, int] = {}
    for row in grid:
        for value in row:
            counts[value] = counts.get(value, 0) + 1
    background = max(counts, key=counts.get)
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != background
    ]
    return background, cells


def _component_count(grid: list[list[int]]) -> int:
    _background, cells = _shape_cells(grid)
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
    return count


def test_rule_hash_and_all_canonical_pairs_match_the_authority_contract():
    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 6
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_override_branches_are_observable_lawful_and_connected():
    cases = [
        {
            "grid_h": 16,
            "grid_w": 16,
            "bbox_h": 8,
            "bbox_w": 5,
            "background_color": 8,
            "black_shape": True,
        },
        {
            "grid_h": 12,
            "grid_w": 16,
            "bbox_h": 4,
            "bbox_w": 3,
            "background_color": 1,
            "black_shape": False,
        },
        {
            "grid_h": 20,
            "grid_w": 24,
            "bbox_h": 8,
            "bbox_w": 7,
            "background_color": 9,
            "black_shape": False,
        },
        {
            "grid_h": 12,
            "grid_w": 16,
            "bbox_h": 4,
            "bbox_w": 7,
            "background_color": 7,
            "black_shape": False,
        },
    ]
    for difficulty in ("easy", "medium", "hard"):
        for seed, requested in enumerate(cases):
            grid = gen.generate(seed, 0, difficulty=difficulty, **requested)
            assert gen.observe_overrides(grid) == requested
            assert gen.self_check(grid, meta={"overrides": requested}) == []
            assert _component_count(grid) == 1
            assert len({value for row in grid for value in row}) == 3


def test_unknown_and_out_of_domain_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, bogus_axis=1)
    for key, value in (
        ("grid_h", 11),
        ("grid_h", 21),
        ("grid_w", 15),
        ("grid_w", 25),
        ("bbox_h", 3),
        ("bbox_h", 9),
        ("bbox_w", 2),
        ("bbox_w", 8),
        ("background_color", 0),
        ("background_color", 10),
        ("black_shape", "yes"),
    ):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(0, 0, **{key: value})


def test_black_branch_uses_nonzero_span_not_full_bbox_width():
    requested = {
        "grid_h": 16,
        "grid_w": 16,
        "bbox_h": 8,
        "bbox_w": 7,
        "background_color": 8,
        "black_shape": True,
    }
    grid = gen.generate(81, 2, difficulty="medium", **requested)
    truth = gen.rule_mirror(grid)
    assert gen._black_span_exception_witness(grid)
    assert gen._rival_full_bbox_shift(grid) != truth
    assert gen._rival_no_color_swap(grid) != truth
    assert gen._rival_move_both_halves(grid) != truth


def test_nonblack_branch_uses_full_bbox_width_and_keeps_bottom_in_place():
    requested = {
        "grid_h": 16,
        "grid_w": 16,
        "bbox_h": 6,
        "bbox_w": 5,
        "background_color": 8,
        "black_shape": False,
    }
    grid = gen.generate(91, 4, difficulty="hard", **requested)
    truth = gen.rule_mirror(grid)
    assert not gen._black_span_exception_witness(grid)
    assert gen._color_swap_witness(grid)
    assert gen._stationary_bottom_witness(grid)
    assert gen._rival_no_color_swap(grid) != truth
    assert gen._rival_move_both_halves(grid) != truth


def test_all_declared_rival_claims_are_real_on_their_witnesses():
    fired = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(24):
            grid = gen.generate(20261003, sample_index, difficulty=difficulty)
            truth = gen.rule_mirror(grid)
            assert gen.self_check(grid) == []
            for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    fired[witness_name] += 1
                    for rival_name in gen.WITNESS_RIVALS[witness_name]:
                        assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth
    assert all(count > 0 for count in fired.values()), fired


def test_determinism_fresh_returns_and_process_global_rng_purity():
    random.seed(918273)
    state = random.getstate()
    first = gen.generate(77, 5, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(77, 5, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_self_check_rejects_targeted_structural_impostors():
    valid = gen.generate(
        11,
        0,
        grid_h=16,
        grid_w=16,
        bbox_h=8,
        bbox_w=5,
        background_color=8,
        black_shape=False,
    )

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    assert any("rectangular" in reason for reason in gen.self_check(ragged))

    one_shape_color = copy.deepcopy(valid)
    background, cells = _shape_cells(one_shape_color)
    replacement = one_shape_color[cells[0][0]][cells[0][1]]
    for r, c in cells:
        one_shape_color[r][c] = replacement
    assert any("two shape colors" in reason for reason in gen.self_check(one_shape_color))

    disconnected = copy.deepcopy(valid)
    background, cells = _shape_cells(disconnected)
    r, c = cells[len(cells) // 2]
    disconnected[r][c] = background
    # Removing an interior bridge may not disconnect every silhouette, so also
    # plant an isolated shape-colored cell well outside the bounding object.
    isolated = next(
        (rr, cc)
        for rr in range(len(disconnected))
        for cc in range(len(disconnected[0]))
        if disconnected[rr][cc] == background
        and all(
            not (0 <= nr < len(disconnected) and 0 <= nc < len(disconnected[0]))
            or disconnected[nr][nc] == background
            for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1))
        )
    )
    disconnected[isolated[0]][isolated[1]] = replacement
    assert any("connected" in reason for reason in gen.self_check(disconnected))


def test_every_sliding_two_demo_window_identifies_the_rule_and_refutes_competitors():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(16):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(7000 + start, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                7000 + start,
                start + gen.EXAMPLES_NEEDED,
                difficulty=difficulty,
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name

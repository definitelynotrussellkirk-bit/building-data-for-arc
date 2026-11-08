"""Focused regression tests for generator c8f64d644ba6."""
from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.c8f64d644ba6 import generator as gen

ROOT = Path(__file__).resolve().parents[1]


def _canonical_rows():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                rows.append(row)
    return rows


def _canonical_pairs():
    for row in _canonical_rows():
        for split in ("train", "test"):
            for index, pair in enumerate(row.get(split) or []):
                yield row["content_hash"], split, index, pair


def _clear_component(grid, cells):
    out = copy.deepcopy(grid)
    for r, c in cells:
        out[r][c] = 0
    return out


def _mutations(grid):
    trace, _ = gen._placement_trace(grid)

    # 1. Remove a required support pixel above a source's first placement.
    supported = copy.deepcopy(grid)
    first = trace[0]
    pr, pc = first["placement"]
    top_cells = [cell for cell in first["shape"] if cell[0] == 0]
    _, dc = top_cells[0]
    supported[pr - 1][pc + dc] = 0

    # 2. Lift one source off the bottom row while preserving its shape.
    components = gen._components(grid, 5)
    component = min(components, key=len)
    lifted = _clear_component(grid, component)
    for r, c in component:
        lifted[r - 1][c] = 5

    # 3. Merge two bottom-anchored sources with a gray bridge.
    merged = copy.deepcopy(grid)
    ordered = sorted(components, key=lambda cells: gen._bbox(cells)[1])
    left, right = ordered[0], ordered[1]
    left_edge = max(c for r, c in left if r == len(grid) - 1)
    right_edge = min(c for r, c in right if r == len(grid) - 1)
    for c in range(left_edge + 1, right_edge):
        merged[-1][c] = 5

    # 4. Replace the smallest source with a shape absent from all sockets.
    replaced = _clear_component(grid, component)
    absent = gen._shape("###")
    assert absent not in {item["shape"] for item in trace}
    width = len(grid[0])
    occupied = {(r, c) for comp in gen._components(replaced, 5) for r, c in comp}
    placement = None
    for c0 in range(width - 2):
        cells = {(len(grid) - 1, c0 + dc) for _, dc in absent}
        if not (cells & occupied):
            placement = cells
            break
    assert placement is not None
    for r, c in placement:
        replaced[r][c] = 5

    return {
        "missing_support": supported,
        "source_off_bottom": lifted,
        "merged_sources": merged,
        "absent_recombination": replaced,
    }


def test_all_canonical_source_rows_are_owned_and_linked():
    rows = _canonical_rows()
    assert len(rows) == 2
    seen_profiles = set()
    reviewed = 0
    for _content_hash, _split, _index, pair in _canonical_pairs():
        reviewed += 1
        assert gen.self_check(pair["input"]) == []
        signature = gen.canonical_profile_signature(pair["input"])
        assert signature in gen._CANONICAL_SIGNATURES
        seen_profiles.add(signature)
        assert gen._python_apply(pair["input"]) == pair["output"]
    assert reviewed == 6
    assert seen_profiles == set(gen._CANONICAL_SIGNATURES)


def test_scheduled_lesson_covers_all_rule_branches():
    pairs = []
    for sample_index in range(4):
        grid = gen.generate(1000 + sample_index, sample_index, difficulty="medium")
        assert gen.self_check(grid) == []
        if sample_index < 3:
            assert gen.strict_canonical_like(grid) == []
        pairs.append({"input": grid, "output": gen._python_apply(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
    assert all(any(fn(pair["input"]) for pair in pairs) for fn in gen.SEMANTIC_WITNESSES.values())


def test_replay_fresh_returns_global_rng_and_override_boundaries():
    global_state = random.getstate()
    first = gen.generate(90210, 17, difficulty="hard")
    second = gen.generate(90210, 17, difficulty="hard")
    assert random.getstate() == global_state
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert gen.generate(90210, 17, difficulty="hard") == second

    for difficulty in ("easy", "medium", "hard"):
        for overrides in (
            {"grid_h": 10, "grid_w": 15, "n_shapes": 3},
            {"grid_h": 14, "grid_w": 22, "n_shapes": 4},
        ):
            grid = gen.generate(44, 99, difficulty=difficulty, **overrides)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == overrides

    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 1, difficulty="impossible")
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, bogus_axis=7)


def test_self_check_rejects_targeted_structural_impostors():
    grid = gen.generate(4242, 0, difficulty="medium")
    assert gen.self_check(grid) == []
    mutations = _mutations(grid)
    assert len(mutations) >= 4
    for name, impostor in mutations.items():
        assert gen.self_check(impostor), name


def test_canonical_profile_support_is_positive_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        matches = 0
        for index in range(40):
            grid = gen.generate(12000 + index, index, difficulty=difficulty)
            matches += not bool(gen.strict_canonical_like(grid))
        assert matches >= 10

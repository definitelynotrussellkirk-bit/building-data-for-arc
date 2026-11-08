"""Focused regression tests for generator b1af643b5c32."""
from __future__ import annotations

import copy
import random

from puzzle_generators.per_puzzle.b1af643b5c32 import generator as gen


def _scene(sample_index: int = 2):
    return gen.generate(910_000 + sample_index, sample_index, difficulty="hard")


def _blocks_and_target(grid):
    analysis = gen.analyze_scene(grid)
    assert not analysis["errors"]
    facts = analysis["facts"]
    return facts["blocks"], facts["target"]


def test_b1af643b5c32_canonical_schedule_is_strict_and_identifiable():
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "a0d30c9b14a8"
    for start in range(len(gen.SCHEDULE_PROFILES)):
        pairs = []
        for offset in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(920_000 + start, start + offset, difficulty="medium")
            assert gen.strict_canonical_like(grid) == []
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_b1af643b5c32_self_check_rejects_four_structural_impostors():
    grid = _scene(2)  # canonical 3-block / wide profile
    facts = gen.analyze_scene(grid)["facts"]
    blocks, target = facts["blocks"], facts["target"]

    collapsed = copy.deepcopy(grid)
    pattern_value = facts["pattern_colors"][0]
    for r, row in enumerate(collapsed):
        for c in range(len(row)):
            if not gen._inside_any_block(r, c, blocks):
                row[c] = pattern_value

    punctured = copy.deepcopy(grid)
    punctured[target["r0"]][target["c0"]] = pattern_value

    extra_block = copy.deepcopy(grid)
    used = {v for row in grid for v in row}
    fresh = next(color for color in range(10) if color not in used)
    occupied = {(r, c) for block in blocks for r in range(block["r0"], block["r1"] + 1)
                for c in range(block["c0"], block["c1"] + 1)}
    anchor = next(
        (r, c)
        for r in range(len(grid) - 2)
        for c in range(len(grid[0]) - 2)
        if all((rr, cc) not in occupied for rr in range(r, r + 3) for cc in range(c, c + 3))
    )
    for r in range(anchor[0], anchor[0] + 3):
        for c in range(anchor[1], anchor[1] + 3):
            extra_block[r][c] = fresh

    tied = copy.deepcopy(grid)
    secondary = max((b for b in blocks if b is not target), key=lambda b: b["area"])
    reconstructed = gen.rule_mirror(grid)
    for i, r in enumerate(range(target["r0"], target["r1"] + 1)):
        for j, c in enumerate(range(target["c0"], target["c1"] + 1)):
            if i >= secondary["height"] or j >= secondary["width"]:
                tied[r][c] = reconstructed[i][j]

    for impostor in (collapsed, punctured, extra_block, tied):
        assert gen.self_check(impostor), "structural impostor was incorrectly accepted"


def test_b1af643b5c32_override_observability_and_replay():
    overrides = {
        "grid_h": 21,
        "grid_w": 19,
        "period": 4,
        "n_blocks": 3,
        "largest_shape": "6x12",
        "pattern_palette_size": 4,
    }
    first = gen.generate(930_001, 17, difficulty="easy", **overrides)
    second = gen.generate(930_001, 17, difficulty="easy", **overrides)
    assert first == second
    assert first is not second and first[0] is not second[0]
    assert gen.observe_overrides(first) == overrides
    assert gen.self_check(first, difficulty="easy", meta={"overrides": overrides}) == []


def test_b1af643b5c32_preserves_global_rng_and_input_purity():
    random.seed(940_001)
    state = random.getstate()
    grid = gen.generate(940_002, 23, difficulty="hard")
    assert random.getstate() == state
    before = copy.deepcopy(grid)
    _ = gen.rule_mirror(grid)
    assert grid == before

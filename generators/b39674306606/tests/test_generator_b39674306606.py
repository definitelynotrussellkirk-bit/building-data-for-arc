"""Focused regression tests for generator b39674306606."""
from __future__ import annotations

import copy
import importlib
import random
from collections import Counter, deque
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs

TASK_ID = "b39674306606"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.b39674306606.generator"
)


def _canonical_pairs():
    return canonical_pairs(TASK_ID)


def _independent_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            queue = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            r0 = min(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            key = tuple(sorted((r - r0, c - c0) for r, c in cells))
            out.append({"cells": cells, "key": key, "size": len(cells)})
    return out


def _independent_answer(grid, key_name):
    comps = _independent_components(grid)
    counts = Counter(obj[key_name] for obj in comps)
    chosen = [obj for obj in comps if counts[obj[key_name]] == 1]
    out = [[0] * len(grid[0]) for _ in grid]
    if len(chosen) == 1:
        for r, c in chosen[0]["cells"]:
            out[r][c] = 8
    return out


def test_rule_hash_and_all_canonical_pairs_are_pinned():
    assert GEN.RULE_HASH == "c78264ef8c54"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN._solve_exact(pair["input"]) == pair["output"]

    fitting = {
        name
        for name, rival in GEN.SEMANTIC_RIVALS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in pairs)
    }
    assert fitting == {"same_up_to_rotation_or_reflection"}
    assert set(GEN.CANONICAL_SHORTCUTS) == fitting


def test_curriculum_refutes_the_pre_repair_size_only_shortcut():
    # Independent mirror: the pre-repair generator made the singleton a
    # different size on every ordinary draw, so these two answers were always
    # equal. At least one of every three repaired profiles must separate them.
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(913, i, difficulty=difficulty) for i in range(3)]
        assert any(
            _independent_answer(grid, "key") != _independent_answer(grid, "size")
            for grid in grids
        )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_public_axis_boundaries_and_enum_values_are_exactly_observable(difficulty):
    for h in (10, 14):
        for w in (12, 16):
            for pair_count in (1, 2):
                for singleton_size in (3, 6):
                    for relation in (
                        "different_size",
                        "rotated",
                        "same_size_distinct",
                    ):
                        for palette in ("canonical", "monochrome", "multicolor"):
                            grid = GEN.generate(
                                202,
                                5,
                                difficulty=difficulty,
                                grid_h=h,
                                grid_w=w,
                                pair_count=pair_count,
                                singleton_size=singleton_size,
                                odd_relation=relation,
                                palette_kind=palette,
                            )
                            assert GEN.observe_overrides(grid) == {
                                "grid_h": h,
                                "grid_w": w,
                                "pair_count": pair_count,
                                "singleton_size": singleton_size,
                                "odd_relation": relation,
                                "palette_kind": palette,
                            }
                            assert GEN.self_check(grid) == []


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=7)


def test_self_check_rejects_four_task_local_impostors():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(copy.deepcopy(grid)), name


def test_three_consecutive_profiles_refute_every_named_rival_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(404, i, difficulty=difficulty) for i in range(3)]
        assert {
            GEN.schedule_profile(404, i, difficulty) for i in range(3)
        } == set(GEN.SCHEDULE_PROFILES)
        for witness in GEN.SEMANTIC_WITNESSES.values():
            assert any(witness(grid) for grid in grids)

        demos = [{"input": grid, "output": GEN._solve_exact(grid)} for grid in grids]
        query_grid = GEN.generate(404, 3, difficulty=difficulty)
        query = {"input": query_grid, "output": GEN._solve_exact(query_grid)}
        assert GEN.lesson_identifiable(demos, query) == []


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(8675309)
    state = random.getstate()
    first = GEN.generate(505, 2, difficulty="hard")
    second = GEN.generate(505, 2, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert first != second

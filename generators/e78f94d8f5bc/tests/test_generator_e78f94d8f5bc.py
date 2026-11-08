from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.e78f94d8f5bc.generator"
)


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(GEN.TASK_ID, root=find_root(__file__))


def _find_ambiguous_opening(grid):
    """Open one wall that makes the endpoint shortest route non-unique."""
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1:
                continue
            candidate = copy.deepcopy(grid)
            candidate[r][c] = 0
            errors = GEN.self_check(candidate)
            if any("multiple" in error for error in errors):
                return candidate
    raise AssertionError("no one-wall ambiguity mutation found")


def _find_generated_ambiguous_opening():
    """Find a deterministic generated fixture that admits an ambiguity mutation."""
    for sample_index in range(24):
        grid = GEN.generate(120031, sample_index, difficulty="hard")
        try:
            return _find_ambiguous_opening(grid)
        except AssertionError:
            continue
    raise AssertionError("no generated one-wall ambiguity mutation found")


def test_canonical_pairs_are_accepted_and_python_mirror_matches_outputs():
    pairs = _canonical_pairs()
    assert len(pairs) == 6
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_determinism_fresh_returns_and_global_rng_purity(difficulty):
    random.seed(8675309)
    before = random.getstate()
    first = GEN.generate(94103, 7, difficulty=difficulty)
    middle = random.getstate()
    second = GEN.generate(94103, 7, difficulty=difficulty)
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == middle == after
    first[0][0] = 99
    assert second[0][0] != 99


def test_exact_override_boundaries_and_unknown_override_rejection():
    for h in (5, 10):
        for w in (5, 10):
            for turns in (2, 4):
                grid = GEN.generate(
                    7711,
                    h * 100 + w * 10 + turns,
                    difficulty="hard",
                    grid_h=h,
                    grid_w=w,
                    route_turns=turns,
                )
                assert GEN.observe_overrides(grid) == {
                    "grid_h": h,
                    "grid_w": w,
                    "route_turns": turns,
                }
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, mystery_axis=3)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, grid_h=4)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, route_turns=5)


def test_self_check_rejects_four_targeted_impostors():
    grid = GEN.generate(120031, 2, difficulty="hard")
    analysis = GEN._analyze(grid)

    missing_endpoint = copy.deepcopy(grid)
    r, c = analysis["endpoints"][0]
    missing_endpoint[r][c] = 0

    disconnected = copy.deepcopy(grid)
    internal = analysis["path"][len(analysis["path"]) // 2]
    disconnected[internal[0]][internal[1]] = 1

    prepainted = copy.deepcopy(grid)
    paint = analysis["path"][1]
    prepainted[paint[0]][paint[1]] = 4

    ambiguous = _find_generated_ambiguous_opening()

    checks = [
        GEN.self_check(missing_endpoint),
        GEN.self_check(disconnected),
        GEN.self_check(prepainted),
        GEN.self_check(ambiguous),
    ]
    assert all(errors for errors in checks)
    assert any("two color-2" in error for error in checks[0])
    assert any("disconnected" in error or "share" in error for error in checks[1])
    assert any("invalid input color" in error for error in checks[2])
    assert any("multiple" in error for error in checks[3])


def test_three_demo_schedule_identifies_every_sliding_window():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(18):
            demos = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(518081, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            query_grid = GEN.generate(
                518081, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty
            )
            assert GEN.lesson_identifiable(
                demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            ) == []


def test_sparse_two_demo_episode_remains_vulnerable_to_size_conditioned_rival():
    demos = []
    for sample_index in (2, 3):
        grid = GEN.generate(9001, sample_index, difficulty="easy")
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query = GEN.generate(9001, 4, difficulty="easy")
    assert all(GEN._skip_10x10(d["input"]) == d["output"] for d in demos)
    assert GEN._skip_10x10(query) != GEN.rule_mirror(query)


def test_every_query_rotation_of_sliding_four_pair_window_is_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(18):
            pairs = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(620241, sample_index, difficulty=difficulty)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == [], (
                    difficulty,
                    start,
                    query_index,
                    GEN.lesson_identifiable(demos, query),
                )


def test_even_sized_generation_varies_endpoint_lattice_phase():
    parity_patterns = set()
    for sample_index in range(24):
        grid = GEN.generate(
            20261007,
            sample_index,
            difficulty="medium",
            grid_h=6,
            grid_w=6,
            route_turns=3,
        )
        endpoints = GEN._analyze(grid)["endpoints"]
        parity_patterns.add(tuple((r % 2, c % 2) for r, c in endpoints))

    assert len(parity_patterns) >= 2, parity_patterns


def test_even_sized_generation_breaks_fixed_odd_odd_wall_lattice():
    grids = [
        GEN.generate(
            20261007,
            sample_index,
            difficulty="medium",
            grid_h=6,
            grid_w=6,
            route_turns=3,
        )
        for sample_index in range(24)
    ]

    assert any(
        any(grid[r][c] != 1 for r in range(1, 6, 2) for c in range(1, 6, 2))
        for grid in grids
    )

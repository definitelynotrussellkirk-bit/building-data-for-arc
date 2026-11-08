"""Source-bound regressions for keyed Boolean-algebra generator 8881f54cf3c8."""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

TASK_ID = "8881f54cf3c8"
HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(
        f"generator_under_test_{TASK_ID}", source
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
CANONICAL = canonical_pairs(TASK_ID, root=find_root(__file__))


def test_authority_pin_and_all_canonical_pairs() -> None:
    assert GEN.RULE_HASH == "d4cbbd7307ee"
    assert len(CANONICAL) == 4
    for pair in CANONICAL:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"], "validation and mirror must not mutate input"


def test_op4_xor_alias_is_declared_and_generated_op4_refutes_it() -> None:
    """Canonical B⊆A hides the distinction between A-B and symmetric difference."""
    name = "op4_xor_instead_of_a_minus_b"
    rival = GEN.CANONICAL_SHORTCUTS[name]

    # This is a true canonical shortcut: it reproduces every public pair.
    assert all(rival(copy.deepcopy(pair["input"])) == pair["output"] for pair in CANONICAL)
    assert GEN.SEMANTIC_RIVALS[name] is rival
    assert GEN.LESSON_COMPETITORS[name] is rival
    assert name in GEN.WITNESS_RIVALS["a_minus_b_branch"]

    # Ordinary op-4 draws guarantee both A-only and B-only cells, so XOR adds
    # B-only cells that the selected A-minus-B authority must omit.
    for seed in range(32):
        grid = GEN.generate(seed, 3, difficulty="hard", op=4)
        facts = GEN.semantic_observables(grid)
        assert facts["a_only_cells"] >= 1
        assert facts["b_only_cells"] >= 1
        assert rival(copy.deepcopy(grid)) != GEN.rule_mirror(grid)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_seed_permuted_schedule_covers_all_ops_and_varies_query_key(difficulty) -> None:
    demo_orders: set[tuple[int, ...]] = set()
    query_ops: set[int] = set()
    for seed in range(64):
        ops = tuple(
            GEN.generate(seed, index, difficulty=difficulty)[0][0]
            for index in range(5)
        )
        assert set(ops[:4]) == {1, 2, 3, 4}
        # The complete four-operation cycle still deliberately repeats at +4,
        # but the repeated operation must not be globally pinned to key 1.
        assert ops[4] == ops[0]
        demo_orders.add(ops[:4])
        query_ops.add(ops[4])
    assert query_ops == {1, 2, 3, 4}
    assert len(demo_orders) > 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8, "grid_w": 13, "op": 1, "a_size": 4, "b_size": 4, "overlap_cells": 1},
        {"grid_h": 9, "grid_w": 14, "op": 2, "a_size": 6, "b_size": 6, "overlap_cells": 2},
        {"grid_h": 8, "grid_w": 14, "op": 3, "a_size": 5, "b_size": 6, "overlap_cells": 1},
        {"grid_h": 9, "grid_w": 13, "op": 4, "a_size": 6, "b_size": 4, "overlap_cells": 2},
    ],
)
def test_override_boundaries_are_exact_and_observable(overrides) -> None:
    grid = GEN.generate(7001, 19, difficulty="hard", **overrides)
    assert GEN.self_check(grid) == []
    observed = GEN.observe_overrides(grid)
    assert {key: observed[key] for key in overrides} == overrides


@pytest.mark.parametrize(
    "override",
    [
        {"typo_axis": 3},
        {"grid_h": 7},
        {"grid_w": 15},
        {"op": 0},
        {"op": 5},
        {"a_size": 3},
        {"b_size": 7},
        {"overlap_cells": 0},
        {"grid_h": True},
    ],
)
def test_invalid_overrides_are_rejected(override) -> None:
    with pytest.raises(ValueError):
        GEN.generate(1, 0, **override)


def test_self_check_rejects_structural_impostors() -> None:
    good = GEN.generate(9001, 0, difficulty="medium")
    assert GEN.self_check(good) == []

    ragged = copy.deepcopy(good)
    ragged[0].pop()
    bad_key = copy.deepcopy(good)
    bad_key[0][0] = 0
    polluted_key_band = copy.deepcopy(good)
    polluted_key_band[1][1] = 2

    for bad in (
        ragged,
        bad_key,
        polluted_key_band,
        GEN.generate(1, 0, texture="no_op"),
        GEN.generate(1, 0, texture="missing_color"),
        GEN.generate(1, 0, texture="identical_sets"),
    ):
        assert GEN.self_check(bad)


def test_replay_freshness_and_global_rng_purity() -> None:
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(42, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    assert before == after


def test_every_ordinary_op3_draw_exposes_key_participation() -> None:
    for seed in range(20):
        grid = GEN.generate(seed, 2, difficulty="hard", op=3)
        assert grid[0][0] == 3
        assert GEN.rule_mirror(grid) != GEN._clean_boolean(grid)

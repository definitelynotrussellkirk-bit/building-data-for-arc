"""Task-local regression tests for the Boolean-panel curriculum."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve()
TASK_HOME = HERE.parent.parent
sys.path.insert(0, str(TASK_HOME / "workspace"))
from reference_probe import (  # noqa: E402
    all_one_operation,
    canonical_pairs,
    fixed_or_and_xor_order,
    gallery,
    key4_only_xor,
    load_generator,
    observed,
    parse,
    truth_state_counts,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_authority_is_pinned() -> None:
    assert gen.RULE_HASH == "dfc8cc699169"


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_accepted_and_independent_oracle_matches(pair: dict) -> None:
    assert gen.self_check(deepcopy(pair["input"])) == []
    assert gen.strict_canonical_like(deepcopy(pair["input"])) == []
    assert gallery(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band: str | None) -> None:
    requested = {"interior_h": 6, "interior_w": 3, "n_keys": 5, "gap": 4}
    grid = gen.generate(193, 17, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "override",
    [
        {"typo_axis": 1},
        {"interior_h": 2},
        {"interior_h": 7},
        {"interior_w": 2},
        {"interior_w": 7},
        {"n_keys": 0},
        {"n_keys": 6},
        {"gap": 0},
        {"gap": 5},
        {"interior_h": 5.0},
        {"interior_w": True},
        {"n_keys": "3"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(override: dict) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **override)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_schedule_has_exact_canonical_profile_support_in_each_band(band: str) -> None:
    grids = [gen.generate(8801, index, difficulty=band) for index in range(20)]
    canonical_profiles = {(9, 15, 5), (9, 17, 5), (9, 19, 5)}
    profiles = {
        (len(grid), len(grid[0]), len({cell for row in grid for cell in row}))
        for grid in grids
    }
    assert profiles & canonical_profiles
    assert {gen.schedule_profile(8801, i, band) for i in range(20)} == set(gen.SCHEDULE_PROFILES)
    assert all(gen.self_check(grid) == [] for grid in grids)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_examples_expose_boolean_truth_table_and_refute_simple_rivals(
    band: str | None,
) -> None:
    for index in range(18):
        grid = gen.generate(4100 + index, index, difficulty=band)
        info = parse(grid)
        assert all(count > 0 for count in truth_state_counts(grid).values())
        assert {"or", "and", "xor"} <= {
            "or" if key == 2 else "and" if key == 3 else "xor"
            for key in info["keys"]
        }
        authority = gallery(grid)
        assert all_one_operation(grid, 2) != authority
        assert all_one_operation(grid, 3) != authority
        assert all_one_operation(grid, 4) != authority
        assert fixed_or_and_xor_order(grid) != authority


def test_key4_only_shortcut_fits_canonical_but_each_schedule_window_refutes_it() -> None:
    assert all(key4_only_xor(pair["input"]) == pair["output"] for pair in canonical_pairs())
    for start in range(12):
        demos = [gen.generate(7331, start + offset, difficulty="hard") for offset in range(3)]
        assert any(key4_only_xor(grid) != gallery(grid) for grid in demos)


@pytest.mark.parametrize("start", range(12))
def test_each_three_demo_window_refutes_declared_lesson_competitors(start: int) -> None:
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(7331, start + offset, difficulty="hard")
        demos.append({"input": grid, "output": gallery(grid)})
    query_grid = gen.generate(7331, start + gen.EXAMPLES_NEEDED, difficulty="hard")
    query = {"input": query_grid, "output": gallery(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(deepcopy(pair["input"])) != pair["output"] for pair in demos), name


def test_declared_semantic_witnesses_and_rivals_are_real_counterexamples() -> None:
    required = {"or_branch", "and_branch", "xor_branch", "key_order", "non4_xor_key"}
    assert required <= set(gen.SEMANTIC_WITNESSES)
    assert {"all_or", "all_and", "all_xor", "fixed_order", "key4_only_xor"} <= set(
        gen.SEMANTIC_RIVALS
    )
    for index in range(12):
        grid = gen.generate(991, index, difficulty="medium")
        authority = gallery(grid)
        for witness in ("or_branch", "and_branch", "xor_branch", "key_order"):
            assert gen.SEMANTIC_WITNESSES[witness](grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            if name == "key4_only_xor" and not gen.SEMANTIC_WITNESSES["non4_xor_key"](grid):
                continue
            assert rival(deepcopy(grid)) != authority, name


@pytest.mark.parametrize(
    "mutation",
    ["ragged", "unknown_color", "remove_key", "break_frame", "wrong_mask_color"],
)
def test_self_check_rejects_destructive_mutations(mutation: str) -> None:
    grid = gen.generate(43, 6, interior_h=5, interior_w=5, n_keys=3, gap=1)
    if mutation == "ragged":
        grid[-1].pop()
    elif mutation == "unknown_color":
        grid[1][0] = 1
    elif mutation == "remove_key":
        grid[0] = [0] * len(grid[0])
    elif mutation == "break_frame":
        grid[2][0] = 0
    elif mutation == "wrong_mask_color":
        left = parse(grid)["frames"][0]
        grid[left[0] + 1][left[1] + 1] = 3
    assert gen.self_check(grid)


def test_replay_is_deterministic_and_call_order_independent() -> None:
    expected = gen.generate(1201, 17, difficulty="hard")
    for index in range(100):
        gen.generate(index, index * 7, difficulty="easy")
    assert gen.generate(1201, 17, difficulty="hard") == expected

"""Focused regressions for the 78ab57735469 input curriculum."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

# Portable bootstrap for both the packet and the isolated task-test runtime.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "78ab57735469"
ROOT = find_root(__file__)
DEFAULT_GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_GENERATOR.is_file():
    DEFAULT_GENERATOR = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def intended(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python reading of the unchanged 3x3 block rule."""
    n = len(grid)
    return [
        [
            grid[n - 1 - (row % n) if (row // n) % 2 == 0 else row % n]
                [n - 1 - (col % n) if (col // n) % 2 == 0 else col % n]
            for col in range(3 * n)
        ]
        for row in range(3 * n)
    ]


def vertical_only(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: perform row-block flips but ignore column-block flips."""
    n = len(grid)
    return [
        [
            grid[n - 1 - (row % n) if (row // n) % 2 == 0 else row % n][col % n]
            for col in range(3 * n)
        ]
        for row in range(3 * n)
    ]


def horizontal_only(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: perform column-block flips but ignore row-block flips."""
    n = len(grid)
    return [
        [
            grid[row % n]
                [n - 1 - (col % n) if (col // n) % 2 == 0 else col % n]
            for col in range(3 * n)
        ]
        for row in range(3 * n)
    ]


def fixed_three(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: assume every input is exactly 3x3."""
    tile = [row[:3] for row in grid[:3]]
    return intended(tile)


def pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT)


def require(name: str):
    assert hasattr(GEN, name), f"generator must declare {name}"
    return getattr(GEN, name)


def demo(seed: int, index: int, band: str) -> dict:
    grid = GEN.generate(seed, index, difficulty=band)
    return {"input": grid, "output": intended(grid)}


def test_rule_pin_and_canonical_pairs_match_independent_oracle():
    assert getattr(GEN, "RULE_HASH", None) == "18918c7192ef"
    for pair in pairs():
        source = deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert intended(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("requested", [{"side": 3, "palette_size": 3}, {"side": 5, "palette_size": 4}])
def test_exact_overrides_are_global_observable_and_lawful(band, requested):
    observe = require("observe_overrides")
    grid = GEN.generate(41, 9, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert observe(grid) == requested
    assert intended(grid) != vertical_only(grid)
    assert intended(grid) != horizontal_only(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"side": 2},
        {"side": 6},
        {"palette_size": 2},
        {"palette_size": 5},
        {"side": True},
        {"palette_size": 3.5},
        {"texture": "full_symmetric"},  # retired ordinary/degenerate axis
        {"asymmetry_force": False},      # retired ambiguity switch
    ],
)
def test_invalid_unknown_and_retired_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


def test_audit_one_axis_symmetric_counterexample_is_rejected():
    # Retained audit review-15f5f8fd63911ebe:v0001, easy indices 417..419.
    lr_only = [[2, 2, 2], [4, 4, 4], [2, 4, 2]]
    ud_only = [[1, 2, 3], [2, 3, 1], [1, 2, 3]]
    assert GEN._is_lr_sym(lr_only) and not GEN._is_ud_sym(lr_only)
    assert GEN._is_ud_sym(ud_only) and not GEN._is_lr_sym(ud_only)
    assert GEN.self_check(lr_only)
    assert GEN.self_check(ud_only)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_ordinary_draw_exposes_both_flip_axes(band):
    for index in range(180):
        grid = GEN.generate(20260928, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert not GEN._is_lr_sym(grid), (band, index, grid)
        assert not GEN._is_ud_sym(grid), (band, index, grid)
        assert intended(grid) != vertical_only(grid)
        assert intended(grid) != horizontal_only(grid)


def test_self_check_rejects_malformed_and_minimal_impostors():
    for grid in (
        None,
        [],
        [[]],
        [[1, 2, 3], [1, 2]],
        [[1, 2], [3, 4]],
        [[1, 1, 1], [1, 2, 1], [1, 1, 1]],
        [[1, 1, 1], [2, 2, 2], [1, 1, 1]],
        [[True, 2, 3], [3, 1, 2], [2, 3, 1]],
    ):
        errors = GEN.self_check(grid)
        assert isinstance(errors, list) and errors
        assert all(isinstance(error, str) and error for error in errors)


def test_semantic_contract_names_and_refutes_the_three_main_shortcuts():
    rivals = require("SEMANTIC_RIVALS")
    shortcuts = require("CANONICAL_SHORTCUTS")
    competitors = require("LESSON_COMPETITORS")
    witnesses = require("SEMANTIC_WITNESSES")
    claims = require("WITNESS_RIVALS")

    assert {"ignore_horizontal_flips", "ignore_vertical_flips", "fixed_3x3"} <= set(rivals)
    assert "fixed_3x3" in shortcuts
    assert set(rivals) <= set(competitors)
    assert set(claims) <= set(witnesses)

    canonical = pairs()
    assert all(shortcuts["fixed_3x3"](pair["input"]) == pair["output"] for pair in canonical)

    witness = GEN.generate(77, 1, difficulty="medium", side=4, palette_size=4)
    authority = intended(witness)
    assert shortcuts["fixed_3x3"](witness) != authority
    assert rivals["ignore_horizontal_flips"](witness) != authority
    assert rivals["ignore_vertical_flips"](witness) != authority


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_consecutive_lessons_and_all_query_rotations_refute_declared_rivals(band):
    hook = require("lesson_identifiable")
    competitors = require("LESSON_COMPETITORS")
    for start in range(8):
        examples = [demo(9100, start + offset, band) for offset in range(4)]
        for query_index in range(4):
            query = examples[query_index]
            demos = [example for i, example in enumerate(examples) if i != query_index]
            assert hook(demos, query) == []
            for name, rival in competitors.items():
                assert not all(rival(item["input"]) == item["output"] for item in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


def test_pinned_profile_floor_keeps_at_least_a_quarter_of_draws_canonical_scale():
    profiles = {(3, 3, 3), (3, 3, 4)}
    exact = 0
    total = 0
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = GEN.generate(seed, sample_index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({cell for row in grid for cell in row}),
            )
            exact += profile in profiles
            total += 1
    assert exact / total >= 0.25, (exact, total)


def test_replay_is_fresh_deterministic_and_does_not_touch_global_random():
    random.seed(321)
    before = random.getstate()
    first = GEN.generate(404, 5, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(404, 5, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second

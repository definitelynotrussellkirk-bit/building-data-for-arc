from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "f29955be8ba2"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("f29955be8ba2_generator_under_test", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _expected(grid):
    """Independent mirror of the documented rule for task-local assertions."""
    block_h = len(grid) // 3
    blocks = [
        [row[1:] for row in grid[index * block_h : (index + 1) * block_h]]
        for index in range(3)
    ]
    permutation = [grid[row][0] for row in range(3)]
    return [row[:] for item in permutation for row in blocks[item - 1]]


def _facts(grid):
    block_h = len(grid) // 3
    block_w = len(grid[0]) - 1
    colors = []
    masks = []
    for index in range(3):
        cells = []
        nonzero = set()
        for r in range(block_h):
            for c in range(block_w):
                value = grid[index * block_h + r][c + 1]
                if value:
                    cells.append((r, c))
                    nonzero.add(value)
        assert len(nonzero) == 1
        colors.append(next(iter(nonzero)))
        masks.append(frozenset(cells))
    return {
        "block_h": block_h,
        "block_w": block_w,
        "permutation": "".join(str(grid[row][0]) for row in range(3)),
        "colors": tuple(colors),
        "masks": tuple(masks),
        "palette_size": len({value for row in grid for value in row}),
    }


def _episode(grid):
    return {"input": grid, "output": _expected(grid)}


def test_rule_pin_and_canonical_examples_match_the_authority_contract():
    assert MODULE.RULE_HASH == "7f09fab6403a"
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        assert _expected(pair["input"]) == pair["output"]
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_draws_are_deterministic_strict_nonidentity_lessons(band):
    random.seed(90210)
    state = random.getstate()
    for index in range(45):
        grid = MODULE.generate(700 + index, index, difficulty=band)
        assert random.getstate() == state
        assert grid == MODULE.generate(700 + index, index, difficulty=band)
        assert MODULE.self_check(grid) == []
        assert MODULE.strict_canonical_like(grid) == []
        observed = MODULE.observe_overrides(grid)
        facts = _facts(grid)
        for key in ("block_h", "block_w", "permutation"):
            assert observed[key] == facts[key]
        assert observed["permutation"] != "123"
        assert len(set(facts["masks"])) == 3
        assert _expected(grid) != [row[1:] for row in grid]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"block_h": 2, "block_w": 3, "permutation": "123", "palette_profile": "canonical_low"},
        {"block_h": 5, "block_w": 18, "permutation": "321", "palette_profile": "canonical_high"},
        {"block_h": 3, "block_w": 7, "permutation": "213", "palette_profile": "varied"},
    ],
)
def test_exact_override_boundaries_are_observable_in_every_band(band, overrides):
    grid = MODULE.generate(77, 13, difficulty=band, **overrides)
    assert MODULE.self_check(grid) == []
    observed = MODULE.observe_overrides(grid)
    for key, value in overrides.items():
        assert observed[key] == value


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown": 1},
        {"block_h": 1},
        {"block_h": 6},
        {"block_h": True},
        {"block_w": 2},
        {"block_w": 19},
        {"block_w": 3.0},
        {"permutation": "111"},
        {"permutation": 132},
        {"palette_profile": "warm"},
        {"palette_profile": 7},
    ],
)
def test_invalid_overrides_fail_loudly(overrides):
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, **overrides)


def test_self_check_is_structural_and_mutation_sensitive():
    base = MODULE.generate(
        91,
        8,
        block_h=3,
        block_w=7,
        permutation="213",
        palette_profile="varied",
    )
    mutations = {}

    grid = copy.deepcopy(base)
    grid[0][0] = grid[1][0]
    mutations["duplicate header value"] = grid

    grid = copy.deepcopy(base)
    grid[4][0] = 2
    mutations["header-column junk"] = grid

    grid = copy.deepcopy(base)
    for r in range(3):
        for c in range(1, 8):
            grid[r][c] = 0
    mutations["empty block"] = grid

    grid = copy.deepcopy(base)
    original = grid[0][1]
    replacement = 9 if original != 9 else 8
    grid[0][1] = replacement
    mutations["multicolor block"] = grid

    grid = copy.deepcopy(base)
    block0_color = next(v for row in grid[:3] for v in row[1:] if v)
    for r in range(3, 6):
        for c in range(1, 8):
            if grid[r][c]:
                grid[r][c] = block0_color
    mutations["duplicate block colors"] = grid

    for name, changed in mutations.items():
        assert MODULE.self_check(changed), name

    assert MODULE.self_check([])
    assert MODULE.self_check([[0], [0, 1]])
    assert MODULE.self_check([[True] * 4 for _ in range(6)])


def test_every_band_hits_both_canonical_size_palette_profiles_in_twenty_draws():
    wanted = {(9, 8, 5), (9, 9, 7)}
    for band in ("easy", "medium", "hard"):
        seen = set()
        for index in range(20):
            grid = MODULE.generate(1234, index, difficulty=band)
            seen.add((len(grid), len(grid[0]), _facts(grid)["palette_size"]))
        assert wanted <= seen


def test_schedule_breaks_color_rank_and_first_header_cyclic_shortcuts_in_every_demo_window():
    for band in ("easy", "medium", "hard"):
        for start in range(24):
            grids = [MODULE.generate(314, start + offset, difficulty=band) for offset in range(3)]
            assert any(MODULE.SEMANTIC_WITNESSES["palette_order_decoupled"](grid) for grid in grids)
            assert any(MODULE.SEMANTIC_WITNESSES["noncyclic_header"](grid) for grid in grids)


def test_declared_color_rank_shortcut_fits_all_canonical_pairs_but_generated_witness_refutes_it():
    rival = MODULE.CANONICAL_SHORTCUTS["header_values_as_color_ranks"]
    assert all(rival(pair["input"]) == pair["output"] for pair in _pairs())

    grid = MODULE.generate(
        19,
        1,
        block_h=3,
        block_w=7,
        permutation="213",
        palette_profile="varied",
    )
    assert MODULE.SEMANTIC_WITNESSES["palette_order_decoupled"](grid)
    assert rival(grid) != _expected(grid)


def test_lesson_hook_accepts_scheduled_windows_and_names_a_deliberately_ambiguous_window():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            items = [_episode(MODULE.generate(88, start + offset, difficulty=band)) for offset in range(4)]
            assert MODULE.lesson_identifiable(items[:3], items[3]) == []

    demos = [_episode(MODULE.generate(55, index, palette_profile="canonical_low")) for index in (0, 3, 6)]
    query = _episode(MODULE.generate(55, 1, palette_profile="varied"))
    reasons = MODULE.lesson_identifiable(demos, query)
    assert any("header_values_as_color_ranks" in reason for reason in reasons)


def test_every_declared_witness_rival_claim_is_true_when_the_witness_fires():
    for band in ("easy", "medium", "hard"):
        for index in range(60):
            grid = MODULE.generate(2718, index, difficulty=band)
            truth = _expected(grid)
            for witness_name, rival_names in MODULE.WITNESS_RIVALS.items():
                witness = MODULE.SEMANTIC_WITNESSES[witness_name]
                if not witness(grid):
                    continue
                assert any(
                    MODULE.SEMANTIC_RIVALS[rival_name](grid) != truth
                    for rival_name in rival_names
                ), (band, index, witness_name, rival_names)

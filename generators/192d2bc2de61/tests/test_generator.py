"""Focused regressions for the legend-ordered largest-component curriculum."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "192d2bc2de61"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

PROFILE_NAMES = (
    "prefix_10x13",
    "spaced_10x14",
    "offset_11x14",
    "wide_11x15",
)
CANONICAL_PROFILES = {(10, 13, 4), (10, 14, 4), (11, 14, 4), (11, 15, 4)}


def _legend(grid):
    return [value for value in grid[0] if value != 0]


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(1, h)
        for c in range(w)
        if grid[r][c] == color
    }
    found = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        cells = {first}
        stack = [first]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        found.append(cells)
    return found


def _crop(grid, cells):
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    return [list(row[c1 : c2 + 1]) for row in grid[r1 : r2 + 1]]


def _pack(blocks):
    h = max(map(len, blocks))
    w = sum(len(block[0]) for block in blocks) + len(blocks) - 1
    out = [[0] * w for _ in range(h)]
    left = 0
    for block in blocks:
        for r, row in enumerate(block):
            for c, value in enumerate(row):
                if value != 0:
                    out[r][left + c] = value
        left += len(block[0]) + 1
    return out


def intended_output(grid):
    """Independent mirror of the selected Racket authority."""
    blocks = []
    for color in _legend(grid):
        components = sorted(
            _components(grid, color),
            key=lambda cells: (-len(cells), min(r for r, _ in cells), min(c for _, c in cells)),
        )
        blocks.append(_crop(grid, components[0]))
    return _pack(blocks)


def first_component_shortcut(grid):
    """Canonical-fitting rival: choose the upper-left component, not the largest."""
    blocks = []
    for color in _legend(grid):
        components = sorted(
            _components(grid, color),
            key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells), -len(cells)),
        )
        blocks.append(_crop(grid, components[0]))
    return _pack(blocks)


EXACT_WITNESS = [
    [2, 0, 4, 0, 6, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [2, 0, 0, 0, 0, 4, 0, 0, 0, 0, 6, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [4, 4, 0, 0, 0, 6, 6, 0, 0, 0, 2, 2, 2],
    [4, 0, 0, 0, 0, 6, 6, 0, 0, 0, 0, 2, 0],
    [4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]
EXACT_WITNESS_OUTPUT = [
    [2, 2, 2, 0, 4, 4, 0, 6, 6],
    [0, 2, 0, 0, 4, 0, 0, 6, 6],
    [0, 0, 0, 0, 4, 4, 0, 0, 0],
]


def test_rule_pin_and_exact_profile_contract():
    assert GEN.RULE_HASH == "5ea0808c0383"
    assert GEN.VERSION == "4.0.0"
    assert tuple(GEN.SCHEDULE_PROFILES) == PROFILE_NAMES
    assert set(GEN.AXES) == {"scene_profile"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.EXAMPLES_NEEDED == 2


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", PROFILE_NAMES)
def test_every_profile_override_is_exact_constructive_and_semantic(band, profile):
    grid = GEN.generate(271, 13, difficulty=band, scene_profile=profile)
    observed = GEN.observe_overrides(grid)
    assert observed == {"scene_profile": profile}
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert (len(grid), len(grid[0]), len({value for row in grid for value in row})) in CANONICAL_PROFILES
    truth = intended_output(grid)
    assert truth != grid
    assert GEN.SEMANTIC_WITNESSES["legend_order_controls_packing"](grid)
    assert GEN.SEMANTIC_RIVALS["body_order"](grid) != truth
    if profile == "prefix_10x13":
        assert not GEN.SEMANTIC_WITNESSES["same_color_largest_choice"](grid)
        assert GEN.SEMANTIC_RIVALS["first_component"](grid) == truth
    else:
        assert GEN.SEMANTIC_WITNESSES["same_color_largest_choice"](grid)
        assert GEN.SEMANTIC_RIVALS["first_component"](grid) != truth
        assert GEN.SEMANTIC_WITNESSES["nonprefix_legend"](grid)
        assert GEN.SEMANTIC_RIVALS["prefix_legend"](grid) != truth


@pytest.mark.parametrize(
    "key,value",
    [
        ("scene_profile", "unknown"),
        ("scene_profile", 3),
        ("scene_profile", None),
        ("typo_axis", 1),
    ],
)
def test_invalid_and_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", ["simple", 1, True])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, difficulty=difficulty)


def test_canonical_inputs_are_accepted_and_independent_oracle_matches_answers():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]


def test_strongest_canonical_shortcut_fits_every_public_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert all(first_component_shortcut(pair["input"]) == pair["output"] for pair in pairs)
    shortcut = GEN.CANONICAL_SHORTCUTS["first_component"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs)


def test_exact_generated_counterexample_refutes_first_component_shortcut():
    assert GEN.self_check(EXACT_WITNESS) == []
    assert intended_output(EXACT_WITNESS) == EXACT_WITNESS_OUTPUT
    assert first_component_shortcut(EXACT_WITNESS) == [[2, 0, 4, 0, 6]]
    assert GEN.SEMANTIC_WITNESSES["same_color_largest_choice"](EXACT_WITNESS)
    assert GEN.SEMANTIC_RIVALS["first_component"](EXACT_WITNESS) == [[2, 0, 4, 0, 6]]


def test_prefix_profile_reaches_canonical_single_component_count():
    grid = GEN.generate(71, 0, scene_profile="prefix_10x13")
    assert all(len(_components(grid, color)) == 1 for color in _legend(grid))
    assert first_component_shortcut(grid) == intended_output(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_covers_all_profiles_and_every_three_pair_window_refutes_all_rivals(band):
    seen = set()
    unique = set()
    for start in range(16):
        pairs = []
        for offset in range(3):
            index = start + offset
            grid = GEN.generate(811, index, difficulty=band)
            assert grid == GEN.generate(811, index, difficulty=band)
            assert GEN.self_check(grid) == []
            profile = GEN.observe_overrides(grid)["scene_profile"]
            seen.add(profile)
            unique.add(repr(grid))
            pairs.append({"input": grid, "output": intended_output(grid)})
        demos, query = pairs[:2], pairs[2]
        assert GEN.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
        for rival in GEN.LESSON_COMPETITORS.values():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos)
    assert seen == set(PROFILE_NAMES)
    assert len(unique) >= 17


def test_profile_floor_has_exact_canonical_support_in_every_band():
    import hashlib

    for band in ("easy", "medium", "hard"):
        exact = 0
        for index in range(20):
            digest = hashlib.sha256(f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            exact += profile in CANONICAL_PROFILES
        assert exact == 20


def test_validator_rejects_targeted_impostors_without_raising():
    grid = GEN.generate(19, 3, scene_profile="spaced_10x14")
    legend_cols = [c for c, value in enumerate(grid[0]) if value != 0]

    duplicate_legend = deepcopy(grid)
    duplicate_legend[0][legend_cols[1]] = duplicate_legend[0][legend_cols[0]]
    assert GEN.self_check(duplicate_legend)

    unknown_body_color = deepcopy(grid)
    unknown_body_color[1][0] = next(color for color in range(1, 10) if color not in _legend(grid))
    assert GEN.self_check(unknown_body_color)

    missing_body = deepcopy(grid)
    missing = _legend(grid)[0]
    for r in range(1, len(missing_body)):
        for c in range(len(missing_body[0])):
            if missing_body[r][c] == missing:
                missing_body[r][c] = 0
    assert GEN.self_check(missing_body)

    for malformed in (None, [], [[]], [[0], [0, 1]], [[True] * 13 for _ in range(10)]):
        assert GEN.self_check(malformed)


def test_helpers_do_not_mutate_inputs():
    grid = GEN.generate(101, 8, scene_profile="offset_11x14")
    original = deepcopy(grid)
    intended_output(grid)
    GEN.observe_overrides(grid)
    GEN.self_check(grid)
    GEN.strict_canonical_like(grid)
    for fn in GEN.SEMANTIC_WITNESSES.values():
        fn(grid)
    for fn in GEN.SEMANTIC_RIVALS.values():
        fn(grid)
    assert grid == original


def test_default_difficulty_bands_are_not_byte_identical():
    for index in range(8):
        grids = {
            band: GEN.generate(1771, index, difficulty=band)
            for band in ("easy", "medium", "hard")
        }
        assert len({repr(grid) for grid in grids.values()}) == 3

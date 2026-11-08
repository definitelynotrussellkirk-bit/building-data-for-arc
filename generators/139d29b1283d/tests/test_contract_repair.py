"""Observable contract regressions for the stamp-overlap generator repair.

The graph walk and stamp-set construction below are independent test oracles.
They use input pixels, never the generator's geometry or analysis helpers.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "139d29b1283d"
ROOT = find_root(__file__)
TASK_HOME = next(
    path for path in Path(__file__).resolve().parents
    if (path / "generator.py").is_file()
)
SPEC = importlib.util.spec_from_file_location(
    "stamp_overlap_contract_under_test", TASK_HOME / "generator.py"
)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

BANDS = (None, "easy", "medium", "hard")
TEXTURES = ("overlap", "no_overlap", "clipped")
AXES = {"grid_h", "grid_w", "template_size", "n_distractors", "texture"}
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _positions(grid, color):
    return {
        (r, c) for r, row in enumerate(grid)
        for c, value in enumerate(row) if value == color
    }


def _green_components(grid):
    unseen = _positions(grid, 3)
    components = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        component = {first}
        frontier = [first]
        while frontier:
            r, c = frontier.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    frontier.append(neighbor)
        components.append(component)
    return sorted(components, key=len, reverse=True)


def _geometry(grid):
    components = _green_components(grid)
    assert components, "input has no color-3 template"
    if len(components) > 1:
        assert len(components[0]) > len(components[1]), "largest template is tied"
    top = min(r for r, _ in components[0])
    left = min(c for _, c in components[0])
    shape = {(r - top, c - left) for r, c in components[0]}
    anchors = [_positions(grid, color) for color in (1, 2)]
    assert [len(cells) for cells in anchors] == [1, 1]
    stamps = []
    for anchor in anchors:
        ar, ac = next(iter(anchor))
        stamps.append({(ar + r, ac + c) for r, c in shape})
    h, w = len(grid), len(grid[0])
    in_bounds = lambda cell: 0 <= cell[0] < h and 0 <= cell[1] < w
    visible_overlap = {cell for cell in stamps[0] & stamps[1] if in_bounds(cell)}
    off_grid = {cell for cell in stamps[0] | stamps[1] if not in_bounds(cell)}
    return components, visible_overlap, off_grid


def _observed(grid):
    components, overlap, off_grid = _geometry(grid)
    if off_grid:
        assert overlap, "clipped examples must still have visible overlap"
        texture = "clipped"
    else:
        texture = "overlap" if overlap else "no_overlap"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_size": len(components[0]),
        "n_distractors": len(components) - 1,
        "texture": texture,
    }


def _output_from_pixels(grid):
    _, overlap, _ = _geometry(grid)
    output = [[0] * len(grid[0]) for _ in grid]
    for r, c in overlap:
        output[r][c] = 8
    return output


def _assert_contract(grid, requested=None):
    assert isinstance(grid, list) and grid and grid[0]
    assert all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    assert all(type(value) is int for row in grid for value in row)
    assert {value for row in grid for value in row} == {0, 1, 2, 3}
    observed = _observed(grid)
    assert 8 <= observed["grid_h"] <= 24
    assert 8 <= observed["grid_w"] <= 24
    assert 2 <= observed["template_size"] <= 8
    assert 0 <= observed["n_distractors"] <= 2
    assert GEN.self_check(grid) == []
    if requested:
        assert {key: observed[key] for key in requested} == requested
    reported = GEN.observe_overrides(grid)
    assert {key: reported[key] for key in AXES} == observed


def _scene(texture="overlap", *, distractors=False):
    grid = [[0] * 10 for _ in range(8)]
    for r, c in ((1, 1), (1, 2), (2, 1), (2, 2)):
        grid[r][c] = 3
    anchors = {
        "overlap": ((4, 4), (4, 5)),
        "no_overlap": ((4, 4), (4, 7)),
        "clipped": ((7, 6), (7, 7)),
    }[texture]
    for color, (r, c) in enumerate(anchors, start=1):
        grid[r][c] = color
    if distractors:
        for r, c in ((1, 6), (1, 7), (3, 8)):
            grid[r][c] = 3
    return grid


def _malformed_cases():
    cases = [
        pytest.param([], id="empty"),
        pytest.param([[]], id="empty-row"),
        pytest.param([[0] * 8 for _ in range(8)], id="all-zero-audit-witness"),
    ]
    for missing in (3, 1, 2):
        grid = _scene()
        for r, c in _positions(grid, missing):
            grid[r][c] = 0
        cases.append(pytest.param(grid, id=f"missing-color-{missing}"))
    for color in (1, 2, 4, 8):
        grid = _scene()
        grid[0][0] = color
        cases.append(pytest.param(grid, id=f"extra-color-{color}"))
    grid = _scene()
    grid[-1].pop()
    cases.append(pytest.param(grid, id="ragged"))
    for name, value in (("noninteger", 1.5), ("boolean", False)):
        grid = _scene()
        grid[0][0] = value
        cases.append(pytest.param(grid, id=name))
    grid = _scene()
    for r, c in ((1, 6), (1, 7), (2, 6), (2, 7)):
        grid[r][c] = 3
    cases.append(pytest.param(grid, id="tied-largest-templates"))
    return cases


def test_authority_is_pinned_and_axes_describe_real_controls():
    assert getattr(GEN, "RULE_HASH", None) == "fcd41965ebef"
    assert set(GEN.AXES) == AXES


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"v{p['variant']}-{p['split']}-{p['pair_index']}")
def test_every_canonical_pair_remains_in_the_validator_domain(pair):
    assert GEN.self_check(pair["input"]) == []
    assert _output_from_pixels(pair["input"]) == pair["output"]


def test_retained_seed_123_index_7_exact_size_eight_regression():
    grid = GEN.generate(123, 7, template_size=8)
    assert len(_green_components(grid)[0]) == 8
    _assert_contract(grid, {"template_size": 8})


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("height,width,size,distractors", [
    (8, 8, 2, 0), (8, 8, 8, 2),
    (24, 24, 2, 2), (24, 24, 8, 0),
    (8, 24, 8, 2), (24, 8, 8, 2),
])
def test_joint_extreme_controls_work_in_every_difficulty(band, height, width, size, distractors):
    for texture in TEXTURES:
        requested = {
            "grid_h": height, "grid_w": width, "template_size": size,
            "n_distractors": distractors, "texture": texture,
        }
        grid = GEN.generate(71, 5, difficulty=band, **requested)
        _assert_contract(grid, requested)


@pytest.mark.parametrize("size", range(2, 9))
def test_all_advertised_template_sizes_are_exact(size):
    for band in BANDS:
        requested = {
            "grid_h": 16, "grid_w": 18, "template_size": size,
            "n_distractors": size % 3, "texture": TEXTURES[size % 3],
        }
        _assert_contract(GEN.generate(103, size, difficulty=band, **requested), requested)


@pytest.mark.parametrize("texture", TEXTURES)
def test_observer_recovers_axes_from_hand_authored_pixels(texture):
    grid = _scene(texture, distractors=True)
    assert [len(component) for component in _green_components(grid)] == [4, 2, 1]
    _assert_contract(grid, {
        "grid_h": 8, "grid_w": 10, "template_size": 4,
        "n_distractors": 2, "texture": texture,
    })


@pytest.mark.parametrize("band", BANDS)
def test_default_draws_have_fixed_color_roles_and_are_repeatable(band):
    for index in range(8):
        grid = GEN.generate(431, index, difficulty=band)
        _assert_contract(grid)
        assert grid == GEN.generate(431, index, difficulty=band)


@pytest.mark.parametrize("axis,value", [
    (axis, value)
    for axis, lower, upper in (
        ("grid_h", 8, 24), ("grid_w", 8, 24),
        ("template_size", 2, 8), ("n_distractors", 0, 2),
    )
    for value in (True, float(lower), str(lower), lower - 1, upper + 1)
])
def test_invalid_exact_integer_values_are_rejected(axis, value):
    with pytest.raises(ValueError):
        GEN.generate(9, 2, **{axis: value})


@pytest.mark.parametrize("overrides", [
    {"unknown_axis": 1}, {"unknown_axis": None},
    {"palette_kind": "warm"}, {"texture": "default"},
    {"texture": True}, {"difficulty": "expert"},
])
def test_unknown_axes_and_invalid_modes_are_rejected(overrides):
    with pytest.raises(ValueError):
        GEN.generate(9, 2, **overrides)


@pytest.mark.parametrize("band", BANDS)
def test_none_controls_mean_the_same_as_omitted_controls(band):
    expected = GEN.generate(29, 4, difficulty=band)
    assert GEN.generate(29, 4, difficulty=band, **dict.fromkeys(AXES)) == expected


@pytest.mark.parametrize("grid", _malformed_cases())
def test_validator_rejects_actual_malformed_or_ambiguous_inputs(grid):
    assert GEN.self_check(grid), "malformed input was accepted without findings"


@pytest.mark.parametrize("texture", TEXTURES)
def test_public_analysis_does_not_modify_input_pixels(texture):
    grid = _scene(texture, distractors=True)
    original = deepcopy(grid)
    assert GEN.self_check(grid) == []
    GEN.observe_overrides(grid)
    assert grid == original


def _size_cutoff_rival(grid):
    """Wrong selection policy exposed by the independently found review case."""
    components = _green_components(grid)
    first_large = sorted((cells for cells in components if len(cells) >= 4), key=min)
    chosen = first_large[0] if first_large else components[0]
    top, left = min(r for r, _ in chosen), min(c for _, c in chosen)
    shape = {(r - top, c - left) for r, c in chosen}
    stamps = []
    for color in (1, 2):
        ar, ac = next(iter(_positions(grid, color)))
        stamps.append({(ar + r, ac + c) for r, c in shape})
    output = [[0] * len(grid[0]) for _ in grid]
    for r, c in stamps[0] & stamps[1]:
        if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
            output[r][c] = 8
    return output


@pytest.mark.parametrize("size", (5, 6, 7, 8))
def test_strong_draws_refute_fixed_size_cutoff_selection(size):
    for seed in range(12):
        grid = GEN.generate(seed, 0, grid_h=8, grid_w=8,
                            template_size=size, n_distractors=2, texture="overlap")
        assert _size_cutoff_rival(grid) != _output_from_pixels(grid), (
            "a size cutoff still selects the template without comparing component sizes", seed, size)


def test_size_cutoff_witness_is_lawful_and_canonical_pairs_cannot_refute_it():
    for pair in PAIRS:
        assert _size_cutoff_rival(pair["input"]) == pair["output"]
    grid = [[0] * 14 for _ in range(12)]
    grid[1][2:9] = [3] * 7
    grid[3][2:10] = [3] * 8
    grid[7][5], grid[7][6] = 1, 2
    assert GEN.self_check(grid) == []
    assert _positions(_output_from_pixels(grid), 8) == {(7, c) for c in range(6, 13)}
    assert _positions(_size_cutoff_rival(grid), 8) == {(7, c) for c in range(6, 12)}


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
@pytest.mark.parametrize("start", (0, 1, 2))
def test_default_four_pair_windows_keep_a_full_refuter_after_every_holdout(band, start):
    grids = [GEN.generate(37, start + i, difficulty=band) for i in range(4)]
    rivals = dict(GEN.CANONICAL_SHORTCUTS)
    rivals["independent_size_cutoff"] = _size_cutoff_rival
    for query in range(4):
        demonstrations = [grid for i, grid in enumerate(grids) if i != query]
        for name, rival in rivals.items():
            assert any(rival(grid) != _output_from_pixels(grid) for grid in demonstrations), (query, name)

"""Portable regressions for fixed-background, same-color border components.

The component oracle is deliberately independent of the generator's helpers.
Run in a packet through review.py, or in a copied runtime with pytest.
"""
from collections import deque
import importlib
import importlib.util

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "04c98e3e35bb"
ROOT = find_root(__file__)
LOCAL_SOURCE = ROOT / "generators" / TASK / "generator.py"
if LOCAL_SOURCE.is_file():
    SPEC = importlib.util.spec_from_file_location("border_generator_under_test", LOCAL_SOURCE)
    generator = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(generator)
else:
    generator = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def components(grid):
    """Observe same-color four-components, excluding only the fixed color 0."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            todo = deque([(r, c)])
            seen.add((r, c))
            cells = set()
            while todo:
                rr, cc = todo.popleft()
                cells.add((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] == color and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            border = any(rr in (0, h - 1) or cc in (0, w - 1) for rr, cc in cells)
            result.append((color, cells, border))
    return result


def observed_counts(grid):
    objs = components(grid)
    return sum(border for _, _, border in objs), sum(not border for _, _, border in objs)


def reference_python(grid):
    out = [row[:] for row in grid]
    for _, cells, border in components(grid):
        for r, c in cells:
            out[r][c] = 2 if border else 8
    return out


CANONICAL = canonical_pairs(TASK, root=ROOT)


@pytest.mark.parametrize("pair", CANONICAL,
                         ids=lambda p: f"v{p['variant']}-{p['split']}-{p['pair_index']}")
def test_all_canonical_inputs_are_valid_and_match_component_semantics(pair):
    assert generator.self_check(pair["input"]) == []
    assert reference_python(pair["input"]) == pair["output"]


def test_border_cells_inside_grid_are_not_a_strictly_interior_object():
    grid = [[0] * 6 for _ in range(6)]
    for r, c in ((0, 0), (0, 1), (1, 0), (1, 1)):
        grid[r][c] = 3
    assert observed_counts(grid) == (1, 0)
    assert generator.self_check(grid), "A border 2x2 has interior cells, but no interior component"


def grid_with_invalid_color(value):
    # Retain both required component classes: rejection must concern the bad
    # color, rather than an unrelated absence of an interior object.
    grid = [[0] * 6 for _ in range(6)]
    grid[0][1] = grid[3][3] = 3
    grid[2][2] = value
    return grid


@pytest.mark.parametrize("grid", [
    [], [[]], [[0, 0], [0]],
    *[grid_with_invalid_color(v) for v in (False, 10, -1, 1.0, "1")],
    [[0, 0], [0, 0]],
])
def test_malformed_or_objectless_grids_are_rejected(grid):
    assert generator.self_check(grid), "self_check must report invalid grids without crashing"


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_band_supports_canonical_dimension_profiles(difficulty):
    wanted = {(len(p["input"]), len(p["input"][0])) for p in CANONICAL}
    observed = set()
    for index in range(30):
        grid = generator.generate(17, index, difficulty=difficulty)
        assert generator.self_check(grid, difficulty=difficulty) == []
        assert 6 <= len(grid) <= 25 and 6 <= len(grid[0]) <= 25
        nb, ni = observed_counts(grid)
        assert nb >= 1 and ni >= 1
        observed.add((len(grid), len(grid[0])))
    assert wanted <= observed, f"Missing canonical dimensions in {difficulty}: {wanted - observed}"


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(6, 6), (6, 25), (25, 6), (25, 25)])
@pytest.mark.parametrize("border,interior", [(1, 1), (1, 4), (4, 1), (4, 4)])
def test_dimension_and_object_count_overrides_are_exact(difficulty, height, width, border, interior):
    grid = generator.generate(23, 7, difficulty=difficulty, grid_h=height, grid_w=width,
                              n_border_objs=border, n_interior_objs=interior)
    assert (len(grid), len(grid[0])) == (height, width)
    assert observed_counts(grid) == (border, interior)
    assert generator.self_check(grid, difficulty=difficulty) == []


@pytest.mark.parametrize("color", range(1, 10))
@pytest.mark.parametrize("mixed", [False, True])
def test_color_anchor_and_mixed_palette_overrides(color, mixed):
    grid = generator.generate(41, 5, obj_color=color, mixed_colors=mixed)
    colors = [v for row in grid for v in row if v != 0]
    assert colors[0] == color, "obj_color binds the lexicographically first occupied cell"
    assert (len(set(colors)) >= 2) if mixed else set(colors) == {color}
    assert generator.self_check(grid) == []


@pytest.mark.parametrize("overrides", [
    {"unknown_axis": 1}, {"grid_h": 5}, {"grid_w": 26},
    {"grid_h": True}, {"grid_w": "8"}, {"grid_h": 8.5},
    {"n_border_objs": 0}, {"n_interior_objs": 0}, {"n_border_objs": 5},
    {"n_interior_objs": True}, {"n_border_objs": "2"},
    {"obj_color": 0}, {"obj_color": 10}, {"obj_color": True}, {"obj_color": "3"},
    {"mixed_colors": 2}, {"mixed_colors": "1"},
    {"obj_shape": "unknown"}, {"texture": "unknown"},
    {"obj_size_min": True}, {"obj_size_max": "3"},
])
def test_invalid_or_unknown_overrides_raise(overrides):
    with pytest.raises(ValueError):
        generator.generate(31, 8, **overrides)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_generation_is_deterministic(difficulty):
    kwargs = dict(difficulty=difficulty, grid_h=8, grid_w=9,
                  n_border_objs=2, n_interior_objs=3, obj_color=8, mixed_colors=True)
    assert generator.generate(73, 11, **kwargs) == generator.generate(73, 11, **kwargs)


def test_contact_witness_keeps_color_and_diagonal_components_distinct():
    grid = [[0] * 6 for _ in range(6)]
    for r, c in ((0, 0), (0, 1), (1, 0)):
        grid[r][c] = 3
    grid[1][1] = 4
    grid[2][1] = 3
    assert observed_counts(grid) == (1, 2)
    expected = [[0] * 6 for _ in range(6)]
    for r, c in ((0, 0), (0, 1), (1, 0)):
        expected[r][c] = 2
    expected[1][1] = expected[2][1] = 8
    assert reference_python(grid) == expected
    assert generator.self_check(grid) == []


@pytest.mark.parametrize("color", [2, 8])
def test_output_palette_colors_are_valid_inside_and_at_border(color):
    grid = [[0] * 6 for _ in range(6)]
    grid[0][1] = grid[3][3] = color
    assert generator.self_check(grid) == []
    result = reference_python(grid)
    assert result[0][1] == 2 and result[3][3] == 8


def test_contact_profiles_always_demonstrate_propagation_beyond_literal_edge_cells():
    # A corner L can have every cell on the frame. The lesson then fails to
    # distinguish whole-component recoloring from per-cell border coloring.
    for index in range(32):
        if generator.schedule_profile(847206725, index) == 'free':
            continue
        grid = generator.generate(847206725, index, difficulty='easy')
        h,w = len(grid),len(grid[0])
        assert any(border and any(0 < r < h-1 and 0 < c < w-1 for r,c in cells)
                   for _,cells,border in components(grid)), f'no propagation witness at index {index}'


def test_contact_profiles_refute_the_independently_authored_degree_two_shortcut():
    rival_path = LOCAL_SOURCE.parent / 'workspace' / 'degree_two_rival.py'
    if not rival_path.is_file():
        rival_path = ROOT / 'puzzle_generators' / 'per_puzzle' / TASK / 'workspace' / 'degree_two_rival.py'
    spec = importlib.util.spec_from_file_location('observed_degree_rival', rival_path)
    rival = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rival)
    for index in range(16):
        if generator.schedule_profile(294787216, index) == 'free':
            continue
        grid = generator.generate(294787216, index, difficulty='easy')
        assert rival.solve(grid) != reference_python(grid), f'geometry shortcut survives contact profile {index}'


def test_contact_profiles_refute_the_authored_largest_component_shortcut():
    rival_path = LOCAL_SOURCE.parent / 'workspace' / 'largest_component_rival.py'
    if not rival_path.is_file():
        rival_path = ROOT / 'puzzle_generators' / 'per_puzzle' / TASK / 'workspace' / 'largest_component_rival.py'
    spec = importlib.util.spec_from_file_location('observed_largest_rival', rival_path)
    rival = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rival)
    for seed in (1982757076, 294787216, 847206725):
        for index in range(16):
            if generator.schedule_profile(seed, index) == 'free':
                continue
            grid = generator.generate(seed, index, difficulty='easy')
            assert rival.solve(grid) != reference_python(grid), f'rank shortcut survives {seed}:{index}'

"""Public sampler controls and input-domain regressions from baseline witnesses."""
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "bd05f2963d17"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = spec_from_file_location("second_smallest_sampler_contract", SOURCE)
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)
PAIRS = canonical_pairs(TASK, root=ROOT, labeled_only=True)
BANDS = (None, "easy", "medium", "hard")


def components(grid):
    """Observe four-neighbor green components without generator internals."""
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, color in enumerate(row) if color == 3}
    result = []
    while remaining:
        cells = {remaining.pop()}
        queue = list(cells)
        while queue:
            r, c = queue.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    queue.append(neighbor)
        result.append(cells)
    return sorted(result, key=lambda cells: (len(cells), min(cells)))


def assert_lawful(grid):
    assert isinstance(grid, list) and grid
    width = len(grid[0])
    assert width and all(isinstance(row, list) and len(row) == width for row in grid)
    assert all(type(color) is int and color in (0, 3) for row in grid for color in row)
    found = components(grid)
    assert len(found) >= 3
    assert len({len(cells) for cells in found}) == len(found)
    target = found[1]
    rows, cols = zip(*target)
    assert min(rows) + 2 * (max(rows) - min(rows) + 1) <= len(grid)
    assert min(cols) + 2 * (max(cols) - min(cols) + 1) <= width
    assert GEN.self_check(grid) == []
    return found


def domain_grid(count=3):
    """Separated horizontal bars with sizes 1..count; the size-2 target fits."""
    grid = [[0] * 17 for _ in range(16)]
    for index in range(count):
        for col in range(1, index + 2):
            grid[1 + 3 * index][col] = 3
    return grid


@pytest.mark.parametrize("pair", PAIRS,
                         ids=[f"v{p['variant']}-{p['split']}-{p['pair_index']}" for p in PAIRS])
def test_canonical_labeled_inputs_remain_valid(pair):
    assert_lawful(pair["input"])


def test_axes_advertise_only_actual_integer_controls():
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_components"}
    assert all(axis["type"] == "int" for axis in GEN.AXES.values())


@pytest.mark.parametrize("band", BANDS)
def test_canonical_size_is_supported_in_each_twenty_draw_band(band):
    grids = [GEN.generate(73, index, difficulty=band) for index in range(20)]
    for grid in grids:
        assert_lawful(grid)
    assert sum(len(grid) == len(grid[0]) == 11 for grid in grids) >= 1


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("height,width", [(10, 11), (10, 17), (16, 11), (16, 17), (11, 11)])
@pytest.mark.parametrize("count", [3, 4, 5])
def test_joint_exact_controls_work_in_every_band(band, height, width, count):
    controls = {"grid_h": height, "grid_w": width, "n_components": count}
    grid = GEN.generate(17, 2, difficulty=band, **controls)
    assert (len(grid), len(grid[0])) == (height, width)
    assert len(assert_lawful(grid)) == count
    assert GEN.generate(17, 2, difficulty=band, **controls) == grid


@pytest.mark.parametrize("axis,value", [
    (axis, value) for axis, integer in (("grid_h", 11), ("grid_w", 13), ("n_components", 3))
    for value in (True, False, float(integer), str(integer), [], {})
])
def test_integer_controls_reject_noninteger_values(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(17, 2, **{axis: value})


@pytest.mark.parametrize("axis,value", [
    ("grid_h", 9), ("grid_h", 17), ("grid_w", 10), ("grid_w", 18),
    ("n_components", 2), ("n_components", 6),
])
def test_integer_controls_reject_values_outside_advertised_domains(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(17, 2, **{axis: value})


@pytest.mark.parametrize("controls", [
    {"palette_kind": "warm"}, {"palette_size": 1}, {"texture": "default"},
    {"texture": "tied_sizes"}, {"texture": None}, {"density": "sparse"},
    {"position_bias": "three_distinct_size_motifs"}, {"n_distinct_colors": 1},
    {"unknown_axis": 17}, {"unknown_axis": None},
])
def test_unknown_and_removed_controls_are_rejected(controls):
    with pytest.raises(ValueError):
        GEN.generate(17, 2, **controls)


@pytest.mark.parametrize("count", [3, 4, 5])
def test_checker_accepts_distinct_component_counts(count):
    assert_lawful(domain_grid(count))


@pytest.mark.parametrize("bad", [None, [], [[]], [0], [[0], 0]])
def test_malformed_grid_shapes_return_reasons_instead_of_raising(bad):
    reasons = GEN.self_check(bad)
    assert isinstance(reasons, list) and reasons
    assert all(isinstance(reason, str) and reason for reason in reasons)


@pytest.mark.parametrize("value", [2, 10, -1, 0.5, True, "x", None, {}, []])
def test_malformed_cells_are_rejected_on_an_otherwise_valid_grid(value):
    grid = domain_grid()
    assert GEN.self_check(grid) == []
    grid[-1][-1] = value
    assert GEN.self_check(grid)


@pytest.mark.parametrize("extra", [False, True], ids=["short-row", "long-row"])
def test_ragged_grids_return_reasons(extra):
    grid = domain_grid()
    grid[-1] = grid[-1] + [10] if extra else grid[-1][:-1]
    assert GEN.self_check(grid)


@pytest.mark.parametrize("failure", ["too-few", "tied-sizes", "scaled-out-of-bounds"])
def test_domain_violations_remain_rejected(failure):
    grid = deepcopy(domain_grid(2 if failure == "too-few" else 3))
    if failure == "tied-sizes":
        grid[7][3] = 0
    if failure == "scaled-out-of-bounds":
        grid[4][1] = grid[4][2] = 0
        grid[-1][-3] = grid[-1][-2] = 3
    assert GEN.self_check(grid)

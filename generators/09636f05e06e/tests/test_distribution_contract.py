"""Behavioral regressions for the sparse zero-band teaching distribution."""
from importlib.util import module_from_spec, spec_from_file_location

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "09636f05e06e"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = spec_from_file_location("zero_band_generator_under_test", SOURCE)
GEN = module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def observed(grid):
    zeros = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0}
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "palette_size": len({value for row in grid for value in row}),
        "n_zero_rows": len({r for r, c in zeros}),
        "n_zero_cols": len({c for r, c in zeros}),
    }


def expected(grid):
    """Independent literal statement of the unchanged canonical operation."""
    rows = {r for r, row in enumerate(grid) if 0 in row}
    cols = {c for row in grid for c, value in enumerate(row) if value == 0}
    return [[0 if value != 2 and (r in rows or c in cols) else value
             for c, value in enumerate(row)] for r, row in enumerate(grid)]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_joint_canonical_profile_is_in_every_band(band):
    grids = [GEN.generate(73, i, difficulty=band) for i in range(20)]
    assert any(observed(g) == {"grid_h": 20, "grid_w": 20, "palette_size": 10,
                               "n_zero_rows": 2, "n_zero_cols": 2}
               and sum(row.count(0) for row in g) == 4 for g in grids)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("controls", [
    {"grid_h": 8, "grid_w": 22, "n_zero_rows": 1, "n_zero_cols": 5, "palette_size": 3},
    {"grid_h": 22, "grid_w": 8, "n_zero_rows": 5, "n_zero_cols": 1, "palette_size": 10},
    {"grid_h": 8, "grid_w": 8, "n_zero_rows": 5, "n_zero_cols": 5, "palette_size": 10},
])
def test_exact_controls_are_observable_in_all_bands(band, controls):
    grid = GEN.generate(0, 0, difficulty=band, **controls)
    assert observed(grid) == controls
    assert GEN.observe_overrides(grid) == controls
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("palette", [3, 4, 7, 10])
def test_single_zero_honors_palette(palette):
    grid = GEN.generate(0, 0, texture="single_zero", palette_size=palette)
    assert sum(row.count(0) for row in grid) == 1
    assert observed(grid)["palette_size"] == palette
    assert GEN.self_check(grid) == []


def test_gap_witness_does_not_remove_last_palette_color():
    grid = GEN.generate(114, 0, grid_h=8, grid_w=8, n_zero_rows=5,
                        n_zero_cols=5, palette_size=10, twos_density=0.4,
                        texture="scatter")
    assert observed(grid)["palette_size"] == 10


def test_edge_placement_reaches_actual_boundary():
    grid = GEN.generate(0, 0, grid_h=12, grid_w=12, n_zero_rows=2,
                        n_zero_cols=2, texture="rectangle", position_bias="edge")
    zeros = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0]
    assert any(r in (0, 11) for r, c in zeros)
    assert any(c in (0, 11) for r, c in zeros)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0, 2], [1]],
    [[0, 2], [1, 99]], [[0, 2], [1, False]], [[0, 2], [1, "bad"]],
    [[0, 2], [1, -1]], [[0, 2], [1, 1.0]]])
def test_malformed_grids_return_reasons(bad):
    assert GEN.self_check(bad)


@pytest.mark.parametrize("controls", [
    {"grid_h": True}, {"grid_w": 8.5}, {"grid_h": "8"},
    {"twos_density": -0.1}, {"twos_density": 0.5},
    {"twos_density": float("nan")}, {"twos_density": float("inf")},
    {"twos_density": False}, {"position_bias": "nonsense"},
    {"texture": "nonsense"}, {"unknown_axis": 1},
    {"twos_density": 10 ** 400},
])
def test_invalid_overrides_fail_visibly(controls):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **controls)


@pytest.mark.parametrize("axis", ["n_zero_rows", "n_zero_cols"])
def test_single_zero_refuses_conflicting_count(axis):
    with pytest.raises(ValueError) as error:
        GEN.generate(0, 0, texture="single_zero", **{axis: 2})
    assert {axis, "texture"}.issubset(error.value.incompatible_axes)


def test_none_retains_default_convention():
    assert GEN.generate(11, 2, n_zero_cols=None, palette_size=None) == GEN.generate(11, 2)


def test_zero_density_control_has_explicitly_retired():
    with pytest.raises(ValueError):
        GEN.generate(0, 0, zero_density=0.1)


def test_twos_probability_is_not_uniform_base_palette_sampling():
    grid = GEN.generate(0, 1, grid_h=20, grid_w=20, twos_density=0)
    assert sum(row.count(2) for row in grid) == 2
    assert GEN.self_check(grid) == []
    denser = GEN.generate(0, 1, grid_h=20, grid_w=20, twos_density=0.4)
    assert sum(row.count(2) for row in denser) > 2


def test_canonical_pairs_remain_accepted_and_declared_shortcuts_really_fit():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 4
    assert GEN.CANONICAL_SHORTCUTS
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert expected(pair["input"]) == pair["output"]
        for name, rival in GEN.CANONICAL_SHORTCUTS.items():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 17, 73])
def test_every_schedule_start_teaches_each_query_rotation(band, seed):
    for start in range(GEN.LESSON_SCHEDULE_PERIOD):
        grids = [GEN.generate(seed, start + i, difficulty=band) for i in range(5)]
        labels = [expected(g) for g in grids]
        for query in range(5):
            for name, rival in GEN.LESSON_COMPETITORS.items():
                if rival(grids[query]) != labels[query]:
                    assert any(rival(grids[i]) != labels[i] for i in range(5) if i != query), (start, query, name)

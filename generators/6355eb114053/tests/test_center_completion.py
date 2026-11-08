"""Task regressions: honest controls and lessons that teach every condition."""
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "6355eb114053"
SPEC = importlib.util.spec_from_file_location(
    "center_completion_under_test", Path(__file__).resolve().parent.parent / "generator.py"
)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
BANDS = ("easy", "medium", "hard")


def centers(grid):
    """Independent local-law observation, without generator helper reuse."""
    result = {}
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            neighbors = (grid[r-1][c], grid[r+1][c], grid[r][c-1], grid[r][c+1])
            if grid[r][c] == 0 and len(set(neighbors)) == 1 and neighbors[0] != 0:
                result[r, c] = neighbors[0]
    return result


def oracle(grid):
    out = [row[:] for row in grid]
    for (r, c), color in centers(grid).items():
        out[r][c] = color
    return out


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("axis,value", [
    ("grid_h", 5), ("grid_h", 14), ("grid_w", 5), ("grid_w", 14),
    ("n_pluses", 1), ("n_pluses", 6),
    ("palette_size", 1), ("palette_size", 9),
    ("n_distinct_colors", 1), ("n_distinct_colors", 9),
])
def test_single_axis_endpoints_are_realized(band, axis, value):
    # Catches the old difficulty-bound rejection and ignored palette controls.
    grid = GEN.generate(123, 0, difficulty=band, **{axis: value})
    observed = {"grid_h": len(grid), "grid_w": len(grid[0]),
                "n_pluses": len(centers(grid)),
                "palette_size": len({v for row in grid for v in row} - {0})}
    observed["n_distinct_colors"] = observed["palette_size"]
    assert observed[axis] == value
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("palette", (1, 2, 5, 9))
def test_joint_exact_counts_and_palette_alias(palette):
    grid = GEN.generate(25, 4, grid_h=14, grid_w=14, n_pluses=6,
                        palette_size=palette, n_distinct_colors=palette)
    assert len(centers(grid)) == 6
    assert len({v for row in grid for v in row} - {0}) == palette


def test_conflicting_palette_aliases_fail_loudly():
    with pytest.raises(ValueError, match="palette_size.*n_distinct_colors|n_distinct_colors.*palette_size"):
        GEN.generate(0, 0, palette_size=2, n_distinct_colors=9)


def test_infeasible_geometry_is_not_silently_shortened():
    with pytest.raises(ValueError):
        GEN.generate(0, 0, grid_h=5, grid_w=5, n_pluses=6)


@pytest.mark.parametrize("axis", ("pallete_size", "palette_kind", "position_bias", "density", "texture"))
def test_unknown_or_retired_noop_axes_are_rejected(axis):
    with pytest.raises(ValueError, match="unknown|retired"):
        GEN.generate(0, 0, **{axis: "default"})


@pytest.mark.parametrize("value", (True, 6.7, "6", 0, 15))
def test_invalid_dimension_values_are_rejected(value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, grid_h=value)


@pytest.mark.parametrize("grid", (
    None, [], [[]], [[0, 1], [1]], [[0, True, 0], [True, 0, True], [0, True, 0]],
    [[0, 10, 0], [10, 0, 10], [0, 10, 0]],
    [[0, 1.0, 0], [1.0, 0, 1.0], [0, 1.0, 0]],
    [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
))
def test_validator_rejects_bad_inputs_without_crashing(grid):
    assert GEN.self_check(grid)


def test_connected_shared_arm_pluses_remain_lawful():
    grid = [[0, 0, 0, 0, 0], [0, 5, 0, 5, 0], [5, 0, 5, 0, 5],
            [0, 5, 0, 5, 0], [0, 0, 0, 0, 0]]
    assert GEN.self_check(grid) == []
    assert centers(grid) == {(2, 1): 5, (2, 3): 5}


def test_canonical_inputs_and_declared_shortcuts():
    pairs = canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 5
    assert hasattr(GEN, "CANONICAL_SHORTCUTS"), "Missing task-linked shortcut contract"
    assert len(GEN.CANONICAL_SHORTCUTS) >= 6
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert oracle(pair["input"]) == pair["output"]
        for name, rival in GEN.CANONICAL_SHORTCUTS.items():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", BANDS)
def test_every_nominal_four_pair_window_teaches_all_declared_rivals(band):
    # Catches an omitted direction, a missing equality/center cue, and rotations
    # that remove the only discriminating demonstration. Authoritative census
    # separately rechecks actual production assembly and Racket labels.
    assert hasattr(GEN, "LESSON_COMPETITORS"), "Missing lesson rival contract"
    for seed in range(12):
        for start in range(2):
            pairs = [{"input": GEN.generate(seed, start+i, difficulty=band)} for i in range(4)]
            for pair in pairs:
                pair["output"] = oracle(pair["input"])
            for held_out in range(4):
                demos = [p for i, p in enumerate(pairs) if i != held_out]
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(p["input"]) != p["output"] for p in demos), (seed, start, held_out, name)


@pytest.mark.parametrize("band", BANDS)
def test_default_support_includes_nine_and_varied_center_residues(band):
    colors, rows, columns = set(), set(), set()
    canonical_profiles = {(7, 8, 3), (8, 9, 3), (6, 10, 4), (9, 9, 3), (8, 10, 4)}
    hits = 0
    for index in range(100):
        grid = GEN.generate(10000+index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert grid == GEN.generate(10000+index, index, difficulty=band)
        cc = centers(grid)
        colors.update(cc.values())
        rows.update(r % 3 for r, _ in cc)
        columns.update(c % 3 for _, c in cc)
        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        hits += profile in canonical_profiles
    assert colors == set(range(1, 10))
    assert rows == columns == {0, 1, 2}
    assert hits >= 10

"""Source-bound regressions for controls, domain validation, and schedule geometry."""
import itertools
import pytest
from reviewer_support import find_root, load_selected_generator, canonical_pairs

ROOT = find_root(__file__)
G, _, _ = load_selected_generator("f9cd85012aa8", root=ROOT)


def measured(grid):
    colors = {v for row in grid for v in row} - {0, 6}
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "shape_size": sum(row.count(6) for row in grid),
            "n_distractor": len(colors)}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("h,w,size,count", list(itertools.product([5, 20], [6, 24], [3, 10], [0, 4])))
def test_joint_boundaries_exact(band, h, w, size, count):
    requested = dict(grid_h=h, grid_w=w, shape_size=size, n_distractor=count)
    grid = G.generate(71, 0, difficulty=band, **requested)
    assert measured(grid) == requested
    assert not G.self_check(grid)
    assert G.observe_overrides(grid) == requested


@pytest.mark.parametrize("axis", ["grid_h", "grid_w", "shape_size", "n_distractor"])
@pytest.mark.parametrize("value", [True, 5.0, "5", -1])
def test_strict_scalar_controls(axis, value):
    with pytest.raises((ValueError, TypeError)):
        G.generate(2, 0, **{axis: value})


@pytest.mark.parametrize("axis", ["palette_kind", "palette_size", "position_bias", "n_distinct_colors", "density", "texture", "typo"])
def test_removed_and_unknown_axes_reject(axis):
    with pytest.raises((ValueError, TypeError)):
        G.generate(2, 0, **{axis: None})


@pytest.mark.parametrize("bad", [True, 6.0, "6", -1, 10])
def test_validator_rejects_non_arc_cells(bad):
    grid = [[0] * 6 for _ in range(5)]
    for r, c in [(0, 0), (1, 0), (1, 1)]:
        grid[r][c] = 6
    grid[4][5] = bad
    assert G.self_check(grid)


class StuckRng:
    def choice(self, choices):
        return choices[0]


@pytest.mark.parametrize("size", range(3, 11))
def test_sparse_poly_fallback_preserves_requested_count(size):
    cells = G._sparse_poly(StuckRng(), size)
    assert len(set(cells)) == size
    assert len(cells) < (max(r for r, _ in cells) + 1) * (max(c for _, c in cells) + 1)


def test_none_controls_and_canonical_inputs():
    assert G.generate(8, 2) == G.generate(8, 2, **dict.fromkeys(["grid_h", "grid_w", "shape_size", "n_distractor"]))
    for pair in canonical_pairs("f9cd85012aa8", root=ROOT, labeled_only=True):
        assert not G.self_check(pair["input"])


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_and_canonical_support(band):
    assert G.EXAMPLES_NEEDED == 7
    assert G.LESSON_SCHEDULE_PERIOD == 8
    profiles = set()
    for index in range(60):
        grid = G.generate(19, index, difficulty=band)
        assert not G.self_check(grid)
        assert grid == G.generate(19, index, difficulty=band)
        if index % 8 in (0, 2, 4, 6):
            signature = (len(grid), len(grid[0]), measured(grid)["shape_size"])
            profiles.add(signature)
            assert signature in {(7, 8, 4), (8, 9, 4), (9, 10, 5)}
            assert not G.strict_canonical_like(grid)
        else:
            assert measured(grid)["n_distractor"] == 2
            objects = G._components(grid)
            target = next(cells for color, cells in objects if color == 6)
            areas = [(max(r for r, _ in cells) - min(r for r, _ in cells) + 1) *
                     (max(c for _, c in cells) - min(c for _, c in cells) + 1) for _, cells in objects]
            rank = lambda vals: sorted(vals).index(vals[next(i for i, (color, _) in enumerate(objects) if color == 6)])
            expected = {1: (0, 2, 2, 1), 3: (1, 1, 1, 0), 5: (2, 0, 0, 1), 7: (1, 2, 1, 2)}[index % 8]
            assert (rank([len(cells) for _, cells in objects]), rank(areas),
                    rank([color for color, _ in objects]), rank([min(cells) for _, cells in objects])) == expected
            if index % 8 in (3, 7):
                assert max(max(r for r, _ in target) - min(r for r, _ in target) + 1,
                           max(c for _, c in target) - min(c for _, c in target) + 1) >= 4
    assert profiles == {(7, 8, 4), (8, 9, 4), (9, 10, 5)}


def test_observer_counts_objects_in_pixels():
    grid = [[0] * 6 for _ in range(5)]
    for r, c in [(0, 0), (1, 0), (1, 1)]:
        grid[r][c] = 6
    grid[4][0] = grid[4][5] = 2
    assert G.observe_overrides(grid)["n_distractor"] == 2


@pytest.mark.parametrize("index", [True, False, 1.0, -1, "0", 0.0])
def test_sample_index_is_a_nonnegative_python_integer(index):
    with pytest.raises((ValueError, TypeError)):
        G.generate(4, index)


def test_rich_difficulty_changes_dimensions():
    grids = [G.generate(4, 1, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({(len(grid), len(grid[0])) for grid in grids}) == 3
    assert len(grids[0]) * len(grids[0][0]) < len(grids[-1]) * len(grids[-1][0])


def test_area_twelve_shortcut_has_redundant_refutations():
    refuting = []
    for index in range(G.LESSON_SCHEDULE_PERIOD):
        grid = G.generate(7, index)
        parts = G._components(grid)
        chosen = [cells for _, cells in parts if G._bbox(cells)[0] * G._bbox(cells)[1] == 12]
        selected = parts[0][1] if len(parts) == 1 else chosen[0] if len(chosen) == 1 else set()
        target = next(cells for color, cells in parts if color == 6)
        if selected != target:
            refuting.append(index)
    assert len(refuting) >= 2, refuting


def test_rich_bbox_areas_vary_without_rank_coupling():
    areas, wide_sides = [], 0
    for index in (1, 3, 5, 7):
        grid = G.generate(7, index)
        target = next(cells for color, cells in G._components(grid) if color == 6)
        h, w = G._bbox(target)
        areas.append(h * w)
        wide_sides += max(h, w) >= 5
    assert len(set(areas)) == 4
    assert wide_sides >= 2


def test_most_elongated_rival_cannot_survive_a_query_holdout():
    from fractions import Fraction
    def selected(grid):
        parts = G._components(grid)
        def aspect(part):
            h, w = G._bbox(part[1])
            return Fraction(max(h, w), min(h, w)), min(part[1]), part[0]
        return max(parts, key=aspect)[1]
    grids = [G.generate(7, index, difficulty="hard") for index in range(8)]
    target = lambda grid: next(cells for color, cells in G._components(grid) if color == 6)
    query = grids[1]
    assert selected(query) != target(query)
    demos = [grid for index, grid in enumerate(grids) if index != 1]
    assert any(selected(grid) != target(grid) for grid in demos), "elongated rival fits all7 demos and disagrees on held-out residue1"


def test_aspect_and_four_cell_cap_rivals_are_declared():
    required = {"aspect_min", "aspect_max", "aspect_median", "cap_four"}
    assert required <= set(G.CANONICAL_SHORTCUTS)
    assert len(G.CANONICAL_SHORTCUTS) == 21
    for name in required:
        assert G.CANONICAL_SHORTCUTS[name] is G.LESSON_COMPETITORS[name]
        assert G.CANONICAL_SHORTCUTS[name] is G.SEMANTIC_RIVALS[name]
        assert callable(G.SEMANTIC_WITNESSES[name])

"""Public behavior regressions for component centers, with independent oracles."""
from collections import defaultdict, deque
import importlib.util

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "6e068328f4ce"


root = find_root(__file__)
library = (root / "generators" / TASK_ID / "generator.py").is_file()
source = root / "generators" / TASK_ID / "generator.py" if library else root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location("component_centers_under_test", source)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def components(grid, diagonal=False):
    """Find foreground same-color components without production helpers."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    steps = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if diagonal:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in seen:
                continue
            color = grid[r][c]
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                x, y = queue.popleft()
                cells.append((x, y))
                for dx, dy in steps:
                    p = (x + dx, y + dy)
                    if 0 <= p[0] < h and 0 <= p[1] < w and p not in seen and grid[p[0]][p[1]] == color:
                        seen.add(p)
                        queue.append(p)
            result.append((color, cells))
    return result


def render_centers(grid, rival=None):
    groups = components(grid, diagonal=rival == "eight_connected")
    if rival == "per_color":
        merged = defaultdict(list)
        for color, cells in groups:
            merged[color].extend(cells)
        groups = list(merged.items())
    out = [[0] * len(grid[0]) for _ in grid]
    for color, cells in groups:
        rs, cs = zip(*cells)
        r, c = (min(rs) + max(rs)) // 2, (min(cs) + max(cs)) // 2
        if rival == "ceil_midpoint":
            r, c = (min(rs) + max(rs) + 1) // 2, (min(cs) + max(cs) + 1) // 2
        elif rival == "floor_centroid":
            r, c = sum(rs) // len(rs), sum(cs) // len(cs)
        elif rival == "rounded_centroid":
            r, c = round(sum(rs) / len(rs)), round(sum(cs) / len(cs))
        if rival != "existing_cells_only" or grid[r][c] == color:
            out[r][c] = color
    return out


def assert_helpful(grid, *, height=None, width=None, count=None, colors=None):
    assert grid and grid[0]
    assert all(len(row) == len(grid[0]) for row in grid)
    assert all(type(v) is int and 0 <= v <= 9 for row in grid for v in row)
    if height is not None:
        assert len(grid) == height
    if width is not None:
        assert len(grid[0]) == width
    objs = components(grid)
    assert 2 <= len(objs) <= 5
    assert all(len(cells) > 1 for _, cells in objs)
    if count is not None:
        assert len(objs) == count
    if colors is not None:
        assert len({color for color, _ in objs}) == colors
    assert generator.self_check(grid) == []


def test_observed_controls_recover_dimensions_components_and_colors():
    controls = {"grid_h": 12, "grid_w": 13, "n_blobs": 4, "n_distinct_colors": 2}
    grid = generator.generate(17, 1, **controls)
    assert_helpful(grid, height=12, width=13, count=4, colors=2)
    assert generator.observe_overrides(grid) == controls


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_even_lessons_use_canonical_size_rectangles(difficulty):
    for seed in (0, 17):
        grid = generator.generate(seed, 0, difficulty=difficulty)
        assert_helpful(grid)
        for _, cells in components(grid):
            rs, cs = zip(*cells)
            assert max(rs) - min(rs) == 2 and max(cs) - min(cs) == 2
            assert len(cells) == 9


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_odd_lessons_refute_all_center_shortcuts(difficulty):
    for seed in (0, 17):
        for index in (1, 3):
            grid = generator.generate(seed, index, difficulty=difficulty)
            assert_helpful(grid)
            correct = render_centers(grid)
            for rival in ("per_color", "eight_connected", "ceil_midpoint", "floor_centroid", "rounded_centroid", "existing_cells_only"):
                assert correct != render_centers(grid, rival), (seed, index, difficulty, rival)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_feasible_overrides_honor_dimensions_component_and_color_counts(difficulty):
    for index in (0, 1):
        for height, width, count, colors in ((7, 7, 2, 1), (8, 12, 3, 2), (16, 16, 5, 5)):
            grid = generator.generate(17, index, difficulty=difficulty, grid_h=height, grid_w=width, n_blobs=count, n_distinct_colors=colors)
            assert_helpful(grid, height=height, width=width, count=count, colors=colors)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_distinct_colors_only_increases_unspecified_component_count(difficulty):
    for index in (0, 1):
        grid = generator.generate(17, index, difficulty=difficulty, n_distinct_colors=5)
        assert_helpful(grid, count=5, colors=5)


def test_incompatible_explicit_color_count_rejected():
    with pytest.raises(ValueError):
        generator.generate(17, 1, n_blobs=2, n_distinct_colors=3)


@pytest.mark.parametrize("name,value", [("palette_kind", "warm"), ("palette_size", 4), ("position_bias", "spread_blobs"), ("density", "sparse"), ("texture", "cool"), ("texture", "all_singletons")])
def test_unsupported_old_controls_rejected(name, value):
    with pytest.raises(ValueError):
        generator.generate(17, 0, **{name: value})


@pytest.mark.parametrize("name", ["grid_h", "grid_w", "n_blobs", "n_distinct_colors"])
def test_integer_controls_reject_bool_float_and_string(name):
    for value in (True, 8.0 if name.startswith("grid_") else 2.0, "8" if name.startswith("grid_") else "2"):
        with pytest.raises((TypeError, ValueError)):
            generator.generate(17, 1, **{name: value})


@pytest.mark.parametrize("name,bounds", [("grid_h", (6, 17)), ("grid_w", (6, 17)), ("n_blobs", (1, 6)), ("n_distinct_colors", (0, 6))])
def test_integer_controls_reject_out_of_range_values(name, bounds):
    for value in bounds:
        with pytest.raises(ValueError):
            generator.generate(17, 0, **{name: value})


@pytest.mark.parametrize("grid", [[], [[]], [[2, 2], [3]], [[2.0, 2.0, 0, 3, 3]], [[True, True, 0, 3, 3]], [["2", "2", 0, 3, 3]], [[12, 12, 0, 3, 3]], [[-1, -1, 0, 3, 3]]])
def test_self_check_rejects_malformed_grids_even_with_degenerate_meta(grid):
    assert generator.self_check(grid, meta={"texture": "all_singletons"})


def test_self_check_rejects_singletons_hidden_by_per_color_counts():
    assert generator.self_check([[2, 0, 2, 0, 3, 3]])


def test_self_check_accepts_repeated_color_multicell_components():
    assert generator.self_check([[2, 2, 0, 2, 2]]) == []


def test_self_check_accepts_all_five_canonical_pairs():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        grid, output = pair["input"], pair["output"]
        assert generator.self_check(grid) == []
        assert render_centers(grid) == output


def test_independent_oracle_matches_six_live_racket_verified_witnesses():
    # Expected arrays were verified using canonical Racket, not generator code.
    fixtures = [
        ([[2, 2, 0, 2, 2]], [[2, 0, 0, 2, 0]]),
        ([[2, 2, 0], [0, 0, 2], [0, 0, 2]], [[2, 0, 0], [0, 0, 2], [0, 0, 0]]),
        ([[2, 2], [2, 2]], [[2, 0], [0, 0]]),
        ([[2, 2, 2, 2, 2, 2, 2], [2, 0, 0, 0, 0, 0, 0], [2, 0, 0, 0, 0, 0, 0]], [[0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 2, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0]]),
        ([[2, 2, 3, 3], [2, 2, 3, 3]], [[2, 0, 3, 0], [0, 0, 0, 0]]),
        ([[2, 2, 2], [2, 3, 2], [2, 2, 2]], [[0, 0, 0], [0, 3, 0], [0, 0, 0]]),
    ]
    for grid, expected in fixtures:
        assert render_centers(grid) == expected


def test_generation_is_reproducible():
    for index in (0, 1):
        assert generator.generate(17, index) == generator.generate(17, index)


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, "1"])
def test_schedule_rejects_non_integer_or_negative_sample_indices(sample_index):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(17, sample_index)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_rich_support_includes_larger_asymmetric_components(difficulty):
    # Two large, same-color elbows require variation in the primary witness pair.
    found = False
    for seed in range(48):
        large_by_color = defaultdict(int)
        for color, cells in components(generator.generate(seed, 1, difficulty=difficulty)):
            rs, cs = zip(*cells)
            height, width = max(rs)-min(rs)+1, max(cs)-min(cs)+1
            if min(height, width) >= 3 and max(height, width) >= 6 and len(cells) == height+width-1:
                large_by_color[color] += 1
        found = found or any(count >= 2 for count in large_by_color.values())
    assert found, "the broad sampler never supplies a larger same-color elbow pair"

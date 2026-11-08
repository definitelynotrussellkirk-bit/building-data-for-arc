"""Behavioral tests for the repaired halo base and proposed two-step family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from arcpuzzles import Catalog


HOME = Path(__file__).resolve().parents[1]
GENERATOR = HOME / "generator.py"
PROTOTYPE = HOME / "workspace/parametric/prototype.py"


def load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def base():
    return load_path("halo_base_subject", GENERATOR)


@pytest.fixture(scope="module")
def p():
    assert PROTOTYPE.is_file(), "parametric prototype is missing"
    return load_path("halo_parametric_subject", PROTOTYPE)


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def test_exact_sizes_take_precedence_over_difficulty(base):
    grid = base.generate(0, 0, difficulty="easy", grid_h=16, grid_w=18)
    assert (len(grid), len(grid[0])) == (16, 18)


def test_requested_object_and_distinct_color_counts_are_respected(base):
    grid = base.generate(
        3,
        0,
        grid_h=16,
        grid_w=18,
        n_objects=5,
        n_distinct_colors=5,
        palette_size=5,
        palette_kind="default",
    )
    objects = components(grid)
    assert len(objects) == 5
    assert len({color for color, _ in objects}) == 5


def test_repeated_color_objects_and_single_object_are_valid(base):
    repeated = base.generate(
        9,
        0,
        grid_h=16,
        grid_w=18,
        n_objects=2,
        n_distinct_colors=1,
        palette_size=1,
        palette_kind="cool",
    )
    assert len(components(repeated)) == 2
    assert len({cell for row in repeated for cell in row if cell}) == 1
    assert base.self_check(repeated) == []

    single = base.generate(
        11,
        0,
        grid_h=12,
        grid_w=14,
        n_objects=1,
        n_distinct_colors=1,
        palette_size=1,
        palette_kind="warm",
    )
    assert len(components(single)) == 1
    assert base.self_check(single) == []


def test_default_program_is_exact_catalog_source(p):
    catalog = Catalog(Path(__file__).resolve().parents[3])
    programs = {
        row["program_solution"]
        for row in catalog.get("7e826540d45d")["variants"]
        if isinstance(row.get("program_solution"), str)
    }
    assert programs == {p.program({"halo_mode": "one_ring"})}


def test_inputs_are_setting_independent_and_query_prefix_stable(p):
    one_ring = p.generate(17, {"halo_mode": "one_ring"}, 3, 4)
    two_step = p.generate(17, {"halo_mode": "selected_two_step"}, 3, 4)
    one = p.generate(17, {"halo_mode": "one_ring"}, 3, 1)
    for split in ("train", "test"):
        assert [pair["input"] for pair in one_ring[split]] == [pair["input"] for pair in two_step[split]]
    assert one_ring["train"] != two_step["train"]
    assert one_ring["train"] == one["train"]
    assert one_ring["test"][0] == one["test"][0]


@pytest.mark.parametrize("halo_mode", ["one_ring", "selected_two_step"])
def test_counts_labels_and_distinct_inputs(p, halo_mode):
    episode = p.generate(23, {"halo_mode": halo_mode}, 6, 4)
    assert len(episode["train"]) == 6
    assert len(episode["test"]) == 4
    inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    assert len({p.digest(grid) for grid in inputs}) == 10
    for split in ("train", "test"):
        for pair in episode[split]:
            assert pair["output"] == p.transform(pair["input"], {"halo_mode": halo_mode})


def test_each_demonstration_distinguishes_the_two_programs(p):
    episode = p.generate(31, {"halo_mode": "selected_two_step"}, 3, 4)
    for pair in episode["train"]:
        assert p.transform(pair["input"], {"halo_mode": "one_ring"}) != pair["output"]


def test_intermediate_color_selection_differs_from_skip_a_on_teaching_inputs(p):
    episode = p.generate(5, {"halo_mode": "selected_two_step"}, 3, 4)
    for pair in episode["train"]:
        original_choice = p.selected_color(pair["input"])
        intermediate = p.one_ring_halo(pair["input"])
        assert p.selected_color(intermediate) != original_choice


def test_fourth_query_is_substantive_30_square(p):
    episode = p.generate(7, {"halo_mode": "one_ring"}, 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    for r0 in (0, 15):
        for c0 in (0, 15):
            assert sum(cell != 0 for row in grid[r0 : r0 + 15] for cell in row[c0 : c0 + 15]) >= 4


@pytest.mark.parametrize(
    "case",
    [
        {"seed": True, "settings": {"halo_mode": "one_ring"}, "demos": 3, "queries": 4},
        {"seed": 0, "settings": {"halo_mode": "wrong"}, "demos": 3, "queries": 4},
        {"seed": 0, "settings": {"halo_mode": "one_ring"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"halo_mode": "one_ring"}, "demos": 3, "queries": 5},
    ],
)
def test_invalid_requests_are_rejected(p, case):
    with pytest.raises(ValueError):
        p.generate(**case)


def test_unknown_base_override_is_rejected(base):
    with pytest.raises(ValueError, match="unknown override"):
        base.generate(0, 0, not_a_real_axis=1)


@pytest.mark.parametrize("axis,value", [
    ("n_objects", 1),
    ("n_objects", 5),
    ("n_distinct_colors", 1),
    ("n_distinct_colors", 5),
    ("palette_size", 1),
    ("palette_size", 5),
])
def test_each_count_control_is_valid_when_pinned_alone(base, axis, value):
    grid = base.generate(21, 0, grid_h=16, grid_w=18, **{axis: value})
    assert base.self_check(grid) == []
    observed = base.observe_overrides(grid)
    if axis == "palette_size":
        assert 1 <= observed["n_distinct_colors"] <= value
    else:
        assert observed[axis] == value


def test_observed_object_and_color_counts_match_grid(base):
    grid = base.generate(
        27,
        0,
        grid_h=16,
        grid_w=18,
        n_objects=5,
        n_distinct_colors=4,
        palette_size=5,
        palette_kind="warm",
    )
    observed = base.observe_overrides(grid)
    assert observed["grid_h"] == 16
    assert observed["grid_w"] == 18
    assert observed["n_objects"] == 5
    assert observed["n_distinct_colors"] == 4

def _expand_one_ring_color(p, grid, selected):
    intermediate = p.one_ring_halo(grid)
    h, w = len(intermediate), len(intermediate[0])
    out = [row[:] for row in intermediate]
    for r in range(h):
        for c in range(w):
            if intermediate[r][c] != selected:
                continue
            for dr, dc in p.CARDINAL:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and intermediate[nr][nc] == 0:
                    out[nr][nc] = selected
    return out


def _widest_object_shortcut(p, grid):
    color, _cells = max(
        p._components(grid),
        key=lambda item: (
            max(c for _r, c in item[1]) - min(c for _r, c in item[1]) + 1,
            -len(item[1]),
            -item[0],
        ),
    )
    return _expand_one_ring_color(p, grid, color)


def _bottommost_object_shortcut(p, grid):
    color, _cells = max(
        p._components(grid),
        key=lambda item: (
            sum(r for r, _c in item[1]) / len(item[1]),
            max(r for r, _c in item[1]),
            -item[0],
        ),
    )
    return _expand_one_ring_color(p, grid, color)


def test_two_step_lessons_defeat_fixed_shape_and_position_shortcuts(p):
    episode = p.generate(0, {"halo_mode": "selected_two_step"}, 6, 4)
    orientations = set()
    vertical_halves = set()
    widest_matches = []
    bottom_matches = []
    for pair in episode["train"]:
        grid = pair["input"]
        selected = p.selected_color(p.one_ring_halo(grid))
        cells = next(cells for color, cells in p._components(grid) if color == selected)
        height = max(r for r, _c in cells) - min(r for r, _c in cells) + 1
        width = max(c for _r, c in cells) - min(c for _r, c in cells) + 1
        orientations.add("horizontal" if width > height else "vertical")
        centroid_row = sum(r for r, _c in cells) / len(cells)
        vertical_halves.add("top" if centroid_row < len(grid) / 2 else "bottom")
        widest_matches.append(_widest_object_shortcut(p, grid) == pair["output"])
        bottom_matches.append(_bottommost_object_shortcut(p, grid) == pair["output"])

    assert orientations == {"horizontal", "vertical"}
    assert vertical_halves == {"top", "bottom"}
    assert not all(widest_matches)
    assert not all(bottom_matches)


def test_self_check_rejects_sources_with_overlapping_halo_zones(base):
    grid = [[0] * 10 for _ in range(8)]
    grid[3][3] = 2
    grid[3][5] = 4
    errors = base.self_check(grid)
    assert any("separat" in error or "overlap" in error for error in errors)


def _longest_straight_object_shortcut(p, grid):
    components = p._components(grid)
    straight = [
        item
        for item in components
        if len({r for r, _c in item[1]}) == 1
        or len({c for _r, c in item[1]}) == 1
    ]
    if not straight:
        return [row[:] for row in grid]
    color, _cells = max(straight, key=lambda item: (len(item[1]), -item[0]))
    return _expand_one_ring_color(p, grid, color)


def test_two_step_lessons_vary_selected_topology_and_source_size(p):
    episode = p.generate(0, {"halo_mode": "selected_two_step"}, 3, 4)
    source_sizes = set()
    topologies = set()
    orientations = set()
    straight_matches = []
    widest_matches = []
    for pair in episode["train"]:
        grid = pair["input"]
        selected = p.selected_color(p.one_ring_halo(grid))
        cells = next(cells for color, cells in p._components(grid) if color == selected)
        source_sizes.add(len(cells))
        is_straight = (
            len({r for r, _c in cells}) == 1
            or len({c for _r, c in cells}) == 1
        )
        topologies.add("straight" if is_straight else "bent")
        height = max(r for r, _c in cells) - min(r for r, _c in cells) + 1
        width = max(c for _r, c in cells) - min(c for _r, c in cells) + 1
        orientations.add("horizontal" if width > height else "vertical")
        straight_matches.append(
            _longest_straight_object_shortcut(p, grid) == pair["output"]
        )
        widest_matches.append(_widest_object_shortcut(p, grid) == pair["output"])

    assert source_sizes == {6, 8}
    assert topologies == {"straight", "bent"}
    assert orientations == {"horizontal", "vertical"}
    assert not all(straight_matches)
    assert not all(widest_matches)



def _source_size_rank_shortcut(p, grid, rank):
    ordered = sorted(
        p._components(grid),
        key=lambda item: (-len(item[1]), item[0]),
    )
    color, _cells = ordered[rank - 1]
    return _expand_one_ring_color(p, grid, color)


def test_two_step_lessons_vary_selected_source_size_rank(p):
    episode = p.generate(0, {"halo_mode": "selected_two_step"}, 3, 4)
    ranks = set()
    rank_two_matches = []
    rank_three_matches = []
    for pair in episode["train"]:
        grid = pair["input"]
        selected = p.selected_color(p.one_ring_halo(grid))
        ordered = sorted(
            p._components(grid),
            key=lambda item: (-len(item[1]), item[0]),
        )
        ranks.add(next(index + 1 for index, (color, _cells) in enumerate(ordered) if color == selected))
        rank_two_matches.append(
            _source_size_rank_shortcut(p, grid, 2) == pair["output"]
        )
        rank_three_matches.append(
            _source_size_rank_shortcut(p, grid, 3) == pair["output"]
        )

    assert ranks == {2, 3}
    assert not all(rank_two_matches)
    assert not all(rank_three_matches)

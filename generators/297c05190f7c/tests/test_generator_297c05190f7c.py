"""Focused regressions for generator 297c05190f7c."""
from __future__ import annotations

import copy
import importlib
import itertools
import random
from collections import deque

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "297c05190f7c"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.297c05190f7c.generator"
)


def _independent_components4(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells = set()
            while queue:
                row, col = queue.popleft()
                cells.add((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append((color, cells))
    return components


def _independent_answer(grid):
    output = [[0 for _ in row] for row in grid]
    for color, cells in _independent_components4(grid):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        for row in range(min(rows), max(rows) + 1):
            for col in range(min(cols), max(cols) + 1):
                output[row][col] = color
    return output


def test_rule_hash_and_all_canonical_pairs_are_pinned() -> None:
    assert GEN.RULE_HASH == "3cad5a2fcf1f"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert _independent_answer(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_boundary_override_cartesian_product_is_exactly_observable(difficulty) -> None:
    for grid_h, grid_w, scene_profile in itertools.product(
        (8, 12), (9, 13), GEN.SCENE_PROFILES
    ):
        requested = {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "scene_profile": scene_profile,
        }
        grid = GEN.generate(
            7301,
            grid_h * 100 + grid_w,
            difficulty=difficulty,
            **requested,
        )
        assert GEN.observe_overrides(grid) == requested
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == _independent_answer(grid)


def test_component_split_refutes_color_and_eight_connectivity_shortcuts() -> None:
    for difficulty in ("easy", "medium", "hard"):
        grid = GEN.generate(
            811,
            1,
            difficulty=difficulty,
            scene_profile="component_split",
        )
        analysis = GEN._analyze(grid)
        assert analysis["component_count"] == 3
        assert len(analysis["foreground_colors"]) == 2
        assert analysis["diagonal_same_color_pairs"]
        expected = _independent_answer(grid)
        assert GEN.CANONICAL_SHORTCUTS["one_bbox_per_color"](grid) != expected
        assert GEN.CANONICAL_SHORTCUTS["eight_connected_objects"](grid) != expected


def test_every_sliding_three_example_window_is_identifiable() -> None:
    for difficulty in ("easy", "medium", "hard"):
        pairs = []
        for sample_index in range(8):
            grid = GEN.generate(991, sample_index, difficulty=difficulty)
            pairs.append({"input": grid, "output": _independent_answer(grid)})
        for start in range(5):
            assert {
                GEN.schedule_profile(991, index, difficulty)
                for index in range(start, start + GEN.EXAMPLES_NEEDED)
            } == set(GEN.SCHEDULE_PROFILES)
            assert GEN.lesson_identifiable(
                pairs[start : start + GEN.EXAMPLES_NEEDED],
                pairs[start + GEN.EXAMPLES_NEEDED],
            ) == []


def test_unknown_and_invalid_overrides_are_rejected_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=7)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, grid_h=7)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, scene_profile="not_a_profile")


def test_determinism_fresh_returns_and_process_rng_purity() -> None:
    random.seed(24681357)
    before = random.getstate()
    first = GEN.generate(19, 7, difficulty="medium")
    second = GEN.generate(19, 7, difficulty="medium")
    assert random.getstate() == before
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(19, 7, difficulty="medium") == second


def test_self_check_rejects_non_teaching_recombinations() -> None:
    one_component = [[0] * 9 for _ in range(8)]
    one_component[1][1] = 2
    one_component[2][1] = 2
    one_component[2][2] = 2
    assert GEN.self_check(one_component)

    already_rectangular = [[0] * 9 for _ in range(8)]
    for row in (1, 2):
        for col in (1, 2):
            already_rectangular[row][col] = 2
    for row in (5, 6):
        for col in (6, 7):
            already_rectangular[row][col] = 4
    assert GEN.self_check(already_rectangular)


def _near_public_corner(component, height, width, margin=2):
    r1, c1, r2, c2 = component["bbox"]
    return (
        min(r1, height - 1 - r2) <= margin
        and min(c1, width - 1 - c2) <= margin
    )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_expanded_profile_has_a_nonrectangular_component_away_from_corners(
    difficulty,
) -> None:
    for seed in (0, 1, 17):
        grid = GEN.generate(
            seed,
            2,
            difficulty=difficulty,
            grid_h=8,
            grid_w=9,
            scene_profile="expanded",
        )
        analysis = GEN._analyze(grid)
        assert any(
            not component["solid"]
            and not _near_public_corner(component, len(grid), len(grid[0]))
            for component in analysis["components"]
        )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_expanded_profile_has_a_nonrectangular_bbox_larger_than_three(
    difficulty,
) -> None:
    for seed in (0, 1, 17):
        grid = GEN.generate(
            seed,
            2,
            difficulty=difficulty,
            grid_h=8,
            grid_w=9,
            scene_profile="expanded",
        )
        analysis = GEN._analyze(grid)
        assert any(
            not component["solid"]
            and max(
                component["bbox"][2] - component["bbox"][0] + 1,
                component["bbox"][3] - component["bbox"][1] + 1,
            )
            > 3
            for component in analysis["components"]
        )


def test_spatial_and_extent_shortcuts_fit_canonical_pairs_but_not_curriculum(
) -> None:
    shortcut_names = ("corner_components_only", "bbox_extent_at_most_three")
    pairs = canonical_pairs(TASK_ID)
    for name in shortcut_names:
        assert name in GEN.CANONICAL_SHORTCUTS
        shortcut = GEN.CANONICAL_SHORTCUTS[name]
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs)

    for difficulty in ("easy", "medium", "hard"):
        demos = []
        for sample_index in range(GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(1701, sample_index, difficulty=difficulty)
            demos.append({"input": grid, "output": _independent_answer(grid)})
        for name in shortcut_names:
            shortcut = GEN.CANONICAL_SHORTCUTS[name]
            assert any(
                shortcut(demo["input"]) != demo["output"] for demo in demos
            )
        query_grid = GEN.generate(
            1701, GEN.EXAMPLES_NEEDED, difficulty=difficulty
        )
        assert GEN.lesson_identifiable(
            demos,
            {"input": query_grid, "output": _independent_answer(query_grid)},
        ) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_scene_profile_refutes_corner_components_only(difficulty) -> None:
    shortcut = GEN.CANONICAL_SHORTCUTS["corner_components_only"]
    for profile in GEN.SCENE_PROFILES:
        for seed in (0, 1, 17):
            grid = GEN.generate(
                seed,
                11,
                difficulty=difficulty,
                grid_h=8,
                grid_w=9,
                scene_profile=profile,
            )
            assert shortcut(grid) != _independent_answer(grid)


def test_distribution_probe_independently_detects_new_shortcuts() -> None:
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path

    probe_path = (
        Path(__file__).resolve().parents[1] / "workspace" / "distribution_probe.py"
    )
    spec = spec_from_file_location("distribution_probe_297c05190f7c", probe_path)
    assert spec is not None and spec.loader is not None
    probe = module_from_spec(spec)
    spec.loader.exec_module(probe)

    grid = [[0] * 9 for _ in range(9)]
    for row, col in ((3, 3), (4, 3), (4, 4)):
        grid[row][col] = 2
    for row, col in (
        (0, 5),
        (1, 5),
        (2, 5),
        (3, 5),
        (3, 6),
        (3, 7),
        (3, 8),
    ):
        grid[row][col] = 3

    summary = probe.summarize_grid(grid)
    assert summary["component_count"] == 2
    assert summary["noncorner_nonrectangular_components"] == 1
    assert summary["bbox_extent_over_three_components"] == 1
    intended = probe.intended_output(grid)
    assert probe.corner_components_only(grid) != intended
    assert probe.bbox_extent_at_most_three(grid) != intended


def _independent_has_full_2x2(cells) -> bool:
    return any(
        {(row, col), (row + 1, col), (row, col + 1), (row + 1, col + 1)}
        <= cells
        for row, col in cells
    )


def _independent_has_adjacency_cycle(cells) -> bool:
    edge_count = sum(
        (row + dr, col + dc) in cells
        for row, col in cells
        for dr, dc in ((1, 0), (0, 1))
    )
    return edge_count >= len(cells)


def _independent_has_enclosed_hole(cells) -> bool:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    r1, r2 = min(rows), max(rows)
    c1, c2 = min(cols), max(cols)
    background = {
        (row, col)
        for row in range(r1, r2 + 1)
        for col in range(c1, c2 + 1)
        if (row, col) not in cells
    }
    frontier = [
        cell
        for cell in background
        if cell[0] in (r1, r2) or cell[1] in (c1, c2)
    ]
    reachable = set(frontier)
    while frontier:
        row, col = frontier.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = (row + dr, col + dc)
            if neighbor in background and neighbor not in reachable:
                reachable.add(neighbor)
                frontier.append(neighbor)
    return bool(background - reachable)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_expanded_profile_refutes_shape_topology_and_density_shortcuts(
    difficulty,
) -> None:
    shortcut_names = (
        "thin_components_only",
        "acyclic_components_only",
        "hole_free_components_only",
        "bbox_density_at_most_five_sixths",
        "component_size_at_most_eight",
    )
    pairs = canonical_pairs(TASK_ID)
    for name in shortcut_names:
        assert name in GEN.CANONICAL_SHORTCUTS
        shortcut = GEN.CANONICAL_SHORTCUTS[name]
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs)

    for seed in (0, 1, 17):
        grid = GEN.generate(
            seed,
            2,
            difficulty=difficulty,
            grid_h=8,
            grid_w=9,
            scene_profile="expanded",
        )
        expected = _independent_answer(grid)
        components = _independent_components4(grid)
        discriminating = []
        for _, cells in components:
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
            if (
                len(cells) > 8
                and len(cells) * 6 > area * 5
                and _independent_has_full_2x2(cells)
                and _independent_has_adjacency_cycle(cells)
                and _independent_has_enclosed_hole(cells)
            ):
                discriminating.append(cells)
        assert discriminating
        for name in shortcut_names:
            assert GEN.CANONICAL_SHORTCUTS[name](grid) != expected


def test_shortcut_miner_independently_detects_shape_family_shortcuts() -> None:
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path

    miner_path = (
        Path(__file__).resolve().parents[1] / "workspace" / "shortcut_miner.py"
    )
    spec = spec_from_file_location("shortcut_miner_297c05190f7c", miner_path)
    assert spec is not None and spec.loader is not None
    miner = module_from_spec(spec)
    spec.loader.exec_module(miner)

    grid = [[0] * 9 for _ in range(8)]
    for row in range(4):
        for col in range(4):
            if (row, col) != (1, 1):
                grid[row][col] = 2
    intended = miner.intended_output(grid)
    properties = miner.component_properties(grid)[0]
    assert properties["has_full_2x2"] is True
    assert properties["has_adjacency_cycle"] is True
    assert properties["has_enclosed_hole"] is True
    assert properties["size"] == 15
    assert properties["density_numerator"] * 6 > properties["bbox_area"] * 5
    for name in (
        "thin_components_only",
        "acyclic_components_only",
        "hole_free_components_only",
        "bbox_density_at_most_five_sixths",
        "component_size_at_most_eight",
    ):
        assert miner.RIVALS[name](grid) != intended


def _independent_component_geometry(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    r1, r2 = min(rows), max(rows)
    c1, c2 = min(cols), max(cols)
    area = (r2 - r1 + 1) * (c2 - c1 + 1)
    missing = {
        (row, col)
        for row in range(r1, r2 + 1)
        for col in range(c1, c2 + 1)
        if (row, col) not in cells
    }
    max_fill_distance = max(
        (
            min(abs(row - rr) + abs(col - cc) for rr, cc in cells)
            for row, col in missing
        ),
        default=0,
    )
    return {
        "bbox_height": r2 - r1 + 1,
        "bbox_width": c2 - c1 + 1,
        "bbox_area": area,
        "size": len(cells),
        "fill_gain": len(missing),
        "max_fill_manhattan_distance": max_fill_distance,
    }


def _independent_diagonal_touch(first, second) -> bool:
    return any(
        (row + dr, col + dc) in second
        for row, col in first
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1))
    )


def _independent_min_manhattan_distance(first, second) -> int:
    return min(
        abs(row - rr) + abs(col - cc)
        for row, col in first
        for rr, cc in second
    )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_canonical_pair_has_sparse_deep_large_component(difficulty) -> None:
    for seed in (0, 1, 17):
        grid = GEN.generate(
            seed,
            0,
            difficulty=difficulty,
            grid_h=8,
            grid_w=9,
            scene_profile="canonical_pair",
        )
        profiles = [
            _independent_component_geometry(cells)
            for _, cells in _independent_components4(grid)
        ]
        assert any(
            profile["bbox_area"] > 16
            and profile["fill_gain"] > 4
            and profile["size"] * 9 < profile["bbox_area"] * 5
            and profile["max_fill_manhattan_distance"] > 3
            and profile["bbox_height"] != profile["bbox_width"]
            for profile in profiles
        )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_component_split_has_an_elongated_changing_component(difficulty) -> None:
    for seed in (0, 1, 17):
        grid = GEN.generate(
            seed,
            1,
            difficulty=difficulty,
            grid_h=8,
            grid_w=9,
            scene_profile="component_split",
        )
        profiles = [
            _independent_component_geometry(cells)
            for _, cells in _independent_components4(grid)
        ]
        assert any(
            profile["fill_gain"] > 0
            and max(profile["bbox_height"], profile["bbox_width"])
            > 3 * min(profile["bbox_height"], profile["bbox_width"])
            for profile in profiles
        )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_expanded_profile_has_large_dense_object_and_irregular_same_color_pair(
    difficulty,
) -> None:
    for seed in (0, 1, 17):
        grid = GEN.generate(
            seed,
            2,
            difficulty=difficulty,
            grid_h=8,
            grid_w=9,
            scene_profile="expanded",
        )
        components = _independent_components4(grid)
        profiles = [
            (color, cells, _independent_component_geometry(cells))
            for color, cells in components
        ]
        assert any(
            profile["size"] > 20
            and profile["fill_gain"] > 0
            and profile["size"] * 6 > profile["bbox_area"] * 5
            and _independent_has_full_2x2(cells)
            and _independent_has_adjacency_cycle(cells)
            and _independent_has_enclosed_hole(cells)
            for _, cells, profile in profiles
        )

        assert any(
            first_profile["fill_gain"] > 0
            and second_profile["fill_gain"] > 0
            and first_profile["size"] != second_profile["size"]
            and first_profile["fill_gain"] != second_profile["fill_gain"]
            and not _independent_diagonal_touch(first_cells, second_cells)
            and 1 < _independent_min_manhattan_distance(first_cells, second_cells) < 4
            for index, (first_color, first_cells, first_profile) in enumerate(profiles)
            for second_color, second_cells, second_profile in profiles[index + 1 :]
            if first_color == second_color
        )


def test_round3_shortcuts_fit_canonical_pairs_but_not_curriculum() -> None:
    shortcut_names = (
        "fill_manhattan_distance_at_most_one",
        "fill_gain_at_most_four",
        "bbox_density_at_least_five_ninths",
        "aspect_ratio_at_most_three_halves",
        "bbox_area_at_most_sixteen",
        "component_size_at_most_fifteen",
        "extent_at_most_three_or_square",
        "largest_per_color_unless_equal_diagonal_or_far",
    )
    pairs = canonical_pairs(TASK_ID)
    for name in shortcut_names:
        assert name in GEN.CANONICAL_SHORTCUTS
        shortcut = GEN.CANONICAL_SHORTCUTS[name]
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs)

    for difficulty in ("easy", "medium", "hard"):
        demos = []
        for sample_index in range(GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(2903, sample_index, difficulty=difficulty)
            demos.append({"input": grid, "output": _independent_answer(grid)})
        for name in shortcut_names:
            shortcut = GEN.CANONICAL_SHORTCUTS[name]
            assert any(shortcut(demo["input"]) != demo["output"] for demo in demos)
        query_grid = GEN.generate(2903, GEN.EXAMPLES_NEEDED, difficulty=difficulty)
        assert GEN.lesson_identifiable(
            demos,
            {"input": query_grid, "output": _independent_answer(query_grid)},
        ) == []


def test_shortcut_miner_detects_round3_geometry_and_grouping_shortcuts() -> None:
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path

    miner_path = (
        Path(__file__).resolve().parents[1] / "workspace" / "shortcut_miner.py"
    )
    spec = spec_from_file_location("shortcut_miner_round3_297c05190f7c", miner_path)
    assert spec is not None and spec.loader is not None
    miner = module_from_spec(spec)
    spec.loader.exec_module(miner)

    sparse = [[0] * 9 for _ in range(8)]
    for col in range(8):
        sparse[0][col] = 2
    for row in range(1, 6):
        sparse[row][0] = 2
    for row, col in ((6, 3), (7, 3), (7, 4)):
        sparse[row][col] = 3

    elongated = [[0] * 9 for _ in range(8)]
    for col in range(8):
        elongated[0][col] = 4
    elongated[1][0] = 4
    for row, col in ((3, 3), (4, 3), (4, 4), (5, 5)):
        elongated[row][col] = 6

    grouped = [[0] * 9 for _ in range(8)]
    for row in range(5):
        for col in range(5):
            if (row, col) not in {(1, 1), (2, 2)}:
                grouped[row][col] = 5
    for row, col in ((0, 6), (1, 6), (1, 7)):
        grouped[row][col] = 5
    for row, col in ((3, 6), (4, 6), (4, 7)):
        grouped[row][col] = 6
    for row, col in ((6, 3), (7, 3), (7, 4)):
        grouped[row][col] = 7

    sparse_profile = max(
        miner.component_properties(sparse), key=lambda component: component["bbox_area"]
    )
    assert sparse_profile["fill_gain"] > 4
    assert sparse_profile["max_fill_manhattan_distance"] > 3
    assert sparse_profile["density_numerator"] * 9 < sparse_profile["bbox_area"] * 5

    elongated_profile = max(
        miner.component_properties(elongated),
        key=lambda component: max(component["bbox_height"], component["bbox_width"]),
    )
    assert max(elongated_profile["bbox_height"], elongated_profile["bbox_width"]) > (
        3 * min(elongated_profile["bbox_height"], elongated_profile["bbox_width"])
    )

    expected_by_grid = {
        "fill_manhattan_distance_at_most_one": sparse,
        "fill_gain_at_most_four": sparse,
        "bbox_density_at_least_five_ninths": sparse,
        "aspect_ratio_at_most_three_halves": elongated,
        "bbox_area_at_most_sixteen": sparse,
        "component_size_at_most_fifteen": grouped,
        "extent_at_most_three_or_square": sparse,
        "largest_per_color_unless_equal_diagonal_or_far": grouped,
    }
    for name, grid in expected_by_grid.items():
        assert name in miner.RIVALS
        assert miner.RIVALS[name](grid) != miner.intended_output(grid)


def test_default_distribution_reaches_canonical_component_scale() -> None:
    """At least one default lesson must look like the size-3/4 public objects."""
    maximum_component_sizes = []
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(1, 9):
            grid = GEN.generate(seed, seed, difficulty=difficulty)
            maximum_component_sizes.append(
                max(len(cells) for _, cells in _independent_components4(grid))
            )
    assert min(maximum_component_sizes) <= 8
    assert max(maximum_component_sizes) > 20


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_scheduled_canonical_scale_branch_keeps_shortcut_pressure(difficulty) -> None:
    grid = GEN.generate(
        3,
        3,
        difficulty=difficulty,
        scene_profile="canonical_pair",
    )
    profiles = [
        _independent_component_geometry(cells)
        for _, cells in _independent_components4(grid)
    ]
    assert max(profile["size"] for profile in profiles) <= 8
    assert any(
        profile["fill_gain"] > 4
        and profile["max_fill_manhattan_distance"] > 1
        and profile["size"] * 9 < profile["bbox_area"] * 5
        and max(profile["bbox_height"], profile["bbox_width"]) * 2
        > min(profile["bbox_height"], profile["bbox_width"]) * 3
        and max(profile["bbox_height"], profile["bbox_width"]) > 3
        and profile["bbox_height"] != profile["bbox_width"]
        for profile in profiles
    )

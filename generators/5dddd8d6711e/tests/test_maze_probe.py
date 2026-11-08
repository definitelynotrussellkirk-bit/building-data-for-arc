"""Independent oracle fixtures; no generator implementation is imported here."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
SPEC = importlib.util.spec_from_file_location("selected_maze_probe", HOME / "workspace/maze_probe.py")
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


def lattice(heights, widths, edges, red, green):
    """Small literal-fixture builder, independent of the selected generator."""
    row_starts, col_starts = [], []
    r = c = 1
    for height in heights:
        row_starts.append(r)
        r += height + 1
    for width in widths:
        col_starts.append(c)
        c += width + 1
    grid = [[1] * c for _ in range(r)]
    rooms = []
    for i, height in enumerate(heights):
        for j, width in enumerate(widths):
            room = [(rr, cc) for rr in range(row_starts[i], row_starts[i] + height)
                    for cc in range(col_starts[j], col_starts[j] + width)]
            rooms.append(room)
            for rr, cc in room:
                grid[rr][cc] = 0
    for a, b in edges:
        ai, aj = divmod(a, len(widths))
        bi, bj = divmod(b, len(widths))
        if ai == bi:
            rr, cc = row_starts[ai], col_starts[max(aj, bj)] - 1
        else:
            rr, cc = row_starts[max(ai, bi)] - 1, col_starts[aj]
        grid[rr][cc] = 7
    for rid, color in ((red, 2), (green, 3)):
        rr, cc = rooms[rid][-1]
        grid[rr][cc] = color
    return grid, rooms


def painted(grid, rooms, path):
    expected = [[v if v in (1, 7, 9) else 0 for v in row] for row in grid]
    for rid in path:
        for r, c in rooms[rid]:
            expected[r][c] = 8
    return expected


def canonical_record():
    for parent in HOME.parents:
        for relative in ("shared/data/canonical/puzzles.jsonl", "data/canonical/puzzles.jsonl"):
            ledger = parent / relative
            if ledger.is_file():
                with ledger.open() as handle:
                    for line in handle:
                        if '"task_id": "5dddd8d6711e"' in line:
                            return json.loads(line)
    raise AssertionError("selected canonical record missing")


@pytest.mark.parametrize("split,index", [("train", 0), ("train", 1), ("test", 0)])
def test_all_three_original_pairs(split, index):
    records = canonical_record()[split]
    pair = records[index] if isinstance(records, list) else records
    assert PROBE.solve(pair["input"]) == pair["output"]


def test_sorted_bfs_selects_one_equal_length_route():
    grid, rooms = lattice([1, 1], [1, 1], [(0, 1), (0, 2), (1, 3), (2, 3)], 0, 3)
    assert PROBE.solve(grid) == painted(grid, rooms, [0, 1, 3])
    features = PROBE.inspect_grid(grid)
    assert features["path"] == [0, 1, 3]
    assert features["shortest_path_count"] == 2
    assert features["cycle_rank"] == 1


def test_tie_is_resolved_from_red_and_is_not_endpoint_swap_invariant():
    edges = [(0, 3), (0, 1), (1, 2), (2, 5), (3, 6), (4, 7), (4, 5), (6, 7)]
    grid, rooms = lattice([1, 1, 1], [1, 1, 1], edges, 1, 7)
    swapped, _ = lattice([1, 1, 1], [1, 1, 1], edges, 7, 1)
    assert PROBE.solve(grid) == painted(grid, rooms, [1, 0, 3, 6, 7])
    assert PROBE.solve(swapped) == painted(swapped, rooms, [7, 4, 5, 2, 1])


def test_walls_9_and_nonwall_noise_have_distinct_roles():
    grid = [
        [9, 9, 9, 9, 9, 9, 9],
        [9, 2, 7, 3, 9, 4, 9],
        [9, 4, 9, 9, 9, 5, 9],
        [9, 9, 9, 8, 9, 6, 9],
        [9, 9, 9, 9, 9, 9, 9],
    ]
    expected = [
        [9, 9, 9, 9, 9, 9, 9],
        [9, 8, 7, 8, 9, 0, 9],
        [9, 8, 9, 9, 9, 0, 9],
        [9, 9, 9, 0, 9, 0, 9],
        [9, 9, 9, 9, 9, 9, 9],
    ]
    assert PROBE.solve(grid) == expected
    features = PROBE.inspect_grid(grid)
    assert features["noise_on_path"] == 1
    assert features["noise_off_path"] == 4
    assert features["shared_noise_colors"] == [4]
    assert features["unreachable_rooms"] == 2


@pytest.mark.parametrize("grid,expected,path", [
    ([[1, 1, 1, 1, 1], [1, 2, 1, 3, 1], [1, 1, 1, 1, 1]],
     [[1, 1, 1, 1, 1], [1, 0, 1, 0, 1], [1, 1, 1, 1, 1]], []),
    ([[1, 1, 1, 1], [1, 2, 3, 1], [1, 1, 1, 1]],
     [[1, 1, 1, 1], [1, 8, 8, 1], [1, 1, 1, 1]], [0]),
])
def test_disconnected_and_same_room_endpoints(grid, expected, path):
    assert PROBE.solve(grid) == expected
    assert PROBE.inspect_grid(grid)["path"] == path


def test_one_door_links_all_distinct_neighboring_rooms():
    grid = [[1, 1, 1, 1, 1], [1, 1, 2, 1, 1], [1, 0, 7, 3, 1],
            [1, 1, 0, 1, 1], [1, 1, 1, 1, 1]]
    expected = [[1, 1, 1, 1, 1], [1, 1, 8, 1, 1], [1, 0, 7, 8, 1],
                [1, 1, 0, 1, 1], [1, 1, 1, 1, 1]]
    assert PROBE.solve(grid) == expected
    assert PROBE.inspect_grid(grid)["edge_count"] == 6


def test_adjacent_doors_do_not_relay_through_each_other():
    grid = [[1, 1, 1, 1, 1, 1], [1, 2, 7, 7, 3, 1], [1, 1, 1, 1, 1, 1]]
    assert PROBE.solve(grid)[1] == [1, 0, 7, 7, 0, 1]
    assert PROBE.inspect_grid(grid)["edge_count"] == 0


def test_irregular_rooms_paint_only_their_connected_cells():
    grid = [[1, 1, 1, 1, 1], [1, 2, 0, 0, 1], [1, 0, 1, 7, 1],
            [1, 0, 1, 3, 1], [1, 1, 1, 1, 1]]
    expected = [[1, 1, 1, 1, 1], [1, 8, 8, 8, 1], [1, 8, 1, 7, 1],
                [1, 8, 1, 8, 1], [1, 1, 1, 1, 1]]
    assert PROBE.solve(grid) == expected
    assert PROBE.inspect_grid(grid)["all_rooms_rectangular"] is False


def test_marker_selection_uses_first_room_not_first_marker_pixel():
    grid = [[1, 1, 1, 1, 1, 1, 1], [1, 0, 1, 2, 7, 3, 1],
            [1, 0, 1, 0, 1, 0, 1], [1, 2, 1, 0, 1, 0, 1],
            [1, 1, 1, 1, 1, 1, 1]]
    features = PROBE.inspect_grid(grid)
    assert features["red_room"] == 0
    assert features["red_marker_count"] == 2
    assert features["path"] == []
    assert all(v != 8 for row in PROBE.solve(grid) for v in row)


def test_fewer_doors_wins_even_when_it_paints_more_area():
    edges = [(0, 1), (1, 2), (2, 5), (5, 4), (4, 3), (3, 0)]
    grid, rooms = lattice([5, 1], [1, 5, 1], edges, 0, 2)
    features = PROBE.inspect_grid(grid)
    assert features["path"] == [0, 1, 2]
    assert features["path_area"] == 35
    assert sum(len(rooms[i]) for i in [0, 3, 4, 5, 2]) == 17
    assert PROBE.solve(grid) == painted(grid, rooms, [0, 1, 2])


@pytest.mark.parametrize("grid", [[], [[]], [[1, 2], [3]], [[2, True, 3]], [[2, 10, 3]], [[0] * 31]])
def test_malformed_grids_are_rejected(grid):
    with pytest.raises(ValueError):
        PROBE.solve(grid)


@pytest.mark.parametrize("grid", [[[0]], [[2]], [[3]]])
def test_missing_endpoint_is_undefined_instead_of_a_fabricated_output(grid):
    with pytest.raises(ValueError, match="marker"):
        PROBE.solve(grid)


def test_authoring_normalization_keeps_dictionary_test_pair():
    class CatalogFixture:
        def get(self, task_id):
            assert task_id == "5dddd8d6711e"
            return {"variants": [{"train": [{"input": ["123"], "output": ["183"]}],
                                   "test": {"input": ["203"], "output": ["888"]}}]}
    pairs = PROBE.canonical_pairs(CatalogFixture())
    assert [p["label"] for p in pairs] == ["variant0/train0", "variant0/test0"]
    assert pairs[-1]["output"] == [[8, 8, 8]]


def test_sampler_reports_overlap_and_exercises_all_three_starting_offsets():
    schedule = PROBE.lesson_schedule(2, seed_start=40, bands=("easy", "hard"))
    assert len(schedule["draws"]) == 24
    assert len(schedule["lessons"]) == 12
    assert len({draw["id"] for draw in schedule["draws"]}) == 24
    for band in ("easy", "hard"):
        for seed in (40, 41):
            lessons = [row for row in schedule["lessons"] if row["band"] == band and row["seed"] == seed]
            assert [row["start_index"] for row in lessons] == [0, 1, 2]
            assert [row["demo_indices"] for row in lessons] == [[0, 1, 2], [1, 2, 3], [2, 3, 4]]
            assert [row["query_index"] for row in lessons] == [3, 4, 5]


def test_query_changing_survivors_are_distinct_from_all_survivors():
    demos = [{"one": "matches", "two": "matches", "three": "differs"}] * 3
    query = {"one": "matches", "two": "differs", "three": "differs"}
    result = PROBE.lesson_outcome(demos, query, ["one", "two", "three"])
    assert result["survivors"] == ["one", "two"]
    assert result["query_changing_survivors"] == ["two"]
    assert result["complete_witness_demo_indices"] == []


def test_candidate_errors_do_not_count_as_successful_witness_disagreements():
    result = PROBE.lesson_outcome([{"one": "differs", "two": "error"}] * 3,
                                   {"one": "differs", "two": "differs"}, ["one", "two"])
    assert result["survivors"] == []
    assert result["complete_witness_demo_indices"] == []

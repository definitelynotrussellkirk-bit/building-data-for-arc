"""Source-portable regressions for exact controls and room-graph structure.

Observations come from the emitted cells, independently of generator metadata.
No reference program or private solve labels are needed by these checks.
"""
from collections import deque
import unittest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "1b2b9283b4ab"
WALLS = {1, 7, 9}
SEEDS = {2, 3, 4, 5, 6}
DOMAINS = {
    "n_room_rows": range(1, 4),
    "n_room_cols": range(1, 7),
    "room_h": range(2, 7),
    "room_w": range(2, 7),
    "n_seeds": range(1, 6),
}
DEGENERATES = ("single_room", "no_doors", "two_seeds_same_color")


def neighbours(cell, height, width):
    r, c = cell
    return [(rr, cc) for rr, cc in ((r - 1, c), (r + 1, c),
                                   (r, c - 1), (r, c + 1))
            if 0 <= rr < height and 0 <= cc < width]


def parse_rooms(grid):
    """Find non-wall components and graph edges without layout assumptions."""
    height, width = len(grid), len(grid[0])
    owner, rooms, doors, edges = {}, [], {}, set()
    for r in range(height):
        for c in range(width):
            if grid[r][c] in WALLS or (r, c) in owner:
                continue
            room_id = len(rooms)
            cells, queue = set(), deque([(r, c)])
            owner[r, c] = room_id
            while queue:
                cell = queue.popleft()
                cells.add(cell)
                for other in neighbours(cell, height, width):
                    rr, cc = other
                    if grid[rr][cc] not in WALLS and other not in owner:
                        owner[other] = room_id
                        queue.append(other)
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            rooms.append({
                "cells": cells,
                "bounds": (min(rows), max(rows), min(cols), max(cols)),
                "seed_cells": [(rr, cc) for rr, cc in cells
                               if grid[rr][cc] in SEEDS],
                "colors": {grid[rr][cc] for rr, cc in cells
                           if grid[rr][cc] in SEEDS},
            })
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 7:
                adjacent = {owner[other] for other in neighbours((r, c), height, width)
                            if other in owner}
                doors[r, c] = adjacent
                if len(adjacent) == 2:
                    edges.add(tuple(sorted(adjacent)))
    return rooms, doors, edges


def observe(grid):
    rooms, _, _ = parse_rooms(grid)
    bounds = [room["bounds"] for room in rooms]
    return {
        "n_room_rows": len({r0 for r0, _, _, _ in bounds}),
        "n_room_cols": len({c0 for _, _, c0, _ in bounds}),
        "room_h": {r1 - r0 + 1 for r0, r1, _, _ in bounds},
        "room_w": {c1 - c0 + 1 for _, _, c0, c1 in bounds},
        "n_seeds": sum(bool(room["seed_cells"]) for room in rooms),
    }


class TestRoomGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = find_root(__file__)
        cls.generator, cls.source, cls.source_sha256 = load_selected_generator(
            TASK_ID, root=cls.root)

    def draw(self, *, difficulty="medium", seed=31, sample_index=0, **overrides):
        return self.generator.generate(seed, sample_index, difficulty=difficulty,
                                       **overrides)

    def assert_valid(self, grid, *, meta=None):
        self.assertTrue(grid and grid[0])
        self.assertLessEqual(len(grid), 30)
        self.assertLessEqual(len(grid[0]), 30)
        self.assertEqual({len(row) for row in grid}, {len(grid[0])})
        self.assertTrue(all(type(value) is int and 0 <= value <= 9 and value != 8
                            for row in grid for value in row))
        rooms, doors, edges = parse_rooms(grid)
        self.assertTrue(rooms)
        self.assertTrue(any(room["seed_cells"] for room in rooms))
        for room in rooms:
            r0, r1, c0, c1 = room["bounds"]
            rectangle = {(r, c) for r in range(r0, r1 + 1)
                         for c in range(c0, c1 + 1)}
            self.assertEqual(room["cells"], rectangle, "room interior is not rectangular")
        for location, adjacent in doors.items():
            self.assertEqual(len(adjacent), 2,
                             f"door at {location} must join two distinct rooms")
        self.assertEqual(self.generator.self_check(grid, meta=meta), [])
        return rooms, doors, edges

    def assert_controls(self, grid, **expected):
        measured = observe(grid)
        for key, value in expected.items():
            self.assertEqual(measured[key], {value} if key in ("room_h", "room_w")
                             else value, f"{key} was not honored exactly")

    def assert_connected(self, count, edges):
        reached, queue = {0}, deque([0])
        while queue:
            room = queue.popleft()
            for a, b in edges:
                other = b if a == room else a if b == room else None
                if other is not None and other not in reached:
                    reached.add(other)
                    queue.append(other)
        self.assertEqual(len(reached), count, "room graph is disconnected")

    def test_unknown_controls_and_textures_are_rejected(self):
        for overrides in ({"n_seed": 2}, {"door_position": "random"},
                          {"texture": "grdi"}, {"door_positions": "invalid"},
                          {"seed_positions": "invalid"}):
            with self.subTest(overrides=overrides):
                with self.assertRaises((TypeError, ValueError)):
                    self.draw(**overrides)

    def test_integer_controls_do_not_coerce_bool_float_or_string(self):
        for key, domain in DOMAINS.items():
            value = 3 if key == "n_room_cols" else 2
            for invalid in (True, float(value), str(value)):
                with self.subTest(key=key, invalid=invalid):
                    with self.assertRaises((TypeError, ValueError)):
                        self.draw(**{key: invalid})

    def test_integer_controls_reject_values_outside_public_domains(self):
        for key, domain in DOMAINS.items():
            for invalid in (domain.start - 1, domain.stop):
                with self.subTest(key=key, invalid=invalid):
                    with self.assertRaises(ValueError):
                        self.draw(**{key: invalid})

    def test_each_legal_lone_numeric_override_is_realizable_in_every_band(self):
        for difficulty in (None, "easy", "medium", "hard"):
            for key, domain in DOMAINS.items():
                for value in domain:
                    with self.subTest(difficulty=difficulty, key=key, value=value):
                        grid = self.draw(difficulty=difficulty, **{key: value})
                        self.assert_valid(grid)
                        self.assert_controls(grid, **{key: value})

    def test_explicit_canvas_conflicts_raise_instead_of_clamping_room_width(self):
        for ncols, width in ((5, 5), (6, 6)):
            with self.subTest(ncols=ncols, width=width):
                with self.assertRaises(ValueError):
                    self.draw(difficulty="hard", n_room_cols=ncols, room_w=width)

    def test_more_seeds_than_explicit_room_capacity_is_rejected(self):
        with self.assertRaises(ValueError):
            self.draw(n_room_rows=1, n_room_cols=1, n_seeds=2)

    def test_compatible_joint_numeric_controls_are_exact(self):
        expected = dict(n_room_rows=3, n_room_cols=6, room_h=6, room_w=3, n_seeds=5)
        grid = self.draw(difficulty="easy", **expected)
        self.assert_valid(grid)
        self.assert_controls(grid, **expected)
        self.assertEqual((len(grid), len(grid[0])), (22, 25))

    def test_observer_reports_values_visible_in_cells(self):
        expected = dict(n_room_rows=2, n_room_cols=3, room_h=2, room_w=4, n_seeds=3)
        grid = self.draw(**expected)
        self.assert_controls(grid, **expected)
        observer = getattr(self.generator, "observe_overrides", None)
        self.assertTrue(callable(observer), "generator needs an observe_overrides hook")
        actual = observer(grid)
        for key, value in expected.items():
            self.assertEqual(actual[key], value)

    def test_chain_is_a_connected_path_of_actual_rooms(self):
        rooms, _, edges = self.assert_valid(self.draw(
            texture="chain", n_room_rows=2, n_room_cols=3))
        self.assert_connected(len(rooms), edges)
        self.assertEqual(len(edges), len(rooms) - 1)
        degrees = [sum(i in edge for edge in edges) for i in range(len(rooms))]
        self.assertEqual(sorted(degrees), [1, 1, 2, 2, 2, 2])

    def test_grid_connects_every_geometrically_adjacent_room(self):
        rooms, _, edges = self.assert_valid(self.draw(
            texture="grid", n_room_rows=2, n_room_cols=3))
        self.assert_connected(len(rooms), edges)
        expected = set()
        for a, left in enumerate(rooms):
            ar0, ar1, ac0, ac1 = left["bounds"]
            for b, right in enumerate(rooms[a + 1:], a + 1):
                br0, br1, bc0, bc1 = right["bounds"]
                if ((ar0 == br0 and ar1 == br1 and ac1 + 2 == bc0)
                        or (ac0 == bc0 and ac1 == bc1 and ar1 + 2 == br0)):
                    expected.add((a, b))
        self.assertEqual(edges, expected)

    def test_tree_is_connected_and_acyclic(self):
        rooms, _, edges = self.assert_valid(self.draw(
            texture="tree", n_room_rows=2, n_room_cols=3))
        self.assert_connected(len(rooms), edges)
        self.assertEqual(len(edges), len(rooms) - 1)

    def test_single_room_honors_applicable_room_dimensions(self):
        expected = dict(n_room_rows=1, n_room_cols=1, room_h=6, room_w=6, n_seeds=1)
        grid = self.draw(texture="single_room", **expected)
        rooms, doors, edges = self.assert_valid(grid, meta={"texture": "single_room"})
        self.assertEqual(len(rooms), 1)
        self.assertFalse(doors or edges)
        self.assert_controls(grid, **expected)

    def test_no_doors_honors_room_and_seed_counts(self):
        expected = dict(n_room_rows=2, n_room_cols=3, room_h=2, room_w=3, n_seeds=3)
        grid = self.draw(texture="no_doors", **expected)
        _, doors, edges = self.assert_valid(grid, meta={"texture": "no_doors"})
        self.assertFalse(doors or edges)
        self.assert_controls(grid, **expected)

    def test_same_color_seeds_are_connected_through_separating_walls(self):
        grid = self.draw(texture="two_seeds_same_color")
        rooms, doors, edges = self.assert_valid(
            grid, meta={"texture": "two_seeds_same_color"})
        seeded = [room for room in rooms if room["seed_cells"]]
        self.assertEqual(len(seeded), 2)
        self.assertEqual(len(set.union(*(room["colors"] for room in seeded))), 1)
        self.assertTrue(doors)
        self.assert_connected(len(rooms), edges)

    def test_modes_reject_explicit_incompatible_controls(self):
        for overrides in ({"texture": "single_room", "n_room_rows": 2},
                          {"texture": "single_room", "n_seeds": 2},
                          {"texture": "two_seeds_same_color", "n_seeds": 3}):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    self.draw(**overrides)

    def test_witness_and_canonical_modes_emit_valid_rooms(self):
        for texture in ("witness", "canonical"):
            with self.subTest(texture=texture):
                self.assert_valid(self.draw(texture=texture))

    def test_self_check_rejects_empty_or_ragged_grids_even_with_mode_metadata(self):
        for grid in ([], [[]], [[1, 1], [1]]):
            for texture in DEGENERATES:
                with self.subTest(grid=grid, texture=texture):
                    self.assertTrue(self.generator.self_check(grid, meta={"texture": texture}))

    def test_self_check_rejects_unseeded_rooms_even_with_mode_metadata(self):
        grid = [[1, 1, 1, 1], [1, 0, 0, 1], [1, 0, 0, 1], [1, 1, 1, 1]]
        for texture in DEGENERATES:
            with self.subTest(texture=texture):
                self.assertTrue(self.generator.self_check(grid, meta={"texture": texture}))

    def test_self_check_rejects_noninteger_and_out_of_domain_colors(self):
        for invalid in (True, 2.0, "2", -1, 10):
            grid = [[1, 1, 1, 1], [1, 3, invalid, 1], [1, 0, 0, 1], [1, 1, 1, 1]]
            for texture in (None, *DEGENERATES):
                with self.subTest(invalid=invalid, texture=texture):
                    self.assertTrue(self.generator.self_check(grid, meta={"texture": texture}))

    def test_self_check_rejects_input_tie_color_even_with_mode_metadata(self):
        grid = [[1, 1, 1, 1], [1, 3, 8, 1], [1, 0, 0, 1], [1, 1, 1, 1]]
        for texture in DEGENERATES:
            with self.subTest(texture=texture):
                self.assertTrue(self.generator.self_check(grid, meta={"texture": texture}))

    def test_self_check_rejects_nonrectangular_rooms_and_bad_doorways(self):
        malformed = (
            [[1, 1, 1, 1], [1, 3, 0, 1], [1, 1, 0, 1], [1, 1, 1, 1]],
            [[1, 7, 1, 1], [1, 3, 0, 1], [1, 0, 0, 1], [1, 1, 1, 1]],
            [[1, 1, 1, 1, 1], [1, 3, 0, 0, 1], [1, 0, 7, 0, 1],
             [1, 0, 0, 0, 1], [1, 1, 1, 1, 1]],
        )
        for index, grid in enumerate(malformed):
            for texture in (None, *DEGENERATES):
                with self.subTest(case=index, texture=texture):
                    self.assertTrue(self.generator.self_check(grid, meta={"texture": texture}))

    def test_self_check_accepts_nonuniform_and_canonical_room_inputs(self):
        nonuniform = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 2, 0, 7, 0, 0, 0, 3, 1],
            [1, 0, 0, 1, 0, 0, 0, 0, 1],
            [1, 0, 0, 1, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]
        self.assert_valid(nonuniform)
        pairs = canonical_pairs(TASK_ID, root=self.root)
        self.assertTrue(pairs)
        for pair in pairs:
            with self.subTest(variant=pair["variant"], split=pair["split"],
                              pair_index=pair["pair_index"]):
                self.assertEqual(self.generator.self_check(pair["input"]), [])

    def test_default_profiles_remain_bounded_varied_and_replayable(self):
        profiles = {}
        for difficulty in ("easy", "medium", "hard"):
            signatures = set()
            for seed in range(64):
                sample_index = seed % 4
                grid = self.draw(difficulty=difficulty, seed=seed,
                                 sample_index=sample_index)
                self.assert_valid(grid)
                observed = observe(grid)
                signatures.add((observed["n_room_rows"], observed["n_room_cols"],
                                tuple(sorted(observed["room_h"])),
                                tuple(sorted(observed["room_w"]))))
                self.assertEqual(grid, self.draw(difficulty=difficulty, seed=seed,
                                                sample_index=sample_index))
            self.assertGreaterEqual(len(signatures), 4)
            profiles[difficulty] = signatures
        self.assertIn(1, {row[0] for row in profiles["easy"]})
        self.assertTrue({1, 2} <= {row[0] for row in profiles["medium"]})
        self.assertTrue({2, 3} <= {row[0] for row in profiles["hard"]})


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Behavioral checks for the separate matching/opposite-wall prototype."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators/4295e17d5995/workspace/parametric"


def load_local(name):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"Parametric implementation is missing: {path}"
    spec = importlib.util.spec_from_file_location(f"parametric_4295e17d5995_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def framed(h, w, left, right, colored):
    grid = [[7] * w for _ in range(h)]
    for row in grid:
        row[0], row[-1] = left, right
    for color, cells in colored.items():
        for r, c in cells:
            grid[r][c] = color
    return grid


class ParametricWallTests(unittest.TestCase):
    def test_literal_rigid_diagonal_and_queued_packing_labels(self):
        # Changing connectivity, independent packing, or min-shift rigidity
        # changes these hand-derived cells. No production helper supplies gold.
        model = load_local("prototype")
        grid = framed(9, 13, 2, 5, {
            2: [(1, 3), (2, 3), (2, 4), (1, 9), (2, 8)],
            5: [(5, 3), (5, 4), (6, 4), (5, 8), (6, 8), (6, 9)],
        })
        expected = {
            "matching": framed(9, 13, 2, 5, {
                2: [(1, 1), (2, 1), (2, 2), (1, 4), (2, 3)],
                5: [(5, 8), (5, 9), (6, 9), (5, 10), (6, 10), (6, 11)],
            }),
            "opposite": framed(9, 13, 2, 5, {
                2: [(1, 8), (2, 8), (2, 9), (1, 11), (2, 10)],
                5: [(5, 1), (5, 2), (6, 2), (5, 3), (6, 3), (6, 4)],
            }),
        }
        original = json.dumps(grid)
        for relation, wanted in expected.items():
            with self.subTest(relation=relation):
                self.assertEqual(wanted, model.solve(grid, {"wall_relation": relation}))
        self.assertEqual(original, json.dumps(grid), "The rule must not edit its input")

    def test_matching_program_is_exact_selected_catalog_authority(self):
        from arcpuzzles import Catalog

        adapter = load_local("adapter")
        catalog = Catalog(ROOT)
        selected = catalog.describe("4295e17d5995").get("rule_task_id", "4295e17d5995")
        sources = {v["program_solution"] for v in catalog.get(selected)["variants"]}
        self.assertEqual(1, len(sources))
        canonical = sources.pop()
        self.assertEqual(canonical, adapter.program({"wall_relation": "matching"}))
        self.assertEqual(
            canonical.replace("(list (list lw -1) (list rw 1))", "(list (list lw 1) (list rw -1))"),
            adapter.program({"wall_relation": "opposite"}),
        )

    def test_request_boundaries_reject_coercion_and_unknown_settings(self):
        adapter = load_local("adapter")
        for settings in (None, {}, [], "matching", {"wall_relation": True},
                         {"wall_relation": 0}, {"wall_relation": "MATCHING"},
                         {"wall_relation": "matching", "typo": 1}):
            with self.subTest(settings=settings):
                with self.assertRaises((TypeError, ValueError)):
                    adapter.program(settings)
                with self.assertRaises((TypeError, ValueError)):
                    adapter.generate(0, settings, 3, 4)
        for seed in (True, False, -1, 2**63, 1.0, "1", None):
            with self.subTest(seed=seed), self.assertRaises((TypeError, ValueError)):
                adapter.generate(seed, {"wall_relation": "matching"}, 3, 4)
        for field, bads in (("demos", (1, 7, True, 3.0, "3")),
                            ("queries", (0, 5, True, 4.0, "4"))):
            for value in bads:
                request = {"demos": 3, "queries": 4, field: value}
                with self.subTest(field=field, value=value), self.assertRaises((TypeError, ValueError)):
                    adapter.generate(0, {"wall_relation": "matching"}, **request)

    def test_all_supported_counts_are_exact_and_all_inputs_are_distinct(self):
        adapter = load_local("adapter")
        for demos in range(2, 7):
            for queries in range(1, 5):
                with self.subTest(demos=demos, queries=queries):
                    episode = adapter.generate(17, {"wall_relation": "opposite"}, demos, queries)
                    self.assertEqual(demos, len(episode["train"]))
                    self.assertEqual(queries, len(episode["test"]))
                    pairs = episode["train"] + episode["test"]
                    self.assertEqual(len(pairs), len({json.dumps(p["input"]) for p in pairs}))
                    for pair in pairs:
                        self.assertTrue(all(type(c) is int and 0 <= c <= 9 for row in pair["input"] for c in row))

    def test_inputs_are_matched_and_split_streams_do_not_depend_on_counts(self):
        adapter = load_local("adapter")
        for seed in (0, 17):
            a = adapter.generate(seed, {"wall_relation": "matching"}, 2, 4)
            b = adapter.generate(seed, {"wall_relation": "opposite"}, 2, 4)
            long = adapter.generate(seed, {"wall_relation": "matching"}, 6, 1)
            short = adapter.generate(seed, {"wall_relation": "matching"}, 2, 1)
            self.assertEqual(a["train"], long["train"][:2])
            self.assertEqual(a["test"][:1], long["test"])
            self.assertEqual(a["train"], short["train"])
            self.assertEqual(a["test"][:1], short["test"])
            for split in ("train", "test"):
                self.assertEqual([p["input"] for p in a[split]], [p["input"] for p in b[split]])
            self.assertNotEqual(a["train"][0]["output"], b["train"][0]["output"])

    def test_two_demos_reject_each_declared_rival_under_both_settings(self):
        model = load_local("prototype")
        for seed in (0, 3, 17, 29):
            inputs = model.sample_inputs(seed, 2, 4)
            for relation in ("matching", "opposite"):
                setting = {"wall_relation": relation}
                demos = [{"input": g, "output": model.solve(g, setting)} for g in inputs["train"]]
                with self.subTest(seed=seed, relation=relation):
                    self.assertEqual([], model.demo_rival_failures(demos, setting))

    def test_large_query_has_substantive_geometry_and_conserved_content(self):
        model = load_local("prototype")
        for seed in (0, 17, 991):
            queries = model.sample_inputs(seed, 3, 4)["test"]
            self.assertEqual([(9, 9), (16, 20), (24, 27), (30, 30)],
                             [(len(g), len(g[0])) for g in queries])
            grid = queries[-1]
            cells = [(r, c) for r in range(30) for c in range(1, 29) if grid[r][c] != 7]
            self.assertGreaterEqual(len(cells), 110)
            self.assertGreaterEqual(len({r for r, _ in cells}), 22)
            self.assertLessEqual(min(c for _, c in cells), 2)
            self.assertGreaterEqual(max(c for _, c in cells), 27)
            self.assertIn(0, {r for r, _ in cells})
            self.assertIn(29, {r for r, _ in cells})
            self.assertGreaterEqual(sum(2 <= len({grid[r][c] for c in range(1, 29)} - {7})
                                        for r in range(30)), 8)
            objects = model.components(grid, grid[0][0]) + model.components(grid, grid[0][-1])
            self.assertGreaterEqual(len(objects), 18)
            normalized = {tuple(sorted((r - min(rr for rr, _ in o), c - min(cc for _, cc in o))
                                       for r, c in o)) for o in objects}
            self.assertGreaterEqual(len(normalized), 6)
            for relation in ("matching", "opposite"):
                out = model.solve(grid, {"wall_relation": relation})
                self.assertEqual(Counter(v for row in grid for v in row), Counter(v for row in out for v in row))
                self.assertGreaterEqual(sum(a != b for ra, rb in zip(grid, out) for a, b in zip(ra, rb)), 100)

    def test_grid_validation_rejects_bool_cells_and_nonwall_colors(self):
        model = load_local("prototype")
        good = framed(9, 9, 2, 5, {2: [(1, 2)], 5: [(7, 6)]})
        for value in (True, 0, "7"):
            bad = [row[:] for row in good]
            bad[4][4] = value
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                model.solve(bad, {"wall_relation": "matching"})

    def test_sampler_grammar_rejects_original_positions_inside_settled_shapes(self):
        model = load_local("prototype")
        unsafe = framed(9, 12, 2, 4, {
            2: [(0, 6), (0, 7), (0, 8), (1, 6), (2, 6), (2, 7), (2, 8)],
            4: [(2, 2), (3, 2)],
        })
        with self.assertRaises(ValueError):
            model.validate_grid(unsafe)


if __name__ == "__main__":
    unittest.main()

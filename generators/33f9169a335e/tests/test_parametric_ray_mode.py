"""Focused regressions for the proposed endpoint/trace rule only."""
import copy
import importlib.util
import json
from pathlib import Path
import random
import unittest
from unittest import mock

from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)
TASK = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "proposed_ray_mode", TASK / "workspace/parametric/ray_mode.py")
ray = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ray)


def witness():
    # Two mixed-color positional Us; the second intersects the first ray.
    return [[0, 1, 2, 3, 0, 0, 0],
            [0, 5, 0, 6, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 7, 8, 9, 0, 0],
            [0, 0, 1, 0, 2, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0]]


class RayModeTests(unittest.TestCase):
    def test_canonical_program_and_pairs(self):
        with canonical_path(ROOT).open(encoding="utf-8") as handle:
            records = [json.loads(line) for line in handle if line.strip()]
        canonical = [r for r in records if r["task_id"] == ray.TASK_ID]
        self.assertEqual(len(canonical), 1)
        self.assertEqual(ray.MODES, ("endpoint", "trace"))
        self.assertEqual(ray.canonical_program(), canonical[0]["program_solution"].strip())
        self.assertEqual(ray.rule_source("endpoint"), ray.canonical_program())
        self.assertNotEqual(ray.rule_source("trace"), ray.canonical_program())
        for pair in canonical_pairs(ray.TASK_ID, root=ROOT):
            self.assertEqual(ray.python_transform(pair["input"], "endpoint"), pair["output"])

    def test_mixed_witness_trace_preserves_nonzero(self):
        grid = witness()
        self.assertEqual(ray._generator().self_check(grid), [])
        expected = copy.deepcopy(grid)
        for row, col in ((1, 2), (2, 2), (5, 2), (6, 2),
                         (4, 3), (5, 3), (6, 3)):
            expected[row][col] = 4
        self.assertEqual(ray.python_transform(grid, "trace"), expected)
        endpoint = copy.deepcopy(grid)
        endpoint[-1][2] = endpoint[-1][3] = 4
        self.assertEqual(ray.python_transform(grid, "endpoint"), endpoint)

    def test_repeated_color_two_us(self):
        grid = [[0] * 8 for _ in range(6)]
        for top, gap in ((0, 2), (2, 6)):
            for row, col in ((top, gap - 1), (top, gap), (top, gap + 1),
                             (top + 1, gap - 1), (top + 1, gap + 1)):
                grid[row][col] = 6
        expected = copy.deepcopy(grid)
        for row in range(1, 6):
            expected[row][2] = 4
        for row in range(3, 6):
            expected[row][6] = 4
        self.assertEqual(ray.python_transform(grid, "trace"), expected)
        self.assertEqual(ray.python_transform(grid, "endpoint")[-1], [0, 0, 4, 0, 0, 0, 4, 0])

    def test_transforms_preserve_input_and_return_fresh_rows(self):
        grid, original = witness(), witness()
        for mode in ray.MODES:
            out = ray.python_transform(grid, mode)
            self.assertEqual(grid, original)
            self.assertIsNot(out, grid)
            self.assertTrue(all(a is not b for a, b in zip(out, grid)))
            out[0][0] = 9
            self.assertEqual(grid, original)
            self.assertEqual(ray.python_transform(grid, mode)[0][0], 0)

    def test_seeded_episodes_and_global_rng(self):
        before = random.getstate()
        a = ray.sample_episode(17, mode=None)
        self.assertEqual(a, ray.sample_episode(17, mode=None))
        self.assertEqual(before, random.getstate())
        self.assertIn(a["parameters"]["mode"], ray.MODES)
        self.assertEqual(ray.sample_episode(17)["parameters"], {"mode": "endpoint"})
        self.assertEqual(a["program"], ray.rule_source(a["parameters"]["mode"]))
        self.assertEqual(a["status"], "proposed")

    def test_shared_inputs_unique_and_domain_valid(self):
        a = ray.sample_episode(17, mode="endpoint", input_seed=39)
        b = ray.sample_episode(42, mode="trace", input_seed=39)
        self.assertEqual((len(a["train"]), len(a["test"])), (2, 4))
        self.assertEqual((a["demo_count"], a["query_count"]), (2, 4))
        left, right = a["train"] + a["test"], b["train"] + b["test"]
        self.assertEqual([p["input"] for p in left], [p["input"] for p in right])
        self.assertEqual(len({json.dumps(p["input"]) for p in left}), 6)
        for p, q in zip(left, right):
            self.assertEqual(ray._generator().self_check(p["input"]), [])
            self.assertNotEqual(p["output"], q["output"])
        wide = ray.sample_episode(3, demo_count=8, query_count=8)
        self.assertEqual((len(wide["train"]), len(wide["test"])), (8, 8))

    def test_numeric_and_mode_validation(self):
        for name in ("demo_count", "query_count"):
            for value in (True, False, 0, 9, -1, 1.0, "2", None):
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    ray.sample_episode(17, **{name: value})
        for value in (True, 1.5, "17", None):
            with self.subTest(seed=value), self.assertRaises(ValueError):
                ray.sample_episode(value)
        for value in (True, 1.5, "17"):
            with self.subTest(input_seed=value), self.assertRaises(ValueError):
                ray.sample_episode(17, input_seed=value)
        for value in ("", "ray", 4, True):
            with self.assertRaises(ValueError):
                ray.sample_episode(17, mode=value)
            with self.assertRaises(ValueError):
                ray.rule_source(value)
        with self.assertRaises(ValueError):
            ray.python_transform([[True] * 5 for _ in range(5)], "trace")

    def test_bounded_duplicate_and_invalid_draw_failures(self):
        fake = mock.Mock()
        fake.generate.return_value = witness()
        for errors in ([], ["deliberately invalid"]):
            fake.reset_mock()
            fake.self_check.return_value = errors
            with mock.patch.object(ray, "_generator", return_value=fake), \
                 mock.patch.object(ray, "MAX_ATTEMPTS_PER_PAIR", 2):
                with self.assertRaisesRegex(RuntimeError, "distinct"):
                    ray.sample_episode(1, demo_count=1, query_count=1)
            self.assertEqual(fake.generate.call_count, 4)


if __name__ == "__main__":
    unittest.main()

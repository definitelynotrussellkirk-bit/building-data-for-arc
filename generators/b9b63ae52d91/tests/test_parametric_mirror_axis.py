"""Public contract for the task-local mirror-axis prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


TASK_DIR = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_DIR / "workspace/parametric/prototype.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location("mirror_axis_prototype", PROTOTYPE)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ParametricMirrorAxisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prototype = _load_prototype()

    def test_parameter_is_chosen_once_from_two_lossless_settings(self):
        self.assertEqual(
            self.prototype.MIRROR_AXES, ("vertical", "horizontal")
        )
        self.assertEqual(self.prototype.DEFAULT_MIRROR_AXIS, "vertical")
        self.assertEqual(self.prototype.choose_mirror_axis(0), "vertical")
        self.assertEqual(self.prototype.choose_mirror_axis(1), "horizontal")
        with self.assertRaisesRegex(ValueError, "seed must be a nonnegative integer"):
            self.prototype.choose_mirror_axis(True)

    def test_python_rules_change_only_the_mirror_axis(self):
        grid = [
            [0, 8, 0, 0, 0],
            [0, 8, 0, 8, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 8, 0, 0, 0],
        ]
        vertical = self.prototype.apply_python(grid, "vertical")
        horizontal = self.prototype.apply_python(grid, "horizontal")
        self.assertNotEqual(vertical, horizontal)
        self.assertEqual(vertical[0][1], 2)
        self.assertEqual([horizontal[1][1], horizontal[1][3]], [2, 2])
        self.assertEqual([vertical[1][1], vertical[1][3]], [5, 5])

    def test_complete_racket_sources_exist_for_both_settings(self):
        sources = self.prototype.RACKET_RULES
        self.assertEqual(set(sources), set(self.prototype.MIRROR_AXES))
        self.assertIn("(rows g)", sources["vertical"])
        self.assertIn("(cols g)", sources["horizontal"])
        self.assertTrue(all(source.strip().startswith("(rule!") for source in sources.values()))
        for axis in self.prototype.MIRROR_AXES:
            callable_source = self.prototype.callable_racket_rule(axis)
            self.assertTrue(callable_source.startswith("(lambda (g)"))
            self.assertNotIn("(rule!", callable_source)

    def test_episode_validation_requires_demo_and_query_witnesses(self):
        distinguishing = [
            [
                [0, 8, 0, 0, 0],
                [0, 8, 0, 8, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [0, 8, 0, 0, 0],
            ]
            for _ in range(4)
        ]
        episode = self.prototype.assemble_episode(
            distinguishing, "vertical", labeler=self.prototype.apply_python
        )
        self.assertEqual(episode["parameter"], {"mirror_axis": "vertical"})
        self.assertEqual(len(episode["train"]), 3)
        self.assertEqual(len(episode["test"]), 1)
        self.assertNotIn("output", episode["test"][0])
        self.assertTrue(episode["evidence"]["demo_distinguishes_rival"])
        self.assertTrue(episode["evidence"]["query_distinguishes_rival"])


if __name__ == "__main__":
    unittest.main()

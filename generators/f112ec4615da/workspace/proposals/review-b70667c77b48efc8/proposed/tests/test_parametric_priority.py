from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import unittest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "f112ec4615da"
ROOT = find_root(__file__)
generator, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(
    TASK_ID,
    root=ROOT,
)
PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1]
    / "workspace"
    / "parametric"
    / "prototype.py"
)


def load_prototype():
    spec = importlib.util.spec_from_file_location(
        "f112ec4615da_parametric_prototype",
        PROTOTYPE_PATH,
    )
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ParametricPriorityPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prototype = load_prototype()

    def test_default_matches_canonical_and_each_input_separates_settings(self):
        p = self.prototype
        for seed in (18, 19):
            for pair_index in range(3):
                grid = p.build_input(seed, pair_index)
                canonical = p.python_reference(
                    grid,
                    overlay_priority=p.DEFAULT_OVERLAY_PRIORITY,
                )
                alternative = p.python_reference(
                    grid,
                    overlay_priority=p.ALTERNATIVE_OVERLAY_PRIORITY,
                )
                self.assertEqual(canonical, generator.rule_mirror(grid))
                self.assertNotEqual(canonical, alternative)

    def test_episode_uses_one_setting_and_public_view_hides_it(self):
        p = self.prototype
        for seed in (18, 19):
            episode = p.build_episode(seed)
            setting = episode["parameter"][p.PARAMETER_NAME]
            self.assertEqual(setting, p.choose_parameters(seed)[p.PARAMETER_NAME])
            self.assertEqual(len(episode["train"]), 2)
            self.assertEqual(len(episode["test"]), 1)
            other = (
                p.ALTERNATIVE_OVERLAY_PRIORITY
                if setting == p.DEFAULT_OVERLAY_PRIORITY
                else p.DEFAULT_OVERLAY_PRIORITY
            )
            for pair in episode["train"] + episode["test"]:
                self.assertEqual(
                    pair["output"],
                    p.python_reference(
                        pair["input"],
                        overlay_priority=setting,
                    ),
                )
                self.assertNotEqual(
                    pair["output"],
                    p.python_reference(
                        pair["input"],
                        overlay_priority=other,
                    ),
                )

            public = p.public_challenge(episode)
            self.assertNotIn("parameter", public)
            self.assertNotIn("seed", public)
            self.assertTrue(all("output" in pair for pair in public["train"]))
            self.assertTrue(all("output" not in pair for pair in public["test"]))

    def test_retained_racket_programs_match_python(self):
        if shutil.which("racket") is None:
            self.skipTest("racket is not on PATH")
        p = self.prototype
        p.materialize_rules()
        grid = p.build_input(19, 0)
        for setting in p.ALLOWED_OVERLAY_PRIORITIES:
            with self.subTest(setting=setting):
                self.assertEqual(
                    p.run_racket(setting, grid),
                    p.python_reference(grid, overlay_priority=setting),
                )


if __name__ == "__main__":
    unittest.main()

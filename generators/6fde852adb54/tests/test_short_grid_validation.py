"""Malformed short grids must be rejected through public validation APIs."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "generator.py"


class ShortGridValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("short_grid_6fde852adb54", SOURCE)
        cls.generator = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.generator
        spec.loader.exec_module(cls.generator)

    def cases(self):
        top = [9, 9, 9, 7, 7, 7, 1, 5, 7, 7, 7, 7, 7, 7]
        second = [9, 9, 9] + [7] * 11
        return [[top], [top, second]]

    def test_self_check_reports_short_dimensions_without_crashing(self):
        for grid in self.cases():
            with self.subTest(height=len(grid)):
                original = deepcopy(grid)
                try:
                    errors = self.generator.self_check(grid)
                except Exception as exc:
                    self.fail(f"self_check raised {type(exc).__name__}: {exc}")
                self.assertTrue(any("dimensions" in item for item in errors))
                self.assertEqual(grid, original)

    def test_rule_mirror_rejects_short_dimensions_with_value_error(self):
        for grid in self.cases():
            with self.subTest(height=len(grid)):
                original = deepcopy(grid)
                try:
                    self.generator.rule_mirror(grid)
                except ValueError as exc:
                    self.assertIn("dimensions", str(exc))
                except Exception as exc:
                    self.fail(f"rule_mirror raised {type(exc).__name__}: {exc}")
                else:
                    self.fail("rule_mirror accepted an out-of-domain short grid")
                self.assertEqual(grid, original)

    def test_observe_overrides_rejects_short_dimensions_without_crashing(self):
        for grid in self.cases():
            with self.subTest(height=len(grid)):
                original = deepcopy(grid)
                try:
                    observed = self.generator.observe_overrides(grid)
                except Exception as exc:
                    self.fail(f"observe_overrides raised {type(exc).__name__}: {exc}")
                self.assertEqual(observed, {})
                self.assertEqual(grid, original)


if __name__ == "__main__":
    unittest.main()

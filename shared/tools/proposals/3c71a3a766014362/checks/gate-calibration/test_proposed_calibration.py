#!/usr/bin/env python3
"""Test only the optional isolated generic calibration proposal."""
from pathlib import Path
import importlib.util
import sys
import unittest

HERE = Path(__file__).resolve().parent
candidate = Path(sys.argv.pop(1)).resolve() if len(sys.argv) > 1 else HERE / "proposed/scripts/generator_defect_lint.py"
sys.path.insert(0, str(candidate.parents[1]))
spec = importlib.util.spec_from_file_location("isolated_candidate", candidate)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class GenericCalibrationProposal(unittest.TestCase):
    def test_exact_canonical_top_left_block_is_calibrated(self):
        grid = [[0, 0, 9], [0, 0, 9], [9, 9, 9]]
        self.assertIn("solid_2x2", mod._canonical_minimal_kinds([(grid, grid)]))

    def test_exact_canonical_short_line_is_calibrated(self):
        grid = [[9, 9, 9], [0, 0, 0], [9, 9, 9]]
        self.assertIn("short_line", mod._canonical_minimal_kinds([(grid, grid)]))

    def test_nonmatching_geometry_does_not_calibrate_block_or_line(self):
        for grid in ([[9, 0, 0], [9, 0, 0], [9, 9, 9]],
                     [[0, 0, 9], [0, 9, 9], [9, 9, 9]]):
            lawful = mod._canonical_minimal_kinds([(grid, grid)])
            self.assertNotIn("solid_2x2", lawful)
            self.assertNotIn("short_line", lawful)

    def test_existing_singleton_calibration_preserved(self):
        grid = [[0, 9, 9], [9, 9, 9], [9, 9, 9]]
        self.assertIn("singleton", mod._canonical_minimal_kinds([(grid, grid)]))

    def test_canonical_block_does_not_waive_remaining_named_findings(self):
        class Permissive:
            @staticmethod
            def self_check(grid, **kwargs):
                return []
        grid = [[0, 0, 9], [0, 0, 9], [9, 9, 9]]
        findings = mod.probe_selfcheck_minimal_impostors(Permissive, [grid], [None], [(grid, grid)])
        self.assertEqual(len(findings), 1)
        self.assertNotIn("solid_2x2 1/1", findings[0])
        for kind in ("all_background", "full_one_color", "singleton", "short_line"):
            self.assertIn(kind + " 1/1", findings[0])

    def test_power_warning_is_unchanged_by_named_calibration(self):
        class Permissive:
            @staticmethod
            def self_check(grid, **kwargs):
                return []
        grid = [[0, 0, 9], [0, 0, 9], [9, 9, 9]]
        self.assertTrue(mod.probe_selfcheck_power(Permissive, [grid], [None]))


if __name__ == "__main__":
    unittest.main()

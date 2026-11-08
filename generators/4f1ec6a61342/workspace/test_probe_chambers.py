"""Focused tests for the independent oracle; portable beside its probe file."""
import importlib.util
from pathlib import Path
import unittest

_path = Path(__file__).with_name('probe_chambers.py')
_spec = importlib.util.spec_from_file_location('_independent_chamber_probe', _path)
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)


class ChamberOracleTests(unittest.TestCase):
    def scene(self, target):
        grid = [[5] * 9 for _ in range(7)]
        for r in range(1, 6):
            for c in (1, 2, 3, 5, 6, 7):
                grid[r][c] = 0
        left = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)]
        for r, c in left[:target]:
            grid[r][c] = 2
        grid[1][5] = 2
        grid[2][5] = 2
        grid[0][0] = target
        expected = [[5] * 9 for _ in range(7)]
        expected[0][0] = 5 if target == 5 else 0
        for r in range(1, 6):
            for c in (1, 2, 3):
                expected[r][c] = 8
            for c in (5, 6, 7):
                expected[r][c] = 0
        return grid, expected

    def test_color5_control_is_preserved_as_wall(self):
        grid, expected = self.scene(5)
        original = [row[:] for row in grid]
        errors, output, detail = probe.analyze(grid)
        self.assertEqual(errors, [])
        self.assertEqual(output, expected)
        self.assertEqual(detail['observed']['target_count'], 5)
        self.assertEqual(grid, original)

    def test_nonwall_control_and_red_seeds_are_erased(self):
        for target in (3, 6):
            with self.subTest(target=target):
                grid, expected = self.scene(target)
                errors, output, detail = probe.analyze(grid)
                self.assertEqual(errors, [])
                self.assertEqual(output, expected)
                self.assertNotIn(2, [value for row in output for value in row])
                self.assertEqual(sorted(room['seeds'] for room in detail['rooms']), [2, target])


if __name__ == '__main__':
    unittest.main()

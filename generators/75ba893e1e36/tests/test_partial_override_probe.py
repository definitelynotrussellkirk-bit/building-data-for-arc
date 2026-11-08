"""Focused falsification and false-positive tests for the portable completion probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

from reviewer_support import find_root

ROOT = find_root(__file__)
PATH = Path(__file__).resolve().parents[1] / "workspace/partial_override_probe.py"
SPEC = importlib.util.spec_from_file_location("partial_override_probe_test_subject", PATH)
assert SPEC and SPEC.loader
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


class RejectionFixture:
    @staticmethod
    def generate(seed, sample_index, *, difficulty=None, **request):
        if request.get("grid_w", 2) == 2:
            error = ValueError("grid_h * grid_w cannot fit palette_size distinct colors")
            error.incompatible_axes = ("grid_h", "grid_w", "palette_size")
            raise error
        return [[1, 2, 3, 1]]

    @staticmethod
    def self_check(grid, *, difficulty=None):
        return []

    @staticmethod
    def observe_overrides(grid):
        return {"grid_h": len(grid), "grid_w": len(grid[0]),
                "palette_size": len({cell for row in grid for cell in row})}


class TestPartialOverrideProbe(unittest.TestCase):
    def test_feasible_completion_falsifies_rejection_and_keeps_seed_and_controls(self):
        result = probe.run_probe(RejectionFixture, request={"grid_h": 1, "palette_size": 3},
                                 free_axis="grid_w", candidates=[2, 4], seeds=[4],
                                 sample_index=1, band="medium")
        self.assertEqual(result["exit_code"], 1)
        self.assertEqual(result["counts"]["falsified_rejections"], 1)
        row = result["records"][0]
        self.assertEqual(row["original"]["error"]["incompatible_axes"], ["grid_h", "grid_w", "palette_size"])
        witness = row["first_feasible_completion"]
        self.assertEqual((witness["seed"], witness["sample_index"], witness["band"]), (4, 1, "medium"))
        self.assertEqual(witness["request"], {"grid_h": 1, "grid_w": 4, "palette_size": 3})
        self.assertTrue(witness["validation"]["valid"])

    def test_wrong_observed_completion_is_not_a_witness_and_absence_is_inconclusive(self):
        result = probe.run_probe(RejectionFixture, request={"grid_h": 1, "palette_size": 3},
                                 free_axis="grid_w", candidates=[3], seeds=[4],
                                 sample_index=1, band="medium")
        self.assertEqual(result["status"], "inconclusive")
        self.assertEqual(result["exit_code"], 2)
        self.assertEqual(result["counts"]["falsified_rejections"], 0)
        self.assertEqual(result["counts"]["invalid_candidate_returns"], 1)
        self.assertNotIn("first_feasible_completion", result["records"][0])

    def test_palette_set_is_checked_and_unsupported_or_fixed_free_axes_rejected(self):
        checked = probe.validate_return(RejectionFixture, [[1, 2, 3, 1]],
                                        {"grid_h": 1, "palette": [1, 2, 4]}, "medium")
        self.assertFalse(checked["valid"])
        for request, free_axis in (({"texture": "noise"}, "grid_w"),
                                   ({"grid_h": 1, "grid_w": 4}, "grid_w")):
            with self.assertRaises(ValueError):
                probe.run_probe(RejectionFixture, request=request, free_axis=free_axis,
                                candidates=[4], seeds=[4], sample_index=1, band="medium")


    def test_weak_validator_and_lying_observer_cannot_certify_wrong_pixels_or_row_strings(self):
        class LyingFixture(RejectionFixture):
            @staticmethod
            def generate(seed, sample_index, *, difficulty=None, **request):
                if "grid_w" not in request:
                    raise ValueError("claimed incompatibility")
                return [[1, 2]]  # Width 2 and two colors, despite the claimed completion.

            @staticmethod
            def observe_overrides(grid):
                return {"grid_h": 1, "grid_w": 4, "palette_size": 3}

        with self.subTest("lying observer and weak self_check"):
            result = probe.run_probe(LyingFixture, request={"grid_h": 1, "palette_size": 3},
                                     free_axis="grid_w", candidates=[4], seeds=[4],
                                     sample_index=1, band="medium")
            self.assertEqual(result["status"], "inconclusive")
            self.assertEqual(result["counts"]["falsified_rejections"], 0)
            self.assertEqual(result["counts"]["invalid_candidate_returns"], 1)
            self.assertNotIn("first_feasible_completion", result["records"][0])
        with self.subTest("raw row strings are not valid generator grids"):
            checked = probe.validate_return(RejectionFixture, ["1231"],
                                            {"grid_h": 1, "grid_w": 4, "palette_size": 3}, "medium")
            self.assertFalse(checked["valid"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

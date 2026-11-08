#!/usr/bin/env python3
"""Focused checks of probe argument, validation, and witness audit behavior."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PROBE = Path(__file__).resolve().parents[1] / "workspace" / "probe_laser_distribution.py"
spec = importlib.util.spec_from_file_location("probe_under_test", PROBE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeRegression(unittest.TestCase):
    def test_invalid_bands_exit_before_output_creation(self):
        for bands in ("", ",", "easy,", "easy,,hard", "easy,easy", "unknown", "easy,unknown"):
            with self.subTest(bands=bands), tempfile.TemporaryDirectory() as temp:
                out = Path(temp) / "must-not-exist"
                run = subprocess.run([sys.executable, str(PROBE), "--bands", bands, "--out", str(out)],
                                     capture_output=True, text=True)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertFalse(out.exists())

    def test_boolean_and_violation_list_checks(self):
        for value, valid in ((True, True), (False, False), ([], True), (["violation"], False)):
            with self.subTest(value=value):
                raw, actual, errors = probe.evaluate_check(lambda grid: value, [[0]])
                self.assertEqual(raw, value)
                self.assertEqual(actual, valid)
                self.assertEqual(bool(errors), not valid)

    def test_strict_violation_is_retained_without_self_check_false_positive(self):
        generator = SimpleNamespace(EXAMPLES_NEEDED=4, MIN_STRICT_FRAC=1.0,
                                    generate=lambda seed, index, **kwargs: [[0]],
                                    self_check=lambda grid, **kwargs: True,
                                    strict_canonical_like=lambda grid: False)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "strict"
            argv = [str(PROBE), "--generate-only", "--seeds", "1", "--starts", "1",
                    "--bands", "easy", "--out", str(out)]
            with patch.object(sys, "argv", argv), patch.object(probe, "load_generator", return_value=generator):
                self.assertEqual(probe.main(), 1)
            failures = json.loads((out / "failures.json").read_text())
            self.assertEqual(len(failures), 5)
            self.assertEqual({row["kind"] for row in failures}, {"strict_canonical_like_violation"})
            self.assertTrue(all(row["self_check_valid"] for row in json.loads((out / "draws.json").read_text())))

    def test_fired_witness_must_refute_each_claimed_rival(self):
        base = {"id": "draw", "input_sha256": "input", "output_sha256": "racket-output",
                "witnesses": {"w": True}, "competitors": {"r": {"agrees": False}}}
        row = deepcopy(base)
        self.assertEqual(probe.verify_witness_claims(row, {"w": ["r"]}), [])
        self.assertTrue(row["witness_claims_verified"]["w"])
        for result in ({"agrees": True}, {"agrees": False, "error": "rival crashed"}):
            row = deepcopy(base)
            row["competitors"]["r"] = result
            failures = probe.verify_witness_claims(row, {"w": ["r"]})
            self.assertEqual(len(failures), 1)
            self.assertEqual(failures[0]["kind"], "false_witness_claim")
            self.assertFalse(row["witness_claims_verified"]["w"])
        row = deepcopy(base)
        row["witnesses"]["w"] = False
        row["competitors"]["r"]["agrees"] = True
        self.assertEqual(probe.verify_witness_claims(row, {"w": ["r"]}), [])
        self.assertIsNone(row["witness_claims_verified"]["w"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

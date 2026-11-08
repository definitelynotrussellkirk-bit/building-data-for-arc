"""Structured Racket evidence from `scripts/rule_smoke.py`.

Two workers reported that the standard smoke omits measurements their
evidence contract requires — p95 latency, input-purity accounting, bridge
restart accounting — so each of them wrote a private bridge harness instead
(v13-z WFB-702), and that a bare `IDENTITY=1` count forced a manual replay of
120 draws to locate the offending seed (30d3af94d21e WFB-001).

`--json-out` now emits all of it, and the first crash/identity is pinned to a
replayable (band, seed, sample_index) witness.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts import rule_smoke

TASK = "6aaddc95d135"


class PercentileTests(unittest.TestCase):
    def test_empty_is_none_not_zero(self) -> None:
        """A zero p95 would read as 'instant', not 'never measured'."""
        self.assertIsNone(rule_smoke._percentile([], 95))

    def test_nearest_rank(self) -> None:
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        self.assertEqual(rule_smoke._percentile(values, 95), 10.0)
        self.assertEqual(rule_smoke._percentile(values, 50), 5.0)

    def test_does_not_require_sorted_input(self) -> None:
        self.assertEqual(rule_smoke._percentile([9.0, 1.0, 5.0], 50), 5.0)

    def test_single_sample(self) -> None:
        self.assertEqual(rule_smoke._percentile([42.0], 95), 42.0)


class GridDigestTests(unittest.TestCase):
    def test_stable_and_discriminating(self) -> None:
        a = [[1, 0], [0, 2]]
        self.assertEqual(rule_smoke._grid_sha16(a), rule_smoke._grid_sha16([[1, 0], [0, 2]]))
        self.assertNotEqual(rule_smoke._grid_sha16(a), rule_smoke._grid_sha16([[1, 0], [0, 3]]))
        self.assertEqual(len(rule_smoke._grid_sha16(a)), 16)


class JsonEvidenceTests(unittest.TestCase):
    def _run(self, extra=()):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "evidence.json"
            proc = subprocess.run(
                [sys.executable, "scripts/rule_smoke.py", TASK,
                 "--seeds", "3", "--json-out", str(out), *extra],
                cwd=REPO, capture_output=True, text=True, timeout=900,
            )
            self.assertTrue(out.exists(), proc.stderr)
            return json.loads(out.read_text()), proc

    def test_emits_the_contract_fields(self) -> None:
        payload, _ = self._run()
        self.assertEqual(payload["scanned"], 1)
        row = payload["tasks"][0]
        self.assertEqual(row["task_id"], TASK)
        for field in ("applied", "crash", "input_pure", "bridge_restarts",
                      "reentrant_aba_checked", "first_failure_witness"):
            self.assertIn(field, row)
        latency = row["latency_ms"]
        for field in ("p50", "p95", "max", "timed_calls",
                      "restart_contaminated_calls_excluded"):
            self.assertIn(field, latency)
        self.assertGreater(latency["timed_calls"], 0)
        self.assertIsNotNone(latency["p95"])
        self.assertGreaterEqual(latency["p95"], latency["p50"])

    def test_clean_task_has_no_witness(self) -> None:
        payload, _ = self._run()
        row = payload["tasks"][0]
        self.assertEqual(row["crash"], 0)
        self.assertIsNone(row["first_failure_witness"])
        self.assertTrue(row["input_pure"])


class IdentityWitnessTests(unittest.TestCase):
    """The case that cost a worker a manual 120-draw replay."""

    def test_identity_rule_yields_a_replayable_witness(self) -> None:
        # Force the identity rule for one task without touching the corpus.
        script = (
            "import json, sys;"
            "sys.path.insert(0, %r);"
            "from scripts import rule_smoke;"
            "_orig = rule_smoke.load_rules;"
            "rule_smoke.load_rules = lambda ids: "
            "{i: '(rule! (lambda (g) g))' for i in ids};"
            "sys.argv = ['rule_smoke', %r, '--seeds', '2', '--json-out', sys.argv[1]];"
            "sys.exit(rule_smoke.main())"
        ) % (str(REPO), TASK)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "identity.json"
            subprocess.run([sys.executable, "-c", script, str(out)],
                           cwd=REPO, capture_output=True, text=True, timeout=900)
            self.assertTrue(out.exists())
            row = json.loads(out.read_text())["tasks"][0]
        self.assertGreater(row["identity"], 0, "identity rule was not detected")
        witness = row["first_failure_witness"]
        self.assertIsNotNone(witness, "identity produced no replay witness")
        self.assertEqual(witness["kind"], "identity")
        # Every field needed to reproduce the exact draw.
        for field in ("band", "seed", "sample_index", "input_sha16"):
            self.assertIn(field, witness)
        self.assertIn(witness["band"], ("easy", "medium", "hard"))


if __name__ == "__main__":
    unittest.main()

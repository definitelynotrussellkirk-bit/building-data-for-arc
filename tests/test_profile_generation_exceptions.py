"""Bounded, replayable crash diagnostics from the actual profile-floor gate."""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from test_canonical_profile_floor import CANONICAL, EXACT, DEFAULT_SOURCE, load_gate


class GenerationExceptionDiagnostics(unittest.TestCase):
    gate = load_gate(DEFAULT_SOURCE)

    def audit(self, generate, **kwargs):
        generator = types.SimpleNamespace(generate=generate, self_check=lambda grid: [])
        with patch.object(self.gate, "canonical_inputs", return_value=CANONICAL), patch.object(
            self.gate.importlib, "import_module", return_value=generator
        ):
            return self.gate.audit_task("controlled_fixture", per_band=20, **kwargs)

    def test_uint32_rejection_exposes_exact_replay_coordinates(self):
        def generate(seed, sample_index, **kwargs):
            if not 0 <= seed < 2**32:
                raise ValueError("seed must be uint32")
            return EXACT

        result = self.audit(generate)
        self.assertEqual((result["status"], result["crashes"], result["draws_total"]),
                         ("FAIL", 60, 0))
        examples = result["generation_exception_examples"]
        self.assertEqual(len(examples), 1)
        example = examples[0]
        seed = self.gate._pinned_seed("controlled_fixture", "easy", 0)
        self.assertGreaterEqual(seed, 2**32)
        self.assertEqual((example["band"], example["seed"], example["sample_index"]),
                         ("easy", seed, seed % 7919))
        self.assertEqual((example["exception_type"], example["message"]),
                         ("ValueError", "seed must be uint32"))
        self.assertFalse(example["message_truncated"])

    def test_distinct_examples_are_capped_without_losing_crash_counts(self):
        calls = 0
        def generate(seed, sample_index, **kwargs):
            nonlocal calls
            calls += 1
            raise RuntimeError(f"failure {calls}")

        result = self.audit(generate)
        self.assertEqual(result["crashes"], 60)
        self.assertEqual([row["message"] for row in result["generation_exception_examples"]],
                         ["failure 1", "failure 2", "failure 3"])
        self.assertEqual(sum(row["crashes"] for row in result["per_band"].values()), 60)
        self.assertEqual(result["status"], "FAIL")

    def test_long_messages_are_bounded_but_distinct_suffixes_survive(self):
        calls = 0
        def generate(seed, sample_index, **kwargs):
            nonlocal calls
            calls += 1
            raise ValueError("x" * 1000 + str(calls % 2))

        examples = self.audit(generate)["generation_exception_examples"]
        self.assertEqual(len(examples), 2)
        self.assertTrue(all(len(row["message"]) <= 500 and row["message_truncated"]
                            for row in examples))
        self.assertEqual({row["message_sha256"] for row in examples},
                         {hashlib.sha256(("x" * 1000 + str(i)).encode()).hexdigest()
                          for i in (0, 1)})

    def test_clean_and_minority_crash_verdicts_are_unchanged(self):
        clean = self.audit(lambda *args, **kwargs: EXACT)
        self.assertEqual(clean["generation_exception_examples"], [])
        self.assertEqual(clean["status"], "PASS")
        for strict, expected in ((False, "WARN"), (True, "FAIL")):
            seen = set()
            def generate(seed, sample_index, *, difficulty):
                if difficulty not in seen:
                    seen.add(difficulty)
                    raise ValueError("one failed draw per band")
                return EXACT
            result = self.audit(generate, strict=strict)
            self.assertEqual((result["status"], result["crashes"], result["draws_total"]),
                             (expected, 3, 57))

    def test_cli_emits_json_and_concise_exception_line(self):
        def generate(seed, sample_index, **kwargs):
            raise ValueError("seed must be uint32")
        generator = types.SimpleNamespace(generate=generate, self_check=lambda grid: [])
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / "report.json"
            output = io.StringIO()
            with patch.object(self.gate, "canonical_inputs", return_value=CANONICAL), patch.object(
                self.gate.importlib, "import_module", return_value=generator
            ), patch.object(sys, "argv", ["profile-floor", "controlled_fixture", "--json-out", str(report)]), redirect_stdout(output):
                code = self.gate.main()
            self.assertEqual(code, 1)
            audit = json.loads(report.read_text())["audits"][0]
            self.assertEqual(audit["crashes"], 60)
            example = audit["generation_exception_examples"][0]
            self.assertIn("EXCEPTION: ValueError: seed must be uint32", output.getvalue())
            self.assertIn(f"seed={example['seed']}", output.getvalue())
            self.assertIn(f"sample_index={example['sample_index']}", output.getvalue())
            self.assertIn("canonical-profile-floor: 0/1 pass, 1 FAIL", output.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)

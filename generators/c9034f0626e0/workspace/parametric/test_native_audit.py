"""Focused audit regressions; run directly with the same Python as the audit."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest


class NativeAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).with_name("audit_native.py")
        if path.is_file():
            spec = importlib.util.spec_from_file_location("_native_audit_tests", path)
            cls.audit = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.audit)
        else:
            cls.audit = None

    def require_audit(self):
        self.assertIsNotNone(self.audit, "audit_native.py must exist")
        return self.audit

    def test_existing_output_is_rejected_without_modification(self):
        audit = self.require_audit()
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "new-run"
            audit.prepare_output(out)
            sentinel = out / "keep"
            sentinel.write_text("unchanged", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                audit.prepare_output(out)
            self.assertEqual(sentinel.read_text(), "unchanged")

    def test_source_mutations_fail_on_missing_or_repeated_needles(self):
        audit = self.require_audit()
        self.assertEqual(audit.replace_once("x y z", "y", "q"), "x q z")
        for source in ("x z", "x y y z"):
            with self.assertRaises(ValueError):
                audit.replace_once(source, "y", "q")

    def test_rejected_rivals_never_receive_queries_and_ambiguity_is_retained(self):
        audit = self.require_audit()
        episode = {"train": [{"input": [[1]], "output": [[2]]}],
                   "test": [{"input": [[3]], "output": [[4]]}]}
        candidates = {name: name for name in ("actual", "rejected", "same", "ambiguous")}
        calls = []

        def execute(program, grid, phase):
            calls.append((program, grid[0][0], phase))
            if program == "rejected":
                self.assertEqual(grid, [[1]], "a rejected rival received a query")
                return [[0]]
            if program == "ambiguous" and grid == [[3]]:
                return [[5]]
            return [[grid[0][0] + 1]]

        result = audit.audit_predictions(episode, candidates, "actual", execute)
        self.assertEqual([call[1] for call in calls], [1, 1, 1, 1, 3, 3, 3])
        self.assertEqual(result["surviving_rivals"], ["same", "ambiguous"])
        self.assertEqual(result["ambiguous_rivals"], ["ambiguous"])
        self.assertEqual(result["rivals"]["rejected"]["query_status"], "not_run_demo_rejected")
        self.assertEqual(result["rivals"]["ambiguous"]["query_mismatch_indices"], [0])
        self.assertEqual(result["failures"], [])

    def test_execution_error_is_explicit_and_does_not_become_rejection(self):
        audit = self.require_audit()
        episode = {"train": [{"input": [[1]], "output": [[2]]}],
                   "test": [{"input": [[3]], "output": [[4]]}]}

        def execute(program, grid, phase):
            if program == "broken":
                raise RuntimeError("intentional evaluator failure")
            return [[grid[0][0] + 1]]

        result = audit.audit_predictions(episode, {"actual": "actual", "broken": "broken"},
                                         "actual", execute)
        self.assertEqual(result["rivals"]["broken"]["demo_status"], "execution_error")
        self.assertEqual(result["rivals"]["broken"]["query_status"], "not_run_demo_error")
        self.assertEqual(result["failures"][0]["candidate"], "broken")
        self.assertIn("intentional evaluator failure", result["failures"][0]["message"])

    def test_ambiguity_witness_keeps_demos_and_only_one_disagreeing_query(self):
        audit = self.require_audit()
        self.assertTrue(hasattr(audit, "ambiguity_witnesses"), "witness export must exist")
        episode = {"train": [{"input": [[1]], "output": [[2]]}],
                   "test": [{"input": [[3]], "output": [[4]]},
                            {"input": [[6]], "output": [[7]]}]}
        result = {"ambiguous_rivals": ["rival"],
                  "rivals": {"rival": {"query_mismatch_indices": [0, 1]}},
                  "actual_predictions": {"train": [[[2]]], "test": [[[4]], [[7]]]},
                  "survivor_query_predictions": {"rival": [[[5]], [[8]]]}}
        witnesses = audit.ambiguity_witnesses(episode, result, {"actual": "a", "rival": "b"}, "actual")
        self.assertEqual(len(witnesses), 1)
        witness = witnesses[0]
        self.assertEqual(witness["visible"], {"train": episode["train"], "test": [{"input": [[3]]}]})
        self.assertEqual(witness["actual_output"], [[4]])
        self.assertEqual(witness["rival_output"], [[5]])
        self.assertEqual(witness["rival_program"], "b")
        self.assertNotIn("future_queries", witness)

    def test_public_files_use_canonical_bytes_and_exact_visible_schema(self):
        audit = self.require_audit()
        with audit.same_checkout() as (adapter, worker, support, runtime):
            episode = adapter.generate(0, {"lattice_rule": "ray_size"}, 3, 4)
            checked = audit.check_public_projection(adapter, support, episode, 0, "ray_size", 3)
            self.assertTrue(checked["private_metadata_invariant"])
            self.assertTrue(checked["query1_single_vs_four_exact_bytes"])
            self.assertTrue(checked["future_queries_invariant"])
            turn = support.public_challenge_bytes(adapter.public_challenge(episode, 0))
            altered = deepcopy(episode)
            altered["test"] = altered["test"][:1]
            self.assertEqual(turn, support.public_challenge_bytes(adapter.public_challenge(altered, 0)))


if __name__ == "__main__":
    unittest.main()

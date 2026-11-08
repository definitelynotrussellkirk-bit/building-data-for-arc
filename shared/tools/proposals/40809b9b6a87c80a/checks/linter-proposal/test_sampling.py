"""Targeted regression tests for the optional sampling proposal."""
import unittest

import reproduce as r


class SamplingProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r.verify_manifest()
        cls.generator = r.load_generator()

    def test_existing_linter_reproduces_five_false_axis_warnings(self):
        measured, _, _ = r.sample_population(r.ORIGINAL, self.generator)
        self.assertEqual(measured["profile_counts"], {"rich_top": 24})
        self.assertEqual(measured["sample_count"], 24)
        self.assertEqual(measured["axis_errors"], [])
        self.assertEqual(len(measured["axis_warnings"]), 5)

    def test_candidate_samples_both_phases_without_increasing_budget(self):
        measured, _, _ = r.sample_population(r.CANDIDATE, self.generator)
        self.assertEqual(measured["profile_counts"], {"varied": 12, "rich_top": 12})
        self.assertEqual(measured["sample_count"], 24)
        self.assertEqual(measured["axis_errors"], [])
        self.assertEqual(measured["axis_warnings"], [])
        self.assertEqual(measured["requests"][:8], [
            {"seed": 1, "sample_index": index, "difficulty": "easy"}
            for index in range(8)])

    def test_genuinely_narrow_generator_still_warns(self):
        measured, _, _ = r.sample_population(r.CANDIDATE, r.narrow_fixture())
        self.assertEqual(measured["axis_errors"], [])
        self.assertEqual(len(measured["axis_warnings"]), 1)
        self.assertIn("axis-span", measured["axis_warnings"][0])
        self.assertIn("[6, 6]", measured["axis_warnings"][0])

    def test_declared_period_coverage_is_honest_when_budget_is_partial(self):
        fixture = r.narrow_fixture()
        fixture.LESSON_SCHEDULE_PERIOD = 10
        partial, _, _ = r.sample_population(r.CANDIDATE, fixture, count=8)
        complete, _, _ = r.sample_population(r.CANDIDATE, fixture, count=10)
        for band in r.BANDS:
            self.assertEqual(partial["sampling"]["generated_index_coverage"][band],
                             {"residues": list(range(8)), "complete_at_fixed_seed": False})
            self.assertEqual(complete["sampling"]["generated_index_coverage"][band],
                             {"residues": list(range(10)), "complete_at_fixed_seed": True})

    def test_failed_generation_keeps_failed_request_and_partial_coverage(self):
        fixture = r.narrow_fixture()
        fixture.LESSON_SCHEDULE_PERIOD = 2
        generate = fixture.generate

        def fail_second(seed, sample_index, *, difficulty=None):
            if sample_index == 1:
                raise ValueError("deliberate failure fixture")
            return generate(seed, sample_index, difficulty=difficulty)

        fixture.generate = fail_second
        measured, _, _ = r.sample_population(r.CANDIDATE, fixture)
        receipt = measured["error"]["sampling"]
        self.assertIn("deliberate failure fixture", measured["error"]["error"])
        self.assertEqual([row["status"] for row in receipt["requests"]],
                         ["generated", "requested"])
        self.assertEqual(receipt["generated_index_coverage"]["easy"],
                         {"residues": [0], "complete_at_fixed_seed": False})

    def test_proposal_does_not_modify_other_detector_implementations(self):
        import ast
        original = ast.parse(r.ORIGINAL.read_text())
        candidate = ast.parse(r.CANDIDATE.read_text())
        original_functions = {node.name: ast.dump(node, include_attributes=False)
                              for node in original.body if isinstance(node, ast.FunctionDef)}
        candidate_functions = {node.name: ast.dump(node, include_attributes=False)
                               for node in candidate.body if isinstance(node, ast.FunctionDef)}
        for name, body in original_functions.items():
            if name != "lint_one":
                self.assertEqual(candidate_functions[name], body, name)


if __name__ == "__main__":
    unittest.main(verbosity=2)

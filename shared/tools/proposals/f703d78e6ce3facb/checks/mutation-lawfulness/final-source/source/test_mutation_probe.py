"""Focused checks of the mutation diagnostic, including its real reference route."""
import hashlib
import importlib.util
from pathlib import Path

import tempfile
import unittest

from reviewer_support import find_root

ROOT = find_root(__file__)
PROBE = Path(__file__).resolve().parents[1] / "workspace/mutation_probe.py"
WITNESS = [[7, 7, 5], [7, 7, 5], [5, 5, 5]]


def load_probe():
    assert PROBE.is_file(), "The task-local mutation probe has not been implemented"
    spec = importlib.util.spec_from_file_location("task_mutation_probe", PROBE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_minimal_mutations_reconstruct_named_lint_cases_without_mutating_input():
    probe = load_probe()
    original = [row[:] for row in WITNESS]
    mutations = probe.minimal_mutations(original)
    assert original == WITNESS
    assert mutations == {
        "all_background": [[5, 5, 5], [5, 5, 5], [5, 5, 5]],
        "full_one_color": [[7, 7, 7], [7, 7, 7], [7, 7, 7]],
        "singleton": [[5, 5, 5], [5, 7, 5], [5, 5, 5]],
        "solid_2x2": WITNESS,
        "short_line": [[5, 5, 5], [7, 7, 7], [5, 5, 5]],
    }
    mutations["solid_2x2"][0][0] = 8
    assert original == WITNESS


def test_modal_tie_follows_row_major_first_occurrence_and_small_shapes_clip():
    probe = load_probe()
    mutations = probe.minimal_mutations([[7, 5]])
    assert mutations["all_background"] == [[7, 7]]
    assert mutations["singleton"] == [[7, 5]]
    assert mutations["solid_2x2"] == [[5, 5]]
    assert mutations["short_line"] == [[5, 5]]
    assert probe.minimal_mutations([[5, 5]]) == {}
    with unittest.TestCase().assertRaises(ValueError):
        probe.minimal_mutations([[5, 7], [5]])


def test_racket_reference_keeps_domain_rejections_and_distinguishes_copy_rival():
    probe = load_probe()
    with tempfile.TemporaryDirectory(prefix="mutation-test-") as directory:
        report = probe.run_probe(
            task_id="75ba893e1e36", base_inputs=[WITNESS], root=ROOT,
            out=Path(directory) / "evidence", rival_name="horizontal-copy-4", timeout=90,
        )
    assert report["status"] == "completed", report.get("failures")
    assert report["apply_receipt"]["executed_rule_hash"] == "6d59d4b5186a"
    assert report["apply_receipt"]["rule_hash_matches_catalog"] is True
    source = ROOT / "generators/75ba893e1e36/generator.py"
    assert report["sources"]["generator"]["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    cases = {row["mutation_kind"]: row for row in report["cases"]}
    solid = cases["solid_2x2"]
    assert solid["generator_domain"] == {"status": "valid", "errors": []}
    assert solid["reference"]["valid_output"] is True
    assert solid["reference"]["output"] == [
        [5, 7, 7, 7, 7, 5, 5, 7, 7, 7, 7, 5],
        [5, 7, 7, 7, 7, 5, 5, 7, 7, 7, 7, 5],
        [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    ]
    assert solid["reference"]["metrics"]["dimensions"] == [3, 12]
    assert solid["reference"]["metrics"]["cell_count"] == 36
    assert solid["rival"]["equal_to_reference"] is False
    assert solid["rival"]["differing_cells"] == 8
    for name in ("all_background", "full_one_color", "singleton", "short_line"):
        assert cases[name]["generator_domain"]["status"] == "invalid"
        assert cases[name]["generator_domain"]["errors"]
        assert cases[name]["reference"]["valid_output"] is True
    assert report["summary"]["cases"] == 6
    assert report["summary"]["domain_accepted"] == 2
    assert report["summary"]["accepted_and_distinguishes_rival"] == 2
    assert report["claims"] == {
        "generic_mutation_acceptance_proves_safety": False,
        "generic_mutation_acceptance_proves_identifiability": False,
        "legal_reference_output_proves_domain_membership": False,
    }


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(test) for test in (
            test_minimal_mutations_reconstruct_named_lint_cases_without_mutating_input,
            test_modal_tie_follows_row_major_first_occurrence_and_small_shapes_clip,
            test_racket_reference_keeps_domain_rejections_and_distinguishes_copy_rival,
        )
    )


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Independent semantic regressions against the unchanged canonical Racket rule.

Portable canonical access uses reviewer_support. The module labels its literal
edge cases and canonical examples in one public Catalog.apply batch, then checks
the selected generator against those labels and a separate run-based detector.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
import shutil
import sys

import pytest

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root


TASK_ID = "d48317a7c7c8"
ROOT = find_root(__file__)
PROBE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "probe_review.py"
if not PROBE_PATH.is_file():
    PROBE_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "workspace" / "probe_review.py"
SPEC = importlib.util.spec_from_file_location(f"reference_semantics_{TASK_ID}", PROBE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROBE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROBE
SPEC.loader.exec_module(PROBE)
GEN = PROBE.load_generator(ROOT)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
CASES = PROBE.semantic_cases()
RACKET = os.environ.get("RACKET_PATH") or shutil.which("racket")


@pytest.fixture(scope="module")
def reference_labels():
    if not RACKET:
        pytest.skip("Racket is required; use the review packet's verified wrapper")
    catalog = Catalog(ROOT)
    description = catalog.describe(TASK_ID)
    inputs = [pair["input"] for pair in CANONICAL] + [case["input"] for case in CASES]
    assert len(inputs) <= 64
    receipt = catalog.apply(TASK_ID, inputs, reference="canonical", timeout=300)
    assert receipt["generator_sha256"] == description["generator_sha256"]
    assert receipt["rule_hash_matches_catalog"] is True
    assert receipt["catalog_rule_hash"] == PROBE.RULE_HASH
    assert receipt["executed_rule_hash"] == PROBE.RULE_HASH
    assert all(result["error"] is None for result in receipt["results"])
    return receipt["results"]


def test_reference_pin_matches_the_selected_canonical_authority():
    assert GEN.RULE_HASH == PROBE.RULE_HASH
    assert Catalog(ROOT).describe(TASK_ID)["rule_hash"] == PROBE.RULE_HASH


def test_every_canonical_pair_matches_actual_racket_and_independent_detection(reference_labels):
    assert len(CANONICAL) == 5
    for pair, result in zip(CANONICAL, reference_labels[:len(CANONICAL)], strict=True):
        assert result["output"] == pair["output"]
        assert PROBE.independent_reference(pair["input"]) == result["output"]
        assert GEN.self_check(deepcopy(pair["input"])) == []
        assert GEN.strict_canonical_like(deepcopy(pair["input"])) in ([], True)
        assert GEN.rule_mirror(deepcopy(pair["input"])) == result["output"]


@pytest.mark.parametrize("case_index", range(len(CASES)), ids=[case["name"] for case in CASES])
def test_exact_components_connectivity_and_cap_conditions(case_index, reference_labels):
    case = CASES[case_index]
    result = reference_labels[len(CANONICAL) + case_index]
    assert result["input"] == case["input"]
    assert result["output"] == case["expected_output"], case["name"]
    assert PROBE.independent_reference(case["input"]) == result["output"]
    assert GEN.rule_mirror(deepcopy(case["input"])) == result["output"]


@pytest.mark.parametrize("name", [
    "yellow_four_bar_unchanged", "triple_inside_bent_four_unchanged",
])
def test_self_check_rejects_substrings_that_are_not_exact_target_components(name):
    grid = next(case["input"] for case in CASES if case["name"] == name)
    assert len(grid) == len(grid[0]) == 8
    assert PROBE.exact_yellow_bars(grid) == []
    assert GEN.self_check(deepcopy(grid)), "A yellow three-run inside a larger component is not a target"


def test_compact_rich_witness_is_small_and_refutes_the_actual_declared_rivals(reference_labels):
    index = next(i for i, case in enumerate(CASES) if case["name"] == "compact_rich_counterexample")
    grid = CASES[index]["input"]
    expected = reference_labels[len(CANONICAL) + index]["output"]
    assert len(grid) == len(grid[0]) == 8
    assert PROBE.output_difference(grid, expected) == [[1, 3, 0, 8], [6, 6, 0, 8]]
    assert len(PROBE.exact_yellow_bars(grid)) == 2
    rivals, _, _ = PROBE.discover_rivals(GEN)
    assert rivals, "The repair must expose its executable teaching rivals"
    for name, solve in rivals.items():
        assert solve(deepcopy(grid)) != expected, name


def test_firing_witnesses_really_refute_their_named_rivals(reference_labels):
    for case, result in zip(CASES, reference_labels[len(CANONICAL):], strict=True):
        for witness, named in GEN.WITNESS_RIVALS.items():
            if GEN.SEMANTIC_WITNESSES[witness](deepcopy(case["input"])):
                named = [named] if isinstance(named, str) else named
                assert any(GEN.SEMANTIC_RIVALS[name](deepcopy(case["input"])) != result["output"]
                           for name in named), (case["name"], witness)

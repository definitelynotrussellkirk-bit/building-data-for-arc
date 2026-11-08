"""Portable behavioral characterization of the optimized Racket authority.

No wall-clock performance threshold belongs in these unit tests.  Separate
source-bound benchmarks retain baseline failures and measured timings.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "4f065093e631"
ROOT = find_root(__file__)
_generator, _source_path, _source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
# Staged generators live under puzzle_generators/per_puzzle, while authored
# workspace files retain their generators/TASK location under the public root.
PERFORMANCE = ROOT / "generators" / TASK_ID / "workspace" / "performance"
_spec = importlib.util.spec_from_file_location("task_frame_performance_probe", PERFORMANCE / "probe_rule.py")
probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(probe)


@pytest.fixture(scope="module")
def rule_source():
    path = PERFORMANCE / "optimized_rule.rkt"
    assert path.is_file(), "Optimized authority candidate has not yet been implemented"
    return path.read_text()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=30) as value:
        yield value


@pytest.mark.parametrize("pair", canonical_pairs(TASK_ID, root=ROOT),
                         ids=lambda p: f"{p['split']}-{p['pair_index']}")
def test_reference_candidate_preserves_every_canonical_anchor(pair, rule_source, bridge):
    assert probe.execute(bridge, rule_source, pair["input"]) == pair["output"]


@pytest.mark.parametrize("case", probe.handmade_cases(), ids=lambda case: case["id"])
def test_reference_candidate_preserves_broad_boundary_target_and_tie_behavior(case, rule_source, bridge):
    snapshot = [row[:] for row in case["input"]]
    actual = probe.execute(bridge, rule_source, case["input"])
    assert actual == case["expected"]
    assert case["input"] == snapshot


@pytest.mark.parametrize("case", [case for case in probe.handmade_cases()
                                  if case["id"].startswith("equal_area_")],
                         ids=lambda case: case["id"])
def test_python_mirror_preserves_reference_equal_area_ties(case):
    assert _generator.rule_mirror(case["input"]) == case["expected"]


def test_default_parametric_selection_fragments_remain_unambiguous(rule_source):
    assert rule_source.count("(target (fst slots))") == 1
    paint = "(paint-cells g (border-cells (first target) (second target) (third target) (fourth target)) color)"
    assert rule_source.count(paint) == 1

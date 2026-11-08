"""Bounded reference tests; these neither approve nor parameterize the variant."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("waypoint_reference_validation", HOME / "workspace/validate_reference.py")
SUPPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUPPORT)
GENERATOR_SHA256 = "b0c6b063ee8f18c10ddaefc8692939d88365692671eb8d255e0ced0b596cc3bc"
PROGRAM_SHA256 = "151b92a1061d985d8cd21e3dbc8ddea3a8f01bdffe7365b618d5adf2571144f3"


@pytest.fixture(scope="module")
def live():
    with SUPPORT.executor() as executor:
        yield executor


def test_standalone_preserves_exact_existing_rule_and_source():
    gen = SUPPORT.generator()
    assert hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest() == GENERATOR_SHA256
    assert (HOME / "reference.rkt").read_text() == gen.PROGRAM
    assert hashlib.sha256(gen.PROGRAM.encode()).hexdigest() == PROGRAM_SHA256
    assert gen.RULE_HASH == "ad2fb3607800"


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", range(4))
def test_generated_labels_match_real_racket(live, difficulty, seed):
    gen = SUPPORT.generator()
    task = gen.generate_task(seed, difficulty=difficulty)
    assert gen.self_check_task(task) == []
    for pair in task["train"] + task["test"]:
        assert gen.strict_canonical_like(pair["input"]) == []
        assert SUPPORT.execute(live, pair["input"]) == pair["output"] == gen._apply(pair["input"])


@pytest.mark.parametrize("turns,heading", [(0, "up"), (1, "right"), (2, "down"), (3, "left")])
def test_two_step_route_determines_final_position_and_orientation(live, turns, heading):
    case = SUPPORT.direction_case(turns)
    assert case["heading"] == heading
    assert SUPPORT.generator().strict_canonical_like(case["input"]) == []
    assert SUPPORT.execute(live, case["input"]) == case["expected"]


def test_fixed_teaching_and_four_query_record_relabels_exactly(live):
    row = json.loads((HOME / "evidence/canonical-reference/canonical-record.json").read_text())
    assert row == SUPPORT.candidate(live)
    assert len(row["train"]) == 3
    assert len(row["test"]) == 4
    assert len({json.dumps(pair["input"]) for pair in row["train"] + row["test"]}) == 7
    assert row["parent_hash"] == "5545f144"
    assert row["parent_reason"].startswith("semantic_variant")
    gen = SUPPORT.generator()
    assert gen.self_check_task({"train": row["train"], "test": row["test"],
                               "program": gen.PROGRAM, "meta": {"rule_hash": gen.RULE_HASH}}) == []


def test_earlier_panel_erasure_remains_a_known_unresolved_limitation(live):
    case = SUPPORT.direction_case(0)
    erased = copy.deepcopy(case["input"])
    for row in erased:
        row[:10] = [0] * 10
    assert SUPPORT.execute(live, erased) == SUPPORT.execute(live, case["input"])
    assert SUPPORT.generator().strict_canonical_like(erased) == []


def test_sequential_waypoint_change_changes_racket_answer(live):
    case = SUPPORT.direction_case(0)
    altered = copy.deepcopy(case["input"])
    # Replace only the final waypoint, keeping the same unique two-step route.
    altered[4][11 + 4] = 0
    altered[1][11 + 4] = 2
    assert SUPPORT.generator().strict_canonical_like(altered) == []
    assert SUPPORT.execute(live, altered) != SUPPORT.execute(live, case["input"])

"""Racket-backed contracts for the proposed junction-degree prototype.

The prototype is separate from canonical production generation and approval.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest
from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

TASK_ID = "6c93e8516229"
ROOT = find_root(__file__)
PROTOTYPE = (
    ROOT
    / "generators"
    / TASK_ID
    / "workspace"
    / "parametric"
    / "prototype.py"
)


def load_prototype():
    assert PROTOTYPE.is_file(), "the runnable parametric prototype must exist"
    spec = importlib.util.spec_from_file_location(
        f"parametric_{TASK_ID}", PROTOTYPE
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return load_prototype()


@pytest.fixture(scope="module")
def racket():
    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=64) as bridge:
        yield bridge


def test_default_program_is_exact_canonical_and_alternative_is_bounded(prototype):
    canonical = prototype.canonical_record()["program_solution"]
    assert prototype.PARAMETER == {
        "name": "junction_degree",
        "values": [3, 4],
        "default": 3,
        "input_constraints": (
            "unchanged canonical tree-component grammar; demonstrations include "
            "both degree-3 and degree-4 junctions"
        ),
    }
    assert prototype.program_for(3) == canonical
    alternative = prototype.program_for(4)
    assert alternative != canonical
    assert canonical.count("(= nbr-count 3)") == 1
    assert alternative.count("(= nbr-count 4)") == 1
    with pytest.raises(ValueError):
        prototype.program_for(2)
    with pytest.raises(ValueError):
        prototype.program_for(True)


def test_default_racket_program_matches_all_canonical_pairs(prototype, racket):
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    assert [
        prototype.execute(racket, prototype.program_for(3), pair["input"])
        for pair in pairs
    ] == [pair["output"] for pair in pairs]


@pytest.mark.parametrize("seed,expected_degree", [(0, 3), (1, 4)])
def test_complete_episode_uses_one_identifiable_setting(
    prototype, racket, seed, expected_degree
):
    public, private = prototype.generate_episode(seed, racket)
    assert private["parameter"] == {"junction_degree": expected_degree}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert all(prototype.GEN.self_check(pair["input"]) == [] for pair in public["train"])
    assert prototype.GEN.self_check(public["test"][0]["input"]) == []

    rival = 4 if expected_degree == 3 else 3
    assert private["rival_checks"][str(rival)]["matches_all_demonstrations"] is False
    assert private["rival_checks"][str(rival)]["query_matches_selected"] is False
    serialized = json.dumps(public, sort_keys=True)
    assert "junction_degree" not in serialized
    assert "program" not in serialized
    assert "query_answers" not in serialized


def test_degree_three_and_four_rules_disagree_on_lawful_witness(prototype, racket):
    inputs = prototype.episode_inputs(0)
    witness = inputs[0]
    assert prototype.GEN.self_check(witness) == []
    degree3 = prototype.execute(racket, prototype.program_for(3), witness)
    degree4 = prototype.execute(racket, prototype.program_for(4), witness)
    assert degree3 != degree4

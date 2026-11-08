"""Native post-expansion component family tests for 724d5770b986."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK = "724d5770b986"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    return _load("post_component_family_724d5770b986_test", HOME / "family.py")


def test_contract_and_default_program_are_exact(family):
    contract = json.loads((HOME / "promotion.json").read_text())
    canonical = (HOME / "canonical.rkt").read_text()
    assert contract["parameters"] == {
        "post_action": ["expand_only", "highlight_largest_post_component"]
    }
    assert contract["default"] == {"post_action": "expand_only"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 2
    assert family.program({"post_action": "expand_only"}) == canonical
    assert family.program({"post_action": "highlight_largest_post_component"}) != canonical


@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (3, 4), (6, 1), (6, 4)])
def test_counts_matched_inputs_prefix_stability_and_claims(family, demos, queries):
    episodes = [family.generate(17, setting, demos, queries) for setting in family.SETTINGS]
    assert [p["input"] for p in episodes[0]["train"] + episodes[0]["test"]] == [
        p["input"] for p in episodes[1]["train"] + episodes[1]["test"]
    ]
    for setting, episode in zip(family.SETTINGS, episodes):
        assert episode == family.generate(17, setting, demos, queries)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        assert episode["program_solution"] == family.program(setting)
        serial = [json.dumps(p["input"], separators=(",", ":")) for p in episode["train"] + episode["test"]]
        assert len(serial) == len(set(serial))
        assert all(p["output"] == family.solve(p["input"], setting) for p in episode["train"] + episode["test"])
    assert family.generate(17, family.SETTINGS[1], demos, 1)["test"] == episodes[1]["test"][:1]
    assert all(a["output"] != b["output"] for a, b in zip(episodes[0]["train"], episodes[1]["train"]))


def test_scene_grammar_forces_post_expansion_reasoning_and_large_stress(family):
    episode = family.generate(0, family.SETTINGS[1], 6, 4)
    assert [(len(p["input"]), len(p["input"][0])) for p in episode["test"]][-1] == (30, 30)
    for pair in episode["train"] + episode["test"]:
        facts = family.analyze(pair["input"])
        assert facts["valid"] is True
        assert facts["post_component_sizes"][0] > facts["post_component_sizes"][1]
        assert facts["largest_original_component"] != facts["largest_post_component_original_triggers"]
        assert facts["setting_outputs_distinct"] is True
    large = episode["test"][-1]["input"]
    occupied = [(r, c) for r, row in enumerate(large) for c, v in enumerate(row) if v]
    assert len(occupied) >= 40
    assert {r for r, _ in occupied} & {0, 29} == {0, 29}
    assert {c for _, c in occupied} & {0, 29} == {0, 29}


def test_public_turn_is_allowlisted_and_private_invariant(family):
    episode = family.generate(19, family.SETTINGS[1], 3, 4)
    turn = family.public_turn(episode, 0)
    assert set(turn) == {"train", "test"}
    assert len(turn["test"]) == 1 and set(turn["test"][0]) == {"input"}
    assert hashlib.sha256(public_challenge_bytes(turn)).hexdigest() == public_challenge_id(turn)
    altered = copy.deepcopy(episode)
    altered["settings"] = {"private": True}
    altered["program_solution"] = "private"
    altered["test"][0]["output"] = [[9]]
    altered["test"][1:] = [{"input": [[8]], "output": [[7]]}] * 3
    assert family.public_turn(altered, 0) == turn


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    bridge = RacketBridge()
    assert bridge.runtime_identity["backend"] == "racket"
    assert bridge.runtime_identity["protected"] is True
    def apply(program, grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrap_rule(program)} {literal})")
    yield apply
    bridge.close()


def test_protected_racket_matches_and_wrong_intermediate_changes_result(family, racket):
    for setting in family.SETTINGS:
        episode = family.generate(3, setting, 2, 4)
        for pair in episode["train"] + episode["test"]:
            assert racket(family.program(setting), pair["input"]) == pair["output"]
    pair = family.generate(3, family.SETTINGS[1], 2, 4)["test"][-1]
    wrong = racket((HOME / "rank_before_expand.rkt").read_text(), pair["input"])
    assert wrong != pair["output"]


def test_bounded_audit_refutes_named_rivals(family, racket):
    audit = _load("post_component_audit_724d5770b986_test", HOME / "audit.py")
    report = audit.run(seeds=[0], demo_counts=[2], queries=4, apply_program=racket)
    assert report["passed"] is True
    assert report["job_count"] == 2
    assert report["racket_evaluations"] > 0
    assert all(job["surviving_rivals"] == [] for job in report["jobs"])
    assert report["causal_case"]["output"] != report["causal_case"]["counterfactual_output"]

"""Native transform-codebook family tests for 600ed4e5d09c."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK = "600ed4e5d09c"
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
    return _load("transform_codebook_family_600ed4e5d09c_test", HOME / "family.py")


def test_contract_and_byte_exact_default(family):
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["parameters"] == {"transform_codebook": ["canonical", "inverse"]}
    assert contract["default"] == {"transform_codebook": "canonical"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 2
    assert family.program(family.SETTINGS[0]) == (HOME / "canonical.rkt").read_text()


@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (3, 4), (6, 1), (6, 4)])
def test_counts_matched_inputs_prefix_stability_and_labels(family, demos, queries):
    episodes = [family.generate(23, setting, demos, queries) for setting in family.SETTINGS]
    inputs = [[p["input"] for p in ep["train"] + ep["test"]] for ep in episodes]
    assert inputs[0] == inputs[1]
    for setting, episode in zip(family.SETTINGS, episodes):
        assert episode == family.generate(23, setting, demos, queries)
        assert len(episode["train"]) == demos and len(episode["test"]) == queries
        assert episode["program_solution"] == family.program(setting)
        assert all(p["output"] == family.solve(p["input"], setting) for p in episode["train"] + episode["test"])
        serial = [json.dumps(p["input"], separators=(",", ":")) for p in episode["train"] + episode["test"]]
        assert len(serial) == len(set(serial))
    assert family.generate(23, family.SETTINGS[1], demos, 1)["test"] == episodes[1]["test"][:1]
    assert any(a["output"] != b["output"] for a, b in zip(episodes[0]["train"], episodes[1]["train"]))


def test_scene_grammar_and_30x30_stress(family):
    episode = family.generate(0, family.SETTINGS[0], 6, 4)
    assert [(len(p["input"]), len(p["input"][0])) for p in episode["test"]][-1] == (30, 30)
    for pair in episode["train"] + episode["test"]:
        facts = family.analyze(pair["input"])
        assert facts["valid"] is True
        assert facts["target_dihedral_orbit"] == 8
        assert facts["frame_count"] == 1
        assert facts["target_count"] == 1
    large = episode["test"][-1]["input"]
    occupied = [(r, c) for r, row in enumerate(large) for c, v in enumerate(row) if v]
    assert len(occupied) >= 55
    assert {r for r, _ in occupied} & {0, 29} == {0, 29}
    assert {c for _, c in occupied} & {0, 29} == {0, 29}


def test_public_turn_allowlist_and_private_invariance(family):
    episode = family.generate(3, family.SETTINGS[1], 3, 4)
    turn = family.public_turn(episode, 0)
    assert set(turn) == {"train", "test"}
    assert len(turn["test"]) == 1 and set(turn["test"][0]) == {"input"}
    assert hashlib.sha256(public_challenge_bytes(turn)).hexdigest() == public_challenge_id(turn)
    altered = copy.deepcopy(episode)
    altered["settings"] = {"secret": 1}
    altered["program_solution"] = "secret"
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


def test_protected_racket_matches_and_skip_transform_changes_output(family, racket):
    for setting in family.SETTINGS:
        episode = family.generate(5, setting, 2, 4)
        for pair in episode["train"] + episode["test"]:
            assert racket(family.program(setting), pair["input"]) == pair["output"]
    pair = family.generate(5, family.SETTINGS[1], 2, 4)["test"][0]
    wrong = racket((HOME / "skip_transform.rkt").read_text(), pair["input"])
    assert wrong != pair["output"]


def test_bounded_audit_refutes_named_rivals(family, racket):
    audit = _load("transform_codebook_audit_600ed4e5d09c_test", HOME / "audit.py")
    report = audit.run(seeds=[0], demo_counts=[2], queries=4, apply_program=racket)
    assert report["passed"] is True
    assert report["job_count"] == 2
    assert report["racket_evaluations"] > 0
    assert all(job["surviving_rivals"] == [] for job in report["jobs"])
    assert report["causal_case"]["output"] != report["causal_case"]["counterfactual_output"]

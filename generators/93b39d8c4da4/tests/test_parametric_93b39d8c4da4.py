"""Native parametric family tests for 93b39d8c4da4."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK = "93b39d8c4da4"
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
    return _load("parametric_family_93b39d8c4da4_test", HOME / "family.py")


def test_default_program_is_byte_exact_and_contract_is_bounded(family):
    canonical = (HOME / "canonical.rkt").read_text(encoding="utf-8")
    assert family.program({"template_transform": "identity"}) == canonical
    assert family.program({"template_transform": "mirror_lr"}) != canonical
    assert family.program({"template_transform": "rotate_cw"}) != canonical
    contract = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    assert contract["parameters"] == {
        "template_transform": ["identity", "mirror_lr", "rotate_cw"]
    }
    assert contract["default"] == {"template_transform": "identity"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 2


@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (3, 4), (6, 1), (6, 4)])
def test_counts_are_independent_matched_unique_and_prefix_stable(family, demos, queries):
    episodes = [family.generate(17, setting, demos, queries) for setting in family.SETTINGS]
    for setting, episode in zip(family.SETTINGS, episodes):
        assert episode == family.generate(17, setting, demos, queries)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        assert episode["program_solution"] == family.program(setting)
        pairs = episode["train"] + episode["test"]
        inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
        assert len(inputs) == len(set(inputs))
        assert all(pair["output"] == family.solve(pair["input"], setting) for pair in pairs)

    reference_inputs = [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]]
    for episode in episodes[1:]:
        assert [pair["input"] for pair in episode["train"] + episode["test"]] == reference_inputs
    for pair_index in range(demos):
        assert len({json.dumps(ep["train"][pair_index]["output"]) for ep in episodes}) == 3

    one = family.generate(17, family.SETTINGS[1], demos, 1)
    four = family.generate(17, family.SETTINGS[1], demos, 4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]


def test_grammar_and_substantive_large_queries(family):
    episode = family.generate(0, family.SETTINGS[0], 6, 4)
    assert [(len(p["input"]), len(p["input"][0])) for p in episode["test"]] == [
        (30, 30), (24, 30), (30, 24), (27, 29)
    ]
    for pair in episode["train"] + episode["test"]:
        facts = family.analyze(pair["input"])
        assert facts["valid_for_all_settings"] is True
        assert facts["template_bbox"] == [3, 3]
        assert facts["template_orbit"] == 8
        assert facts["marker_count"] >= 6
        assert facts["setting_outputs_distinct"] is True
        assert facts["overlapping_stamp_pair"] is True
    large = episode["test"][0]["input"]
    occupied = [(r, c) for r, row in enumerate(large) for c, v in enumerate(row) if v]
    assert len(occupied) >= 14
    assert {r for r, _ in occupied} & {0, 29} == {0, 29}
    assert {c for _, c in occupied} & {0, 29} == {0, 29}


def test_public_turn_reveals_only_one_query_and_hashes_visible_bytes(family):
    episode = family.generate(19, family.SETTINGS[2], 3, 4)
    turn = family.public_turn(episode, 0)
    assert set(turn) == {"train", "test"}
    assert len(turn["test"]) == 1
    assert set(turn["test"][0]) == {"input"}
    assert hashlib.sha256(public_challenge_bytes(turn)).hexdigest() == public_challenge_id(turn)

    altered = copy.deepcopy(episode)
    altered["program_solution"] = "private"
    altered["test"][0]["output"] = [[9]]
    altered["test"][1:] = [{"input": [[8]], "output": [[7]]}] * 3
    altered["settings"] = {"secret": True}
    assert family.public_turn(altered, 0) == turn
    assert family.public_turn(family.generate(19, family.SETTINGS[2], 3, 1), 0) == turn


@pytest.mark.parametrize("settings", [
    None, {}, {"template_transform": "bad"}, {"template_transform": True},
    {"template_transform": "identity", "extra": 1},
])
def test_invalid_settings_are_rejected(family, settings):
    with pytest.raises((TypeError, ValueError)):
        family.program(settings)


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 2, 4), (-1, 2, 4), (2**63, 2, 4),
    (0, True, 4), (0, 1, 4), (0, 7, 4),
    (0, 2, True), (0, 2, 0), (0, 2, 5),
])
def test_invalid_requests_are_rejected_before_sampling(family, seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        family.generate(seed, family.SETTINGS[0], demos, queries)


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


@pytest.mark.parametrize("seed", [0, 17])
def test_protected_racket_matches_claims(family, racket, seed):
    for setting in family.SETTINGS:
        episode = family.generate(seed, setting, 2, 4)
        for pair in episode["train"] + episode["test"]:
            assert racket(family.program(setting), pair["input"]) == pair["output"]


def test_wrong_intermediate_changes_final_output(family):
    episode = family.generate(0, family.SETTINGS[1], 2, 4)
    grid = episode["test"][0]["input"]
    intended = family.solve(grid, family.SETTINGS[1])
    wrong = family.solve_with_shape(grid, family.SETTINGS[1], ((0, 0), (1, 0), (2, 0), (2, 1)))
    assert wrong != intended


def test_bounded_self_audit_executes_racket_rivals(family, racket):
    audit = _load("parametric_audit_93b39d8c4da4_test", HOME / "audit.py")
    report = audit.run(seeds=[0], demo_counts=[2], queries=4, apply_program=racket)
    assert report["passed"] is True
    assert report["job_count"] == 3
    assert report["racket_evaluations"] > 0
    assert all(job["surviving_rivals"] == [] for job in report["jobs"])
    assert report["causal_case"]["output"] != report["causal_case"]["counterfactual_output"]

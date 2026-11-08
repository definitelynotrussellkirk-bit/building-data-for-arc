"""Focused native parametric checks for prototype-controlled stamp transforms."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import (
    canonical_path, find_root, public_challenge_bytes, public_challenge_id,
)

TASK_ID = "274345a1792c"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


@pytest.fixture(scope="module")
def p():
    path = HOME / "prototype.py"
    assert path.is_file(), "native parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("stamp_transform_parametric", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_program():
    for line in canonical_path(ROOT).open():
        row = json.loads(line)
        if row.get("task_id") == "274345a1792c":
            return row["program_solution"]
    raise AssertionError("canonical rule missing")


def test_default_program_is_exact_canonical_and_contract_is_bounded(p):
    assert p.program({"transform_family": "mixed"}) == canonical_program()
    assert p.program({"transform_family": "rotations"}) != canonical_program()
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["parameters"] == {"transform_family": ["mixed", "rotations"]}
    assert contract["default"] == {"transform_family": "mixed"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3


@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (3, 4), (6, 1), (6, 4)])
def test_counts_are_independent_deterministic_matched_and_unique(p, demos, queries):
    episodes = [p.generate(17, settings, demos, queries) for settings in p.SETTINGS]
    for settings, episode in zip(p.SETTINGS, episodes):
        assert episode == p.generate(17, settings, demos, queries)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        assert episode["program_solution"] == p.program(settings)
        pairs = episode["train"] + episode["test"]
        keys = [json.dumps(pair["input"]) for pair in pairs]
        assert len(keys) == len(set(keys))
        assert all(pair["output"] == p.solve(pair["input"], settings) for pair in pairs)
    left = episodes[0]["train"] + episodes[0]["test"]
    right = episodes[1]["train"] + episodes[1]["test"]
    assert [pair["input"] for pair in left] == [pair["input"] for pair in right]
    assert all(a["output"] != b["output"] for a, b in zip(episodes[0]["train"], episodes[1]["train"]))

    single = p.generate(17, p.SETTINGS[1], demos, 1)
    four = p.generate(17, p.SETTINGS[1], demos, 4)
    assert single["train"] == four["train"]
    assert single["test"] == four["test"][:1]


def test_constructive_grammar_and_substantive_large_queries(p):
    episode = p.generate(0, p.SETTINGS[0], 6, 4)
    assert [(len(x["input"]), len(x["input"][0])) for x in episode["test"]] == [
        (30, 30), (24, 30), (30, 24), (27, 29)
    ]
    for pair in episode["train"] + episode["test"]:
        facts = p.analyze(pair["input"])
        assert facts["prototype_cells"] in {5, 6, 7}
        assert facts["prototype_bbox"] == [3, 3]
        assert facts["prototype_orbit"] == 8
        assert facts["anchor_count"] == 5
        assert facts["controls"] == [1, 2, 3, 4]
        assert facts["repeated_control"] is True
        assert facts["valid_for_both_settings"] is True
    grid = episode["test"][0]["input"]
    occupied = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    assert len(occupied) >= 15
    assert {r for r, _ in occupied} & {0, 29} == {0, 29}
    assert {c for _, c in occupied} & {0, 29} == {0, 29}
    assert max(r for r, _ in occupied) - min(r for r, _ in occupied) == 29
    assert max(c for _, c in occupied) - min(c for _, c in occupied) == 29


def test_public_turn_reveals_one_query_without_private_or_future_fields(p):
    episode = p.generate(19, p.SETTINGS[1], 3, 4)
    turn = p.public_turn(episode, 0)
    assert set(turn) == {"train", "test"}
    assert len(turn["test"]) == 1
    assert set(turn["test"][0]) == {"input"}
    assert hashlib.sha256(public_challenge_bytes(turn)).hexdigest() == public_challenge_id(turn)

    altered = copy.deepcopy(episode)
    altered.update(seed=999, settings={"secret": True}, program_solution="private")
    altered["test"][0]["output"] = [[9]]
    altered["test"][1:] = [{"input": [[8]], "output": [[7]]}] * 3
    assert p.public_turn(altered, 0) == turn
    assert p.public_turn(p.generate(19, p.SETTINGS[1], 3, 1), 0) == turn


@pytest.mark.parametrize("settings", [
    {}, {"transform_family": "bad"}, {"transform_family": True},
    {"transform_family": "mixed", "extra": 1},
])
def test_invalid_settings_are_rejected(p, settings):
    with pytest.raises((TypeError, ValueError)):
        p.program(settings)


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 3, 4), (-1, 3, 4), (2**63, 3, 4),
    (0, True, 4), (0, 1, 4), (0, 7, 4),
    (0, 3, True), (0, 3, 0), (0, 3, 5),
])
def test_invalid_requests_are_rejected_before_sampling(p, seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        p.generate(seed, p.SETTINGS[0], demos, queries)


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
def test_protected_racket_matches_python_claims(p, racket, seed):
    for settings in p.SETTINGS:
        episode = p.generate(seed, settings, 2, 4)
        for pair in episode["train"] + episode["test"]:
            assert racket(p.program(settings), pair["input"]) == pair["output"]


def test_wrong_intermediate_fixed_l_changes_final_output(p):
    episode = p.generate(0, p.SETTINGS[0], 2, 4)
    grid = episode["test"][0]["input"]
    intended = p.solve(grid, p.SETTINGS[0])
    wrong = p.solve_with_shape(grid, p.SETTINGS[0], ((0, 0), (1, 0), (2, 0), (2, 1)))
    assert wrong != intended


def test_bounded_self_audit_executes_declared_rivals(p, racket):
    path = HOME / "audit.py"
    assert path.is_file(), "bounded protected-Racket audit tool is missing"
    spec = importlib.util.spec_from_file_location("stamp_transform_audit_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    report = module.run(seeds=[0], demo_counts=[2], queries=4, apply_program=racket)
    assert report["passed"] is True
    assert report["job_count"] == 2
    assert report["racket_evaluations"] > 0
    assert report["causal_case"]["output"] != report["causal_case"]["counterfactual_output"]
    assert report["causal_case"]["ablation"] == "wrong_intermediate"
    assert all(job["surviving_rivals"] == [] for job in report["jobs"])

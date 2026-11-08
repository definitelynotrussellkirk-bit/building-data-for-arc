"""Native parametric regressions for be6269bef667."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id


TASK_ID = "be6269bef667"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
CANONICAL = {"weighting": "unit"}
PLURALITY = {"weighting": "plurality_double"}


def load(name: str):
    path = PARAMETRIC / name
    assert path.is_file(), f"missing parametric source: {path}"
    module_name = f"_{TASK_ID}_{name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def canonical_record() -> dict:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical record missing")


def inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_contract_and_programs_preserve_exact_canonical_default():
    adapter = load("adapter.py")
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"weighting": ["unit", "plurality_double"]},
        "default": CANONICAL,
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/plurality_double.rkt",
        ],
    }
    assert adapter.program(CANONICAL) == canonical_record()["program_solution"]
    assert adapter.program(PLURALITY) != adapter.program(CANONICAL)


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_inputs_identify_settings_and_supply_four_distinct_queries(seed, demos):
    adapter = load("adapter.py")
    canonical = adapter.generate(seed, CANONICAL, demos, 4)
    plurality = adapter.generate(seed, PLURALITY, demos, 4)
    assert inputs(canonical) == inputs(plurality)
    assert len(canonical["train"]) == demos
    assert len(canonical["test"]) == 4
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in inputs(canonical)]
    assert len(serialized) == len(set(serialized)) == demos + 4
    assert all(a["output"] != b["output"] for a, b in zip(canonical["train"], plurality["train"]))

    for settings, episode in ((CANONICAL, canonical), (PLURALITY, plurality)):
        assert episode["program_solution"] == adapter.program(settings)
        for pair in episode["train"] + episode["test"]:
            facts = adapter.analyze(pair["input"])
            assert set(facts["direction_counts"]) == {1, 2, 3, 4}
            assert len(set(facts["direction_counts"].values())) >= 2
            assert facts["plurality_direction"] in {1, 2, 3, 4}
            assert pair["output"] == adapter.solve(pair["input"], settings["weighting"])
            assert max(max(row) for row in pair["output"]) <= 9

    first_two = [adapter.analyze(pair["input"])["plurality_direction"] for pair in canonical["train"][:2]]
    assert len(set(first_two)) == 2

    assert [(len(pair["input"]), len(pair["input"][0])) for pair in canonical["test"]] == [
        (10, 13), (17, 19), (30, 30), (24, 29)
    ]
    stress_input = canonical["test"][2]["input"]
    stress_output = canonical["test"][2]["output"]
    assert sum(value != 0 for row in stress_input for value in row) >= 28
    assert sum(value != 0 for row in stress_output for value in row) >= 420
    assert any(stress_input[0]) and any(stress_input[-1])
    assert any(row[0] for row in stress_input) and any(row[-1] for row in stress_input)


@pytest.mark.parametrize("weighting", ["unit", "plurality_double"])
def test_programs_execute_through_protected_racket_and_match_claims(weighting):
    adapter = load("adapter.py")
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    episode = adapter.generate(17, {"weighting": weighting}, 2, 4)
    source = wrap_rule(adapter.program({"weighting": weighting}))
    with RacketBridge() as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for pair in episode["train"] + episode["test"]:
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
            assert bridge.eval_text(f"({source} {literal})") == pair["output"]


def test_public_turn_is_prefix_stable_and_hashes_visible_bytes_only():
    adapter = load("adapter.py")
    one = adapter.generate(17, PLURALITY, 3, 1)
    four = adapter.generate(17, PLURALITY, 3, 4)
    assert public_challenge_bytes(adapter.public_turn(one)) == public_challenge_bytes(adapter.public_turn(four))
    public = adapter.public_turn(four, 1)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    before = copy.deepcopy(four)
    payload = public_challenge_bytes(public)
    assert public_challenge_id(public) == hashlib.sha256(payload).hexdigest()
    assert b"plurality_double" not in payload and b"program_solution" not in payload
    assert four == before


@pytest.mark.parametrize("weighting", ["unit", "plurality_double"])
def test_generation_is_deterministic_fresh_prefix_stable_and_rng_isolated(weighting):
    adapter = load("adapter.py")
    settings = {"weighting": weighting}
    state = random.getstate()
    full = adapter.generate(2**63 - 1, settings, 6, 4)
    again = adapter.generate(2**63 - 1, settings, 6, 4)
    assert full == again and full is not again
    assert random.getstate() == state
    for demos, queries in ((2, 1), (3, 4), (6, 1)):
        small = adapter.generate(2**63 - 1, settings, demos, queries)
        assert small["train"] == full["train"][:demos]
        assert small["test"] == full["test"][:queries]
    full["train"][0]["input"][0][0] = 8
    assert adapter.generate(2**63 - 1, settings, 6, 4) == again


@pytest.mark.parametrize(
    "args",
    [
        (True, CANONICAL, 3, 4), (-1, CANONICAL, 3, 4), (2**63, CANONICAL, 3, 4),
        (0, CANONICAL, 1, 4), (0, CANONICAL, 7, 4),
        (0, CANONICAL, 3, 0), (0, CANONICAL, 3, 5),
        (0, {}, 3, 4), (0, {"weighting": "unknown"}, 3, 4),
        (0, {"weighting": "unit", "extra": 1}, 3, 4),
    ],
)
def test_invalid_controls_fail_loudly(args):
    adapter = load("adapter.py")
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(*args)


def test_finite_demo_only_self_audit_rejects_plausible_shortcuts():
    adapter = load("adapter.py")
    rivals = load("rivals.py")
    for seed in (0, 17, 31):
        for demos in (2, 3, 6):
            for setting in (CANONICAL, PLURALITY):
                episode = adapter.generate(seed, setting, demos, 4)
                correct = setting["weighting"]
                survivors = [
                    name for name in rivals.RIVAL_NAMES
                    if all(rivals.predict(pair["input"], name) == pair["output"] for pair in episode["train"])
                ]
                assert survivors == [correct]
                assert all(
                    rivals.predict(pair["input"], correct) == pair["output"]
                    for pair in episode["test"]
                )

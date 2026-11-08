"""Native parametric regressions for 4ebdc8d865ce."""
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


TASK_ID = "4ebdc8d865ce"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric" / "anchor"
CANONICAL = {"selection": "isolated_twos"}
ANCHORED = {"selection": "anchor_sized_twos"}


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


def test_contract_and_programs_preserve_the_exact_canonical_default():
    adapter = load("adapter.py")
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"selection": ["isolated_twos", "anchor_sized_twos"]},
        "default": CANONICAL,
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/anchor_sized.rkt",
        ],
    }
    assert adapter.program(CANONICAL) == canonical_record()["program_solution"]
    assert adapter.program(ANCHORED) != adapter.program(CANONICAL)


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_inputs_identify_settings_and_supply_four_distinct_queries(seed, demos):
    adapter = load("adapter.py")
    canonical = adapter.generate(seed, CANONICAL, demos, 4)
    anchored = adapter.generate(seed, ANCHORED, demos, 4)
    assert inputs(canonical) == inputs(anchored)
    assert len(canonical["train"]) == demos
    assert len(canonical["test"]) == 4
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in inputs(canonical)]
    assert len(serialized) == len(set(serialized)) == demos + 4
    assert any(a["output"] != b["output"] for a, b in zip(canonical["train"], anchored["train"]))
    for settings, episode in ((CANONICAL, canonical), (ANCHORED, anchored)):
        assert episode["program_solution"] == adapter.program(settings)
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == adapter.solve(pair["input"], settings["selection"])
            facts = adapter.analyze(pair["input"])
            assert facts["anchor_size"] >= 2
            assert 1 in facts["two_sizes"]
            assert facts["anchor_size"] in facts["two_sizes"]
            assert facts["color4_sizes"].count(facts["anchor_size"]) == 1

    # The first two demonstrations vary the input-derived intermediate, ruling
    # out a fixed component-size shortcut at the minimum supported demo count.
    assert len({adapter.analyze(pair["input"])["anchor_size"] for pair in canonical["train"][:2]}) == 2

    assert [(len(pair["input"]), len(pair["input"][0])) for pair in canonical["test"]] == [
        (12, 14), (20, 23), (30, 30), (24, 29)
    ]
    large = canonical["test"][2]["input"]
    assert sum(value != 0 for row in large for value in row) >= 110
    occupied_rows = {r for r, row in enumerate(large) if any(row)}
    occupied_cols = {c for c in range(30) if any(large[r][c] for r in range(30))}
    assert min(occupied_rows) == 0 and max(occupied_rows) == 29
    assert min(occupied_cols) == 0 and max(occupied_cols) == 29


@pytest.mark.parametrize("selection", ["isolated_twos", "anchor_sized_twos"])
def test_programs_execute_through_protected_racket_and_match_claims(selection):
    adapter = load("adapter.py")
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    episode = adapter.generate(17, {"selection": selection}, 2, 4)
    source = wrap_rule(adapter.program({"selection": selection}))
    with RacketBridge() as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        for pair in episode["train"] + episode["test"]:
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
            assert bridge.eval_text(f"({source} {literal})") == pair["output"]


def test_public_turn_is_prefix_stable_and_hashes_visible_bytes_only():
    adapter = load("adapter.py")
    one = adapter.generate(17, ANCHORED, 3, 1)
    four = adapter.generate(17, ANCHORED, 3, 4)
    assert public_challenge_bytes(adapter.public_turn(one)) == public_challenge_bytes(adapter.public_turn(four))
    public = adapter.public_turn(four, 2)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    before = copy.deepcopy(four)
    payload = public_challenge_bytes(public)
    assert public_challenge_id(public) == hashlib.sha256(payload).hexdigest()
    assert b"anchor_sized_twos" not in payload and b"program_solution" not in payload
    assert four == before


@pytest.mark.parametrize("selection", ["isolated_twos", "anchor_sized_twos"])
def test_generation_is_deterministic_fresh_prefix_stable_and_rng_isolated(selection):
    adapter = load("adapter.py")
    settings = {"selection": selection}
    state = random.getstate()
    full = adapter.generate(2**63 - 1, settings, 6, 4)
    again = adapter.generate(2**63 - 1, settings, 6, 4)
    assert full == again and full is not again
    assert random.getstate() == state
    for demos, queries in ((2, 1), (3, 4), (6, 1)):
        small = adapter.generate(2**63 - 1, settings, demos, queries)
        assert small["train"] == full["train"][:demos]
        assert small["test"] == full["test"][:queries]
    full["train"][0]["input"][0][0] = 9
    assert adapter.generate(2**63 - 1, settings, 6, 4) == again


@pytest.mark.parametrize(
    "args",
    [
        (True, CANONICAL, 3, 4), (-1, CANONICAL, 3, 4), (2**63, CANONICAL, 3, 4),
        (0, CANONICAL, 1, 4), (0, CANONICAL, 7, 4),
        (0, CANONICAL, 3, 0), (0, CANONICAL, 3, 5),
        (0, {}, 3, 4), (0, {"selection": "unknown"}, 3, 4),
        (0, {"selection": "isolated_twos", "extra": 1}, 3, 4),
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
            for setting in (CANONICAL, ANCHORED):
                episode = adapter.generate(seed, setting, demos, 4)
                correct = setting["selection"]
                survivors = []
                for name in rivals.RIVAL_NAMES:
                    if all(
                        rivals.predict(pair["input"], name) == pair["output"]
                        for pair in episode["train"]
                    ):
                        survivors.append(name)
                assert survivors == [correct]
                # This is a demo-only fit check. Query labels are consulted only
                # after survivor selection to verify transfer/disagreement.
                assert all(
                    rivals.predict(pair["input"], correct) == pair["output"]
                    for pair in episode["test"]
                )

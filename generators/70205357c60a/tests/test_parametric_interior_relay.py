from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import find_root

TASK_ID = "70205357c60a"


def _load(name: str):
    root = Path(find_root(__file__))
    path = root / "generators" / TASK_ID / "workspace" / "parametric" / name
    spec = spec_from_file_location(f"_{TASK_ID}_{name.replace('.', '_')}", path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket():
    bridge = RacketBridge()
    assert bridge.runtime_identity["backend"] == "racket"
    assert bridge.runtime_identity["protected"] is True

    def run(program: str, grid: list[list[int]]) -> list[list[int]]:
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrap_rule(program)} {literal})")

    yield run
    bridge.close()


def test_default_program_is_exact_canonical_and_relay_is_distinct():
    family = _load("family.py")
    adapter = _load("adapter.py")
    canonical = (Path(family.__file__).with_name("canonical.rkt")).read_text()
    assert adapter.program({"mode": "canonical"}) == canonical
    assert adapter.program({"mode": "interior_count_relay"}) != canonical
    assert adapter.program({"mode": "interior_count_relay"}).startswith("(rule!")


def test_counts_are_independent_inputs_are_matched_and_fourth_query_is_30x30():
    adapter = _load("adapter.py")
    small = adapter.generate(11, {"mode": "canonical"}, demos=2, queries=1)
    large = adapter.generate(11, {"mode": "canonical"}, demos=6, queries=4)
    relay = adapter.generate(11, {"mode": "interior_count_relay"}, demos=6, queries=4)
    assert len(small["train"]) == 2 and len(small["test"]) == 1
    assert len(large["train"]) == 6 and len(large["test"]) == 4
    assert [p["input"] for p in large["train"] + large["test"]] == [
        p["input"] for p in relay["train"] + relay["test"]
    ]
    all_inputs = [json.dumps(p["input"], sort_keys=True) for p in large["train"] + large["test"]]
    assert len(all_inputs) == len(set(all_inputs))
    assert len(large["test"][3]["input"]) == 30
    assert len(large["test"][3]["input"][0]) == 30


def test_python_claims_match_protected_racket_and_demos_identify_mode(racket):
    adapter = _load("adapter.py")
    for mode in ("canonical", "interior_count_relay"):
        episode = adapter.generate(17, {"mode": mode}, demos=3, queries=4)
        chosen_program = adapter.program({"mode": mode})
        other_mode = "interior_count_relay" if mode == "canonical" else "canonical"
        other_program = adapter.program({"mode": other_mode})
        for pair in episode["train"] + episode["test"]:
            assert racket(chosen_program, pair["input"]) == pair["output"]
        assert all(racket(other_program, pair["input"]) != pair["output"] for pair in episode["train"])


def test_relay_intermediate_covers_one_two_three_and_wrong_intermediate_changes_output(racket):
    family = _load("family.py")
    values = set()
    for seed in range(9):
        episode = family.build_episode(seed, "interior_count_relay", 3, 4)
        values.update(family.interior_count(pair["input"]) for pair in episode["train"] + episode["test"])
    assert values == {1, 2, 3}

    episode = family.build_episode(0, "interior_count_relay", 3, 4)
    witness = next(pair for pair in episode["test"] if family.interior_count(pair["input"]) != 1)
    correct = racket(family.program_for("interior_count_relay"), witness["input"])
    wrong = racket(family.counterfactual_program(), witness["input"])
    assert correct == witness["output"]
    assert wrong != correct


@pytest.mark.parametrize("bad", [True, 1.0, -1, 2**63])
def test_seed_contract_is_strict(bad):
    adapter = _load("adapter.py")
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(bad, {"mode": "canonical"}, demos=3, queries=4)

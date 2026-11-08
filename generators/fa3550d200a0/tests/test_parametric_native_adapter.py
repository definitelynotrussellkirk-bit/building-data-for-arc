"""Native promotion contract for the fa3550d200a0 quarter-turn family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, public_challenge_bytes


TASK_ID = "fa3550d200a0"
ROOT = find_root(__file__)
HERE = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
SETTINGS = tuple({"quarter_turns": value} for value in range(4))


def _load(path: Path, suffix: str):
    assert path.is_file(), f"required native source is missing: {path.name}"
    source = path.read_bytes()
    name = f"_native_{TASK_ID}_{suffix}_{hashlib.sha256(str(path).encode() + source).hexdigest()}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load(HERE / "adapter.py", "adapter")


@pytest.fixture(scope="module")
def family():
    return _load(HERE / "native_family.py", "family")


@pytest.fixture(scope="module")
def racket_bridge():
    with RacketBridge(timeout=20.0) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        yield bridge


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _pairs(episode):
    return [*episode["train"], *episode["test"]]


def _inputs(episode):
    return [pair["input"] for pair in _pairs(episode)]


def _apply(bridge: RacketBridge, source: str, grid):
    proc = wrap_rule(source)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({proc} {literal})")


def test_promotion_contract_declares_four_turns_and_native_limits():
    contract = json.loads((HERE / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"quarter_turns": [0, 1, 2, 3]},
        "default": {"quarter_turns": 0},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [f"generators/{TASK_ID}/workspace/parametric/canonical.rkt"],
    }


def test_default_program_is_exact_canonical_and_all_turns_are_distinct(adapter):
    canonical = _canonical_program()
    programs = [adapter.program(setting) for setting in SETTINGS]
    assert programs[0] == canonical
    assert programs[0] == (HERE / "canonical.rkt").read_text(encoding="utf-8")
    assert len(set(programs)) == 4
    assert programs == [adapter.program(copy.deepcopy(setting)) for setting in SETTINGS]


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"quarter_turns": 4}, {"quarter_turns": -1},
     {"quarter_turns": True}, {"quarter_turns": 1.0},
     {"quarter_turns": "1"}, {"quarter_turns": 1, "extra": 0}],
)
def test_program_rejects_noncontract_settings(adapter, settings):
    with pytest.raises(ValueError, match="settings|quarter_turns"):
        adapter.program(settings)


@pytest.mark.parametrize("bad", [True, False, -1, 1.0, "1", None])
def test_generate_rejects_invalid_seed_scalars(adapter, bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        adapter.generate(bad, {"quarter_turns": 0}, 3, 4)


@pytest.mark.parametrize(
    "name,bad",
    [("demos", True), ("demos", 1), ("demos", 7),
     ("queries", False), ("queries", 0), ("queries", 5)],
)
def test_generate_rejects_invalid_counts(adapter, name, bad):
    request = {"seed": 0, "settings": {"quarter_turns": 0}, "demos": 3, "queries": 4}
    request[name] = bad
    with pytest.raises(ValueError, match=name):
        adapter.generate(**request)


def test_counts_are_independent_prefix_stable_and_deterministic(adapter):
    settings = {"quarter_turns": 1}
    minimum = adapter.generate(23, settings, 2, 1)
    maximum = adapter.generate(23, settings, 6, 4)
    replay = adapter.generate(23, settings, 6, 4)
    assert maximum == replay
    assert set(maximum) == {"train", "test", "program_solution"}
    assert minimum["train"] == maximum["train"][:2]
    assert minimum["test"] == maximum["test"][:1]
    assert len(maximum["train"]) == 6
    assert len(maximum["test"]) == 4
    assert maximum["program_solution"] == adapter.program(settings)
    fingerprints = {json.dumps(grid, separators=(",", ":")) for grid in _inputs(maximum)}
    assert len(fingerprints) == 10


def test_same_seed_uses_matched_inputs_across_all_settings(adapter):
    episodes = [adapter.generate(91, setting, 3, 4) for setting in SETTINGS]
    assert all(_inputs(episode) == _inputs(episodes[0]) for episode in episodes[1:])
    for left, right in zip(episodes, episodes[1:]):
        assert any(a["output"] != b["output"] for a, b in zip(left["train"], right["train"]))


@pytest.mark.parametrize("chosen", range(4))
def test_two_demonstrations_identify_the_chosen_turn(family, adapter, chosen):
    episode = adapter.generate(0, {"quarter_turns": chosen}, 2, 4)
    survivors = []
    for rival in range(4):
        if all(
            family.native_transform(pair["input"], rival) == pair["output"]
            for pair in episode["train"]
        ):
            survivors.append(rival)
    assert survivors == [chosen]


def test_fourth_query_is_substantive_exact_30x30_rotation_safe_stress(family, adapter):
    episode = adapter.generate(123, {"quarter_turns": 3}, 3, 4)
    stress = episode["test"][3]
    assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
    analysis = family.analyze_input(stress["input"])
    assert analysis["piece_count"] >= 2
    assert analysis["canvas_h"] >= 8 and analysis["canvas_w"] >= 8
    assert family.rotation_domain_errors(stress["input"]) == []
    assert sum(value == 2 for row in stress["output"] for value in row) >= 4


@pytest.mark.parametrize("turns", range(4))
def test_python_claim_labels_match_protected_racket(adapter, racket_bridge, turns):
    episode = adapter.generate(37, {"quarter_turns": turns}, 2, 1)
    source = adapter.program({"quarter_turns": turns})
    pair = episode["test"][0]
    assert _apply(racket_bridge, source, pair["input"]) == pair["output"]


def test_public_first_turn_masks_settings_program_and_all_query_answers(adapter):
    one = adapter.generate(17, {"quarter_turns": 0}, 3, 1)
    four = adapter.generate(17, {"quarter_turns": 0}, 3, 4)
    first_turn = {"train": four["train"], "test": [four["test"][0]]}
    assert public_challenge_bytes(one) == public_challenge_bytes(first_turn)
    visible = json.loads(public_challenge_bytes(four))
    assert all(set(pair) == {"input"} for pair in visible["test"])
    text = json.dumps(visible, sort_keys=True)
    assert "quarter_turns" not in text
    assert "program_solution" not in text


def test_dependency_witness_changes_rotated_intermediate_and_output(family):
    witness = family.dependency_witness()
    assert witness["settings"] == {"quarter_turns": 1}
    assert witness["ablation"] == "wrong_intermediate"
    assert witness["intermediate_value"] != witness["wrong_intermediate_value"]
    assert witness["output"] != witness["counterfactual_output"]
    assert witness["output"] == family.native_transform(witness["input"], 1)
    assert witness["counterfactual_output"] == family.native_transform(witness["input"], 0)

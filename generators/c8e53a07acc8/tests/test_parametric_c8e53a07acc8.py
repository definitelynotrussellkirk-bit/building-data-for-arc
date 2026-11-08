"""Contract, teaching, parity, and privacy tests for the c8e53 parametric family."""
from __future__ import annotations

from functools import cache
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "c8e53a07acc8"
ROOT = find_root(__file__)
BASE = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
PROTOTYPE = BASE / "prototype.py"
ADAPTER = BASE / "adapter.py"
PROMOTION = BASE / "promotion.json"


@cache
def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    programs = []
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            programs.append(row["program_solution"])
    assert len(set(programs)) == 1
    return programs[0]


def test_native_files_and_exact_default_program_exist():
    assert PROTOTYPE.is_file()
    assert ADAPTER.is_file()
    assert PROMOTION.is_file()
    proto = load(PROTOTYPE, "_c8_parametric_proto")
    assert proto.program({"anchor_size_relation": "same_count"}) == canonical_program()
    alternate = proto.program({"anchor_size_relation": "one_extra"})
    assert alternate != canonical_program()
    assert alternate.count("(+ cnt 1)") == 2
    contract = json.loads(PROMOTION.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"anchor_size_relation": ["same_count", "one_extra"]},
        "default": {"anchor_size_relation": "same_count"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 2,
        "resources": [f"generators/{TASK_ID}/workspace/parametric/prototype.py"],
    }


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_shared_inputs_teach_each_setting_and_keep_four_distinct_queries(demos):
    proto = load(PROTOTYPE, "_c8_parametric_proto")
    settings = list(proto.SETTINGS)
    episodes = [proto.generate(881, setting, demos, 4) for setting in settings]
    assert [[p["input"] for p in ep["train"] + ep["test"]] for ep in episodes][0] == [
        [p["input"] for p in ep["train"] + ep["test"]] for ep in episodes
    ][1]
    for setting, episode in zip(settings, episodes):
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        all_inputs = [p["input"] for p in episode["train"] + episode["test"]]
        assert len({proto.digest(grid) for grid in all_inputs}) == demos + 4
        assert episode["program_solution"] == proto.program(setting)
        assert all(pair["output"] == proto.transform(pair["input"], setting)
                   for pair in episode["train"] + episode["test"])
        survivors = [candidate for candidate in settings if all(
            proto.transform(pair["input"], candidate) == pair["output"]
            for pair in episode["train"]
        )]
        assert survivors == [setting]
        assert proto.certify(episode)["survivors"] == [setting]
    assert len(episodes[0]["test"][-1]["input"]) == 30
    assert len(episodes[0]["test"][-1]["input"][0]) == 30


def test_adapter_matches_prototype_and_public_projection_hides_future_state():
    proto = load(PROTOTYPE, "_c8_parametric_proto")
    adapter = load(ADAPTER, "_c8_parametric_adapter")
    setting = {"anchor_size_relation": "one_extra"}
    assert adapter.program(setting) == proto.program(setting)
    episode = adapter.generate(22, setting, 2, 4)
    direct = proto.generate(22, setting, 2, 4)
    assert episode == {"train": direct["train"], "test": direct["test"],
                       "program_solution": direct["program_solution"]}
    turn = proto.public_turn(direct, 0)
    assert set(turn) == {"train", "test"}
    assert len(turn["test"]) == 1 and set(turn["test"][0]) == {"input"}
    body = public_challenge_bytes(turn)
    assert public_challenge_id(turn) == proto.public_id(direct, 0)
    decoded = json.loads(body)
    assert "settings" not in decoded and "program" not in decoded
    assert set(decoded["test"][0]) == {"input"}


def test_protected_racket_matches_both_programs_on_generated_pairs():
    proto = load(PROTOTYPE, "_c8_parametric_proto")
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    def datum(grid):
        return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"

    with RacketBridge(max_calls_before_restart=128) as bridge:
        for setting in proto.SETTINGS:
            episode = proto.generate(501, setting, 2, 4)
            wrapped = wrap_rule(proto.program(setting))
            for pair in episode["train"] + episode["test"]:
                assert bridge.eval_text(f"({wrapped} {datum(pair['input'])})") == pair["output"]
            assert proto.certify(episode, lambda source, grid: bridge.eval_text(
                f"({wrap_rule(source)} {datum(grid)})"))["racket_checked"] is True


def test_rejects_malformed_settings_counts_and_grids():
    proto = load(PROTOTYPE, "_c8_parametric_proto")
    with pytest.raises(ValueError):
        proto.program({"anchor_size_relation": "typo"})
    with pytest.raises(ValueError):
        proto.generate(1, {"anchor_size_relation": "same_count"}, 1, 4)
    with pytest.raises(ValueError):
        proto.generate(1, {"anchor_size_relation": "same_count"}, 2, 3)
    with pytest.raises(ValueError):
        proto.transform([[True]], {"anchor_size_relation": "same_count"})

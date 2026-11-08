"""Behavior tests for the crop-then-dominant-key rotation family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_path, find_root

TASK_ID = "f2e717c7c250"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical row missing")


def test_adapter_default_is_byte_exact_and_settings_are_strict():
    adapter = _load("f2_parametric_adapter_test", HOME / "adapter.py")
    assert adapter.program({"postprocess": "crop_only"}) == _canonical_program()
    with pytest.raises(ValueError):
        adapter.program({})
    with pytest.raises(ValueError):
        adapter.program({"postprocess": "unknown"})
    with pytest.raises(ValueError):
        adapter.program({"postprocess": "crop_only", "extra": 1})


def test_episode_counts_prefix_stability_and_all_inputs_are_distinct():
    prototype = _load("f2_parametric_prefix_test", HOME / "prototype.py")
    full = prototype.generate_episode(17, postprocess="dominant_key_rotate", demos=6, queries=4)
    short = prototype.generate_episode(17, postprocess="dominant_key_rotate", demos=2, queries=1)
    assert short["train"] == full["train"][:2]
    assert short["test"] == full["test"][:1]
    assert short["program_solution"] == prototype.rule_text("dominant_key_rotate")
    encoded = [json.dumps(pair["input"]) for pair in full["train"] + full["test"]]
    assert len(encoded) == len(set(encoded))


@pytest.mark.parametrize("seed", [0, 17, 999])
def test_first_two_demos_teach_both_input_dependent_rotation_branches(seed):
    prototype = _load(f"f2_parametric_teach_{seed}", HOME / "prototype.py")
    episode = prototype.generate_episode(seed, postprocess="dominant_key_rotate", demos=2, queries=4)
    facts = [prototype.analyze(pair["input"]) for pair in episode["train"]]
    assert [fact["dominant_key_index"] for fact in facts] == [0, 1]
    for pair, fact in zip(episode["train"], facts):
        assert pair["output"] != fact["crop"]
        expected = prototype.rotate_cw(fact["crop"]) if fact["dominant_key_index"] == 0 else prototype.rotate_ccw(fact["crop"])
        assert pair["output"] == expected


def test_fourth_query_is_substantive_30x30_and_crop_spans_canvas_body():
    prototype = _load("f2_parametric_stress", HOME / "prototype.py")
    episode = prototype.generate_episode(17, postprocess="dominant_key_rotate", demos=3, queries=4)
    pair = episode["test"][3]
    grid = pair["input"]
    facts = prototype.analyze(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert facts["bbox"] == (0, 0, 27, 29)
    assert sum(value != 0 for row in grid for value in row) >= 120
    assert pair["output"] != facts["crop"]


def test_public_turn_hides_private_fields_and_matches_single_query_prefix():
    prototype = _load("f2_parametric_public", HOME / "prototype.py")
    full = prototype.generate_episode(23, postprocess="dominant_key_rotate", demos=3, queries=4)
    single = prototype.generate_episode(23, postprocess="dominant_key_rotate", demos=3, queries=1)
    first = prototype.public_turn(full, 0)
    assert first == prototype.public_turn(single, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1 and set(first["test"][0]) == {"input"}
    text = json.dumps(first, sort_keys=True)
    for forbidden in ("postprocess", "program", "seed", "answer"):
        assert forbidden not in text


def test_bounded_rival_audit_and_causal_case():
    audit = _load("f2_parametric_audit_test", HOME / "audit.py")
    prototype = _load("f2_parametric_causal_test", HOME / "prototype.py")
    report = audit.python_audit(seeds=(0, 17), demo_counts=range(2, 7))
    assert report["status"] == "passed"
    assert report["ambiguities"] == []
    assert report["episodes"] == 10
    assert report["stress_30x30"] == 10
    case = prototype.causal_case(0)
    assert case["settings"] == {"postprocess": "dominant_key_rotate"}
    assert case["output"] != case["counterfactual_output"]
    assert case["ablation"] == "wrong_intermediate"
    assert case["intermediate_value"]["dominant_key_index"] in (0, 1)


def test_racket_programs_match_python_on_constructive_cases():
    prototype = _load("f2_parametric_racket", HOME / "prototype.py")
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        for mode in prototype.POSTPROCESSES:
            episode = prototype.generate_episode(0, postprocess=mode, demos=2, queries=1)
            wrapped = wrap_rule(prototype.rule_text(mode))
            for pair in episode["train"] + episode["test"]:
                literal = "'(" + " ".join(
                    "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
                ) + ")"
                actual = bridge.eval_text(f"({wrapped} {literal})")
                assert actual == pair["output"]

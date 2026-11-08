"""Behavior tests for the selector-row rotational-equivalence family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_path, find_root

TASK_ID = "95be702ec4db"
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
    adapter = _load("rot_equiv_adapter_test", HOME / "adapter.py")
    assert adapter.program({"matrix_view": "full_matrix"}) == _canonical_program()
    with pytest.raises(ValueError):
        adapter.program({})
    with pytest.raises(ValueError):
        adapter.program({"matrix_view": "unknown"})
    with pytest.raises(ValueError):
        adapter.program({"matrix_view": "full_matrix", "extra": 1})


def test_episode_counts_prefix_stability_and_unique_inputs():
    prototype = _load("rot_equiv_prefix", HOME / "prototype.py")
    full = prototype.generate_episode(17, matrix_view="selector_row", demos=6, queries=4)
    short = prototype.generate_episode(17, matrix_view="selector_row", demos=2, queries=1)
    assert short["train"] == full["train"][:2]
    assert short["test"] == full["test"][:1]
    encoded = [json.dumps(pair["input"]) for pair in full["train"] + full["test"]]
    assert len(encoded) == len(set(encoded))


@pytest.mark.parametrize("seed", [0, 17, 999])
def test_first_two_demos_require_two_different_selector_rows(seed):
    prototype = _load(f"rot_equiv_teach_{seed}", HOME / "prototype.py")
    episode = prototype.generate_episode(seed, matrix_view="selector_row", demos=2, queries=4)
    facts = [prototype.analyze(pair["input"]) for pair in episode["train"]]
    assert [fact["selector_index"] for fact in facts] == [0, 2]
    assert facts[0]["matrix"][0] != facts[1]["matrix"][0]
    for pair, fact in zip(episode["train"], facts):
        assert pair["output"] == [fact["matrix"][fact["selector_index"]]]
        assert pair["output"] != fact["matrix"]


def test_fourth_query_is_substantive_30x30_diagonal_gallery():
    prototype = _load("rot_equiv_stress", HOME / "prototype.py")
    pair = prototype.generate_episode(17, matrix_view="selector_row", demos=3, queries=4)["test"][3]
    grid = pair["input"]
    facts = prototype.analyze(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert len(facts["frames"]) == 5
    boxes = [frame["bbox"] for frame in facts["frames"]]
    assert boxes[0][0] == 1 and boxes[-1][2] == 29
    assert boxes[0][1] == 0 and boxes[-1][3] == 28
    assert sum(value != 0 for row in grid for value in row) >= 80


def test_public_turn_hides_private_fields_and_matches_single_query_prefix():
    prototype = _load("rot_equiv_public", HOME / "prototype.py")
    full = prototype.generate_episode(23, matrix_view="selector_row", demos=3, queries=4)
    single = prototype.generate_episode(23, matrix_view="selector_row", demos=3, queries=1)
    first = prototype.public_turn(full, 0)
    assert first == prototype.public_turn(single, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1 and set(first["test"][0]) == {"input"}
    text = json.dumps(first, sort_keys=True)
    for forbidden in ("matrix_view", "program", "seed", "answer"):
        assert forbidden not in text


def test_bounded_rival_audit_and_causal_case():
    audit = _load("rot_equiv_audit_test", HOME / "audit.py")
    prototype = _load("rot_equiv_causal_test", HOME / "prototype.py")
    report = audit.python_audit(seeds=(0, 17), demo_counts=range(2, 7))
    assert report["status"] == "passed"
    assert report["ambiguities"] == []
    assert report["episodes"] == 10
    assert report["stress_30x30"] == 10
    case = prototype.causal_case(0)
    assert case["settings"] == {"matrix_view": "selector_row"}
    assert case["output"] != case["counterfactual_output"]
    assert case["ablation"] == "wrong_intermediate"


def test_all_declared_racket_programs_are_single_complete_forms():
    prototype = _load("rot_equiv_forms", HOME / "prototype.py")
    from arc_repl import parser

    for program in (
        prototype.CANONICAL_PROGRAM,
        prototype.SELECTOR_ROW_PROGRAM,
        prototype.counterfactual_program(),
    ):
        assert len(parser.parse_all(program)) == 1


def test_racket_programs_match_python_on_constructive_cases():
    prototype = _load("rot_equiv_racket", HOME / "prototype.py")
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        for mode in prototype.MATRIX_VIEWS:
            episode = prototype.generate_episode(0, matrix_view=mode, demos=2, queries=1)
            wrapped = wrap_rule(prototype.rule_text(mode))
            for pair in episode["train"] + episode["test"]:
                literal = "'(" + " ".join(
                    "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
                ) + ")"
                actual = bridge.eval_text(f"({wrapped} {literal})")
                assert actual == pair["output"]

"""Contract tests for the native rotation-sense parametric family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "17de34436a9f"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PROTOTYPE_PATH, "rotation_sense_parametric_prototype")


def _adapter():
    return _load(ADAPTER_PATH, "rotation_sense_parametric_adapter")


def _canonical_program() -> str:
    programs = []
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    assert len(programs) == 1
    return programs[0]


def _racket_apply(bridge: RacketBridge, program: str, grid: list[list[int]]):
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def test_program_contract_preserves_exact_canonical_default():
    prototype = _prototype()
    canonical = _canonical_program()

    assert prototype.TASK_ID == TASK_ID
    assert prototype.ROTATION_SENSES == ("clockwise", "counterclockwise")
    assert prototype.DEFAULT_ROTATION_SENSE == "clockwise"
    assert prototype.program_for("clockwise") == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "9f94f78b9fd26ca22f06035669600941ff89acb16f31d9e422bb6a645fec6ff3"
    )
    alternate = prototype.program_for("counterclockwise")
    assert alternate != canonical
    assert "((= code 2) (rotate-ccw grid))" in alternate
    assert "((= code 4) (rotate-cw grid))" in alternate

    for bad in (None, True, 0, "reverse", {"rotation_sense": "clockwise"}):
        with pytest.raises((TypeError, ValueError)):
            prototype.program_for(bad)


def test_counts_are_independent_prefix_stable_and_inputs_are_distinct():
    prototype = _prototype()
    two = prototype.generate_episode(
        91, rotation_sense="clockwise", demos=2, queries=4
    )
    one = prototype.generate_episode(
        91, rotation_sense="clockwise", demos=3, queries=1
    )
    four = prototype.generate_episode(
        91, rotation_sense="clockwise", demos=3, queries=4
    )
    six = prototype.generate_episode(
        91, rotation_sense="clockwise", demos=6, queries=4
    )

    assert two["train"] == four["train"][:2]
    assert two["test"] == four["test"]
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert six["train"][:3] == four["train"]
    assert six["test"] == four["test"]
    assert len(four["test"]) == 4

    inputs = [pair["input"] for pair in four["train"] + four["test"]]
    encoded = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    assert len(encoded) == len(set(encoded))

    stress = four["test"][3]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    analysis = prototype.analyze_input(stress)
    assert analysis["body_size"] >= 200
    assert analysis["touches_boundary"] is True
    assert analysis["marker_corner"] == "tr"


def test_two_demonstrations_cover_every_query_corner_and_identify_each_setting():
    prototype = _prototype()
    for setting in prototype.ROTATION_SENSES:
        episode = prototype.generate_episode(
            119, rotation_sense=setting, demos=2, queries=4
        )
        demo_corners = {
            prototype.analyze_input(pair["input"])["marker_corner"]
            for pair in episode["train"]
        }
        query_corners = {
            prototype.analyze_input(pair["input"])["marker_corner"]
            for pair in episode["test"]
        }
        certificate = prototype.teaching_certificate(episode, setting)

        assert query_corners <= demo_corners
        assert certificate["declared_setting_survivors"] == [setting]
        assert certificate["query_changing_survivors"] == []


def test_three_demonstrations_identify_each_setting_for_every_query():
    prototype = _prototype()
    for setting in prototype.ROTATION_SENSES:
        episode = prototype.generate_episode(
            137, rotation_sense=setting, demos=3, queries=4
        )
        certificate = prototype.teaching_certificate(episode, setting)
        assert certificate["query_changing_survivors"] == []
        assert certificate["declared_setting_survivors"] == [setting]
        assert certificate["queries_checked"] == 4
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == prototype.apply_python(pair["input"], setting)


def test_adapter_contract_and_public_projection_keep_private_data_hidden():
    prototype = _prototype()
    adapter = _adapter()
    promotion = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))

    assert promotion["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert promotion["parameters"] == {
        "rotation_sense": ["clockwise", "counterclockwise"]
    }
    assert promotion["default"] == {"rotation_sense": "clockwise"}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}

    settings = {"rotation_sense": "counterclockwise"}
    assert adapter.program(settings) == prototype.program_for("counterclockwise")
    episode = adapter.generate(17, settings, 3, 4)
    assert set(episode) >= {"train", "test", "program_solution"}
    assert episode["program_solution"] == adapter.program(settings)

    original_bytes = public_challenge_bytes(episode)
    original_id = public_challenge_id(episode)
    poisoned = copy.deepcopy(episode)
    poisoned["settings"] = {"rotation_sense": "clockwise"}
    poisoned["program_solution"] = "private program changed"
    for pair in poisoned["test"]:
        pair["output"] = [[9]]
    assert public_challenge_bytes(poisoned) == original_bytes
    assert public_challenge_id(poisoned) == original_id
    public = json.loads(original_bytes)
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "rotation_sense" not in original_bytes.decode()

    for bad in ({}, {"rotation_sense": "clockwise", "extra": 1}, {"rotation_sense": "reverse"}):
        with pytest.raises(ValueError):
            adapter.program(bad)


def test_real_racket_matches_python_for_both_settings_and_large_query():
    prototype = _prototype()
    with RacketBridge(timeout=20, max_calls_before_restart=32) as bridge:
        for setting in prototype.ROTATION_SENSES:
            episode = prototype.generate_episode(
                211, rotation_sense=setting, demos=3, queries=4
            )
            for pair in (episode["train"][1], episode["test"][3]):
                assert _racket_apply(
                    bridge, prototype.program_for(setting), pair["input"]
                ) == pair["output"]


def test_input_dependent_corner_code_is_causally_used_by_rotation():
    prototype = _prototype()
    grid = prototype.make_input(313, split="query", index=3)
    clockwise = prototype.intermediate_turns(grid, "clockwise")
    counterclockwise = prototype.intermediate_turns(grid, "counterclockwise")
    assert clockwise == 1
    assert counterclockwise == 3
    assert prototype.apply_python(grid, "clockwise") != prototype.apply_python(
        grid, "counterclockwise"
    )

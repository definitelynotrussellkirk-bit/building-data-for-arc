"""Native parametric contract tests for canonical versus orientation-controlled order."""
from __future__ import annotations

import importlib.util
import json

import pytest
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

ROOT = find_root(__file__)
SOURCE = ROOT / "generators/0ff4b77946cc/workspace/parametric/prototype.py"


def _load():
    spec = importlib.util.spec_from_file_location("parametric_0ff4b77946cc", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == "0ff4b77946cc"}
    assert len(programs) == 1
    return next(iter(programs))


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def test_default_program_is_exact_canonical_and_settings_are_strict():
    p = _load()
    assert p.SETTINGS == ("size_desc", "largest_orientation")
    assert p.program({"order_policy": "size_desc"}) == _canonical()
    assert p.program({"order_policy": "largest_orientation"}) != _canonical()
    for bad in ({}, {"order_policy": "x"}, {"order_policy": True}, {"order_policy": "size_desc", "x": 1}):
        with pytest.raises((TypeError, ValueError)):
            p.program(bad)


def test_two_demos_teach_wide_and_tall_anchor_cases_and_four_queries():
    p = _load()
    generator, _path, _sha = load_selected_generator("0ff4b77946cc", root=ROOT)
    for setting in p.SETTINGS:
        episode = p.generate(17, {"order_policy": setting}, demos=2, queries=4)
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert {p.analyze(pair["input"])["largest_orientation"] for pair in episode["train"]} == {"wide_or_square", "tall"}
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 6
        assert any(
            len(pair["input"]) == 30 and len(pair["input"][0]) == 30
            for pair in episode["test"]
        )
        for pair in episode["train"] + episode["test"]:
            assert generator.self_check(pair["input"]) == []
            assert pair["output"] == p.apply_python(pair["input"], setting)
        rival = next(value for value in p.SETTINGS if value != setting)
        assert any(p.apply_python(pair["input"], rival) != pair["output"] for pair in episode["train"])


def test_orientation_intermediate_controls_second_stage_order():
    p = _load()
    episode = p.generate(0, {"order_policy": "largest_orientation"}, demos=2, queries=4)
    tall = next(pair["input"] for pair in episode["train"] if p.analyze(pair["input"])["largest_orientation"] == "tall")
    analysis = p.analyze(tall)
    assert analysis["selected_direction"] == "ascending"
    assert p.apply_python(tall, "largest_orientation") != p.apply_python(tall, "size_desc")


def test_exact_racket_programs_match_python_claims_on_one_full_episode_each():
    p = _load()
    with RacketBridge(timeout=30, max_calls_before_restart=32) as bridge:
        for setting in p.SETTINGS:
            episode = p.generate(0, {"order_policy": setting}, demos=2, queries=4)
            callable_source = wrap_rule(episode["program_solution"])
            for pair in episode["train"] + episode["test"]:
                actual = bridge.eval_text(f"({callable_source} {_literal(pair['input'])})")
                assert actual == pair["output"]


def test_count_validation_is_bounded():
    p = _load()
    for demos, queries in ((1, 4), (7, 4), (2, 0), (2, 5), (True, 4)):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, {"order_policy": "size_desc"}, demos=demos, queries=queries)

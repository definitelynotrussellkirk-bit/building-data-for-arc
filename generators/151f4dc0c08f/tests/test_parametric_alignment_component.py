"""Native parametric contract tests for pair alignment versus anchor component."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

ROOT = find_root(__file__)
SOURCE = ROOT / "generators/151f4dc0c08f/workspace/parametric/prototype.py"


def _load():
    spec = importlib.util.spec_from_file_location("parametric_151f4dc0c08f", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == "151f4dc0c08f"}
    assert len(programs) == 1
    return next(iter(programs))


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def test_default_program_is_exact_canonical_and_settings_are_strict():
    p = _load()
    assert p.SETTINGS == ("pair_alignment", "anchor_component")
    assert p.program({"matrix_rule": "pair_alignment"}) == _canonical()
    assert p.program({"matrix_rule": "anchor_component"}) != _canonical()
    for bad in ({}, {"matrix_rule": "x"}, {"matrix_rule": True}, {"matrix_rule": "pair_alignment", "x": 1}):
        with pytest.raises((TypeError, ValueError)):
            p.program(bad)


def test_complete_episodes_support_independent_counts_and_four_queries():
    p = _load()
    generator, _path, _sha = load_selected_generator("151f4dc0c08f", root=ROOT)
    for setting in p.SETTINGS:
        episode = p.generate(17, {"matrix_rule": setting}, demos=2, queries=4)
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == p.program({"matrix_rule": setting})
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 6
        assert any(len(grid) == 30 and len(grid[0]) == 30 for grid in inputs[2:])
        for pair in episode["train"] + episode["test"]:
            assert generator.self_check(pair["input"]) == []
            assert pair["output"] == p.apply_python(pair["input"], setting)
        rival = next(value for value in p.SETTINGS if value != setting)
        assert any(p.apply_python(pair["input"], rival) != pair["output"] for pair in episode["train"])


def test_anchor_component_requires_transitive_intermediate():
    p = _load()
    episode = p.generate(0, {"matrix_rule": "anchor_component"}, demos=2, queries=4)
    witness = episode["train"][0]["input"]
    analysis = p.analyze(witness)
    assert analysis["anchor_component"] != analysis["anchor_direct_neighborhood"]
    assert p.apply_python(witness, "anchor_component") != p.apply_wrong_direct_neighbors(witness)


def test_every_authored_scene_keeps_a_transitive_extension_and_an_isolated_marker():
    p = _load()
    for seed in range(16):
        for setting in p.SETTINGS:
            episode = p.generate(seed, {"matrix_rule": setting}, demos=6, queries=4)
            for pair in episode["train"] + episode["test"]:
                analysis = p.analyze(pair["input"])
                assert analysis["anchor_component"] != analysis["anchor_direct_neighborhood"]
                assert len(analysis["anchor_component"]) < len(analysis["positions"])


def test_exact_racket_programs_match_python_claims_on_one_full_episode_each():
    p = _load()
    with RacketBridge(timeout=30, max_calls_before_restart=32) as bridge:
        for setting in p.SETTINGS:
            episode = p.generate(0, {"matrix_rule": setting}, demos=2, queries=4)
            callable_source = wrap_rule(episode["program_solution"])
            for pair in episode["train"] + episode["test"]:
                actual = bridge.eval_text(f"({callable_source} {_literal(pair['input'])})")
                assert actual == pair["output"]


def test_count_validation_is_bounded():
    p = _load()
    for demos, queries in ((1, 4), (7, 4), (2, 0), (2, 5), (True, 4)):
        with pytest.raises((TypeError, ValueError)):
            p.generate(0, {"matrix_rule": "pair_alignment"}, demos=demos, queries=queries)

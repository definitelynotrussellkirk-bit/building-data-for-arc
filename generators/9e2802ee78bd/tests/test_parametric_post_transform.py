"""Regression and parametric tests for the marker-panel family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
PARAM = HOME / "workspace" / "parametric"
GENERATOR = HOME / "generator.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical() -> str:
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "9e2802ee78bd":
            return row["program_solution"]
    raise AssertionError("canonical source missing")


def _apply(bridge: RacketBridge, program: str, grid: list[list[int]]):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def test_base_generator_rejects_unknowns_and_honors_exact_size_controls():
    generator = _load(GENERATOR, "p9e_generator_contract")
    grid = generator.generate(
        11, 4, difficulty="medium", grid_h=30, grid_w=30,
        panel_h=29, panel_w=2, marker=2, palette_size=5, texture="varied",
        position_bias="left_panel",
    )
    assert (len(grid), len(grid[0])) == (30, 30)
    observed = generator.observe_overrides(grid)
    assert observed == {
        "grid_h": 30, "grid_w": 30, "panel_h": 29, "panel_w": 2,
        "marker": 2, "palette_size": 5, "position_bias": "left_panel",
        "texture": "varied",
    }
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, panel_height_typo=8)
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, marker=True)
    with pytest.raises(ValueError, match="inconsistent"):
        generator.generate(0, 0, grid_h=10, panel_h=3)


def test_base_self_check_rejects_declared_degenerates_and_mutations():
    generator = _load(GENERATOR, "p9e_generator_selfcheck")
    for name in generator.DEGENERATE_TEXTURES:
        grid = generator.generate(3, 1, texture=name)
        assert generator.self_check(grid), name
    assert generator.self_check([[0] * 9 for _ in range(4)])
    valid = generator.generate(7, 2, difficulty=None)
    assert generator.self_check(valid) == []
    damaged = copy.deepcopy(valid)
    sep = generator.observe_overrides(valid)["panel_w"] + 1
    damaged[-1][sep] = 0
    assert generator.self_check(damaged)


def test_default_program_exact_inputs_matched_and_counts_independent():
    adapter = _load(PARAM / "adapter.py", "p9e_adapter_counts")
    assert adapter.program({"post_transform": "none"}) == _canonical()
    assert (PARAM / "canonical.rkt").read_bytes() == _canonical().encode()
    for demos, queries in ((2, 1), (3, 4), (6, 2)):
        episodes = {
            mode: adapter.generate(17, {"post_transform": mode}, demos, queries)
            for mode in ("none", "flip_ud")
        }
        assert [p["input"] for p in episodes["none"]["train"]] == [
            p["input"] for p in episodes["flip_ud"]["train"]
        ]
        assert [p["input"] for p in episodes["none"]["test"]] == [
            p["input"] for p in episodes["flip_ud"]["test"]
        ]
        for episode in episodes.values():
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == queries
            assert adapter.public_turn(episode, 0) == {
                "train": episode["train"],
                "test": [{"input": episode["test"][0]["input"]}],
            }


def test_racket_labels_distinguish_post_transform_and_cover_30x30():
    adapter = _load(PARAM / "adapter.py", "p9e_adapter_racket")
    episodes = {
        mode: adapter.generate(0, {"post_transform": mode}, 2, 4)
        for mode in ("none", "flip_ud")
    }
    assert any(len(pair["input"]) == 30 and len(pair["input"][0]) == 30
               for pair in episodes["none"]["test"])
    programs = {mode: adapter.program({"post_transform": mode}) for mode in episodes}
    with RacketBridge() as bridge:
        assert bridge.runtime_identity["protected"] is True
        for mode, episode in episodes.items():
            for pair in (*episode["train"], *episode["test"]):
                assert _apply(bridge, programs[mode], pair["input"]) == pair["output"]
            rival = "flip_ud" if mode == "none" else "none"
            assert any(
                _apply(bridge, programs[rival], pair["input"]) != pair["output"]
                for pair in episode["train"]
            )


def test_transformed_panel_is_input_dependent_and_wrong_intermediate_changes_paste():
    prototype = _load(PARAM / "prototype.py", "p9e_prototype_dependency")
    first = prototype.scene(0, 0)
    second = prototype.scene(0, 1)
    a = prototype.transform_intermediate(first)
    b = prototype.transform_intermediate(second)
    assert a != b
    correct = prototype.transform(first, "flip_ud")
    wrong = prototype.transform(first, "flip_ud", wrong_intermediate="identity_source")
    assert correct != wrong

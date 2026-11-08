from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[5]


def load(name: str):
    path = HERE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_297_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == "297c05190f7c"
    }
    assert len(programs) == 1
    return programs.pop()


MERGE_INPUT = [
    [0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 0, 0],
    [0, 2, 2, 2, 0, 2, 2, 0, 7, 0, 0, 0],
    [0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0],
    [0, 2, 2, 0, 2, 2, 2, 0, 0, 0, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 0, 0],
]
FILLED = [
    [0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 0, 0],
    [0, 2, 2, 2, 2, 2, 2, 0, 7, 7, 0, 0],
    [0, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0],
    [0, 2, 2, 2, 2, 2, 2, 0, 4, 4, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 0],
]
RETAINED = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0],
    [0, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0],
    [0, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]


def test_literal_postfill_merge_and_retention() -> None:
    family = load("family")
    assert family.evaluate(MERGE_INPUT, "all") == FILLED
    assert family.evaluate(MERGE_INPUT, "largest_postfill_component") == RETAINED
    assert family.evaluate_candidate(MERGE_INPUT, "largest_original_component") != RETAINED
    assert family.evaluate_candidate(MERGE_INPUT, "largest_original_bbox") != RETAINED


def test_default_program_is_exact_canonical_authority() -> None:
    family = load("family")
    assert family.program_for("all") == canonical_program()
    assert family.program_for("largest_postfill_component") != canonical_program()


@pytest.mark.parametrize("retention", ["all", "largest_postfill_component"])
def test_episode_counts_prefixes_identification_and_stress(retention: str) -> None:
    family = load("family")
    full = family.generate_episode(83, retention, demos=6, queries=4)
    assert len(full["train"]) == 6
    assert len(full["test"]) == 4
    inputs = [pair["input"] for pair in full["train"] + full["test"]]
    assert len({json.dumps(grid) for grid in inputs}) == 10
    assert any(len(grid) == 30 and len(grid[0]) == 30 for grid in inputs)
    assert family.teaching_survivors(full["train"]) == [retention]
    for demos in range(2, 7):
        episode = family.generate_episode(83, retention, demos=demos, queries=1)
        assert episode["train"] == full["train"][:demos]
        assert episode["test"] == full["test"][:1]
        assert family.teaching_survivors(episode["train"]) == [retention]
    assert all(
        family.evaluate(pair["input"], "all")
        != family.evaluate(pair["input"], "largest_postfill_component")
        for pair in full["train"] + full["test"]
    )


def test_adapter_contract_and_rejections() -> None:
    adapter = load("adapter")
    episode = adapter.generate(5, {"retention": "all"}, 2, 1)
    assert episode["program_solution"] == canonical_program()
    assert len(episode["train"]) == 2 and len(episode["test"]) == 1
    for bad in ({}, {"retention": True}, {"retention": "largest"},
                {"retention": "all", "extra": 1}):
        with pytest.raises(ValueError):
            adapter.program(bad)
    for args in ((-1, {"retention": "all"}, 2, 1),
                 (0, {"retention": "all"}, 1, 1),
                 (0, {"retention": "all"}, 2, 5)):
        with pytest.raises(ValueError):
            adapter.generate(*args)

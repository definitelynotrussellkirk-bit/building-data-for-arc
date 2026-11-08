from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[5]


def load(name: str):
    path = HERE / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_26_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == "26cfe7595a4a"
    }
    assert len(programs) == 1
    return programs.pop()


CROP = [
    [3, 2, 2, 0, 3],
    [2, 3, 3, 3, 3],
    [2, 3, 3, 3, 3],
    [2, 2, 0, 3, 2],
]
PADDED = [[0] * 7] + [[0] + row + [0] for row in CROP] + [[0] * 7]
HIGHLIGHTED = [[8 if v == 2 else v for v in row] for row in CROP]


def test_literal_crop_created_perimeter_selection() -> None:
    family = load("family")
    assert family.evaluate(PADDED, "crop_only") == CROP
    assert family.perimeter_mode(CROP) == 2
    assert family.global_mode(CROP) == 3
    assert family.evaluate(PADDED, "highlight_perimeter_mode") == HIGHLIGHTED
    assert family.evaluate_candidate(PADDED, "highlight_global_mode") != HIGHLIGHTED
    assert family.evaluate_candidate(PADDED, "highlight_first_nonzero") != HIGHLIGHTED


def test_default_program_is_exact_canonical_authority() -> None:
    family = load("family")
    assert family.program_for("crop_only") == canonical_program()
    assert family.program_for("highlight_perimeter_mode") != canonical_program()


@pytest.mark.parametrize("border_rule", ["crop_only", "highlight_perimeter_mode"])
def test_episode_counts_prefixes_identification_and_stress(border_rule: str) -> None:
    family = load("family")
    full = family.generate_episode(91, border_rule, demos=6, queries=4)
    assert len(full["train"]) == 6 and len(full["test"]) == 4
    inputs = [pair["input"] for pair in full["train"] + full["test"]]
    assert len({json.dumps(grid) for grid in inputs}) == 10
    assert any(len(grid) == 30 and len(grid[0]) == 30 for grid in inputs)
    assert family.teaching_survivors(full["train"]) == [border_rule]
    for demos in range(2, 7):
        episode = family.generate_episode(91, border_rule, demos=demos, queries=1)
        assert episode["train"] == full["train"][:demos]
        assert episode["test"] == full["test"][:1]
        assert family.teaching_survivors(episode["train"]) == [border_rule]
    assert all(
        family.evaluate(pair["input"], "crop_only")
        != family.evaluate(pair["input"], "highlight_perimeter_mode")
        for pair in full["train"] + full["test"]
    )


def test_all_seeded_transforms_keep_the_crop_inside_its_canvas() -> None:
    family = load("family")
    for seed in (0, 3, 17, 91):
        for border_rule in ("crop_only", "highlight_perimeter_mode"):
            episode = family.generate_episode(seed, border_rule, demos=2, queries=4)
            assert len(episode["test"]) == 4


def test_adapter_contract_and_rejections() -> None:
    adapter = load("adapter")
    episode = adapter.generate(7, {"border_rule": "crop_only"}, 2, 1)
    assert episode["program_solution"] == canonical_program()
    for bad in ({}, {"border_rule": True}, {"border_rule": "global"},
                {"border_rule": "crop_only", "extra": 1}):
        with pytest.raises(ValueError):
            adapter.program(bad)
    for args in ((-1, {"border_rule": "crop_only"}, 2, 1),
                 (0, {"border_rule": "crop_only"}, 1, 1),
                 (0, {"border_rule": "crop_only"}, 2, 5)):
        with pytest.raises(ValueError):
            adapter.generate(*args)

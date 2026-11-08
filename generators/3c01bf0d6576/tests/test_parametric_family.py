from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "workspace/parametric/native_family.py"
ROOT = HOME.parents[1]


def family():
    assert SOURCE.is_file(), "native parametric family is not implemented"
    spec = importlib.util.spec_from_file_location("transform_example_native_test", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "3c01bf0d6576":
            return row["program_solution"]
    raise AssertionError("canonical task missing")


def literal_flip_scene() -> list[list[int]]:
    grid = [[0] * 15 for _ in range(11)]
    a = [[1, 0, 0], [1, 4, 4], [0, 4, 0]]
    ap = [row[::-1] for row in a]
    b = [[2, 0, 3], [2, 2, 0], [0, 2, 2]]
    for r, row in enumerate(a):
        for c, value in enumerate(row):
            grid[1 + r][1 + c] = value
    for r, row in enumerate(ap):
        for c, value in enumerate(row):
            grid[1 + r][10 + c] = value
    for r, row in enumerate(b):
        for c, value in enumerate(row):
            grid[7 + r][5 + c] = value
    return grid


def test_wrong_order_racket_program_is_standalone_and_distinct() -> None:
    mod = family()
    counterfactual = mod.wrong_order_program()
    assert counterfactual.startswith("(rule!")
    assert counterfactual != mod.program({"finish": "mark_first_after_transform"})
    assert "marked" in counterfactual
    assert "apply-transform marked" in counterfactual


def test_exact_default_and_post_transform_component_selection() -> None:
    mod = family()
    assert mod.program({"finish": "transform_only"}) == canonical_program()
    assert mod.program() == canonical_program()

    grid = literal_flip_scene()
    transformed = [[3, 0, 2], [0, 2, 2], [2, 2, 0]]
    marked = [[9, 0, 2], [0, 2, 2], [2, 2, 0]]
    assert mod.transform(grid, {"finish": "transform_only"}) == transformed
    assert mod.transform(grid, {"finish": "mark_first_after_transform"}) == marked
    assert mod.wrong_order_transform(grid) != marked


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_episode_contract_prefixes_matched_inputs_and_setting_identification(seed: int) -> None:
    mod = family()
    full_by_setting = [mod.generate(seed, setting, demos=6, queries=4) for setting in mod.SETTINGS]
    shared = [pair["input"] for pair in full_by_setting[0]["train"] + full_by_setting[0]["test"]]
    assert len({json.dumps(grid) for grid in shared}) == 10
    for setting, full in zip(mod.SETTINGS, full_by_setting):
        assert full == mod.generate(seed, setting, demos=6, queries=4)
        assert full["settings"] == setting
        assert full["program_solution"] == mod.program(setting)
        assert [pair["input"] for pair in full["train"] + full["test"]] == shared
        for demos, queries in ((4, 1), (5, 3), (6, 4)):
            smaller = mod.generate(seed, setting, demos=demos, queries=queries)
            assert smaller["train"] == full["train"][:demos]
            assert smaller["test"] == full["test"][:queries]
    for index in range(4):
        assert full_by_setting[0]["train"][index]["output"] != full_by_setting[1]["train"][index]["output"]


def test_bank_has_layout_diversity_all_transforms_and_substantive_30_square() -> None:
    mod = family()
    episode = mod.generate(29, {"finish": "transform_only"}, demos=6, queries=4)
    pairs = episode["train"] + episode["test"]
    transforms = {mod.analyze(pair["input"])["transform"] for pair in pairs}
    assert transforms == {1, 2, 3, 4, 5}
    assert any(mod.layout_signature(pair["input"]) == "vertical_or_staggered" for pair in pairs)
    large = [pair for pair in pairs if len(pair["input"]) == len(pair["input"][0]) == 30]
    assert len(large) == 1
    grid = large[0]["input"]
    assert sum(value != 0 for row in grid for value in row) >= 70
    assert all(any(grid[r][c] for r in range(r0, r0 + 15) for c in range(c0, c0 + 15))
               for r0 in (0, 15) for c0 in (0, 15))
    assert any(grid[0]) and any(grid[-1]) and any(row[0] for row in grid) and any(row[-1] for row in grid)


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": -1}, {"seed": 2**63},
    {"demos": 3}, {"demos": 7}, {"demos": 4.0},
    {"queries": 0}, {"queries": 5}, {"queries": True},
    {"settings": {}}, {"settings": {"finish": "other"}},
    {"settings": {"finish": "transform_only", "extra": 1}},
])
def test_strict_request_controls(kwargs) -> None:
    request = {"seed": 0, "settings": {"finish": "transform_only"}, "demos": 4, "queries": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        family().generate(**request)

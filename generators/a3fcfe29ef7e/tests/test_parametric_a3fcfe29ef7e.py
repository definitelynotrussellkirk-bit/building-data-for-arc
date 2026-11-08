from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


HERE = Path(__file__).resolve()
TASK_ID = "a3fcfe29ef7e"
ROOT = find_root(HERE)
PARAMETRIC = HERE.parents[1] / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    assert path.is_file(), f"missing native parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical task missing")


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_and_global_variant_is_distinct():
    adapter = _load("parametric_adapter_a3fcfe29ef7e", "adapter.py")

    canonical = adapter.program({"row_policy": "all"})
    densest = adapter.program({"row_policy": "densest"})

    assert canonical == _canonical_program()
    assert densest != canonical
    assert densest.startswith("(rule!")


@pytest.mark.parametrize(
    "bad",
    [
        None,
        {},
        {"row_policy": "all", "extra": 1},
        {"row_policy": "unknown"},
        {"row_policy": 1},
    ],
)
def test_settings_reject_malformed_or_undeclared_values(bad):
    adapter = _load("parametric_adapter_validation_a3fcfe29ef7e", "adapter.py")

    with pytest.raises(ValueError):
        adapter.program(bad)


def test_densest_rule_uses_the_nor_mask_then_global_row_counts():
    prototype = _load("parametric_prototype_fixture_a3fcfe29ef7e", "prototype.py")
    grid = [
        [0, 0, 1, 8, 0, 0, 2],
        [0, 0, 0, 8, 0, 0, 0],
        [0, 1, 1, 8, 0, 2, 0],
        [1, 0, 1, 8, 0, 2, 2],
    ]

    analysis = prototype.analyze(grid)

    assert analysis == {
        "mask": [
            [3, 3, 0],
            [3, 3, 3],
            [3, 0, 0],
            [0, 0, 0],
        ],
        "row_counts": [2, 3, 1, 0],
        "max_count": 3,
    }
    assert prototype.transform(grid, row_policy="all") == analysis["mask"]
    assert prototype.transform(grid, row_policy="densest") == [
        [0, 0, 0],
        [3, 3, 3],
        [0, 0, 0],
        [0, 0, 0],
    ]


def test_episode_is_paired_setting_blind_distinct_and_includes_30_row_stress():
    adapter = _load("parametric_adapter_episode_a3fcfe29ef7e", "adapter.py")

    all_rows = adapter.generate(2718, {"row_policy": "all"}, 3, 4)
    densest = adapter.generate(2718, {"row_policy": "densest"}, 3, 4)

    assert len(all_rows["train"]) == len(densest["train"]) == 3
    assert len(all_rows["test"]) == len(densest["test"]) == 4
    assert _inputs(all_rows) == _inputs(densest)
    assert len({json.dumps(grid) for grid in _inputs(all_rows)}) == 7
    assert len(all_rows["test"][-1]["input"]) == 30
    assert all(len(row) == 7 for row in all_rows["test"][-1]["input"])
    assert set(all_rows) == set(densest) == {"train", "test", "program_solution"}

    for all_pair, dense_pair in zip(
        all_rows["train"] + all_rows["test"],
        densest["train"] + densest["test"],
    ):
        assert all_pair["input"] == dense_pair["input"]
        assert all_pair["output"] != dense_pair["output"]


def test_each_demo_alone_separates_the_two_declared_programs():
    prototype = _load("parametric_prototype_identification_a3fcfe29ef7e", "prototype.py")
    adapter = _load("parametric_adapter_identification_a3fcfe29ef7e", "adapter.py")

    for chosen in ("all", "densest"):
        episode = adapter.generate(17, {"row_policy": chosen}, 6, 4)
        for pair in episode["train"]:
            outputs = {
                policy: prototype.transform(pair["input"], row_policy=policy)
                for policy in ("all", "densest")
            }
            assert outputs[chosen] == pair["output"]
            assert outputs["all"] != outputs["densest"]


@pytest.mark.parametrize(
    ("seed", "demos", "queries"),
    [
        (-1, 3, 4),
        (True, 3, 4),
        (0, 1, 4),
        (0, 7, 4),
        (0, 3, 0),
        (0, 3, 5),
    ],
)
def test_episode_bounds_fail_loudly(seed, demos, queries):
    adapter = _load("parametric_adapter_bounds_a3fcfe29ef7e", "adapter.py")

    with pytest.raises(ValueError):
        adapter.generate(seed, {"row_policy": "all"}, demos, queries)


def test_minimum_lesson_refutes_local_count_threshold_and_single_winner_shortcuts():
    prototype = _load("parametric_prototype_shortcuts_a3fcfe29ef7e", "prototype.py")
    adapter = _load("parametric_adapter_shortcuts_a3fcfe29ef7e", "adapter.py")
    episode = adapter.generate(0, {"row_policy": "densest"}, 3, 4)
    demos = episode["train"]
    analyses = [prototype.analyze(pair["input"]) for pair in demos]

    assert {item["max_count"] for item in analyses} == {2, 3}
    assert any(
        sum(count == item["max_count"] for count in item["row_counts"]) > 1
        for item in analyses
    )

    def exact_three(item):
        return [
            [value if item["row_counts"][r] == 3 else 0 for value in row]
            for r, row in enumerate(item["mask"])
        ]

    def threshold_two(item):
        return [
            [value if item["row_counts"][r] >= 2 else 0 for value in row]
            for r, row in enumerate(item["mask"])
        ]

    def first_max_only(item):
        row = item["row_counts"].index(item["max_count"])
        return [mask_row if r == row else [0, 0, 0] for r, mask_row in enumerate(item["mask"])]

    rivals = (exact_three, threshold_two, first_max_only)
    for rival in rivals:
        assert any(
            rival(item) != pair["output"]
            for item, pair in zip(analyses, demos)
        )

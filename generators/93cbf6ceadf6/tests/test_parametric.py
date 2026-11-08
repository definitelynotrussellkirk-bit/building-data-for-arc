"""Focused contract tests for the native 93cbf6ceadf6 parametric family."""
from __future__ import annotations

from collections import Counter
import importlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "93cbf6ceadf6"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
SETTINGS = [
    {"output_transform": value}
    for value in ("identity", "rotate_cw", "flip_lr")
]
BASE = importlib.import_module("puzzle_generators.per_puzzle.93cbf6ceadf6.generator")


def _load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing parametric source: {path}"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row["program_solution"])
    assert len(set(rows)) == 1
    return rows[0]


def _key(grid):
    return tuple(tuple(row) for row in grid)


def _rotate_cw_grid(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr_grid(grid):
    return [list(reversed(row)) for row in grid]


def test_sources_contract_and_exact_transform_programs() -> None:
    prototype = _load("prototype")
    adapter = _load("adapter")
    contract = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    canonical = _canonical_source()

    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["adapter"] == f"generators/{TASK_ID}/workspace/parametric/adapter.py"
    assert contract["parameters"] == {
        "output_transform": ["identity", "rotate_cw", "flip_lr"]
    }
    assert contract["default"] == {"output_transform": "identity"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}

    assert adapter.program(contract["default"]) == canonical
    assert prototype.program_for("identity") == canonical
    assert prototype.program_for("rotate_cw") == canonical.replace(
        prototype._PAINT_EXPRESSION,
        f"(rotate-cw {prototype._PAINT_EXPRESSION})",
    )
    assert prototype.program_for("flip_lr") == canonical.replace(
        prototype._PAINT_EXPRESSION,
        f"(flip-lr {prototype._PAINT_EXPRESSION})",
    )
    assert len({adapter.program(setting) for setting in SETTINGS}) == 3


def test_inputs_are_setting_independent_distinct_and_boundary_bearing() -> None:
    adapter = _load("adapter")
    episodes = [adapter.generate(31, setting, 2, 4) for setting in SETTINGS]
    visible_inputs = [
        [_key(pair["input"]) for pair in episode["train"] + episode["test"]]
        for episode in episodes
    ]
    assert all(inputs == visible_inputs[0] for inputs in visible_inputs[1:])
    assert len(set(visible_inputs[0])) == 6

    boundary = episodes[0]["test"][-1]["input"]
    assert len(boundary) == len(boundary[0]) == 30
    assert sum(cell != 0 for row in boundary for cell in row) >= 60
    assert any(boundary[0])
    assert any(boundary[-1])
    assert any(row[0] for row in boundary)
    assert any(row[-1] for row in boundary)


def test_two_demonstrations_identify_setting_and_each_scene_is_asymmetric() -> None:
    adapter = _load("adapter")
    episodes = {
        setting["output_transform"]: adapter.generate(83, setting, 2, 4)
        for setting in SETTINGS
    }
    demo_signatures = {
        name: tuple(_key(pair["output"]) for pair in episode["train"])
        for name, episode in episodes.items()
    }
    assert len(set(demo_signatures.values())) == 3

    for index in range(6):
        outputs = {
            _key((episode["train"] + episode["test"])[index]["output"])
            for episode in episodes.values()
        }
        assert len(outputs) == 3
    for episode in episodes.values():
        assert len({_key(pair["output"]) for pair in episode["train"] + episode["test"]}) >= 4


def test_exact_requested_counts_and_validation() -> None:
    adapter = _load("adapter")
    for demos in (2, 6):
        episode = adapter.generate(107 + demos, SETTINGS[0], demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program(SETTINGS[0])
    for bad in (1, 7, True, 2.0):
        with pytest.raises(ValueError):
            adapter.generate(1, SETTINGS[0], bad, 4)
    for bad in (3, 5, True, 4.0):
        with pytest.raises(ValueError):
            adapter.generate(1, SETTINGS[0], 2, bad)
    with pytest.raises(ValueError):
        adapter.program({"output_transform": "identity", "extra": 1})
    with pytest.raises(ValueError):
        adapter.program({"output_transform": "transpose"})
    with pytest.raises(ValueError):
        adapter.generate(True, SETTINGS[0], 2, 4)


def test_scene_controls_refute_position_color_area_and_bbox_shortcuts() -> None:
    prototype = _load("prototype")
    odd_reading_positions = set()
    odd_colors = set()
    odd_shapes = set()
    color_multiplicities = set()
    non_unique_odd_color = False

    for seed in (0, 17, 83, 211):
        for grid in prototype.sample_inputs(seed, 10):
            assert BASE.self_check(grid) == []
            items = BASE._component_items(grid)
            frequencies = Counter(item["shape"] for item in items)
            assert sorted(frequencies.values()) == [1, 2]
            odd_index = next(
                index for index, item in enumerate(items)
                if frequencies[item["shape"]] == 1
            )
            odd = items[odd_index]
            repeated = next(item for item in items if frequencies[item["shape"]] == 2)
            assert len(odd["shape"]) == len(repeated["shape"])
            assert (odd["height"], odd["width"]) == (
                repeated["height"], repeated["width"]
            )
            colors = Counter(item["color"] for item in items)
            if colors[odd["color"]] != 1:
                non_unique_odd_color = True
            odd_reading_positions.add(odd_index)
            odd_colors.add(odd["color"])
            odd_shapes.add(odd["shape"])
            color_multiplicities.add(tuple(sorted(colors.values())))

    assert odd_reading_positions == {0, 1, 2}
    assert len(odd_colors) >= 7
    assert len(odd_shapes) >= 8
    assert color_multiplicities >= {(3,), (1, 2), (1, 1, 1)}
    assert non_unique_odd_color


def test_python_transform_stage_uses_selected_odd_intermediate() -> None:
    prototype = _load("prototype")
    for grid in prototype.sample_inputs(307, 10):
        intermediate = BASE._odd_output(grid)
        identity = prototype.python_output(grid, output_transform="identity")
        rotated = prototype.python_output(grid, output_transform="rotate_cw")
        flipped = prototype.python_output(grid, output_transform="flip_lr")
        assert identity == intermediate
        assert rotated == _rotate_cw_grid(intermediate)
        assert flipped == _flip_lr_grid(intermediate)
        assert len({_key(identity), _key(rotated), _key(flipped)}) == 3

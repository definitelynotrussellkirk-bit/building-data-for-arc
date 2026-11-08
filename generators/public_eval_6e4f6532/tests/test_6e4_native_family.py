from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace/parametric"


def load(name: str):
    path = PARAMETRIC / f"{name}.py"
    assert path.is_file(), f"missing {path.name}"
    spec = importlib.util.spec_from_file_location(f"_6e4_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_native_contract_and_canonical_bytes():
    native = load("native_family")
    assert (PARAMETRIC / "canonical.rkt").read_bytes() == (HOME / "reference.rkt").read_bytes()
    assert native.program({"orientation_mode": "toward"}) == (HOME / "reference.rkt").read_text()
    assert native.program({"orientation_mode": "away"}) != native.CANONICAL
    assert native.PARAMETERS == {"orientation_mode": ["toward", "away"]}
    assert native.DEFAULT == {"orientation_mode": "toward"}
    assert native.LIMITS == {"demos": [2, 6], "queries": [1, 4]}


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_generated_episode_counts_prefixes_and_matched_inputs(seed):
    native = load("native_family")
    toward = native.generate(seed, {"orientation_mode": "toward"}, 6, 4)
    away = native.generate(seed, {"orientation_mode": "away"}, 6, 4)
    assert toward == native.generate(seed, {"orientation_mode": "toward"}, 6, 4)
    assert [p["input"] for p in toward["train"] + toward["test"]] == [
        p["input"] for p in away["train"] + away["test"]
    ]
    assert len({json.dumps(p["input"]) for p in toward["train"] + toward["test"]}) == 10
    assert all(a["output"] != b["output"] for a, b in zip(toward["train"][:2], away["train"][:2]))
    for demos, queries in ((2, 1), (3, 4), (6, 2)):
        short = native.generate(seed, {"orientation_mode": "toward"}, demos, queries)
        assert short["train"] == toward["train"][:demos]
        assert short["test"] == toward["test"][:queries]


@pytest.mark.parametrize("seed", [0, 5, 17])
def test_all_generated_outputs_are_solver_outputs(seed):
    native, family = load("native_family"), load("family")
    for mode in ("toward", "away"):
        episode = native.generate(seed, {"orientation_mode": mode}, 6, 4)
        for pair in episode["train"] + episode["test"]:
            assert family.solve_grid(pair["input"], mode) == pair["output"]


def test_required_demos_vary_guide_geometry_and_d4_transform():
    native = load("native_family")
    descriptions = [native.describe_scene(grid) for grid in native.input_bank(11)[0][:2]]
    assert descriptions[0]["toward_transform_ids"] != descriptions[1]["toward_transform_ids"]
    assert descriptions[0]["guide_colors"] != descriptions[1]["guide_colors"]
    assert descriptions[0]["background"] != descriptions[1]["background"]


def test_large_query_is_substantive_30_by_30():
    native = load("native_family")
    _, queries = native.input_bank(9)
    large = [grid for grid in queries if len(grid) == len(grid[0]) == 30]
    assert len(large) == 1
    grid = large[0]
    bg = native.describe_scene(grid)["background"]
    assert sum(value != bg for row in grid for value in row) >= 160
    assert len(native.describe_scene(grid)["objects"]) >= 2


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True}, {"seed": -1}, {"seed": 2**63},
        {"demos": 1}, {"demos": 7}, {"demos": 2.0},
        {"queries": 0}, {"queries": 5}, {"queries": False},
        {"settings": {}}, {"settings": {"orientation_mode": True}},
    ],
)
def test_invalid_episode_boundaries(kwargs):
    native = load("native_family")
    with pytest.raises(ValueError):
        native.generate(**{"seed": 17, **kwargs})


@pytest.mark.parametrize("seed", [17, 43])
def test_minimum_lesson_changes_inferred_background(seed):
    native = load("native_family")
    descriptions = [native.describe_scene(grid) for grid in native.input_bank(seed)[0][:2]]
    assert descriptions[0]["background"] != descriptions[1]["background"]

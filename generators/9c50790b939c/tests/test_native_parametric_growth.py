from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest
from reviewer_support import find_root

ROOT = find_root(__file__)
HERE = ROOT / "generators" / "9c50790b939c" / "workspace" / "parametric"
SOURCE = HERE / "prototype.py"


def load_prototype():
    name = "_test_9c50790b939c_native_parametric"
    spec = importlib.util.spec_from_file_location(name, SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_native_default_program_is_exact_canonical():
    p = load_prototype()
    assert p.program({"growth_delta": 1}) == (HERE / "canonical.rkt").read_text()


def test_native_counts_are_independent_and_prefix_stable():
    p = load_prototype()
    settings = {"growth_delta": 2}
    large = p.generate(17, settings, demos=6, queries=4)
    small = p.generate(17, settings, demos=2, queries=1)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    assert len({json.dumps(pair["input"]) for pair in large["train"] + large["test"]}) == 10


def test_native_settings_share_inputs_and_two_demos_identify_rivals():
    p = load_prototype()
    episodes = [p.generate(0, {"growth_delta": delta}, demos=2, queries=4) for delta in (0, 1, 2)]
    expected_inputs = [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]]
    assert all(
        [pair["input"] for pair in episode["train"] + episode["test"]] == expected_inputs
        for episode in episodes[1:]
    )
    for delta, episode in zip((0, 1, 2), episodes, strict=True):
        assert p.native_teaching_survivors(episode["train"]) == [f"growth_{delta}"]


def test_native_fourth_query_is_substantive_30x30():
    p = load_prototype()
    grid = p.native_sample_input(17, "query", 3)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 7 for row in grid for value in row) >= 180
    outputs = [p.native_solve(grid, delta) for delta in (0, 1, 2)]
    assert len({json.dumps(output) for output in outputs}) == 3


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"growth_delta": 1}, 2, 1),
        (0, {"growth_delta": 3}, 2, 1),
        (0, {"growth_delta": 1}, 1, 1),
        (0, {"growth_delta": 1}, 2, 5),
    ],
)
def test_native_invalid_requests_are_rejected(seed, settings, demos, queries):
    p = load_prototype()
    with pytest.raises((TypeError, ValueError)):
        p.generate(seed, settings, demos=demos, queries=queries)

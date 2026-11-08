"""Native parametric contract for the local-link versus linked-color family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import find_root


TASK_ID = "8e8d21720efb"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
CANONICAL_SHA256 = "89d99422f73ed0261300be3f62a00ca29212b923d5111eb1d5d0bd8eaf769646"


def _load(name: str, filename: str):
    path = HOME / filename
    assert path.is_file(), f"missing native parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load("test_8e8d_parametric_adapter", "adapter.py")


@pytest.fixture(scope="module")
def family():
    return _load("test_8e8d_parametric_family", "family.py")


def _pairs(episode):
    return episode["train"] + episode["test"]


def _inputs(episode):
    return [pair["input"] for pair in _pairs(episode)]


def _local_reference(grid):
    height, width = len(grid), len(grid[0])
    return [
        [
            value
            if value != 0
            and any(
                0 <= row + dr < height
                and 0 <= col + dc < width
                and grid[row + dr][col + dc] == value
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            else 0
            for col, value in enumerate(values)
        ]
        for row, values in enumerate(grid)
    ]


def _linked_colors_reference(grid):
    output = _local_reference(grid)
    return {value for row in output for value in row if value != 0}


def _global_reference(grid):
    linked = _linked_colors_reference(grid)
    return [[value if value in linked else 0 for value in row] for row in grid]


def test_default_program_is_exact_selected_canonical_source(adapter):
    canonical = (HOME / "canonical.rkt").read_text(encoding="utf-8")
    assert hashlib.sha256(canonical.encode()).hexdigest() == CANONICAL_SHA256
    assert adapter.program({"projection_mode": "local_cells"}) == canonical
    assert adapter.program({"projection_mode": "linked_colors"}) != canonical


@pytest.mark.parametrize(
    "settings",
    [
        None,
        {},
        {"projection_mode": "local_cells", "extra": 1},
        {"projection_mode": "unknown"},
        {"projection_mode": 1},
    ],
)
def test_settings_are_exact_and_finite(adapter, settings):
    with pytest.raises(ValueError, match="projection_mode"):
        adapter.program(settings)


@pytest.mark.parametrize("bad", [True, False, -1, 1.5, "0", None])
def test_seed_is_a_nonnegative_plain_integer(adapter, bad):
    with pytest.raises((TypeError, ValueError), match="seed"):
        adapter.generate(bad, {"projection_mode": "local_cells"}, 3, 4)


@pytest.mark.parametrize("bad", [True, False, 1, 7, 2.5, "3", None])
def test_demo_count_is_two_through_six(adapter, bad):
    with pytest.raises(ValueError, match="demos"):
        adapter.generate(0, {"projection_mode": "local_cells"}, bad, 4)


@pytest.mark.parametrize("bad", [True, False, 0, 1, 3, 5, 4.0, "4", None])
def test_query_count_is_exactly_four(adapter, bad):
    with pytest.raises(ValueError, match="queries"):
        adapter.generate(0, {"projection_mode": "local_cells"}, 3, bad)


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_episode_shape_distinctness_and_matching_inputs(adapter, demos):
    local = adapter.generate(17, {"projection_mode": "local_cells"}, demos, 4)
    global_projection = adapter.generate(17, {"projection_mode": "linked_colors"}, demos, 4)
    assert len(local["train"]) == len(global_projection["train"]) == demos
    assert len(local["test"]) == len(global_projection["test"]) == 4
    assert _inputs(local) == _inputs(global_projection)
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(local)]
    assert len(serialized) == len(set(serialized)) == demos + 4
    assert all(
        left["output"] != right["output"]
        for left, right in zip(_pairs(local), _pairs(global_projection), strict=True)
    )


def test_claimed_labels_match_independent_two_stage_references(adapter):
    for mode, reference in (
        ("local_cells", _local_reference),
        ("linked_colors", _global_reference),
    ):
        episode = adapter.generate(31, {"projection_mode": mode}, 6, 4)
        for pair in _pairs(episode):
            assert pair["output"] == reference(pair["input"])


def test_dependency_intermediate_is_input_derived_and_varies(family, adapter):
    episode = adapter.generate(29, {"projection_mode": "linked_colors"}, 6, 4)
    intermediates = [tuple(family.dependency_intermediate(pair["input"])) for pair in _pairs(episode)]
    assert len(set(intermediates)) >= 4
    for pair, intermediate in zip(_pairs(episode), intermediates, strict=True):
        assert set(intermediate) == _linked_colors_reference(pair["input"])
        remote = [
            (r, c)
            for r, row in enumerate(pair["input"])
            for c, value in enumerate(row)
            if value in intermediate and _local_reference(pair["input"])[r][c] == 0
        ]
        assert remote
        assert all(pair["output"][r][c] == pair["input"][r][c] for r, c in remote)


def test_determinism_does_not_touch_process_random_state(adapter):
    random.seed(991)
    before = random.getstate()
    first = adapter.generate(123, {"projection_mode": "linked_colors"}, 3, 4)
    after = random.getstate()
    second = adapter.generate(123, {"projection_mode": "linked_colors"}, 3, 4)
    assert before == after
    assert first == second
    copied = copy.deepcopy(first)
    copied["train"][0]["input"][0][0] = 9
    assert adapter.generate(123, {"projection_mode": "linked_colors"}, 3, 4) == second


def test_fourth_query_is_substantive_boundary_spanning_30_by_30(adapter):
    episode = adapter.generate(0, {"projection_mode": "linked_colors"}, 3, 4)
    pair = episode["test"][3]
    grid, output = pair["input"], pair["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 100
    assert sum(value != 0 for row in output for value in row) >= 80
    assert any(grid[r][c] != 0 for r, c in ((0, 0), (0, 29), (29, 0), (29, 29)))
    assert output != _local_reference(grid)


def test_promotion_contract_declares_only_supported_surface():
    contract = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"projection_mode": ["local_cells", "linked_colors"]},
        "default": {"projection_mode": "local_cells"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/family.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
        ],
    }

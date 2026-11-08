"""Behavior tests for the proposed render-mode parametric family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / "generators/924a6f0f0549/workspace/parametric"
PROTOTYPE_PATH = HOME / "prototype.py"
ADAPTER_PATH = HOME / "adapter.py"
CONTRACT_PATH = HOME / "promotion.json"
PROBE_PATH = HOME / "adversarial_probe.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_task_local_parametric_artifacts_are_present() -> None:
    assert PROTOTYPE_PATH.is_file()
    assert ADAPTER_PATH.is_file()
    assert CONTRACT_PATH.is_file()
    assert PROBE_PATH.is_file()


@pytest.fixture(scope="module")
def prototype():
    return _load("parametric_924a6f0f0549", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    sys.path.insert(0, str(HOME))
    try:
        return _load("parametric_924a6f0f0549_adapter", ADAPTER_PATH)
    finally:
        sys.path.remove(str(HOME))


@pytest.fixture(scope="module")
def bridge(prototype):
    with prototype.RacketBridge(max_calls_before_restart=128) as active:
        yield active


def test_default_program_is_exact_and_alternative_patch_is_guarded(prototype) -> None:
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "23fd1d61a026f5aed86bf59e77a3fc5ffae49ebbeaea5ff89f5916ea88c264c5"
    )
    assert prototype.program_for("outline", root=ROOT) == canonical
    silhouette = prototype.program_for("silhouette", root=ROOT)
    assert silhouette != canonical
    assert "(outline cells)" in silhouette
    assert "(outline (e5-outline-cells cells))" not in silhouette
    for bad in ("filled", "", 0, True, None):
        with pytest.raises(ValueError, match="render_mode"):
            prototype.program_for(bad, root=ROOT)


def test_real_racket_and_python_mirror_distinguish_both_modes(prototype, bridge) -> None:
    grid = prototype.build_input(7, 0, 7, "medium")
    before = copy.deepcopy(grid)
    outputs = {}
    for mode in prototype.ALLOWED_MODES:
        expected = prototype.python_mirror(grid, render_mode=mode)
        actual = prototype.execute_rule(
            prototype.program_for(mode, root=ROOT), grid, bridge=bridge
        )
        assert actual == expected
        outputs[mode] = actual
    assert outputs["outline"] != outputs["silhouette"]
    assert grid == before


def test_adapter_outputs_matched_identifiable_episodes_with_four_queries(
    prototype, adapter, bridge
) -> None:
    families = {
        mode: adapter.generate(17, {"render_mode": mode}, 2, 4)
        for mode in prototype.ALLOWED_MODES
    }
    inputs = [
        pair["input"] for pair in families["outline"]["train"] + families["outline"]["test"]
    ]
    assert len({prototype.grid_sha256(grid) for grid in inputs}) == 6
    for mode, claims in families.items():
        assert claims["program_solution"] == prototype.program_for(mode, root=ROOT)
        assert len(claims["train"]) == 2
        assert len(claims["test"]) == 4
        assert [pair["input"] for pair in claims["train"] + claims["test"]] == inputs
        rival = next(value for value in prototype.ALLOWED_MODES if value != mode)
        assert all(
            pair["output"] == prototype.python_mirror(pair["input"], render_mode=mode)
            and pair["output"] != prototype.python_mirror(pair["input"], render_mode=rival)
            for pair in claims["train"]
        )
        for pair in claims["train"] + claims["test"]:
            actual = prototype.execute_rule(claims["program_solution"], pair["input"], bridge=bridge)
            assert actual == pair["output"]


def test_counts_validation_and_contract_are_strict(prototype, adapter) -> None:
    for demos in (2, 6):
        claims = adapter.generate(29, {"render_mode": "outline"}, demos, 4)
        assert len(claims["train"]) == demos
        assert len(claims["test"]) == 4
    for demos in (1, 7, True):
        with pytest.raises(ValueError, match="demos"):
            adapter.generate(1, {"render_mode": "outline"}, demos, 4)
    for queries in (0, 3, 5, True):
        with pytest.raises(ValueError, match="queries"):
            adapter.generate(1, {"render_mode": "outline"}, 2, queries)
    for settings in ({}, {"render_mode": "bad"}, {"extra": "outline"}):
        with pytest.raises(ValueError):
            adapter.program(settings)

    assert json.loads(CONTRACT_PATH.read_text()) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/924a6f0f0549/workspace/parametric/adapter.py",
        "parameters": {"render_mode": ["outline", "silhouette"]},
        "default": {"render_mode": "outline"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }


def test_final_query_is_substantive_30_by_30_not_padding(prototype, adapter) -> None:
    claims = adapter.generate(31, {"render_mode": "silhouette"}, 2, 4)
    grid = claims["test"][-1]["input"]
    assert [len(grid), len(grid[0])] == [30, 30]
    marker_count = sum(value == 1 for value in grid[0])
    assert marker_count == 25
    body_cells = sum(value != 0 for row in grid[1:] for value in row)
    assert body_cells >= 44
    silhouette = prototype.python_mirror(grid, render_mode="silhouette")
    outline = prototype.python_mirror(grid, render_mode="outline")
    assert [len(silhouette), len(silhouette[0])] == [5, 5]
    assert sum(value != 0 for row in silhouette for value in row) == 25
    assert sum(value != 0 for row in outline for value in row) == 16

"""Focused tests for the bottom-survivor modal-colour parametric family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / "generators/e89e3ed7cb28/workspace/parametric"
PROTOTYPE_PATH = HOME / "prototype.py"
ADAPTER_PATH = HOME / "adapter.py"
CONTRACT_PATH = HOME / "promotion.json"
PROBE_PATH = HOME / "adversarial_probe.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_task_local_parametric_artifacts_are_present():
    assert PROTOTYPE_PATH.is_file()
    assert ADAPTER_PATH.is_file()
    assert CONTRACT_PATH.is_file()
    assert PROBE_PATH.is_file()


@pytest.fixture(scope="module")
def prototype():
    return _load("parametric_e89e3ed7cb28", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_e89e3ed7cb28_adapter", ADAPTER_PATH)


@pytest.fixture(scope="module")
def racket_bridge(prototype):
    with prototype.RacketBridge() as bridge:
        yield bridge


def test_programs_preserve_exact_canonical_default(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert prototype.program_for("bottommost", root=ROOT) == canonical
    alternate = prototype.program_for("modal_survivor_color", root=ROOT)
    assert alternate != canonical
    assert "stage-a" in alternate
    assert "key-color" in alternate
    for invalid in ("mode", "", 0, None, True):
        with pytest.raises(ValueError, match="output_mode"):
            prototype.program_for(invalid, root=ROOT)


def test_real_racket_and_python_mirror_distinguish_both_modes(
    prototype, racket_bridge
):
    grid = prototype.make_input(17, 0, height=12, width=14)
    before = copy.deepcopy(grid)
    outputs = {}
    for mode in prototype.ALLOWED_MODES:
        program = prototype.program_for(mode, root=ROOT)
        outputs[mode] = prototype.execute_rule(program, grid, bridge=racket_bridge)
        assert outputs[mode] == prototype.python_mirror(grid, output_mode=mode)
    assert outputs["bottommost"] != outputs["modal_survivor_color"]
    assert grid == before


def test_episode_counts_determinism_and_substantive_30x30_query(prototype):
    for demos in (2, 3, 6):
        episode = prototype.make_episode(
            31,
            output_mode="modal_survivor_color",
            demos=demos,
            queries=4,
            root=ROOT,
        )
        replay = prototype.make_episode(
            31,
            output_mode="modal_survivor_color",
            demos=demos,
            queries=4,
            root=ROOT,
        )
        assert episode == replay
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({hashlib.sha256(json.dumps(grid).encode()).hexdigest() for grid in inputs}) == len(inputs)
        stress = episode["test"][-1]["input"]
        assert (len(stress), len(stress[0])) == (30, 30)
        occupied = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
        assert len(occupied) >= 80
        assert {0, 29} <= {r for r, _ in occupied}
        assert {0, 29} <= {c for _, c in occupied}


def test_modal_survivor_intermediate_refutes_whole_grid_mode_shortcut(prototype):
    for index in range(8):
        grid = prototype.make_input(73, index, height=14, width=16)
        stage_a = prototype.bottommost_grid(grid)
        key = prototype.modal_survivor_color(stage_a)
        whole_grid_mode = prototype.whole_grid_modal_color(grid)
        assert key != whole_grid_mode
        official = prototype.python_mirror(grid, output_mode="modal_survivor_color")
        shortcut = prototype.filter_to_color(grid, whole_grid_mode)
        assert official != shortcut
        assert any(
            grid[r][c] == key and stage_a[r][c] == 0
            for r in range(len(grid))
            for c in range(len(grid[0]))
        )


def test_adapter_contract_is_strict_and_generation_is_racket_free(
    prototype, adapter, monkeypatch
):
    contract = json.loads(CONTRACT_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/e89e3ed7cb28/workspace/parametric/adapter.py",
        "parameters": {
            "output_mode": ["bottommost", "modal_survivor_color"]
        },
        "default": {"output_mode": "bottommost"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    monkeypatch.setattr(
        adapter.prototype,
        "RacketBridge",
        lambda: pytest.fail("adapter generation must not execute Racket"),
    )
    claims = adapter.generate(
        89,
        {"output_mode": "modal_survivor_color"},
        demos=2,
        queries=4,
    )
    assert set(claims) == {"train", "test", "program_solution"}
    assert len(claims["train"]) == 2
    assert len(claims["test"]) == 4
    assert claims["program_solution"] == prototype.program_for(
        "modal_survivor_color", root=ROOT
    )
    for bad in ({}, {"output_mode": "bad"}, {"output_mode": "bottommost", "x": 1}):
        with pytest.raises(ValueError):
            adapter.program(bad)

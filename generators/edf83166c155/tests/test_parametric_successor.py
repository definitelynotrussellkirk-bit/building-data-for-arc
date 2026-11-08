"""Focused tests for the symmetric-key successor-object parametric family."""
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
HOME = ROOT / "generators/edf83166c155/workspace/parametric"
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


def _quadrant(component, height: int, width: int) -> str:
    vertical = "top" if component["top"] < height // 2 else "bottom"
    horizontal = "left" if component["left"] < width // 2 else "right"
    return {
        ("top", "left"): "tl",
        ("top", "right"): "tr",
        ("bottom", "left"): "bl",
        ("bottom", "right"): "br",
    }[(vertical, horizontal)]


def test_task_local_parametric_artifacts_are_present():
    assert PROTOTYPE_PATH.is_file()
    assert ADAPTER_PATH.is_file()
    assert CONTRACT_PATH.is_file()
    assert PROBE_PATH.is_file()


@pytest.fixture(scope="module")
def prototype():
    return _load("parametric_edf83166c155", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    return _load("parametric_edf83166c155_adapter", ADAPTER_PATH)


@pytest.fixture(scope="module")
def racket_bridge(prototype):
    with prototype.RacketBridge() as bridge:
        yield bridge


def test_programs_preserve_exact_canonical_default(prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert prototype.program_for("symmetric_object", root=ROOT) == canonical
    alternate = prototype.program_for("successor_of_symmetric", root=ROOT)
    assert alternate != canonical
    assert "key" in alternate
    assert "wanted" in alternate
    assert "obj-color key" in alternate
    for invalid in ("mode", "", 0, None, True):
        with pytest.raises(ValueError, match="output_mode"):
            prototype.program_for(invalid, root=ROOT)


def test_real_racket_and_python_mirror_distinguish_both_modes(
    prototype, racket_bridge
):
    grid = prototype.make_input(17, 0, height=14, width=16)
    before = copy.deepcopy(grid)
    outputs = {}
    for mode in prototype.ALLOWED_MODES:
        program = prototype.program_for(mode, root=ROOT)
        outputs[mode] = prototype.execute_rule(program, grid, bridge=racket_bridge)
        assert outputs[mode] == prototype.python_mirror(grid, output_mode=mode)
    assert outputs["symmetric_object"] != outputs["successor_of_symmetric"]
    assert grid == before


def test_episode_counts_determinism_and_substantive_30x30_query(prototype):
    for demos in (2, 3, 6):
        episode = prototype.make_episode(
            31,
            output_mode="successor_of_symmetric",
            demos=demos,
            queries=4,
            root=ROOT,
        )
        replay = prototype.make_episode(
            31,
            output_mode="successor_of_symmetric",
            demos=demos,
            queries=4,
            root=ROOT,
        )
        assert episode == replay
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        digests = {hashlib.sha256(json.dumps(grid).encode()).hexdigest() for grid in inputs}
        assert len(digests) == len(inputs)
        for grid in inputs:
            components = prototype.components(grid)
            keys = [component for component in components if component["lr"]]
            assert len(keys) == 1
            key = keys[0]
            partners = [
                component
                for component in components
                if component["color"] == prototype.successor_color(key["color"])
            ]
            assert len(partners) == 1
        stress = episode["test"][-1]["input"]
        assert (len(stress), len(stress[0])) == (30, 30)
        occupied = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
        assert len(occupied) >= 40
        assert {0, 29} <= {r for r, _ in occupied}
        assert {0, 29} <= {c for _, c in occupied}
        assert len(prototype.components(stress)) == 9


def test_symmetric_key_intermediate_refutes_location_and_first_object_shortcuts(
    prototype,
):
    key_regions = set()
    partner_regions = set()
    partner_colors = set()
    first_object_disagreements = 0
    first_successor_disagreements = 0
    for index in range(12):
        grid = prototype.make_input(73, index, height=14, width=16)
        components = prototype.components(grid)
        key = prototype.find_symmetric_component(grid)
        partner = prototype.find_successor_component(grid, key)
        official = prototype.python_mirror(grid, output_mode="successor_of_symmetric")
        key_regions.add(_quadrant(key, len(grid), len(grid[0])))
        partner_regions.add(_quadrant(partner, len(grid), len(grid[0])))
        partner_colors.add(partner["color"])
        first_object_disagreements += prototype.crop_component(grid, components[0]) != official
        desired = prototype.successor_color(components[0]["color"])
        first_hit = next((c for c in components if c["color"] == desired), None)
        shortcut = [] if first_hit is None else prototype.crop_component(grid, first_hit)
        first_successor_disagreements += shortcut != official
    assert key_regions == {"tl", "tr", "bl", "br"}
    assert partner_regions == {"tl", "tr", "bl", "br"}
    assert len(partner_colors) >= 6
    assert first_object_disagreements >= 9
    assert first_successor_disagreements >= 9


def test_adapter_contract_is_strict_and_generation_is_racket_free(
    prototype, adapter, monkeypatch
):
    contract = json.loads(CONTRACT_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/edf83166c155/workspace/parametric/adapter.py",
        "parameters": {
            "output_mode": ["symmetric_object", "successor_of_symmetric"]
        },
        "default": {"output_mode": "symmetric_object"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    monkeypatch.setattr(
        adapter.prototype,
        "RacketBridge",
        lambda: pytest.fail("adapter generation must not execute Racket"),
    )
    claims = adapter.generate(
        89,
        {"output_mode": "successor_of_symmetric"},
        demos=2,
        queries=4,
    )
    assert set(claims) == {"train", "test", "program_solution"}
    assert len(claims["train"]) == 2
    assert len(claims["test"]) == 4
    assert claims["program_solution"] == prototype.program_for(
        "successor_of_symmetric", root=ROOT
    )
    for bad in ({}, {"output_mode": "bad"}, {"output_mode": "symmetric_object", "x": 1}):
        with pytest.raises(ValueError):
            adapter.program(bad)

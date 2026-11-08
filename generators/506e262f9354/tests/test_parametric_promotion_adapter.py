"""Promotion-contract tests for the expansion-direction prototype."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
HOME = ROOT / "generators/506e262f9354/workspace/parametric"
PROTOTYPE_PATH = HOME / "prototype.py"
ADAPTER_PATH = HOME / "adapter.py"
CONTRACT_PATH = HOME / "promotion.json"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load("parametric_506e262f9354_promotion_prototype", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    assert ADAPTER_PATH.is_file(), "promotion adapter must be task-local"
    sys.path.insert(0, str(HOME))
    try:
        return _load("parametric_506e262f9354_adapter", ADAPTER_PATH)
    finally:
        sys.path.remove(str(HOME))


def test_promotion_contract_declares_exact_bounded_direction_setting():
    assert CONTRACT_PATH.is_file(), "promotion contract must exist"
    contract = json.loads(CONTRACT_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/506e262f9354/workspace/parametric/adapter.py",
        "parameters": {"expansion_direction": ["up", "down"]},
        "default": {"expansion_direction": "up"},
        "limits": {"demos": [3, 8], "queries": [1, 8]},
    }


def test_adapter_default_program_is_exact_canonical(adapter, prototype):
    assert adapter.program({"expansion_direction": "up"}) == prototype.canonical_source(
        root=ROOT
    )
    assert adapter.program({"expansion_direction": "down"}) == prototype.program_for(
        "down", root=ROOT
    )
    for settings in ({}, {"expansion_direction": "left"}, {"extra": "up"}):
        with pytest.raises(ValueError):
            adapter.program(settings)


def test_adapter_generates_python_claims_without_starting_racket(
    adapter, prototype, monkeypatch
):
    monkeypatch.setattr(
        adapter.prototype,
        "RacketBridge",
        lambda: pytest.fail("promotion adapter must leave protected Racket replay to worker"),
    )
    episode = adapter.generate(
        53, {"expansion_direction": "down"}, demos=3, queries=4
    )

    assert set(episode) == {"train", "test", "program_solution"}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == prototype.program_for("down", root=ROOT)
    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
    assert len({prototype.grid_sha256(grid) for grid in inputs}) == 7
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == prototype.python_mirror(
            pair["input"], expansion_direction="down"
        )

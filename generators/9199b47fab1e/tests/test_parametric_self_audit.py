"""Behavioral checks for the bounded visible-lesson self-audit."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace/parametric"


def load(name: str):
    path = PARAMETRIC / name
    assert path.is_file(), f"missing {name}"
    spec = importlib.util.spec_from_file_location(f"test_9199_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_declared_rivals_are_distinct_and_eliminated_by_constructive_demos():
    adapter = load("adapter.py")
    audit = load("audit.py")
    for seed in (0, 17, 91):
        for mode in ("original_seeds", "farthest_relay"):
            episode = adapter.generate(seed, {"source_mode": mode}, demos=2, queries=4)
            result = audit.audit_episode(episode, {"source_mode": mode})
            assert result["ambiguous_rivals"] == []
            assert result["demo_survivors"] == []
            assert result["rival_count"] >= 4


def test_audit_detects_a_demo_survivor_that_disagrees_on_a_query():
    adapter = load("adapter.py")
    audit = load("audit.py")
    episode = adapter.generate(5, {"source_mode": "farthest_relay"}, demos=2, queries=4)
    # Replace the visible demos with the first-seed relay rival while preserving
    # the intended query labels. The audit must identify the shortcut rather
    # than treating it as a harmless mismatch.
    for pair in episode["train"]:
        pair["output"] = audit.first_seed_relay(pair["input"])
    result = audit.audit_episode(episode, {"source_mode": "farthest_relay"})
    assert "first_seed_relay" in result["ambiguous_rivals"]

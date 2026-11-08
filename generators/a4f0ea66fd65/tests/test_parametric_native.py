"""Native parametric admission tests for the vector-copy repeat family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAM / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _input_keys(episode):
    return [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in ("train", "test")
        for pair in episode[split]
    ]


def test_exact_canonical_program_and_settings_validation():
    adapter = _load("vector_repeat_adapter_program", "adapter.py")
    canonical = (PARAM / "canonical.rkt").read_text(encoding="utf-8")
    assert adapter.program({"copy_extent": "single"}) == canonical
    assert adapter.program({"copy_extent": "decoy_size"}) != canonical
    for bad in (
        None,
        {},
        {"copy_extent": "decoy_size", "extra": 1},
        {"copy_extent": "unknown"},
        {"copy_extent": 3},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)


def test_counts_are_independent_prefix_stable_matched_and_fresh():
    adapter = _load("vector_repeat_adapter_counts", "adapter.py")
    settings = [{"copy_extent": "single"}, {"copy_extent": "decoy_size"}]
    full = [adapter.generate(17, setting, demos=6, queries=4) for setting in settings]
    assert _input_keys(full[0]) == _input_keys(full[1])
    assert len(set(_input_keys(full[0]))) == 10
    for setting, complete in zip(settings, full, strict=True):
        for demos in (2, 3, 5):
            short = adapter.generate(17, setting, demos=demos, queries=4)
            assert short["train"] == complete["train"][:demos]
            assert short["test"] == complete["test"]
        for queries in (1, 2, 3):
            short = adapter.generate(17, setting, demos=6, queries=queries)
            assert short["train"] == complete["train"]
            assert short["test"] == complete["test"][:queries]
    first = adapter.generate(17, settings[0], demos=3, queries=4)
    second = adapter.generate(17, settings[0], demos=3, queries=4)
    assert first == second and first is not second
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(17, settings[0], demos=3, queries=4) == second


def test_two_demonstrations_teach_both_settings_and_declared_rivals():
    adapter = _load("vector_repeat_adapter_teaching", "adapter.py")
    prototype = _load("vector_repeat_prototype_teaching", "prototype.py")
    for seed in (0, 17, 31):
        for mode in prototype.MODES:
            episode = adapter.generate(seed, {"copy_extent": mode}, demos=2, queries=4)
            report = prototype.teaching_report(episode, mode)
            assert report["surviving_harmful_rivals"] == [], (seed, mode, report)
            other = next(value for value in prototype.MODES if value != mode)
            assert any(
                prototype.apply_python(pair["input"], other) != pair["output"]
                for pair in episode["train"]
            )


def test_fourth_query_is_distributed_boundary_spanning_30x30():
    adapter = _load("vector_repeat_adapter_large", "adapter.py")
    prototype = _load("vector_repeat_prototype_large", "prototype.py")
    for mode in prototype.MODES:
        pair = adapter.generate(17, {"copy_extent": mode}, demos=3, queries=4)["test"][3]
        grid = pair["input"]
        output = pair["output"]
        assert (len(grid), len(grid[0])) == (30, 30)
        occupied_in = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
        occupied_out = [(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value]
        assert len(occupied_in) >= 13
        assert len(occupied_out) >= (20 if mode == "single" else 40)
        assert min(r for r, _ in occupied_out) == 0
        assert max(r for r, _ in occupied_out) == 29
        assert min(c for _, c in occupied_out) == 0
        assert max(c for _, c in occupied_out) == 29
        assert prototype.validate_grid(grid) == (30, 30)


def test_public_turn_masks_private_state_and_future_queries():
    prototype = _load("vector_repeat_prototype_public", "prototype.py")
    episode = prototype.generate(5, {"copy_extent": "decoy_size"}, demos=3, queries=4)
    first = prototype.public_turn(episode, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    text = json.dumps(first, sort_keys=True)
    for forbidden in ("copy_extent", "program_solution", "decoy_size"):
        assert forbidden not in text
    assert first["test"][0]["input"] == episode["test"][0]["input"]


def test_invalid_requests_fail_loudly():
    adapter = _load("vector_repeat_adapter_invalid", "adapter.py")
    valid = {
        "seed": 17,
        "settings": {"copy_extent": "single"},
        "demos": 3,
        "queries": 4,
    }
    for field, values in {
        "seed": (-1, 2**63, True, 1.5, "17"),
        "demos": (1, 7, True, 3.0, "3"),
        "queries": (0, 5, True, 1.0, "1"),
    }.items():
        for value in values:
            with pytest.raises((TypeError, ValueError)):
                adapter.generate(**{**valid, field: value})

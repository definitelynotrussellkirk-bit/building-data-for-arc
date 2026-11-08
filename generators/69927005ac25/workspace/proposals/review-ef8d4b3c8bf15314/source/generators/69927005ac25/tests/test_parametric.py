"""Native parametric contract for 69927005ac25."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
HOME = REPO / "generators/69927005ac25/workspace/parametric"


def _load(name, filename):
    path = HOME / filename
    assert path.exists(), f"missing {filename}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _adapter():
    return _load("parametric_69927005ac25", "adapter.py")


def _bridge(grid):
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0:
                continue
            for dc in (2, -2):
                nr, nc = r + 2, c + dc
                mr, mc = r + 1, c + dc // 2
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == value and out[mr][mc] == 0:
                    out[mr][mc] = value
    return out


def _complete_x(grid):
    bridged = _bridge(grid)
    out = deepcopy(bridged)
    h, w = len(grid), len(grid[0])
    for r in range(h - 2):
        for c in range(w):
            value = bridged[r][c]
            if value == 0:
                continue
            for dc in (1, -1):
                if not (0 <= c + 2 * dc < w):
                    continue
                if bridged[r + 1][c + dc] != value or bridged[r + 2][c + 2 * dc] != value:
                    continue
                for rr, cc in ((r, c + 2 * dc), (r + 2, c)):
                    if out[rr][cc] == 0:
                        out[rr][cc] = value
    return out


def _inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def test_programs_and_settings_are_exact_and_strict():
    adapter = _adapter()
    assert adapter.program({"completion_mode": "midpoint_only"}) == (HOME / "canonical.rkt").read_text()
    assert adapter.program({"completion_mode": "complete_x"}) == (HOME / "complete_x.rkt").read_text()
    for bad in ({}, None, {"completion_mode": "bad"}, {"completion_mode": 1},
                {"completion_mode": "midpoint_only", "extra": 1}):
        with pytest.raises(ValueError):
            adapter.program(bad)


def test_inputs_are_matched_and_demo_query_prefixes_are_independent():
    adapter = _adapter()
    canonical = adapter.generate(17, {"completion_mode": "midpoint_only"}, 3, 4)
    alternate = adapter.generate(17, {"completion_mode": "complete_x"}, 3, 4)
    assert _inputs(canonical, "train") == _inputs(alternate, "train")
    assert _inputs(canonical, "test") == _inputs(alternate, "test")
    two = adapter.generate(17, {"completion_mode": "midpoint_only"}, 2, 4)
    six = adapter.generate(17, {"completion_mode": "midpoint_only"}, 6, 4)
    one = adapter.generate(17, {"completion_mode": "midpoint_only"}, 3, 1)
    assert _inputs(two, "train") == _inputs(six, "train")[:2]
    assert _inputs(two, "test") == _inputs(six, "test")
    assert _inputs(one, "test") == _inputs(canonical, "test")[:1]
    all_inputs = _inputs(six, "train") + _inputs(six, "test")
    assert len({repr(grid) for grid in all_inputs}) == len(all_inputs)


@pytest.mark.parametrize("seed", [0, 17, 991])
def test_python_claims_match_both_rules_and_two_demos_distinguish(seed):
    adapter = _adapter()
    canonical = adapter.generate(seed, {"completion_mode": "midpoint_only"}, 2, 4)
    alternate = adapter.generate(seed, {"completion_mode": "complete_x"}, 2, 4)
    for left, right in zip(canonical["train"] + canonical["test"],
                           alternate["train"] + alternate["test"]):
        assert left["input"] == right["input"]
        assert left["output"] == _bridge(left["input"])
        assert right["output"] == _complete_x(right["input"])
    assert all(a["output"] != b["output"] for a, b in zip(canonical["train"], alternate["train"]))


@pytest.mark.parametrize("mode", ["midpoint_only", "complete_x"])
def test_four_queries_include_substantive_30x30_stress(mode):
    adapter = _adapter()
    episode = adapter.generate(42, {"completion_mode": mode}, 3, 4)
    grid = episode["test"][-1]["input"]
    output = episode["test"][-1]["output"]
    assert len(grid) == 30 and all(len(row) == 30 for row in grid)
    assert sum(value != 0 for row in grid for value in row) >= 48
    assert len(output) == 30 and all(len(row) == 30 for row in output)
    assert output != grid


def test_public_turn_reveals_only_one_query_input():
    adapter = _adapter()
    episode = adapter.generate(7, {"completion_mode": "complete_x"}, 3, 4)
    view = adapter.public_turn(episode, 2)
    assert view["train"] == episode["train"]
    assert view["test"] == [{"input": episode["test"][2]["input"]}]
    assert "program_solution" not in view


def test_invalid_counts_and_seed_types_are_rejected():
    adapter = _adapter()
    settings = {"completion_mode": "midpoint_only"}
    for args in ((True, settings, 3, 4), (-1, settings, 3, 4),
                 (0, settings, 1, 4), (0, settings, 7, 4),
                 (0, settings, 3, 0), (0, settings, 3, 5),
                 (0, settings, 3.0, 4)):
        with pytest.raises(ValueError):
            adapter.generate(*args)


def test_bounded_self_audit_refutes_named_shortcuts():
    audit = _load("audit_69927005ac25", "audit.py")
    report = audit.run(seeds=(0, 17, 991))
    assert report["schema"] == "arcpuzzles-parametric-self-audit-v1"
    assert report["status"] == "passed"
    assert report["surviving_rivals"] == []
    assert report["episodes_checked"] == 6
    assert report["has_30x30"] is True

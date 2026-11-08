"""Focused tests for the native parametric family of 75ff4423494a."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog

TASK_ID = "75ff4423494a"
ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load(MODULE_PATH, "_parametric_75ff4423494a")


def _canonical_program() -> str:
    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical(proto):
    assert proto.program({"copy_policy": "all_anchors"}) == _canonical_program()
    assert proto.program({"copy_policy": "signal_ranked_anchor"}) != _canonical_program()


@pytest.mark.parametrize("bad", [None, {}, {"copy_policy": True}, {"copy_policy": "bad"}, {"x": "all_anchors"}])
def test_settings_fail_closed(proto, bad):
    with pytest.raises(ValueError):
        proto.program(bad)


def test_counts_matched_inputs_and_prefix_stability(proto):
    canonical = proto.generate(17, {"copy_policy": "all_anchors"}, 2, 4)
    alternate = proto.generate(17, {"copy_policy": "signal_ranked_anchor"}, 2, 4)
    longer = proto.generate(17, {"copy_policy": "all_anchors"}, 6, 4)

    assert len(canonical["train"]) == 2
    assert len(canonical["test"]) == 4
    assert _inputs(canonical) == _inputs(alternate)
    assert canonical["train"] == longer["train"][:2]
    assert canonical["test"] == longer["test"]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)}) == 6
    assert [(len(p["input"]), len(p["input"][0])) for p in canonical["test"]] == [
        (15, 17), (20, 22), (25, 27), (30, 30)
    ]
    assert all(a["output"] != b["output"] for a, b in zip(canonical["train"] + canonical["test"], alternate["train"] + alternate["test"]))


@pytest.mark.parametrize("mode", ["all_anchors", "signal_ranked_anchor"])
def test_first_two_demos_identify_the_setting(proto, mode):
    episode = proto.generate(3, {"copy_policy": mode}, 2, 4)
    survivors = []
    for candidate in proto.MODES:
        if all(proto.apply_mode(pair["input"], candidate) == pair["output"] for pair in episode["train"]):
            survivors.append(candidate)
    assert survivors == [mode]
    assert all(proto.apply_mode(pair["input"], mode) == pair["output"] for pair in episode["test"])


def test_stress_query_and_causal_counterfactual(proto):
    episode = proto.generate(29, {"copy_policy": "signal_ranked_anchor"}, 3, 4)
    grid = episode["test"][3]["input"]
    assert len(grid) == len(grid[0]) == 30
    assert sum(cell != 0 for row in grid for cell in row) >= 80
    assert all(any(grid[r][c] != 0 for r, c in cells) for cells in (
        [(0, c) for c in range(30)],
        [(29, c) for c in range(30)],
        [(r, 0) for r in range(30)],
        [(r, 29) for r in range(30)],
    ))
    actual = proto.signal_intermediate(grid)
    wrong_rank = 1 if actual["rank"] != 1 else 2
    assert proto.apply_ranked(grid, wrong_rank) != episode["test"][3]["output"]


def test_invalid_counts_are_rejected(proto):
    for demos, queries in ((1, 4), (7, 4), (2, 0), (2, 5), (True, 4)):
        with pytest.raises(ValueError):
            proto.generate(0, {"copy_policy": "all_anchors"}, demos, queries)


def test_reusable_audit_rejects_declared_shortcuts_and_checks_public_projection():
    audit_path = MODULE_PATH.with_name("audit_lessons.py")
    audit = _load(audit_path, "_audit_75ff4423494a")
    report = audit.build_report(seeds=range(4), demo_counts=(2, 3, 6))
    assert report["status"] == "passed"
    assert report["episodes"] == 24
    assert report["harmful_survivors"] == 0
    assert report["exact_30x30_pairs"] == 24
    assert report["public_projection_failures"] == []

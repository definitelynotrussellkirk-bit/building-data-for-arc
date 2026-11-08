"""Focused invariants for the opt-in diagonal gap family, not production admission."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PROTOTYPE = HOME / "workspace/parametric"


@pytest.fixture(scope="module")
def adapter():
    path = PROTOTYPE / "adapter.py"
    assert path.is_file(), "The native parametric adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_59a7762bc6da_native", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def settings(policy="keep"):
    return {"gap_policy": policy}


def canonical():
    return next(json.loads(line)["program_solution"] for line in
                (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
                if json.loads(line).get("task_id") == HOME.name)


def fingerprint(grid):
    return tuple(map(tuple, grid))


def test_native_contract_and_exact_canonical_default(adapter):
    contract = json.loads((PROTOTYPE / "promotion.json").read_text())
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {"gap_policy": ["keep", "bridge_once"]}
    assert contract["default"] == settings()
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert adapter.program(settings()) == canonical()
    assert (PROTOTYPE / "canonical.rkt").read_text() == canonical()
    assert adapter.program(settings("bridge_once")) != canonical()


@pytest.mark.parametrize("policy", ["keep", "bridge_once"])
def test_every_program_uses_real_rule_wrapper(adapter, policy):
    from puzzle_generators.rule_wrap import wrap_rule
    wrapped = wrap_rule(adapter.program(settings(policy)))
    assert isinstance(wrapped, str) and wrapped.strip()


@pytest.mark.parametrize("bad", [None, {}, {"gap_policy": "other"},
    {"gap_policy": True}, {"gap_policy": 1}, {"gap_policy": "keep", "extra": 3}])
def test_invalid_settings_are_rejected(adapter, bad):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(bad)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, bad, 3, 4)


@pytest.mark.parametrize("seed", [True, -1, 2**63, 1.0, "0"])
def test_seed_boundary_is_strict(adapter, seed):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, settings(), 3, 4)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (True, 4),
    (3.0, 4), (3, 0), (3, 5), (3, True), (3, 4.0)])
def test_count_boundary_is_strict(adapter, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings(), demos, queries)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_counts_are_independent_prefixes_and_inputs_are_paired(adapter, seed):
    short = adapter.generate(seed, settings(), 2, 1)
    long = adapter.generate(seed, settings(), 6, 4)
    other = adapter.generate(seed, settings("bridge_once"), 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert len(long["train"]) == 6 and len(long["test"]) == 4
    assert len({fingerprint(p["input"]) for split in ("train", "test") for p in long[split]}) == 10
    for split in ("train", "test"):
        assert [p["input"] for p in long[split]] == [p["input"] for p in other[split]]
    assert any(a["output"] != b["output"] for a, b in zip(long["train"][:2], other["train"][:2]))


@pytest.mark.parametrize("height,width", [(16, 16), (16, 30), (30, 16), (30, 30)])
def test_substantive_boundary_canvases(adapter, height, width):
    grid = adapter.sample_input(17, "test", 3, height=height, width=width)
    assert len(grid) == height and all(len(row) == width for row in grid)
    assert {c for row in grid for c in row} == {5, 7}
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5}
    assert min(r for r, c in cells) == 0 and max(r for r, c in cells) == height - 1
    assert min(c for r, c in cells) == 0 and max(c for r, c in cells) == width - 1
    assert {(int(r >= height / 2), int(c >= width / 2)) for r, c in cells} == {(0, 0), (0, 1), (1, 0), (1, 1)}
    assert len(cells) >= (40 if height == width == 30 else 18)
    for policy in ("keep", "bridge_once"):
        result = adapter.transform(grid, settings(policy))
        assert len(result) == height and all(len(row) == width for row in result)
        assert 5 in {c for row in result for c in row} and 8 in {c for row in result for c in row}


def test_simultaneous_fill_does_not_cascade(adapter):
    grid = [[7] * 7 for _ in range(7)]
    for r, c in ((0, 2), (2, 0), (3, 3)):
        grid[r][c] = 5
    middle = adapter.bridge_once(grid)
    assert middle[1][1] == 5 and middle[2][2] == 7
    result = adapter.transform(grid, settings("bridge_once"))
    assert all(result[r][c] == 8 for r, c in ((0, 2), (1, 1), (2, 0)))
    assert result[3][3] == 5 and result[2][2] == 7
    assert grid[1][1] == 7


def test_bridge_recomputes_connectivity_and_colors_remote_branch(adapter):
    grid = [[7] * 8 for _ in range(6)]
    for r, c in ((0, 0), (2, 2), (2, 3), (2, 4), (2, 5)):
        grid[r][c] = 5
    assert adapter.transform(grid, settings()) == grid
    result = adapter.transform(grid, settings("bridge_once"))
    assert all(result[r][c] == 8 for r, c in ((0, 0), (1, 1), (2, 2), (2, 3), (2, 4), (2, 5)))
    assert sum(v == 8 for row in result for v in row) == 6


def test_rng_and_returned_values_are_isolated(adapter):
    random.seed(512)
    before = random.getstate()
    first = adapter.generate(31, settings("bridge_once"), 3, 4)
    assert random.getstate() == before
    expected = adapter.generate(31, settings("bridge_once"), 3, 4)
    assert first == expected
    first["train"][0]["input"][0][0] = 9
    first["test"][0]["output"][0][0] = 9
    assert adapter.generate(31, settings("bridge_once"), 3, 4) == expected


def test_public_projection_has_single_query_and_opaque_content_id(adapter):
    from reviewer_support import public_challenge_bytes, public_challenge_id
    episode = adapter.generate(17, settings("bridge_once"), 3, 4)
    view = {"train": episode["train"], "test": episode["test"][:1]}
    raw = public_challenge_bytes(view)
    public = json.loads(raw)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
    assert raw == public_challenge_bytes(adapter.generate(17, settings("bridge_once"), 3, 1))
    assert public_challenge_id(view) == hashlib.sha256(raw).hexdigest()
    view["settings"] = {"secret": 812}
    view["program_solution"] = "secret"
    view["test"][0]["output"] = [[0]]
    assert public_challenge_bytes(view) == raw

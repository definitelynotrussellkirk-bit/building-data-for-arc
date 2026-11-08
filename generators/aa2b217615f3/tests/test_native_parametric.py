"""Focused contract and teaching tests for aa2b217615f3 parametric stacking."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
PARAM = HOME / "workspace/parametric"
RUNTIME = ROOT / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load(PARAM / "adapter.py", "_aa2b217615f3_parametric_test")


@pytest.fixture(scope="module")
def generator():
    return _load(HOME / "generator.py", "_aa2b217615f3_generator_test")


def _canonical() -> str:
    from arcpuzzles import Catalog
    row = Catalog(ROOT).get(HOME.name)
    programs = {v["program_solution"] for v in row["variants"] if isinstance(v.get("program_solution"), str)}
    assert len(programs) == 1
    return next(iter(programs))


def _fp(grid):
    return tuple(tuple(row) for row in grid)


def test_native_contract_and_exact_default(adapter):
    contract = json.loads((PARAM / "promotion.json").read_text())
    assert contract["parameters"] == {"stack_order": ["near_first", "far_first"]}
    assert contract["default"] == {"stack_order": "near_first"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 2
    assert adapter.program({"stack_order": "near_first"}) == _canonical()
    assert (PARAM / "canonical.rkt").read_text() == _canonical()
    assert adapter.program({"stack_order": "far_first"}) != _canonical()


@pytest.mark.parametrize("bad", [None, {}, {"stack_order": "nearest"}, {"stack_order": 1}, {"stack_order": "near_first", "x": 1}])
def test_bad_settings_rejected(adapter, bad):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(bad)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, bad, 2, 4)


@pytest.mark.parametrize("seed", [True, -1, 2**63, 1.0, "0"])
def test_seed_bounds_are_strict(adapter, seed):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"stack_order": "near_first"}, 2, 4)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (2, 0), (2, 5), (True, 4), (2.0, 4), (2, True)])
def test_count_bounds_are_strict(adapter, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"stack_order": "near_first"}, demos, queries)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_prefix_stable_matched_distinct_inputs(adapter, seed):
    near_short = adapter.generate(seed, {"stack_order": "near_first"}, 2, 1)
    near_long = adapter.generate(seed, {"stack_order": "near_first"}, 6, 4)
    far_long = adapter.generate(seed, {"stack_order": "far_first"}, 6, 4)
    assert near_short["train"] == near_long["train"][:2]
    assert near_short["test"] == near_long["test"][:1]
    near_inputs = [p["input"] for s in ("train", "test") for p in near_long[s]]
    far_inputs = [p["input"] for s in ("train", "test") for p in far_long[s]]
    assert near_inputs == far_inputs
    assert len({_fp(g) for g in near_inputs}) == 10
    assert all(a["output"] != b["output"] for a, b in zip(near_long["train"][:2], far_long["train"][:2]))


def test_large_query_is_substantive_and_order_sensitive(adapter):
    grid = adapter.sample_input(17, "test", 3)
    assert len(grid) == 30 and len(grid[0]) == 30
    nonzero = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    assert len(nonzero) >= 40
    assert {int(r >= 15) for r, _ in nonzero} == {0, 1}
    assert {int(c >= 15) for _, c in nonzero} == {0, 1}
    assert adapter.has_stacking_witness(grid)
    assert adapter.transform(grid, {"stack_order": "near_first"}) != adapter.transform(grid, {"stack_order": "far_first"})


def test_base_generator_repairs_independent_slide_shortcut(generator):
    for difficulty in (None, "medium", "easy", "hard"):
        for index in range(24):
            grid = generator.generate(700 + index, index, difficulty=difficulty)
            assert generator.self_check(grid) == []
            assert generator.has_stacking_witness(grid)


def test_rng_and_return_values_are_isolated(adapter):
    random.seed(41)
    before = random.getstate()
    first = adapter.generate(31, {"stack_order": "far_first"}, 3, 4)
    assert random.getstate() == before
    expected = adapter.generate(31, {"stack_order": "far_first"}, 3, 4)
    assert first == expected
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(31, {"stack_order": "far_first"}, 3, 4) == expected


def test_public_projection_is_single_query_and_private_invariant(adapter):
    from reviewer_support import public_challenge_bytes, public_challenge_id
    episode = adapter.generate(17, {"stack_order": "far_first"}, 3, 4)
    view = {"train": copy.deepcopy(episode["train"]), "test": [copy.deepcopy(episode["test"][0])]}
    raw = public_challenge_bytes(view)
    public = json.loads(raw)
    assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
    assert raw == public_challenge_bytes(adapter.generate(17, {"stack_order": "far_first"}, 3, 1))
    assert public_challenge_id(view) == hashlib.sha256(raw).hexdigest()
    view["settings"] = {"secret": 1}
    view["program_solution"] = "secret"
    view["test"][0]["output"] = [[0]]
    assert public_challenge_bytes(view) == raw


def test_programs_parse(adapter):
    from puzzle_generators.rule_wrap import wrap_rule
    for setting in ({"stack_order": "near_first"}, {"stack_order": "far_first"}):
        assert wrap_rule(adapter.program(setting)).strip()

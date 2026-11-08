"""Contract, causal-teaching, and robustness tests for a53fa114c4a9."""
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
    return _load(PARAM / "adapter.py", "_a53fa114c4a9_parametric_test")


@pytest.fixture(scope="module")
def generator():
    return _load(HOME / "generator.py", "_a53fa114c4a9_generator_test")


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
    assert contract["parameters"] == {"column_mode": ["explicit_mask", "merged_component"]}
    assert contract["default"] == {"column_mode": "explicit_mask"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 2
    assert adapter.program({"column_mode": "explicit_mask"}) == _canonical()
    assert (PARAM / "canonical.rkt").read_text() == _canonical()
    assert adapter.program({"column_mode": "merged_component"}) != _canonical()


@pytest.mark.parametrize("bad", [None, {}, {"column_mode": "largest"}, {"column_mode": 1}, {"column_mode": "explicit_mask", "x": 1}])
def test_bad_settings_rejected(adapter, bad):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(bad)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, bad, 2, 4)


@pytest.mark.parametrize("seed", [True, -1, 2**63, 1.0, "0"])
def test_seed_bounds_are_strict(adapter, seed):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(seed, {"column_mode": "explicit_mask"}, 2, 4)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (2, 0), (2, 5), (True, 4), (2.0, 4), (2, True)])
def test_count_bounds_are_strict(adapter, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, {"column_mode": "explicit_mask"}, demos, queries)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_prefix_stable_matched_distinct_inputs(adapter, seed):
    explicit_short = adapter.generate(seed, {"column_mode": "explicit_mask"}, 2, 1)
    explicit_long = adapter.generate(seed, {"column_mode": "explicit_mask"}, 6, 4)
    merged_long = adapter.generate(seed, {"column_mode": "merged_component"}, 6, 4)
    assert explicit_short["train"] == explicit_long["train"][:2]
    assert explicit_short["test"] == explicit_long["test"][:1]
    explicit_inputs = [p["input"] for s in ("train", "test") for p in explicit_long[s]]
    merged_inputs = [p["input"] for s in ("train", "test") for p in merged_long[s]]
    assert explicit_inputs == merged_inputs
    assert len({_fp(g) for g in explicit_inputs}) == 10
    assert all(a["output"] != b["output"] for a, b in zip(explicit_long["train"][:2], merged_long["train"][:2]))


@pytest.mark.parametrize("seed", range(16))
def test_first_two_demos_teach_recolor_before_component_selection(adapter, seed):
    episode = adapter.generate(seed, {"column_mode": "merged_component"}, 2, 4)
    for pair in episode["train"]:
        grid = pair["input"]
        recolored = adapter.recolor_body(grid)
        raw = [row[:] for row in grid[3:]]
        keep = adapter.keep_columns(grid)
        recolored_winner = adapter.largest_component_columns(recolored)
        raw_winner = adapter.largest_component_columns(raw)
        assert recolored_winner != raw_winner
        assert set(recolored_winner) & set(keep)
        assert set(raw_winner) & set(keep)
        assert adapter.transform(grid, {"column_mode": "merged_component"}) != adapter.transform_with_raw_component(grid)


def test_large_query_is_substantive_and_causal(adapter):
    grid = adapter.sample_input(17, "test", 3)
    assert len(grid) == 30 and len(grid[0]) == 30
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    assert len(nonzero) >= 110
    assert {int(r >= 15) for r, _ in nonzero} == {0, 1}
    assert {int(c >= 15) for _, c in nonzero} == {0, 1}
    assert adapter.transform(grid, {"column_mode": "explicit_mask"}) != adapter.transform(grid, {"column_mode": "merged_component"})
    assert adapter.transform(grid, {"column_mode": "merged_component"}) != adapter.transform_with_raw_component(grid)


def test_base_generator_advertises_only_reachable_pair_counts(generator):
    assert generator.VERSION == "2.1.2"
    assert generator.AXES["n_pairs"]["valid"] == "2..4"
    for difficulty in (None, "medium", "easy", "hard"):
        for index in range(32):
            grid = generator.generate(900 + index, index, difficulty=difficulty)
            assert generator.self_check(grid) == []
            pair_count = sum(value != 0 for value in grid[0])
            assert 2 <= pair_count <= 4


def test_rng_and_return_values_are_isolated(adapter):
    random.seed(41)
    before = random.getstate()
    first = adapter.generate(31, {"column_mode": "merged_component"}, 3, 4)
    assert random.getstate() == before
    expected = adapter.generate(31, {"column_mode": "merged_component"}, 3, 4)
    assert first == expected
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(31, {"column_mode": "merged_component"}, 3, 4) == expected


def test_public_projection_is_single_query_and_private_invariant(adapter):
    from reviewer_support import public_challenge_bytes, public_challenge_id
    episode = adapter.generate(17, {"column_mode": "merged_component"}, 3, 4)
    view = {"train": copy.deepcopy(episode["train"]), "test": [copy.deepcopy(episode["test"][0])]}
    raw = public_challenge_bytes(view)
    public = json.loads(raw)
    assert len(public["test"]) == 1 and set(public["test"][0]) == {"input"}
    assert raw == public_challenge_bytes(adapter.generate(17, {"column_mode": "merged_component"}, 3, 1))
    assert public_challenge_id(view) == hashlib.sha256(raw).hexdigest()
    view["settings"] = {"secret": 1}
    view["program_solution"] = "secret"
    view["test"][0]["output"] = [[0]]
    assert public_challenge_bytes(view) == raw


def test_programs_parse(adapter):
    from puzzle_generators.rule_wrap import wrap_rule
    for setting in ({"column_mode": "explicit_mask"}, {"column_mode": "merged_component"}):
        assert wrap_rule(adapter.program(setting)).strip()

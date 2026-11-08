"""Contract tests for the native 78fd2bcdbb99 parametric family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_ID = "78fd2bcdbb99"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"


def _load():
    assert SOURCE.is_file(), "task-local near-symmetry prototype is missing"
    spec = importlib.util.spec_from_file_location("parametric_78fd2bcdbb99", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load()


def _canonical_program() -> str:
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    matches = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            matches.append(row["program_solution"])
    assert matches and len(set(matches)) == 1
    return matches[0]


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_alternate_is_distinct(proto) -> None:
    canonical = _canonical_program()
    assert proto.program({"repair": "fill"}) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "038edcc7127447e984bafa0c0cba02a66e7f43f9b838edcfeb56ddd824e8fc1f"
    )
    alternate = proto.program({"repair": "erase"})
    assert alternate != canonical
    assert "(!= value 0)" in alternate
    assert "(= mirror 0)" in alternate


def test_matched_inputs_identify_setting_and_cover_axes_palette_and_30x30(proto) -> None:
    fill = proto.generate(17, {"repair": "fill"}, demos=3, queries=4)
    erase = proto.generate(17, {"repair": "erase"}, demos=3, queries=4)
    assert _inputs(fill) == _inputs(erase)
    assert len(fill["train"]) == len(erase["train"]) == 3
    assert len(fill["test"]) == len(erase["test"]) == 4
    assert len({proto.digest(grid) for grid in _inputs(fill)}) == 7
    assert all(a["output"] != b["output"] for a, b in zip(fill["train"], erase["train"]))
    facts = [proto.semantic_observables(pair["input"]) for pair in fill["train"]]
    assert {row["selected_axis"] for row in facts} == {"lr", "ud"}
    assert any(row["palette_size"] >= 3 for row in facts)
    assert all(row["fillable_count"] >= 2 for row in facts)
    stress = fill["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    stress_facts = proto.semantic_observables(stress)
    assert stress_facts["nonzero_count"] >= 100
    assert stress_facts["bbox"] == [0, 0, 29, 29]


@pytest.mark.parametrize("demos", [2, 6])
def test_supported_demo_boundaries_return_four_queries(proto, demos: int) -> None:
    episode = proto.generate(5, {"repair": "fill"}, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4


def test_demo_and_query_prefixes_are_count_independent(proto) -> None:
    small = proto.generate(13, {"repair": "fill"}, demos=2, queries=1)
    large = proto.generate(13, {"repair": "fill"}, demos=6, queries=4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    same_demos_more_queries = proto.generate(13, {"repair": "fill"}, demos=2, queries=4)
    assert small["train"] == same_demos_more_queries["train"]
    assert small["test"][0] == same_demos_more_queries["test"][0]


def test_determinism_freshness_global_rng_and_setting_independence(proto) -> None:
    random.seed(20261026)
    state = random.getstate()
    first = proto.generate(4242, {"repair": "fill"}, demos=3, queries=4)
    second = proto.generate(4242, {"repair": "fill"}, demos=3, queries=4)
    rival = proto.generate(4242, {"repair": "erase"}, demos=3, queries=4)
    assert first == second
    assert first is not second
    assert _inputs(first) == _inputs(rival)
    assert random.getstate() == state
    first["train"][0]["input"][0][0] = (first["train"][0]["input"][0][0] + 1) % 10
    assert first != second
    assert proto.generate(4242, {"repair": "fill"}, demos=3, queries=4) == second


def test_transform_is_pure_and_fill_erase_are_opposite_repairs(proto) -> None:
    grid = proto.generate(2, {"repair": "fill"}, demos=2, queries=1)["train"][0]["input"]
    original = copy.deepcopy(grid)
    fill = proto.transform(grid, {"repair": "fill"})
    erase = proto.transform(grid, {"repair": "erase"})
    assert grid == original
    assert fill != erase
    assert proto.semantic_observables(fill)["fillable_count"] == 0
    assert proto.semantic_observables(erase)["fillable_count"] == 0
    assert proto.selected_axis(fill) == proto.selected_axis(erase)


def test_invalid_contracts_fail_closed_without_bool_aliases(proto) -> None:
    for bad in ({}, {"repair": "fill", "extra": 1}, {"repair": "blend"}, None):
        with pytest.raises(ValueError):
            proto.program(bad)
    for request in (
        {"demos": 1, "queries": 4},
        {"demos": 7, "queries": 4},
        {"demos": 3, "queries": 0},
        {"demos": 3, "queries": 5},
        {"demos": True, "queries": 4},
        {"demos": 3, "queries": False},
    ):
        with pytest.raises(ValueError):
            proto.generate(0, {"repair": "fill"}, **request)
    with pytest.raises(ValueError):
        proto.generate(True, {"repair": "fill"}, demos=3, queries=4)
    with pytest.raises(ValueError):
        proto.generate(0, {"repair": "blend"}, demos=3, queries=4)


def test_probe_declares_full_two_setting_two_seed_matrix() -> None:
    source = ROOT / f"generators/{TASK_ID}/workspace/parametric/probe.py"
    assert source.is_file(), "protected-worker probe is missing"
    spec = importlib.util.spec_from_file_location("probe_78fd2bcdbb99", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    jobs = module.qualification_jobs()
    assert len(jobs) == 4
    assert {row["seed"] for row in jobs} == {0, 17}
    assert {row["settings"]["repair"] for row in jobs} == {"fill", "erase"}
    assert {(row["demos"], row["queries"]) for row in jobs} == {(3, 4)}

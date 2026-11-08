"""Native parametric payload-policy contract for 25c140f9307d."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

for parent in Path(__file__).resolve().parents:
    support = next(
        (
            candidate
            for candidate in (
                parent / "reviewer_support.py",
                parent / "shared/runtime/reviewer_support.py",
            )
            if candidate.is_file()
        ),
        None,
    )
    if support is not None:
        sys.path.insert(0, str(support.parent))
        break

from reviewer_support import find_root
from arcpuzzles.catalog import Catalog

TASK_ID = "25c140f9307d"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
PROMOTION = PARAMETRIC / "promotion.json"
ADAPTER = PARAMETRIC / "adapter.py"


def _module(path: Path, label: str):
    assert path.is_file(), f"missing native parametric {label}: {path}"
    name = f"_test_{label}_{TASK_ID}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    catalog = Catalog(ROOT)
    row = catalog.describe(TASK_ID)
    authority = row.get("rule_task_id", TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in catalog._variants()[authority]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _pairs(episode: dict) -> list[dict]:
    return [*episode["train"], *episode["test"]]


def _assert_grid(grid: list[list[int]]) -> None:
    assert 1 <= len(grid) <= 30
    assert 1 <= len(grid[0]) <= 30
    assert all(len(row) == len(grid[0]) for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)


def test_native_contract_declares_two_payload_policies_and_fixed_four_queries():
    assert PROMOTION.is_file(), f"missing native promotion contract: {PROMOTION}"
    contract = json.loads(PROMOTION.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"payload_policy": ["preserve", "swap"]},
        "default": {"payload_policy": "preserve"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }


def test_default_program_is_exact_canonical_bytes_and_alternative_is_distinct():
    adapter = _module(ADAPTER, "adapter")
    canonical = _canonical_program()
    assert adapter.program({"payload_policy": "preserve"}) == canonical
    alternate = adapter.program({"payload_policy": "swap"})
    assert isinstance(alternate, str) and alternate.strip()
    assert alternate != canonical
    with pytest.raises(ValueError, match="payload_policy"):
        adapter.program({"payload_policy": "unknown"})


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_generation_honors_independent_demo_count_and_exact_four_queries(demos):
    adapter = _module(ADAPTER, "adapter")
    episode = adapter.generate(20261024 + demos, {"payload_policy": "preserve"}, demos, 4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program({"payload_policy": "preserve"})
    serialized = []
    for pair in _pairs(episode):
        assert set(pair) >= {"input", "output"}
        _assert_grid(pair["input"])
        _assert_grid(pair["output"])
        serialized.append(json.dumps(pair["input"], separators=(",", ":")))
    assert len(serialized) == len(set(serialized))


@pytest.mark.parametrize(
    ("demos", "queries", "message"),
    [(1, 4, "demos"), (7, 4, "demos"), (2, 3, "queries"), (2, 5, "queries"), (True, 4, "demos")],
)
def test_generation_rejects_counts_outside_the_admitted_contract(demos, queries, message):
    adapter = _module(ADAPTER, "adapter")
    with pytest.raises((TypeError, ValueError), match=message):
        adapter.generate(1, {"payload_policy": "preserve"}, demos, queries)


def test_settings_share_identical_inputs_but_change_every_label():
    adapter = _module(ADAPTER, "adapter")
    preserve = adapter.generate(77123, {"payload_policy": "preserve"}, 3, 4)
    swap = adapter.generate(77123, {"payload_policy": "swap"}, 3, 4)
    preserve_pairs = _pairs(preserve)
    swap_pairs = _pairs(swap)
    assert [pair["input"] for pair in preserve_pairs] == [pair["input"] for pair in swap_pairs]
    assert all(a["output"] != b["output"] for a, b in zip(preserve_pairs, swap_pairs))
    assert preserve["program_solution"] != swap["program_solution"]


def test_generation_is_deterministic_and_returns_fresh_nested_grids():
    adapter = _module(ADAPTER, "adapter")
    first = adapter.generate(8128, {"payload_policy": "swap"}, 3, 4)
    second = adapter.generate(8128, {"payload_policy": "swap"}, 3, 4)
    assert first == second
    assert first is not second
    assert first["train"][0]["input"] is not second["train"][0]["input"]
    untouched = copy.deepcopy(second)
    first["train"][0]["input"][0][0] = 9
    first["train"][0]["output"][0][0] = 9
    assert second == untouched


def test_each_episode_contains_a_substantive_exact_30x30_stress_scene():
    adapter = _module(ADAPTER, "adapter")
    episode = adapter.generate(303030, {"payload_policy": "preserve"}, 2, 4)
    stress = [
        pair
        for pair in _pairs(episode)
        if len(pair["input"]) == 30 and len(pair["input"][0]) == 30
    ]
    assert len(stress) == 1
    pair = stress[0]
    assert (len(pair["output"]), len(pair["output"][0])) == (22, 22)
    # The plate is genuinely enlarged and four detached key objects touch the
    # right boundary; this is not a small puzzle surrounded by zero padding.
    assert sum(cell != 0 for row in pair["output"] for cell in row) > 430
    assert any(row[-1] != 0 for row in pair["input"])
    assert sum(cell == 0 for row in pair["output"] for cell in row) == 0

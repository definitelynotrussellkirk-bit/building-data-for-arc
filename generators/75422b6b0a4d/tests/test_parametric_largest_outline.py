"""Focused contracts for the native flood-then-outline parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import find_root

TASK_ID = "75422b6b0a4d"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
FAMILY_PATH = PARAMETRIC / "family.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
CONTRACT_PATH = PARAMETRIC / "promotion.json"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing requested parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    return _load(FAMILY_PATH, "task_75422b6b0a4d_parametric_family_test")


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _digest(grid):
    return json.dumps(grid, separators=(",", ":"))


def test_program_contract_preserves_exact_canonical_default(family):
    variants = Catalog(ROOT)._variants()[TASK_ID]
    canonical = {row["program_solution"] for row in variants}
    assert len(canonical) == 1
    assert family.PARAMETER_NAME == "finish"
    assert family.SETTINGS == ("flood", "outline_largest")
    assert family.DEFAULT_SETTINGS == {"finish": "flood"}
    programs = {setting: family.program({"finish": setting}) for setting in family.SETTINGS}
    assert {programs["flood"]} == canonical
    assert programs["outline_largest"] != programs["flood"]
    assert "neighbor-count-4 filled" in programs["outline_largest"]


@pytest.mark.parametrize("demos", range(2, 7))
def test_counts_are_exact_setting_neutral_and_prefix_stable(family, demos):
    canonical = family.generate(17, {"finish": "flood"}, demos=demos, queries=4)
    alternate = family.generate(17, {"finish": "outline_largest"}, demos=demos, queries=4)
    assert len(canonical["train"]) == demos
    assert len(canonical["test"]) == 4
    assert _inputs(canonical) == _inputs(alternate)
    assert len({_digest(grid) for grid in _inputs(canonical)}) == demos + 4
    assert canonical["program_solution"] == family.program({"finish": "flood"})
    assert alternate["program_solution"] == family.program({"finish": "outline_largest"})

    shortest = family.generate(17, {"finish": "flood"}, demos=2, queries=1)
    assert canonical["train"][:2] == shortest["train"]
    assert canonical["test"][:1] == shortest["test"]


@pytest.mark.parametrize("setting", ("flood", "outline_largest"))
def test_two_demos_identify_setting_and_refute_declared_shortcuts(family, setting):
    episode = family.generate(31, {"finish": setting}, demos=2, queries=4)
    assert family.finite_program_survivors(episode["train"]) == [setting]
    reports = family.audit_shortcuts(episode["train"], selected=setting)
    assert reports
    assert all(report["refuted"] for report in reports), reports
    assert all(report["mismatching_demo_indices"] for report in reports), reports


@pytest.mark.parametrize("seed", (0, 17, 2**32 + 9))
def test_outline_is_flood_plus_boundary_of_unique_largest_room(family, seed):
    episode = family.generate(seed, {"finish": "outline_largest"}, demos=2, queries=4)
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        flood = family.transform(grid, "flood")
        outlined = pair["output"]
        chosen = family.selected_room(grid, "largest")
        assert chosen["area"] > max(
            room["area"] for room in family.room_records(grid) if room != chosen
        )
        boundary = set(map(tuple, family.boundary_cells(grid, chosen["cells"], outer=True)))
        changed = {
            (row, col)
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if flood[row][col] != outlined[row][col]
        }
        assert changed == boundary
        assert changed
        assert all(outlined[row][col] == chosen["color"] for row, col in changed)

    # The minimum lesson is constructed to defeat "top-left" and "color 1" selectors.
    for pair in episode["train"]:
        rooms = family.room_records(pair["input"])
        chosen = family.selected_room(pair["input"], "largest")
        assert chosen != rooms[0]
        assert chosen["color"] != 1


def test_flood_minimum_lesson_refutes_seed_touch_outline_regression(family):
    episode = family.generate(8, {"finish": "flood"}, demos=2, queries=1)
    reports = family.audit_shortcuts(episode["train"], selected="flood")
    seed_touch = next(row for row in reports if row["rival"] == "outline_seed_touch_only")
    assert seed_touch["refuted"] is True
    assert seed_touch["mismatching_demo_indices"]


def test_four_queries_cover_real_large_fields_and_substantive_30x30(family):
    episode = family.generate(101, {"finish": "outline_largest"}, demos=3, queries=4)
    sizes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert sizes == [(14, 16), (20, 23), (26, 28), (30, 30)]
    grid = episode["test"][-1]["input"]
    rooms = family.room_records(grid)
    assert len(rooms) in (3, 4)
    assert sum(room["area"] for room in rooms) >= 650
    assert len(family.boundary_cells(grid, family.selected_room(grid, "largest")["cells"], outer=True)) >= 30
    assert family.transform(grid, "flood") != family.transform(grid, "outline_largest")


@pytest.mark.parametrize(
    "seed,settings,demos,queries,error",
    [
        (True, {"finish": "flood"}, 2, 4, ValueError),
        (-1, {"finish": "flood"}, 2, 4, ValueError),
        (0, {"finish": "flood"}, 1, 4, ValueError),
        (0, {"finish": "flood"}, 7, 4, ValueError),
        (0, {"finish": "flood"}, 2, 0, ValueError),
        (0, {"finish": "flood"}, 2, 5, ValueError),
        (0, {"finish": "flood"}, 2.0, 4, ValueError),
        (0, {"finish": "other"}, 2, 4, ValueError),
        (0, {"mode": "flood"}, 2, 4, ValueError),
        (0, {"finish": "flood", "extra": 1}, 2, 4, ValueError),
    ],
)
def test_invalid_requests_fail_without_partial_episode(family, seed, settings, demos, queries, error):
    with pytest.raises(error):
        family.generate(seed, settings, demos, queries)


def test_adapter_uses_exact_adjacent_family_module(monkeypatch):
    foreign = types.ModuleType("family")
    foreign.program = lambda settings: "foreign"
    foreign.generate = lambda *args, **kwargs: {"foreign": True}
    monkeypatch.setitem(sys.modules, "family", foreign)
    adapter = _load(ADAPTER_PATH, "task_75422b6b0a4d_parametric_adapter_test")
    assert adapter.program({"finish": "flood"}) != "foreign"
    assert len(adapter.generate(7, {"finish": "flood"}, 2, 1)["train"]) == 2


def test_native_worker_executes_both_settings_through_protected_racket():
    assert CONTRACT_PATH.is_file(), "missing promotion contract"
    contract = json.loads(CONTRACT_PATH.read_text())
    jobs = [
        {"seed": 0, "settings": {"finish": "flood"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"finish": "outline_largest"}, "demos": 2, "queries": 4},
    ]
    result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert result["racket_evaluations"] == 16
    assert [row["survivors"] for row in result["checks"]] == [
        [{"finish": "flood"}],
        [{"finish": "outline_largest"}],
    ]

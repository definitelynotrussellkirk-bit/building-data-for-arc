from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes

TASK = "e245314f96d8"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK
PARAMETRIC = HOME / "workspace" / "parametric"
SETTINGS = (
    {"contact_neighborhood": "cardinal"},
    {"contact_neighborhood": "king"},
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _adapter():
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "native contact-neighborhood adapter has not been implemented"
    return _load(f"review_{TASK}_contact_adapter", path)


def _canonical_program() -> str:
    from arcpuzzles.catalog import Catalog

    programs = {
        variant["program_solution"]
        for variant in Catalog(ROOT)._variants()[TASK]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_and_king_program_is_distinct():
    adapter = _adapter()
    assert adapter.program(SETTINGS[0]) == _canonical_program()
    assert adapter.program(SETTINGS[1]) != _canonical_program()
    assert adapter.program(SETTINGS[1]).startswith("(rule!")


@pytest.mark.parametrize("demos", (2, 3, 6))
@pytest.mark.parametrize("queries", (1, 4))
def test_counts_prefixes_matched_inputs_distinctness_and_teaching(demos, queries):
    adapter = _adapter()
    for seed in (0, 17, 91):
        full = adapter.generate(seed, SETTINGS[0], demos=6, queries=4)
        episodes = [adapter.generate(seed, setting, demos=demos, queries=queries) for setting in SETTINGS]
        assert _inputs(episodes[0]) == _inputs(episodes[1])
        assert episodes[0]["train"] == full["train"][:demos]
        assert episodes[0]["test"] == full["test"][:queries]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(episodes[0])}) == demos + queries
        for setting, episode in zip(SETTINGS, episodes, strict=True):
            assert len(episode["train"]) == demos and len(episode["test"]) == queries
            assert episode["program_solution"] == adapter.program(setting)
            assert adapter.audit_episode(episode, setting["contact_neighborhood"]) == []
        assert all(
            left["output"] != right["output"]
            for left, right in zip(episodes[0]["train"][:2], episodes[1]["train"][:2], strict=True)
        )


def test_graph_degree_intermediate_is_input_dependent_and_consumed_by_painting():
    adapter = _adapter()
    grid = adapter.generate(7, SETTINGS[1], demos=2, queries=4)["test"][0]["input"]
    cardinal = adapter.dependency_intermediate(grid, SETTINGS[0])
    king = adapter.dependency_intermediate(grid, SETTINGS[1])
    assert cardinal["objects"] == king["objects"]
    assert cardinal["degrees"] != king["degrees"]
    assert adapter.solve_from_intermediate(grid, king) == adapter.solve(grid, SETTINGS[1])
    wrong = copy.deepcopy(king)
    wrong["degrees"] = cardinal["degrees"]
    assert adapter.solve_from_intermediate(grid, wrong) != adapter.solve(grid, SETTINGS[1])


def test_stress_query_is_substantive_30x30_and_hits_every_boundary():
    adapter = _adapter()
    grid = adapter.generate(2**63 - 1, SETTINGS[1], demos=2, queries=4)["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 350
    assert any(grid[0][col] for col in range(30))
    assert any(grid[-1][col] for col in range(30))
    assert any(row[0] for row in grid)
    assert any(row[-1] for row in grid)
    cardinal = adapter.dependency_intermediate(grid, SETTINGS[0])
    king = adapter.dependency_intermediate(grid, SETTINGS[1])
    assert len(cardinal["objects"]) >= 80
    assert cardinal["degrees"] != king["degrees"]


def test_first_turn_bytes_hide_setting_program_answers_and_future_queries():
    adapter = _adapter()
    episode = adapter.generate(23, SETTINGS[1], demos=3, queries=4)
    encoded = adapter.first_turn_bytes(episode)
    one = adapter.generate(23, SETTINGS[1], demos=3, queries=1)
    assert encoded == adapter.first_turn_bytes(one)
    assert encoded == public_challenge_bytes({"train": episode["train"], "test": episode["test"][:1]})

    changed = copy.deepcopy(episode)
    changed["settings"] = {"contact_neighborhood": "PRIVATE"}
    changed["program_solution"] = "PRIVATE"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    changed["test"][1:] = [{"input": [[9]], "output": [[1]]}]
    assert adapter.first_turn_bytes(changed) == encoded


def test_protected_racket_matches_python_for_both_settings():
    _adapter()
    from arcpuzzles.parametric_worker import evaluate_contract

    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    jobs = [
        {"seed": 17, "settings": setting, "demos": 2, "queries": 4}
        for setting in SETTINGS
    ]
    result = evaluate_contract(ROOT, TASK, contract, jobs)
    assert result["racket"]["backend"] == "racket"
    assert result["racket"]["protected"] is True
    assert [check["survivors"] for check in result["checks"]] == [
        [job["settings"]] for job in jobs
    ]
    assert [check["label_count"] for check in result["checks"]] == [6, 6]


@pytest.mark.parametrize(
    "payload",
    [
        {"seed": True, "settings": SETTINGS[0], "demos": 2, "queries": 4},
        {"seed": -1, "settings": SETTINGS[0], "demos": 2, "queries": 4},
        {"seed": 2**63, "settings": SETTINGS[0], "demos": 2, "queries": 4},
        {"seed": 0, "settings": None, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"contact_neighborhood": "bogus"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"contact_neighborhood": "cardinal", "x": 1}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": SETTINGS[0], "demos": 1, "queries": 4},
        {"seed": 0, "settings": SETTINGS[0], "demos": 7, "queries": 4},
        {"seed": 0, "settings": SETTINGS[0], "demos": 2, "queries": 0},
        {"seed": 0, "settings": SETTINGS[0], "demos": 2, "queries": 5},
    ],
)
def test_invalid_requests_fail_closed(payload):
    adapter = _adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(**payload)

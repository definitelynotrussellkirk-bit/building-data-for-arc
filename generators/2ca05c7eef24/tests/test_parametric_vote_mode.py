from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.catalog import Catalog
from reviewer_support import find_root, public_challenge_bytes

TASK_ID = "2ca05c7eef24"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str):
    path = PARAMETRIC / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_{name}_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical() -> str:
    catalog = Catalog(ROOT)
    row = catalog.describe(TASK_ID)
    programs = {
        item["program_solution"]
        for item in catalog._variants()[row.get("rule_task_id", TASK_ID)]
        if isinstance(item.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _settings(value: str) -> dict[str, str]:
    return {"finish_rule": value}


def test_default_is_exact_canonical_and_composed_rule_is_distinct() -> None:
    p = _load("prototype")
    assert p.program(_settings("vote_only")) == _canonical()
    assert (PARAMETRIC / "canonical.rkt").read_text() == _canonical()
    assert p.program(_settings("vote_then_keep_output_mode")) != _canonical()


def test_supported_counts_are_matched_distinct_and_prefix_stable() -> None:
    p = _load("prototype")
    for demos in range(2, 7):
        for queries in range(1, 5):
            a = p.generate(2000 + demos * 10 + queries, _settings("vote_only"), demos, queries)
            b = p.generate(2000 + demos * 10 + queries, _settings("vote_then_keep_output_mode"), demos, queries)
            assert len(a["train"]) == len(b["train"]) == demos
            assert len(a["test"]) == len(b["test"]) == queries
            assert [x["input"] for x in a["train"] + a["test"]] == [x["input"] for x in b["train"] + b["test"]]
            assert len({json.dumps(x["input"]) for x in a["train"] + a["test"]}) == demos + queries
            assert p.teaching_check(a)["ok"] is True
            assert p.teaching_check(b)["ok"] is True
    full = p.generate(88, _settings("vote_then_keep_output_mode"), 6, 4)
    short = p.generate(88, _settings("vote_then_keep_output_mode"), 2, 1)
    assert short["train"] == full["train"][:2]
    assert short["test"] == full["test"][:1]


def test_stage_b_uses_voted_output_not_raw_global_frequency() -> None:
    p = _load("prototype")
    for seed in (0, 17, 91):
        plain = p.generate(seed, _settings("vote_only"), 2, 4)
        composed = p.generate(seed, _settings("vote_then_keep_output_mode"), 2, 4)
        for a, b in zip(plain["train"] + plain["test"], composed["train"] + composed["test"]):
            assert a["input"] == b["input"]
            stage = p.vote_grid(a["input"])
            facts = p.analyze_input(a["input"])
            assert a["output"] == stage
            assert b["output"] == p.finish_python(a["input"], _settings("vote_then_keep_output_mode"))
            assert facts["output_mode"] != facts["raw_input_mode"]
            assert b["output"] != a["output"]
            assert b["output"] != p.keep_color(stage, facts["raw_input_mode"])


def test_largest_query_is_lawful_30x29_and_touches_all_boundaries() -> None:
    p = _load("prototype")
    episode = p.generate(0, _settings("vote_then_keep_output_mode"), 3, 4)
    grid = episode["test"][3]["input"]
    out = episode["test"][3]["output"]
    assert (len(grid), len(grid[0])) == (30, 29)
    assert any(v not in (0, 5) for v in grid[0])
    assert any(v not in (0, 5) for v in grid[-1])
    assert any(row[0] not in (0, 5) for row in grid)
    assert any(row[-1] not in (0, 5) for row in grid)
    assert sum(v not in (0, 5) for row in grid for v in row) >= 300
    assert sum(v != 0 for row in out for v in row) >= 50


def test_public_turn_masks_answers_settings_program_and_future_queries() -> None:
    p = _load("prototype")
    episode = p.generate(7, _settings("vote_then_keep_output_mode"), 3, 4)
    first = p.public_turn(episode, 0)
    last = p.public_turn(episode, 3)
    assert first["train"] == last["train"] == episode["train"]
    assert first["test"] == [{"input": episode["test"][0]["input"]}]
    assert last["test"] == [{"input": episode["test"][3]["input"]}]
    payload = public_challenge_bytes(first)
    for secret in (b"finish_rule", b"vote_only", b"output_mode", b"settings", b"program_solution", b"metadata"):
        assert secret not in payload


def test_generation_is_fresh_and_strictly_validates_typed_requests() -> None:
    p = _load("prototype")
    a = p.generate(9, _settings("vote_only"), 2, 4)
    b = p.generate(9, _settings("vote_only"), 2, 4)
    assert a == b and a is not b
    frozen = copy.deepcopy(b)
    a["train"][0]["input"][0][0] = 9
    assert b == frozen
    for settings in ({}, {"finish_rule": "bad"}, {"finish_rule": 1}, {"finish_rule": "vote_only", "x": 1}):
        with pytest.raises(ValueError):
            p.generate(0, settings, 2, 4)
    for demos, queries in ((True, 4), (1, 4), (7, 4), (2, True), (2, 0), (2, 5)):
        with pytest.raises(ValueError):
            p.generate(0, _settings("vote_only"), demos, queries)

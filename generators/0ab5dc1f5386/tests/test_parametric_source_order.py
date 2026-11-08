"""Native source-order family for size-matched frame insertion."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "0ab5dc1f5386"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
SETTINGS = (
    {"source_order": "row_major"},
    {"source_order": "column_major"},
)


def _load_adapter():
    path = HOME / "adapter.py"
    assert path.is_file(), "native source-order adapter is missing"
    name = "_tested_source_order_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for row in map(json.loads, handle):
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_byte_exact_and_contract_is_bounded():
    adapter = _load_adapter()
    canonical = _canonical_program()
    assert adapter.program(SETTINGS[0]) == canonical
    assert adapter.program(SETTINGS[1]) != canonical
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["parameters"] == {"source_order": ["row_major", "column_major"]}
    assert contract["default"] == SETTINGS[0]
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3


@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (3, 4), (6, 1), (6, 4)])
def test_counts_inputs_prefixes_outputs_and_uniqueness(demos, queries):
    adapter = _load_adapter()
    episodes = [adapter.generate(17, setting, demos, queries) for setting in SETTINGS]
    for setting, episode in zip(SETTINGS, episodes, strict=True):
        assert episode == adapter.generate(17, setting, demos, queries)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        assert episode["program_solution"] == adapter.program(setting)
        assert all(pair["output"] == adapter.solve(pair["input"], setting)
                   for split in ("train", "test") for pair in episode[split])
        keys = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(episode)]
        assert len(keys) == len(set(keys))
    assert _inputs(episodes[0]) == _inputs(episodes[1])
    assert all(
        left["output"] != right["output"]
        for split in ("train", "test")
        for left, right in zip(episodes[0][split], episodes[1][split], strict=True)
    )
    single = adapter.generate(17, SETTINGS[1], demos, 1)
    full = adapter.generate(17, SETTINGS[1], demos, 4)
    assert single["train"] == full["train"]
    assert single["test"] == full["test"][:1]


def test_every_minimum_demo_contains_decisive_order_conflict_and_state_dependency():
    adapter = _load_adapter()
    episode = adapter.generate(0, SETTINGS[1], 2, 4)
    for pair in episode["train"]:
        facts = adapter.analyze_input(pair["input"])
        assert facts["frame_count"] >= 2
        assert facts["matching_source_count"] >= 2
        assert facts["row_major_first_bbox"] != facts["column_major_first_bbox"]
        assert facts["row_major_first_value"] != facts["column_major_first_value"]
        intended = adapter.solve(pair["input"], SETTINGS[1])
        wrong = adapter.solve(pair["input"], SETTINGS[1], track_used=False)
        assert wrong != intended


def test_fourth_query_is_substantive_30_by_30_and_touches_all_boundaries():
    adapter = _load_adapter()
    pair = adapter.generate(2**63 - 1, SETTINGS[1], 2, 4)["test"][-1]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(occupied) >= 100
    assert {r for r, _ in occupied} & {0, 29} == {0, 29}
    assert {c for _, c in occupied} & {0, 29} == {0, 29}
    facts = adapter.analyze_input(grid)
    assert facts["frame_count"] >= 2
    assert facts["matching_source_count"] >= 2


def test_public_turn_hides_private_fields_answers_and_future_queries():
    adapter = _load_adapter()
    episode = adapter.generate(23, SETTINGS[1], 3, 4)
    first = adapter.public_turn(episode, 0)
    one = adapter.generate(23, SETTINGS[1], 3, 1)
    assert first == adapter.public_turn(one, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1 and set(first["test"][0]) == {"input"}
    encoded = adapter.public_turn_bytes(episode, 0)
    assert encoded == public_challenge_bytes(first)
    assert adapter.public_turn_id(episode, 0) == hashlib.sha256(encoded).hexdigest()

    changed = deepcopy(episode)
    changed.update(seed=999, settings=SETTINGS[0], program_solution="PRIVATE", note="PRIVATE")
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert adapter.public_turn_bytes(changed, 0) == encoded


@pytest.mark.parametrize("patch", [
    {"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 1.0},
    {"settings": None}, {"settings": {}},
    {"settings": {"source_order": True}},
    {"settings": {"source_order": "bad"}},
    {"settings": {"source_order": "row_major", "extra": 1}},
    {"demos": 1}, {"demos": 7}, {"demos": True}, {"demos": 3.0},
    {"queries": 0}, {"queries": 5}, {"queries": True}, {"queries": 4.0},
])
def test_invalid_controls_fail_closed(patch):
    adapter = _load_adapter()
    request = {"seed": 17, "settings": SETTINGS[0], "demos": 3, "queries": 4}
    request.update(patch)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(**request)


def test_protected_racket_labels_and_demo_only_identification():
    adapter = _load_adapter()
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    programs = [adapter.program(setting) for setting in SETTINGS]
    jobs = [
        {"seed": seed, "settings": setting, "demos": demos, "queries": 4}
        for seed, demos in ((0, 2), (17, 6))
        for setting in SETTINGS
    ]

    def execute(bridge, source, grid):
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        return bridge.eval_text(f"({wrap_rule(source)} {literal})")

    observed = []
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket"
        assert identity["protected"] is True
        for job in jobs:
            episode = adapter.generate(**job)
            survivors = [
                SETTINGS[index]
                for index, source in enumerate(programs)
                if all(
                    execute(bridge, source, pair["input"]) == pair["output"]
                    for pair in episode["train"]
                )
            ]
            assert survivors == [job["settings"]]
            chosen = SETTINGS.index(job["settings"])
            assert all(
                execute(bridge, programs[chosen], pair["input"]) == pair["output"]
                for pair in episode["test"]
            )
            observed.append(job["demos"] + job["queries"])
    assert observed == [job["demos"] + 4 for job in jobs]

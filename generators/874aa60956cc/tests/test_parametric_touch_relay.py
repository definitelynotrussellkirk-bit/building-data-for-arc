"""Focused regressions for the native border-touch relay family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

from arcpuzzles import Catalog

TASK = "874aa60956cc"
HOME = Path(__file__).resolve().parent.parent
PARAM = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prototype = _load("touch_relay_prototype_tests", PARAM / "prototype.py")
adapter = _load("touch_relay_adapter_tests", PARAM / "adapter.py")

CANONICAL = {"border_mode": "all"}
RELAY = {"border_mode": "touch_count_relay"}


def _catalog_program() -> str:
    root = HOME.parents[1]
    record = Catalog(root).get(TASK)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_default_program_is_exact_selected_canonical_bytes():
    assert prototype.program(CANONICAL) == _catalog_program()
    assert adapter.program(CANONICAL) == _catalog_program()
    assert (PARAM / "canonical.rkt").read_bytes() == _catalog_program().encode()


def test_independent_counts_and_matched_inputs_across_settings():
    for demos in (2, 3, 6):
        for queries in (1, 4):
            all_episode = adapter.generate(17, CANONICAL, demos, queries)
            relay_episode = adapter.generate(17, RELAY, demos, queries)
            assert len(all_episode["train"]) == demos
            assert len(all_episode["test"]) == queries
            assert len(relay_episode["train"]) == demos
            assert len(relay_episode["test"]) == queries
            assert [pair["input"] for pair in all_episode["train"]] == [
                pair["input"] for pair in relay_episode["train"]
            ]
            assert [pair["input"] for pair in all_episode["test"]] == [
                pair["input"] for pair in relay_episode["test"]
            ]
            visible = [json.dumps(pair["input"]) for split in ("train", "test") for pair in all_episode[split]]
            assert len(visible) == len(set(visible))


def test_prefixes_are_stable_and_first_public_turn_matches_single_query_use():
    short = adapter.generate(91, RELAY, 2, 1)
    same_demos_long_queries = adapter.generate(91, RELAY, 2, 4)
    long = adapter.generate(91, RELAY, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    assert adapter.public_turn_bytes(short, 0) == adapter.public_turn_bytes(same_demos_long_queries, 0)
    public = adapter.public_turn(long, 0)
    assert set(public) == {"train", "test"}
    assert len(public["test"]) == 1
    assert set(public["test"][0]) == {"input"}
    raw = adapter.public_turn_bytes(long, 0)
    assert b"border_mode" not in raw
    assert b"program" not in raw
    assert set(json.loads(raw)["test"][0]) == {"input"}


def test_every_scene_has_valid_input_dependent_relay_and_distinct_setting_outputs():
    for seed in (0, 17, 2**32 + 9):
        episode = adapter.generate(seed, RELAY, 6, 4)
        for pair in episode["train"] + episode["test"]:
            analysis = adapter.analyze_input(pair["input"])
            assert len(analysis["paired_colors"]) == 4
            assert analysis["controller_color"] == analysis["paired_colors"][0]
            assert analysis["touch_count"] in (1, 2, 3)
            assert analysis["selected_color"] == analysis["candidate_colors"][analysis["touch_count"] - 1]
            assert prototype.solve(pair["input"], "touch_count_relay") == pair["output"]
            assert prototype.solve(pair["input"], "all") != pair["output"]


def test_minimum_two_demo_lesson_rejects_declared_shortcuts():
    episode = adapter.generate(19, RELAY, 2, 4)
    for name, rival in prototype.RIVAL_SOLVERS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in episode["train"]), name


def test_wrong_intermediate_changes_substantive_30x30_query():
    episode = adapter.generate(19, RELAY, 3, 4)
    pair = episode["test"][-1]
    analysis = adapter.analyze_input(pair["input"])
    assert (len(pair["input"]), len(pair["input"][0])) == (30, 30)
    assert analysis["touch_count"] == 3
    assert prototype.solve(pair["input"], "touch_count_relay") != prototype.solve(
        pair["input"], "fixed_1"
    )
    assert sum(cell != 0 for row in pair["input"] for cell in row) >= 12
    boundary = pair["input"][0] + pair["input"][-1]
    boundary += [row[0] for row in pair["input"]] + [row[-1] for row in pair["input"]]
    assert sum(cell != 0 for cell in boundary) >= 4


def test_sampler_does_not_mutate_global_random_state():
    random.seed(12345)
    before = random.getstate()
    adapter.generate(7, RELAY, 3, 4)
    assert random.getstate() == before


@pytest.mark.parametrize(
    "call",
    [
        lambda: adapter.generate(True, RELAY, 3, 4),
        lambda: adapter.generate(-1, RELAY, 3, 4),
        lambda: adapter.generate(0, RELAY, 1, 4),
        lambda: adapter.generate(0, RELAY, 7, 4),
        lambda: adapter.generate(0, RELAY, 3, 0),
        lambda: adapter.generate(0, RELAY, 3, 5),
        lambda: adapter.generate(0, {"border_mode": "unknown"}, 3, 4),
        lambda: adapter.generate(0, {"border_mode": "all", "extra": 1}, 3, 4),
    ],
)
def test_invalid_api_values_are_rejected(call):
    with pytest.raises((TypeError, ValueError)):
        call()


def test_program_rejects_invalid_settings():
    with pytest.raises(ValueError):
        adapter.program({"border_mode": "bad"})

"""Bounded native-contract checks for the distance/origin episode family.

Literal output fixtures catch metric and reflection-branch errors. Sampled
episodes separately check teaching, setting-neutral inputs and public visibility.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


ROOT = find_root(__file__)
HOME = ROOT / "generators/e07bbcbe6ba4/workspace/parametric"
SETTINGS = [
    {"distance_metric": metric, "origin_mode": origin}
    for metric, origin in itertools.product(
        ("chebyshev", "manhattan"), ("marker", "nearest_wall_reflection")
    )
]
DEFAULT = SETTINGS[0]


def _load(name):
    path = HOME / (name + ".py")
    assert path.is_file(), f"native {name}.py has not been built"
    spec = importlib.util.spec_from_file_location("native_e07bbcbe6ba4_" + name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load("prototype")


@pytest.fixture(scope="module")
def adapter():
    return _load("adapter")


@pytest.fixture(scope="module")
def bridge():
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    with RacketBridge() as live:
        assert live.runtime_identity["backend"] == "racket"
        assert live.runtime_identity["protected"] is True
        yield live


@pytest.fixture(scope="module")
def episodes(prototype, bridge):
    return [prototype.make_episode(17, settings=setting, demos=2, queries=4,
                                   root=ROOT, bridge=bridge) for setting in SETTINGS]


def _rows(*rows):
    return [[int(value) for value in row] for row in rows]


INPUT_TOP = _rows(
    "000000000", "033333330", "030030030", "030000030", "030000030",
    "030000030", "030000030", "033333330", "000000000",
)
EXPECTED = {
    ("chebyshev", "marker"): _rows(
        "000000000", "033333330", "032434230", "032444230", "032222230",
        "034444430", "032222230", "033333330", "000000000"),
    ("manhattan", "marker"): _rows(
        "000000000", "033333330", "032434230", "034242430", "032424230",
        "034242430", "032424230", "033333330", "000000000"),
    ("chebyshev", "nearest_wall_reflection"): _rows(
        "000000000", "033333330", "032222230", "034444430", "032222230",
        "032444230", "032434230", "033333330", "000000000"),
    ("manhattan", "nearest_wall_reflection"): _rows(
        "000000000", "033333330", "032424230", "034242430", "032424230",
        "034242430", "032434230", "033333330", "000000000"),
}


def test_adapter_file_exposes_native_api():
    adapter = _load("adapter")
    assert callable(adapter.program)
    assert callable(adapter.generate)


def test_default_is_exact_canonical_and_four_programs_are_distinct(adapter, prototype):
    canonical = prototype.canonical_source(root=ROOT)
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "037ff6659c65492403f63da021ff422d16b36719afed937502aaf70fa93d8d02")
    assert adapter.program(DEFAULT) == canonical
    assert len({adapter.program(setting) for setting in SETTINGS}) == 4


@pytest.mark.parametrize("setting", SETTINGS)
@pytest.mark.parametrize("transpose", [False, True], ids=["nearest-top", "nearest-left"])
def test_racket_metric_and_reflection_outputs_match_literal_grids(
        adapter, prototype, bridge, setting, transpose):
    # Top fixture: nearest wall is top, so (2,4) reflects to (6,4).
    # Its transpose selects left and reflects (4,2) to (4,6).
    grid = copy.deepcopy(INPUT_TOP)
    expected = EXPECTED[(setting["distance_metric"], setting["origin_mode"])]
    if transpose:
        grid = [list(row) for row in zip(*grid)]
        expected = [list(row) for row in zip(*expected)]
    assert prototype.execute_rule(adapter.program(setting), grid, bridge=bridge) == expected


@pytest.mark.parametrize("setting", [None, {}, {"distance_metric": "chebyshev"},
    {"origin_mode": "marker"}, {**DEFAULT, "extra": 1},
    {**DEFAULT, "distance_metric": True}, {**DEFAULT, "distance_metric": "euclidean"},
    {**DEFAULT, "origin_mode": "center"}])
def test_adapter_rejects_missing_unknown_or_untyped_settings(adapter, setting):
    with pytest.raises(ValueError):
        adapter.program(setting)
    with pytest.raises(ValueError):
        adapter.generate(0, setting, 2, 1)


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 2, 1), (-1, 2, 1), (2**63, 2, 1), (1.0, 2, 1),
    (0, True, 1), (0, 1, 1), (0, 7, 1), (0, 2.0, 1),
    (0, 2, True), (0, 2, 0), (0, 2, 5), (0, 2, 1.0),
])
def test_adapter_rejects_nonliteral_or_out_of_range_counts(adapter, seed, demos, queries):
    with pytest.raises(ValueError):
        adapter.generate(seed, DEFAULT, demos, queries)


def _geometry(grid):
    green = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value == 3]
    top, bottom = min(r for r, _ in green), max(r for r, _ in green)
    left, right = min(c for _, c in green), max(c for _, c in green)
    markers = [(r, c) for r, c in green if top < r < bottom and left < c < right]
    assert len(markers) == 1
    mr, mc = markers[0]
    assert set(green) == ({(top, c) for c in range(left, right + 1)}
                         | {(bottom, c) for c in range(left, right + 1)}
                         | {(r, left) for r in range(top, bottom + 1)}
                         | {(r, right) for r in range(top, bottom + 1)} | {(mr, mc)})
    distances = [mr - top, bottom - mr, mc - left, right - mc]
    assert distances.count(min(distances)) == 1
    assert 7 <= bottom - top + 1 <= 24
    assert 7 <= right - left + 1 <= 24
    assert 0 < top < bottom < len(grid) - 1
    assert 0 < left < right < len(grid[0]) - 1
    assert all(value in (0, 3) and type(value) is int for row in grid for value in row)
    return distances.index(min(distances)) // 2, (bottom - top + 1, right - left + 1)


def test_episode_inputs_are_setting_neutral_distinct_and_cover_grammar(episodes):
    expected = [pair["input"] for split in ("train", "test") for pair in episodes[0][split]]
    assert len({json.dumps(grid) for grid in expected}) == 6
    assert all(9 <= len(grid) <= 30 and 9 <= len(grid[0]) <= 30 for grid in expected)
    assert {_geometry(pair["input"])[0] for pair in episodes[0]["train"]} == {0, 1}
    assert any(len(pair["input"]) == len(pair["input"][0]) == 30
               and _geometry(pair["input"])[1] == (24, 24) for pair in episodes[0]["test"])
    for episode, setting in zip(episodes, SETTINGS):
        assert len(episode["train"]) == 2 and len(episode["test"]) == 4
        assert episode["parameters"] == setting
        assert [pair["input"] for split in ("train", "test") for pair in episode[split]] == expected
        for grid in expected:
            _geometry(grid)


def test_demonstrations_alone_identify_all_settings(adapter, prototype, bridge, episodes):
    for chosen, episode in enumerate(episodes):
        assert episode["program_solution"] == adapter.program(SETTINGS[chosen])
        survivors = []
        for rival, setting in enumerate(SETTINGS):
            outputs = [prototype.execute_rule(adapter.program(setting), pair["input"], bridge=bridge)
                       for pair in episode["train"]]
            if outputs == [pair["output"] for pair in episode["train"]]:
                survivors.append(rival)
        assert survivors == [chosen]
        for pair in episode["test"]:
            assert prototype.execute_rule(episode["program_solution"], pair["input"], bridge=bridge) == pair["output"]


def test_one_query_prefix_and_independent_count_boundaries(adapter, prototype, bridge, episodes):
    one = prototype.make_episode(17, settings=DEFAULT, demos=2, queries=1, root=ROOT, bridge=bridge)
    assert one["train"] == episodes[0]["train"]
    assert one["test"] == episodes[0]["test"][:1]
    six = adapter.generate(19, DEFAULT, 6, 1)
    assert len(six["train"]) == 6 and len(six["test"]) == 1
    assert six["program_solution"] == adapter.program(DEFAULT)
    assert len({json.dumps(pair["input"]) for pair in six["train"] + six["test"]}) == 7


def test_single_query_public_bytes_hide_future_answers_settings_and_metadata(prototype, episodes):
    episode = episodes[0]
    public = prototype.public_challenge(episode, query_index=0)
    assert public == {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}
    original_bytes = public_challenge_bytes(public)
    assert public_challenge_id(public) == hashlib.sha256(original_bytes).hexdigest()
    changed = copy.deepcopy(episode)
    changed["parameters"] = SETTINGS[-1]
    changed["program_solution"] = "PRIVATE CHANGED RULE"
    changed["identifiability"] = {"private": "CHANGED"}
    changed["test"][0]["output"] = [[9]]
    changed["test"][1:] = [{"input": [[8]], "output": [[7]]}]
    assert public_challenge_bytes(prototype.public_challenge(changed, query_index=0)) == original_bytes
    assert prototype.public_challenge(episode, query_index=3)["test"] == [
        {"input": episode["test"][3]["input"]}]
    for invalid in (True, -1, 4, 0.0):
        with pytest.raises(ValueError):
            prototype.public_challenge(episode, query_index=invalid)


@pytest.mark.parametrize("seed,origin", [(0, "marker"), (1, "nearest_wall_reflection")])
def test_minimum_demo_curriculum_refutes_frame_center(prototype, bridge, seed, origin):
    episode = prototype.make_episode(seed, settings={"distance_metric": "manhattan", "origin_mode": origin},
                                     demos=2, queries=4, root=ROOT, bridge=bridge)
    assert episode["identifiability"]["rivals"]["frame_center"]["refuted_by_demo"] is True

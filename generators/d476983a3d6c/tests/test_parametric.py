"""Contract regressions for the separate native route family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest


HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def load():
    spec = importlib.util.spec_from_file_location("d476_native_contract", HOME / "prototype.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def api():
    return load()


def causal_grid(command=1):
    g = [[0] * 5 for _ in range(5)]
    g[0][0] = command
    for r, c in [(1, 1), (3, 3)]:
        g[r][c] = 3
    for r, c in ([(2, 1), (4, 4)] if command == 1 else [(1, 2), (4, 4)]):
        g[r][c] = 4
    return g


@pytest.mark.parametrize("command", [1, 2])
def test_previous_path_changes_next_route(api, command):
    g = causal_grid(command)
    original = copy.deepcopy(g)
    a = api.mirror(g, {"routing_mode": "command"})
    b = api.mirror(g, {"routing_mode": "avoid_painted"})
    assert a != b
    assert g == original
    trace = api.analyze(g, {"routing_mode": "avoid_painted"})
    assert trace["routes"][0]["chosen"] == command
    assert trace["routes"][1]["chosen"] == 3 - command
    assert trace["routes"][1]["costs"][str(command)] == 1
    assert trace["routes"][1]["costs"][str(3 - command)] == 0


def test_exact_canonical_bytes_and_standalone_alternate(api):
    assert api.program({"routing_mode": "command"}).encode() == (HOME / "canonical.rkt").read_bytes()
    assert api.program({"routing_mode": "avoid_painted"}).lstrip().startswith("(rule!")


@pytest.mark.parametrize("grid", [[[1]], [[1, 3, 0, 3]], [[2], [3], [0], [3]]])
@pytest.mark.parametrize("mode", ["command", "avoid_painted"])
def test_thin_legal_grids(api, grid, mode):
    actual = api.mirror(grid, {"routing_mode": mode})
    expected = [[v if v else 3 for v in row] for row in grid]
    assert actual == expected


@pytest.mark.parametrize("grid", [[], [[]], [[1], [0, 0]], [[True]], [[1, 1]], [[0]], [[3]], [[1, 0.0]], [[1, -1]], [[1, 10]], [[1] + [0] * 30]])
def test_grid_grammar_rejects_bad_types_shapes_and_commands(api, grid):
    with pytest.raises((TypeError, ValueError)):
        api.mirror(grid, {"routing_mode": "command"})


@pytest.mark.parametrize("settings", [{}, {"routing_mode": True}, {"routing_mode": "other"}, {"routing_mode": "command", "x": 1}, None])
def test_settings_are_exact(api, settings):
    with pytest.raises((TypeError, ValueError)):
        api.program(settings)


@pytest.mark.parametrize("seed,demos,queries", [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0.0, 3, 4), (0, 1, 4), (0, 7, 4), (0, True, 4), (0, 3, 0), (0, 3, 5), (0, 3, 1.0)])
def test_request_bounds(api, seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        api.generate(seed, {"routing_mode": "command"}, demos=demos, queries=queries)


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_counts_matched_inputs_prefixes_distinct_and_local_rng(api, seed):
    before = random.getstate()
    a = api.generate(seed, {"routing_mode": "command"}, demos=2, queries=1)
    b = api.generate(seed, {"routing_mode": "command"}, demos=6, queries=4)
    c = api.generate(seed, {"routing_mode": "avoid_painted"}, demos=6, queries=4)
    assert random.getstate() == before
    assert a == api.generate(seed, {"routing_mode": "command"}, demos=2, queries=1)
    assert a["train"] == b["train"][:2]
    assert a["test"] == b["test"][:1]
    for split in ["train", "test"]:
        assert [x["input"] for x in b[split]] == [x["input"] for x in c[split]]
    grids = [p["input"] for p in b["train"] + b["test"]]
    assert len({json.dumps(g) for g in grids}) == 10
    assert {(len(p["input"]), len(p["input"][0])) for p in b["test"]} == {(7, 9), (15, 19), (24, 28), (30, 30)}
    for settings, episode in [({"routing_mode": "command"}, b), ({"routing_mode": "avoid_painted"}, c)]:
        assert all(p["output"] == api.mirror(p["input"], settings) for p in episode["train"] + episode["test"])


def test_returned_grids_do_not_alias_cache(api):
    a = api.generate(0, {"routing_mode": "command"}, demos=3, queries=4)
    before = copy.deepcopy(a)
    a["train"][0]["input"][0][0] = 9
    a["test"][0]["output"][0][0] = 9
    assert api.generate(0, {"routing_mode": "command"}, demos=3, queries=4) == before


def test_command_is_not_encoded_by_exact_count_profile(api):
    for profile in range(4):
        commands = {api._scene(seed, "profile-regression", profile, 11, 13)[0][0]
                    for seed in range(32)}
        assert commands == {1, 2}


def test_full_span_query_endpoints_are_reserved(api):
    for seed in range(128):
        g = api._scene(seed, "boundary-regression", 3, 30, 30, boundary=True)
        assert g[0][-1] != 0
        assert g[0][-1] == g[-1][0]


def test_seed8_teaching_cover_regression(api):
    episode = api.generate(8, {"routing_mode": "avoid_painted"}, demos=2, queries=4)
    assert len(episode["train"]) == 2 and len(episode["test"]) == 4

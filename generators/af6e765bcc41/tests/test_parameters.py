"""Behavioral contracts for the separate gap-completion family."""
from __future__ import annotations

import importlib.util
import copy
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def load():
    path = HOME / "workspace/parametric/adapter.py"
    assert path.is_file(), "Native parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location("test_gap_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frame(h=5, w=7, color=7):
    return [[color if r in (0, h-1) or c in (0, w-1) else 0
             for c in range(w)] for r in range(h)]


def test_native_adapter_surface():
    adapter = load()
    assert callable(adapter.program) and callable(adapter.generate)


def test_default_preserves_exact_selected_canonical_source():
    from arcpuzzles import Catalog
    adapter = load()
    programs = {v["program_solution"] for v in Catalog(HOME.parents[1]).get(HOME.name)["variants"]}
    assert programs == {adapter.program({"completion": "none"})}


@pytest.mark.parametrize("gap", [(0,0), (0,3), (4,6), (2,0), (3,6)])
def test_single_gap_is_closed_then_zero_interior_filled(gap):
    adapter = load()
    g = frame()
    g[gap[0]][gap[1]] = 0
    assert adapter.mirror(g, {"completion": "none"}) == g
    got = adapter.mirror(g, {"completion": "single_gap"})
    assert got == [[7 if r in (0,4) or c in (0,6) else 8 for c in range(7)] for r in range(5)]
    assert g[gap[0]][gap[1]] == 0


def test_repair_merging_with_satellite_prevents_fill():
    adapter = load()
    g = [[0]*7 for _ in range(7)]
    for r in range(2,7):
        for c in range(1,6):
            if r in (2,6) or c in (1,5):
                g[r][c] = 7
    g[2][3] = 0
    g[1][3] = 7
    expected = [row[:] for row in g]
    expected[2][3] = 7
    assert adapter.first_stage(g, {"completion": "single_gap"}) == expected
    assert adapter.mirror(g, {"completion": "single_gap"}) == expected
    assert all(expected[r][c] == 0 for r in range(3,6) for c in range(2,5))


def test_fill_preserves_colored_interior_and_preexisting_cyan():
    adapter = load()
    g = frame()
    g[2][2], g[2][3] = 3, 8
    for mode in ("none", "single_gap"):
        got = adapter.mirror(g, {"completion": mode})
        assert got[2][2:4] == [3,8]
        assert got[1][1:6] == [8]*5


@pytest.mark.parametrize("kind", ["two_gaps", "nonorange", "tail", "solid"])
def test_near_miss_shapes_are_preserved(kind):
    adapter = load()
    g = frame(5,7,3 if kind == "nonorange" else 7)
    if kind == "two_gaps":
        g[0][2] = g[0][3] = 0
    elif kind == "tail":
        g[1][3] = 7
    elif kind == "solid":
        g = [[7]*7 for _ in range(5)]
    for mode in ("none", "single_gap"):
        assert adapter.mirror(g, {"completion":mode}) == g


@pytest.mark.parametrize("g", [[], [[0]], [[0]*3]*2, [[0]*31]*3,
    [[0,0,0],[0,True,0],[0,0,0]], [[0,0,0],[0,1.0,0],[0,0,0]],
    [[0,0,0],[0,-1,0],[0,0,0]], [[0,0,0],[0,10,0],[0,0,0]],
    [[0,0,0],[0,0],[0,0,0]], ((0,0,0),)*3])
def test_invalid_grids_rejected(g):
    with pytest.raises((TypeError,ValueError)):
        load().mirror(g, {"completion":"none"})


@pytest.mark.parametrize("settings", [{}, {"completion":True}, {"completion":"bad"},
    {"completion":"none","extra":0}, None, []])
def test_invalid_settings_rejected(settings):
    with pytest.raises((TypeError,ValueError)):
        load().program(settings)


@pytest.mark.parametrize("change", [{"seed":True},{"seed":-1},{"seed":2**63},
    {"demos":2},{"demos":7},{"demos":3.0},{"queries":0},{"queries":5},{"queries":True}])
def test_invalid_requests_rejected(change):
    args = dict(seed=0,settings={"completion":"none"},demos=3,queries=4)
    args.update(change)
    with pytest.raises((TypeError,ValueError)):
        load().generate(**args)


def test_counts_prefixes_distinctness_matched_settings_and_no_aliases():
    adapter = load()
    a = adapter.generate(17, {"completion":"none"}, 6, 4)
    b = adapter.generate(17, {"completion":"single_gap"}, 6, 4)
    for split in ("train", "test"):
        assert [p["input"] for p in a[split]] == [p["input"] for p in b[split]]
    assert any(x["output"] != y["output"] for x,y in zip(a["train"],b["train"]))
    for demos in range(3,7):
        for queries in range(1,5):
            x = adapter.generate(17,{"completion":"none"},demos,queries)
            assert x["train"] == a["train"][:demos]
            assert x["test"] == a["test"][:queries]
    inputs = [p["input"] for split in ("train","test") for p in a[split]]
    assert len({str(g) for g in inputs}) == 10
    pristine = copy.deepcopy(a)
    a["train"][0]["input"][0][0] = 99
    assert adapter.generate(17,{"completion":"none"},6,4) == pristine
    assert b["train"][0]["input"][0][0] != 99


def test_large_query_has_substantial_content_and_writes():
    adapter=load()
    for seed in range(4):
        ep=adapter.generate(seed,{"completion":"single_gap"},3,4)
        large=[p for p in ep["test"] if len(p["input"])==30 and len(p["input"][0])==30]
        assert len(large)==1
        pair=large[0]
        assert sum(v!=0 for row in pair["input"] for v in row)>=120
        assert sum(a!=b for x,y in zip(pair["input"],pair["output"]) for a,b in zip(x,y))>=20

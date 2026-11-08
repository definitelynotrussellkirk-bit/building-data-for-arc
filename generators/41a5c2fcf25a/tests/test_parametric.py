"""Behavioral checks for the opt-in area/perimeter ranking family."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id


HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "workspace/parametric/adapter.py"


@pytest.fixture(scope="module")
def adapter():
    assert SOURCE.is_file(), "Native area/perimeter adapter is not implemented"
    spec = importlib.util.spec_from_file_location("tested_rank_adapter", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def edge_set_perimeter(cells):
    edges = set()
    for r,c in cells:
        for edge in (((r,c),(r,c+1)),((r+1,c),(r+1,c+1)),
                     ((r,c),(r+1,c)),((r,c+1),(r+1,c+1))):
            if edge in edges:
                edges.remove(edge)
            else:
                edges.add(edge)
    return len(edges)


def test_exact_default_and_two_meaningful_programs(adapter):
    with canonical_path(find_root(__file__)).open() as stream:
        canonical = next(x["program_solution"] for x in map(json.loads,stream) if x.get("task_id") == "41a5c2fcf25a")
    assert adapter.program({"rank_by":"area"}) == canonical
    assert adapter.program({"rank_by":"perimeter"}) != canonical
    first = adapter.generate(0,{"rank_by":"area"},2,4)
    second = adapter.generate(0,{"rank_by":"perimeter"},2,4)
    assert first["train"][0]["output"] != second["train"][0]["output"]


def test_perimeter_counts_holes_and_separates_area_order(adapter):
    bar = {(0,c) for c in range(5)}
    rect = {(r,c) for r in range(2) for c in range(3)}
    ring = {(r,c) for r in range(3) for c in range(3)}-{(1,1)}
    assert adapter.perimeter(bar) == edge_set_perimeter(bar) == 12
    assert adapter.perimeter(rect) == edge_set_perimeter(rect) == 10
    assert adapter.perimeter(ring) == edge_set_perimeter(ring) == 16


@pytest.mark.parametrize("metric", ["area", "perimeter"])
def test_complete_sort_key_tie_keeps_canonical_discovery_order(adapter, metric):
    # Both objects have area 13, perimeter 28, top=1 and left=2. Racket
    # cons-builds its component list before stable sorting, so later B wins.
    a = {(1, c) for c in range(2, 9)} | {(2, 8)} | {(3, c) for c in range(4, 9)}
    b = {(r, 10) for r in range(1, 5)} | {(5, c) for c in range(2, 11)}
    grid = [[0] * 12 for _ in range(7)]
    grid[0][:2] = [3, 4]
    expected = copy.deepcopy(grid)
    for cells, color in ((a, 4), (b, 3)):
        for r, c in cells:
            grid[r][c] = 8
            expected[r][c] = color
    assert len(adapter.analyze(grid)[1]) == 2
    assert adapter.solve(grid, metric) == expected


@pytest.mark.parametrize("metric",["area","perimeter"])
def test_counts_match_inputs_and_first_turn(adapter,metric):
    for demos in range(2,7):
        e = adapter.generate(17,{"rank_by":metric},demos,4)
        other = adapter.generate(17,{"rank_by":"perimeter" if metric == "area" else "area"},demos,4)
        assert len(e["train"]) == demos and len(e["test"]) == 4
        all_inputs = [tuple(map(tuple,p["input"])) for s in ("train","test") for p in e[s]]
        assert len(all_inputs) == len(set(all_inputs))
        for split in ("train","test"):
            assert [p["input"] for p in e[split]] == [p["input"] for p in other[split]]
        singleton = adapter.generate(17,{"rank_by":metric},demos,1)
        assert adapter.public_turn(e,0) == adapter.public_turn(singleton,0)
        assert any(len(p["input"]) == len(p["input"][0]) == 30 for p in e["test"])
        big = e["test"][2]["input"]
        body = [(r,c) for r,row in enumerate(big[1:],1) for c,v in enumerate(row) if v]
        assert len(body) >= 180 and max(r for r,c in body)-min(r for r,c in body) >= 24
        assert max(c for r,c in body)-min(c for r,c in body) >= 25


def test_independent_perimeter_on_generated_components(adapter):
    for seed in (0,17,29):
        e = adapter.generate(seed,{"rank_by":"perimeter"},3,4)
        for split in ("train","test"):
            for pair in e[split]:
                colors, comps = adapter.analyze(pair["input"])
                ordered = sorted(comps,key=lambda c:(-edge_set_perimeter(c),min(r for r,k in c),min(k for r,k in c)))
                expected = copy.deepcopy(pair["input"])
                for color,cells in zip(colors,ordered):
                    for r,c in cells:expected[r][c]=color
                assert expected == pair["output"]


@pytest.mark.parametrize("metric", ["area", "perimeter"])
def test_minimum_lesson_rejects_declared_shortcuts(adapter, metric):
    path = SOURCE.with_name("rivals.py")
    spec = importlib.util.spec_from_file_location("tested_rank_rivals", path)
    rivals = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rivals)
    for seed in (0, 17, 29, 2**63 - 1):
        lesson = adapter.generate(seed, {"rank_by": metric}, 2, 4)
        rows = rivals.check_episode(lesson)
        assert len(rows) == 12
        assert not [row["rival"] for row in rows if row["survives_demos"]]


@pytest.mark.parametrize("demos,queries",[(1,4),(7,4),(2,0),(2,5),(True,4),(2,4.0)])
def test_bad_counts_rejected(adapter,demos,queries):
    with pytest.raises(ValueError):adapter.generate(0,{"rank_by":"area"},demos,queries)


def test_bad_settings_seeds_and_grids_rejected(adapter):
    for settings in ({},{"rank_by":"bbox"},{"rank_by":True},{"rank_by":"area","extra":1}):
        with pytest.raises(ValueError):adapter.generate(0,settings,3,4)
    for seed in (-1,True,1.0,2**63):
        with pytest.raises(ValueError):adapter.generate(seed,{"rank_by":"area"},3,4)
    good = adapter.generate(0,{"rank_by":"area"},2,1)["train"][0]["input"]
    bad = copy.deepcopy(good);bad[0][0]=True
    with pytest.raises(ValueError):adapter.solve(bad,"area")
    bad = copy.deepcopy(good);bad[0][0]=bad[0][1]
    with pytest.raises(ValueError):adapter.solve(bad,"area")
    bad = copy.deepcopy(good);bad[3][0]=3
    with pytest.raises(ValueError):adapter.solve(bad,"area")
    bad = copy.deepcopy(good);bad[0][0]=0
    with pytest.raises(ValueError):adapter.solve(bad,"area")


def test_public_projection_ignores_private_fields(adapter):
    e=adapter.generate(17,{"rank_by":"area"},3,4)
    before=copy.deepcopy(e)
    turn=adapter.public_turn(e,0)
    assert set(turn)=={"train","test"} and len(turn["test"])==1 and set(turn["test"][0])=={"input"}
    private=copy.deepcopy(e);private.update(seed=777,settings={"private":"changed"},program_solution="changed")
    for pair in private["test"]:pair["output"]=[[9]]
    assert public_challenge_bytes(e)==public_challenge_bytes(private)
    assert public_challenge_id(e)==public_challenge_id(private)
    assert adapter.public_turn(private,0)==turn
    assert e==before
    with pytest.raises(ValueError):adapter.public_turn(e,True)

from pathlib import Path
import copy
import importlib.util
import json
import random

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def base():
    return load(HOME / "generator.py", "gravity_test_base")


@pytest.fixture(scope="module")
def adapter():
    return load(HOME / "workspace/parametric/adapter.py", "gravity_test_adapter")


def fixture(diagonal=False, wall=5, tail=1):
    g = [[0] * 16 for _ in range(16)]
    ph, pw = (6, 7) if diagonal else (5, 5)
    for r in range(ph):
        for c in range(pw): g[r][c] = wall
    tails = [(1,3),(2,4),(2,1),(3,2)] if diagonal else [(1,1),(1,2),(3,1),(3,2)]
    heads = [(3,5),(4,3)] if diagonal else [(1,3),(3,3)]
    for r,c in tails: g[r][c] = tail
    for r,c in heads: g[r][c] = 2
    interior = ({(r,c) for r in range(8,10) for c in range(3,6)} |
                {(r,c) for r in range(10,13) for c in range(3,8)}) if diagonal else {
                (r,c) for r in range(8,13) for c in range(2,9)}
    for r,c in interior:
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                p = r+dr,c+dc
                if p not in interior: g[p[0]][p[1]] = wall
    tokens = [(8,4)] if diagonal else [(10,3),(12,7)]
    for r,c in tokens: g[r][c] = 4
    return g, tokens


@pytest.mark.parametrize("index", range(5))
def test_all_original_labels(base, index):
    raw = REPO / "shared/data/raw"
    d = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["88e364bc"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["88e364bc"]
    pairs = d["train"] + [dict(input=p["input"],output=o) for p,o in zip(d["test"],gold)]
    assert base.solve(pairs[index]["input"]) == pairs[index]["output"]


@pytest.mark.parametrize("mode,col", [("toward_head",8),("toward_tail",2)])
@pytest.mark.parametrize("wall,tail", [(5,1),(1,5)])
def test_literal_cardinal_stops_and_contextual_tail(base, mode, col, wall, tail):
    g,tokens = fixture(wall=wall,tail=tail); expected = copy.deepcopy(g)
    for r,c in tokens: expected[r][c] = 0
    for r,c in tokens: expected[r][col] = 4
    assert base.solve(g,mode) == expected


def test_literal_diagonal_corner_blocks_empty_diagonal(base):
    g,tokens = fixture(diagonal=True)
    assert g[10][6] == 0 and g[9][6] == 5
    expected = copy.deepcopy(g);expected[8][4]=0;expected[9][5]=4
    assert base.solve(g) == expected
    assert base.solve(g,"toward_tail") == g


def test_reject_untaught_token_collisions(base):
    g,_ = fixture();g[10][5]=4
    with pytest.raises(ValueError,match="motion line"):
        base.solve(g)


@pytest.mark.parametrize("bad", [[],[[0]],[[True]*10]*10,[[1.0]*10]*10,
    [[10]*10]*10,[[0]*10]*10,[tuple([0]*10)]*10,[[0]*10,[0]*11]])
def test_strict_grid_types(base,bad):
    with pytest.raises((ValueError,TypeError)):
        base.solve(bad)


@pytest.mark.parametrize("mode",["toward_head","toward_tail"])
def test_count_prefixes_ownership_and_matched_inputs(adapter,mode):
    state=random.getstate();settings={"motion":mode}
    full=adapter.generate(17,settings,6,4);short=adapter.generate(17,settings,2,1)
    other=adapter.generate(17,{"motion":"toward_tail" if mode=="toward_head" else "toward_head"},6,4)
    assert state==random.getstate()
    assert short["train"]==full["train"][:2] and short["test"]==full["test"][:1]
    for split in ("train","test"):
        assert [p["input"] for p in full[split]]==[p["input"] for p in other[split]]
    pairs=full["train"]+full["test"]
    assert len({json.dumps(p["input"]) for p in pairs})==10
    rows=[r for p in pairs for side in ("input","output") for r in p[side]]
    assert len({id(r) for r in rows})==len(rows)


def test_exact_resources_and_root_api(base,adapter):
    from arc_repl.parser import parse_all,Symbol
    assert base.RULE_TASK_ID=="ee_88e364bc" and base.AXES=={}
    assert (HOME/"generator.py").read_bytes()==(HOME/"workspace/parametric/sampler.py").read_bytes()
    assert adapter.program({"motion":"toward_head"}).encode()==(HOME/"reference.rkt").read_bytes()
    for mode in ("toward_head","toward_tail"):
        forms=parse_all(adapter.program({"motion":mode}));assert len(forms)==1 and forms[0][0]==Symbol("rule!")
    grids=[base.generate(29,i) for i in range(6)]
    assert len({json.dumps(g) for g in grids})==6
    for g in grids:
        before=copy.deepcopy(g);assert base.self_check(g)==[] and g==before
    assert base.self_check([[0]])
    with pytest.raises(ValueError):base.generate(17,unknown=1)


@pytest.mark.parametrize("seed,settings,demos,queries",[
    (True,{"motion":"toward_head"},2,4),(-1,{"motion":"toward_head"},2,4),
    (2**63,{"motion":"toward_head"},2,4),(0,{"motion":"bad"},2,4),
    (0,{"motion":"toward_head","extra":1},2,4),(0,{"motion":"toward_head"},True,4),
    (0,{"motion":"toward_head"},1,4),(0,{"motion":"toward_head"},7,4),
    (0,{"motion":"toward_head"},2,0),(0,{"motion":"toward_head"},2,5)])
def test_invalid_episode_requests(adapter,seed,settings,demos,queries):
    with pytest.raises((ValueError,TypeError)):
        adapter.generate(seed,settings,demos,queries)


def test_substantive_large_query(adapter):
    e=adapter.generate(2**63-1,{"motion":"toward_head"},2,4)
    p=next(p for p in e["test"] if len(p["input"])==len(p["input"][0])==30)
    a=adapter.analyze(p["input"],{"motion":"toward_head"})
    assert len(a["tokens"])>=12
    assert len(a["regions"])>=2 and len(a["legends"])==2
    assert sum(v not in(0,2,4) for row in p["input"] for v in row)>=100
    assert sum(x!=y for rx,ry in zip(p["input"],p["output"]) for x,y in zip(rx,ry))>=8

from pathlib import Path
import copy
import importlib.util
import json
import random

import pytest

HOME=Path(__file__).resolve().parents[1]
REPO=HOME.parents[1]


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


@pytest.fixture(scope="module")
def base():return load(HOME/"generator.py","bar_test_base")


@pytest.fixture(scope="module")
def adapter():return load(HOME/"workspace/parametric/adapter.py","bar_test_adapter")


def scene(axis,side,objects,h,w):
    g=[[8]*w for _ in range(h)];edge=0 if side=="left" else w-1
    for c in range(w):g[0][c]=1 if axis=="horizontal" else 2
    for r in range(h):g[r][edge]=2 if axis=="horizontal" else 1
    g[0][edge]=0
    for r,c,tile in objects:
        for y,row in enumerate(tile):
            for x,v in enumerate(row):g[r+y][c+x]=v
    return g


@pytest.mark.parametrize("index",range(5))
def test_all_original_labels(base,index):
    raw=REPO/"shared/data/raw";d=json.loads((raw/"arc-agi_evaluation_challenges.json").read_text())["291dc1e1"]
    gold=json.loads((raw/"arc-agi_evaluation_solutions.json").read_text())["291dc1e1"]
    pairs=d["train"]+[dict(input=p["input"],output=o) for p,o in zip(d["test"],gold)]
    assert base.solve(pairs[index]["input"])==pairs[index]["output"]


@pytest.mark.parametrize("order",["forward","reverse"])
def test_literal_horizontal_right_order_without_reflection(base,order):
    a=[[3,4,5,6],[7,9,1,2]];b=[[3,4],[5,6]];c=[[6,6],[6,6]]
    g=scene("horizontal","right",[(2,1,a),(2,7,b),(5,2,c)],8,12)
    tiles=[[[8,3,4,8],[8,5,6,8]],a,[[8,6,6,8],[8,6,6,8]]]
    if order=="reverse":tiles.reverse()
    assert base.solve(g,order)==[row for t in tiles for row in t]


@pytest.mark.parametrize("side",["left","right"])
def test_vertical_mixed_square_and_internal_border_colors(base,side):
    a=[[3,4],[5,6]];b=[[7,9],[1,2],[3,4],[5,6]];c=[[6,6],[6,6]]
    g=scene("vertical",side,[(2,2,a),(6,2,b),(3,6,c)],14,10)
    normalized=[[[8,4,6,8],[8,3,5,8]],[[9,2,4,6],[7,1,3,5]],[[8,6,6,8],[8,6,6,8]]]
    if side=="right":normalized=[normalized[2],normalized[0],normalized[1]]
    assert base.solve(g)==[row for t in normalized for row in t]


def test_repeated_identical_bars_are_not_deduplicated(base):
    a=[[3,4],[5,6]];g=scene("horizontal","left",[(2,2,a),(2,6,a),(5,1,a)],8,10)
    assert base.solve(g)==a+a+a


@pytest.mark.parametrize("bad",[[],[[0]],[[True]*8]*8,[[1.0]*8]*8,[[10]*8]*8,[[8]*8]*8,[tuple([8]*8)]*8,[[0]*8,[0]*9]])
def test_strict_grid_types(base,bad):
    with pytest.raises((ValueError,TypeError)):base.solve(bad)


@pytest.mark.parametrize("kind",["odd","hollow","wrong_thickness","bad_border"])
def test_reject_unsupported_bar_grammar(base,kind):
    tile=[[3,4],[5,6]]
    if kind=="odd":tile=[[3,4,5],[6,7,9]]
    if kind=="hollow":tile=[[3,8],[5,6]]
    if kind=="wrong_thickness":tile=[[3,4],[5,6],[7,9]]
    g=scene("horizontal","left",[(2,2,tile)],8,10)
    if kind=="bad_border":g[0][5]=2
    with pytest.raises(ValueError):base.solve(g)


@pytest.mark.parametrize("order",["forward","reverse"])
def test_prefixes_matched_inputs_and_row_ownership(adapter,order):
    state=random.getstate();full=adapter.generate(17,{"stack_order":order},6,4)
    short=adapter.generate(17,{"stack_order":order},3,1)
    other=adapter.generate(17,{"stack_order":"reverse" if order=="forward" else "forward"},6,4)
    assert random.getstate()==state and short["train"]==full["train"][:3] and short["test"]==full["test"][:1]
    pairs=full["train"]+full["test"]
    assert len({json.dumps(p["input"]) for p in pairs})==10
    for split in ("train","test"):assert [p["input"] for p in full[split]]==[p["input"] for p in other[split]]
    rows=[r for p in pairs for side in ("input","output") for r in p[side]]
    assert len({id(r) for r in rows})==len(rows)


def test_resources_and_root_api(base,adapter):
    from arc_repl.parser import parse_all,Symbol
    assert base.RULE_TASK_ID=="ee_291dc1e1" and base.AXES=={}
    assert (HOME/"generator.py").read_bytes()==(HOME/"workspace/parametric/sampler.py").read_bytes()
    assert adapter.program({"stack_order":"forward"}).encode()==(HOME/"reference.rkt").read_bytes()
    for order in ("forward","reverse"):
        forms=parse_all(adapter.program({"stack_order":order}));assert len(forms)==1 and forms[0][0]==Symbol("rule!")
    grids=[base.generate(29,i) for i in range(7)]
    assert len({json.dumps(g) for g in grids})==7
    for g in grids:
        before=copy.deepcopy(g);assert base.self_check(g)==[] and g==before
    assert base.self_check([[0]])
    with pytest.raises(ValueError):base.generate(17,unknown=1)


@pytest.mark.parametrize("seed,settings,demos,queries",[
    (True,{"stack_order":"forward"},3,4),(-1,{"stack_order":"forward"},3,4),
    (2**63,{"stack_order":"forward"},3,4),(0,{"stack_order":"bad"},3,4),
    (0,{"stack_order":"forward","extra":1},3,4),(0,{"stack_order":"forward"},True,4),
    (0,{"stack_order":"forward"},2,4),(0,{"stack_order":"forward"},7,4),
    (0,{"stack_order":"forward"},3,0),(0,{"stack_order":"forward"},3,5)])
def test_invalid_requests(adapter,seed,settings,demos,queries):
    with pytest.raises((ValueError,TypeError)):adapter.generate(seed,settings,demos,queries)


def test_large_input_and_substantial_output(adapter):
    e=adapter.generate(2**63-1,{"stack_order":"forward"},3,4)
    p=next(p for p in e["test"] if len(p["input"])==len(p["input"][0])==30)
    assert len(p["output"])==26 and len(p["output"][0])==28
    assert sum(v!=8 for row in p["output"] for v in row)>=150

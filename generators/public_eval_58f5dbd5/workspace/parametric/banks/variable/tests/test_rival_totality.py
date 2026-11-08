"""Wrong associations fit their selected mask, including unequal template sizes."""
import importlib.util
from pathlib import Path
import sys
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]


def mixed_sizes():
    g=[[0]*20 for _ in range(16)]
    for color,(top,left,bottom,right) in [(2,(2,12,5,15)),(3,(8,12,13,17))]:
        for r in range(top,bottom+1):
            for c in range(left,right+1):g[r][c]=color
    for color,top,left,mask in [(3,1,1,[[1,0,1,0],[0,1,0,1],[1,1,1,0],[1,0,0,1]]),
                                (2,8,1,[[1,0],[0,1]])]:
        for r,row in enumerate(mask):
            for c,v in enumerate(row):
                if v:g[top+r][left+c]=color
    return g

@pytest.fixture(scope='module')
def runtime():
    p=HOME/'workspace/parametric/native_family.py'
    spec=importlib.util.spec_from_file_location('_rival_totality_family',p)
    F=importlib.util.module_from_spec(spec);sys.modules[spec.name]=F
    spec.loader.exec_module(F)
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    assert identity['backend']=='racket' and identity['protected'] is True
    try:yield F,apply
    finally:bridge.close()

@pytest.mark.parametrize('name',['template_reading_order','first_target_template_for_all','next_target_color_template'])
def test_wrong_association_is_total_for_mixed_rectangle_sizes(runtime,name):
    F,execute=runtime
    grid=mixed_sizes()
    for mode in ('carve','stamp'):
        setting={'ink_mode':mode}
        output=execute(F.rival_programs(setting)[name],grid)
        assert len(output)==14 and all(len(row)==8 for row in output)
        assert all(type(v) is int and 0<=v<=9 for row in output for v in row)
        assert output!=execute(F.program(setting),grid)

@pytest.mark.parametrize('mode',['carve','stamp'])
def test_all_declared_shortcuts_execute_on_original_input(runtime,mode):
    import json
    F,execute=runtime
    raw=ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json'
    grid=json.loads(raw.read_text())['58f5dbd5']['train'][0]['input']
    correct=execute(F.program({'ink_mode':mode}),grid)
    rivals=F.rival_programs({'ink_mode':mode})
    assert len(rivals)==11 and len(set(rivals.values()))==11
    for name,source in rivals.items():
        output=execute(source,grid)
        assert len(output)==len(correct) and all(len(row)==len(correct[0]) for row in output),name
        assert all(type(v) is int and 0<=v<=9 for row in output for v in row),name

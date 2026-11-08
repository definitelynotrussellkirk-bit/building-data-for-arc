"""Opt-in, rule-independent component ownership gate regression tests."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import pytest

TOOL=Path(__file__).resolve().parent.parent/'workspace/component_contract.py'


def run_cli(tmp_path, grid, **contract):
    source=tmp_path/'input.json'; source.write_text(json.dumps(grid))
    roles=tmp_path/'contract.json'; roles.write_text(json.dumps({'background':0,'wall_colors':[5], 'connectivity':4,'max_seed_cells_per_component':1,**contract}))
    output=tmp_path/'report.json'
    result=subprocess.run([sys.executable,str(TOOL),'--input',str(source),'--contract',str(roles),'--out',str(output)],capture_output=True,text=True)
    return result, output


def test_cli_detects_independent_component_collision(tmp_path):
    # Replacing the actual connectivity traversal with assumed geometric rooms
    # (or trusting a generator's self_check) must make this fail.
    result,path=run_cli(tmp_path,[[1,0,5],[0,2,5],[5,5,0]])
    assert result.returncode==1, result.stderr
    data=json.loads(path.read_text())
    assert data['status']=='violation'
    assert data['violations'][0]['seed_cells']==[[0,0,1],[1,1,2]]
    assert data['violations'][0]['component_size']==4
    assert len(data['input_sha256'])==64


def test_cli_accepts_seeds_separated_by_walls(tmp_path):
    result,path=run_cli(tmp_path,[[1,0,5,0,2],[0,0,5,0,0]])
    assert result.returncode==0,result.stderr
    assert json.loads(path.read_text())['violations']==[]


def load_tool():
    spec=importlib.util.spec_from_file_location('component_contract',TOOL)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_connectivity_is_explicit():
    m=load_tool(); grid=[[1,5],[5,2]]
    assert not m.analyze(grid,background=0,wall_colors=[5],connectivity=4,max_seed_cells_per_component=1)['violations']
    assert m.analyze(grid,background=0,wall_colors=[5],connectivity=8,max_seed_cells_per_component=1)['violations']


def test_intentional_competing_seeds_can_opt_out():
    m=load_tool(); grid=[[1,0,2]]
    assert not m.analyze(grid,background=0,wall_colors=[5],connectivity=4,max_seed_cells_per_component=2)['violations']


@pytest.mark.parametrize('grid',[[],[[]],[[0],[0,1]],[[True]],[[1.2]],[[10]],None])
def test_malformed_grids_rejected(grid):
    with pytest.raises(ValueError):
        load_tool().analyze(grid,background=0,wall_colors=[5],connectivity=4,max_seed_cells_per_component=1)


@pytest.mark.parametrize('overrides',[{'connectivity':6},{'background':5},{'wall_colors':[True]},{'max_seed_cells_per_component':-1},{'max_seed_cells_per_component':True}])
def test_invalid_contract_rejected(overrides):
    options=dict(background=0,wall_colors=[5],connectivity=4,max_seed_cells_per_component=1);options.update(overrides)
    with pytest.raises(ValueError):
        load_tool().analyze([[1]],**options)


def test_cli_invalid_data_is_error_not_clean_pass(tmp_path):
    result,path=run_cli(tmp_path,[[True]])
    assert result.returncode==2
    assert json.loads(path.read_text())['status']=='error'


def test_result_is_deterministic_and_input_preserved():
    import copy
    m=load_tool();g=[[1,0,2],[5,5,5],[3,0,0]];before=copy.deepcopy(g)
    options=dict(background=0,wall_colors=[5],connectivity=4,max_seed_cells_per_component=1)
    assert m.analyze(g,**options)==m.analyze(g,**options)
    assert g==before

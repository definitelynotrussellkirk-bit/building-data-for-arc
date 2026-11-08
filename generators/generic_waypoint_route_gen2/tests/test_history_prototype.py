"""Independent literal next-state cases and source-bound authoring guarantees."""
import importlib.util
import json
from pathlib import Path
import random

import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]
POINTS=[(12,1),(12,4),(3,4),(3,9),(8,9),(8,6),(5,6),(5,11)]


def adapter():
    source=HOME/'workspace/parametric/adapter.py'
    spec=importlib.util.spec_from_file_location('_typed_history_adapter_test',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def literal_panel(index,*,keep=True):
    grid=[[0]*13 for _ in range(16)];r,c=POINTS[index]
    previous=POINTS[index-1] if index else POINTS[1]
    dr,dc=(r-previous[0],c-previous[1]) if index else (previous[0]-r,previous[1]-c)
    dr,dc=(dr>0)-(dr<0),(dc>0)-(dc<0)
    grid[r][c]=4;grid[r-dr][c-dc]=8
    if keep:
        for rr,cc in POINTS[index+1:]:grid[rr][cc]=4
    return grid


def literal_input(previous_index):
    return [left+[7]+right for left,right in zip(literal_panel(previous_index),literal_panel(2))]


@pytest.fixture(scope='module')
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    with RacketBridge(timeout=10) as bridge:
        assert bridge.runtime_identity['protected'] is True
        def apply(program,grid):
            bridge.define_grid('history-test-grid',grid)
            return bridge.eval_text('('+wrap_rule(program)+' history-test-grid)')
        yield apply


def test_default_is_the_exact_existing_canonical_program():
    programs={row['program_solution'] for line in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines()
              if (row:=json.loads(line))['task_id']=='generic_waypoint_route_gen2'}
    assert programs=={adapter().program({'mode':'finish'})}


@pytest.mark.parametrize('mode,previous,target,keep',[
    ('finish',1,7,False),('finish',0,7,False),('history',1,3,True),('history',0,4,True)])
def test_literal_history_and_final_route_labels_match_racket(racket,mode,previous,target,keep):
    module=adapter();grid=literal_input(previous);expected=literal_panel(target,keep=keep)
    assert module.transform(grid,mode)==expected
    assert racket(module.program({'mode':mode}),grid)==expected


def test_same_final_panel_needs_different_history_outputs():
    module=adapter();first,second=literal_input(1),literal_input(0)
    assert [row[14:] for row in first]==[row[14:] for row in second]
    assert module.transform(first,'history')!=module.transform(second,'history')
    assert module.transform(first,'finish')==module.transform(second,'finish')


def test_inputs_are_setting_neutral_deterministic_and_do_not_use_global_rng():
    module=adapter();before=random.getstate()
    finish=module.generate(17,{'mode':'finish'},3,4);history=module.generate(17,{'mode':'history'},3,4)
    inputs=lambda episode:[pair['input'] for pair in episode['train']+episode['test']]
    assert inputs(finish)==inputs(history)
    assert finish==module.generate(17,{'mode':'finish'},3,4) and random.getstate()==before
    assert len({json.dumps(grid) for grid in inputs(finish)})==7
    assert len(history['train'])==3 and len(history['test'])==4
    assert history['train'][0]['output']!=history['train'][1]['output']
    assert [row[len(row)//2+1:] for row in history['train'][0]['input']]==[row[len(row)//2+1:] for row in history['train'][1]['input']]
    assert (len(history['test'][-1]['input']),len(history['test'][-1]['input'][0]))==(30,29)


@pytest.mark.parametrize('seed,settings,demos,queries',[(True,{'mode':'finish'},3,4),
    (0,{'mode':'wrong'},3,4),(0,{'mode':'finish','unknown':1},3,4),
    (0,{'mode':'finish'},2,4),(0,{'mode':'finish'},3,0),(0,{'mode':'finish'},3,True)])
def test_bad_requests_fail_explicitly(seed,settings,demos,queries):
    with pytest.raises(ValueError):adapter().generate(seed,settings,demos,queries)


def test_boolean_grid_cells_are_not_integer_labels():
    grid=literal_input(1);grid[0][0]=False
    with pytest.raises(ValueError):adapter().transform(grid,'history')


@pytest.mark.parametrize('mode',['finish','history'])
def test_generated_demonstrations_eliminate_declared_shortcuts_without_query_answers(mode):
    module=adapter();episode=module.generate(17,{'mode':mode},3,4)
    certificate=module.certificate(episode['train'],[p['input'] for p in episode['test']])
    assert certificate['survivors']==[mode]
    assert certificate['same_last_panel_witness'] is True
    assert certificate['last_panel_only_refuted'] is (mode=='history')


def test_export_and_saved_replay_keep_public_ids_labels_and_settings_separate(tmp_path):
    path=HOME/'workspace/parametric/exports.py';spec=importlib.util.spec_from_file_location('_waypoint_history_exports',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    jobs=[{'seed':seed,'settings':{'mode':mode}} for seed in [0,17] for mode in ['finish','history']]
    out=tmp_path/'episodes';report=module.export_batch(out,jobs,demos=3,queries=4)
    assert report['episodes']==4 and report['query_labels']==16 and report['training_admitted'] is False
    assert report['racket']['protected'] is True
    replay=module.verify_export(out);assert replay['episodes']==4 and replay['query_labels']==16
    for f in (out/'public').glob('*.json'):
        import hashlib
        assert f.stem==hashlib.sha256(f.read_bytes()).hexdigest()
        public=json.loads(f.read_bytes());assert set(public)=={'train','test'}
        assert all(set(pair)=={'input'} for pair in public['test'])
    with pytest.raises(FileExistsError):module.export_batch(out,jobs)
    with pytest.raises(ValueError,match='[Dd]uplicate'):module.export_batch(tmp_path/'duplicates',[jobs[0],jobs[0]])
    assert not (tmp_path/'duplicates').exists()


def exports_module():
    source=HOME/'workspace/parametric/exports.py';spec=importlib.util.spec_from_file_location('_history_exports_case',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


@pytest.fixture(scope='module')
def saved_export(tmp_path_factory):
    module=exports_module();out=tmp_path_factory.mktemp('history-parent')/'export'
    module.export_batch(out,[{'seed':17,'settings':{'mode':mode}} for mode in ['finish','history']])
    return out


def alter_private(out,change):
    import hashlib
    manifest=json.loads((out/'manifest.json').read_text())
    for record in manifest['records']:
        path=out/record['private'];private=json.loads(path.read_text())
        if private['settings']['mode']=='history':break
    change(private);path.write_text(json.dumps(private))
    manifest['files'][record['private']]=hashlib.sha256(path.read_bytes()).hexdigest()
    (out/'manifest.json').write_text(json.dumps(manifest))


def test_unlisted_public_manifest_file_is_not_ignored(saved_export,tmp_path):
    import shutil
    out=tmp_path/'copy';shutil.copytree(saved_export,out)
    (out/'public/manifest.json').write_text('{"test":[{"output":[[9]]}]}')
    with pytest.raises(ValueError,match='inventory'):exports_module().verify_export(out)


def test_listed_but_unreferenced_public_file_is_rejected(saved_export,tmp_path):
    import hashlib
    import shutil
    out=tmp_path/'copy';shutil.copytree(saved_export,out)
    extra=out/'public/extra.json';extra.write_text('{"output":[[9]]}')
    manifest=json.loads((out/'manifest.json').read_text())
    manifest['files']['public/extra.json']=hashlib.sha256(extra.read_bytes()).hexdigest()
    (out/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='inventory'):exports_module().verify_export(out)


def test_saved_seed_must_reproduce_the_declared_episode(saved_export,tmp_path):
    import shutil
    out=tmp_path/'copy';shutil.copytree(saved_export,out)
    alter_private(out,lambda private:private.update(seed=999))
    with pytest.raises(ValueError,match='seed|reproduce'):exports_module().verify_export(out)


@pytest.mark.parametrize('location',['manifest','private'])
def test_false_parent_lineage_cannot_pass_replay(saved_export,tmp_path,location):
    import shutil
    out=tmp_path/'copy';shutil.copytree(saved_export,out)
    if location=='manifest':
        manifest=json.loads((out/'manifest.json').read_text());manifest['source_task_id']='00000000'
        (out/'manifest.json').write_text(json.dumps(manifest))
    else:alter_private(out,lambda private:private.update(source_task_id='00000000'))
    with pytest.raises(ValueError,match='metadata|lineage'):exports_module().verify_export(out)


@pytest.mark.parametrize('kind',['bool','float','certificate'])
def test_numeric_aliases_in_saved_labels_and_certificates_are_rejected(saved_export,tmp_path,kind):
    import shutil
    out=tmp_path/'copy';shutil.copytree(saved_export,out)
    def mutate(private):
        if kind=='certificate':private['certificate']['last_panel_only_refuted']=1
        else:
            cell=private['test'][0]['output'][0][0]
            private['test'][0]['output'][0][0]=(False if cell==0 else True) if kind=='bool' else float(cell)
    alter_private(out,mutate)
    with pytest.raises(ValueError):exports_module().verify_export(out)


def test_private_changes_do_not_change_public_identity(saved_export):
    import copy
    from reviewer_support import public_challenge_id
    module=exports_module();manifest=json.loads((saved_export/'manifest.json').read_text());private=json.loads((saved_export/manifest['records'][0]['private']).read_text())
    identity=public_challenge_id(module.public_projection(private));changed=copy.deepcopy(private)
    changed['seed']=999;changed['settings']={'mode':'secret'};changed['program_sha256']='f'*64;changed['test'][0]['output']=[[9]]
    assert public_challenge_id(module.public_projection(changed))==identity
    changed['test'][0]['input'][0][0]=(changed['test'][0]['input'][0][0]+1)%10
    assert public_challenge_id(module.public_projection(changed))!=identity

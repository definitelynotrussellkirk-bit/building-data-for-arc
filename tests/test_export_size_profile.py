"""Literal geometry and pair denominators in verified controller exports."""
import hashlib
import importlib
import json
from pathlib import Path

import pytest

from arcpuzzles.datasets import _identity, verify_dataset


def implementation():
    assert (Path(__file__).resolve().parents[1]/'src/arcpuzzles/dataset_profile.py').is_file(), 'Missing static export size profiler'
    return importlib.import_module('arcpuzzles.dataset_profile')


def grid(h,w,color=0):return [[color]*w for _ in range(h)]


def save(root,public,private):
    root.mkdir(exist_ok=True)
    for name,rows in [('public.jsonl',public),('labels.private.jsonl',private)]:
        (root/name).write_text(''.join(json.dumps(row)+'\n' for row in rows))
    files={name:{'bytes':(root/name).stat().st_size,'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest()}
           for name in ['public.jsonl','labels.private.jsonl']}
    manifest={'schema':'arcpuzzles-dataset-v1','status':'complete','options':{'style':'episodes'},
              'accepted_episodes':len(public),'files':files}
    manifest['dataset_id']=_identity(manifest);(root/'manifest.json').write_text(json.dumps(manifest))
    return manifest


@pytest.fixture
def exported(tmp_path):
    public=[{'episode_id':'a','train':[{'input':grid(30,30),'output':grid(20,1,2)},
                                     {'input':grid(10,5),'output':[[1]]}],
             'test':[{'input':grid(20,30)},{'input':grid(30,30,1)},{'input':grid(5,30)},{'input':[[3]]}]},
            {'episode_id':'b','train':[{'input':[[0]],'output':grid(30,30,5)}],
             'test':[{'input':grid(10,10)}]}]
    private=[{'episode_id':'a','task_id':'literal-a','provenance':{},
              'test_outputs':[[[1]],grid(21,1),grid(30,30),grid(5,4)]},
             {'episode_id':'b','task_id':'literal-b','provenance':{},'test_outputs':[grid(20,20)]}]
    root=tmp_path/'export';manifest=save(root,public,private)
    assert verify_dataset(root)==manifest
    return root,public,private,manifest


def test_literal_query_geometry_and_pair_denominators(exported):
    root,_,_,manifest=exported;report=implementation().profile_dataset(root)
    assert report['schema']=='arcpuzzles-export-size-profile-v1' and report['visibility']=='controller_only'
    assert report['dataset_id']==manifest['dataset_id'] and report['observed_episodes']==2
    pairs=report['supervision'];assert pairs['demonstration_pairs']==3 and pairs['query_pairs']==5
    assert pairs['query_pairs_per_demonstration_pair']==pytest.approx(5/3)
    assert pairs['queries_per_episode']=={'1':1,'4':1} and pairs['demos_per_episode']=={'1':1,'2':1}
    assert pairs['episodes_with_four_distinct_novel_queries']=={'count':1,'fraction':0.5}
    sizes=report['grids']['query_inputs'];assert sizes['grids']==5 and sizes['cells']==1751
    assert sizes['exact_30x30']=={'count':1,'fraction':0.2}
    assert sizes['longest_side_at_least_20']=={'count':3,'fraction':0.6}
    assert sizes['longest_side_over_20']=={'count':3,'fraction':0.6}
    assert sizes['both_sides_at_least_20']=={'count':2,'fraction':0.4}
    assert sizes['area_at_least_400']=={'count':2,'fraction':0.4}
    outputs=report['grids']['query_outputs'];assert outputs['cells']==1342 and outputs['median_area']==21
    assert outputs['longest_side_at_least_20']['count']==3 and outputs['longest_side_over_20']['count']==2
    assert pairs['query_output_cells_per_demo_output_cell']==pytest.approx(1342/921)
    assert report['verification']['racket_reexecuted'] is False


def test_detailed_shape_histograms_are_opt_in(exported):
    root=exported[0];simple=implementation().profile_dataset(root)
    assert 'shapes' not in simple['grids']['query_inputs']
    detailed=implementation().profile_dataset(root,detailed_shapes=True)
    assert detailed['grids']['query_inputs']['shapes']=={'20x30':1,'30x30':1,'5x30':1,'1x1':1,'10x10':1}


def test_empty_episode_view_uses_unknown_fractions(tmp_path):
    root=tmp_path/'empty';save(root,[],[]);report=implementation().profile_dataset(root)
    assert report['observed_episodes']==0 and report['supervision']['query_pairs_per_demonstration_pair'] is None
    assert report['supervision']['episodes_with_four_distinct_novel_queries']=={'count':0,'fraction':None}
    for summary in report['grids'].values():
        assert summary['grids']==0 and summary['median_area'] is None and summary['exact_30x30']['fraction'] is None


def test_repeated_and_previously_shown_queries_are_reported_not_hidden(exported):
    root,public,private,_=exported
    public[0]['test'][1]['input']=public[0]['test'][0]['input']
    public[0]['test'][2]['input']=public[0]['train'][0]['input'];save(root,public,private)
    counts=implementation().profile_dataset(root)['supervision']
    assert counts['repeated_query_inputs_within_episodes']==1
    assert counts['query_inputs_repeating_demonstrations']==1
    assert counts['episodes_with_four_distinct_novel_queries']['count']==0


@pytest.mark.parametrize('bad',[[],[[]],[[0],[0,1]],[[False]],[[1.0]],[[10]],[[0]*31]])
def test_even_hash_consistent_malformed_grids_fail(exported,bad):
    root,public,private,_=exported;private[0]['test_outputs'][0]=bad;save(root,public,private)
    with pytest.raises(ValueError,match='grid'):implementation().profile_dataset(root)


def test_hash_tampering_is_rejected_before_a_profile_is_returned(exported):
    root=exported[0];(root/'public.jsonl').write_text('{}\n')
    with pytest.raises(ValueError,match='changed|inventory'):implementation().profile_dataset(root)


def test_profile_does_not_modify_any_artifact(exported):
    root=exported[0];before={p.name:p.read_bytes() for p in root.iterdir()}
    implementation().profile_dataset(root)
    assert before=={p.name:p.read_bytes() for p in root.iterdir()}


def test_cli_default_stays_manifest_and_sizes_is_explicit(exported,library,capsys):
    from arcpuzzles.cli import main
    root,_,_,manifest=exported
    assert main(['--library',str(library),'inspect-export',str(root)])==0
    assert json.loads(capsys.readouterr().out)==manifest
    assert main(['--library',str(library),'inspect-export',str(root),'--sizes'])==0
    assert json.loads(capsys.readouterr().out)['observed_episodes']==2


@pytest.mark.parametrize('changed',['public','manifest'])
def test_changed_snapshot_is_rejected(exported,monkeypatch,changed):
    root=exported[0];module=implementation();original=module.verify_dataset
    def verified_then_changed(path):
        result=original(path)
        if changed=='public':(root/'public.jsonl').write_text('{}\n')
        else:
            p=root/'manifest.json';p.write_bytes(p.read_bytes()+b' ')
        return result
    monkeypatch.setattr(module,'verify_dataset',verified_then_changed)
    with pytest.raises(ValueError,match='changed'):module.profile_dataset(root)


def test_detailed_flag_requires_sizes_and_api_requires_a_boolean(exported,library,capsys):
    from arcpuzzles.cli import main
    with pytest.raises(ValueError,match='boolean'):implementation().profile_dataset(exported[0],detailed_shapes=1)
    assert main(['--library',str(library),'inspect-export',str(exported[0]),'--detailed-shapes'])==1
    assert 'requires --sizes' in capsys.readouterr().err


def test_queries_without_demonstrations_have_undefined_demo_ratios(tmp_path):
    root=tmp_path/'no-demos';public=[{'episode_id':'a','train':[],'test':[{'input':[[1]]}]}]
    private=[{'episode_id':'a','task_id':'literal','provenance':{},'test_outputs':[[[2]]]}];save(root,public,private)
    counts=implementation().profile_dataset(root)['supervision']
    assert counts['query_pairs']==1 and counts['demonstration_pairs']==0
    assert counts['query_pairs_per_demonstration_pair'] is None and counts['query_output_cells_per_demo_output_cell'] is None

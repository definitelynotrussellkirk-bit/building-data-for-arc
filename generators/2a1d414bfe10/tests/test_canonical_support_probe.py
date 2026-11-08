"""Generic support comparison and input-only adapter contract."""
import importlib.util
import json
from pathlib import Path
import pytest

# Workspace and tests are siblings in both supported layouts; no canonical lookup.
PATH=Path(__file__).resolve().parent.with_name('workspace')/'probe_canonical_support.py'
spec=importlib.util.spec_from_file_location('support_probe',PATH)
probe=importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_absent_canonical_boolean_is_warning_not_error():
    result=probe.compare_support([{'flag':True},{'flag':False}],{'hard':[{'flag':True}]*4})
    assert result['features']['flag']['missing']['hard']==[{'type':'bool','value':False}]
    assert result['features']['flag']['generated']['hard']==[{'type':'bool','value':True,'count':4}]
    assert len(result['warnings'])==1
    json.dumps(result,allow_nan=False)


def test_mixed_scalar_types_are_distinct_categories():
    result=probe.compare_support([{'x':True},{'x':1},{'x':'1'},{'x':None}],{'easy':[{'x':1}]})
    assert result['features']['x']['missing']['easy']==[
        {'type':'NoneType','value':None},{'type':'bool','value':True},{'type':'str','value':'1'}]


def test_missing_extractor_field_is_not_silently_dropped():
    with pytest.raises(ValueError,match='fields'):
        probe.compare_support([{'x':True,'y':False}],{'easy':[{'x':True}]})


def test_complete_support_needs_no_warning():
    result=probe.compare_support([{'x':False},{'x':True},{'x':True}],
                                 {'easy':[{'x':True},{'x':False}], 'hard':[{'x':False},{'x':True}]})
    assert result['warnings']==[]
    assert result['features']['x']['canonical']==[
        {'type':'bool','value':False,'count':1},{'type':'bool','value':True,'count':2}]


def test_empty_canonical_is_explicit_and_has_no_missing_values():
    result=probe.compare_support([],{'easy':[{'x':False}]})
    assert result['canonical_rows']==0
    assert result['features']['x']['canonical']==[]
    assert result['features']['x']['missing']['easy']==[]
    assert result['warnings']==[]


def test_empty_generated_band_warns_for_all_canonical_values():
    result=probe.compare_support([{'x':True}],{'hard':[]})
    assert result['generated_rows_by_band']=={'hard':0}
    assert result['features']['x']['missing']['hard']==[{'type':'bool','value':True}]
    assert probe.compare_support([], {})['features']=={}


@pytest.mark.parametrize('canonical,bands', [
    ([{'x':[]}],{'easy':[]}), ([{'x':float('nan')}],{'easy':[]}),
    ([{}],{'easy':[]}), ([{'x':True}],{'easy':[None]}),
    ([{'x':True}],{1:[]}), ([{'x':True}],[{'x':True}]),
])
def test_malformed_rows_and_collections_fail(canonical,bands):
    with pytest.raises(ValueError):
        probe.compare_support(canonical,bands)


def test_adapter_recognizes_mixed_boxes_and_interleaving_without_answers():
    grid=[[1,1,0,0,2,0],[1,0,0,0,2,0],[0,0,0,0,2,0],
          [0,0,0,0,0,0],[3,3,3,0,0,0]]
    features=probe.extract_features(grid)
    assert features['equal_normalized_bboxes'] is False
    assert features['blank_internal_row'] is True
    assert features['blank_internal_column'] is True
    assert features['all_shapes_five_cells'] is False

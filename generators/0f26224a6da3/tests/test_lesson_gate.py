"""Tests for the reusable post-assembly admission gate."""
import copy
import importlib.util
from pathlib import Path
import pytest

PATH=Path(__file__).resolve().parents[1]/'workspace'/'check_assembled_lessons.py'

@pytest.fixture
def check():
    assert PATH.exists(), 'post-assembly gate not implemented'
    spec=importlib.util.spec_from_file_location('assembly_gate',PATH)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.check_episode


def test_refuted_competitor_passes(check):
    ep={'train':[{'input':[[1]],'output':[[2]]}],'test':[{'input':[[3]],'output':[[4]]}]}
    assert check(ep,{'identity':lambda g:g})['passed']


def test_query_danger_is_reported(check):
    ep={'train':[{'input':[[1]],'output':[[1]]}],'test':[{'input':[[3]],'output':[[4]]}]}
    report=check(ep,{'identity':lambda g:g})
    assert not report['passed']
    assert report['survivors']==['identity']
    assert report['query_disagreements']=={'identity':[0]}


def test_same_query_survivor_still_flags_underinformative_lesson(check):
    ep={'train':[{'input':[[1]],'output':[[1]]}],'test':[{'input':[[3]],'output':[[3]]}]}
    report=check(ep,{'identity':lambda g:g})
    assert not report['passed']
    assert report['query_disagreements']=={'identity':[]}


def test_rival_exception_is_not_silently_dropped(check):
    def broken(g):raise RuntimeError('probe failed')
    ep={'train':[{'input':[[1]],'output':[[2]]}],'test':[{'input':[[3]],'output':[[4]]}]}
    report=check(ep,{'broken':broken})
    assert not report['passed'] and report['errors']


def test_missing_private_labels_is_explicit_failure(check):
    ep={'train':[{'input':[[1]],'output':[[2]]}],'test':[{'input':[[3]]}]}
    report=check(ep,{'identity':lambda g:g})
    assert not report['passed'] and 'output' in str(report['errors'])


def test_no_contract_is_not_a_pass(check):
    report=check({'train':[],'test':[]},{})
    assert not report['passed'] and report['errors']


def test_mutating_rival_does_not_mutate_input(check):
    def mutating(g):g[0][0]=5;return g
    ep={'train':[{'input':[[1]],'output':[[2]]}],'test':[{'input':[[3]],'output':[[4]]}]}
    before=copy.deepcopy(ep);check(ep,{'mutating':mutating})
    assert ep==before

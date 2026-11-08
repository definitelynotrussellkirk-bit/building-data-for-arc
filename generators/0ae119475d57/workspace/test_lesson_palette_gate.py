import copy
import pytest
from lesson_palette_gate import analyze_challenge


def pair(top, bottom):
    return {'input': [[top,top,0,0],[5,5,5,5],[bottom,0,bottom,0]],
            'output': [[bottom,top,bottom,0]]}


def test_flags_color_rank_confounded_demos_without_query_labels():
    challenge={'train':[pair(9,4),pair(7,1)], 'test':[{'input':pair(2,7)['input']}]}
    before=copy.deepcopy(challenge)
    report=analyze_challenge(challenge)
    assert report['status']=='ambiguous'
    assert report['ambiguous_query_count']==1
    assert set(report['surviving_candidates'])=={'bottom_overlay','nonzero_minimum'}
    assert challenge==before


def test_contrastive_demo_removes_the_rival():
    challenge={'train':[pair(9,4),pair(2,7)], 'test':[{'input':pair(2,7)['input']}]}
    report=analyze_challenge(challenge)
    assert report['status']=='passed'
    assert report['surviving_candidates']==['bottom_overlay']


def test_survivors_that_agree_on_query_do_not_trigger_false_rejection():
    report=analyze_challenge({'train':[pair(9,4)], 'test':[{'input':pair(7,1)['input']}]})
    assert report['status']=='passed'
    assert len(report['surviving_candidates'])==2


def test_bad_shapes_and_no_fit_are_not_green():
    malformed={'train':[pair(9,4)], 'test':[{'input':[[1],[]]}]}
    with pytest.raises(ValueError):
        analyze_challenge(malformed)
    bad=pair(9,4)
    bad['output']=[[8,8,8,8]]
    report=analyze_challenge({'train':[bad], 'test':[{'input':pair(7,1)['input']}]})
    assert report['status']=='unsupported'


def test_does_not_accept_query_labels_or_empty_demonstrations():
    with pytest.raises(ValueError):
        analyze_challenge({'train':[pair(9,4)],'test':[pair(2,7)]})
    with pytest.raises(ValueError):
        analyze_challenge({'train':[],'test':[{'input':pair(2,7)['input']}]})

"""Public authoring transport must reach its owner gate without prior catalog approval."""
import json
from pathlib import Path
import sys
import types

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_draw import draw_main
from arcpuzzles.review_full_return import build_full_return
from arcpuzzles.review_full_collect import collect_full_returns
from arcpuzzles.review_full_integrate import integrate_full_candidate
from arcpuzzles.review_parametric_admission import admit_assignment
from arcpuzzles.review_public_creation import PUBLIC_WORK_POLICY
from test_review_public_creation import public_packet


def helper_stub(monkeypatch, callback):
    module=types.ModuleType('arcpuzzles.review_public_admission')
    module.verified_coverage=lambda root:set()
    module.admit_public_creation=callback
    monkeypatch.setitem(sys.modules,'arcpuzzles.review_public_admission',module)


@pytest.mark.parametrize('statuses,expected', [(['accepted','accepted'],True), (['accepted','blocked'],False), (['blocked','accepted'],False)])
def test_public_pair_objective_requires_both_owner_acceptances(monkeypatch,statuses,expected):
    ids=['public_eval_11111111','public_eval_22222222']
    targets=[{'task_id':tid,'generator':{}} for tid in ids]
    contract={'schema':'arcpuzzles-full-assignment-v3','assignment_id':'review-1234567890abcdef',
              **targets[0],'repair_targets':targets,'work_policy':PUBLIC_WORK_POLICY}
    calls=[]
    def admit(catalog,scoped,outcome,archive,*,withheld_paths=()):
        i=ids.index(scoped['task_id']);calls.append((scoped['task_id'],withheld_paths))
        return {'task_id':scoped['task_id'],'status':statuses[i],'objective_met':statuses[i]=='accepted'}
    helper_stub(monkeypatch,admit)
    result=admit_assignment(None,contract,{tid:{} for tid in ids},Path('unused.zip'),withheld_paths={ids[1]:['withheld.py']})
    assert result['objective_met'] is expected
    assert calls==[(ids[0],()),(ids[1],['withheld.py'])]
    assert len(result['targets'])==2


@pytest.mark.parametrize('prior_parent_change',['none','status','source'])
@pytest.mark.parametrize('source_outcome',['repaired','prototype'])
def test_new_home_integrates_source_without_ordinary_approval_or_catalog_lookup(library,tmp_path,monkeypatch,prior_parent_change,source_outcome):
    calls=[]
    def admit(catalog,contract,outcome,archive,*,withheld_paths=()):
        tid=contract['task_id'];home=catalog.root/'generators'/tid
        assert (home/'generator.py').read_text()=='# New unapproved source\n'
        assert (home/'reference.rkt').read_text()=='(rule! (lambda (g) g))'
        parent=json.loads((home/'workspace/public-parent.json').read_text())
        assert parent['task_id']==tid
        assert not withheld_paths
        calls.append(tid)
        return {'task_id':tid,'status':'blocked','objective_met':False,'blocker':'Deliberate owner gate stub'}
    helper_stub(monkeypatch,admit)
    def forbid(*args,**kwargs):
        raise AssertionError('Ordinary approval must never approve new public placeholders')
    monkeypatch.setattr('arcpuzzles.review_approval.approve_reviews',forbid)
    packet=public_packet(library,tmp_path)
    contract=draw_main(packet,bytes(32))
    results=json.loads((packet/'RESULTS.json').read_text())
    for outcome in results['repair_targets']:
        home=packet/'repo/generators'/outcome['task_id']
        (home/'generator.py').write_text('# New unapproved source\n')
        (home/'reference.rkt').write_text('(rule! (lambda (g) g))')
        (home/'notes.md').write_text('Partial build; owner registration remains pending.\n')
        outcome.update(outcome=source_outcome,changed_components=['generator','racket','tests_notes'])
    (packet/'RESULTS.json').write_text(json.dumps(results))
    (packet/'REVIEW.md').write_text('Authoring source; preflight not yet complete.\n')
    (packet/'FEEDBACK_TO_CODEX.md').write_text('No extra feedback.\n')
    returned=build_full_return(packet,tmp_path/'review_response_public.zip')
    collected=collect_full_returns(library/'REVIEW',tmp_path)
    receipt=next(r for r in collected['receipts'] if r.get('zip_sha256')==returned['zip_sha256'])
    if prior_parent_change!='none':
        first=contract['repair_targets'][0]['task_id']
        parent=json.loads((packet/f'repo/generators/{first}/workspace/public-parent.json').read_text())
        if prior_parent_change=='status':parent['needs_creation']=not parent['needs_creation']
        else:parent['challenge_sha256']='0'*64
        path=library/f'generators/{first}/workspace/public-parent.json'
        path.parent.mkdir(parents=True);path.write_text(json.dumps(parent))
    if prior_parent_change=='source':
        with pytest.raises(ValueError,match='provenance collides'):
            integrate_full_candidate(Catalog(library),library/'REVIEW',contract['assignment_id'],receipt['version'],
                  {'generator','racket','tests_notes'},reviewer_reported=True)
        assert not calls and not (library/f'generators/{first}/generator.py').exists()
        return
    before=(library/'catalog/puzzles.jsonl').read_bytes()
    integrated=integrate_full_candidate(Catalog(library),library/'REVIEW',contract['assignment_id'],receipt['version'],
                  {'generator','racket','tests_notes'},reviewer_reported=True)
    assert calls==[r['task_id'] for r in contract['repair_targets']]
    assert integrated['objective_met'] is False and len(integrated['parametric_admissions'])==2
    assert integrated['approval']['status']=='pending_public_registration'
    assert (library/'catalog/puzzles.jsonl').read_bytes()==before

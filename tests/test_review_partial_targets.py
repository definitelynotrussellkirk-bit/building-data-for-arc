"""Owner can accept a fresh half without overwriting a colliding accepted half."""
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from arcpuzzles.review_full_draw import draw_main
from arcpuzzles.review_full_return import build_full_return
from arcpuzzles.review_full_collect import collect_full_returns
from arcpuzzles.review_full_integrate import integrate_full_candidate
from test_review_full_draw import _packet
from test_review_two_parametric import POLICY, reports


def prepared(library, tmp_path):
    packet = _packet(library, tmp_path, repair_target_count=2, work_policy=POLICY)
    c = draw_main(packet, bytes(32))
    result = json.loads((packet/'RESULTS.json').read_text())
    for row in result['repair_targets']:
        home = packet/f"repo/generators/{row['task_id']}/workspace/parametric"
        home.mkdir(parents=True, exist_ok=True)
        (home/'candidate.py').write_text('# incoming candidate\n')
        row.update(outcome='prototype', summary='Partial source retained', changed_components=['tests_notes'])
    (packet/'RESULTS.json').write_text(json.dumps(result))
    for name in ['REVIEW.md', 'FEEDBACK_TO_CODEX.md']:
        (packet/name).write_text('Incomplete fixtures; no native acceptance claimed.\n')
    b = build_full_return(packet, tmp_path/'review_response_partial.zip')
    collected = collect_full_returns(library/'REVIEW', tmp_path)
    r = next(r for r in collected['receipts'] if r['zip_sha256']==b['zip_sha256'])
    return c, r


def test_selected_target_integrates_and_colliding_half_is_untouched(library, tmp_path):
    c, receipt = prepared(library, tmp_path)
    first, second = [t['task_id'] for t in c['repair_targets']]
    other = library/f'generators/{second}/workspace/parametric/candidate.py'
    other.parent.mkdir(parents=True, exist_ok=True)
    other.write_text('# accepted owner source that must survive\n')
    admission = library/f'generators/{second}/evidence/parametric-admission-current.json'
    admission.parent.mkdir(parents=True, exist_ok=True)
    admission.write_text('{"status":"accepted","sentinel":true}\n')
    result = integrate_full_candidate(Catalog(library), library/'REVIEW', c['assignment_id'],
        receipt['version'], {'tests_notes'}, reviewer_reported=True, selected_targets={first})
    assert (library/f'generators/{first}/workspace/parametric/candidate.py').read_text()=='# incoming candidate\n'
    assert other.read_text()=='# accepted owner source that must survive\n'
    assert admission.read_text()=='{"status":"accepted","sentinel":true}\n'
    assert result['objective_met'] is False
    by_id={r['task_id']:r for r in result['parametric_admissions']}
    assert by_id[second]['status']=='not_selected'
    assert all(not p.startswith(f'generators/{second}/') for p in result['files'])


@pytest.mark.parametrize('selected',[set(), {'not-assigned'}])
def test_invalid_selection_refused_before_source_writes(library,tmp_path,selected):
    c,r=prepared(library,tmp_path)
    with pytest.raises(ValueError,match='selected|selection|assigned'):
        integrate_full_candidate(Catalog(library),library/'REVIEW',c['assignment_id'],r['version'],
                                 {'tests_notes'},reviewer_reported=True,selected_targets=selected)
    for t in c['repair_targets']:
        assert not (library/f"generators/{t['task_id']}/workspace/parametric/candidate.py").exists()


def test_partial_native_success_is_never_round_complete(monkeypatch,tmp_path):
    from arcpuzzles import review_parametric_admission as m
    c,r=reports();first=c['task_id'];calls=[]
    def accept(cat,scoped,row,archive,**kw):
        calls.append(scoped['task_id'])
        return {'task_id':scoped['task_id'],'status':'accepted','objective_met':True}
    monkeypatch.setattr(m,'admit_main',accept)
    result=m.admit_assignment(None,c,{r['task_id']:r for r in r['repair_targets']},tmp_path/'return.zip',selected_targets={first})
    assert calls==[first]
    assert result['objective_met'] is False
    assert [a['status'] for a in result['targets']]==['accepted','not_selected']

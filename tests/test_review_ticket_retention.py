import hashlib
import json
from pathlib import Path

from arcpuzzles.review_ticket_retention import (prepare_ticket_retention,
    ticket_evidence_names, merge_ticket_notes, validate_current_ticket_assessments)
from arcpuzzles.review_notes import append_suggestions,validate_proposal_assets


def _row(kind,tid='a',status='completed',evidence=()):
    return {'ticket':{'ticket_id':'ticket-'+hashlib.sha256((kind+tid).encode()).hexdigest()[:16],
        'type':kind,'task_id':tid,'generator_sha256':hashlib.sha256((tid+'source').encode()).hexdigest(),
        'rule_hash':'a'*12,'seed':'1'*64,'consumer':{
          'api_boundary':'target_current_audit','parameter_queries':'task_support_or_prototype_followup',
          'tool_reproduction':'existing_tool_request_disposition','allocation_quality':'bounded_owner_allocation_experiment_proposal'}[kind]},
        'report':{'ticket_id':'ticket-'+hashlib.sha256((kind+tid).encode()).hexdigest()[:16],
            'type':kind,'status':status,'summary':'Bounded observation, no safety approval.',
            'evidence_paths':list(evidence),'elapsed_minutes':None},'verification_status':'reviewer_reported'}


def test_authored_audit_document_is_retained_with_ticket_finding(tmp_path):
    owner = _owner(tmp_path)
    files = {'AUDIT.md': b'## a\nSource-bound peer finding.\n',
             'checks/witness.json': b'{"observed":true}'}
    rows = [_row('api_boundary', 'a', 'finding', evidence=list(files)),
            _row('parameter_queries', 'b', 'unknown')]
    receipt = {'assignment_id': 'review-audit', 'version': 1,
               'zip_sha256': 'c' * 64, 'validation_status': 'accepted'}
    result = prepare_ticket_retention(owner, receipt, rows, set(files), files.__getitem__)
    assert result['selected_names'] == set(files)
    _apply(owner, result)
    assert any(path.endswith('AUDIT.md') for path in validate_current_ticket_assessments(owner))


def _owner(tmp_path):
    for tid in ['a','b']:
        h=tmp_path/'generators'/tid;h.mkdir(parents=True);(h/'generator.py').write_text(tid+'source')
        (h/'notes.md').write_text('Author decision.\n')
    (tmp_path/'REVIEW').mkdir();(tmp_path/'REVIEW/suggestions.json').write_text(json.dumps({'schema':'arcpuzzles-tool-requests-v1','items':[]}))
    return tmp_path


def _apply(owner,result):
    for relative,raw in result['selected_files']:
        p=owner/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    for path,raw in result['plans']:
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    for path,row in result['notes_updates'].items():
        text=path.read_text() if path.is_file() else ''
        path.write_text(merge_ticket_notes(text,row['task_id'],row['pointer']))
    append_suggestions(owner/'REVIEW',result['suggestion_events'])


def test_two_passive_outcomes_survive_without_feedback_or_archives(tmp_path):
    owner=_owner(tmp_path);files={'checks/tickets/probe.json':b'{"observed":true}',
        'checks/unselected.log':b'ignore'}
    rows=[_row('api_boundary','a',evidence=['checks/tickets/probe.json']),_row('parameter_queries','b','blocked')]
    receipt={'assignment_id':'review-test','version':1,'zip_sha256':'c'*64,'validation_status':'accepted'}
    result=prepare_ticket_retention(owner,receipt,rows,set(files),files.__getitem__)
    assert result['selected_names']=={'checks/tickets/probe.json'}
    assert not result['suggestion_events'];_apply(owner,result)
    assert len(validate_current_ticket_assessments(owner))>=3
    assert not list(owner.glob('generators/*/evidence/review_index.json'))
    note=(owner/'generators/a/notes.md').read_text();assert 'Author decision.' in note
    assert merge_ticket_notes(note,'a','generators/a/evidence/supplementary-current.json')==note
    assert 'unselected.log' not in '\n'.join(p for p,_ in result['selected_files'])


def test_tool_report_merges_original_assets_and_preserves_owner_state(tmp_path):
    owner=_owner(tmp_path);request_id='existing:tool';base='shared/tools/proposals/'+hashlib.sha256(request_id.encode()).hexdigest()[:16]
    code=owner/base/'tool.py';code.parent.mkdir(parents=True);code.write_text('pass\n')
    manifest={'schema':'arcpuzzles-tool-proposal-assets-v1','request_id':request_id,'runtime_approved':False,
        'files':[{'path':base+'/tool.py','sha256':hashlib.sha256(code.read_bytes()).hexdigest(),'bytes':5}]}
    p=owner/base/'manifest.json';p.write_text(json.dumps(manifest))
    original={'request_id':request_id,'text':'Owner edited original request','status':'deferred','reason':'Owner decision',
        'assets_manifest':{'path':base+'/manifest.json','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}}
    (owner/'REVIEW/suggestions.json').write_text(json.dumps({'schema':'arcpuzzles-tool-requests-v1','items':[original]}))
    tool=_row('tool_reproduction','a');tool['ticket']['request_id']=request_id
    rows=[tool,_row('allocation_quality','b','unknown')]
    receipt={'assignment_id':'r','version':1,'zip_sha256':'c'*64,'validation_status':'accepted'}
    result=prepare_ticket_retention(owner,receipt,rows,set(),lambda _:None);_apply(owner,result)
    requests=json.loads((owner/'REVIEW/suggestions.json').read_text());validate_proposal_assets(owner,requests)
    row=next(r for r in requests['items'] if r['request_id']==request_id)
    assert all(row[k]==original[k] for k in ['text','status','reason'])
    assert code.read_text()=='pass\n'
    assert len(requests['items'])==2
    # Repeated allocation feedback uses one stable current consumer.
    result=prepare_ticket_retention(owner,receipt,rows,set(),lambda _:None);_apply(owner,result)
    requests=json.loads((owner/'REVIEW/suggestions.json').read_text())
    assert len(requests['items'])==2;validate_proposal_assets(owner,requests)


def test_declared_gzip_dependency_closure_is_retained_and_verified(tmp_path):
    import gzip
    import pytest
    owner=_owner(tmp_path);raw=b'{"bounded": "actual observation"}\n';compressed=gzip.compress(raw,mtime=0)
    index={'schema':'arcpuzzles-evidence-gzip-v1','files':[{
        'path':'observation.json','compressed_path':'observation.json.gz',
        'raw_size':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),
        'compressed_size':len(compressed),'compressed_sha256':hashlib.sha256(compressed).hexdigest()}]}
    files={'checks/tickets/EVIDENCE.json':json.dumps(index).encode(),
           'checks/tickets/observation.json.gz':compressed,'checks/unrelated.log':b'unselected'}
    rows=[_row('api_boundary','a',evidence=['checks/tickets/EVIDENCE.json']),_row('parameter_queries','b','unknown')]
    receipt={'assignment_id':'r','version':1,'zip_sha256':'c'*64,'validation_status':'accepted'}
    assert ticket_evidence_names(rows,set(files))=={'checks/tickets/EVIDENCE.json'}
    result=prepare_ticket_retention(owner,receipt,rows,set(files),files.__getitem__)
    assert result['selected_names']=={'checks/tickets/EVIDENCE.json','checks/tickets/observation.json.gz'}
    _apply(owner,result);retained=validate_current_ticket_assessments(owner)
    payload=next(p for p in retained if p.endswith('observation.json.gz'))
    (owner/payload).write_bytes(b'corrupt gzip')
    with pytest.raises(ValueError,match='changed supplementary dependency'):
        validate_current_ticket_assessments(owner)


def test_current_pointer_replaces_same_type_without_history_or_notes_churn(tmp_path):
    owner=_owner(tmp_path);receipt={'assignment_id':'r','version':1,'zip_sha256':'c'*64,'validation_status':'accepted'}
    rows=[_row('parameter_queries','a','unknown'),_row('api_boundary','b','blocked')]
    _apply(owner,prepare_ticket_retention(owner,receipt,rows,set(),lambda _:None))
    first=validate_current_ticket_assessments(owner)
    first_link=json.loads((owner/'generators/a/evidence/supplementary-current.json').read_text())['files'][0]['path']
    rows[0]['report']['summary']='New current bounded observation'
    receipt['version']=2
    _apply(owner,prepare_ticket_retention(owner,receipt,rows,set(),lambda _:None))
    current=validate_current_ticket_assessments(owner)
    assert first_link in first and first_link not in current and (owner/first_link).is_file()
    note=(owner/'generators/a/notes.md').read_text()
    assert note.count('## Current supplementary checks')==1 and 'Author decision.' in note


def test_copying_runtime_evidence_is_rejected_before_planning(tmp_path):
    import pytest
    owner=_owner(tmp_path);name='checks/runtime/repo/generator.py'
    rows=[_row('api_boundary','a',evidence=[name]),_row('parameter_queries','b','unknown')]
    receipt={'assignment_id':'r','version':1,'zip_sha256':'c'*64,'validation_status':'accepted'}
    with pytest.raises(ValueError,match='Invalid supplementary ticket evidence'):
        prepare_ticket_retention(owner,receipt,rows,{name},lambda _:b'copied')
    assert not list(owner.glob('generators/*/evidence/supplementary-current.json'))


def test_staged_pointer_merges_different_types_before_any_write(tmp_path):
    owner=_owner(tmp_path);receipt={'assignment_id':'r','version':1,'zip_sha256':'c'*64,'validation_status':'accepted'}
    first=prepare_ticket_retention(owner,receipt,[_row('parameter_queries','a'),_row('api_boundary','b')],set(),lambda _:None)
    staged={owner/path:raw for path,raw in first['selected_files']};staged.update(dict(first['plans']))
    receipt['version']=2
    second=prepare_ticket_retention(owner,receipt,[_row('api_boundary','a'),_row('parameter_queries','b')],set(),lambda _:None,staged_plans=staged)
    _apply(owner,first);_apply(owner,second)
    validate_current_ticket_assessments(owner)
    for tid in ['a','b']:
        pointer=json.loads((owner/f'generators/{tid}/evidence/supplementary-current.json').read_text())
        assert set(pointer['assessments'])=={'api_boundary','parameter_queries'}


def test_only_exact_ticket_boilerplate_is_suppressed():
    from arcpuzzles.review_ticket_retention import ticket_feedback_only
    rows=[_row('api_boundary','a'),_row('parameter_queries','b')]
    text='Ticket outcomes\n\n'+'\n'.join(r['ticket']['ticket_id']+': '+r['report']['summary'] for r in rows)
    assert ticket_feedback_only(text,rows)
    assert not ticket_feedback_only(text+'\nA genuine additional tooling suggestion.',rows)
    assert not ticket_feedback_only('Real defect '+rows[0]['ticket']['ticket_id'],rows)

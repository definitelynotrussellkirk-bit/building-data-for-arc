import copy
import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from arcpuzzles.review_tickets import (TICKET_POLICY, build_ticket_policy,
    supplementary_contract, validate_ticket_reports, ticket_safety_targets)


def _manifest(tmp_path):
    rows = {f't{i}': {'generator': f'generators/t{i}/generator.py',
            'generator_sha256': str(i)*64, 'rule_hash': str(i)*12,
            'rule_task_id': f't{i}'} for i in range(4)}
    m = {'generators': rows, 'all_ids': list(rows), 'files': {}}
    sources = {}
    def add(name, value):
        p = tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(value));sources[name]=p
        m['files'][name]=hashlib.sha256(p.read_bytes()).hexdigest()
    for tid,row in rows.items():
        m['files']['repo/'+row['generator']]=row['generator_sha256']
    add('repo/generators/t0/evidence/audit-assets.json', {'files': []})
    add('repo/generators/t0/evidence/review_index.json', {'audits': [{
        'return_id':'old:v0001','source_sha256':'0'*64,'resolution':'unresolved',
        'assets_manifest':'generators/t0/evidence/audit-assets.json',
        'assets_manifest_sha256':m['files']['repo/generators/t0/evidence/audit-assets.json']}]})
    add('repo/generators/t1/workspace/parametric/evidence/manifest.json', {
        'generator_sha256':'1'*64, 'files': []})
    add('repo/shared/tools/proposals/tool/manifest.json', {'files': []})
    add('repo/REVIEW/suggestions.json', {'items':[{'request_id':'request:one','status':'accepted',
        'assets_manifest':'shared/tools/proposals/tool/manifest.json',
        'assets_manifest_sha256':m['files']['repo/shared/tools/proposals/tool/manifest.json']}]})
    return m,sources


def test_policy_eligibility_and_two_distinct_reproducible_types(tmp_path):
    m,sources=_manifest(tmp_path);m['supplementary_ticket_policy']=build_ticket_policy(m,sources)
    assert set(m['supplementary_ticket_policy']['candidates']) == set(TICKET_POLICY['weights'])
    main={'assignment_id':'review-test','task_id':'t0','seed':'1'*64}
    a=supplementary_contract(m,'a'*64,main,bytes(32),blind_id='t3')
    assert a==supplementary_contract(m,'a'*64,main,bytes(32),blind_id='t3')
    assert len(a['tickets'])==2 and len({t['type'] for t in a['tickets']})==2
    assert all(t.get('task_id')!='t3' and t['budget']=={'authoring_minutes':10,'targeted_probe_seconds':120,'targeted_probes':1} for t in a['tickets'])
    assert a['schema']=='arcpuzzles-full-audit-v4'


def test_unavailable_types_are_excluded_and_weights_renormalized(tmp_path):
    m,_=_manifest(tmp_path);m['supplementary_ticket_policy']=build_ticket_policy(m)
    a=supplementary_contract(m,'a'*64,{'assignment_id':'r','seed':'0'*64},bytes(32))
    assert a['eligible_weights']=={'adversarial_witness':35,'api_boundary':15,'allocation_quality':10}
    assert a['eligible_weight_total']==60


def test_only_real_findings_become_safety_targets_and_reports_are_bound(tmp_path):
    m,sources=_manifest(tmp_path);m['supplementary_ticket_policy']=build_ticket_policy(m,sources)
    main={'assignment_id':'r','seed':'0'*64}
    a=next(supplementary_contract(m,'a'*64,main,n.to_bytes(32,'big')) for n in range(100)
           if any(t['type']=='parameter_queries' for t in supplementary_contract(m,'a'*64,main,n.to_bytes(32,'big'))['tickets']))
    reports=[{'ticket_id':t['ticket_id'],'type':t['type'],'status':'unknown',
              'summary':'No probe was run.','evidence_paths':[],'elapsed_minutes':None} for t in a['tickets']]
    assert validate_ticket_reports(a,reports,set())==reports
    assert ticket_safety_targets(a,reports)==[]
    for mutation in ['missing','type','elapsed','evidence','non_safety_finding']:
        bad=copy.deepcopy(reports)
        if mutation=='missing':bad.pop()
        elif mutation=='type':bad[0]['type']='wrong'
        elif mutation=='elapsed':bad[0]['elapsed_minutes']=True
        elif mutation=='evidence':bad[0]['evidence_paths']=['checks/missing.json']
        else:next(x for x in bad if x['type']=='parameter_queries')['status']='finding'
        with pytest.raises(ValueError):validate_ticket_reports(a,bad,set())


def _ticket_packet(library, tmp_path, question_id="q"):
    from arcpuzzles import Catalog
    from arcpuzzles.review_full_packet import build_full_packet, canonical_json
    question=library/'REVIEW/questions'/ (question_id+'.json');question.parent.mkdir(parents=True)
    question.write_text(json.dumps({'schema':'arcpuzzles-review-question-v1','id':question_id,
                                  'version':1,'owner':'ARCpuzzles','text':'Optional question'}))
    built=build_full_packet(Catalog(library),library/'REVIEW',tmp_path/'request.zip')
    packet=tmp_path/'packet';packet.mkdir()
    with zipfile.ZipFile(built['zip']) as archive:archive.extractall(packet)
    m=json.loads((packet/'PACKET-MANIFEST.json').read_text())
    sources={name:packet/name for name in m['files']}
    m['supplementary_ticket_policy']=build_ticket_policy(m,sources)
    data=canonical_json(m);(packet/'PACKET-MANIFEST.json').write_bytes(data)
    packet_id=hashlib.sha256(data).hexdigest()
    cached=library/'var/review/full-packets'/packet_id/'request.zip';cached.parent.mkdir(parents=True)
    with zipfile.ZipFile(cached,'w') as archive:
        for p in sorted(packet.rglob('*')):
            if p.is_file():archive.write(p,p.relative_to(packet).as_posix())
    return packet,m


def _finish(packet, *, finding=False):
    from arcpuzzles.review_full_draw import draw_main,draw_audit
    main=draw_main(packet,bytes(32))
    audit=draw_audit(packet,bytes(32))
    assert audit==draw_audit(packet,bytes([1])*32)
    for name in ['REVIEW.md']:(packet/name).write_text('Scoped prototype-only work; production is unchanged.\n')
    result=json.loads((packet/'RESULTS.json').read_text())
    rows=result['supplementary_tickets']
    for row in rows:
        row['status']='unknown';row['summary']='No extra probe: this fixture retains an explicit coverage limit.'
    if finding:
        row=next(x for x in rows if x['type'] in {'adversarial_witness','api_boundary'})
        row['status']='finding'
        ticket=next(t for t in audit['tickets'] if t['ticket_id']==row['ticket_id'])
        (packet/'AUDIT.md').write_text(f"## {ticket['task_id']}\nOne source-bound API defect observed.\n")
    (packet/'FEEDBACK_TO_CODEX.md').write_text('## F1: Ticket outcomes\n\n'+ '\n'.join(x['ticket_id']+': '+x['summary'] for x in rows))
    result.update(completion_state='complete',stopping_reason='Fixture complete',
                  work_scope={'production':'not_applicable','prototype':'not_run'})
    (packet/'RESULTS.json').write_text(json.dumps(result))
    return main,audit


def test_delta_return_collect_and_inbox_do_not_create_fake_safety_audits(library,tmp_path):
    from arcpuzzles.review_full_return import build_full_return
    from arcpuzzles.review_full_collect import _collect_one
    from arcpuzzles.review_full_inbox import build_full_inbox
    packet,m=_ticket_packet(library,tmp_path);main,audit=_finish(packet)
    duties=(packet/'DUTIES.md').read_text()
    assert 'Verify only what you changed' in duties
    assert 'before --out' not in duties and '--per-band 100' not in duties
    assert 'QUESTION_ANSWER.md` is optional' in duties
    # Deliberately stage transport debris; the delta builder omits it.
    for name in ['checks/runtime/repo/unchanged.py','checks/request.zip','checks/runtime/RUNTIME_MANIFEST.json']:
        p=packet/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'copied')
    p=packet/'repo/generators'/main['task_id']/'notes.md';p.write_text('New concise current decision.\n')
    returned=build_full_return(packet,tmp_path/'review_response_delta.zip')
    with zipfile.ZipFile(returned['zip']) as z:
        names=set(z.namelist());assert 'QUESTION_ANSWER.md' not in names and 'DECISIONS.md' not in names and 'AUDIT.md' not in names
        assert 'patches/source.patch' in names
        assert not any(n.startswith('repo/') or '/runtime/' in n or n=='checks/request.zip' for n in names)
        intake=json.loads(z.read('INTAKE.json'));assert len(intake['supplementary_tickets'])==2
        assert intake['audit_targets']==[]
        assert intake['delta_omissions']['copied_transport_or_runtime_files']==3
    receipt=_collect_one(library/'REVIEW',Path(returned['zip']))
    assert receipt['validation_status']=='accepted',receipt
    assert receipt['audit_targets']==[] and len(receipt['supplementary_tickets'])==2
    built=build_full_inbox(library/'REVIEW',library/'var/inbox')
    data=json.loads(Path(built['index_json']).read_text()) if 'index_json' in built else json.loads((library/'var/inbox/index.json').read_text())
    assert not data['audits'] and len(data['supplementary_tickets'])==2


def test_real_ticket_finding_has_one_source_bound_audit(library,tmp_path):
    from arcpuzzles.review_full_return import build_full_return
    from arcpuzzles.review_full_collect import _collect_one
    from arcpuzzles.review_full_inbox import build_full_inbox
    packet,m=_ticket_packet(library,tmp_path);main,audit=_finish(packet,finding=True)
    returned=build_full_return(packet,tmp_path/'review_response_finding.zip')
    receipt=_collect_one(library/'REVIEW',Path(returned['zip']))
    assert receipt['validation_status']=='accepted',receipt
    assert len(receipt['audit_targets'])==1
    build_full_inbox(library/'REVIEW',library/'var/inbox')
    data=json.loads((library/'var/inbox/index.json').read_text())
    assert len(data['audits'])==1
    row=next(iter(data['audits'].values()))[0]
    target=receipt['audit_targets'][0]
    assert row['source_sha256']==m['generators'][target]['generator_sha256']


@pytest.mark.parametrize('field',['consumer','generator_sha256','seed','budget'])
def test_ticket_identity_tamper_is_rejected(library,tmp_path,field):
    from arcpuzzles.review_full_return import build_full_return
    packet,m=_ticket_packet(library,tmp_path);main,audit=_finish(packet)
    audit['tickets'][0][field]='forged'
    (packet/'AUDIT_ASSIGNMENT.json').write_text(json.dumps(audit))
    with pytest.raises(ValueError,match='ticket draw cannot be reproduced'):
        build_full_return(packet,tmp_path/'bad.zip')


def test_selected_metadata_changes_fail_before_ticket_assignment(tmp_path):
    m,sources=_manifest(tmp_path)
    sources['repo/REVIEW/suggestions.json'].write_text('{"items":[]}')
    with pytest.raises(ValueError,match='Ticket metadata source changed'):
        build_ticket_policy(m,sources)


@pytest.mark.parametrize('copied_name',['repo/generators/t/generator.py',
    'checks/runtime/repo/generator.py','checks/racket-minimal-8.10.tgz','checks/request.zip'])
def test_validator_rejects_full_checkout_and_runtime_even_with_artifact_declarations(library,tmp_path,copied_name):
    from arcpuzzles.review_full_return import build_full_return,validate_full_return
    packet,m=_ticket_packet(library,tmp_path);_finish(packet)
    returned=build_full_return(packet,tmp_path/'review_response_good.zip')
    bad=tmp_path/'bad-full-copy.zip'
    with zipfile.ZipFile(returned['zip']) as source,zipfile.ZipFile(bad,'w') as target:
        for name in source.namelist():target.writestr(name,source.read(name))
        target.writestr(copied_name,b'unchanged checkout or runtime bytes')
    with zipfile.ZipFile(bad) as archive,pytest.raises(ValueError,match='send only the delta'):
        validate_full_return(archive,m)


def test_tool_ticket_supports_real_nested_assets_manifest_binding(tmp_path):
    m,sources=_manifest(tmp_path)
    name='repo/REVIEW/suggestions.json';value=json.loads(sources[name].read_text())
    row=value['items'][0]
    row['assets_manifest']={'path':row['assets_manifest'],
                            'sha256':row.pop('assets_manifest_sha256')}
    sources[name].write_text(json.dumps(value))
    m['files'][name]=hashlib.sha256(sources[name].read_bytes()).hexdigest()
    policy=build_ticket_policy(m,sources)
    ticket=policy['candidates']['tool_reproduction'][0]
    assert ticket['assets_manifest']=={
        'path':'repo/shared/tools/proposals/tool/manifest.json',
        'sha256':m['files']['repo/shared/tools/proposals/tool/manifest.json']}
    row['assets_manifest']['sha256']='f'*64
    sources[name].write_text(json.dumps(value))
    m['files'][name]=hashlib.sha256(sources[name].read_bytes()).hexdigest()
    assert 'tool_reproduction' not in build_ticket_policy(m,sources)['candidates']


def test_main_generator_is_excluded_from_every_peer_ticket_type(tmp_path):
    m,sources=_manifest(tmp_path)
    m['supplementary_ticket_policy']=build_ticket_policy(m,sources)
    main={'assignment_id':'review-main','task_id':'t1','seed':'1'*64}
    contracts=[supplementary_contract(m,'a'*64,main,n.to_bytes(32,'big'),blind_id='t3')
               for n in range(200)]
    assert all(ticket.get('task_id') not in {'t1','t3'}
               for contract in contracts for ticket in contract['tickets'])
    # The sole parameter prototype belongs to the main task; it is already
    # being edited and must not create a stale peer verification obligation.
    assert all('parameter_queries' not in c['eligible_weights'] for c in contracts)


def test_ticket_draw_after_main_prototype_edit_uses_untouched_peers(library,tmp_path):
    from arcpuzzles.review_full_draw import draw_main,draw_audit
    tid='aaaa00000003';home=library/'generators'/tid
    source_hash=hashlib.sha256((home/'generator.py').read_bytes()).hexdigest()
    metadata=home/'workspace/parametric/evidence/manifest.json';metadata.parent.mkdir(parents=True)
    metadata.write_text(json.dumps({'schema':'arcpuzzles-parametric-prototype-evidence-v1',
        'task_id':tid,'generator_sha256':source_hash,'files':[]}))
    packet,m=_ticket_packet(library,tmp_path)
    # New packets draw uniformly, so select this fixture's prototype explicitly
    # instead of relying on the retired priority-tier preference at seed zero.
    seed=m['main_ids'].index(tid).to_bytes(32,'big')
    main=draw_main(packet,seed);assert main['task_id']==tid
    selected=packet/'repo'/metadata.relative_to(library)
    selected.write_text('{"edited_prototype_evidence":true}')
    audit=draw_audit(packet,bytes(32))
    assert len(audit['tickets'])==2
    assert all(t.get('task_id')!=tid for t in audit['tickets'])


def test_old_audit_and_current_api_never_share_a_target_identity(tmp_path):
    m,sources=_manifest(tmp_path);policy=build_ticket_policy(m,sources)
    old=dict(policy['candidates']['audit_replay'][0],audited_generator_sha256='e'*64)
    current=policy['candidates']['api_boundary']
    policy['candidates']={'audit_replay':[old],'api_boundary':current[:2]}
    m['supplementary_ticket_policy']=policy
    main={'assignment_id':'r','task_id':'t3','seed':'0'*64}
    for n in range(100):
        contract=supplementary_contract(m,'a'*64,main,n.to_bytes(32,'big'))
        assert {t['task_id'] for t in contract['tickets']}=={'t0','t1'}
        reports=[{'ticket_id':t['ticket_id'],'type':t['type'],'status':'finding'} for t in contract['tickets']]
        sources_by_id={row['task_id']:row['generator_sha256'] for row in ticket_safety_targets(contract,reports)}
        assert sources_by_id=={'t0':'e'*64,'t1':'1'*64}
    # If only one peer identity exists, fail instead of collapsing old and new
    # source bytes into contradictory records for one target.
    policy['candidates']['api_boundary']=current[:1]
    with pytest.raises(ValueError,match='distinct'):
        supplementary_contract(m,'a'*64,main,bytes(32))


def test_failed_ticket_verification_resumes_pinned_seed(library,tmp_path,monkeypatch):
    import arcpuzzles.review_full_draw as draw
    packet,m=_ticket_packet(library,tmp_path);draw.draw_main(packet,bytes(32))
    calls=[]
    def entropy(size):calls.append(size);return bytes([len(calls)])*size
    monkeypatch.setattr(draw.os,'urandom',entropy)
    original=draw._verify
    def fail_source(root,manifest,path):
        if path.endswith('/generator.py'):raise ValueError('test verification interruption')
        return original(root,manifest,path)
    monkeypatch.setattr(draw,'_verify',fail_source)
    with pytest.raises(ValueError,match='verification interruption'):draw.draw_audit(packet)
    pending=packet/'.review/pending-audit-draw.json'
    saved=json.loads(pending.read_text());assert saved['seed']==bytes([1]*32).hex()
    with pytest.raises(ValueError,match='seed conflicts'):draw.draw_audit(packet,bytes([2]*32))
    monkeypatch.setattr(draw,'_verify',original)
    result=draw.draw_audit(packet)
    assert result['seed']==saved['seed'] and calls==[32]
    assert not pending.exists()


def test_ticket_draw_concurrent_callers_commit_one_contract(library,tmp_path,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import arcpuzzles.review_full_draw as draw
    packet,m=_ticket_packet(library,tmp_path);draw.draw_main(packet,bytes(32))
    calls=[]
    def entropy(size):calls.append(size);return bytes([len(calls)])*size
    monkeypatch.setattr(draw.os,'urandom',entropy)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:draw.draw_audit(packet),range(2)))
    assert results[0]==results[1] and calls==[32]
    assert json.loads((packet/'AUDIT_ASSIGNMENT.json').read_text())==results[0]


@pytest.mark.parametrize('state_name',['.review/pending-audit-draw.json',
    '.review/audit-draw-staging','.review/audit-draw.lock','AUDIT_ASSIGNMENT.json'])
def test_audit_draw_state_symlinks_fail_without_modifying_external_files(library,tmp_path,state_name):
    import arcpuzzles.review_full_draw as draw
    packet,m=_ticket_packet(library,tmp_path);draw.draw_main(packet,bytes(32))
    external=tmp_path/'external-state';external.write_text('preserve original')
    p=packet/state_name;p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to(external)
    with pytest.raises(ValueError,match='symlink'):draw.draw_audit(packet,bytes(32))
    assert external.read_text()=='preserve original' and p.is_symlink()


def test_corrupt_pending_audit_draw_does_not_reroll(library,tmp_path,monkeypatch):
    import arcpuzzles.review_full_draw as draw
    packet,m=_ticket_packet(library,tmp_path);draw.draw_main(packet,bytes(32))
    pending=packet/'.review/pending-audit-draw.json';pending.write_text('{"schema":"corrupt"}')
    def no_entropy(_):raise AssertionError('corruption must not choose another seed')
    monkeypatch.setattr(draw.os,'urandom',no_entropy)
    with pytest.raises(ValueError,match='Invalid pending audit draw'):draw.draw_audit(packet)
    assert pending.read_text()=='{"schema":"corrupt"}'


def test_partial_ticket_commit_resumes_same_contract(library,tmp_path,monkeypatch):
    import arcpuzzles.review_full_draw as draw
    packet,m=_ticket_packet(library,tmp_path);draw.draw_main(packet,bytes(32))
    original=draw._write_draw_bytes
    def interrupt(path,raw,staging,**kwargs):
        if path.name=='TICKETS.md':raise OSError('interrupted ticket documentation write')
        return original(path,raw,staging,**kwargs)
    monkeypatch.setattr(draw,'_write_draw_bytes',interrupt)
    with pytest.raises(OSError,match='interrupted ticket'):draw.draw_audit(packet,bytes([7]*32))
    committed=(packet/'AUDIT_ASSIGNMENT.json').read_bytes()
    assert (packet/'.review/pending-audit-draw.json').is_file()
    monkeypatch.setattr(draw,'_write_draw_bytes',original)
    result=draw.draw_audit(packet)
    assert result['seed']==bytes([7]*32).hex()
    assert (packet/'AUDIT_ASSIGNMENT.json').read_bytes()==committed
    assert (packet/'TICKETS.md').is_file() and not (packet/'.review/pending-audit-draw.json').exists()


def test_legacy_audit_recovery_preserves_original_contract_bytes(library,tmp_path,monkeypatch):
    import arcpuzzles.review_full_draw as draw
    from arcpuzzles.review_full_packet import canonical_json
    packet,m=_ticket_packet(library,tmp_path);m.pop('supplementary_ticket_policy')
    raw=canonical_json(m);(packet/'PACKET-MANIFEST.json').write_bytes(raw)
    draw.draw_main(packet,bytes(32))
    seed=bytes([8]*32);original=draw._verify
    def fail_peer(root,manifest,path):
        if path.endswith('/generator.py'):raise ValueError('legacy peer failed')
        return original(root,manifest,path)
    monkeypatch.setattr(draw,'_verify',fail_peer)
    with pytest.raises(ValueError,match='legacy peer failed'):draw.draw_audit(packet,seed)
    monkeypatch.setattr(draw,'_verify',original)
    result=draw.draw_audit(packet)
    expected={'schema':'arcpuzzles-full-audit-v3','packet_id':hashlib.sha256(raw).hexdigest(),
              'seed':seed.hex(),'targets':[{'task_id':tid,
                 'generator_sha256':m['generators'][tid]['generator_sha256']}
                 for tid in draw.audit_ids_for_seed(m['all_ids'],seed)]}
    assert result==expected
    assert (packet/'AUDIT_ASSIGNMENT.json').read_text()==json.dumps(expected,sort_keys=True,indent=2)+'\n'


def test_new_ticket_workflow_does_not_require_general_feedback_essay(library,tmp_path):
    from arcpuzzles.review_full_return import build_full_return
    packet,m=_ticket_packet(library,tmp_path);_finish(packet)
    (packet/'FEEDBACK_TO_CODEX.md').unlink()
    returned=build_full_return(packet,tmp_path/'review_response_no_feedback.zip')
    with zipfile.ZipFile(returned['zip']) as archive:
        assert archive.read('FEEDBACK_TO_CODEX.md')==b''
        intake=json.loads(archive.read('INTAKE.json'))
        assert intake['feedback_items']==[] and len(intake['supplementary_tickets'])==2

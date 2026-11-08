import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_packet import build_full_packet, _source_files
from arcpuzzles.review_packet_selection import choose_selection, project_library


def expand_library(root, count=12):
    rows = [json.loads(line) for line in (root/'catalog/puzzles.jsonl').read_text().splitlines()]
    canonical = [json.loads(line) for line in (root/'shared/data/canonical/puzzles.jsonl').read_text().splitlines()]
    mappings = json.loads((root/'catalog/runtime_files.json').read_text())
    for i in range(4, count + 1):
        tid = f'aaaa{i:08d}'
        row = {**rows[0], 'id':tid, 'aliases':[f'alias-{i}'], 'rule_task_id':tid,
               'generator':f'generators/{tid}/generator.py', 'runtime_generator':f'puzzle_generators/per_puzzle/{tid}/generator.py'}
        path=root/row['generator'];path.parent.mkdir(parents=True);path.write_text("VERSION='fixture'\n")
        row['reviewed_generator_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(row);canonical.append({**canonical[0], 'task_id':tid})
        mappings.append({'path':row['generator'],'target':row['runtime_generator']})
    (root/'catalog/puzzles.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    (root/'shared/data/canonical/puzzles.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in canonical))
    (root/'catalog/runtime_files.json').write_text(json.dumps(mappings))
    return rows


def questions(root):
    p=root/'REVIEW/questions/q.json';p.parent.mkdir(parents=True)
    p.write_text(json.dumps({'schema':'arcpuzzles-review-question-v1','id':'q','version':1,'owner':'owner','text':'review'}))


def test_new_packet_draw_includes_reviewed_and_unreviewed_targets_equally(library, tmp_path):
    from arcpuzzles.review_full_draw import main_selection_for_seed
    questions(library)
    built = build_full_packet(Catalog(library), library/'REVIEW', tmp_path/'uniform.zip')
    with zipfile.ZipFile(built['zip']) as archive:
        manifest = json.loads(archive.read('PACKET-MANIFEST.json'))
    assert manifest['main_ids'] == manifest['all_ids']
    assert manifest['main_draw_policy']['schema'] == 'arcpuzzles-main-draw-policy-v2'
    assert [main_selection_for_seed(manifest, i.to_bytes(32, 'big'))[0]
            for i in range(3)] == manifest['main_ids']


def test_uniform_draw_keeps_priority_metadata_out_of_target_probabilities():
    from arcpuzzles.review_full_draw import main_selection_for_seed
    ids = ['a', 'b', 'c']
    manifest = {'main_ids': ids, 'parametric_priority': {'main_ids': ['c']},
                'main_draw_policy': {'schema': 'arcpuzzles-main-draw-policy-v2',
                                     'distribution': 'uniform', 'ids': ids}}
    assert [main_selection_for_seed(manifest, i.to_bytes(32, 'big'))
            for i in range(6)] == [(tid, None) for tid in ids * 2]


def test_legacy_weighted_draws_keep_their_original_assignments():
    from arcpuzzles.review_full_draw import main_selection_for_seed
    manifest = {'main_ids': ['a', 'b', 'c'], 'main_draw_policy': {
        'schema': 'arcpuzzles-main-draw-policy-v1', 'normal_ids': ['c'],
        'evaluation_focus': {'schema': 'arcpuzzles-evaluation-focus-v1',
                             'probability': {'numerator': 1, 'denominator': 10},
                             'anchors': []}}}
    assert [main_selection_for_seed(manifest, i.to_bytes(32, 'big'))
            for i in range(6)] == [('c', None)] * 6


def test_default_packet_now_contains_500_targets(library, tmp_path):
    expand_library(library, count=505)
    questions(library)
    built = build_full_packet(Catalog(library), library/'REVIEW', tmp_path/'default500.zip')
    assert built['generator_count'] == 500
    assert built['eligible_count'] == 500


def test_rotation_focus_and_coverage_are_deterministic(library):
    expand_library(library)
    cat=Catalog(library)
    first, state=choose_selection(cat, library/'REVIEW', size=4, focus_ids=['aaaa00000010'])
    again, same=choose_selection(cat, library/'REVIEW', size=4, focus_ids=['aaaa00000010'])
    assert first == again and state == same
    assert 'aaaa00000010' in first['selected_ids']
    assert any('coverage' in why for why in first['reasons'].values())
    p=library/'REVIEW/packet-rotation.json';p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(state))
    second,_=choose_selection(cat, library/'REVIEW', size=4)
    assert set(second['selected_ids']) != set(first['selected_ids'])
    assert set(second['selected_ids']) - set(first['selected_ids'])


def test_transitive_dependencies_fit_budget_and_unknown_dependencies_fail(library):
    rows=expand_library(library)
    rows[9]['runtime_dependencies']=[rows[8]['id']];rows[8]['runtime_dependencies']=[rows[7]['id']]
    (library/'catalog/puzzles.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    selected,_=choose_selection(Catalog(library),library/'REVIEW',size=3,task_ids=[rows[9]['id']])
    assert set(selected['selected_ids'])=={rows[i]['id'] for i in [7,8,9]}
    with pytest.raises(ValueError,match='budget'):
        choose_selection(Catalog(library),library/'REVIEW',size=2,task_ids=[rows[9]['id']])
    rows[9]['runtime_dependencies']=['unknown']
    (library/'catalog/puzzles.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    with pytest.raises(ValueError,match='dependency'):
        choose_selection(Catalog(library),library/'REVIEW',size=4,task_ids=[rows[9]['id']])


def test_projected_aliases_rules_and_runtime_are_independent(library,tmp_path):
    expand_library(library)
    (library/'catalog/aliases.json').write_text(json.dumps({'first':['aaaa00000001'],'absent':['aaaa00000010']}))
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=1,task_ids=['aaaa00000001'])
    files,receipt=project_library(library,library/'REVIEW',selection)
    dest=tmp_path/'relocated'
    for name,path in files.items():
        out=dest/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(path.read_bytes())
    cat=Catalog(dest)
    assert [row['id'] for row in cat.query()]==['aaaa00000001']
    assert cat.resolve('first')=='aaaa00000001'
    assert cat.describe('aaaa00000001')['approved']
    assert len(cat.get('aaaa00000001')['variants'])==1
    assert json.loads((dest/'catalog/aliases.json').read_text())=={'first':['aaaa00000001']}
    assert len(json.loads((dest/'catalog/runtime_files.json').read_text()))==1
    binding=next(x for x in receipt['files'] if x['path']=='catalog/puzzles.jsonl')
    assert binding['owner_sha256'] != binding['projected_sha256']


def test_prototype_and_active_audit_hash_closure_survives_pruning(library):
    expand_library(library)
    tid='aaaa00000001';home=library/'generators'/tid
    payload=home/'workspace/parametric/evidence/a.zip';payload.parent.mkdir(parents=True);payload.write_bytes(b'cited zip')
    manifest=payload.parent/'manifest.json';relative=payload.relative_to(library).as_posix()
    manifest.write_text(json.dumps({'task_id':tid,'files':[{'path':relative,'sha256':hashlib.sha256(payload.read_bytes()).hexdigest()}]}))
    diary=home/'workspace/progress.md';diary.write_text('unreferenced diary')
    solve=home/'evidence/reviewer-solves/old.json';solve.parent.mkdir(parents=True);solve.write_text('{}')
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=1,task_ids=[tid])
    files,_=project_library(library,library/'REVIEW',selection)
    assert relative in files
    assert diary.relative_to(library).as_posix() not in files
    assert solve.relative_to(library).as_posix() not in files
    payload.unlink()
    with pytest.raises((FileNotFoundError,ValueError),match='(inventory|evidence|dependency)'):
        project_library(library,library/'REVIEW',selection)


def test_build_failure_does_not_advance_rotation_and_reprojection_is_frozen(library,tmp_path):
    expand_library(library);questions(library)
    output=tmp_path/'packet.zip';output.write_bytes(b'existing conflicting output')
    state=library/'REVIEW/packet-rotation.json'
    with pytest.raises(FileExistsError):
        build_full_packet(Catalog(library),library/'REVIEW',output,selection_size=4)
    assert not state.exists()
    built=build_full_packet(Catalog(library),library/'REVIEW',tmp_path/'good.zip',selection_size=4)
    before=state.read_bytes()
    with zipfile.ZipFile(built['zip']) as archive:
        manifest=json.loads(archive.read('PACKET-MANIFEST.json'))
        frozen=_source_files(library,library/'REVIEW',selection=manifest['selection'])
        assert {name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in frozen.items()}==manifest['files']
    assert state.read_bytes()==before


def test_current_intake_focus_and_failed_dependency_leave_rotation_unchanged(library):
    expand_library(library)
    receipt=library/'var/review/current-intake.json';receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({'returns':[{'assignment':{'task_id':'aaaa00000012'},
        'intake':{'audit_targets':[{'task_id':'aaaa00000011'}]}}]}))
    current=library/'REVIEW/full-packet-current.json';current.parent.mkdir(exist_ok=True)
    current.write_text(json.dumps({'current_intake':{'source_receipt':str(receipt)}}))
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=6)
    assert any('recent_return' in reasons for reasons in selection['reasons'].values())
    assert {'aaaa00000011','aaaa00000012'} & set(selection['selected_ids'])
    assert not (library/'REVIEW/packet-rotation.json').exists()


def test_current_intake_focus_uses_declared_latest_returns_not_older_transport_rows(library):
    expand_library(library)
    receipt=library/'var/review/current-intake.json';receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({'recent_focus_assignment_ids':['review-new'], 'returns':[
        {'assignment':{'assignment_id':'review-old','task_id':'aaaa00000008'},
         'intake':{'audit_targets':[{'task_id':'aaaa00000007'}]}},
        {'assignment':{'assignment_id':'review-new','task_id':'aaaa00000012'},
         'intake':{'audit_targets':[{'task_id':'aaaa00000011'}]}}]}))
    current=library/'REVIEW/full-packet-current.json';current.parent.mkdir(exist_ok=True)
    current.write_text(json.dumps({'current_intake':{'source_receipt':str(receipt)}}))
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=6)
    assert 'recent_return' in selection['reasons']['aaaa00000011']
    assert not any('recent_return' in selection['reasons'].get(tid, [])
                   for tid in ['aaaa00000007','aaaa00000008'])


@pytest.mark.parametrize('ids', ['review-new', ['review-new','review-new'], ['missing']])
def test_invalid_latest_intake_focus_is_explicit_and_manual_selection_can_override(library, ids):
    expand_library(library)
    receipt=library/'var/review/current-intake.json';receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({'recent_focus_assignment_ids':ids, 'returns':[
        {'assignment':{'assignment_id':'review-new','task_id':'aaaa00000012'},'intake':{}}]}))
    current=library/'REVIEW/full-packet-current.json';current.parent.mkdir(exist_ok=True)
    current.write_text(json.dumps({'current_intake':{'source_receipt':str(receipt)}}))
    with pytest.raises(ValueError,match='focus assignment'):
        choose_selection(Catalog(library),library/'REVIEW',size=6)
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=6,
                                  focus_ids=['aaaa00000010'])
    assert 'recent_return' in selection['reasons']['aaaa00000010']


def test_500_target_quota_reports_the_actual_ten_percent_evaluation_reserve(library):
    expand_library(library, count=505)
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=500)
    assert selection['quotas']['public_evaluation_roots'] == 50


def test_bound_historical_source_receipt_does_not_requalify_old_source(library):
    tid='aaaa00000001';home=library/'generators'/tid
    evidence=home/'workspace/parametric/evidence';old=evidence/'provenance/old-manifest.json'
    old.parent.mkdir(parents=True);old.write_text(json.dumps({'files':[{'path':f'generators/{tid}/generator.py','sha256':'0'*64}]}))
    manifest=evidence/'manifest.json';name=old.relative_to(library).as_posix()
    manifest.write_text(json.dumps({'files':[{'path':name,'sha256':hashlib.sha256(old.read_bytes()).hexdigest()}]}))
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=1,task_ids=[tid])
    files,_=project_library(library,library/'REVIEW',selection)
    assert files[name].read_bytes()==old.read_bytes()
    # The outer binding is always strict, even for passive historical content.
    old.write_text('{}')
    with pytest.raises(ValueError,match='changed retained'):
        project_library(library,library/'REVIEW',selection)


def test_gzip_evidence_closure_is_hash_checked(library):
    import gzip
    tid='aaaa00000001';folder=library/'generators'/tid/'evidence/gzip'
    folder.mkdir(parents=True);raw=b'minimal witness';blob=gzip.compress(raw,mtime=0)
    payload=folder/'witness.json.gz';payload.write_bytes(blob)
    index=folder/'manifest.json';index.write_text(json.dumps({'schema':'arcpuzzles-evidence-gzip-v1','files':[{
        'path':'witness.json','compressed_path':'witness.json.gz','raw_size':len(raw),
        'raw_sha256':hashlib.sha256(raw).hexdigest(),'compressed_size':len(blob),
        'compressed_sha256':hashlib.sha256(blob).hexdigest()}]}))
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=1,task_ids=[tid])
    files,_=project_library(library,library/'REVIEW',selection)
    assert payload.relative_to(library).as_posix() in files
    payload.write_bytes(gzip.compress(b'changed',mtime=0))
    with pytest.raises(ValueError,match='compressed evidence'):
        project_library(library,library/'REVIEW',selection)


def test_selected_active_audit_inventory_and_safety_identity_survive(library):
    tid='aaaa00000001';home=library/'generators'/tid
    payload=home/'counterexamples/active/witness.zip';payload.parent.mkdir(parents=True);payload.write_bytes(b'audit witness')
    manifest=payload.parent/'audit_assets.json';manifest.write_text(json.dumps({'files':[{
        'path':payload.relative_to(library).as_posix(),'sha256':hashlib.sha256(payload.read_bytes()).hexdigest()}]}))
    index=home/'evidence/review_index.json';index.parent.mkdir(parents=True)
    index.write_text(json.dumps({'schema':'arcpuzzles-task-review-current-v1','task_id':tid,'decisions':[],
        'audits':[{'return_id':'review-a:v0001','source_sha256':'0'*64,'resolution':'unresolved',
                  'assets_manifest':manifest.relative_to(library).as_posix(),
                  'assets_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()}]}))
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=1,task_ids=[tid])
    files,_=project_library(library,library/'REVIEW',selection)
    projected=Catalog(files['catalog/puzzles.jsonl'].parent.parent)
    assert projected.describe(tid)['approved']==Catalog(library).describe(tid)['approved']
    assert projected.describe(tid)['audit_unresolved']
    assert files[manifest.relative_to(library).as_posix()].read_bytes()==manifest.read_bytes()


def test_projected_runtime_relocated_without_owner_and_legacy_opt_out(library,tmp_path):
    from arcpuzzles.runtime import prepare_runtime
    expand_library(library);questions(library)
    built=build_full_packet(Catalog(library),library/'REVIEW',tmp_path/'subset.zip',selection_size=2,
        task_ids=['aaaa00000001','aaaa00000002'])
    with zipfile.ZipFile(built['zip']) as archive:
        archive.extractall(tmp_path/'fresh')
    library.rename(library.with_name('owner-hidden'))
    relocated=Catalog(tmp_path/'fresh/repo')
    receipt=prepare_runtime(relocated,tmp_path/'runtime',task_id='aaaa00000001')
    assert (tmp_path/'runtime/puzzle_generators/per_puzzle/aaaa00000001/generator.py').is_file()
    assert receipt['files']
    full=build_full_packet(Catalog(library.with_name('owner-hidden')),library.with_name('owner-hidden')/'REVIEW',
        tmp_path/'legacy.zip',selection_size=None)
    with zipfile.ZipFile(full['zip']) as archive:
        assert 'selection' not in json.loads(archive.read('PACKET-MANIFEST.json'))


def test_only_selected_actionable_tool_request_assets_ship(library):
    selected='aaaa00000001';other='aaaa00000002';items=[]
    for tid in [selected,other]:
        request_id=f'review-{tid}:v0001:F1'
        base='shared/tools/proposals/'+hashlib.sha256(request_id.encode()).hexdigest()[:16]
        payload=library/base/'probe.py';payload.parent.mkdir(parents=True);payload.write_text('print("passive")\n')
        manifest=payload.parent/'manifest.json'
        manifest.write_text(json.dumps({'schema':'arcpuzzles-tool-proposal-assets-v1','request_id':request_id,
            'runtime_approved':False,'files':[{'path':payload.relative_to(library).as_posix(),
                'sha256':hashlib.sha256(payload.read_bytes()).hexdigest()}]}))
        items.append({'request_id':request_id,'generator_id':tid,'status':'accepted',
            'assets_manifest':{'path':manifest.relative_to(library).as_posix(),
                'sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()}})
    suggestions=library/'REVIEW/suggestions.json';suggestions.parent.mkdir(exist_ok=True)
    suggestions.write_text(json.dumps({'schema':'arcpuzzles-tool-requests-v1','items':items}))
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=1,task_ids=[selected])
    files,_=project_library(library,library/'REVIEW',selection)
    assert items[0]['assets_manifest']['path'] in files
    assert items[1]['assets_manifest']['path'] not in files
    assert len(json.loads(files['REVIEW/suggestions.json'].read_text())['items'])==1
    # An unrelated broken proposal cannot force every packet to ship/repair it.
    (library/items[1]['assets_manifest']['path']).unlink()
    project_library(library,library/'REVIEW',selection)


def test_bound_tool_observation_input_is_not_current_inventory(library):
    tid='aaaa00000001';request_id=f'review-{tid}:v0001:F1'
    base='shared/tools/proposals/'+hashlib.sha256(request_id.encode()).hexdigest()[:16]
    manifest=library/base/'manifest.json';manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({'schema':'arcpuzzles-tool-proposal-assets-v1',
        'request_id':request_id,'runtime_approved':False,'files':[]}))
    old_hash=hashlib.sha256(manifest.read_bytes()).hexdigest()
    folder=manifest.parent/'supplementary/current';report=folder/'evidence/checks/result.json'
    report.parent.mkdir(parents=True)
    report.write_text(json.dumps({'assets_manifest':{'path':'repo/'+base+'/manifest.json',
        'sha256':old_hash},'status':'completed'}))
    report_name=report.relative_to(library).as_posix()
    wrapper=folder/'manifest.json'
    wrapper.write_text(json.dumps({'schema':'arcpuzzles-supplementary-assessment-v1','files':[{
        'path':report_name,'sha256':hashlib.sha256(report.read_bytes()).hexdigest()}]}))
    manifest.write_text(json.dumps({'schema':'arcpuzzles-tool-proposal-assets-v1',
        'request_id':request_id,'runtime_approved':False,'files':[{'path':wrapper.relative_to(library).as_posix(),
            'sha256':hashlib.sha256(wrapper.read_bytes()).hexdigest()}]}))
    suggestions=library/'REVIEW/suggestions.json';suggestions.parent.mkdir(exist_ok=True)
    suggestions.write_text(json.dumps({'schema':'arcpuzzles-tool-requests-v1','items':[{
        'request_id':request_id,'generator_id':tid,'status':'accepted','assets_manifest':{
            'path':manifest.relative_to(library).as_posix(),
            'sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()}}]}))
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=1,task_ids=[tid])
    files,_=project_library(library,library/'REVIEW',selection)
    assert files[report_name].read_bytes()==report.read_bytes()
    assert json.loads(files[report_name].read_text())['assets_manifest']['sha256']==old_hash
    report.write_text('{}')
    with pytest.raises(ValueError,match='(changed|mismatch)'):
        project_library(library,library/'REVIEW',selection)
    manifest.write_text('{}')
    with pytest.raises(ValueError,match='(changed|mismatch|manifest)'):
        project_library(library,library/'REVIEW',selection)


def test_unregistered_public_return_focus_is_handled_by_creation_queue(library):
    from arcpuzzles.review_packet_selection import queue_review_focus
    raw = library / 'shared/data/raw/arc-agi_evaluation_challenges.json'
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text(json.dumps({'1234abcd': {'train': [], 'test': []}}))
    queue_review_focus(library / 'REVIEW', ['public_eval_1234abcd'])
    selection, state = choose_selection(Catalog(library), library / 'REVIEW', size=1)
    assert selection['selected_ids']
    assert 'public_eval_1234abcd' in state['pending_focus']
    with pytest.raises(ValueError, match='Unknown packet focus'):
        choose_selection(Catalog(library), library / 'REVIEW', size=1,
                         focus_ids=['public_eval_87654321'])


def test_focus_queue_updates_only_pending_and_failed_build_preserves_it(library,tmp_path):
    from arcpuzzles.review_packet_selection import queue_review_focus, queue_receipt_focus
    expand_library(library);questions(library)
    state=library/'REVIEW/packet-rotation.json'
    state.write_text(json.dumps({'schema':'arcpuzzles-packet-rotation-v1','round':7,
        'last_selected':{'aaaa00000002':6},'pending_focus':['aaaa00000001']}))
    queue_review_focus(library/'REVIEW',['aaaa00000010','aaaa00000010'])
    before=state.read_bytes();queue_review_focus(library/'REVIEW',['aaaa00000010'])
    assert state.read_bytes()==before
    value=json.loads(before);assert value['round']==7 and value['last_selected']=={'aaaa00000002':6}
    assert value['pending_focus']==['aaaa00000001','aaaa00000010']
    queue_receipt_focus(library/'REVIEW',{'validation_status':'rejected','task_id':'aaaa00000012'})
    assert state.read_bytes()==before
    bad=tmp_path/'bad.zip';bad.write_bytes(b'conflict')
    with pytest.raises(FileExistsError):
        build_full_packet(Catalog(library),library/'REVIEW',bad,selection_size=4)
    assert state.read_bytes()==before
    queue_receipt_focus(library/'REVIEW',{'validation_status':'accepted','task_id':'aaaa00000003',
        'audit_targets':['aaaa00000004'],
        'supplementary_tickets':[{'ticket':{'task_id':'aaaa00000005'}}]})
    assert set(json.loads(state.read_text())['pending_focus'])=={
        'aaaa00000001','aaaa00000003','aaaa00000004','aaaa00000005','aaaa00000010'}


def test_current_pointer_selects_only_current_immutable_supplementary_evidence(library):
    tid='aaaa00000001';base=library/'generators'/tid/'evidence'
    for name in ['old','current']:
        home=base/'supplementary'/name;home.mkdir(parents=True)
        (home/'manifest.json').write_text(json.dumps({'schema':'immutable-ticket','files':[]}))
    active=base/'supplementary/current/manifest.json'
    pointer=base/'supplementary-current.json';pointer.write_text(json.dumps({'files':[{
        'path':active.relative_to(library).as_posix(),'sha256':hashlib.sha256(active.read_bytes()).hexdigest()}]}))
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=1,task_ids=[tid])
    files,receipt=project_library(library,library/'REVIEW',selection)
    assert active.relative_to(library).as_posix() in files
    assert (base/'supplementary/old/manifest.json').relative_to(library).as_posix() not in files
    assert receipt['purpose_counts']['current_supplementary_ticket_evidence']['files']>=2
    assert all(row.get('purpose') for row in receipt['files'])


def test_historical_manifest_filename_is_passive_only_under_outer_binding(library):
    tid='aaaa00000001';home=library/'generators'/tid/'workspace/parametric/evidence'
    home.mkdir(parents=True)
    old=home/'prior-manifest-review-old.json';old.write_text(json.dumps({'files':[{
        'path':f'generators/{tid}/generator.py','sha256':'0'*64}]}))
    unreferenced=home/'prior-manifest-unused.json';unreferenced.write_text('{}')
    manifest=home/'manifest.json';manifest.write_text(json.dumps({'files':[{
        'path':old.relative_to(library).as_posix(),'sha256':hashlib.sha256(old.read_bytes()).hexdigest()}]}))
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=1,task_ids=[tid])
    files,_=project_library(library,library/'REVIEW',selection)
    assert old.relative_to(library).as_posix() in files
    assert unreferenced.relative_to(library).as_posix() not in files
    old.write_text('{"changed":true}')
    with pytest.raises(ValueError,match='changed retained'):
        project_library(library,library/'REVIEW',selection)


def test_duplicate_collection_after_successful_build_does_not_requeue(library,tmp_path,monkeypatch):
    import arcpuzzles.review_full_collect as collect
    questions(library)
    source=tmp_path/'return.zip'
    with zipfile.ZipFile(source,'w') as archive: archive.writestr('evidence.txt','minimal')
    with zipfile.ZipFile(source) as archive: infos=archive.infolist()
    checked={'assignment_id':'review-0123456789abcdef','task_id':'aaaa00000003',
             'packet_id':'0'*64,'audit_targets':['aaaa00000001']}
    monkeypatch.setattr(collect,'_validate',lambda *_:(checked,b'{}',infos))
    first=collect._collect_one(library/'REVIEW',source)
    state=library/'REVIEW/packet-rotation.json'
    assert json.loads(state.read_text())['pending_focus']==['aaaa00000001','aaaa00000003']
    build_full_packet(Catalog(library),library/'REVIEW',tmp_path/'next.zip')
    assert json.loads(state.read_text())['pending_focus']==[]
    before=state.read_bytes();second=collect._collect_one(library/'REVIEW',source)
    assert second==first and state.read_bytes()==before


def test_mapped_public_evaluation_descendant_has_reserved_small_budget_coverage(library):
    expand_library(library)
    canonical=library/'shared/data/canonical/puzzles.jsonl'
    rows=[json.loads(line) for line in canonical.read_text().splitlines()]
    selected='aaaa00000012'
    for row in rows:
        if row['task_id']==selected:
            row['train']=[{'input':[[4]],'output':[[5]]}];row['test']=[{'input':[[6]],'output':[[7]]}]
    canonical.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    raw=library/'shared/data/raw/arc-agi_evaluation_challenges.json';raw.parent.mkdir(parents=True)
    raw.write_text(json.dumps({'1eaf0001':{'train':[{'input':[[4]],'output':[[5]]}], 'test':[{'input':[[6]]}]}}))
    selection,_=choose_selection(Catalog(library),library/'REVIEW',size=3,focus_ids=['aaaa00000010'])
    assert selected in selection['selected_ids']
    assert 'public_evaluation_coverage' in selection['reasons'][selected]
    assert len(selection['selected_ids'])==3
    files,_=project_library(library,library/'REVIEW',selection)
    from arcpuzzles.parametric_priority import build_parametric_priority
    projected=build_parametric_priority(Catalog(files['catalog/puzzles.jsonl'].parent.parent))
    assert projected['evaluation_focus']['provided_tasks']==1
    assert projected['evaluation_focus']['anchors'][0]['main_ids']==[selected]


def _remove_reference(root, tid):
    p = root / 'shared/data/canonical/puzzles.jsonl'
    rows = [json.loads(line) for line in p.read_text().splitlines()]
    p.write_text(''.join(json.dumps(row) + '\n' for row in rows if row['task_id'] != tid))


def test_rotation_does_not_spend_main_slots_on_unassignable_roots(library):
    expand_library(library, count=8);orphan = 'aaaa00000008';_remove_reference(library, orphan)
    from arcpuzzles.review_packet_selection import rotation_state
    state = rotation_state(library / 'REVIEW');state['round'] = 1
    state['last_selected'] = {f'aaaa{i:08d}': 1 for i in range(1, 8)}
    (library / 'REVIEW').mkdir(exist_ok=True)
    (library / 'REVIEW/packet-rotation.json').write_text(json.dumps(state))
    selected, after = choose_selection(Catalog(library), library / 'REVIEW', size=4,
                                       focus_ids=[orphan, 'aaaa00000007'])
    assert orphan not in selected['selected_ids'] and len(selected['selected_ids']) == 4
    assert 'aaaa00000007' in selected['selected_ids']
    assert selected['unreviewable_focus_ids'] == [orphan]
    assert orphan in after['pending_focus']


def test_unassignable_dependency_is_still_shipped_with_its_reviewable_root(library):
    expand_library(library, count=8);dependency = 'aaaa00000008';_remove_reference(library, dependency)
    p = library / 'catalog/puzzles.jsonl';rows = [json.loads(line) for line in p.read_text().splitlines()]
    rows[0]['runtime_dependencies'] = [dependency]
    p.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    selected, _ = choose_selection(Catalog(library), library / 'REVIEW', size=4,
                                   focus_ids=['aaaa00000001'])
    assert {'aaaa00000001', dependency} <= set(selected['selected_ids'])
    assert dependency in selected['dependency_ids']
    assert selected['reasons'][dependency] == ['runtime_dependency:aaaa00000001']


def test_explicit_authoring_selection_can_still_include_an_unassignable_source(library):
    expand_library(library, count=8);orphan = 'aaaa00000008';_remove_reference(library, orphan)
    selected, _ = choose_selection(Catalog(library), library / 'REVIEW', size=4,
                                   task_ids=[orphan, 'aaaa00000001'])
    assert selected['selected_ids'] == ['aaaa00000001', orphan]


def test_missing_reference_everywhere_fails_before_rotation_is_written(library):
    p = library / 'shared/data/canonical/puzzles.jsonl';p.write_text('')
    with pytest.raises(ValueError, match='reviewable'):
        choose_selection(Catalog(library), library / 'REVIEW', size=3)
    assert not (library / 'REVIEW/packet-rotation.json').exists()

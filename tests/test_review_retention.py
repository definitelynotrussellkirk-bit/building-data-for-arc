import hashlib
import json
from pathlib import Path
import shutil

import pytest

from arcpuzzles.review_retention import compact_reviews
from arcpuzzles.review_solve_tracker import build_solve_tracker, retain_solve_examples
from arcpuzzles.review_full_collect import collect_full_returns, _collect_one
from arcpuzzles.review_full_inbox import build_full_inbox
from arcpuzzles.review_full_integrate import record_full_disposition
from arcpuzzles.review_solve import digest, instance_hash
from arcpuzzles.review_full_packet import canonical_json
from arcpuzzles.review_full_return import build_full_return
from test_review_full_collect import _return


@pytest.mark.parametrize('folder,citation', [
    ('checks/proposals', 'checks/proposals/gate.py'),
    ('checks/tooling/resource-preflight', 'checks/tooling/resource-preflight/'),
    ('checks/optional-tools', '`gate.py`'),
    ('checks/teaching-gate-prototype', 'checks/teaching-gate-prototype/'),
    ('checks/authority-proposal', 'checks/authority-proposal/gate.py'),
])
def test_cited_shared_tool_prototype_survives_transport_disposal(library, tmp_path, folder, citation):
    feedback = '**F1: Prototype a lesson gate.**\n\nBuilt ' + citation + '.\n'
    contract, returned = _return(library, tmp_path, feedback_text=feedback)
    Path(returned['zip']).unlink()
    packet = tmp_path / 'packet-0'
    examples = {folder + '/gate.patch': b'proposed delta\n',
                folder + '/gate.py': b'raise AssertionError("must not execute")\n',
                folder + '/report.md': b'CPU-only proposal, not an accepted implementation.\n',
                folder + '/witness.zip': b'exact compressed witness bytes'}
    for name, raw in examples.items():
        path = packet / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    copied_runtime = packet / (folder + '/runtime/src/unused.py')
    copied_runtime.parent.mkdir(parents=True)
    copied_runtime.write_text('unneeded source copy\n')
    build_full_return(packet, tmp_path / 'review_response_0.zip')
    receipt = collect_full_returns(library / 'REVIEW', tmp_path)['receipts'][0]
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], 1,
                            'decision', 'deferred', 'Retain useful prototype.')
    # Earlier inbox compaction may already have dropped the decision prose.
    # Retiring the archive must recover context even if the request list is gone.
    (library / 'REVIEW/suggestions.json').unlink()
    compact_reviews(library, apply=True)
    assert not Path(receipt['archive_path']).exists()
    request = json.loads((library / 'REVIEW/suggestions.json').read_text())['items'][0]
    assert request['text'] == 'Prototype a lesson gate.\n\nBuilt ' + citation + '.'
    assert request['generator_id'] == contract['task_id']
    assert request['return_id'] == contract['assignment_id'] + ':v0001'
    assert request['source_sha256'] == contract['generator']['generator_sha256']
    manifest_path = library / request['assets_manifest']['path']
    assert digest(manifest_path.read_bytes()) == request['assets_manifest']['sha256']
    manifest = json.loads(manifest_path.read_text())
    assert manifest['runtime_approved'] is False
    assert {row['source_member'] for row in manifest['files']} == set(examples)
    for row in manifest['files']:
        assert (library / row['path']).read_bytes() == examples[row['source_member']]
    assert not list((library / 'shared/tools/proposals').rglob('unused.py'))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.review_full_packet import build_full_packet
    import zipfile
    built = build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'next-request.zip')
    with zipfile.ZipFile(built['zip']) as archive:
        for row in manifest['files']:
            assert archive.read('repo/' + row['path']) == examples[row['source_member']]
    (library / manifest['files'][0]['path']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='proposal'):
        build_full_packet(Catalog(library), library / 'REVIEW', tmp_path / 'drift.zip')


@pytest.mark.parametrize('feedback,items', [
    ('## F1: Keep a useful request\n\nNo prototype was supplied.\n'
     '## F2: Keep another request\n\nIts evidence lives with the task.\n',
     [('F1', 'Keep a useful request\n\nNo prototype was supplied.'),
      ('F2', 'Keep another request\n\nIts evidence lives with the task.')]),
    ('Unnumbered feedback still describes a useful workflow gap.\n',
     [('unstructured', 'Unnumbered feedback still describes a useful workflow gap.')]),
])
def test_feedback_survives_compaction_without_prior_inbox_or_assets(library, tmp_path, feedback, items):
    contract, returned = _return(library, tmp_path, feedback_text=feedback)
    receipt = collect_full_returns(library / 'REVIEW', tmp_path)['receipts'][0]
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], 1,
                            'decision', 'deferred', 'Retain the shared workflow requests.')
    requests_path = library / 'REVIEW/suggestions.json'
    prior = json.loads(requests_path.read_text())
    first = prior['items'][0]
    # Simulate legacy sparse entries while preserving an owner's later decision.
    prior['items'] = [{'request_id': first['request_id'], 'status': 'implemented',
                       'reason': 'Owner selected a separate implementation.'}]
    requests_path.write_text(json.dumps(prior))
    compact_reviews(library, apply=True)
    assert not Path(receipt['archive_path']).exists()
    requests = json.loads((library / 'REVIEW/suggestions.json').read_text())['items']
    by_id = {r['request_id']: r for r in requests}
    for item_id, text in items:
        request_id = contract['assignment_id'] + ':v0001:' + item_id
        assert request_id in by_id
        request = by_id[request_id]
        assert request['text'] == text
        assert request['generator_id'] == contract['task_id']
        assert request['return_id'] == contract['assignment_id'] + ':v0001'
        assert request['source_sha256'] == contract['generator']['generator_sha256']
        if request_id == first['request_id']:
            assert request['status'] == 'implemented'
            assert request['reason'] == 'Owner selected a separate implementation.'
        else:
            assert request['status'] == 'proposed'
    before = (library / 'REVIEW/suggestions.json').read_bytes()
    assert compact_reviews(library, apply=True)['archives_deleted'] == 0
    assert (library / 'REVIEW/suggestions.json').read_bytes() == before


def test_processed_zip_is_deleted_but_current_audits_survive(library, tmp_path):
    contract, returned = _return(library, tmp_path, audit=True, feedback_text='**F1: Need a grid diff.**\n')
    received = collect_full_returns(library / 'REVIEW', tmp_path)['receipts'][0]
    archive = Path(received['archive_path'])
    with pytest.raises(ValueError, match='Triage'):
        compact_reviews(library, apply=True)
    assert archive.exists()
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], 1,
                            'decision', 'deferred', 'Port this proposal after comparing current source.')
    build_full_inbox(library / 'REVIEW', tmp_path / 'inbox')
    for parent in ('full-candidates', 'full-checks', 'solve-checks'):
        tree = library / 'var/review' / parent / contract['assignment_id']
        tree.mkdir(parents=True)
        (tree / 'copied-runtime.txt').write_text('disposable processed workspace')
        other = tree.parent / 'unreturned-assignment'
        other.mkdir()
        (other / 'work.txt').write_text('pending work')
    before = compact_reviews(library)
    assert archive.exists() and before['archives_deleted'] == 0
    applied = compact_reviews(library, apply=True)
    assert applied['archives_deleted'] == 1
    assert applied['processed_assignment_trees_deleted'] == 3
    for parent in ('full-candidates', 'full-checks', 'solve-checks'):
        assert not (library / 'var/review' / parent / contract['assignment_id']).exists()
        assert (library / 'var/review' / parent / 'unreturned-assignment/work.txt').is_file()
    assert not archive.exists()
    assert not (library / 'REVIEW/assignments' / contract['assignment_id']).exists()
    assert not (library / 'REVIEW/suggestions.jsonl').exists()
    assert len(json.loads((library / 'REVIEW/suggestions.json').read_text())['items']) == 1
    assert len(list((library / 'generators').glob('*/workspace/proposals/*.json'))) == 1
    for target in received['audit_targets']:
        state = json.loads((library / f'generators/{target}/evidence/review_index.json').read_text())
        assert state['audits'][0]['text'].strip().endswith('questionable shortcut')
        assert state['audits'][0]['resolution'] == 'needs_triage'
    assert compact_reviews(library, apply=True)['archives_deleted'] == 0


@pytest.mark.parametrize('closed_first_audit', [False, True])
def test_compaction_discovers_audit_assets_without_a_prior_inbox_refresh(
        library, tmp_path, closed_first_audit):
    contract, returned = _return(library, tmp_path, audit=True)
    packet = tmp_path / 'packet-0'
    witnesses = {
        'aaaa00000001': b'{"input":[[1]],"expected":[[2]],"got":[[1]]}\n',
        'aaaa00000002': b'{"input":[[3]],"expected":[[4]],"got":[[3]]}\n',
    }
    for tid, raw in witnesses.items():
        p = packet / f'checks/audit/{tid}/reproduction.json'
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    (packet / 'AUDIT.md').write_text(''.join(
        f'## {tid}\nCounterexample: `checks/audit/{tid}/reproduction.json`.\n\n'
        for tid in witnesses))
    Path(returned['zip']).unlink()
    build_full_return(packet, Path(returned['zip']))
    # The single-return path validates and retains transport without rendering
    # an inbox. Disposal must not depend on a separate UI/materialization step.
    received = _collect_one(library / 'REVIEW', Path(returned['zip']))
    assert received['validation_status'] == 'accepted'
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], 1,
                            'decision', 'deferred', 'Retain both source-bound audits.')
    if closed_first_audit:
        from arcpuzzles.review_full_inbox import compile_task_review_index
        from arcpuzzles.review_notes import index_path, record_audit_status
        tid = 'aaaa00000001'
        p = index_path(library, tid)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(compile_task_review_index(library / 'REVIEW', tid)))
        record_audit_status(library, tid, contract['assignment_id'] + ':v0001',
                            'no_issue', 'Explicit finite assessment by the owner.')
    # The second target remains absent even when the first has a disposition.
    assert not (library / 'generators/aaaa00000002/evidence/review_index.json').exists()
    preview = compact_reviews(library)
    assert preview['active_audits'] == (1 if closed_first_audit else 2)
    assert Path(received['archive_path']).is_file()
    assert not (library / 'generators/aaaa00000002/evidence/review_index.json').exists()
    result = compact_reviews(library, apply=True)
    assert result['archives_deleted'] == 1
    assert result['active_audits'] == (1 if closed_first_audit else 2)
    assert not Path(received['archive_path']).exists()
    for tid, raw in witnesses.items():
        p = library / f'generators/{tid}/evidence/review_index.json'
        state = json.loads(p.read_text())
        if closed_first_audit and tid == 'aaaa00000001':
            assert state['audits'] == []
            assert 'Explicit finite assessment by the owner.' in (
                library / f'generators/{tid}/notes.md').read_text()
            continue
        assert len(state['audits']) == 1
        audit = state['audits'][0]
        assert audit['return_id'] == contract['assignment_id'] + ':v0001'
        assert audit['resolution'] == 'needs_triage'
        manifest_path = library / audit['assets_manifest']
        assert digest(manifest_path.read_bytes()) == audit['assets_manifest_sha256']
        assets = json.loads(manifest_path.read_text())
        witness = next(i for i in assets['files'] if i['original_member'] ==
                       f'checks/audit/{tid}/reproduction.json')
        assert (library / witness['path']).read_bytes() == raw
        assert witness['sha256'] == digest(raw)
    assert compact_reviews(library, apply=True)['archives_deleted'] == 0


def test_named_top_level_tooling_files_survive_without_retaining_unrelated_tools(library, tmp_path):
    feedback = '**F1: Lossless compaction.**\n\nIncluded `compress_evidence.py` and `test_compress_evidence.py`.\n'
    contract, returned = _return(library, tmp_path, feedback_text=feedback)
    Path(returned['zip']).unlink()
    packet = tmp_path / 'packet-0'
    examples = {
        'checks/tooling/compress_evidence.py': b'raise AssertionError("passive proposal only")\n',
        'checks/tooling/test_compress_evidence.py': b'# exact restoration regression\n',
    }
    for name, raw in {**examples, 'checks/tooling/unrelated.py': b'other tool\n',
                      'checks/tooling/runtime/src/copied.py': b'runtime copy\n'}.items():
        path = packet / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    build_full_return(packet, tmp_path / 'review_response_0.zip')
    receipt = collect_full_returns(library / 'REVIEW', tmp_path)['receipts'][0]
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], 1,
                            'decision', 'deferred', 'Keep the named passive compression prototype.')
    compact_reviews(library, apply=True)
    assert not Path(receipt['archive_path']).exists()
    request = json.loads((library / 'REVIEW/suggestions.json').read_text())['items'][0]
    manifest_path = library / request['assets_manifest']['path']
    assert digest(manifest_path.read_bytes()) == request['assets_manifest']['sha256']
    manifest = json.loads(manifest_path.read_text())
    assert manifest['runtime_approved'] is False
    assert {row['source_member'] for row in manifest['files']} == set(examples)
    for row in manifest['files']:
        assert (library / row['path']).read_bytes() == examples[row['source_member']]
    assert not list((library / 'shared/tools/proposals').rglob('unrelated.py'))
    assert not list((library / 'shared/tools/proposals').rglob('copied.py'))


def test_changed_archive_blocks_disposal(library, tmp_path):
    contract, _ = _return(library, tmp_path)
    receipt = collect_full_returns(library / 'REVIEW', tmp_path)['receipts'][0]
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], 1, 'decision', 'deferred', 'Keep proposal')
    path = Path(receipt['archive_path'])
    path.write_bytes(path.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='bytes changed'):
        compact_reviews(library, apply=True)
    assert path.exists()


def test_unmapped_pending_return_does_not_block_disposal_of_extracted_returns(library, tmp_path):
    contract, _ = _return(library, tmp_path, audit=True)
    receipt = collect_full_returns(library / 'REVIEW', tmp_path)['receipts'][0]
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], 1,
                            'decision', 'deferred', 'Retain useful witnesses.')
    pending_archive = library / 'var/review/returns/unmapped/pending/original.zip'
    pending_archive.parent.mkdir(parents=True)
    pending_archive.write_bytes(b'unexamined transport must remain')
    invalid = library / 'REVIEW/returns/unmapped/return-pending.json'
    invalid.parent.mkdir(parents=True)
    invalid.write_text(json.dumps({'assignment_id': 'unmapped', 'version': 1,
        'validation_status': 'missing_packet', 'archive_path': str(pending_archive),
        'zip_sha256': digest(pending_archive.read_bytes())}))
    original_invalid = invalid.read_bytes()
    applied = compact_reviews(library, apply=True)
    assert applied['archives_deleted'] == 1
    assert not Path(receipt['archive_path']).exists()
    assert invalid.read_bytes() == original_invalid
    assert pending_archive.read_bytes() == b'unexamined transport must remain'
    assert build_full_inbox(library / 'REVIEW', tmp_path / 'inbox')['counts']['invalid'] == 1


def test_authored_data_survives_without_transport_and_hash_drift_is_rejected(library, tmp_path):
    feed = tmp_path / 'feed'
    feed.mkdir()
    task = 'aaaa00000001'
    public = {'train':[{'input':[[1]],'output':[[2]]}], 'test':[{'input':[[3]]}]}
    question = {'schema':'arc-reviewer-question-v1','question_id':'q','generator_id':task,
                'generator_hash':'g','instance_hash':instance_hash(public),
                'private_labels_sha256':'private-hash-only','public':public}
    program = b'def solve(grid):\n    return grid\n'
    notes = b'Tested identity; it fails the visible example.\n'
    files = {}
    for key, name, raw in [('program','solution.py',program),('work_log','SOLVE_NOTES.md',notes)]:
        path = feed / f'records/a/{name}'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        files[key]={'path':str(path.relative_to(feed)),'sha256':digest(raw),'bytes':len(raw)}
    attempt = {'schema':'arc-reviewer-attempt-v1','attempt_id':'a','question_id':'q','generator_id':task,
               'generator_hash':'g','instance_hash':question['instance_hash'],'program_hash':digest(program),
               'revision':1,'label':'unknown','reported_label':'bad','attempt_intent':'candidate','note':'Wrong visible fit',
               'reference_consulted_during_solve':False,'earlier_rule_exposure':'yes','files':files,
               'source_returns':[{'assignment_id':'gone','version':1,'archive_path':'/removed.zip','return_sha256':'h'}],
               'training_admitted':False}
    for name, rows in [('attempts.jsonl',[attempt]),('questions.jsonl',[question]),('curriculum.jsonl',[])]:
        (feed/name).write_bytes(b''.join(canonical_json(r)+b'\n' for r in rows))
    hashes = {str(p.relative_to(feed)):digest(p.read_bytes()) for p in feed.rglob('*') if p.is_file()}
    (feed/'manifest.json').write_text(json.dumps({'schema':'arc-reviewer-solve-feed-v1','counts':{'errors':0},'files':hashes}))
    retain_solve_examples(library, feed)
    shutil.rmtree(feed)
    built = build_solve_tracker(library/'REVIEW',tmp_path/'restored')
    assert built['counts']['attempts'] == 1 and built['counts']['unverified'] == 1
    assert built['counts']['verified_bad'] == 0
    rows = json.loads(Path(built['attempts']).read_text())
    assert rows['reported_label'] == 'bad' and rows['earlier_rule_exposure'] == 'yes'
    assert 'archive_path' not in json.dumps(rows)
    assert json.loads(Path(built['questions']).read_text())['public']['test'] == [{'input':[[3]]}]
    next((library/'generators').glob('*/evidence/reviewer-solves/records/*/solution.py')).write_text('changed')
    with pytest.raises(ValueError, match='asset changed'):
        build_solve_tracker(library/'REVIEW', tmp_path/'broken')


def test_explicit_witness_citations_win_over_filename_heuristics():
    from arcpuzzles.review_retention import _audit_members
    names = {'checks/audit-lesson-census.json.gz', 'checks/audit/data/input.json',
             'checks/audit/task_tests.xml', 'checks/runtime/lib/unused.py'}
    cited = 'Evidence: checks/audit-lesson-census.json.gz checks/audit/data/input.json checks/audit/task_tests.xml'
    assert _audit_members(names, 'aaaa00000001', cited) == names - {'checks/runtime/lib/unused.py'}


def test_missing_existing_witness_prevents_archive_deletion(library, tmp_path):
    contract, _ = _return(library, tmp_path, audit=True)
    receipt = collect_full_returns(library / 'REVIEW', tmp_path)['receipts'][0]
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], 1, 'decision', 'deferred', 'Keep proposal')
    target = receipt['audit_targets'][0]
    key = f"{contract['assignment_id']}:v0001"
    home = library / f"generators/{target}/counterexamples/{key.replace(':v','-v')}"
    home.mkdir(parents=True)
    state = json.loads((library / f'generators/{target}/evidence/review_index.json').read_text())
    audit = state['audits'][0]
    (home/'audit_assets.json').write_text(json.dumps({'task_id':target,'return_id':key,
        'zip_sha256':receipt['zip_sha256'],
        'audited_generator_sha256':audit['source_sha256'], 'files':[
            {'path':str((home/'missing.json').relative_to(library)),'sha256':'0'*64}]}))
    with pytest.raises(ValueError, match='Missing or changed retained witness'):
        compact_reviews(library, apply=True)
    assert Path(receipt['archive_path']).exists()


def test_large_green_census_is_reduced_without_discarding_failure_witnesses():
    from arcpuzzles.review_retention import _curate_report
    lesson = {'band':'easy','ambiguous':False,'instance':{'train':[]},'filler':'x'*140000}
    bad = {'band':'easy','ambiguous':True,'instance':{'input':[[7]],'expected':[[2]]}}
    raw=json.dumps({'schema':'arcpuzzles-lesson-census-v1','lessons':[lesson,lesson,bad],
                    'summary':{'requested':3,'ambiguous':1},'runtime_manifest':{'files':['obsolete']}}).encode()
    derived, meta=_curate_report(raw,'checks/census.json')
    record=json.loads(derived)
    assert len(record['lessons'])==2 and record['lessons'][1]==bad
    assert record['summary']=={'requested':3,'ambiguous':1}
    assert meta['source_member_sha256']==digest(raw)
    assert 'runtime_manifest' not in record
    reverse, _ = _curate_report(json.dumps({'schema':'arcpuzzles-lesson-census-v1',
        'lessons':[bad,lesson,lesson]}).encode(), 'checks/census.json')
    assert json.loads(reverse)['lessons'] == [bad,lesson]


def test_audit_relative_receipt_is_resolved_within_its_target():
    from arcpuzzles.review_retention import _audit_members
    task = 'aaaa00000001'
    reference = f'checks/audit/{task}/racket.json'
    verifier = f'checks/audit/{task}/verify_witness.py'
    names = {reference, verifier, 'checks/audit/aaaa00000002/racket.json',
             f'checks/audit/{task}/runtime/lib/racket.json',
             'checks/audit-other-task/result.json'}
    assert _audit_members(names, task, 'Evidence: `racket.json` and `verify_witness.py`.') == {reference, verifier}


def test_relative_audit_citation_cannot_bind_another_target_when_own_file_is_missing():
    from arcpuzzles.review_retention import _audit_members
    names = {'checks/audit/aaaa00000002/racket.json'}
    with pytest.raises(ValueError, match='outside.*task scope'):
        _audit_members(names, 'aaaa00000001', 'Evidence: `racket.json`.')


def test_audit_source_prose_can_be_clarified_without_retaining_another_source():
    from arcpuzzles.review_retention import _audit_members
    task = 'aaaa00000001'
    witness = f'checks/audit/{task}/racket.json'
    names = {witness, 'checks/parametric/private/source/generator.py'}
    text = (f'`generator.py` always draws contiguous legends. Evidence: `{witness}`. '
            f'The source mention means `repo/generators/{task}/generator.py`.')
    assert _audit_members(names, task, text) == {witness}


def test_audit_source_clarification_must_name_the_audited_task():
    from arcpuzzles.review_retention import _audit_members
    task = 'aaaa00000001'
    names = {f'checks/audit/{task}/racket.json',
             'checks/parametric/private/source/generator.py'}
    with pytest.raises(ValueError, match='outside.*task scope'):
        _audit_members(names, task, '`generator.py`; '
                       'source: `repo/generators/aaaa00000002/generator.py`.')


def test_source_clarification_does_not_hide_ambiguous_audit_source_artifacts():
    from arcpuzzles.review_retention import _audit_members
    task = 'aaaa00000001'
    names = {f'checks/audit/{task}/before/generator.py',
             f'checks/audit/{task}/after/generator.py'}
    with pytest.raises(ValueError, match='Ambiguous.*generator.py'):
        _audit_members(names, task, f'Compare `generator.py`; '
                       f'source: `repo/generators/{task}/generator.py`.')


def test_explicit_audit_runtime_source_is_not_retained():
    from arcpuzzles.review_retention import _audit_members
    name = 'checks/audit/aaaa00000001/runtime/src/unused.py'
    assert _audit_members({name}, 'aaaa00000001', f'Unused copied source: `{name}`.') == set()


def test_path_citation_does_not_match_a_different_filename_prefix():
    from arcpuzzles.review_retention import _feedback_members
    names = {'checks/report.json', 'checks/report.json.old'}
    assert _feedback_members(names, 'Read `checks/report.json.old`.') == {'checks/report.json.old'}


def test_ambiguous_audit_relative_receipt_requires_an_explicit_path():
    from arcpuzzles.review_retention import _audit_members
    task = 'aaaa00000001'
    names = {f'checks/audit/{task}/before/racket.json',
             f'checks/audit/{task}/after/racket.json'}
    with pytest.raises(ValueError, match='Ambiguous.*racket.json'):
        _audit_members(names, task, 'Evidence: `racket.json`.')


def test_cited_tool_folder_does_not_keep_runtime_copies_even_if_named():
    from arcpuzzles.review_retention import _feedback_members
    names = {'checks/custom-prototype/gate.py', 'checks/custom-prototype/test_gate.py',
             'checks/custom-prototype/data/witness.json',
             'checks/custom-prototype/runtime/src/unused.py',
             'checks/custom-prototype/RUNTIME_MANIFEST.json'}
    text = 'Use `checks/custom-prototype/`; copied `checks/custom-prototype/runtime/src/unused.py` is not needed.'
    assert _feedback_members(names, text) == {
        'checks/custom-prototype/gate.py', 'checks/custom-prototype/test_gate.py',
        'checks/custom-prototype/data/witness.json'}


def test_ambiguous_prototype_basename_prevents_transport_deletion(library, tmp_path):
    contract, returned = _return(library, tmp_path, feedback_text='**F1: Tool.**\n\nKeep `gate.py`.\n')
    Path(returned['zip']).unlink()
    packet = tmp_path / 'packet-0'
    for folder in ('first-prototype', 'second-prototype'):
        path = packet / 'checks' / folder / 'gate.py'
        path.parent.mkdir(parents=True)
        path.write_text('raise AssertionError("passive only")\n')
    build_full_return(packet, tmp_path / 'review_response_0.zip')
    receipt = collect_full_returns(library / 'REVIEW', tmp_path)['receipts'][0]
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], 1,
                            'decision', 'deferred', 'Keep useful authored code.')
    with pytest.raises(ValueError, match='Ambiguous.*gate.py'):
        compact_reviews(library, apply=True)
    assert Path(receipt['archive_path']).is_file()
    assert (library / 'REVIEW/assignments' / contract['assignment_id']).is_dir()
    from arcpuzzles.review_assess import record_feedback
    record_feedback(library / 'REVIEW', contract['assignment_id'], 1, 'F1', 'deferred',
                    'Exact intended prototype: `checks/first-prototype/gate.py`.')
    compact_reviews(library, apply=True)
    assert not Path(receipt['archive_path']).exists()
    request = json.loads((library / 'REVIEW/suggestions.json').read_text())['items'][0]
    manifest = json.loads((library / request['assets_manifest']['path']).read_text())
    assert {row['source_member'] for row in manifest['files']} == {'checks/first-prototype/gate.py'}
    assert request['text'].endswith('Keep `gate.py`.')
    assert 'checks/first-prototype/gate.py' in request['reason']


def test_audit_disposition_clarifies_relative_receipt_before_transport_deletion(library, tmp_path):
    contract, returned = _return(library, tmp_path, audit=True)
    Path(returned['zip']).unlink()
    packet = tmp_path / 'packet-0'
    targets = json.loads((packet / 'AUDIT_ASSIGNMENT.json').read_text())['targets']
    tid = targets[0]['task_id']
    (packet / 'AUDIT.md').write_text(f"## {tid}\nEvidence: `racket.json`.\n\n"
                                   f"## {targets[1]['task_id']}\nNo additional witness.\n")
    for folder in ('first', 'second'):
        path = packet / f'checks/{folder}/racket.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'task_id': tid, 'selected': folder}))
    build_full_return(packet, tmp_path / 'review_response_0.zip')
    receipt = collect_full_returns(library / 'REVIEW', tmp_path)['receipts'][0]
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], 1,
                            'decision', 'deferred', 'Retain relevant witnesses.')
    with pytest.raises(ValueError, match='Ambiguous.*racket.json'):
        compact_reviews(library, apply=True)
    assert Path(receipt['archive_path']).is_file()
    from arcpuzzles.review_notes import record_audit_status, read_index
    record_audit_status(library, tid, contract['assignment_id'] + ':v0001', 'unresolved',
                        'Intended receipt: `checks/first/racket.json`; finding remains open.')
    compact_reviews(library, apply=True)
    assert not Path(receipt['archive_path']).exists()
    audit = read_index(library, tid)['audits'][0]
    assert audit['resolution'] == 'unresolved'
    assert audit['text'] == f'## {tid}\nEvidence: `racket.json`.\n\n'
    manifest = json.loads((library / audit['assets_manifest']).read_text())
    assert {row['original_member'] for row in manifest['files']} == {'checks/first/racket.json'}


def test_relative_audit_receipts_survive_without_return_archive(library, tmp_path):
    contract, returned = _return(library, tmp_path, audit=True)
    Path(returned['zip']).unlink()
    packet = tmp_path / 'packet-0'
    targets = json.loads((packet / 'AUDIT_ASSIGNMENT.json').read_text())['targets']
    sections = []
    for target in targets:
        tid = target['task_id']
        path = packet / f'checks/audit/{tid}/racket.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'task_id': tid, 'output': [[3]], 'scope': 'synthetic fixture'}))
        sections.append(f'## {tid}\nCounterexample authority receipt: `racket.json`.\n')
    (packet / 'AUDIT.md').write_text('\n'.join(sections))
    build_full_return(packet, tmp_path / 'review_response_0.zip')
    receipt = collect_full_returns(library / 'REVIEW', tmp_path)['receipts'][0]
    record_full_disposition(library / 'REVIEW', contract['assignment_id'], 1,
                            'decision', 'deferred', 'Retain both audit receipts.')
    compact_reviews(library, apply=True)
    assert not Path(receipt['archive_path']).exists()
    shutil.rmtree(packet)
    for target in targets:
        tid = target['task_id']
        state = json.loads((library / f'generators/{tid}/evidence/review_index.json').read_text())
        manifest = json.loads((library / state['audits'][0]['assets_manifest']).read_text())
        records = [x for x in manifest['files'] if x.get('original_member') == f'checks/audit/{tid}/racket.json']
        assert len(records) == 1
        assert json.loads((library / records[0]['path']).read_text())['task_id'] == tid
        assert digest((library / records[0]['path']).read_bytes()) == records[0]['sha256']


@pytest.mark.parametrize('file_format', ['mapping', 'runtime_records'])
def test_small_check_report_drops_unrelated_runtime_inventory_only(file_format):
    from arcpuzzles.review_retention import _curate_report
    task = 'aaaa00000001'
    files = {f'generators/{task}/generator.py': 'bound-generator',
             'generators/aaaa00000002/generator.py': 'unrelated-source'}
    expected = {f'generators/{task}/generator.py': 'bound-generator'}
    if file_format == 'runtime_records':
        files = [{'library_path': path, 'runtime_path': path, 'sha256': binding}
                 for path, binding in files.items()]
        expected = files[:1]
    value = {'schema': 'arcpuzzles-check-v1', 'task_id': task, 'status': 'completed',
             'passed': False, 'test_counts': {'failed': 1}, 'stderr': 'actual failure',
             'settings': {'controller_sha256': 'controller'},
             'runtime_manifest': {'task_ids': [task], 'canonical_scope': 'task', 'files': files}}
    raw = canonical_json(value)
    derived, metadata = _curate_report(raw, 'checks/result.json')
    result = json.loads(derived)
    assert result['runtime_manifest']['files'] == expected
    assert result['status'] == value['status'] and result['passed'] is False
    assert result['test_counts'] == value['test_counts'] and result['stderr'] == value['stderr']
    assert result['settings'] == value['settings']
    assert metadata['source_member_sha256'] == digest(raw)
    assert metadata['selection']['runtime_inventory_sha256'] == digest(canonical_json(files))


def test_unknown_report_schema_remains_byte_exact():
    from arcpuzzles.review_retention import _curate_report
    raw = b'{"schema":"future-format","runtime_manifest":{"files":["do not interpret"]}}'
    assert _curate_report(raw, 'checks/result.json') == (raw, {})

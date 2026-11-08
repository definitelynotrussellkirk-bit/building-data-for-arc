"""Research preflight must not grant base approval or native acceptance."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from arcpuzzles import Catalog, parametric_promotion as native
from test_parametric_promotion import candidate, fake_execution


@pytest.fixture
def base_checks_catalog(tmp_path, monkeypatch):
    """Exercise pair handling with deterministic evaluator/generator boundaries."""
    from arcpuzzles import parametric_worker as worker
    state = {'executed': [], 'draws': [], 'closed': False}

    def apply(program, grid):
        state['executed'].append((program, copy.deepcopy(grid)))
        return grid

    def close():
        state['closed'] = True

    def generate(tid, **kwargs):
        state['draws'].append((tid, kwargs))
        return [{'seed': kwargs['seed']}]

    monkeypatch.setattr(worker, '_real_evaluator', lambda runtime: (
        apply, {'backend': 'test_double'}, SimpleNamespace(close=close)))
    catalog = SimpleNamespace(root=tmp_path, records=[], generate=generate,
        describe=lambda tid: {'rule_task_id': 'canonical-base', 'approved': False})
    catalog._variants = lambda: {'canonical-base': catalog.records}
    return catalog, state


@pytest.mark.parametrize('train_mapping', [False, True], ids=['train-list', 'train-mapping'])
@pytest.mark.parametrize('test_mapping', [False, True], ids=['test-list', 'test-mapping'])
def test_base_checks_normalize_pair_views_without_changing_raw_records(
        base_checks_catalog, train_mapping, test_mapping):
    from arcpuzzles import review_base_preflight as author
    catalog, state = base_checks_catalog
    train = {'input': ['12'], 'output': [[1, 2]]}
    test = {'input': [[3]], 'output': ['3']}
    catalog.records = [
        {'program_solution': '(rule! g)', 'lineage': {'seed': 17},
         'train': train if train_mapping else [train],
         'test': test if test_mapping else [test]},
        {'program_solution': '(rule! g)', 'train': [],
         'test': [{'input': [[4]]}, {'input': ['5'], 'output': [[5]]}]},
    ]
    train_collection = catalog.records[0]['train']
    test_collection = catalog.records[0]['test']
    before = copy.deepcopy(catalog.records)
    raw_hash = hashlib.sha256(native._raw(before)).hexdigest()

    report = author._base_checks(catalog, 'base')

    assert [(p['variant'], p['split'], p['index']) for p in report['pairs']] == [
        (0, 'train', 0), (0, 'test', 0), (1, 'test', 1)]
    assert [p['input'] for p in report['pairs']] == [[[1, 2]], [[3]], [[5]]]
    assert state['executed'] == [('(rule! g)', p['input']) for p in report['pairs']]
    assert catalog.records == before
    assert report['canonical_records_sha256'] == raw_hash == author._records_hash(catalog, 'base')
    assert catalog.records[0]['train'] is train_collection
    assert catalog.records[0]['test'] is test_collection
    if train_mapping or test_mapping:
        normalized = copy.deepcopy(before)
        normalized[0]['train'] = [normalized[0]['train']] if train_mapping else normalized[0]['train']
        normalized[0]['test'] = [normalized[0]['test']] if test_mapping else normalized[0]['test']
        assert report['canonical_records_sha256'] != hashlib.sha256(native._raw(normalized)).hexdigest()
    assert state['closed'] and report['base_approved_before'] is False
    assert [(kw['seed'], kw['difficulty']) for _, kw in state['draws']] == [(17, None), (43, 'medium')]
    assert all(tid == 'base' and kw['allow_unapproved'] for tid, kw in state['draws'])


@pytest.mark.parametrize('singleton_mapping', [False, True], ids=['list', 'mapping'])
def test_base_checks_still_reject_label_mismatch_and_close_evaluator(
        base_checks_catalog, singleton_mapping):
    from arcpuzzles import review_base_preflight as author
    catalog, state = base_checks_catalog
    pair = {'input': [[1]], 'output': [[2]]}
    catalog.records = [{'program_solution': '(rule! g)',
                        'test': pair if singleton_mapping else [pair]}]
    before = copy.deepcopy(catalog.records)
    with pytest.raises(ValueError, match=r'Original label mismatch: variant 0 test\[0\]'):
        author._base_checks(catalog, 'base')
    assert state['closed'] and not state['draws']
    assert catalog.records == before


def unapprove(root):
    path = root/'catalog/puzzles.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]['train_safety'] = 'unverified'
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    return path


def test_unapproved_preflight_keeps_catalog_and_native_gate(candidate, monkeypatch, tmp_path):
    from arcpuzzles import review_base_preflight as author
    catalog, tid, _ = candidate
    metadata = unapprove(catalog.root); before = metadata.read_bytes()
    monkeypatch.setattr(author, '_base_checks', lambda catalog, tid: {
        'status': 'passed', 'pairs': [1], 'generation': [[], []],
        'canonical_records_sha256': author._records_hash(catalog, tid)})
    monkeypatch.setattr(native, '_execute', fake_execution)
    result = author.preflight(catalog.root, tid, tmp_path/'preflight')
    assert result['schema'] == author.SCHEMA and result['status'] == 'passed'
    assert result['owner_accepted'] is False and result['training_admitted'] is False
    assert metadata.read_bytes() == before
    assert not Catalog(catalog.root).describe(tid)['approved']
    with pytest.raises(ValueError, match='approved'):
        native.qualify(Catalog(catalog.root), tid, tmp_path/'owner-qualification')
    with pytest.raises(ValueError, match='approved'):
        native.accept(Catalog(catalog.root), tid, Path(result['receipt']), reason='Cannot accept research preflight')
    from arcpuzzles.review_witness import _qualified
    loaded, execution = _qualified(catalog.root, result['receipt'])
    assert loaded['schema'] == author.SCHEMA and execution['base_review']['status'] == 'passed'
    # The report is reusable for causal/private-export helpers, never approval.
    from arcpuzzles.review_parametric_admission import validate_ready_evidence
    progress = {'qualification_path': 'checks/main/qualification.json',
                'promotion_path': f'repo/generators/{tid}/workspace/parametric/promotion.json',
                'inventory_path': f'repo/generators/{tid}/workspace/parametric/evidence/manifest.json'}
    files = {'checks/main/qualification.json': Path(result['receipt']).read_bytes(),
             'checks/main/execution.json': (tmp_path/'preflight/execution.json').read_bytes()}
    inventory = {'repo/'+r['path'] for r in result['source_binding']['files']} | {progress['inventory_path']}
    with pytest.raises(ValueError, match='authoring|qualification'):
        validate_ready_evidence({'task_id': tid}, progress, files.__getitem__, inventory)
    validate_ready_evidence({'task_id': tid, 'base_review_policy': author.POLICY}, progress, files.__getitem__, inventory)


def test_preflight_fails_closed_on_veto_source_drift_and_base_failure(candidate, monkeypatch, tmp_path):
    from arcpuzzles import review_base_preflight as author
    catalog, tid, home = candidate
    metadata = unapprove(catalog.root); before = metadata.read_bytes()
    def broken(*args):
        raise ValueError('Original label mismatch')
    monkeypatch.setattr(author, '_base_checks', broken)
    with pytest.raises(ValueError, match='label mismatch'):
        author.preflight(catalog.root, tid, tmp_path/'broken')
    assert not (tmp_path/'broken').exists() and metadata.read_bytes() == before
    rows = [json.loads(line) for line in metadata.read_text().splitlines()]
    rows[0]['semantic_veto'] = True
    metadata.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    with pytest.raises(ValueError, match='veto'):
        author.source_ready(catalog.root, tid)


def test_only_completed_explicit_base_reviews_can_approve_unchanged_source():
    from arcpuzzles.review_base_preflight import POLICY, completed_base_review
    contract = {'base_review_policy': POLICY}
    report = {'outcome': 'prototype', 'remaining_failures': [],
              'changed_components': ['tests_notes'], 'parametric_work': {'status': 'ready'}}
    assert completed_base_review(contract, report)
    assert not completed_base_review({}, report)
    assert not completed_base_review(contract, {**report, 'parametric_work': {'status': 'blocked'}})
    assert not completed_base_review(contract, {**report, 'remaining_failures': ['base label mismatch']})


def test_missing_inventory_reports_path_and_recovery_command(candidate):
    from arcpuzzles.review_base_preflight import source_ready
    catalog, tid, home = candidate
    (home/'evidence/manifest.json').unlink()
    with pytest.raises(ValueError, match='parametric manifest') as error:
        source_ready(catalog.root, tid)
    assert f'generators/{tid}/workspace/parametric/evidence/manifest.json' in str(error.value)
    assert '--reported-checks' in str(error.value)


def test_owner_reviews_unchanged_unapproved_base_before_native_admission(candidate, monkeypatch, tmp_path):
    """Static intake/approval plumbing; native execution is covered separately."""
    from arcpuzzles import review_base_preflight as author
    from arcpuzzles import review_parametric_admission as admission
    from arcpuzzles.review_full_draw import draw_main, repair_selection_for_seed
    from arcpuzzles.review_full_return import build_full_return
    from arcpuzzles.review_full_collect import collect_full_returns
    from arcpuzzles.review_full_integrate import integrate_full_candidate
    from arcpuzzles.review_targets import TWO_WORK_POLICY
    from test_review_full_draw import _packet
    catalog, tid, _ = candidate
    unapprove(catalog.root)
    packet = _packet(catalog.root, tmp_path, repair_target_count=2, work_policy=TWO_WORK_POLICY)
    manifest = json.loads((packet/'PACKET-MANIFEST.json').read_text())
    seed = next(i.to_bytes(32, 'big') for i in range(100)
                if repair_selection_for_seed(manifest, i.to_bytes(32, 'big'))[0]['task_id'] == tid)
    contract = draw_main(packet, seed)
    monkeypatch.setattr(author, '_base_checks', lambda c, task: {
        'status': 'passed', 'pairs': [1], 'generation': [[], []],
        'canonical_records_sha256': author._records_hash(c, task)})
    monkeypatch.setattr(native, '_execute', fake_execution)
    qpath = f'checks/{tid}/qualification/qualification.json'
    q = author.preflight(packet/'repo', tid, packet/Path(qpath).parent)
    descriptions = dict(step_a='Find the input object.', intermediate='Selected object.',
                        step_b='Transform the selected object.', why_b_depends_on_a='The selection determines the output.')
    witness = {**descriptions, 'schema': 'arcpuzzles-sequential-dependency-witness-v1',
        'source_binding': q['source_binding'], 'racket': {'backend': 'racket', 'protected': True},
        'cases': [{'input': [[1, 2]], 'settings': {'side': 'left'},
                   'intermediate_value': 1, 'output': [[1]], 'counterfactual_output': [[2]],
                   'ablation': 'wrong_intermediate', 'program': '(rule! g)',
                   'counterfactual_program': '(rule! (flip-lr g))'}]}
    wpath = f'checks/{tid}/witness.json'
    (packet/wpath).write_text(json.dumps(witness))
    results = json.loads((packet/'RESULTS.json').read_text())
    row = results['repair_targets'][0]
    home = f'repo/generators/{tid}/workspace/parametric/'
    row.update(outcome='prototype', summary='Base reviewed unchanged; full family built',
               changed_components=['tests_notes'], remaining_failures=[], evidence_paths=[qpath,wpath])
    row['parametric_work'] = {'status': 'ready', 'summary': 'Base and family checked',
        'prototype_path': home+'adapter.py', 'promotion_path': home+'promotion.json',
        'inventory_path': home+'evidence/manifest.json', 'qualification_path': qpath,
        'sequential_dependency': {**descriptions, 'witness_path': wpath}}
    (packet/f'repo/generators/{tid}/notes.md').write_text('Reviewed this exact unchanged base; no outstanding findings.\n')
    (packet/'RESULTS.json').write_text(json.dumps(results))
    for name in ('REVIEW.md','FEEDBACK_TO_CODEX.md'):
        (packet/name).write_text('Research preflight ready; owner admission remains required.\n')
    build_full_return(packet, tmp_path/'review_response_base.zip')
    collected = collect_full_returns(catalog.root/'REVIEW', tmp_path)
    receipt = next(r for r in collected['receipts'] if r.get('assignment_id') == contract['assignment_id'])
    assert receipt['validation_status'] == 'accepted'
    seen = []
    def owner_gate(live, scoped, report, archive, **kwargs):
        if scoped['task_id'] == tid:
            seen.append(Catalog(live.root).describe(tid)['approved'])
        return {'task_id': scoped['task_id'], 'status': 'blocked',
                'objective_met': False, 'training_admitted': False}
    monkeypatch.setattr(admission, 'admit_main', owner_gate)
    result = integrate_full_candidate(Catalog(catalog.root), catalog.root/'REVIEW',
        contract['assignment_id'], receipt['version'], {'tests_notes'}, reviewer_reported=True)
    assert seen == [True]
    assert Catalog(catalog.root).describe(tid)['approved']
    assert result['objective_met'] is False

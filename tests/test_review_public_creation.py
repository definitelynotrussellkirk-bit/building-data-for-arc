import hashlib
import json
import zipfile

import pytest
from test_review_public_admission import public_source

from arcpuzzles.catalog import Catalog
from arcpuzzles.review_full_packet import build_full_packet
from arcpuzzles.review_full_draw import draw_main, repair_selection_for_seed
from arcpuzzles.review_full_return import build_full_return, validate_full_return, _allowed
from arcpuzzles.review_public_creation import PUBLIC_WORK_SCHEMA, creation_queue, preflight, validate_preflight


def public_packet(library, tmp_path):
    raw = library/'shared/data/raw'; raw.mkdir(parents=True)
    parents = {pid: {'train': [{'input': [[1, 2]], 'output': [[1, 2]]}], 'test': [{'input': [[3, 4]]}]}
               for pid in ('11111111', '22222222', '33333333')}
    (raw/'arc-agi_evaluation_challenges.json').write_text(json.dumps(parents))
    questions = library/'REVIEW/questions'; questions.mkdir(parents=True)
    (questions/'q.json').write_text(json.dumps({'schema':'arcpuzzles-review-question-v1', 'id':'q', 'version':1, 'owner':'ARCpuzzles', 'text':'Why?'}))
    result = build_full_packet(Catalog(library), library/'REVIEW', tmp_path/'public.zip', repair_target_count=2)
    packet=tmp_path/'packet'; packet.mkdir()
    with zipfile.ZipFile(result['zip']) as z: z.extractall(packet)
    return packet


def test_public_queue_preempts_approved_generators_and_frozen_draw_resumes(library, tmp_path):
    packet=public_packet(library,tmp_path)
    manifest=json.loads((packet/'PACKET-MANIFEST.json').read_text())
    assert manifest['work_policy']['schema']==PUBLIC_WORK_SCHEMA
    assert len(manifest['public_eval_creation']['parents'])==3
    assert manifest['public_eval_creation']['coverage_cutoff']==2
    assert manifest['public_eval_creation']['allocation_phase']=='uniform_all_public'
    contract=draw_main(packet, bytes(32))
    rows=contract['repair_targets']
    assert len(rows)==2 and len({r['task_id'] for r in rows})==2
    assert all(r['task_id'].startswith('public_eval_') and r['generator']['approved'] is False for r in rows)
    assert not any((packet/'repo/generators'/r['task_id']/'generator.py').exists() for r in rows)
    assert draw_main(packet,bytes([1])*32)==contract
    text=(packet/'DUTIES.md').read_text()
    assert 'YOU MUST CREATE ONE' in text and 'BOTH' in text and 'ALL 120' in text
    results=json.loads((packet/'RESULTS.json').read_text())
    assert len(results['repair_targets'])==2
    assert all(r['parametric_work']['status']=='blocked' for r in results['repair_targets'])
    assert _allowed('repo/generators/'+rows[0]['task_id']+'/reference.rkt',contract)
    assert not _allowed('repo/generators/'+rows[0]['task_id']+'/workspace/public-parent.json',contract)


def test_missing_public_rule_is_not_ordinary_ready_and_partial_return_roundtrips(library,tmp_path):
    packet=public_packet(library,tmp_path); contract=draw_main(packet,bytes(32))
    (packet/'REVIEW.md').write_text('Public rule authoring remains unfinished.')
    (packet/'FEEDBACK_TO_CODEX.md').write_text('No extra feedback.')
    for row in contract['repair_targets']:
        home=packet/'repo/generators'/row['task_id']
        (home/'notes.md').write_text('Unfinished; no approval claimed.\n')
    results=json.loads((packet/'RESULTS.json').read_text())
    for row in results['repair_targets']: row['changed_components']=['tests_notes']
    (packet/'RESULTS.json').write_text(json.dumps(results))
    result=build_full_return(packet,tmp_path/'returned.zip')
    manifest=json.loads((packet/'PACKET-MANIFEST.json').read_text())
    with zipfile.ZipFile(result['zip']) as z:
        checked=validate_full_return(z,manifest)
        intake=json.loads(z.read('INTAKE.json'))
    assert checked['completion_state']=='in_progress'
    assert intake['parametric_admission']['objective_met'] is False
    assert intake['parametric_admission']['required_count']==2


def test_preflight_rejects_source_drift_before_loading_adapter(library,tmp_path):
    packet=public_packet(library,tmp_path); contract=draw_main(packet,bytes(32))
    root=packet/'repo'; row=contract['repair_targets'][0]; tid=row['task_id']
    source=root/'shared/data/raw/arc-agi_evaluation_challenges.json'
    parents=json.loads(source.read_text()); parents[row['generator']['public_creation']['public_task_id']]['train'][0]['output']=[[9]]
    source.write_text(json.dumps(parents))
    with pytest.raises(ValueError,match='Official source identity changed'):
        preflight(root,tid,tmp_path/'checks')


def test_uniform_selection_keeps_unapproved_missing_parents_in_pool(library,tmp_path):
    packet=public_packet(library,tmp_path)
    manifest=json.loads((packet/'PACKET-MANIFEST.json').read_text())
    seen=set()
    for seed in range(60):
        rows=repair_selection_for_seed(manifest,seed.to_bytes(32,'big'))
        assert len({r['task_id'] for r in rows})==2
        seen.update(r['task_id'] for r in rows)
    assert seen==set(manifest['public_eval_creation']['ids'])


def test_last_missing_parent_is_always_first_and_second_is_distinct_public(library,tmp_path,monkeypatch):
    import sys, types
    public_packet(library,tmp_path)
    module=types.ModuleType('arcpuzzles.review_public_admission')
    module.verified_coverage=lambda root: {'11111111','22222222'}
    monkeypatch.setitem(sys.modules,'arcpuzzles.review_public_admission',module)
    queue=creation_queue(library)
    assert len(queue)==3
    assert [r['public_task_id'] for r in queue if r['needs_creation']]==['33333333']
    from arcpuzzles.review_public_creation import PUBLIC_WORK_POLICY, select
    rows={r['task_id']:{'job_kind':'public_eval_creation','public_creation':r} for r in queue}
    manifest={'work_policy':PUBLIC_WORK_POLICY,'public_eval_creation':{'ids':sorted(rows)},'generators':rows}
    for n in range(20):
        chosen=select(manifest,n.to_bytes(32,'big'))
        assert chosen[0]['task_id']=='public_eval_33333333'
        assert chosen[1]['task_id']!=chosen[0]['task_id']


def test_supplied_test_gold_is_bound_separately_and_cannot_drift(library,tmp_path):
    # Gold must never enter the public challenge identity.
    raw=library/'shared/data/raw';raw.mkdir(parents=True)
    task={'train':[{'input':[[1]],'output':[[1]]}], 'test':[{'input':[[2]]}]}
    (raw/'arc-agi_evaluation_challenges.json').write_text(json.dumps({'1234abcd':task}))
    gold=raw/'arc-agi_evaluation_solutions.json';gold.write_text(json.dumps({'1234abcd':[[[2]]]}))
    from arcpuzzles.review_public_creation import add_creation_sources, digest
    queue=creation_queue(library);files={};add_creation_sources(library,files,queue)
    item=queue[0];assert item['test_outputs_sha256']==digest([[[2]]])
    source=files['repo/generators/public_eval_1234abcd/workspace/public-parent.json']
    home=library/'generators/public_eval_1234abcd/workspace';home.mkdir(parents=True)
    (home/'public-parent.json').write_bytes(source.read_bytes())
    gold.write_text(json.dumps({'1234abcd':[[[9]]]}))
    with pytest.raises(ValueError,match='Official test gold identity changed'):
        preflight(library,'public_eval_1234abcd',tmp_path/'gold-check')


def phased_manifest(count, covered):
    from arcpuzzles.review_public_creation import PUBLIC_WORK_POLICY, allocation_policy
    queue=[{'public_task_id':f'{i:08x}','task_id':f'public_eval_{i:08x}','needs_creation':i>=covered} for i in range(count)]
    rows={r['task_id']:{'job_kind':'public_eval_creation','public_creation':r} for r in queue}
    return {'work_policy':PUBLIC_WORK_POLICY,'generators':rows,
            'public_eval_creation':{'ids':sorted(rows),'parents':queue,**allocation_policy(queue)}}


def test_all_120_remain_equally_eligible_until_60_distinct_are_covered():
    from arcpuzzles.review_public_creation import select
    empty=phased_manifest(120,0);half_less_one=phased_manifest(120,59)
    assert half_less_one['public_eval_creation']['coverage_cutoff']==60
    assert half_less_one['public_eval_creation']['allocation_phase']=='uniform_all_public'
    seen=set()
    for seed in range(400):
        raw=seed.to_bytes(32,'big')
        # Coverage flags have no influence whatsoever on an early-phase draw.
        first=select(empty,raw);second=select(half_less_one,raw)
        assert [r['task_id'] for r in first]==[r['task_id'] for r in second]
        assert len({r['task_id'] for r in second})==2
        seen.update(r['task_id'] for r in second)
    assert seen==set(empty['public_eval_creation']['ids'])


def test_cutoff_switches_to_uncovered_and_last_missing_is_first():
    from arcpuzzles.review_public_creation import select
    threshold=phased_manifest(120,60)
    assert threshold['public_eval_creation']['allocation_phase']=='uncovered_first'
    for seed in range(40):
        assert all(r['generator']['public_creation']['needs_creation'] for r in select(threshold,seed.to_bytes(32,'big')))
    last=phased_manifest(120,119)
    for seed in range(20):
        rows=select(last,seed.to_bytes(32,'big'))
        assert rows[0]['task_id']=='public_eval_00000077'
        assert rows[1]['task_id']!=rows[0]['task_id']


def test_toy_cutoff_is_ceil_half_and_manifest_claims_are_checked():
    from arcpuzzles.review_public_creation import select
    toy=phased_manifest(3,1)
    assert toy['public_eval_creation']['coverage_cutoff']==2
    assert toy['public_eval_creation']['allocation_phase']=='uniform_all_public'
    toy['public_eval_creation']['coverage_cutoff']=1
    with pytest.raises(ValueError,match='cutoff'):select(toy,bytes(32))


def test_public_home_payload_omits_repeated_owner_proofs_and_acceptance(public_source):
    # Reuse an independent source fixture; accepted evidence is intentionally huge in real homes.
    from arcpuzzles.review_public_creation import add_creation_sources
    root,item,parent,program=public_source
    home=root/'generators'/item['task_id']
    keep=['tests/test_family.py','notes.md','workspace/parametric/canonical.rkt']
    drop=['evidence/public-owner/run/preflight/execution.json','evidence/public-coverage/proof.json',
          'parametric/accepted.json','workspace/parametric/evidence/manifest.json']
    for name in keep+drop:
        path=home/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('{}\n')
    files={'repo/'+(home/name).relative_to(root).as_posix():home/name for name in keep+drop}
    add_creation_sources(root,files,[item])
    for name in keep:assert 'repo/'+(home/name).relative_to(root).as_posix() in files
    for name in drop:assert 'repo/'+(home/name).relative_to(root).as_posix() not in files


def test_issued_public_policy_without_phase_keeps_its_original_missing_first_draw():
    from arcpuzzles.review_public_creation import PUBLIC_LEGACY_WORK_POLICY, select
    from arcpuzzles.review_targets import validate_work_policy
    manifest=phased_manifest(3,1)
    manifest['work_policy']=PUBLIC_LEGACY_WORK_POLICY
    for key in ('allocation_phase','coverage_cutoff','verified_covered_count','source_count'):
        manifest['public_eval_creation'].pop(key)
    validate_work_policy(manifest,manifest)
    for seed in range(12):
        assert all(row['generator']['public_creation']['needs_creation'] for row in select(manifest,seed.to_bytes(32,'big')))


@pytest.fixture
def base_preflight(public_source, monkeypatch):
    """Complete authoring flow with a counted evaluator, no catalog admission."""
    import copy
    from types import SimpleNamespace
    root, item, parent, program = public_source
    home = root / 'generators' / item['task_id']
    (home/'workspace/public-parent.json').write_text(json.dumps(item))
    parser = root/'shared/tools/comment_solutions.py'
    parser.parent.mkdir(parents=True, exist_ok=True); parser.write_text('# fixture parser\n')
    import shutil
    from pathlib import Path
    parser_source = Path(__file__).resolve().parents[1]/'shared/runtime/arc_repl/parser.py'
    parser_target = root/'shared/runtime/arc_repl/parser.py'
    parser_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(parser_source, parser_target)
    (home/'workspace/parametric/adapter.py').write_text(f'''
def program(settings):
    return '(rule! (flip-lr g))' if settings['reverse'] else {program!r}
def generate(seed, settings, demos, queries):
    pairs = [{{'input': [[i, 9]], 'output': [[9, i]] if settings['reverse'] else [[i, 9]]}}
             for i in range(demos + queries)]
    return {{'program_solution': program(settings), 'train': pairs[:demos], 'test': pairs[demos:]}}
''')
    state = {'starts': 0, 'closed': 0, 'calls': []}
    def evaluator(runtime):
        assert runtime == root/'shared/runtime'
        state['starts'] += 1
        def apply(rule, grid):
            state['calls'].append(copy.deepcopy(grid))
            return [row[::-1] for row in grid] if rule == '(rule! (flip-lr g))' else copy.deepcopy(grid)
        def close(): state['closed'] += 1
        return apply, {'backend': 'racket', 'protected': True}, SimpleNamespace(close=close)
    monkeypatch.setattr('arcpuzzles.parametric_worker._real_evaluator', evaluator)
    return root, item, home, state


def test_preflight_base_dict_draws_use_same_evaluator_and_local_imports(base_preflight, tmp_path):
    import sys
    root, item, home, state = base_preflight
    neighbor = '_base_neighbor_' + hashlib.sha256(str(root).encode()).hexdigest()[:12]
    (home/(neighbor+'.py')).write_text('def draw(seed, sample_index):\n    return [[seed % 10, sample_index]]\n')
    (home/'generator.py').write_text(f'''RULE_TASK_ID='ee_1234abcd'
from {neighbor} import draw
def generate(*, seed, sample_index, difficulty):
    assert difficulty in (None, 'medium')
    return {{'input': draw(seed, sample_index), 'metadata': 'allowed'}}
def self_check(grid, **kwargs):
    assert kwargs == {{'difficulty': None if grid[0][1] == 0 else 'medium'}}
    return []
''')
    out = tmp_path/'base-pass'
    try:
        preflight(root, item['task_id'], out)
        assert str(home) in sys.modules[neighbor].__file__
    finally:
        sys.modules.pop(neighbor, None)
    execution = json.loads((out/'execution.json').read_text())
    assert execution['program_syntax'] == {'status': 'passed', 'check': 'one_complete_rule_or_lambda', 'program_count': 3}
    checks = execution['base_generation']
    assert [(c['seed'], c['sample_index'], c['input'], c['output']) for c in checks] == [
        (17, 0, [[7, 0]], [[7, 0]]), (43, 1, [[3, 1]], [[3, 1]])]
    assert [c['difficulty'] for c in checks] == [None, 'medium']
    assert all(c['self_check_run'] for c in checks)
    assert state['starts'] == state['closed'] == 1
    assert state['calls'][:2] == [[[7, 0]], [[3, 1]]]


def test_preflight_rejects_base_tuple_before_adapter_lessons(base_preflight, tmp_path):
    root, item, home, state = base_preflight
    (home/'generator.py').write_text("RULE_TASK_ID='ee_1234abcd'\ndef generate(**kwargs):\n    return ([[1]], {'metadata': 1})\n")
    with pytest.raises(ValueError, match='grid must be rectangular'):
        preflight(root, item['task_id'], tmp_path/'base-fail')
    assert state == {'starts': 1, 'closed': 1, 'calls': []}
    assert not (tmp_path/'base-fail').exists()


@pytest.mark.parametrize('checker, error', [
    ('def self_check(grid):\n    grid[0][0] = 2\n    return []\n', 'mutated its input'),
    ('def self_check(grid, difficulty):\n    assert difficulty is None\n    return ["bad scene"]\n', 'bad scene'),
])
def test_base_self_check_findings_and_mutation_fail(checker, error):
    from types import SimpleNamespace
    from arcpuzzles.review_public_creation import _base_generation
    namespace = {}; exec(checker, namespace)
    module = SimpleNamespace(generate=lambda **kwargs: [[1]], self_check=namespace['self_check'])
    with pytest.raises(ValueError, match=error):
        _base_generation(module, lambda rule, grid: grid, 'identity')


def test_base_plain_grid_and_plain_self_check_signature():
    from types import SimpleNamespace
    from arcpuzzles.review_public_creation import _base_generation
    module = SimpleNamespace(generate=lambda **kwargs: [[1]], self_check=lambda grid: [])
    assert len(_base_generation(module, lambda rule, grid: grid, 'identity')) == 2
    with pytest.raises(ValueError, match='exact integer'):
        _base_generation(module, lambda rule, grid: [[True]], 'invalid-output')
    with pytest.raises(ValueError, match='callable generate'):
        _base_generation(SimpleNamespace(), lambda rule, grid: grid, 'identity')


@pytest.mark.parametrize('bad', ['(rule! (flip-lr g)))', '(rule! (flip-lr g)) (rule! g)', '(rule! (flip-lr g)'])
def test_public_preflight_rejects_whole_form_errors_before_evaluator(base_preflight, tmp_path, bad):
    root, item, home, state = base_preflight
    adapter = home/'workspace/parametric/adapter.py'
    adapter.write_text(adapter.read_text().replace(repr('(rule! (flip-lr g))'), repr(bad)))
    with pytest.raises(ValueError, match='one complete'):
        preflight(root, item['task_id'], tmp_path/'bad-syntax')
    assert state['starts'] == 0
    assert not (tmp_path/'bad-syntax').exists()


def test_public_preflight_rejects_malformed_canonical_before_evaluator(base_preflight, tmp_path):
    root, item, home, state = base_preflight
    reference = home/'reference.rkt'; original = reference.read_text(); bad = original + ')'
    reference.write_text(bad)
    adapter = home/'workspace/parametric/adapter.py'
    adapter.write_text(adapter.read_text().replace(repr(original), repr(bad)))
    with pytest.raises(ValueError, match='one complete'):
        preflight(root, item['task_id'], tmp_path/'bad-canonical')
    assert state['starts'] == 0


@pytest.mark.parametrize('reject_in', ['generate', 'self_check'])
def test_preflight_rejects_default_worker_difficulty_before_lessons(base_preflight, tmp_path, reject_in):
    root, item, home, state = base_preflight
    (home/'generator.py').write_text(f"""RULE_TASK_ID='ee_1234abcd'
def generate(*, seed, sample_index, difficulty):
    if {reject_in!r} == 'generate' and difficulty is None:
        raise ValueError('Unknown difficulty: None')
    return [[1]]
def self_check(grid, *, difficulty):
    if {reject_in!r} == 'self_check' and difficulty is None:
        return ['Unknown difficulty: None']
    return []
""")
    out = tmp_path/'default-worker-fail'
    with pytest.raises(ValueError, match='Unknown difficulty: None'):
        preflight(root, item['task_id'], out)
    assert state == {'starts': 1, 'closed': 1, 'calls': []}
    assert not out.exists()


def test_syntax_only_command_checks_whole_forms_without_evaluator(base_preflight, capsys):
    from arcpuzzles.review_programs import main
    root, item, home, state = base_preflight
    reference = home/'reference.rkt'
    assert main(['--library', str(root), str(reference)]) == 0
    assert json.loads(capsys.readouterr().out)['program_count'] == 1
    reference.write_text('(rule! g))')
    with pytest.raises(ValueError, match='one complete'):
        main(['--library', str(root), str(reference)])
    assert state['starts'] == 0

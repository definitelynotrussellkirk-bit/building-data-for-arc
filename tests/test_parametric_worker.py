import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from arcpuzzles.parametric_worker import evaluate_contract


TID = 'aaaa00000001'


def _contract(root, extra='', default_program='(rule! g)'):
    path = root / f'generators/{TID}/workspace/parametric/adapter.py'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'''
print('adapter import chatter')
def program(settings):
    return {default_program!r} if settings['side'] == 'normal' else '(rule! (flip-lr g))'
def generate(seed, settings, demos, queries):
    print('adapter generation chatter')
    pairs = []
    for i in range(demos + queries):
        grid = [[((seed+i)//10)%10, (seed+i)%10, 9]]
        output = [list(grid[0])] if settings['side'] == 'normal' else [list(reversed(grid[0]))]
        pairs.append({{'input': grid, 'output': output}})
    train, test = pairs[:demos], pairs[demos:]
    {extra or 'pass'}
    return {{'train': train, 'test': test, 'program_solution': program(settings)}}
''')
    return {'adapter': path.relative_to(root).as_posix(),
            'parameters': {'side': ['normal', 'reversed']}, 'default': {'side': 'normal'}}


def _job(**kw):
    return {'seed': 17, 'settings': {'side': 'normal'}, 'demos': 2, 'queries': 2, **kw}


def _apply(program, grid):
    return [list(reversed(row)) for row in grid] if 'flip-lr' in program else copy.deepcopy(grid)


def test_finite_demo_identification_and_private_labels(library):
    result = evaluate_contract(library, TID, _contract(library), [_job()], apply_program=_apply)
    assert result['racket'] == {'backend': 'test', 'protected': False}
    assert result['racket_evaluations'] == 6
    check = result['checks'][0]
    assert check['settings'] == {'side': 'normal'} and check['seed'] == 17
    assert check['survivors'] == [{'side': 'normal'}] and check['label_count'] == 4
    episode = result['episodes'][0]
    assert episode['task_id'] == TID and episode['program'] == '(rule! g)'
    assert episode['reference'] == 'accepted_parametric'
    assert len(episode['train']) == len(episode['test']) == 2
    assert len(episode['program_sha256']) == 64


@pytest.mark.parametrize('key,value', [('seed', True), ('seed', -1), ('seed', 2**63),
    ('seed', 1.0), ('demos', True), ('demos', 0), ('demos', 33), ('queries', 0), ('queries', 1.0)])
def test_strict_job_counts_and_seed(library, key, value):
    with pytest.raises(ValueError):
        evaluate_contract(library, TID, _contract(library), [_job(**{key: value})], apply_program=_apply)


@pytest.mark.parametrize('settings', [{'side': True}, {'side': 1}, {}, {'side': 'normal', 'extra': 0}])
def test_exact_typed_setting_membership(library, settings):
    with pytest.raises(ValueError, match='settings'):
        evaluate_contract(library, TID, _contract(library), [_job(settings=settings)], apply_program=_apply)


def test_type_equality_does_not_equate_boolean_and_integer(library):
    contract = _contract(library);contract['parameters'] = {'side': [1]};contract['default'] = {'side': 1}
    with pytest.raises(ValueError, match='settings'):
        evaluate_contract(library, TID, contract, [_job(settings={'side': True})], apply_program=_apply)


@pytest.mark.parametrize('extra', ["train[0]['input'] = [[True]]", "test[0]['output'] = [[1.0]]",
    "train[0]['input'] = [[1], [1, 2]]", "test[0]['input'] = [[1]*31]",
    "test[0]['output'] = []", "train.pop()", "test[0]['input'] = train[0]['input']",
    "test[0]['output'] = [[0]]"])
def test_rejects_bad_grids_counts_duplicates_and_unexecuted_labels(library, extra):
    with pytest.raises(ValueError):
        evaluate_contract(library, TID, _contract(library, extra), [_job()], apply_program=_apply)


def test_default_program_must_match_canonical_bytes(library):
    with pytest.raises(ValueError, match='canonical'):
        evaluate_contract(library, TID, _contract(library, default_program='(rule! g)\n'),
                          [_job()], apply_program=_apply)


def test_default_program_uses_distinct_selected_rule_authority(library):
    authority = 'aaaa00000002'
    catalog_path = library / 'catalog/puzzles.jsonl'
    rows = [json.loads(line) for line in catalog_path.read_text().splitlines()]
    for row in rows:
        if row['id'] == TID:
            row['rule_task_id'] = authority
    # A projected packet can retain authority rows without its catalog/generator.
    rows = [row for row in rows if row['id'] != authority]
    catalog_path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    canonical_path = library / 'shared/data/canonical/puzzles.jsonl'
    canonical = [json.loads(line) for line in canonical_path.read_text().splitlines()]
    selected_program = '(rule! (lambda (g) g))'
    for row in canonical:
        if row['task_id'] == authority:
            row['program_solution'] = selected_program
    canonical_path.write_text(''.join(json.dumps(row) + '\n' for row in canonical))
    # The generator's own archival rule differs from its selected authority.
    result = evaluate_contract(library, TID, _contract(library, default_program=selected_program),
                               [_job()], apply_program=_apply)
    assert result['episodes'][0]['task_id'] == TID
    assert result['episodes'][0]['program'] == selected_program
    with pytest.raises(ValueError, match='canonical'):
        evaluate_contract(library, TID, _contract(library), [_job()], apply_program=_apply)


def test_program_solution_must_match_selected_program(library):
    contract = _contract(library)
    path = library / contract['adapter']
    path.write_text(path.read_text().replace("'program_solution': program(settings)", "'program_solution': '(rule! wrong)'"))
    with pytest.raises(ValueError, match='program_solution'):
        evaluate_contract(library, TID, contract, [_job()], apply_program=_apply)


def test_more_than_sixteen_settings_is_rejected(library):
    contract = _contract(library);contract['parameters']['side'] = list(range(17))
    with pytest.raises(ValueError, match='16'):
        evaluate_contract(library, TID, contract, [_job()], apply_program=_apply)


@pytest.mark.parametrize('behavior', ['agree', 'exception', 'invalid_grid'])
def test_rival_agreement_or_broken_execution_cannot_manufacture_identifiability(library, behavior):
    calls = []
    def apply(program, grid):
        calls.append((program, grid))
        if 'flip-lr' in program:
            if behavior == 'exception':
                raise RuntimeError('broken rival')
            if behavior == 'invalid_grid':
                return [[False]]
        return copy.deepcopy(grid)
    with pytest.raises((ValueError, RuntimeError)):
        evaluate_contract(library, TID, _contract(library), [_job()], apply_program=apply)
    assert len(calls) <= 4  # No query input is executed when demos do not identify a valid sole setting.


def test_only_demo_survivor_executes_query_inputs(library):
    calls = []
    def apply(program, grid):
        calls.append((program, grid));return _apply(program, grid)
    evaluate_contract(library, TID, _contract(library), [_job()], apply_program=apply)
    queries = {json.dumps([[1, 9, 9]]), json.dumps([[2, 0, 9]])}
    assert all('flip-lr' not in p for p, g in calls if json.dumps(g) in queries)


def test_adapter_path_cannot_escape_same_task_home(library):
    contract = _contract(library);contract['adapter'] = '../adapter.py'
    with pytest.raises(ValueError, match='adapter'):
        evaluate_contract(library, TID, contract, [_job()], apply_program=_apply)


def test_real_worker_cli_emits_one_json_with_protected_same_checkout_runtime(library, tmp_path):
    if shutil.which('racket') is None:
        pytest.skip('A real Racket executable is required')
    source = Path(__file__).resolve().parents[1]
    runtime = library / 'shared/runtime';runtime.mkdir(parents=True)
    shutil.copytree(source / 'shared/runtime/arc_repl', runtime / 'arc_repl',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    (runtime / 'puzzle_generators').mkdir()
    for name in ('__init__.py', 'base.py', 'rule_wrap.py'):
        shutil.copy2(source / 'shared/runtime/puzzle_generators' / name, runtime / 'puzzle_generators' / name)
    tools = library / 'shared/tools';tools.mkdir()
    shutil.copy2(source / 'shared/tools/comment_solutions.py', tools / 'comment_solutions.py')
    identity = '(rule! (lambda (g) g))'
    canonical_path = library / 'shared/data/canonical/puzzles.jsonl'
    canonical = [json.loads(line) for line in canonical_path.read_text().splitlines()]
    for row in canonical:
        if row['task_id'] == TID:
            row['program_solution'] = identity
    canonical_path.write_text(''.join(json.dumps(row) + '\n' for row in canonical))
    contract = _contract(library, default_program=identity)
    request = tmp_path / 'request.json'
    request.write_text(json.dumps({'root': str(library), 'task_id': TID, 'contract': contract, 'jobs': [_job()]}))
    env = dict(os.environ, PYTHONPATH=str(source / 'src'))
    run = subprocess.run([sys.executable, '-m', 'arcpuzzles.parametric_worker', str(request)],
                         cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stdout + run.stderr
    assert len(run.stdout.splitlines()) == 1
    result = json.loads(run.stdout)
    assert result['racket']['backend'] == 'racket' and result['racket']['protected'] is True
    assert result['racket_evaluations'] == 6
    assert 'adapter import chatter' in run.stderr and 'adapter generation chatter' in run.stderr
    assert not list((library / 'generators').rglob('__pycache__'))

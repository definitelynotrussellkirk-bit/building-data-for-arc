"""Saved draws keep their original source while live rivals are rechecked."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_lesson_census import load, ROOT


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def saved():
    tool = load('rescore_worker', ROOT / 'shared/tools/lesson_census.py')
    instance = {'task_id': 'x', 'rule_task_id': 'x', 'rule_file': 'canonical',
                'train': [{'input': [[1]], 'output': [[1]]}, {'input': [[2]], 'output': [[2]]}],
                'test': [{'input': [[3]], 'output': [[3]]}]}
    manifest = {'task_id': 'x', 'files': [{'library_path': 'generators/x/generator.py', 'sha256': 'a' * 64}]}
    return {'schema': 'arcpuzzles-lesson-census-v1', 'task_id': 'x', 'status': 'no_ambiguity_found',
            'production_status': 'no_ambiguity_found', 'rotation_status': 'not_requested', 'errors': [],
            'execution': {'exit_code': 0, 'timed_out': False}, 'generator_sha256': 'a' * 64,
            'declared_rule_hash': 'rulepin', 'rule_task_id': 'x', 'rule_file': 'canonical',
            'rule_source_sha256': sha(b'rule'), 'rule_callable_sha256': sha(b'callable'),
            'runtime_manifest': manifest, 'runtime_manifest_sha256': sha((json.dumps(manifest, indent=2) + '\n').encode()),
            'summary': {'requested': 1, 'materialized': 1, 'pairs': 3, 'rotations': 0,
                        'materialization_errors': 0, 'scoring_errors': 0, 'rotation_scoring_errors': 0},
            'sampler': {'bands': ['easy'], 'per_band': 1, 'n_demos': 2, 'n_queries': 1, 'rotate_query': False},
            'per_band': {'easy': {'requested': 1, 'materialized': 1}},
            'lessons': [{'band': 'easy', 'index': 0, 'seed': 1, 'sample_index': 0, 'errors': [],
                         'instance': instance, 'instance_sha256': tool.digest(instance), 'rotations': []}]}


def bundle(tmp_path, *, broken=False):
    source = tmp_path / 'generator.py'
    source.write_text("TASK_ID = 'x'\nRULE_HASH = 'rulepin'\n"
                      'def rival(grid):\n    return [[9]] if grid == [[1]] else grid\n'
                      'SEMANTIC_RIVALS = {"witness": rival}\nLESSON_COMPETITORS = {"witness": lambda g: g}\n'
                      + ('CANONICAL_SHORTCUTS = {"broken": lambda g: None}\n' if broken else ''))
    gen = SimpleNamespace(__file__=str(source))
    exec(compile(source.read_bytes(), str(source), 'exec'), gen.__dict__)
    return SimpleNamespace(generator_module=gen, kind='per_puzzle', rule_source='rule',
                           rule_callable_text='callable', rule_task_id='x', rule_file='canonical')


def test_rescore_checks_every_position_and_retains_counterexample(saved, tmp_path):
    tool = load('rescore_worker', ROOT / 'shared/tools/lesson_census.py')
    assert hasattr(tool, 'rescore_census')
    current = bundle(tmp_path)
    original = deepcopy(saved)
    report = tool.rescore_census(saved, current)
    assert report['status'] == 'ambiguous'
    assert report['production_status'] == 'no_ambiguity_found'
    assert report['rotation_status'] == 'ambiguous'
    assert report['input_generator_sha256'] == 'a' * 64
    assert report['rival_generator_sha256'] == sha(Path(current.generator_module.__file__).read_bytes())
    assert report['new_reference_executions'] == report['new_generated_instances'] == 0
    wrong = report['rival_summary']['SEMANTIC_RIVALS:witness']
    assert wrong['production'] == {'refuted': 1}
    assert wrong['rotations'] == {'ambiguous': 1, 'refuted': 2}
    example = wrong['counterexample']
    assert example['query_index'] == 0 and example['prediction'] == [[9]]
    assert example['instance'] == saved['lessons'][0]['instance']
    assert report['rival_summary']['LESSON_COMPETITORS:witness']['rotations'] == {'survived_all': 3}
    assert saved == original


@pytest.mark.parametrize('case', ['empty', 'incomplete', 'errors', 'timeout', 'exit', 'partial', 'manifest',
    'generator', 'instance', 'bad_label', 'duplicate', 'band', 'rotation_error', 'sampler_partial', 'rule'])
def test_invalid_retained_evidence_is_rejected(saved, tmp_path, case):
    tool = load('rescore_worker', ROOT / 'shared/tools/lesson_census.py')
    assert hasattr(tool, 'rescore_census')
    if case == 'empty': saved['lessons'] = []
    elif case == 'incomplete': saved['status'] = 'incomplete'
    elif case == 'errors': saved['errors'] = ['bad']
    elif case == 'timeout': saved['execution']['timed_out'] = True
    elif case == 'exit': saved['execution']['exit_code'] = 2
    elif case == 'partial': saved['summary']['requested'] = 2
    elif case == 'manifest': saved['runtime_manifest_sha256'] = '0' * 64
    elif case == 'generator': saved['generator_sha256'] = '0' * 64
    elif case == 'instance': saved['lessons'][0]['instance_sha256'] = '0' * 64
    elif case == 'bad_label':
        saved['lessons'][0]['instance']['test'][0]['output'] = [[True]]
        saved['lessons'][0]['instance_sha256'] = tool.digest(saved['lessons'][0]['instance'])
    elif case == 'duplicate':
        saved['lessons'] *= 2; saved['summary'].update(requested=2, materialized=2)
    elif case == 'band': saved['per_band'] = {}
    elif case == 'rotation_error': saved['lessons'][0]['rotations'] = [{'errors': ['bad']}]
    elif case == 'sampler_partial': saved['sampler']['per_band'] = 2
    elif case == 'rule': saved['rule_callable_sha256'] = '0' * 64
    with pytest.raises((ValueError, KeyError, TypeError)):
        tool.rescore_census(saved, bundle(tmp_path))


def test_rescore_retains_rival_errors_and_no_rivals_is_not_pass(saved, tmp_path):
    tool = load('rescore_worker', ROOT / 'shared/tools/lesson_census.py')
    assert hasattr(tool, 'rescore_census')
    current = bundle(tmp_path, broken=True)
    report = tool.rescore_census(saved, current)
    assert report['status'] == 'error'
    assert report['rival_summary']['CANONICAL_SHORTCUTS:broken']['rotations'] == {'error': 3}
    current.generator_module = SimpleNamespace(__file__=current.generator_module.__file__, TASK_ID='x', RULE_HASH='rulepin')
    with pytest.raises(ValueError, match='No rivals'):
        tool.rescore_census(saved, current)


def test_cli_exposes_existing_census_rescore_option():
    from arcpuzzles.cli import parser
    args = parser().parse_args(['lesson-census', 'x', '--rescore', 'old.json', '--out', 'new.json'])
    assert args.rescore == Path('old.json')


def test_public_rescore_runs_in_staged_subprocess_without_materialization(saved, library, tmp_path):
    from arcpuzzles import Catalog
    from arcpuzzles.lesson_census import lesson_census
    task = 'aaaa00000001'
    # A tiny independent runtime with deliberately forbidden materialization.
    current = bundle(tmp_path)
    (library / f'generators/{task}/generator.py').write_text(
        Path(current.generator_module.__file__).read_text().replace("TASK_ID = 'x'", f'TASK_ID = {task!r}'))
    runner = library / 'shared/runtime/puzzle_generators/runner.py'
    runner.parent.mkdir(parents=True)
    runner.write_text('from types import SimpleNamespace\nimport importlib\n'
                      'def _load_bundle(task):\n'
                      ' return SimpleNamespace(kind="per_puzzle", rule_source="rule", rule_callable_text="callable", rule_task_id=task, rule_file="canonical", generator_module=importlib.import_module(f"puzzle_generators.per_puzzle.{task}.generator"))\n'
                      'def run_one(*a, **k): raise AssertionError("must not generate")\n'
                      'def _open_bridge_with_rule(*a): raise AssertionError("must not execute Racket")\n')
    mapping_path = library / 'catalog/runtime_files.json'
    mappings = json.loads(mapping_path.read_text())
    for src, target in [('shared/tools/lesson_census.py', 'scripts/lesson_census.py'),
                        ('shared/runtime/reviewer_support.py', 'reviewer_support.py'),
                        ('shared/runtime/review_diagnostics.py', 'review_diagnostics.py')]:
        path = library / src; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / src).read_bytes())
        mappings.append({'path': src, 'target': target})
    mappings.append({'path': str(runner.relative_to(library)), 'target': 'puzzle_generators/runner.py'})
    mapping_path.write_text(json.dumps(mappings))
    saved['task_id'] = saved['rule_task_id'] = task
    saved['runtime_manifest']['task_id'] = task
    saved['runtime_manifest']['files'][0]['library_path'] = f'generators/{task}/generator.py'
    saved['runtime_manifest_sha256'] = sha((json.dumps(saved['runtime_manifest'], indent=2) + '\n').encode())
    instance = saved['lessons'][0]['instance']; instance['task_id'] = instance['rule_task_id'] = task
    tool = load('rescore_worker', ROOT / 'shared/tools/lesson_census.py')
    saved['lessons'][0]['instance_sha256'] = tool.digest(instance)
    path = tmp_path / 'saved.json'; path.write_text(json.dumps(saved))
    report = lesson_census(Catalog(library), task, rescore=path)
    assert report['status'] == 'ambiguous', report
    assert report['execution']['exit_code'] == 1
    assert report['input_census_sha256'] == sha(path.read_bytes())
    assert report['runtime_manifest']['task_id'] == task
    assert report['summary']['rotations'] == 3
    # Invalid evidence is returned as an error report by the same worker.
    saved['execution']['timed_out'] = True
    path.write_text(json.dumps(saved))
    report = lesson_census(Catalog(library), task, rescore=path)
    assert report['status'] == 'error' and report['execution']['exit_code'] == 2
    assert 'did not complete' in report['errors'][0]


def test_rescore_detects_source_changed_by_rival(saved, tmp_path):
    tool = load('rescore_worker', ROOT / 'shared/tools/lesson_census.py')
    current = bundle(tmp_path)
    def changes_source(grid):
        Path(current.generator_module.__file__).write_text('changed')
        return grid
    current.generator_module.SEMANTIC_RIVALS = {'mutator': changes_source}
    with pytest.raises(ValueError, match='source changed'):
        tool.rescore_census(saved, current)


@pytest.mark.parametrize('case', ['missing_pair', 'boolean_count', 'missing_rotation'])
def test_retained_sampler_shape_is_not_silently_shrunk(saved, tmp_path, case):
    tool = load('rescore_worker', ROOT / 'shared/tools/lesson_census.py')
    if case == 'missing_pair':
        saved['sampler']['n_demos'] = 3
    elif case == 'boolean_count':
        saved['summary']['materialized'] = True
    else:
        saved['sampler']['rotate_query'] = True
        saved['rotation_status'] = 'no_ambiguity_found'
    with pytest.raises(ValueError):
        tool.rescore_census(saved, bundle(tmp_path))

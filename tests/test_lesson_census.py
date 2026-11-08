"""Regression checks for reviewer census semantics and portable data access."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rival_survival_is_not_ambiguity():
    tool = load('census_worker', ROOT / 'shared/tools/lesson_census.py')
    lesson = {'train': [{'input': [[1]], 'output': [[1]]}],
              'test': [{'input': [[2]], 'output': [[2]]}]}
    rivals = {'same': lambda g: g, 'ambiguous': lambda g: [[1]],
              'refuted': lambda g: [[9]], 'broken': lambda g: 1 / 0}
    before = json.dumps(lesson)
    result = tool.score_lesson(SimpleNamespace(), rivals, lesson)
    assert result['rivals']['same'] == 'survived_all'
    assert result['rivals']['ambiguous'] == 'ambiguous'
    assert result['rivals']['refuted'] == 'refuted'
    assert result['rivals']['broken'] == 'error'
    assert result['ambiguous'] is True
    assert result['errors']
    assert json.dumps(lesson) == before


def test_query_rotation_finds_held_out_discriminator_without_mutation():
    tool = load('census_worker', ROOT / 'shared/tools/lesson_census.py')
    lesson = {'train': [{'input': [[1]], 'output': [[1]]},
                        {'input': [[2]], 'output': [[2]]}],
              'test': [{'input': [[3]], 'output': [[3]]}]}
    calls = []
    def rival(grid):
        calls.append(grid[0][0])
        if grid == [[1]]:
            grid[0][0] = 9
        return grid
    before = json.dumps(lesson)
    cache = {}
    assert not tool.score_lesson(SimpleNamespace(), {'wrong': rival}, lesson,
                                 prediction_cache=cache)['ambiguous']
    rotations = tool.score_rotations(SimpleNamespace(), {'wrong': rival}, lesson,
                                     prediction_cache=cache)
    assert [r['ambiguous'] for r in rotations] == [True, False, False]
    assert rotations[0]['query_index'] == 0
    assert rotations[0]['train_indices'] == [1, 2]
    assert rotations[0]['rivals'] == {'wrong': 'ambiguous'}
    assert sorted(calls) == [1, 2, 3]
    assert json.dumps(lesson) == before


def test_rotation_keeps_survival_hook_warnings_and_rival_errors():
    tool = load('census_worker', ROOT / 'shared/tools/lesson_census.py')
    lesson = {'train': [{'input': [[1]], 'output': [[1]]}],
              'test': [{'input': [[2]], 'output': [[2]]}]}
    gen = SimpleNamespace(lesson_identifiable=lambda d, q: ['weak'])
    rotations = tool.score_rotations(gen, {'same': lambda g: g, 'broken': lambda g: 1 / 0}, lesson)
    assert all(not r['ambiguous'] and r['rivals']['same'] == 'survived_all' for r in rotations)
    assert all(r['warnings'] == ['weak'] and r['errors'] for r in rotations)


def test_rotation_rejects_multiple_queries_before_staging(library, monkeypatch):
    from arcpuzzles import Catalog
    import arcpuzzles.lesson_census as controller
    monkeypatch.setattr(controller, 'prepare_runtime', lambda *a: pytest.fail('must validate before staging'))
    with pytest.raises(ValueError, match='one query'):
        controller.lesson_census(Catalog(library), 'aaaa00000001', n_queries=2, rotate_query=True)


def test_dynamic_declarations_keep_colliding_names():
    tool = load('census_worker', ROOT / 'shared/tools/lesson_census.py')
    fn = lambda g: g
    rivals, errors = tool.declared_rivals(SimpleNamespace(
        LESSON_COMPETITORS={'a': fn}, SEMANTIC_RIVALS={'a': fn}, CANONICAL_SHORTCUTS={'bad': 4}))
    assert set(rivals) == {'LESSON_COMPETITORS:a', 'SEMANTIC_RIVALS:a'}
    assert errors


def test_hook_warning_and_missing_contract_are_not_proof():
    tool = load('census_worker', ROOT / 'shared/tools/lesson_census.py')
    lesson = {'train': [{'input': [[1]], 'output': [[1]]}], 'test': [{'input': [[2]], 'output': [[2]]}]}
    result = tool.score_lesson(SimpleNamespace(lesson_identifiable=lambda d, q: ['weak']), {}, lesson)
    assert result['warnings'] == ['weak']
    assert result['ambiguous'] is False
    assert result['contract'] == 'hook_only'
    assert tool.score_lesson(SimpleNamespace(), {}, lesson)['contract'] == 'none'


def test_portable_root_and_canonical_shapes(tmp_path):
    helper = load('reviewer_support', ROOT / 'shared/runtime/reviewer_support.py')
    data = tmp_path / 'data/canonical/puzzles.jsonl'
    data.parent.mkdir(parents=True)
    data.write_text(json.dumps({'task_id': 'x', 'train': [{'input': ['01'], 'output': [[1, 0]]}],
                                'test': {'input': [[2]], 'output': ['3']}}) + '\n')
    nested = tmp_path / 'tests/x/test_task.py'
    nested.parent.mkdir(parents=True)
    nested.touch()
    assert helper.find_root(nested) == tmp_path
    assert helper.canonical_pairs('x', root=tmp_path)[0]['input'] == [[0, 1]]
    assert len(helper.canonical_pairs('x', root=tmp_path)) == 2
    with pytest.raises(KeyError):
        helper.canonical_pairs('missing', root=tmp_path)
    data.write_text(json.dumps({'task_id': 'x', 'train': [{'input': [[1]], 'output': None}]}) + '\n')
    with pytest.raises(ValueError):
        helper.canonical_pairs('x', root=tmp_path)


def test_canonical_labeled_only_preserves_pair_identity_and_strict_default(tmp_path):
    helper = load('reviewer_support', ROOT / 'shared/runtime/reviewer_support.py')
    data = tmp_path / 'data/canonical/puzzles.jsonl'
    data.parent.mkdir(parents=True)
    data.write_text('\n'.join(json.dumps(row) for row in [
        {'task_id': 'x', 'train': {'input': ['1'], 'output': ['2']},
         'test': [{'input': [[3]]}, {'input': [[4]], 'output': [[5]]}]},
        {'task_id': 'x', 'test': {'input': [[6]], 'output': [[7]]}},
    ]) + '\n')
    with pytest.raises(ValueError):
        helper.canonical_pairs('x', root=tmp_path)
    pairs = helper.canonical_pairs('x', root=tmp_path, labeled_only=True)
    assert [(p['variant'], p['split'], p['pair_index']) for p in pairs] == [
        (0, 'train', 0), (0, 'test', 1), (1, 'test', 0)]
    assert pairs[0]['output'] == [[2]]
    assert helper.canonical_pairs('x', root=tmp_path, variant=1, labeled_only=True) == pairs[-1:]


@pytest.mark.parametrize('split,pair', [
    ('train', {'input': [[1]]}),
    ('test', {'input': []}),
    ('test', {'input': [[1]], 'output': None}),
    ('test', {'input': [[1]], 'output': []}),
    ('test', {'input': [[1]], 'output': [[1], [2, 3]]}),
])
def test_canonical_labeled_only_still_rejects_malformed_pairs(tmp_path, split, pair):
    helper = load('reviewer_support', ROOT / 'shared/runtime/reviewer_support.py')
    data = tmp_path / 'data/canonical/puzzles.jsonl'
    data.parent.mkdir(parents=True)
    data.write_text(json.dumps({'task_id': 'x', split: [pair]}) + '\n')
    with pytest.raises(ValueError):
        helper.canonical_pairs('x', root=tmp_path, labeled_only=True)


@pytest.mark.parametrize('case', ['unlabeled_query', 'zero_labels', 'malformed_output'])
def test_census_canonical_fit_uses_only_available_labels(tmp_path, monkeypatch, case):
    import sys
    tool = load('census_worker', ROOT / 'shared/tools/lesson_census.py')
    helper = load('reviewer_support', ROOT / 'shared/runtime/reviewer_support.py')
    data = tmp_path / 'data/canonical/puzzles.jsonl'
    data.parent.mkdir(parents=True)
    canonical = {'task_id': 'x', 'test': [{'input': [[2]]}]}
    if case != 'zero_labels':
        canonical['train'] = [{'input': [[1]], 'output': [[1]]}]
    if case == 'malformed_output':
        canonical['test'][0]['output'] = None
    data.write_text(json.dumps(canonical) + '\n')
    gen = SimpleNamespace(__file__=__file__, LESSON_COMPETITORS={'identity': lambda g: g})
    bundle = SimpleNamespace(kind='per_puzzle', generator_module=gen, rule_source='rule',
                             rule_callable_text='callable', rule_task_id='x', rule_file='canonical')
    runner = SimpleNamespace(_load_bundle=lambda task: bundle,
                             _open_bridge_with_rule=lambda rule: (SimpleNamespace(shutdown=lambda: None), 'fn'),
                             run_one=lambda *a, **k: {'train': [{'input': [[1]], 'output': [[1]]}],
                                                      'test': [{'input': [[2]], 'output': [[2]]}]})
    monkeypatch.setitem(sys.modules, 'puzzle_generators', SimpleNamespace(runner=runner))
    monkeypatch.setattr(tool, '__file__', str(tmp_path / 'scripts/lesson_census.py'))
    monkeypatch.setattr(tool, '_support', lambda: helper)
    report = tool.census({'task_id': 'x', 'n_demos': 1, 'n_queries': 1, 'period': 1,
                          'per_band': 1, 'bands': ['easy']})
    if case == 'unlabeled_query':
        assert report['status'] == 'no_ambiguity_found'
        assert report['canonical_pairs'] == 1
        assert report['canonical_rival_fit']['LESSON_COMPETITORS:identity']['status'] == 'fits_all'
    else:
        assert report['status'] == 'error'
        assert report['canonical_rival_fit'] == {}
        assert report['canonical_read_error'].startswith('ValueError:')
        if case == 'zero_labels':
            assert 'No labeled canonical pairs' in report['canonical_read_error']


def test_multiple_queries_and_invalid_grid_are_not_silent():
    tool = load('census_worker', ROOT / 'shared/tools/lesson_census.py')
    lesson = {'train': [{'input': [[1]], 'output': [[1]]}],
              'test': [{'input': [[1]], 'output': [[1]]}, {'input': [[2]], 'output': [[2]]}]}
    result = tool.score_lesson(SimpleNamespace(), {'constant': lambda g: [[1]], 'invalid': lambda g: None}, lesson)
    assert result['rivals'] == {'constant': 'ambiguous', 'invalid': 'error'}


def test_controller_timeout_retains_source_and_error(library, monkeypatch):
    from arcpuzzles import Catalog
    import arcpuzzles.lesson_census as controller
    monkeypatch.setattr(controller, 'run_process', lambda *a, **k: {
        'exit_code': -15, 'timed_out': True, 'stdout': '', 'stderr': 'timed out'})
    result = controller.lesson_census(Catalog(library), 'aaaa00000001', per_band=1)
    assert result['status'] == 'error'
    assert result['errors']
    assert result['runtime_manifest']['files']
    assert len(result['runtime_manifest_sha256']) == 64


def test_census_cli_exists():
    from arcpuzzles.cli import parser
    args = parser().parse_args(['lesson-census', 'ebff81ea3252', '--period', '7', '--rotate-query', '--out', 'x.json'])
    assert args.period == 7
    assert args.rotate_query


def test_runtime_helper_survives_relocation(tmp_path):
    import shutil
    import subprocess
    import sys
    runtime = tmp_path / 'runtime'
    (runtime / 'data/canonical').mkdir(parents=True)
    shutil.copy2(ROOT / 'shared/runtime/reviewer_support.py', runtime / 'reviewer_support.py')
    (runtime / 'data/canonical/puzzles.jsonl').write_text(json.dumps({
        'task_id': 'x', 'train': [{'input': ['01'], 'output': ['10']}]}) + '\n')
    (runtime / 'probe.py').write_text('from reviewer_support import canonical_pairs, find_root\n'
                                    'assert canonical_pairs("x", root=find_root(__file__))[0]["output"] == [[1,0]]\n')
    moved = tmp_path / 'moved'
    runtime.rename(moved)
    subprocess.run([sys.executable, '-E', '-s', str(moved / 'probe.py')], cwd=tmp_path,
                   check=True, capture_output=True)


def test_timeout_preserves_checkpoint_instances(library, monkeypatch):
    from arcpuzzles import Catalog
    import arcpuzzles.lesson_census as controller
    def interrupted(command, stage, **kwargs):
        (stage / 'report.json').write_text(json.dumps({'task_id': 'aaaa00000001', 'status': 'incomplete',
            'lessons': [{'instance_sha256': 'kept', 'instance': {'train': [], 'test': []}}], 'errors': []}))
        return {'exit_code': -15, 'timed_out': True, 'stdout': '', 'stderr': ''}
    monkeypatch.setattr(controller, 'run_process', interrupted)
    result = controller.lesson_census(Catalog(library), 'aaaa00000001', per_band=1)
    assert result['status'] == 'error'
    assert result['lessons'][0]['instance_sha256'] == 'kept'
    assert 'partial' in result['errors'][-1]


@pytest.mark.parametrize(('rotate', 'wrong', 'policy'), [
    (False, False, 'require'), (True, False, 'require'),
    (True, True, 'require'), (True, True, 'diagnostic')])
def test_worker_checkpoints_and_canonical_fit(monkeypatch, rotate, wrong, policy):
    import sys
    tool = load('census_worker', ROOT / 'shared/tools/lesson_census.py')
    gen = SimpleNamespace(__file__=__file__, EXAMPLES_NEEDED=1,
                          LESSON_COMPETITORS={'identity': lambda g: [[9]] if wrong and g == [[1]] else g})
    bundle = SimpleNamespace(kind='per_puzzle', generator_module=gen, rule_source='rule',
                             rule_callable_text='callable', rule_task_id='x', rule_file='canonical')
    runner = SimpleNamespace(_load_bundle=lambda task: bundle,
                             _open_bridge_with_rule=lambda rule: (SimpleNamespace(shutdown=lambda: None), 'fn'),
                             run_one=lambda *a, **k: {'sampling': {'accepted_pairs': [
                                 {'split': 'train', 'sample_index': 4}, {'split': 'test', 'sample_index': 7}]},
                                                      'train': [{'input': [[1]], 'output': [[1]]}],
                                                      'test': [{'input': [[2]], 'output': [[2]]}]})
    helper = load('reviewer_support', ROOT / 'shared/runtime/reviewer_support.py')
    helper.canonical_pairs = lambda *a, **k: [{'input': [[1]], 'output': [[1]], 'variant': 0, 'split': 'train', 'pair_index': 0}]
    monkeypatch.setitem(sys.modules, 'puzzle_generators', SimpleNamespace(runner=runner))
    monkeypatch.setattr(tool, '_support', lambda: helper)
    snapshots = []
    report = tool.census({'task_id': 'x', 'n_demos': 1, 'n_queries': 1, 'period': 2,
                          'per_band': 2, 'bands': ['easy'], 'rotate_query': rotate,
                          'rotation_policy': policy},
                         checkpoint=lambda r: snapshots.append(json.loads(json.dumps(r))))
    assert [len(s['lessons']) for s in snapshots] == [0, 1, 2]
    assert all(s['status'] == 'incomplete' for s in snapshots)
    assert report['canonical_rival_fit']['LESSON_COMPETITORS:identity']['status'] == ('refuted' if wrong else 'fits_all')
    assert report['status'] == ('ambiguous' if wrong and policy == 'require' else 'no_ambiguity_found')
    assert report['production_status'] == 'no_ambiguity_found'
    assert report['rotation_status'] == ('not_requested' if not rotate else
                                        'ambiguous' if wrong else 'no_ambiguity_found')
    assert report['summary']['materialized'] == 2
    assert report['summary']['pairs'] == 4
    assert report['summary']['rotations'] == (4 if rotate else 0)
    assert report['summary']['ambiguous_rotations'] == (2 if wrong else 0)
    assert report['summary']['ambiguous'] == 0  # production queries still pass
    assert report['per_band']['easy']['start_residues'] == {'0': 1, '1': 1}
    assert report['per_band']['easy']['accepted_pair_residues'] == {
        'train': {'0': 2, '1': 0}, 'test': {'0': 0, '1': 2}}
    assert report['per_band']['easy']['accepted_indices_recorded'] == 4
    assert all(0 <= r['seed'] < 2**32 for r in report['lessons'])


def test_rotation_policy_cli_and_controller_validate_before_staging(library, monkeypatch):
    from arcpuzzles import Catalog
    from arcpuzzles.cli import parser
    import arcpuzzles.lesson_census as controller
    args = parser().parse_args(['lesson-census', 'x', '--rotate-query',
                                '--rotation-policy', 'diagnostic', '--out', 'x.json'])
    assert args.rotation_policy == 'diagnostic'
    monkeypatch.setattr(controller, 'prepare_runtime', lambda *a: pytest.fail('must validate before staging'))
    with pytest.raises(ValueError, match='rotation_policy'):
        controller.lesson_census(Catalog(library), 'aaaa00000001', rotation_policy='ignore')


@pytest.mark.parametrize('status,exit_code', [('running', 1), ('incomplete', 0),
                                               ('no_declared_ambiguity', 2), ('ambiguous', 0)])
def test_checkpoint_and_exit_must_agree(library, monkeypatch, status, exit_code):
    from arcpuzzles import Catalog
    import arcpuzzles.lesson_census as controller
    def stopped(command, stage, **kwargs):
        (stage / 'report.json').write_text(json.dumps({'task_id': 'aaaa00000001', 'status': status,
                                                      'lessons': [{'instance_sha256': 'kept'}], 'errors': []}))
        return {'exit_code': exit_code, 'timed_out': False, 'stdout': '', 'stderr': ''}
    monkeypatch.setattr(controller, 'run_process', stopped)
    result = controller.lesson_census(Catalog(library), 'aaaa00000001', per_band=1)
    assert result['status'] == 'error'
    assert result['lessons'][0]['instance_sha256'] == 'kept'
    assert result['errors']


@pytest.fixture
def schedule_worker(monkeypatch, tmp_path, request):
    """Use production sampling; replace only Racket IPC and canonical I/O."""
    import importlib
    monkeypatch.syspath_prepend(str(ROOT / 'shared/runtime'))
    runner = importlib.import_module('puzzle_generators.runner')
    tool = load('schedule_census_worker', ROOT / 'shared/tools/lesson_census.py')
    gen = SimpleNamespace(__file__=__file__, EXAMPLES_NEEDED=1, LESSON_SCHEDULE_PERIOD=7,
        generate=lambda seed, sample_index, **axes: [[sample_index % 7 + 1, 0], [0, 0]],
        LESSON_COMPETITORS={'rare': lambda g: [[9, 0], [0, 0]] if g[0][0] == 7 else g})
    bundle = SimpleNamespace(kind='per_puzzle', generator_module=gen, rule_source='rule',
        rule_callable_text='(lambda (g) g)', rule_task_id='x', rule_file='canonical', allow_identity_output=True)
    monkeypatch.setattr(runner, '_load_bundle', lambda task: bundle)
    if getattr(request, 'param', None) != 'racket':
        monkeypatch.setattr(runner, '_open_bridge_with_rule', lambda rule: (SimpleNamespace(shutdown=lambda: None), 'fn'))
        monkeypatch.setattr(runner, '_apply_rule', lambda bridge, fn, grid: grid)
    monkeypatch.setattr(runner, 'REJECT_DIR', tmp_path)
    helper = load('schedule_support', ROOT / 'shared/runtime/reviewer_support.py')
    helper.canonical_pairs = lambda *a, **k: [{'input': [[1, 0], [0, 0]], 'output': [[1, 0], [0, 0]],
                                              'variant': 0, 'split': 'train', 'pair_index': 0}]
    monkeypatch.setattr(tool, '_support', lambda: helper)
    request = {'task_id': 'x', 'n_demos': 1, 'n_queries': 1, 'period': 2,
               'per_band': 2, 'bands': ['easy', 'hard']}
    return tool, gen, request


def test_schedule_enumeration_finds_rare_residue_missed_by_smoke(schedule_worker):
    tool, gen, request = schedule_worker
    smoke = tool.census(request)
    assert smoke['status'] == 'no_ambiguity_found'
    assert smoke['summary']['materialized'] == 4
    snapshots = []
    report = tool.census({**request, 'enumerate_schedule_period': True, 'schedule_seed': 31},
                         checkpoint=lambda r: snapshots.append(json.loads(json.dumps(r))))
    assert report['status'] == report['production_status'] == report['rotation_status'] == 'ambiguous'
    assert report['summary']['materialized'] == 14
    assert report['summary']['rotations'] == 28
    assert report['summary']['ambiguous'] == 2
    assert report['summary']['ambiguous_rotations'] == 4
    assert report['schedule_coverage']['status'] == 'complete_fixed_seed'
    assert report['schedule_coverage']['period'] == 7
    assert report['sampler']['period'] == 2  # reporting modulus remains independent
    for band in request['bands']:
        rows = [r for r in report['lessons'] if r['band'] == band]
        assert [r['sample_index'] for r in rows] == list(range(7))
        assert {r['seed'] for r in rows} == {31}
        assert all([x['query_index'] for x in r['rotations']] == [0, 1] for r in rows)
        assert all(r['instance']['sampling']['requested_start'] == r['sample_index'] for r in rows)
    assert all(r['status'] == 'incomplete' and r['schedule_coverage']['status'] == 'incomplete'
               for r in snapshots)


@pytest.mark.parametrize('period', [None, 0, -1, True, 1.5, '7', {'easy': 7}])
def test_schedule_enumeration_requires_explicit_positive_period(schedule_worker, period):
    tool, gen, request = schedule_worker
    gen.LESSON_SCHEDULE_PERIOD = period
    with pytest.raises(ValueError, match='LESSON_SCHEDULE_PERIOD'):
        tool.census({**request, 'enumerate_schedule_period': True})


def test_schedule_partial_materialization_is_not_complete(schedule_worker):
    tool, gen, request = schedule_worker
    gen.generate = lambda **kwargs: (_ for _ in ()).throw(ValueError('broken draw'))
    report = tool.census({**request, 'enumerate_schedule_period': True})
    assert report['status'] == 'error'
    assert report['schedule_coverage']['status'] == 'incomplete'
    assert report['summary']['materialized'] == 0


def test_schedule_cli_and_early_validation(library, monkeypatch):
    from arcpuzzles.cli import parser
    from arcpuzzles import Catalog
    import arcpuzzles.lesson_census as controller
    args = parser().parse_args(['lesson-census', 'x', '--enumerate-schedule-period',
                                '--schedule-seed', '31', '--out', 'x.json'])
    assert args.enumerate_schedule_period and args.schedule_seed == 31
    monkeypatch.setattr(controller, 'prepare_runtime', lambda *a: pytest.fail('must reject before staging'))
    for kwargs in ({'n_queries': 2}, {'schedule_seed': True}, {'rescore': 'missing.json'}):
        with pytest.raises(ValueError):
            controller.lesson_census(Catalog(library), 'aaaa00000001', enumerate_schedule_period=True, **kwargs)


@pytest.mark.parametrize('policy,expected', [('require', 'warning'), ('diagnostic', 'no_ambiguity_found')])
def test_schedule_preserves_ordered_only_policy(schedule_worker, policy, expected):
    tool, gen, request = schedule_worker
    gen.LESSON_COMPETITORS = {'identity': lambda g: g}
    gen.lesson_identifiable = lambda demos, query: ['ordered curriculum'] if (
        demos[0]['input'][0][0] == 2 and query['input'][0][0] == 1) else []
    result = tool.census({**request, 'enumerate_schedule_period': True, 'rotation_policy': policy})
    assert result['production_status'] == 'no_ambiguity_found'
    assert result['rotation_status'] == 'warning'
    assert result['status'] == expected


def test_retained_schedule_cannot_claim_different_seed_or_partial_coverage(schedule_worker):
    import hashlib
    tool, gen, request = schedule_worker
    result = tool.census({**request, 'enumerate_schedule_period': True})
    result['execution'] = {'exit_code': 1, 'timed_out': False}
    manifest = {'task_id': 'x', 'files': [{'library_path': 'generators/x/generator.py',
                                        'sha256': result['generator_sha256']}]}
    result['runtime_manifest'] = manifest
    result['runtime_manifest_sha256'] = hashlib.sha256((json.dumps(manifest, indent=2) + '\n').encode()).hexdigest()
    assert tool.validate_retained_census(result) == 'x'
    for mutation in ('seed', 'coverage', 'rotation', 'start'):
        bad = json.loads(json.dumps(result))
        if mutation == 'seed': bad['lessons'][0]['seed'] = 91
        elif mutation == 'coverage': bad['schedule_coverage']['status'] = 'incomplete'
        elif mutation == 'rotation': bad['lessons'][0]['rotations'][0]['query_index'] = 1
        else: bad['lessons'][0]['sample_index'] = 91
        with pytest.raises(ValueError, match='schedule|Schedule'):
            tool.validate_retained_census(bad)


def complete_schedule_receipt(schedule_worker, namespace='LESSON_COMPETITORS'):
    """A completed native-worker receipt with cheap deterministic IPC fixtures."""
    import hashlib
    tool, gen, request = schedule_worker
    gen.LESSON_COMPETITORS = {}
    setattr(gen, namespace, {'same': lambda g: g})
    gen.RULE_HASH = 'bound-rule'
    report = tool.census({**request, 'enumerate_schedule_period': True, 'schedule_seed': 31})
    report['execution'] = {'exit_code': 0, 'timed_out': False}
    manifest = {'task_id': 'x', 'files': [{'library_path': 'generators/x/generator.py',
                                       'sha256': report['generator_sha256']}]}
    report['runtime_manifest'] = manifest
    report['runtime_manifest_sha256'] = hashlib.sha256((json.dumps(manifest, indent=2) + '\n').encode()).hexdigest()
    binding = {k: report[k] for k in ('generator_sha256', 'rule_source_sha256',
               'rule_callable_sha256', 'rule_task_id', 'rule_file', 'declared_rule_hash')}
    binding['rivals'] = report['rivals']
    options = dict(task_id='x', binding=binding, period=7, seed=31,
                   bands=['easy', 'hard'], n_demos=1)
    return tool, report, options


def test_schedule_receipt_accepts_only_the_bound_fixed_population(schedule_worker):
    tool, report, options = complete_schedule_receipt(schedule_worker)
    original = json.dumps(report)
    assert tool.validate_schedule_receipt(report, **options) == 'x'
    assert json.dumps(report) == original


@pytest.mark.parametrize('damage', ['generator', 'rule', 'callable', 'task', 'period', 'seed',
    'bands', 'demos', 'partial', 'rotation_error', 'rotation_ambiguous', 'diagnostic',
    'missing_enumeration', 'boolean_seed', 'false_topline', 'rival_subset'])
def test_schedule_receipt_rejects_stale_partial_or_failed_evidence(schedule_worker, damage):
    tool, report, options = complete_schedule_receipt(schedule_worker)
    if damage in ('generator', 'rule', 'callable'):
        key = {'generator': 'generator_sha256', 'rule': 'rule_source_sha256',
               'callable': 'rule_callable_sha256'}[damage]
        options['binding'][key] = '0' * 64
    elif damage in ('task', 'period', 'seed', 'bands', 'demos'):
        key = {'task': 'task_id', 'demos': 'n_demos'}.get(damage, damage)
        options[key] = {'task': 'y', 'period': 8, 'seed': 32, 'bands': ['easy'], 'demos': 2}[damage]
    elif damage == 'partial': report['summary']['materialized'] -= 1
    elif damage == 'rotation_error': report['lessons'][0]['rotations'][0]['errors'] = ['failed']
    elif damage == 'rotation_ambiguous': report['lessons'][0]['rotations'][0]['ambiguous'] = True
    elif damage == 'diagnostic': report['rotation_policy'] = report['sampler']['rotation_policy'] = 'diagnostic'
    elif damage == 'missing_enumeration': report['sampler']['enumerate_schedule_period'] = False
    elif damage == 'boolean_seed': options['seed'] = True
    elif damage == 'rival_subset': options['binding']['rivals'] = ['different:required']
    else: report['lessons'][0]['rivals']['LESSON_COMPETITORS:same'] = 'ambiguous'
    with pytest.raises((ValueError, KeyError, TypeError)):
        tool.validate_schedule_receipt(report, **options)


@pytest.mark.parametrize('schedule_worker', ['racket'], indirect=True)
def test_schedule_uses_real_racket_labels(schedule_worker):
    import shutil
    if shutil.which('racket') is None:
        pytest.skip('Racket is not installed')
    tool, gen, request = schedule_worker
    result = tool.census({**request, 'bands': ['easy'], 'enumerate_schedule_period': True, 'schedule_seed': 41})
    assert result['status'] == 'ambiguous'
    assert result['schedule_coverage']['status'] == 'complete_fixed_seed'
    assert result['summary']['materialized'] == 7
    assert result['summary']['rotations'] == 14
    assert result['summary']['materialization_errors'] == 0
    assert all(p['input'] == p['output'] for r in result['lessons']
               for p in r['instance']['train'] + r['instance']['test'])


def test_schedule_authority_error_does_not_claim_completed_coverage(schedule_worker):
    tool, gen, request = schedule_worker
    tool._support().canonical_pairs = lambda *a, **k: []
    result = tool.census({**request, 'enumerate_schedule_period': True})
    assert result['status'] == 'error'
    assert result['schedule_coverage']['status'] == 'incomplete'


def test_schedule_controller_interruption_revokes_completion(library, monkeypatch):
    from arcpuzzles import Catalog
    import arcpuzzles.lesson_census as controller
    def interrupted(command, stage, **kwargs):
        (stage / 'report.json').write_text(json.dumps({'task_id': 'aaaa00000001',
            'status': 'no_ambiguity_found', 'schedule_coverage': {'status': 'complete_fixed_seed'}, 'errors': []}))
        return {'exit_code': -15, 'timed_out': True, 'stdout': '', 'stderr': ''}
    monkeypatch.setattr(controller, 'run_process', interrupted)
    result = controller.lesson_census(Catalog(library), 'aaaa00000001', enumerate_schedule_period=True)
    assert result['status'] == 'error'
    assert result['schedule_coverage']['status'] == 'incomplete'


def test_schedule_rejections_preserve_actual_accepted_indices(schedule_worker):
    tool, gen, request = schedule_worker
    generate = gen.generate
    def rejecting(seed, sample_index, **axes):
        if sample_index % 7 == 2:
            raise ValueError('deliberately unavailable residue')
        return generate(seed, sample_index, **axes)
    gen.generate = rejecting
    result = tool.census({**request, 'enumerate_schedule_period': True})
    lesson = next(r for r in result['lessons'] if r['band'] == 'easy' and r['sample_index'] == 2)
    assert result['schedule_coverage']['status'] == 'complete_fixed_seed'
    assert lesson['instance']['sampling']['requested_start'] == 2
    assert [r['sample_index'] for r in lesson['instance']['sampling']['accepted_pairs']] == [3, 4]
    assert lesson['instance']['sampling']['rejections'][0]['sample_index'] == 2


def test_schedule_missing_contract_has_no_sampled_fallback(schedule_worker):
    tool, gen, request = schedule_worker
    del gen.LESSON_SCHEDULE_PERIOD
    assert tool.census(request)['status'] == 'no_ambiguity_found'
    with pytest.raises(ValueError, match='LESSON_SCHEDULE_PERIOD'):
        tool.census({**request, 'enumerate_schedule_period': True})

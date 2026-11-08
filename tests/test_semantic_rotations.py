"""A unique discriminator must remain visible when a query is exchanged."""
import importlib.util
import json
from pathlib import Path
from types import ModuleType
import sys

import pytest
from test_lesson_census import schedule_worker, complete_schedule_receipt

ROOT = Path(__file__).resolve().parents[1]


def gate(monkeypatch):
    package = ModuleType('scripts'); package.__path__ = []
    profile = ModuleType('scripts.canonical_profile_gate')
    profile.BANDS = ('easy', 'medium', 'hard')
    profile._pinned_seed = lambda *args: 1
    profile.canonical_inputs = lambda *args: []
    profile.canonical_pairs = lambda *args: []
    verifier = ModuleType('scripts.coder_synth_verify'); verifier._grids_equal = lambda a, b: a == b
    for name, value in [('scripts', package), ('scripts.canonical_profile_gate', profile),
                        ('scripts.coder_synth_verify', verifier)]:
        monkeypatch.setitem(sys.modules, name, value)
    spec = importlib.util.spec_from_file_location('rotation_gate_fixture', ROOT / 'shared/tools/generator_semantic_gate.py')
    tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)
    pair = lambda value: {'input': [[value]], 'output': [[value]]}
    lesson = {'index': 0, 'seed': 1, 'sample_index': 0, 'band': 'easy', 'replay': 'fixture',
              'demos': [pair(1), pair(2)], 'query': pair(3)}
    monkeypatch.setattr(tool, 'materialize_lessons', lambda *a, **k: ([lesson], []))
    return tool, lesson


@pytest.mark.parametrize('stale', [False, True])
@pytest.mark.parametrize('storage', ['json', 'gzip', 'manifest'])
def test_schedule_receipt_cannot_launder_a_missing_contract(schedule_worker, monkeypatch, tmp_path, stale, storage):
    _, report, _ = complete_schedule_receipt(schedule_worker, namespace='SEMANTIC_RIVALS')
    _, gen, _ = schedule_worker
    tool, _ = gate(monkeypatch)
    monkeypatch.setattr(tool, 'BANDS', ('easy', 'hard'))
    original_import = tool.importlib.import_module
    monkeypatch.setattr(tool.importlib, 'import_module',
        lambda name, *a, **k: gen if name == 'puzzle_generators.per_puzzle.x.generator'
        else original_import(name, *a, **k))
    if stale:
        report['rule_callable_sha256'] = '0' * 64
    path = tmp_path / 'census.json'
    path.write_text(json.dumps(report))
    if storage != 'json':
        from test_check_schedule_receipt import compressed_receipt
        packed, manifest, _ = compressed_receipt(tmp_path, path.read_bytes())
        path = packed if storage == 'gzip' else manifest
    audit = tool.audit_task('x', schedule_census=path, schedule_seed=31)
    if stale:
        assert audit['status'] == 'FAIL'
        assert audit['errors'] and audit['schedule_coverage']['receipt_status'] == 'rejected'
        assert audit['schedule_coverage']['status'] == 'declared_period_not_enumerated'
    else:
        assert audit['status'] == 'NO_CONTRACT'
        assert audit['schedule_coverage']['status'] == 'complete_fixed_seed_reported'
        assert not any('declared_period_not_enumerated' in w for w in audit['warnings'])
        if storage != 'json':
            assert audit['schedule_coverage']['receipt_transport']['format'] == 'arcpuzzles-evidence-gzip-v1'


@pytest.mark.parametrize('required', [False, True])
def test_rotation_smoke_finds_unique_witness_without_materializing_again(monkeypatch, required):
    tool, lesson = gate(monkeypatch)
    calls = []
    def rival(grid):
        calls.append(grid[0][0])
        return [[9]] if grid == [[1]] else grid
    stats, errors, warnings = tool.score_lessons('fixture', lambda d, q: [], count=1, n_demos=2,
        competitors={'wrong': rival}, rotate_query=True, require_rotations=required)
    assert stats['unidentifiable'] == 0
    assert stats['rotations']['checked'] == 3
    assert stats['rotations']['ambiguous'] == 1
    assert stats['rotations']['status'] == 'ambiguous'
    assert stats['rotations']['examples'][0]['query_index'] == 0
    assert stats['rotations']['examples'][0]['rivals']['wrong'] == 'ambiguous'
    assert stats['rotations']['examples'][0]['instance']['train'] == lesson['demos']
    assert stats['rotations']['examples'][0]['refuting_pair_indices']['wrong'] == [0]
    assert stats['rotations']['examples'][0]['query_predictions']['wrong'] == [[9]]
    assert len(calls) <= 6  # three production calls plus one cached prediction per pair
    assert bool(errors) is required


def test_answer_equivalent_rival_is_not_a_rotation_failure(monkeypatch):
    tool, _ = gate(monkeypatch)
    stats, errors, warnings = tool.score_lessons('fixture', lambda d, q: [], count=1, n_demos=2,
        competitors={'same': lambda grid: grid}, rotate_query=True, require_rotations=True)
    assert stats['rotations']['ambiguous'] == 0
    assert stats['rotations']['status'] == 'no_ambiguity_found'
    assert not errors and not warnings


def test_rotation_errors_are_retained_and_required_errors_block(monkeypatch):
    tool, _ = gate(monkeypatch)
    stats, errors, _ = tool.score_lessons('fixture', lambda d, q: [], count=1, n_demos=2,
        competitors={'broken': lambda grid: 1 / 0}, rotate_query=True, require_rotations=True)
    assert stats['rotations']['status'] == 'error'
    assert stats['rotations']['errors'] == 3
    assert errors


@pytest.mark.parametrize('declared, expected, warned', [
    (1, 1, False), (6, 6, False), (32, 32, False),
    (None, 3, False), (True, 3, True), (0, 3, True), (-1, 3, True),
    (1.5, 3, True), ('2', 3, True), (33, 3, True),
])
def test_declared_demo_count_scores_actual_shape(monkeypatch, declared, expected, warned):
    tool, _ = gate(monkeypatch)
    gen = ModuleType('demo_count_fixture')
    if declared is not None:
        gen.EXAMPLES_NEEDED = declared
    gen.generate = lambda seed, difficulty=None: None
    # Each rich demonstration refutes both wrong rules, even when there is only one.
    gen.LESSON_COMPETITORS = {
        'erase_one': lambda g: [[0 if c == 1 else c for c in row] for row in g],
        'erase_two': lambda g: [[0 if c == 2 else c for c in row] for row in g],
    }
    monkeypatch.setitem(sys.modules, 'puzzle_generators.per_puzzle.fixture.generator', gen)
    def materialize(task, count, *, n_demos, **kwargs):
        pair = lambda v: {'input': [[v, 3 - v]], 'output': [[v, 3 - v]]}
        return [{'index': 0, 'seed': 1, 'sample_index': 0, 'band': 'easy', 'replay': 'fixture',
                 'demos': [pair(1) for _ in range(n_demos)], 'query': pair(2)}], []
    monkeypatch.setattr(tool, 'materialize_lessons', materialize)
    result = tool.audit_task('fixture', lessons=1, require_rotations=True)
    assert result['lessons']['n_demos'] == expected
    assert result['lessons']['identifiable'] == 1
    assert result['lessons']['rotations']['checked'] == expected + 1
    assert result['lessons']['rotations']['ambiguous'] == 0
    assert not result['errors']
    assert any('EXAMPLES_NEEDED' in w for w in result['warnings']) is warned


def test_required_rotations_cannot_pass_without_lesson_contract(monkeypatch):
    tool, _ = gate(monkeypatch)
    monkeypatch.setitem(sys.modules, 'puzzle_generators.per_puzzle.fixture.generator', ModuleType('empty'))
    assert tool.audit_task('fixture')['status'] == 'NO_CONTRACT'
    result = tool.audit_task('fixture', require_rotations=True)
    assert result['status'] == 'FAIL'
    assert any('rotation' in e for e in result['errors'])


def test_required_rotations_fail_partial_materialization(monkeypatch):
    tool, lesson = gate(monkeypatch)
    monkeypatch.setattr(tool, 'materialize_lessons', lambda *a, **k: ([lesson], ['reference failed']))
    stats, errors, _ = tool.score_lessons('fixture', None, count=2, n_demos=2,
        competitors={'same': lambda g: g}, require_rotations=True)
    assert stats['rotations']['status'] == 'error'
    assert any('reference failed' in e for e in errors)
    assert any('required query rotations' in e for e in errors)


@pytest.mark.parametrize('period,status', [
    (6, 'declared_period_not_enumerated'),
    (65, 'declared_period_not_enumerated'),
    (None, 'not_declared'),
    (True, 'invalid_declaration'),
    (0, 'invalid_declaration'),
])
def test_semantic_smoke_reports_schedule_enumeration_separately(monkeypatch, capsys, period, status):
    tool, _ = gate(monkeypatch)
    gen = ModuleType('schedule_fixture')
    gen.EXAMPLES_NEEDED = 2
    gen.generate = lambda seed, difficulty=None: None
    gen.LESSON_COMPETITORS = {'identity': lambda grid: grid}
    if period is not None:
        gen.LESSON_SCHEDULE_PERIOD = period
    monkeypatch.setitem(sys.modules, 'puzzle_generators.per_puzzle.fixture.generator', gen)
    result = tool.audit_task('fixture', lessons=1, require_rotations=True)
    assert result['lessons']['identifiable'] == 1
    assert result['lessons']['rotations']['checked'] == 3
    coverage = result['schedule_coverage']
    assert coverage['status'] == status
    assert coverage['declared_period'] == period
    assert coverage['enumerated'] is False
    if period is not None:
        assert result['status'] == 'WARN'
    else:
        assert not any('schedule' in warning.lower() for warning in result['warnings'])
    if status == 'declared_period_not_enumerated':
        argv = coverage['followup_argv']
        assert argv[:5] == ['python3', '-m', 'arcpuzzles', 'lesson-census', 'fixture']
        assert '--enumerate-schedule-period' in argv
        assert argv[argv.index('--schedule-seed') + 1] == '0'
        assert argv.count('--band') == 3
        assert 'var/checks/fixture/schedule-period-s0.json' in argv
        tool.report(result)
        output = capsys.readouterr().out
        assert 'declared_period_not_enumerated' in output
        assert 'lesson-census fixture' in output
    else:
        assert coverage['followup_argv'] is None

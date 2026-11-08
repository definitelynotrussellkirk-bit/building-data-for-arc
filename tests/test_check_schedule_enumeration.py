"""Inline enumeration must find rare gaps, retain labels and bind resume policy."""
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from arcpuzzles import Catalog, runtime
from arcpuzzles.cli import main
from test_check_rotations import install_native_battery
from test_lesson_census import schedule_worker
from test_semantic_rotations import gate

TASK = 'aaaa00000001'


def inline_gate(schedule_worker, monkeypatch, tmp_path):
    worker, gen, _ = schedule_worker
    tool, _ = gate(monkeypatch)
    gen.RULE_HASH = 'bound-rule'
    monkeypatch.chdir(tmp_path)
    manifest = {'task_id': 'x', 'files': [{'library_path': 'generators/x/generator.py',
                 'sha256': hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()}]}
    (tmp_path / 'RUNTIME_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    monkeypatch.setattr(tool, 'BANDS', ('easy', 'hard'))
    monkeypatch.setattr(tool, '_load_census_worker', lambda: worker, raising=False)
    original = tool.importlib.import_module
    monkeypatch.setattr(tool.importlib, 'import_module',
        lambda name, *a, **k: gen if name == 'puzzle_generators.per_puzzle.x.generator'
        else original(name, *a, **k))
    return tool, worker, gen


@pytest.mark.parametrize('schedule_worker', [None, 'racket'], indirect=True)
def test_inline_enumeration_retains_fresh_fixed_seed_labels(schedule_worker, monkeypatch, tmp_path):
    tool, _, gen = inline_gate(schedule_worker, monkeypatch, tmp_path)
    gen.LESSON_COMPETITORS = {}
    gen.SEMANTIC_RIVALS = {'identity': lambda grid: grid}
    out = tmp_path / 'inline.json'
    audit = tool.audit_task('x', enumerate_schedule_period=True, schedule_seed=31,
                            schedule_census_out=out)
    coverage = audit['schedule_coverage']
    assert coverage['status'] == 'complete_fixed_seed_executed', json.dumps(coverage, indent=2)
    assert coverage['evidence_basis'] == 'source_bound_native_label_execution'
    assert coverage['lessons'] == 14 and coverage['rotations'] == 28
    assert coverage['receipt_sha256'] == hashlib.sha256(out.read_bytes()).hexdigest()
    assert not any('declared_period_not_enumerated' in x for x in audit['warnings'])
    # A census is not permission to erase the missing ordinary semantic contract.
    assert audit['status'] == 'NO_CONTRACT'
    report = json.loads(out.read_text())
    assert report['schedule_coverage']['seed'] == 31
    assert all(r['instance']['train'][0]['output'] == r['instance']['train'][0]['input']
               for r in report['lessons'])


def test_inline_enumeration_blocks_rare_residue_that_smoke_misses(schedule_worker, monkeypatch, tmp_path):
    tool, _, _ = inline_gate(schedule_worker, monkeypatch, tmp_path)
    out = tmp_path / 'rare.json'
    audit = tool.audit_task('x', enumerate_schedule_period=True, schedule_seed=31,
                            schedule_census_out=out)
    assert audit['status'] == 'FAIL'
    assert audit['schedule_coverage']['receipt_status'] == 'rejected'
    assert audit['schedule_coverage']['enumerated'] is False
    report = json.loads(out.read_text())
    assert report['summary']['ambiguous'] == 2
    assert report['summary']['ambiguous_rotations'] == 4
    assert report['schedule_coverage']['status'] == 'complete_fixed_seed'


def test_hook_only_contract_reports_hook_scope_without_inventing_rivals(schedule_worker, monkeypatch, tmp_path):
    tool, _, gen = inline_gate(schedule_worker, monkeypatch, tmp_path)
    gen.LESSON_COMPETITORS = {}
    gen.lesson_identifiable = lambda demos, query: []
    audit = tool.audit_task('x', enumerate_schedule_period=True,
                            schedule_census_out=tmp_path / 'hook.json')
    assert audit['schedule_coverage']['status'] == 'complete_fixed_seed_executed'
    assert audit['schedule_coverage']['semantic_contract'] == 'hook_only'
    assert audit['schedule_coverage']['rivals'] == []


def test_hook_warning_in_rare_start_cannot_satisfy_schedule(schedule_worker, monkeypatch, tmp_path):
    tool, _, gen = inline_gate(schedule_worker, monkeypatch, tmp_path)
    gen.LESSON_COMPETITORS = {}
    gen.lesson_identifiable = lambda demos, query: ['missing teaching evidence'] if query['input'][0][0] == 7 else []
    out = tmp_path / 'hook-warning.json'
    audit = tool.audit_task('x', enumerate_schedule_period=True, schedule_census_out=out)
    assert audit['status'] == 'FAIL' and not audit['schedule_coverage']['enumerated']
    assert json.loads(out.read_text())['summary']['hook_warnings'] == 2


def test_failed_draws_keep_incomplete_census_and_fail_gate(schedule_worker, monkeypatch, tmp_path):
    tool, _, gen = inline_gate(schedule_worker, monkeypatch, tmp_path)
    gen.generate = lambda **kw: (_ for _ in ()).throw(ValueError('broken draw'))
    out = tmp_path / 'broken.json'
    audit = tool.audit_task('x', enumerate_schedule_period=True, schedule_census_out=out)
    assert audit['status'] == 'FAIL'
    assert json.loads(out.read_text())['schedule_coverage']['status'] == 'incomplete'


def test_generated_receipt_with_changed_source_cannot_upgrade_coverage(schedule_worker, monkeypatch, tmp_path):
    tool, worker, gen = inline_gate(schedule_worker, monkeypatch, tmp_path)
    gen.LESSON_COMPETITORS = {}
    gen.SEMANTIC_RIVALS = {'same': lambda grid: grid}
    original = worker.census
    def changed(*args, **kw):
        report = original(*args, **kw)
        report['generator_sha256'] = '0' * 64
        return report
    monkeypatch.setattr(worker, 'census', changed)
    audit = tool.audit_task('x', enumerate_schedule_period=True,
                            schedule_census_out=tmp_path / 'stale.json')
    assert audit['status'] == 'FAIL' and not audit['schedule_coverage']['enumerated']
    assert 'generator hash' in audit['schedule_coverage']['rejection']


@pytest.mark.parametrize('period', [None, 0, True, -1, '7'])
def test_invalid_period_cannot_open_label_bridge(schedule_worker, monkeypatch, tmp_path, period):
    tool, _, gen = inline_gate(schedule_worker, monkeypatch, tmp_path)
    gen.LESSON_SCHEDULE_PERIOD = period
    gen.LESSON_COMPETITORS = {}
    from puzzle_generators import runner
    monkeypatch.setattr(runner, '_open_bridge_with_rule', lambda *a: pytest.fail('invalid period opened bridge'))
    audit = tool.audit_task('x', enumerate_schedule_period=True, schedule_census_out=tmp_path / 'bad.json')
    assert audit['status'] == 'FAIL'
    assert not audit['schedule_coverage']['enumerated']


def test_interruption_retains_checkpoint_without_completed_coverage(schedule_worker, monkeypatch, tmp_path):
    tool, worker, gen = inline_gate(schedule_worker, monkeypatch, tmp_path)
    original = gen.generate
    def generate(**kw):
        if kw['sample_index'] == 2:
            raise KeyboardInterrupt()
        return original(**kw)
    gen.generate = generate
    out = tmp_path / 'interrupted.json'
    with pytest.raises(KeyboardInterrupt):
        tool.audit_task('x', enumerate_schedule_period=True, schedule_census_out=out)
    partial = json.loads(out.read_text())
    assert partial['status'] == 'incomplete'
    assert partial['schedule_coverage']['status'] == 'incomplete'
    assert partial['summary']['materialized'] == 1


def install_inline_forwarding_gate(library):
    install_native_battery(library)
    (library / 'shared/tools/generator_semantic_gate.py').write_text('''import json,sys
from pathlib import Path
assert '--enumerate-schedule-period' in sys.argv
assert sys.argv[sys.argv.index('--schedule-seed')+1] == '31'
Path(sys.argv[sys.argv.index('--json-out')+1]).write_text(json.dumps({'audits':[{'status':'PASS'}]}))
''')


@pytest.mark.parametrize('battery', [False, True])
def test_public_flag_reaches_native_stage_and_summary(library, tmp_path, battery):
    install_inline_forwarding_gate(library)
    mode = ['--battery'] if battery else ['--stage', 'semantic_gate']
    out = tmp_path / 'out'
    assert main(['--library', str(library), 'check', TASK, *mode,
                 '--enumerate-schedule-period', '--schedule-seed', '31', '--out', str(out)]) == 0
    result = json.loads((out / 'result.json').read_text())
    assert result['settings']['enumerate_schedule_period'] is True
    assert result['settings']['schedule_seed'] == 31
    assert result['battery_summary']['enumerate_schedule_period'] is True
    assert result['battery_summary']['schedule_seed'] == 31
    if battery:
        assert '--enumerate-schedule-period' in result['resume_argv']


@pytest.mark.parametrize('options', [{'stage': 'lint'}, {'stage': 'task_tests'},
    {'stage': 'semantic_gate', 'schedule_census': Path('missing.json')},
    {'stage': 'semantic_gate', 'enumerate_schedule_period': 1}])
def test_invalid_inline_request_is_rejected_before_staging(library, monkeypatch, options):
    monkeypatch.setattr(runtime, 'prepare_runtime', lambda *a: pytest.fail('invalid request staged'))
    with pytest.raises(ValueError, match='schedule|enumerat'):
        runtime.check(Catalog(library), TASK, **{'enumerate_schedule_period': True, **options})


def test_resume_and_native_marker_cannot_reuse_different_enumeration_seed(library, tmp_path):
    install_inline_forwarding_gate(library)
    out = tmp_path / 'out'
    first = runtime.check(Catalog(library), TASK, full_battery=True, output=out,
                          enumerate_schedule_period=True, schedule_seed=31)
    assert first['passed']
    before = (out / 'result.json').read_bytes()
    with pytest.raises(ValueError, match='Settings differ'):
        runtime.check(Catalog(library), TASK, full_battery=True, output=out, resume=True,
                      enumerate_schedule_period=True, schedule_seed=32)
    assert (out / 'result.json').read_bytes() == before
    root = tmp_path / 'native'
    runtime.prepare_runtime(Catalog(library), root, TASK)
    argv = ['bash', 'scripts/run_generator_battery.sh', TASK, 'before', 'semantic_gate',
            '--enumerate-schedule-period', '--schedule-seed', '31']
    assert subprocess.run(argv, cwd=root, capture_output=True).returncode == 0
    changed = subprocess.run(argv[:-1]+['32'], cwd=root, capture_output=True, text=True)
    assert changed.returncode != 0 and 'SKIP  semantic_gate' not in changed.stdout


def test_audit_preset_forwards_enumeration_to_semantic_stage(library, tmp_path):
    from test_check_audit_preset import install_tests
    install_inline_forwarding_gate(library)
    install_tests(library)
    audit = runtime.check(Catalog(library), TASK, stage='audit', output=tmp_path / 'audit',
                          enumerate_schedule_period=True, schedule_seed=31)
    assert audit['passed'] and audit['audit_stages']['task_tests']['passed']
    assert '--enumerate-schedule-period' in audit['audit_stages']['semantic_gate']['command']

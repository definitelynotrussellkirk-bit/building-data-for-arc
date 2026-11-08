import importlib.util
import json
from pathlib import Path
import sys
import types
import pytest


def load_checker(monkeypatch):
    base = types.ModuleType('puzzle_generators.base'); base.set_ctx_observer = lambda observer: None
    monkeypatch.setitem(sys.modules, 'puzzle_generators.base', base)
    path = Path(__file__).resolve().parents[1] / 'shared/tools/check_generator_override_contract.py'
    spec = importlib.util.spec_from_file_location('override_report_fixture', path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module); spec.loader.exec_module(module)
    return module


def test_compact_matches_full_verdict_and_emits_plan_before_draw(monkeypatch, tmp_path, capsys):
    checker = load_checker(monkeypatch)
    calls = []
    def generate(seed, index, difficulty='easy', **overrides):
        if not calls:
            assert 'PLAN' in capsys.readouterr().out
        calls.append((seed, index))
        return [[1]]
    generator = types.SimpleNamespace(AXES={'grid_h': {'type': 'int', 'valid': '1..2'}},
                                      generate=generate, __file__=__file__)
    monkeypatch.setattr(checker, '_load_module', lambda tid: generator)
    reports = []
    for compact in (False, True):
        calls.clear()
        path = tmp_path / ('compact.json' if compact else 'full.json')
        monkeypatch.setattr(sys, 'argv', ['checker', 'fixture', '--seeds', '2', '--bands', 'easy',
                                         '--progress-every', '1', '--write-results', str(path)] +
                                        (['--compact-results'] if compact else ['--full-results']))
        assert checker.main() == 1
        assert 'PROGRESS' in capsys.readouterr().out
        reports.append(json.loads(path.read_text()))
    full, compact = reports
    for key in ('status', 'draws_total', 'accepted_total', 'finding_count', 'root_causes', 'case_count'):
        assert compact[key] == full[key]
    assert len(compact['cases']) < len(full['cases'])
    assert compact['report_mode'] == 'compact'
    assert compact['case_results_sha256'] == full['case_results_sha256']
    assert compact['source_sha256']
    assert compact['plan']['estimated_matrix_draws'] == full['draws_total']


def test_compact_retains_every_failed_case_even_above_console_cap(monkeypatch, tmp_path):
    checker = load_checker(monkeypatch)
    def generate(seed, index, difficulty='easy', **overrides):
        if overrides:
            raise RuntimeError('fixture draw failure')
        return [[1]]
    generator = types.SimpleNamespace(AXES={'grid_h': {'type': 'int', 'valid': '1..4'}},
                                      generate=generate, __file__=__file__)
    monkeypatch.setattr(checker, '_load_module', lambda tid: generator)
    reports = []
    for compact in (False, True):
        path = tmp_path / ('compact.json' if compact else 'full.json')
        monkeypatch.setattr(sys, 'argv', ['checker', 'fixture', '--seeds', '2', '--bands', 'easy',
                                         '--max-findings', '1', '--write-results', str(path)] +
                                        (['--compact-results'] if compact else ['--full-results']))
        assert checker.main() == 1
        reports.append(json.loads(path.read_text()))
    full, compact = reports
    failed = [row for row in full['cases'] if row['errors'] or row['finding_count']]
    assert len(failed) > 1
    assert compact['cases'] == failed
    for key in ('status', 'draws_total', 'accepted_total', 'finding_count', 'root_causes',
                'case_count', 'band_totals', 'plan', 'case_results_sha256', 'source_sha256'):
        assert compact[key] == full[key]
    assert compact['settings']['seeds'] == 2
    assert compact['settings']['bands'] == 'easy'
    assert compact['findings'] == full['findings']
    assert len(compact['findings']) == compact['finding_count']
    assert compact['findings_complete'] is True
    assert {finding['seed'] for finding in compact['findings']} == {0, 1}


@pytest.mark.parametrize('compact', [False, True])
def test_report_reproduces_index_sensitive_failure(monkeypatch, tmp_path, compact):
    checker = load_checker(monkeypatch)
    observed = []
    def generate(seed, index, difficulty='easy', **overrides):
        observed.append((seed, index, difficulty, dict(overrides)))
        if checker.UNKNOWN_OVERRIDE_PROBE_KEY in overrides:
            raise ValueError('unknown override')
        if seed == 1 and index == 20 and overrides.get('grid_h') == 2:
            raise RuntimeError('index-sensitive chamber defect')
        return [[1] for _ in range(overrides.get('grid_h', 1))]
    generator = types.SimpleNamespace(AXES={'grid_h': {'type': 'int', 'valid': '1..2'}},
                                      generate=generate, __file__=__file__)
    monkeypatch.setattr(checker, '_load_module', lambda tid: generator)
    path = tmp_path / 'report.json'
    monkeypatch.setattr(sys, 'argv', ['checker', 'fixture', '--seeds', '2', '--bands', 'easy',
                                     '--write-results', str(path)] +
                                    (['--compact-results'] if compact else ['--full-results']))
    assert checker.main() == 1
    report = json.loads(path.read_text())
    raw = next(row for row in report['findings'] if 'index-sensitive chamber defect' in row['message'])
    representative = next(row for row in report['representative_findings']
                          if 'index-sensitive chamber defect' in row['message'])
    witness = next(row['minimized_witness'] for row in report['root_causes']
                   if 'index-sensitive chamber defect' in row['signature'])
    for row in (raw, representative, witness):
        assert row['sample_index'] == 20
        call = row['generate_call']
        assert call == {'seed': 1, 'sample_index': 20, 'difficulty': 'easy',
                        'overrides': {'grid_h': 2}}
        assert (call['seed'], call['sample_index'], call['difficulty'], call['overrides']) in observed
        with pytest.raises(RuntimeError, match='index-sensitive chamber defect'):
            generate(call['seed'], call['sample_index'], difficulty=call['difficulty'], **call['overrides'])
    for row in report['findings']:
        assert 'sample_index' in row and 'generate_call' in row
        if row['seed'] is None:
            assert row['sample_index'] is None and row['generate_call'] is None


def test_unknown_override_witness_preserves_probe_index(monkeypatch, tmp_path):
    checker = load_checker(monkeypatch)
    generator = types.SimpleNamespace(AXES={}, generate=lambda seed, index, difficulty='easy', **kw: [[1]],
                                      __file__=__file__)
    monkeypatch.setattr(checker, '_load_module', lambda tid: generator)
    path = tmp_path / 'report.json'
    monkeypatch.setattr(sys, 'argv', ['checker', 'fixture', '--seeds', '2', '--bands', 'hard',
                                     '--strict-unknown-key', '--write-results', str(path)])
    assert checker.main() == 1
    row = next(row for row in json.loads(path.read_text())['findings'] if row['category'] == 'unknown_key')
    assert row['generate_call'] == {'seed': 0, 'sample_index': 3, 'difficulty': 'hard',
                                    'overrides': {checker.UNKNOWN_OVERRIDE_PROBE_KEY: 123}}


def test_static_and_aggregate_findings_have_no_invented_draw(monkeypatch):
    checker = load_checker(monkeypatch)
    findings = checker.FindingLog()
    findings.add('static axis has no probeable values', axis='variant')
    findings.add('aggregate axis never affects returned grids', axis='count')
    for row in [f.as_report() for f in findings] + [
        cause['minimized_witness'] for cause in findings.root_causes()
    ]:
        assert row['sample_index'] is None
        assert row['generate_call'] is None


def test_default_summary_preserves_failure_counts_and_replay(monkeypatch,tmp_path):
    checker=load_checker(monkeypatch)
    def generate(seed,index,difficulty=None,**overrides):
        if overrides: raise RuntimeError("same cause")
        return [[1]]
    generator=types.SimpleNamespace(AXES={"grid_h":{"type":"int","valid":"1..4"}}, generate=generate,__file__=__file__)
    monkeypatch.setattr(checker,"_load_module",lambda tid:generator)
    reports=[]
    for detail in (False,True):
        dest=tmp_path/("full.json" if detail else "summary.json")
        monkeypatch.setattr(sys,"argv",["checker","fixture","--seeds","2","--bands","easy","--write-results",str(dest)]+(["--full-results"] if detail else []))
        assert checker.main()==1
        reports.append(json.loads(dest.read_text()))
    summary,full=reports
    assert summary["report_mode"]=="summary" and not summary["findings_complete"]
    assert summary["finding_count"]==full["finding_count"]
    assert summary["root_causes"]==full["root_causes"]
    assert len(summary["findings"])==len(full["root_causes"])
    assert summary["replay_recipe"] and not summary["cases"]


def test_observed_scalar_checks_type_and_declared_float_policy(monkeypatch):
    checker=load_checker(monkeypatch)
    gen=types.SimpleNamespace(AXES={"color":{"type":"color"},"rate":{"type":"float"}},observe_overrides=lambda grid:{"color":1,"rate":1})
    assert checker._observed_override_errors(gen,[[1]],{"color":True},"fixture")
    assert checker._observed_override_errors(gen,[[1]],{"color":1.0},"fixture")
    assert checker._observed_override_errors(gen,[[1]],{"rate":1.0},"fixture")==[]

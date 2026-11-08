"""Setup failures must never masquerade as measured authority disagreement."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'shared/tools/check_task_authority_sync.py'
DEPENDENCIES = ('scripts/coder_synth_verify.py', 'scripts/comment_solutions.py',
                'arc_repl/racket_bridge.py', 'puzzle_generators/rule_wrap.py')


def load():
    spec = importlib.util.spec_from_file_location('_authority_layout_test', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sources(root, raw='; preserved header\n(rule! (lambda (g) g))'):
    canonical = root / 'data/canonical/puzzles.jsonl'
    canonical.parent.mkdir(parents=True)
    canonical.write_text(json.dumps({'task_id': 'fixture00',
        'program_solution': '(rule! (lambda (g) g))',
        'train': [{'input': [[1,2]], 'output': [[1,2]]}],
        'test': [{'input': [[3,4]], 'output': [[3,4]]}]}) + '\n')
    base = root / 'data/base/solutions'; base.mkdir(parents=True)
    (base / 'one.json').write_text(json.dumps({'task_id':'fixture00',
        'racket_target': {'raw_code':raw, 'target_code':'(rule! (lambda (g) g))'}}))
    return canonical, base


@pytest.mark.parametrize('missing', DEPENDENCIES)
def test_missing_execution_dependency_is_unscored_infrastructure(tmp_path, monkeypatch, missing):
    tool = load(); tool.ROOT = tmp_path
    tool.CANONICAL, tool.BASE_SOLUTIONS = sources(tmp_path)
    for name in DEPENDENCIES:
        if name != missing:
            path = tmp_path / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('raise AssertionError("No execution permitted in incomplete layout")\n')
    parity = tool.verify_execution_parity(tool.audit_task('fixture00'))
    assert parity['status'] == 'INFRASTRUCTURE_ERROR'
    assert parity['executed'] is False and parity['sources'] == []
    assert missing in parity['missing_runtime_files']
    assert parity['supported_command'] == ['arcpuzzles', 'check', 'fixture00',
                                          '--stage', 'authority_sync', '--out', 'NEW_OUTPUT_DIRECTORY']
    assert 'prepared runtime' in parity['error'].lower()


def test_direct_checkout_cli_reports_supported_route_without_semantic_scores(tmp_path):
    # Tiny source-layout copy exercises the real entrypoint without altering owner data.
    tool = tmp_path / 'shared/tools/check_task_authority_sync.py'
    tool.parent.mkdir(parents=True); shutil.copy2(TOOL, tool)
    sources(tmp_path / 'shared')
    report = tmp_path / 'direct.json'
    env = {k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')}
    p = subprocess.run([sys.executable, str(tool), 'fixture00', '--verify-execution-parity',
                        '--require-selected-exact-sync', '--json-out', str(report)],
                       cwd=tmp_path, env=env, capture_output=True, text=True, timeout=20)
    assert p.returncode == 1, p.stderr
    result = json.loads(report.read_text())
    assert result['status'] == 'FAIL'  # Gate still fails; reason stays infrastructure.
    parity = result['audits'][0]['execution_parity']
    assert parity['status'] == 'INFRASTRUCTURE_ERROR' and parity['sources'] == []
    assert 'arcpuzzles check fixture00 --stage authority_sync --out NEW_OUTPUT_DIRECTORY' in p.stdout
    assert 'ModuleNotFoundError' not in p.stdout + p.stderr


@pytest.mark.parametrize('raw,expected', [
    ('; same semantics\n(rule! (lambda (g) g))', 'PASS'),
    ('(rule! (lambda (g) (flip-lr g)))', 'FAIL'),
])
def test_prepared_relocated_runtime_scores_real_rules(tmp_path, raw, expected):
    if shutil.which('racket') is None:
        pytest.skip('Real Racket fixture requires the documented runtime')
    runtime = tmp_path / 'runtime'; scripts = runtime / 'scripts'; scripts.mkdir(parents=True)
    shutil.copy2(TOOL, scripts / TOOL.name)
    for name in ['coder_synth_verify.py', 'comment_solutions.py']:
        shutil.copy2(ROOT / 'shared/tools' / name, scripts / name)
    for name in ['arc_repl', 'puzzle_generators']:
        shutil.copytree(ROOT / 'shared/runtime' / name, runtime / name,
                        ignore=shutil.ignore_patterns('__pycache__', 'per_puzzle', 'generic'))
    sources(runtime, raw)
    report = runtime / 'parity.json'
    env = {k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')}
    p = subprocess.run([sys.executable, str(scripts / TOOL.name), 'fixture00',
                        '--verify-execution-parity', '--json-out', str(report)],
                       cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30)
    assert p.returncode == (0 if expected == 'PASS' else 1), p.stdout + p.stderr
    parity = json.loads(report.read_text())['audits'][0]['execution_parity']
    assert parity['status'] == expected and len(parity['sources']) == 2
    assert all(row['score']['error'] is None for row in parity['sources'])
    assert any(not row['solves_all_canonical_pairs'] for row in parity['sources']) == (expected == 'FAIL')


def test_text_only_audit_remains_available_without_execution_layout(tmp_path, monkeypatch, capsys):
    tool = load(); tool.ROOT = tmp_path
    tool.CANONICAL, tool.BASE_SOLUTIONS = sources(tmp_path)
    monkeypatch.setattr(sys, 'argv', [TOOL.name, 'fixture00', '--require-selected-exact-sync'])
    assert tool.main() == 0
    assert 'execution-parity' not in capsys.readouterr().out

"""Portable launcher and receipt-kind diagnostics preserve explicit boundaries."""
import json
import sys

import pytest

from arcpuzzles import review_witness as witness
from arcpuzzles.review_base_preflight import SCHEMA as BASE
from arcpuzzles.parametric_promotion import QUALIFICATION
from arcpuzzles.review_public_creation import PREFLIGHT as PUBLIC
from test_review_qualified_projection import EXPORTER
from test_review_run_receipt import packet, invoke


def test_bare_arcpuzzles_uses_controller_module_and_records_actual_argv(packet, monkeypatch):
    package = packet/'WORK/repo/src/arcpuzzles'
    package.mkdir(parents=True)
    (package/'__init__.py').write_text('')
    (package/'__main__.py').write_text('import sys,json; print(json.dumps([sys.executable,sys.argv[1:]])); raise SystemExit(7)')
    monkeypatch.setenv('PATH', '')
    result = invoke(packet, ['--receipt', 'checks/module.json', 'arcpuzzles', 'parametric', 'manifest', '--help'])
    assert result.returncode == 7, result.stderr
    assert json.loads(result.stdout) == [sys.executable, ['parametric', 'manifest', '--help']]
    row = json.loads((packet/'WORK/checks/module.json').read_text())
    assert row['payload']['argv'] == [sys.executable, '-m', 'arcpuzzles', 'parametric', 'manifest', '--help']
    assert 'arcpuzzles' in row['invocation']['argv']


def test_explicit_arcpuzzles_executable_is_not_rewritten(packet):
    executable = packet/'custom-arcpuzzles'
    executable.write_text(f'#!{sys.executable}\nprint("explicit executable")\n')
    executable.chmod(0o755)
    result = invoke(packet, [str(executable), '--help'])
    assert result.returncode == 0 and result.stdout.strip() == 'explicit executable'


@pytest.mark.parametrize('tool', ['witness', 'preview'])
@pytest.mark.parametrize('schema', [BASE, QUALIFICATION])
def test_wrong_public_flag_explains_correct_base_or_native_flag(tool, schema, tmp_path, capsys):
    receipt = tmp_path/'qualification.json'
    receipt.write_text(json.dumps({'schema': schema, 'task_id': 'fixture'}))
    (tmp_path/'execution.json').write_text('{}')
    output = tmp_path/'output'
    before = receipt.read_bytes()
    if tool == 'witness':
        result = witness.main(['--library', str(tmp_path), 'template', '--public-preflight', str(receipt), '--out', str(output)])
    else:
        result = EXPORTER.main(['export', '--public-preflight', str(receipt), '--out', str(output)])
    assert result == 1
    error = capsys.readouterr().err
    assert '--qualification' in error and '--public-preflight' in error
    assert schema in error
    assert receipt.read_bytes() == before and not output.exists()


@pytest.mark.parametrize('tool', ['witness', 'preview'])
def test_wrong_qualification_flag_names_public_creation_mode(tool, tmp_path, capsys):
    receipt = tmp_path/'preflight.json'
    receipt.write_text(json.dumps({'schema': PUBLIC}))
    (tmp_path/'execution.json').write_text('{}')
    output = tmp_path/'out'
    args = ['--qualification', str(receipt), '--out', str(output)]
    result = witness.main(['template', *args]) if tool == 'witness' else EXPORTER.main(['export', *args])
    assert result == 1
    assert '--public-preflight' in capsys.readouterr().err
    assert not output.exists()


@pytest.mark.parametrize('tool', ['witness', 'preview'])
def test_receipt_help_distinguishes_base_from_public_creation(tool, capsys):
    with pytest.raises(SystemExit) as status:
        witness.main(['template', '--help']) if tool == 'witness' else EXPORTER.main(['export', '--help'])
    assert status.value.code == 0
    output = capsys.readouterr().out
    assert 'review_base_preflight' in output
    assert 'public-evaluation creation' in output

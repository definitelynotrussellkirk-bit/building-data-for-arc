"""Caller time allowance reaches real native wrappers and retains truthful stops."""
import json
import os
from pathlib import Path
import subprocess

import pytest

from arcpuzzles import Catalog, runtime
from test_check_rotations import install_native_battery, TASK


def timeout_spy(tmp_path, monkeypatch):
    commands = tmp_path / 'timeout-arguments.jsonl'
    tools = tmp_path / 'bin'; tools.mkdir()
    spy = tools / 'timeout'
    spy.write_text('''#!/usr/bin/env python3
import json, os, sys
with open(os.environ['TEST_TIMEOUT_ARGUMENTS'], 'a') as stream:
    stream.write(json.dumps(sys.argv[1:]) + '\\n')
os.execv('/usr/bin/timeout', ['/usr/bin/timeout', *sys.argv[1:]])
''')
    spy.chmod(0o755)
    monkeypatch.setenv('PATH', str(tools) + os.pathsep + os.environ['PATH'])
    monkeypatch.setenv('TEST_TIMEOUT_ARGUMENTS', str(commands))
    # Runtime deliberately prepends the selected interpreter's bin directory.
    # On a system Python that is /usr/bin and would bypass this PATH spy.
    # Instrument only the environment; execute the real process/controller.
    real_run = runtime.run_process
    def observed_run(*args, **kwargs):
        env = dict(kwargs.get('extra_env') or {})
        env['PATH'] = str(tools) + os.pathsep + os.environ['PATH']
        kwargs['extra_env'] = env
        return real_run(*args, **kwargs)
    monkeypatch.setattr(runtime, 'run_process', observed_run)
    return commands


def budgets(path):
    return [float(json.loads(line)[2]) for line in path.read_text().splitlines()]


@pytest.mark.parametrize('battery', [False, True])
def test_public_large_allowance_is_not_capped_at_300(library, tmp_path, monkeypatch, battery):
    install_native_battery(library)
    spy = timeout_spy(tmp_path, monkeypatch)
    result = runtime.check(Catalog(library), TASK, stage='override', full_battery=battery,
                           timeout=1800, output=tmp_path/'result')
    caps = budgets(spy)
    assert caps and all(900 < value < 1800 for value in caps), caps
    assert result['execution_timeouts']['controller_seconds'] == 1800
    assert result['execution_timeouts']['native_budget_seconds'] < 1800
    # The real native wrappers record actual allowances.
    stages = result['battery_summary']['stages']
    for row in stages.values():
        if row['status'] not in ['pending', 'unknown']:
            assert 0 < row['timeout_seconds'] < 1800


def test_audit_semantic_allowance_uses_remaining_controller_budget(library, tmp_path, monkeypatch):
    install_native_battery(library)
    tests = library / f'generators/{TASK}/tests'; tests.mkdir()
    (tests/'test_ok.py').write_text('def test_ok():\n    assert 2 + 3 == 5\n')
    spy = timeout_spy(tmp_path, monkeypatch)
    result = runtime.check(Catalog(library), TASK, stage='audit', timeout=1800,
                           output=tmp_path/'audit')
    assert 900 < budgets(spy)[0] < 1800
    semantic = result['audit_stages']['semantic_gate']
    limits = semantic['execution_timeouts']
    assert 0 < limits['native_budget_seconds'] < limits['controller_seconds'] <= 1800


def test_native_budget_timeout_is_a_resource_stop_not_green(library, tmp_path):
    install_native_battery(library)
    (library/'shared/tools/check_generator_override_contract.py').write_text('import time\ntime.sleep(3)\n')
    stage = tmp_path/'staged'; runtime.prepare_runtime(Catalog(library), stage, TASK)
    command = ['bash','scripts/run_generator_battery.sh',TASK,'after','override','--fresh','--time-budget','2']
    run = subprocess.run(command,cwd=stage,capture_output=True,text=True,timeout=8)
    assert run.returncode != 0
    summary = json.loads((stage/f'checks/{TASK}_after_battery_summary.json').read_text())
    row = summary['stages']['override']
    assert row['timed_out'] is True and row['status'] != 'green'
    assert 0 < row['timeout_seconds'] <= 2
    assert summary['time_budget_seconds'] == 2
    assert not (stage/f'checks/{TASK}_after_override.ok').exists()
    receipt = json.loads((stage/f'checks/{TASK}_after_override.receipt').read_text())
    assert receipt['timeout_seconds'] == row['timeout_seconds']
    assert 0 < receipt['kill_after_seconds'] <= .2


def test_public_inner_timeout_is_reported_even_when_outer_did_not_expire(library, tmp_path):
    install_native_battery(library)
    (library/'shared/tools/check_generator_override_contract.py').write_text('import time\ntime.sleep(4)\n')
    result = runtime.check(Catalog(library),TASK,stage='override',timeout=3,output=tmp_path/'timeout')
    assert result['timed_out'] is True
    assert not result['passed']
    assert result['battery_summary']['stages']['override']['timed_out'] is True


def test_one_native_budget_is_shared_across_the_whole_battery(library, tmp_path):
    install_native_battery(library)
    for filename,_ in runtime.STAGES.values():
        (library/'shared/tools'/filename).write_text('import time\ntime.sleep(1)\nprint("gate completed")\n')
    stage=tmp_path/'staged';runtime.prepare_runtime(Catalog(library),stage,TASK)
    run=subprocess.run(['bash','scripts/run_generator_battery.sh',TASK,'after','--fresh','--keep-going','--time-budget','2.5'],cwd=stage,capture_output=True,text=True,timeout=9)
    assert run.returncode != 0
    summary=json.loads((stage/f'checks/{TASK}_after_battery_summary.json').read_text())
    assert summary['time_budget_seconds'] == 2.5 and summary['budget_exhausted'] is True
    started=[json.loads(line) for line in (stage/f'checks/{TASK}_after_commands.jsonl').read_text().splitlines() if json.loads(line)['status']=='started']
    assert 1 <= len(started) <= 3
    assert any(row['status']=='pending' for row in summary['stages'].values())
    status = subprocess.run(['bash','scripts/run_generator_battery.sh',TASK,'after','--status'],
                            cwd=stage,capture_output=True,text=True,timeout=8)
    assert status.returncode != 0
    reconstructed=json.loads((stage/f'checks/{TASK}_after_battery_summary.json').read_text())
    assert reconstructed['budget_exhausted'] is True
    assert reconstructed['time_budget_seconds'] == 2.5
    for filename,_ in runtime.STAGES.values():
        (stage/'scripts'/filename).write_text('print("gate completed")\n')
    resumed=subprocess.run(['bash','scripts/run_generator_battery.sh',TASK,'after','--resume',
                            '--time-budget','10'],cwd=stage,capture_output=True,text=True,timeout=15)
    assert resumed.returncode==0,(resumed.stdout,resumed.stderr)
    current=json.loads((stage/f'checks/{TASK}_after_battery_summary.json').read_text())
    assert current['budget_exhausted'] is False and current['time_budget_seconds']==10


def test_direct_native_default_cap_remains_explicit(library,tmp_path,monkeypatch):
    install_native_battery(library)
    spy=timeout_spy(tmp_path,monkeypatch)
    stage=tmp_path/'staged';runtime.prepare_runtime(Catalog(library),stage,TASK)
    run=subprocess.run(['bash','scripts/run_generator_battery.sh',TASK,'after','override','--fresh'],
                       cwd=stage,capture_output=True,text=True,timeout=8)
    assert run.returncode==0,(run.stdout,run.stderr)
    assert budgets(spy)==[300]
    row=json.loads((stage/f'checks/{TASK}_after_override.receipt').read_text())
    assert row['timeout_seconds']==300 and row['kill_after_seconds']==10
    assert 'time_budget_seconds' not in row


@pytest.mark.parametrize('value',['0','-1','nan','inf'])
def test_invalid_native_budget_rejects_without_mutating_staged_evidence(library,tmp_path,value):
    install_native_battery(library)
    stage=tmp_path/'staged';runtime.prepare_runtime(Catalog(library),stage,TASK)
    before={p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}
    run=subprocess.run(['bash','scripts/run_generator_battery.sh',TASK,'after','override','--time-budget',value],cwd=stage,capture_output=True,text=True,timeout=8)
    assert run.returncode != 0 and 'time-budget' in run.stderr
    assert before=={p.relative_to(stage).as_posix():p.read_bytes() for p in stage.rglob('*') if p.is_file()}


@pytest.mark.parametrize('value',[0,-1,float('inf'),float('nan')])
def test_invalid_public_budget_refuses_before_snapshot(library,monkeypatch,value):
    monkeypatch.setattr(runtime,'prepare_runtime',lambda *a,**k:pytest.fail('invalid request staged'))
    with pytest.raises(ValueError,match='finite|positive'):
        runtime.check(Catalog(library),TASK,stage='override',timeout=value)

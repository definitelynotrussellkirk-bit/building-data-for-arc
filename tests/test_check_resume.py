"""Resume exercises real child processes in a disposable fixture library."""
import json
from pathlib import Path
import pytest
from arcpuzzles import Catalog, runtime


def install_battery(library):
    tools = library / 'shared/tools'; tools.mkdir(parents=True)
    # Fixture has a completed first stage and a failed second stage. Resume
    # must retain the former and rerun the latter from a reconstructed runtime.
    (tools / 'run_generator_battery.sh').write_text('''mkdir -p checks
if [ "$3" = "--resume" ]; then
  test -f checks/aaaa00000001_after_lint.ok || exit 91
  test ! -d checks/.lock_aaaa00000001_after || exit 92
  echo SKIP-lint
  echo repaired > checks/aaaa00000001_after_override.log
  exit 0
fi
echo original > checks/aaaa00000001_after_lint.log
echo source > checks/aaaa00000001_after_lint.ok
echo failure > checks/aaaa00000001_after_override.log
echo checkpoint
exit 1
''')
    mapping = library / 'catalog/runtime_files.json'
    rows = json.loads(mapping.read_text())
    rows.append({'path': 'shared/tools/run_generator_battery.sh', 'target': 'scripts/run_generator_battery.sh'})
    rows.append({'path': 'shared/data/canonical/puzzles.jsonl', 'target': 'data/canonical/puzzles.jsonl'})
    mapping.write_text(json.dumps(rows))


def test_resume_reconstructs_and_retains_failed_attempt(library, tmp_path):
    install_battery(library)
    out = tmp_path / 'out'
    first = runtime.check(Catalog(library), 'aaaa00000001', full_battery=True, phase='after', output=out)
    assert not first['passed'] and not Path(first['runtime_path']).exists()
    (out / 'checks/.lock_aaaa00000001_after').mkdir()
    second = runtime.check(Catalog(library), 'aaaa00000001', full_battery=True, output=out, resume=True)
    assert second['passed'] and second['phase'] == 'after' and 'SKIP-lint' in second['stdout']
    assert (out / 'attempts/0001/checks/aaaa00000001_after_override.log').read_text().strip() == 'failure'
    assert (out / 'checks/aaaa00000001_after_lint.log').read_text().strip() == 'original'


@pytest.mark.parametrize('drift', ['source', 'authority', 'phase', 'racket'])
def test_resume_rejects_drift(library, tmp_path, monkeypatch, drift):
    install_battery(library)
    out = tmp_path / 'out'
    runtime.check(Catalog(library), 'aaaa00000001', full_battery=True, phase='after', output=out)
    kwargs = {}
    if drift == 'source':
        (library / 'generators/aaaa00000001/generator.py').write_text('VERSION = "changed"\n')
    elif drift == 'authority':
        with (library / 'shared/data/canonical/puzzles.jsonl').open('a') as stream:
            stream.write('\n')
    elif drift == 'phase':
        kwargs['phase'] = 'before'
    else:
        monkeypatch.setenv('RACKET_PATH', '/different/racket')
    before = (out / 'result.json').read_bytes()
    with pytest.raises(ValueError, match='[Ss]ource|[Ss]ettings|[Pp]hase'):
        runtime.check(Catalog(library), 'aaaa00000001', full_battery=True, output=out, resume=True, **kwargs)
    assert (out / 'result.json').read_bytes() == before


def test_resume_is_battery_only(library, tmp_path):
    with pytest.raises(ValueError, match='battery'):
        runtime.check(Catalog(library), 'aaaa00000001', output=tmp_path / 'out', resume=True)


@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_missing_log_invalidates_success_marker(library, tmp_path, damage):
    install_battery(library)
    out = tmp_path / 'out'
    runtime.check(Catalog(library), 'aaaa00000001', full_battery=True, phase='after', output=out)
    log = out / 'checks/aaaa00000001_after_lint.log'
    if damage == 'missing':
        log.unlink()
    else:
        log.write_text('tampered')
    result = runtime.check(Catalog(library), 'aaaa00000001', full_battery=True, output=out, resume=True)
    assert 'lint' in result['invalidated_stages']
    assert result['exit_code'] == 91 and not result['passed']


def test_dependency_missing_is_not_executed(library, tmp_path, monkeypatch):
    tests = library / 'generators/aaaa00000001/tests'; tests.mkdir()
    (tests / 'test_example.py').write_text('def test_example(): pass\n')
    import subprocess
    subprocess.run(['python3', '-m', 'venv', '--without-pip', str(tmp_path / 'isolated')], check=True)
    monkeypatch.setattr(runtime.sys, 'executable', str(tmp_path / 'isolated/bin/python'))
    result = runtime.check(Catalog(library), 'aaaa00000001', stage='task_tests')
    assert result['test_status'] == 'dependency_missing'
    assert result['missing_dependency'] == 'pytest' and not result['passed']
    assert result['test_interpreter'] == str(tmp_path / 'isolated/bin/python')


def test_native_battery_reuses_receipts_after_interruption(library, tmp_path):
    tools = library / 'shared/tools'; tools.mkdir(parents=True)
    repository = Path(__file__).resolve().parents[1]
    (tools / 'run_generator_battery.sh').write_bytes((repository / 'shared/tools/run_generator_battery.sh').read_bytes())
    (tools / 'generator_battery_subject.py').write_text('print("generator\\tauthority\\tbound-subject")\n')
    # Real shell orchestration, synthetic cheap gate commands (no corpus runs).
    for filename, _ in runtime.STAGES.values():
        (tools / filename).write_text('''import json, sys
from pathlib import Path
if '--json-out' in sys.argv:
    Path(sys.argv[sys.argv.index('--json-out') + 1]).write_text(json.dumps({'audits': []}))
print('PASS fixture gate')
''')
    mapping = library / 'catalog/runtime_files.json'
    rows = json.loads(mapping.read_text())
    rows.extend({'path': 'shared/tools/' + source.name, 'target': 'scripts/' + source.name}
                for source in tools.iterdir())
    mapping.write_text(json.dumps(rows))
    out = tmp_path / 'native'
    def interrupt(chunk):
        if 'PASS  lint' in chunk:
            raise KeyboardInterrupt('simulate lost caller')
    with pytest.raises(KeyboardInterrupt):
        runtime.check(Catalog(library), 'aaaa00000001', full_battery=True, phase='after', output=out,
                      on_output=interrupt)
    first = json.loads((out / 'result.json').read_text())
    assert first['status'] == 'interrupted'
    result = runtime.check(Catalog(library), 'aaaa00000001', full_battery=True, output=out, resume=True)
    assert result['passed'], result['stderr']
    assert 'SKIP  lint' in result['stdout']
    assert json.loads((out / 'attempts/0001/result.json').read_text())['status'] == 'interrupted'
    journal = [json.loads(line) for line in (out / 'checks/aaaa00000001_after_commands.jsonl').read_text().splitlines()]
    assert sum(row.get('stage') == 'lint' and row.get('status') == 'started' for row in journal) == 1


def test_output_lock_rejects_concurrent_writer(library, tmp_path):
    import fcntl
    out = tmp_path / 'locked'
    with (tmp_path / '.locked.check.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ValueError, match='active writer'):
            runtime.check(Catalog(library), 'aaaa00000001', full_battery=True, output=out)

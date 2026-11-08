"""Public check policy reaches the native shell and cannot reuse diagnostic evidence."""
import json
from pathlib import Path
import subprocess

import pytest

from arcpuzzles import Catalog, runtime
from arcpuzzles.cli import main

ROOT = Path(__file__).resolve().parents[1]
TASK = 'aaaa00000001'


def install_native_battery(library):
    tools = library / 'shared/tools'
    tools.mkdir(parents=True)
    (tools / 'run_generator_battery.sh').write_bytes((ROOT / 'shared/tools/run_generator_battery.sh').read_bytes())
    (tools / 'generator_battery_subject.py').write_text('print("generator\\tauthority\\tbound-subject")\n')
    # Cheap fake gates isolate shell orchestration; native semantic scoring has
    # separate concrete labeled-grid tests in test_semantic_rotations.py.
    for filename, _ in runtime.STAGES.values():
        (tools / filename).write_text('''import json, sys
from pathlib import Path
required = '--require-rotations-identifiable' in sys.argv
status = 'FAIL' if required else 'PASS'
if '--json-out' in sys.argv:
    Path(sys.argv[sys.argv.index('--json-out') + 1]).write_text(json.dumps({'audits': [{'status': status}]}))
print('required rotations failed' if required else 'diagnostic rotations only')
sys.exit(2 if required else 0)
''')
    mapping = library / 'catalog/runtime_files.json'
    rows = json.loads(mapping.read_text())
    rows.extend({'path': 'shared/tools/' + p.name, 'target': 'scripts/' + p.name} for p in tools.iterdir())
    mapping.write_text(json.dumps(rows))


@pytest.mark.parametrize('battery', [False, True])
def test_public_required_policy_changes_verdict_and_is_retained(library, tmp_path, battery):
    install_native_battery(library)
    mode = ['--battery'] if battery else ['--stage', 'semantic_gate']
    out = tmp_path / 'strict'
    assert main(['--library', str(library), 'check', TASK, *mode,
                 '--require-rotations-identifiable', '--out', str(out)]) == 1
    result = json.loads((out / 'result.json').read_text())
    assert not result['passed']
    assert result['settings']['require_rotations_identifiable'] is True
    assert result['battery_summary']['require_rotations_identifiable'] is True
    assert result['battery_summary']['stages']['semantic_gate']['status'] == 'failed'
    assert 'required rotations failed' in (out / f'checks/{TASK}_before_semantic_gate.log').read_text()


def test_default_policy_is_diagnostic_and_resume_rejects_changed_policy(library, tmp_path):
    install_native_battery(library)
    out = tmp_path / 'default'
    result = runtime.check(Catalog(library), TASK, full_battery=True, phase='after', output=out)
    assert result['passed']
    before = (out / 'result.json').read_bytes()
    with pytest.raises(ValueError, match='Settings differ'):
        runtime.check(Catalog(library), TASK, full_battery=True, output=out, resume=True,
                      require_rotations_identifiable=True)
    assert (out / 'result.json').read_bytes() == before


@pytest.mark.parametrize('resume', [False, True])
def test_native_strict_policy_does_not_reuse_diagnostic_marker(library, tmp_path, resume):
    install_native_battery(library)
    staged = tmp_path / 'runtime'
    runtime.prepare_runtime(Catalog(library), staged, TASK)
    argv = ['bash', 'scripts/run_generator_battery.sh', TASK, 'after', 'semantic_gate']
    first = subprocess.run(argv, cwd=staged, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    second_argv = argv[:4] + ['--resume'] if resume else argv
    second = subprocess.run([*second_argv, '--require-rotations-identifiable'], cwd=staged, capture_output=True, text=True)
    assert second.returncode != 0
    assert 'required rotations failed' in (staged / f'checks/{TASK}_after_semantic_gate.log').read_text()


@pytest.mark.parametrize('options', [{'stage': 'lint'}, {'stage': 'task_tests'},
                                      {'stage': 'semantic_gate', 'require_rotations_identifiable': 'yes'}])
def test_invalid_rotation_policy_is_rejected_before_staging(library, monkeypatch, options):
    monkeypatch.setattr(runtime, 'prepare_runtime', lambda *a: pytest.fail('invalid request staged'))
    kwargs = {'require_rotations_identifiable': True, **options}
    with pytest.raises(ValueError, match='require.rotations|boolean'):
        runtime.check(Catalog(library), TASK, **kwargs)

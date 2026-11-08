"""Public compact receipts bind native resume without changing gate outcomes."""
import json
from pathlib import Path
import subprocess

import pytest

from arcpuzzles import Catalog, runtime
from arcpuzzles.cli import main
from test_check_rotations import install_native_battery

TASK = 'aaaa00000001'


@pytest.mark.parametrize('battery', [False, True])
def test_public_compact_mode_reaches_override_and_is_retained(library, tmp_path, battery):
    install_native_battery(library)
    checker = library / 'shared/tools/check_generator_override_contract.py'
    checker.write_text('''import json, sys
from pathlib import Path
path = Path(sys.argv[sys.argv.index('--write-results') + 1])
path.write_text(json.dumps({'status': 'FAIL', 'compact': '--compact-results' in sys.argv}))
print('failing override fixture')
sys.exit(1)
''')
    out = tmp_path / 'compact'
    mode = ['--battery'] if battery else ['--stage', 'override']
    assert main(['--library', str(library), 'check', TASK, *mode,
                 '--compact-results', '--out', str(out)]) == 1
    result = json.loads((out / 'result.json').read_text())
    assert result['passed'] is False
    assert result['settings']['compact_results'] is True
    assert result['battery_summary']['compact_results'] is True
    assert result['battery_summary']['stages']['override']['status'] == 'failed'
    report = json.loads((out / f'checks/{TASK}_before_override_results.json').read_text())
    assert report == {'status': 'FAIL', 'compact': True}


def test_public_resume_rejects_changed_receipt_mode(library, tmp_path):
    install_native_battery(library)
    out = tmp_path / 'original'
    runtime.check(Catalog(library), TASK, full_battery=True, output=out)
    before = (out / 'result.json').read_bytes()
    with pytest.raises(ValueError, match='Settings differ'):
        runtime.check(Catalog(library), TASK, full_battery=True, output=out, resume=True,
                      compact_results=True)
    assert (out / 'result.json').read_bytes() == before


@pytest.mark.parametrize('resume', [False, True])
def test_native_changed_mode_reruns_override_instead_of_reusing_receipt(library, tmp_path, resume):
    install_native_battery(library)
    checker = library / 'shared/tools/check_generator_override_contract.py'
    checker.write_text('''import json, sys
from pathlib import Path
path = Path(sys.argv[sys.argv.index('--write-results') + 1])
path.write_text(json.dumps({'status': 'PASS', 'compact': '--compact-results' in sys.argv}))
print('override fixture ran')
''')
    staged = tmp_path / 'runtime'
    runtime.prepare_runtime(Catalog(library), staged, TASK)
    argv = ['bash', 'scripts/run_generator_battery.sh', TASK, 'after', 'override']
    first = subprocess.run(argv, cwd=staged, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    second = subprocess.run([*(argv[:4] + ['--resume'] if resume else argv), '--compact-results'],
                            cwd=staged, capture_output=True, text=True)
    assert second.returncode == 0, second.stderr
    report = json.loads((staged / f'checks/{TASK}_after_override_results.json').read_text())
    assert report['compact'] is True
    assert 'SKIP  override' not in second.stdout


@pytest.mark.parametrize('options', [{'stage': 'lint'}, {'stage': 'task_tests'},
                                    {'stage': 'override', 'compact_results': 'yes'}])
def test_invalid_compact_request_fails_before_staging(library, monkeypatch, options):
    monkeypatch.setattr(runtime, 'prepare_runtime', lambda *a: pytest.fail('invalid request staged'))
    with pytest.raises(ValueError, match='compact.results|boolean'):
        runtime.check(Catalog(library), TASK, **{'compact_results': True, **options})

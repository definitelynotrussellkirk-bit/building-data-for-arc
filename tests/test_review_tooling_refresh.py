"""Exercise real staged tests, interrupted children and Git patch replay."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from arcpuzzles import Catalog, runtime
from arcpuzzles.review_full_return import _diff


def test_task_tests_include_new_workspace_and_use_staged_catalog(library, tmp_path):
    home = library / 'generators/aaaa00000001'
    (home / 'tests').mkdir()
    (home / 'workspace').mkdir()
    (home / 'workspace/value.txt').write_text('fresh dependency')
    (home / 'tests/test_new.py').write_text(
        'from pathlib import Path\nfrom arcpuzzles import Catalog\n'
        'def test_staged():\n'
        ' assert Catalog().root == Path.cwd()\n'
        ' assert Catalog().describe("aaaa00000001")["version"] == "1.0.0"\n'
        ' assert (Path(__file__).parents[1]/"workspace/value.txt").read_text() == "fresh dependency"\n')
    out = tmp_path / 'tests-out'
    result = runtime.check(Catalog(library), 'aaaa00000001', stage='task_tests', output=out)
    assert result['passed'] and '1 passed' in result['stdout']
    files = result['runtime_manifest']['files']
    assert any(f['library_path'].endswith('workspace/value.txt') and
               f['sha256'] == hashlib.sha256(b'fresh dependency').hexdigest() for f in files)


@pytest.mark.parametrize("distinct_legacy", [False, True])
def test_task_tests_collect_source_once_and_keep_legacy_imports(library, tmp_path, distinct_legacy):
    home = library / 'generators/aaaa00000001/tests'
    home.mkdir()
    legacy = 'tests/test_generator_aaaa00000001.py'
    source = home / 'test_generator_aaaa00000001.py'
    source.write_text(
        'from pathlib import Path\n'
        'def test_once():\n'
        ' assert Path("tests/test_generator_aaaa00000001.py").is_file()\n'
        ' marker = Path("executed-once")\n'
        ' assert not marker.exists(), "mirrored test ran twice"\n'
        ' marker.touch()\n')
    mapping = library / 'catalog/runtime_files.json'
    rows = json.loads(mapping.read_text())
    rows.append({'path': source.relative_to(library).as_posix(), 'target': legacy})
    if distinct_legacy:
        other = library / 'shared/legacy_test.py'
        other.write_text('def test_distinct_legacy(): assert True\n')
        rows.append({'path': 'shared/legacy_test.py',
                     'target': 'tests/test_generator_aaaa00000001_extra.py'})
    mapping.write_text(json.dumps(rows))
    result = runtime.check(Catalog(library), 'aaaa00000001', stage='task_tests',
                           output=tmp_path / 'once')
    assert result['passed'], result['stdout'] + result['stderr']
    assert result['test_counts']['tests'] == 1 + int(distinct_legacy)
    selection = result['runtime_manifest']['task_test_collection']
    assert selection['omitted_mirrors'] == [legacy]


def test_task_tests_keep_legacy_collection_for_nonstandard_source_name(library, tmp_path):
    home = library / 'generators/aaaa00000001/tests'
    home.mkdir()
    source = home / 'testlegacy.py'  # Not a default pytest collection filename.
    source.write_text('def test_legacy(): assert True\n')
    mapping = library / 'catalog/runtime_files.json'
    rows = json.loads(mapping.read_text())
    rows.append({'path': source.relative_to(library).as_posix(),
                 'target': 'tests/test_generator_aaaa00000001.py'})
    mapping.write_text(json.dumps(rows))
    result = runtime.check(Catalog(library), 'aaaa00000001', stage='task_tests',
                           output=tmp_path / 'legacy-name')
    assert result['passed'], result['stdout'] + result['stderr']
    assert result['test_counts']['tests'] == 1
    assert result['runtime_manifest']['task_test_collection']['omitted_mirrors'] == []


def test_missing_task_tests_are_not_a_pass(library, tmp_path):
    result = runtime.check(Catalog(library), 'aaaa00000001', stage='task_tests',
                           output=tmp_path / 'no-tests')
    assert result['passed'] is False and result['exit_code'] == 5
    assert result['test_status'] == 'no_tests'


def test_task_test_import_warning_is_actionable_without_breaking_legacy_snapshot(library, tmp_path):
    home = library / 'generators/aaaa00000001/tests'; home.mkdir()
    (home / 'test_old.py').write_text(
        'from scripts.legacy_helper import VALUE\n'
        'def test_old(): assert VALUE == 7\n')
    tools = library / 'shared/tools'; tools.mkdir(parents=True)
    (tools / 'legacy_helper.py').write_text('VALUE = 7\n')
    mapping = library / 'catalog/runtime_files.json'
    rows = json.loads(mapping.read_text())
    rows.append({'path': 'shared/tools/legacy_helper.py', 'target': 'scripts/legacy_helper.py'})
    mapping.write_text(json.dumps(rows))
    result = runtime.check(Catalog(library), 'aaaa00000001', stage='task_tests', output=tmp_path / 'old-tests')
    assert result['passed']
    warning = result['test_import_diagnostics'][0]
    assert warning['path'] == 'generators/aaaa00000001/tests/test_old.py'
    assert warning['line'] == 1
    assert 'reviewer_support' in warning['message']
    assert 'scripts.legacy_helper' in warning['message']
    assert result['test_counts'] == {'tests': 1, 'passed': 1, 'failed': 0, 'errors': 0, 'skipped': 0}


def test_task_tests_expose_portable_helper_and_count_skips(library, tmp_path):
    home = library / 'generators/aaaa00000001/tests'; home.mkdir()
    (home / 'test_portable.py').write_text(
        'import pytest\nfrom reviewer_support import canonical_pairs, find_root\n'
        'def test_pairs():\n'
        ' assert canonical_pairs("aaaa00000001", root=find_root(__file__))[0]["output"] == [[2]]\n'
        '@pytest.mark.skip(reason="optional dependency")\n'
        'def test_optional(): pass\n')
    shared = library / 'shared/runtime'; shared.mkdir(parents=True)
    source = Path(__file__).resolve().parents[1] / 'shared/runtime/reviewer_support.py'
    (shared / 'reviewer_support.py').write_bytes(source.read_bytes())
    mapping = library / 'catalog/runtime_files.json'
    rows = json.loads(mapping.read_text())
    rows.append({'path': 'shared/runtime/reviewer_support.py', 'target': 'reviewer_support.py'})
    mapping.write_text(json.dumps(rows))
    result = runtime.check(Catalog(library), 'aaaa00000001', stage='task_tests', output=tmp_path / 'portable-tests')
    assert result['passed']
    assert result['test_import_diagnostics'] == []
    assert result['test_counts'] == {'tests': 2, 'passed': 1, 'failed': 0, 'errors': 0, 'skipped': 1}
    assert 'checks/task_tests.xml' in result['evidence_sha256']


def test_completed_receipts_survive_interruption_and_child_stops(library, tmp_path):
    tools = library / 'shared/tools'; tools.mkdir(parents=True)
    script = tools / 'run_generator_battery.sh'
    script.write_text('mkdir -p checks\necho $$ > checks/pid\n'
                      'echo completed > checks/lint.log\n'
                      'echo "{\\"phase\\":\\"after\\"}" > checks/aaaa00000001_after_battery_summary.json\n'
                      'echo "PASS  lint"\nsleep 30\n')
    mapping = library / 'catalog/runtime_files.json'
    rows = json.loads(mapping.read_text()); rows.append({'path': 'shared/tools/run_generator_battery.sh',
                                                        'target': 'scripts/run_generator_battery.sh'})
    mapping.write_text(json.dumps(rows))
    out = tmp_path / 'interrupted'
    def interrupt(chunk):
        if 'PASS' in chunk:
            assert (out / 'checks/lint.log').read_text().strip() == 'completed'
            assert json.loads((out / 'result.json').read_text())['status'] == 'running'
            raise KeyboardInterrupt('controlled caller interruption')
    with pytest.raises(KeyboardInterrupt):
        runtime.check(Catalog(library), 'aaaa00000001', full_battery=True,
                      phase='after', output=out, on_output=interrupt)
    result = json.loads((out / 'result.json').read_text())
    assert result['status'] == 'interrupted' and result['passed'] is None
    assert (out / 'RUNTIME_MANIFEST.json').exists()
    pid = int((out / 'checks/pid').read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


@pytest.mark.parametrize(('before', 'after'), [
    (b'old', b'new'), (b'old\n', b'new'), (b'old', b'new\n'),
    (None, b'new'), (b'old', b''), (b'a\rb\n', b'a\rc\n'),
    ('a\u2028b\n'.encode(), 'a\u2028c\n'.encode()), (b'a\r\n', b'b\r\n'),
])
def test_return_diff_replays_exact_bytes_with_git(tmp_path, before, after):
    path = tmp_path / 'source.txt'
    if before is not None:
        path.write_bytes(before)
    patch = _diff('source.txt', before, after).encode()
    checked = subprocess.run(['git', 'apply', '--check', '-'], input=patch,
                             cwd=tmp_path, capture_output=True)
    assert checked.returncode == 0, checked.stderr.decode()
    applied = subprocess.run(['git', 'apply', '-'], input=patch,
                             cwd=tmp_path, capture_output=True)
    assert applied.returncode == 0, applied.stderr.decode()
    assert path.read_bytes() == after


def test_preflight_blocks_missing_import_before_pytest(library, tmp_path):
    home = library / 'generators/aaaa00000001/tests'; home.mkdir()
    marker = tmp_path / 'pytest-started'
    (home / 'test_broken.py').write_text(
        f'from pathlib import Path\nPath({str(marker)!r}).touch()\n'
        'from scripts.no_longer_shipped import _canonical_path\n')
    result = runtime.check(Catalog(library), 'aaaa00000001', stage='task_tests', output=tmp_path / 'preflight')
    assert result['test_status'] == 'preflight_failed'
    assert result['passed'] is False and result['exit_code'] == 2
    assert result['test_counts'] is None
    assert not marker.exists()
    assert 'reviewer_support' in result['stderr']

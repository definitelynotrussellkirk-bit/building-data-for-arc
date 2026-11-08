"""Selected frozen fixtures must run, fail visibly, and not run twice."""
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog, runtime

TASK = 'aaaa00000001'
ROOT_FIXTURE = f'generators/{TASK}/test_generator_{TASK}.py'


def test_generator_root_fixture_runs_in_isolated_audit_without_source_edits(library, tmp_path):
    fixture = library / ROOT_FIXTURE
    fixture.write_text('def test_frozen():\n assert 6 * 7 == 42\n')
    original = fixture.read_bytes()
    result = runtime.check(Catalog(library), TASK, stage='task_tests', phase='audit', output=tmp_path/'checks')
    assert result['test_status'] == 'executed'
    assert result['passed'] and result['test_counts']['passed'] == 1
    assert result['phase'] == 'audit' and result['test_paths'] == [ROOT_FIXTURE]
    assert fixture.read_bytes() == original
    copied = next(r for r in result['runtime_manifest']['files'] if r['runtime_path'] == ROOT_FIXTURE)
    assert copied['sha256'] == hashlib.sha256(original).hexdigest()


def test_failing_frozen_root_fixture_blocks_passing_editable_tests(library, tmp_path):
    (library / ROOT_FIXTURE).write_text('def test_frozen():\n assert False, "frozen defect"\n')
    tests = library / f'generators/{TASK}/tests'; tests.mkdir()
    (tests/'test_editable.py').write_text('def test_editable():\n assert True\n')
    result = runtime.check(Catalog(library), TASK, stage='task_tests', output=tmp_path/'checks')
    assert result['test_status'] == 'executed' and not result['passed']
    assert result['test_counts']['passed'] == 1 and result['test_counts']['failed'] == 1
    assert 'frozen defect' in result['stdout']


def test_same_source_root_fixture_mirror_is_not_executed_twice(library, tmp_path):
    (library/ROOT_FIXTURE).write_text('def test_once():\n assert True\n')
    mapping = library/'catalog/runtime_files.json'; rows = json.loads(mapping.read_text())
    mirror = f'tests/test_generator_{TASK}.py'
    rows.append({'path': ROOT_FIXTURE, 'target': mirror}); mapping.write_text(json.dumps(rows))
    result = runtime.check(Catalog(library), TASK, stage='task_tests', output=tmp_path/'checks')
    assert result['passed'] and result['test_counts']['passed'] == 1
    assert result['test_paths'] == [ROOT_FIXTURE]
    assert result['runtime_manifest']['task_test_collection']['omitted_mirrors'] == [mirror]


def test_identical_bytes_from_distinct_test_homes_are_both_executed(library, tmp_path):
    raw = 'def test_separate_origin():\n assert True\n'
    (library/ROOT_FIXTURE).write_text(raw)
    other = library/'shared/tests/other_frozen.py'; other.parent.mkdir(parents=True); other.write_text(raw)
    mapping = library/'catalog/runtime_files.json'; rows = json.loads(mapping.read_text())
    target = f'tests/test_generator_{TASK}_other.py'
    rows.append({'path': 'shared/tests/other_frozen.py', 'target': target}); mapping.write_text(json.dumps(rows))
    result = runtime.check(Catalog(library), TASK, stage='task_tests', output=tmp_path/'checks')
    assert result['passed'] and result['test_counts']['passed'] == 2
    assert result['test_paths'] == [ROOT_FIXTURE, target]


def test_missing_import_in_frozen_root_fixture_is_preflight_failure_not_absence(library, tmp_path):
    (library/ROOT_FIXTURE).write_text('from scripts.no_longer_shipped import _helper\n')
    result = runtime.check(Catalog(library), TASK, stage='task_tests', output=tmp_path/'checks')
    assert result['test_status'] == 'preflight_failed' and not result['passed']
    assert result['test_paths'] == [ROOT_FIXTURE]
    assert any(r['severity'] == 'error' for r in result['test_import_diagnostics'])


def test_unrelated_root_test_is_not_silently_added_to_selected_scope(library, tmp_path):
    (library/f'generators/{TASK}/test_unrelated.py').write_text('def test_other():\n assert False\n')
    result = runtime.check(Catalog(library), TASK, stage='task_tests', output=tmp_path/'checks')
    assert result['test_status'] == 'no_tests' and not result['passed']
    assert result['test_paths'] == []

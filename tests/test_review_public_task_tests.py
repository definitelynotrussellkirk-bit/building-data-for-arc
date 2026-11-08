"""Relocated reviewer tests: no owner registration or native acceptance."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pytest

from arcpuzzles.review_full_draw import draw_main
from arcpuzzles.review_public_task_tests import assigned_home, run_tests
from test_review_public_creation import public_packet


@pytest.fixture
def assigned_packet(library, tmp_path):
    runtime = library/'shared/runtime'; runtime.mkdir(parents=True)
    (runtime/'fixture_runtime.py').write_text('VALUE = 43\n')
    parser = library/'shared/tools/comment_solutions.py'; parser.parent.mkdir(parents=True)
    parser.write_text('# exact private test runtime fixture\n')
    src = library/'src/arcpuzzles'; src.mkdir(parents=True)
    (src/'__init__.py').write_text('')
    packet = public_packet(library, tmp_path)
    contract = draw_main(packet, bytes(32)); tid = contract['task_id']
    home = packet/'repo/generators'/tid
    (home/'generator.py').write_text('VALUE = 17\n')
    (home/'tests').mkdir()
    (home/'tests/test_local.py').write_text('''from pathlib import Path
import importlib.util
import fixture_runtime

def test_relocated_source_and_private_fixture():
    home = Path(__file__).resolve().parents[1]
    root = home.parents[1]
    assert (root/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file()
    assert (home/'workspace/private.json').read_text() == 'private label'
    assert not (root/'catalog').exists()
    assert 'runtime' in str(root)
    spec = importlib.util.spec_from_file_location('assigned_generator', home/'generator.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    assert module.VALUE == 17 and fixture_runtime.VALUE == 43
''')
    (home/'workspace/private.json').write_text('private label')
    return packet, tid, home


def test_unregistered_tests_run_from_exact_relocated_source(assigned_packet, tmp_path):
    packet, tid, home = assigned_packet
    catalog = packet/'repo/catalog/puzzles.jsonl'; before = catalog.read_bytes()
    out = tmp_path/'task-evidence'
    result = run_tests(packet, tid, out, timeout=30)
    assert result['status'] == 'passed', (out/'task-tests.log').read_text()
    assert result['test_counts']['tests'] == 1
    assert result['owner_accepted'] is False
    assert catalog.read_bytes() == before
    assert not (home/'parametric/accepted.json').exists()
    for row in result['source_binding']['files']:
        assert hashlib.sha256((packet/'repo'/row['path']).read_bytes()).hexdigest() == row['sha256']
    assert (out/'task_tests.xml').is_file()
    assert (out/'result.json').is_file()
    assert not (out/'runtime').exists()
    assert {p.name for p in out.iterdir()} == {'source-binding.json', 'task-tests.log', 'task_tests.xml', 'result.json'}


def test_runtime_scratch_is_removed_if_execution_raises(assigned_packet, tmp_path, monkeypatch):
    from arcpuzzles import runtime
    packet, tid, home = assigned_packet
    out = tmp_path/'raised'
    stages = []

    def fail(command, cwd, **kwargs):
        stages.append(Path(cwd))
        raise RuntimeError('execution failed')

    monkeypatch.setattr(runtime, 'run_process', fail)
    with pytest.raises(RuntimeError, match='execution failed'):
        run_tests(packet, tid, out)
    assert stages and not stages[0].exists()
    assert not (out/'result.json').exists()


def test_unassigned_or_changed_parent_cannot_run(assigned_packet, tmp_path):
    packet, tid, home = assigned_packet
    manifest = json.loads((packet/'PACKET-MANIFEST.json').read_text())
    contract = json.loads((packet/'ASSIGNMENT.json').read_text())
    unassigned = next(t for t in manifest['public_eval_creation']['ids'] if t not in {r['task_id'] for r in contract['repair_targets']})
    with pytest.raises(ValueError, match='one assigned'):
        run_tests(packet, unassigned, tmp_path/'unassigned')
    parent = home/'workspace/public-parent.json'; parent.write_text(parent.read_text()+'\n')
    with pytest.raises(ValueError, match='Immutable'):
        run_tests(packet, tid, tmp_path/'changed')
    assert not (tmp_path/'changed').exists()


def test_shared_source_and_symlink_are_rejected_before_test_execution(assigned_packet, tmp_path):
    packet, tid, home = assigned_packet
    shared = packet/'repo/shared/runtime/fixture_runtime.py'; original = shared.read_bytes()
    shared.write_text('VALUE = 99\n')
    with pytest.raises(ValueError, match='Shared packet source changed'):
        run_tests(packet, tid, tmp_path/'drift')
    shared.write_bytes(original)
    (home/'workspace/link.py').symlink_to(shared)
    with pytest.raises(ValueError, match='symlinks'):
        run_tests(packet, tid, tmp_path/'link')


def test_timeout_and_test_failure_are_retained(assigned_packet, tmp_path):
    packet, tid, home = assigned_packet
    test = home/'tests/test_local.py'
    test.write_text('def test_failure():\n    assert False\n')
    result = run_tests(packet, tid, tmp_path/'failed', timeout=30)
    assert result['status'] == 'failed' and result['exit_code'] == 1
    test.write_text('import time\ndef test_slow():\n    time.sleep(20)\n')
    result = run_tests(packet, tid, tmp_path/'timeout', timeout=.2)
    assert result['status'] == 'failed' and result['timed_out']
    assert (tmp_path/'timeout/result.json').is_file()


def test_stage_source_mutation_cannot_report_pass(assigned_packet, tmp_path):
    packet, tid, home = assigned_packet
    test = home/'tests/test_local.py'
    test.write_text("from pathlib import Path\ndef test_mutation():\n    (Path(__file__).parents[1]/'generator.py').write_text('VALUE=99')\n")
    result = run_tests(packet, tid, tmp_path/'mutation', timeout=30)
    assert result['exit_code'] == 0 and result['status'] == 'failed'
    assert result['staged_source_drift'] == [f'generators/{tid}/generator.py']
    assert (home/'generator.py').read_text() == 'VALUE = 17\n'


def test_wrapper_routes_only_unregistered_assigned_public_tasks(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1]/'src/arcpuzzles/review_workspace_files/review.py'
    spec = importlib.util.spec_from_file_location('public_test_entry', path)
    entry = importlib.util.module_from_spec(spec); spec.loader.exec_module(entry)
    tid = 'public_eval_1234abcd'
    contract = {'task_id': tid, 'work_policy': {'schema': 'arcpuzzles-public-eval-creation-v1'},
                'repair_targets': [{'task_id': tid}]}
    (tmp_path/'ASSIGNMENT.json').write_text(json.dumps(contract))
    catalog = tmp_path/'repo/catalog/puzzles.jsonl'; catalog.parent.mkdir(parents=True); catalog.write_text('')
    monkeypatch.setattr(entry, 'WORK', tmp_path)
    monkeypatch.setattr(entry, 'manifest', lambda: {'generators': {tid: {}}})
    calls = []
    monkeypatch.setattr(entry.subprocess, 'run', lambda argv, **kw: calls.append(argv) or SimpleNamespace(returncode=0))
    args = ['task-tests', tid, '--timeout', '30', '--out', '../checks/test']
    assert entry.main(args) == 0
    assert 'arcpuzzles.review_public_task_tests' in calls[-1] and '--stage' not in calls[-1]
    catalog.write_text(json.dumps({'id': tid})+'\n')
    assert entry.main(args) == 0
    assert 'check' in calls[-1] and 'task_tests' in calls[-1]


@pytest.mark.parametrize('failed', [False, True])
def test_cli_summary_keeps_full_receipt_on_disk(assigned_packet, tmp_path, capsys, failed):
    from arcpuzzles.review_public_task_tests import main
    packet, tid, home = assigned_packet
    if failed:
        (home/'tests/test_local.py').write_text('def test_failure():\n    assert False\n')
    args = [tid, '--packet', str(packet), '--timeout', '30']
    out = tmp_path/'compact'
    assert main([*args, '--out', str(out)]) == int(failed)
    summary = json.loads(capsys.readouterr().out)
    full = json.loads((out/'result.json').read_text())
    assert 'source_binding' not in summary and full['source_binding']['files']
    assert summary['status'] == full['status']
    assert summary['result_path'] == str(out/'result.json')
    detailed = tmp_path/'detailed'
    assert main([*args, '--out', str(detailed), '--full-json']) == int(failed)
    assert json.loads(capsys.readouterr().out)['source_binding'] == full['source_binding']

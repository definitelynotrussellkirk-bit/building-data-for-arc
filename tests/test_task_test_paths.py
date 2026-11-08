from arcpuzzles.runtime import _task_test_import_diagnostics
import pytest


@pytest.mark.parametrize('source', [
    'from pathlib import Path\np = Path(__file__).resolve().parents[1] / "data/canonical/puzzles.jsonl"\n',
    'from pathlib import Path\nROOT = Path(__file__).resolve().parents[2]\np = ROOT / "data" / "canonical" / "puzzles.jsonl"\n'])
def test_unused_fixed_depth_canonical_path_is_actionable_warning(tmp_path, source):
    (tmp_path / 'test_task.py').write_text(source)
    messages = _task_test_import_diagnostics(tmp_path, ['test_task.py'])
    finding = next(m for m in messages if m['code'] == 'fixed_depth_canonical_path')
    assert finding['severity'] == 'warning'
    assert 'reviewer_support' in finding['message']


def test_portable_helper_and_unrelated_fixture_paths_are_not_warned(tmp_path):
    (tmp_path / 'test_task.py').write_text('from reviewer_support import find_root, canonical_path\n'
        'from pathlib import Path\np = canonical_path(find_root(__file__))\n'
        'q = Path(__file__).resolve().parents[1] / "fixtures/example.json"\n')
    assert _task_test_import_diagnostics(tmp_path, ['test_task.py']) == []


def test_missing_legacy_module_is_preflight_error(tmp_path):
    (tmp_path / 'test_task.py').write_text('from scripts.no_longer_shipped import _canonical_path\n')
    messages = _task_test_import_diagnostics(tmp_path, ['test_task.py'])
    assert messages[0]['severity'] == 'error'
    assert 'canonical_pairs' in messages[0]['message']


def test_missing_private_legacy_symbol_is_preflight_error(tmp_path):
    (tmp_path / 'scripts').mkdir()
    (tmp_path / 'scripts/helper.py').write_text('VALUE = 7\n')
    (tmp_path / 'test_task.py').write_text('from scripts.helper import _read_canonical\n')
    messages = _task_test_import_diagnostics(tmp_path, ['test_task.py'])
    assert messages[0]['severity'] == 'error'
    assert '_read_canonical' in messages[0]['message']


def test_task_relative_canonical_path_is_preflight_error(tmp_path):
    task = tmp_path / 'generators/x/tests/test_task.py'
    task.parent.mkdir(parents=True)
    task.write_text('from pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\n'
                    'DATA = ROOT / "data/canonical/puzzles.jsonl"\nDATA.read_text()\n')
    messages = _task_test_import_diagnostics(tmp_path, ['generators/x/tests'])
    assert messages[0]['severity'] == 'error'
    assert 'find_root' in messages[0]['message']


def test_valid_fixed_depth_canonical_path_remains_warning(tmp_path):
    data = tmp_path / 'data/canonical/puzzles.jsonl'
    data.parent.mkdir(parents=True); data.touch()
    task = tmp_path / 'tests/test_task.py'; task.parent.mkdir()
    task.write_text('from pathlib import Path\np = Path(__file__).resolve().parents[1] / "data/canonical/puzzles.jsonl"\n')
    messages = _task_test_import_diagnostics(tmp_path, ['tests'])
    assert messages[0]['severity'] == 'warning'


def test_optional_legacy_import_with_fallback_remains_warning(tmp_path):
    (tmp_path / 'test_task.py').write_text('try:\n from scripts.optional import _helper\n'
                                        'except ImportError:\n _helper = None\n')
    messages = _task_test_import_diagnostics(tmp_path, ['test_task.py'])
    assert messages[0]['severity'] == 'warning'


def test_task_parent_canonical_path_is_also_checked(tmp_path):
    (tmp_path / 'test_task.py').write_text('from pathlib import Path\n'
        'DATA = Path(__file__).parent / "data/canonical/puzzles.jsonl"\nDATA.read_text()\n')
    messages = _task_test_import_diagnostics(tmp_path, ['test_task.py'])
    assert messages and messages[0]['severity'] == 'error'


def test_portable_canonical_fallback_after_candidate_path_remains_warning(tmp_path):
    data = tmp_path / 'data/canonical/puzzles.jsonl'
    data.parent.mkdir(parents=True); data.touch()
    test = tmp_path / 'generators/x/tests/test_task.py'; test.parent.mkdir(parents=True)
    test.write_text('from pathlib import Path\nfrom reviewer_support import canonical_path, find_root\n'
                   'DATA = Path(__file__).resolve().parents[1] / "data/canonical/puzzles.jsonl"\n'
                   'if not DATA.is_file():\n DATA = canonical_path(find_root(__file__))\n')
    messages = _task_test_import_diagnostics(tmp_path, ['generators/x/tests'])
    assert messages and all(m['severity'] == 'warning' for m in messages)


def test_inline_missing_canonical_read_is_error(tmp_path):
    (tmp_path / 'test_task.py').write_text('from pathlib import Path\n'
        'data = (Path(__file__).parent / "data/canonical/puzzles.jsonl").read_text()\n')
    messages = _task_test_import_diagnostics(tmp_path, ['test_task.py'])
    assert messages and messages[0]['severity'] == 'error'


def test_guarded_missing_canonical_read_remains_warning(tmp_path):
    (tmp_path / 'test_task.py').write_text('from pathlib import Path\n'
        'DATA = Path(__file__).parent / "data/canonical/puzzles.jsonl"\n'
        'if DATA.is_file():\n data = DATA.read_text()\n')
    messages = _task_test_import_diagnostics(tmp_path, ['test_task.py'])
    assert messages and messages[0]['severity'] == 'warning'

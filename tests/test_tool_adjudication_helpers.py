"""Focused regressions for primitive-name severity and retained-check roots."""
import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    spec = importlib.util.spec_from_file_location(Path(relative).stem, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def runtime_imports(monkeypatch):
    # Use the real dependencies through the same scripts/runtime namespaces
    # as a staged check, without executing any generator or Racket program.
    package = types.ModuleType('scripts')
    package.__path__ = [str(ROOT / 'shared/tools')]
    monkeypatch.setitem(sys.modules, 'scripts', package)
    monkeypatch.syspath_prepend(str(ROOT / 'shared/runtime'))


def lint(tmp_path, body, extra=''):
    source = ('GENERATOR_ID="fixture"\nVERSION="1.0"\nTASK_ID="fixture"\n'
              'RULE_HASH="123456789abc"\nSUMMARY="fixture"\nINVARIANTS=["fixture"]\n'
              'AXES={"size": {"type": "int", "valid": "1..2"}}\ndef self_check(grid):\n    return []\n' + extra + '\n'
              'def generate(seed, sample_index, *, difficulty=None, **overrides):\n' + body)
    path = tmp_path / 'generator.py'
    path.write_text(source)
    return load('shared/tools/lint_generator.py').lint_generator(path)


def test_local_placement_records_do_not_block_lint(tmp_path):
    report = lint(tmp_path, '    objects = [(1, [[1]])]\n    objects.append((2, [[2]]))\n    return objects[0][1]\n')
    assert report.exit_code == 0, (report.errors, report.warnings)
    assert any('objects' in note and 'generate' in note for note in report.notes)


@pytest.mark.parametrize('body,extra', [
    ('    return objects([[1]])\n', ''),
    ('    def objects(grid):\n        return grid\n    return [[1]]\n', ''),
    ('    objects = lambda grid: grid\n    return [[1]]\n', ''),
    ('    objects = helper\n    return [[1]]\n', ''),
    ('    objects: object = helpers.labeler\n    return [[1]]\n', ''),
    ('    from helpers import objects\n    return [[1]]\n', ''),
    ('    objects = []\n    recolor = []\n    return [[1]]\n', ''),
    ('    return [[1]]\n', 'objects = []\n'),
    ('    global objects\n    objects = []\n    return [[1]]\n', ''),
    ('    return [[1]]\n', 'async def objects(grid):\n    return grid\n'),
])
def test_suspicious_primitive_contexts_still_warn(tmp_path, body, extra):
    report = lint(tmp_path, body, extra)
    assert any('objects' in warning for warning in report.warnings)
    assert report.exit_code == 1
    assert any('scope' in warning for warning in report.warnings if 'objects' in warning)


def test_separate_functions_do_not_form_a_primitive_cluster(tmp_path):
    report = lint(tmp_path, '    objects = []\n    return [[1]]\n',
                  'def helper():\n    recolor = []\n    return recolor\n')
    assert report.exit_code == 0, report.warnings


def library(root):
    ledger = root / 'shared/data/canonical/puzzles.jsonl'
    ledger.parent.mkdir(parents=True)
    ledger.write_text('')
    return root


def artifact(root, relative='checks/audit/task/probe.py'):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path


def test_find_root_from_retained_checks_ignores_cwd_and_env(tmp_path, monkeypatch):
    work = tmp_path / 'WORK'
    repo = library(work / 'repo')
    probe = artifact(work)
    elsewhere = library(tmp_path / 'elsewhere')
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv('ARCPUZZLES_HOME', str(elsewhere))
    assert load('shared/runtime/reviewer_support.py').find_root(probe) == repo


def test_nearest_copied_runtime_wins_over_workspace_repo(tmp_path):
    work = tmp_path / 'WORK'
    library(work / 'repo')
    runtime = library(work / 'checks/audit/runtime')
    probe = artifact(runtime, 'tests/probe.py')
    assert load('shared/runtime/reviewer_support.py').find_root(probe) == runtime


def test_find_root_does_not_search_arbitrary_siblings(tmp_path):
    library(tmp_path / 'repo')
    probe = artifact(tmp_path, 'unrelated/probe.py')
    with pytest.raises(FileNotFoundError):
        load('shared/runtime/reviewer_support.py').find_root(probe)


@pytest.mark.parametrize('escape', ['repo', 'ledger'])
def test_workspace_discovery_rejects_escaping_symlinks(tmp_path, escape):
    work = tmp_path / 'WORK'
    probe = artifact(work)
    external = library(tmp_path / 'external')
    if escape == 'repo':
        (work / 'repo').symlink_to(external, target_is_directory=True)
    else:
        ledger = work / 'repo/shared/data/canonical/puzzles.jsonl'
        ledger.parent.mkdir(parents=True)
        ledger.symlink_to(external / 'shared/data/canonical/puzzles.jsonl')
    with pytest.raises((ValueError, FileNotFoundError)):
        load('shared/runtime/reviewer_support.py').find_root(probe)


def test_find_root_from_repository_generator_uses_repository(tmp_path):
    work = tmp_path / 'WORK'
    repo = library(work / 'repo')
    probe = artifact(repo, 'generators/task/tests/test_task.py')
    assert load('shared/runtime/reviewer_support.py').find_root(probe) == repo


def test_workspace_repo_wins_over_outer_library(tmp_path):
    library(tmp_path)
    work = tmp_path / 'WORK'
    repo = library(work / 'repo')
    probe = artifact(work)
    assert load('shared/runtime/reviewer_support.py').find_root(probe) == repo

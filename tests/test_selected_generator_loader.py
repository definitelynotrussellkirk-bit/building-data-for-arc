"""Selected source imports must remain usable after repository/runtime relocation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


HELPER = Path(__file__).resolve().parents[1] / 'shared/runtime/reviewer_support.py'
TASK = 'aaaa00000001'
SOURCE = '''from __future__ import annotations
from dataclasses import dataclass
from puzzle_generators.base import VALUE
@dataclass
class Example:
    value: int = VALUE
def generate(seed, sample_index): return [[VALUE]]
'''


def tree(root, layout, *, value=7, task=TASK):
    ledger = root / ('shared/data/canonical/puzzles.jsonl' if layout == 'repo' else 'data/canonical/puzzles.jsonl')
    ledger.parent.mkdir(parents=True)
    ledger.write_text('{}\n')
    dependencies = root / ('shared/runtime' if layout == 'repo' else '')
    package = dependencies / 'puzzle_generators'
    package.mkdir(parents=True)
    (package / '__init__.py').write_text('')
    (package / 'base.py').write_text(f'VALUE = {value}\n')
    relative = f'generators/{task}/generator.py' if layout == 'repo' else f'puzzle_generators/per_puzzle/{task}/generator.py'
    source = root / relative
    source.parent.mkdir(parents=True)
    source.write_text(SOURCE)
    if layout == 'runtime':
        (root / 'RUNTIME_MANIFEST.json').write_text(json.dumps({'files': [
            {'library_path': f'generators/{task}/generator.py', 'runtime_path': relative,
             'sha256': hashlib.sha256(SOURCE.encode()).hexdigest()}]}))
    return source


def probe(tmp_path, code, *, helper=HELPER):
    bootstrap = f'''import importlib.util, json, os, sys
from pathlib import Path
os.environ.pop('ARCPUZZLES_HOME', None)
spec = importlib.util.spec_from_file_location('selected_support', {str(helper)!r})
support = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = support
spec.loader.exec_module(support)
'''
    process = subprocess.run([sys.executable, '-I', '-c', bootstrap + code], cwd=tmp_path,
                             capture_output=True, text=True, timeout=30)
    assert process.returncode == 0, process.stdout + process.stderr
    return json.loads(process.stdout)


@pytest.mark.parametrize('layout', ['repo', 'runtime'])
@pytest.mark.parametrize('task', [TASK, TASK + '_2'])
def test_loads_selected_tree_with_dataclasses_and_dependency_identity(tmp_path, layout, task):
    root = tmp_path / 'selected'; source = tree(root, layout, task=task)
    result = probe(tmp_path, f'''
before = list(sys.path)
module, path, digest = support.load_selected_generator({task!r}, root={str(root)!r})
print(json.dumps({{'grid': module.generate(1, 0), 'dataclass_value': module.Example().value,
                  'path': str(path), 'module_path': module.__file__, 'sha256': digest,
                  'path_restored': sys.path == before}}))
''')
    assert result == {'grid': [[7]], 'dataclass_value': 7, 'path': str(source),
                      'module_path': str(source), 'sha256': hashlib.sha256(SOURCE.encode()).hexdigest(),
                      'path_restored': True}


def test_explicit_root_wins_over_environment_and_current_directory(tmp_path):
    first = tmp_path / 'first'; second = tmp_path / 'second'
    source = tree(first, 'repo', value=7); tree(second, 'repo', value=9)
    result = probe(tmp_path, f'''
os.environ['ARCPUZZLES_HOME'] = {str(second)!r}
os.chdir({str(second)!r})
module, path, digest = support.load_selected_generator({TASK!r}, root={str(first)!r})
print(json.dumps({{'grid': module.generate(1, 0), 'path': str(path)}}))
''')
    assert result == {'grid': [[7]], 'path': str(source)}


def test_default_root_uses_explicit_library_environment(tmp_path):
    root = tmp_path / 'selected'; source = tree(root, 'repo')
    result = probe(tmp_path, f'''
os.environ['ARCPUZZLES_HOME'] = {str(root)!r}
module, path, digest = support.load_selected_generator({TASK!r})
print(json.dumps({{'grid': module.generate(1, 0), 'path': str(path)}}))
''')
    assert result == {'grid': [[7]], 'path': str(source)}


def test_copied_helper_defaults_to_its_own_runtime_without_environment(tmp_path):
    root = tmp_path / 'selected'; source = tree(root, 'runtime')
    helper = root / 'reviewer_support.py'; helper.write_bytes(HELPER.read_bytes())
    result = probe(tmp_path, f'''
module, path, digest = support.load_selected_generator({TASK!r})
print(json.dumps({{'grid': module.generate(1, 0), 'path': str(path)}}))
''', helper=helper)
    assert result == {'grid': [[7]], 'path': str(source)}


def test_repository_helper_defaults_to_repository_not_shared_data_root(tmp_path):
    root = tmp_path / 'selected'; source = tree(root, 'repo')
    helper = root / 'shared/runtime/reviewer_support.py'
    helper.write_bytes(HELPER.read_bytes())
    result = probe(tmp_path, f'''
module, path, digest = support.load_selected_generator({TASK!r})
print(json.dumps({{'grid': module.generate(1, 0), 'path': str(path)}}))
''', helper=helper)
    assert result == {'grid': [[7]], 'path': str(source)}


def test_rejects_dependencies_cached_from_a_different_tree(tmp_path):
    first = tmp_path / 'first'; second = tmp_path / 'second'
    tree(first, 'repo', value=7); tree(second, 'repo', value=9)
    result = probe(tmp_path, f'''
support.load_selected_generator({TASK!r}, root={str(first)!r})
try:
    support.load_selected_generator({TASK!r}, root={str(second)!r})
except ImportError as error:
    print(json.dumps({{'blocked': True, 'fresh_process': 'fresh process' in str(error)}}))
else:
    print(json.dumps({{'blocked': False}}))
''')
    assert result == {'blocked': True, 'fresh_process': True}


def test_loads_current_bytes_even_when_file_size_and_mtime_are_unchanged(tmp_path):
    root = tmp_path / 'selected'; source = tree(root, 'repo')
    replacement = SOURCE.replace('[[VALUE]]', '[[8    ]]')
    assert len(replacement) == len(SOURCE)
    result = probe(tmp_path, f'''
import hashlib
source = Path({str(source)!r})
support.load_selected_generator({TASK!r}, root={str(root)!r})
timestamp = source.stat().st_mtime_ns
source.write_text({replacement!r})
os.utime(source, ns=(timestamp, timestamp))
module, path, digest = support.load_selected_generator({TASK!r}, root={str(root)!r})
print(json.dumps({{'grid': module.generate(1, 0), 'sha256': digest}}))
''')
    assert result == {'grid': [[8]], 'sha256': hashlib.sha256(replacement.encode()).hexdigest()}


@pytest.mark.parametrize('task', ['../outside', '/absolute', '', 'missing'])
def test_missing_or_unsafe_task_never_borrows_another_source(tmp_path, task):
    root = tmp_path / 'selected'; tree(root, 'repo')
    result = probe(tmp_path, f'''
try:
    support.load_selected_generator({task!r}, root={str(root)!r})
except (ValueError, FileNotFoundError):
    print(json.dumps({{'blocked': True}}))
else:
    print(json.dumps({{'blocked': False}}))
''')
    assert result == {'blocked': True}


def test_runtime_requires_an_unambiguous_selected_mapping(tmp_path):
    root = tmp_path / 'selected'; tree(root, 'runtime')
    manifest = root / 'RUNTIME_MANIFEST.json'
    manifest.write_text(json.dumps({'files': []}))
    result = probe(tmp_path, f'''
try:
    support.load_selected_generator({TASK!r}, root={str(root)!r})
except FileNotFoundError:
    print(json.dumps({{'blocked': True}}))
else:
    print(json.dumps({{'blocked': False}}))
''')
    assert result == {'blocked': True}


def test_source_symlink_outside_selected_tree_is_rejected(tmp_path):
    root = tmp_path / 'selected'; source = tree(root, 'repo')
    outside = tmp_path / 'outside.py'; outside.write_text(SOURCE)
    source.unlink(); source.symlink_to(outside)
    result = probe(tmp_path, f'''
try:
    support.load_selected_generator({TASK!r}, root={str(root)!r})
except ValueError:
    print(json.dumps({{'blocked': True}}))
else:
    print(json.dumps({{'blocked': False}}))
''')
    assert result == {'blocked': True}


def test_generic_runtime_uses_selected_mapping_instead_of_a_guessed_path(tmp_path):
    root = tmp_path / 'selected'; task = 'generic_fixture_gen1'
    original = tree(root, 'runtime', task=task)
    relative = 'puzzle_generators/generic/concepts/fixture/gen1.py'
    source = root / relative; source.parent.mkdir(parents=True)
    original.rename(source)
    (root / 'RUNTIME_MANIFEST.json').write_text(json.dumps({'files': [
        {'library_path': f'generators/{task}/generator.py', 'runtime_path': relative}]}))
    result = probe(tmp_path, f'''
module, path, digest = support.load_selected_generator({task!r}, root={str(root)!r})
print(json.dumps({{'grid': module.generate(1, 0), 'path': str(path)}}))
''')
    assert result == {'grid': [[7]], 'path': str(source)}


def test_task_test_runtime_uses_its_selected_source_not_repository_mirrors(tmp_path):
    root = tmp_path / 'selected'; source = tree(root, 'runtime')
    mirror = root / f'generators/{TASK}/generator.py'
    mirror.parent.mkdir(parents=True); mirror.write_text(SOURCE)
    dependencies = root / 'shared/runtime/puzzle_generators'
    dependencies.mkdir(parents=True)
    (dependencies / '__init__.py').write_text('')
    (dependencies / 'base.py').write_text('VALUE = 9\n')
    p = root / 'RUNTIME_MANIFEST.json'; manifest = json.loads(p.read_text())
    manifest['files'].append({'library_path': f'generators/{TASK}/generator.py',
                              'runtime_path': f'generators/{TASK}/generator.py'})
    p.write_text(json.dumps(manifest))
    result = probe(tmp_path, f'''
sys.path.insert(0, {str(root)!r})
import puzzle_generators.base
module, path, digest = support.load_selected_generator({TASK!r}, root={str(root)!r})
print(json.dumps({{'grid': module.generate(1, 0), 'path': str(path)}}))
''')
    assert result == {'grid': [[7]], 'path': str(source)}


@pytest.mark.parametrize('case', ['identical', 'drift', 'unlisted', 'late_drift'])
def test_task_runtime_allows_only_source_bound_dependency_mirrors(tmp_path, case):
    root = tmp_path / 'selected'; source = tree(root, 'runtime')
    mirror = root / 'shared/runtime/puzzle_generators'
    mirror.mkdir(parents=True)
    (mirror / '__init__.py').write_text('')
    (mirror / 'base.py').write_text('VALUE = 7\n' if case == 'identical' else 'VALUE = 9\n')
    manifest_path = root / 'RUNTIME_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    if case != 'unlisted':
        for name in ('__init__.py', 'base.py'):
            primary = root / 'puzzle_generators' / name
            digest = hashlib.sha256(primary.read_bytes()).hexdigest()
            for path in (primary, mirror / name):
                manifest['files'].append({'library_path': f'shared/runtime/puzzle_generators/{name}',
                                          'runtime_path': path.relative_to(root).as_posix(),
                                          'sha256': digest})
    manifest_path.write_text(json.dumps(manifest))
    preload = 'import puzzle_generators' if case == 'late_drift' else 'import puzzle_generators.base'
    result = probe(tmp_path, f'''
sys.path.insert(0, {str(root / 'shared/runtime')!r})
{preload}
try:
    module, path, digest = support.load_selected_generator({TASK!r}, root={str(root)!r})
    print(json.dumps({{'grid': module.generate(1, 0), 'path': str(path)}}))
except ImportError:
    print(json.dumps({{'blocked': True}}))
''')
    assert result == ({'grid': [[7]], 'path': str(source)} if case == 'identical' else {'blocked': True})


@pytest.mark.parametrize('mapping', ['duplicate', 'escape'])
def test_runtime_rejects_ambiguous_or_escaping_mapping(tmp_path, mapping):
    root = tmp_path / 'selected'; tree(root, 'runtime')
    p = root / 'RUNTIME_MANIFEST.json'; manifest = json.loads(p.read_text())
    if mapping == 'duplicate':
        manifest['files'].append(dict(manifest['files'][0]))
    else:
        manifest['files'][0]['runtime_path'] = '../outside.py'
        (tmp_path / 'outside.py').write_text(SOURCE)
    p.write_text(json.dumps(manifest))
    result = probe(tmp_path, f'''
try:
    support.load_selected_generator({TASK!r}, root={str(root)!r})
except ValueError:
    print(json.dumps({{'blocked': True}}))
else:
    print(json.dumps({{'blocked': False}}))
''')
    assert result == {'blocked': True}


def test_failed_import_restores_path_and_removes_partial_generator_module(tmp_path):
    root = tmp_path / 'selected'; source = tree(root, 'repo')
    source.write_text(SOURCE + '\nraise RuntimeError("broken generator")\n')
    result = probe(tmp_path, f'''
before_path = list(sys.path)
before_modules = set(sys.modules)
try:
    support.load_selected_generator({TASK!r}, root={str(root)!r})
except RuntimeError as error:
    leftovers = [name for name in set(sys.modules) - before_modules
                 if name.startswith('_arcpuzzles_selected_')]
    print(json.dumps({{'error': str(error), 'leftovers': leftovers,
                      'path_restored': before_path == sys.path}}))
''')
    assert result == {'error': 'broken generator', 'leftovers': [], 'path_restored': True}

"""Explicit owner migrations preserve assertions, source bindings and frozen packets."""
import ast
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from arcpuzzles import Catalog, runtime

TASK = 'aaaa00000001'
SOURCE = '''"""Portable-test example — keep this docstring."""
from __future__ import annotations
from pathlib import Path
import importlib
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module("puzzle_generators.per_puzzle.aaaa00000001.generator")
def test_ledger():
    assert GEN.VERSION == "1.0.0"
    assert "aaaa00000001" in (ROOT / "data/canonical/puzzles.jsonl").read_text()
'''


def tool():
    from arcpuzzles import test_portability
    return test_portability


def source_file(library, text=SOURCE):
    path = library / f'generators/{TASK}/tests/test_portable.py'
    path.parent.mkdir(exist_ok=True)
    path.write_text(text)
    return path


def test_preview_keeps_source_and_assertions_and_apply_backs_up_original(library):
    path = source_file(library)
    before = path.read_bytes()
    plan = tool().plan_migration(library, TASK)
    assert path.read_bytes() == before
    assert len(plan['files']) == 1 and plan['manual_review'] == []
    assert plan['files'][0]['changes'] == ['canonical_path', 'selected_generator']
    assert 'canonical_path' in plan['files'][0]['patch']
    result = tool().apply_migration(library, plan)
    after = path.read_text()
    assert result['status'] == 'applied'
    assert (library / result['backup_directory'] / plan['files'][0]['path']).read_bytes() == before
    assert ast.get_docstring(ast.parse(after)) == ast.get_docstring(ast.parse(SOURCE))
    assert 'from __future__ import annotations' in after
    old_asserts = [ast.dump(n.test) for n in ast.walk(ast.parse(SOURCE)) if isinstance(n, ast.Assert)]
    new_asserts = [ast.dump(n.test) for n in ast.walk(ast.parse(after)) if isinstance(n, ast.Assert)]
    assert old_asserts[0] == new_asserts[0]
    assert 'assert "aaaa00000001" in ' in after
    assert 'ROOT = Path(__file__).resolve().parents[1]' in after  # unrelated root uses are untouched
    assert tool().plan_migration(library, TASK)['files'] == []


def test_saved_plan_rejects_changed_sources_or_tampered_patch(library):
    path = source_file(library)
    plan = tool().plan_migration(library, TASK)
    plan['files'][0]['patch'] += '\n# misleading display'
    with pytest.raises(ValueError, match='proposal'):
        tool().apply_migration(library, plan)
    plan = tool().plan_migration(library, TASK)
    path.write_text(SOURCE + '\n# new work\n')
    with pytest.raises(ValueError, match='source|proposal'):
        tool().apply_migration(library, plan)
    assert path.read_text().endswith('# new work\n')
    assert not (library / 'var/test-portability').exists()


def test_ambiguous_roots_private_imports_and_other_tasks_require_manual_review(library):
    path = source_file(library, '''from pathlib import Path
from scripts.missing import _read_canonical
ROOT = Path(__file__).parents[1]
ROOT = Path("/another/place")
DATA = ROOT / "data/canonical/puzzles.jsonl"
OTHER = Path("fixtures") / "data/canonical/puzzles.jsonl"
''')
    plan = tool().plan_migration(library, TASK)
    assert plan['files'] == []
    assert any(r['code'] == 'legacy_scripts_import' for r in plan['manual_review'])
    assert path.read_text().startswith('from pathlib')


def test_frozen_packet_and_symlink_sources_cannot_be_applied(library, tmp_path):
    path = source_file(library)
    plan = tool().plan_migration(library, TASK)
    (library.parent / 'PACKET-MANIFEST.json').write_text('{}')
    with pytest.raises(ValueError, match='issued|packet|frozen'):
        tool().apply_migration(library, plan)
    (library.parent / 'PACKET-MANIFEST.json').unlink()
    original = tmp_path / 'original.py'; original.write_text(SOURCE)
    path.unlink(); path.symlink_to(original)
    with pytest.raises(ValueError, match='symlink'):
        tool().plan_migration(library, TASK)
    assert original.read_text() == SOURCE


def test_relocated_runtime_runs_migrated_tests_without_owner_source(library, tmp_path):
    source_file(library)
    # The normal full library already maps this helper; add that mapping to the tiny fixture.
    owner = Path(__file__).resolve().parents[1]
    helper = library / 'shared/runtime/reviewer_support.py'
    helper.parent.mkdir(parents=True)
    shutil.copyfile(owner / 'shared/runtime/reviewer_support.py', helper)
    mapping = library / 'catalog/runtime_files.json'
    rows = json.loads(mapping.read_text())
    rows.append({'path': 'shared/runtime/reviewer_support.py', 'target': 'reviewer_support.py'})
    mapping.write_text(json.dumps(rows))
    before = runtime.check(Catalog(library), TASK, stage='task_tests', output=tmp_path / 'before')
    assert before['test_status'] == 'preflight_failed' and not before['passed']
    plan = tool().plan_migration(library, TASK)
    tool().apply_migration(library, plan)
    after = runtime.check(Catalog(library), TASK, stage='task_tests', output=tmp_path / 'after')
    assert after['passed'], after.get('stderr') or after.get('stdout')
    assert after['test_counts']['passed'] == 1
    assert after['runtime_path'] != str(library)
    assert after['test_import_diagnostics'] == []


def test_cli_previews_without_mutation_and_applies_saved_proposal(library, tmp_path, capsys):
    from arcpuzzles.cli import main
    path = source_file(library)
    proposal = tmp_path / 'proposal.json'
    assert main(['--library', str(library), 'review', 'migrate-tests', TASK, '--check', '--out', str(proposal)]) == 0
    assert path.read_text() == SOURCE
    assert main(['--library', str(library), 'review', 'migrate-tests', TASK, '--apply', str(proposal)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'applied'


def test_helper_import_precedes_edited_expression_even_with_late_import(library, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'shared/runtime'))
    path = source_file(library, '''from pathlib import Path
DATA = Path(__file__).parents[1] / "data/canonical/puzzles.jsonl"
import json
''')
    plan = tool().plan_migration(library, TASK)
    tool().apply_migration(library, plan)
    namespace = {'__file__': str(path)}
    exec(compile(path.read_bytes(), str(path), 'exec'), namespace)
    assert namespace['DATA'] == library / 'shared/data/canonical/puzzles.jsonl'


@pytest.mark.parametrize('binding', ['def Path(value): return value', 'import other as Path',
                                   'from other import Path', 'class Path: pass'])
def test_shadowed_path_binding_is_not_rewritten(library, binding):
    source_file(library, 'from pathlib import Path\n' + binding +
                '\nDATA = Path(__file__).parents[1] / "data/canonical/puzzles.jsonl"\n')
    assert tool().plan_migration(library, TASK)['files'] == []


def test_unrelated_canonical_file_and_function_shadow_are_not_rewritten(library):
    source_file(library, '''from pathlib import Path
ROOT = Path(__file__).parents[1]
def lookup(ROOT):
    return ROOT / "data/canonical/puzzles.jsonl"
OTHER = Path("fixtures") / "data/canonical/puzzles.jsonl"
''')
    assert tool().plan_migration(library, TASK)['files'] == []


def test_dynamic_generator_calls_are_not_changed_to_fresh_module_loads(library):
    source_file(library, '''import importlib
def get_generator():
    return importlib.import_module("puzzle_generators.per_puzzle.aaaa00000001.generator")
''')
    assert tool().plan_migration(library, TASK)['files'] == []


def test_generated_import_aliases_do_not_collide_with_function_parameters(library, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'shared/runtime'))
    path = source_file(library, '''from pathlib import Path
def data(_arc_review_root0):
    return Path(__file__).parents[1] / "data/canonical/puzzles.jsonl"
''')
    tool().apply_migration(library, tool().plan_migration(library, TASK))
    namespace = {'__file__': str(path)}
    exec(compile(path.read_bytes(), str(path), 'exec'), namespace)
    assert namespace['data'](None) == library / 'shared/data/canonical/puzzles.jsonl'


def test_cli_refuses_existing_result_path_before_applying(library, tmp_path, capsys):
    from arcpuzzles.cli import main
    path = source_file(library)
    proposal = tmp_path / 'proposal.json'; proposal.write_text(json.dumps(tool().plan_migration(library, TASK)))
    result = tmp_path / 'result.json'; result.write_text('retained evidence')
    assert main(['--library', str(library), 'review', 'migrate-tests', TASK,
                 '--apply', str(proposal), '--out', str(result)]) == 1
    assert path.read_text() == SOURCE
    assert result.read_text() == 'retained evidence'

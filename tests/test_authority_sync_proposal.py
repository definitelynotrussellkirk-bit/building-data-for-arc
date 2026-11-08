"""Dry-run remediation must preserve canonical and archival authority bytes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from arcpuzzles.catalog import Catalog
from arcpuzzles.cli import main

TASK = 'aaaa00000001'
RELATIVE = 'shared/data/base/solutions/training/fixture.json'
ROOT = Path(__file__).resolve().parents[1]


def _sources(library, selected='; old presentation\n( rule! g )', canonical='(rule! g)'):
    ledger = library / 'shared/data/canonical/puzzles.jsonl'
    rows = [json.loads(line) for line in ledger.read_text().splitlines()]
    rows[0]['program_solution'] = canonical
    ledger.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    file = library / RELATIVE
    file.parent.mkdir(parents=True, exist_ok=True)
    row = {'task_id': TASK, 'racket_target': {'target_code': selected,
           'raw_code': '(archival unmodified)', 'target_status': 'selected'},
           'unrelated': {'target': 'kept', 'array': [1, 2]}}
    file.write_text(json.dumps(row, indent=2))  # No final newline is valid JSON.
    (library / 'catalog/authority_files.json').write_text(json.dumps({RELATIVE[7:]: TASK}))
    return file


def proposal(library):
    from arcpuzzles.authority_sync import propose_selected_sync
    return propose_selected_sync(Catalog(library), TASK)


def snapshot(library):
    return {str(p.relative_to(library)): p.read_bytes()
            for p in library.rglob('*') if p.is_file()}


def test_proposal_is_readonly_and_patch_changes_only_selected_string(library):
    file = _sources(library)
    before = snapshot(library)
    result = proposal(library)
    assert snapshot(library) == before
    assert result['status'] == 'proposal' and result['applied'] is False
    assert result['canonical_rule_hash'] == hashlib.sha256(b'(rule! g)').hexdigest()[:12]
    assert result['roles']['source'] == 'canonical program_solution'
    assert result['roles']['preserved'] == 'archival raw_code'
    assert result['files'][0]['path'] == RELATIVE
    assert result['files'][0]['changed_json_pointers'] == ['/racket_target/target_code']
    assert result['files'][0]['old_sha256'] == hashlib.sha256(before[RELATIVE]).hexdigest()
    patch = library.parent / 'proposal.patch'; patch.write_text(result['patch'])
    run = subprocess.run(['git', 'apply', '--no-index', str(patch)], cwd=library,
                         capture_output=True, text=True, timeout=10)
    assert run.returncode == 0, run.stderr
    after = snapshot(library)
    assert {name for name in before if before[name] != after[name]} == {RELATIVE}
    expected = json.loads(before[RELATIVE]); expected['racket_target']['target_code'] = '(rule! g)'
    assert json.loads(file.read_text()) == expected
    assert result['files'][0]['new_sha256'] == hashlib.sha256(after[RELATIVE]).hexdigest()
    assert proposal(library)['status'] == 'already_synchronized'


def test_cli_writes_new_report_without_mutating_library(library, tmp_path, capsys):
    _sources(library); before = snapshot(library)
    out = tmp_path / 'proposal.json'
    assert main(['--library', str(library), 'authority-sync', 'old-first',
                 '--selected-only', '--out', str(out)]) == 0
    result = json.loads(out.read_text()); assert result['task_id'] == TASK
    assert snapshot(library) == before
    assert main(['--library', str(library), 'authority-sync', TASK,
                 '--selected-only', '--out', str(out)]) == 1
    assert 'exists' in capsys.readouterr().err.lower()


@pytest.mark.parametrize('source', ['(rule! different)', '(rule! "two  spaces")',
                                  '(rule! |escaped symbol|)', '(rule! #;(g) g)',
                                  '(rule! #\\space)', '(rule! #reader(foo))'])
def test_unsupported_or_semantically_different_text_is_refused(library, source):
    _sources(library, selected=source); before = snapshot(library)
    with pytest.raises(ValueError):
        proposal(library)
    assert snapshot(library) == before


def test_comment_whitespace_does_not_consume_the_following_tokens(library):
    _sources(library, selected='(rule!; presentation\n g)', canonical='(rule! g)')
    assert proposal(library)['status'] == 'proposal'
    _sources(library, selected='(rule!; hides g)\n)', canonical='(rule! g)')
    with pytest.raises(ValueError, match='tokens differ'):
        proposal(library)


def test_cr_ends_line_comment_and_cannot_hide_semantic_edit(library):
    _sources(library, selected='(rule! g); presentation\r(mutate!)')
    with pytest.raises(ValueError, match='tokens differ'):
        proposal(library)


def test_restricted_booleans_keywords_and_quote_are_supported(library):
    _sources(library, selected="( rule! '#t #:when #f )", canonical="(rule! '#t #:when #f)")
    assert proposal(library)['status'] == 'proposal'


def test_differently_formatted_canonical_sources_are_ambiguous(library):
    _sources(library)
    ledger = library / 'shared/data/canonical/puzzles.jsonl'
    row = json.loads(ledger.read_text().splitlines()[0]); row['program_solution'] = '( rule! g )'
    with ledger.open('a') as stream:
        stream.write(json.dumps(row) + '\n')
    with pytest.raises(ValueError, match='one exact canonical'):
        proposal(library)


@pytest.mark.parametrize('failure', ['duplicate_key', 'wrong_task', 'missing_target',
                                    'outside_path', 'external_symlink', 'no_selected'])
def test_malformed_or_unbound_selected_authority_is_refused(library, tmp_path, failure):
    file = _sources(library)
    if failure == 'duplicate_key':
        file.write_text(file.read_text().replace('"task_id":', '"task_id": "duplicate", "task_id":'))
    elif failure == 'wrong_task':
        file.write_text(file.read_text().replace(TASK, 'aaaa00000002'))
    elif failure == 'missing_target':
        row = json.loads(file.read_text()); del row['racket_target']['target_code']
        file.write_text(json.dumps(row))
    elif failure == 'outside_path':
        (library / 'catalog/authority_files.json').write_text(json.dumps({'../outside.json': TASK}))
    elif failure == 'external_symlink':
        other = tmp_path / 'outside.json'; other.write_bytes(file.read_bytes())
        file.unlink(); file.symlink_to(other)
    else:
        (library / 'catalog/authority_files.json').write_text('{}')
    before = snapshot(library)
    with pytest.raises(ValueError):
        proposal(library)
    assert snapshot(library) == before


def test_checker_names_roles_and_non_applying_next_step(library, monkeypatch):
    _sources(library)
    spec = importlib.util.spec_from_file_location('_sync_advice', ROOT / 'shared/tools/check_task_authority_sync.py')
    tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)
    monkeypatch.setattr(tool, 'ROOT', library / 'shared')
    monkeypatch.setattr(tool, 'CANONICAL', library / 'shared/data/canonical/puzzles.jsonl')
    monkeypatch.setattr(tool, 'BASE_SOLUTIONS', library / 'shared/data/base/solutions')
    result = tool.audit_task(TASK)
    advice = result['selected_sync_remediation']
    assert advice['applied'] is False
    assert advice['copy_from'] == 'canonical program_solution'
    assert advice['copy_to'] == 'selected racket_target.target_code'
    assert advice['preserve'] == 'archival racket_target.raw_code'
    assert advice['proposal_argv'] == ['arcpuzzles', 'authority-sync', TASK, '--selected-only']
    assert [c[4] for c in advice['verify_argv']] == ['authority_sync', 'rule_smoke']


def test_defect_lint_divergence_explains_source_direction(monkeypatch, tmp_path):
    import puzzle_generators.runner as runner
    monkeypatch.setattr(runner, '_load_rule', lambda _: ('(rule! other)', Path('fixture.json')))
    scripts = tmp_path / 'scripts'; scripts.mkdir()
    for name in ['generator_defect_lint.py', 'generator_module_loader.py']:
        shutil.copy2(ROOT / 'shared/tools' / name, scripts / name)
    monkeypatch.syspath_prepend(str(tmp_path))
    spec = importlib.util.spec_from_file_location('_sync_lint_advice', scripts / 'generator_defect_lint.py')
    tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)
    message, source = tool.probe_rule_source_parity(TASK, {TASK: '(rule! g)'})[0]
    assert source == '(rule! other)'
    assert 'preserving archival raw_code' in message
    assert f'arcpuzzles authority-sync {TASK} --selected-only' in message
    assert 'Semantic edits are refused' in message


def test_already_synchronized_strings_need_no_equivalence_claim(library):
    _sources(library, selected='(rule! "literal")', canonical='(rule! "literal")')
    result = proposal(library)
    assert result['status'] == 'already_synchronized' and result['patch'] == ''


def test_two_selected_files_with_one_bad_source_emit_no_partial_proposal(library):
    file = _sources(library)
    second = file.with_name('second.json')
    row = json.loads(file.read_text()); row['racket_target']['target_code'] = '(rule! different)'
    second.write_text(json.dumps(row))
    mapping = {RELATIVE[7:]: TASK, str(second.relative_to(library / 'shared')): TASK}
    (library / 'catalog/authority_files.json').write_text(json.dumps(mapping))
    before = snapshot(library)
    with pytest.raises(ValueError, match='tokens differ'):
        proposal(library)
    assert snapshot(library) == before

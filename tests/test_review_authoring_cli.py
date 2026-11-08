"""Authoring CLI output paths and concise execution counts stay evidence-bound."""
import hashlib
import json
import sys

import pytest

from arcpuzzles import parametric_promotion as native
from arcpuzzles import review_base_preflight as author
from arcpuzzles import review_witness as witness
from test_parametric_promotion import candidate, fake_execution
from test_review_base_preflight import unapprove
from test_review_witness import qualified, recipe
from test_review_sequential_replay import runtime


@pytest.mark.parametrize('action, expected', [
    ('build', 'new directory'), ('template', 'new recipe JSON file'),
    ('check', 'new replay JSON file'),
])
def test_witness_help_names_output_kind(action, expected, capsys):
    with pytest.raises(SystemExit) as result:
        witness.main([action, '--help'])
    assert result.value.code == 0
    help_text = capsys.readouterr().out
    assert expected in help_text
    assert ('--out-dir' in help_text) is (action == 'build')


@pytest.mark.parametrize('option', ['--out', '--out-dir'])
def test_witness_build_alias_preserves_file_layout_and_check(qualified, tmp_path, capsys, option):
    root, qualification = qualified
    draft = tmp_path/'recipe.json'
    draft.write_text(json.dumps(recipe()))
    out = tmp_path/'causal'
    common = ['--library', str(root)]
    assert witness.main(common + ['build', '--qualification', str(qualification),
        '--recipe', str(draft), option, str(out)]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed['witness_path'] == str(out/'witness.json')
    assert sorted(p.name for p in out.iterdir()) == ['replay.json', 'witness.json']
    original = (out/'witness.json').read_bytes()
    check = tmp_path/'checked.json'
    assert witness.main(common + ['check', '--qualification', str(qualification),
        '--witness', str(out/'witness.json'), '--out', str(check)]) == 0
    assert check.is_file() and (out/'witness.json').read_bytes() == original
    assert json.loads(check.read_text())['training_admitted'] is False


def test_base_preflight_summary_uses_execution_counts_without_rewriting_receipts(
        candidate, monkeypatch, capsys, tmp_path):
    catalog, tid, _ = candidate
    metadata = unapprove(catalog.root)
    before = metadata.read_bytes()
    monkeypatch.setattr(author, '_base_checks', lambda catalog, tid: {
        'status': 'passed', 'pairs': [1, 2, 3], 'generation': [[], []],
        'canonical_records_sha256': author._records_hash(catalog, tid)})
    monkeypatch.setattr(native, '_execute', fake_execution)
    out = tmp_path/'preflight'
    monkeypatch.setattr(sys, 'argv', ['review_base_preflight', tid,
        '--root', str(catalog.root), '--out', str(out)])
    author.main()
    printed = json.loads(capsys.readouterr().out)
    receipt = json.loads((out/'qualification.json').read_text())
    execution_bytes = (out/'execution.json').read_bytes()
    execution = json.loads(execution_bytes)
    assert printed['job_count'] == len(receipt['jobs']) == 4
    assert printed['settings_count'] == len(receipt['programs']) == 2
    assert printed['racket_evaluations'] == execution['racket_evaluations']
    assert printed['parametric_labelled_pairs'] == sum(
        len(e['train']) + len(e['test']) for e in execution['episodes'])
    assert printed['base_canonical_pairs'] == 3
    assert printed['protected_racket'] is True
    assert printed['owner_accepted'] is False and printed['training_admitted'] is False
    assert 'source_binding' not in printed and 'jobs' not in printed
    assert 'job_count' not in receipt
    assert hashlib.sha256(execution_bytes).hexdigest() == receipt['execution']['sha256']
    assert metadata.read_bytes() == before

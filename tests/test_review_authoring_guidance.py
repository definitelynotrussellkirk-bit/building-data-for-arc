"""Authoring hints do not fill causal claims or weaken output freshness."""
import json
import sys

import pytest

from arcpuzzles import review_base_preflight as author
from arcpuzzles import review_witness as witness
from test_parametric_promotion import candidate
from test_review_witness import qualified, recipe
from test_review_sequential_replay import runtime


def test_template_identity_example_is_guidance_until_authored_and_replayed(qualified, tmp_path):
    root, qualification = qualified
    draft_path = tmp_path/'recipe.json'
    witness.write_template(root, qualification, draft_path)
    draft = json.loads(draft_path.read_text())
    example = draft['syntax_examples']['identity']
    assert example['program'] == '(rule! (lambda (g) g))'
    assert 'not a causal claim' in example['limits']
    assert draft['cases'][0]['counterfactual_program'] == ''
    assert draft['cases'][0]['intermediate_value'] is None
    with pytest.raises(ValueError, match='Fill all four'):
        witness.build_witness(root, qualification, draft, tmp_path/'unfilled')
    assert not (tmp_path/'unfilled').exists()
    draft.update({key: recipe()[key] for key in witness.FIELDS})
    draft['cases'][0].update(counterfactual_program=example['program'],
                             intermediate_value={'order': 'reversed'}, ablation='skip_a')
    result = witness.build_witness(root, qualification, draft, tmp_path/'built')
    saved = json.loads((tmp_path/'built/witness.json').read_text())
    assert saved['cases'][0]['counterfactual_output'] == saved['cases'][0]['input']
    assert saved['cases'][0]['counterfactual_output'] != saved['cases'][0]['output']
    assert result['training_admitted'] is False
    assert result['replay']['evaluations'] == 2


def test_preflight_help_states_directory_must_not_exist(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['review_base_preflight', '--help'])
    with pytest.raises(SystemExit) as status:
        author.main()
    assert status.value.code == 0
    output = capsys.readouterr().out
    assert 'must not exist' in output and 'qualification.json' in output


def test_preflight_still_refuses_existing_empty_directory(tmp_path):
    out = tmp_path/'preflight'
    out.mkdir()
    with pytest.raises(FileExistsError):
        author.preflight(tmp_path, 'fixture', out)
    assert list(out.iterdir()) == []

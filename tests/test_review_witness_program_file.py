"""Hashed recipe files become self-contained witness program strings."""
from copy import deepcopy
import hashlib
import pytest
from arcpuzzles.review_witness import _cases


def fixture(root):
    raw = b'(rule! (lambda (g) g))\r\n'
    path = root / 'generators/task/workspace/alternate.rkt'
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    recipe = {'cases': [dict(episode_index=0, split='test', pair_index=0,
        counterfactual_program_path='generators/task/workspace/alternate.rkt',
        counterfactual_program_sha256=hashlib.sha256(raw).hexdigest(),
        intermediate_value=[[2, 1]], ablation='wrong_order')]}
    execution = {'episodes': [dict(settings={}, program='(rule! (flip-lr g))',
        train=[], test=[{'input': [[1, 2]], 'output': [[2, 1]]}])]}
    return raw, path, recipe, execution


def test_copies_exact_bytes_and_hash_then_no_longer_needs_file(tmp_path):
    raw, path, recipe, execution = fixture(tmp_path)
    cases = _cases(recipe, execution, root=tmp_path)
    path.unlink()
    assert cases[0]['counterfactual_program'].encode() == raw
    assert cases[0]['counterfactual_program_sha256'] == hashlib.sha256(raw).hexdigest()
    assert 'counterfactual_program_path' not in cases[0]


@pytest.mark.parametrize('change', ['hash', 'missing_hash', 'absolute', 'traversal', 'symlink', 'ambiguous', 'oversize', 'bad_utf8'])
def test_rejects_unbound_or_unsafe_program_files(tmp_path, change):
    raw, path, recipe, execution = fixture(tmp_path)
    case = recipe['cases'][0]
    if change == 'hash': case['counterfactual_program_sha256'] = '0' * 64
    if change == 'missing_hash': case.pop('counterfactual_program_sha256')
    if change == 'absolute': case['counterfactual_program_path'] = str(path)
    if change == 'traversal': case['counterfactual_program_path'] = '../outside.rkt'
    if change == 'symlink':
        saved = path.with_suffix('.saved'); path.rename(saved); path.symlink_to(saved)
    if change == 'ambiguous': case['counterfactual_program'] = '(rule! g)'
    if change in ('oversize', 'bad_utf8'):
        raw = b'x' * 100001 if change == 'oversize' else b'\xff'
        path.write_bytes(raw); case['counterfactual_program_sha256'] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError):
        _cases(recipe, execution, root=tmp_path)


from test_review_witness import qualified, recipe as witness_recipe
from test_parametric_promotion import candidate
from test_review_sequential_replay import runtime


def test_file_program_survives_source_deletion_and_protected_replay(qualified, tmp_path):
    from arcpuzzles.review_witness import build_witness, check_witness
    import json
    root, qualification = qualified
    draft = witness_recipe()
    raw = draft['cases'][0].pop('counterfactual_program').encode() + b'\r\n'
    path = root / 'alternate.rkt'; path.write_bytes(raw)
    draft['cases'][0].update(counterfactual_program_path='alternate.rkt',
        counterfactual_program_sha256=hashlib.sha256(raw).hexdigest())
    built = tmp_path / 'file-built'
    result = build_witness(root, qualification, draft, built)
    assert result['status'] == 'reviewer_replayed'
    path.unlink()
    witness = json.loads((built / 'witness.json').read_bytes())
    assert witness['cases'][0]['counterfactual_program'].encode() == raw
    result = check_witness(root, qualification, built / 'witness.json', tmp_path / 'file-replayed.json')
    assert result['status'] == 'reviewer_replayed'
    assert result['training_admitted'] is False

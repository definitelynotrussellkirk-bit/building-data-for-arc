"""Focused contract tests; installed beside the unchanged generator tests."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
PROTOTYPE = HERE.parents[1] / 'workspace/parametric/prototype.py'
if not PROTOTYPE.is_file():
    PROTOTYPE = HERE.with_name('parametric_shear.py')
spec = importlib.util.spec_from_file_location('parametric_shear_under_test', PROTOTYPE)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

@pytest.mark.parametrize('value', [True, False, 2.0, '3', None, 1, 5])
def test_exact_parameter_gate(value):
    with pytest.raises(ValueError):
        p.validate_parameter(value)

@pytest.mark.parametrize('kwargs', [dict(seed=True), dict(seed=-1), dict(seed=1.0),
    dict(n_demo=0), dict(n_demo=9), dict(n_demo=True), dict(n_demo=2.0),
    dict(n_query=0), dict(n_query=33), dict(n_query='4'), dict(input_seed=True),
    dict(timeout_ms=False), dict(timeout_ms=0)])
def test_requests_rejected_before_source_loading(monkeypatch, kwargs):
    def forbidden():
        raise AssertionError('source loaded before validation')
    monkeypatch.setattr(p, '_context', forbidden)
    request = dict(seed=10)
    request.update(kwargs)
    with pytest.raises(ValueError):
        p.make_episode(**request)

@pytest.fixture(scope='module')
def episodes():
    return [p.make_episode(17023, shear_start_rows=s, input_seed=42042) for s in p.SETTINGS]


def test_canonical_program_and_outputs(episodes):
    c = p._context()
    assert p.program_for(3) == c['canonical_program']
    assert c['generator'].RULE_HASH == '6de9bdaa4c45'
    from reviewer_support import canonical_pairs
    pairs = canonical_pairs(p.TASK_ID, root=c['root'], labeled_only=True)
    assert p.racket_outputs([v['input'] for v in pairs], p.program_for(3)) == [v['output'] for v in pairs]
    assert all(pair['output'] == c['generator'].rule_mirror(pair['input'])
               for pair in episodes[1]['train'] + episodes[1]['test'])


def test_shared_inputs_exact_counts_and_geometry(episodes):
    c = p._context()
    for e in episodes:
        assert len(e['train']) == 2 and len(e['test']) == 4
        grids = [v['input'] for v in e['train'] + e['test']]
        assert len({json.dumps(g) for g in grids}) == 6
        assert c['generator']._noncanonical_mask(grids[0])
        assert {c['generator'].observe_overrides(v['input'])['side'] for v in e['train']} == {'left', 'right'}
        assert {c['generator'].observe_overrides(v['input'])['patch_height'] for v in e['test']} >= {4, 10}
    assert [[v['input'] for v in e['train'] + e['test']] for e in episodes].count(
        [v['input'] for v in episodes[0]['train'] + episodes[0]['test']]) == 3
    for i in range(3):
        for j in range(i):
            assert all(a['output'] != b['output'] for a, b in zip(episodes[i]['test'], episodes[j]['test']))


def test_finite_demo_certificate_ignores_query_labels(episodes):
    e = episodes[0]
    cert = e['certificate']
    assert cert['scope'] == 'explicit finite candidate family only'
    assert cert['survivors'] == ['shear_start_rows=2']
    changed = deepcopy(e)
    changed['test'][0]['output'] = [[0]]
    assert p.certify(changed['train'], [v['input'] for v in changed['test']]) == cert
    assert all(not v for v in cert['per_query_disagreements'])


def test_public_bytes_privacy_and_sorted_names(episodes, tmp_path):
    out = tmp_path / 'batch'
    p.write_batch(reversed(episodes), out)
    from reviewer_support import public_challenge_bytes, public_challenge_id
    expected = sorted(public_challenge_id(e) for e in episodes)
    assert sorted(x.stem for x in (out/'public').iterdir()) == expected
    manifest = json.loads((out/'private/manifest.json').read_text())
    assert manifest['public_ids'] == expected
    for e in episodes:
        data = (out/'public'/f'{public_challenge_id(e)}.json').read_bytes()
        assert data == public_challenge_bytes(e)
        assert hashlib.sha256(data).hexdigest() == public_challenge_id(e)
        public = json.loads(data)
        assert set(public) == {'train', 'test'}
        assert all(set(q) == {'input'} for q in public['test'])
        assert all(set(d) == {'input','output'} for d in public['train'])


def test_duplicate_batch_fails_without_output(episodes, tmp_path):
    out = tmp_path/'duplicate'
    with pytest.raises(ValueError, match='duplicate'):
        p.write_batch([episodes[0], deepcopy(episodes[0])], out)
    assert not out.exists()

@pytest.mark.parametrize('attack', ['query_label', 'certificate', 'program', 'counts', 'input', 'identity'])
def test_writer_rejects_tampering(episodes, tmp_path, attack):
    e = deepcopy(episodes[0])
    if attack == 'query_label': e['test'][0]['output'][0][0] = 0
    elif attack == 'certificate': e['certificate']['survivors'] = []
    elif attack == 'program': e['program'] += '\n; forged'
    elif attack == 'counts': e['test'].pop()
    elif attack == 'input': e['train'][0]['input'][0][0] = 6
    elif attack == 'identity': e['generator_sha256'] = '0'*64
    out = tmp_path/attack
    with pytest.raises(ValueError): p.write_batch([e], out)
    assert not out.exists()


def test_sampler_exhaustion_is_bounded(monkeypatch):
    c = p._context()
    grid = c['generator'].generate(19, 1, side='left', patch_height=4)
    monkeypatch.setattr(c['generator'], 'generate', lambda *a, **k: deepcopy(grid))
    monkeypatch.setattr(p, '_context', lambda: c)
    with pytest.raises(RuntimeError, match='retry budget'):
        p.make_episode(9)


@pytest.mark.parametrize('bad_cell', [True, 1.0])
def test_certificate_rejects_noninteger_demonstration_outputs(episodes, bad_cell):
    demos = deepcopy(episodes[0]['train'])
    for row in demos[0]['output']:
        if 1 in row:
            row[row.index(1)] = bad_cell
            break
    with pytest.raises(ValueError):
        p.certify(demos, [pair['input'] for pair in episodes[0]['test']])


def test_nondefault_requested_counts():
    e = p.make_episode(17024, shear_start_rows=4, n_demo=1, n_query=2)
    assert len(e['train']) == 1 and len(e['test']) == 2
    assert len({json.dumps(v['input']) for v in e['train'] + e['test']}) == 3


def test_certificate_rejects_no_fit_and_query_changing_survivors():
    demos, queries = [dict(input=[[1]], output=[[5]])], [[[1]]]
    with pytest.raises(ValueError, match='no finite candidate'):
        p._certificate(demos, queries, {'wrong': [[[1]], [[1]]]})
    with pytest.raises(ValueError, match='query-changing survivors'):
        p._certificate(demos, queries,
                       {'a': [[[5]], [[5]]], 'b': [[[5]], [[6]]]})

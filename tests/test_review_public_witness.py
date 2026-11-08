"""Public authoring receipts can build witnesses without owner registration."""
from copy import deepcopy
import hashlib
import json

import pytest

from test_review_public_admission import public_source
from test_review_sequential_replay import runtime
from arcpuzzles.review_public_creation import preflight
from arcpuzzles.review_witness import _public_preflight, build_witness, check_witness, main


@pytest.fixture
def public_preflight(public_source, runtime, tmp_path):
    root, item, parent, program = public_source
    tid = item['task_id']; home = root/'generators'/tid
    (home/'workspace/public-parent.json').write_text(json.dumps(item))
    (home/'generator.py').write_text("RULE_TASK_ID='ee_1234abcd'\ndef generate(**kw):\n    return {'input': [[1, 2]]}\n")
    (home/'workspace/parametric/adapter.py').write_text(f'''
def program(settings):
    return '(rule! (flip-lr g))' if settings['reverse'] else {program!r}
def generate(seed, settings, demos, queries):
    pairs = [{{'input': [[i, 9]], 'output': [[9, i]] if settings['reverse'] else [[i, 9]]}}
             for i in range(demos + queries)]
    return {{'program_solution': program(settings), 'train': pairs[:demos], 'test': pairs[demos:]}}
''')
    out = tmp_path/'preflight'
    preflight(root, tid, out)
    return root, out/'preflight.json'


def recipe():
    return dict(step_a='Identify row order.', intermediate='The row order.',
                step_b='Return the identified ordering.', why_b_depends_on_a='Order changes final cells.',
                cases=[dict(episode_index=2, split='test', pair_index=0,
                            counterfactual_program='(rule! (lambda (g) g))',
                            intermediate_value={'ordering': 'input order'}, ablation='wrong_intermediate')])


def test_public_cli_template_and_real_protected_build_check(public_preflight, tmp_path):
    root, receipt = public_preflight
    catalog = root/'catalog/puzzles.jsonl'; old = catalog.read_bytes()
    assert main(['--library', str(root), 'template', '--public-preflight', str(receipt),
                 '--out', str(tmp_path/'recipe.json')]) == 0
    out = tmp_path/'witness'
    built = build_witness(root, receipt, recipe(), out, public_preflight=True)
    assert built['verification_status'] == 'authoring_preflight_not_owner_qualification'
    assert 'qualification_sha256' not in built and built['public_preflight_sha256']
    assert built['replay']['evaluations'] == 2 and built['owner_acceptance'] == 'not_performed'
    witness = json.loads((out/'witness.json').read_text())
    assert witness['cases'][0]['output'] == [[9, 2]]
    assert witness['cases'][0]['counterfactual_output'] == [[2, 9]]
    assert check_witness(root, receipt, out/'witness.json', tmp_path/'checked.json', public_preflight=True)['training_admitted'] is False
    assert catalog.read_bytes() == old
    with pytest.raises(ValueError, match='native qualified'):
        build_witness(root, receipt, recipe(), tmp_path/'wrong-mode')


@pytest.mark.parametrize('change', ['source', 'execution', 'originals', 'program_map', 'omitted_source', 'labels_bool', 'jobs'])
def test_public_receipt_drift_rejected(public_preflight, change):
    root, receipt = public_preflight
    q = json.loads(receipt.read_text())
    if change == 'source':
        (root/'generators'/q['task_id']/'generator.py').write_text('# changed')
    elif change in ('execution', 'originals', 'labels_bool'):
        name = 'original-pairs.json' if change == 'originals' else 'execution.json'
        path = receipt.with_name(name); evidence = json.loads(path.read_text())
        if change == 'originals':
            evidence['pairs'].pop()  # Even a rehashed incomplete original receipt fails.
        elif change == 'labels_bool':
            evidence['episodes'][0]['train'][0]['input'][0][0] = False
        else:
            evidence['episodes'][0]['program_solution'] += ')'
        path.write_text(json.dumps(evidence))
        q['evidence_sha256'][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    elif change == 'program_map':
        q['programs'][next(iter(q['programs']))] = '0'*64
    elif change == 'omitted_source':
        q['source_binding']['files'].pop()
    else:
        q['jobs'][0]['queries'] = True
    receipt.write_text(json.dumps(q))
    with pytest.raises(ValueError):
        _public_preflight(root, receipt)


def test_public_counterfactual_strictness_and_source_change_during_replay(public_preflight, tmp_path, monkeypatch):
    from arcpuzzles import review_witness
    root, receipt = public_preflight; draft = recipe()
    draft['cases'][0]['counterfactual_program'] += ')'
    with pytest.raises(ValueError, match='complete|delimiter'):
        build_witness(root, receipt, draft, tmp_path/'bad', public_preflight=True)
    original = review_witness.replay_witness
    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        (root/'generators/public_eval_1234abcd/generator.py').write_text('# drift')
        return result
    monkeypatch.setattr(review_witness, 'replay_witness', mutate)
    with pytest.raises(ValueError, match='source differs'):
        build_witness(root, receipt, recipe(), tmp_path/'changed', public_preflight=True)
    assert not (tmp_path/'changed').exists()

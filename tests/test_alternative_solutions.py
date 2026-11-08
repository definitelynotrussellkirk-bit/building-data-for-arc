"""Alternative answers are valid only for their exact ambiguous demonstrations."""
import copy
import hashlib
import json

import pytest

from arcpuzzles import alternative_solutions as alt


def candidate():
    return {'schema': alt.CANDIDATE, 'generator_id': 'example',
            'train': [{'input': [[1]], 'output': [[1]]},
                      {'input': [[2]], 'output': [[2]]}],
            'query': {'input': [[3]]},
            'hypotheses': [{'name': 'a', 'description': 'First rule', 'program': '(lambda (g) g)'},
                           {'name': 'b', 'description': 'Second rule', 'program': '(lambda (g) (list (list 4)))'}],
            'source_evidence': [{'path': 'generators/example/source.json', 'sha256': '0' * 64}],
            'lineage': {'family': 'example'}}


def certificate(c, outputs=None):
    return {'status': 'verified', 'candidate_sha256': alt.digest(c),
            'racket': {'backend': 'racket', 'protected': True},
            'evaluations': len(c['hypotheses']) * (len(c['train']) + 1),
            'hypotheses': [{'program_sha256': hashlib.sha256(h['program'].encode()).hexdigest(),
                            'train_outputs': [d['output'] for d in c['train']],
                            'query_output': (outputs or [[[3]], [[4]]])[i]}
                           for i, h in enumerate(c['hypotheses'])]}


def test_both_directions_and_private_target_invariance():
    c = candidate(); cert = certificate(c)
    rows = alt.examples(c, cert)
    assert len(rows) == 2
    assert {tuple(map(tuple, r['target'])) for r in rows} == {((3,),), ((4,),)}
    assert rows[0]['group_id'] == rows[1]['group_id']
    prompt = rows[0]['prompt']
    assert 'program' not in json.dumps(prompt)
    changed = copy.deepcopy(c); changed['hypotheses'][1]['description'] = 'Different private description'
    assert alt.examples(changed, certificate(changed))[0]['prompt_id'] == rows[0]['prompt_id']
    assert rows[0]['prompt_id'] == alt.digest(prompt)


def test_shared_public_prompt_keeps_multiple_acceptable_targets():
    c = candidate(); a = alt.examples(c, certificate(c))
    d = copy.deepcopy(c); d['hypotheses'][1]['description'] = 'Third rule'
    d['hypotheses'][1]['program'] = '(lambda (g) (list (list 5)))'
    b = alt.examples(d, certificate(d, [[[3]], [[5]]]))
    public, private, train = alt.combine(a + b)
    assert len(public) == 3
    assert len(train) == 4
    first = next(r for r in private if r['prompt_id'] == a[0]['prompt_id'])
    assert {tuple(map(tuple, t['output'])) for t in first['acceptable_targets']} == {((4,),), ((5,),)}
    assert len(alt.combine(a + a)[2]) == 2


@pytest.mark.parametrize('fault', ['demo', 'same_query', 'bool', 'program_hash', 'binding', 'unprotected'])
def test_bad_certificates_are_not_training_data(fault):
    c = candidate(); cert = certificate(c)
    if fault == 'demo': cert['hypotheses'][1]['train_outputs'][0] = [[9]]
    if fault == 'same_query': cert['hypotheses'][1]['query_output'] = [[3]]
    if fault == 'bool': cert['hypotheses'][1]['query_output'] = [[False]]
    if fault == 'program_hash': cert['hypotheses'][1]['program_sha256'] = '0' * 64
    if fault == 'binding': cert['candidate_sha256'] = '0' * 64
    if fault == 'unprotected': cert['racket']['protected'] = False
    with pytest.raises(ValueError): alt.examples(c, cert)


def test_sources_are_hash_bound_and_stay_inside_library(tmp_path):
    c = candidate(); p = tmp_path / c['source_evidence'][0]['path']
    p.parent.mkdir(parents=True); p.write_bytes(b'original')
    c['source_evidence'][0]['sha256'] = hashlib.sha256(b'original').hexdigest()
    alt.validate(c, tmp_path)
    p.write_bytes(b'changed')
    with pytest.raises(ValueError, match='source'): alt.validate(c, tmp_path)
    c['source_evidence'][0]['path'] = '../outside'
    with pytest.raises(ValueError, match='path'): alt.validate(c, tmp_path)


def test_publish_is_hash_bound_and_reader_refuses_corruption(tmp_path):
    c = candidate(); cert = certificate(c)
    result = alt.publish(tmp_path, alt.examples(c, cert), [{'candidate': c, 'certificate': cert}], [])
    rows = list(alt.iter_training_rows(tmp_path))
    assert len(rows) == 2
    assert result['counts']['public_prompts'] == 2
    assert alt.publish(tmp_path, alt.examples(c, cert), [{'candidate': c, 'certificate': cert}], []) == result
    path = tmp_path / 'snapshots' / result['snapshot_id'] / 'train.jsonl'
    path.write_text('{}\n')
    with pytest.raises(ValueError, match='hash'): list(alt.iter_training_rows(tmp_path))


def test_exact_demo_types_and_count_are_required():
    c = candidate(); c['train'][0]['output'] = [[True]]
    with pytest.raises(ValueError): alt.examples(c, certificate(c))
    c = candidate(); c['train'] = c['train'][:1]
    with pytest.raises(ValueError): alt.examples(c, certificate(c))

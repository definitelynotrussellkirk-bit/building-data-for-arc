"""Reviewer witness convenience keeps native source/schema/replay boundaries."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from arcpuzzles import parametric_promotion as promotion
from test_parametric_promotion import candidate
from test_review_sequential_replay import runtime


@pytest.fixture
def qualified(candidate, runtime, monkeypatch, tmp_path):
    catalog, tid, _ = candidate
    def fixture_execution(catalog, tid, contract, jobs, timeout):
        episodes = []; checks = []
        for job in jobs:
            program = '(rule! g)' if job['settings']['side'] == 'left' else '(rule! (flip-lr g))'
            pairs = [{'input': [[i, 9]], 'output': [[i, 9]] if job['settings']['side'] == 'left' else [[9, i]]}
                     for i in range(job['demos'] + job['queries'])]
            episodes.append(dict(task_id=tid, seed=job['seed'], settings=job['settings'],
                                 train=pairs[:job['demos']], test=pairs[job['demos']:],
                                 program=program, program_sha256=hashlib.sha256(program.encode()).hexdigest()))
            checks.append(dict(seed=job['seed'], settings=job['settings'], demos=job['demos'],
                               queries=job['queries'], survivors=[job['settings']],
                               label_count=job['demos'] + job['queries']))
        return dict(episodes=episodes, checks=checks, racket={'backend': 'racket', 'protected': True},
                    racket_evaluations=sum(j['demos'] + j['queries'] for j in jobs))
    # Synthetic qualification tests plumbing only. Witness execution below uses real protected Racket.
    with monkeypatch.context() as patch:
        patch.setattr(promotion, '_execute', fixture_execution)
        result = promotion.qualify(catalog, tid, tmp_path / 'qualification')
    return catalog.root, Path(result['receipt'])


def recipe():
    return dict(step_a='Identify row order.', intermediate='The row ordering.',
                step_b='Return the identified ordering.', why_b_depends_on_a='Changing the ordering changes final cells.',
                cases=[dict(episode_index=2, split='test', pair_index=0,
                            counterfactual_program='(rule! (lambda (g) g))',
                            intermediate_value={'ordering': 'input order'}, ablation='wrong_intermediate')])


def test_build_and_check_use_real_protected_replay(qualified, tmp_path):
    from arcpuzzles.review_witness import build_witness, check_witness
    root, qualification = qualified
    out = tmp_path / 'built'
    result = build_witness(root, qualification, recipe(), out)
    witness = json.loads((out / 'witness.json').read_text())
    assert witness['cases'][0]['output'] == [[9, 3]]
    assert witness['cases'][0]['counterfactual_output'] == [[3, 9]]
    assert witness['cases'][0]['settings'] == {'side': 'right'}
    assert result['status'] == 'reviewer_replayed'
    assert result['training_admitted'] is False
    assert result['source_binding'] == witness['source_binding']
    assert result['replay']['evaluations'] == 2
    checked = check_witness(root, qualification, out / 'witness.json', tmp_path / 'checked.json')
    assert checked['status'] == 'reviewer_replayed'


@pytest.mark.parametrize('change', ['same_output', 'program_error', 'bad_index', 'blank_description', 'bad_ablation'])
def test_invalid_recipe_leaves_no_output(qualified, tmp_path, change):
    from arcpuzzles.review_witness import build_witness
    root, qualification = qualified; draft = recipe()
    if change == 'same_output': draft['cases'][0]['counterfactual_program'] = '(rule! (flip-lr g))'
    elif change == 'program_error': draft['cases'][0]['counterfactual_program'] = '(rule! (/ 1 0))'
    elif change == 'bad_index': draft['cases'][0]['episode_index'] = True
    elif change == 'blank_description': draft['step_a'] = ' '
    else: draft['cases'][0]['ablation'] = 'not_an_ablation'
    with pytest.raises((ValueError, TypeError)):
        build_witness(root, qualification, draft, tmp_path / 'bad')
    assert not (tmp_path / 'bad').exists()


def test_changed_source_and_execution_rejected_before_output(qualified, tmp_path):
    from arcpuzzles.review_witness import build_witness
    root, qualification = qualified
    execution = qualification.with_name('execution.json')
    previous = execution.read_bytes(); execution.write_bytes(previous + b' ')
    with pytest.raises(ValueError, match='execution'):
        build_witness(root, qualification, recipe(), tmp_path / 'bad')
    execution.write_bytes(previous)
    (root / 'generators/aaaa00000001/workspace/parametric/adapter.py').write_text('# source changed\n')
    with pytest.raises(ValueError):
        build_witness(root, qualification, recipe(), tmp_path / 'bad')
    assert not (tmp_path / 'bad').exists()


def test_existing_outputs_preserved_and_template_is_only_draft(qualified, tmp_path):
    from arcpuzzles.review_witness import build_witness, write_template
    root, qualification = qualified
    draft = tmp_path / 'recipe.json'
    write_template(root, qualification, draft)
    value = json.loads(draft.read_text())
    assert 'source_binding' not in value and not value['cases'][0]['counterfactual_program']
    old = draft.read_bytes()
    with pytest.raises(FileExistsError): write_template(root, qualification, draft)
    assert draft.read_bytes() == old
    out = tmp_path / 'existing';out.mkdir();(out / 'keep.txt').write_text('keep')
    with pytest.raises(FileExistsError): build_witness(root, qualification, recipe(), out)
    assert (out / 'keep.txt').read_text() == 'keep'


def test_check_rejects_fabricated_labels_and_foreign_binding(qualified, tmp_path):
    from arcpuzzles.review_witness import build_witness, check_witness
    root, qualification = qualified
    build_witness(root, qualification, recipe(), tmp_path / 'built')
    original = json.loads((tmp_path / 'built/witness.json').read_text())
    witness = tmp_path / 'tampered.json'
    for change in ('labels', 'binding'):
        value = deepcopy(original)
        if change == 'labels': value['cases'][0]['output'] = [[1]]
        else: value['source_binding']['task_id'] = 'different'
        witness.write_text(json.dumps(value))
        with pytest.raises(ValueError):
            check_witness(root, qualification, witness, tmp_path / 'check.json')
        assert not (tmp_path / 'check.json').exists()


def test_invalid_timeout_and_source_change_during_replay_are_not_saved(qualified, tmp_path, monkeypatch):
    from arcpuzzles import review_witness
    root, qualification = qualified
    with pytest.raises(ValueError, match='Timeout'):
        review_witness.build_witness(root, qualification, recipe(), tmp_path / 'bad', timeout=float('nan'))
    original = review_witness.replay_witness
    def mutate_after_replay(*args, **kwargs):
        result = original(*args, **kwargs)
        adapter = root / 'generators/aaaa00000001/workspace/parametric/adapter.py'
        adapter.write_text('# changed while witness replayed\n')
        return result
    monkeypatch.setattr(review_witness, 'replay_witness', mutate_after_replay)
    with pytest.raises(ValueError):
        review_witness.build_witness(root, qualification, recipe(), tmp_path / 'bad')
    assert not (tmp_path / 'bad').exists()


def test_trailing_delimiter_is_rejected_by_builder_and_checker(qualified, tmp_path):
    from arcpuzzles.review_witness import build_witness, check_witness
    root, qualification = qualified
    draft = recipe(); draft['cases'][0]['counterfactual_program'] += ')'
    with pytest.raises(ValueError, match='complete|delimiter|Unexpected|unexpected'):
        build_witness(root, qualification, draft, tmp_path / 'bad-build')
    assert not (tmp_path / 'bad-build').exists()
    build_witness(root, qualification, recipe(), tmp_path / 'good')
    witness = json.loads((tmp_path / 'good/witness.json').read_text())
    witness['cases'][0]['counterfactual_program'] += ')'
    path = tmp_path / 'malformed.json';path.write_text(json.dumps(witness))
    with pytest.raises(ValueError, match='complete|delimiter|Unexpected|unexpected'):
        check_witness(root, qualification, path, tmp_path / 'bad-check.json')
    assert not (tmp_path / 'bad-check.json').exists()


def audited_case(qualification):
    episode = json.loads(qualification.with_name('execution.json').read_text())['episodes'][2]
    return dict(settings=episode['settings'], program=episode['program'],
                **episode['train'][1], counterfactual_program='(rule! (lambda (g) g))',
                intermediate_value={'ordering': 'input order'}, ablation='wrong_intermediate')


def test_template_matches_audited_demonstration_then_protected_build(qualified, tmp_path):
    from arcpuzzles.review_witness import main, build_witness
    root, qualification = qualified
    audited = tmp_path / 'audited.json'; audited.write_text(json.dumps(audited_case(qualification)))
    draft = tmp_path / 'draft.json'
    assert main(['--library', str(root), 'template', '--qualification', str(qualification),
                 '--match-case', str(audited), '--out', str(draft)]) == 0
    value = json.loads(draft.read_text()); selected = value['cases'][0]
    assert (selected['episode_index'], selected['split'], selected['pair_index']) == (2, 'train', 1)
    assert selected['counterfactual_program'] == '(rule! (lambda (g) g))'
    assert 'source_binding' not in value
    value.update({key: recipe()[key] for key in ('step_a', 'intermediate', 'step_b', 'why_b_depends_on_a')})
    result = build_witness(root, qualification, value, tmp_path / 'matched-build')
    assert result['replay']['evaluations'] == 2
    assert result['status'] == 'reviewer_replayed'


@pytest.mark.parametrize('field', ['settings', 'program', 'input', 'output', 'missing'])
def test_unmatched_audited_case_leaves_no_template(qualified, tmp_path, field):
    from arcpuzzles.review_witness import write_template
    root, qualification = qualified; case = audited_case(qualification)
    if field == 'missing': del case['settings']
    elif field == 'settings': case[field] = {'side': 'left'}
    elif field == 'program': case[field] += ' '
    elif field == 'input': case[field] = [[True, 9]]  # bool must not match integer 1
    else: case[field] = [[9, 2]]
    with pytest.raises(ValueError, match='requires|no exact'):
        write_template(root, qualification, tmp_path / 'absent.json', match_case=case)
    assert not (tmp_path / 'absent.json').exists()


def test_settings_template_uses_alternate_program_then_real_protected_build(qualified, tmp_path, monkeypatch):
    from arcpuzzles.review_witness import main, build_witness
    from arcpuzzles import Catalog
    root, prior = qualified
    # The common fixture's canonical (rule! g) is synthetic. Add a real,
    # nondefault identity branch to exercise two executable alternate programs.
    contract_path = root / 'generators/aaaa00000001/workspace/parametric/promotion.json'
    contract = json.loads(contract_path.read_text())
    contract['parameters']['side'].append('identity')
    contract_path.write_text(json.dumps(contract))
    old = json.loads(prior.with_name('execution.json').read_text())
    def execute(catalog, tid, contract, jobs, timeout):
        episodes, checks = [], []
        for job in jobs:
            source = old['episodes'][2 if job['settings']['side'] == 'right' else 0]
            episode = deepcopy(source)
            episode.update(settings=job['settings'], seed=job['seed'])
            if job['settings']['side'] == 'identity':
                episode['program'] = '(rule! (lambda (g) g))'
                episode['program_sha256'] = hashlib.sha256(episode['program'].encode()).hexdigest()
            episodes.append(episode)
            checks.append(dict(seed=job['seed'], settings=job['settings'], demos=job['demos'],
                               queries=job['queries'], survivors=[job['settings']],
                               label_count=job['demos'] + job['queries']))
        return dict(episodes=episodes, checks=checks, racket={'backend':'racket', 'protected':True},
                    racket_evaluations=sum(j['demos']+j['queries'] for j in jobs))
    with monkeypatch.context() as patch:
        patch.setattr(promotion, '_execute', execute)
        result = promotion.qualify(Catalog(root), 'aaaa00000001', tmp_path/'three-settings')
    qualification = Path(result['receipt']); out = tmp_path/'selected-draft.json'
    assert main(['--library', str(root), 'template', '--qualification', str(qualification),
                 '--settings', '{"side":"right"}', '--counterfactual-settings', '{"side":"identity"}',
                 '--out', str(out)]) == 0
    draft = json.loads(out.read_text())
    assert draft['cases'][0]['counterfactual_program'] == '(rule! (lambda (g) g))'
    assert draft['selected_counterfactual']['counterfactual_checked'] is False
    draft.update({key: recipe()[key] for key in ('step_a', 'intermediate', 'step_b', 'why_b_depends_on_a')})
    draft['cases'][0]['intermediate_value'] = {'ordering': 'input order'}
    result = build_witness(root, qualification, draft, tmp_path/'selected-built')
    assert result['status'] == 'reviewer_replayed'
    assert result['replay']['evaluations'] == 2

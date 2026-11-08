import json
import pytest
from arcpuzzles.host_dataset import export_host
from arcpuzzles.datasets import verify_dataset


def source(tmp_path):
    root = tmp_path/'raw'
    root.mkdir()
    task = {'train': [{'input': [[1]], 'output': [[2]]}],
            'test': [{'input': [[3]]}, {'input': [[4]]}]}
    (root/'arc-agi_training_challenges.json').write_text(json.dumps({'task-a': task}))
    (root/'arc-agi_training_solutions.json').write_text(json.dumps({'task-a': [[[5]], [[6]]]}))
    return root, task


def test_original_pairs_unchanged_and_answers_private(tmp_path):
    root, task = source(tmp_path)
    out = tmp_path/'export'
    manifest = export_host(root, out)
    public = json.loads((out/'public.jsonl').read_text())
    private = json.loads((out/'labels.private.jsonl').read_text())
    assert public['train'] == task['train'] and public['test'] == task['test']
    assert set(public) == {'episode_id', 'train', 'test'}
    assert private['test_outputs'] == [[[5]], [[6]]]
    assert manifest['generated'] is False and manifest['queries'] == 2
    assert verify_dataset(out) == manifest


def test_missing_host_answer_rejected_before_export(tmp_path):
    root, _ = source(tmp_path)
    (root/'arc-agi_training_solutions.json').write_text(json.dumps({'task-a': [[[5]]]}))
    with pytest.raises(ValueError, match='Every original query'):
        export_host(root, tmp_path/'export')
    assert not (tmp_path/'export').exists()


def test_all_public_keeps_original_split_and_four_private_sources(tmp_path):
    root, training_task = source(tmp_path)
    evaluation_task = {'train': [{'input': [[7]], 'output': [[8]]}],
                       'test': [{'input': [[9]]}]}
    (root/'arc-agi_evaluation_challenges.json').write_text(json.dumps({'task-b': evaluation_task}))
    (root/'arc-agi_evaluation_solutions.json').write_text(json.dumps({'task-b': [[[1]]]}))
    out = tmp_path/'all-public'
    manifest = export_host(root, out, all_public=True)
    public = [json.loads(line) for line in (out/'public.jsonl').read_text().splitlines()]
    private = [json.loads(line) for line in (out/'labels.private.jsonl').read_text().splitlines()]
    by_task = {label['task_id']: (row, label) for row, label in zip(public, private)}
    assert manifest['source_split'] == 'mixed_public'
    assert manifest['source_splits'] == {'training': 1, 'evaluation': 1}
    assert manifest['accepted_episodes'] == 2 and manifest['queries'] == 3
    assert set(manifest['source_sha256']) == {
        f'arc-agi_{split}_{kind}.json'
        for split in ('training', 'evaluation') for kind in ('challenges', 'solutions')}
    assert by_task['task-a'][0]['train'] == training_task['train']
    assert by_task['task-b'][0]['test'] == evaluation_task['test']
    assert by_task['task-a'][1]['provenance']['source_split'] == 'training'
    assert by_task['task-b'][1]['provenance']['source_split'] == 'evaluation'
    assert by_task['task-b'][1]['test_outputs'] == [[[1]]]
    assert all(set(row) == {'episode_id', 'train', 'test'} for row in public)
    assert len(list((out/'source.private').glob('*.json'))) == 4
    assert verify_dataset(out) == manifest


def test_all_public_rejects_overlapping_task_ids_before_export(tmp_path):
    root, training_task = source(tmp_path)
    (root/'arc-agi_evaluation_challenges.json').write_text(json.dumps({'task-a': training_task}))
    (root/'arc-agi_evaluation_solutions.json').write_text(json.dumps({'task-a': [[[5]], [[6]]]}))
    with pytest.raises(ValueError, match='overlap'):
        export_host(root, tmp_path/'all-public', all_public=True)
    assert not (tmp_path/'all-public').exists()

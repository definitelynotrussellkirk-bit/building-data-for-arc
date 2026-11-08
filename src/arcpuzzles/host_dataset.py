"""Export original host tasks without invoking generators."""
import argparse
import json
from pathlib import Path
import shutil

from .catalog import sha256
from .datasets import _identity, verify_dataset


def is_grid(value: object) -> bool:
    return (isinstance(value, list) and 1 <= len(value) <= 30
            and all(isinstance(row, list) and 1 <= len(row) <= 30 for row in value)
            and len({len(row) for row in value}) == 1
            and all(type(cell) is int and 0 <= cell <= 9 for row in value for cell in row))


def export_host(source: Path, output: Path, order_seed: int = 20260912,
                *, all_public: bool = False) -> dict:
    """Keep every original demonstration/query, with answers in a private file."""
    splits = ('training', 'evaluation') if all_public else ('training',)
    paths = {(split, kind): source / f'arc-agi_{split}_{kind}.json'
             for split in splits for kind in ('challenges', 'solutions')}
    source_rows = {}
    seen_task_ids = set()
    for split in splits:
        challenges = json.loads(paths[split, 'challenges'].read_text())
        solutions = json.loads(paths[split, 'solutions'].read_text())
        if not challenges or set(challenges) != set(solutions):
            raise ValueError(f'Host {split} challenge and solution IDs must match exactly')
        if seen_task_ids.intersection(challenges):
            raise ValueError('Original training and evaluation task IDs overlap')
        seen_task_ids.update(challenges)
        source_rows[split] = (challenges, solutions)
    hashes = {path.name: sha256(path) for path in paths.values()}
    public, private = [], []
    for split in splits:
        challenges, solutions = source_rows[split]
        for task_id, task in challenges.items():
            if set(task) != {'train', 'test'} or not task['train'] or not task['test']:
                raise ValueError('Original host task must contain train and test')
            if any(set(p) != {'input', 'output'} or not all(is_grid(g) for g in p.values()) for p in task['train']):
                raise ValueError('Invalid original demonstration')
            if any(set(p) != {'input'} or not is_grid(p['input']) for p in task['test']):
                raise ValueError('Query observations must contain input only')
            answers = solutions[task_id]
            if len(answers) != len(task['test']) or not all(is_grid(g) for g in answers):
                raise ValueError('Every original query must have one valid private answer')
            episode_id = _identity({'task_id': task_id, 'source_split': split, 'sources': hashes})
            public.append({'episode_id': episode_id, **task})
            private.append({'episode_id': episode_id, 'task_id': task_id, 'seed': None,
                            'test_outputs': answers, 'provenance': {
                                'generated': False, 'source_split': split,
                                'official_task_id': task_id, 'family': f'official:{split}:{task_id}',
                                'source_sha256': hashes}})
    public.sort(key=lambda row: _identity(['host-order', order_seed, row['episode_id']]))
    lookup = {r['episode_id']: r for r in private}
    private = [lookup[r['episode_id']] for r in public]
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in (('public.jsonl', public), ('labels.private.jsonl', private)):
        (output / name).write_text(''.join(json.dumps(row, separators=(',', ':')) + '\n' for row in rows))
    originals = output / 'source.private'
    originals.mkdir()
    for path in paths.values():
        shutil.copyfile(path, originals / path.name)
        if sha256(originals / path.name) != hashes[path.name]:
            raise ValueError('Host source changed during export')
    files = {p.relative_to(output).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha256(p)}
             for p in output.rglob('*') if p.is_file()}
    manifest = {'schema': 'arcpuzzles-dataset-v1', 'status': 'complete',
                'options': {'style': 'challenges', 'order_seed': order_seed},
                'generated': False, 'source_split': 'mixed_public' if all_public else 'training',
                'score_scope': 'host_queries',
                'accepted_episodes': len(public), 'queries': sum(len(r['test']) for r in public),
                'source_sha256': hashes, 'files': files, 'training_eligible': False}
    if all_public:
        manifest['source_splits'] = {split: len(source_rows[split][0]) for split in splits}
    manifest['dataset_id'] = _identity(manifest)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return verify_dataset(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--order-seed', type=int, default=20260912)
    parser.add_argument('--all-public', action='store_true',
                        help='Include original training and public-evaluation tasks with their source labels')
    args = parser.parse_args()
    print(json.dumps(export_host(args.source, args.out, args.order_seed,
                                 all_public=args.all_public), indent=2))

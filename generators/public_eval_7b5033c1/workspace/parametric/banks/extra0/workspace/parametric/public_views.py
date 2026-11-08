"""Controller-side single-query projection. Never give its private manifest to a model."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import random


def encoded(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')


def validate_grid(grid):
    """Reject non-ARC values before computing public identities or writing files."""
    if (type(grid) is not list or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
        or any(type(row) is not list or len(row) != len(grid[0])
               or any(type(v) is not int or not 0 <= v <= 9 for v in row)
               for row in grid)):
        raise ValueError('Invalid ARC integer grid')


def project(episode, presentation_seed, turns=4):
    if type(presentation_seed) is not int or not 0<=presentation_seed<2**63:
        raise ValueError('presentation_seed must be a nonnegative exact integer')
    if type(turns) is not int or not 1<=turns<=4:
        raise ValueError('turns must be an integer in 1..4')
    if len(episode.get('test',[]))!=4 or not 2<=len(episode.get('train',[]))<=6:
        raise ValueError('Projection requires the complete four-query bank and 2..6 demos')
    train=[{'input':copy.deepcopy(p['input']),'output':copy.deepcopy(p['output'])} for p in episode['train']]
    queries=[copy.deepcopy(p['input']) for p in episode['test']]
    for pair in train:
        validate_grid(pair['input']);validate_grid(pair['output'])
    for grid in queries:validate_grid(grid)
    all_inputs=[p['input'] for p in train]+queries
    if len({encoded(g) for g in all_inputs})!=len(all_inputs):
        raise ValueError('Duplicate demo/query inputs are not publishable')
    order=list(range(4))
    entropy=hashlib.sha256(f'public-presentation-v1:{presentation_seed}'.encode()).digest()
    random.Random(int.from_bytes(entropy,'big')).shuffle(order)
    # Shuffle the bank BEFORE truncation; total requested turns never influence order.
    return ([{'train':copy.deepcopy(train),'test':[{'input':queries[i]}]} for i in order[:turns]],order[:turns])



def export_batch(requests, destination):
    """Validate the entire batch before mutation; write one flat, sorted directory."""
    groups = []
    rows = []
    for episode, seed in requests:
        views, order = project(episode, seed, 4)
        group = []
        for view, source_index in zip(views, order):
            raw = encoded(view)
            identifier = hashlib.sha256(raw).hexdigest()
            rows.append((identifier, raw))
            group.append({'id': identifier, 'source_index': source_index})
        groups.append({'presentation_seed': seed, 'mapping': group})
    if not rows:
        raise ValueError('Cannot publish an empty batch')
    if len({i for i, raw in rows}) != len(rows):
        raise ValueError('Duplicate public challenges across batch')
    directory = Path(destination)
    if directory.exists():
        raise FileExistsError(directory)
    directory.mkdir(parents=True)
    for identifier, raw in sorted(rows):
        (directory/f'{identifier}.json').write_bytes(raw)
    return {'schema': 'task-local-private-public-batch-v1',
            'groups': groups, 'physical_creation_order': sorted(i for i, raw in rows),
            'visibility': 'Each file individually; this manifest and directory listing are controller-private.'}


def export(episode, destination, presentation_seed):
    batch = export_batch([(episode, presentation_seed)], destination)
    return {**batch['groups'][0],
            'physical_creation_order': batch['physical_creation_order'],
            'visibility': batch['visibility']}


def verify(directory, expected_ids=None):
    """Check exact visible bytes and shape. Does not re-execute labels or authenticate receipts."""
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError('Missing public directory')
    files = sorted(directory.iterdir())
    if not files or any(not p.is_file() or p.is_symlink() or p.suffix != '.json' for p in files):
        raise ValueError('Expected only regular public JSON files')
    actual_ids = [p.stem for p in files]
    if expected_ids is not None and sorted(expected_ids) != actual_ids:
        raise ValueError('Public file inventory mismatch')
    for path in files:
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != path.stem:
            raise ValueError('Public content hash mismatch')
        value = json.loads(raw)
        if type(value) is not dict or set(value) != {'train', 'test'}:
            raise ValueError('Unexpected public metadata')
        if (type(value['train']) is not list or not 2 <= len(value['train']) <= 6
            or type(value['test']) is not list or len(value['test']) != 1):
            raise ValueError('Public count mismatch')
        for pair in value['train']:
            if type(pair) is not dict or set(pair) != {'input', 'output'}:
                raise ValueError('Private demonstration fields')
            validate_grid(pair['input']); validate_grid(pair['output'])
        query = value['test'][0]
        if type(query) is not dict or set(query) != {'input'}:
            raise ValueError('Query output or metadata leaked')
        validate_grid(query['input'])
        inputs = [p['input'] for p in value['train']] + [query['input']]
        if len({encoded(g) for g in inputs}) != len(inputs):
            raise ValueError('Duplicate visible inputs')
        if raw != encoded(value):
            raise ValueError('Unexpected public serialization')
    return {'status': 'passed', 'files': len(files),
            'scope': 'Visible byte/hash/grid/isolation check only; not label replay.'}

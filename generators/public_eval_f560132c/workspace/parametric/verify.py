"""Source-bound audit, public projection, and causal replay for f560132c.

Run only after the public-creation preflight. This tool does not register,
qualify, approve, accept, or admit the family for training.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
ROOT = HOME.parents[1]

MODES = ('pack_only', 'highlight_hub')
RIVALS = {
    'pack_only': 'canonical.rkt',
    'highlight_hub': 'highlight_hub.rkt',
    'highlight_largest': 'highlight_largest.rkt',
    'highlight_key': 'highlight_key.rkt',
}
DESCRIPTIONS = {
    'step_a': 'Recover the disconnected pieces, keep the palette-bearing piece unrotated at the top-left, rotate the others, and exact-cover the output square into a complete piece-ID tiling.',
    'intermediate': 'The complete packed piece-ID grid together with its four-neighbor piece-adjacency graph and degree vector.',
    'step_b': 'Select the unique maximum-degree piece in the packed adjacency graph and recolor exactly that packed region to color 1.',
    'why_b_depends_on_a': 'Input component area and scatter location do not determine adjacency after packing. The full exact-cover placement must be known before the hub can be selected.',
}
COUNTERFACTUAL = 'highlight_largest.rkt'


def raw(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw(value))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_binding(root, binding):
    root = Path(root).resolve()
    for row in binding['files']:
        relative = Path(row['path'])
        path = root / relative
        if (relative.is_absolute() or '..' in relative.parts or path.is_symlink()
                or not path.is_file() or not path.resolve().is_relative_to(root)
                or sha(path) != row['sha256']):
            raise ValueError('Source binding differs: ' + str(relative))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def changed_cells(a, b):
    if len(a) != len(b) or any(len(x) != len(y) for x, y in zip(a, b)):
        raise ValueError('Cannot compare different output shapes')
    return sum(x != y for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def intermediate(prototype, grid):
    data = prototype.decode(grid)
    owner = data['owner']
    return {
        'output_side': data['side'],
        'piece_id_grid': owner,
        'piece_id_grid_sha256': hashlib.sha256(raw(owner)).hexdigest(),
        'piece_areas': list(data['areas']),
        'adjacency': [sorted(values) for values in data['adjacency']],
        'degrees': list(data['degrees']),
        'hub_piece': data['hub_piece'],
        'largest_piece': data['largest_piece'],
    }


def semantic_failures(adapter, prototype, seed, mode, demos):
    episode = adapter.generate(seed, {'finish_rule': mode}, demos, 4)
    failures = []
    for rival in RIVALS:
        if rival == mode:
            continue
        fits = all(prototype.solve(pair['input'], rival) == pair['output'] for pair in episode['train'])
        if not fits:
            continue
        changes_query = any(prototype.solve(pair['input'], rival) != pair['output'] for pair in episode['test'])
        if changes_query:
            failures.append(rival)
    return episode, failures


def verify(preflight_path, out, seeds):
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
    from arcpuzzles.review_witness import _validate_programs
    from arcpuzzles.review_sequential_replay import replay_witness
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from reviewer_support import public_challenge_bytes

    preflight_path = Path(preflight_path).resolve()
    out = Path(out).resolve()
    if out.exists():
        raise ValueError('Choose a fresh audit output directory')
    qualification = json.loads(preflight_path.read_bytes())
    if qualification.get('status') != 'passed' or qualification.get('owner_accepted') is not False:
        raise ValueError('Expected a passing unapproved authoring preflight')
    check_binding(ROOT, qualification['source_binding'])
    for name, digest in qualification['evidence_sha256'].items():
        if sha(preflight_path.parent / name) != digest:
            raise ValueError('Preflight evidence hash differs: ' + name)

    adapter = load('_f560132c_audit_adapter', HERE / 'adapter.py')
    # Reuse the adapter's source-local prototype module so decoded exact-cover
    # intermediates are shared across generation and all semantic rivals.
    prototype = adapter.P

    episodes = 0
    semantic_checks = 0
    failures = []
    dimensions = set()
    orders = set()
    input_hashes = set()
    large = 0
    for seed in range(seeds):
        for mode in MODES:
            for demos in (2, 3, 6):
                episode, surviving = semantic_failures(adapter, prototype, seed, mode, demos)
                episodes += 1
                semantic_checks += len(RIVALS) - 1
                if surviving:
                    failures.append({
                        'seed': seed,
                        'finish_rule': mode,
                        'demos': demos,
                        'harmful_demo_survivors': surviving,
                    })
                inputs = [pair['input'] for split in ('train', 'test') for pair in episode[split]]
                fingerprints = [hashlib.sha256(raw(grid)).hexdigest() for grid in inputs]
                if len(fingerprints) != len(set(fingerprints)):
                    raise ValueError('Duplicate input inside episode')
                input_hashes.update(fingerprints)
                orders.add(tuple(episode['query_source_indices']))
                for grid in inputs:
                    if prototype.self_check(grid):
                        raise ValueError('Generated scene violates grammar')
                    dimensions.add((len(grid), len(grid[0])))
                    if len(grid) == len(grid[0]) == 30:
                        large += 1

    out.mkdir(parents=True)
    report = {
        'schema': 'arcpuzzles-task-authoring-audit-v1',
        'task_id': HOME.name,
        'status': 'failed' if failures else 'passed',
        'source_binding': qualification['source_binding'],
        'preflight_sha256': sha(preflight_path),
        'finite_seeds': seeds,
        'episodes': episodes,
        'semantic_rival_checks': semantic_checks,
        'declared_programs': list(RIVALS),
        'failures': failures,
        'distinct_inputs': len(input_hashes),
        'input_dimensions': sorted(dimensions),
        'distinct_presentation_orders': len(orders),
        'large_30x30_instances': large,
        'limits': 'Finite declared semantic rivals and sampled seeds only; not universal uniqueness, owner qualification, acceptance, or training admission.',
    }
    write(out / 'audit.json', report)
    if failures:
        raise ValueError(f'{len(failures)} ambiguous lessons; see audit.json')

    execution = json.loads((preflight_path.parent / 'execution.json').read_bytes())
    public_rows = []
    seen = set()
    mutations = 0
    positive = 0
    for episode_index, episode in enumerate(execution['episodes']):
        for query_index in range(len(episode['test'])):
            data = adapter.public_bytes(episode, query_index)
            visible = json.loads(data)
            if data != public_challenge_bytes(visible):
                raise ValueError('Wrong canonical public encoding')
            if (set(visible) != {'train', 'test'} or len(visible['test']) != 1
                    or set(visible['test'][0]) != {'input'}):
                raise ValueError('Public field leak')
            identifier = hashlib.sha256(data).hexdigest()
            if identifier in seen:
                raise ValueError('Duplicate public view')
            seen.add(identifier)
            (out / 'public').mkdir(exist_ok=True)
            (out / 'public' / f'{identifier}.json').write_bytes(data)
            public_rows.append({
                'episode_index': episode_index,
                'query_index': query_index,
                'source_index': episode['query_source_indices'][query_index],
                'public_id': identifier,
            })

        first = adapter.public_bytes(episode, 0)
        variants = []
        private = copy.deepcopy(episode)
        private['program_solution'] = 'PRIVATE'
        private['settings'] = {'private': True}
        private['seed'] = -9
        private['query_source_indices'] = ['PRIVATE']
        variants.append(private)
        private = copy.deepcopy(episode)
        for pair in private['test']:
            pair['output'] = {'private': 'not a grid'}
        variants.append(private)
        private = copy.deepcopy(episode)
        for pair in private['test']:
            pair.pop('output', None)
        variants.append(private)
        private = copy.deepcopy(episode)
        private['test'][1:] = [{'private': 'invalid future'}]
        variants.append(private)
        private = copy.deepcopy(episode)
        private['test'] = private['test'][:1]
        variants.append(private)
        for variant in variants:
            if adapter.public_bytes(variant, 0) != first:
                raise ValueError('Private metadata changes visible bytes')
            mutations += 1
        visible_change = copy.deepcopy(episode)
        visible_change['test'][0]['input'][0][0] = (visible_change['test'][0]['input'][0][0] + 1) % 10
        if adapter.public_bytes(visible_change, 0) == first:
            raise ValueError('Visible-input positive control failed')
        positive += 1

    write(out / 'public-projection.json', {
        'status': 'passed',
        'views': public_rows,
        'private_mutation_checks': mutations,
        'positive_controls': positive,
        'directory_is_controller_private': True,
    })

    programs = {name: (HERE / filename).read_text() for name, filename in RIVALS.items()}
    protected_evaluations = 0
    protected_survivors = []
    case = None
    with _local_imports(ROOT / 'shared/runtime', HERE):
        _validate_programs([{'program': program, 'counterfactual_program': program}
                            for program in programs.values()])
        apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
        try:
            # Execute selected programs and declared rivals through protected
            # Racket on a bounded but diverse set. The broad seed sweep above
            # remains Python-mirror based for tractable authoring latency.
            for seed in (0, 5, 17, 43):
                for mode in MODES:
                    episode = adapter.generate(seed, {'finish_rule': mode}, 2, 4)
                    selected = programs[mode]
                    for split in ('train', 'test'):
                        for pair in episode[split]:
                            actual = _grid(apply(selected, pair['input']))
                            protected_evaluations += 1
                            if actual != pair['output']:
                                raise ValueError(f'Protected Racket parity failed: {seed} {mode} {split}')
                    for rival, program in programs.items():
                        if rival == mode:
                            continue
                        fits = True
                        for pair in episode['train']:
                            actual = _grid(apply(program, pair['input']))
                            protected_evaluations += 1
                            if actual != pair['output']:
                                fits = False
                                break
                        if fits:
                            changes = False
                            for pair in episode['test']:
                                actual = _grid(apply(program, pair['input']))
                                protected_evaluations += 1
                                if actual != pair['output']:
                                    changes = True
                                    break
                            if changes:
                                protected_survivors.append({'seed': seed, 'finish_rule': mode, 'rival': rival})

            # Bind the causal witness to an exact preflight-generated 30x30
            # input, the selected Racket source, and the wrong-intermediate
            # Racket source.
            for episode in execution['episodes']:
                if episode['settings'].get('finish_rule') != 'highlight_hub':
                    continue
                for pair in episode['test']:
                    if len(pair['input']) != 30 or len(pair['input'][0]) != 30:
                        continue
                    counterfactual = _grid(apply(programs['highlight_largest'], pair['input']))
                    protected_evaluations += 1
                    if counterfactual == pair['output']:
                        continue
                    actual = _grid(apply(episode['program_solution'], pair['input']))
                    protected_evaluations += 1
                    if actual != pair['output']:
                        raise ValueError('Witness selected program differs from retained label')
                    case = {
                        'input': pair['input'],
                        'settings': episode['settings'],
                        'program': episode['program_solution'],
                        'output': actual,
                        'counterfactual_program': programs['highlight_largest'],
                        'counterfactual_output': counterfactual,
                        'intermediate_value': intermediate(prototype, pair['input']),
                        'ablation': 'wrong_intermediate',
                    }
                    break
                if case:
                    break
        finally:
            bridge.close()

    if protected_survivors:
        write(out / 'protected-survivors.json', protected_survivors)
        raise ValueError(f'{len(protected_survivors)} protected-Racket harmful rivals survived')
    if case is None:
        raise ValueError('No substantive changing 30x30 causal witness')

    witness = {
        'schema': 'arcpuzzles-sequential-dependency-witness-v1',
        'source_binding': qualification['source_binding'],
        **DESCRIPTIONS,
        'racket': {'backend': 'racket', 'protected': True},
        'cases': [case],
        'limits': 'Authoring witness for an unregistered family; no owner qualification or acceptance.',
    }
    progress = {'sequential_dependency': {**DESCRIPTIONS, 'witness_path': 'witness.json'}}
    static = validate_sequential_witness(progress, qualification, lambda _: raw(witness))
    replay = replay_witness(ROOT, witness, timeout=60)
    replay['status'] = 'reviewer_replayed'
    changed = changed_cells(case['output'], case['counterfactual_output'])
    write(out / 'causal' / 'witness.json', witness)
    write(out / 'causal' / 'replay.json', {
        'status': 'reviewer_replayed',
        'static_binding': static,
        'replay': replay,
        'changed_cells': changed,
        'preflight_sha256': sha(preflight_path),
        'owner_accepted': False,
        'training_admitted': False,
    })

    check_binding(ROOT, qualification['source_binding'])
    report.update({
        'protected_racket_evaluations': protected_evaluations,
        'racket': identity,
        'protected_harmful_survivors': 0,
        'causal_replay_evaluations': replay['evaluations'],
        'causal_changed_cells': changed,
        'public_views': len(public_rows),
        'private_mutation_checks': mutations,
    })
    write(out / 'audit.json', report)
    return {key: value for key, value in report.items()
            if key not in ('source_binding', 'input_dimensions', 'racket')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--seeds', type=int, default=32)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 256:
        parser.error('--seeds must be 1..256')
    print(json.dumps(verify(args.preflight, args.out, args.seeds), sort_keys=True))


if __name__ == '__main__':
    main()

"""Task-local, unapproved parametric prototype and finite-rival evidence CLI.

Outputs are executed with the selected Racket bridge. The Python functions are
independent diagnostic predictions, never the source of example labels.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
# Bootstrap only from this file's ancestors, never cwd or a predecessor tree.
for ancestor in HERE.parents:
    candidates = (ancestor / 'shared/runtime', ancestor)
    found = next((p for p in candidates if (p / 'reviewer_support.py').is_file()), None)
    if found is not None:
        sys.path.insert(0, str(found))
        break
else:
    raise ImportError('No local reviewer_support helper in this source tree')
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

REPO = find_root(HERE)
RUNTIME = REPO / 'shared/runtime' if (REPO / 'shared/runtime').is_dir() else REPO

TASK_ID = '5bba6e671cec'
FRAME = frozenset((4, 7))


@dataclass(frozen=True)
class Setting:
    direction: str = 'cw'
    steps: int = 1

    def __post_init__(self):
        if self.direction not in ('cw', 'ccw') or type(self.steps) is not int or self.steps not in (1, 2):
            raise ValueError('direction must be cw|ccw and steps must be integer 1|2')

    @property
    def key(self):
        return f'{self.direction}{self.steps}'

    @property
    def offset(self):
        return self.steps if self.direction == 'cw' else -self.steps


DEFAULT = Setting()
SETTINGS = tuple(Setting(d, s) for d in ('cw', 'ccw') for s in (1, 2))


def digest(value):
    if not isinstance(value, bytes):
        value = value.encode() if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(value).hexdigest()


@lru_cache(maxsize=1)
def selected_generator():
    return load_selected_generator(TASK_ID, root=REPO)


def generator():
    return selected_generator()[0]


@lru_cache(maxsize=1)
def canonical_rule():
    rules = set()
    for line in canonical_path(REPO).read_text().splitlines():
        if TASK_ID in line:
            row = json.loads(line)
            if row.get('task_id') == TASK_ID:
                rules.add(row['program_solution'])
    if len(rules) != 1:
        raise ValueError('Expected one unambiguous canonical Racket authority')
    return rules.pop()


def instantiate_rule(setting=DEFAULT):
    if not isinstance(setting, Setting):
        raise ValueError('Expected a validated Setting')
    source = canonical_rule()
    site = '(modulo (+ i 1) n)'
    if source.count(site) != 1:
        raise ValueError('Canonical mapping site changed; re-review this prototype')
    if setting == DEFAULT:
        return source  # Exact authority bytes, including formatting.
    return source.replace(site, f'(modulo (+ i {setting.offset}) n)')


def choose_setting(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    # A fixed hash avoids dependence on the input RNG and Python hash randomization.
    index = int(digest(f'{TASK_ID}:parametric-rule-v1:{seed}')[:16], 16) % len(SETTINGS)
    return SETTINGS[index]


def seed_for_setting(base_seed, setting):
    """Bounded, reproducible strata of seed-selected episodes for the audit."""
    if type(base_seed) is not int:
        raise ValueError('base seed must be an integer')
    for seed in range(base_seed * 1024, (base_seed + 1) * 1024):
        if choose_setting(seed) == setting:
            return seed
    raise ValueError('No matching seed in the declared 1024-seed stratum')


def evaluate(bridge, program, grid):
    grid = normalize_grid(grid)
    datum = '(' + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
    return normalize_grid(bridge.eval_text(f"({strip_rule_wrapper(program)} '{datum})"))


def predict(grid, setting=DEFAULT, *, mode='pixels', excluded=FRAME):
    """Diagnostic mirror; all cells of a color are treated as one region."""
    grid = normalize_grid(grid)
    order = generator()._ordered_colors(grid, mode=mode, excluded=excluded)
    if not order:
        return deepcopy(grid)
    mapping = {v: order[(i-setting.offset) % len(order)] for i, v in enumerate(order)}
    return [[v if v in excluded else mapping[v] for v in row] for row in grid]


def declared_rival_bindings(setting):
    """Iterate live contracts; unknown declarations require an explicit adapter."""
    opposite = Setting('ccw' if setting.direction == 'cw' else 'cw', setting.steps)
    targets = {
        'row_major_first_occurrence': 'semantic:row_major',
        'fixed_quadrant_order': 'semantic:quadrant',
        'first_cell_angle': 'semantic:first',
        'identity': 'semantic:identity',
        'counterclockwise': f'parameter:{opposite.key}',
        'numeric_color_cycle': 'semantic:numeric',
        'zero_is_background': 'semantic:zero_background',
        'rotate_frame_too': 'semantic:rotate_frame',
    }
    bindings = []
    for namespace in ('CANONICAL_SHORTCUTS', 'SEMANTIC_RIVALS', 'LESSON_COMPETITORS'):
        registry = getattr(generator(), namespace, None)
        if not isinstance(registry, dict) or not registry:
            raise ValueError(f'Missing/invalid live rival registry: {namespace}')
        for name, function in registry.items():
            if name not in targets or not callable(function):
                raise ValueError(f'Unsupported live rival declaration: {namespace}.{name}')
            bindings.append({'namespace': namespace, 'name': name, 'adapter': targets[name]})
    return bindings


def _adapters(setting):
    result = {f'parameter:{other.key}': (lambda g, other=other: predict(g, other)) for other in SETTINGS}
    result.update({f'semantic:{mode}': (lambda g, mode=mode: predict(g, setting, mode=mode))
                   for mode in ('numeric', 'row_major', 'quadrant', 'first')})
    result['semantic:zero_background'] = lambda g: predict(g, setting, excluded=FRAME | {0})
    result['semantic:rotate_frame'] = lambda g: predict(g, setting, excluded=frozenset())
    result['semantic:identity'] = deepcopy
    return result


def rivals(setting):
    adapters = _adapters(setting)
    keys = {binding['adapter'] for binding in declared_rival_bindings(setting)}
    keys.update(f'parameter:{other.key}' for other in SETTINGS)
    return {name: function for name, function in adapters.items() if name in keys}


def verify_live_adapters(grid):
    """At cw1, every adapted rival must match its live canonical callable."""
    adapters = _adapters(DEFAULT)
    checked = set()
    for binding in declared_rival_bindings(DEFAULT):
        function = getattr(generator(), binding['namespace'])[binding['name']]
        identity = (binding['name'], id(function))
        if identity in checked:
            continue
        checked.add(identity)
        if function(grid) != adapters[binding['adapter']](grid):
            raise ValueError(f'Live rival semantics changed: {binding["namespace"]}.{binding["name"]}')


def score(pairs, demo_indices, query_indices, competitors):
    """A surviving rival is ambiguous only if a query requires its distinction."""
    result = {}
    for name, rival in competitors.items():
        demo_disagreements = [i for i in demo_indices if rival(pairs[i]['input']) != pairs[i]['output']]
        query_disagreements = [i for i in query_indices if rival(pairs[i]['input']) != pairs[i]['output']]
        status = 'refuted' if demo_disagreements else ('ambiguous' if query_disagreements else 'survived_all')
        result[name] = {'status': status, 'demo_disagreements': demo_disagreements,
                        'query_disagreements': query_disagreements}
    return result


def score_episode(episode):
    setting = Setting(**episode['parameters'])
    pairs = episode['pairs']
    competitors = rivals(setting)
    production = score(pairs, list(range(3)), [3], competitors)
    rotations = [score(pairs, [i for i in range(4) if i != q], [q], competitors) for q in range(4)]
    return {'production': production, 'rotations': rotations,
            'production_ambiguous': any(r['status'] == 'ambiguous' for r in production.values()),
            'ambiguous_rotations': [q for q, rows in enumerate(rotations) if any(r['status'] == 'ambiguous' for r in rows.values())]}


def make_episode(bridge, seed, *, setting=None, difficulty='medium', start=0):
    if type(seed) is not int or type(start) is not int or start < 0:
        raise ValueError('seed/start must be integers and start nonnegative')
    if difficulty not in ('easy', 'medium', 'hard'):
        raise ValueError('difficulty must be easy|medium|hard')
    chosen = choose_setting(seed) if setting is None else setting
    program = instantiate_rule(chosen)
    pairs = []
    for index in range(start, start+4):
        grid = generator().generate(seed, index, difficulty=difficulty)
        errors = generator().strict_canonical_like(grid)
        if errors:
            raise ValueError(f'Invalid generated input at {index}: {errors}')
        pairs.append({'input': grid, 'output': evaluate(bridge, program, grid),
                      'sample_index': index, 'input_sha256': digest(grid),
                      'profile': generator().schedule_profile(seed, index, difficulty)})
    episode = {'seed': seed, 'start': start, 'difficulty': difficulty, 'parameters': asdict(chosen),
               'selection': 'deterministic_seed_once' if setting is None else 'explicit_once_per_episode',
               'rule_sha256': digest(program), 'pairs': pairs}
    verify_python_labels(episode)
    episode['scores'] = score_episode(episode)
    return episode


def public_challenge(episode):
    pairs = episode['pairs']
    return deepcopy({'train': [{'input': p['input'], 'output': p['output']} for p in pairs[:3]],
                     'test': [{'input': p['input']} for p in pairs[3:]]})


def verify_python_labels(episode):
    setting = Setting(**episode['parameters'])
    for pair in episode['pairs']:
        if predict(pair['input'], setting) != pair['output']:
            raise ValueError('Selected Racket labels disagree with the diagnostic semantic mirror')


def verify_episode(bridge, episode, *, cache=None):
    cache = {} if cache is None else cache
    setting = Setting(**episode['parameters'])
    if len(episode['pairs']) != 4:
        raise ValueError('Expected exactly three demos and one query')
    if episode['rule_sha256'] != digest(instantiate_rule(setting)):
        raise ValueError('Episode rule hash mismatch')
    if episode['selection'] == 'deterministic_seed_once' and setting != choose_setting(episode['seed']):
        raise ValueError('Seed-selected episode parameters changed')
    for pair in episode['pairs']:
        verify_live_adapters(pair['input'])
    all_outputs = {}
    for other in SETTINGS:
        program = instantiate_rule(other)
        outputs = []
        for position, pair in enumerate(episode['pairs']):
            expected_index = episode['start'] + position
            if pair['sample_index'] != expected_index:
                raise ValueError('Sample index mismatch')
            regenerated = generator().generate(episode['seed'], expected_index, difficulty=episode['difficulty'])
            if pair['input'] != regenerated or pair['input_sha256'] != digest(regenerated):
                raise ValueError('Input regeneration/hash mismatch')
            key = (digest(program), digest(pair['input']))
            if key not in cache:
                cache[key] = evaluate(bridge, program, pair['input'])
            output = cache[key]
            if output != predict(pair['input'], other):
                raise ValueError(f'Racket/Python disagreement for {other.key}')
            if other == setting and output != pair['output']:
                raise ValueError('Stored label differs from executed Racket output')
            outputs.append(output)
        all_outputs[other.key] = outputs
    scored = score_episode(episode)
    if 'scores' in episode and episode['scores'] != scored:
        raise ValueError('Stored rival scores differ from executable rescore')
    return all_outputs, scored


def source_hashes():
    paths = [HERE, selected_generator()[1],
             RUNTIME / 'arc_repl/racket_bridge.py', RUNTIME / 'reviewer_support.py']
    return {str(path.relative_to(REPO)): digest(path.read_bytes()) for path in paths}


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n')


def audit(out, seeds, bands, starts, rotation_policy):
    for name, values in (('seeds', seeds), ('bands', bands), ('starts', starts)):
        if not values or len(values) != len(set(values)):
            raise ValueError(f'{name} must be nonempty and contain no duplicates')
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / 'public').mkdir()
    (out / 'private').mkdir()
    source_before = source_hashes()
    episodes, witnesses, canonical_checks = [], {}, []
    cache = {}
    with RacketBridge() as bridge:
        racket_version = bridge.eval_text('(version)')
        for setting in SETTINGS:
            for requested_seed in seeds:
                seed = seed_for_setting(requested_seed, setting)
                for band in bands:
                    for start in starts:
                        episode = make_episode(bridge, seed, difficulty=band, start=start)
                        episode['requested_seed_stratum'] = requested_seed
                        outputs, _ = verify_episode(bridge, episode, cache=cache)
                        episode_id = f'{setting.key}-s{seed}-{band}-i{start}'
                        episode['episode_id'] = episode_id
                        episodes.append(episode)
                        for other in SETTINGS:
                            if other == setting:
                                continue
                            pairkey = ':'.join(sorted((setting.key, other.key)))
                            if pairkey in witnesses:
                                continue
                            for i, pair in enumerate(episode['pairs']):
                                if outputs[setting.key][i] != outputs[other.key][i]:
                                    witnesses[pairkey] = {'episode_id': episode_id, 'pair_index': i,
                                        'sample_index': pair['sample_index'], 'input': pair['input'],
                                        'outputs': {setting.key: outputs[setting.key][i], other.key: outputs[other.key][i]}}
                                    break
        # Check the exact default against every labeled canonical pair, including variants.
        from reviewer_support import canonical_pairs
        for pair in canonical_pairs(TASK_ID, root=REPO, labeled_only=True):
            output = evaluate(bridge, instantiate_rule(), pair['input'])
            if output != pair['output']:
                raise ValueError('Default disagrees with a labeled canonical pair')
            canonical_checks.append({k: pair[k] for k in ('variant', 'split', 'pair_index')})
    if source_before != source_hashes():
        raise ValueError('Source changed during audit; rerun after source freeze')
    production_failures = [e['episode_id'] for e in episodes if e['scores']['production_ambiguous']]
    rotation_failures = {e['episode_id']: e['scores']['ambiguous_rotations'] for e in episodes if e['scores']['ambiguous_rotations']}
    failures = bool(production_failures or (rotation_policy == 'require' and rotation_failures) or len(witnesses) != 6)
    rules = {s.key: {'parameters': asdict(s), 'program': instantiate_rule(s), 'sha256': digest(instantiate_rule(s))} for s in SETTINGS}
    private = {'schema': '5bba6e671cec-parametric-v1', 'status': 'failed' if failures else 'passed',
        'prototype': True, 'rules': rules, 'source_hashes': source_before, 'racket_version': racket_version,
        'canonical_rule_sha256': digest(canonical_rule()), 'canonical_checks': canonical_checks,
        'episodes': episodes, 'cross_setting_witnesses': witnesses,
        'production_failures': production_failures, 'rotation_failures': rotation_failures,
        'rotation_policy': rotation_policy, 'rival_inventory': list(rivals(DEFAULT)),
        'rival_adaptations': {s.key: declared_rival_bindings(s) for s in SETTINGS},
        'counts': {'settings': 4, 'episodes': len(episodes), 'pairs': 4*len(episodes),
                   'rotations': 4*len(episodes), 'unique_racket_rule_input_checks': len(cache),
                   'cross_setting_witnesses': len(witnesses), 'canonical_labels': len(canonical_checks)},
        'limits': ['Finite declared-rival evidence only; no universal identifiability claim.',
                   'Inputs remain canonical-scale 8x8; this prototype does not test size generalization.',
                   'Direction aliases for two regions; two-step directions alias for four regions; cw1=ccw2 and ccw1=cw2 on three regions.',
                   'Prototype variants have no production approval or training admission.']}
    write_json(out / 'private/evidence.json', private)
    public_path = out / 'public/challenges.jsonl'
    public_path.write_text(''.join(json.dumps(public_challenge(e), separators=(',', ':'))+'\n' for e in episodes))
    manifest = {'schema': '5bba6e671cec-parametric-manifest-v1', 'status': private['status'],
        'argv': sys.argv, 'cwd': str(Path.cwd()), 'counts': private['counts'], 'source_hashes': source_before,
        'assets': {name: digest((out/name).read_bytes()) for name in ('private/evidence.json', 'public/challenges.jsonl')},
        'production_failures': len(production_failures), 'ambiguous_rotations': sum(map(len, rotation_failures.values()))}
    write_json(out/'manifest.json', manifest)
    return manifest


def rescore(source, out):
    source = Path(source).resolve()
    manifest = json.loads((source/'manifest.json').read_text())
    if set(manifest['assets']) != {'private/evidence.json', 'public/challenges.jsonl'}:
        raise ValueError('Evidence asset inventory mismatch')
    for name, expected in manifest['assets'].items():
        if name not in ('private/evidence.json', 'public/challenges.jsonl') or digest((source/name).read_bytes()) != expected:
            raise ValueError('Evidence asset hash mismatch')
    evidence = json.loads((source/'private/evidence.json').read_text())
    if evidence['rotation_policy'] not in ('require', 'diagnostic'):
        raise ValueError('Invalid retained rotation policy')
    if evidence['canonical_rule_sha256'] != digest(canonical_rule()):
        raise ValueError('Canonical rule authority mismatch')
    if evidence['rival_adaptations'] != {s.key: declared_rival_bindings(s) for s in SETTINGS}:
        raise ValueError('Live rival adaptation inventory mismatch')
    if evidence['rival_inventory'] != list(rivals(DEFAULT)):
        raise ValueError('Declared rival inventory mismatch')
    if evidence['source_hashes'] != source_hashes() or manifest['source_hashes'] != source_hashes():
        raise ValueError('Current source does not match retained evidence')
    for setting in SETTINGS:
        if evidence['rules'][setting.key] != {'parameters': asdict(setting), 'program': instantiate_rule(setting), 'sha256': digest(instantiate_rule(setting))}:
            raise ValueError('Exact materialized rule mismatch')
    public = [json.loads(line) for line in (source/'public/challenges.jsonl').read_text().splitlines()]
    if public != [public_challenge(e) for e in evidence['episodes']]:
        raise ValueError('Public/private projection mismatch')
    production_failures = [e['episode_id'] for e in evidence['episodes'] if e['scores']['production_ambiguous']]
    rotation_failures = {e['episode_id']: e['scores']['ambiguous_rotations'] for e in evidence['episodes'] if e['scores']['ambiguous_rotations']}
    expected_status = 'failed' if production_failures or (evidence['rotation_policy'] == 'require' and rotation_failures) else 'passed'
    if evidence['production_failures'] != production_failures or evidence['rotation_failures'] != rotation_failures:
        raise ValueError('Retained aggregate findings disagree with episode scores')
    if evidence['status'] != expected_status or manifest['status'] != expected_status:
        raise ValueError('Retained aggregate status mismatch')
    if manifest['production_failures'] != len(production_failures) or manifest['ambiguous_rotations'] != sum(map(len, rotation_failures.values())):
        raise ValueError('Retained manifest finding counts mismatch')
    failures = []
    cache = {}
    with RacketBridge() as bridge:
        expected_keys = {':'.join(sorted((a.key, b.key))) for a in SETTINGS for b in SETTINGS if a != b}
        if set(evidence['cross_setting_witnesses']) != expected_keys:
            raise ValueError('Missing cross-setting witness')
        episode_by_id = {e['episode_id']: e for e in evidence['episodes']}
        if len(episode_by_id) != len(evidence['episodes']):
            raise ValueError('Duplicate episode identity')
        for key, witness in evidence['cross_setting_witnesses'].items():
            pair = episode_by_id[witness['episode_id']]['pairs'][witness['pair_index']]
            if witness['input'] != pair['input'] or witness['sample_index'] != pair['sample_index']:
                raise ValueError('Cross-setting witness provenance mismatch')
            settings = [s for s in SETTINGS if s.key in key.split(':')]
            if set(witness['outputs']) != {s.key for s in settings}:
                raise ValueError('Cross-setting witness setting mismatch')
            observed = {s.key: evaluate(bridge, instantiate_rule(s), witness['input']) for s in settings}
            if observed != witness['outputs'] or len({digest(g) for g in observed.values()}) != 2:
                raise ValueError('Cross-setting witness output mismatch')
        from reviewer_support import canonical_pairs
        expected_checks = []
        for pair in canonical_pairs(TASK_ID, root=REPO, labeled_only=True):
            if evaluate(bridge, instantiate_rule(), pair['input']) != pair['output']:
                raise ValueError('Canonical default mismatch on replay')
            expected_checks.append({k: pair[k] for k in ('variant', 'split', 'pair_index')})
        if expected_checks != evidence['canonical_checks']:
            raise ValueError('Canonical pair coverage mismatch')
        for episode in evidence['episodes']:
            if episode['selection'] != 'deterministic_seed_once' or episode['seed'] != seed_for_setting(episode['requested_seed_stratum'], Setting(**episode['parameters'])):
                raise ValueError('Seed stratification mismatch')
            _, scored = verify_episode(bridge, episode, cache=cache)
            if scored['production_ambiguous'] or (evidence['rotation_policy'] == 'require' and scored['ambiguous_rotations']):
                failures.append(episode['episode_id'])
    expected_counts = {'settings': 4, 'episodes': len(public), 'pairs': 4*len(public),
        'rotations': 4*len(public), 'unique_racket_rule_input_checks': len(cache),
        'cross_setting_witnesses': 6, 'canonical_labels': len(expected_checks)}
    if evidence['counts'] != expected_counts or manifest['counts'] != expected_counts:
        raise ValueError('Retained aggregate population/check counts mismatch')
    result = {'status': 'failed' if failures else 'passed', 'argv': sys.argv, 'cwd': str(Path.cwd()),
              'input_manifest_sha256': digest((source/'manifest.json').read_bytes()),
              'episodes_checked': len(public), 'racket_rule_input_checks': len(cache), 'failures': failures}
    out = Path(out).resolve()
    if out.exists():
        raise ValueError('Use a new rescore output path')
    write_json(out, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    a = sub.add_parser('audit')
    a.add_argument('--out', required=True)
    a.add_argument('--seed', type=int, action='append', dest='seeds')
    a.add_argument('--band', choices=('easy', 'medium', 'hard'), action='append', dest='bands')
    a.add_argument('--start', type=int, action='append', dest='starts')
    a.add_argument('--rotation-policy', choices=('require', 'diagnostic'), default='require')
    r = sub.add_parser('rescore')
    r.add_argument('--input', required=True)
    r.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        result = audit(args.out, args.seeds or [0, 1, 2], args.bands or ['easy','medium','hard'], args.starts or [0,1,2,3], args.rotation_policy) if args.command == 'audit' else rescore(args.input, args.out)
        print(json.dumps(result, sort_keys=True))
        return 0 if result['status'] == 'passed' else 1
    except Exception as exc:
        print(json.dumps({'status': 'error', 'error': f'{type(exc).__name__}: {exc}', 'argv': sys.argv}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

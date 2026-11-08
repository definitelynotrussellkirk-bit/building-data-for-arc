"""Protected Racket replay and visible-only export for this proposed family.

Run from the packet through ``review.py run python3``.  This task-local tool
does not qualify a native adapter, approve a rule, or admit training records.
Every exported label is compared with the live protected Racket result.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RUNTIME = ROOT / 'shared/runtime'
TASK_ID = '25e78410d5bb'
SETTINGS = ({'retention': 'all'}, {'retention': 'largest_filled_component'})
sys.dont_write_bytecode = True


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _load_local(path, purpose):
    """Import exactly these source bytes without a bare sibling-module name."""
    path = Path(path)
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
        raise ValueError(f'{purpose} must be a regular source inside this checkout')
    raw = path.read_bytes()
    name = '_25e78410d5bb_' + purpose + '_' + _sha(str(path).encode() + raw)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def _public_helpers():
    return _load_local(RUNTIME / 'reviewer_support.py', 'public_helpers')


def first_turn_bytes(episode):
    """Project demos and only query one's input; this is not a turn controller."""
    helpers = _public_helpers()
    if not episode.get('test'):
        raise ValueError('A first turn requires a query input')
    return helpers.public_challenge_bytes({
        'train': episode['train'], 'test': [{'input': episode['test'][0]['input']}]})


def _projection_certificate(episode, raw, public_id):
    first = first_turn_bytes(episode)
    changed = copy.deepcopy(episode)
    changed.update(seed='changed private seed', settings={'hidden': 'changed'},
                   program='changed private program', program_solution='changed private program',
                   private_metadata={'changed': True})
    for pair in changed['test']:
        pair['output'] = [[9]]
    helpers = _public_helpers()
    if helpers.public_challenge_bytes(changed) != raw:
        raise ValueError('Public bytes depend on private metadata or query answers')
    if helpers.public_challenge_id(episode) != public_id:
        raise ValueError('Public ID differs from the exact serialized bytes')
    changed['test'] = changed['test'][:1] + [{'input': [[8]], 'output': [[7]]}]
    if first_turn_bytes(changed) != first:
        raise ValueError('First-turn projection depends on a later query')
    one = {'train': episode['train'], 'test': episode['test'][:1]}
    if first_turn_bytes(one) != first:
        raise ValueError('One-query and multiple-query first-turn bytes differ')
    return {'visible_only_identity': True, 'first_turn_sha256': _sha(first),
            'first_turn_demo_count': len(episode['train']), 'first_turn_query_count': 1,
            'same_first_turn_as_one_query_projection': True,
            'private_metadata_and_query_answers_ignored': True,
            'later_query_mutation_invariant': True}


def build_export_plan(episodes):
    """Prepare sorted public bytes, rejecting duplicate visible challenges."""
    helpers = _public_helpers()
    planned = []
    seen = set()
    for episode in episodes:
        raw = helpers.public_challenge_bytes(episode)
        public_id = helpers.public_challenge_id(episode)
        if public_id in seen:
            raise ValueError('duplicate public challenge payload')
        seen.add(public_id)
        planned.append({'public_id': public_id, 'public_bytes': raw,
                        'episode': copy.deepcopy(episode),
                        'projection': _projection_certificate(episode, raw, public_id)})
    if not planned:
        raise ValueError('At least one episode is required')
    return sorted(planned, key=lambda item: item['public_id'])


def write_export(out, plan, certificates, summary):
    """Write prepared data to a fresh directory, with the summary written last."""
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(f'Output destination must be fresh: {out}')
    ordered = sorted(plan, key=lambda item: item['public_id'])
    public_raw = b''.join(item['public_bytes'] for item in ordered)
    private_raw = b''.join(_json_bytes(dict(item['episode'], public_id=item['public_id']))
                           for item in ordered)
    certificate_raw = b''.join(_json_bytes(row) for row in
                              sorted(certificates, key=lambda row: row['public_id']))
    out.mkdir(parents=True, exist_ok=False)
    (out / 'public').mkdir()
    for item in ordered:
        (out / 'public' / (item['public_id'] + '.json')).write_bytes(item['public_bytes'])
    (out / 'public.jsonl').write_bytes(public_raw)
    (out / 'episodes.private.jsonl').write_bytes(private_raw)
    (out / 'certificates.private.jsonl').write_bytes(certificate_raw)
    final_summary = dict(summary)
    final_summary['files'] = {
        'public.jsonl': {'sha256': _sha(public_raw), 'rows': len(ordered)},
        'episodes.private.jsonl': {'sha256': _sha(private_raw), 'rows': len(ordered)},
        'certificates.private.jsonl': {'sha256': _sha(certificate_raw), 'rows': len(certificates)},
    }
    final_summary['public_ids'] = [item['public_id'] for item in ordered]
    (out / 'summary.private.json').write_bytes(_json_bytes(final_summary))
    return final_summary


@contextlib.contextmanager
def _local_runtime():
    before = list(sys.path)
    prefixes = ('arc_repl', 'puzzle_generators')
    saved = {key: value for key, value in sys.modules.items()
             if key.split('.')[0] in prefixes}
    for key in saved:
        del sys.modules[key]
    sys.path.insert(0, str(RUNTIME))
    try:
        yield
    finally:
        sys.path[:] = before
        for key in list(sys.modules):
            if key.split('.')[0] in prefixes:
                del sys.modules[key]
        sys.modules.update(saved)


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30 or type(value[0]) is not list
            or not 1 <= len(value[0]) <= 30 or any(type(row) is not list
            or len(row) != len(value[0]) or any(type(cell) is not int or not 0 <= cell <= 9
            for cell in row) for row in value)):
        raise ValueError('Grid must be rectangular 1..30 with exact integer colors 0..9')
    return copy.deepcopy(value)


class ProtectedReplay:
    """Live same-checkout Racket oracle; no Python or unprotected fallback."""

    def __init__(self):
        bridge_module = importlib.import_module('arc_repl.racket_bridge')
        wrap_module = importlib.import_module('puzzle_generators.rule_wrap')
        for module in (bridge_module, wrap_module):
            if not Path(module.__file__).resolve().is_relative_to(RUNTIME):
                raise ValueError('Reference runtime must come from this checkout')
        self.bridge = bridge_module.RacketBridge()
        try:
            identity = self.bridge.runtime_identity
            if identity.get('backend') != 'racket' or identity.get('protected') is not True:
                raise ValueError('Replay requires a live protected Racket backend')
            keys = ('schema', 'backend', 'protected', 'binary_sha256', 'prelude_sha256',
                    'bridge_sha256', 'boot_script_sha256', 'candidate_symbol_policy_sha256')
            self.identity = {key: identity[key] for key in keys if key in identity}
        except Exception:
            self.bridge.close()
            raise
        self.wrap_rule = wrap_module.wrap_rule
        self.wrapped = {}
        self.results = {}
        self.evaluations = 0
        self.cache_hits = 0

    def apply(self, program, grid):
        if type(program) is not str or not program.strip():
            raise ValueError('Reference program must be nonempty exact Racket text')
        grid = _grid(grid)
        key = (program, _json_bytes(grid))
        if key not in self.results:
            if program not in self.wrapped:
                self.wrapped[program] = self.wrap_rule(program)
            literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
            self.evaluations += 1
            self.results[key] = _grid(self.bridge.eval_text(f'({self.wrapped[program]} {literal})'))
        else:
            self.cache_hits += 1
        return copy.deepcopy(self.results[key])

    def close(self):
        self.bridge.close()


def _source_hashes():
    paths = [HERE / name for name in ('adapter.py', 'programs.py', 'sampler.py', 'probe.py')]
    paths += [ROOT / 'generators' / TASK_ID / 'generator.py',
              ROOT / 'shared/data/canonical/puzzles.jsonl', RUNTIME / 'reviewer_support.py',
              RUNTIME / 'puzzle_generators/rule_wrap.py', RUNTIME / 'arc_repl/racket_bridge.py']
    return {path.relative_to(ROOT).as_posix(): _sha(path.read_bytes()) for path in paths}


def _episode(adapter, seed, settings, demos, queries):
    value = adapter.generate(seed, copy.deepcopy(settings), demos=demos, queries=queries)
    if not isinstance(value, dict) or value.get('program_solution') != adapter.program(settings):
        raise ValueError('Generated program_solution must equal program(settings) exactly')
    episode = copy.deepcopy(value)
    for split, expected in (('train', demos), ('test', queries)):
        pairs = episode.get(split)
        if type(pairs) is not list or len(pairs) != expected:
            raise ValueError(f'Generated {split} count differs from the requested count')
        episode[split] = [{'input': _grid(pair['input']), 'output': _grid(pair['output'])}
                          for pair in pairs]
    inputs = [_json_bytes(pair['input']) for pair in episode['train'] + episode['test']]
    if len(inputs) != len(set(inputs)):
        raise ValueError('Demonstration and query inputs must all be distinct')
    episode.update(task_id=TASK_ID, seed=seed, settings=copy.deepcopy(settings),
                   reference='proposed_parametric', training_admitted=False,
                   program_sha256=_sha(episode['program_solution'].encode()))
    return episode


def _compare_python(replay, programs, program, grid, retention, rival, context):
    actual = replay.apply(program, grid)
    claimed = _grid(programs.evaluate(copy.deepcopy(grid), retention=retention, rival=rival))
    if claimed != actual:
        raise ValueError(f'Python/Racket parity mismatch: {context}')
    return actual


def _check_episode(episode, adapter, programs, replay):
    retention = episode['settings']['retention']
    program = episode['program_solution']
    labels = []
    for split in ('train', 'test'):
        for index, pair in enumerate(episode[split]):
            actual = _compare_python(replay, programs, program, pair['input'], retention,
                                     None, f'{retention} {split}[{index}]')
            if actual != pair['output']:
                raise ValueError(f'Generated label disagrees with Racket: {retention} {split}[{index}]')
            labels.append({'split': split, 'index': index, 'input_sha256': _sha(_json_bytes(pair['input'])),
                           'output_sha256': _sha(_json_bytes(actual)), 'racket_verified': True})
    candidates = []
    for settings in SETTINGS:
        if settings != episode['settings']:
            candidates.append(('setting:' + settings['retention'], adapter.program(settings),
                               settings['retention'], None, 'alternative_setting'))
    for rival in programs.rivals_for(retention):
        candidates.append(('rival:' + rival, programs.rival_program(rival, retention=retention),
                           retention, rival, 'named_shortcut'))
    checked = []
    for name, candidate, candidate_retention, rival, kind in candidates:
        result = {'name': name, 'kind': kind, 'program_sha256': _sha(candidate.encode()),
                  'demonstrations_checked': 0, 'queries_checked': 0, 'rejecting_demos': []}
        for index, pair in enumerate(episode['train']):
            actual = _compare_python(replay, programs, candidate, pair['input'], candidate_retention,
                                     rival, f'{name} demo[{index}]')
            result['demonstrations_checked'] += 1
            if actual != pair['output']:
                result['rejecting_demos'].append(index)
                if 'witness' not in result:
                    result.update(status='rejected_by_demonstrations', first_rejecting_demo=index,
                                  witness={'input_sha256': _sha(_json_bytes(pair['input'])),
                                           'expected_output_sha256': _sha(_json_bytes(pair['output'])),
                                           'rival_output_sha256': _sha(_json_bytes(actual)),
                                           'rival_output': actual})
        if not result['rejecting_demos']:
            result['status'] = 'survives_demonstrations'
            for index, pair in enumerate(episode['test']):
                actual = _compare_python(replay, programs, candidate, pair['input'], candidate_retention,
                                         rival, f'{name} query[{index}]')
                result['queries_checked'] += 1
                if actual != pair['output']:
                    raise ValueError(f'Surviving rival disagrees on query {index}: {name}')
            result['status'] = 'survives_and_agrees_on_all_queries'
            if kind == 'named_shortcut':
                raise ValueError('Named rival survives demonstrations: ' + name)
        checked.append(result)
    finite_survivors = [row['name'] for row in checked if row['kind'] == 'alternative_setting'
                        and row['status'] != 'rejected_by_demonstrations']
    if finite_survivors:
        raise ValueError('Demonstrations do not identify the sole finite setting: ' + ', '.join(finite_survivors))
    return {'seed': episode['seed'], 'settings': episode['settings'],
            'program_sha256': episode['program_sha256'],
            'counts': {'demonstrations': len(episode['train']), 'queries': len(episode['test'])},
            'input_shapes': {split: [[len(pair['input']), len(pair['input'][0])]
                                     for pair in episode[split]] for split in ('train', 'test')},
            'reference_labels_verified': len(labels), 'label_evidence': labels,
            'distinct_inputs': len(labels), 'finite_setting_identified_by_demos': True,
            'all_named_rivals_rejected_by_demos': True,
            'rivals': checked,
            'surviving_rivals_agree_on_each_query': True,
            'query_answers_used_for_demo_selection': False,
            'scope': 'Only the declared finite settings and named rivals, not universal rule uniqueness.'}


def run_probe(out, *, seeds=(0, 17), demos=3, queries=4):
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(f'Output destination must be fresh: {out}')
    if (type(demos) is not int or not 2 <= demos <= 6 or type(queries) is not int
            or not 1 <= queries <= 4):
        raise ValueError('Use 2..6 demonstrations and 1..4 queries')
    seeds = list(seeds)
    if (not seeds or len(seeds) > 16 or any(type(seed) is not int or not 0 <= seed < 2**63
            for seed in seeds) or len(seeds) != len(set(seeds))):
        raise ValueError('Use 1..16 distinct integer seeds in 0..2**63-1')
    source_hashes = _source_hashes()
    episodes, certificates = [], []
    with _local_runtime():
        adapter = _load_local(HERE / 'adapter.py', 'adapter')
        programs = _load_local(HERE / 'programs.py', 'programs')
        if adapter.program({'retention': 'all'}) != programs.canonical_program():
            raise ValueError('Default program differs from the exact canonical source')
        replay = ProtectedReplay()
        try:
            for seed in seeds:
                matched_inputs = None
                for settings in SETTINGS:
                    episode = _episode(adapter, seed, settings, demos, queries)
                    inputs = {split: [pair['input'] for pair in episode[split]]
                              for split in ('train', 'test')}
                    if matched_inputs is not None and inputs != matched_inputs:
                        raise ValueError('Input distribution depends on the private setting')
                    matched_inputs = inputs
                    single = _episode(adapter, seed, settings, demos, 1)
                    if first_turn_bytes(single) != first_turn_bytes(episode):
                        raise ValueError('Adapter changes first-turn bytes when query count changes')
                    certificate = _check_episode(episode, adapter, programs, replay)
                    certificate['adapter_one_query_first_turn_equal'] = True
                    certificate['matched_inputs_across_settings'] = True
                    episodes.append(episode)
                    certificates.append(certificate)
            identity = copy.deepcopy(replay.identity)
            evaluations, cache_hits = replay.evaluations, replay.cache_hits
        finally:
            replay.close()
    if _source_hashes() != source_hashes:
        raise ValueError('Source changed during replay; no export was published')
    plan = build_export_plan(episodes)
    by_job = {(item['episode']['seed'], item['episode']['settings']['retention']): item for item in plan}
    for certificate in certificates:
        item = by_job[(certificate['seed'], certificate['settings']['retention'])]
        certificate.update(public_id=item['public_id'], projection=item['projection'], racket=identity,
                           source_hashes=source_hashes)
    summary = {'schema': '25e78410d5bb-parametric-replay-v1', 'status': 'passed',
               'task_id': TASK_ID, 'scope': 'Task-local proposed family; no approval or training admission.',
               'training_admitted': False, 'settings': list(SETTINGS), 'seeds': seeds,
               'episodes': len(episodes), 'demonstrations_per_episode': demos,
               'queries_per_episode': queries,
               'verified_labels': len(episodes) * (demos + queries),
               'candidate_demo_checks': sum(row['demonstrations_checked']
                   for certificate in certificates for row in certificate['rivals']),
               'candidate_query_checks': sum(row['queries_checked']
                   for certificate in certificates for row in certificate['rivals']),
               'named_rivals_rejected': sum(row['kind'] == 'named_shortcut'
                   for certificate in certificates for row in certificate['rivals']),
               'racket_evaluations': evaluations, 'racket_cache_hits': cache_hits,
               'racket': identity, 'source_hashes': source_hashes,
               'public_identity': 'SHA-256 of reviewer_support.public_challenge_bytes exactly',
               'first_turn_projection': 'Original demonstrations plus first query input only; no controller.',
               'rival_policy': ('Every named rival and alternative setting must be rejected by demos. '
                                'Survivors are replayed for query counterexamples and fail export.'),
               'limitations': ['Finite named-rival audit does not prove semantic uniqueness.',
                               'A public multi-query file is controller data, not a whole model prompt.']}
    return write_export(out, plan, certificates, summary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='Fresh export directory')
    parser.add_argument('--seed', action='append', type=int, help='Repeat for each seed; default: 0 and 17')
    parser.add_argument('--demos', type=int, default=3)
    parser.add_argument('--queries', type=int, default=4)
    args = parser.parse_args(argv)
    try:
        result = run_probe(args.out, seeds=(0, 17) if args.seed is None else args.seed,
                           demos=args.demos, queries=args.queries)
    except Exception as error:
        print(json.dumps({'status': 'failed', 'error': type(error).__name__, 'message': str(error)},
                         sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps({key: result[key] for key in ('status', 'episodes', 'verified_labels',
                     'racket_evaluations', 'racket_cache_hits')} | {'out': str(args.out)}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

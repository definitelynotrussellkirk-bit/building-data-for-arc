"""Reusable finite-rival, protected-Racket, public-view, and causal audit.

This tool is intentionally source-bound and bounded. It checks named shortcuts
and sampled seeds; it is not owner acceptance or a universal learnability proof.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
import random
import sys

BASE = Path(__file__).resolve().parent
TASK = 'public_eval_1818057f'
RIVALS = (
    'exact_only',
    'first_center',
    'last_center',
    'one_per_component',
    'first_component',
    'last_component',
    'largest_area',
    'smallest_area',
    'topmost_centers',
    'paint_components',
    'all_fours',
)
CAUSAL_DESCRIPTIONS = {
    'step_a': ('Detect every orthogonal color-4 plus, group plus centers by the original '
               'four-connected color-4 component, count centers per component, and choose '
               'the earliest component attaining the maximum plus count.'),
    'intermediate': ('The ordered component records with each component size, its ordered '
                     'plus-center list and count, plus the selected dominant component index.'),
    'step_b': ('Recolor to 8 only cells belonging to plus motifs whose centers lie in the '
               'selected dominant component.'),
    'why_b_depends_on_a': ('Component area and reading order are independent decoys; the '
                           'component that step B must paint is unknowable until step A has '
                           'detected and counted the input-specific plus centers.'),
}


def _load(name: str):
    path = BASE / f'{name}.py'
    token = '_plus_audit_' + name + '_' + hashlib.sha256(str(path.resolve()).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(token, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[token] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _root() -> Path:
    from reviewer_support import find_root
    return find_root(__file__)


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def _sources() -> dict[str, str]:
    root = _root()
    home = BASE.parents[1]
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(home.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts
            and (p.suffix in ('.py', '.rkt') or p.name in ('promotion.json', 'public-parent.json'))}


def _settings() -> list[dict[str, str]]:
    params = json.loads((BASE / 'promotion.json').read_text())['parameters']
    keys = sorted(params)
    return [dict(zip(keys, values)) for values in itertools.product(*(params[k] for k in keys))]


def run_audit(out: Path, *, seeds: list[int], racket_seeds: list[int]) -> dict:
    from reviewer_support import public_challenge_bytes, public_challenge_id

    out = Path(out)
    if out.exists():
        raise FileExistsError('choose a fresh audit directory')
    if not seeds or len(set(seeds)) != len(seeds) or any(type(s) is not int or not 0 <= s < 2**63 for s in seeds):
        raise ValueError('seeds must be unique exact nonnegative integers')
    if any(s not in seeds for s in racket_seeds):
        raise ValueError('racket_seeds must be a subset of seeds')

    adapter = _load('adapter')
    source = _sources()
    findings = []
    harmful = []
    benign = {}
    refuted = {}
    exports: dict[str, bytes] = {}
    controller_rows = []
    report = {
        'schema': 'public-plus-component-finite-audit-v1',
        'task_id': TASK,
        'status': 'running',
        'settings': _settings(),
        'seeds': list(seeds),
        'racket_seeds': list(racket_seeds),
        'demo_counts': [2, 3, 6],
        'rivals': list(RIVALS),
        'episodes': 0,
        'pair_claims': 0,
        'rival_checks': 0,
        'racket_evaluations': 0,
        'public_turns': 0,
        'substantive_30x30_queries': 0,
        'harmful_survivors': harmful,
        'benign_survivals': benign,
        'refuted_examples': refuted,
        'findings': findings,
        'source_sha256': source,
        'limits': ('Finite named rivals and sampled sources only; no universal uniqueness, '
                   'measured learning benefit, owner acceptance, or training admission.'),
    }

    apply = identity = bridge = None
    cache = {}
    if racket_seeds:
        from arcpuzzles.parametric_worker import _real_evaluator, _grid
        apply, identity, bridge = _real_evaluator(_root() / 'shared/runtime')
    matched = {}
    try:
        for setting in _settings():
            scope = setting['mark_scope']
            for seed in seeds:
                for demos in (2, 3, 6):
                    episode = adapter.generate(seed, copy.deepcopy(setting), demos, 4)
                    report['episodes'] += 1
                    pairs = episode['train'] + episode['test']
                    report['pair_claims'] += len(pairs)
                    inputs = [p['input'] for p in pairs]
                    if len({_digest(g) for g in inputs}) != len(inputs):
                        findings.append({'kind': 'duplicate_input', 'settings': setting,
                                         'seed': seed, 'demos': demos})
                    key = (seed, demos)
                    if key in matched and matched[key] != inputs:
                        findings.append({'kind': 'unmatched_settings', 'seed': seed, 'demos': demos})
                    matched[key] = inputs

                    other = 'dominant_component' if scope == 'all' else 'all'
                    if all(adapter.impl.solve(p['input'], other) == p['output'] for p in episode['train']):
                        findings.append({'kind': 'declared_setting_not_identified', 'settings': setting,
                                         'seed': seed, 'demos': demos})

                    for rival in RIVALS:
                        report['rival_checks'] += 1
                        survives = all(adapter.impl.rival_solve(p['input'], scope, rival) == p['output']
                                       for p in episode['train'])
                        token = f'{scope}:{rival}'
                        if survives:
                            bad = [i for i, p in enumerate(episode['test'])
                                   if adapter.impl.rival_solve(p['input'], scope, rival) != p['output']]
                            if bad:
                                row = {'kind': 'harmful_survivor', 'settings': setting, 'seed': seed,
                                       'demos': demos, 'rival': rival, 'query_indices': bad}
                                harmful.append(row); findings.append(row)
                            else:
                                benign[token] = benign.get(token, 0) + 1
                        else:
                            refuted.setdefault(token, {'seed': seed, 'demos': demos})

                    for pair in episode['test']:
                        g = pair['input']
                        if len(g) == 30 and len(g[0]) == 30:
                            report['substantive_30x30_queries'] += 1
                            cells = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 4]
                            if (len(cells) < 100 or min(r for r, _ in cells) != 0
                                    or max(r for r, _ in cells) != 29
                                    or min(c for _, c in cells) != 0
                                    or max(c for _, c in cells) != 29):
                                findings.append({'kind': 'weak_30x30_stress', 'settings': setting,
                                                 'seed': seed, 'demos': demos})

                    if seed in racket_seeds:
                        for pair in pairs:
                            token = (_digest(episode['program_solution']), _digest(pair['input']))
                            if token not in cache:
                                cache[token] = _grid(apply(episode['program_solution'], pair['input']))
                                report['racket_evaluations'] += 1
                            if cache[token] != pair['output']:
                                findings.append({'kind': 'racket_parity', 'settings': setting,
                                                 'seed': seed, 'demos': demos})

                    if demos == 2:
                        presentation_seed = seed ^ 0x1818057F
                        views = adapter.impl.public_turns(episode, presentation_seed)
                        if views[:1] != adapter.impl.public_turns(episode, presentation_seed, stop_after=1):
                            findings.append({'kind': 'first_turn_prefix', 'settings': setting, 'seed': seed})
                        poisoned = copy.deepcopy(episode)
                        poisoned.update(settings={'secret': True}, seed='PRIVATE', program_solution='PRIVATE')
                        for p in poisoned['train']:
                            p['hidden'] = True
                        for p in poisoned['test']:
                            p['output'] = [[9]]; p['hidden'] = True
                        if views != adapter.impl.public_turns(poisoned, presentation_seed):
                            findings.append({'kind': 'private_leak', 'settings': setting, 'seed': seed})
                        source_indices = []
                        view_ids = []
                        for view in views:
                            query = view['test'][0]['input']
                            source_index = next(i for i, p in enumerate(episode['test']) if p['input'] == query)
                            source_indices.append(source_index)
                            payload = public_challenge_bytes(view)
                            identifier = public_challenge_id(view)
                            if identifier in exports and exports[identifier] != payload:
                                findings.append({'kind': 'public_id_collision', 'id': identifier})
                            exports[identifier] = payload
                            view_ids.append(identifier)
                            report['public_turns'] += 1
                        controller_rows.append({'settings': setting, 'seed': seed,
                                                'source_indices': source_indices,
                                                'view_ids': view_ids,
                                                'answers': [episode['test'][i]['output'] for i in source_indices]})
    finally:
        if bridge is not None:
            bridge.close()

    first_indices = set()
    probe = adapter.generate(0, {'mark_scope': 'all'}, 2, 4)
    for presentation_seed in range(64):
        first = adapter.impl.public_turns(probe, presentation_seed, stop_after=1)[0]['test'][0]['input']
        first_indices.add(next(i for i, p in enumerate(probe['test']) if p['input'] == first))
    report['first_query_indices'] = sorted(first_indices)
    if report['first_query_indices'] != [0, 1, 2, 3]:
        findings.append({'kind': 'presentation_not_varied', 'indices': report['first_query_indices']})
    if _sources() != source:
        raise ValueError('source changed during audit')

    report['status'] = 'passed' if not findings else 'failed'
    report['racket'] = identity
    out.mkdir(parents=True)
    (out / 'public').mkdir()
    for identifier, payload in sorted(exports.items()):
        (out / 'public' / f'{identifier}.json').write_bytes(payload)
    _write(out / 'private/index.json', {'controller_only': True, 'episodes': controller_rows})
    _write(out / 'report.json', report)
    return report


def build_causal(preflight: Path, out: Path) -> dict:
    from arcpuzzles.parametric_worker import _real_evaluator, _grid
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from arcpuzzles.review_sequential_replay import replay_witness

    preflight = Path(preflight)
    out = Path(out)
    if out.exists():
        raise FileExistsError('choose a fresh causal directory')
    receipt = json.loads(preflight.read_text())
    if (receipt.get('task_id') != TASK or receipt.get('status') != 'passed'
            or receipt.get('owner_accepted') is not False):
        raise ValueError('expected this task authoring preflight, not owner acceptance')
    root = _root()
    for row in receipt['source_binding']['files']:
        if hashlib.sha256((root / row['path']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('source changed since preflight: ' + row['path'])
    execution_path = preflight.with_name('execution.json')
    if hashlib.sha256(execution_path.read_bytes()).hexdigest() != receipt['evidence_sha256']['execution.json']:
        raise ValueError('preflight execution evidence changed')
    execution = json.loads(execution_path.read_text())
    episode = next(e for e in execution['episodes']
                   if e['settings'] == {'mark_scope': 'dominant_component'} and e['seed'] == 17)
    pair = episode['test'][-1]
    counterfactual = (BASE / 'largest-area-counterfactual.rkt').read_text()
    adapter = _load('adapter')
    apply, identity, bridge = _real_evaluator(root / 'shared/runtime')
    try:
        actual = _grid(apply(episode['program_solution'], pair['input']))
        wrong = _grid(apply(counterfactual, pair['input']))
    finally:
        bridge.close()
    if actual != pair['output']:
        raise ValueError('qualified program output differs from retained label')
    if actual == wrong:
        raise ValueError('counterfactual did not change the final output')
    witness = {
        'schema': 'arcpuzzles-sequential-dependency-witness-v1',
        'source_binding': receipt['source_binding'],
        'racket': {'backend': 'racket', 'protected': True},
        **CAUSAL_DESCRIPTIONS,
        'cases': [{
            'input': pair['input'],
            'settings': episode['settings'],
            'intermediate_value': adapter.impl.intermediate(pair['input']),
            'program': episode['program_solution'],
            'output': actual,
            'counterfactual_program': counterfactual,
            'counterfactual_output': wrong,
            'ablation': 'wrong_intermediate',
        }],
    }
    raw = (json.dumps(witness, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    progress = {'sequential_dependency': {**CAUSAL_DESCRIPTIONS, 'witness_path': 'witness.json'}}
    validate_sequential_witness(progress, receipt, lambda _: raw)
    replay = replay_witness(root, witness)
    replay.update(status='reviewer_replayed', owner_accepted=False,
                  caller_scope='Reviewer authoring replay, not owner acceptance')
    out.mkdir(parents=True)
    (out / 'witness.json').write_bytes(raw)
    _write(out / 'replay.json', replay)
    return {'status': 'reviewer_replayed',
            'evaluations': 4,
            'changed_cells': sum(a != b for ra, rb in zip(actual, wrong) for a, b in zip(ra, rb)),
            'racket': identity,
            'owner_accepted': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seeds', type=int, nargs='+', default=[0, 1, 17, 43])
    parser.add_argument('--racket-seeds', type=int, nargs='*', default=[0, 17, 43])
    parser.add_argument('--causal-preflight', type=Path)
    args = parser.parse_args()
    report = (build_causal(args.causal_preflight, args.out) if args.causal_preflight
              else run_audit(args.out, seeds=args.seeds, racket_seeds=args.racket_seeds))
    print(json.dumps({k: v for k, v in report.items() if k not in ('source_sha256', 'racket')},
                     sort_keys=True))
    return 0 if report['status'] in ('passed', 'reviewer_replayed') else 1


if __name__ == '__main__':
    raise SystemExit(main())

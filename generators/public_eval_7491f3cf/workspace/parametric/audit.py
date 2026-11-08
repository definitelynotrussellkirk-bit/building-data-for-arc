"""Reusable source-bound structural, protected-Racket, export, and causal audit.

This is authoring evidence only.  It never registers, qualifies, accepts, or
training-admits a public-evaluation family.
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
TASK = HOME.name
CAUSAL_DESCRIPTIONS = {'step_a': 'Parse the framed panels, derive the largest 8-connected divider, and flood the singleton marker side without crossing that divider.', 'intermediate': 'The exact divider cells and input-dependent marker-side region in panel coordinates.', 'step_b': 'Use that region to select panel two inside and panel three outside, admitting both on the divider, then paste the composition into panel four.', 'why_b_depends_on_a': 'Diagonal and offset dividers change which source cells belong to each side; composition cannot be determined from source panels alone.'}
CAUSAL_QUERY_INDEX = 2


def _load_adapter():
    name = '_audit_adapter_' + hashlib.sha256(str(HERE).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, HERE / 'adapter.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


a = _load_adapter()


def _encoded(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _digest(value) -> str:
    return hashlib.sha256(_encoded(value)).hexdigest()


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def source_inventory() -> dict:
    files = []
    for path in sorted(HOME.rglob('*')):
        if (path.is_file() and '__pycache__' not in path.parts
                and (path.suffix in ('.py', '.rkt') or path.name in ('promotion.json', 'public-parent.json'))):
            files.append({'path': path.relative_to(ROOT).as_posix(),
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return {'task_id': TASK, 'files': files}


def _verify_binding(binding: dict) -> None:
    if binding.get('task_id') != TASK or not binding.get('files'):
        raise ValueError('wrong or empty source binding')
    for row in binding['files']:
        path = ROOT / row['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('source binding drift: ' + row['path'])


def counterfactual_program() -> str:
    selected = a.program(a.DEFAULT)
    old = '(lambda (r c v) (not (member (list r c) divider))) 4))'
    new = '(lambda (r c v) (not (member (list r c) divider))) 8))'
    if selected.count(old) != 1:
        raise ValueError('counterfactual source anchor changed')
    return selected.replace(old, new)


def structural(seeds: list[int]) -> dict:
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError('seeds must be nonempty and unique')
    report = {'task_id': TASK, 'status': 'running', 'seeds': list(seeds),
              'episodes': 0, 'pairs': 0, 'public_views': 0,
              'prefix_checks': 0, 'matched_input_checks': 0,
              'finite_rival_checks': 0, 'stress_30x30': 0, 'failures': [],
              'scope': 'Finite declared settings/rivals and sampled seeds; not universal uniqueness.'}
    for seed in seeds:
        matched = None
        for value in a.VALUES:
            setting = {a.PARAMETER: value}
            full = a.generate(seed, setting, 6, 4)
            inputs = [p['input'] for split in ('train', 'test') for p in full[split]]
            if len(inputs) != 10 or len({_digest(g) for g in inputs}) != 10:
                report['failures'].append({'kind': 'duplicate_or_missing_input', 'seed': seed, 'setting': value})
            if matched is not None and matched != inputs:
                report['failures'].append({'kind': 'unmatched_setting_inputs', 'seed': seed})
            matched = inputs
            report['matched_input_checks'] += 1
            if a.survivors(full['train'][:2], value) != ['intended']:
                report['failures'].append({'kind': 'harmful_finite_rival', 'seed': seed, 'setting': value})
            report['finite_rival_checks'] += 1
            if len(full['test'][3]['input']) == 30 and len(full['test'][3]['input'][0]) >= 29:
                report['stress_30x30'] += 1
            else:
                report['failures'].append({'kind': 'missing_30x30_stress', 'seed': seed, 'setting': value})
            for demos, queries in ((2, 1), (2, 4), (3, 4), (6, 2), (6, 4)):
                short = a.generate(seed, setting, demos, queries)
                if short['train'] != full['train'][:demos] or short['test'] != full['test'][:queries]:
                    report['failures'].append({'kind': 'count_prefix', 'seed': seed, 'setting': value,
                                               'demos': demos, 'queries': queries})
                report['episodes'] += 1
                report['pairs'] += demos + queries
                report['prefix_checks'] += 1
            for pseed in range(4):
                first = a.public_turns(seed, setting, 2, pseed, 1)
                all_turns = a.public_turns(seed, setting, 2, pseed, 4)
                if first != all_turns[:1]:
                    report['failures'].append({'kind': 'first_turn_count_leak', 'seed': seed,
                                               'setting': value, 'presentation_seed': pseed})
                report['public_views'] += len(all_turns)
            for i in range(4):
                clean = a.public_view(full, i)
                polluted = copy.deepcopy(full)
                polluted['program_solution'] = 'PRIVATE CANARY'
                polluted['settings'] = {'PRIVATE': True}
                for j, pair in enumerate(polluted['test']):
                    pair['output'] = [[9]]
                    if j != i:
                        pair['input'] = [[7]]
                if a.public_view(polluted, i) != clean:
                    report['failures'].append({'kind': 'private_projection_leak', 'seed': seed,
                                               'setting': value, 'query': i})
    report['status'] = 'passed' if not report['failures'] else 'failed'
    return report


def run_audit(out: Path, seeds: list[int], racket_seeds: list[int]) -> dict:
    from reviewer_support import public_challenge_bytes, public_challenge_id
    from arcpuzzles.parametric_worker import _real_evaluator, _grid
    out = Path(out)
    if out.exists():
        raise FileExistsError('choose a fresh audit output directory')
    binding = source_inventory()
    report = structural(seeds)
    report.update(source_binding=binding, racket_evaluations=0, exports=0,
                  protected_jobs=[], racket=None)
    exports: dict[str, bytes] = {}
    private_rows = []
    apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
    report['racket'] = identity
    try:
        for seed in racket_seeds:
            for value in a.VALUES:
                setting = {a.PARAMETER: value}
                episode = a.generate(seed, setting, 6, 4)
                for pair in episode['train'] + episode['test']:
                    actual = _grid(apply(episode['program_solution'], pair['input']))
                    report['racket_evaluations'] += 1
                    if actual != pair['output']:
                        report['failures'].append({'kind': 'protected_racket_parity', 'seed': seed,
                                                   'setting': value})
                ids = []
                order = a.presentation_order(seed ^ 0x5EED, 4)
                for index in order:
                    view = a.public_view(episode, index)
                    raw = public_challenge_bytes(view)
                    identifier = public_challenge_id(view)
                    if identifier != hashlib.sha256(raw).hexdigest():
                        report['failures'].append({'kind': 'content_id_mismatch', 'id': identifier})
                    if identifier in exports and exports[identifier] != raw:
                        report['failures'].append({'kind': 'public_id_collision', 'id': identifier})
                    exports[identifier] = raw
                    ids.append(identifier)
                report['exports'] += len(ids)
                private_rows.append({'seed': seed, 'settings': setting, 'source_indices': order,
                                     'view_ids': ids,
                                     'answers': [episode['test'][i]['output'] for i in order]})
                report['protected_jobs'].append({'seed': seed, 'settings': setting,
                                                 'demos': 6, 'queries': 4})
    finally:
        bridge.close()
    _verify_binding(binding)
    report['status'] = 'passed' if not report['failures'] else 'failed'
    out.mkdir(parents=True)
    (out / 'public').mkdir()
    for identifier, raw in sorted(exports.items()):
        (out / 'public' / f'{identifier}.json').write_bytes(raw)
    _write(out / 'private' / 'index.json', {'controller_only': True, 'episodes': private_rows})
    _write(out / 'report.json', report)
    return report


def build_causal(preflight: Path, out: Path) -> dict:
    from arcpuzzles.parametric_worker import _real_evaluator, _grid
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from arcpuzzles.review_sequential_replay import replay_witness
    preflight = Path(preflight); out = Path(out)
    if out.exists():
        raise FileExistsError('choose a fresh causal output directory')
    receipt = json.loads(preflight.read_text())
    _verify_binding(receipt['source_binding'])
    execution_path = preflight.with_name('execution.json')
    if hashlib.sha256(execution_path.read_bytes()).hexdigest() != receipt['evidence_sha256']['execution.json']:
        raise ValueError('preflight execution evidence changed')
    execution = json.loads(execution_path.read_text())
    episode = next(e for e in execution['episodes']
                   if e['settings'] == a.DEFAULT and e['seed'] == 17)
    pair = episode['test'][CAUSAL_QUERY_INDEX]
    selected = episode['program_solution']
    counter = counterfactual_program()
    apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
    try:
        actual = _grid(apply(selected, pair['input']))
        wrong = _grid(apply(counter, pair['input']))
    finally:
        bridge.close()
    if actual != pair['output'] or actual == wrong:
        raise ValueError('causal replay did not preserve selected output and change counterfactual')
    witness = {'schema': 'arcpuzzles-sequential-dependency-witness-v1',
               'source_binding': receipt['source_binding'],
               'racket': {'backend': 'racket', 'protected': True},
               **CAUSAL_DESCRIPTIONS,
               'cases': [{'input': pair['input'], 'settings': episode['settings'],
                          'intermediate_value': a.derive(pair['input']),
                          'program': selected, 'output': actual,
                          'counterfactual_program': counter,
                          'counterfactual_output': wrong,
                          'ablation': 'wrong_intermediate'}]}
    raw = (json.dumps(witness, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    validate_sequential_witness(
        {'sequential_dependency': {**CAUSAL_DESCRIPTIONS, 'witness_path': 'witness.json'}},
        receipt, lambda _: raw)
    replay = replay_witness(ROOT, witness)
    replay.update(status='reviewer_replayed', owner_accepted=False,
                  caller_scope='Authoring replay only; not owner qualification or acceptance.')
    out.mkdir(parents=True)
    (out / 'witness.json').write_bytes(raw)
    _write(out / 'replay.json', replay)
    summary = {'status': 'reviewer_replayed', 'racket': identity, 'evaluations': 2,
               'changed_cells': sum(x != y for ar, br in zip(actual, wrong) for x, y in zip(ar, br)),
               'owner_accepted': False}
    _write(out / 'summary.json', summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seeds', type=int, nargs='+', default=list(range(32)))
    parser.add_argument('--racket-seeds', type=int, nargs='*', default=[0, 17])
    parser.add_argument('--causal-preflight', type=Path)
    args = parser.parse_args()
    result = (build_causal(args.causal_preflight, args.out) if args.causal_preflight
              else run_audit(args.out, args.seeds, args.racket_seeds))
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ('source_binding', 'racket', 'protected_jobs')}, sort_keys=True))
    return 0 if result['status'] in ('passed', 'reviewer_replayed') else 1


if __name__ == '__main__':
    raise SystemExit(main())

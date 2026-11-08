"""Opt-in canonical lesson curation: three demonstrations, one preserved query.

Export requires both named rivals to be refuted by demonstrations under every
single-query holdout. This does not change the production generator/worker.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from contextlib import nullcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import normalize_grid

_GAP_PATH = Path(__file__).resolve().parent / 'parametric/gap_variant.py'
_spec = importlib.util.spec_from_file_location('_dc2c4869445c_curator_gap', _GAP_PATH)
_gap = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _gap
_spec.loader.exec_module(_gap)
RuleExecutor = _gap.RuleExecutor
selected_generator = _gap.selected_generator
RIVALS = ('globally_unique_seeds', 'translate_copies')


class CuratorError(ValueError):
    def __init__(self, message, details=None):
        self.details = {} if details is None else deepcopy(details)
        super().__init__(message)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _hash(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def source_identity():
    generator, path, loaded = selected_generator()
    if _sha(path.read_bytes()) != loaded:
        raise CuratorError('selected generator changed during curation')
    raw = _gap.program_for_gap(0)
    if _sha(' '.join(raw.split()).encode())[:12] != generator.RULE_HASH:
        raise CuratorError('canonical rule does not match selected generator pin')
    paths = {'curator': Path(__file__).resolve(), 'generator': path,
             'gap_executor': _GAP_PATH,
             'reviewer_support': Path(sys.modules[normalize_grid.__module__].__file__),
             'racket_bridge': Path(sys.modules[_gap.RacketBridge.__module__].__file__),
             'rule_wrap': Path(sys.modules[_gap.strip_rule_wrapper.__module__].__file__)}
    programs = {'raw_rule': ('canonical.rkt', raw),
                'callable': ('canonical.callable.rkt', _gap.callable_for_gap(0)),
                'bridge_definition': ('canonical.definition.rkt', _gap.bridge_definition_for_gap(0))}
    return {'generator_sha256': loaded, 'rule_hash': generator.RULE_HASH,
            'files': {name: {'path': str(p.resolve().relative_to(_gap.ROOT)),
                             'sha256': _sha(p.read_bytes())} for name, p in paths.items()},
            'programs': {name: {'path': filename, 'sha256': _sha(text.encode())}
                         for name, (filename, text) in programs.items()}}


def _pairs(lesson):
    if (not isinstance(lesson, dict) or set(lesson) != {'train', 'test'}
            or not isinstance(lesson['train'], list) or len(lesson['train']) != 3
            or not isinstance(lesson['test'], list) or len(lesson['test']) != 1):
        raise CuratorError('expected exactly three labeled demonstrations and one labeled query')
    pairs = deepcopy(lesson['train'] + lesson['test'])
    for pair in pairs:
        if not isinstance(pair, dict) or set(pair) != {'input', 'output'}:
            raise CuratorError('each pair must contain only input and output')
        for key in ('input', 'output'):
            try:
                pair[key] = normalize_grid(pair[key])
            except Exception as exc:
                raise CuratorError(f'invalid {key} grid: {exc}') from exc
    if len({_hash(p['input']) for p in pairs}) != 4:
        raise CuratorError('duplicate_input: demonstration/query inputs must be distinct')
    return pairs


def _rival_flags(pair):
    rivals = selected_generator()[0].SEMANTIC_RIVALS
    if not isinstance(rivals, dict) or set(rivals) != set(RIVALS):
        raise CuratorError('rival inventory must contain exactly the two supported named rivals')
    flags = {}
    for name in RIVALS:
        fn = rivals[name]
        if not callable(fn):
            raise CuratorError(f'rival {name} is not callable')
        predictions = []
        try:
            for _ in range(2):
                grid = deepcopy(pair['input'])
                output = normalize_grid(fn(grid))
                if grid != pair['input']:
                    raise ValueError('mutated its input')
                predictions.append(output)
            if predictions[0] != predictions[1]:
                raise ValueError('returned nondeterministic predictions')
        except Exception as exc:
            raise CuratorError(f'rival {name} could not be scored: {exc}') from exc
        flags[name] = predictions[0] != pair['output']
    return flags


def _score_flags(flags):
    holdouts = []
    for query_index in range(4):
        rivals = {}
        for name in RIVALS:
            refuters = [i for i in range(4) if i != query_index and flags[i][name]]
            rivals[name] = {'status': 'refuted' if refuters else (
                'ambiguous' if flags[query_index][name] else 'survived_all'),
                'demonstration_refuting_indices': refuters,
                'query_differs': flags[query_index][name]}
        holdouts.append({'query_pair_index': query_index, 'rivals': rivals,
                         'strict_demo_elimination': all(r['status'] == 'refuted' for r in rivals.values())})
    return {'production': deepcopy(holdouts[3]), 'holdouts': holdouts,
            'strict_all_holdouts': all(r['strict_demo_elimination'] for r in holdouts),
            'refutation_counts': {name: sum(row[name] for row in flags) for name in RIVALS}}


def score_lesson(lesson):
    """Pure finite-rival scoring; supplied labels must be Racket-verified separately."""
    return _score_flags([_rival_flags(pair) for pair in _pairs(lesson)])


def _coverage(flags):
    # At least two refuting pairs per rival ensures one remains in any 3-demo holdout.
    return sum(min(2, sum(row[name] for row in flags)) for name in RIVALS)


def curate_lesson(lesson, *, seed, difficulty='easy', start_index=0, max_attempts=256, executor=None):
    """Return {public, private, report}; never mutate input or change its query.

    A caller-supplied executor must be an actual RuleExecutor, allowing a batch
    to reuse one Racket process. The production exporter is not modified.
    """
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    for name, value in (('start_index', start_index), ('max_attempts', max_attempts)):
        if type(value) is not int or value < 0 or (name == 'max_attempts' and value > 10000):
            raise ValueError(f'{name} must be a nonnegative integer (max_attempts <= 10000)')
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ('easy', 'medium', 'hard')):
        raise ValueError('difficulty must be None, easy, medium or hard')
    if executor is not None and not isinstance(executor, RuleExecutor):
        raise ValueError('executor must be an actual RuleExecutor')
    identity = source_identity()
    pairs = _pairs(lesson)
    query = deepcopy(pairs[3])
    gen = selected_generator()[0]
    report = {'schema': 'dc2c4869445c-lesson-curator-v1', 'source_identity': identity,
              'request': {'seed': seed, 'difficulty': difficulty, 'start_index': start_index,
                          'max_attempts': max_attempts, 'n_train': 3, 'n_test': 1},
              'policy': 'Both named rivals refuted by demonstrations at all four query holdouts',
              'attempts': 0, 'attempted_indices': [], 'accepted_indices': [], 'rejections': [],
              'replacements': [], 'actual_racket_label_calls': 0,
              'scope': 'Optional finite-rival canonical curation; raw sampler and training admission unchanged.'}
    with (RuleExecutor() if executor is None else nullcontext(executor)) as live:
        call_start = live.calls
        try:
            # Do not silently repair an incorrect saved label.
            for i, pair in enumerate(pairs):
                errors = gen.self_check(pair['input'])
                if errors:
                    raise CuratorError(f'pair {i} outside generator domain: {errors}')
                actual = live.apply(pair['input'], 0)
                if actual != pair['output']:
                    raise CuratorError(f'canonical label mismatch at pair {i}')
                pair['output'] = actual
            flags = [_rival_flags(pair) for pair in pairs]
            report['before'] = _score_flags(flags)
            seen = {_hash(p['input']) for p in pairs}
            for offset in range(max_attempts):
                if _coverage(flags) == 2 * len(RIVALS):
                    break
                index = start_index + offset
                report['attempts'] += 1
                report['attempted_indices'].append(index)
                try:
                    grid = gen.generate(seed, index, difficulty=difficulty)
                except ValueError as exc:
                    report['rejections'].append({'sample_index': index, 'reason': 'generation_error', 'detail': str(exc)})
                    continue
                key = _hash(grid)
                if key in seen:
                    report['rejections'].append({'sample_index': index, 'reason': 'duplicate_input', 'input_sha256': key})
                    continue
                seen.add(key)
                errors = gen.self_check(grid)
                if errors:
                    report['rejections'].append({'sample_index': index, 'reason': 'outside_domain', 'details': errors})
                    continue
                candidate = {'input': deepcopy(grid), 'output': live.apply(grid, 0)}
                candidate_flags = _rival_flags(candidate)
                current = _coverage(flags)
                best_index, best_value = None, current
                for slot in range(3):
                    trial = flags[:]
                    trial[slot] = candidate_flags
                    value = _coverage(trial)
                    if value > best_value:
                        best_index, best_value = slot, value
                if best_index is None:
                    report['rejections'].append({'sample_index': index, 'reason': 'no_strict_coverage_gain',
                                                'input_sha256': key, 'rival_refutations': candidate_flags})
                    continue
                report['replacements'].append({'demonstration_index': best_index, 'sample_index': index,
                    'old_input_sha256': _hash(pairs[best_index]['input']), 'new_input_sha256': key,
                    'rival_refutations': candidate_flags, 'coverage_before': current, 'coverage_after': best_value})
                pairs[best_index], flags[best_index] = candidate, candidate_flags
                report['accepted_indices'].append(index)
            report['after'] = _score_flags(flags)
            report['actual_racket_label_calls'] = live.calls - call_start
            if not report['after']['strict_all_holdouts']:
                raise CuratorError('bounded candidate search exhausted before strict lesson support', report)
            if source_identity() != identity:
                raise CuratorError('source files changed during curation', report)
            private = {'train': deepcopy(pairs[:3]), 'test': [deepcopy(pairs[3])]}
            assert private['test'][0] == query
            public = {'train': deepcopy(private['train']), 'test': [{'input': deepcopy(query['input'])}]}
            # Full rescoring is independent of the greedy objective's bookkeeping.
            assert score_lesson(private) == report['after']
            report.update(status='complete_finite_rival_curation', query_preserved=True,
                          public_sha256=_hash(public), private_sha256=_hash(private),
                          original_lesson_sha256=_hash(lesson), runtime_identity=deepcopy(live.bridge.runtime_identity))
            return {'public': public, 'private': private, 'report': report}
        except CuratorError as exc:
            report['actual_racket_label_calls'] = live.calls - call_start
            raise CuratorError(str(exc), {**report, **exc.details}) from exc


def _write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def write_evidence(out, *, lesson_path, seed, difficulty='easy', start_index=0, max_attempts=256):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    raw, identity = None, None
    try:
        identity = source_identity()
        raw = Path(lesson_path).read_bytes()
        result = curate_lesson(json.loads(raw), seed=seed, difficulty=difficulty,
                               start_index=start_index, max_attempts=max_attempts)
        programs = {'canonical.rkt': _gap.program_for_gap(0),
                    'canonical.callable.rkt': _gap.callable_for_gap(0),
                    'canonical.definition.rkt': _gap.bridge_definition_for_gap(0)}
        for filename, program in programs.items():
            (out / filename).write_text(program)
        _write(out / 'private.json', result['private'])
        report = result['report']
        report['input_lesson_sha256'] = _sha(raw)
        report['artifacts'] = {p.name: _sha(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}
        public_bytes = (json.dumps(result['public'], indent=2, sort_keys=True) + '\n').encode()
        report['artifacts']['public.json'] = _sha(public_bytes)
        _write(out / 'report.json', report)
        # Publish the challenge last; failed writes cannot masquerade as success.
        _write(out / 'public.json', result['public'])
        return report
    except BaseException as exc:
        cleanup_errors = []
        for name in ('public.json', 'private.json', 'report.json'):
            try:
                (out / name).unlink(missing_ok=True)
            except OSError as cleanup_error:
                cleanup_errors.append(f'{name}: {cleanup_error}')
        _write(out / 'failure.json', {
            'status': 'failed_partial_artifacts' if cleanup_errors else 'failed_no_export',
            'source_identity': identity, 'input_lesson_sha256': _sha(raw) if raw is not None else None,
            'error': f'{type(exc).__name__}: {exc}', 'cleanup_errors': cleanup_errors,
            'details': getattr(exc, 'details', {})})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lesson', type=Path, required=True)
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--difficulty', choices=('easy', 'medium', 'hard'), default='easy')
    parser.add_argument('--start-index', type=int, default=0)
    parser.add_argument('--max-attempts', type=int, default=256)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(args.out, lesson_path=args.lesson, seed=args.seed,
        difficulty=args.difficulty, start_index=args.start_index, max_attempts=args.max_attempts)
    print(json.dumps({k: report[k] for k in ('status','attempts','accepted_indices','actual_racket_label_calls','query_preserved')}))


if __name__ == '__main__':
    main()

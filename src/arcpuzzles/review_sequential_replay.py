"""Bounded owner replay of private causal witnesses through protected Racket."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

from .runtime import run_process


def _evaluate(root, witness):
    from .parametric_worker import _grid, _local_imports, _real_evaluator
    cases = witness.get('cases')
    if not isinstance(cases, list) or not 1 <= len(cases) <= 16:
        raise ValueError('Witness requires 1..16 cases')
    from .review_programs import strict_programs
    strict_programs(root, [case.get(key) for case in cases
                           for key in ('program', 'counterfactual_program')])
    runtime = root / 'shared/runtime'
    with _local_imports(runtime, runtime):
        apply, identity, bridge = _real_evaluator(runtime)
        results = []
        try:
            for index, case in enumerate(cases):
                grid = _grid(case['input'])
                expected, alternative = _grid(case['output']), _grid(case['counterfactual_output'])
                programs = [case['program'], case['counterfactual_program']]
                if any(type(p) is not str or not p.strip() or len(p.encode()) > 100000 for p in programs):
                    raise ValueError('Witness programs must be nonempty and bounded')
                actual = [_grid(apply(program, grid)) for program in programs]
                if actual != [expected, alternative]:
                    raise ValueError(f'Witness case {index}: executed Racket outputs differ from reported labels')
                if actual[0] == actual[1]:
                    raise ValueError(f'Witness case {index}: counterfactual does not change final output')
                results.append({'index': index, 'input': grid, 'output': actual[0],
                                'counterfactual_output': actual[1],
                                'program_sha256': hashlib.sha256(programs[0].encode()).hexdigest(),
                                'counterfactual_program_sha256': hashlib.sha256(programs[1].encode()).hexdigest()})
        finally:
            bridge.close()
    return {'status': 'owner_replayed', 'racket': identity,
            'evaluations': 2 * len(results), 'cases': results,
            'limits': 'Executed finite counterfactual labels; causal interpretation still requires review, not a universal depth proof.'}


def replay_witness(root, witness, *, timeout=30):
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 60:
        raise ValueError('Witness timeout must be finite in (0, 60] seconds')
    root = Path(root).resolve()
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-causal-replay-') as directory:
        request = Path(directory) / 'request.json'
        request.write_text(json.dumps({'root': str(root), 'witness': witness}, allow_nan=False))
        result = run_process([sys.executable, '-m', 'arcpuzzles.review_sequential_replay', str(request)],
            root, timeout=timeout, extra_env={'PYTHONPATH': str(Path(__file__).resolve().parents[1]),
                                            'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1'})
    if result['timed_out'] or result['exit_code'] != 0:
        raise ValueError('Protected witness replay failed: ' + json.dumps({
            'timed_out': result['timed_out'], 'exit_code': result['exit_code'],
            'stdout': result['stdout'][-1800:], 'stderr': result['stderr'][-1800:]}))
    return json.loads(result['stdout'])


def main():
    try:
        request = json.loads(Path(sys.argv[1]).read_text())
        result = _evaluate(Path(request['root']), request['witness'])
    except Exception as exc:
        print(json.dumps({'error': type(exc).__name__, 'message': str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

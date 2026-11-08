#!/usr/bin/env python3
"""Automatic canonical-memorizer gate on real, deduplicated runner lessons.

Exit 1 means a surviving canonical-lookup/identity rival is wrong on a query
(or a probe error). It is a finite-rival data check, NOT a model evaluation.
Run from packet root through run_with_racket.py; --out is relative to repo.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any


def signature(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(',', ':'))


def canonical_map(pairs: list[dict[str, Any]]) -> dict[str, list[list[int]]]:
    result: dict[str, list[list[int]]] = {}
    for pair in pairs:
        key = signature(pair['input'])
        if key in result and result[key] != pair['output']:
            raise ValueError('conflicting canonical labels for the same input')
        result[key] = pair['output']
    return result


def assess_episode(episode: dict[str, Any], known: dict[str, list[list[int]]]) -> dict[str, Any]:
    """Evaluate a deliberately wrong lookup-table rule against materialized labels."""
    demos, queries = episode['train'], episode['test']
    if not demos:
        raise ValueError('at least one demonstration is required')
    if not queries:
        raise ValueError('at least one query is required')
    def prediction(pair):
        return known.get(signature(pair['input']), pair['input'])
    survives = all(prediction(p) == p['output'] for p in demos)
    wrong = [i for i, p in enumerate(queries) if prediction(p) != p['output']]
    return {
        'survives_demos': survives,
        'wrong_on_query': survives and bool(wrong),
        'wrong_query_indices': wrong if survives else [],
        'exact_replay_demonstrations': sum(signature(p['input']) in known for p in demos),
        'unique_demo_inputs': len({signature(p['input']) for p in demos}),
        'query_rival_predictions': [prediction(p) for p in queries],
    }


WORKER = r'''
from collections import Counter
import hashlib, json
from pathlib import Path
from puzzle_generators import runner
from replay_gate import assess_episode, canonical_map, signature

request=json.loads(Path('replay-request.json').read_text())
known=canonical_map(request['canonical_pairs'])
bundle=runner._load_bundle(request['task_id'])
module=bundle.generator_module
bridge,name=runner._open_bridge_with_rule(bundle.rule_callable_text)
result={**{k:request[k] for k in ('task_id','generator_sha256','tool_sha256','rule_text_sha256')},
        'rival':'canonical_lookup_else_identity',
        'sampler':'puzzle_generators.runner.run_one; n_train=3, n_test=1; seeds=0..N-1; start=0; normal duplicate filtering; trace-only generate wrapper',
        'bands':{}, 'harmful_examples':[], 'probe_errors':[],
        'canonical_occurrences':len(request['canonical_pairs']), 'unique_canonical_inputs':len(known)}
original=module.generate
attempts=[]
def traced(*a, **kw):
    attempts.append({'sample_index':kw.get('sample_index')})
    return original(*a, **kw)
module.generate=traced
try:
    for band in ('easy','medium','hard'):
        counts=Counter(); unique=set()
        for seed in range(request['lessons_per_band']):
            attempts.clear()
            try:
                lesson=runner.run_one(request['task_id'],seed,0,n_train=3,n_test=1,
                        bundle=bundle,bridge=bridge,fn_name=name,difficulty=band)
                assessment=assess_episode(lesson,known)
            except Exception as exc:
                result['probe_errors'].append({'band':band,'seed':seed,'exception':repr(exc)})
                continue
            counts['lessons']+=1;counts['generation_attempts']+=len(attempts)
            counts['unaccepted_attempts']+=len(attempts)-4
            counts['lessons_with_surviving_memorizer']+=assessment['survives_demos']
            counts['harmful_lessons']+=assessment['wrong_on_query']
            counts['duplicate_demo_lessons']+=assessment['unique_demo_inputs']<3
            counts['exact_replay_demonstrations']+=assessment['exact_replay_demonstrations']
            for pair in lesson['train']+lesson['test']:unique.add(signature(pair['input']))
            if assessment['wrong_on_query'] and len(result['harmful_examples'])<9:
                result['harmful_examples'].append({'band':band,'seed':seed,'sample_start':0,
                    'overrides':{},'generation_attempts':list(attempts),
                    'lesson':lesson, 'assessment':assessment,
                    'validator_errors':[module.self_check(p['input']) for p in lesson['train']+lesson['test']]})
        result['bands'][band]={**dict(counts), 'unique_inputs':len(unique)}
finally:bridge.close()
result['passed']=not result['probe_errors'] and not any(b['harmful_lessons'] for b in result['bands'].values())
print(json.dumps(result))
'''


def main() -> int:
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    from probe import ROOT, canonical, sha256
    from audit_targets import all_canonical
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--lessons-per-band', type=int, default=100)
    args = parser.parse_args()
    if args.lessons_per_band < 1:
        parser.error('--lessons-per-band must be positive')
    if len(args.task) != 12 or any(c not in '0123456789abcdef' for c in args.task):
        parser.error('--task must be a 12-character lowercase hexadecimal task ID')
    source = ROOT / 'generators' / args.task / 'generator.py'
    if not source.is_file():
        parser.error('task generator does not exist')
    request = {
        'task_id': args.task, 'lessons_per_band': args.lessons_per_band,
        'canonical_pairs': all_canonical(args.task),
        'generator_sha256': sha256(source), 'tool_sha256': sha256(Path(__file__)),
        'rule_text_sha256': hashlib.sha256(canonical(args.task)['program_solution'].encode()).hexdigest(),
    }
    # Validate label consistency before starting the expensive subprocess.
    canonical_map(request['canonical_pairs'])
    with tempfile.TemporaryDirectory(prefix='replay-gate-') as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, args.task)
        shutil.copy2(Path(__file__), stage / 'replay_gate.py')
        (stage / 'replay-request.json').write_text(json.dumps(request))
        (stage / 'replay_worker.py').write_text(WORKER)
        run = run_process([sys.executable, '-B', 'replay_worker.py'], stage, timeout=600)
        result = ({'passed': False, 'worker_failure': run} if run['exit_code'] or run['timed_out']
                  else json.loads(run['stdout']))
    result['reproduction'] = {
        'cwd': 'packet_root',
        'argv': ['python3', 'run_with_racket.py', 'python3',
                 'generators/779c7c31edc3/workspace/replay_gate.py', '--task', args.task,
                 '--lessons-per-band', str(args.lessons_per_band), '--out', str(args.out)],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result.get(k) for k in ('task_id', 'passed', 'bands', 'probe_errors')}, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

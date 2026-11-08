"""Reusable same-directory adapter audit. No owner acceptance or training writes."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def load_adapter():
    path = Path(__file__).with_name('adapter.py')
    spec = importlib.util.spec_from_file_location('_audit_'+hashlib.sha256(str(path).encode()).hexdigest(), path)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    return adapter


def write_turns(adapter, episode, directory):
    from reviewer_support import public_challenge_bytes
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    names = []
    for index in range(len(episode['test'])):
        data = public_challenge_bytes(adapter.public_turn(episode,index))
        name = hashlib.sha256(data).hexdigest()+'.json'
        path = directory/name
        if path.exists() and path.read_bytes() != data:
            raise ValueError('public digest collision')
        path.write_bytes(data)
        names.append(name)
    return names


def sweep(adapter, seeds):
    from reviewer_support import public_challenge_bytes
    result = dict(episodes=0,pairs=0,matched_input_comparisons=0,public_turns=0,failures=[])
    for seed in seeds:
        full = {s:adapter.generate(seed,{adapter.PARAMETER:s},6,4) for s in adapter.SETTINGS}
        for demos in range(2,7):
            for queries in range(1,5):
                inputs = []
                for setting in adapter.SETTINGS:
                    try:
                        e = adapter.generate(seed,{adapter.PARAMETER:setting},demos,queries)
                        assert len(e['train']) == demos and len(e['test']) == queries
                        assert e['train'] == full[setting]['train'][:demos]
                        assert e['test'] == full[setting]['test'][:queries]
                        keys = [json.dumps(p['input'],sort_keys=True) for p in e['train']+e['test']]
                        assert len(keys) == len(set(keys))
                        inputs.append(keys)
                        for i in range(queries):
                            p = adapter.public_turn(e,i)
                            assert set(p) == {'train','test'} and len(p['test']) == 1
                            assert set(p['test'][0]) == {'input'}
                            public_challenge_bytes(p)  # Exact integer colors, shapes and schema.
                            result['public_turns'] += 1
                        if queries == 4:
                            assert any(len(p['input']) == len(p['input'][0]) == 30 for p in e['test'])
                        result['episodes'] += 1
                        result['pairs'] += demos+queries
                    except Exception as exc:
                        result['failures'].append(dict(seed=seed,setting=setting,demos=demos,
                                                       queries=queries,error=repr(exc)))
                if len(inputs) == len(adapter.SETTINGS):
                    if any(x != inputs[0] for x in inputs[1:]):
                        result['failures'].append(dict(seed=seed,demos=demos,queries=queries,error='settings leak into inputs'))
                    result['matched_input_comparisons'] += 1
    return result


def protected_audit(adapter, directory):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    directory = Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    bridge = RacketBridge()
    cache, wrapped = {}, {}
    private, teaching = [], []
    try:
        identity = bridge.runtime_identity
        assert identity['backend'] == 'racket' and identity['protected'] is True
        def execute(mode, grid):
            key = (mode,json.dumps(grid,separators=(',',':')))
            if key not in cache:
                src = wrapped.setdefault(mode,wrap_rule(adapter.rule(mode)))
                literal = "'("+' '.join('('+' '.join(map(str,row))+')' for row in grid)+')'
                value = bridge.eval_text(f'({src} {literal})')
                if value != adapter.predict(grid,mode):
                    raise AssertionError(f'Python/Racket disagreement for {mode}')
                cache[key] = value
            return cache[key]
        for seed in (0,17):
            for setting in adapter.SETTINGS:
                e = adapter.generate(seed,{adapter.PARAMETER:setting},3,4)
                for pair in e['train']+e['test']:
                    assert execute(setting,pair['input']) == pair['output']
                rivals = list(dict.fromkeys((*adapter.SETTINGS,*adapter.RIVALS)))
                rivals.remove(setting)
                for rival in rivals:
                    # This explicitly fits two visible demos before any query is inspected.
                    predictions = [execute(rival,p['input']) for p in e['train'][:2]]
                    rejected = any(y != p['output'] for y,p in zip(predictions,e['train']))
                    if not rejected:
                        query_conflict = any(execute(rival,p['input']) != p['output'] for p in e['test'])
                        if query_conflict:
                            raise AssertionError(f'underidentified lesson: {seed}/{setting}/{rival}')
                    teaching.append(dict(seed=seed,setting=setting,rival=rival,
                                         rejected_by_two_demos=rejected))
                names = write_turns(adapter,e,directory/'public')
                private.append(dict(seed=seed,settings={adapter.PARAMETER:setting},
                                    program=adapter.program({adapter.PARAMETER:setting}),
                                    train=e['train'],test=e['test'],public_turns=names))
        (directory/'episodes.private.json').write_text(json.dumps(private,sort_keys=True)+'\n')
        return dict(racket=identity,racket_evaluations=len(cache),episodes=len(private),
                    public_turns=sum(len(x['public_turns']) for x in private),teaching=teaching)
    finally:
        bridge.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--seeds',type=int,default=20)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 1000:
        parser.error('--seeds must be in 1..1000')
    if args.out.exists():
        parser.error('--out must be a new directory')
    args.out.mkdir(parents=True)
    adapter = load_adapter()
    result = dict(schema='task-local-parametric-audit-v1',task_id=adapter.TASK,
                  source_sha256=hashlib.sha256(Path(adapter.__file__).read_bytes()).hexdigest(),
                  bounded_scope='finite rivals; not universal uniqueness; no training admission')
    result['sweep'] = sweep(adapter,range(args.seeds))
    result['protected'] = protected_audit(adapter,args.out)
    result['passed'] = not result['sweep']['failures']
    (args.out/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(passed=result['passed'],sweep=result['sweep'],
                         racket_evaluations=result['protected']['racket_evaluations'])))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

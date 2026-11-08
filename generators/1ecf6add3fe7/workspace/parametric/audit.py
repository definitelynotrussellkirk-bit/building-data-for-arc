"""Bounded native-family audit; standalone inside this task's own workspace.

Run through review.py run, or with this checkout's src/shared/runtime on
PYTHONPATH and the bundled RACKET_PATH. No prior checkout is imported. Reports
separate repeated count requests from independently drawn scenes. The tool
refuses to overwrite an output directory and returns nonzero on any failure.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes

HOME = Path(__file__).resolve().parent


def load_adapter():
    spec = importlib.util.spec_from_file_location(
        '_bounded_audit_' + hashlib.sha256(str(HOME).encode()).hexdigest()[:12],
        HOME / 'adapter.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n',encoding='utf-8')


def grid_key(grid):
    return tuple(map(tuple,grid))


def run(out: Path, seeds: int, racket_seeds: list[int]) -> dict:
    out.mkdir(parents=True,exist_ok=False)
    start = time.monotonic()
    a = load_adapter()
    contract = json.loads((HOME/'promotion.json').read_text())
    parameter = next(iter(contract['parameters']))
    task = HOME.parents[1].name
    report = {'schema':'arcpuzzles-task-parametric-audit-v1','task_id':task,
              'status':'running','seeds':list(range(seeds)), 'requests':0,
              'labelled_pairs_across_repeated_requests':0,'matched_inputs':0,
              'public_turns':0,'query_prefix_checks':0,'rival_survivors':[],
              'racket_evaluations':0,'errors':[],
              'limits':'Finite seeds and declared rivals only; Python sweep labels are claims. '
                       'Protected executions are counted separately. No owner acceptance or training admission.'}
    try:
        unique = set()
        stats = []
        for seed in range(seeds):
            full = {s:a.generate(seed,{parameter:s},6,4) for s in a.SETTINGS}
            stats.append({'seed':seed,'query4':a.describe(full[a.SETTINGS[0]]['test'][3]['input'])})
            for ep in full.values():
                inputs = ep['train']+ep['test']
                assert len({grid_key(p['input']) for p in inputs}) == 10
                unique.update(grid_key(p['input']) for p in inputs)
            for demos in range(2,7):
                for queries in range(1,5):
                    previous = None
                    for setting in a.SETTINGS:
                        ep = a.generate(seed,{parameter:setting},demos,queries)
                        assert ep['train'] == full[setting]['train'][:demos]
                        assert ep['test'] == full[setting]['test'][:queries]
                        assert ep['program_solution'] == a.program({parameter:setting})
                        visible = [p['input'] for p in ep['train']+ep['test']]
                        if previous is not None:
                            assert visible == previous
                            report['matched_inputs'] += 1
                        previous = visible
                        for i in range(queries):
                            view = a.public_turn(ep,i)
                            assert set(view) == {'train','test'}
                            assert view['test'] == [{'input':ep['test'][i]['input']}]
                            assert all(set(p) == {'input','output'} for p in view['train'])
                            public_challenge_bytes(view)  # Strict exact-integer grid validation.
                            private_changed = deepcopy(ep)
                            private_changed['program_solution'] = 'PRIVATE SENTINEL'
                            private_changed['settings'] = {'PRIVATE':'SENTINEL'}
                            for p in private_changed['test']:
                                p['output'] = [[9]]
                            for j in range(i+1,len(private_changed['test'])):
                                private_changed['test'][j]['input'] = [[9]]
                            assert a.public_turn(private_changed,i) == view
                            report['public_turns'] += 1
                        assert a.public_turn(ep,0) == a.public_turn(a.generate(seed,{parameter:setting},demos,1),0)
                        report['query_prefix_checks'] += 1
                        report['requests'] += 1
                        report['labelled_pairs_across_repeated_requests'] += demos+queries
        report['distinct_scene_inputs'] = len(unique)
        report['stress_queries'] = stats
        programs = {name:a.rule_for(name) for name in dict.fromkeys(a.SETTINGS+a.RIVALS)}
        episodes, teaching, cache = [], [], {}
        public = out/'public'; public.mkdir()
        turns = out/'turns'; turns.mkdir()
        with RacketBridge() as bridge:
            identity = bridge.runtime_identity
            assert identity['backend'] == 'racket' and identity['protected'] is True
            report['racket'] = identity
            wrapped = {name:wrap_rule(src) for name,src in programs.items()}
            def evaluate(name, grid):
                key = (programs[name],grid_key(grid))
                if key not in cache:
                    literal = "'("+' '.join('('+' '.join(map(str,row))+')' for row in grid)+')'
                    value = bridge.eval_text(f'({wrapped[name]} {literal})')
                    assert value == a.transform(grid,name), f'Racket/Python disagreement for {name}'
                    cache[key] = value
                    report['racket_evaluations'] += 1
                return deepcopy(cache[key])
            for seed in racket_seeds:
                for setting in a.SETTINGS:
                    ep = a.generate(seed,{parameter:setting},3,4)
                    for p in ep['train']+ep['test']:
                        actual = evaluate(setting,p['input'])
                        assert p['output'] == actual
                        p['output'] = actual
                    # Test rivals against only the minimum two demonstrations.
                    lesson = {'seed':seed,'setting':setting,'demos_used':2,'rivals':[]}
                    for name in programs:
                        if name == setting:
                            continue
                        mismatch = []
                        for index,p in enumerate(ep['train'][:2]):
                            actual = evaluate(name,p['input'])
                            if actual != p['output']:
                                mismatch.append(index)
                        if not mismatch:
                            report['rival_survivors'].append({'seed':seed,'setting':setting,'rival':name})
                        row = {'name':name,'program':programs[name],'mismatching_demo_indices':mismatch}
                        if mismatch:
                            p = ep['train'][mismatch[0]]
                            row['counterexample'] = {'input':p['input'],'selected_output':p['output'],
                                                     'rival_output':evaluate(name,p['input'])}
                        lesson['rivals'].append(row)
                    teaching.append(lesson)
                    challenge = {'train':ep['train'],'test':[{'input':p['input']} for p in ep['test']]}
                    raw = public_challenge_bytes(challenge)
                    (public/(hashlib.sha256(raw).hexdigest()+'.json')).write_bytes(raw)
                    for i in range(4):
                        raw = public_challenge_bytes(a.public_turn(ep,i))
                        (turns/(hashlib.sha256(raw).hexdigest()+'.json')).write_bytes(raw)
                    episodes.append({'seed':seed,'settings':{parameter:setting},**ep})
        assert not report['rival_survivors'], 'a declared rival survives the minimum lesson'
        report['status'] = 'passed'
        write_json(out/'episodes.private.json',episodes)
        write_json(out/'teaching.private.json',teaching)
        report['protected_episode_count'] = len(episodes)
        report['protected_selected_labels'] = sum(len(e['train'])+len(e['test']) for e in episodes)
        report['public_challenges'] = len(list(public.glob('*.json')))
        report['saved_single_query_turns'] = len(list(turns.glob('*.json')))
    except Exception as error:
        report['status'] = 'failed'
        report['errors'].append(f'{type(error).__name__}: {error}')
    report['elapsed_seconds'] = round(time.monotonic()-start,3)
    report['source_sha256'] = {name:hashlib.sha256((HOME/name).read_bytes()).hexdigest()
                               for name in ('adapter.py','audit.py','promotion.json','canonical.rkt')}
    write_json(out/'report.json',report)
    return report


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError('must be positive')
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--seeds',type=positive,default=20)
    parser.add_argument('--racket-seeds',type=int,nargs='+',default=[0,17])
    args = parser.parse_args()
    try:
        report = run(args.out,args.seeds,list(dict.fromkeys(args.racket_seeds)))
    except (OSError,ValueError) as error:
        print(str(error),file=sys.stderr)
        return 2
    print(json.dumps({k:v for k,v in report.items() if k not in {'stress_queries','racket','source_sha256'}},indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())

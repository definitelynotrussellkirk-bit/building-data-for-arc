"""Reusable task-local native audit: count/prefix API, teaching, Racket, exports.

Run with the packet interpreter/runtime launcher. It loads only adjacent native.py,
never a predecessor checkout. Public files each contain ONE current query;
private episodes, source programs and answers remain in private/.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes

HERE = Path(__file__).resolve().parent


def load_native():
    path = HERE / 'native.py'
    name = '_audit_native_' + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def key(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def grid_check(g):
    if (type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list
            or not 1 <= len(g[0]) <= 30 or any(type(r) is not list or len(r) != len(g[0])
            or any(type(v) is not int or not 0 <= v <= 9 for v in r) for r in g)):
        raise ValueError('not a rectangular exact-integer ARC grid')


def run(out: Path, seeds: int, racket_seeds: list[int]) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    (out/'public').mkdir(); (out/'private').mkdir()
    m = load_native()
    report = {'task_id':m.TASK_ID, 'passed':False, 'seed_count':seeds,
              'count_requests':0, 'labelled_pair_instances':0,
              'matched_input_comparisons':0, 'prefix_checks':0,
              'public_turns':0, 'teaching_checks':0, 'teaching_failures':[],
              'racket_evaluations':0, 'racket_seeds':racket_seeds}
    seen_inputs = set()
    try:
        for seed in range(seeds):
            maximal = {v:m.generate(seed,{m.PARAMETER:v},6,4) for v in m.VALUES}
            for d in range(2,7):
                for q in range(1,5):
                    lessons = []
                    for v in m.VALUES:
                        e = m.generate(seed,{m.PARAMETER:v},d,q)
                        assert e['train']==maximal[v]['train'][:d]
                        assert e['test']==maximal[v]['test'][:q]
                        report['prefix_checks'] += 1
                        pairs=e['train']+e['test']
                        assert len(pairs)==d+q and len({key(p['input']) for p in pairs})==d+q
                        for p in pairs:
                            grid_check(p['input']); grid_check(p['output'])
                            seen_inputs.add(key(p['input']))
                        report['count_requests'] += 1
                        report['labelled_pair_instances'] += len(pairs)
                        for i in range(q):
                            view=m.public_turn(e,i)
                            assert set(view)=={'train','test'} and len(view['test'])==1
                            assert set(view['test'][0])=={'input'}
                            raw=public_challenge_bytes(view)
                            private_mutation=deepcopy(e)
                            private_mutation['program_solution']='PRIVATE_SENTINEL'
                            private_mutation['seed']='PRIVATE_SENTINEL'
                            private_mutation['settings']={'secret':v}
                            for p in private_mutation['test']: p['output']=[[9]]
                            for j,p in enumerate(private_mutation['test']):
                                if j!=i: p['input']=[[9]]
                            assert raw==public_challenge_bytes(m.public_turn(private_mutation,i))
                            report['public_turns'] += 1
                        lessons.append(e)
                    assert [p['input'] for p in lessons[0]['train']+lessons[0]['test']] == [p['input'] for p in lessons[1]['train']+lessons[1]['test']]
                    report['matched_input_comparisons'] += 1
            for v,e in maximal.items():
                lesson={'train':e['train'][:2],'test':e['test']}
                findings=m.teaching_findings(lesson,v)
                report['teaching_checks'] += 1
                if findings: report['teaching_failures'].append({'seed':seed,'setting':v,'rivals':findings})
        assert not report['teaching_failures'], report['teaching_failures']
        # All declared rules run on every pair in each retained 3-demo/4-query
        # lesson. Compare to independent Python predictions; malformed or failing
        # rivals are errors, never evidence of elimination.
        private=[]; teaching=[]; cache={}
        with RacketBridge(timeout=25, max_calls_before_restart=100) as bridge:
            report['racket']=bridge.runtime_identity
            assert report['racket']['protected'] is True
            for seed in racket_seeds:
                input_lesson=m.generate(seed,{m.PARAMETER:m.VALUES[0]},3,4)
                pairs=input_lesson['train']+input_lesson['test']
                outputs={}
                for name,src in m.hypotheses().items():
                    values=[]
                    for p in pairs:
                        identity=(src,key(p['input']))
                        if identity not in cache:
                            literal="'("+' '.join('('+' '.join(map(str,r))+')' for r in p['input'])+')'
                            actual=bridge.eval_text(f'({wrap_rule(src)} {literal})')
                            grid_check(actual)
                            assert actual==m.predict(p['input'],name),(seed,name)
                            cache[identity]=actual
                            report['racket_evaluations']+=1
                        values.append(cache[identity])
                    outputs[name]=values
                for v in m.VALUES:
                    e=m.generate(seed,{m.PARAMETER:v},3,4)
                    assert outputs[v]==[p['output'] for p in e['train']+e['test']]
                    private.append({'seed':seed,'settings':{m.PARAMETER:v},'episode':e})
                    for rival,values in outputs.items():
                        if rival==v: continue
                        refuters=[i for i in range(2) if values[i]!=outputs[v][i]]
                        query_diff=[i for i in range(4) if values[i+3]!=outputs[v][i+3]]
                        assert refuters or not query_diff, (seed,v,rival)
                        teaching.append({'seed':seed,'setting':v,'rival':rival,
                                         'refuting_demo_indices':refuters,'differing_query_indices':query_diff})
                    for i in range(4):
                        raw=public_challenge_bytes(m.public_turn(e,i))
                        path=out/'public'/(hashlib.sha256(raw).hexdigest()+'.json')
                        if path.exists(): raise ValueError('duplicate public payload')
                        path.write_bytes(raw)
        (out/'private/episodes.json').write_text(json.dumps(private,indent=2)+'\n')
        (out/'private/hypotheses.json').write_text(json.dumps(m.hypotheses(),indent=2)+'\n')
        (out/'private/teaching.json').write_text(json.dumps(teaching,indent=2)+'\n')
        report['distinct_input_grids']=len(seen_inputs)
        report['saved_public_turns']=len(list((out/'public').glob('*.json')))
        report['protected_teaching_rows']=len(teaching)
        report['source_hashes']={p.relative_to(HERE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(HERE.rglob('*')) if p.is_file() and p.suffix in ('.py','.rkt') and '__pycache__' not in p.parts}
        report['limits']='Finite seeds and authored rivals; not universal identifiability, owner acceptance, or training admission.'
        report['passed']=True
    except Exception as exc:
        report['error']=f'{type(exc).__name__}: {exc}'
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        raise
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seeds',type=int,default=20)
    p.add_argument('--racket-seeds',default='0,17')
    a=p.parse_args()
    if a.seeds<1: p.error('--seeds must be positive')
    rs=[int(s) for s in a.racket_seeds.split(',')]
    report=run(a.out,a.seeds,rs)
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_hashes','racket')},indent=2))

if __name__=='__main__': main()

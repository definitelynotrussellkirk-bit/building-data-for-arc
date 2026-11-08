"""Reproducible task census + Racket differential checks + both assigned audits.

Run from packet root via run_with_racket.py; see workspace/README.md.
No shared files are edited. Every report binds exact sources, seeds and inputs.
Do NOT run or read this tool during the separate fresh-solve phase.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / 'shared/runtime'))
# Adapt only this process to the inherited normalizer's portable package name.
# This is read-only: no shared files, installed packages or sys.path globally change.
if 'scripts' not in sys.modules:
    scripts = ModuleType('scripts')
    scripts.__path__ = [str(ROOT / 'shared/tools')]
    sys.modules['scripts'] = scripts
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.runner import wrap_rule


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load_module(path):
    spec = importlib.util.spec_from_file_location('probe_'+hashlib.sha256(str(path).encode()).hexdigest()[:16], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def task_record(task_id):
    rows = [json.loads(line) for line in (ROOT/'shared/data/canonical/puzzles.jsonl').open()
            if line.strip()]
    selected = [r for r in rows if r.get('task_id') == task_id]
    if len(selected) != 1:
        raise ValueError(f'expected one canonical row for {task_id}; got {len(selected)}')
    return selected[0]


def source_identity(module, record):
    return {'task_id': module.TASK_ID,
            'generator_sha256': hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
            'rule_source_sha256': hashlib.sha256(record['program_solution'].encode()).hexdigest(),
            'version': module.VERSION}


class Oracle:
    def __init__(self):
        self.bridge = RacketBridge(timeout=20)
        self.calls = 0

    def apply(self, rule, grid):
        literal = "'(" + ' '.join('('+' '.join(map(str,row))+')' for row in grid) + ')'
        result = self.bridge.eval_text(f'({wrap_rule(rule)} {literal})')
        self.calls += 1
        return result

    def close(self):
        self.bridge.shutdown()


def census(args, oracle):
    diagnostic = load_module(HOME/'generator.py')
    subject = load_module(args.generator.resolve()) if args.generator else diagnostic
    record = task_record(subject.TASK_ID)
    rule = record['program_solution']
    report = {'schema': 'f99263121e8a-review-census-v1', **source_identity(subject,record),
              'diagnostic_generator_sha256': hashlib.sha256((HOME/'generator.py').read_bytes()).hexdigest(),
              'seed_range': [0,args.seeds-1], 'sample_index': 'seed % 11',
              'racket_sample': f'first {args.racket_per_band} seeds in each band',
              'bands': {}, 'failures': [], 'counterexamples': {}, 'canonical': []}
    for split in ('train','test'):
        for index,pair in enumerate(record[split]):
            output = oracle.apply(rule, pair['input'])
            matched = output == pair['output'] == diagnostic.rule_mirror(pair['input'])
            report['canonical'].append({'split':split,'index':index,'matched':matched,
                'surviving_rivals':[name for name,fn in diagnostic.SEMANTIC_RIVALS.items() if fn(pair['input']) == output]})
            if not matched:
                report['failures'].append({'kind':'canonical','split':split,'index':index,'actual':output})
    for band in ('easy','medium','hard'):
        inputs, outputs = set(), set()
        counts, shapes, witnesses = Counter(), Counter(), Counter()
        strict = selfcheck_clean = racket_matched = generated = 0
        for seed in range(args.seeds):
            try:
                grid = subject.generate(seed,seed%11,difficulty=band)
                generated += 1
                expected = diagnostic.rule_mirror(grid)
                inputs.add(digest(grid)); outputs.add(digest(expected))
                counts[len(diagnostic._components_same_color(grid))] += 1
                shapes[f'{len(expected)}x{len(expected[0])}'] += 1
                strict += int(diagnostic.strict_canonical_like(grid))
                errors = subject.self_check(grid,difficulty=band)
                selfcheck_clean += int(not errors)
                if errors:
                    report['failures'].append({'kind':'selfcheck','band':band,'seed':seed,'errors':errors,'input':grid})
                for name,fn in diagnostic.SEMANTIC_RIVALS.items():
                    if fn(grid) != expected:
                        witnesses[name] += 1
                        report['counterexamples'].setdefault(name,{'band':band,'seed':seed,'sample_index':seed%11,
                            'input':grid,'mirror_output':expected,'rival_output':fn(grid)})
                if seed < args.racket_per_band:
                    actual = oracle.apply(rule,grid)
                    racket_matched += int(actual == expected)
                    if actual != expected:
                        report['failures'].append({'kind':'racket_disagreement','band':band,'seed':seed,'input':grid,'actual':actual,'expected':expected})
            except Exception as exc:
                report['failures'].append({'kind':'exception','band':band,'seed':seed,'error':repr(exc)})
        report['bands'][band] = {'attempted':args.seeds,'generated':generated,'unique_inputs':len(inputs),
            'unique_mirror_outputs':len(outputs),'selfcheck_clean':selfcheck_clean,'strict_canonical_like':strict,
            'component_counts':dict(counts),'output_shapes':dict(shapes),'rival_refutations':dict(witnesses),
            'racket_matched':racket_matched,'racket_requested':args.racket_per_band}
    # Exact counterexamples receive authoritative outputs, not only mirror labels.
    for name,case in report['counterexamples'].items():
        case['racket_output'] = oracle.apply(rule,case['input'])
        case['verified_disagreement'] = case['racket_output'] == case['mirror_output'] != case['rival_output']
        if not case['verified_disagreement']:
            report['failures'].append({'kind':'counterexample_verification','rival':name})
    if not args.generator:
        report['override_matrix'] = {'seed_range':[0,4],'textures':list(subject.HELPFUL_TEXTURES),
            'component_counts':[2,3,4,5,6],'dimensions':[[8,9],[10,10],[30,30]],'attempted':0,'passed':0}
        m=report['override_matrix']
        for texture in subject.HELPFUL_TEXTURES:
            for n in range(2,7):
                for h,w in ((8,9),(10,10),(30,30)):
                    for seed in range(5):
                        m['attempted'] += 1
                        kwargs={'texture':texture,'n_components':n,'grid_h':h,'grid_w':w}
                        try:
                            g=subject.generate(seed,0,**kwargs)
                            observed=subject.observe_overrides(g)
                            if subject.self_check(g) or any(observed[k]!=v for k,v in kwargs.items() if k!='texture'):
                                raise AssertionError({'observed':observed,'errors':subject.self_check(g)})
                            m['passed'] += 1
                        except Exception as exc:
                            report['failures'].append({'kind':'override','seed':seed,'kwargs':kwargs,'error':repr(exc)})
        report['lessons']={'seed_range':[10000,10000+args.lessons-1], 'start_index':'(seed-10000) % 10',
            'demos':subject.EXAMPLES_NEEDED,'per_band':{},'note':'mirror-scored; differential Racket sampling is separately counted above'}
        for band in ('easy','medium','hard'):
            count=0
            for seed in range(10000,10000+args.lessons):
                start=(seed-10000)%10
                grids=[subject.generate(seed,start+i,difficulty=band) for i in range(subject.EXAMPLES_NEEDED+1)]
                demos=[{'input':g,'output':subject.rule_mirror(g)} for g in grids[:-1]]
                reasons=subject.lesson_identifiable(demos,{'input':grids[-1]})
                count += int(not reasons)
                if reasons:
                    report['failures'].append({'kind':'lesson','band':band,'seed':seed,'sample_index':start,'reasons':reasons})
            report['lessons']['per_band'][band]={'attempted':args.lessons,'identifiable_against_named_rivals':count}
    report['passed'] = not report['failures']
    return report


def independent_equal_distances(grid):
    def distances(color):
        p=next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color)
        d={p:0}; queue=deque([p])
        while queue:
            r,c=queue.popleft()
            for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if 0<=rr<len(grid) and 0<=cc<len(grid[0]) and grid[rr][cc]!=5 and (rr,cc) not in d:
                    d[rr,cc]=d[r,c]+1; queue.append((rr,cc))
        return d
    d2,d3=distances(2),distances(3)
    return [[8 if v==0 and (r,c) in d2 and (r,c) in d3 and d2[r,c]==d3[r,c] else v
             for c,v in enumerate(row)] for r,row in enumerate(grid)]


def audit(args, oracle):
    diagnostic=load_module(HOME/'generator.py')
    report={'schema':'assigned-adversarial-audits-v1','targets':{},'failures':[]}
    for task_id in ('4e7f50f23507','6e175c009c2a'):
        mod=load_module(ROOT/'generators'/task_id/'generator.py')
        rec=task_record(task_id)
        rule=rec['program_solution']
        entry={**source_identity(mod,rec),'seed_range':[0,args.seeds-1],'sample_index':'seed % 11',
               'bands':['easy','medium','hard'],'attempted':args.seeds*3,'generated':0,
               'selfcheck_clean':0,'racket_checked':0,'racket_matches':0,'rival_matches':0,
               'unique_inputs':0,'max_component_area':0,'canonical_rival_matches':0,
               'counterexample':None}
        def reference(g):
            if task_id=='4e7f50f23507': return independent_equal_distances(g)
            return [[v if v and sum(0<=rr<len(g) and 0<=cc<len(row) and g[rr][cc]==v
                     for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)))==1 else 0
                     for c,v in enumerate(row)] for r,row in enumerate(g)]
        def rival(g):
            out=reference(g)
            if task_id=='4e7f50f23507':
                if out==g:
                    r,c=next((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==0)
                    out[r][c]=8
            else:
                for color,cells in diagnostic._components_same_color(g):
                    if len(cells)>5:
                        for r,c in cells: out[r][c]=0
            return out
        unique=set()
        for band in entry['bands']:
            for seed in range(args.seeds):
                try:
                    g=mod.generate(seed,seed%11,difficulty=band)
                    out=reference(g)
                    unique.add(digest(g)); entry['generated']+=1
                    entry['selfcheck_clean']+=int(not mod.self_check(g,difficulty=band))
                    entry['rival_matches']+=int(rival(g)==out)
                    entry['max_component_area']=max(entry['max_component_area'],max(len(c) for _,c in diagnostic._components_same_color(g)))
                    if seed < args.racket_per_band:
                        actual=oracle.apply(rule,g)
                        entry['racket_checked']+=1
                        entry['racket_matches']+=int(actual==out)
                        if actual!=out: report['failures'].append({'task_id':task_id,'kind':'racket','seed':seed,'band':band,'input':g,'actual':actual,'expected':out})
                except Exception as exc:
                    report['failures'].append({'task_id':task_id,'seed':seed,'band':band,'error':repr(exc)})
        entry['unique_inputs']=len(unique)
        for pair in rec['train']+rec['test']:
            entry['canonical_rival_matches']+=int(rival(pair['input'])==pair['output'])
        entry['canonical_count']=len(rec['train'])+len(rec['test'])
        if task_id=='4e7f50f23507':
            g=[[5 if r in (0,10) or c in (0,14) else 0 for c in range(15)] for r in range(11)]
            g[5][3],g[5][10]=2,3
            entry['finding']='No zero-tie/identity outcomes: always-paint-a-cell fallback cannot be falsified.'
            entry['classification']='reproduced coverage restriction; domain extension, not an incorrect emitted label'
        else:
            g=[[0]*10 for _ in range(7)]
            g[1][1:7]=[2]*6
            for r,c in ((3,7),(4,7),(5,7),(5,8),(5,9)):g[r][c]=7
            entry['finding']='All generated components have area at most five; larger-component suppression survives.'
            entry['classification']='reproduced shortcut undercoverage inside self_check-accepted input domain'
        actual=oracle.apply(rule,g)
        entry['counterexample']={'input':g,'racket_output':actual,'independent_output':reference(g),
            'rival_output':rival(g),'selfcheck_errors':mod.self_check(g),
            'verified_disagreement':actual==reference(g) and actual!=rival(g)}
        if not entry['counterexample']['verified_disagreement']:
            report['failures'].append({'task_id':task_id,'kind':'counterexample'})
        report['targets'][task_id]=entry
    report['passed']=not report['failures']
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['census','audit'])
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--generator',type=Path)
    parser.add_argument('--seeds',type=int,default=300)
    parser.add_argument('--racket-per-band',type=int,default=80)
    parser.add_argument('--lessons',type=int,default=60)
    args=parser.parse_args()
    if not 0<=args.racket_per_band<=args.seeds or args.seeds<1 or args.lessons<1:
        parser.error('require seeds>=1, lessons>=1 and 0<=racket-per-band<=seeds')
    if args.out.exists():
        parser.error(f'refusing to overwrite retained evidence: {args.out}')
    oracle=Oracle()
    try:
        report=census(args,oracle) if args.mode=='census' else audit(args,oracle)
        report['racket_calls']=oracle.calls
    finally:
        oracle.close()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report':str(args.out),'passed':report['passed'],'racket_calls':report['racket_calls'],'failures':len(report['failures'])}))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())

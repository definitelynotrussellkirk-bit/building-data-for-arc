#!/usr/bin/env python3
"""Findings-only deterministic audit; leaves both assigned targets unchanged."""
import argparse, importlib.util, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT/'repo/generators/056999828b88/workspace/connectivity_probe.py'
spec = importlib.util.spec_from_file_location('authoring_oracle_support', HELPER)
support = importlib.util.module_from_spec(spec); spec.loader.exec_module(support)
from puzzle_generators.runner import _apply_rule, _open_bridge_with_rule, wrap_rule
REPO = ROOT/'repo'


def load(tid):
    path = REPO/'generators'/tid/'generator.py'
    spec = importlib.util.spec_from_file_location('audit_'+tid, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    row = next(json.loads(line) for line in (REPO/'shared/data/canonical/puzzles.jsonl').open()
               if json.loads(line).get('task_id') == tid)
    return mod, path, row


def normalize(grid):
    return [[int(v) for v in row] for row in grid]


def crop(grid):
    cells = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    if not cells: return None
    r0,c0 = min(r for r,c in cells),min(c for r,c in cells)
    r1,c1 = max(r for r,c in cells),max(c for r,c in cells)
    return [row[c0:c1+1] for row in grid[r0:r1+1]]


def xform(g,t):
    if t==0: return [row[:] for row in g]
    if t==1: return [list(row) for row in zip(*g[::-1])]
    if t==2: return [row[::-1] for row in g[::-1]]
    if t==3: return [list(row) for row in zip(*g)]
    if t==4: return [row[::-1] for row in g]
    if t==5: return [row[:] for row in g[::-1]]
    raise ValueError(t)


def zones_rival(grid):
    """No components: upper occupied row-band split in half, then lower crop."""
    start = next((r for r,row in enumerate(grid) if any(row)),0)
    end = next((r for r in range(start,len(grid)) if not any(grid[r])),len(grid))
    middle = len(grid[0])//2
    a = crop([row[:middle] for row in grid[start:end]])
    ap = crop([row[middle:] for row in grid[start:end]])
    b = crop(grid[end:])
    if b is None: return [[0]]
    if a is None or ap is None: return b
    matching = [t for t in range(6) if xform(a,t)==ap]
    return xform(b,matching[0] if matching else 0)


def base_report(tid,path,row):
    return {'task_id':tid,'generator_sha256':support.digest(path.read_bytes()),
        'rule_source_sha256':support.digest(row['program_solution'].encode()),
        'command':{'cwd':'packet_root','argv':['python3','run_with_racket.py','python3','../checks/audit_probe.py','--out','../checks/audits.json']},
        'failures':[]}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--out',type=Path,required=True); args=parser.parse_args()
    reports=[]
    tid='c53c24435976'; m,path,row=load(tid); report=base_report(tid,path,row)
    bridge,fn=_open_bridge_with_rule(wrap_rule(row['program_solution']))
    try:
        requests=[]; mismatch=0
        for code in range(1,5):
            g=m.generate(0,0,code=code)
            actual=_apply_rule(bridge,fn,g)
            body=[r[:] for r in g]; body[0][0]=0; cropped=crop(body)
            wanted=m._apply_code(cropped,code)
            bad=g[0][0]!=code
            mismatch+=bad
            requests.append({'seed':0,'sample_index':0,'difficulty':None,'overrides':{'code':code},
                'observed_code':g[0][0], 'override_honored':not bad})
            if bad and actual!=wanted and 'counterexample' not in report:
                report['counterexample']={'seed':0,'sample_index':0,'difficulty':None,'overrides':{'code':code},
                    'input':g,'actual_racket_output':actual,'rival_output':wanted,
                    'rival_description':'apply the explicitly requested transform override instead of emitted command',
                    'validator_errors':m.self_check(g),'in_documented_generator_domain':not m.self_check(g),
                    'emitted_by_generator':True,'observed_code':g[0][0]}
        report.update({'classification':'reproduced override-contract defect','requests':requests,
                       'override_mismatches':mismatch,'request_count':len(requests)})
        if mismatch==0 or 'counterexample' not in report: report['failures'].append('expected defect not reproduced')
    finally: bridge.close()
    reports.append(report)
    tid='3c01bf0d6576'; m,path,row=load(tid); report=base_report(tid,path,row)
    bridge,fn=_open_bridge_with_rule(wrap_rule(row['program_solution']))
    try:
        report['canonical']=[]
        pairs=row['train']+[row['test']]
        for index,pair in enumerate(pairs):
            g=normalize(pair['input']); actual=_apply_rule(bridge,fn,g)
            fits=zones_rival(g)==actual
            report['canonical'].append({'index':index,'oracle_matches_stored':actual==normalize(pair['output']),
                                         'rival_matches':fits,'validator_errors':m.self_check(g)})
        count, matched, hashes = 0,0,set()
        for band in ('easy','medium','hard'):
            for index in range(100):
                g=m.generate(20261002,index,difficulty=band)
                actual=_apply_rule(bridge,fn,g); other=zones_rival(g); errors=m.self_check(g)
                count+=1; matched+=other==actual; hashes.add(support.digest(g))
                if errors or actual!=m._solve_python(g):
                    report['failures'].append({'band':band,'sample_index':index,'input':g,
                                               'validator_errors':errors,'actual_racket_output':actual})
        request={'seed':17,'sample_index':0,'difficulty':'medium',
                 'overrides':{'grid_h':14,'grid_w':18,'texture':'standard','transform':1,'palette_size':5}}
        seed_grid=m.generate(request['seed'],request['sample_index'],difficulty=request['difficulty'],**request['overrides'])
        info,errors=m._analyze(seed_grid)
        stacked=[[0]*18 for _ in range(14)]
        for top,motif in ((0,info['A']),(4,info['Aprime']),(9,info['B'])):
            for r,values in enumerate(motif):
                for c,value in enumerate(values): stacked[top+r][c]=value
        actual=_apply_rule(bridge,fn,stacked); other=zones_rival(stacked); errors=m.self_check(stacked)
        report.update({'classification':'reproduced spatial-layout shortcut; not a label defect',
            'seed':20261002,'bands':['easy','medium','hard'],'sample_indices_per_band':[0,99],
            'draws':count,'unique_inputs':len(hashes),'unique_input_sha256':sorted(hashes),'rival_matches':matched,
            'counterexample':{'input':stacked,'actual_racket_output':actual,'rival_output':other,
                'construction':'reposition unchanged A, Aprime, B crops at (0,0), (4,0), (9,0) in a 14x18 board',
                'source_request':request,'validator_errors':errors,'passes_target_validator':not errors,
                'in_documented_generator_domain':False,
                'domain_note':'satisfies task semantics and validator but cannot be emitted by _place_scene, which forces ar == pr',
                'emitted_by_generator':False}})
        if errors or actual==other: report['failures'].append('stacked-layout counterexample failed')
    finally: bridge.close()
    reports.append(report)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps({'schema':'arc-findings-only-audits-v1','targets':reports},indent=2)+'\n')
    for report in reports:
        summary={key:report[key] for key in ('task_id','classification','failures')}
        summary.update({key:report[key] for key in ('override_mismatches','request_count','draws','unique_inputs','rival_matches') if key in report})
        print(json.dumps(summary))
    return 1 if any(r['failures'] for r in reports) else 0

if __name__=='__main__': raise SystemExit(main())

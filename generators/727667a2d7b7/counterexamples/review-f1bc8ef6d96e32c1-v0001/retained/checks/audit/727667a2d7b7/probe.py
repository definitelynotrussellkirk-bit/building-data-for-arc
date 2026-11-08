"""Bounded read-only audit of selected source; labels here are diagnostics only.

Authoritative labels are generated separately through arcpuzzles apply/generate.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
from collections import Counter

TASK = '727667a2d7b7'
REPO = Path(__file__).resolve().parents[3] / 'repo'
OUT = Path(__file__).resolve().parent
GEN = REPO / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_target', GEN)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()

def components(grid):
    todo = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 6}
    groups = []
    while todo:
        p = min(todo)
        todo.remove(p)
        group = {p}
        stack = [p]
        while stack:
            r, c = stack.pop()
            for q in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                if q in todo:
                    todo.remove(q)
                    group.add(q)
                    stack.append(q)
        groups.append(group)
    return groups

def rotate_rule(grid, *, code4_identity=False):
    result = [row[:] for row in grid]
    for group in components(grid):
        r0 = min(r for r,c in group)
        c0 = min(c for r,c in group)
        h = max(r for r,c in group) - r0 + 1
        w = max(c for r,c in group) - c0 + 1
        code = grid[r0-1][c0] if r0 else 0
        shape = [(r-r0,c-c0) for r,c in group]
        if code == 1 or (code == 4 and code4_identity):
            transformed = shape
        elif code == 2:
            transformed = [(c,h-1-r) for r,c in shape]
        elif code == 3:
            transformed = [(h-1-r,w-1-c) for r,c in shape]
        else:
            transformed = [(w-1-c,r) for r,c in shape]
        mr = min(r for r,c in transformed)
        mc = min(c for r,c in transformed)
        for r,c in group:
            result[r][c] = 0
        for r,c in transformed:
            rr,cc = r0+r-mr,c0+c-mc
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                result[rr][cc] = 6
    return result

def properties(grid):
    groups = components(grid)
    codes = []
    for group in groups:
        r0 = min(r for r,c in group)
        c0 = min(c for r,c in group)
        codes.append(grid[r0-1][c0] if r0 else 0)
    return {'height':len(grid),'width':len(grid[0]),'n_objects':len(groups),
            'cell_counts':sorted(len(c) for c in groups), 'codes':codes,
            'palette_size':len({v for row in grid for v in row}),
            'self_check':g.self_check(grid)}

def main():
    rows = []
    canonical = []
    for line in (REPO / 'shared/data/canonical/puzzles.jsonl').open():
        rec = json.loads(line)
        if rec['task_id'] == TASK:
            canonical.append(rec)
    report = {'task_id':TASK,'generator_sha256':hashlib.sha256(GEN.read_bytes()).hexdigest(),
              'version':g.VERSION,'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'rule_raw_sha256':hashlib.sha256(canonical[0]['program_solution'].encode()).hexdigest(),
              'rule_hash':hashlib.sha256(' '.join(canonical[0]['program_solution'].split()).encode()).hexdigest()[:12]}
    canon_inputs = []
    for split in ('train','test'):
        for i,pair in enumerate(canonical[0][split]):
            props = properties(pair['input'])
            props.update(split=split,index=i,diagnostic_matches_label=rotate_rule(pair['input'])==pair['output'],
                         code4_identity_matches_label=rotate_rule(pair['input'],code4_identity=True)==pair['output'])
            rows.append(props)
            canon_inputs.append(pair['input'])
    report['canonical'] = rows
    report['ordinary_sample'] = {}
    for band in ('easy','medium','hard'):
        inputs = [g.generate(seed,0,difficulty=band) for seed in range(32)]
        props = [properties(inp) for inp in inputs]
        report['ordinary_sample'][band] = {'count':len(inputs), 'unique_inputs':len({digest(i) for i in inputs}),
            'self_check_failures':sum(bool(p['self_check']) for p in props),
            'object_counts':dict(Counter(p['n_objects'] for p in props)),
            'component_sizes':dict(Counter(s for p in props for s in p['cell_counts']))}
    a = g.generate(0,0,difficulty='easy',n_objects=2)
    b = g.generate(0,0,difficulty='easy',n_objects=3)
    report['override'] = {'seed':0,'sample_index':0,'difficulty':'easy','a':{'n_objects':2},
        'b':{'n_objects':3},'byte_identical':a==b,'a_properties':properties(a),'b_properties':properties(b),
        'input_sha256':digest(b)}
    (OUT/'override-input.json').write_text(json.dumps(b)+'\n')
    found = None
    for seed in range(128):
        inputs = [g.generate(seed,i,difficulty='easy') for i in range(5)]
        outputs = [rotate_rule(i) for i in inputs]
        rival_outputs = [rotate_rule(i,code4_identity=True) for i in inputs]
        if all(a==b for a,b in zip(outputs[:4],rival_outputs[:4])) and outputs[4]!=rival_outputs[4]:
            found = {'seed':seed,'sample_index':0,'difficulty':'easy', 'n_train':4,'n_test':1,
                'sampling':'diagnostic direct generate; verify actual production materialization separately',
                'train':[{'input':i,'output':o,'rival_output':r,'properties':properties(i)} for i,o,r in zip(inputs[:4],outputs[:4],rival_outputs[:4])],
                'test':[{'input':inputs[4],'output':outputs[4],'rival_output':rival_outputs[4],'properties':properties(inputs[4])}]}
            break
    report['search'] = {'seeds_considered':seed+1,'max_seeds':128,'found':found is not None,
                        'rival':'code4_identity: code 4 means no rotation; other controls follow selected rotation rule'}
    if found:
        (OUT/'diagnostic-lesson.json').write_text(json.dumps(found,indent=2)+'\n')
        (OUT/'input.json').write_text(json.dumps({'inputs':inputs+[b]+canon_inputs})+'\n')
        report['witness_seed']=found['seed']
        report['racket_input_order']=['lesson train 0','lesson train 1','lesson train 2','lesson train 3','lesson test 0','n_objects=3 override']+['canonical '+p['split']+' '+str(p['index']) for p in rows]
    (OUT/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__ == '__main__':
    main()

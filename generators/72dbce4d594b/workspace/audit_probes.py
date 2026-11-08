"""Reproduce the two assigned findings-only audits; does not modify either task."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def load(repo, tid):
    path = repo / 'generators' / tid / 'generator.py'
    spec = importlib.util.spec_from_file_location('audit_' + tid, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, hashlib.sha256(path.read_bytes()).hexdigest()


def components(grid, same_color=True):
    remaining = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v}
    result = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        todo = [first]
        cells = []
        while todo:
            r,c = todo.pop()
            cells.append((r,c))
            for nr,nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if (nr,nc) in remaining and (not same_color or grid[nr][nc] == grid[r][c]):
                    remaining.remove((nr,nc))
                    todo.append((nr,nc))
        result.append({'color':grid[first[0]][first[1]], 'size':len(cells), 'cells':cells})
    return sorted(result,key=lambda row:row['size'],reverse=True)


def run(repo):
    sys.path.insert(0,str(repo/'shared/runtime'))
    gen, sha = load(repo,'005c7091fce2')
    narrow = []
    distinct = []
    default_invalid = []
    for seed in range(200):
        g = gen.generate(seed,0,difficulty='easy',size_gap='narrow')
        objects = components(g)
        sizes = [obj['size'] for obj in objects]
        if len(sizes)<2 or sizes[0]-sizes[1]!=1:
            narrow.append({'seed':seed,'sample_index':0,'difficulty':'easy','overrides':{'size_gap':'narrow'},
                           'sizes':sizes,'input':g,'self_check':gen.self_check(g)})
        g = gen.generate(seed,0,color_policy='distinct')
        cols = [o['color'] for o in components(g)]
        if len(set(cols)) != len(cols):
            distinct.append({'seed':seed,'sample_index':0,'overrides':{'color_policy':'distinct'},
                             'object_colors':cols,'input':g})
        g = gen.generate(seed,0)
        findings = gen.self_check(g)
        if findings:
            default_invalid.append({'seed':seed,'findings':findings,'input':g})
    mutation = [[0]*7 for _ in range(6)]
    mutation[1][1:5] = [1,1,2,2]
    mutation[4][1] = 3
    first = {'generator_sha256':sha,'seeds_tested':200,
             'narrow_gap_violations':len(narrow),'narrow_examples':narrow[:3],
             'distinct_color_violations':len(distinct),'distinct_examples':distinct[:3],
             'default_self_check_failures':len(default_invalid),'default_failure_examples':default_invalid[:3],
             'mutated_touching_colors':{'input':mutation,'self_check':gen.self_check(mutation),
                                       'monochrome_sizes':[c['size'] for c in components(mutation)]}}
    gen, sha = load(repo,'2d7dbc0024f8')
    ignored = []
    overrange = []
    invalid = []
    for seed in range(200):
        a = gen.generate(seed,0,difficulty='medium',blob_size=2)
        b = gen.generate(seed,0,difficulty='medium',blob_size=5)
        area = sum(v not in (0,8) for row in a for v in row)
        if a == b:
            ignored.append({'seed':seed,'sample_index':0,'difficulty':'medium',
                            'override_values':[2,5],'returned_blob_size':area,'input':a})
        h = gen.generate(seed,0,difficulty='hard')
        area = sum(v not in (0,8) for row in h for v in row)
        if area > 5:
            overrange.append({'seed':seed,'sample_index':0,'difficulty':'hard','blob_size':area,'input':h})
        for band in ('easy','medium','hard'):
            g = gen.generate(seed,0,difficulty=band)
            findings = gen.self_check(g)
            if findings:
                invalid.append({'seed':seed,'difficulty':band,'input':g,'findings':findings})
    second = {'generator_sha256':sha,'seeds_tested':200,
              'ignored_blob_size_pairs':len(ignored),'override_examples':ignored[:2],
              'hard_blob_size_above_declared_max':len(overrange),'range_examples':overrange[:2],
              'default_self_check_failures':len(invalid),'default_checks':600,'default_failure_examples':invalid[:2]}
    return {'schema':'assigned-audit-probes-v1','005c7091fce2':first,'2d7dbc0024f8':second}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    report=run(a.repo.resolve())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({tid:{k:v for k,v in row.items() if not isinstance(v,(dict,list))}
                      for tid,row in report.items() if isinstance(row,dict)},indent=2))

if __name__=='__main__':
    main()

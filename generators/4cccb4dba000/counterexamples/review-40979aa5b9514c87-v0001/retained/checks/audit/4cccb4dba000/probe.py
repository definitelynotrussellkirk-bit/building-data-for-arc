"""Bounded audit: search for diagonal merging caused by misplaced margin."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from reviewer_support import canonical_pairs, find_root, canonical_path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / 'repo'
SOURCE = REPO / 'generators/4cccb4dba000/generator.py'
spec = importlib.util.spec_from_file_location('audit_4cccb4', SOURCE)
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)

def components(g, conn):
    unseen = {(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v}
    out = []
    offsets = [(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1)
               if (dr or dc) and (conn == 8 or abs(dr)+abs(dc) == 1)]
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        pending = [start]
        cells = []
        while pending:
            r,c = pending.pop()
            cells.append((r,c))
            for dr,dc in offsets:
                p = r+dr,c+dc
                if p in unseen:
                    unseen.remove(p)
                    pending.append(p)
        rs,cs = zip(*cells)
        out.append({'cells':sorted(cells), 'bbox':[min(rs),min(cs),max(rs),max(cs)],
                    'red_count':sum(g[r][c] == 2 for r,c in cells)})
    return out

def output(g, conn):
    comp = max(components(g,conn), key=lambda c:c['red_count'])
    r1,c1,r2,c2 = comp['bbox']
    return [row[c1:c2+1] for row in g[r1:r2+1]]

def save(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2)+'\n')

root = find_root(SOURCE)
canonical = []
for p in canonical_pairs(gen.TASK_ID, root=root, labeled_only=True):
    predicted = output(p['input'],4)
    canonical.append({'variant':p['variant'],'split':p['split'],'pair_index':p['pair_index'],
                      'matches':predicted == p['output'], 'rival_output':predicted,
                      'expected_output':p['output']})
overrides = dict(grid_h=12,grid_w=12,n_clusters=3,cluster_size_kind='small',
                 red_count_distribution='ascending',inter_cluster_margin=2)
seen = set()
results = []
witness = None
for sample in range(200):
    grid = gen.generate(0, sample, difficulty=None, **overrides)
    seen.add(json.dumps(grid))
    c4,c8 = components(grid,4), components(grid,8)
    results.append({'sample_index':sample,'components_4':len(c4),'components_8':len(c8),
                    'self_check':gen.self_check(grid)})
    if len(c4) > len(c8) and output(grid,4) != output(grid,8):
        witness = {'seed':0,'sample_index':sample,'difficulty':None,'overrides':overrides,
                   'input':grid,'components_4':c4,'components_8':c8,
                   'self_check':gen.self_check(grid),'rival_name':'most_red_4connected_bbox',
                   'rival_output':output(grid,4),'python_8connected_output':output(grid,8)}
        save('input.json',grid)
        break
save('probe.json', {'task_id':gen.TASK_ID,'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                    'canonical_file_sha256':hashlib.sha256(canonical_path(root).read_bytes()).hexdigest(),
                    'declared_rivals':{name:getattr(gen,name,[]) for name in ('CANONICAL_SHORTCUTS','LESSON_COMPETITORS')},
                    'canonical_comparisons':canonical,'bounded_scan':results,
                    'draws':len(results),'distinct_inputs':len(seen),'witness':witness})
print(json.dumps({'draws':len(results),'distinct_inputs':len(seen),
                  'witness_index':witness['sample_index'] if witness else None,
                  'canonical_matches':sum(p['matches'] for p in canonical),
                  'canonical_denominator':len(canonical)}))

"""Finite source-bound review probe; labels must come from public Racket apply."""
import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from reviewer_support import canonical_pairs, find_root
from puzzle_generators.helpers.selfcheck import components_cells, bbox, normalize

HERE = Path(__file__).resolve().parent
PARSER = argparse.ArgumentParser(description=__doc__)
PARSER.add_argument('--out', type=Path, default=HERE, help='New output directory; retained receipts are never overwritten.')
OUT = PARSER.parse_args().out.resolve()
if (OUT/'finite-probe.json').exists() or (OUT/'racket-inputs.json').exists():
    raise FileExistsError(f'Existing evidence under {OUT}; choose a fresh --out')
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = HERE.parents[1] / 'generator.py'
SPEC = importlib.util.spec_from_file_location('reviewed_generator', SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

def footprints(grid):
    result = []
    for cells in components_cells(grid, same_color=True):
        r1, c1, _, _ = bbox(cells)
        result.append((set(cells), {(r1+c-c1,c1+r-r1) for r,c in cells}, grid[cells[0][0]][cells[0][1]]))
    return result

def interactions(grid):
    fs=footprints(grid)
    collisions=[]
    erase=[]
    for i,(source,target,color) in enumerate(fs):
        for j,(source2,target2,color2) in enumerate(fs):
            if i < j and target & target2:
                collisions.append({'objects':[i,j], 'colors':[color,color2], 'cells':sorted(target & target2)})
            if i != j and target & source2:
                erase.append({'target_object':i,'source_object':j,'colors':[color,color2], 'cells':sorted(target & source2)})
    return {'target_collisions':collisions,'target_source_intersections':erase}

pairs=canonical_pairs(GEN.TASK_ID,root=find_root(SOURCE))
canonical_shapes=set(normalize(cells) for p in pairs for cells in components_cells(p['input'],same_color=True))
seen_shapes=Counter()
first={}
for seed in range(256):
    grid=GEN.generate(seed,0)
    for cells in components_cells(grid,same_color=True):
        seen_shapes[normalize(cells)]+=1
    violations=interactions(grid)
    for kind,cases in violations.items():
        if cases and kind not in first:
            first[kind]={'seed':seed,'sample_index':0,'input':grid,'self_check':GEN.self_check(grid),**violations}
report={'task_id':GEN.TASK_ID,'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'scope':{'seeds':[0,255],'sample_indices':[0,0],'generation_calls':256},
 'canonical_shape_count':len(canonical_shapes),
 'canonical_shapes':[list(shape) for shape in sorted(canonical_shapes)],
 'generated_shape_counts':[{'shape':list(s),'count':n} for s,n in sorted(seen_shapes.items())],
 'canonical_shapes_absent':[list(s) for s in sorted(canonical_shapes-set(seen_shapes))],
 'first_witnesses':first}
(OUT/'finite-probe.json').write_text(json.dumps(report,indent=2)+'\n')
retained=GEN.generate(0,0,n_distinct_colors=2)
inputs=[retained]+[w['input'] for w in first.values()]
(OUT/'racket-inputs.json').write_text(json.dumps(inputs)+'\n')
print(json.dumps({**{k:v for k,v in report.items() if k not in ('generated_shape_counts','first_witnesses')},'first_witnesses':{k:{a:b for a,b in v.items() if a!='input'} for k,v in first.items()}}))

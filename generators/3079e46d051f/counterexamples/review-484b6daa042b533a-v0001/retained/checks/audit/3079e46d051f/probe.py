from __future__ import annotations
from collections import Counter
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK='3079e46d051f'
ROOT=find_root(__file__)
gen, source, source_sha=load_selected_generator(TASK, root=ROOT)

def norm(cells):
    mr=min(r for r,_ in cells); mc=min(c for _,c in cells)
    return tuple(sorted((r-mr,c-mc) for r,c in cells))

def shape_grid(cells, color=2):
    cells=tuple(cells)
    h=max(r for r,_ in cells)+1; w=max(c for _,c in cells)+1
    out=[[0]*w for _ in range(h)]
    for r,c in cells: out[r][c]=color
    return out

def exact_orientation_rival(grid):
    comps=gen._components6(grid)
    exact=[norm(c) for c in comps]
    counts=Counter(exact)
    best=max(counts.values())
    # Stable row-major tie break: _components6 is row-major.
    chosen=next(shape for shape in exact if counts[shape]==best)
    return shape_grid(gen._canon_rot(chosen))

def intended_mirror(grid):
    comps=gen._components6(grid)
    canons=[gen._canon_rot(norm(c)) for c in comps]
    counts=Counter(canons)
    best=max(counts.values())
    chosen=next(shape for shape in canons if counts[shape]==best)
    return shape_grid(chosen)

# Lawful counterexample: a square is first in reading order, while three L
# tetrominoes are rotations of one free shape but have distinct exact orientations.
witness=[[0]*16 for _ in range(10)]
components=[
    [(1,1),(1,2),(2,1),(2,2)],                         # square minority, first
    [(1,6),(1,7),(1,8),(2,6)],                         # L orientation 1
    [(4,1),(5,1),(6,1),(6,2)],                         # L orientation 2
    [(5,8),(6,8),(6,9),(6,10)],                        # L orientation 3
]
for cells in components:
    for r,c in cells: witness[r][c]=6
assert gen.self_check(witness)==[], gen.self_check(witness)
assert intended_mirror(witness)!=exact_orientation_rival(witness)

records=[]; apply_inputs=[]; apply_expected=[]
for band_index,band in enumerate(('easy','medium','hard')):
    for i in range(100):
        seed=307900000+band_index*10000+i
        grid=gen.generate(seed,i,difficulty=band)
        comps=gen._components6(grid)
        exact=[norm(c) for c in comps]
        canons=[gen._canon_rot(x) for x in exact]
        cc=Counter(canons); ec=Counter(exact)
        canonical_mode=max(cc, key=lambda x: cc[x])
        majority_exact={e for e,c in zip(exact,canons) if c==canonical_mode}
        rival=exact_orientation_rival(grid)
        intended=intended_mirror(grid)
        records.append({
            'band':band,'seed':seed,'sample_index':i,
            'component_count':len(comps),
            'canonical_mode_count':cc[canonical_mode],
            'majority_exact_orientation_count':len(majority_exact),
            'unique_exact_mode':sum(v==max(ec.values()) for v in ec.values())==1,
            'rival_matches_intended_mirror':rival==intended,
            'self_check':gen.self_check(grid),
        })
        if len(apply_inputs)<30:
            apply_inputs.append(grid); apply_expected.append(rival)

apply_inputs.append(witness); apply_expected.append(exact_orientation_rival(witness))
summary={
    'schema':'arcpuzzles-audit-probe-v1','task_id':TASK,
    'generator_source':str(source.relative_to(ROOT)),'generator_sha256':source_sha,
    'sample_count':len(records),'bands':['easy','medium','hard'],
    'seed_recipe':'307900000 + band_index*10000 + sample_index; sample_index 0..99',
    'all_self_check_pass':all(not r['self_check'] for r in records),
    'all_majority_motifs_share_one_exact_orientation':all(r['majority_exact_orientation_count']==1 for r in records),
    'all_exact_orientation_modes_unique':all(r['unique_exact_mode'] for r in records),
    'rival_matches_intended_mirror_count':sum(r['rival_matches_intended_mirror'] for r in records),
    'witness':{
        'input':witness,'self_check':gen.self_check(witness),
        'intended_python_mirror':intended_mirror(witness),
        'exact_orientation_rival':exact_orientation_rival(witness),
        'disagrees':intended_mirror(witness)!=exact_orientation_rival(witness),
        'domain_note':'four separated color-6 motifs; three rotated L tetrominoes form the unique rotation-canonical majority; one square minority',
    },
    'racket_batch':{'generated_cases':30,'witness_index':30,'total':len(apply_inputs)},
}
out=Path(__file__).resolve().parent
(out/'probe.json').write_text(json.dumps({'summary':summary,'records':records},indent=2,sort_keys=True)+'\n')
(out/'input.json').write_text(json.dumps(apply_inputs,indent=2)+'\n')
(out/'rival_outputs.json').write_text(json.dumps(apply_expected,indent=2)+'\n')
print(json.dumps(summary,sort_keys=True))

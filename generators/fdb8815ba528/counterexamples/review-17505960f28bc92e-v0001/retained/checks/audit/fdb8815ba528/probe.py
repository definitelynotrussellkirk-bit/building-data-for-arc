"""Source-bound findings-only audit; independent flood fill and bbox renderer."""
from collections import Counter, deque
from itertools import product
from pathlib import Path
import hashlib, json
from reviewer_support import find_root, load_selected_generator, canonical_pairs
HERE=Path(__file__).resolve().parent
ROOT=find_root(__file__)
GEN, SOURCE, DIGEST=load_selected_generator('fdb8815ba528',root=ROOT)
def components(grid):
    seen=set(); result=[]
    for r,row in enumerate(grid):
        for c,color in enumerate(row):
            if not color or (r,c) in seen:continue
            cells={(r,c)};seen.add((r,c));q=deque([(r,c)])
            while q:
                rr,cc=q.popleft()
                for nr,nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                    if 0<=nr<len(grid) and 0<=nc<len(row) and (nr,nc) not in seen and grid[nr][nc]==color:
                        cells.add((nr,nc));seen.add((nr,nc));q.append((nr,nc))
            result.append((color,cells))
    return result
def render(grid, legacy=False):
    out=[[0]*len(grid[0]) for _ in grid]
    for color,cells in components(grid):
        r0=min(r for r,c in cells);r1=max(r for r,c in cells)
        c0=min(c for r,c in cells);c1=max(c for r,c in cells)
        span=(r1-r0+1,c1-c0+1)
        paint=cells if legacy and span not in GEN._LEGACY_BBOX_SPANS else {(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1) if r in (r0,r1) or c in (c0,c1)}
        for r,c in paint:out[r][c]=color
    return out
pairs=canonical_pairs(GEN.TASK_ID,root=ROOT)
canonical=[]
for p in pairs:
    canonical.append({'variant':p['variant'],'split':p['split'],'pair_index':p['pair_index'],'validator_errors':GEN.self_check(p['input']),'independent_matches_label':render(p['input'])==p['output'],'legacy_matches_label':render(p['input'],True)==p['output'],'declared_canonical_shortcuts':{name: rival(p['input'])==p['output'] for name,rival in GEN.CANONICAL_SHORTCUTS.items()}})
counts=Counter();spans=Counter();unique=set(); failures=[]
def check(seed,index,band,overrides,category):
    grid=GEN.generate(seed,index,difficulty=band,**overrides)
    errors=GEN.self_check(grid,meta={'overrides':overrides})
    expected=render(grid);rival=render(grid,True)
    counts[category]+=1;counts['validator_accepted']+=not errors
    counts['legacy_agrees']+=rival==expected
    counts['mirror_agrees']+=GEN.rule_mirror(grid)==expected
    counts['legacy_implementation_agrees']+=GEN._legacy_bbox_span_lookup(grid)==rival
    for color,cells in components(grid):
        span=(max(r for r,c in cells)-min(r for r,c in cells)+1,max(c for r,c in cells)-min(c for r,c in cells)+1)
        spans[str(span)]+=1;counts['components']+=1
    unique.add(hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest())
    if errors or expected!=rival:failures.append({'seed':seed,'sample_index':index,'difficulty':band,'overrides':overrides,'errors':errors,'input':grid})
for band in ('easy','medium','hard'):
    for seed in range(32):
        for index in range(12):check(seed,index,band,{},'default_grids')
    for seed in range(4):
        for profile,n,relation,edge,palette in product(GEN.SCENE_PROFILES,GEN.N_BLOBS,GEN.COLOR_RELATIONS,GEN.EDGE_MODES,GEN.PALETTE_KINDS):
            check(seed,seed,band,dict(scene_profile=profile,n_blobs=n,color_relation=relation,edge_mode=edge,palette_kind=palette),'joint_override_grids')
# Independent witness, within validator grammar; not claimed sampled by generate().
grid=[[0]*10 for _ in range(7)]
for r,c in ((0,0),(0,1),(1,1),(1,2),(1,3),(2,3),(2,4)):grid[r+1][c+1]=2
for r,c in ((4,7),(4,8),(5,7)):grid[r][c]=3
witness={'task_id':GEN.TASK_ID,'generator_sha256':DIGEST,'rule_hash':GEN.RULE_HASH,'provenance':'independently constructed accepted 7x10 input; lead: unresolved review-4bfe455c92aabee9:v0001 legacy-span finding','generated':False,'seed':None,'sample_index':None,'overrides':{},'input':grid,'validator_errors':GEN.self_check(grid),'within_documented_structural_domain':not GEN.self_check(grid),'in_generated_support':'not claimed; static generate branches never use generalized shape tables','independent_expected_output':render(grid),'rival_output':render(grid,True),'difference_coordinates':[[r,c] for r in range(len(grid)) for c in range(len(grid[0])) if render(grid)[r][c]!=render(grid,True)[r][c]]}
(HERE/'input.json').write_text(json.dumps(grid)+'\n')
(HERE/'witness.json').write_text(json.dumps(witness,indent=2)+'\n')
report={'task_id':GEN.TASK_ID,'generator_sha256':DIGEST,'rule_hash':GEN.RULE_HASH,'rule_file_sha256':'pending official apply receipt','source_path':str(SOURCE),'lead':'generators/fdb8815ba528/evidence/review_index.json; review-4bfe455c92aabee9:v0001 unresolved legacy-span audit','counts':dict(counts),'unique_input_hashes':len(unique),'component_bbox_spans':dict(spans),'default_settings':{'bands':['easy','medium','hard'],'seeds':[0,31],'sample_indices':[0,11]},'joint_override_settings':{'bands':['easy','medium','hard'],'seeds':[0,3],'sample_index':'same integer as seed','combinations_per_seed_band':144},'canonical':canonical,'failures':failures,'legacy_span_set':sorted(map(list,GEN._LEGACY_BBOX_SPANS)),'declared_competitors':list(GEN.LESSON_COMPETITORS),'legacy_rival_declared':any(r is GEN._legacy_bbox_span_lookup for r in GEN.LESSON_COMPETITORS.values()),'novel_span_witness_registered':any(r is GEN._witness_novel_bbox_span for r in GEN.SEMANTIC_WITNESSES.values()),'scope':'Finite source-bound Python sampling and independent oracle; actual Racket witness retained separately. Not a semantic battery or universal identifiability claim.'}
(HERE/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'generator_sha256':DIGEST,'counts':dict(counts),'unique_input_hashes':len(unique),'spans':dict(spans),'canonical_pairs':len(canonical),'witness_validator_errors':witness['validator_errors'],'witness_differences':len(witness['difference_coordinates']),'failures':len(failures)},sort_keys=True))

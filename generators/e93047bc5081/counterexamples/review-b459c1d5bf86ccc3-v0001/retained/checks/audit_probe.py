"""Run from a prepared runtime containing both immutable audit targets."""
from __future__ import annotations
import importlib, json, hashlib, copy, sys
from pathlib import Path
from scripts.canonical_profile_gate import canonical_pairs
from scripts.generator_semantic_gate import _RuleOracle

report={'schema':'two-target-audit-probe-v1','data_use':'review-only-never-train','targets':{}}
for task in ('f4a707214fb5','e93047bc5081'):
    gen=importlib.import_module(f'puzzle_generators.per_puzzle.{task}.generator')
    oracle=_RuleOracle(task)
    row={'generator_sha256':hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
         'generator_version':gen.VERSION,'generation_failures':[],'parity_failures':[],
         'self_check_failures':[],'canonical_failures':[],'draws':0,'canonical_pairs':0}
    report['targets'][task]=row
    try:
        if not oracle.ready:
            row['oracle_error']=oracle.error
            continue
        for i,pair in enumerate(canonical_pairs(task)):
            output,error=oracle.apply(pair['input'])
            row['canonical_pairs']+=1
            if error or output!=pair['output']:
                row['canonical_failures'].append({'pair':i,'error':error,'actual':output,'expected':pair['output']})
        reference_mirror=gen.rule_mirror if task=='f4a707214fb5' else gen._python_apply
        ordinary=[]
        for band in ('easy','medium','hard'):
            for index in range(32):
                seed=57_000+index
                try:
                    grid=gen.generate(seed,index,difficulty=band)
                    row['draws']+=1
                    errors=gen.self_check(grid)
                    if errors: row['self_check_failures'].append({'seed':seed,'index':index,'band':band,'errors':errors})
                    output,error=oracle.apply(grid)
                    if error or output!=reference_mirror(grid):
                        row['parity_failures'].append({'seed':seed,'index':index,'band':band,'error':error,'input':grid,'actual':output})
                    ordinary.append((seed,index,band,grid,output))
                except Exception as exc:
                    row['generation_failures'].append({'seed':seed,'index':index,'band':band,'error':repr(exc)})
        if task=='f4a707214fb5':
            row['zero_only_rival_agrees']=sum([r for r in output if any(value==8 for value in r)]==output for *_,output in ordinary)
            for seed,index,band,grid,output in ordinary:
                (cells1,b1),(cells2,b2)=gen._big_figures(grid)
                fh,fw=b1[2]-b1[0]+1,b1[3]-b1[1]+1
                choice=None
                for rr in range(fh):
                    if any(grid[b1[0]+rr][b1[1]+cc] != grid[b2[0]+rr][b2[1]+cc] for cc in range(fw)):
                        continue
                    for cc in range(fw):
                        old=grid[b2[0]+rr][b2[1]+cc]
                        colors={value for grow in grid for value in grow}-{0,8,old}
                        if old!=0 and colors:
                            choice=(rr,cc,old,min(colors)); break
                    if choice: break
                if choice:
                    rr,cc,old,new=choice
                    mutated=copy.deepcopy(grid); mutated[b2[0]+rr][b2[1]+cc]=new
                    actual,error=oracle.apply(mutated)
                    row['color_only_branch_counterexample']={
                        'seed':seed,'sample_index':index,'difficulty':band,
                        'source_input':grid,'source_output':output,
                        'mutation':{'row':b2[0]+rr,'col':b2[1]+cc,'old':old,'new':new,'crop_row':rr},
                        'input':mutated,'racket_output':actual,'oracle_error':error,
                        'zero_only_rival':[r for r in actual if any(value==8 for value in r)] if actual is not None else None,
                        'self_check_errors':gen.self_check(mutated),
                        'classification':'authority-valid extension excluded by the declared shared-picture grammar; not a generated-label bug'}
                    break
        else:
            seed,index,band,grid,output=ordinary[0]
            colors={v for gr in grid for v in gr}-{0,9}
            chosen=min(colors)
            # Replace all instances of one object color with True. If a
            # separate color-1 object exists, keep it distinct via color 8.
            mutant=copy.deepcopy(grid)
            for r,gr in enumerate(grid):
                for c,v in enumerate(gr):
                    if v==chosen: mutant[r][c]=True
                    elif v==1: mutant[r][c]=8 if 8 not in colors else 7
            actual,error=oracle.apply(mutant)
            row['boolean_counterexample']={
                'seed':seed,'sample_index':index,'difficulty':band,'original_color':chosen,
                'source_input':grid,'input':mutant,'self_check_errors':gen.self_check(mutant),
                'racket_output':actual,'oracle_error':error}
            observed=gen.observe_overrides(grid)
            requested={'marker_side':'bottom' if observed['marker_side']!='bottom' else 'top'}
            row['ignored_meta_counterexample']={'seed':seed,'sample_index':index,'difficulty':band,
                'observed':observed,'requested':requested,'self_check_errors':gen.self_check(grid,meta={'overrides':requested})}
    finally:
        oracle.close()
Path(sys.argv[1]).write_text(json.dumps(report,indent=2)+'\n')
for task,row in report['targets'].items():
    print(task,json.dumps({k:v for k,v in row.items() if k not in ('color_only_branch_counterexample','boolean_counterexample','ignored_meta_counterexample')},indent=2))
    for key in ('color_only_branch_counterexample','boolean_counterexample','ignored_meta_counterexample'):
        if key in row:
            print(key,json.dumps({k:v for k,v in row[key].items() if 'input' not in k and 'output' not in k and k!='zero_only_rival'},indent=2))

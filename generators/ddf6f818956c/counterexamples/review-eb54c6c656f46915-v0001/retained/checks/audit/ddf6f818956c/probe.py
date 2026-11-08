"""Findings-only source-bound Python probes; selected Racket replay is separate."""
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK='ddf6f818956c'
ROOT=find_root(__file__)
OUT=Path(__file__).resolve().parent
MOD,SOURCE,SOURCE_SHA=load_selected_generator(TASK,root=ROOT)


def digest(value):
    if not isinstance(value,bytes):value=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(value).hexdigest()


def facts(grid):
    red=[(r,c) for r,line in enumerate(grid) for c,v in enumerate(line) if v==2]
    gray=[(r,c) for r,line in enumerate(grid) for c,v in enumerate(line) if v==5]
    top,bot=min(r for r,c in red),max(r for r,c in red)
    left,right=min(c for r,c in red),max(c for r,c in red)
    return {'bbox':[top,left,bot,right], 'top_solid':all(grid[top][c]==2 for c in range(left,right+1)),
            'left_solid':all(grid[r][left]==2 for r in range(top,bot+1)),
            'right_solid':all(grid[r][right]==2 for r in range(top,bot+1)),
            'gray':gray,'gray_inside':sum(top<r<bot and left<c<right for r,c in gray),
            'shape':[len(grid),len(grid[0])]}


def predicted(grid,*,outside_only=False):
    f=facts(grid);top,left,bot,right=f['bbox']
    result=[[0 if v==5 else v for v in line] for line in grid]
    for gr,gc in f['gray']:
        if outside_only and top<=gr<=bot and left<=gc<=right:
            nr,nc=gr,gc
        elif f['top_solid']:
            nr=2*(top if 2*gr<top+bot else bot)-gr;nc=gc
        else:
            nr=gr;nc=2*(left if 2*gc<left+right else right)-gc
        if 0<=nr<len(grid) and 0<=nc<len(grid[0]):result[nr][nc]=5
    return result


rows=[json.loads(line) for line in canonical_path(ROOT).open() if json.loads(line).get('task_id')==TASK]
programs={row['program_solution'] for row in rows}
assert len(programs)==1
program=next(iter(programs))
canonical=[];unique={};selected=[]
for vi,row in enumerate(rows):
    for split in ('train','test'):
        for pi,pair in enumerate(row[split]):
            grid=pair['input'];f=facts(grid)
            rec={'variant':vi,'split':split,'pair_index':pi,'input_sha256':digest(grid),'facts':f,'self_check_errors':MOD.self_check(grid),'python_mirror_matches_supplied':predicted(grid)==pair['output'],'outside_only_rival_matches_supplied':predicted(grid,outside_only=True)==pair['output']}
            canonical.append(rec);unique[digest(grid)]=rec
            if vi==0 and split=='train' and pi in (0,2):
                selected.append({'identity':f'canonical-v{vi}-{split}-{pi}','input':grid,'expected':pair['output'],'rival':predicted(grid,outside_only=True),'self_check_errors':rec['self_check_errors'],'origin':'canonical_only; rejected by selected generator self_check'})
counts={'draws':0,'self_check_accepted':0,'all_gray_outside':0,'outside_only_rival_agrees_with_python_mirror':0,'vertical':0,'horizontal':0}
for seed in range(200):
    for difficulty in ('easy','medium','hard'):
        index=seed*19
        grid=MOD.generate(seed,index,difficulty=difficulty)
        f=facts(grid);errors=MOD.self_check(grid,difficulty=difficulty,meta={'overrides':{}})
        counts['draws']+=1;counts['self_check_accepted']+=not bool(errors)
        counts['all_gray_outside']+=f['gray_inside']==0
        counts['outside_only_rival_agrees_with_python_mirror']+=predicted(grid,outside_only=True)==predicted(grid)
        counts['vertical' if f['top_solid'] else 'horizontal']+=1
        if seed==0 and difficulty in ('easy','hard'):
            selected.append({'identity':f'generated-seed0-index{index}-{difficulty}','seed':seed,'sample_index':index,'difficulty':difficulty,'overrides':{},'input':grid,'expected':predicted(grid),'rival':predicted(grid,outside_only=True),'self_check_errors':errors,'origin':'generated_input accepted by self_check; expected/rival are Python predictions pending Racket replay'})
overrides=[]
for request in ({'grid_h':10,'grid_w':10},{'frame_h':8,'frame_w':8},{'grid_h':18,'grid_w':18,'reflection_axis':'horizontal'}):
    grid=MOD.generate(0,0,difficulty='medium',**request);f=facts(grid)
    meta={'overrides':request}
    rec={'seed':0,'sample_index':0,'difficulty':'medium','overrides':request,'facts':f,'input':grid,'input_sha256':digest(grid),'self_check_errors':MOD.self_check(grid,difficulty='medium',meta=meta),'observed_frame_shape':[f['bbox'][2]-f['bbox'][0]+1,f['bbox'][3]-f['bbox'][1]+1]}
    overrides.append(rec)
    if len(overrides)==1:selected.append({'identity':'generated-ignored-grid10-override','input':grid,'expected':predicted(grid),'rival':predicted(grid,outside_only=True),'self_check_errors':rec['self_check_errors'],'seed':0,'sample_index':0,'difficulty':'medium','overrides':request,'origin':'generated_input; requested legal dimensions silently ignored; Python expected pending Racket replay'})
report={'status':'python_inspection_only_pending_selected_racket','task_id':TASK,'generator_sha256':SOURCE_SHA,'canonical_ledger_sha256':digest(canonical_path(ROOT).read_bytes()),'rule_raw_sha256':digest(program.encode()),'rule_normalized_short_hash':digest(' '.join(program.split()).encode())[:12],'canonical_rows':len(rows),'canonical_records':canonical,'unique_canonical_inputs':len(unique),'canonical_self_check_rejected':sum(bool(x['self_check_errors']) for x in canonical),'default_draw_scope':{'seeds':'0..199','sample_index':'seed*19','difficulties':['easy','medium','hard'],'overrides':{},'results':counts},'override_probes':overrides,'selected_cases':[{k:v for k,v in p.items() if k not in ('input','expected','rival')} for p in selected],'notes':['Existing unresolved audit source hash matches current source; these are independent corroborations, not newly introduced regressions.','Canonical-domain rejection is visible in self_check. Legal override mismatch is silently accepted even when requested overrides are passed to self_check meta.','No Racket execution performed by this Python probe.']}
for name,value in [('python-report.json',report),('input.json',{'inputs':[p['input'] for p in selected]}),('selected-expected-rivals.json',selected)]:
    path=OUT/name
    if path.exists():raise FileExistsError(path)
    path.write_text(json.dumps(value,indent=2)+'\n')
(OUT/'reference-program.rkt').write_text(program)
(OUT/'generator-source.py').write_bytes(SOURCE.read_bytes())
print(json.dumps({'status':'ok','canonical_records':len(canonical),'unique_canonical_inputs':len(unique),'self_check_rejected':report['canonical_self_check_rejected'],'draws':counts,'selected_racket_cases':len(selected),'generator_sha256':SOURCE_SHA,'rule_raw_sha256':report['rule_raw_sha256']}))

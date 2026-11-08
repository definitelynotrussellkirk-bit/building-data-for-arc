"""Public selected-source audit probe; run through outer review.py run."""
import argparse, hashlib, json, sys
from fractions import Fraction
from pathlib import Path
ROOT=Path.cwd().resolve()
sys.path.insert(0,str(ROOT/'shared/runtime'))
from reviewer_support import canonical_pairs, load_selected_generator
ID='75be7448827f'
OUT=ROOT.parent/'checks/audit'/ID

def frames(g):
    seen=set(); result=[]
    for r,row in enumerate(g):
        for c,v in enumerate(row):
            if v!=1 or (r,c) in seen: continue
            stack=[(r,c)];seen.add((r,c));cells=[]
            while stack:
                y,x=stack.pop();cells.append((y,x))
                for yy,xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                    if 0<=yy<len(g) and 0<=xx<len(g[0]) and g[yy][xx]==1 and (yy,xx) not in seen:
                        seen.add((yy,xx));stack.append((yy,xx))
            r1=min(y for y,x in cells);r2=max(y for y,x in cells)
            c1=min(x for y,x in cells);c2=max(x for y,x in cells)
            border={(y,x) for y in range(r1,r2+1) for x in range(c1,c2+1) if y in (r1,r2) or x in (c1,c2)}
            if set(cells)!=border or r2-r1<2 or c2-c1<2: continue
            crop=[row[c1+1:c2] for row in g[r1+1:r2]]
            count=sum(v!=0 for row in crop for v in row)
            area=sum(len(row) for row in crop)
            result.append({'bbox':[r1,c1,r2,c2],'count':count,'area':area,'density':str(Fraction(count,area)),'crop':crop})
    return result

def select(g,mode):
    ff=frames(g)
    if not ff:return None
    if mode=='density':score=lambda f:Fraction(f['count'],f['area'])
    elif mode=='count':score=lambda f:f['count']
    elif mode=='count_density':score=lambda f:(f['count'],Fraction(f['count'],f['area']))
    else:raise ValueError(mode)
    return max(ff,key=score)['crop']

def main():
    m,source,sha=load_selected_generator(ID,root=ROOT)
    canon=canonical_pairs(ID,root=ROOT,labeled_only=True)
    records=[];inputs=[]
    for p in canon:
        g=p['input']; idx=len(inputs); inputs.append(g)
        records.append({'input_index':idx,'origin':'canonical','variant':p['variant'],'split':p['split'],'pair_index':p['pair_index'],'input':g,'canonical_output':p['output'],'frames':frames(g),'density_rival_output':select(g,'density'),'density_fits_canonical':select(g,'density')==p['output'],'count_density_rival_output':select(g,'count_density'),'count_density_fits_canonical':select(g,'count_density')==p['output'],'count_fits_canonical':select(g,'count')==p['output']})
    for i in range(32):
        g=m.generate(0,i,difficulty='medium');idx=len(inputs);inputs.append(g)
        ff=frames(g);mx=max(f['count'] for f in ff) if ff else 0
        records.append({'input_index':idx,'origin':'generated','seed':0,'sample_index':i,'difficulty':'medium','overrides':{},'input':g,'self_check_errors':m.self_check(g,difficulty='medium'),'frames':ff,'density_rival_output':select(g,'density'),'count_mirror_output':select(g,'count'),'count_density_rival_output':select(g,'count_density'),'maximum_count_tied':sum(f['count']==mx for f in ff)>1,'density_count_disagree':select(g,'density')!=select(g,'count')})
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'input.json').write_text(json.dumps(inputs)+'\n')
    data={'task_id':ID,'generator_sha256':sha,'source_path':str(source.relative_to(ROOT)),'seed_range':[0,0],'sample_indices':[0,31],'records':records,'declared_CANONICAL_SHORTCUTS':str(getattr(m,'CANONICAL_SHORTCUTS',None)),'declared_LESSON_COMPETITORS':str(getattr(m,'LESSON_COMPETITORS',None))}
    (OUT/'probe.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'generator_sha256':sha,'canonical_pairs':len(canon),'density_fits_canonical':sum(r.get('density_fits_canonical',False) for r in records),'count_fits_canonical':sum(r.get('count_fits_canonical',False) for r in records),'generated':32,'count_ties':sum(r.get('maximum_count_tied',False) for r in records),'density_count_disagree':sum(r.get('density_count_disagree',False) for r in records)}))

if __name__=='__main__':main()

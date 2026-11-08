from __future__ import annotations
import hashlib, json
from reviewer_support import canonical_pairs, find_root, load_selected_generator
ROOT=find_root(__file__)
M, PATH, SHA=load_selected_generator('f3076f3858b4', root=ROOT)

def clipping_facts(grid):
    comps=M._components(grid)
    multi=[(color,cells) for color,cells in comps if len(cells)>1]
    singles=[(color,cells[0]) for color,cells in comps if len(cells)==1]
    if len(multi)!=1: return {'template_count':len(multi),'clipping_markers':[]}
    cells=multi[0][1]
    r0=min(r for r,c in cells);r1=max(r for r,c in cells)
    c0=min(c for r,c in cells);c1=max(c for r,c in cells)
    th,tw=r1-r0+1,c1-c0+1
    h,w=len(grid),len(grid[0])
    return {'template_bbox':[th,tw], 'clipping_markers':[[r,c] for _,(r,c) in singles if r+th>h or c+tw>w]}
canonical=[]
for pair in canonical_pairs('f3076f3858b4', root=ROOT, labeled_only=True):
    facts=clipping_facts(pair['input'])
    canonical.append({
      'variant':pair['variant'],'split':pair['split'],'pair_index':pair['pair_index'],
      'self_check':M.self_check(pair['input']), **facts,
    })
production=[]
for band in ('easy','medium','hard'):
    for index in range(100):
        grid=M.generate(0xF3076, index, difficulty=band)
        production.append({'band':band,'index':index,'shape':[len(grid),len(grid[0])],
                           'self_check':M.self_check(grid),**clipping_facts(grid)})
base=M.generate(77,3)
base_hash=hashlib.sha256(json.dumps(base,separators=(',',':')).encode()).hexdigest()
overrides={}
for name,value in [('grid_h',6),('grid_h',18),('grid_w',6),('grid_w',20),
                   ('n_markers',1),('n_markers',6),('template_size',2),('template_size',7),
                   ('density','sparse'),('texture','warm')]:
    grid=M.generate(77,3,**{name:value})
    key=f'{name}={value!r}'
    overrides[key]={
       'same_as_default':grid==base,'shape':[len(grid),len(grid[0])],
       'components':[[color,len(cells)] for color,cells in M._components(grid)],
    }
report={
 'task_id':'f3076f3858b4','generator_path':str(PATH),'generator_sha256':SHA,
 'canonical':canonical,
 'canonical_pairs_rejected_by_self_check':sum(bool(x['self_check']) for x in canonical),
 'canonical_pairs_with_clipping':sum(bool(x['clipping_markers']) for x in canonical),
 'production_draws':len(production),
 'production_self_check_failures':sum(bool(x['self_check']) for x in production),
 'production_draws_with_clipping':sum(bool(x['clipping_markers']) for x in production),
 'production_shape_minmax':{
   'height':[min(x['shape'][0] for x in production),max(x['shape'][0] for x in production)],
   'width':[min(x['shape'][1] for x in production),max(x['shape'][1] for x in production)],
 },
 'canonical_shape_minmax':{'height':[5,5],'width':[6,8]},
 'default_sha256':base_hash,'override_probes':overrides,
 'scope':'All four labeled canonical pairs, 100 production draws per band, and declared-axis endpoint probes.',
}
print(json.dumps(report,indent=2))

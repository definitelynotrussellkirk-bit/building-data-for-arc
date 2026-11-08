from reviewer_support import find_root, load_selected_generator
TASK='d1dd527dba87'
root=find_root(__file__)
g,_,sha=load_selected_generator(TASK,root=root)

def bbox(comp):
    rs=[r for r,c in comp]; cs=[c for r,c in comp]
    return min(rs),min(cs),max(rs),max(cs)
def norm(comp):
    r0,c0,_,_=bbox(comp)
    return frozenset((r-r0,c-c0) for r,c in comp)
def out(mask):
    if not mask:return [[0]]
    r0,c0,r1,c1=bbox(mask)
    z=[[0]*(c1-c0+1) for _ in range(r1-r0+1)]
    for r,c in mask:z[r-r0][c-c0]=8
    return z

def choose(comps,kind):
    if kind=='topmost': return min(comps,key=lambda x:bbox(x))
    if kind=='leftmost': return min(comps,key=lambda x:(bbox(x)[1],bbox(x)[0]))
    if kind=='bottommost': return max(comps,key=lambda x:(bbox(x)[2],bbox(x)[3]))
    if kind=='rightmost': return max(comps,key=lambda x:(bbox(x)[3],bbox(x)[2]))
    if kind=='bbox_area': return max(comps,key=lambda x:((bbox(x)[2]-bbox(x)[0]+1)*(bbox(x)[3]-bbox(x)[1]+1),-bbox(x)[0],-bbox(x)[1]))
    if kind=='largest_perimeter': return max(comps,key=lambda x:((bbox(x)[2]-bbox(x)[0]+1)+(bbox(x)[3]-bbox(x)[1]+1),-bbox(x)[0],-bbox(x)[1]))

def rival(grid,kind):
    b=choose(g._components(grid,1),kind); r=choose(g._components(grid,2),kind)
    return out(norm(b)^norm(r))

kinds=['topmost','leftmost','bottommost','rightmost','bbox_area','largest_perimeter']
for seed in range(500):
  for start in range(48):
    grids=[g.generate(100000+seed,start+i,difficulty='medium') for i in range(4)]
    truths=[g._truth_xor(x) for x in grids]
    for kind in kinds:
      preds=[rival(x,kind) for x in grids]
      if preds[:3]==truths[:3] and preds[3]!=truths[3]:
        print('FOUND',sha,seed,start,kind)
        import json
        print(json.dumps({'seed':100000+seed,'start':start,'kind':kind,'grids':grids,'truths':truths,'preds':preds},separators=(',',':')))
        raise SystemExit
print('NONE')

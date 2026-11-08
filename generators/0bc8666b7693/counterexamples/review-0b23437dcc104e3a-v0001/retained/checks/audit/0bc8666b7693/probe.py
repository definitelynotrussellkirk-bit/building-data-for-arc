import importlib.util, json
from pathlib import Path

path=Path('generators/0bc8666b7693/generator.py')
spec=importlib.util.spec_from_file_location('audit_0bc',path)
g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
DIR4=((-1,0),(1,0),(0,-1),(0,1))

def components(cells):
    rem=set(cells); out=[]
    while rem:
        start=min(rem); rem.remove(start); stack=[start]; comp={start}
        while stack:
            r,c=stack.pop()
            for dr,dc in DIR4:
                q=(r+dr,c+dc)
                if q in rem:
                    rem.remove(q); comp.add(q); stack.append(q)
        out.append(comp)
    return out

def legend_box(grid):
    h,w=len(grid),len(grid[0]); seen=set(); found=[]
    for r in range(h):
        for c in range(w):
            if grid[r][c]!=1 or (r,c) in seen: continue
            comp={(r,c)}; seen.add((r,c)); stack=[(r,c)]
            while stack:
                x,y=stack.pop()
                for dx,dy in DIR4:
                    q=(x+dx,y+dy)
                    if 0<=q[0]<h and 0<=q[1]<w and q not in seen and grid[q[0]][q[1]]==1:
                        seen.add(q); comp.add(q); stack.append(q)
            rs=[x for x,_ in comp]; cs=[y for _,y in comp]
            if max(rs)-min(rs)==6 and max(cs)-min(cs)==6:
                found.append((min(rs),min(cs),max(rs),max(cs)))
    assert len(found)==1
    return found[0]

def largest_component_rival(grid):
    h,w=len(grid),len(grid[0]); lr,lc,lr2,lc2=legend_box(grid)
    corners={(0,0):grid[lr+1][lc+1],(0,1):grid[lr+1][lc+5],
             (1,0):grid[lr+5][lc+1],(1,1):grid[lr+5][lc+5]}
    wins={}
    for q,color in corners.items():
        cells={(r,c) for r in range(h) for c in range(w)
               if grid[r][c]==color and not (lr<=r<=lr2 and lc<=c<=lc2)}
        comps=components(cells)
        comp=max(comps,key=lambda x:(len(x),tuple(sorted(x,reverse=True))))
        r0=min(r for r,_ in comp); c0=min(c for _,c in comp)
        norm={(r-r0,c-c0) for r,c in comp}
        wins[q]=(color,norm)
    out=[[0]*7 for _ in range(7)]
    for r in range(7):
        for c in range(7):
            if r==3 or c==3: continue
            qr,rr=(0,r) if r<=2 else (1,r-4)
            qc,cc=(0,c) if c<=2 else (1,c-4)
            color,norm=wins[(qr,qc)]
            if (rr,cc) in norm: out[r][c]=color
    return out

witness=None
for seed in range(2000):
    grid=g.generate(seed,0,difficulty='hard',texture='plain')
    h,w=len(grid),len(grid[0]); lr,lc,lr2,lc2=legend_box(grid)
    corner_colors=[]
    for p in ((lr+1,lc+1),(lr+1,lc+5),(lr+5,lc+1),(lr+5,lc+5)):
        if grid[p[0]][p[1]] not in corner_colors: corner_colors.append(grid[p[0]][p[1]])
    for color in corner_colors:
        existing={(r,c) for r in range(h) for c in range(w)
                  if grid[r][c]==color and not (lr<=r<=lr2 and lc<=c<=lc2)}
        minr=min(r for r,_ in existing); minc=min(c for _,c in existing)
        candidates=[]
        for r in range(h):
            for c in range(w):
                if grid[r][c]!=0 or (lr<=r<=lr2 and lc<=c<=lc2): continue
                if any((r+dr,c+dc) in existing for dr,dc in DIR4): continue
                # Prefer a decoy that moves the union's normalization origin.
                if r < minr or c < minc:
                    candidates.append((r,c))
        candidates.sort(key=lambda p:(-(minr-p[0])-(minc-p[1]),p))
        for decoy in candidates:
            mutated=[row[:] for row in grid]; mutated[decoy[0]][decoy[1]]=color
            if g.self_check(mutated): continue
            official=g._mirror(mutated); rival=largest_component_rival(mutated)
            if official != rival:
                witness=(seed,color,decoy,grid,mutated,official,rival,legend_box(mutated))
                break
        if witness: break
    if witness: break
if witness is None:
    raise SystemExit('no witness found')
seed,color,decoy,original,mutated,official,rival,legend=witness
report={
  'task_id': g.TASK_ID,
  'generator_version': g.VERSION,
  'probe': 'add an isolated cell of a named color; official rule aggregates all outside cells, largest-component shortcut ignores it',
  'seed': seed,
  'sample_index': 0,
  'difficulty': 'hard',
  'texture': 'plain',
  'legend_bbox': legend,
  'named_color': color,
  'added_decoy_cell': decoy,
  'self_check': g.self_check(mutated),
  'generator_mirror_equals_rival': official==rival,
  'input': mutated,
  'mirror_output': official,
  'largest_component_rival_output': rival,
}
base=Path('../checks/audit/0bc8666b7693')
(base/'multi_component_input.json').write_text(json.dumps(mutated,indent=2)+'\n')
(base/'rival_output.json').write_text(json.dumps(rival,indent=2)+'\n')
(base/'probe.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in {'input','mirror_output','largest_component_rival_output'}},indent=2,sort_keys=True))

"""Read-only source-bound assigned audits; independently reconstruct grid rules."""
import hashlib, importlib.util, json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT/'repo'

def load(tid):
    path=REPO/'generators'/tid/'generator.py'
    spec=importlib.util.spec_from_file_location('audit_'+tid,path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def digest(x):
    return hashlib.sha256(json.dumps(x,separators=(',',':'),sort_keys=True).encode()).hexdigest()

def lattice_oracle(g):
    h,w=len(g),len(g[0]); seen=set(); regions=[]
    for r in range(h):
        for c in range(w):
            if g[r][c] or (r,c) in seen: continue
            comp=[(r,c)]; seen.add((r,c))
            for y,x in comp:
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    q=(y+dy,x+dx)
                    if 0<=q[0]<h and 0<=q[1]<w and not g[q[0]][q[1]] and q not in seen:
                        seen.add(q); comp.append(q)
            regions.append(comp)
    starts_r=sorted({min(r for r,c in p) for p in regions})
    starts_c=sorted({min(c for r,c in p) for p in regions})
    out=[row[:] for row in g]
    for comp in regions:
        ri=starts_r.index(min(r for r,c in comp)); ci=starts_c.index(min(c for r,c in comp))
        if ri==0 and ci==0: color=2
        elif ri==0 and ci==len(starts_c)-1: color=4
        elif ri==len(starts_r)-1 and ci==0: color=1
        elif ri==len(starts_r)-1 and ci==len(starts_c)-1: color=8
        elif 0<ri<len(starts_r)-1 and 0<ci<len(starts_c)-1: color=7
        else: color=0
        for r,c in comp: out[r][c]=color
    return out

def parse_icons(g):
    icons=[]; excluded=set()
    for r in range(len(g)-2):
        for c in range(len(g[0])-2):
            cells={(r+dr,c+dc) for dr in range(3) for dc in range(3)}
            ring=[g[y][x] for y,x in cells if (y,x)!=(r+1,c+1)]
            b=g[r][c]; center=g[r+1][c+1]
            if b and center and center!=b and all(v==b for v in ring):
                icons.append((r,c,b,center,cells)); excluded.update(cells)
            alt=g[r][c+1]
            if b and alt and b!=alt and all(g[r+dr][c+dc]==(b if (dr+dc)%2==0 else alt) for dr in range(3) for dc in range(3)):
                excluded.update(cells)
    dots={(r,c):v for r,row in enumerate(g) for c,v in enumerate(row) if v and (r,c) not in excluded}
    return icons,dots

def touches(icon,points):
    return any((r+dr,c+dc) in points for r,c in icon[4] for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)))

def signature(icon):
    b,c=icon[2:4]
    return [[b,b,b],[b,c,b],[b,b,b]]

def icon_rule(g,any_dot=False):
    icons,dots=parse_icons(g)
    counts=Counter(dots.values())
    majority=max(counts,key=counts.get)
    points=set(dots) if any_dot else {p for p,v in dots.items() if v==majority}
    return signature(next(icon for icon in icons if touches(icon,points)))

def counterexample():
    g=[[0]*14 for _ in range(14)]
    for r,c,b,k in ((1,1,1,2),(1,9,3,4),(9,1,5,6)):
        for dr in range(3):
            for dc in range(3): g[r+dr][c+dc]=b
        g[r+1][c+1]=k
    g[0][2]=8
    for r,c in ((0,10),(1,12),(4,10)): g[r][c]=7
    return g

def prepare():
    for tid in ('9c5bdbcdcd50','48c4cd5004a1'):
        m=load(tid); home=ROOT/'checks'/'audit'/tid; home.mkdir(exist_ok=True)
        cases=[]
        if tid=='9c5bdbcdcd50':
            for band in ('easy','medium','hard'):
                for profile in m.SCENE_PROFILES:
                    for seed in (0,1):
                        cases.append(({'seed':seed,'sample_index':0,'difficulty':band,'overrides':{'scene_profile':profile}},m.generate(seed,0,difficulty=band,scene_profile=profile)))
                for seed in range(5):
                    cases.append(({'seed':seed,'sample_index':1,'difficulty':band,'overrides':{}},m.generate(seed,1,difficulty=band)))
            func=lattice_oracle
        else:
            for band in ('easy','medium','hard'):
                for seed in range(20):
                    cases.append(({'seed':seed,'sample_index':0,'difficulty':band,'overrides':{}},m.generate(seed,0,difficulty=band)))
            cases.append(({'constructed':True,'generator_domain':'rule-valid but outside default generator support; minority dot touches distractor'},counterexample()))
            func=icon_rule
        payload=[]
        for meta,g in cases:
            row={'request':meta,'input':g,'input_sha256':digest(g),'validator_errors':m.self_check(g),'independent_expected':func(g)}
            if tid=='48c4cd5004a1': row['any_dot_rival']=icon_rule(g,True)
            payload.append(row)
        (home/'input.json').write_text(json.dumps([g for meta,g in cases])+'\n')
        report={'task_id':tid,'generator_sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),
                'rule_hash':m.RULE_HASH,'cases':payload,'unique_inputs':len({digest(g) for meta,g in cases})}
        (home/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
        print(tid,'cases',len(cases),'unique',report['unique_inputs'])
    m=load('48c4cd5004a1')
    weak=[[0]*14 for _ in range(14)]
    for c in range(3): weak[0][c*2]=c+1
    extra={'weak_validator_input':weak,'validator_errors':m.self_check(weak),'icons_found':len(parse_icons(weak)[0]),'axis_probes':[]}
    for kw in ({'n_icons':5},{'palette_size':4},{'grid_h':24}):
        try:
            g=m.generate(0,0,difficulty='easy',**kw)
            extra['axis_probes'].append({'seed':0,'sample_index':0,'difficulty':'easy','overrides':kw,'actual_grid_h':len(g),'actual_palette_size':len(set(sum(g,[]))-{0}),'input_sha256':digest(g)})
        except Exception as e:
            extra['axis_probes'].append({'seed':0,'sample_index':0,'difficulty':'easy','overrides':kw,'error':str(e)})
    (ROOT/'checks/audit/48c4cd5004a1/additional-probes.json').write_text(json.dumps(extra,indent=2)+'\n')

if __name__=='__main__': prepare()

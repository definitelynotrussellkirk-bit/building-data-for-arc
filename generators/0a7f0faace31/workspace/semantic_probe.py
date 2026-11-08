"""Read-only canonical rival census and small supported-CLI reference witnesses."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root

TASK = '0a7f0faace31'
ROOT = find_root(__file__)
OUT = ROOT.parent / 'checks' / 'semantic'
RING = [(r,c) for r in range(3) for c in range(3) if (r,c)!=(1,1)]

def components(g, connectivity=4, group_color=False):
    seen=set(); out=[]; h=len(g); w=len(g[0])
    for r in range(h):
        for c in range(w):
            color=g[r][c]
            if color in (5,7) or (r,c) in seen: continue
            stack=[(r,c)]; seen.add((r,c)); cells=[]
            if group_color:
                cells=[(a,b) for a in range(h) for b in range(w) if g[a][b]==color]
                seen.update(cells)
            else:
                while stack:
                    a,b=stack.pop(); cells.append((a,b))
                    ds=[(-1,0),(1,0),(0,-1),(0,1)]
                    if connectivity==8: ds += [(-1,-1),(-1,1),(1,-1),(1,1)]
                    for da,db in ds:
                        p=(a+da,b+db)
                        if 0<=p[0]<h and 0<=p[1]<w and p not in seen and g[p[0]][p[1]]==color:
                            seen.add(p); stack.append(p)
            rs=[p[0] for p in cells]; cs=[p[1] for p in cells]
            out.append({'color':color,'cells':cells,'bbox':(min(rs),min(cs),max(rs),max(cs))})
    return out

def predict(g, rival='authority_mirror'):
    sevens=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==7]
    if not sevens: return None
    gr0=min(r for r,c in sevens); gr1=max(r for r,c in sevens)
    gc0=min(c for r,c in sevens); gc1=max(c for r,c in sevens)
    objs=components(g, 8 if rival=='eight_connected' else 4, rival=='one_object_per_color')
    selected=[]
    for o in objs:
        r0,c0,r1,c1=o['bbox']; cr=(r0+r1)//2; cc=(c0+c1)//2
        keep=gr0<=cr<=gr1 and gc0<=cc<=gc1
        if rival=='fully_contained': keep=gr0<=r0<=r1<=gr1 and gc0<=c0<=c1<=gc1
        elif rival=='any_overlap': keep=any(gr0<=r<=gr1 and gc0<=c<=gc1 for r,c in o['cells'])
        elif rival=='real_center': keep=gr0<=(r0+r1)/2<=gr1 and gc0<=(c0+c1)/2<=gc1
        elif rival=='ceil_center': keep=gr0<=(r0+r1+1)//2<=gr1 and gc0<=(c0+c1+1)//2<=gc1
        elif rival=='strict_center': keep=gr0<cr<gr1 and gc0<cc<gc1
        if keep: selected.append(o)
    if not selected: return None
    o=selected[0]
    if rival=='last_eligible': o=selected[-1]
    elif rival=='largest_eligible': o=max(selected,key=lambda o:len(o['cells']))
    elif rival=='smallest_eligible': o=min(selected,key=lambda o:len(o['cells']))
    elif rival=='nearest_guide_center':
        o=min(objs,key=lambda o:((o['bbox'][0]+o['bbox'][2]-gr0-gr1)**2+(o['bbox'][1]+o['bbox'][3]-gc0-gc1)**2))
    r0,c0,r1,c1=o['bbox']
    if rival=='object_mask':
        s=set(o['cells']); return [[g[r][c] if (r,c) in s else 5 for c in range(c0,c1+1)] for r in range(r0,r1+1)]
    if rival=='always_hollow_ring':
        return [[o['color'] if (r,c)!=(1,1) else 5 for c in range(3)] for r in range(3)]
    return [row[c0:c1+1] for row in g[r0:r1+1]]

RIVALS = ('fully_contained','any_overlap','real_center','ceil_center','strict_center',
          'eight_connected','one_object_per_color','object_mask','last_eligible',
          'largest_eligible','smallest_eligible','nearest_guide_center','always_hollow_ring')

def board(marks=((3,3),(3,9),(8,3),(8,9))):
    g=[[5]*14 for _ in range(12)]
    for r,c in marks: g[r][c]=7
    return g

def put(g, cells, r0,c0,color):
    for r,c in cells:
        assert g[r+r0][c+c0]==5
        g[r+r0][c+c0]=color

def witnesses():
    out=[]
    def save(name,g): out.append({'name':name,'input':g})
    g=board(); put(g,RING,2,5,1); put(g,RING,6,6,2); save('inclusive_top_boundary_and_sticks_out',g)
    g=board(); put(g,RING,1,5,1); put(g,RING,5,5,2); save('early_overlap_center_outside',g)
    g=board(); put(g,[(r,c) for r in range(4) for c in range(3) if (r,c) not in ((1,1),(2,1))],7,5,1); save('floor_bottom_boundary',g)
    g=board(); put(g,[(r,c) for r in range(2) for c in range(3) if (r,c)!=(0,1)],2,5,1); put(g,RING,5,5,2); save('ceil_top_outside',g)
    g=board(); put(g,[(0,0)],3,4,1); put(g,RING,4,5,1); save('diagonal_bridge_four_vs_eight',g)
    g=board(); put(g,RING,0,0,1); put(g,RING,5,5,1); save('repeated_color_disconnected_components',g)
    g=board(); put(g,RING,4,5,1); put(g,[(0,0)],5,6,2); save('raw_crop_preserves_foreign_color',g)
    g=board(); put(g,[(0,0),(1,0),(2,0),(2,1),(2,2)],3,4,1); put(g,RING,6,6,2); save('first_eligible_smaller_farther_than_later',g)
    g=board(); put(g,RING,3,4,1); put(g,[(0,0),(1,0),(2,0),(2,1),(2,2)],6,6,2); save('first_eligible_larger_than_later',g)
    g=board(marks=((3,3),(8,9),(5,6))); put(g,RING,4,5,1); save('raw_crop_preserves_guide_cell',g)
    g=board(marks=((3,3),(3,10),(10,3),(10,10)))
    put(g,RING,0,0,1)
    put(g,RING,1,5,3)
    put(g,[(0,0)],3,13,1)
    put(g,[(r,c) for r in range(3) for c in range(4) if r in (0,2) or c in (0,3)],4,9,1)
    put(g,[(0,0)],5,10,4)
    put(g,[(r,c) for r in range(4) for c in range(4) if r in (0,3) or c in (0,3)],7,5,2)
    save('compound_all_thirteen_canonical_fitting_rivals',g)
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pairs=canonical_pairs(TASK,root=ROOT)
    canonical=[]
    for p in pairs:
        g=p['input']; canonical.append({
            'variant':p['variant'],'split':p['split'],'pair_index':p['pair_index'],
            'input_shape':[len(g),len(g[0])],'output_shape':[len(p['output']),len(p['output'][0])],
            'palette':sorted({x for row in g for x in row}),
            'objects':components(g),'authority_mirror_agrees':predict(g)==p['output']})
    fit={r:all(predict(p['input'],r)==p['output'] for p in pairs) for r in RIVALS}
    ws=witnesses()
    for w in ws:
        w['authority_mirror']=predict(w['input'])
        w['rivals']={r:predict(w['input'],r) for r in RIVALS}
        w['refutes']=[r for r in RIVALS if w['rivals'][r]!=w['authority_mirror']]
    gpath=ROOT/'generators'/TASK/'generator.py'
    report={'task_id':TASK,'source_generator_sha256':hashlib.sha256(gpath.read_bytes()).hexdigest(),
            'canonical_pairs':canonical,'canonical_fit':fit,'witnesses':ws,
            'limitations':'Witnesses are authored semantic domain probes, not samples from the current generator distribution.'}
    import sys
    stem=sys.argv[1] if len(sys.argv)>1 else ''
    racket_path=OUT/(stem+'racket.json')
    if racket_path.exists():
        actual=json.loads(racket_path.read_text())
        assert len(actual['results'])==len(ws)
        count=0
        for w,a in zip(ws,actual['results']):
            assert a['input']==w['input'], 'Racket record does not match these witnesses'
            count += a['error'] is None and a['output']==w['authority_mirror']
            w.update(actual_racket_output=a['output'],actual_input_sha256=a['input_sha256'],
                     actual_output_sha256=a['output_sha256'],actual_error=a['error'])
        report['racket_verification']={
            'actual_count':len(ws),'mirror_agreement_count':count,
            'rule_text_sha256':actual['rule_text_sha256'],
            'executed_rule_hash':actual['executed_rule_hash'],
            'generator_sha256':actual['generator_sha256'],
            'cwd':actual['cwd'],'command':actual['command'],
            'racket_record':racket_path.name,
            'exit_code':'See wrapper process record; this script reads rather than executes Racket.'}
    (OUT/(stem+'probe.json')).write_text(json.dumps(report,indent=2)+'\n')
    (OUT/(stem+'input.json')).write_text(json.dumps([w['input'] for w in ws],indent=2)+'\n')
    print(json.dumps({'canonical_count':len(pairs),'canonical_fit':fit,'witness_refutes':{w['name']:w['refutes'] for w in ws}},indent=2))

if __name__=='__main__': main()

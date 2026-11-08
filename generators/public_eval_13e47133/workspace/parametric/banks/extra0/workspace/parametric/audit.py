"""Executable finite rivals for ring geometry, palette extraction and propagation."""
import argparse,importlib.util,json
from pathlib import Path
B=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_ring_audit_adapter',B/'adapter.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A);C=A.CORE
MODES=('bbox_depth','cardinal_depth','global_palette','sorted_palette','reversed_palette','ignore_background','cue_count_period','fixed_two','solid_outer','vertical_stripes','horizontal_stripes')


def predictions(g):
    bg,wall,recs=C.records(g)
    result={'cyclic':C.solve(g,'cyclic'),'bouncing':C.solve(g,'bouncing'),'unchanged_input':[row[:] for row in g]}
    largest=max(recs,key=lambda r:len(r['cells']))['palette']
    for propagation in ('cyclic','bouncing'):
        for mode in MODES:
            if mode=='cardinal_depth':result[mode+'_'+propagation]=C.solve(g,propagation,metric='cardinal');continue
            out=[row[:] for row in g]
            for rec in recs:
                cells=rec['cells'];palette=rec['palette'][:];ds=rec['depth']
                r0=min(r for r,c in cells);r1=max(r for r,c in cells);c0=min(c for r,c in cells);c1=max(c for r,c in cells)
                if mode=='global_palette':palette=largest
                elif mode=='sorted_palette':palette=sorted(palette)
                elif mode=='reversed_palette':palette=palette[::-1]
                elif mode=='ignore_background':palette=[v for v in palette if v!=bg] or [bg]
                elif mode=='cue_count_period':palette=[g[r][c] for r,c in sorted(cells,key=lambda p:(ds[p],p)) if g[r][c]!=bg] or [bg]
                elif mode=='fixed_two':palette=palette[:2]
                for r,c in cells:
                    depth=ds[(r,c)]
                    if mode=='bbox_depth':depth=min(r-r0,r1-r,c-c0,c1-c)
                    elif mode=='vertical_stripes':depth=min(c-c0,c1-c)
                    elif mode=='horizontal_stripes':depth=min(r-r0,r1-r)
                    elif mode=='solid_outer':depth=0
                    out[r][c]=palette[C.color_index(depth,len(palette),propagation)]
            result[mode+'_'+propagation]=out
    return result


def audit(seeds=range(16),demo_counts=(2,3,6)):
    seeds=list(seeds);harmful=[];equivalent=[];episodes=0;pairs=0;boundary=0;names=None
    for seed in seeds:
        bank=A.generate(seed,{'propagation':'cyclic'},6,4)
        train=[predictions(p['input']) for p in bank['train']];test=[predictions(p['input']) for p in bank['test']]
        names=list(train[0])
        for demos in demo_counts:
            for chosen in ('cyclic','bouncing'):
                episodes+=1;pairs+=demos+4
                for name in names:
                    if name==chosen or not all(p[name]==p[chosen] for p in train[:demos]):continue
                    row={'seed':seed,'demos':demos,'setting':chosen,'rival':name}
                    if any(p[name]!=p[chosen] for p in test):harmful.append(row)
                    else:equivalent.append(row)
                boundary+=int(len(bank['test'][3]['input'])==len(bank['test'][3]['input'][0])==30)
    return {'schema':'arcpuzzles-finite-teaching-audit-v1','status':'passed' if not harmful else 'failed','episodes':episodes,'labeled_pairs':pairs,'seeds':seeds,'demo_counts':list(demo_counts),'rivals':names,'harmful_survivors':harmful,'finite_equivalent_survivors':equivalent,'substantive_30x30_episodes':boundary,'label_backend':'Python claims; protected reference checks are separate','limits':'Finite tested rules and seeds, not universal uniqueness or admission.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=16);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    report=audit(range(a.seeds));a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','episodes','labeled_pairs','harmful_survivors')}));raise SystemExit(report['status']!='passed')

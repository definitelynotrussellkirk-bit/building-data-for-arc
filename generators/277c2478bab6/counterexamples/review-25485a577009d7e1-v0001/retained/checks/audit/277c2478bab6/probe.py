"""Bounded audit: advertised dimension edge and strongest fixed-gap rival."""
import hashlib, importlib.util, json, pathlib, traceback
ROOT = pathlib.Path(__file__).resolve().parents[3]
REPO = ROOT / 'repo'
OUT = pathlib.Path(__file__).resolve().parent
source = REPO / 'generators/277c2478bab6/generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
canonical = json.loads((REPO / 'shared/data/base/solutions/banks/ce088a50599a/H157__277c2478bab6.json').read_text())
# This intentionally shortcuts recognition of three separate hollow frames:
# derive every frame from the outermost blue bounding box and a hard-coded gap 2.
def fixed_gap_rival(g):
    h,w=len(g),len(g[0]); out=[[0]*w for _ in range(h)]
    blue=[(r,c) for r in range(h) for c in range(w) if g[r][c]==1]
    if not blue: return out
    r0=min(r for r,c in blue); r1=max(r for r,c in blue)
    c0=min(c for r,c in blue); c1=max(c for r,c in blue)
    if r1-r0+1<11 or c1-c0+1<11: return out
    ctrl=2 if any(2 in row for row in g) else 3 if any(3 in row for row in g) else 4
    a,b=(r0+1,c0+1) if ctrl==2 else ((r0+3,c0+3) if ctrl==3 else (r0+5,c0+5))
    x,y=(r1-1,c1-1) if ctrl==2 else ((r1-3,c1-3) if ctrl==3 else (r1-5,c1-5))
    for r in range(a,x+1):
        for c in range(b,y+1):
            if ctrl==2 and r0+3<=r<=r1-3 and c0+3<=c<=c1-3: continue
            if ctrl==3 and r0+5<=r<=r1-5 and c0+5<=c<=c1-5: continue
            out[r][c]=8
    return out
results={'task_id':gen.TASK_ID,'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(), 'seed':0, 'sample_indices':list(range(12)), 'difficulty':None, 'overrides':{}, 'boundary_probes':[], 'canonical_rival_fit':[]}
for overrides in ({'grid_h':11,'grid_w':13},{'grid_h':14,'grid_w':11}):
    try:
        grid=gen.generate(0,0,**overrides)
        results['boundary_probes'].append({'seed':0,'sample_index':0,'overrides':overrides,'result':'generated','validator_errors':gen.self_check(grid)})
    except Exception as e:
        results['boundary_probes'].append({'seed':0,'sample_index':0,'overrides':overrides,'result':'exception','exception_type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
grids=[gen.generate(0,i) for i in range(12)]
results['generated_validation_errors']=[gen.self_check(g) for g in grids]
manual=[[0]*18 for _ in range(18)]; manual[0][0]=2
for off in (0,3,6):
    gen.draw_frame(manual,1+off,1+off,15-off,15-off,1)
results['manual_witness']={'index':12,'construction':'18x18; control2 at0,0; frames bbox(1,1,15,15), (4,4,12,12), (7,7,9,9)', 'overrides':None,'seed':None,'sample_index':None,'self_check_errors':gen.self_check(manual),'documented_generator_domain':False,'reason':'offsets0,3,6 instead of generator offsets0,2,4'}
grids.append(manual)
pairs=list(canonical['visible_context']['train'])
pairs += [{'input':p['input'],'output':o} for p,o in zip(canonical['visible_context']['test_inputs'],canonical['verification']['expected_test_outputs'])]
results['canonical_rival_fit']=[fixed_gap_rival(p['input'])==p['output'] for p in pairs]
results['canonical_pair_count']=len(pairs)
results['canonical_blue_bbox_dimensions']=[(max(r for r,row in enumerate(p['input']) for c,x in enumerate(row) if x==1)-min(r for r,row in enumerate(p['input']) for c,x in enumerate(row) if x==1)+1,max(c for row in p['input'] for c,x in enumerate(row) if x==1)-min(c for row in p['input'] for c,x in enumerate(row) if x==1)+1) for p in pairs]
results['declared_shortcuts']=list(getattr(gen,'CANONICAL_SHORTCUTS',()))
results['declared_competitors']=list(getattr(gen,'LESSON_COMPETITORS',()))
(OUT/'input.json').write_text(json.dumps(grids)+'\n')
(OUT/'rival.json').write_text(json.dumps([fixed_gap_rival(g) for g in grids])+'\n')
(OUT/'probe_results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({'boundary_probes':results['boundary_probes'],'canonical_rival_fit':results['canonical_rival_fit'],'generated_validation_errors':results['generated_validation_errors']}))

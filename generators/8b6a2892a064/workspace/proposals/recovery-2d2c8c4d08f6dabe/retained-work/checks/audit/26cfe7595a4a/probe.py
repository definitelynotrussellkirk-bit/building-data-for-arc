"""Bounded, read-only selected-generator audit; ZIP or extracted-repo input."""
import argparse, hashlib, importlib.util, json, sys, types, zipfile
from pathlib import Path
P=argparse.ArgumentParser(); src=P.add_mutually_exclusive_group(required=True)
src.add_argument('--zip'); src.add_argument('--repo');P.add_argument('--out',required=True)
a=P.parse_args(); task='26cfe7595a4a'; rel=f'generators/{task}/generator.py'
if a.zip:
    z=zipfile.ZipFile(a.zip)
    code=z.read('WORK/repo/'+rel)
    deps=Path(a.out).resolve().parent/'deps'
    members=['puzzle_generators/__init__.py','puzzle_generators/base.py',
             'puzzle_generators/helpers/__init__.py','puzzle_generators/helpers/grid.py',
             'puzzle_generators/helpers/shape.py','puzzle_generators/helpers/place.py',
             'puzzle_generators/helpers/palette.py','puzzle_generators/helpers/blobs.py']
    for member in members:
        destination=deps/member;destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(z.read('WORK/repo/shared/runtime/'+member))
    sys.path.insert(0,str(deps))
    canonical_file=z.open('WORK/repo/shared/data/canonical/puzzles.jsonl')
    source_name=str(Path(a.zip).resolve())+'/WORK/repo/'+rel
else:
    root=Path(a.repo).resolve();code=(root/rel).read_bytes()
    sys.path.insert(0,str(root/'shared/runtime'))
    canonical_file=(root/'shared/data/canonical/puzzles.jsonl').open('rb')
    source_name=str(root/rel)
source_hash=hashlib.sha256(code).hexdigest()
assert source_hash=='7e1c0eea19980272d2cb3067d01cd9e7f59997346d996d9cc3b0ca136b71c09a',source_hash
m=types.ModuleType('audit_selected_26cfe7595a4a');m.__file__=source_name
sys.modules[m.__name__]=m
exec(compile(code,source_name,'exec'),m.__dict__)
with canonical_file as f:
    for raw in f:
        candidate=json.loads(raw)
        if candidate.get('task_id')==task:
            canonical=candidate;break
    else:raise ValueError('missing canonical row')
def sha(value):
    return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()
def components(g):
    left={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=0};out=[]
    while left:
        p=min(left);left.remove(p);pending=[p];cells={p};color=g[p[0]][p[1]]
        while pending:
            r,c=pending.pop()
            for q in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                if q in left and g[q[0]][q[1]]==color:
                    left.remove(q);pending.append(q);cells.add(q)
        out.append({'color':color,'size':len(cells)})
    return out
def crop(g):
    cells=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v]
    r0=min(r for r,c in cells);r1=max(r for r,c in cells)
    c0=min(c for r,c in cells);c1=max(c for r,c in cells)
    return [row[c0:c1+1] for row in g[r0:r1+1]]
def facts(g):
    return {'input_sha256':sha(g),'height':len(g),'width':len(g[0]),'nonzero_colors':sorted({v for row in g for v in row if v}),'components':components(g),'self_check_errors':m.self_check(g)}
rows=[]
for band in ('easy','medium','hard'):
    for index in range(4):
        g=m.generate(23,index,difficulty=band)
        rows.append({'seed':23,'sample_index':index,'difficulty':band,**facts(g)})
canonical_rows=[]
for split in ('train','test'):
    for index,pair in enumerate(canonical[split]):
        canonical_rows.append({'split':split,'index':index,**facts(pair['input']),'python_crop_matches_supplied_output':crop(pair['input'])==pair['output']})
overrides=[]
base=m.generate(23,4,difficulty='medium')
for kw in ({'motif_size':2},{'motif_size':4},{'palette_kind':'warm'},{'palette_kind':'cool'},{'typo':1}):
    try:
        g=m.generate(23,4,difficulty='medium',**kw)
        overrides.append({'overrides':kw,'outcome':'accepted','equal_to_no_override':g==base,**facts(g)})
    except Exception as e:overrides.append({'overrides':kw,'outcome':'raised','exception':repr(e)})
try:
    m.generate(23,4,difficulty='easy',grid_h=16)
    boundary={'outcome':'accepted'}
except Exception as e:boundary={'outcome':'raised','exception':repr(e)}
one=[[0]*8 for _ in range(7)];one[3][4]=5
report={'schema':'arcpuzzles-bounded-adversarial-audit-v1','task_id':task,'source_path':rel,'generator_sha256':source_hash,'rule_hash':hashlib.sha256(' '.join(canonical['program_solution'].split()).encode()).hexdigest()[:12],'canonical_rule_text_sha256':hashlib.sha256(canonical['program_solution'].encode()).hexdigest(),'generator_has_RULE_HASH':hasattr(m,'RULE_HASH'),'canonical_profile':canonical_rows,'ordinary_generated_probe':{'seed':23,'indices':[0,1,2,3],'bands':['easy','medium','hard'],'draw_count':12,'rows':rows,'all_components_singletons':all(c['size']==1 for r in rows for c in r['components'])},'override_probes':overrides,'advertised_grid_h_16_easy':boundary,'singleton_validator_probe':facts(one),'racket_labels_executed_in_this_probe':False}
out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
inputs=[canonical['train'][0]['input'],base,one]
report['racket_probe_inputs']=[{'index':0,'kind':'canonical_train_0','belongs_to_documented_generator_multicolor_domain':False},{'index':1,'kind':'ordinary_generate_seed23_index4_medium','belongs_to_documented_generator_multicolor_domain':True},{'index':2,'kind':'singleton_validator_impostor','belongs_to_documented_generator_multicolor_domain':False}]
report['python_crop_outputs_for_comparison_only']=[crop(g) for g in inputs]
report['command']=[sys.executable,*sys.argv]
report['cwd']=str(Path.cwd())
out.write_text(json.dumps(report,indent=2)+'\n')
(out.parent/'input.json').write_text(json.dumps(inputs,indent=2)+'\n')
print(json.dumps({'report':str(out),'report_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'input_path':str(out.parent/'input.json'),'input_sha256':hashlib.sha256((out.parent/'input.json').read_bytes()).hexdigest(),'source_sha256':source_hash,'rule_hash':report['rule_hash'],'all_components_singletons':report['ordinary_generated_probe']['all_components_singletons'],'canonical_components':[r['components'] for r in canonical_rows],'override_outcomes':[{k:v for k,v in r.items() if k in ['overrides','outcome','equal_to_no_override']} for r in overrides],'grid_h_16_easy':boundary,'singleton_errors':report['singleton_validator_probe']['self_check_errors']},sort_keys=True))

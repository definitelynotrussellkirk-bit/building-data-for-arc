from pathlib import Path
import hashlib,json,sys
from reviewer_support import load_selected_generator,find_root,canonical_pairs
OUT=Path(__file__).resolve().parent
ROOT=find_root(__file__)
ID='bb1b1e111e1a'
gen,source,sha=load_selected_generator(ID,root=ROOT)
def save(n,x): (OUT/n).write_text(json.dumps(x,indent=2)+'\n')
def panels(g):
 w=(len(g[0])-2)//3
 return [r[:w] for r in g],[r[w+1:2*w+1] for r in g],[r[2*w+2:] for r in g]
def mirror(g):
 m,a,b=panels(g)
 return [[a[r][c] if m[r][c] else b[r][c] for c in range(len(m[0]))] for r in range(len(m))]
if len(sys.argv)>1 and sys.argv[1]=='compare':
 raw=json.loads((OUT/'racket.json').read_text())
 probe=json.loads((OUT/'probe.json').read_text())
 rows=raw['results']
 cases=probe['normal']+probe['degeneracies']+probe['canonical']
 comparisons=[{'index':i,'valid_output':r['valid_output'],'error':r['error'],'matches_python_select':r['output']==c['python_select']} for i,(r,c) in enumerate(zip(rows,cases))]
 assert len(rows)==len(cases)==36
 assert all(r['matches_python_select'] and r['valid_output'] and r['error'] is None for r in comparisons)
 d=probe['degeneracies'][2]
 actual=rows[32]['output']
 witness={**d,'actual_racket_output':actual,'actual_equals_A':actual==d['rival_copy_A'],'actual_equals_B':actual==d['rival_copy_B'],'generator_sha256':sha,'rule_text_sha256':raw['rule_text_sha256'],'executed_rule_hash':raw['executed_rule_hash'],'racket_input_sha256':rows[32]['input_sha256'],'racket_output_sha256':rows[32]['output_sha256']}
 assert d['self_check']==[] and not witness['actual_equals_A'] and not d['a_equals_b']
 save('identical_panels_witness.json',witness)
 summary={'generator_sha256':sha,'rule_text_sha256':raw['rule_text_sha256'],'executed_rule_hash':raw['executed_rule_hash'],'racket_comparisons':comparisons,'normal_passed':30,'normal_total':30,'canonical_passed':3,'canonical_total':3,'degenerate_semantics_passed':3,'degenerate_total':3,'false_identity_reproduced':True,'control_groups':len(probe['controls']),'density_equal_groups':sum(x['density_low_high_equal'] for x in probe['controls']),'palette_equal_groups':sum(x['all_palette_kinds_equal'] for x in probe['controls']),'helpful_texture_equal_groups':sum(x['all_helpful_textures_equal'] for x in probe['controls'])}
 save('summary.json',summary)
 print(json.dumps({k:v for k,v in summary.items() if k!='racket_comparisons'}))
 exit()
normal=[]
for i in range(30):
 difficulty=('easy','medium','hard')[i%3]
 grid=gen.generate('audit-current-panels',i,difficulty=difficulty)
 normal.append({'seed':'audit-current-panels','sample_index':i,'difficulty':difficulty,'input':grid,'self_check':gen.self_check(grid),'python_select':mirror(grid)})
controls=[]
for i in range(30):
 low=gen.generate('audit-current-controls',i,mask_density=0.1)
 high=gen.generate('audit-current-controls',i,mask_density=0.9)
 palettes=[gen.generate('audit-current-controls',i,palette_kind=x) for x in gen.PALETTE_KINDS]
 textures=[gen.generate('audit-current-controls',i,texture=x) for x in gen.HELPFUL_TEXTURES]
 controls.append({'seed':'audit-current-controls','sample_index':i,'density_low_high_equal':low==high,'all_palette_kinds_equal':all(g==palettes[0] for g in palettes),'all_helpful_textures_equal':all(g==textures[0] for g in textures),'low_input_sha256':hashlib.sha256(json.dumps(low).encode()).hexdigest(),'high_input_sha256':hashlib.sha256(json.dumps(high).encode()).hexdigest()})
deg=[]
for name in gen.DEGENERATE_TEXTURES:
 g=gen.generate('audit-current-degeneracy',0,texture=name)
 m,a,b=panels(g)
 deg.append({'seed':'audit-current-degeneracy','sample_index':0,'overrides':{'texture':name},'input':g,'self_check':gen.self_check(g),'a_equals_b':a==b,'rival_copy_A':a,'rival_copy_B':b,'python_select':mirror(g)})
canon=canonical_pairs(ID,root=ROOT,labeled_only=True)
canonical=[]
for p in canon:
 canonical.append({**p,'self_check':gen.self_check(p['input']),'python_select':mirror(p['input']),'mirror_matches_label':mirror(p['input'])==p['output']})
inputs=[x['input'] for x in normal]+[x['input'] for x in deg]+[x['input'] for x in canonical]
save('input.json',inputs)
save('probe.json',{'task_id':ID,'generator_path':str(source.relative_to(ROOT)),'generator_sha256':sha,'normal':normal,'controls':controls,'degeneracies':deg,'canonical':canonical,'input_order':['normal indices 0..29','degeneracies in DEGENERATE_TEXTURES order','canonical pairs helper order']})
print(json.dumps({'generator_sha256':sha,'normal_valid':sum(not x['self_check'] for x in normal),'normal_total':len(normal),'density_equal':sum(x['density_low_high_equal'] for x in controls),'palette_equal':sum(x['all_palette_kinds_equal'] for x in controls),'texture_equal':sum(x['all_helpful_textures_equal'] for x in controls),'degenerate_results':[{k:x[k] for k in ('overrides','self_check','a_equals_b')} for x in deg],'canonical_count':len(canonical),'canonical_mirror_pass':sum(x['mirror_matches_label'] for x in canonical),'racket_batch_count':len(inputs)}))

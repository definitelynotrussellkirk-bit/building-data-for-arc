from pathlib import Path
import json, hashlib, importlib.util
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
B=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('candidate',B/'generator.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=json.loads((B/'originals.json').read_text());rule=(B/'reference.rkt').read_text();b=RacketBridge();rows=[]
try:
 for split in ('train','test'):
  for i,pair in enumerate(p[split]):
   g,y=pair['input'],pair['output'];lit="'("+' '.join('('+' '.join(map(str,r))+')' for r in g)+')'
   actual=b.eval_text('('+wrap_rule(rule)+' '+lit+')');assert actual==m.solve(g)
   diffs=[{'row':r,'col':c,'input':g[r][c],'predicted':actual[r][c],'gold':y[r][c]} for r in range(len(g)) for c in range(len(g[0])) if actual[r][c]!=y[r][c]]
   rows.append({'split':split,'index':i,'matches':not diffs,'differences':diffs})
 report={'status':'blocked_original_rule_recovery','qualified':False,'accepted':False,'runtime':b.runtime_identity,'results':rows,'matches':sum(x['matches'] for x in rows),'total':len(rows)}
finally:b.close()
a,c=p['train'][0],p['train'][3]
report['paired_counterexample']={'input_differing_cells':[[r,k] for r in range(30) for k in range(22) if a['input'][r][k]!=c['input'][r][k]],'train0_output_header_equals_train3_input_with_background_green':a['output'][:5]==[[3 if v==8 else v for v in row] for row in c['input'][:5]],'board_inputs_identical':a['input'][5:]==c['input'][5:],'interpretation':'Train0 gold header substitutes the glyph from board row2,col1 for selected row1,col1, but its board highlight still selects row1,col1. Train1 selects and preserves that same blue I in a winning column. No justified general replacement rule identified; this does not prove an annotation error.'}
report['source_bindings']=[{'path':str(f.relative_to(B)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(B.rglob('*')) if f.is_file() and '__pycache__' not in str(f) and f.suffix in ('.py','.rkt','.json') and f.name!='result.json']
(B/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('status','matches','total','paired_counterexample')},indent=2))

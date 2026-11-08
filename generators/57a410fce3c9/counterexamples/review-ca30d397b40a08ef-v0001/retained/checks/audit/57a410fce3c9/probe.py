from __future__ import annotations
import hashlib, importlib.util, json
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
GEN = ROOT/'repo/generators/57a410fce3c9/generator.py'
CAN = ROOT/'repo/shared/data/canonical/puzzles.jsonl'
spec=importlib.util.spec_from_file_location('audit57', GEN); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
counts=Counter(); samples=0
for band in ('easy','medium','hard'):
  for seed in range(1,101):
    for idx in range(20):
      g=m.generate(seed,idx,difficulty=band); h,w=len(g),len(g[0]); samples+=1
      zr=[r for r in range(h) if all(v==0 for v in g[r])]
      zc=[c for c in range(w) if all(g[r][c]==0 for r in range(h))]
      pos=('row',zr[0]) if zr else ('col',zc[0])
      counts[str(pos)]+=1
canonical=None
for line in CAN.read_text().splitlines():
  row=json.loads(line)
  if row.get('task_id')=='57a410fce3c9': canonical=row; break
assert canonical
canonical_zero_lines=[]
for split in ('train','test'):
  for i,pair in enumerate(canonical[split]):
    g=pair['input']; h,w=len(g),len(g[0])
    zr=[r for r in range(h) if all(v==0 for v in g[r])]
    zc=[c for c in range(w) if all(g[r][c]==0 for r in range(h))]
    canonical_zero_lines.append({'split':split,'index':i,'shape':[h,w],'zero_rows':zr,'zero_cols':zc})
out={
 'task_id':'57a410fce3c9','generator_sha256':hashlib.sha256(GEN.read_bytes()).hexdigest(),
 'canonical_sha256':hashlib.sha256(CAN.read_bytes()).hexdigest(),'sample_policy':'difficulty easy/medium/hard; seeds 1..100; sample_index 0..19',
 'generated_samples':samples,'generated_zero_line_positions':dict(counts),
 'canonical_zero_lines':canonical_zero_lines,
 'finding':'The generator emits only row 0 or column 0 separators; canonical test[0] uses the final row, so bottom/right-side rule behavior is absent from training data.'}
Path(__file__).with_name('finding.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))

"""Attach transparent rival predictions to independently obtained Racket evidence."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
racket=json.loads((HERE/'racket.json').read_text())
diag=json.loads((HERE/'diagnostic.json').read_text())
def rival(g):
    out=[row[:] for row in g]
    for color in sorted({v for row in g for v in row if v}):
        cells=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==color]
        if len(cells)<2: continue
        r0=min(r for r,c in cells); r1=max(r for r,c in cells)
        c0=min(c for r,c in cells); c1=max(c for r,c in cells)
        if r0==r1 or c0==c1: continue
        for r in range(r0,r1+1):
            for c in range(c0,c1+1): out[r][c]=color
    return out
canonical=next(json.loads(line) for line in (ROOT/'repo/shared/data/canonical/puzzles.jsonl').open() if json.loads(line).get('task_id')=='89c85768abe1')
pairs=canonical['train']+canonical['test']
report={'identity':diag['identity'],'racket_rule_text_sha256':racket['rule_text_sha256'],'executed_rule_hash':racket['executed_rule_hash'],'rival_description':'Fill only genuinely two-dimensional same-color bounding boxes; leave collinear pairs unchanged. Domain-extension rival, not an in-domain rule defect.','canonical_fit':[rival(p['input'])==p['output'] for p in pairs],'canonical_denominator':len(pairs),'comparisons':[]}
for result,manifest in zip(racket['results'],diag['racket_input_manifest']):
    prediction=rival(result['input'])
    report['comparisons'].append({'index':result['index'],'name':manifest['name'],'domain':manifest['domain'],'actual_racket_output':result['output'],'actual_racket_valid_output':result['valid_output'],'actual_racket_error':result['error'],'rival_prediction':prediction,'rival_matches_racket':prediction==result['output']})
(HERE/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'canonical_fit':report['canonical_fit'],'canonical_denominator':len(pairs),'comparisons':[{'index':c['index'],'rival_matches_racket':c['rival_matches_racket']} for c in report['comparisons']]}))

from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import load_selected_generator

TASK='213c98056707'
root=Path.cwd()
gen,path,sha=load_selected_generator(TASK, root=root)
grid=gen.generate(0,0,texture='tied_heights')
# Identify nonzero color row spans and counts for concise structural evidence.
colors=sorted({v for row in grid for v in row if v})
stats={}
for color in colors:
    pts=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color]
    stats[str(color)]={
        'count':len(pts),
        'row_min':min(r for r,c in pts),
        'row_max':max(r for r,c in pts),
        'height':max(r for r,c in pts)-min(r for r,c in pts)+1,
    }
payload={
    'schema':'audit-probe-v1','task_id':TASK,
    'generator_path':str(path.relative_to(root)),'generator_sha256':sha,
    'call':{'seed':0,'sample_index':0,'difficulty':None,'overrides':{'texture':'tied_heights'}},
    'input':grid,'self_check':gen.self_check(grid),'color_stats':stats,
    'finding':'The explicitly degenerate tied_heights board is accepted by self_check although both ring colors span the same 5-row height.'
}
out=Path('../checks/audit/213c98056707/tied-heights-probe.json')
out.write_text(json.dumps(payload,indent=2)+'\n')
Path('../checks/audit/213c98056707/input.json').write_text(json.dumps(grid,indent=2)+'\n')
print(json.dumps({'out':str(out),'self_check':payload['self_check'],'stats':stats},indent=2))

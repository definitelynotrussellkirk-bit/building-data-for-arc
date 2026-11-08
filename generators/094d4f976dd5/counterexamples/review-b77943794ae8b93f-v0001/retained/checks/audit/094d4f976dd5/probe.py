from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import load_selected_generator

TASK='094d4f976dd5'
root=Path.cwd()
gen,path,sha=load_selected_generator(TASK, root=root)
trials=[]
for band in (None,'easy','medium','hard'):
    for axis,values in (('panel_h',range(7,15)),('panel_w',range(3,7))):
        for value in values:
            row={'difficulty':band,'axis':axis,'value':value}
            try:
                grid=gen.generate(20261012,0,difficulty=band,**{axis:value})
                row.update(status='accepted',observed_panel_h=len(grid),observed_panel_w=(len(grid[0])-2)//3,
                           self_check=gen.self_check(grid))
            except Exception as exc:
                row.update(status='rejected',error_type=type(exc).__name__,error=str(exc))
            trials.append(row)
payload={
    'schema':'audit-probe-v1','task_id':TASK,
    'generator_path':str(path.relative_to(root)),'generator_sha256':sha,
    'declared_axes':gen.AXES,
    'trials':trials,
    'rejected_declared_exact_values':[r for r in trials if r['status']=='rejected'],
    'finding':'Advertised exact panel_h 7..14 and panel_w 3..6 controls are band-dependent; many declared values are rejected.'
}
out=Path('../checks/audit/094d4f976dd5/override-probe.json')
out.write_text(json.dumps(payload,indent=2)+'\n')
print(json.dumps({'out':str(out),'rejected':len(payload['rejected_declared_exact_values']),
                  'examples':payload['rejected_declared_exact_values'][:6]},indent=2))

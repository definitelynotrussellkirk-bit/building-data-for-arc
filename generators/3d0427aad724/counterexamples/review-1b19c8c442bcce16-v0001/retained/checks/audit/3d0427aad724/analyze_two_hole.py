#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator
TASK='3d0427aad724'
gen, source, sha=load_selected_generator(TASK, root=find_root(__file__))
grid=json.loads(Path('../checks/audit/3d0427aad724/two_hole_input.json').read_text())
racket=json.loads(Path('../checks/audit/3d0427aad724/racket.json').read_text())
binary=[[8 if v else 0 for v in row] for row in grid]
record={
 'schema':'arc-audit-two-hole-witness-v1',
 'task_id':TASK,
 'generator_path':str(source),
 'generator_sha256':sha,
 'rule_hash':racket['executed_rule_hash'],
 'rule_text_sha256':racket['rule_text_sha256'],
 'input':grid,
 'generator_self_check':gen.self_check(grid),
 'intended_racket_output':racket['results'][0]['output'],
 'binary_any_hole_rival_output':binary,
 'rival_disagrees':binary!=racket['results'][0]['output'],
 'input_sha256':racket['results'][0]['input_sha256'],
 'output_sha256':racket['results'][0]['output_sha256'],
 'racket_command':racket['command'],
 'finding':'Authority maps two holes to color 6, but the generator and self_check only admit single rectangular frames plus hole-free blobs.',
}
Path('../checks/audit/3d0427aad724/two_hole_witness.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps({'sha':sha,'self_check':record['generator_self_check'],'rival_disagrees':record['rival_disagrees'],'output_colors':sorted({v for row in record['intended_racket_output'] for v in row})}))

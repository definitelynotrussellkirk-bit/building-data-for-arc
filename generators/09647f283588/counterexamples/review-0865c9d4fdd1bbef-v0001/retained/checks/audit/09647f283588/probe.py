"""Bounded findings-only audit of frame placement and advertised near misses."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator

TASK = '09647f283588'
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
gen, source, digest = load_selected_generator(TASK, root=ROOT)

def windows(grid):
    out = []
    for r in range(len(grid)-2):
        for c in range(len(grid[0])-2):
            corners = [grid[r+dr][c+dc] for dr,dc in gen._CORNERS]
            if corners[0] and len(set(corners))==1:
                out.append({'r':r,'c':c,'color':corners[0],'center':grid[r+1][c+1]})
    return out

search=[]
selected=None
for seed in range(8):
    grid=gen.generate(seed,0,difficulty='easy',texture='center_filled',n_frames=2)
    found=windows(grid)
    near=sum(w['center']!=0 for w in found)
    search.append({'seed':seed,'sample_index':0,'active_windows':sum(w['center']==0 for w in found),'center_filled_windows':near})
    if near==0:
        selected={'seed':seed,'sample_index':0,'difficulty':'easy','texture':'center_filled','n_frames':2,'input':grid,'windows':found,'self_check':gen.self_check(grid)}
        break
assert selected is not None,'No missing near-miss reproduced within the eight-draw bound'
plain=gen.generate(selected['seed'],0,difficulty='easy',texture='plain',n_frames=2)
selected['identical_to_plain']=plain==selected['input']
# Hand-crafted canonical contrast, one valid frame plus one center-filled near-miss.
control=[[0]*9 for _ in range(5)]
for dr,dc in gen._CORNERS:
    control[1+dr][dr*0+dc]=4
    control[1+dr][6+dc]=7
control[2][7]=3
inputs=[selected['input'],control]
receipt=Catalog(ROOT).apply(TASK,inputs,reference='canonical',timeout=90)
assert receipt['generator_sha256']==digest
assert receipt['rule_hash_matches_catalog'] is True
assert all(row['error'] is None for row in receipt['results'])
(OUT/'apply-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
selected['output']=receipt['results'][0]['output']
report={'task_id':TASK,'generator_sha256':digest,'search_limit':8,'generated_draws':len(search)+1,'search':search,'reproduced':selected,'control':{'input':control,'output':receipt['results'][1]['output']},'authority':{k:receipt[k] for k in ('catalog_rule_hash','executed_rule_hash','rule_hash_matches_catalog','rule_text_sha256')},'source_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==digest}
assert report['source_unchanged']
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('reproduced','control')},indent=2))
print('replay', {k:v for k,v in selected.items() if k not in ('input','output')})

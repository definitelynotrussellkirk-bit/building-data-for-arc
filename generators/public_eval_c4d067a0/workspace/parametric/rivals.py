"""Ten explicit plausible enlargement shortcuts, total on the admitted grammar."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_rivalc4_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:12],BASE/'family.py')
f=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=f;_spec.loader.exec_module(f)


def _clipped(g,data,selected=None):
    out=[row[:] for row in g];ar,ac=data['origin'];s=data['block_size'];pitch=data['pitch']
    for r,row in enumerate(data['pattern']):
        for c,color in enumerate(row):
            if color==data['bg'] or (selected is not None and (r,c) not in selected):continue
            for dr in range(s):
                for dc in range(s):
                    rr,cc=ar+r*pitch+dr,ac+c*pitch+dc
                    if 0<=rr<len(g) and 0<=cc<len(g[0]):out[rr][cc]=color
    return out


def predict(g,completion):
    data=f.infer(g);selected=f.selected_positions(data) if completion=='anchored_components' else None
    result={'identity':[row[:] for row in g],
            'other_setting':f.solve(g,'anchored_components' if completion=='all' else 'all')}
    wrong=copy.deepcopy(data);wrong['origin']=list(data['blocks'][0]['bbox'][:2])
    result['first_seed_is_origin']=_clipped(g,wrong,selected)
    wrong=copy.deepcopy(data);wrong['block_size']=2
    result['fixed_size_two']=_clipped(g,wrong,selected)
    wrong=copy.deepcopy(data);wrong['pitch']=data['block_size']+1
    result['unit_gap']=_clipped(g,wrong,selected)
    wrong=copy.deepcopy(data);wrong['pitch']=data['block_size']
    result['no_gaps']=_clipped(g,wrong,selected)
    seed_color=data['blocks'][0]['color']
    wrong=copy.deepcopy(data)
    wrong['pattern']=[[seed_color if v!=data['bg'] else v for v in row] for row in data['pattern']]
    result['seed_color_only']=_clipped(g,wrong,selected)
    wrong=copy.deepcopy(data)
    wrong['pattern']=[[seed_color if v==data['bg'] else v for v in row] for row in data['pattern']]
    result['fill_template_holes']=_clipped(g,wrong)
    result['eight_connected']=_clipped(g,data,f.selected_positions(data,eight=True))
    result['color_sensitive_components']=_clipped(g,data,f.selected_positions(data,color_sensitive=True))
    return result

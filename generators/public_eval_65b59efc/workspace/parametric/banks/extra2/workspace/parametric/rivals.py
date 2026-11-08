"""Finite shortcut population for template-blueprint expansion."""
from __future__ import annotations
import hashlib,importlib.util,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_r65_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:12],BASE/'family.py')
f=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=f;_spec.loader.exec_module(f)

def predict(grid,setting):
    d=f.parse(grid);ts=d['templates'];colors=[t['color'] for t in ts]
    candidates={
      'identity':[row[:] for row in grid],
      'opposite_scope':f.solve(grid,'modal_template' if setting=='all' else 'all'),
      'first_template':f.solve(grid,'selected',colors[0]),
      'last_template':f.solve(grid,'selected',colors[-1]),
      'largest_template_mask':f.solve(grid,'selected',max(ts,key=lambda t:t['area'])['color']),
      'smallest_template_mask':f.solve(grid,'selected',min(ts,key=lambda t:t['area'])['color']),
      'largest_numeric_color':f.solve(grid,'selected',max(colors)),
      'smallest_numeric_color':f.solve(grid,'selected',min(colors)),
      'first_blueprint_mark':f.solve(grid,'selected',d['placements'][0]['color']),
    }
    correct=f.solve(grid,setting)
    return {k:v for k,v in candidates.items() if v!=correct}

"""Finite shortcut population for missing-center tile projection."""
from __future__ import annotations
import hashlib,importlib.util,sys
from collections import Counter
from pathlib import Path
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_rdb0_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:12],BASE/'family.py')
f=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=f;_spec.loader.exec_module(f)


def _selected(grid,indices):return f.solve(grid,'selected_indices',selected_indices=indices)


def predict(grid,setting):
    d=f.parse(grid);records=d['records'];samples=[r['sample'] for r in records];counts=Counter(samples)
    rare=min(counts.values());rarest=next(v for v in samples if counts[v]==rare)
    corners=[r['index'] for r in records if r['tile_row']!=1 and r['tile_col']!=1]
    cardinals=[r['index'] for r in records if (r['tile_row']==1) != (r['tile_col']==1)]
    candidates={
      'identity':[row[:] for row in grid],
      'opposite_scope':f.solve(grid,'modal_inward' if setting=='all' else 'all'),
      'no_outer':f.solve(grid,'none'),
      'corners_only':_selected(grid,corners),
      'cardinals_only':_selected(grid,cardinals),
      'first_sample_color':f.solve(grid,'selected_color',selected_color=samples[0]),
      'last_sample_color':f.solve(grid,'selected_color',selected_color=samples[-1]),
      'rarest_sample_color':f.solve(grid,'selected_color',selected_color=rarest),
      'largest_numeric_sample':f.solve(grid,'selected_color',selected_color=max(samples)),
      'smallest_numeric_sample':f.solve(grid,'selected_color',selected_color=min(samples)),
      'base_color_samples':f.solve(grid,'selected_color',selected_color=d['base_color']),
      'first_four_tiles':_selected(grid,[0,1,2,3]),
    }
    correct=f.solve(grid,setting)
    return {k:v for k,v in candidates.items() if v!=correct}

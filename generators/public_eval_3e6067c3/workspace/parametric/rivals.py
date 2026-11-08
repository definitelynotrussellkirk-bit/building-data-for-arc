"""Executable finite shortcut population for the legend-ordered route family.

These are intentionally plausible wrong rules, not claims of exhaustive
identifiability.  The audit requires every rule that fits the demonstrations
to disagree with at least one retained private query.
"""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
_key='_rivals3e_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:12]
_spec=importlib.util.spec_from_file_location(_key,BASE/'family.py')
f=importlib.util.module_from_spec(_spec);sys.modules[_key]=f;_spec.loader.exec_module(f)


def _bridge_cells(a,b):
    ap=a['payload_bbox'];bp=b['payload_bbox'];ab=a['bbox'];bb=b['bbox']
    if ap[0]==bp[0] and ap[2]==bp[2]:
        lo,hi=(ab[3]+1,bb[1]) if ab[1]<bb[1] else (bb[3]+1,ab[1])
        return [(r,c) for r in range(ap[0],ap[2]+1) for c in range(lo,hi)]
    if ap[1]==bp[1] and ap[3]==bp[3]:
        lo,hi=(ab[2]+1,bb[0]) if ab[0]<bb[0] else (bb[2]+1,ab[0])
        return [(r,c) for r in range(lo,hi) for c in range(ap[1],ap[3]+1)]
    return []


def _paint(grid,route,endpoint='source',*,constant=None,frame=None,axis=None,thin=False):
    out=[row[:] for row in grid]
    for a,b in zip(route,route[1:]):
        cells=_bridge_cells(a,b)
        if not cells:continue
        horizontal=a['payload_bbox'][0]==b['payload_bbox'][0]
        if axis=='horizontal' and not horizontal:continue
        if axis=='vertical' and horizontal:continue
        if thin:
            # Preserve only one row/column of the otherwise correct corridor.
            target=min(r for r,c in cells) if horizontal else min(c for r,c in cells)
            cells=[(r,c) for r,c in cells if (r if horizontal else c)==target]
        color=(a['color'] if endpoint=='source' else b['color'])
        if constant is not None:color=constant
        if frame is not None:color=frame
        for r,c in cells:out[r][c]=color
    return out


def _first_occurrence_route(data):
    by={}
    for b in data['blocks']:by.setdefault(b['color'],b)
    return [by[color] for color in data['sequence']]


def _all_aligned(grid,data,endpoint):
    out=[row[:] for row in grid]
    blocks=data['blocks']
    for i,a in enumerate(blocks):
        for b in blocks[i+1:]:
            cells=_bridge_cells(a,b)
            if not cells:continue
            color=a['color'] if endpoint=='source' else b['color']
            for r,c in cells:out[r][c]=color
    return out


def predict(grid, setting):
    """Return name -> predicted grid for each bounded wrong rule."""
    if setting not in ('source','destination'):raise ValueError('setting must be source|destination')
    data=f.parse(grid);route=data['route'];opposite='destination' if setting=='source' else 'source'
    return {
        'identity':[row[:] for row in grid],
        'opposite_endpoint':_paint(grid,route,opposite),
        'reverse_route':_paint(grid,list(reversed(route)),setting),
        'spatial_reading_order':_paint(grid,data['blocks'],setting),
        'first_occurrence_for_repeated_colors':_paint(grid,_first_occurrence_route(data),setting),
        'all_spatial_blocks':_paint(grid,data['blocks'],setting),
        'all_aligned_block_pairs':_all_aligned(grid,data,setting),
        'constant_first_route_color':_paint(grid,route,setting,constant=route[0]['color']),
        'frame_colored_corridors':_paint(grid,route,setting,frame=data['frame']),
        'one_cell_thick_corridors':_paint(grid,route,setting,thin=True),
        'horizontal_edges_only':_paint(grid,route,setting,axis='horizontal'),
        'vertical_edges_only':_paint(grid,route,setting,axis='vertical'),
    }

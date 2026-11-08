"""Input-only canonical generator for public ARC contour assembly parent 16b78196."""
from pathlib import Path
import hashlib
import importlib.util
import sys

GENERATOR_ID = TASK_ID = 'public_eval_16b78196'
RULE_TASK_ID = 'ee_16b78196'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
SUMMARY = 'Assemble same-color pieces into contour-compatible chains extending from a spanning wall.'
AXES = {name:{'type':'int','valid':bounds} for name,bounds in {
 'grid_h':'24..30','grid_w':'24..30','orientation_id':'0..7','chain_count':'1..2',
 'chain_depth':'2..4; depth four needs >=28 normal dimension','piece_width':'5..6'}.items()}
INVARIANTS=['one full-span connected wall','column-convex interlocking pieces','complete assembly','black background']

def _adapter():
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py';key='_contour_generator_'+hashlib.sha256(str(path).encode()).hexdigest()[:16]
    if key not in sys.modules:
        spec=importlib.util.spec_from_file_location(key,path);m=importlib.util.module_from_spec(spec);sys.modules[key]=m;spec.loader.exec_module(m)
    return sys.modules[key]

def generate(seed,sample_index,*,difficulty=None,**overrides):
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unknown difficulty')
    if set(overrides)-set(AXES):raise ValueError('Unknown controls')
    if difficulty=='easy':overrides.setdefault('chain_count',1)
    if difficulty=='hard':
        overrides.setdefault('chain_depth',4);overrides.setdefault('grid_h',30);overrides.setdefault('grid_w',30)
    return _adapter().sampler.draw(seed,sample_index,split='production',**overrides)


def self_check(grid,*,difficulty=None,meta=None):
    try:_adapter().model.analyze(grid)
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []

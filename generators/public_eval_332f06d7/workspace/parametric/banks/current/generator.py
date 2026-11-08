"""Public-parent 332f06d7: move a rigid black block through a blue corridor."""
from pathlib import Path
import hashlib
import importlib.util
import sys
RULE_TASK_ID = 'ee_332f06d7'
TASK_ID = 'public_eval_332f06d7'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
AXES = {}
SUMMARY = 'Find whole-footprint reachable anchors and move goalward through a maze.'

def _adapter():
    base=Path(__file__).resolve().parent/'workspace/parametric'
    if not (base/'adapter.py').is_file():
        from reviewer_support import find_root
        base=find_root(__file__)/'generators'/TASK_ID/'workspace/parametric'
    path=base/'adapter.py';name='_base_'+hashlib.sha256(str(path).encode()).hexdigest()
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return sys.modules[name]

def generate(seed,sample_index,*,difficulty=None,**overrides):
    if overrides:raise ValueError('No overrides supported')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    return _adapter().sample_input(seed,sample_index)

def self_check(grid,**kwargs):
    try:_adapter().model.analyze(grid);return []
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]

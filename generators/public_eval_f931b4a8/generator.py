"""Single-grid ordinary worker entrypoint, independent of private episode controls."""
from pathlib import Path
import importlib.util
RULE_TASK_ID = 'ee_f931b4a8'
VERSION = '1.0.0'
_path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
_spec=importlib.util.spec_from_file_location('_quadrant_generator_adapter_'+str(_path),_path)
_adapter=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_adapter)

def generate(seed=0,sample_index=0,difficulty='medium',**overrides):
    if overrides:raise ValueError('Unknown controls: '+', '.join(sorted(overrides)))
    if difficulty is None:difficulty='medium'
    if difficulty not in ('easy','medium','hard'):raise ValueError('Unknown difficulty')
    _adapter.model.integer(seed,0,2**63-1,'seed');_adapter.model.integer(sample_index,0,2**31-1,'sample_index')
    profile={'easy':(3,7,8),'medium':(6,17,23),'hard':(15,30,30)}[difficulty]
    return _adapter.model.sample_grid(seed,f'ordinary:{sample_index}',profile)

def self_check(grid,difficulty=None):
    try:_adapter.model.analyze(grid)
    except ValueError as error:return [str(error)]
    return []

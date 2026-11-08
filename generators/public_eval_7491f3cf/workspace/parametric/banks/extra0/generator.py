"""Single-input interface. Native episode settings remain in the adjacent adapter."""
import importlib.util
from pathlib import Path
RULE_TASK_ID = 'ee_7491f3cf'
VERSION = '1.0.0'
_path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
_spec=importlib.util.spec_from_file_location('_selector_generator_'+str(_path),_path)
_adapter=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_adapter)

def generate(seed=0,sample_index=0,difficulty='medium',**overrides):
    difficulty = 'medium' if difficulty is None else difficulty
    if overrides:raise ValueError('Unknown controls: '+', '.join(sorted(overrides)))
    if type(difficulty) is not str or difficulty not in ('easy','medium','hard'):raise ValueError('Unknown difficulty')
    _adapter.model.integer(seed,0,2**63-1,'seed');_adapter.model.integer(sample_index,0,2**31-1,'sample_index')
    profile={'easy':(5,5,'diagonal',sample_index%2,0),'medium':(12,6,'elbow',sample_index%2,0),'hard':(28,6,'stair',sample_index%2,1)}[difficulty]
    return _adapter.model.sample_grid(seed,f'ordinary:{sample_index}',profile)

def self_check(grid,difficulty=None):
    try:_adapter.model.analyze(grid)
    except ValueError as exc:return [str(exc)]
    return []

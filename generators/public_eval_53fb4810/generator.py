"""Input-only ordinary generator; protected Racket supplies canonical labels."""
from pathlib import Path
import importlib.util
RULE_TASK_ID = 'ee_53fb4810'
GENERATOR_VERSION = '1.0.0'
HOME=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_ordinary_53fb4810_'+str(HOME),HOME/'workspace/parametric/model.py')
_model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_model)

def generate(seed=0,sample_index=0,difficulty='medium'):
    return _model.sample_input(seed,sample_index,'base','medium' if difficulty is None else difficulty)

def self_check(grid,difficulty='medium'):
    try:
        _model.grid_copy(grid)
        if not _model.analyze(grid):return ['No blue anchor with an observed beam']
    except (TypeError,ValueError,IndexError) as exc:return [str(exc)]
    return []

"""Ordinary input generator; all production labels are supplied by Racket."""
from pathlib import Path
import importlib.util
RULE_TASK_ID = 'ee_7666fa5d'
GENERATOR_VERSION = '1.0.0'
HOME=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_ordinary_7666fa5d_'+str(HOME),HOME/'workspace/parametric/model.py')
_model=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_model)

def generate(seed=0,sample_index=0,difficulty='medium'):
    return _model.sample_input(seed,sample_index,'base','medium' if difficulty is None else difficulty)

def self_check(grid,difficulty='medium'):
    try:
        _model.grid_copy(grid)
        if len(_model.analyze(grid))<2:return ['At least two strokes are needed']
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []

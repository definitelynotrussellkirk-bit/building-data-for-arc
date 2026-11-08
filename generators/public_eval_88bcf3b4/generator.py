"""Fresh input-only wrapper for the strand/obstacle public-evaluation family."""
from pathlib import Path
import importlib.util

GENERATOR_ID = TASK_ID = 'public_eval_88bcf3b4'
RULE_TASK_ID = 'ee_88bcf3b4'
VERSION = '1.0.0'
SUMMARY = 'Measure finite strands, derive obstacle silhouettes, and straighten along their contours.'


def _adapter():
    path = Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
    spec = importlib.util.spec_from_file_location('_strand_local_adapter',path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def generate(seed, sample_index, *, difficulty=None, **overrides):
    a = _adapter(); a.integer(seed,0,2**63-1,'seed'); a.integer(sample_index,0,2**63-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard') or overrides:
        raise ValueError('Unsupported generation request')
    index = 3 if difficulty == 'hard' else sample_index % 4
    return a.sample((seed + sample_index//4) % (2**63), 'query', index)


def self_check(input_grid):
    return _adapter().input_errors(input_grid)

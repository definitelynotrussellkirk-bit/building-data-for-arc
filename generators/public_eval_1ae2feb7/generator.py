"""Fresh run-code inputs; no official fixtures or lookup labels are used."""
from pathlib import Path
import importlib.util
GENERATOR_ID = TASK_ID = 'public_eval_1ae2feb7'
RULE_TASK_ID = 'ee_1ae2feb7'
VERSION = '1.0.0'
SUMMARY = 'Derive run periods, then superpose outward pulses with near-run priority.'


def _adapter():
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
    spec=importlib.util.spec_from_file_location('_pulse_local_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def generate(seed, sample_index, *, difficulty=None, **overrides):
    a=_adapter();a.integer(seed,0,2**63-1,'seed');a.integer(sample_index,0,2**63-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Unsupported difficulty')
    if overrides:raise ValueError('No generation overrides are declared')
    mixed=(seed+sample_index*104729)%(2**63)
    return a.sample(mixed,'query',3 if difficulty=='hard' else sample_index%4)


def self_check(value, *, difficulty=None, meta=None):
    a=_adapter()
    try:
        g=a.grid(value);state=a.derive(g);wall=state['separator']
        if not 0<wall<len(g[0])-1:return ['Separator must have both a code and target side']
        if not state['rows']:return ['Missing run codes']
        if any(any(r[:wall]) and any(r[wall+1:]) for r in g):return ['Both sides occupied in one row']
        return []
    except (TypeError,ValueError,IndexError) as error:return [str(error)]

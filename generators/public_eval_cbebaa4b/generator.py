"""Unapproved public-evaluation family; labels are replayed during preflight."""
from pathlib import Path
import importlib.util
import hashlib
RULE_TASK_ID = 'ee_cbebaa4b'
GENERATOR_ID = TASK_ID = 'public_eval_cbebaa4b'
VERSION = '1.0.0'
SUMMARY = 'Assemble red-connected pieces around a yellow anchor.'

def generate(seed=0, sample_index=0, *, difficulty=None, **overrides):
    if type(seed) is not int or seed<0 or type(sample_index) is not int or sample_index<0:
        raise ValueError('seed and sample_index must be exact nonnegative integers')
    if difficulty not in (None,'easy','medium','hard') or overrides:
        raise ValueError('Unsupported generation request')
    path=Path(__file__).resolve().parent/'workspace/parametric/adapter.py'
    spec=importlib.util.spec_from_file_location('_cbebaa4b_native',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    stream=int.from_bytes(hashlib.sha256(f'{TASK_ID}|{seed}|{sample_index//4}'.encode()).digest()[:8],'big')%(2**63)
    episode=module.generate(stream,{'assembly_policy':'assemble'},2,4)
    return episode['test'][sample_index%4]['input']

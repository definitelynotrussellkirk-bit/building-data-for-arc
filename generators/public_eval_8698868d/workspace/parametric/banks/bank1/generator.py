"""Fresh canonical inputs for public parent 8698868d; no embedded original data."""
import hashlib
import importlib.util
from pathlib import Path
import sys

TASK_ID='public_eval_8698868d'
GENERATOR_VERSION='1.0.0'
_PATH=Path(__file__).resolve().parent/'workspace/parametric/family.py'
_NAME='_panel_family_'+hashlib.sha256(str(_PATH).encode()).hexdigest()
if _NAME not in sys.modules:
    _spec=importlib.util.spec_from_file_location(_NAME,_PATH)
    _module=importlib.util.module_from_spec(_spec);sys.modules[_NAME]=_module;_spec.loader.exec_module(_module)
_family=sys.modules[_NAME]


def generate(seed=0,sample_index=0,difficulty='medium',**overrides):
    if overrides: raise ValueError('no additional controls: '+', '.join(sorted(overrides)))
    return _family.sample_input(seed,sample_index,difficulty)

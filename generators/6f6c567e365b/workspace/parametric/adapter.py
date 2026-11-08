"""Native parametric adapter for 6f6c567e365b."""
from __future__ import annotations
import hashlib, importlib.util, sys
from pathlib import Path
_PATH=Path(__file__).with_name('family.py').resolve()
_NAME='_arc_6f6c567e365b_family_'+hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC=importlib.util.spec_from_file_location(_NAME,_PATH)
if _SPEC is None or _SPEC.loader is None: raise ImportError('cannot load adjacent family.py')
_FAMILY=importlib.util.module_from_spec(_SPEC); sys.modules[_NAME]=_FAMILY; _SPEC.loader.exec_module(_FAMILY)
program=_FAMILY.program
generate=_FAMILY.generate

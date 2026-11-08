"""Native parametric adapter for 69927005ac25."""
from __future__ import annotations
import hashlib, importlib.util, sys
from pathlib import Path
_PATH=Path(__file__).with_name('family.py').resolve()
_NAME='_arc_69927005ac25_family_'+hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC=importlib.util.spec_from_file_location(_NAME,_PATH)
if _SPEC is None or _SPEC.loader is None: raise ImportError('cannot load adjacent family.py')
_FAMILY=importlib.util.module_from_spec(_SPEC); sys.modules[_NAME]=_FAMILY; _SPEC.loader.exec_module(_FAMILY)
program=_FAMILY.program
generate=_FAMILY.generate

# The union keeps the existing helpers available for source-bound old tests.
_UNION_PATH = Path(__file__).resolve().with_name("union.py")
_UNION_SPEC = importlib.util.spec_from_file_location("_union_69927005ac25", _UNION_PATH)
_UNION = importlib.util.module_from_spec(_UNION_SPEC)
_UNION_SPEC.loader.exec_module(_UNION)
program = _UNION.program
generate = _UNION.generate

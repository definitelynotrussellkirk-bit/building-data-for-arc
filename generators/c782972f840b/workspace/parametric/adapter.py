"""Native adapter for the rotation-versus-dihedral relation family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arcp_c782972f840b_equivalence_policy"
_MODULE = sys.modules.get(_NAME)
if _MODULE is None or Path(getattr(_MODULE, "__file__", "")).resolve() != _PATH:
    _SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
    if _SPEC is None or _SPEC.loader is None:  # pragma: no cover
        raise ImportError(_PATH)
    _MODULE = importlib.util.module_from_spec(_SPEC)
    sys.modules[_NAME] = _MODULE
    _SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate

"""Qualification entrypoint for the native landing-metric family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_arcp_6fde852adb54_parametric_prototype"
_MODULE = sys.modules.get(_NAME)
if _MODULE is None:
    _SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
    if _SPEC is None or _SPEC.loader is None:
        raise ImportError(f"cannot load {_PATH}")
    _MODULE = importlib.util.module_from_spec(_SPEC)
    sys.modules[_NAME] = _MODULE
    _SPEC.loader.exec_module(_MODULE)

program = _MODULE.program
generate = _MODULE.generate

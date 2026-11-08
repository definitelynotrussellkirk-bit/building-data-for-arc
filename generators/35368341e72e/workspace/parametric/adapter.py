"""Thin native adapter for the 35368341e72e assembly-order family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_lookup_assembly_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load sibling prototype: {_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _PROTOTYPE
_SPEC.loader.exec_module(_PROTOTYPE)

program = _PROTOTYPE.program_for
generate = _PROTOTYPE.generate_episode

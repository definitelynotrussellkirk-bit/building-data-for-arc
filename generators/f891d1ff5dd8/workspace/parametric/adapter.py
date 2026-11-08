"""Thin native adapter for the marker-derived cycle-phase family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_parametric_f891d1ff5dd8_" + hashlib.sha256(str(_PATH).encode()).hexdigest()
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent marker-phase prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = prototype
_SPEC.loader.exec_module(prototype)

program = prototype.program
generate = prototype.generate

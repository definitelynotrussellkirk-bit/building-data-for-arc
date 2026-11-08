"""Exact-path aliases to the self-contained sidebar-stamp implementation."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import sys

_PATH = Path(__file__).resolve().parents[2] / 'generator.py'
_NAME = '_sidebar_stamp_' + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
_IMPL = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = _IMPL
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_IMPL)

SETTINGS = _IMPL.SETTINGS
RIVALS = _IMPL.RIVALS
check_grid = _IMPL.check_grid
analyze = _IMPL.analyze
render = _IMPL.render
solve = _IMPL.solve
inputs = _IMPL.inputs
components = _IMPL._components
rotate_cells = _IMPL._rotate_cells
bbox = _IMPL._bbox

"""Task-local aliases to the self-contained canonical generator implementation.

The owner maps generator.py alone into ordinary generation runtimes. Keep the
algorithm there; this exact-path alias avoids a duplicate drifting Python oracle.
Protected Racket remains the independent executed label authority.
"""
from pathlib import Path
import hashlib
import importlib.util
import sys
_PATH = Path(__file__).resolve().parents[2] / 'generator.py'
_SPEC = importlib.util.spec_from_file_location('_family_' + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16], _PATH)
_IMPL = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _IMPL
_SPEC.loader.exec_module(_IMPL)
check_grid = _IMPL.check_grid
frame = _IMPL.frame
depth = _IMPL.depth
solve = _IMPL.solve
components = _IMPL.components
intermediate = _IMPL.intermediate
integer = _IMPL.integer
sample = _IMPL.sample

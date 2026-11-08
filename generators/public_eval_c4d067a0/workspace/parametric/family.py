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
integer = _IMPL.integer
check_grid = _IMPL.check_grid
components = _IMPL.components
extract = _IMPL.extract
registrations = _IMPL.registrations
infer = _IMPL.infer
render = _IMPL.render
solve = _IMPL.solve
pattern_components = _IMPL.pattern_components
selected_positions = _IMPL.selected_positions
intermediate = _IMPL.intermediate
make_scene = _IMPL.make_scene
sample = _IMPL.sample

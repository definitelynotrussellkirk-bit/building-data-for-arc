"""Promotion adapter for the c792bb147617 palette-rotation prototype."""
from importlib.util import module_from_spec, spec_from_file_location
import hashlib
from pathlib import Path

_SOURCE = Path(__file__).with_name("prototype.py")
_SPEC = spec_from_file_location(
    "_palette_rotation_c792bb147617_" + hashlib.sha256(str(_SOURCE).encode()).hexdigest(),
    _SOURCE,
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype from {_SOURCE}")
_PROTOTYPE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _orientation(settings):
    if type(settings) is not dict or set(settings) != {"orientation"}:
        raise ValueError("settings must contain exactly the orientation key")
    return _PROTOTYPE._orientation(settings["orientation"])


def program(settings):
    return _PROTOTYPE.program_for(_orientation(settings))


def generate(seed, settings, demos, queries):
    return _PROTOTYPE.generate_episode(
        seed,
        _orientation(settings),
        demos=demos,
        queries=queries,
    )

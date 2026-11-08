"""Native promotion adapter for the proposed 7842d7d91514 rule family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PROTOTYPE_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_arc_7842d7d91514_parametric_prototype", _PROTOTYPE_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load native prototype at {_PROTOTYPE_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings):
    """Return exact complete Racket source for one declared setting."""
    return _PROTOTYPE.program(settings)


def generate(seed, settings, demos, queries):
    """Generate one private fully labelled episode for native qualification."""
    return _PROTOTYPE.generate_episode(
        seed=seed,
        settings=settings,
        demos=demos,
        queries=queries,
    )

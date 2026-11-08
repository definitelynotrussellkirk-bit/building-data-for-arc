"""Promotion adapter for the reviewed expansion-direction prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("506e262f9354_direction_claims_adapter", _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"cannot load local prototype: {_path}")
prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prototype)


_PARAMETER = "expansion_direction"


def _direction(settings):
    if not isinstance(settings, dict) or set(settings) != {_PARAMETER}:
        raise ValueError("settings must contain only expansion_direction")
    direction = settings[_PARAMETER]
    # program_for performs the exact typed/value validation and source guard.
    prototype.program_for(direction)
    return direction


def program(settings):
    """Return exact Racket source for one bounded setting."""
    return prototype.program_for(_direction(settings))


def generate(seed, settings, demos, queries):
    """Return deterministic claims for the qualification worker to replay."""
    return prototype.generate_claims(
        seed,
        expansion_direction=_direction(settings),
        train_count=demos,
        query_count=queries,
    )

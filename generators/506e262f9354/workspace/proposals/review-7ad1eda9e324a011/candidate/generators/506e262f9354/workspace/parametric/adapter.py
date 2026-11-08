"""Promotion adapter for the reviewed expansion-direction prototype."""
from __future__ import annotations

import prototype


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

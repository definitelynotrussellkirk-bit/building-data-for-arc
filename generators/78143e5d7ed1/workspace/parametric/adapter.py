"""Native adapter for episode-fixed sort direction on component crops."""
from __future__ import annotations

from sort_pack_family import episode_pairs, program_for


def _settings(settings) -> str:
    if (type(settings) is not dict or set(settings) != {"sort_direction"}
            or type(settings["sort_direction"]) is not str):
        raise ValueError("settings must contain exactly sort_direction")
    direction = settings["sort_direction"]
    # program_for performs the closed finite-value check.
    program_for(direction)
    return direction


def program(settings) -> str:
    return program_for(_settings(settings))


def generate(seed, settings, demos, queries):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact nonnegative 63-bit integer")
    direction = _settings(settings)
    train, test = episode_pairs(seed, direction, demos, queries)
    return {"train": train, "test": test, "program_solution": program_for(direction)}

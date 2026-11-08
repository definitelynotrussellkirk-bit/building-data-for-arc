"""Native adapter for episode-fixed contact-degree finish."""
from __future__ import annotations

from contact_degree_family import episode_pairs, program_for


def _settings(settings) -> str:
    if (type(settings) is not dict or set(settings) != {"finish"}
            or type(settings["finish"]) is not str):
        raise ValueError("settings must contain exactly finish")
    finish = settings["finish"]
    program_for(finish)
    return finish


def program(settings) -> str:
    return program_for(_settings(settings))


def generate(seed, settings, demos, queries):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an exact nonnegative 63-bit integer")
    finish = _settings(settings)
    train, test = episode_pairs(seed, finish, demos, queries)
    return {"train": train, "test": test, "program_solution": program_for(finish)}

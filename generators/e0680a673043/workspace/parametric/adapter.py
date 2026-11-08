"""Native finite adapter for the e0680a673043 rank-policy family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("e0680a673043_parametric_prototype", _HOME / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local parametric prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _policy(settings) -> str:
    if type(settings) is not dict or set(settings) != {"rank_policy"}:
        raise ValueError("settings must contain exactly rank_policy")
    policy = settings["rank_policy"]
    prototype._validate_policy(policy)
    return policy


def program(settings):
    return prototype.program_for(_policy(settings), root=prototype.ROOT)


def generate(seed, settings, demos=2, queries=4):
    return prototype.generate_claims(
        seed,
        _policy(settings),
        demos,
        queries,
        root=prototype.ROOT,
    )

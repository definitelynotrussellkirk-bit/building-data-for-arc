"""Native promotion adapter for direction-parametric L-tromino projection."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_e99db71ae23d_direction_policy_prototype",
    _HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load direction-policy prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = prototype
_SPEC.loader.exec_module(prototype)


def _policy(settings) -> str:
    if type(settings) is not dict or set(settings) != {"direction_policy"}:
        raise ValueError("settings must contain exactly direction_policy")
    return prototype._validate_policy(settings["direction_policy"])


def program(settings) -> str:
    return prototype.program_for(_policy(settings))


def generate(seed, settings, demos, queries) -> dict:
    return prototype.generate_episode(
        seed,
        policy=_policy(settings),
        demos=demos,
        queries=queries,
    )

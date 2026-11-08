"""Guarded promotion adapter for the proposed scale-basis family."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_SPEC = spec_from_file_location(
    "_scale_basis_78a914ac492e",
    Path(__file__).with_name("prototype.py"),
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent scale-basis prototype")
_PROTOTYPE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _setting(settings):
    if type(settings) is not dict or set(settings) != {_PROTOTYPE.PARAMETER_NAME}:
        raise ValueError("settings must contain exactly {'scale_basis': VALUE}")
    return _PROTOTYPE._validate_setting(settings[_PROTOTYPE.PARAMETER_NAME])


def program(settings):
    return _PROTOTYPE.program_for(_setting(settings))


def generate(seed, settings, demos, queries):
    """Return private labeled pairs; the shared worker replays exact Racket."""
    selected = _setting(settings)
    episode = _PROTOTYPE.build_episode(
        seed,
        scale_basis=selected,
        demos=demos,
        queries=queries,
    )
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["test"]
        ],
        "program_solution": episode["program"],
    }

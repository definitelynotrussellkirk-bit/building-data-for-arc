"""Strict native promotion adapter for 93cbf6ceadf6."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_93cbf6ceadf6_prototype", _HOME / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _settings(settings) -> str:
    if type(settings) is not dict or set(settings) != {"output_transform"}:
        raise ValueError("settings must contain exactly output_transform")
    output_transform = settings["output_transform"]
    prototype._validate_transform(output_transform)
    return output_transform


def program(settings):
    output_transform = _settings(settings)
    return prototype.program_for(output_transform, root=prototype.ROOT)


def generate(seed, settings, demos=2, queries=4):
    output_transform = _settings(settings)
    return prototype.generate_claims(
        seed,
        output_transform=output_transform,
        demos=demos,
        queries=queries,
        root=prototype.ROOT,
    )

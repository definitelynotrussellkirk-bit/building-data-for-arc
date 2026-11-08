"""Strict native promotion adapter for 99d71aabd753."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_99d71aabd753_prototype", _HOME / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _settings(settings) -> tuple[str, str]:
    if type(settings) is not dict or set(settings) != {"alignment", "measure"}:
        raise ValueError("settings must contain exactly alignment and measure")
    alignment = settings["alignment"]
    measure = settings["measure"]
    prototype._validate_alignment(alignment)
    prototype._validate_measure(measure)
    return measure, alignment


def program(settings):
    measure, alignment = _settings(settings)
    return prototype.program_for(measure, alignment, root=prototype.ROOT)


def generate(seed, settings, demos=2, queries=4):
    measure, alignment = _settings(settings)
    return prototype.generate_claims(
        seed,
        measure=measure,
        alignment=alignment,
        demos=demos,
        queries=queries,
        root=prototype.ROOT,
    )

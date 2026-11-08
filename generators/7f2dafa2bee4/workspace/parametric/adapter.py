"""Promotion adapter for the proposed contact-neighborhood family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "contact_mode_prototype_adapter_target",
    _HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load contact-mode prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"contact_mode"}:
        raise ValueError("settings must contain exactly contact_mode")
    if settings["contact_mode"] not in prototype.PARAMETERS["contact_mode"]:
        raise ValueError("contact_mode must be cardinal or eight_neighbor")
    return {"contact_mode": settings["contact_mode"]}


def program(settings):
    return prototype.program(_settings(settings))


def generate(seed, settings, demos, queries):
    return prototype.generate_episode(
        seed,
        settings=_settings(settings),
        demos=demos,
        queries=queries,
    )

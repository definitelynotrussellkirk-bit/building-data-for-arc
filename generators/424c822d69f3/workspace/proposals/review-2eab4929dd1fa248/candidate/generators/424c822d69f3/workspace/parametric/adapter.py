"""Promotion adapter for the proposed rectangle-anchor parameter family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("rectangle_anchor_prototype_adapter_target", _HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load rectangle-anchor prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def program(settings):
    return prototype.rule_text(settings["anchor"])


def generate(seed, settings, demos, queries):
    return prototype.generate_episode(
        seed,
        anchor=settings["anchor"],
        demos=demos,
        queries=queries,
    )

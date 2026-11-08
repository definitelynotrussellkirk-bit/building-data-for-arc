"""Native promotion adapter for the largest-object/size-keyed-partner family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "largest_blue_size_keyed_partner_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent parametric prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _settings(settings):
    return prototype.validate_settings(settings)


def program(settings):
    settings = _settings(settings)
    return prototype.rule_text(settings["mode"])


def generate(seed, settings, demos, queries):
    settings = _settings(settings)
    return prototype.generate_episode(
        seed,
        mode=settings["mode"],
        demos=demos,
        queries=queries,
    )

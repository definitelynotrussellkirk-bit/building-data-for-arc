"""Native adapter for the f2e717c7c250 crop-then-rotate family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_HOME = Path(__file__).resolve().parent
_PATH = _HOME / "prototype.py"
_NAME = "_f2e717c7c250_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:12]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = prototype
_SPEC.loader.exec_module(prototype)


def program(settings):
    values = prototype.validate_settings(settings)
    return prototype.rule_text(values["postprocess"])


def generate(seed, settings, demos=3, queries=4):
    values = prototype.validate_settings(settings)
    return prototype.generate_episode(
        seed,
        postprocess=values["postprocess"],
        demos=demos,
        queries=queries,
    )


public_turn = prototype.public_turn

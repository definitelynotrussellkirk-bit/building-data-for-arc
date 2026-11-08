"""Native adapter for the a89702404b3c parity-key payload family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

_HOME = Path(__file__).resolve().parent
_PATH = _HOME / "prototype.py"
_NAME = "_a89702404b3c_parametric_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:12]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = prototype
_SPEC.loader.exec_module(prototype)


def program(settings):
    values = prototype.validate_settings(settings)
    return prototype.program_for(values["rule_mode"])


def generate(seed, settings, demos=3, queries=4):
    values = prototype.validate_settings(settings)
    return prototype.generate_episode(seed, values["rule_mode"], demos, queries)


public_turn = prototype.public_turn

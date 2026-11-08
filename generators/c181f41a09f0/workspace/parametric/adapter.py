"""Thin promotion adapter for c181f41a09f0's task-local sequential prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location("_task_c181f41a09f0_parametric", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"travel_rule"}:
        raise ValueError("settings must contain exactly travel_rule")
    rule = settings["travel_rule"]
    _PROTOTYPE._validate_rule(rule)
    return rule


def program(settings):
    return _PROTOTYPE.program_for(_setting(settings))


def generate(seed, settings, demos, queries):
    rule = _setting(settings)
    return _PROTOTYPE.generate_claimed_episode(seed, rule, demos, queries)

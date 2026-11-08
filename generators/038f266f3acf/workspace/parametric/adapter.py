"""Thin native adapter for the adjacent marker-derived beam-width prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


_source = Path(__file__).resolve().with_name("beam_width.py")
if _source.is_symlink() or not _source.is_file():
    raise ImportError("The adapter requires its adjacent regular beam_width.py")
_body = _source.read_bytes()
_name = "_beam_width_native_" + hashlib.sha256(str(_source).encode() + _body).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _source)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load adjacent prototype: {_source}")
_prototype = importlib.util.module_from_spec(_spec)
exec(compile(_body, str(_source), "exec"), _prototype.__dict__)


def _multiplier(settings):
    if type(settings) is not dict or set(settings) != {"wing_multiplier"}:
        raise ValueError("settings must contain exactly wing_multiplier")
    value = settings["wing_multiplier"]
    if type(value) is not int or value not in _prototype.ALLOWED_MULTIPLIERS:
        raise ValueError("wing_multiplier must be the exact integer 1 or 2")
    return value


def program(settings):
    return _prototype.materialize_program(_multiplier(settings))


def generate(seed, settings, demos, queries):
    episode = _prototype.generate_native_episode(
        seed=seed,
        wing_multiplier=_multiplier(settings),
        n_train=demos,
        n_test=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }

"""Thin native adapter for the adjacent, source-bound frequency prototype."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


_source = Path(__file__).resolve().with_name("prototype.py")
if _source.is_symlink() or not _source.is_file():
    raise ImportError("The adapter requires its adjacent regular prototype.py")
_body = _source.read_bytes()
_name = "_section_frequency_native_" + hashlib.sha256(str(_source).encode() + _body).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _source)
_prototype = importlib.util.module_from_spec(_spec)
# Compile the exact adjacent bytes; do not import a cached bare `prototype` or
# let timestamp-based bytecode reuse substitute a different source revision.
exec(compile(_body, str(_source), "exec"), _prototype.__dict__)


def _selection(settings):
    if type(settings) is not dict or set(settings) != {"selection"}:
        raise ValueError("settings must contain exactly selection")
    value = settings["selection"]
    if type(value) is not str or value not in _prototype.SELECTIONS:
        raise ValueError("selection must be most_frequent or least_frequent")
    return value


def program(settings):
    return _prototype.materialize_program(_selection(settings))


def generate(seed, settings, demos, queries):
    episode = _prototype.generate_episode(seed, selection=_selection(settings),
                                           demos=demos, queries=queries)
    return {"train": episode["train"], "test": episode["test"],
            "program_solution": episode["program"]}

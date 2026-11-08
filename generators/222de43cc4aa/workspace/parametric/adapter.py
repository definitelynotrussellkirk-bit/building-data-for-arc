"""Thin promotion adapter for the proposed round-trip-count prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any

_spec = importlib.util.spec_from_file_location(
    "_arc_round_trip_prototype_222de43cc4aa",
    Path(__file__).resolve().with_name("prototype.py"),
)
assert _spec and _spec.loader
prototype = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = prototype
_spec.loader.exec_module(prototype)


def _round_trips(settings: Any) -> int:
    if type(settings) is not dict or set(settings) != {"round_trips"}:
        raise ValueError("settings must contain exactly round_trips")
    value = settings["round_trips"]
    # rule_source is the one source of truth for typed finite validation.
    prototype.rule_source(value)
    return value


def _count(name: str, value: Any, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be a literal integer in {minimum}..{maximum}")
    return value


def program(settings):
    return prototype.rule_source(_round_trips(settings))


def generate(seed, settings, demos, queries):
    demo_count = _count(
        "demos",
        demos,
        prototype.DEFAULT_DEMO_COUNT,
        prototype.MAX_DEMO_COUNT,
    )
    query_count = _count("queries", queries, 1, prototype.MAX_QUERY_COUNT)
    episode = prototype.generate_episode(
        seed,
        round_trips=_round_trips(settings),
        demos=demo_count,
        queries=query_count,
    )
    return {**episode, "program_solution": episode["program"]}

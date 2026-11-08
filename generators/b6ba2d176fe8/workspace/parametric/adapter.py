"""Promotion adapter for the proposed b6ba2d176fe8 sort-order prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "b6ba2d176fe8_sort_order_prototype_adapter",
    HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - import guard
    raise ImportError("cannot load local sort-order prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _settings(settings) -> prototype.Settings:
    if type(settings) is not dict or set(settings) != {"sort_order"}:
        raise ValueError("settings must name exactly sort_order")
    return prototype.Settings(settings["sort_order"])


def program(settings) -> str:
    return prototype.program(_settings(settings))


def generate(seed, settings, demos, queries) -> dict:
    episode = prototype.build_claimed_episode(
        seed,
        _settings(settings),
        demos=demos,
        queries=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }

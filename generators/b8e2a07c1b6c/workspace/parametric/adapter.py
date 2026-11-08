"""Thin promotion adapter for the proposed extension-length component."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any


def _load_prototype():
    path = Path(__file__).with_name("prototype.py")
    name = "_arcpuzzles_b8e2a07c1b6c_extension_length_prototype"
    module = sys.modules.get(name)
    if module is not None and Path(module.__file__).resolve() == path.resolve():
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load extension-length prototype at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load_prototype()


def _setting(settings: Any) -> int:
    if type(settings) is not dict or set(settings) != {"extension_length"}:
        raise ValueError("settings must name exactly extension_length")
    try:
        return PROTOTYPE._validate_extension_length(settings["extension_length"])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"settings contain invalid extension_length: {settings.get('extension_length')!r}"
        ) from exc


def program(settings: dict[str, Any]) -> str:
    return PROTOTYPE.materialize_rule(_setting(settings))


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int,
    queries: int,
) -> dict[str, Any]:
    """Return a fully labeled matched-input episode for qualification.

    The shared qualification worker independently re-executes every claim
    through protected Racket.  This adapter reuses the reviewed prototype and
    never forks its sampler or rule materialization.
    """
    selected = _setting(settings)
    public, private = PROTOTYPE.generate_episode(
        seed,
        extension_length=selected,
        demo_count=demos,
        query_count=queries,
    )
    test = [
        {"input": pair["input"], "output": output}
        for pair, output in zip(public["test"], private["query_answers"], strict=True)
    ]
    return {
        "train": public["train"],
        "test": test,
        "program_solution": program(settings),
    }

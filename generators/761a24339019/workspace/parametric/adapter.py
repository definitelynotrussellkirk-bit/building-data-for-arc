"""Thin promotion adapter for the unapproved stamp-transform prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


_PROTOTYPE_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_arcpuzzles_761a24339019_parametric_prototype", _PROTOTYPE_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load prototype from {_PROTOTYPE_PATH}")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def program(settings: Any) -> str:
    """Return exact Racket source for one declared parameter setting."""
    return _PROTOTYPE.materialize_rule(settings)


def generate(
    seed: Any,
    settings: Any,
    demos: Any,
    queries: Any,
    *,
    bridge: Any = None,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Generate one fixed-setting private episode for future qualification."""
    return _PROTOTYPE.generate_episode(
        seed,
        settings=settings,
        demos=demos,
        queries=queries,
        bridge=bridge,
        root=root,
    )

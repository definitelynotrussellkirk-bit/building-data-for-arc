"""Thin native-promotion adapter for the 083ba0fc4534 agreement family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "consensus_parametric_prototype_adapter_target", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling consensus parametric prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"agreement"}:
        raise ValueError("settings must contain exactly agreement")
    agreement = settings["agreement"]
    if type(agreement) is not str or agreement not in _PROTOTYPE.AGREEMENTS:
        raise ValueError(f"agreement must be one of {list(_PROTOTYPE.AGREEMENTS)}")
    return {"agreement": agreement}


def program(settings: dict[str, Any]) -> str:
    checked = _settings(settings)
    return _PROTOTYPE.program_for(checked["agreement"])


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    checked = _settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        agreement=checked["agreement"],
        demos=demos,
        queries=queries,
    )

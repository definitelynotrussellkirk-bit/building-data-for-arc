"""Native promotion adapter for the transform-matching family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "panel_match_parametric_prototype_adapter_target", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling transform-matching prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"match_policy"}:
        raise ValueError("settings must contain exactly match_policy")
    policy = settings["match_policy"]
    if type(policy) is not str or policy not in _PROTOTYPE.MATCH_POLICIES:
        raise ValueError(f"match_policy must be one of {_PROTOTYPE.MATCH_POLICIES}")
    return {"match_policy": policy}


def program(settings: dict[str, Any]) -> str:
    checked = _settings(settings)
    return _PROTOTYPE.rule_text(checked["match_policy"])


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    checked = _settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        match_policy=checked["match_policy"],
        demos=demos,
        queries=queries,
    )

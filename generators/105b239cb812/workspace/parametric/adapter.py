"""Thin native-promotion adapter for the 105b239cb812 application family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "transform_application_parametric_prototype_adapter_target",
    _HERE / "prototype.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling transform-application prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"application"}:
        raise ValueError("settings must contain exactly application")
    application = settings["application"]
    if type(application) is not str or application not in _PROTOTYPE.APPLICATIONS:
        raise ValueError(f"application must be one of {list(_PROTOTYPE.APPLICATIONS)}")
    return {"application": application}


def program(settings: dict[str, Any]) -> str:
    checked = _settings(settings)
    return _PROTOTYPE.program_for(checked["application"])


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    checked = _settings(settings)
    return _PROTOTYPE.generate_episode(
        seed,
        application=checked["application"],
        demos=demos,
        queries=queries,
    )

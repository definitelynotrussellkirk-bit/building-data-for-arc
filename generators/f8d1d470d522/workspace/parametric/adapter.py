"""Native promotion adapter for the f8d1d470d522 turn-preference family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "f8d1d470d522_turn_preference_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load sibling turn-preference prototype")
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"turn_preference"}:
        raise ValueError("settings must contain exactly {'turn_preference'}")
    preference = settings["turn_preference"]
    if type(preference) is not str or preference not in _PROTOTYPE.ALLOWED_TURN_PREFERENCES:
        raise ValueError(
            "turn_preference must be one of "
            f"{_PROTOTYPE.ALLOWED_TURN_PREFERENCES}"
        )
    return {"turn_preference": preference}


def _counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly 4")


def program(settings: dict[str, Any]) -> str:
    checked = _settings(settings)
    return _PROTOTYPE.program_for(checked["turn_preference"])


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 2,
    queries: int = 4,
) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    checked = _settings(settings)
    _counts(demos, queries)
    return _PROTOTYPE.generate_episode(
        seed,
        checked["turn_preference"],
        demos,
        queries,
    )

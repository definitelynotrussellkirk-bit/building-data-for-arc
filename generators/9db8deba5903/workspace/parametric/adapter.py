"""Native promotion adapter for the rotation/component family."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from typing import Any

_PATH = Path(__file__).resolve().with_name("prototype.py")
_NAME = "_parametric_9db8_" + hashlib.sha256(str(_PATH).encode()).hexdigest()[:16]
_SPEC = importlib.util.spec_from_file_location(_NAME, _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(_PATH)
_PROTOTYPE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROTOTYPE)


def _settings(settings: Any) -> dict[str, str]:
    return _PROTOTYPE.validate_settings(settings)


def program(settings: dict[str, Any]) -> str:
    checked = _settings(settings)
    return _PROTOTYPE.rule_text(checked["mode"])


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    checked = _settings(settings)
    episode = _PROTOTYPE.generate_episode(
        seed,
        mode=checked["mode"],
        demos=demos,
        queries=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }

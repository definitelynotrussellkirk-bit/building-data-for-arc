"""Native promotion adapter for query operand order in 0938f7c346fb."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("query_operand_order_prototype", _HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load query-operand-order prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _settings(settings) -> dict:
    if type(settings) is not dict or set(settings) != {"query_operand_order"}:
        raise ValueError("settings must contain exactly query_operand_order")
    order = settings["query_operand_order"]
    if type(order) is not str or order not in prototype.ORDERS:
        raise ValueError(f"query_operand_order must be one of {prototype.ORDERS}")
    return settings


def program(settings):
    settings = _settings(settings)
    return prototype.program_for(settings["query_operand_order"])


def generate(seed, settings, demos, queries):
    settings = _settings(settings)
    return prototype.generate_episode(seed, settings["query_operand_order"], demos, queries)

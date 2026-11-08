"""Native adapter: exact adjacent prototype, fixed private rule, executed labels."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("orientation.py")
_spec = importlib.util.spec_from_file_location("cf5ccd73cfe5_native_orientation", _path)
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"orientation"}:
        raise ValueError("settings must name exactly orientation")
    value = settings["orientation"]
    if type(value) is not str or value not in _prototype.SETTINGS:
        raise ValueError("undeclared orientation")
    return value


def program(settings):
    return _prototype.program(_setting(settings))


def generate(seed, settings, demos, queries):
    setting = _setting(settings)
    for name, value, low, high in (("seed", seed, 0, 2**63 - 1),
                                   ("demos", demos, 2, 6), ("queries", queries, 1, 4)):
        _prototype._integer(name, value, low, high)
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge() as bridge:
        public, private = _prototype.build_episode(seed, bridge, setting, demos=demos, queries=queries)
    return {"train": public["train"],
            "test": [{"input": pair["input"], "output": output}
                     for pair, output in zip(public["test"], private["query_outputs"])],
            "program_solution": program(settings)}

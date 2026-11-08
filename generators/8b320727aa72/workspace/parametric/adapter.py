"""Native mark / restore / restore-then-component-mark parametric family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path


def _load(filename):
    path = Path(__file__).with_name(filename)
    name = "_arc_8b320727aa72_" + path.stem + "_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy = _load("prototype.py")
inputs = _load("native_inputs.py")
analyze = inputs.analyze
execute = legacy.execute_rule
ACTIONS = ("mark", "restore", "mark_component")


def _action(settings):
    if (type(settings) is not dict or set(settings) != {"disagreement_action"}
            or type(settings["disagreement_action"]) is not str
            or settings["disagreement_action"] not in ACTIONS):
        raise ValueError("settings must contain exactly a declared disagreement_action")
    return settings["disagreement_action"]


def program(settings):
    action = _action(settings)
    if action == "mark":
        return legacy.rule_for("mark")
    source = Path(__file__).with_name("native_rule.rkt").read_text(encoding="utf-8")
    return source if action == "mark_component" else source.replace("(recolor-cells consensus marked 1)", "consensus")


def generate(seed, settings, demos=3, queries=4):
    action = _action(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    episode = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    for split, role, count in (("train", "demo", demos), ("test", "query", queries)):
        for index in range(count):
            for attempt in range(8):
                grid = inputs.sample(seed, role, index,
                                     expanded=role == "query" and index == 3 and action != "mark",
                                     attempt=attempt)
                fingerprint = json.dumps(grid, separators=(",", ":"))
                if fingerprint not in seen:
                    break
            else:
                raise ValueError("distinct-input retry budget exhausted")
            seen.add(fingerprint)
            info = analyze(grid)
            if action == "mark_component":
                output = inputs.component_output(info)
            else:
                output = deepcopy(info["consensus"])
                if action == "mark":
                    for r, c in info["disagreements"]:
                        output[r][c] = 1
            episode[split].append({"input": grid, "output": output})
    return episode

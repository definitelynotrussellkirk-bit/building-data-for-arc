"""Native matched-input adapter for routed pocket propagation."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import random
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
TASK = "public_eval_8b7bacbf"
VERSION = "1.0.0"


def _local(name: str):
    path = BASE / f"{name}.py"
    key = "_routes_" + name + "_" + hashlib.sha256(str(path).encode()).hexdigest()
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[key] = module
        spec.loader.exec_module(module)
    return sys.modules[key]


model = _local("model")


def _bridge(settings: object) -> bool:
    if type(settings) is not dict or set(settings) != {"bridge_short_gaps"}:
        raise ValueError("settings must contain exactly bridge_short_gaps")
    value = settings["bridge_short_gaps"]
    if type(value) is not bool:
        raise ValueError("bridge_short_gaps must be Boolean")
    return value


def program(settings: object) -> str:
    filename = "canonical.rkt" if _bridge(settings) else "no_bridge.rkt"
    return (BASE / filename).read_text()


def sample_input(seed: int, index: int) -> list[list[int]]:
    return model.sample_input(seed, index)


def intermediate(grid: list[list[int]], settings: object) -> dict[str, object]:
    return model.analyze(grid, bridge_short_gaps=_bridge(settings))


def generate(seed: int, settings: object, demos: int = 2, queries: int = 4) -> dict[str, object]:
    bridge = _bridge(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")

    def pair(index: int) -> dict[str, list[list[int]]]:
        grid = sample_input(seed, index)
        return {"input": grid, "output": model.solve(grid, bridge_short_gaps=bridge)}

    train = [pair(index) for index in range(demos)]
    bank = [pair(100 + index) for index in range(4)]
    return {
        "train": train,
        "test": copy.deepcopy(bank[:queries]),
        "program_solution": program(settings),
        "settings": copy.deepcopy(settings),
        "seed": seed,
        "private": {"query_bank": bank},
    }


def public_view(episode: dict[str, object], turn: int = 0, presentation_seed: int = 0) -> dict[str, object]:
    if type(turn) is not int or not 0 <= turn < 4:
        raise ValueError("turn must be an exact integer in 0..3")
    if type(presentation_seed) is not int:
        raise ValueError("presentation_seed must be an exact integer")
    bank = episode["private"]["query_bank"]
    if type(bank) is not list or len(bank) != 4:
        raise ValueError("episode must retain exactly four private queries")
    source_seed = episode.get("seed")
    if type(source_seed) is not int:
        raise ValueError("episode must retain its exact integer source seed")
    order = list(range(4))
    random.Random(f"{TASK}|{source_seed}|{presentation_seed}").shuffle(order)
    train = [
        {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
        for pair in episode["train"]
    ]
    return {
        "train": train,
        "test": [{"input": copy.deepcopy(bank[order[turn]]["input"])}],
    }

"""Native matched-input parametric adapter for public parent 45a5af55."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import random
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
TASK = "public_eval_45a5af55"
VERSION = "1.0.0"


def _local(name: str):
    path = BASE / f"{name}.py"
    key = "_layers_" + name + "_" + hashlib.sha256(str(path).encode()).hexdigest()
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[key] = module
        spec.loader.exec_module(module)
    return sys.modules[key]


model = _local("model")


def _scope(settings: object) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"scope"}
        or settings["scope"] not in ("full", "from_longest_run")
    ):
        raise ValueError("settings must be exactly scope=full|from_longest_run")
    return settings["scope"]


def program(settings: object) -> str:
    scope = _scope(settings)
    filename = "canonical.rkt" if scope == "full" else "from_longest_run.rkt"
    return (BASE / filename).read_text()


def sample_input(seed: int, index: int) -> list[list[int]]:
    return model.sample_input(seed, index)


def generate(seed: int, settings: object, demos: int = 2, queries: int = 4) -> dict[str, object]:
    scope = _scope(settings)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")

    def pair(index: int) -> dict[str, list[list[int]]]:
        grid = sample_input(seed, index)
        return {"input": grid, "output": model.solve(grid, scope=scope)}

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
    query = bank[order[turn]]
    return {"train": train, "test": [{"input": copy.deepcopy(query["input"])}]}

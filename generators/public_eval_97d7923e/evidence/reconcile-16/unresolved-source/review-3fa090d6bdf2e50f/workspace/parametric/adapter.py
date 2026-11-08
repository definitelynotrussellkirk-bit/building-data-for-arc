"""Episode-fixed adapter for public_eval_97d7923e."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import random
import sys
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent


def _load(name: str):
    path = BASE / f"{name}.py"
    key = f"_sticks_{name}_{hashlib.sha256(str(path).encode()).hexdigest()[:16]}"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[key] = module
        spec.loader.exec_module(module)
    return sys.modules[key]


engine = _load("engine")
sampler = _load("sampler")
SETTINGS = ({"finish": "rank_only"}, {"finish": "highlight_longest_selected"})


def validate_settings(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"finish"}
        or type(settings["finish"]) is not str
        or settings["finish"] not in {"rank_only", "highlight_longest_selected"}
    ):
        raise ValueError("expected exactly finish=rank_only|highlight_longest_selected")
    return settings["finish"]


def program(settings: Any) -> str:
    finish = validate_settings(settings)
    filename = "canonical.rkt" if finish == "rank_only" else "highlight.rkt"
    return (BASE / filename).read_text()


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    sampler.integer(seed, 0, 2**63 - 1, "seed")
    sampler.integer(demos, 2, 6, "demos")
    sampler.integer(queries, 1, 4, "queries")
    finish = validate_settings(settings)

    def pair(split: str, index: int) -> dict[str, Any]:
        inp = sampler.draw(seed, index, split=split)
        return {"input": inp, "output": engine.solve(inp, finish)}

    train = [pair("train", i) for i in range(demos)]
    bank = [pair("test", 100 + i) for i in range(3)]
    random.Random(f"sticks-private-order-v1:{seed}").shuffle(bank)
    bank.append(pair("test", 103))
    return {
        "train": train,
        "test": copy.deepcopy(bank[:queries]),
        "private_query_bank": bank,
        "program_solution": program(settings),
        "settings": copy.deepcopy(settings),
        "seed": seed,
    }


def public_view(episode: dict[str, Any], *, turn: int, presentation_seed: int = 0) -> dict[str, Any]:
    sampler.integer(turn, 0, 3, "turn")
    sampler.integer(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    train = copy.deepcopy(episode["train"])
    bank = copy.deepcopy(episode.get("private_query_bank", episode["test"]))
    # Presentation order is private and independent from source sampling order.
    random.Random(f"sticks-public-order-v1:{presentation_seed}").shuffle(bank)
    if turn >= len(bank):
        raise ValueError("turn exceeds query bank")
    return {"train": train, "test": [{"input": bank[turn]["input"]}]}

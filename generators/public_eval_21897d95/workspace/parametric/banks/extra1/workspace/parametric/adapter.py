"""Native matched-input adapter for public_eval_21897d95."""
from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

BASE = Path(__file__).resolve().parent
_name = "_family2189_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, BASE / "family.py")
family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = family
assert _spec.loader is not None
_spec.loader.exec_module(family)


def _setting(settings: object) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"payload"}
        or type(settings["payload"]) is not str
        or settings["payload"] not in family.SETTINGS
    ):
        raise ValueError("settings must be exactly payload=center_override|host_only")
    return settings["payload"]


def program(settings: object) -> str:
    setting = _setting(settings)
    filename = "canonical.rkt" if setting == "center_override" else "host_only.rkt"
    return (BASE / filename).read_text()


@lru_cache(maxsize=64)
def _bank(seed: int) -> tuple[tuple[list[list[int]], ...], tuple[list[list[int]], ...]]:
    family.integer(seed, 0, 2**63 - 1, "seed")
    demo_shapes, query_shapes = family._shapes()
    demos = tuple(
        family.make_scene(seed, ["demo", i], h, w, rooms=rooms)
        for i, (h, w, rooms) in enumerate(demo_shapes)
    )
    queries = tuple(
        family.make_scene(seed, ["query", i], h, w, rooms=rooms, stress=i == 3)
        for i, (h, w, rooms) in enumerate(query_shapes)
    )
    return demos, queries


def generate(seed: int, settings: dict[str, str], demos: int, queries: int) -> dict[str, object]:
    setting = _setting(settings)
    family.integer(seed, 0, 2**63 - 1, "seed")
    family.integer(demos, 2, 6, "demos")
    family.integer(queries, 1, 4, "queries")
    demo_bank, query_bank = _bank(seed)
    train = [{"input": copy.deepcopy(g), "output": family.solve(g, setting)} for g in demo_bank[:demos]]
    private = [{"input": copy.deepcopy(g), "output": family.solve(g, setting)} for g in query_bank]
    return {
        "train": train,
        "test": copy.deepcopy(private[:queries]),
        "private_query_bank": private,
        "settings": {"payload": setting},
        "seed": seed,
        "program_solution": program(settings),
    }


def presentation_order(presentation_seed: int) -> list[int]:
    family.integer(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    order = list(range(4))
    material = hashlib.sha256(f"21897d95:{presentation_seed}".encode()).digest()[:16]
    random.Random(int.from_bytes(material, "big")).shuffle(order)
    return order


def public_view(episode: dict[str, object], source_query_index: int) -> dict[str, object]:
    family.integer(source_query_index, 0, 3, "source_query_index")
    bank = episode.get("private_query_bank")
    if type(bank) is not list or len(bank) != 4:
        raise ValueError("controller must retain exactly four private queries")
    visible = {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(bank[source_query_index]["input"])}],
    }
    return json.loads(json.dumps(visible, sort_keys=True, separators=(",", ":")))


def counterfactual_program() -> str:
    return program({"payload": "center_override"})


def intermediate(grid: object, settings: dict[str, str] | None = None) -> dict[str, object]:
    if settings is None:
        settings = {"payload": "center_override"}
    _setting(settings)
    return family.intermediate(grid, settings)


def dependency() -> dict[str, str]:
    return family.dependency()

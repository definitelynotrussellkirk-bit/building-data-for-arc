"""Native parametric adapter for crop completion and enclosed-pocket marking."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARAMETERS = {"pocket_policy": ["preserve", "mark_enclosed"]}
DEFAULT = {"pocket_policy": "preserve"}
_spec = importlib.util.spec_from_file_location("_crop_completion_sampler", HERE / "sampler.py")
BASE = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(BASE)


def _settings(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"pocket_policy"}:
        raise ValueError("settings must contain exactly pocket_policy")
    return BASE._policy(settings["pocket_policy"])


def program(settings: object) -> str:
    policy = _settings(settings)
    return (HERE / ("canonical.rkt" if policy == "preserve" else "mark_enclosed.rkt")).read_text()


def mirror(grid: object, settings: object):
    return BASE.solve(grid, _settings(settings))


def analyze(grid: object, settings: object):
    return BASE.analyze(grid, _settings(settings))


def generate(seed: int, settings: object, demos: int = 2, queries: int = 4):
    policy = _settings(settings)
    BASE._integer(seed, 0, 2**63 - 1, "seed")
    BASE._integer(demos, 2, 6, "demos")
    BASE._integer(queries, 1, 4, "queries")
    demo_scenes, query_scenes, order = BASE.lesson_scenes(seed)

    def pair(scene):
        return {"input": deepcopy(scene["input"]), "output": deepcopy(scene[policy])}

    selected_demos = demo_scenes[:demos]
    selected_queries = query_scenes[:queries]
    return {
        "train": [pair(scene) for scene in selected_demos],
        "test": [pair(scene) for scene in selected_queries],
        "program_solution": program(settings),
        "private": {
            "seed": seed,
            "settings": {"pocket_policy": policy},
            "query_permutation": order,
            "certificates": [deepcopy(scene["certificate"]) for scene in selected_demos + selected_queries],
        },
    }


def public_turn(episode: dict, index: int) -> dict:
    if type(index) is not int or not 0 <= index < len(episode["test"]):
        raise ValueError("invalid query index")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][index]["input"])}],
    }

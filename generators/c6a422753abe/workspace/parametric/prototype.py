"""Proposed source-side versus reflection-side color swap family.

The separator/shape grammar is independent of the private setting. Python
outputs are authoring claims until verify.py replays every retained label via
the protected Racket runtime.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
TASK_ID = "c6a422753abe"
SWAP_LOCATIONS = ("source", "reflection")


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(
        "_c6_parametric_geometry_" + hashlib.sha256(str(path).encode()).hexdigest(), path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
# h, w, axis, side, separator, n_cells, palette.
_DEMOS = (
    (11, 12, "col", "before", 6, 7, "4,8"),
    (12, 9, "row", "after", 4, 7, "2,3"),
    (14, 11, "row", "before", 8, 10, "5,6"),
    (14, 16, "col", "after", 8, 11, "2,8"),
    (18, 20, "row", "after", 9, 14, "3,7"),
    (20, 18, "col", "before", 9, 16, "4,9"),
)
_QUERIES = (
    (13, 17, "col", "before", 8, 9, "2,3"),
    (21, 16, "row", "before", 10, 12, "4,8"),
    (26, 25, "row", "after", 13, 16, "5,6"),
    (30, 30, "col", "before", 15, 18, "2,8"),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"swap_location"}
        or type(settings["swap_location"]) is not str
        or settings["swap_location"] not in SWAP_LOCATIONS
    ):
        raise ValueError("settings must be exactly {'swap_location': 'source'|'reflection'}")
    return settings["swap_location"]


def program(settings):
    location = _setting(settings)
    name = "canonical.rkt" if location == "source" else "reflection-swap.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _derived_seed(seed, split, index, attempt=0):
    raw = json.dumps([TASK_ID, "input-v1", seed, split, index, attempt], separators=(",", ":")).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") & (2**63 - 1)


def sample_input(seed, index, *, split, attempt=0):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(attempt, 0, 31, "attempt")
    specs = _DEMOS if split == "train" else _QUERIES if split == "test" else None
    if specs is None:
        raise ValueError("split must be train or test")
    _integer(index, 0, len(specs) - 1, "index")
    height, width, axis, side, separator, n_cells, palette = specs[index]
    difficulty = "hard" if max(height, width) >= 22 else "medium"
    return GEN.generate(
        _derived_seed(seed, split, index, attempt),
        index + (0 if split == "train" else 100),
        difficulty=difficulty,
        grid_h=height,
        grid_w=width,
        separator_axis=axis,
        separator_index=separator,
        source_side=side,
        n_cells=n_cells,
        palette_pair=palette,
    )


def claimed_output(grid, settings):
    return GEN.rule_mirror(deepcopy(grid), swap_location=_setting(settings))


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    draws = 0
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            for attempt in range(32):
                grid = sample_input(seed, index, split=split, attempt=attempt)
                draws += 1
                key = json.dumps(grid, separators=(",", ":"))
                if key not in seen:
                    break
            else:
                raise ValueError(f"distinct input budget exhausted for {split}[{index}]")
            seen.add(key)
            result[split].append({"input": grid, "output": claimed_output(grid, settings)})
    result["sampling"] = {"draws": draws, "duplicate_rejections": draws - demos - queries}
    return result


def teaching_certificate(episode):
    if type(episode) is not dict or type(episode.get("train")) is not list:
        raise ValueError("episode must contain demonstrations")
    survivors, rejected = [], {}
    for location in SWAP_LOCATIONS:
        setting = {"swap_location": location}
        mismatch = next(
            (i for i, pair in enumerate(episode["train"]) if claimed_output(pair["input"], setting) != pair["output"]),
            None,
        )
        if mismatch is None:
            survivors.append(setting)
        else:
            rejected[location] = mismatch
    return {"survivors": survivors, "rejected_by_demo": rejected, "query_answers_used": False}


def visible_turn(episode, index):
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]})


def public_identity(episode):
    return public_challenge_id(episode)

"""Proposed clockwise/counterclockwise control-6 family for d336f5fb2da4.

Inputs are sampled independently of the private episode setting. Python labels
are authoring claims until workspace/parametric/verify.py replays them through
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
TASK_ID = "d336f5fb2da4"
ROTATIONS = ("cw", "ccw")


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(
        "_d336_parametric_geometry_" + hashlib.sha256(str(path).encode()).hexdigest(), path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
# h, w, control, source, vector. The first two demonstrations are asymmetric
# control-6 witnesses, so every allowed 2..6-demo prefix identifies handedness.
_DEMOS = (
    (14, 17, 6, "asym5", "right3"),
    (17, 14, 6, "l3", "down3"),
    (18, 19, 4, "t4", "diag_down_right"),
    (19, 20, 7, "zig4", "diag_down_left"),
    (22, 24, 6, "stair6", "left3"),
    (24, 22, 4, "asym5", "up3"),
)
_QUERIES = (
    (17, 21, 6, "hook5", "diag_down_right"),
    (22, 19, 7, "stair6", "down3"),
    (26, 27, 4, "t4", "diag_up_left"),
    (30, 30, 6, "asym5", "diag_down_right"),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"magenta_rotation"}
        or type(settings["magenta_rotation"]) is not str
        or settings["magenta_rotation"] not in ROTATIONS
    ):
        raise ValueError("settings must be exactly {'magenta_rotation': 'cw'|'ccw'}")
    return settings["magenta_rotation"]


def program(settings):
    rotation = _setting(settings)
    name = "canonical.rkt" if rotation == "cw" else "counterclockwise.rkt"
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
    height, width, control, source, vector = specs[index]
    difficulty = "hard" if max(height, width) >= 22 else "medium"
    return GEN.generate(
        _derived_seed(seed, split, index, attempt),
        index + (0 if split == "train" else 100),
        difficulty=difficulty,
        grid_h=height,
        grid_w=width,
        control_color=control,
        source_profile=source,
        vector_profile=vector,
    )


def claimed_output(grid, settings):
    return GEN.rule_mirror(deepcopy(grid), magenta_rotation=_setting(settings))


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
    survivors = []
    rejected = {}
    for rotation in ROTATIONS:
        setting = {"magenta_rotation": rotation}
        mismatch = next(
            (
                i
                for i, pair in enumerate(episode["train"])
                if claimed_output(pair["input"], setting) != pair["output"]
            ),
            None,
        )
        if mismatch is None:
            survivors.append(setting)
        else:
            rejected[rotation] = mismatch
    return {"survivors": survivors, "rejected_by_demo": rejected, "query_answers_used": False}


def visible_turn(episode, index):
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    return public_challenge_bytes({"train": episode["train"], "test": [episode["test"][index]]})


def public_identity(episode):
    return public_challenge_id(episode)

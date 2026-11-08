"""Matched-input transform-codebook family for ARC task 600ed4e5d09c.

Both settings use the same lawful input scenes.  The canonical setting preserves
the original key mapping.  The inverse setting interprets each key as the
inverse reflection/rotation where that distinction exists.  In either setting,
the transformed target crop is a genuine intermediate that is then centered
inside the detected frame.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any

TASK_ID = "600ed4e5d09c"
CODEBOOKS = ("canonical", "inverse")
SETTINGS = tuple({"transform_codebook": value} for value in CODEBOOKS)
DEMO_SIZES = ((12, 14), (14, 16), (16, 18), (18, 20), (20, 22), (22, 24))
QUERY_SIZES = ((16, 18), (20, 22), (24, 26), (30, 30))
DEMO_KEYS = (1, 3, 4, 1, 3, 4)
QUERY_KEYS = (4, 1, 3, 2)
HERE = Path(__file__).resolve().parent


def _load_generator():
    path = HERE.parents[1] / "generator.py"
    name = "_generator_600ed4e5d09c_parametric_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _setting(settings: Any) -> str:
    if (
        type(settings) is not dict
        or set(settings) != {"transform_codebook"}
        or type(settings["transform_codebook"]) is not str
        or settings["transform_codebook"] not in CODEBOOKS
    ):
        raise ValueError("settings must be exactly transform_codebook=canonical|inverse")
    return settings["transform_codebook"]


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: dict[str, Any]) -> str:
    codebook = _setting(settings)
    return (HERE / ("canonical.rkt" if codebook == "canonical" else "inverse.rkt")).read_text()


def solve(grid: Any, settings: dict[str, Any]) -> list[list[int]]:
    return GEN.rule_mirror(grid, codebook=_setting(settings))


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _place_shape(
    grid: list[list[int]], cells: tuple[tuple[int, int], ...], r0: int, c0: int, color: int
) -> None:
    for r, c in cells:
        if grid[r0 + r][c0 + c] != 0:
            raise RuntimeError("shape placement collision")
        grid[r0 + r][c0 + c] = color


def _sample_input(
    seed: int, split: str, index: int, *, height: int, width: int, key: int
) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("demo", "query"):
        raise ValueError("split must be demo or query")
    _integer(index, 0, 63, "index")
    _integer(height, 10, 30, "height")
    _integer(width, 10, 30, "width")
    _integer(key, 1, 4, "key")
    rng = _rng(seed, split, index)
    palette = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(palette)
    selected, frame_color, distractor_a, distractor_b = palette[:4]
    # Avoid accidental semantic coupling between the transform key cell and
    # selected/frame colors in visual inspection while keeping key fixed.
    if selected == key:
        selected, palette[4] = palette[4], selected
    if frame_color == selected:
        raise RuntimeError("color construction failed")

    grid = [[0 for _ in range(width)] for _ in range(height)]
    grid[0][0] = selected
    grid[0][width - 1] = key

    frame_h = min(14, max(5, height // 2))
    frame_w = min(16, max(5, width // 2))
    fr0 = height - frame_h - 2
    fc0 = width - frame_w - 2
    GEN.draw_frame(grid, fr0, fc0, fr0 + frame_h - 1, fc0 + frame_w - 1, frame_color)

    orientations = GEN._shape_orientations(GEN._BASE_SHAPE)
    target = orientations[(seed + 3 * index + (0 if split == "demo" else 5)) % len(orientations)]
    _place_shape(grid, target, 1, 1, selected)

    # Two non-outline, non-selected L objects make object parsing nontrivial.
    # One touches the bottom boundary, providing boundary stress without adding
    # a singleton/line that the canonical predicate would misclassify as a frame.
    bottom = ((0, 0), (0, 1), (0, 2), (1, 0))
    _place_shape(grid, bottom, height - 2, 1, distractor_a)
    top_right = ((0, 2), (1, 0), (1, 1), (1, 2))
    _place_shape(grid, top_right, 1, width - 4, distractor_b)

    facts = analyze(grid)
    if not facts["valid"]:
        raise RuntimeError(f"constructed invalid transform-codebook scene: {facts}")
    return grid


def analyze(grid: Any) -> dict[str, Any]:
    try:
        work, selected, key, frames, targets = GEN._semantic_parts(grid)
    except (TypeError, ValueError) as exc:
        return {"valid": False, "error": str(exc)}
    target_orbit = 0
    if len(targets) == 1:
        target_orbit = len(GEN._shape_orientations(GEN._normalize(targets[0]["cells"])))
    fit = False
    if len(frames) == 1 and len(targets) == 1:
        crop = GEN._crop(work, targets[0])
        r0, c0, r1, c1 = frames[0]["bbox"]
        ih, iw = r1 - r0 - 1, c1 - c0 - 1
        fit = all(
            len(GEN.transform_crop(crop, k)) <= ih
            and len(GEN.transform_crop(crop, k)[0]) <= iw
            for k in range(1, 5)
        )
    outputs_distinct = False
    if len(frames) == 1 and len(targets) == 1:
        outputs_distinct = solve(grid, SETTINGS[0]) != solve(grid, SETTINGS[1])
    return {
        "valid": (
            selected != 0
            and 1 <= key <= 4
            and len(frames) == 1
            and len(targets) == 1
            and target_orbit == 8
            and fit
        ),
        "selected_color": selected,
        "transform_key": key,
        "frame_count": len(frames),
        "target_count": len(targets),
        "target_dihedral_orbit": target_orbit,
        "all_transforms_fit": fit,
        "setting_outputs_distinct": outputs_distinct,
    }


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    codebook = _setting(settings)
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")
    normalized = {"transform_codebook": codebook}
    train_inputs = [
        _sample_input(
            seed,
            "demo",
            index,
            height=DEMO_SIZES[index][0],
            width=DEMO_SIZES[index][1],
            key=DEMO_KEYS[index],
        )
        for index in range(demos)
    ]
    test_inputs = [
        _sample_input(
            seed,
            "query",
            index,
            height=QUERY_SIZES[index][0],
            width=QUERY_SIZES[index][1],
            key=QUERY_KEYS[index],
        )
        for index in range(queries)
    ]
    serial = [json.dumps(grid, separators=(",", ":")) for grid in train_inputs + test_inputs]
    if len(serial) != len(set(serial)):
        raise RuntimeError("generated inputs must be unique")
    return {
        "task_id": TASK_ID,
        "settings": copy.deepcopy(normalized),
        "program_solution": program(normalized),
        "train": [
            {"input": copy.deepcopy(grid), "output": solve(grid, normalized)}
            for grid in train_inputs
        ],
        "test": [
            {"input": copy.deepcopy(grid), "output": solve(grid, normalized)}
            for grid in test_inputs
        ],
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index is out of range")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }

"""Matched-input object-boundary scope family for ``37ef814e99dd``.

Step A segments the input into true same-color cardinal objects and derives
component sizes.  The episode-fixed scope then selects either every object
(the exact canonical default) or the unique largest object.  Step B outlines
the selected *actual cell set*, not its bounding box.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
from typing import Any

TASK_ID = "37ef814e99dd"
SETTINGS = ("all_objects", "largest_only")
DEFAULT = "all_objects"
RIVALS = ("opposite_scope", "bbox_perimeter", "keep_filled", "smallest_only")

# (height, width, object count, source-domain profile)
DEMO_SPECS = (
    (12, 14, 2, "mixed"),
    (15, 16, 3, "notched"),
    (18, 14, 3, "mixed"),
    (20, 22, 4, "notched"),
    (26, 24, 4, "mixed"),
    (30, 30, 4, "notched"),
)
QUERY_SPECS = (
    (14, 17, 3, "mixed"),
    (19, 21, 4, "notched"),
    (25, 27, 4, "mixed"),
    (30, 30, 4, "notched"),
)

_BASE = Path(__file__).resolve().parents[2]
_name = "_generator_37ef_" + hashlib.sha256(str(_BASE).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, _BASE / "generator.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load task generator.py")
generator = importlib.util.module_from_spec(_spec)
sys.modules[_name] = generator
_spec.loader.exec_module(generator)


def integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def setting(value: object) -> str:
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("scope must be all_objects or largest_only")
    return value


def _analysis(value: object) -> dict[str, Any]:
    return generator.analyze_scene(value)


def _ranked_objects(value: object) -> list[dict[str, Any]]:
    analysis = _analysis(value)
    return sorted(
        analysis["objects"],
        key=lambda obj: (-obj["size"], obj["bbox"][0], obj["bbox"][1], obj["color"]),
    )


def intermediate(value: object) -> dict[str, Any]:
    analysis = _analysis(value)
    ranked = _ranked_objects(value)
    return {
        "height": analysis["height"],
        "width": analysis["width"],
        "scene_profile": analysis["scene_profile"],
        "object_count": len(analysis["objects"]),
        "objects": [
            {
                "color": obj["color"],
                "size": obj["size"],
                "bbox": list(obj["bbox"]),
                "solid_bbox": obj["solid_bbox"],
                "boundary_size": len(obj["boundary_cells"]),
                "interior_size": len(obj["interior_cells"]),
            }
            for obj in analysis["objects"]
        ],
        "largest_color": ranked[0]["color"],
        "largest_size": ranked[0]["size"],
        "largest_bbox": list(ranked[0]["bbox"]),
        "largest_is_unique": sum(
            obj["size"] == ranked[0]["size"] for obj in analysis["objects"]
        ) == 1,
    }


def solve(value: object, scope: str) -> list[list[int]]:
    return generator.rule_mirror(value, setting(scope))


def _paint_full_selected(value: object, scope: str) -> list[list[int]]:
    mode = setting(scope)
    analysis = _analysis(value)
    if mode == "all_objects":
        objects = analysis["objects"]
    else:
        objects = [_ranked_objects(value)[0]]
    out = [[0] * analysis["width"] for _ in range(analysis["height"])]
    for obj in objects:
        for row, col in obj["cells"]:
            out[row][col] = obj["color"]
    return out


def _smallest_object(value: object) -> dict[str, Any]:
    analysis = _analysis(value)
    return min(
        analysis["objects"],
        key=lambda obj: (obj["size"], obj["bbox"][0], obj["bbox"][1], obj["color"]),
    )


def solve_smallest_only(value: object) -> list[list[int]]:
    analysis = _analysis(value)
    obj = _smallest_object(value)
    out = [[0] * analysis["width"] for _ in range(analysis["height"])]
    for row, col in obj["boundary_cells"]:
        out[row][col] = obj["color"]
    return out


def solve_rival(value: object, scope: str, rival: str) -> list[list[int]]:
    mode = setting(scope)
    if rival not in RIVALS:
        raise ValueError("unknown rival")
    if rival == "opposite_scope":
        return solve(value, "largest_only" if mode == "all_objects" else "all_objects")
    if rival == "bbox_perimeter":
        return generator.bbox_outline_rival(value, mode)
    if rival == "keep_filled":
        return _paint_full_selected(value, mode)
    return solve_smallest_only(value)


def _derived_seed(seed: int, split: str, index: int) -> int:
    digest = hashlib.sha256(
        f"{TASK_ID}:boundary-scope-v1:{seed}:{split}:{index}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)


def _draw(seed: int, split: str, index: int) -> list[list[int]]:
    specs = DEMO_SPECS if split == "train" else QUERY_SPECS
    height, width, count, profile = specs[index]
    sample_index = index if split == "train" else 100 + index
    data = generator.generate(
        _derived_seed(seed, split, index),
        sample_index,
        difficulty="hard" if max(height, width) >= 22 else "medium",
        grid_h=height,
        grid_w=width,
        n_blobs=count,
        scene_profile=profile,
    )
    analysis = _analysis(data)
    sizes = [obj["size"] for obj in analysis["objects"]]
    if sizes.count(max(sizes)) != 1:
        raise AssertionError("family requires a unique largest object")
    if not any(not obj["solid_bbox"] for obj in analysis["objects"]):
        raise AssertionError("family requires a nonrectangular object")
    return data


def generate(seed: object, scope: object, demos: object, queries: object) -> dict[str, Any]:
    seed_i = integer(seed, 0, 2**63 - 1, "seed")
    mode = setting(scope)
    demo_count = integer(demos, 2, 6, "demos")
    query_count = integer(queries, 1, 4, "queries")
    train = []
    for index in range(demo_count):
        data = _draw(seed_i, "train", index)
        train.append({"input": data, "output": solve(data, mode)})
    test = []
    for index in range(query_count):
        data = _draw(seed_i, "test", index)
        test.append({"input": data, "output": solve(data, mode)})
    return {
        "train": train,
        "test": test,
        "private_query_bank": copy.deepcopy(test),
    }

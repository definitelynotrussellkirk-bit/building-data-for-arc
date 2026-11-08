"""Native token-size / spatial-order family for task 31b8bedd699a.

Stage A derives the output axis from the top-left row/column ranges of hollow
frames (exactly the canonical comparison, with horizontal ties). Stage B sorts
those frames along the derived axis using the episode-fixed order and redraws
fixed-size outline tokens. The canonical setting is byte-for-byte unchanged.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import types
from typing import Any


_PROTOTYPE_PATH = Path(__file__).resolve().with_name("prototype.py")
_PROTOTYPE_BODY = _PROTOTYPE_PATH.read_bytes()
_PROTOTYPE_NAME = "_token_order_prototype_31b8bedd699a_" + hashlib.sha256(
    str(_PROTOTYPE_PATH).encode() + _PROTOTYPE_BODY
).hexdigest()
prototype = sys.modules.get(_PROTOTYPE_NAME)
if prototype is None:
    prototype = types.ModuleType(_PROTOTYPE_NAME)
    prototype.__file__ = str(_PROTOTYPE_PATH)
    sys.modules[_PROTOTYPE_NAME] = prototype
    try:
        exec(
            compile(_PROTOTYPE_BODY, str(_PROTOTYPE_PATH), "exec"),
            prototype.__dict__,
        )
    except BaseException:
        sys.modules.pop(_PROTOTYPE_NAME, None)
        raise


TOKEN_SIZES = (3, 4, 5)
ORDERS = ("ascending", "descending")
ALL_SETTINGS = tuple(
    {"token_size": token_size, "order": order}
    for token_size in TOKEN_SIZES
    for order in ORDERS
)
DEFAULT = {"token_size": 4, "order": "ascending"}
TEACHING_RIVALS = (
    "always_vertical",
    "always_horizontal",
    "reverse_order",
    "include_solids_axis",
    "row_major_order",
    "color_ascending",
    "color_descending",
    "component_size_order",
)

# The first two demonstrations deliberately expose both axis branches. Broad
# profiles include solids and non-4x4 frames, so the minimum lesson also rejects
# fixed-axis, include-solids-axis, crop, and no-normalization explanations.
DEMO_SPECS = (
    ("vertical", 1),
    ("horizontal", 1),
    ("tie", 1),
    ("vertical", 0),
    ("horizontal", 0),
    ("tie", 0),
)
# Query slots are fixed independently of demo count. Query 1 is a genuine 30x30
# five-frame/three-solid stress case; each query remains novel and setting-blind.
QUERY_SPECS = (
    ("tie", 2),
    ("vertical", 2),
    ("horizontal", 2),
    ("vertical", 3),
)

_REVERSE_TARGET = (
    "(sorted-frames (sort-by frame-info\n"
    "                                        (lambda (f)\n"
    "                                          (if vertical (second f) (list-ref f 2)))))"
)
_REVERSE_REPLACEMENT = (
    "(sorted-frames (reverse\n"
    "                                  (sort-by frame-info\n"
    "                                           (lambda (f)\n"
    "                                             (if vertical (second f) (list-ref f 2))))))"
)


def _integer(name: str, value: Any, lower: int, upper: int) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an exact integer in {lower}..{upper}")
    return value


def validate_settings(settings: Any) -> dict[str, Any]:
    if type(settings) is not dict or set(settings) != {"token_size", "order"}:
        raise ValueError("settings must contain exactly token_size and order")
    size = settings["token_size"]
    order = settings["order"]
    if type(size) is not int or size not in TOKEN_SIZES:
        raise ValueError(f"token_size must be one of {TOKEN_SIZES}")
    if type(order) is not str or order not in ORDERS:
        raise ValueError(f"order must be one of {ORDERS}")
    return {"token_size": size, "order": order}


def program_for(settings: Any) -> str:
    selected = validate_settings(settings)
    program = prototype.racket_program(selected["token_size"], "horizontal")
    if selected["order"] == "ascending":
        return program
    if program.count(_REVERSE_TARGET) != 1:
        raise ValueError("canonical rule changed at the frame-order site")
    return program.replace(_REVERSE_TARGET, _REVERSE_REPLACEMENT, 1)


def axis_intermediate(grid: list[list[int]]) -> dict[str, Any]:
    """Stage A: canonical input-dependent axis, retaining horizontal ties."""
    return prototype.axis_intermediate(grid, "horizontal")


def solve_with_axis(
    grid: list[list[int]], token_size: Any, axis: Any, order: Any
) -> list[list[int]]:
    """Stage B: consume the supplied axis, order frames, and normalize tokens."""
    size = prototype._validate_token_size(token_size)
    if type(axis) is not str or axis not in ("horizontal", "vertical"):
        raise ValueError("axis must be horizontal or vertical")
    if type(order) is not str or order not in ORDERS:
        raise ValueError(f"order must be one of {ORDERS}")
    frames = prototype._frames(grid)
    if not frames:
        return [[0]]
    vertical = axis == "vertical"
    coordinate = "top" if vertical else "left"
    frames = sorted(frames, key=lambda frame: frame[coordinate])
    if order == "descending":
        frames.reverse()
    return prototype._pack(frames, size, vertical)


def solve(grid: list[list[int]], settings: Any) -> list[list[int]]:
    selected = validate_settings(settings)
    state = axis_intermediate(grid)
    return solve_with_axis(
        grid, selected["token_size"], state["axis"], selected["order"]
    )


def _axis_from_objects(objects: list[dict[str, Any]], mode: str) -> str:
    if not objects:
        return "horizontal"
    if mode == "top_left":
        row_values = [obj["top"] for obj in objects]
        col_values = [obj["left"] for obj in objects]
    elif mode == "centers":
        row_values = [obj["top"] + obj["bottom"] for obj in objects]
        col_values = [obj["left"] + obj["right"] for obj in objects]
    elif mode == "extents":
        row_values = [min(obj["top"] for obj in objects), max(obj["bottom"] for obj in objects)]
        col_values = [min(obj["left"] for obj in objects), max(obj["right"] for obj in objects)]
    else:
        raise ValueError(f"unknown axis rival mode: {mode}")
    row_range = max(row_values) - min(row_values)
    col_range = max(col_values) - min(col_values)
    return "vertical" if row_range > col_range else "horizontal"


def _pack_explicit(
    frames: list[dict[str, Any]], token_size: int, axis: str
) -> list[list[int]]:
    return prototype._pack(frames, token_size, axis == "vertical")


def rival_outputs(grid: list[list[int]], settings: Any) -> dict[str, list[list[int]]]:
    """Finite plausible wrong-rule family used by lesson construction/audits."""
    selected = validate_settings(settings)
    size, order = selected["token_size"], selected["order"]
    frames = prototype._frames(grid)
    state = axis_intermediate(grid)
    axis = state["axis"]
    reversed_order = "descending" if order == "ascending" else "ascending"

    row_major = list(frames)
    if order == "descending":
        row_major.reverse()
    color_ascending = sorted(frames, key=lambda frame: frame["color"])
    color_descending = list(reversed(color_ascending))
    size_ascending = sorted(frames, key=lambda frame: len(frame["cells"]))
    if order == "descending":
        size_ascending.reverse()

    return {
        "always_vertical": solve_with_axis(grid, size, "vertical", order),
        "always_horizontal": solve_with_axis(grid, size, "horizontal", order),
        "reverse_order": solve(
            grid, {"token_size": size, "order": reversed_order}
        ),
        "include_solids_axis": solve_with_axis(
            grid,
            size,
            _axis_from_objects(prototype._components(grid), "top_left"),
            order,
        ),
        "center_spread_axis": solve_with_axis(
            grid, size, _axis_from_objects(frames, "centers"), order
        ),
        "extent_spread_axis": solve_with_axis(
            grid, size, _axis_from_objects(frames, "extents"), order
        ),
        "row_major_order": _pack_explicit(row_major, size, axis),
        "color_ascending": _pack_explicit(color_ascending, size, axis),
        "color_descending": _pack_explicit(color_descending, size, axis),
        "component_size_order": _pack_explicit(size_ascending, size, axis),
    }


def minimum_lesson_ambiguities(
    grids: list[list[list[int]]], settings: Any
) -> list[str]:
    """Return tested rivals that fit every visible demonstration grid."""
    selected = validate_settings(settings)
    if type(grids) is not list or not grids:
        raise ValueError("grids must be a nonempty list")
    survivors = None
    for grid in grids:
        expected = solve(grid, selected)
        outputs = rival_outputs(grid, selected)
        matches = {
            name for name in TEACHING_RIVALS if outputs[name] == expected
        }
        survivors = matches if survivors is None else survivors & matches
    return sorted(survivors or ())


def _minimum_pair_safe(grids: list[list[list[int]]]) -> bool:
    return all(not minimum_lesson_ambiguities(grids, settings) for settings in ALL_SETTINGS)


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"), ensure_ascii=False)


def _outputs_distinguish_every_setting(grid: list[list[int]]) -> bool:
    outputs = {
        json.dumps(solve(grid, settings), separators=(",", ":"), ensure_ascii=False)
        for settings in ALL_SETTINGS
    }
    return len(outputs) == len(ALL_SETTINGS)


def _touch_top_left(grid: list[list[int]]) -> list[list[int]]:
    """Translate all content to touch the top and left boundaries."""
    cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not cells:
        return deepcopy(grid)
    dr = min(r for r, _, _ in cells)
    dc = min(c for _, c, _ in cells)
    shifted = [[0] * len(grid[0]) for _ in grid]
    for r, c, value in cells:
        shifted[r - dr][c - dc] = value
    return shifted


def _sample_slot(
    generator,
    *,
    seed: int,
    stream: str,
    index: int,
    role: str,
    role_index: int,
    seen: set[str],
    lesson_prefix: list[list[list[int]]] | None = None,
) -> dict[str, Any]:
    # Stream-specific pair indices keep all demo and query slots stable under
    # independent count changes. Retry only visible collisions or a rare
    # color-palindrome that would fail to teach ascending vs descending order.
    pair_index = index if stream == "demo" else 100 + index
    for attempt in range(64):
        candidate = prototype._candidate(
            generator,
            seed=seed,
            pair_index=pair_index,
            role=role,
            role_index=role_index,
            attempt=attempt,
        )
        grid = candidate["input"]
        if stream == "query" and candidate["controls"]["grid_h"] == 30 and candidate["controls"]["grid_w"] == 30:
            grid = _touch_top_left(grid)
        key = _grid_key(grid)
        if key in seen:
            continue
        errors = generator.self_check(grid)
        if errors:
            raise AssertionError(f"selected generator emitted invalid input: {errors}")
        if prototype._axis_relation(grid) != role:
            raise AssertionError(f"requested {role} but sampled another axis relation")
        if not _outputs_distinguish_every_setting(grid):
            continue
        if lesson_prefix is not None and not _minimum_pair_safe([*lesson_prefix, grid]):
            continue
        seen.add(key)
        return {
            "input": grid,
            "profile": role,
            "controls": deepcopy(candidate["controls"]),
            "generator_seed": candidate["generator_seed"],
            "sample_index": candidate["sample_index"],
        }
    raise RuntimeError(f"could not construct teaching-safe {stream} slot {index}")


def _full_inputs(seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_root = prototype._root()
    generator, _, _ = prototype.load_selected_generator(
        prototype.TASK_ID, root=source_root
    )
    seen: set[str] = set()
    demos = []
    for index, (role, role_index) in enumerate(DEMO_SPECS):
        demos.append(
            _sample_slot(
                generator,
                seed=seed,
                stream="demo",
                index=index,
                role=role,
                role_index=role_index,
                seen=seen,
                lesson_prefix=[row["input"] for row in demos] if index == 1 else None,
            )
        )
    queries = [
        _sample_slot(
            generator,
            seed=seed,
            stream="query",
            index=index,
            role=role,
            role_index=role_index,
            seen=seen,
        )
        for index, (role, role_index) in enumerate(QUERY_SPECS)
    ]
    return demos, queries


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    selected = validate_settings(settings)
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    demo_rows, query_rows = _full_inputs(seed)

    def labeled(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {"input": deepcopy(row["input"]), "output": solve(row["input"], selected)}
            for row in rows
        ]

    train = labeled(demo_rows[:demos])
    test = labeled(query_rows[:queries])
    # Every single sampled pair separates all six declared settings, so every
    # supported 2..6-demo prefix is constructively identifiable.
    survivors = [
        candidate
        for candidate in ALL_SETTINGS
        if all(solve(pair["input"], candidate) == pair["output"] for pair in train)
    ]
    if survivors != [selected]:
        raise RuntimeError(f"demonstrations do not uniquely identify settings: {survivors}")
    return {
        "train": train,
        "test": test,
        "program_solution": program_for(selected),
    }

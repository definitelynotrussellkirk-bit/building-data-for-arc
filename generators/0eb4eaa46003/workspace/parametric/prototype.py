"""Matched-input profile-source family for task 0eb4eaa46003.

The canonical setting derives the target's row profile from the blue anchor and
its column profile from the red anchor.  The alternative swaps those sources.
Every input contains both uniquely matching candidate crops plus anchor-copy and
other same-area decoys; the hidden setting changes labels, never inputs.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any


TASK_ID = "0eb4eaa46003"
FAMILY_VERSION = "1.0.0"
CANONICAL = "blue_rows_red_cols"
SWAPPED = "red_rows_blue_cols"
ALLOWED_PROFILE_SOURCES = (CANONICAL, SWAPPED)
CANONICAL_SHA256 = "bb6e25e7de935b4d6ad8a45e00c560421b23b59c7e436d9a6cb0b41ec6d96d5f"
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
DEMO_PROFILES = (
    (14, 18, 1, 6),
    (16, 20, 1, 7),
    (18, 22, 1, 8),
    (20, 24, 1, 9),
    (22, 26, 1, 10),
    (24, 28, 1, 7),
)
QUERY_PROFILES = (
    (12, 18, 1, 6),
    (18, 22, 1, 7),
    (24, 26, 1, 8),
    (30, 30, 2, 9),
)
CANDIDATE_COLORS = (3, 4, 5, 6, 7, 8, 9)
DECLARED_SHORTCUTS = (
    "copy_blue",
    "copy_red",
    "first_candidate",
    "last_candidate",
    "minimum_color",
    "maximum_color",
    "area_only",
    "row_only_blue",
    "column_only_red",
    "row_only_red",
    "column_only_blue",
    "third_candidate",
    "fourth_candidate",
)


def _load_production_generator():
    path = Path(__file__).resolve().parents[2] / "generator.py"
    body = path.read_bytes()
    name = "_profile_generator_0eb4eaa46003_" + hashlib.sha256(
        str(path).encode() + body
    ).hexdigest()
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module


_GENERATOR = _load_production_generator()


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer; bool is forbidden")
    if not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_counts(demos: Any, queries: Any) -> tuple[int, int]:
    for name, value in (("demos", demos), ("queries", queries)):
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not DEMO_LIMITS[0] <= demos <= DEMO_LIMITS[1]:
        raise ValueError(f"demos must be in {DEMO_LIMITS[0]}..{DEMO_LIMITS[1]}")
    if not QUERY_LIMITS[0] <= queries <= QUERY_LIMITS[1]:
        raise ValueError(f"queries must be in {QUERY_LIMITS[0]}..{QUERY_LIMITS[1]}")
    return demos, queries


def validate_settings(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {"profile_sources"}:
        raise ValueError("settings must contain exactly profile_sources")
    value = settings["profile_sources"]
    if type(value) is not str or value not in ALLOWED_PROFILE_SOURCES:
        raise ValueError(f"profile_sources must be one of {list(ALLOWED_PROFILE_SOURCES)}")
    return value


@lru_cache(maxsize=1)
def canonical_program() -> str:
    raw = Path(__file__).with_name("canonical.rkt").read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != CANONICAL_SHA256:
        raise ValueError(f"canonical.rkt drifted: {digest}")
    return raw.decode("utf-8")


@lru_cache(maxsize=1)
def swapped_program() -> str:
    program = canonical_program()
    old_row = "(equal? (row-profile obj) (row-profile blue))"
    old_col = "(equal? (col-profile obj) (col-profile red))"
    if program.count(old_row) != 1 or program.count(old_col) != 1:
        raise ValueError("canonical profile predicates are not uniquely replaceable")
    return program.replace(old_row, "(equal? (row-profile obj) (row-profile red))").replace(
        old_col, "(equal? (col-profile obj) (col-profile blue))"
    )


def program_for(profile_sources: str) -> str:
    if profile_sources == CANONICAL:
        return canonical_program()
    if profile_sources == SWAPPED:
        return swapped_program()
    raise ValueError(f"unknown profile_sources {profile_sources!r}")


def _stream_rng(seed: int, split: str, index: int, attempt: int = 0) -> random.Random:
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    material = f"{TASK_ID}|{FAMILY_VERSION}|{seed}|{split}|{index}|{attempt}".encode()
    digest = hashlib.sha256(material).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


@lru_cache(maxsize=1)
def _banks():
    _by_size, _peers, profiles = _GENERATOR._shape_catalog()
    shapes = tuple(
        shape
        for shape in sorted(profiles)
        if _shape_dims(shape)[0] <= 4 and _shape_dims(shape)[1] <= 3
    )
    by_profile: dict[tuple[tuple[int, ...], tuple[int, ...]], list] = {}
    by_area: dict[int, list] = {}
    for shape in shapes:
        by_profile.setdefault(profiles[shape], []).append(shape)
        by_area.setdefault(len(shape), []).append(shape)

    cross: dict[int, list] = {area: [] for area in range(4, 11)}
    for canonical in shapes:
        rows_c, cols_c = profiles[canonical]
        for swapped in by_area[len(canonical)]:
            if canonical == swapped:
                continue
            rows_s, cols_s = profiles[swapped]
            if rows_c == rows_s or cols_c == cols_s:
                continue
            blue_options = by_profile.get((rows_c, cols_s), ())
            red_options = by_profile.get((rows_s, cols_c), ())
            found = None
            for blue in blue_options:
                for red in red_options:
                    if len({canonical, swapped, blue, red}) == 4:
                        found = (canonical, swapped, blue, red)
                        break
                if found is not None:
                    break
            if found is not None:
                cross[len(canonical)].append(found)
    if any(not cross[area] for area in range(4, 11)):
        raise RuntimeError("cross-profile bank is incomplete")
    return profiles, {k: tuple(v) for k, v in by_area.items()}, {
        k: tuple(v) for k, v in cross.items()
    }


def _distractors(rng: random.Random, area: int, forbidden: set, forbidden_profiles: set):
    profiles, by_area, _cross = _banks()
    choices = [
        shape
        for shape in by_area[area]
        if shape not in forbidden and profiles[shape] not in forbidden_profiles
    ]
    if len(choices) < 2:
        raise RuntimeError("not enough independent distractor shapes")
    first = rng.choice(choices)
    choices = [shape for shape in choices if shape != first]
    second = rng.choice(choices)
    return first, second


def _scaled(shape: tuple[tuple[int, int], ...], scale: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (row * scale + dr, col * scale + dc)
        for row, col in shape
        for dr in range(scale)
        for dc in range(scale)
    )


def _bands(total: int, count: int) -> list[tuple[int, int]]:
    usable = total - (count - 1)
    if usable < count:
        raise ValueError("grid too small for separated bands")
    return [
        (index + index * usable // count, index + (index + 1) * usable // count)
        for index in range(count)
    ]


def _origin(shape, slot: int, height: int, width: int) -> tuple[int, int]:
    shape_h, shape_w = _shape_dims(shape)
    row_index, col_index = divmod(slot, 4)
    row_start, row_end = _bands(height, 2)[row_index]
    col_start, col_end = _bands(width, 4)[col_index]
    if shape_h > row_end - row_start or shape_w > col_end - col_start:
        raise ValueError("shape does not fit its separated placement band")
    if row_index == 0:
        top = row_start
    else:
        top = row_end - shape_h
    if col_index == 0:
        left = col_start
    elif col_index == 3:
        left = col_end - shape_w
    else:
        left = col_start + (col_end - col_start - shape_w) // 2
    return top, left


def _paint(grid: list[list[int]], shape, color: int, slot: int) -> None:
    top, left = _origin(shape, slot, len(grid), len(grid[0]))
    for row, col in shape:
        if grid[top + row][left + col] != 0:
            raise RuntimeError("placement collision")
        grid[top + row][left + col] = color


def build_input(seed: Any, split: str, index: Any, *, attempt: int = 0) -> list[list[int]]:
    seed = _validate_seed(seed)
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")
    if type(attempt) is not int or attempt < 0:
        raise ValueError("attempt must be a nonnegative exact integer")
    profiles_spec = DEMO_PROFILES if split == "demo" else QUERY_PROFILES
    if split == "query" and index >= len(profiles_spec):
        raise ValueError("query index exceeds supported profile count")
    height, width, scale, area = profiles_spec[index % len(profiles_spec)]
    rng = _stream_rng(seed, split, index, attempt)
    profiles, _by_area, cross = _banks()
    canonical, swapped, blue, red = rng.choice(cross[area])
    forbidden_profiles = {
        profiles[canonical],
        profiles[swapped],
        profiles[blue],
        profiles[red],
    }
    extra_a, extra_b = _distractors(
        rng, area, {canonical, swapped, blue, red}, forbidden_profiles
    )

    candidate_palette = list(rng.sample(CANDIDATE_COLORS, 6))
    ordered_colors = sorted(candidate_palette)
    canonical_color, swapped_color = ordered_colors[2], ordered_colors[3]
    decoy_colors = [c for c in candidate_palette if c not in {canonical_color, swapped_color}]
    rng.shuffle(decoy_colors)

    blue_s = _scaled(blue, scale)
    red_s = _scaled(red, scale)
    canonical_s = _scaled(canonical, scale)
    swapped_s = _scaled(swapped, scale)
    extra_a_s = _scaled(extra_a, scale)
    extra_b_s = _scaled(extra_b, scale)

    # Candidate order is copy-blue, copy-red, then the two true targets, then
    # two unrelated same-area decoys.  Target order alternates by pair index so
    # fixed candidate-rank shortcuts cannot fit the two-demo minimum lesson.
    if index % 2 == 0:
        first_target = (canonical_s, canonical_color)
        second_target = (swapped_s, swapped_color)
    else:
        first_target = (swapped_s, swapped_color)
        second_target = (canonical_s, canonical_color)
    roles = [
        (blue_s, 1),
        (blue_s, decoy_colors[0]),
        (red_s, decoy_colors[1]),
        first_target,
        (red_s, 2),
        second_target,
        (extra_a_s, decoy_colors[2]),
        (extra_b_s, decoy_colors[3]),
    ]

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for slot, (shape, color) in enumerate(roles):
        _paint(grid, shape, color, slot)
    return grid


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = {(row, col)}
            seen.add((row, col))
            stack = [(row, col)]
            while stack:
                r, c = stack.pop()
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        cells.add((rr, cc))
                        stack.append((rr, cc))
            top = min(r for r, _ in cells)
            left = min(c for _, c in cells)
            bottom = max(r for r, _ in cells)
            right = max(c for _, c in cells)
            shape = tuple(sorted((r - top, c - left) for r, c in cells))
            rows = tuple(sum(r == local for r, _ in shape) for local in range(bottom - top + 1))
            cols = tuple(sum(c == local for _, c in shape) for local in range(right - left + 1))
            result.append(
                {
                    "color": color,
                    "origin": (top, left),
                    "shape": shape,
                    "rows": rows,
                    "cols": cols,
                    "height": bottom - top + 1,
                    "width": right - left + 1,
                    "cells": tuple(sorted(cells)),
                }
            )
    return sorted(result, key=lambda item: item["origin"])


def _parts(grid):
    objects = _components(grid)
    blues = [obj for obj in objects if obj["color"] == 1]
    reds = [obj for obj in objects if obj["color"] == 2]
    if len(blues) != 1 or len(reds) != 1:
        raise ValueError("expected exactly one blue and one red anchor")
    candidates = [obj for obj in objects if obj["color"] not in (1, 2)]
    return blues[0], reds[0], candidates


def _crop(obj) -> list[list[int]]:
    if obj is None:
        return [[0]]
    output = [[0 for _ in range(obj["width"])] for _ in range(obj["height"])]
    for row, col in obj["shape"]:
        output[row][col] = 8
    return output


def _selected_object(grid, profile_sources: str):
    blue, red, candidates = _parts(grid)
    if profile_sources == CANONICAL:
        rows, cols = blue["rows"], red["cols"]
    elif profile_sources == SWAPPED:
        rows, cols = red["rows"], blue["cols"]
    else:
        raise ValueError(f"unknown profile_sources {profile_sources!r}")
    matches = [obj for obj in candidates if obj["rows"] == rows and obj["cols"] == cols]
    if len(matches) != 1:
        raise ValueError(f"expected one target for {profile_sources}, found {len(matches)}")
    return matches[0]


def solve(grid, profile_sources: str) -> list[list[int]]:
    return _crop(_selected_object(grid, profile_sources))


def _shortcut_predictions(grid) -> dict[str, list[list[int]]]:
    blue, red, candidates = _parts(grid)

    def first_matching(predicate):
        return next((obj for obj in candidates if predicate(obj)), None)

    predictions = {
        "copy_blue": _crop(blue),
        "copy_red": _crop(red),
        "first_candidate": _crop(candidates[0]),
        "last_candidate": _crop(candidates[-1]),
        "minimum_color": _crop(min(candidates, key=lambda obj: (obj["color"], obj["origin"]))),
        "maximum_color": _crop(max(candidates, key=lambda obj: (obj["color"], tuple(-v for v in obj["origin"]))),),
        "area_only": _crop(max(candidates, key=lambda obj: (len(obj["shape"]), tuple(-v for v in obj["origin"]))),),
        "row_only_blue": _crop(first_matching(lambda obj: obj["rows"] == blue["rows"])),
        "column_only_red": _crop(first_matching(lambda obj: obj["cols"] == red["cols"])),
        "row_only_red": _crop(first_matching(lambda obj: obj["rows"] == red["rows"])),
        "column_only_blue": _crop(first_matching(lambda obj: obj["cols"] == blue["cols"])),
        "third_candidate": _crop(candidates[2]),
        "fourth_candidate": _crop(candidates[3]),
    }
    return predictions


def audit_episode(episode: dict, selected: str) -> dict[str, Any]:
    if selected not in ALLOWED_PROFILE_SOURCES:
        raise ValueError("selected setting is invalid")
    rival = SWAPPED if selected == CANONICAL else CANONICAL
    train = episode["train"]
    tests = episode["test"]
    survivors = []
    for name in DECLARED_SHORTCUTS:
        if all(_shortcut_predictions(pair["input"])[name] == pair["output"] for pair in train):
            survivors.append(name)
    return {
        "opposite_setting_survives": all(
            solve(pair["input"], rival) == pair["output"] for pair in train
        ),
        "query_disagreements": sum(
            solve(pair["input"], rival) != pair["output"] for pair in tests
        ),
        "surviving_declared_shortcuts": survivors,
    }


def input_metrics(grid) -> dict[str, Any]:
    objects = _components(grid)
    height, width = len(grid), len(grid[0])
    sides = set()
    for obj in objects:
        cells = obj["cells"]
        if any(row == 0 for row, _ in cells):
            sides.add("top")
        if any(row == height - 1 for row, _ in cells):
            sides.add("bottom")
        if any(col == 0 for _, col in cells):
            sides.add("left")
        if any(col == width - 1 for _, col in cells):
            sides.add("right")
    return {
        "height": height,
        "width": width,
        "component_count": len(objects),
        "occupied_cells": sum(cell != 0 for row in grid for cell in row),
        "boundary_sides": sorted(sides),
        "max_component_height": max(obj["height"] for obj in objects),
        "max_component_width": max(obj["width"] for obj in objects),
    }


def _pair(seed: int, split: str, index: int, selected: str, seen: set[str]) -> dict:
    for attempt in range(32):
        grid = build_input(seed, split, index, attempt=attempt)
        key = json.dumps(grid, separators=(",", ":"))
        if key not in seen:
            seen.add(key)
            return {"input": grid, "output": solve(grid, selected)}
    raise RuntimeError("could not construct a distinct pair after 32 attempts")


def build_claimed_episode(seed: Any, selected: str, demos: Any, queries: Any) -> dict:
    seed = _validate_seed(seed)
    selected = validate_settings({"profile_sources": selected})
    demos, queries = _validate_counts(demos, queries)
    seen: set[str] = set()
    train = [_pair(seed, "demo", index, selected, seen) for index in range(demos)]
    test = [_pair(seed, "query", index, selected, seen) for index in range(queries)]
    return {"train": train, "test": test, "program_solution": program_for(selected)}


def public_turn(episode: dict, query_index: Any) -> dict:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must select an existing query; bool is forbidden")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }

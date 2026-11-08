"""Parametric rotation-direction family for color-coded template stamping."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "250a48232c34"
DIRECTIONS = ("clockwise", "counterclockwise")
DEFAULT_DIRECTION = "clockwise"
HERE = Path(__file__).resolve().parent
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

TEMPLATES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2)),
    ((0, 1), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)),
)
DEMO_SIZES = ((12, 13), (13, 15), (15, 14), (17, 18), (19, 17), (20, 20))
QUERY_SIZES = ((16, 18), (22, 20), (26, 26), (30, 30))


def _load_base():
    source = HERE.parents[1] / "generator.py"
    name = "_base_250_" + hashlib.sha256(str(source).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError(source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()


def _direction(settings: dict[str, Any]) -> str:
    if type(settings) is not dict or set(settings) != {"rotation_direction"}:
        raise ValueError("settings must contain exactly rotation_direction")
    direction = settings["rotation_direction"]
    if type(direction) is not str or direction not in DIRECTIONS:
        raise ValueError(f"rotation_direction must be one of {DIRECTIONS}")
    return direction


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: dict[str, Any]) -> str:
    direction = _direction(settings)
    filename = "canonical.rkt" if direction == DEFAULT_DIRECTION else "counterclockwise.rkt"
    source = (HERE / "rules" / filename).read_text(encoding="utf-8")
    if not source.strip():
        raise ValueError(f"empty retained rule: {filename}")
    return source


def normalize(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    cells = list(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def rotate(cells: Iterable[tuple[int, int]], turns: int) -> list[tuple[int, int]]:
    cur = normalize(cells)
    for _ in range(turns % 4):
        max_r = max(r for r, _ in cur)
        cur = normalize((c, max_r - r) for r, c in cur)
    return cur


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in DIR4:
                    p = (rr + dr, cc + dc)
                    if 0 <= p[0] < h and 0 <= p[1] < w and p not in seen and grid[p[0]][p[1]] == color:
                        seen.add(p)
                        stack.append(p)
            result.append(sorted(cells))
    return result


def inspect_scene(grid: list[list[int]]) -> dict[str, Any]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be nonempty")
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact ARC colors")
    gray = _components(grid, 5)
    if len(gray) != 1:
        raise ValueError(f"expected one gray template, found {len(gray)}")
    template = normalize(gray[0])
    anchors = sorted(
        [(r, c, grid[r][c]) for r in range(h) for c in range(w) if 1 <= grid[r][c] <= 4],
        key=lambda item: item[2],
    )
    if [color for _r, _c, color in anchors] != [1, 2, 3, 4]:
        raise ValueError("scene must contain one anchor of each color 1..4")
    return {"height": h, "width": w, "template": template, "template_cells": gray[0], "anchors": anchors}


def _rng(seed: int, bank: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|v1|{seed}|{bank}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = list(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _boxes_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int], margin: int = 0) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return not (ar1 + margin <= br0 or br1 + margin <= ar0 or ac1 + margin <= bc0 or bc1 + margin <= ac0)


def _build_scene(seed: int, bank: str, index: int) -> list[list[int]]:
    sizes = DEMO_SIZES if bank == "demo" else QUERY_SIZES
    if not 0 <= index < len(sizes):
        raise ValueError("scene index outside retained bank")
    h, w = sizes[index]
    rng = _rng(seed, bank, index)
    if bank == "query" and index == 3:
        profile_index = 3 + seed % 3
    else:
        profile_index = (seed + index + (0 if bank == "demo" else 2)) % len(TEMPLATES)
    template = list(TEMPLATES[profile_index])
    if rotate(template, 1) == rotate(template, 3):
        raise AssertionError("retained template does not distinguish rotation direction")
    th, tw = _bbox(template)

    # Put the gray source near the center, with seed-dependent one-cell jitter.
    tr = max(4, min(h - th - 4, h // 2 - th // 2 + rng.choice((-1, 0, 1))))
    tc = max(4, min(w - tw - 4, w // 2 - tw // 2 + rng.choice((-1, 0, 1))))
    template_box = (tr, tc, tr + th, tc + tw)

    # Each color is assigned to a different corner; the permutation changes per
    # scene so position cannot stand in for the color/rotation role.
    corners = ("tl", "tr", "bl", "br")
    colors = [1, 2, 3, 4]
    rng.shuffle(colors)
    anchors: list[tuple[int, int, int]] = []
    stamp_boxes: list[tuple[int, int, int, int]] = []
    for corner, color in zip(corners, colors):
        turns = color - 1
        rh, rw = _bbox(rotate(template, turns))
        jitter_r = rng.randint(0, 1)
        jitter_c = rng.randint(0, 1)
        if corner == "tl":
            r, c = jitter_r, jitter_c
        elif corner == "tr":
            r, c = jitter_r, w - rw - jitter_c
        elif corner == "bl":
            r, c = h - rh - jitter_r, jitter_c
        else:
            r, c = h - rh - jitter_r, w - rw - jitter_c
        box = (r, c, r + rh, c + rw)
        if _boxes_overlap(box, template_box, margin=0) or any(_boxes_overlap(box, other, margin=0) for other in stamp_boxes):
            raise AssertionError("retained dimensions do not separate template and stamp regions")
        anchors.append((r, c, color))
        stamp_boxes.append(box)

    grid = [[0 for _ in range(w)] for _ in range(h)]
    for dr, dc in template:
        grid[tr + dr][tc + dc] = 5
    for r, c, color in anchors:
        grid[r][c] = color

    facts = inspect_scene(grid)
    errors = _BASE.self_check(grid, difficulty=None)
    if errors:
        raise AssertionError("constructed scene is outside reviewed base grammar: " + "; ".join(errors))
    # Both direction programs must fit; color-specific footprints are the same
    # dimensions for +/-90 degrees, but verify the exact cells constructively.
    for direction in DIRECTIONS:
        solve(grid, {"rotation_direction": direction})
    return grid


def _turns(color: int, direction: str) -> int:
    return color - 1 if direction == "clockwise" else (1 - color) % 4


def solve(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    direction = _direction(settings)
    facts = inspect_scene(grid)
    out = deepcopy(grid)
    for ar, ac, color in facts["anchors"]:
        cells = rotate(facts["template"], _turns(color, direction))
        for dr, dc in cells:
            rr, cc = ar + dr, ac + dc
            if not (0 <= rr < facts["height"] and 0 <= cc < facts["width"]):
                raise ValueError("rotated stamp does not fit")
            out[rr][cc] = color
    return out


def _pairs(seed: int, settings: dict[str, Any], bank: str, count: int) -> list[dict[str, Any]]:
    return [
        {"input": grid, "output": solve(grid, settings)}
        for grid in (_build_scene(seed, bank, index) for index in range(count))
    ]


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    _direction(settings)
    return {
        "train": _pairs(seed, settings, "demo", demos),
        "test": _pairs(seed, settings, "query", queries),
        "program_solution": program(settings),
    }


def dependency_trace(grid: list[list[int]], settings: dict[str, Any]) -> dict[str, Any]:
    direction = _direction(settings)
    facts = inspect_scene(grid)
    rotated = {
        str(color): {
            "anchor": [r, c],
            "cells": [list(cell) for cell in rotate(facts["template"], _turns(color, direction))],
        }
        for r, c, color in facts["anchors"]
    }
    output = solve(grid, settings)
    return {
        "step_a": "extract_template_and_rotate_for_each_anchor",
        "intermediate": {"normalized_template": [list(cell) for cell in facts["template"]], "rotated_cells_by_color": rotated},
        "step_b": "stamp_each_rotated_template_at_its_anchor",
        "why_b_depends_on_a": "Each stamp's occupied cells are the input template after the direction- and color-dependent rotation; changing those rotated cells changes the colored output support.",
        "output": output,
        "counterfactual_clockwise_output": solve(grid, {"rotation_direction": "clockwise"}),
    }


def _rival_output(grid: list[list[int]], mode: str, fixed_template: list[tuple[int, int]] | None = None) -> list[list[int]]:
    facts = inspect_scene(grid)
    template = facts["template"] if fixed_template is None else fixed_template
    out = deepcopy(grid)
    for ar, ac, color in facts["anchors"]:
        if mode == "always_clockwise":
            turns = color - 1
        elif mode == "always_counterclockwise":
            turns = (1 - color) % 4
        elif mode == "no_rotation":
            turns = 0
        elif mode == "always_half_turn":
            turns = 2
        elif mode == "color_value_turns":
            turns = color % 4
        else:
            raise ValueError(mode)
        for dr, dc in rotate(template, turns):
            rr, cc = ar + dr, ac + dc
            if 0 <= rr < facts["height"] and 0 <= cc < facts["width"]:
                out[rr][cc] = color
    return out


def bounded_audit(*, seeds: Iterable[int] = range(16), demos: int = 2, queries: int = 4) -> dict[str, Any]:
    seeds = list(seeds)
    rivals = (
        "always_clockwise",
        "always_counterclockwise",
        "no_rotation",
        "always_half_turn",
        "color_value_turns",
        "fixed_first_demo_template",
    )
    harmful: list[dict[str, Any]] = []
    for seed in seeds:
        for direction in DIRECTIONS:
            settings = {"rotation_direction": direction}
            episode = generate(seed, settings, demos, queries)
            first_template = inspect_scene(episode["train"][0]["input"])["template"]
            for rival in rivals:
                def predict(pair):
                    if rival == "fixed_first_demo_template":
                        mode = "always_clockwise" if direction == "clockwise" else "always_counterclockwise"
                        return _rival_output(pair["input"], mode, first_template)
                    return _rival_output(pair["input"], rival)
                survives = all(predict(pair) == pair["output"] for pair in episode["train"])
                disagrees = any(predict(pair) != pair["output"] for pair in episode["test"])
                if survives and disagrees:
                    harmful.append({"seed": seed, "settings": settings, "rival": rival})
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "episodes": len(seeds) * len(DIRECTIONS),
        "demos": demos,
        "queries": queries,
        "rivals": list(rivals),
        "harmful_survivors": harmful,
        "limits": "Finite deterministic audit; absence of survivors is not universal uniqueness.",
    }

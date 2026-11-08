"""Boolean-result episodes with an optional post-operation component relay.

``full_result`` is the exact canonical rule. ``mark_largest_component`` first
infers and applies the demonstrated Boolean operator, then recomputes the red
4-connected components in that input-dependent result and recolors the unique
largest component cyan.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "a20ecf84f041"
HERE = Path(__file__).resolve().parent
FINISHES = ("full_result", "mark_largest_component")
POLICIES = (
    "full_result",
    "mark_largest_component",
    "mark_smallest_component",
    "mark_topmost_component",
    "mark_largest_8_connected",
    "mark_all_components",
    "mark_largest_union_intermediate",
    "keep_largest_component",
)
DEMO_SIZES = (5, 6, 3, 4, 7, 8)
QUERY_SIZES = (6, 7, 8, 9)
DEMO_OPS = ("xor", "intersection", "union", "xor", "intersection", "union")
QUERY_OPS = ("intersection", "xor", "union", "xor")


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}; bool is forbidden")
    return value


def _finish(value: Any) -> str:
    if type(value) is not str or value not in FINISHES:
        raise ValueError(f"finish must be one of {FINISHES}")
    return value


def _settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    return _finish(settings["finish"])


def program_for(finish: str) -> str:
    finish = _finish(finish)
    name = "canonical.rkt" if finish == "full_result" else "mark_largest_component.rkt"
    return (HERE / name).read_text()


def counterfactual_program() -> str:
    return (HERE / "wrong_union_intermediate.rkt").read_text()


def program(settings: dict[str, Any]) -> str:
    return program_for(_settings(settings))


def _rng(seed: int, role: str, index: int) -> random.Random:
    payload = f"a20-parametric-v1:{seed}:{role}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _grid(h: int, w: int, fill: int = 0) -> list[list[int]]:
    return [[fill for _ in range(w)] for _ in range(h)]


def _apply_states(states: list[list[int]], op: str) -> list[list[int]]:
    out = _grid(len(states), len(states[0]))
    for r, row in enumerate(states):
        for c, state in enumerate(row):
            a, b = bool(state & 1), bool(state & 2)
            keep = a or b if op == "union" else a and b if op == "intersection" else a != b
            out[r][c] = 2 if keep else 0
    return out


def _operands(states: list[list[int]], color: int) -> tuple[list[list[int]], list[list[int]]]:
    left = _grid(len(states), len(states[0]))
    right = _grid(len(states), len(states[0]))
    for r, row in enumerate(states):
        for c, state in enumerate(row):
            if state & 1:
                left[r][c] = color
            if state & 2:
                right[r][c] = color
    return left, right


def _components(panel: list[list[int]], connectivity: int = 4) -> list[dict[str, Any]]:
    h, w = len(panel), len(panel[0])
    deltas = ((-1, 0), (0, -1), (1, 0), (0, 1))
    if connectivity == 8:
        deltas = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0))
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            if panel[r][c] == 0 or (r, c) in seen:
                continue
            color = panel[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in deltas:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and panel[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            result.append({
                "cells": cells,
                "size": len(cells),
                "bbox": (min(x for x, _ in cells), min(y for _, y in cells),
                         max(x for x, _ in cells), max(y for _, y in cells)),
            })
    return result


def _winner(components: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    if not components:
        raise ValueError("result panel must contain a component")
    if mode == "largest":
        return max(components, key=lambda item: item["size"])
    if mode == "smallest":
        return min(components, key=lambda item: item["size"])
    if mode == "topmost":
        return min(components, key=lambda item: item["bbox"])
    raise ValueError(mode)


def _parse(grid: Any) -> dict[str, Any]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be nonempty")
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30 or any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular within 30x30")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid cells must be exact ARC integers")
    full_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    full_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(full_rows) != 1 or len(full_cols) != 2:
        raise ValueError("expected one divider row and two divider columns")
    p, c1, c2 = full_rows[0], *full_cols
    if h != 2 * p + 1 or w != 3 * p + 2 or c1 != p or c2 != 2 * p + 1 or not 3 <= p <= 9:
        raise ValueError("invalid 2x3 panel geometry")
    def sub(top: int, left: int) -> list[list[int]]:
        return [row[left:left+p] for row in grid[top:top+p]]
    panels = (
        sub(0, 0), sub(0, p + 1), sub(0, 2 * p + 2),
        sub(p + 1, 0), sub(p + 1, p + 1), sub(p + 1, 2 * p + 2),
    )
    a, b, c, d, e, blank = panels
    candidates = [op for op in ("union", "intersection", "xor") if _apply_panels(a, b, op) == c]
    if not candidates:
        raise ValueError("top demonstration identifies no operation")
    answers = [_apply_panels(d, e, op) for op in candidates]
    if any(answer != answers[0] for answer in answers[1:]):
        raise ValueError("top demonstration is ambiguous for the query")
    if any(v != 0 for row in blank for v in row):
        raise ValueError("query answer panel must be blank")
    return {"panel_size": p, "divider_row": p, "divider_cols": (c1, c2),
            "panels": panels, "op": candidates[0], "matching_ops": candidates,
            "answer": answers[0]}


def _apply_panels(left: list[list[int]], right: list[list[int]], op: str) -> list[list[int]]:
    states = [[int(left[r][c] != 0) + 2 * int(right[r][c] != 0)
               for c in range(len(left[0]))] for r in range(len(left))]
    return _apply_states(states, op)


def _paste(grid: list[list[int]], panel: list[list[int]], p: int) -> list[list[int]]:
    out = copy.deepcopy(grid)
    top, left = p + 1, 2 * p + 2
    for r, row in enumerate(panel):
        for c, value in enumerate(row):
            if value != 0:
                out[top + r][left + c] = value
    return out


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    parsed = _parse(grid)
    answer = parsed["answer"]
    components4 = _components(answer, 4)
    components8 = _components(answer, 8)
    return {**parsed, "components4": components4, "components8": components8,
            "largest4": _winner(components4, "largest") if components4 else None,
            "largest8": _winner(components8, "largest") if components8 else None}


def solve_policy(grid: list[list[int]], policy: str) -> list[list[int]]:
    parsed = _parse(grid)
    p = parsed["panel_size"]
    answer = copy.deepcopy(parsed["answer"])
    if policy == "full_result":
        panel = answer
    elif policy == "mark_largest_union_intermediate":
        d, e = parsed["panels"][3], parsed["panels"][4]
        panel = _apply_panels(d, e, "union")
        parts = _components(panel, 4)
        winner = _winner(parts, "largest")
        for r, c in winner["cells"]:
            panel[r][c] = 8
    else:
        parts = _components(answer, 8 if policy == "mark_largest_8_connected" else 4)
        if policy == "mark_all_components":
            panel = [[8 if value != 0 else 0 for value in row] for row in answer]
        elif policy == "keep_largest_component":
            winner = _winner(parts, "largest")
            keep = set(winner["cells"])
            panel = [[2 if (r, c) in keep else 0 for c in range(p)] for r in range(p)]
        else:
            mode = {"mark_largest_component": "largest", "mark_smallest_component": "smallest",
                    "mark_topmost_component": "topmost", "mark_largest_8_connected": "largest"}.get(policy)
            if mode is None:
                raise ValueError(f"unknown policy {policy!r}")
            winner = _winner(parts, mode)
            panel = copy.deepcopy(answer)
            for r, c in winner["cells"]:
                panel[r][c] = 8
    return _paste(grid, panel, p)


def solve(grid: list[list[int]], finish: str) -> list[list[int]]:
    return solve_policy(grid, _finish(finish))


def _random_states(rng: random.Random, p: int) -> list[list[int]]:
    states = [0, 1, 2, 3] + [rng.randrange(4) for _ in range(p * p - 4)]
    rng.shuffle(states)
    return [states[r*p:(r+1)*p] for r in range(p)]


def _strong(states: list[list[int]], op: str) -> bool:
    answer = _apply_states(states, op)
    parts4 = _components(answer, 4)
    if len(parts4) < 3:
        return False
    sizes = [x["size"] for x in parts4]
    if sizes.count(max(sizes)) != 1 or sizes.count(min(sizes)) != 1:
        return False
    largest = _winner(parts4, "largest")
    if largest is _winner(parts4, "smallest") or largest is _winner(parts4, "topmost"):
        return False
    if set(largest["cells"]) == set(_winner(_components(answer, 8), "largest")["cells"]):
        return False
    union = _apply_states(states, "union")
    if set(largest["cells"]) == set(_winner(_components(union, 4), "largest")["cells"]):
        return False
    panels = []
    dummy = _assemble_from_states(states, op, 1, 3)
    for policy in POLICIES:
        # Compare only the query answer panel; full-grid policy evaluation follows below.
        panels.append(json.dumps(_query_panel(solve_policy(dummy, policy)), separators=(",", ":")))
    return len(panels) == len(set(panels))


def _query_panel(grid: list[list[int]]) -> list[list[int]]:
    p = (len(grid) - 1) // 2
    return [row[2*p+2:3*p+2] for row in grid[p+1:2*p+1]]


def _search_states(rng: random.Random, p: int, op: str, strong: bool) -> list[list[int]]:
    for _ in range(10000):
        states = _random_states(rng, p)
        answer = _apply_states(states, op)
        parts = _components(answer, 4)
        sizes = [x["size"] for x in parts]
        if len(parts) < 2 or sizes.count(max(sizes)) != 1:
            continue
        if strong and not _strong(states, op):
            continue
        return states
    raise RuntimeError(f"unable to construct component-rich {p}x{p} {op} scene")


def _assemble(p: int, panels: Iterable[list[list[int]]]) -> list[list[int]]:
    out = _grid(2 * p + 1, 3 * p + 2)
    for c in range(len(out[0])):
        out[p][c] = 9
    for r in range(len(out)):
        out[r][p] = 9
        out[r][2 * p + 1] = 9
    placements = ((0, 0), (0, p + 1), (0, 2*p + 2), (p + 1, 0), (p + 1, p + 1))
    for panel, (top, left) in zip(panels, placements, strict=True):
        for r in range(p):
            out[top+r][left:left+p] = panel[r][:]
    return out


def _assemble_from_states(query_states: list[list[int]], op: str, top_color: int, bottom_color: int,
                          top_states: list[list[int]] | None = None) -> list[list[int]]:
    p = len(query_states)
    if top_states is None:
        # Deterministic complete truth table, then repeated states.
        flat = ([0, 1, 2, 3] * ((p*p + 3)//4))[:p*p]
        top_states = [flat[r*p:(r+1)*p] for r in range(p)]
    a, b = _operands(top_states, top_color)
    c = _apply_states(top_states, op)
    d, e = _operands(query_states, bottom_color)
    return _assemble(p, (a, b, c, d, e))


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _exact_int(seed, 0, 2**63 - 1, "seed")
    if split == "train":
        if type(index) is not int or not 0 <= index < len(DEMO_SIZES):
            raise ValueError("demo index out of range")
        p, op = DEMO_SIZES[index], DEMO_OPS[index]
    elif split == "test":
        if type(index) is not int or not 0 <= index < len(QUERY_SIZES):
            raise ValueError("query index out of range")
        p, op = QUERY_SIZES[index], QUERY_OPS[index]
    else:
        raise ValueError("split must be train or test")
    rng = _rng(seed, split, index)
    top_states = _random_states(rng, p)
    query_states = _search_states(rng, p, op, strong=(split == "train" and index < 2))
    colors = [1, 3, 4, 5, 6, 7]
    rng.shuffle(colors)
    top_color = colors[0]
    bottom_color = colors[0] if (seed + index + (0 if split == "train" else 1)) % 2 == 0 else colors[1]
    grid = _assemble_from_states(query_states, op, top_color, bottom_color, top_states)
    parsed = _parse(grid)
    if parsed["matching_ops"] != [op]:
        raise RuntimeError("top truth table failed to identify operation uniquely")
    return grid


def generate_episode(seed: int, finish: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _exact_int(seed, 0, 2**63 - 1, "seed")
    finish = _finish(finish)
    demos = _exact_int(demos, 2, 6, "demos")
    queries = _exact_int(queries, 1, 4, "queries")
    train = [{"input": sample_input(seed, "train", i), "output": None} for i in range(demos)]
    test = [{"input": sample_input(seed, "test", i), "output": None} for i in range(queries)]
    for pair in train + test:
        pair["output"] = solve(pair["input"], finish)
    return {"train": train, "test": test, "program_solution": program_for(finish)}


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    return generate_episode(seed, _settings(settings), demos=demos, queries=queries)


def teaching_survivors(demos: list[dict[str, Any]]) -> list[str]:
    survivors = []
    for policy in POLICIES:
        if all(solve_policy(pair["input"], policy) == pair["output"] for pair in demos):
            survivors.append(policy)
    return survivors

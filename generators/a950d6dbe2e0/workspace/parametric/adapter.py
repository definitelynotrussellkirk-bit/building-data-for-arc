"""Native parametric adapter for ``a950d6dbe2e0``.

``full_orbit`` is the byte-exact canonical four-way reflection.  The nearby
``largest_after_lateral`` setting first mirrors the upper-left source across the
vertical midline, recomputes same-color four-connected components in that
intermediate, and mirrors only the largest resulting component across the
horizontal midline.  Constructed scenes make the first pass merge a smaller
source object into the new largest component, so selecting before that pass
changes the final output.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "a950d6dbe2e0"
HERE = Path(__file__).resolve().parent
MODES = ("full_orbit", "largest_after_lateral")
HYPOTHESES = MODES + (
    "lateral_only",
    "largest_before_lateral",
    "smallest_after_lateral",
    "first_after_lateral",
    "last_after_lateral",
    "all_largest_color_after_lateral",
    "identity",
)

# (height, width, bridge source size, pre-pass decoy size, extra component sizes)
# Extra 0 repeats the bridge color so a color-wide shortcut is distinguishable.
_DEMO_PROFILES = (
    (10, 12, 3, 4, (1, 2)),
    (12, 14, 4, 6, (2, 3)),
    (14, 16, 5, 7, (3, 4)),
    (16, 18, 6, 9, (3, 5, 2)),
    (20, 22, 7, 10, (4, 6, 3)),
    (24, 26, 8, 12, (5, 7, 4)),
)
_QUERY_PROFILES = (
    (14, 18, 4, 6, (2, 4)),
    (20, 24, 6, 9, (4, 6, 3)),
    (26, 28, 8, 12, (5, 7, 4)),
    (30, 30, 10, 15, (6, 7, 5)),
)


def _integer(value: object, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(value: object) -> str:
    if type(value) is not str or value not in MODES:
        raise ValueError(f"mode must be one of {MODES!r}")
    return value


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"mode"}:
        raise ValueError("settings must contain exactly the mode key")
    return {"mode": _mode(value["mode"])}


def _copy(value: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in value]


def grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return value


@lru_cache(maxsize=1)
def canonical_program() -> str:
    return (HERE / "canonical.rkt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def alternative_program() -> str:
    return (HERE / "largest_after_lateral.rkt").read_text(encoding="utf-8")


def program(settings: object) -> str:
    selected = _settings(settings)["mode"]
    return canonical_program() if selected == "full_orbit" else alternative_program()


def _component_dict(color: int, cells: Iterable[tuple[int, int]]) -> dict[str, object]:
    ordered = sorted(cells)
    rows = [r for r, _ in ordered]
    cols = [c for _, c in ordered]
    return {
        "color": color,
        "cells": [list(cell) for cell in ordered],
        "size": len(ordered),
        "bbox": [min(rows), min(cols), max(rows), max(cols)],
    }


def components(value: object) -> list[dict[str, object]]:
    source = grid(value)
    h, w = len(source), len(source[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, object]] = []
    for r in range(h):
        for c in range(w):
            if source[r][c] == 0 or (r, c) in seen:
                continue
            color = source[r][c]
            queue = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.pop(0)
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and source[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(_component_dict(color, cells))
    return result


def _pick_max(objects: list[dict[str, object]]) -> dict[str, object]:
    if not objects:
        raise ValueError("at least one nonzero component is required")
    # Python max, like the Racket pick-max helper, retains the earliest tie.
    return max(objects, key=lambda item: int(item["size"]))


def _pick_min(objects: list[dict[str, object]]) -> dict[str, object]:
    if not objects:
        raise ValueError("at least one nonzero component is required")
    return min(objects, key=lambda item: int(item["size"]))


def observe(value: object) -> dict[str, object]:
    source = grid(value)
    h, w = len(source), len(source[0])
    if h < 8 or w < 8 or h % 2 or w % 2:
        raise ValueError("parametric grammar requires even dimensions 8..30")
    midr, midc = h // 2, w // 2
    occupied = [(r, c, cell) for r, row in enumerate(source) for c, cell in enumerate(row) if cell]
    if not occupied:
        raise ValueError("source motif must be nonempty")
    if any(r >= midr or c >= midc for r, c, _ in occupied):
        raise ValueError("all source cells must lie in the upper-left quadrant")
    colors = {cell for _, _, cell in occupied}
    if len(colors) < 2:
        raise ValueError("source motif must use at least two colors")
    before = components(source)
    if len(before) < 2:
        raise ValueError("source motif must contain multiple components")
    lateral = _lateral_pass_unchecked(source)
    after = components(lateral)
    return {
        "height": h,
        "width": w,
        "source_cells": len(occupied),
        "colors": sorted(colors),
        "components_before": len(before),
        "components_after": len(after),
        "largest_before": _pick_max(before),
        "largest_after": _pick_max(after),
        "largest_selection_changed": _pick_max(before)["cells"] != _pick_max(after)["cells"],
    }


def _lateral_pass_unchecked(source: list[list[int]]) -> list[list[int]]:
    h, w = len(source), len(source[0])
    out = _copy(source)
    for r in range(h // 2):
        for c in range(w // 2):
            value = source[r][c]
            if value:
                out[r][w - 1 - c] = value
    return out


def lateral_pass(value: object) -> list[list[int]]:
    source = _copy(grid(value))
    observe(source)
    return _lateral_pass_unchecked(source)


def _reflect_component_down(
    top: list[list[int]], selected_cells: Iterable[tuple[int, int] | list[int]]
) -> list[list[int]]:
    h = len(top)
    out = _copy(top)
    for raw in selected_cells:
        r, c = int(raw[0]), int(raw[1])
        out[h - 1 - r][c] = top[r][c]
    return out


def _full_orbit(source: list[list[int]]) -> list[list[int]]:
    h, w = len(source), len(source[0])
    out = _copy(source)
    for r in range(h // 2):
        for c in range(w // 2):
            value = source[r][c]
            if value:
                out[r][c] = value
                out[r][w - 1 - c] = value
                out[h - 1 - r][c] = value
                out[h - 1 - r][w - 1 - c] = value
    return out


def _selected_after(source: list[list[int]], which: str) -> list[list[int]]:
    top = _lateral_pass_unchecked(source)
    objects = components(top)
    if which == "largest":
        selected = _pick_max(objects)
    elif which == "smallest":
        selected = _pick_min(objects)
    elif which == "first":
        selected = objects[0]
    elif which == "last":
        selected = objects[-1]
    else:
        raise ValueError(f"unknown selection {which!r}")
    return _reflect_component_down(top, selected["cells"])


def _largest_before(source: list[list[int]]) -> list[list[int]]:
    top = _lateral_pass_unchecked(source)
    selected = _pick_max(components(source))
    w = len(source[0])
    carried = [tuple(cell) for cell in selected["cells"]]
    carried += [(r, w - 1 - c) for r, c in carried]
    return _reflect_component_down(top, carried)


def _all_largest_color(source: list[list[int]]) -> list[list[int]]:
    top = _lateral_pass_unchecked(source)
    selected = _pick_max(components(top))
    color = int(selected["color"])
    cells = [(r, c) for r, row in enumerate(top) for c, value in enumerate(row) if value == color]
    return _reflect_component_down(top, cells)


def transform(value: object, mode: object) -> list[list[int]]:
    selected = _mode(mode)
    source = _copy(grid(value))
    observe(source)
    if selected == "full_orbit":
        return _full_orbit(source)
    return _selected_after(source, "largest")


def _predict(value: list[list[int]], hypothesis: str) -> list[list[int]]:
    source = _copy(grid(value))
    observe(source)
    if hypothesis == "full_orbit":
        return _full_orbit(source)
    if hypothesis == "largest_after_lateral":
        return _selected_after(source, "largest")
    if hypothesis == "lateral_only":
        return _lateral_pass_unchecked(source)
    if hypothesis == "largest_before_lateral":
        return _largest_before(source)
    if hypothesis == "smallest_after_lateral":
        return _selected_after(source, "smallest")
    if hypothesis == "first_after_lateral":
        return _selected_after(source, "first")
    if hypothesis == "last_after_lateral":
        return _selected_after(source, "last")
    if hypothesis == "all_largest_color_after_lateral":
        return _all_largest_color(source)
    if hypothesis == "identity":
        return source
    raise ValueError(f"unknown declared hypothesis {hypothesis!r}")


def explain_dependency(value: object) -> dict[str, object]:
    source = _copy(grid(value))
    info = observe(source)
    top = _lateral_pass_unchecked(source)
    return {
        "step_a": "reflect every source cell across the vertical full-grid midline",
        "intermediate": top,
        "largest_before": info["largest_before"],
        "largest_after": info["largest_after"],
        "step_b": "reflect only the largest same-color component in the intermediate across the horizontal midline",
        "final": _selected_after(source, "largest"),
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"a950d6dbe2e0-parametric-input-v1:{seed}:{split}:{index}".encode()
    return random.Random(hashlib.sha256(payload).digest())


def _snake(size: int, width: int, reverse_rows: bool) -> set[tuple[int, int]]:
    if size < 1 or width < 1:
        raise ValueError("shape size and width must be positive")
    cells: list[tuple[int, int]] = []
    for r in range(math.ceil(size / width)):
        columns = list(range(width))
        if bool(r % 2) ^ reverse_rows:
            columns.reverse()
        for c in columns:
            cells.append((r, c))
            if len(cells) == size:
                return set(cells)
    raise AssertionError("snake construction did not reach requested size")


def _translate(shape: set[tuple[int, int]], top: int, left: int) -> set[tuple[int, int]]:
    return {(top + r, left + c) for r, c in shape}


def _neighbors(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0))
        if (r + dr, c + dc) not in cells
    }


def _place_extra(
    occupied: set[tuple[int, int]],
    *,
    midr: int,
    midc: int,
    size: int,
    rng: random.Random,
    prefer: str,
) -> set[tuple[int, int]]:
    widths = list(range(1, min(4, size, max(1, midc - 2)) + 1))
    rng.shuffle(widths)
    candidates: list[tuple[tuple[int, int, int], set[tuple[int, int]]]] = []
    for width in widths:
        shape = _snake(size, width, bool(rng.randrange(2)))
        shape_h = max(r for r, _ in shape) + 1
        shape_w = max(c for _, c in shape) + 1
        for top in range(midr - shape_h + 1):
            for left in range(max(0, midc - 1 - shape_w) + 1):
                cells = _translate(shape, top, left)
                if cells & occupied or _neighbors(cells) & occupied:
                    continue
                if prefer == "bottom_left":
                    score = (-top, left, shape_w)
                elif prefer == "bottom_right":
                    score = (-top, -left, shape_w)
                else:
                    score = (abs(top - midr // 2), abs(left - midc // 2), shape_w)
                candidates.append((score, cells))
    if not candidates:
        raise ValueError(f"profile cannot place separated extra component of size {size}")
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    h, w, bridge_size, decoy_size, extras = profiles[index]
    midr, midc = h // 2, w // 2
    rng = _rng(seed, split, index)
    palette = rng.sample(list(range(1, 10)), 4)

    bridge_width_options = [width for width in (2, 3, 4) if width <= bridge_size and width <= midc - 3]
    bridge_width = rng.choice(bridge_width_options or [2])
    bridge_shape = _snake(bridge_size, bridge_width, bool(rng.randrange(2)))
    bridge_h = max(r for r, _ in bridge_shape) + 1
    bridge_top = 0 if (split == "query" and index == 3) else rng.randrange(0, min(2, midr - bridge_h) + 1)
    bridge = _translate(bridge_shape, bridge_top, midc - bridge_width)

    max_decoy_width = max(2, midc - bridge_width - 1)
    decoy_widths = [width for width in (2, 3, 4) if width <= decoy_size and width <= max_decoy_width]
    decoy_width = rng.choice(decoy_widths or [2])
    decoy_shape = _snake(decoy_size, decoy_width, bool(rng.randrange(2)))
    decoy_h = max(r for r, _ in decoy_shape) + 1
    # Keep the away-from-axis decoy first in row-major order.  This makes the
    # minimum two-demo lesson reject a plausible "reflect the first component"
    # shortcut for every seed, rather than relying on a lucky vertical draw.
    decoy_top = 0
    decoy = _translate(decoy_shape, decoy_top, 0)

    if bridge & decoy or _neighbors(bridge) & decoy:
        raise ValueError("profile bridge and decoy are not separated")

    components_spec: list[tuple[set[tuple[int, int]], int]] = [
        (bridge, palette[0]),
        (decoy, palette[1]),
    ]
    occupied = set(bridge) | set(decoy)
    preferences = ("bottom_left", "bottom_right", "middle")
    for extra_index, size in enumerate(extras):
        cells = _place_extra(
            occupied,
            midr=midr,
            midc=midc,
            size=size,
            rng=rng,
            prefer=preferences[min(extra_index, len(preferences) - 1)],
        )
        color = palette[0] if extra_index == 0 else palette[min(extra_index + 1, 3)]
        components_spec.append((cells, color))
        occupied |= cells

    out = [[0] * w for _ in range(h)]
    for cells, color in components_spec:
        for r, c in cells:
            out[r][c] = color

    info = observe(out)
    if int(info["largest_before"]["size"]) != decoy_size:
        raise AssertionError("decoy must be uniquely largest before the lateral pass")
    if int(info["largest_after"]["size"]) != 2 * bridge_size:
        raise AssertionError("bridge must become uniquely largest after the lateral pass")
    if int(info["largest_before"]["color"]) != palette[1]:
        raise AssertionError("wrong pre-pass component selected")
    if int(info["largest_after"]["color"]) != palette[0]:
        raise AssertionError("wrong post-pass component selected")
    expected_cells = bridge_size + decoy_size + sum(extras)
    if int(info["source_cells"]) != expected_cells:
        raise AssertionError("constructed source cell count changed")
    return out


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, object]:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    selected = _settings(settings)
    demos = _integer(demos, "demos", 2, 6)
    queries = _integer(queries, "queries", 1, 4)
    mode = selected["mode"]

    demo_inputs = [_scene(seed, "demo", index) for index in range(6)]
    query_inputs = [_scene(seed, "query", index) for index in range(4)]
    train = [{"input": value, "output": transform(value, mode)} for value in demo_inputs[:demos]]
    test = [{"input": value, "output": transform(value, mode)} for value in query_inputs[:queries]]
    keys = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(keys) != len(set(keys)):
        raise ValueError("all demonstration and query inputs must be distinct")
    episode = {"train": train, "test": test, "program_solution": program(selected)}
    if certificate(train, [pair["input"] for pair in test])["survivors"] != [mode]:
        raise ValueError("constructed demonstrations do not identify the chosen setting")
    return episode


def certificate(train: object, query_inputs: object) -> dict[str, object]:
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("certificate requires 2..6 demonstrations")
    if type(query_inputs) is not list or not 1 <= len(query_inputs) <= 4:
        raise ValueError("certificate requires 1..4 query inputs")
    normalized_train: list[dict[str, list[list[int]]]] = []
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("demonstrations need input and output")
        source = _copy(grid(pair["input"]))
        output = _copy(grid(pair["output"]))
        observe(source)
        normalized_train.append({"input": source, "output": output})
    normalized_queries = [_copy(grid(value)) for value in query_inputs]
    for value in normalized_queries:
        observe(value)
    survivors = [
        name
        for name in HYPOTHESES
        if all(_predict(pair["input"], name) == pair["output"] for pair in normalized_train)
    ]
    selected = survivors[0] if len(survivors) == 1 and survivors[0] in MODES else None
    disagreements: list[str] = []
    if selected:
        selected_outputs = [_predict(value, selected) for value in normalized_queries]
        for name in HYPOTHESES:
            if name == selected:
                continue
            if any(_predict(value, name) != expected for value, expected in zip(normalized_queries, selected_outputs)):
                disagreements.append(name)
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demonstrations": len(normalized_train),
        "queries": len(normalized_queries),
        "query_disagreements": disagreements,
        "predicted_query_sha256": [
            hashlib.sha256(json.dumps(_predict(value, selected), separators=(",", ":")).encode()).hexdigest()
            for value in normalized_queries
        ] if selected else [],
        "scope": "Finite declared rivals checked from demonstrations only; not a proof of universal rule uniqueness.",
    }

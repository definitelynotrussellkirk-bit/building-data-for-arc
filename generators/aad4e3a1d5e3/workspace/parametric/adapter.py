"""Native parametric adapter for ``aad4e3a1d5e3``.

``complete_orbit`` is the exact canonical rule: reflect the source motif across
one guide, then reflect the complete intermediate across the other guide.
``chain_only`` preserves that first pass but lets the second pass consume only
the cells created by the first pass, producing a three-quadrant chain.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Iterable

from reviewer_support import canonical_path, find_root

TASK_ID = "aad4e3a1d5e3"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
MODES = ("complete_orbit", "chain_only")
HYPOTHESES = MODES + (
    "vertical_only",
    "horizontal_only",
    "diagonal_only",
    "identity",
    "horizontal_chain_only",
    "require_unbroken_vertical_guide",
)

# Profiles are fixed structural roles. Seeded randomness chooses exact colors,
# orientation-preserving motif micro-shapes and small axis shifts where lawful.
_DEMO_PROFILES = (
    (11, 13, 5, 6, "top_left", "vertical", 6, "core"),
    (12, 14, 6, 7, "bottom_right", "horizontal", 7, "core"),
    (10, 12, 4, 5, "top_right", "vertical", 8, "core"),
    (14, 16, 7, 8, "bottom_left", "horizontal", 10, "split"),
    (18, 20, 8, 9, "top_left", "vertical", 12, "split"),
    (24, 24, 12, 11, "bottom_right", "horizontal", 14, "split"),
)
_QUERY_PROFILES = (
    (13, 15, 6, 7, "top_right", "horizontal", 9, "core"),
    (20, 18, 10, 9, "bottom_left", "vertical", 12, "split"),
    (26, 28, 12, 14, "top_left", "horizontal", 15, "split"),
    (30, 30, 14, 15, "bottom_right", "vertical", 18, "boundary"),
)
_ALLOWED_MOTIF_COLORS = (1, 2, 3, 4, 7, 8, 9)


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


def _copy(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


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
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    if len(programs) != 1:
        raise ValueError("require one exact canonical authority")
    return programs.pop()


def program(settings: object) -> str:
    mode = _settings(settings)["mode"]
    return canonical_program() if mode == "complete_orbit" else (HERE / "chain_only.rkt").read_text(encoding="utf-8")


def _guide_axes(value: list[list[int]]) -> tuple[int, int]:
    h, w = len(value), len(value[0])
    rows = [
        r
        for r, row in enumerate(value)
        if all(cell in (5, 6) for cell in row) and sum(cell == 6 for cell in row) >= w - 1
    ]
    cols = [
        c
        for c in range(w)
        if all(value[r][c] in (5, 6) for r in range(h))
        and sum(value[r][c] == 5 for r in range(h)) >= h - 1
    ]
    if len(rows) != 1 or len(cols) != 1:
        raise ValueError(f"expected one near-full 6-row and one near-full 5-column, found {len(rows)} and {len(cols)}")
    return rows[0], cols[0]


def _interesting(value: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, cell)
        for r, row in enumerate(value)
        for c, cell in enumerate(row)
        if cell not in (0, 5, 6)
    ]


def observe(value: object) -> dict[str, object]:
    value = grid(value)
    h, w = len(value), len(value[0])
    if not 10 <= h <= 30 or not 10 <= w <= 30:
        raise ValueError("parametric grammar requires dimensions 10..30")
    row_axis, col_axis = _guide_axes(value)
    intersection = value[row_axis][col_axis]
    if intersection not in (5, 6):
        raise ValueError("guide intersection must be 5 or 6")
    if any(value[row_axis][c] != 6 for c in range(w) if c != col_axis):
        raise ValueError("horizontal guide must be color 6 outside the intersection")
    if any(value[r][col_axis] != 5 for r in range(h) if r != row_axis):
        raise ValueError("vertical guide must be color 5 outside the intersection")
    if any(
        cell in (5, 6) and r != row_axis and c != col_axis
        for r, row in enumerate(value)
        for c, cell in enumerate(row)
    ):
        raise ValueError("guide colors may not appear away from the two guides")
    motif = _interesting(value)
    if not 6 <= len(motif) <= 20:
        raise ValueError("motif must contain 6..20 cells")
    colors = {cell for _, _, cell in motif}
    if len(colors) != 2:
        raise ValueError("motif must use exactly two colors")
    row_sides = {-1 if r < row_axis else 1 if r > row_axis else 0 for r, _, _ in motif}
    col_sides = {-1 if c < col_axis else 1 if c > col_axis else 0 for _, c, _ in motif}
    if len(row_sides) != 1 or len(col_sides) != 1 or 0 in row_sides or 0 in col_sides:
        raise ValueError("motif must lie wholly in one guide-defined quadrant")
    for r, c, _ in motif:
        positions = (
            (r, 2 * col_axis - c),
            (2 * row_axis - r, c),
            (2 * row_axis - r, 2 * col_axis - c),
        )
        if any(not (0 <= rr < h and 0 <= cc < w) for rr, cc in positions):
            raise ValueError("all reflected positions must remain in bounds")
        if any(value[rr][cc] != 0 for rr, cc in positions):
            raise ValueError("reflected positions must start empty")
    return {
        "height": h,
        "width": w,
        "row_axis": row_axis,
        "col_axis": col_axis,
        "intersection_owner": "vertical" if intersection == 5 else "horizontal",
        "source_quadrant": ("top" if next(iter(row_sides)) < 0 else "bottom")
        + "_"
        + ("left" if next(iter(col_sides)) < 0 else "right"),
        "motif_cells": len(motif),
        "motif_colors": sorted(colors),
    }


def _mirror_cells(
    out: list[list[int]],
    cells: Iterable[tuple[int, int, int]],
    *,
    axis: str,
    position: int,
) -> list[list[int]]:
    result = _copy(out)
    for r, c, cell in cells:
        rr, cc = (r, 2 * position - c) if axis == "vertical" else (2 * position - r, c)
        result[rr][cc] = cell
    return result


def _vertical_pass(value: list[list[int]]) -> list[list[int]]:
    _, col_axis = _guide_axes(value)
    return _mirror_cells(value, _interesting(value), axis="vertical", position=col_axis)


def _horizontal_pass(value: list[list[int]], cells: Iterable[tuple[int, int, int]]) -> list[list[int]]:
    row_axis, _ = _guide_axes(value)
    return _mirror_cells(value, cells, axis="horizontal", position=row_axis)


def explain_chain(value: object) -> dict[str, object]:
    source = _copy(grid(value))
    observe(source)
    original = set(_interesting(source))
    vertical = _vertical_pass(source)
    created = sorted(set(_interesting(vertical)) - original)
    final = _horizontal_pass(vertical, created)
    return {
        "vertical_pass": vertical,
        "created_by_vertical_pass": [list(cell) for cell in created],
        "final": final,
        "skip_vertical_then_horizontal": source,
    }


def transform(value: object, mode: object) -> list[list[int]]:
    mode = _mode(mode)
    source = _copy(grid(value))
    observe(source)
    vertical = _vertical_pass(source)
    if mode == "chain_only":
        original = set(_interesting(source))
        created = sorted(set(_interesting(vertical)) - original)
        return _horizontal_pass(vertical, created)
    return _horizontal_pass(vertical, _interesting(vertical))


def _predict(value: list[list[int]], hypothesis: str) -> list[list[int]]:
    source = _copy(grid(value))
    info = observe(source)
    original = _interesting(source)
    row_axis, col_axis = int(info["row_axis"]), int(info["col_axis"])
    if hypothesis in MODES:
        return transform(source, hypothesis)
    if hypothesis == "identity":
        return source
    if hypothesis == "vertical_only":
        return _mirror_cells(source, original, axis="vertical", position=col_axis)
    if hypothesis == "horizontal_only":
        return _mirror_cells(source, original, axis="horizontal", position=row_axis)
    if hypothesis == "diagonal_only":
        out = _copy(source)
        for r, c, cell in original:
            out[2 * row_axis - r][2 * col_axis - c] = cell
        return out
    if hypothesis == "horizontal_chain_only":
        horizontal = _mirror_cells(source, original, axis="horizontal", position=row_axis)
        created = sorted(set(_interesting(horizontal)) - set(original))
        return _mirror_cells(horizontal, created, axis="vertical", position=col_axis)
    if hypothesis == "require_unbroken_vertical_guide":
        if all(source[r][col_axis] == 5 for r in range(len(source))):
            return transform(source, "complete_orbit")
        return source
    raise ValueError(f"unknown declared hypothesis {hypothesis!r}")


def _seeded_rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"aad4e3a1d5e3-parametric-input-v1:{seed}:{split}:{index}".encode()
    return random.Random(hashlib.sha256(payload).digest())


def _core_cluster(count: int, row_span: int, col_span: int, rng: random.Random) -> set[tuple[int, int]]:
    candidates = [
        (1, 1), (1, 2), (2, 1), (2, 2), (1, 3), (3, 1), (2, 3), (3, 2),
        (3, 3), (1, 4), (4, 1), (2, 4), (4, 2), (3, 4), (4, 3), (4, 4),
        (1, 5), (5, 1), (2, 5), (5, 2),
    ]
    candidates = [(r, c) for r, c in candidates if r <= row_span and c <= col_span]
    if len(candidates) < count:
        raise ValueError("profile lacks room for requested core motif")
    # Preserve connectedness while changing color/shape ordering independently.
    chosen = set(candidates[:count])
    if rng.randrange(2):
        chosen = {(c, r) for r, c in chosen if c <= row_span and r <= col_span}
        if len(chosen) != count:
            chosen = set(candidates[:count])
    return chosen


def _edge_cluster(count: int, row_span: int, col_span: int) -> set[tuple[int, int]]:
    candidates = [
        (row_span, col_span),
        (row_span, col_span - 1),
        (row_span - 1, col_span),
        (row_span - 1, col_span - 1),
        (row_span, col_span - 2),
        (row_span - 2, col_span),
        (row_span - 1, col_span - 2),
        (row_span - 2, col_span - 1),
        (row_span - 2, col_span - 2),
        (row_span, col_span - 3),
    ]
    valid = [(r, c) for r, c in candidates if r >= 1 and c >= 1]
    if len(valid) < count:
        raise ValueError("profile lacks room for requested edge motif")
    return set(valid[:count])


def _motif_offsets(
    count: int,
    row_span: int,
    col_span: int,
    layout: str,
    rng: random.Random,
) -> set[tuple[int, int]]:
    if layout == "core":
        return _core_cluster(count, row_span, col_span, rng)
    edge_count = count // 2 if layout == "split" else max(8, count // 2)
    core_count = count - edge_count
    core = _core_cluster(core_count, row_span, col_span, rng)
    edge = _edge_cluster(edge_count, row_span, col_span)
    result = core | edge
    if len(result) != count:
        raise ValueError("motif clusters overlap")
    return result


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _DEMO_PROFILES if split == "demo" else _QUERY_PROFILES
    h, w, row_axis, col_axis, quadrant, owner, count, layout = profiles[index]
    rng = _seeded_rng(seed, split, index)
    row_span = min(row_axis, h - 1 - row_axis)
    col_span = min(col_axis, w - 1 - col_axis)
    offsets = _motif_offsets(count, row_span, col_span, layout, rng)
    row_sign = -1 if quadrant.startswith("top") else 1
    col_sign = -1 if quadrant.endswith("left") else 1
    colors = rng.sample(_ALLOWED_MOTIF_COLORS, 2)
    ordered = sorted(offsets)
    rng.shuffle(ordered)

    result = [[0] * w for _ in range(h)]
    for c in range(w):
        result[row_axis][c] = 6
    for r in range(h):
        result[r][col_axis] = 5
    result[row_axis][col_axis] = 5 if owner == "vertical" else 6
    for position, (dr, dc) in enumerate(ordered):
        result[row_axis + row_sign * dr][col_axis + col_sign * dc] = colors[position % 2]
    observed = observe(result)
    if observed["motif_cells"] != count or observed["intersection_owner"] != owner:
        raise AssertionError("constructed scene differs from profile")
    return result


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
    normalized_train = []
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("demonstrations need input and output")
        grid(pair["input"])
        grid(pair["output"])
        observe(pair["input"])
        normalized_train.append(pair)
    for value in query_inputs:
        grid(value)
        observe(value)
    survivors = [
        name
        for name in HYPOTHESES
        if all(_predict(pair["input"], name) == pair["output"] for pair in normalized_train)
    ]
    if len(survivors) != 1 or survivors[0] not in MODES:
        raise ValueError(f"demonstrations leave declared rivals: {survivors!r}")
    selected = survivors[0]
    predictions = [_predict(value, selected) for value in query_inputs]
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demonstrations": len(normalized_train),
        "queries": len(query_inputs),
        "legacy_unbroken_vertical_guide_refuted": "require_unbroken_vertical_guide" not in survivors,
        "predicted_query_sha256": [
            hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()
            for value in predictions
        ],
        "scope": "Finite declared rivals checked from demonstrations only; not a proof of universal rule uniqueness.",
    }

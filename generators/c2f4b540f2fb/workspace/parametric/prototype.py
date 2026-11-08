"""Source-bound local-tier selector family for ``c2f4b540f2fb``.

The canonical setting selects every source-local point on the maximum ``u``
tier and transfers those coordinates through the target frame.  The nearby
variants select the minimum ``u``, maximum ``v`` or minimum ``v`` tier.  The
input grammar and deterministic sampler are shared across settings so only the
executed rule changes.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

from puzzle_generators.helpers.local_frame import DIR4, frame_cells, gpos

TASK_ID = "c2f4b540f2fb"
HERE = Path(__file__).resolve().parent
PARAMETERS = {"axis": ["u", "v"], "extreme": ["max", "min"]}
DEFAULT_SETTINGS = {"axis": "u", "extreme": "max"}
SETTINGS = tuple(
    {"axis": axis, "extreme": extreme}
    for axis in PARAMETERS["axis"]
    for extreme in PARAMETERS["extreme"]
)
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (4, 4)

_CANONICAL_SELECTOR = (
    "(maxu (apply max (map first pts))) "
    "(chosen (filter (lambda (p) (= (first p) maxu)) pts))"
)
_SELECTOR_TEXT = {
    ("u", "max"): _CANONICAL_SELECTOR,
    ("u", "min"): (
        "(minu (apply min (map first pts))) "
        "(chosen (filter (lambda (p) (= (first p) minu)) pts))"
    ),
    ("v", "max"): (
        "(maxv (apply max (map second pts))) "
        "(chosen (filter (lambda (p) (= (second p) maxv)) pts))"
    ),
    ("v", "min"): (
        "(minv (apply min (map second pts))) "
        "(chosen (filter (lambda (p) (= (second p) minv)) pts))"
    ),
}

# Every profile avoids the marker-frame coordinates (0,0), (1,0), (0,1).
# Profile 0 has four distinct unique extrema; profile 1 has two-way ties at all
# four extrema.  These first two profiles make the declared minimum teachable.
_MOTIF_PROFILES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((-3, 0), (3, 1), (0, -3), (1, 3), (-1, 2), (2, -1)),
    ((-3, -1), (-3, 2), (3, -2), (3, 1), (-2, -3), (1, -3), (-1, 3), (2, 3)),
    ((-3, -2), (-1, 3), (0, -3), (2, 1), (3, -1), (3, 2)),
    ((-3, -1), (-2, 2), (1, -3), (2, 3), (3, 0), (-1, 3)),
    ((-3, 1), (3, -1), (3, 2), (-1, -3), (1, 3), (-2, 2), (2, -2)),
    ((-3, 0), (-1, -3), (-1, 2), (1, -2), (2, 3), (3, 0)),
)
_DECOY_PROFILES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((4, 1), (-4, -1)),
    ((1, 4), (-1, -4), (4, -2)),
    ((-4, 2), (2, -4)),
    ((4, 0), (0, 4), (-4, 0), (0, -4)),
)
_TRAIN_SIZES = ((14, 18), (18, 16), (20, 22), (24, 19), (27, 25), (30, 28))
_QUERY_SIZES = ((16, 21), (21, 18), (25, 27), (30, 30))
_LAYOUTS = (
    ("top_left", "bottom_right"),
    ("top_right", "bottom_left"),
    ("bottom_left", "top_right"),
    ("bottom_right", "top_left"),
    ("left", "right"),
    ("top", "bottom"),
)
_BASES = tuple(
    (vx, vy)
    for vx in DIR4
    for vy in DIR4
    if vx[0] * vy[0] + vx[1] * vy[1] == 0
)
_FRAME_LOCAL = ((0, 0), (1, 0), (0, 1))


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != set(PARAMETERS):
        raise ValueError("settings must contain exactly axis and extreme")
    axis, extreme = value["axis"], value["extreme"]
    if type(axis) is not str or axis not in PARAMETERS["axis"]:
        raise ValueError("axis must be 'u' or 'v'")
    if type(extreme) is not str or extreme not in PARAMETERS["extreme"]:
        raise ValueError("extreme must be 'max' or 'min'")
    return {"axis": axis, "extreme": extreme}


def canonical_program() -> str:
    raw = (HERE / "canonical.rkt").read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("canonical.rkt must be UTF-8") from exc
    if text.count(_CANONICAL_SELECTOR) != 1:
        raise ValueError("canonical selector clause changed or is ambiguous")
    return text


def program(settings: object) -> str:
    chosen = _settings(settings)
    canonical = canonical_program()
    if chosen == DEFAULT_SETTINGS:
        return canonical
    replacement = _SELECTOR_TEXT[(chosen["axis"], chosen["extreme"])]
    return canonical.replace(_CANONICAL_SELECTOR, replacement, 1)


def _grid(value: object) -> list[list[int]]:
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return value


def grid_digest(grid: object) -> str:
    _grid(grid)
    raw = json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _rng(seed: int, split: str, index: int, stream: str) -> random.Random:
    body = json.dumps([TASK_ID, "tier-v1", seed, split, index, stream], separators=(",", ":"))
    return random.Random(int(hashlib.sha256(body.encode()).hexdigest(), 16))


def _single(grid: list[list[int]], color: int) -> tuple[int, int]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if len(cells) != 1:
        raise ValueError(f"color {color} must occur exactly once")
    return cells[0]


def _frame(grid: list[list[int]], colors: tuple[int, int, int]):
    origin = _single(grid, colors[0])
    x = _single(grid, colors[1])
    y = _single(grid, colors[2])
    vx = x[0] - origin[0], x[1] - origin[1]
    vy = y[0] - origin[0], y[1] - origin[1]
    if vx not in DIR4 or vy not in DIR4 or vx[0] * vy[0] + vx[1] * vy[1] != 0:
        raise ValueError(f"colors {colors} do not define a unit orthogonal frame")
    return origin, vx, vy


def _lpos(origin: tuple[int, int], vx: tuple[int, int], vy: tuple[int, int], point: tuple[int, int]):
    dr, dc = point[0] - origin[0], point[1] - origin[1]
    return dr * vx[0] + dc * vx[1], dr * vy[0] + dc * vy[1]


def analyze(grid: object) -> dict[str, Any]:
    _grid(grid)
    source = _frame(grid, (2, 3, 4))
    target = _frame(grid, (5, 6, 7))
    so, svx, svy = source
    motif: list[tuple[int, int]] = []
    cyan_decoys: list[tuple[int, int]] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 8:
                continue
            uv = _lpos(so, svx, svy, (r, c))
            (motif if max(abs(uv[0]), abs(uv[1])) <= 3 else cyan_decoys).append(uv)
    motif = sorted(set(motif))
    cyan_decoys = sorted(set(cyan_decoys))
    if not 5 <= len(motif) <= 8:
        raise ValueError(f"source-local motif must have 5..8 cells, found {len(motif)}")
    if any(point in _FRAME_LOCAL for point in motif):
        raise ValueError("motif overlaps source frame")
    if len({u for u, _ in motif}) < 2 or len({v for _, v in motif}) < 2:
        raise ValueError("motif needs both u and v rank contrast")
    return {
        "size": (len(grid), len(grid[0])),
        "source": source,
        "target": target,
        "motif": tuple(motif),
        "cyan_decoys": tuple(cyan_decoys),
    }


def _selected(points: tuple[tuple[int, int], ...], settings: object) -> tuple[tuple[int, int], ...]:
    chosen = _settings(settings)
    axis_index = 0 if chosen["axis"] == "u" else 1
    values = [point[axis_index] for point in points]
    extreme = max(values) if chosen["extreme"] == "max" else min(values)
    return tuple(point for point in points if point[axis_index] == extreme)


def _paint(grid: list[list[int]], points: tuple[tuple[int, int], ...], *, basis: str = "target") -> list[list[int]]:
    info = analyze(grid)
    out = copy.deepcopy(grid)
    to, tvx, tvy = info["target"]
    if basis == "source":
        _, tvx, tvy = info["source"]
    for u, v in points:
        r, c = gpos(to, tvx, tvy, u, v)
        if 0 <= r < len(out) and 0 <= c < len(out[0]):
            out[r][c] = 8
    return out


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    info = analyze(grid)
    return _paint(grid, _selected(info["motif"], settings))


def _symmetry(point: tuple[int, int], code: int) -> tuple[int, int]:
    u, v = point
    return (
        (u, v), (-u, v), (u, -v), (-u, -v),
        (v, u), (-v, u), (v, -u), (-v, -u),
    )[code % 8]


def _profile(seed: int, split: str, index: int) -> tuple[tuple[int, int], ...]:
    if split == "train":
        base_index = index if index < 2 else (index + 1) % len(_MOTIF_PROFILES)
    else:
        base_index = (2, 1, 3, 4)[index]
    rng = _rng(seed, split, index, "profile")
    code = rng.randrange(8)
    points = tuple(sorted(_symmetry(point, code) for point in _MOTIF_PROFILES[base_index]))
    if len(set(points)) != len(points) or any(point in _FRAME_LOCAL for point in points):
        raise RuntimeError("invalid transformed motif profile")
    return points


def _decoys(seed: int, split: str, index: int) -> tuple[tuple[int, int], ...]:
    base = _DECOY_PROFILES[(index + (0 if split == "train" else 1)) % len(_DECOY_PROFILES)]
    code = _rng(seed, split, index, "decoy-profile").randrange(8)
    return tuple(sorted(_symmetry(point, code) for point in base))


def _basis(seed: int, split: str, index: int, target: bool):
    offset = int(hashlib.sha256(f"{TASK_ID}:{seed}:{split}:basis".encode()).hexdigest(), 16) % len(_BASES)
    source_index = (offset + 3 * index) % len(_BASES)
    if not target:
        return _BASES[source_index]
    # Alternate same/different handedness while ensuring most pairs require a
    # real target-basis transfer rather than a simple absolute shift.
    delta = (1, 3, 5, 2)[index % 4]
    return _BASES[(source_index + delta) % len(_BASES)]


def _cells(origin, vx, vy, local_points):
    return {gpos(origin, vx, vy, u, v) for u, v in local_points}


def _origins(h: int, w: int, vx, vy, local_points):
    result = []
    for r in range(h):
        for c in range(w):
            cells = _cells((r, c), vx, vy, local_points)
            if all(0 <= rr < h and 0 <= cc < w for rr, cc in cells):
                result.append(((r, c), cells))
    return result


def _zone(origin: tuple[int, int], h: int, w: int, name: str) -> bool:
    r, c = origin
    if name == "top_left":
        return r < h * 0.48 and c < w * 0.48
    if name == "top_right":
        return r < h * 0.48 and c >= w * 0.52
    if name == "bottom_left":
        return r >= h * 0.52 and c < w * 0.48
    if name == "bottom_right":
        return r >= h * 0.52 and c >= w * 0.52
    if name == "left":
        return c < w * 0.42
    if name == "right":
        return c >= w * 0.58
    if name == "top":
        return r < h * 0.42
    if name == "bottom":
        return r >= h * 0.58
    raise ValueError(name)


def _touches_boundary(cells: set[tuple[int, int]], h: int, w: int) -> bool:
    return any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells)


def _choose_frames(
    h: int,
    w: int,
    motif: tuple[tuple[int, int], ...],
    decoys: tuple[tuple[int, int], ...],
    source_basis,
    target_basis,
    layout: tuple[str, str],
    rng: random.Random,
    boundary: bool,
):
    local_all = tuple(set(_FRAME_LOCAL) | set(motif) | set(decoys))
    svx, svy = source_basis
    tvx, tvy = target_basis
    source_options = [row for row in _origins(h, w, svx, svy, local_all)
                      if _zone(row[0], h, w, layout[0])]
    if boundary:
        boundary_options = [row for row in source_options if _touches_boundary(row[1], h, w)]
        if boundary_options:
            source_options = boundary_options
    rng.shuffle(source_options)
    for source_origin, source_cells in source_options:
        target_options = []
        for target_origin, target_cells in _origins(h, w, tvx, tvy, local_all):
            if not _zone(target_origin, h, w, layout[1]):
                continue
            if source_cells & target_cells:
                continue
            distance = abs(target_origin[0] - source_origin[0]) + abs(target_origin[1] - source_origin[1])
            if distance < max(6, min(h, w) // 3):
                continue
            target_options.append((target_origin, target_cells))
        if target_options:
            target_origin, target_cells = rng.choice(target_options)
            return (source_origin, svx, svy, source_cells), (target_origin, tvx, tvy, target_cells)
    raise RuntimeError(f"no frame placement for {h}x{w}, layout={layout}, boundary={boundary}")


def _draw_frame(grid: list[list[int]], frame, colors: tuple[int, int, int]) -> None:
    origin, vx, vy = frame[:3]
    for point, color in zip(frame_cells(origin, vx, vy), colors):
        r, c = point
        if grid[r][c] != 0:
            raise RuntimeError("frame placement collision")
        grid[r][c] = color


def _available_cell(grid, occupied, rng, zone_name: str | None = None):
    h, w = len(grid), len(grid[0])
    candidates = [
        (r, c) for r in range(h) for c in range(w)
        if (r, c) not in occupied and grid[r][c] == 0
        and (zone_name is None or _zone((r, c), h, w, zone_name))
    ]
    if not candidates:
        return None
    return rng.choice(candidates)


def _add_texture(grid: list[list[int]], occupied: set[tuple[int, int]], rng: random.Random,
                 *, dense: bool, boundary: bool) -> None:
    h, w = len(grid), len(grid[0])
    # Seed all quadrants with visible, non-semantic structure.
    for zone_name, color in zip(("top_left", "top_right", "bottom_left", "bottom_right"), (1, 9, 9, 1)):
        cell = _available_cell(grid, occupied, rng, zone_name)
        if cell is not None:
            grid[cell[0]][cell[1]] = color
            occupied.add(cell)
    bars = 8 if dense else 3 + rng.randrange(3)
    for i in range(bars):
        horizontal = bool(rng.randrange(2))
        length = rng.randint(2, 6 if dense else 4)
        r, c = rng.randrange(h), rng.randrange(w)
        cells = [(r, c + k) for k in range(length)] if horizontal else [(r + k, c) for k in range(length)]
        cells = [(rr, cc) for rr, cc in cells if 0 <= rr < h and 0 <= cc < w
                 and (rr, cc) not in occupied and grid[rr][cc] == 0]
        color = 1 if i % 2 == 0 else 9
        for rr, cc in cells:
            grid[rr][cc] = color
            occupied.add((rr, cc))
    if boundary:
        row = 0 if rng.randrange(2) == 0 else h - 1
        for c in range(0, w, max(2, w // 7)):
            if (row, c) not in occupied and grid[row][c] == 0:
                grid[row][c] = 9
                occupied.add((row, c))


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    limit = 6 if split == "train" else 4
    _integer(index, 0, limit - 1, "scene index")
    h, w = (_TRAIN_SIZES if split == "train" else _QUERY_SIZES)[index]
    motif = _profile(seed, split, index)
    decoys = _decoys(seed, split, index)
    source_basis = _basis(seed, split, index, False)
    target_basis = _basis(seed, split, index, True)
    layout = _LAYOUTS[(index + (0 if split == "train" else 2)) % len(_LAYOUTS)]
    boundary = split == "test" and index in {2, 3}
    rng = _rng(seed, split, index, "placement")
    source, target = _choose_frames(
        h, w, motif, decoys, source_basis, target_basis, layout, rng, boundary
    )
    grid = [[0 for _ in range(w)] for _ in range(h)]
    _draw_frame(grid, source, (2, 3, 4))
    _draw_frame(grid, target, (5, 6, 7))
    so, svx, svy = source[:3]
    for u, v in motif + decoys:
        r, c = gpos(so, svx, svy, u, v)
        if grid[r][c] != 0:
            raise RuntimeError("motif/decoy collision")
        grid[r][c] = 8
    occupied = set(source[3]) | set(target[3])
    _add_texture(grid, occupied, _rng(seed, split, index, "texture"),
                 dense=(h == 30 and w == 30), boundary=boundary)
    # Verify every declared output coordinate is blank before any setting paints it.
    for setting in SETTINGS:
        for u, v in _selected(tuple(sorted(motif)), setting):
            r, c = gpos(target[0], target[1], target[2], u, v)
            if grid[r][c] != 0:
                raise RuntimeError("selected target coordinate is not blank")
    analyze(grid)
    return grid


def _paint_global_axis(grid: list[list[int]], axis: str, extreme: str) -> list[list[int]]:
    info = analyze(grid)
    so, svx, svy = info["source"]
    cells = [(gpos(so, svx, svy, u, v), (u, v)) for u, v in info["motif"]]
    coordinate = 1 if axis == "column" else 0
    values = [cell[coordinate] for cell, _ in cells]
    value = max(values) if extreme == "max" else min(values)
    points = tuple(uv for cell, uv in cells if cell[coordinate] == value)
    return _paint(grid, points)


def _rival(name: str, grid: list[list[int]], settings: object) -> list[list[int]]:
    info = analyze(grid)
    selected = _selected(info["motif"], settings)
    if name == "copy_all_local":
        return _paint(grid, info["motif"])
    if name == "copy_all_cyan_ignore_radius":
        return _paint(grid, tuple(info["motif"]) + tuple(info["cyan_decoys"]))
    if name == "one_selected_only":
        return _paint(grid, tuple(sorted(selected))[:1])
    if name == "global_rightmost":
        return _paint_global_axis(grid, "column", "max")
    if name == "global_topmost":
        return _paint_global_axis(grid, "row", "min")
    if name == "fixed_lexicographic_local":
        return _paint(grid, tuple(sorted(info["motif"]))[:1])
    if name == "source_basis_transfer":
        return _paint(grid, selected, basis="source")
    if name == "identity":
        return copy.deepcopy(grid)
    raise KeyError(name)


EXTRA_RIVALS = (
    "copy_all_local",
    "copy_all_cyan_ignore_radius",
    "one_selected_only",
    "global_rightmost",
    "global_topmost",
    "fixed_lexicographic_local",
    "source_basis_transfer",
    "identity",
)


def certify(episode: dict[str, Any], execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    chosen = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program_solution differs from fixed settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(len(train), *DEMO_LIMITS, "demonstrations")
    if len(test) != 4:
        raise ValueError("queries must contain exactly four pairs")
    pairs = train + test
    if len({grid_digest(pair.get("input")) for pair in pairs}) != len(pairs):
        raise ValueError("all demonstration and query inputs must be distinct")
    for pair in pairs:
        _grid(pair.get("input")); _grid(pair.get("output"))
    apply = execute or (lambda source, grid: transform(
        grid, next(setting for setting in SETTINGS if program(setting) == source)
    ))
    records = []
    survivors = []
    for setting in SETTINGS:
        predictions = [apply(program(setting), pair["input"]) for pair in train]
        disagreements = [i for i, (got, pair) in enumerate(zip(predictions, train))
                         if got != pair["output"]]
        records.append({"settings": dict(setting), "disagreeing_demo_indices": disagreements})
        if not disagreements:
            survivors.append(dict(setting))
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not uniquely identify settings: {survivors}")
    extra_refutations: dict[str, list[int]] = {}
    for name in EXTRA_RIVALS:
        disagreements = [i for i, pair in enumerate(train)
                         if _rival(name, pair["input"], chosen) != pair["output"]]
        if not disagreements:
            raise ValueError(f"extra rival {name!r} survives every demonstration")
        extra_refutations[name] = disagreements
    query_rows = []
    for pair in test:
        actual = apply(program(chosen), pair["input"])
        if actual != pair["output"]:
            raise ValueError("query label disagrees with chosen setting")
        query_rows.append({"input_sha256": grid_digest(pair["input"]),
                           "output_sha256": grid_digest(pair["output"])})
    return {
        "scope": "four tier selectors plus eight finite shortcut rules",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "declared_refutations": records,
        "extra_refutations": extra_refutations,
        "queries": query_rows,
    }


def generate(seed: int, settings: object, demos: int, queries: int) -> dict[str, Any]:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, *DEMO_LIMITS, "demonstrations")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    chosen = _settings(settings)
    train = []
    for index in range(demos):
        grid = _scene(seed, "train", index)
        train.append({"input": grid, "output": transform(grid, chosen)})
    test = []
    for index in range(4):
        grid = _scene(seed, "test", index)
        test.append({"input": grid, "output": transform(grid, chosen)})
    episode = {
        "schema": "c2f4b540f2fb-tier-parametric-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": program(chosen),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    _integer(query_index, 0, 3, "query index")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != 4:
        raise ValueError("episode must retain exactly four queries")
    return {
        "train": [{"input": copy.deepcopy(pair["input"]),
                   "output": copy.deepcopy(pair["output"])} for pair in train],
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }


def scene_profile(grid: list[list[int]]) -> dict[str, Any]:
    info = analyze(grid)
    h, w = info["size"]
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    quadrants = sorted({(0 if r < h / 2 else 2) + (0 if c < w / 2 else 1) for r, c in nonzero})
    counts = {
        "max_u": len(_selected(info["motif"], {"axis": "u", "extreme": "max"})),
        "min_u": len(_selected(info["motif"], {"axis": "u", "extreme": "min"})),
        "max_v": len(_selected(info["motif"], {"axis": "v", "extreme": "max"})),
        "min_v": len(_selected(info["motif"], {"axis": "v", "extreme": "min"})),
    }
    _, svx, svy = info["source"]
    _, tvx, tvy = info["target"]
    return {
        "size": [h, w],
        "source_basis": [*svx, *svy],
        "target_basis": [*tvx, *tvy],
        "motif": [list(point) for point in info["motif"]],
        "cyan_decoys": [list(point) for point in info["cyan_decoys"]],
        "selected_tie_counts": counts,
        "nonzero_count": len(nonzero),
        "occupied_quadrants": quadrants,
        "touches_boundary": any(r in (0, h - 1) or c in (0, w - 1) for r, c in nonzero),
    }

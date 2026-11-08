"""Source-bound parametric family for selector-driven stencil growth.

``render_mode=union`` is the exact canonical rule.  The nearby
``overlap_highlight`` setting keeps the same selector, seeds, and stencil
semantics, but first computes the input-dependent coverage multiplicity of every
cell.  It then paints singly covered cells cyan (8) and cells covered by two or
more distinct seed stencils red (2).

This file generates deterministic claim labels.  Native qualification replays
all labels through protected Racket and remains the authority.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "84730935f58f"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RENDER_MODES = ("union", "overlap_highlight")
DEFAULT = {"render_mode": "union"}
PARAMETERS = {"render_mode": list(RENDER_MODES)}
PLUS_OFFSETS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
X_OFFSETS = ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))
SEED_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
SELECTOR_HALO = {(0, 1), (1, 0), (1, 1)}
DEMO_SIZES = ((8, 10), (9, 11), (10, 12), (11, 13), (12, 14), (14, 16))
QUERY_SIZES = ((10, 12), (16, 18), (24, 27), (30, 30))

_ALT_PROGRAM = r'''(rule! (let ((dummy 0))
  (define plus-offsets (list (list 0 0) (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))
  (define x-offsets (list (list 0 0) (list -1 -1) (list -1 1) (list 1 -1) (list 1 1)))
  (define (nonzero-cells grid)
    (sort (filter (lambda (cell) (not (= (third cell) 0))) (grid-cells grid))
          (lambda (a b) (cell< (list (first a) (second a))
                              (list (first b) (second b))))))
  (define (grow-hits grid centers offsets)
    (filter (lambda (p) (in-bounds? (first p) (second p) (rows grid) (cols grid)))
            (flatmap (lambda (p)
                       (map (lambda (d)
                              (list (+ (first p) (first d))
                                    (+ (second p) (second d))))
                            offsets))
                     centers)))
  (define (same-position? a b)
    (and (= (first a) (first b)) (= (second a) (second b))))
  (define (hit-count p hits)
    (length (filter (lambda (q) (same-position? p q)) hits)))
  (let* ((marker (top-left g))
         (offsets (if (= marker 1) plus-offsets x-offsets))
         (centers (map (lambda (cell) (list (first cell) (second cell)))
                       (filter (lambda (cell)
                                 (not (and (= (first cell) 0)
                                           (= (second cell) 0))))
                               (nonzero-cells g))))
         (hits (grow-hits g centers offsets))
         (covered (remove-duplicates hits))
         (overlaps (filter (lambda (p) (> (hit-count p hits) 1)) covered))
         (base (paint-cells (empty-grid (rows g) (cols g) 0) covered 8)))
    (paint-cells base overlaps 2))))'''


def _canonical_path(root: Path) -> Path:
    for relative in ("shared/data/canonical/puzzles.jsonl", "data/canonical/puzzles.jsonl"):
        path = root / relative
        if path.is_file():
            return path
    raise FileNotFoundError(f"canonical ledger not found under {root}")


def canonical_program(*, root: Path | str = REPO) -> str:
    root = Path(root).resolve()
    rows = []
    with _canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row.get("program_solution"))
    programs = {value for value in rows if isinstance(value, str)}
    if len(programs) != 1:
        raise ValueError("one exact canonical program is required")
    return next(iter(programs))


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"render_mode"}:
        raise ValueError("settings must contain exactly render_mode")
    mode = value["render_mode"]
    if type(mode) is not str or mode not in RENDER_MODES:
        raise ValueError("render_mode must be 'union' or 'overlap_highlight'")
    return {"render_mode": mode}


def _count(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _grid(value: object) -> list[list[int]]:
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid must be rectangular with exact ARC colours")
    return value


def program(settings: object) -> str:
    chosen = _settings(settings)
    return canonical_program() if chosen == DEFAULT else _ALT_PROGRAM


def seed_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    _grid(grid)
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != (0, 0)
    ]


def _stencil(grid: list[list[int]], override: str | None = None) -> str:
    if override is not None:
        if override not in ("plus", "x"):
            raise ValueError("stencil override must be plus or x")
        return override
    return "plus" if grid[0][0] == 1 else "x"


def coverage_counts(grid: list[list[int]], stencil_override: str | None = None) -> dict[tuple[int, int], int]:
    _grid(grid)
    height, width = len(grid), len(grid[0])
    offsets = PLUS_OFFSETS if _stencil(grid, stencil_override) == "plus" else X_OFFSETS
    counts: Counter[tuple[int, int]] = Counter()
    for r, c in seed_cells(grid):
        for dr, dc in offsets:
            rr, cc = r + dr, c + dc
            if 0 <= rr < height and 0 <= cc < width:
                counts[(rr, cc)] += 1
    return dict(counts)


def _render(grid: list[list[int]], render_mode: str, stencil_override: str | None = None) -> list[list[int]]:
    counts = coverage_counts(grid, stencil_override)
    output = [[0 for _ in row] for row in grid]
    for (r, c), count in counts.items():
        output[r][c] = 2 if render_mode == "overlap_highlight" and count >= 2 else 8
    return output


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    chosen = _settings(settings)
    return _render(grid, chosen["render_mode"])


def transform_with_stencil(grid: list[list[int]], settings: object, stencil: str) -> list[list[int]]:
    chosen = _settings(settings)
    return _render(grid, chosen["render_mode"], stencil)


def seed_center_highlight_rival(grid: list[list[int]]) -> list[list[int]]:
    output = _render(grid, "union")
    for r, c in seed_cells(grid):
        output[r][c] = 2
    return output


def grid_digest(grid: list[list[int]]) -> str:
    body = json.dumps(_grid(grid), separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(body).hexdigest()


def _rng(seed: int, domain: str, index: int) -> random.Random:
    body = json.dumps([TASK_ID, "overlap-v1", seed, domain, index], separators=(",", ":")).encode()
    return random.Random(int(hashlib.sha256(body).hexdigest(), 16))


def _footprint(center: tuple[int, int], mode: str, height: int, width: int) -> set[tuple[int, int]]:
    offsets = PLUS_OFFSETS if mode == "plus" else X_OFFSETS
    r, c = center
    return {
        (r + dr, c + dc)
        for dr, dc in offsets
        if 0 <= r + dr < height and 0 <= c + dc < width
    }


def _pair_candidates(height: int, width: int, mode: str) -> list[dict]:
    candidates = []
    for r in range(height):
        for c in range(width):
            for orientation in ("horizontal", "vertical"):
                other = (r, c + 2) if orientation == "horizontal" else (r + 2, c)
                centers = ((r, c), other)
                if not all(0 <= rr < height and 0 <= cc < width for rr, cc in centers):
                    continue
                if any(center == (0, 0) or center in SELECTOR_HALO for center in centers):
                    continue
                footprints = [_footprint(center, mode, height, width) for center in centers]
                overlap = footprints[0] & footprints[1]
                if not overlap:
                    continue
                union = footprints[0] | footprints[1]
                candidates.append({
                    "centers": centers,
                    "footprint": union,
                    "overlap": overlap,
                    "boundary": any(rr in (0, height - 1) or cc in (0, width - 1)
                                    for rr, cc in centers),
                    "mid": ((centers[0][0] + centers[1][0]) / 2,
                            (centers[0][1] + centers[1][1]) / 2),
                })
    return candidates


def _targets(height: int, width: int, count: int) -> list[tuple[float, float]]:
    fractions = (
        (0.22, 0.22), (0.22, 0.76), (0.76, 0.22), (0.76, 0.76),
        (0.50, 0.50), (0.18, 0.50), (0.82, 0.50), (0.50, 0.84),
        (0.50, 0.16), (0.34, 0.68),
    )
    return [((height - 1) * a, (width - 1) * b) for a, b in fractions[:count]]


def _choose_pairs(height: int, width: int, mode: str, count: int, rng: random.Random,
                  *, force_boundary: bool) -> tuple[list[tuple[int, int]], set[tuple[int, int]]]:
    candidates = _pair_candidates(height, width, mode)
    jitter = {id(row): rng.random() for row in candidates}
    chosen: list[dict] = []
    used: set[tuple[int, int]] = set()

    if force_boundary:
        boundary = [row for row in candidates if row["boundary"]]
        if not boundary:
            raise RuntimeError("no boundary pair available")
        target = (height - 1, width * 0.55)
        first = min(boundary, key=lambda row: (
            (row["mid"][0] - target[0]) ** 2 + (row["mid"][1] - target[1]) ** 2,
            jitter[id(row)], row["centers"],
        ))
        chosen.append(first)
        used |= first["footprint"]

    for target in _targets(height, width, count):
        if len(chosen) >= count:
            break
        legal = [row for row in candidates if not (row["footprint"] & used)]
        if not legal:
            break
        row = min(legal, key=lambda item: (
            (item["mid"][0] - target[0]) ** 2 + (item["mid"][1] - target[1]) ** 2,
            jitter[id(item)], item["centers"],
        ))
        chosen.append(row)
        used |= row["footprint"]
    if len(chosen) != count:
        raise RuntimeError(f"could place only {len(chosen)} of {count} overlap pairs")
    centers = [center for row in chosen for center in row["centers"]]
    return centers, used


def _choose_isolated(height: int, width: int, mode: str, count: int,
                     used: set[tuple[int, int]], rng: random.Random) -> list[tuple[int, int]]:
    candidates = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) != (0, 0) and (r, c) not in SELECTOR_HALO
        and not (_footprint((r, c), mode, height, width) & used)
    ]
    jitter = {cell: rng.random() for cell in candidates}
    chosen: list[tuple[int, int]] = []
    while len(chosen) < count:
        legal = [cell for cell in candidates if cell not in chosen
                 and not (_footprint(cell, mode, height, width) & used)]
        if not legal:
            raise RuntimeError(f"could place only {len(chosen)} of {count} isolated seeds")
        if chosen:
            cell = max(legal, key=lambda p: (
                min(abs(p[0] - q[0]) + abs(p[1] - q[1]) for q in chosen),
                -jitter[p], p,
            ))
        else:
            center = ((height - 1) / 2, (width - 1) / 2)
            cell = max(legal, key=lambda p: (
                (p[0] - center[0]) ** 2 + (p[1] - center[1]) ** 2,
                -jitter[p], p,
            ))
        chosen.append(cell)
        used |= _footprint(cell, mode, height, width)
    return chosen


def _scene_shape(domain: str, index: int) -> tuple[int, int, str, int, int, bool]:
    if domain == "demo":
        if not 0 <= index < len(DEMO_SIZES):
            raise ValueError("demo index outside 0..5")
        height, width = DEMO_SIZES[index]
        mode = "plus" if index % 2 == 0 else "x"
        pairs = (1, 1, 2, 2, 3, 3)[index]
        singles = (2, 2, 2, 3, 3, 4)[index]
        return height, width, mode, pairs, singles, index == 5
    if domain == "query":
        if not 0 <= index < 4:
            raise ValueError("query index outside 0..3")
        height, width = QUERY_SIZES[index]
        mode = "x" if index % 2 == 0 else "plus"
        pairs = (2, 3, 5, 8)[index]
        singles = (2, 3, 4, 4)[index]
        return height, width, mode, pairs, singles, index >= 2
    raise ValueError(domain)


def _cross_scene(seed: int, mode: str) -> list[list[int]]:
    height, width = 12, 14
    centers = [(3, 3), (3, 5), (7, 8), (9, 8), (5, 11), (10, 3)]
    rng = _rng(seed, "cross", 0)
    colours = [SEED_COLORS[(index + rng.randrange(len(SEED_COLORS))) % len(SEED_COLORS)]
               for index in range(len(centers))]
    grid = [[0] * width for _ in range(height)]
    grid[0][0] = 1 if mode == "plus" else 2 + rng.randrange(6)
    for (r, c), colour in zip(centers, colours):
        grid[r][c] = colour
    return grid


def scene(seed: int, domain: str, index: int, *, demos: int) -> list[list[int]]:
    _count(seed, 0, 2**63 - 1, "seed")
    _count(demos, 2, 6, "demos")
    if domain == "cross_plus":
        return _cross_scene(seed, "plus")
    if domain == "cross_x":
        return _cross_scene(seed, "x")
    height, width, mode, pair_count, single_count, force_boundary = _scene_shape(domain, index)
    rng = _rng(seed, domain, index)
    pair_centers, used = _choose_pairs(
        height, width, mode, pair_count, rng, force_boundary=force_boundary
    )
    singles = _choose_isolated(height, width, mode, single_count, used, rng)
    centers = pair_centers + singles
    grid = [[0] * width for _ in range(height)]
    grid[0][0] = 1 if mode == "plus" else 2 + rng.randrange(6)
    palette = list(SEED_COLORS)
    rng.shuffle(palette)
    for position, colour in zip(centers, (palette * ((len(centers) + 7) // 8))[:len(centers)]):
        grid[position[0]][position[1]] = colour
    facts = profile(grid)
    if facts["overlap_cells"] <= 0 or facts["num_seeds"] != len(centers):
        raise RuntimeError("constructed scene lost its overlap or seed count")
    return grid


def profile(grid: list[list[int]]) -> dict:
    _grid(grid)
    height, width = len(grid), len(grid[0])
    seeds = seed_cells(grid)
    counts = coverage_counts(grid)
    quadrants = {
        (0 if r < height / 2 else 1, 0 if c < width / 2 else 1)
        for r, c in seeds
    }
    return {
        "height": height,
        "width": width,
        "selector": grid[0][0],
        "mode": _stencil(grid),
        "num_seeds": len(seeds),
        "overlap_cells": sum(value >= 2 for value in counts.values()),
        "single_coverage_cells": sum(value == 1 for value in counts.values()),
        "max_coverage": max(counts.values(), default=0),
        "occupied_quadrants": len(quadrants),
        "boundary_seed_count": sum(r in (0, height - 1) or c in (0, width - 1) for r, c in seeds),
    }


def surviving_settings(train: Iterable[dict]) -> list[dict[str, str]]:
    pairs = list(train)
    survivors = []
    for render_mode in RENDER_MODES:
        settings = {"render_mode": render_mode}
        if all(transform(pair["input"], settings) == pair["output"] for pair in pairs):
            survivors.append(settings)
    return survivors


def generate(seed: int, settings: object, demos: int, queries: int) -> dict:
    _count(seed, 0, 2**63 - 1, "seed")
    chosen = _settings(settings)
    _count(demos, 2, 6, "demos")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly four")
    demo_inputs = [scene(seed, "demo", index, demos=demos) for index in range(demos)]
    query_inputs = [scene(seed, "query", index, demos=demos) for index in range(queries)]
    all_inputs = demo_inputs + query_inputs
    digests = [grid_digest(grid) for grid in all_inputs]
    if len(digests) != len(set(digests)):
        raise RuntimeError("episode inputs must be distinct")
    train = [{"input": grid, "output": transform(grid, chosen)} for grid in demo_inputs]
    test = [{"input": grid, "output": transform(grid, chosen)} for grid in query_inputs]
    if surviving_settings(train) != [chosen]:
        raise RuntimeError("demonstrations do not identify the selected render_mode")
    return {"train": train, "test": test, "program_solution": program(chosen)}


def execute(bridge, racket_program: str, grid: list[list[int]]) -> list[list[int]]:
    from puzzle_generators.rule_wrap import wrap_rule
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in _grid(grid)) + ")"
    return bridge.eval_text(f"({wrap_rule(racket_program)} {literal})")

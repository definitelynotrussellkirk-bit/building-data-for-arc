"""Matched-input parametric family for local tile reflection.

The canonical setting mirrors every tile left-right.  The alternate first
measures foreground occupancy in every tile, selects the unique densest tile,
and mirrors only that selected tile.  The selector is input-dependent and its
result is consumed by the subsequent local transformation.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "ba29d14676d1"
TILE_SCOPES = ("all_tiles", "densest_only")
DEFAULT_SCOPE = "all_tiles"
CANONICAL_PROGRAM = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")

DENSEST_PROGRAM = r"""(rule!
 (let ((dummy 0))
   (define (full-row? grid r color)
     (all? (lambda (c) (= (at grid r c) color)) (range 0 (cols grid))))
   (define (full-col? grid c color)
     (all? (lambda (r) (= (at grid r c) color)) (range 0 (rows grid))))
   (define (segments-from-dividers n dividers)
     (let loop ((ds (append dividers (list n))) (prev -1) (acc (list)))
       (if (empty? ds)
           (reverse acc)
           (let ((x (first ds)))
             (loop (rest ds) x
                   (if (> (- x prev 1) 0)
                       (cons (list (+ prev 1) x) acc)
                       acc))))))
   (define row-bounds
     (segments-from-dividers
      (rows g)
      (filter (lambda (r) (full-row? g r 9)) (range 0 (rows g)))))
   (define col-bounds
     (segments-from-dividers
      (cols g)
      (filter (lambda (c) (full-col? g c 9)) (range 0 (cols g)))))
   (define records
     (for*/list ((tr (in-range (length row-bounds)))
                 (tc (in-range (length col-bounds))))
       (let* ((rb (list-ref row-bounds tr))
              (cb (list-ref col-bounds tc))
              (tile (subgrid g (first rb) (first cb)
                             (- (second rb) 1) (- (second cb) 1)))
              (marks (count-if (lambda (v) (!= v 0)) (apply append tile)))
              (index (+ (* tr (length col-bounds)) tc)))
         (list tr tc tile marks index))))
   (define selected
     (first
      (sort records
            (lambda (a b)
              (or (> (list-ref a 3) (list-ref b 3))
                  (and (= (list-ref a 3) (list-ref b 3))
                       (< (list-ref a 4) (list-ref b 4))))))))
   (for*/fold ((out g))
              ((tr (in-range (length row-bounds)))
               (tc (in-range (length col-bounds)))
               (r (in-range (- (second (list-ref row-bounds tr))
                               (first (list-ref row-bounds tr)))))
               (c (in-range (- (second (list-ref col-bounds tc))
                               (first (list-ref col-bounds tc))))))
     (let* ((rb (list-ref row-bounds tr))
            (cb (list-ref col-bounds tc))
            (tile (subgrid g (first rb) (first cb)
                           (- (second rb) 1) (- (second cb) 1)))
            (source (if (and (= tr (first selected)) (= tc (second selected)))
                        (flip-lr tile)
                        tile)))
       (set-cell out (+ (first rb) r) (+ (first cb) c) (at source r c))))))"""

WRONG_SPARSEST_PROGRAM = DENSEST_PROGRAM.replace(
    "(or (> (list-ref a 3) (list-ref b 3))",
    "(or (< (list-ref a 3) (list-ref b 3))",
    1,
)

# (tile rows, tile columns, tile height, tile width)
_DEMO_SPECS = (
    (1, 3, 3, 3),
    (2, 4, 3, 4),
    (3, 3, 4, 5),
    (1, 5, 5, 5),
    (4, 3, 5, 4),
    (5, 5, 5, 5),
)
_QUERY_SPECS = (
    (2, 5, 4, 4),
    (5, 4, 4, 5),
    (5, 5, 5, 5),
    (1, 1, 30, 30),
)


def validate_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"tile_scope"}:
        raise ValueError("settings must contain exactly tile_scope")
    scope = settings["tile_scope"]
    if type(scope) is not str or scope not in TILE_SCOPES:
        raise ValueError(f"tile_scope must be one of {TILE_SCOPES}")
    return {"tile_scope": scope}


def program(settings: object) -> str:
    scope = validate_settings(settings)["tile_scope"]
    return CANONICAL_PROGRAM if scope == "all_tiles" else DENSEST_PROGRAM


def counterfactual_program() -> str:
    return WRONG_SPARSEST_PROGRAM


def _mix(*parts: object) -> int:
    raw = ":".join(map(str, (TASK_ID, "densest-tile-v1", *parts)))
    return int.from_bytes(hashlib.sha256(raw.encode("utf-8")).digest()[:8], "big")


def _spans(size: int, dividers: list[int]) -> list[tuple[int, int]]:
    cuts = [-1, *dividers, size]
    spans = [(a + 1, b) for a, b in zip(cuts, cuts[1:]) if b - a > 1]
    if not spans:
        raise ValueError("grid has no tile span")
    return spans


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be exact integer ARC colors")
    row_dividers = [r for r, row in enumerate(grid) if all(value == 9 for value in row)]
    col_dividers = [c for c in range(width) if all(grid[r][c] == 9 for r in range(len(grid)))]
    row_spans = _spans(len(grid), row_dividers)
    col_spans = _spans(width, col_dividers)
    records: list[dict[str, Any]] = []
    for tr, (ra, rb) in enumerate(row_spans):
        for tc, (ca, cb) in enumerate(col_spans):
            tile = [row[ca:cb] for row in grid[ra:rb]]
            count = sum(value != 0 for row in tile for value in row)
            records.append(
                {
                    "tile_row": tr,
                    "tile_col": tc,
                    "index": tr * len(col_spans) + tc,
                    "bounds": [ra, rb, ca, cb],
                    "count": count,
                    "tile": tile,
                }
            )
    densest = min(records, key=lambda item: (-item["count"], item["index"]))
    sparsest = min(records, key=lambda item: (item["count"], item["index"]))
    return {
        "row_spans": row_spans,
        "col_spans": col_spans,
        "tiles": records,
        "densest": densest,
        "sparsest": sparsest,
    }


def _mirror(tile: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in tile]


def apply_mode(grid: list[list[int]], scope: str) -> list[list[int]]:
    if scope not in TILE_SCOPES:
        raise ValueError(f"unknown tile scope {scope!r}")
    info = analyze(grid)
    out = deepcopy(grid)
    for record in info["tiles"]:
        selected = scope == "all_tiles" or record["index"] == info["densest"]["index"]
        source = _mirror(record["tile"]) if selected else record["tile"]
        ra, rb, ca, cb = record["bounds"]
        for r in range(rb - ra):
            for c in range(cb - ca):
                out[ra + r][ca + c] = source[r][c]
    return out


def apply_wrong_sparsest(grid: list[list[int]]) -> list[list[int]]:
    info = analyze(grid)
    out = deepcopy(grid)
    record = info["sparsest"]
    ra, rb, ca, cb = record["bounds"]
    source = _mirror(record["tile"])
    for r in range(rb - ra):
        for c in range(cb - ca):
            out[ra + r][ca + c] = source[r][c]
    return out


def _tile(height: int, width: int, count: int, foreground: int, rng: random.Random) -> list[list[int]]:
    area = height * width
    if not 1 <= count <= area - 1 or width < 2:
        raise ValueError("tile count must leave one edge cell blank")
    forced = (0, 0)
    forbidden = (0, width - 1)
    candidates = [(r, c) for r in range(height) for c in range(width) if (r, c) not in {forced, forbidden}]
    rng.shuffle(candidates)
    marked = {forced, *candidates[: count - 1]}
    return [[foreground if (r, c) in marked else 0 for c in range(width)] for r in range(height)]


def _build_input(seed: int, split: str, index: int, spec: tuple[int, int, int, int]) -> list[list[int]]:
    tile_rows, tile_cols, tile_h, tile_w = spec
    height = tile_rows * tile_h + tile_rows - 1
    width = tile_cols * tile_w + tile_cols - 1
    if not (1 <= height <= 30 and 1 <= width <= 30):
        raise ValueError("spec exceeds ARC canvas")
    rng = random.Random(_mix(seed, split, index, spec))
    foreground = 1 + (_mix(seed, split, index, "foreground") % 8)
    n_tiles = tile_rows * tile_cols
    area = tile_h * tile_w
    if n_tiles == 1:
        densest_index = 0
        densest_count = max(1, min(area - 1, area // 2 + (_mix(seed, split, index, "single") % max(1, area // 4))))
    else:
        if split == "train" and index == 0:
            # The minimum lesson starts on a non-edge tile and at low density,
            # refuting fixed-position, majority-filled, and one-blank shortcuts.
            densest_index = 1
            densest_count = max(2, area // 3)
        elif split == "train" and index == 1:
            candidates = [value for value in range(n_tiles) if value not in {0, 1, n_tiles - 1}]
            densest_index = candidates[_mix(seed, split, index, "densest") % len(candidates)]
            densest_count = max(2, area - 2)
        else:
            candidates = list(range(1, n_tiles - 1)) if n_tiles > 2 else list(range(n_tiles))
            densest_index = candidates[_mix(seed, split, index, "densest") % len(candidates)]
            lower = max(2, area // 3)
            densest_count = lower + (_mix(seed, split, index, "density") % (area - lower))
    tiles: list[list[list[list[int]]]] = []
    for tr in range(tile_rows):
        row = []
        for tc in range(tile_cols):
            flat = tr * tile_cols + tc
            if n_tiles == 1 or flat == densest_index:
                count = densest_count
            else:
                count = 1 + (_mix(seed, split, index, flat, "count") % (densest_count - 1))
            row.append(_tile(tile_h, tile_w, count, foreground, rng))
        tiles.append(row)
    grid = [[9 for _ in range(width)] for _ in range(height)]
    for tr in range(tile_rows):
        for tc in range(tile_cols):
            top = tr * (tile_h + 1)
            left = tc * (tile_w + 1)
            for r in range(tile_h):
                for c in range(tile_w):
                    grid[top + r][left + c] = tiles[tr][tc][r][c]
    info = analyze(grid)
    if n_tiles > 1:
        if info["densest"]["index"] != densest_index:
            raise RuntimeError("constructed densest tile changed")
        if any(record["tile"] == _mirror(record["tile"]) for record in info["tiles"]):
            raise RuntimeError("every multi-tile scene must visibly distinguish local reflection")
    return grid


def _validate_request(seed: int, demos: int, queries: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")


def generate_episode(seed: int, *, tile_scope: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _validate_request(seed, demos, queries)
    if tile_scope not in TILE_SCOPES:
        raise ValueError(f"tile_scope must be one of {TILE_SCOPES}")
    train_inputs = [_build_input(seed, "train", index, _DEMO_SPECS[index]) for index in range(demos)]
    test_inputs = [_build_input(seed, "test", index, _QUERY_SPECS[index]) for index in range(queries)]
    return {
        "train": [{"input": grid, "output": apply_mode(grid, tile_scope)} for grid in train_inputs],
        "test": [{"input": grid, "output": apply_mode(grid, tile_scope)} for grid in test_inputs],
        "program_solution": CANONICAL_PROGRAM if tile_scope == "all_tiles" else DENSEST_PROGRAM,
    }


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index is outside the episode")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(episode: dict[str, Any], query_index: int = 0) -> bytes:
    return (json.dumps(public_turn(episode, query_index), sort_keys=True, separators=(",", ":")) + "\n").encode()


def public_id(episode: dict[str, Any], query_index: int = 0) -> str:
    return hashlib.sha256(public_bytes(episode, query_index)).hexdigest()


def causal_case(seed: int = 0) -> dict[str, Any]:
    episode = generate_episode(seed, tile_scope="densest_only", demos=3, queries=4)
    pair = episode["test"][0]
    info = analyze(pair["input"])
    return {
        "input": pair["input"],
        "settings": {"tile_scope": "densest_only"},
        "intermediate_value": {
            "densest_index": info["densest"]["index"],
            "densest_count": info["densest"]["count"],
            "sparsest_index": info["sparsest"]["index"],
            "sparsest_count": info["sparsest"]["count"],
        },
        "program": DENSEST_PROGRAM,
        "output": pair["output"],
        "counterfactual_program": WRONG_SPARSEST_PROGRAM,
        "counterfactual_output": apply_wrong_sparsest(pair["input"]),
        "ablation": "wrong_intermediate",
    }

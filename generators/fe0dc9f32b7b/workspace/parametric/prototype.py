"""Task-local parametric family for ARC task fe0dc9f32b7b.

The canonical setting keeps the exact selected Racket program.  The alternate
setting reverses the palette before the unchanged component qualification,
containment-depth computation, and fill.  Inputs are setting-independent and
include clean, malformed, and count-qualified non-outline components.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "fe0dc9f32b7b"
PALETTE_DIRECTIONS = ("outer_to_inner", "inner_to_outer")
DEFAULT_PALETTE_DIRECTION = "outer_to_inner"
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
_ALLOWED_PALETTE = (1, 2, 3, 4, 5, 6, 7, 9)

CANONICAL_PROGRAM = """(rule!
  (let ((dummy 0))
    (define palette
      (for/list ([r (in-range (rows g))]
                 #:when (and (not (= (at g r 0) 0)) (not (= (at g r 0) 8))))
        (at g r 0)))
    (define (rect-frame? obj)
      (and (= (obj-color obj) 8)
           (>= (obj-h obj) 3)
           (>= (obj-w obj) 3)
           (= (obj-size obj) (- (* 2 (+ (obj-h obj) (obj-w obj))) 4))))
    (define frames
      (sort (filter rect-frame? (objects g 0))
            (lambda (a b)
              (if (= (obj-r1 a) (obj-r1 b))
                  (< (obj-c1 a) (obj-c1 b))
                  (< (obj-r1 a) (obj-r1 b))))))
    (for*/fold ([out g])
               ([r (in-range (rows g))]
                [c (in-range (cols g))])
      (if (= (at g r c) 0)
          (let ((depth (count-where (lambda (fr)
                                      (and (> r (obj-r1 fr)) (< r (obj-r2 fr))
                                           (> c (obj-c1 fr)) (< c (obj-c2 fr))))
                                    frames)))
            (if (and (> depth 0) (<= depth (length palette)))
                (set-cell out r c (nth palette (- depth 1)))
                out))
          out))))"""

_CANONICAL_PALETTE = """    (define palette
      (for/list ([r (in-range (rows g))]
                 #:when (and (not (= (at g r 0) 0)) (not (= (at g r 0) 8))))
        (at g r 0)))"""
_REVERSED_PALETTE = """    (define palette
      (reverse
       (for/list ([r (in-range (rows g))]
                  #:when (and (not (= (at g r 0) 0)) (not (= (at g r 0) 8))))
         (at g r 0))))"""
if CANONICAL_PROGRAM.count(_CANONICAL_PALETTE) != 1:
    raise RuntimeError("canonical palette block changed")
REVERSED_PROGRAM = CANONICAL_PROGRAM.replace(
    _CANONICAL_PALETTE, _REVERSED_PALETTE, 1
)


def _root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "shared/data/canonical/puzzles.jsonl").is_file():
            return parent
    raise FileNotFoundError("cannot locate the source-bound canonical ledger")


def canonical_program_from_ledger() -> str:
    programs: list[str] = []
    with (_root() / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    if programs != [CANONICAL_PROGRAM]:
        raise ValueError("task-local canonical bytes differ from the selected ledger")
    return programs[0]


def _direction(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("palette_direction must be a string")
    if value not in PALETTE_DIRECTIONS:
        raise ValueError("palette_direction must be outer_to_inner or inner_to_outer")
    return value


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a literal integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _counts(demos: Any, queries: Any) -> tuple[int, int]:
    demos = _integer("demos", demos, MIN_DEMOS, MAX_DEMOS)
    if isinstance(queries, bool) or not isinstance(queries, int):
        raise TypeError("queries must be a literal integer")
    if queries != QUERY_COUNT:
        raise ValueError(f"queries must equal {QUERY_COUNT}")
    return demos, queries


def program_for(palette_direction: Any) -> str:
    direction = _direction(palette_direction)
    return CANONICAL_PROGRAM if direction == DEFAULT_PALETTE_DIRECTION else REVERSED_PROGRAM


def _seed_rng(seed: int, namespace: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:parametric-v1:{seed}:{namespace}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _grid(height: int, width: int) -> list[list[int]]:
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    return [[0 for _ in range(width)] for _ in range(height)]


def _draw_frame(grid: list[list[int]], box: tuple[int, int, int, int]) -> None:
    r0, c0, r1, c1 = box
    for c in range(c0, c1 + 1):
        grid[r0][c] = 8
        grid[r1][c] = 8
    for r in range(r0, r1 + 1):
        grid[r][c0] = 8
        grid[r][c1] = 8


def _flip_cell(
    box: tuple[int, int, int, int], offset: tuple[int, int], flip_r: bool, flip_c: bool
) -> tuple[int, int]:
    r0, c0, r1, c1 = box
    rr, cc = offset
    height, width = r1 - r0 + 1, c1 - c0 + 1
    if flip_r:
        rr = height - 1 - rr
    if flip_c:
        cc = width - 1 - cc
    return r0 + rr, c0 + cc


def _draw_warped(
    grid: list[list[int]], box: tuple[int, int, int, int], rng: random.Random, swaps: int
) -> None:
    _draw_frame(grid, box)
    if swaps not in (1, 2):
        raise ValueError("warped component supports one or two swaps")
    flip_r = bool(rng.randrange(2))
    flip_c = bool(rng.randrange(2))
    if swaps == 1:
        missing_offsets = [(0, 1)]
        added_offsets = [(1, 1)]
    else:
        # This connected two-swap topology is authority-positive but is outside
        # the production generator's one-swap restriction.
        missing_offsets = [(0, 1), (box[2] - box[0], 1)]
        added_offsets = [(1, 1), (1, 2)]
    for offset in missing_offsets:
        r, c = _flip_cell(box, offset, flip_r, flip_c)
        grid[r][c] = 0
    for offset in added_offsets:
        r, c = _flip_cell(box, offset, flip_r, flip_c)
        grid[r][c] = 8


def _draw_malformed(
    grid: list[list[int]], box: tuple[int, int, int, int], rng: random.Random
) -> None:
    _draw_frame(grid, box)
    r0, c0, r1, c1 = box
    if rng.randrange(2):
        row = (r0 + r1) // 2
        for c in range(c0 + 1, c1):
            grid[row][c] = 8
    else:
        col = (c0 + c1) // 2
        for r in range(r0 + 1, r1):
            grid[r][col] = 8


def _palette_for(seed: int, namespace: str, index: int, size: int) -> list[int]:
    rng = _seed_rng(seed, namespace + ":palette", index)
    return rng.sample(list(_ALLOWED_PALETTE), size)


def _install_palette(grid: list[list[int]], colors: list[int]) -> None:
    for row, color in enumerate(colors):
        grid[row][0] = color


def _comprehensive_demo(seed: int, index: int) -> list[list[int]]:
    height = 20 + (index % 2)
    width = 26 + (index % 2)
    grid = _grid(height, width)
    _install_palette(grid, _palette_for(seed, "demo-comprehensive", index, 2))
    rng = _seed_rng(seed, "demo-comprehensive", index)
    outer = (0, 2, height - 1, 14 + (index % 2))
    middle = (2, 4, height - 3, 12 + (index % 2))
    inner = (4, 6, height - 5, 10 + (index % 2))
    _draw_frame(grid, outer)
    _draw_frame(grid, middle)
    _draw_warped(grid, inner, rng, swaps=2 if index % 2 == 0 else 1)
    malformed = (4, width - 8, height - 6, width - 2)
    _draw_malformed(grid, malformed, rng)
    return grid


def _warped_demo(seed: int, index: int) -> list[list[int]]:
    height, width = 17 + (index % 2), 21 + (index % 3)
    grid = _grid(height, width)
    _install_palette(grid, _palette_for(seed, "demo-warped", index, 3))
    rng = _seed_rng(seed, "demo-warped", index)
    _draw_frame(grid, (1, 2, height - 2, width - 3))
    _draw_warped(grid, (3, 4, height - 4, width - 5), rng, swaps=1 + index % 2)
    return grid


def _exhaustion_demo(seed: int, index: int) -> list[list[int]]:
    height, width = 19, 21
    grid = _grid(height, width)
    _install_palette(grid, _palette_for(seed, "demo-exhaustion", index, 2))
    _draw_frame(grid, (0, 2, height - 1, width - 2))
    _draw_frame(grid, (2, 4, height - 3, width - 4))
    _draw_frame(grid, (4, 6, height - 5, width - 6))
    return grid


def _malformed_demo(seed: int, index: int) -> list[list[int]]:
    height, width = 16 + index % 2, 22
    grid = _grid(height, width)
    _install_palette(grid, _palette_for(seed, "demo-malformed", index, 3))
    rng = _seed_rng(seed, "demo-malformed", index)
    _draw_frame(grid, (0, 2, height - 1, width - 2))
    _draw_malformed(grid, (3, 6, height - 4, width - 6), rng)
    return grid


def _double_chain_demo(seed: int, index: int) -> list[list[int]]:
    height, width = 18, 25
    grid = _grid(height, width)
    _install_palette(grid, _palette_for(seed, "demo-double", index, 3))
    rng = _seed_rng(seed, "demo-double", index)
    _draw_frame(grid, (0, 2, height - 1, 12))
    _draw_warped(grid, (3, 5, height - 4, 9), rng, swaps=1)
    _draw_frame(grid, (2, 16, height - 3, width - 1))
    return grid


def _build_demo(seed: int, index: int) -> list[list[int]]:
    builders = (
        _comprehensive_demo,
        _comprehensive_demo,
        _warped_demo,
        _exhaustion_demo,
        _malformed_demo,
        _double_chain_demo,
    )
    return builders[index](seed, index)


def _large_query(seed: int, index: int) -> list[list[int]]:
    grid = _grid(30, 30)
    _install_palette(grid, _palette_for(seed, "query-large", index, 3))
    rng = _seed_rng(seed, "query-large", index)
    _draw_frame(grid, (0, 2, 29, 18))
    _draw_frame(grid, (2, 4, 27, 16))
    _draw_warped(grid, (4, 6, 25, 14), rng, swaps=2)
    _draw_frame(grid, (3, 21, 16, 29))
    _draw_malformed(grid, (19, 22, 28, 29), rng)
    return grid


def _mixed_query(seed: int, index: int) -> list[list[int]]:
    grid = _grid(24, 27)
    _install_palette(grid, _palette_for(seed, "query-mixed", index, 2))
    rng = _seed_rng(seed, "query-mixed", index)
    _draw_frame(grid, (1, 2, 22, 16))
    _draw_warped(grid, (3, 4, 20, 14), rng, swaps=2)
    _draw_frame(grid, (5, 6, 18, 12))
    _draw_malformed(grid, (4, 19, 17, 26), rng)
    return grid


def _boundary_query(seed: int, index: int) -> list[list[int]]:
    grid = _grid(17, 20)
    _install_palette(grid, _palette_for(seed, "query-boundary", index, 3))
    rng = _seed_rng(seed, "query-boundary", index)
    _draw_frame(grid, (0, 2, 16, 19))
    _draw_warped(grid, (2, 4, 14, 17), rng, swaps=1)
    return grid


def _exhaustion_query(seed: int, index: int) -> list[list[int]]:
    grid = _grid(22, 25)
    _install_palette(grid, _palette_for(seed, "query-exhaustion", index, 2))
    _draw_frame(grid, (1, 2, 21, 24))
    _draw_frame(grid, (3, 4, 19, 22))
    _draw_frame(grid, (5, 6, 17, 20))
    return grid


def _build_query(seed: int, index: int) -> list[list[int]]:
    builders = (_large_query, _mixed_query, _boundary_query, _exhaustion_query)
    return builders[index](seed, index)


def _shape(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integers 0..9")
    return len(grid), width


def _components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = _shape(grid)
    seen: set[tuple[int, int]] = set()
    result: list[set[tuple[int, int]]] = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 8 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            component: set[tuple[int, int]] = set()
            while todo:
                rr, cc = todo.pop()
                component.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 8
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append(component)
    return result


def _bbox(component: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = list(component)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _perimeter(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _qualifies(component: set[tuple[int, int]]) -> bool:
    r0, c0, r1, c1 = _bbox(component)
    height, width = r1 - r0 + 1, c1 - c0 + 1
    return height >= 3 and width >= 3 and len(component) == 2 * (height + width) - 4


def _palette(grid: list[list[int]]) -> list[int]:
    return [row[0] for row in grid if row[0] not in (0, 8)]


def _boxes(
    grid: list[list[int]], qualifier: str = "authority"
) -> list[tuple[int, int, int, int]]:
    result = []
    for component in _components(grid):
        box = _bbox(component)
        height, width = box[2] - box[0] + 1, box[3] - box[1] + 1
        if qualifier == "authority" and _qualifies(component):
            result.append(box)
        elif qualifier == "all_bboxes" and height >= 3 and width >= 3:
            result.append(box)
        elif qualifier == "clean_only" and _qualifies(component) and component == _perimeter(box):
            result.append(box)
    return result


def _apply(
    grid: list[list[int]],
    palette_direction: str,
    *,
    qualifier: str = "authority",
    depth_cap: int | None = None,
    clamp_palette: bool = False,
    first_palette_only: bool = False,
) -> list[list[int]]:
    direction = _direction(palette_direction)
    _shape(grid)
    palette = _palette(grid)
    if direction == "inner_to_outer":
        palette = list(reversed(palette))
    boxes = _boxes(grid, qualifier)
    output = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            depth = sum(r0 < r < r1 and c0 < c < c1 for r0, c0, r1, c1 in boxes)
            if depth_cap is not None:
                depth = min(depth, depth_cap)
            if first_palette_only and depth > 0:
                depth = 1
            if 0 < depth <= len(palette):
                output[r][c] = palette[depth - 1]
            elif depth > len(palette) and palette and clamp_palette:
                output[r][c] = palette[-1]
    return output


def python_output(grid: list[list[int]], palette_direction: Any) -> list[list[int]]:
    return _apply(grid, _direction(palette_direction))


def scene_facts(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _shape(grid)
    components = _components(grid)
    qualifying = [component for component in components if _qualifies(component)]
    malformed = [component for component in components if not _qualifies(component)]
    warped = [
        component
        for component in qualifying
        if component != _perimeter(_bbox(component))
    ]
    boxes = [_bbox(component) for component in qualifying]
    max_depth = 0
    exhaustion = 0
    palette_size = len(_palette(grid))
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            depth = sum(r0 < r < r1 and c0 < c < c1 for r0, c0, r1, c1 in boxes)
            max_depth = max(max_depth, depth)
            if depth > palette_size:
                exhaustion += 1
    body = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if c >= 2 and value != 0
    ]
    body_bbox = list(_bbox(body)) if body else None
    return {
        "shape": [height, width],
        "palette": _palette(grid),
        "color8_cells": sum(cell == 8 for row in grid for cell in row),
        "qualifying_components": len(qualifying),
        "warped_qualifying_components": len(warped),
        "malformed_components": len(malformed),
        "max_depth": max_depth,
        "palette_exhaustion_cells": exhaustion,
        "nonzero_body_bbox": body_bbox,
    }


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _rival_outputs(
    grid: list[list[int]], selected: str
) -> dict[str, list[list[int]]]:
    opposite = "inner_to_outer" if selected == "outer_to_inner" else "outer_to_inner"
    return {
        "opposite_palette_direction": _apply(grid, opposite),
        "outermost_only": _apply(grid, selected, depth_cap=1),
        "all_color8_bboxes": _apply(grid, selected, qualifier="all_bboxes"),
        "clean_outline_only": _apply(grid, selected, qualifier="clean_only"),
        "clamp_palette": _apply(grid, selected, clamp_palette=True),
        "first_palette_only": _apply(grid, selected, first_palette_only=True),
    }


def audit_episode(episode: dict[str, Any]) -> dict[str, Any]:
    selected = _direction(episode.get("settings", {}).get("palette_direction"))
    demos = episode.get("train")
    queries = episode.get("test")
    if not isinstance(demos, list) or not isinstance(queries, list):
        raise ValueError("episode must have train and test lists")
    names = sorted(_rival_outputs(demos[0]["input"], selected))
    survivors = []
    refutations: dict[str, list[int]] = {}
    for name in names:
        mismatches = [
            index
            for index, pair in enumerate(demos)
            if _rival_outputs(pair["input"], selected)[name] != pair["output"]
        ]
        refutations[name] = mismatches
        if not mismatches:
            survivors.append(name)
    reports = []
    for index, pair in enumerate(queries):
        changing = [
            name
            for name in survivors
            if _rival_outputs(pair["input"], selected)[name] != pair["output"]
        ]
        reports.append(
            {
                "query_index": index,
                "input_sha256": _grid_hash(pair["input"]),
                "surviving_rivals_that_change_query": changing,
                "status": "identified" if not changing else "ambiguous",
            }
        )
    return {
        "schema": "nested-palette-parametric-self-audit-v1",
        "selected": selected,
        "declared_rivals": names,
        "refuting_demo_indices": refutations,
        "surviving_rivals": survivors,
        "queries": reports,
        "limits": "Finite declared-rival audit; it does not prove uniqueness against arbitrary programs.",
    }


def _inputs(seed: int, demos: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demo_inputs = [_build_demo(seed, index) for index in range(demos)]
    query_inputs = [_build_query(seed, index) for index in range(QUERY_COUNT)]
    all_inputs = demo_inputs + query_inputs
    hashes = [_grid_hash(grid) for grid in all_inputs]
    if len(hashes) != len(set(hashes)):
        raise RuntimeError("deterministic sampler produced duplicate inputs")
    return demo_inputs, query_inputs


def generate_episode(
    seed: Any,
    *,
    palette_direction: Any,
    demos: Any = 3,
    queries: Any = 4,
) -> dict[str, Any]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    direction = _direction(palette_direction)
    demos, queries = _counts(demos, queries)
    demo_inputs, query_inputs = _inputs(seed, demos)
    train = [
        {"input": deepcopy(grid), "output": python_output(grid, direction)}
        for grid in demo_inputs
    ]
    test = [
        {"input": deepcopy(grid), "output": python_output(grid, direction)}
        for grid in query_inputs
    ]
    episode = {
        "schema": "nested-palette-direction-parametric-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {"palette_direction": direction},
        "demo_count": demos,
        "query_count": queries,
        "train": train,
        "test": test,
        "program_solution": program_for(direction),
        "program_sha256": hashlib.sha256(program_for(direction).encode()).hexdigest(),
        "scene_facts": {
            "train": [scene_facts(pair["input"]) for pair in train],
            "test": [scene_facts(pair["input"]) for pair in test],
        },
    }
    validate_episode(episode)
    return episode


def validate_episode(episode: dict[str, Any]) -> None:
    if not isinstance(episode, dict) or episode.get("task_id") != TASK_ID:
        raise ValueError("episode task identity mismatch")
    seed = _integer("seed", episode.get("seed"), 0, 2**63 - 1)
    settings = episode.get("settings")
    if not isinstance(settings, dict) or set(settings) != {"palette_direction"}:
        raise ValueError("episode settings must name exactly palette_direction")
    direction = _direction(settings["palette_direction"])
    demos, queries = _counts(episode.get("demo_count"), episode.get("query_count"))
    if episode.get("program_solution") != program_for(direction):
        raise ValueError("episode program differs from its setting")
    if episode.get("program_sha256") != hashlib.sha256(program_for(direction).encode()).hexdigest():
        raise ValueError("episode program hash differs")
    if len(episode.get("train", [])) != demos or len(episode.get("test", [])) != queries:
        raise ValueError("episode pair counts differ")
    expected_demo_inputs, expected_query_inputs = _inputs(seed, demos)
    pairs = episode["train"] + episode["test"]
    expected_inputs = expected_demo_inputs + expected_query_inputs
    if [pair.get("input") for pair in pairs] != expected_inputs:
        raise ValueError("episode inputs differ from deterministic sampler")
    for pair in pairs:
        _shape(pair.get("input"))
        _shape(pair.get("output"))
        if pair["output"] != python_output(pair["input"], direction):
            raise ValueError("episode private label differs from Python oracle")
    audit = audit_episode(episode)
    if audit["surviving_rivals"] or any(q["status"] != "identified" for q in audit["queries"]):
        raise ValueError("visible demonstrations do not identify the supported lesson")


def public_single_query_payload(episode: dict[str, Any]) -> dict[str, Any]:
    validate_episode(episode)
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][0]["input"])}],
    }


def public_turn_payloads(episode: dict[str, Any]) -> list[dict[str, Any]]:
    validate_episode(episode)
    return [
        {
            "train": deepcopy(episode["train"]),
            "test": [{"input": deepcopy(pair["input"])}],
        }
        for pair in episode["test"]
    ]


def public_bytes(payload: dict[str, Any]) -> bytes:
    public = {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in payload["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in payload["test"]],
    }
    return (
        json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def clamped_depth_counterfactual_program(direction: Any) -> str:
    source = program_for(_direction(direction))
    needle = """          (let ((depth (count-where (lambda (fr)
                                      (and (> r (obj-r1 fr)) (< r (obj-r2 fr))
                                           (> c (obj-c1 fr)) (< c (obj-c2 fr))))
                                    frames)))"""
    replacement = """          (let ((depth (min 1 (count-where (lambda (fr)
                                      (and (> r (obj-r1 fr)) (< r (obj-r2 fr))
                                           (> c (obj-c1 fr)) (< c (obj-c2 fr))))
                                    frames))))"""
    if source.count(needle) != 1:
        raise RuntimeError("canonical depth block changed")
    return source.replace(needle, replacement, 1)

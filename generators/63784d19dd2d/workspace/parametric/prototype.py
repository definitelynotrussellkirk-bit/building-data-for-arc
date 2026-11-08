"""Native parametric family for 63784d19dd2d.

The canonical/default setting preserves the selected Racket source byte-for-byte:
infer the unique whole-panel transform mapping A to B and apply it to C.

The alternate setting retains that inference and then marks with red (2) only
those non-background cells of transformed C whose output coordinates are also
occupied in panel B.  This is a genuine sequential dependency: the overlap mask
cannot be known until the input-dependent A->B transform has placed C.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable


TASK_ID = "63784d19dd2d"
OVERLAP_MODES = ("transform_only", "mark_b_overlap")
DEFAULT_MODE = "transform_only"
MARK_COLOR = 2
INPUT_PALETTE = (1, 3, 4, 6, 7, 8, 9)
TRANSFORMS = (1, 2, 3, 4, 5)
NON_IDENTITY_TRANSFORMS = (2, 3, 4, 5)
CANDIDATE_RULES = (
    "transform_only",
    "mark_b_overlap",
    "mark_a_overlap",
    "mark_c_overlap",
    "mark_b_nonoverlap",
    "mark_all",
    "premark_b_then_transform",
    "identity_then_mark_b",
)

HERE = Path(__file__).resolve().parent
CANONICAL_PATH = HERE / "canonical.rkt"
ALTERNATE_PATH = HERE / "mark_b_overlap.rkt"

# The first two profiles are constructive teaching examples. Additional demos
# and queries are prefix-stable.  n=9 gives the largest lawful ARC input under
# N x (3N+2): 9 x 29; exact 30x30 cannot retain three equal square panels and
# two full-height separators.
TEACHING_PROFILES = (
    {"panel_n": 7, "transform": 2, "boundary": False, "dense": False},
    {"panel_n": 8, "transform": 5, "boundary": False, "dense": False},
)
EXTRA_DEMO_PROFILES = (
    {"panel_n": 5, "transform": 3, "boundary": False, "dense": False},
    {"panel_n": 6, "transform": 4, "boundary": False, "dense": False},
    {"panel_n": 9, "transform": 2, "boundary": True, "dense": True},
    {"panel_n": 7, "transform": 5, "boundary": False, "dense": True},
)
QUERY_PROFILES = (
    {"panel_n": 3, "transform": 4, "boundary": True, "dense": False},
    {"panel_n": 5, "transform": 2, "boundary": False, "dense": False},
    {"panel_n": 7, "transform": 3, "boundary": False, "dense": True},
    {"panel_n": 9, "transform": 5, "boundary": True, "dense": True},
)


def _integer(name: str, value: Any, lo: int, hi: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be in {lo}..{hi}, got {value}")
    return value


def _mode(value: Any) -> str:
    if type(value) is not str:
        raise TypeError("overlap_mode must be a string")
    if value not in OVERLAP_MODES:
        raise ValueError(f"overlap_mode must be one of {OVERLAP_MODES}, got {value!r}")
    return value


def _rng(seed: int, stream: str, index: int = 0) -> random.Random:
    payload = f"63784d19dd2d-overlap-v1:{seed}:{stream}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _neighbors(cell: tuple[int, int], n: int) -> list[tuple[int, int]]:
    r, c = cell
    return [
        (nr, nc)
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        if 0 <= nr < n and 0 <= nc < n
    ]


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    pending = [next(iter(cells))]
    seen = {pending[0]}
    while pending:
        cell = pending.pop()
        for neighbor in _neighbors(cell, 10**9):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                pending.append(neighbor)
    return seen == cells


def _xform_cell(cell: tuple[int, int], code: int, n: int) -> tuple[int, int]:
    r, c = cell
    if code == 1:
        return r, c
    if code == 2:
        return c, n - 1 - r
    if code == 3:
        return n - 1 - r, n - 1 - c
    if code == 4:
        return n - 1 - r, c
    if code == 5:
        return r, n - 1 - c
    raise ValueError(f"unknown transform code {code}")


def _inverse_xform_cell(cell: tuple[int, int], code: int, n: int) -> tuple[int, int]:
    r, c = cell
    if code == 2:
        return n - 1 - c, r
    return _xform_cell(cell, code, n)


def _xform_cells(cells: Iterable[tuple[int, int]], code: int, n: int) -> set[tuple[int, int]]:
    return {_xform_cell(cell, code, n) for cell in cells}


def _inverse_xform_cells(cells: Iterable[tuple[int, int]], code: int, n: int) -> set[tuple[int, int]]:
    return {_inverse_xform_cell(cell, code, n) for cell in cells}


def _xform_grid(grid: list[list[int]], code: int) -> list[list[int]]:
    n = len(grid)
    if n == 0 or any(type(row) is not list or len(row) != n for row in grid):
        raise ValueError("whole-panel transform requires a nonempty square grid")
    output = [[0] * n for _ in range(n)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            nr, nc = _xform_cell((r, c), code, n)
            output[nr][nc] = value
    return output


def _grow_shape(
    rng: random.Random,
    n: int,
    size: int,
    initial: Iterable[tuple[int, int]],
) -> set[tuple[int, int]]:
    cells = set(initial)
    if not cells or not _connected(cells):
        raise ValueError("initial shape must be nonempty and connected")
    while len(cells) < size:
        frontier = sorted({neighbor for cell in cells for neighbor in _neighbors(cell, n)} - cells)
        if not frontier:
            raise RuntimeError("shape frontier exhausted")
        cells.add(rng.choice(frontier))
    return cells


def _random_shape(
    rng: random.Random,
    n: int,
    size: int,
    *,
    boundary: bool = False,
) -> set[tuple[int, int]]:
    if boundary:
        side = rng.randrange(4)
        position = rng.randrange(n)
        start = ((position, 0), (0, position), (position, n - 1), (n - 1, position))[side]
    else:
        start = (rng.randrange(n), rng.randrange(n))
    return _grow_shape(rng, n, size, [start])


def _panel(grid: list[list[int]], left: int, n: int) -> list[list[int]]:
    return [row[left:left + n] for row in grid]


def _support(panel: list[list[int]]) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0}


def _palette(panel: list[list[int]]) -> set[int]:
    return {value for row in panel for value in row if value != 0}


def analyze_input(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return {"errors": ["grid must be a nonempty list of rows"]}
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be exact integer ARC colors 0..9")
    n = len(grid)
    separators = [c for c in range(width) if all(grid[r][c] == 5 for r in range(n))]
    if width != 3 * n + 2 or separators != [n, 2 * n + 1]:
        errors.append(
            f"expected N x (3N+2) with separators {[n, 2 * n + 1]}, got {n}x{width} and {separators}"
        )
        return {"errors": errors, "panel_n": n, "width": width, "separators": separators}
    if not 3 <= n <= 9:
        errors.append(f"panel_n must be in 3..9, got {n}")
    panels = (
        _panel(grid, 0, n),
        _panel(grid, n + 1, n),
        _panel(grid, 2 * n + 2, n),
    )
    names = ("A", "B", "C")
    supports = tuple(_support(panel) for panel in panels)
    palettes = tuple(_palette(panel) for panel in panels)
    for name, support, palette in zip(names, supports, palettes):
        if len(support) < 3:
            errors.append(f"panel {name} must contain at least three cells")
        if len(palette) != 1:
            errors.append(f"panel {name} must use one nonzero color, got {sorted(palette)}")
        if support and not _connected(support):
            errors.append(f"panel {name} must be four-connected")
    if len(palettes[0]) == len(palettes[1]) == 1 and palettes[0] != palettes[1]:
        errors.append("A and B must use the same color")
    if len(palettes[0]) == len(palettes[2]) == 1 and palettes[0] == palettes[2]:
        errors.append("C must use a different color")
    matches = [code for code in TRANSFORMS if _xform_grid(panels[0], code) == panels[1]]
    if len(matches) != 1 or matches == [1]:
        errors.append(f"A->B transform must be unique and non-identity, got {matches}")
    transform = matches[0] if len(matches) == 1 else None
    transformed = _xform_grid(panels[2], transform) if transform is not None else None
    transformed_support = _support(transformed) if transformed is not None else set()
    return {
        "errors": sorted(set(errors)),
        "panel_n": n,
        "width": width,
        "separators": separators,
        "panels": panels,
        "a_support": supports[0],
        "b_support": supports[1],
        "c_support": supports[2],
        "transform_matches": matches,
        "transform": transform,
        "transformed_c": transformed,
        "transformed_c_support": transformed_support,
        "transformed_c_size": len(transformed_support),
        "b_overlap": transformed_support & supports[1],
        "b_overlap_count": len(transformed_support & supports[1]),
    }


def _paint_overlap(
    source: list[list[int]],
    reference: list[list[int]],
    *,
    overlap: bool,
) -> list[list[int]]:
    return [
        [
            MARK_COLOR
            if value != 0 and ((reference[r][c] != 0) == overlap)
            else value
            for c, value in enumerate(row)
        ]
        for r, row in enumerate(source)
    ]


def _paint_all(source: list[list[int]]) -> list[list[int]]:
    return [[MARK_COLOR if value != 0 else 0 for value in row] for row in source]


def solve_candidate(grid: list[list[int]], candidate: str) -> list[list[int]]:
    if candidate not in CANDIDATE_RULES:
        raise ValueError(f"unknown candidate rule {candidate!r}")
    facts = analyze_input(grid)
    if facts["errors"]:
        raise ValueError("invalid input: " + "; ".join(facts["errors"]))
    a, b, c = facts["panels"]
    transformed = facts["transformed_c"]
    code = facts["transform"]
    if candidate == "transform_only":
        return copy.deepcopy(transformed)
    if candidate == "mark_b_overlap":
        return _paint_overlap(transformed, b, overlap=True)
    if candidate == "mark_a_overlap":
        return _paint_overlap(transformed, a, overlap=True)
    if candidate == "mark_c_overlap":
        return _paint_overlap(transformed, c, overlap=True)
    if candidate == "mark_b_nonoverlap":
        return _paint_overlap(transformed, b, overlap=False)
    if candidate == "mark_all":
        return _paint_all(transformed)
    if candidate == "premark_b_then_transform":
        return _xform_grid(_paint_overlap(c, b, overlap=True), code)
    if candidate == "identity_then_mark_b":
        return _paint_overlap(c, b, overlap=True)
    raise AssertionError(candidate)


def solve(grid: list[list[int]], mode: Any) -> list[list[int]]:
    return solve_candidate(grid, _mode(mode))


def _common_variant_program(final_expression: str) -> str:
    return f'''(rule!
  (let ((seps (filter (lambda (c) (all? (lambda (r) (= (at g r c) 5)) (range 0 (rows g)))) (range 0 (cols g)))))
    (define (panel start end) (subgrid g 0 start (- (rows g) 1) (- end 1)))
    (define A (panel 0 (first seps)))
    (define B (panel (+ (first seps) 1) (second seps)))
    (define C (panel (+ (second seps) 1) (cols g)))
    (define (xform grid code)
      (cond [(= code 1) grid]
            [(= code 2) (rotate-cw grid)]
            [(= code 3) (rotate-180 grid)]
            [(= code 4) (flip-ud grid)]
            [else (flip-lr grid)]))
    (define code (first (filter (lambda (k) (equal? (xform A k) B)) (list 1 2 3 4 5))))
    (define transformed-c (xform C code))
    (define MARK-COLOR 2)
    (define (overlap-with-b? r c)
      (and (not (= (at transformed-c r c) 0))
           (not (= (at B r c) 0))))
    (define (paint-by-reference source reference overlap?)
      (build-list
       (rows source)
       (lambda (r)
         (build-list
          (cols source)
          (lambda (c)
            (let ((value (at source r c))
                  (occupied? (not (= (at reference r c) 0))))
              (if (and (not (= value 0)) (equal? occupied? overlap?))
                  MARK-COLOR
                  value)))))))
    (define (paint-all source)
      (build-list
       (rows source)
       (lambda (r)
         (build-list
          (cols source)
          (lambda (c)
            (if (= (at source r c) 0) 0 MARK-COLOR))))))
    {final_expression}))'''


def _generated_program(candidate: str) -> str:
    expressions = {
        "mark_b_overlap": "(paint-by-reference transformed-c B #t)",
        "mark_a_overlap": "(paint-by-reference transformed-c A #t)",
        "mark_c_overlap": "(paint-by-reference transformed-c C #t)",
        "mark_b_nonoverlap": "(paint-by-reference transformed-c B #f)",
        "mark_all": "(paint-all transformed-c)",
        "premark_b_then_transform": "(xform (paint-by-reference C B #t) code)",
        "identity_then_mark_b": "(paint-by-reference C B #t)",
    }
    if candidate not in expressions:
        raise ValueError(candidate)
    return _common_variant_program(expressions[candidate])


def program_for(mode: Any) -> str:
    mode = _mode(mode)
    path = CANONICAL_PATH if mode == "transform_only" else ALTERNATE_PATH
    return path.read_text(encoding="utf-8")


def candidate_program(candidate: str) -> str:
    if candidate == "transform_only":
        return program_for(candidate)
    if candidate == "mark_b_overlap":
        return program_for(candidate)
    if candidate not in CANDIDATE_RULES:
        raise ValueError(f"unknown candidate rule {candidate!r}")
    return _generated_program(candidate)


def _freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _selected_outputs_identifiable(grid: list[list[int]]) -> bool:
    outputs = {name: _freeze(solve_candidate(grid, name)) for name in CANDIDATE_RULES}
    return all(
        outputs[selected] != outputs[candidate]
        for selected in OVERLAP_MODES
        for candidate in CANDIDATE_RULES
        if candidate != selected
    )


def _scene(seed: int, stream: str, index: int, profile: dict[str, Any]) -> list[list[int]]:
    n = profile["panel_n"]
    code = profile["transform"]
    boundary = bool(profile["boundary"])
    dense = bool(profile["dense"])
    rng = _rng(seed, stream, index)
    colors = rng.sample(INPUT_PALETTE, 2)
    for _ in range(1200):
        max_cells = max(4, n * n - 3)
        base = n + (3 if dense else 1)
        a_size = min(max_cells, max(3, base + rng.randrange(max(1, n // 2 + 1))))
        a = _random_shape(rng, n, a_size, boundary=boundary)
        b = _xform_cells(a, code, n)
        matches = [candidate for candidate in TRANSFORMS if _xform_cells(a, candidate, n) == b]
        if matches != [code]:
            continue

        triples = []
        for pivot in sorted(b):
            inside = [cell for cell in _neighbors(pivot, n) if cell in b]
            outside = [cell for cell in _neighbors(pivot, n) if cell not in b]
            for inside_cell in inside:
                for outside_cell in outside:
                    triples.append((pivot, inside_cell, outside_cell))
        if not triples:
            continue
        initial = rng.choice(triples)
        d_size = min(max_cells, max(5, n + (4 if dense else 2) + rng.randrange(max(1, n // 2 + 1))))
        d = _grow_shape(rng, n, d_size, initial)
        overlap = d & b
        if not 2 <= len(overlap) <= len(d) - 2:
            continue
        c = _inverse_xform_cells(d, code, n)
        if d == c or c in (a, b) or d in (a, b):
            continue
        if not (_connected(a) and _connected(b) and _connected(c) and _connected(d)):
            continue
        if boundary and not any(col in (0, n - 1) for _, col in a | c):
            continue

        grid = [[0] * (3 * n + 2) for _ in range(n)]
        for r in range(n):
            grid[r][n] = 5
            grid[r][2 * n + 1] = 5
        color_a, color_c = colors
        for r, col in a:
            grid[r][col] = color_a
        for r, col in b:
            grid[r][n + 1 + col] = color_a
        for r, col in c:
            grid[r][2 * n + 2 + col] = color_c
        facts = analyze_input(grid)
        if facts["errors"]:
            continue
        if not _selected_outputs_identifiable(grid):
            continue
        return grid
    raise RuntimeError(f"could not construct scene for seed={seed} stream={stream} index={index} profile={profile}")


def episode_inputs(seed: Any, *, demos: Any = 3, queries: Any = 4) -> dict[str, list[list[list[int]]]]:
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 2, 6)
    queries = _integer("queries", queries, 1, 4)
    training_profiles = list(TEACHING_PROFILES) + list(EXTRA_DEMO_PROFILES)
    train = [_scene(seed, "train", index, training_profiles[index]) for index in range(demos)]
    test = [_scene(seed, "test", index, QUERY_PROFILES[index]) for index in range(queries)]
    frozen = [_freeze(grid) for grid in train + test]
    if len(frozen) != len(set(frozen)):
        raise RuntimeError("episode sampler repeated an input")
    return {"train": train, "test": test}


def generate_episode(
    seed: Any,
    mode: Any,
    *,
    demos: Any = 3,
    queries: Any = 4,
) -> dict[str, Any]:
    mode = _mode(mode)
    inputs = episode_inputs(seed, demos=demos, queries=queries)
    return {
        "train": [{"input": grid, "output": solve(grid, mode)} for grid in inputs["train"]],
        "test": [{"input": grid, "output": solve(grid, mode)} for grid in inputs["test"]],
        "program_solution": program_for(mode),
        "settings": {"overlap_mode": mode},
        "seed": seed,
    }


def public_view(episode: dict[str, Any], query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise TypeError("episode must contain train and test lists")
    query_index = _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }


def public_bytes(public: dict[str, Any]) -> bytes:
    return (
        json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def public_id(public: dict[str, Any]) -> str:
    return hashlib.sha256(public_bytes(public)).hexdigest()


def write_public(episode: dict[str, Any], output: str | Path, query_index: int = 0) -> Path:
    public = public_view(episode, query_index)
    content = public_bytes(public)
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{hashlib.sha256(content).hexdigest()}.json"
    path.write_bytes(content)
    return path

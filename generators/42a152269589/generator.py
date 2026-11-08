"""Generator for ARC task 42a152269589: pack polyominoes into a 3x4.

The input contains three to five separated, single-colour polyominoes whose
areas sum to 12.  The authoritative rule sorts pieces by descending area then
ascending colour and backtracks into a 3x4 rectangle, first without transforms,
then with rotations, then with rotations and reflections.

A three-slot schedule deliberately teaches all three solver depths instead of
only emitting easy translation cases:

* ``translation_anchor`` — the input orientations already tile 3x4;
* ``rotation_required`` — translation fails but rotations suffice;
* ``reflection_and_repeat`` — rotations fail, a reflection is required, and
  at least one colour occurs in more than one disconnected component.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Cell = tuple[int, int]
Shape = tuple[Cell, ...]

GENERATOR_ID = "42a152269589"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "2578a5c05f72"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "A 10x(10..13) zero-background grid with 3..5 separated coloured "
    "polyominoes totalling 12 cells.  Scheduled examples require, in turn, "
    "translation-only packing, rotation, and reflection with repeated colours."
)
INVARIANTS = [
    "background is 0",
    "there are 3..5 four-connected single-colour components",
    "the components contain exactly 12 nonzero cells in exactly three colours",
    "the authoritative rotation/reflection backtracker packs them into 3x4",
]

# grid_h is intentionally fixed: every public input is ten rows high.  It is
# retained as a named input dimension for callers, but marked diagnostic so the
# boundary-matrix linter does not pretend a one-value domain is a variable axis.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "10 (canonical fixed height)",
        "valid": "10..10",
        "probe": "diagnostic",
    },
    "grid_w": {
        "type": "int",
        "default": "keyed 10..13",
        "valid": "10..13",
    },
    "n_pieces": {
        "type": "int",
        "default": "keyed 3..5; reflection profile uses 4..5",
        "valid": "3..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "translation_anchor",
    "rotation_required",
    "reflection_and_repeat",
)

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ZERO_OUTPUT: Grid = [[0, 0, 0, 0] for _ in range(3)]


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the semantic curriculum slot for a draw.

    The schedule depends only on ``sample_index`` so every consecutive
    three-example lesson contains all solver depths regardless of seed/band.
    """

    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _normalize(cells: Iterable[Cell]) -> Shape:
    cells = tuple((int(r), int(c)) for r, c in cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate_cw(cells: Iterable[Cell]) -> Shape:
    return _normalize((c, -r) for r, c in cells)


def _vflip(cells: Iterable[Cell]) -> Shape:
    return _normalize((-r, c) for r, c in cells)


def _rotate_n(cells: Iterable[Cell], turns: int) -> Shape:
    out = _normalize(cells)
    for _ in range(turns % 4):
        out = _rotate_cw(out)
    return out


def _orientations(cells: Iterable[Cell], *, allow_rot: bool, allow_refl: bool) -> list[Shape]:
    """Mirror the authoritative Racket orientation ordering exactly."""

    original = _normalize(cells)
    result: list[Shape] = [original]
    if allow_rot:
        acc = [original]
        cur = original
        for _ in range(3):
            cur = _rotate_cw(cur)
            if cur not in acc:
                acc.insert(0, cur)  # Racket add-unique uses cons.
        result = list(reversed(acc))

    if allow_refl:
        cur = _vflip(original)
        # The Racket reflection loop does not reverse its cons-built list, so
        # reflected orientations are tried before the rotation-only list.
        for _ in range(4):
            normalized = _normalize(cur)
            if normalized not in result:
                result.insert(0, normalized)
            cur = _rotate_cw(cur)
    return result


def _components(grid: Grid) -> list[tuple[int, Shape]]:
    """Return row-major four-connected components, separated by colour."""

    h = len(grid)
    w = len(grid[0]) if h else 0
    seen: set[Cell] = set()
    out: list[tuple[int, Shape]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[Cell] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _CARD:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((int(color), _normalize(cells)))
    return out


def _try_pack(grid: Grid, *, allow_rot: bool, allow_refl: bool) -> Grid | None:
    """Backtrack into 3x4 using the canonical sort and search order."""

    pieces = [
        (color, _orientations(shape, allow_rot=allow_rot, allow_refl=allow_refl))
        for color, shape in _components(grid)
    ]
    pieces.sort(key=lambda item: (-len(item[1][0]), item[0]))
    board = [[0, 0, 0, 0] for _ in range(3)]

    def place(index: int) -> bool:
        if index >= len(pieces):
            return all(value != 0 for row in board for value in row)
        color, orientations = pieces[index]
        for shape in orientations:
            for top in range(3):
                for left in range(4):
                    target = [(top + dr, left + dc) for dr, dc in shape]
                    if not all(
                        0 <= r < 3 and 0 <= c < 4 and board[r][c] == 0
                        for r, c in target
                    ):
                        continue
                    for r, c in target:
                        board[r][c] = color
                    if place(index + 1):
                        return True
                    for r, c in target:
                        board[r][c] = 0
        return False

    return [row[:] for row in board] if place(0) else None


def _translation_only_pack(grid: Grid) -> Grid | None:
    return _try_pack(grid, allow_rot=False, allow_refl=False)


def _rotation_only_pack(grid: Grid) -> Grid | None:
    return _try_pack(grid, allow_rot=True, allow_refl=False)


def rule_mirror(grid: Grid) -> Grid | None:
    """Pure-Python mirror of the selected canonical Racket rule."""

    return (
        _translation_only_pack(grid)
        or _rotation_only_pack(grid)
        or _try_pack(grid, allow_rot=True, allow_refl=True)
    )


def _partition_3x4(rng: Any, n_pieces: int) -> list[Shape]:
    """Randomly grow a connected partition of the twelve output cells."""

    cells = [(r, c) for r in range(3) for c in range(4)]
    seeds = rng.sample(cells, n_pieces)
    regions: list[list[Cell]] = [[seed] for seed in seeds]
    owner = {seed: index for index, seed in enumerate(seeds)}
    remaining = set(cells) - set(seeds)
    while remaining:
        frontier: list[tuple[int, Cell]] = []
        for cell in sorted(remaining):
            r, c = cell
            adjacent = {
                owner[(r + dr, c + dc)]
                for dr, dc in _CARD
                if (r + dr, c + dc) in owner
            }
            frontier.extend((index, cell) for index in sorted(adjacent))
        if not frontier:  # impossible on a connected 3x4 grid, kept loud.
            raise RuntimeError("partition growth lost contact with remaining cells")
        index, cell = rng.choice(frontier)
        regions[index].append(cell)
        owner[cell] = index
        remaining.remove(cell)
    return [_normalize(region) for region in regions]


_ROTATION_REQUIRED: dict[int, tuple[Shape, ...]] = {
    3: (
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    ),
    4: (
        ((0, 0), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)),
        ((0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0),),
        ((0, 0),),
    ),
    5: (
        ((0, 0), (1, 0)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0),),
        ((0, 0),),
        ((0, 0), (0, 1), (0, 2), (0, 3)),
    ),
}

_REFLECTION_REQUIRED: dict[int, tuple[Shape, ...]] = {
    3: (
        ((0, 0), (0, 1)),
        ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (3, 0), (3, 1)),
        ((0, 0),),
        ((0, 0),),
    ),
    5: (
        ((0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0),),
        ((0, 1), (1, 0), (1, 1), (1, 2), (1, 3)),
        ((0, 0),),
        ((0, 0),),
    ),
}


def _fits_with_moat(board: Grid, top: int, left: int, shape: Shape) -> bool:
    h, w = len(board), len(board[0])
    for dr, dc in shape:
        r, c = top + dr, left + dc
        if not (0 <= r < h and 0 <= c < w):
            return False
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if board[rr][cc] != 0:
                    return False
    return True


def _scatter(shapes: Sequence[Shape], colors: Sequence[int], h: int, w: int, rng: Any) -> Grid:
    """Place every shape with a one-cell Chebyshev moat via backtracking."""

    board = full_grid(h, w, 0)
    order = sorted(
        range(len(shapes)),
        key=lambda index: (
            -len(shapes[index]),
            -(max(r for r, _ in shapes[index]) + 1),
            -(max(c for _, c in shapes[index]) + 1),
            index,
        ),
    )
    placements: dict[int, list[tuple[int, int]]] = {}
    for index, shape in enumerate(shapes):
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        candidates = [
            (top, left)
            for top in range(h - sh + 1)
            for left in range(w - sw + 1)
        ]
        rng.shuffle(candidates)
        placements[index] = candidates

    def visit(depth: int) -> bool:
        if depth == len(order):
            return True
        index = order[depth]
        shape = shapes[index]
        color = colors[index]
        for top, left in placements[index]:
            if not _fits_with_moat(board, top, left, shape):
                continue
            painted = [(top + dr, left + dc) for dr, dc in shape]
            for r, c in painted:
                board[r][c] = color
            if visit(depth + 1):
                return True
            for r, c in painted:
                board[r][c] = 0
        return False

    if not visit(0):
        raise ValueError(f"could not scatter {len(shapes)} pieces on {h}x{w}")
    return board


def _piece_colors(rng: Any, n_pieces: int) -> list[int]:
    palette = rng.sample(list(range(1, 10)), 3)
    colors = [palette[index % 3] for index in range(n_pieces)]
    rng.shuffle(colors)
    return colors


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> Grid:
    if type(seed) is not int:
        raise TypeError("seed must be an integer, not bool or a coerced scalar")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer, not bool or a coerced scalar")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty is not None and (
        type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")
    ):
        raise ValueError("difficulty must be None, easy, medium, or hard")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    h = ctx.draw_int_strict("grid_h", 10, 10)
    w = ctx.draw_int_strict("grid_w", 10, 13)
    if "n_pieces" in overrides and overrides["n_pieces"] is not None:
        n_pieces = ctx.draw_int_strict("n_pieces", 3, 5)
    elif profile == "reflection_and_repeat":
        n_pieces = ctx.draw_int_strict("n_pieces", 4, 5)
    else:
        n_pieces = ctx.draw_int_strict("n_pieces", 3, 5)

    band_salt = str(difficulty) if difficulty is not None else "none"
    layout_rng = ctx.draw_rng(f"layout:{band_salt}")
    color_rng = ctx.draw_rng(f"colors:{band_salt}")

    # Retry only the random partition profile; the adversarial templates are
    # fixed, independently verified witnesses.
    attempts = 24 if profile == "translation_anchor" else 1
    last_error: Exception | None = None
    for _ in range(attempts):
        if profile == "translation_anchor":
            shapes = _partition_3x4(layout_rng, n_pieces)
        elif profile == "rotation_required":
            shapes = [_normalize(shape) for shape in _ROTATION_REQUIRED[n_pieces]]
        else:
            # Independent rotations preserve each piece's rotation orbit and
            # therefore preserve the requirement for at least one reflection.
            shapes = [
                _rotate_n(shape, layout_rng.randrange(4))
                for shape in _REFLECTION_REQUIRED[n_pieces]
            ]
        colors = _piece_colors(color_rng, n_pieces)
        try:
            grid = _scatter(shapes, colors, h, w, layout_rng)
        except ValueError as exc:
            last_error = exc
            continue

        # Fail at the source if a template or future edit violates its lesson.
        if profile == "translation_anchor" and _translation_only_pack(grid) is None:
            last_error = ValueError("translation profile lost its translation witness")
            continue
        if profile == "rotation_required" and not (
            _translation_only_pack(grid) is None
            and _rotation_only_pack(grid) is not None
        ):
            last_error = ValueError("rotation profile no longer isolates rotation")
            continue
        needs_repeat = not (
            "n_pieces" in overrides
            and overrides["n_pieces"] is not None
            and n_pieces == 3
        )
        if profile == "reflection_and_repeat" and not (
            _rotation_only_pack(grid) is None
            and rule_mirror(grid) is not None
            and (not needs_repeat or _has_repeated_component_color(grid))
        ):
            last_error = ValueError("reflection profile no longer isolates reflection/repetition")
            continue
        return grid

    raise ValueError(f"could not realize {profile}: {last_error}")


def _grid_shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid is ragged"]
    if not all(
        isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC integer colours 0..9"]
    return []


def self_check(grid: Grid, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    issues = _grid_shape_errors(grid)
    if issues:
        return issues

    components = _components(grid)
    nonzero = sum(len(shape) for _, shape in components)
    colors = {color for color, _ in components}
    if nonzero != 12:
        issues.append(f"piece cells total {nonzero}, expected 12")
    if not 3 <= len(components) <= 5:
        issues.append(f"{len(components)} pieces, expected 3..5")
    if len(colors) != 3:
        issues.append(f"{len(colors)} foreground colours, expected exactly 3")
    if nonzero == 12 and 3 <= len(components) <= 5 and len(colors) == 3:
        packed = rule_mirror(grid)
        if packed is None:
            issues.append("pieces do not pack into 3x4 under the authoritative search")
    return issues


def strict_canonical_like(grid: Grid) -> list[str]:
    issues = self_check(grid)
    if issues:
        return issues
    if len(grid) != 10:
        issues.append(f"height {len(grid)} is outside canonical height 10")
    if not 10 <= len(grid[0]) <= 13:
        issues.append(f"width {len(grid[0])} is outside canonical 10..13")
    return issues


def observe_overrides(grid: Grid) -> dict[str, int]:
    issues = _grid_shape_errors(grid)
    if issues:
        raise ValueError("; ".join(issues))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pieces": len(_components(grid)),
    }


def _has_repeated_component_color(grid: Grid) -> bool:
    colors = [color for color, _ in _components(grid)]
    return len(colors) != len(set(colors))


def _zero_if_none(value: Grid | None) -> Grid:
    return [row[:] for row in (value if value is not None else _ZERO_OUTPUT)]


def _rival_translation_only(grid: Grid) -> Grid:
    return _zero_if_none(_translation_only_pack(grid))


def _rival_rotation_only(grid: Grid) -> Grid:
    return _zero_if_none(_rotation_only_pack(grid))


def _rival_one_piece_per_color(grid: Grid) -> Grid:
    # A common shortcut assumes every colour denotes exactly one object.
    if _has_repeated_component_color(grid):
        return [row[:] for row in _ZERO_OUTPUT]
    return _zero_if_none(rule_mirror(grid))


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "translation_only": _rival_translation_only,
    "rotation_only": _rival_rotation_only,
    "one_piece_per_color": _rival_one_piece_per_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Only rotation-only fits every labeled canonical variant. The other rivals
# remain useful partial hypotheses in LESSON_COMPETITORS.
CANONICAL_SHORTCUTS = {"rotation_only": _rival_rotation_only}

SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "rotation_required": lambda grid: (
        _translation_only_pack(grid) is None and _rotation_only_pack(grid) is not None
    ),
    "reflection_required": lambda grid: (
        _rotation_only_pack(grid) is None and rule_mirror(grid) is not None
    ),
    "repeated_component_color": _has_repeated_component_color,
}
WITNESS_RIVALS = {
    "rotation_required": ["translation_only"],
    "reflection_required": ["rotation_only"],
    "repeated_component_color": ["one_piece_per_color"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Check that a materialized lesson refutes every declared shortcut."""

    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        truth = rule_mirror(demo["input"])
        if truth is None or demo["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the authoritative rule")
    if reasons:
        return reasons

    query_input = query.get("input") if isinstance(query, dict) else None
    if query_input is None:
        return ["query has no input grid"]
    query_truth = rule_mirror(query_input)
    if query_truth is None:
        return ["query input is not solvable by the authoritative rule"]
    if isinstance(query, dict) and "output" in query and query["output"] != query_truth:
        reasons.append("query output disagrees with the authoritative rule")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != query_truth:
                reasons.append(
                    f"competitor {name!r} fits every demonstration but changes the query"
                )
    return reasons

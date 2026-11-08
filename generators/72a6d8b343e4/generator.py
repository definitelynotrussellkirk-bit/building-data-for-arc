"""Input generator for Endpoint Bridge (72a6d8b343e4).

For every nonzero colour appearing in exactly two cells, connect those cells
with an inclusive straight segment only when they share a row or a column.
Adjacent endpoints are already complete.  Misaligned pairs and colours with an
extra occurrence are deliberately present in the curriculum and stay unchanged.

The Racket program selected by ``RULE_HASH`` remains answer authority.  The
Python mirror and rivals below are executable review contracts, not labels.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "72a6d8b343e4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "3650a4704dc3"

SUMMARY = (
    "A 0-background grid contains distinct-colour endpoint groups. Colours "
    "appearing exactly twice are bridged only when the endpoints share a row "
    "or column; the inclusive straight segment is painted in that colour. "
    "Adjacent pairs need no added cells. Misaligned pairs and three-occurrence "
    "groups are unchanged and serve as explicit guards against shortcut rules."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

INVARIANTS = [
    "grid dimensions are 8..12 by 9..15 and the background is 0",
    "every nonzero colour is one declared role: separated line, adjacent pair, misaligned pair, or guarded triplet",
    "at least one separated aligned pair changes under the selected rule",
    "line interiors are blank in the input, so no overwrite precedence is taught",
    "all advertised count overrides are exact and observable from returned pixels",
]

AXES = {
    "grid_h": {"type": "int", "default": "profile schedule", "valid": "8..12"},
    "grid_w": {"type": "int", "default": "profile schedule", "valid": "9..15"},
    "n_lines": {"type": "int", "default": "profile schedule", "valid": "1..3"},
    "n_adjacent": {"type": "int", "default": "profile schedule", "valid": "0..1"},
    "n_misaligned": {"type": "int", "default": "profile schedule", "valid": "0..1"},
    "n_triplets": {"type": "int", "default": "profile schedule", "valid": "0..1"},
}

SCHEDULE_PROFILES = ("canonical_core", "dual_witness")
_CURRICULUM_SEQUENCE = ("canonical_core", "dual_witness")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Alternate exact canonical-profile support with a dual shortcut witness."""
    del seed
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return _CURRICULUM_SEQUENCE[int(sample_index) % len(_CURRICULUM_SEQUENCE)]


def _validate_overrides(overrides: dict[str, Any]) -> dict[str, int]:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    clean: dict[str, int] = {}
    bounds = {
        "grid_h": (8, 12),
        "grid_w": (9, 15),
        "n_lines": (1, 3),
        "n_adjacent": (0, 1),
        "n_misaligned": (0, 1),
        "n_triplets": (0, 1),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo},{hi}]")
        clean[name] = value
    return clean


def _draw_default_int(ctx, overrides: dict[str, int], name: str,
                      default: int, lo: int, hi: int) -> int:
    if name in overrides:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _defaults(profile: str, sample_index: int, difficulty) -> dict[str, int]:
    if profile == "canonical_core":
        phase = int(sample_index) // 2
        lines = 2 if phase % 2 == 0 else 1
        return {
            "grid_h": 8,
            "grid_w": 9 + phase % 3,
            "n_lines": lines,
            "n_adjacent": 2 - lines,
            "n_misaligned": 0,
            "n_triplets": 0,
        }
    by_band = {
        None: (9, 12, 2),
        "easy": (8, 9, 1),
        "medium": (10, 12, 2),
        "hard": (12, 15, 3),
    }
    h, w, lines = by_band[difficulty]
    return {
        "grid_h": h,
        "grid_w": w,
        "n_lines": lines,
        "n_adjacent": (int(sample_index) // 2) % 2,
        "n_misaligned": 1,
        "n_triplets": 1,
    }


def _split_ranges(total: int, count: int) -> list[range]:
    base, extra = divmod(total, count)
    result = []
    start = 0
    for index in range(count):
        size = base + (1 if index < extra else 0)
        result.append(range(start, start + size))
        start += size
    return result


def _block_shape(n_objects: int, rng) -> tuple[int, int]:
    if n_objects <= 1:
        return 1, 1
    if n_objects == 2:
        return rng.choice(((1, 2), (2, 1)))
    if n_objects == 3:
        return rng.choice(((1, 3), (2, 2)))
    if n_objects == 4:
        return 2, 2
    return 2, 3


def _line_candidates(rows: range, cols: range, orientation: str):
    candidates = []
    if orientation == "horizontal":
        for r in rows:
            for c1 in cols:
                for c2 in cols:
                    if c2 >= c1 + 2:
                        candidates.append(((r, c1), (r, c2)))
    else:
        for c in cols:
            for r1 in rows:
                for r2 in rows:
                    if r2 >= r1 + 2:
                        candidates.append(((r1, c), (r2, c)))
    return candidates


def _adjacent_candidates(rows: range, cols: range, orientation: str):
    candidates = []
    if orientation == "horizontal":
        for r in rows:
            for c in range(cols.start, cols.stop - 1):
                candidates.append(((r, c), (r, c + 1)))
    else:
        for c in cols:
            for r in range(rows.start, rows.stop - 1):
                candidates.append(((r, c), (r + 1, c)))
    return candidates


def _misaligned_candidates(rows: range, cols: range):
    cells = [(r, c) for r in rows for c in cols]
    return [
        (a, b)
        for index, a in enumerate(cells)
        for b in cells[index + 1:]
        if a[0] != b[0] and a[1] != b[1]
    ]


def _triplet_candidates(rows: range, cols: range, orientation: str):
    candidates = []
    for a, b in _line_candidates(rows, cols, orientation):
        for third in ((r, c) for r in rows for c in cols):
            if third in (a, b):
                continue
            if orientation == "horizontal":
                if third[0] == a[0] or third[1] in (a[1], b[1]):
                    continue
            else:
                if third[1] == a[1] or third[0] in (a[0], b[0]):
                    continue
            candidates.append((a, b, third))
    return candidates


def _orientations(count: int, rng) -> list[str]:
    if count <= 0:
        return []
    values = []
    if count >= 2:
        values.extend(("horizontal", "vertical"))
    else:
        values.append(rng.choice(("horizontal", "vertical")))
    while len(values) < count:
        values.append(rng.choice(("horizontal", "vertical")))
    rng.shuffle(values)
    return values


def _place_roles(grid: list[list[int]], colors: list[int], counts: dict[str, int], rng) -> None:
    total = sum(counts.values())
    block_rows, block_cols = _block_shape(total, rng)
    row_ranges = _split_ranges(len(grid), block_rows)
    col_ranges = _split_ranges(len(grid[0]), block_cols)
    blocks = [(rows, cols) for rows in row_ranges for cols in col_ranges]
    rng.shuffle(blocks)
    blocks = blocks[:total]

    line_orientations = _orientations(counts["line"], rng)
    adjacent_orientations = _orientations(counts["adjacent"], rng)
    triplet_orientations = _orientations(counts["triplet"], rng)
    roles: list[tuple[str, str | None]] = []
    roles.extend(("line", orientation) for orientation in line_orientations)
    roles.extend(("adjacent", orientation) for orientation in adjacent_orientations)
    roles.extend(("misaligned", None) for _ in range(counts["misaligned"]))
    roles.extend(("triplet", orientation) for orientation in triplet_orientations)
    rng.shuffle(roles)

    for color, (role, orientation), (rows, cols) in zip(colors, roles, blocks):
        if len(rows) < 3 or len(cols) < 3:
            raise RuntimeError("internal block packing produced a block smaller than 3x3")
        if role == "line":
            candidates = _line_candidates(rows, cols, str(orientation))
        elif role == "adjacent":
            candidates = _adjacent_candidates(rows, cols, str(orientation))
        elif role == "misaligned":
            candidates = _misaligned_candidates(rows, cols)
        else:
            candidates = _triplet_candidates(rows, cols, str(orientation))
        if not candidates:
            raise RuntimeError(f"no constructive candidate for {role} in {len(rows)}x{len(cols)} block")
        for r, c in rng.choice(candidates):
            grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic lawful input; every advertised override is exact."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    clean = _validate_overrides(overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _defaults(profile, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=clean,
    )
    h = _draw_default_int(ctx, clean, "grid_h", defaults["grid_h"], 8, 12)
    w = _draw_default_int(ctx, clean, "grid_w", defaults["grid_w"], 9, 15)
    n_lines = _draw_default_int(ctx, clean, "n_lines", defaults["n_lines"], 1, 3)
    n_adjacent = _draw_default_int(ctx, clean, "n_adjacent", defaults["n_adjacent"], 0, 1)
    n_misaligned = _draw_default_int(ctx, clean, "n_misaligned", defaults["n_misaligned"], 0, 1)
    n_triplets = _draw_default_int(ctx, clean, "n_triplets", defaults["n_triplets"], 0, 1)

    counts = {
        "line": n_lines,
        "adjacent": n_adjacent,
        "misaligned": n_misaligned,
        "triplet": n_triplets,
    }
    total = sum(counts.values())
    if total > 9:
        raise ValueError(f"requested {total} colour roles but ARC supplies only 9 nonzero colours")
    grid = full_grid(h, w, 0)
    colors = ctx.draw_rng("palette").sample(list(range(1, 10)), total)
    _place_roles(grid, colors, counts, ctx.draw_rng("layout"))
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": clean})
    if errors:
        raise AssertionError("constructive generator produced an invalid grid: " + "; ".join(errors))
    return grid


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["input must be a non-empty list of rows"]
    if any(not isinstance(row, list) for row in grid):
        return ["every row must be a list"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["input must be a non-empty rectangular grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colours 0..9"]
    return []


def _positions_by_color(grid) -> dict[int, list[tuple[int, int]]]:
    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions[value].append((r, c))
    return dict(positions)


def _axis_path(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    (r1, c1), (r2, c2) = a, b
    if r1 == r2:
        lo, hi = sorted((c1, c2))
        return [(r1, c) for c in range(lo, hi + 1)]
    if c1 == c2:
        lo, hi = sorted((r1, r2))
        return [(r, c1) for r in range(lo, hi + 1)]
    return []


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _basic_grid_errors(grid)
    if errors:
        return {"errors": errors, "categories": {}, "paths": []}
    h, w = len(grid), len(grid[0])
    categories = {"line": [], "adjacent": [], "misaligned": [], "triplet": []}
    paths = []
    for color, points in sorted(_positions_by_color(grid).items()):
        if len(points) == 2:
            path = _axis_path(points[0], points[1])
            if not path:
                categories["misaligned"].append(color)
            elif len(path) == 2:
                categories["adjacent"].append(color)
            else:
                categories["line"].append(color)
                paths.append((color, path))
            continue
        if len(points) == 3:
            aligned = []
            for i in range(3):
                for j in range(i + 1, 3):
                    path = _axis_path(points[i], points[j])
                    if len(path) >= 3:
                        aligned.append(path)
            if len(aligned) == 1:
                categories["triplet"].append(color)
                paths.append((color, aligned[0]))
                continue
        errors.append(
            f"color {color} has unsupported occurrence/geometry pattern: {points}"
        )
    return {
        "errors": errors,
        "height": h,
        "width": w,
        "categories": categories,
        "paths": paths,
        "palette_size": len({value for row in grid for value in row}),
    }


def observe_overrides(grid) -> dict[str, int]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(facts["errors"]))
    categories = facts["categories"]
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_lines": len(categories["line"]),
        "n_adjacent": len(categories["adjacent"]),
        "n_misaligned": len(categories["misaligned"]),
        "n_triplets": len(categories["triplet"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete public grammar and any requested exact controls."""
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    facts = _analyze(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    h, w = facts["height"], facts["width"]
    if not 8 <= h <= 12 or not 9 <= w <= 15:
        errors.append(f"grid dimensions must be 8..12 by 9..15, got {h}x{w}")
    categories = facts["categories"]
    bounds = {"line": (1, 3), "adjacent": (0, 1), "misaligned": (0, 1), "triplet": (0, 1)}
    for name, (lo, hi) in bounds.items():
        count = len(categories[name])
        if not lo <= count <= hi:
            errors.append(f"n_{name}={count} outside [{lo},{hi}]")
    # Both actual line interiors and triplet-rival interiors must be blank. This
    # keeps every output consequence attributable to one colour role.
    for color, path in facts["paths"]:
        nonzero_interior = [(r, c, grid[r][c]) for r, c in path[1:-1] if grid[r][c] != 0]
        if nonzero_interior:
            errors.append(f"color {color} has nonblank aligned interior: {nonzero_interior[:3]}")

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = {name: candidate[name] for name in AXES if name in candidate and candidate[name] is not None}
    if requested and not errors:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if observed[name] != value:
                errors.append(f"override {name}={value!r} realized as {observed[name]!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical 8x(9..11), two-colour endpoint manifold."""
    errors = self_check(grid)
    if errors:
        return errors
    facts = _analyze(grid)
    categories = facts["categories"]
    if facts["height"] != 8 or facts["width"] not in (9, 10, 11):
        errors.append("canonical profile requires height 8 and width 9, 10, or 11")
    if facts["palette_size"] != 3:
        errors.append("canonical profile requires background plus exactly two nonzero colours")
    if len(categories["line"]) + len(categories["adjacent"]) != 2:
        errors.append("canonical profile requires exactly two aligned endpoint colours")
    if categories["misaligned"] or categories["triplet"]:
        errors.append("canonical profile excludes misaligned and extra-occurrence witnesses")
    return errors


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror; selected Racket remains answer authority."""
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = deepcopy(grid)
    for color, points in _positions_by_color(grid).items():
        if len(points) != 2:
            continue
        for r, c in _axis_path(points[0], points[1]):
            output[r][c] = color
    return output


def _rival_connect_misaligned_by_l_path(grid) -> list[list[int]]:
    """Wrong but canonical-fitting: connect every exactly-two group by a Manhattan L."""
    output = deepcopy(grid)
    for color, points in _positions_by_color(grid).items():
        if len(points) != 2:
            continue
        a, b = points
        path = _axis_path(a, b)
        if path:
            for r, c in path:
                output[r][c] = color
            continue
        (r1, c1), (r2, c2) = a, b
        step_c = 1 if c2 >= c1 else -1
        for c in range(c1, c2 + step_c, step_c):
            output[r1][c] = color
        step_r = 1 if r2 >= r1 else -1
        for r in range(r1, r2 + step_r, step_r):
            output[r][c2] = color
    return output


def _rival_connect_aligned_subsets(grid) -> list[list[int]]:
    """Wrong but canonical-fitting: ignore exact multiplicity and join aligned subsets."""
    output = deepcopy(grid)
    for color, points in _positions_by_color(grid).items():
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                for r, c in _axis_path(points[i], points[j]):
                    output[r][c] = color
    return output


def _has_misaligned_pair(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and bool(facts["categories"]["misaligned"])


def _has_guarded_triplet(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and bool(facts["categories"]["triplet"])


SEMANTIC_WITNESSES = {
    "misaligned_pair_ignored": _has_misaligned_pair,
    "extra_occurrence_blocks_line": _has_guarded_triplet,
}
SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "connect_misaligned_by_l_path": _rival_connect_misaligned_by_l_path,
    "connect_aligned_subsets": _rival_connect_aligned_subsets,
}
WITNESS_RIVALS = {
    "misaligned_pair_ignored": ["connect_misaligned_by_l_path"],
    "extra_occurrence_blocks_line": ["connect_aligned_subsets"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Report a declared rival that fits every demo but changes the query."""
    if not demos:
        return ["lesson has no demonstrations"]
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"competitor {name!r} fits every demo but changes the query answer")
    return reasons

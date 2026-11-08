"""Generator for ARC task 07ab476607b3.

Normalize the red (2) shape A and yellow (4) shape B independently to
origin, subtract B's normalized cells from A's, then stamp the residue in
magenta (6) at the first maroon (9) anchor on a fresh black canvas.
Residue cells outside the canvas are clipped by the authoritative rule.

The ordinary curriculum deliberately cycles three decisive examples:
partial normalized overlap, normalized disjointness, and a clipped stamp.
``empty_diff`` remains an exact override for the lawful A == B boundary.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "07ab476607b3"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "11cea0a09738"

SUMMARY = (
    "Normalize the red A-shape and yellow B-shape, compute A minus B in "
    "normalized coordinates, and stamp that residue in magenta at the maroon "
    "anchor on a blank canvas. The curriculum guarantees partial-overlap, "
    "normalized-disjoint, and clipped-stamp counterexamples; empty_diff is an "
    "exact boundary override."
)

INVARIANTS = [
    "the input palette is exactly a subset of black/red/yellow/maroon (0/2/4/9)",
    "there is exactly one 4-connected red object, one 4-connected yellow object, and one maroon anchor",
    "red and yellow are compared only after independent top-left normalization",
    "the output is rebuilt from black and contains only the in-bounds magenta residue",
    "the first three ordinary samples cover partial overlap, disjointness, and clipping",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

TEXTURES = ("plain", "disjoint_b", "clip", "empty_diff")
HELPFUL_TEXTURES = ("plain", "disjoint_b", "clip")
# Missing the anchor crashes the selected Racket rule. Keep the defect named for
# audit visibility, but do not advertise it as an ordinary valid override.
DEGENERATE_TEXTURES = ("no_anchor",)
CANONICAL_PROFILES = ((10, 11), (10, 12), (11, 11), (11, 12))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "cycle canonical profiles by sample_index",
        "valid": "10..13",
    },
    "grid_w": {
        "type": "int",
        "default": "cycle canonical profiles by sample_index",
        "valid": "11..15",
    },
    "a_size": {
        "type": "int",
        "default": "difficulty-banded deterministic keyed draw",
        "valid": "4..7",
    },
    "texture": {
        "type": "str",
        "default": "cycle plain|disjoint_b|clip by sample_index",
        "valid": "plain|disjoint_b|clip|empty_diff",
        "doc": (
            "plain has a nonempty proper normalized overlap; disjoint_b has "
            "no normalized overlap; clip loses only part of a nonempty residue "
            "at the lower/right edge; empty_diff has normalized A == B."
        ),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _norm(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return tuple(sorted((r - min_r, c - min_c) for r, c in points))


def _bbox(shape: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


@lru_cache(maxsize=None)
def _polyominoes(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """All fixed 4-connected polyominoes of ``size`` up to translation.

    Sizes stop at seven (760 fixed heptominoes), so exhaustive construction is
    small, deterministic, and more reliable than retrying random walks until a
    requested normalized relationship happens by chance.
    """
    if size < 1:
        return ()
    if size == 1:
        return (((0, 0),),)
    grown: set[tuple[tuple[int, int], ...]] = set()
    for shape in _polyominoes(size - 1):
        occupied = set(shape)
        for r, c in shape:
            for dr, dc in _NEIGHBORS:
                candidate = (r + dr, c + dc)
                if candidate in occupied:
                    continue
                grown.add(_norm((*shape, candidate)))
    return tuple(sorted(grown))


@lru_cache(maxsize=None)
def _compact_polyominoes(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    return tuple(
        shape
        for shape in _polyominoes(size)
        if _bbox(shape)[0] <= 4 and _bbox(shape)[1] <= 4
    )


@lru_cache(maxsize=4096)
def _related_b_shapes(
    a: tuple[tuple[int, int], ...], relation: str
) -> tuple[tuple[tuple[int, int], ...], ...]:
    a_set = set(a)
    matches: list[tuple[tuple[int, int], ...]] = []
    for size in range(2, 8):
        for b in _compact_polyominoes(size):
            overlap = a_set & set(b)
            if relation == "partial":
                # At least two residue cells make a genuine partial clipping
                # example possible as well as an informative ordinary stamp.
                if 0 < len(overlap) < len(a_set) and len(a_set - set(b)) >= 2:
                    matches.append(b)
            elif relation == "disjoint":
                if not overlap:
                    matches.append(b)
            else:  # programmer error, never caller input
                raise ValueError(f"unknown shape relation: {relation!r}")
    return tuple(matches)


@lru_cache(maxsize=None)
def _eligible_a_shapes(
    size: int, relation: str
) -> tuple[tuple[tuple[int, int], ...], ...]:
    return tuple(
        a for a in _compact_polyominoes(size) if _related_b_shapes(a, relation)
    )


def _choose_shapes(rng, a_size: int, texture: str):
    if texture == "empty_diff":
        choices = _compact_polyominoes(a_size)
        a = choices[rng.randrange(len(choices))]
        return a, a

    relation = "disjoint" if texture == "disjoint_b" else "partial"
    a_choices = _eligible_a_shapes(a_size, relation)
    if not a_choices:
        raise ValueError(
            f"no compact size-{a_size} A shape supports relation {relation!r}"
        )
    a = a_choices[rng.randrange(len(a_choices))]
    b_choices = _related_b_shapes(a, relation)
    b = b_choices[rng.randrange(len(b_choices))]
    return a, b


def _cells_at(
    shape: Sequence[tuple[int, int]], top: int, left: int
) -> frozenset[tuple[int, int]]:
    return frozenset((top + r, left + c) for r, c in shape)


def _placements(
    shape: Sequence[tuple[int, int]], h: int, w: int
) -> list[tuple[int, int]]:
    sh, sw = _bbox(shape)
    if sh > h or sw > w:
        return []
    return [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]


def _halo(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    }


def _place_objects(h: int, w: int, a, b, rng):
    """Place A and B with a one-cell visual gap, or return ``None``."""
    a_positions = _placements(a, h, w)
    rng.shuffle(a_positions)
    b_positions = _placements(b, h, w)
    for ar, ac in a_positions:
        a_cells = _cells_at(a, ar, ac)
        blocked = _halo(a_cells)
        legal_b = [
            (br, bc)
            for br, bc in b_positions
            if not (_cells_at(b, br, bc) & blocked)
        ]
        if not legal_b:
            continue
        br, bc = legal_b[rng.randrange(len(legal_b))]
        return a_cells, _cells_at(b, br, bc)
    return None


def _anchor_candidates(
    h: int,
    w: int,
    diff: Sequence[tuple[int, int]],
    texture: str,
    occupied: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    candidates: list[tuple[int, int]] = []
    for ar in range(h):
        for ac in range(w):
            if (ar, ac) == (0, 0) or (ar, ac) in occupied:
                continue
            placed = [(ar + r, ac + c) for r, c in diff]
            in_bounds = [p for p in placed if 0 <= p[0] < h and 0 <= p[1] < w]
            if texture == "clip":
                if in_bounds and len(in_bounds) < len(placed):
                    candidates.append((ar, ac))
            elif len(in_bounds) == len(placed):
                candidates.append((ar, ac))
    return candidates


def _draw_dimension(ctx, name: str, scheduled: int, lo: int, hi: int, overrides):
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    # A one-option keyed choice records the scheduled value under the exact
    # public axis label while preserving canonical profile coverage.
    return ctx.draw_choice(name, (scheduled,))


def _draw_a_size(ctx, sample_index: int, band: str, overrides) -> int:
    if overrides.get("a_size") is not None:
        return ctx.draw_int("a_size", 4, 7)
    choices = {
        "easy": (4, 5),
        "medium": (4, 5, 6),
        "hard": (5, 6, 7),
    }[band]
    # Cycle the complexity band so all sizes are guaranteed rather than merely
    # probable, but still consume the keyed public draw for provenance.
    scheduled = choices[sample_index % len(choices)]
    return ctx.draw_choice("a_size", (scheduled,))


def _draw_texture(ctx, sample_index: int, overrides) -> str:
    value = overrides.get("texture")
    if value is not None and value not in TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError(f"unknown texture: {value!r}")
    if value in DEGENERATE_TEXTURES:
        # Negative fixtures are deliberately outside AXES.valid. They are not
        # consumed as ordinary public-axis draws, which keeps the exact valid
        # domain honest while allowing the defect linter to materialize them.
        return str(value)
    if value is not None:
        return ctx.draw_choice("texture", TEXTURES)
    return ctx.draw_choice(
        "texture", (HELPFUL_TEXTURES[sample_index % len(HELPFUL_TEXTURES)],)
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    scheduled_h, scheduled_w = CANONICAL_PROFILES[
        sample_index % len(CANONICAL_PROFILES)
    ]
    h = _draw_dimension(ctx, "grid_h", scheduled_h, 10, 13, overrides)
    w = _draw_dimension(ctx, "grid_w", scheduled_w, 11, 15, overrides)
    a_size = _draw_a_size(ctx, sample_index, band, overrides)
    texture = _draw_texture(ctx, sample_index, overrides)
    rng = ctx.draw_rng("construction")

    # Construction is exact; retries only vary compact shape choices when a
    # particular pair cannot be laid out with the intended visual separation.
    for _attempt in range(96):
        a, b = _choose_shapes(rng, a_size, texture)
        placed_objects = _place_objects(h, w, a, b, rng)
        if placed_objects is None:
            continue
        a_cells, b_cells = placed_objects
        if texture == "no_anchor":
            grid = full_grid(h, w, 0)
            for r, c in a_cells:
                grid[r][c] = 2
            for r, c in b_cells:
                grid[r][c] = 4
            return grid

        b_set = set(b)
        diff = tuple(cell for cell in a if cell not in b_set)
        anchors = _anchor_candidates(
            h, w, diff, texture, set(a_cells) | set(b_cells)
        )
        if not anchors:
            continue
        # Prefer an anchor outside the one-cell object halo for legibility,
        # while retaining a guaranteed fallback for cramped legal overrides.
        object_halo = _halo(set(a_cells) | set(b_cells))
        clear = [candidate for candidate in anchors if candidate not in object_halo]
        anchor_pool = clear or anchors
        anchor = anchor_pool[rng.randrange(len(anchor_pool))]

        grid = full_grid(h, w, 0)
        for r, c in a_cells:
            grid[r][c] = 2
        for r, c in b_cells:
            grid[r][c] = 4
        grid[anchor[0]][anchor[1]] = 9
        return grid

    raise ValueError(
        f"could not construct {texture!r} board for {h}x{w}, A size {a_size}"
    )


def _components(grid: Sequence[Sequence[int]], color: int):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[tuple[int, int], ...]] = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _NEIGHBORS:
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            components.append(tuple(sorted(cells)))
    return components


def _empty_analysis(errors: list[str], h: int = 0, w: int = 0) -> dict[str, Any]:
    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "a_size": 0,
        "texture": None,
        "a_cells": (),
        "b_cells": (),
        "a_normalized": (),
        "b_normalized": (),
        "normalized_overlap": (),
        "diff": (),
        "anchor": None,
        "placed": (),
        "output_cells": (),
        "clipped": False,
        "output": full_grid(h, w, 0) if h and w else [],
    }


def analyze(grid: Any) -> dict[str, Any]:
    """Return the structural parse and authoritative Python mirror inputs.

    The function is intentionally total over malformed values: callers receive
    explicit reasons instead of a secondary indexing exception.
    """
    if not isinstance(grid, (list, tuple)) or not grid:
        return _empty_analysis(["grid must be a non-empty sequence of rows"])
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return _empty_analysis(["grid rows must be non-empty"])
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return _empty_analysis(["grid must be rectangular"], h, w)
    if not (10 <= h <= 13):
        errors.append(f"grid height must be 10..13, got {h}")
    if not (11 <= w <= 15):
        errors.append(f"grid width must be 11..15, got {w}")
    invalid = sorted(
        {
            value
            for row in grid
            for value in row
            if isinstance(value, bool)
            or not isinstance(value, int)
            or value not in (0, 2, 4, 9)
        },
        key=repr,
    )
    if invalid:
        errors.append(f"input palette contains invalid value(s): {invalid}")

    a_components = _components(grid, 2)
    b_components = _components(grid, 4)
    anchors = [
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9
    ]
    if len(a_components) != 1:
        errors.append(
            f"expected exactly one connected color-2 object, got {len(a_components)}"
        )
    if len(b_components) != 1:
        errors.append(
            f"expected exactly one connected color-4 object, got {len(b_components)}"
        )
    if len(anchors) != 1:
        errors.append(f"expected exactly one color-9 anchor, got {len(anchors)}")
    if errors:
        return _empty_analysis(errors, h, w)

    a_cells = a_components[0]
    b_cells = b_components[0]
    a_normalized = _norm(a_cells)
    b_normalized = _norm(b_cells)
    b_norm_set = set(b_normalized)
    overlap = tuple(cell for cell in a_normalized if cell in b_norm_set)
    diff = tuple(cell for cell in a_normalized if cell not in b_norm_set)
    anchor = anchors[0]
    placed = tuple((anchor[0] + r, anchor[1] + c) for r, c in diff)
    output_cells = tuple(
        cell for cell in placed if 0 <= cell[0] < h and 0 <= cell[1] < w
    )
    clipped = len(output_cells) != len(placed)
    output = full_grid(h, w, 0)
    for r, c in output_cells:
        output[r][c] = 6

    if not (4 <= len(a_cells) <= 7):
        errors.append(f"A size must be 4..7, got {len(a_cells)}")
    if not diff:
        texture = "empty_diff"
    elif clipped:
        texture = "clip"
    elif overlap:
        texture = "plain"
    else:
        texture = "disjoint_b"

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "a_size": len(a_cells),
        "texture": texture,
        "a_cells": a_cells,
        "b_cells": b_cells,
        "a_normalized": a_normalized,
        "b_normalized": b_normalized,
        "normalized_overlap": overlap,
        "diff": diff,
        "anchor": anchor,
        "placed": placed,
        "output_cells": output_cells,
        "clipped": clipped,
        "output": output,
    }


def observe_overrides(grid: Any) -> dict[str, Any]:
    info = analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None):
    return list(analyze(grid)["errors"])


def strict_canonical_like(grid: Any) -> list[str]:
    return list(analyze(grid)["errors"])


def rule_mirror(grid: Any) -> list[list[int]]:
    info = analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [list(row) for row in info["output"]]


def _paint_at_anchor(
    grid: Any, normalized_cells: Sequence[tuple[int, int]], anchor=None
) -> list[list[int]]:
    info = analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    h, w = info["grid_h"], info["grid_w"]
    ar, ac = info["anchor"] if anchor is None else anchor
    out = full_grid(h, w, 0)
    for r, c in normalized_cells:
        rr, cc = ar + r, ac + c
        if 0 <= rr < h and 0 <= cc < w:
            out[rr][cc] = 6
    return out


def _witness_partial_overlap(grid: Any) -> bool:
    info = analyze(grid)
    return (
        not info["errors"]
        and info["texture"] == "plain"
        and bool(info["normalized_overlap"])
        and bool(info["diff"])
    )


def _witness_disjoint(grid: Any) -> bool:
    info = analyze(grid)
    return not info["errors"] and info["texture"] == "disjoint_b"


def _witness_clipped(grid: Any) -> bool:
    info = analyze(grid)
    return not info["errors"] and info["texture"] == "clip" and info["clipped"]


SEMANTIC_WITNESSES = {
    "normalized_partial_overlap": _witness_partial_overlap,
    "normalized_disjoint": _witness_disjoint,
    "clipped_stamp": _witness_clipped,
}


def _rival_positional_subtraction(grid: Any) -> list[list[int]]:
    """Wrong shortcut: physical separation means B erases none of A."""
    info = analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return _paint_at_anchor(grid, info["a_normalized"])


def _rival_assume_one_overlap(grid: Any) -> list[list[int]]:
    """Wrong shortcut: force one cancellation even when normalized shapes miss."""
    info = analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    forced = info["a_normalized"][1:] if info["a_normalized"] else ()
    return _paint_at_anchor(grid, forced)


def _rival_fit_stamp_inside(grid: Any) -> list[list[int]]:
    """Wrong shortcut: shift the anchor inward instead of clipping."""
    info = analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    if not info["diff"]:
        return _paint_at_anchor(grid, ())
    max_r = max(r for r, _ in info["diff"])
    max_c = max(c for _, c in info["diff"])
    ar, ac = info["anchor"]
    fitted = (
        min(ar, info["grid_h"] - 1 - max_r),
        min(ac, info["grid_w"] - 1 - max_c),
    )
    return _paint_at_anchor(grid, info["diff"], fitted)


SEMANTIC_RIVALS = {
    "positional_subtraction": _rival_positional_subtraction,
    "assume_one_overlap": _rival_assume_one_overlap,
    "fit_stamp_inside": _rival_fit_stamp_inside,
}
WITNESS_RIVALS = {
    "normalized_partial_overlap": ["positional_subtraction"],
    "normalized_disjoint": ["assume_one_overlap"],
    "clipped_stamp": ["fit_stamp_inside"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    valid_demo_inputs: list[Any] = []
    textures: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info = analyze(pair["input"])
        if info["errors"]:
            reasons.append(f"demo {index} malformed: {info['errors'][0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match normalized A minus B")
            continue
        valid_demo_inputs.append(pair["input"])
        textures.add(info["texture"])

    required = set(HELPFUL_TEXTURES)
    if not required <= textures:
        reasons.append(
            "demonstrations must cover plain, disjoint_b, and clip; got "
            f"{sorted(textures)}"
        )

    for rival_name, rival in SEMANTIC_RIVALS.items():
        if valid_demo_inputs and all(
            rival(grid) == rule_mirror(grid) for grid in valid_demo_inputs
        ):
            reasons.append(f"rival {rival_name!r} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        info = analyze(query["input"])
        if info["errors"]:
            reasons.append(f"query malformed: {info['errors'][0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the authoritative transform")
    return reasons

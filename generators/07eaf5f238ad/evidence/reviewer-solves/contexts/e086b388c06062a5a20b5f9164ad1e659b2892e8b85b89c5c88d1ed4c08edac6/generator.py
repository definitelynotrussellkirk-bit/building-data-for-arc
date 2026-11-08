"""Generator for ARC task 07eaf5f238ad — pack body objects in header order.

The unchanged Racket authority reads the nonzero colours in row 0 from left to
right.  For each colour it selects the first matching monochrome body object in
row-major component order, crops that object's bounding box from the body, and
packs the crops left-to-right with one blank column between them.  Missing
header colours are skipped; repeated header colours repeat the selected crop.

The production schedule alternates two roles:

* even sample indexes are rich teaching cases that jointly refute the strongest
  named rivals (body scan order, header deduplication, last-object selection,
  requiring every header colour, and appending non-header objects);
* odd sample indexes rotate through the three canonical height/width/palette
  profiles.  Every four-example sliding lesson therefore contains at least one
  rich witness, while every six draws cover all canonical profiles.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "07eaf5f238ad"
TASK_ID = GENERATOR_ID
RULE_HASH = "d10bfd060d8f"
VERSION = "3.0.0"

SUMMARY = (
    "The nonzero top-row colours select body objects in header order. The first "
    "row-major object of each colour is cropped to its bbox and packed "
    "left-to-right with one zero column between pieces. Missing header colours "
    "are skipped, repeated colours repeat the same crop, and non-header objects "
    "are ignored."
)

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 6
_CANONICAL_PROFILES = ((8, 10, 2), (11, 11, 3), (11, 12, 3))
TEXTURES = (
    "plain",
    "absent_color",
    "repeat_header",
    "first_wins",
    "decoy_colors",
    "rich",
)
HELPFUL_TEXTURES = TEXTURES
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchors or difficulty-weighted 8..16",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchors or difficulty-weighted 10..18",
        "valid": "10..18",
    },
    "n_header": {
        "type": "int",
        "default": "canonical 2|3 or rich 4 distinct header colours",
        "valid": "2..4",
        "doc": "number of distinct nonzero colours in the header; repeat textures add one repeated token",
    },
    "texture": {
        "type": "str",
        "default": "plain on canonical anchors; rich on teaching anchors",
        "valid": "|".join(TEXTURES),
        "doc": (
            "plain: unique present header colours; absent_color: one missing "
            "header colour; repeat_header: one repeated token; first_wins: two "
            "objects of the first header colour; decoy_colors: one non-header "
            "body object; rich: all four distinctions together"
        ),
    },
}

INVARIANTS = [
    "row 0 is the header and row 1 is a blank separator",
    "body objects are monochrome, connected, and halo-disjoint",
    "ordinary outputs are nonempty and at most 30 columns wide",
    "all advertised exact overrides are recoverable from returned pixels",
]

# All shapes fit a 2x2 placement slot.  The first and second shapes are
# deliberately different so first-vs-last selection changes the crop.
_SHAPES = (
    ((0, 0), (1, 0), (1, 1)),  # L triomino
    ((0, 0), (0, 1)),          # horizontal domino
    ((0, 0), (1, 0)),          # vertical domino
    ((0, 0), (0, 1), (1, 0)),  # mirrored L triomino
    ((0, 0), (0, 1), (1, 0), (1, 1)),
)
_FIRST_WINNER_SHAPE = _SHAPES[0]
_LAST_RIVAL_SHAPE = _SHAPES[1]


def schedule_profile(seed: int, sample_index: int, difficulty=None):
    """Return the finite semantic/profile role for schedule census tooling."""
    del seed, difficulty
    if sample_index % 2 == 0:
        return ("rich", sample_index % LESSON_SCHEDULE_PERIOD)
    profile_index = (sample_index // 2) % len(_CANONICAL_PROFILES)
    return ("canonical", profile_index)


SCHEDULE_PROFILES = tuple(
    schedule_profile(0, index) for index in range(LESSON_SCHEDULE_PERIOD)
)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")

    bounds = {"grid_h": (8, 16), "grid_w": (10, 18), "n_header": (2, 4)}
    for name, (lo, hi) in bounds.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")

    texture = overrides.get("texture")
    if texture is not None:
        if not isinstance(texture, str):
            raise TypeError(f"texture must be a string, not {type(texture).__name__}")
        if texture not in TEXTURES:
            raise ValueError(f"texture={texture!r} is not one of {TEXTURES}")


def _draw_int_axis(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_texture(ctx, scheduled: str) -> str:
    if ctx.overrides.get("texture") is not None:
        return ctx.draw_choice("texture", TEXTURES)
    return ctx.draw_choice("texture", (scheduled,))


def _scheduled_defaults(ctx, sample_index: int, difficulty) -> tuple[int, int, int, str]:
    if sample_index % 2 == 1:
        h, w, n_header = _CANONICAL_PROFILES[
            (sample_index // 2) % len(_CANONICAL_PROFILES)
        ]
        return h, w, n_header, "plain"

    ranges = {
        "easy": ((8, 10), (10, 13)),
        "medium": ((10, 13), (12, 15)),
        "hard": ((13, 16), (15, 18)),
    }
    (h_lo, h_hi), (w_lo, w_hi) = ranges.get(
        difficulty, ((9, 15), (11, 17))
    )
    rng = ctx.draw_rng("broad_dimensions")
    return rng.randint(h_lo, h_hi), rng.randint(w_lo, w_hi), 4, "rich"


def _placement_slots(h: int, w: int) -> list[tuple[int, int]]:
    """Six scan-ordered 2x2 slots, valid at the 8x10 lower boundary."""
    rows = (2, h - 2)
    cols = (0, (w - 2) // 2, w - 2)
    return [(row, col) for row in rows for col in cols]


def _put_shape(grid, top: int, left: int, colour: int, shape) -> None:
    for dr, dc in shape:
        if grid[top + dr][left + dc] != 0:
            raise RuntimeError("constructive body placement collided")
        grid[top + dr][left + dc] = colour


def _header_sequence(colours: list[int], texture: str) -> list[int]:
    sequence = list(colours)
    if texture in {"repeat_header", "rich"}:
        sequence.append(colours[0])
    return sequence


def _body_specs(
    colours: list[int], texture: str, decoy_colour: int | None, rng
) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    absent = colours[-1] if texture in {"absent_color", "rich"} else None
    present = [colour for colour in colours if colour != absent]

    # Reverse the primary object scan order relative to the header whenever
    # there is more than one present colour.  This makes header order visible.
    specs: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    for index, colour in enumerate(reversed(present)):
        if texture in {"first_wins", "rich"} and colour == colours[0]:
            shape = _FIRST_WINNER_SHAPE
        else:
            shape = _SHAPES[(index + rng.randrange(len(_SHAPES))) % len(_SHAPES)]
        specs.append((colour, shape))

    if texture in {"first_wins", "rich"}:
        specs.append((colours[0], _LAST_RIVAL_SHAPE))
    if texture in {"decoy_colors", "rich"}:
        if decoy_colour is None:
            raise RuntimeError("decoy texture requested without a decoy colour")
        specs.append((decoy_colour, _SHAPES[2]))
    return specs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_n_header, default_texture = _scheduled_defaults(
        ctx, sample_index, difficulty
    )
    h = _draw_int_axis(ctx, "grid_h", 8, 16, default_h)
    w = _draw_int_axis(ctx, "grid_w", 10, 18, default_w)
    n_header = _draw_int_axis(ctx, "n_header", 2, 4, default_n_header)
    texture = _draw_texture(ctx, default_texture)

    rng = ctx.draw_rng("layout")
    colour_pool = list(range(1, 10))
    rng.shuffle(colour_pool)
    header_colours = colour_pool[:n_header]
    decoy_colour = colour_pool[n_header] if texture in {"decoy_colors", "rich"} else None

    grid = full_grid(h, w, 0)
    sequence = _header_sequence(header_colours, texture)
    header_columns = sorted(rng.sample(range(w), len(sequence)))
    for column, colour in zip(header_columns, sequence):
        grid[0][column] = colour

    specs = _body_specs(header_colours, texture, decoy_colour, rng)
    slots = sorted(rng.sample(_placement_slots(h, w), len(specs)))
    for (colour, shape), (top, left) in zip(specs, slots):
        _put_shape(grid, top, left, colour, shape)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise RuntimeError("constructed invalid header-pack grid: " + "; ".join(errors))
    return grid


def _coerce_grid(grid) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if any(not isinstance(row, list) or not row for row in grid):
        return None, ["every row must be a nonempty list"]
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return None, ["grid is ragged"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["grid colours must be integers in 0..9"]
    return [list(row) for row in grid], []


def _objects(body: list[list[int]]) -> list[dict[str, Any]]:
    if not body:
        return []
    h, w = len(body), len(body[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(h):
        for col in range(w):
            colour = body[row][col]
            if colour == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and body[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            components.append(
                {
                    "colour": colour,
                    "cells": tuple(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return components


def _crop(body: list[list[int]], obj: dict[str, Any]) -> list[list[int]]:
    top, left, bottom, right = obj["bbox"]
    return [row[left : right + 1] for row in body[top : bottom + 1]]


def _pack(pieces: list[list[list[int]]]) -> list[list[int]]:
    if not pieces:
        return [[0]]
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    output = [[0] * width for _ in range(height)]
    left = 0
    for piece in pieces:
        for row, values in enumerate(piece):
            for col, value in enumerate(values):
                if value != 0:
                    output[row][left + col] = value
        left += len(piece[0]) + 1
    return output


def _header(grid: list[list[int]]) -> list[int]:
    return [value for value in grid[0] if value != 0]


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the pinned Racket authority."""
    clean, errors = _coerce_grid(grid)
    if errors or clean is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    header = _header(clean)
    body = clean[1:]
    components = _objects(body)
    pieces = []
    for colour in header:
        hit = next((obj for obj in components if obj["colour"] == colour), None)
        if hit is not None:
            pieces.append(_crop(body, hit))
    return _pack(pieces)


# Compatibility name retained for older task-local probes.
_mirror = rule_mirror


def _solve_with(
    grid,
    *,
    deduplicate_header: bool = False,
    choose_last: bool = False,
    require_all: bool = False,
    append_decoys: bool = False,
    body_scan_order: bool = False,
) -> list[list[int]]:
    clean, errors = _coerce_grid(grid)
    if errors or clean is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    header = _header(clean)
    body = clean[1:]
    components = _objects(body)

    if deduplicate_header:
        header = list(dict.fromkeys(header))
    if require_all and any(not any(obj["colour"] == colour for obj in components) for colour in header):
        return [[0]]

    pieces: list[list[list[int]]] = []
    if body_scan_order:
        wanted = set(header)
        seen_colours: set[int] = set()
        for obj in components:
            colour = obj["colour"]
            if colour in wanted and colour not in seen_colours:
                pieces.append(_crop(body, obj))
                seen_colours.add(colour)
    else:
        for colour in header:
            hits = [obj for obj in components if obj["colour"] == colour]
            if hits:
                pieces.append(_crop(body, hits[-1] if choose_last else hits[0]))

    if append_decoys:
        selected = set(header)
        pieces.extend(_crop(body, obj) for obj in components if obj["colour"] not in selected)
    return _pack(pieces)


def _rival_body_scan_order(grid):
    return _solve_with(grid, body_scan_order=True)


def _rival_deduplicate_header(grid):
    return _solve_with(grid, deduplicate_header=True)


def _rival_last_object(grid):
    return _solve_with(grid, choose_last=True)


def _rival_require_all(grid):
    return _solve_with(grid, require_all=True)


def _rival_append_decoys(grid):
    return _solve_with(grid, append_decoys=True)


def _analysis(grid) -> dict[str, Any]:
    clean, errors = _coerce_grid(grid)
    if errors or clean is None:
        return {"errors": errors}
    h, w = len(clean), len(clean[0])
    header = _header(clean)
    body = clean[1:]
    components = _objects(body)
    object_counts = Counter(obj["colour"] for obj in components)
    header_counts = Counter(header)
    header_colours = list(dict.fromkeys(header))
    header_set = set(header_colours)
    absent = [colour for colour in header_colours if object_counts[colour] == 0]
    repeated = [colour for colour, count in header_counts.items() if count > 1]
    multiple = [colour for colour in header_colours if object_counts[colour] > 1]
    decoys = [obj for obj in components if obj["colour"] not in header_set]

    texture = "mixed"
    flags = (bool(absent), bool(repeated), bool(multiple), bool(decoys))
    if flags == (False, False, False, False):
        texture = "plain"
    elif flags == (True, False, False, False) and len(absent) == 1:
        texture = "absent_color"
    elif flags == (False, True, False, False) and len(repeated) == 1:
        texture = "repeat_header"
    elif flags == (False, False, True, False) and len(multiple) == 1:
        texture = "first_wins"
    elif flags == (False, False, False, True) and len(decoys) == 1:
        texture = "decoy_colors"
    elif all(flags) and len(absent) == len(repeated) == len(multiple) == len(decoys) == 1:
        texture = "rich"

    present_header_order = [
        colour for colour in header_colours if object_counts[colour] > 0
    ]
    body_selected_order = []
    for obj in components:
        colour = obj["colour"]
        if colour in header_set and colour not in body_selected_order:
            body_selected_order.append(colour)

    return {
        "errors": [],
        "grid": clean,
        "height": h,
        "width": w,
        "header": header,
        "header_counts": header_counts,
        "header_colours": header_colours,
        "components": components,
        "object_counts": object_counts,
        "absent": absent,
        "repeated": repeated,
        "multiple": multiple,
        "decoys": decoys,
        "texture": texture,
        "header_order_differs": (
            len(present_header_order) >= 2
            and body_selected_order[: len(present_header_order)] != present_header_order
        ),
    }


def observe_overrides(grid) -> dict[str, Any]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(facts["errors"]))
    if facts["texture"] == "mixed":
        raise ValueError("grid does not match one declared texture")
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_header": len(facts["header_colours"]),
        "texture": facts["texture"],
    }


def _meta_overrides(meta) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    if isinstance(nested, dict):
        return {name: value for name, value in nested.items() if name in AXES and value is not None}
    return {name: value for name, value in meta.items() if name in AXES and value is not None}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts = _analysis(grid)
    errors = list(facts["errors"])
    if errors:
        return errors

    h, w = facts["height"], facts["width"]
    clean = facts["grid"]
    if not 8 <= h <= 16:
        errors.append(f"height {h} outside generator domain 8..16")
    if not 10 <= w <= 18:
        errors.append(f"width {w} outside generator domain 10..18")
    if any(clean[1]):
        errors.append("row 1 must be a blank separator")

    header = facts["header"]
    distinct = facts["header_colours"]
    if not 2 <= len(distinct) <= 4:
        errors.append(f"header must contain 2..4 distinct colours, got {len(distinct)}")
    if len(header) not in {len(distinct), len(distinct) + 1}:
        errors.append("header may repeat at most one token")
    if any(count > 2 for count in facts["header_counts"].values()):
        errors.append("a header colour may occur at most twice")
    if sum(count == 2 for count in facts["header_counts"].values()) > 1:
        errors.append("at most one header colour may repeat")

    components = facts["components"]
    if not 1 <= len(components) <= 6:
        errors.append(f"body must contain 1..6 objects, got {len(components)}")
    occupied_by_object: dict[tuple[int, int], int] = {}
    for index, obj in enumerate(components):
        size = len(obj["cells"])
        if not 2 <= size <= 6:
            errors.append(f"object {index} has {size} cells; expected 2..6")
        top, left, bottom, right = obj["bbox"]
        if bottom - top + 1 > 3 or right - left + 1 > 4:
            errors.append(f"object {index} bbox is too large for the task manifold")
        for cell in obj["cells"]:
            occupied_by_object[cell] = index

    for (row, col), owner in occupied_by_object.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                other = occupied_by_object.get((row + dr, col + dc))
                if other is not None and other != owner:
                    errors.append("body object bounding halos touch")
                    break
            else:
                continue
            break
        if errors and errors[-1] == "body object bounding halos touch":
            break

    if len(facts["absent"]) > 1:
        errors.append("at most one distinct header colour may be absent")
    if len(facts["multiple"]) > 1:
        errors.append("at most one header colour may have multiple body objects")
    if any(facts["object_counts"][colour] > 2 for colour in facts["header_colours"]):
        errors.append("a header colour may have at most two body objects")
    decoy_colours = {obj["colour"] for obj in facts["decoys"]}
    if len(facts["decoys"]) > 1 or len(decoy_colours) > 1:
        errors.append("at most one non-header decoy object is allowed")
    if not any(facts["object_counts"][colour] for colour in facts["header_colours"]):
        errors.append("at least one header colour must select a body object")
    if facts["texture"] not in TEXTURES:
        errors.append("input combines texture features outside the declared grammar")

    try:
        output = rule_mirror(clean)
        if output == [[0]]:
            errors.append("ordinary generator domain may not pack to [[0]]")
        elif len(output[0]) > 30:
            errors.append(f"packed output width {len(output[0])} exceeds 30")
    except Exception as exc:  # pragma: no cover - defensive after structural checks
        errors.append(f"rule mirror failed: {type(exc).__name__}: {exc}")

    if not errors:
        requested = _meta_overrides(meta)
        if requested:
            observed = observe_overrides(clean)
            for name, value in requested.items():
                if observed.get(name) != value:
                    errors.append(
                        f"override {name}={value!r} realized as {observed.get(name)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical/generator manifold used by the semantic gate."""
    return list(self_check(grid))


def _features(grid) -> dict[str, Any]:
    facts = _analysis(grid)
    if facts["errors"]:
        return {}
    return {
        "header_order_differs": facts["header_order_differs"],
        "absent_header_colour": bool(facts["absent"]),
        "repeated_header_colour": bool(facts["repeated"]),
        "multiple_objects_same_header_colour": bool(facts["multiple"]),
        "non_header_decoy": bool(facts["decoys"]),
    }


def _witness(name: str) -> Callable[[list[list[int]]], bool]:
    return lambda grid: bool(_features(grid).get(name, False))


SEMANTIC_WITNESSES = {
    "header_order_differs": _witness("header_order_differs"),
    "absent_header_colour": _witness("absent_header_colour"),
    "repeated_header_colour": _witness("repeated_header_colour"),
    "multiple_objects_same_header_colour": _witness(
        "multiple_objects_same_header_colour"
    ),
    "non_header_decoy": _witness("non_header_decoy"),
}
SEMANTIC_RIVALS = {
    "body_scan_order": _rival_body_scan_order,
    "deduplicate_header": _rival_deduplicate_header,
    "last_object_of_color": _rival_last_object,
    "require_all_header_colors": _rival_require_all,
    "append_non_header_objects": _rival_append_decoys,
}
WITNESS_RIVALS = {
    "header_order_differs": ("body_scan_order",),
    "repeated_header_colour": ("deduplicate_header",),
    "multiple_objects_same_header_colour": ("last_object_of_color",),
    "absent_header_colour": ("require_all_header_colors",),
    "non_header_decoy": ("append_non_header_objects",),
}
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "deduplicate_header",
        "last_object_of_color",
        "require_all_header_colors",
        "append_non_header_objects",
    )
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
MIN_STRICT_FRAC = 0.5


def _pair_errors(pair, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair:
        return [f"{label} is not a labeled pair"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label}: {message}" for message in errors]
    expected = rule_mirror(pair["input"])
    if pair.get("output") is not None and pair.get("output") != expected:
        return [f"{label} output disagrees with the pinned header-pack rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons on which a named plausible rival remains viable."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    reasons.extend(_pair_errors(query, "query"))
    if reasons:
        return reasons

    query_answer = rule_mirror(deepcopy(query["input"]))
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(
            rival(deepcopy(pair["input"])) == pair.get("output") for pair in demos
        )
        if survives and rival(deepcopy(query["input"])) != query_answer:
            reasons.append(f"demonstrations remain consistent with rival: {name}")
    return reasons

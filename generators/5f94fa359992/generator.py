"""Generator for 9b:m61 — order tightly cropped framed figures by key.

A row of maroon (9) rectangular frames contains one monochrome figure per
frame.  Each frame has exactly one non-maroon key cell directly above its top
edge.  The oracle tightly crops each figure, sorts the crops by ascending key
value, vertically centers them in the tallest crop, and separates neighbors by
one blank column.

The canonical task has five linked 9x18 profiles: three 5x5 frames at columns
1, 7, and 13, centered keys, profile-specific key ranks, figure masks, and
key/figure color-equality relations.  Every fourth default draw selects one
whole canonical profile before applying only lawful nuisance variation (color
renaming and figure translation inside its frame).  The other three schedule
slots broaden frame count/size, key order, figure-height pattern, role-color
relation, and key position while guaranteeing that every four consecutive
examples refute reading-order, uncropped-interior, top-alignment, and
figure-color-sort shortcuts.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "5f94fa359992"
TASK_ID = GENERATOR_ID
RULE_HASH = "c5cd0106e07a"
VERSION = "3.0.0"

SUMMARY = (
    "A 0-background grid contains three or four horizontally separated, "
    "equally sized hollow color-9 square frames. Each frame contains one "
    "monochrome figure and has one distinct nonzero/non-9 key directly above "
    "it. Tight-crop every figure, sort the crops by ascending key value, "
    "vertically center them in the tallest crop, and hstack them with one "
    "blank column between neighbors."
)

INVARIANTS = [
    "background is 0 outside frame perimeters, figures, and keys",
    "three or four separated hollow color-9 square frames of common size 5 or 6",
    "each frame contains exactly one nonempty monochrome figure",
    "each frame has exactly one key directly above it and all keys are distinct",
    "key colors and figure colors may overlap across roles",
    "output uses tight figure crops, ascending key order, one-column gaps, and vertical centering",
]

AXES = {
    "n_frames": {
        "type": "int",
        "default": "linked four-slot schedule / canonical prior",
        "valid": "3..4",
    },
    "frame_size": {
        "type": "int",
        "default": "linked four-slot schedule / canonical prior",
        "valid": "5..6",
    },
    "key_order": {
        "type": "str",
        "default": "linked four-slot schedule / canonical profile",
        "valid": "ascending|descending|mixed",
    },
    "figure_height_pattern": {
        "type": "str",
        "default": "linked four-slot schedule / canonical profile",
        "valid": "uniform|varied",
    },
    "color_relation": {
        "type": "str",
        "default": "linked four-slot schedule / canonical profile",
        "valid": "disjoint|overlap",
    },
    "key_position": {
        "type": "str",
        "default": "linked four-slot schedule / canonical profile",
        "valid": "centered|varied",
    },
}

# Every valid cross-product is constructible.  Declaring the empty set opts the
# override checker into strict classification instead of legacy warning mode.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Each frame spec is (key_rank, tight_binary_mask, figure_equals_key_rank).
# figure_equals_key_rank is -1 when the figure color is outside the key set.
# Geometry is the canonical 9x18 row of 5x5 frames at c=1,7,13 with centered
# keys.  Figure translation inside the 3x3 interior is intentionally omitted:
# tight cropping makes it a lawful nuisance.
_CANONICAL_PROFILES = (
    (
        (1, ((1, 0), (1, 0), (1, 1)), 0),
        (2, ((1, 1), (1, 1)), 2),
        (0, ((1, 0, 1), (1, 1, 1)), -1),
    ),
    (
        (0, ((1, 1, 1), (1, 0, 0), (1, 0, 0)), 2),
        (2, ((1, 1), (1, 1)), -1),
        (1, ((1, 1), (1, 1)), 0),
    ),
    (
        (1, ((1, 1, 1), (1, 0, 0), (1, 0, 0)), -1),
        (2, ((1, 1, 1), (0, 1, 0)), 1),
        (0, ((1, 1), (1, 1)), 2),
    ),
    (
        (0, ((1, 1, 1), (0, 1, 0)), 1),
        (1, ((1, 0, 1), (1, 1, 1)), -1),
        (2, ((1, 1), (1, 1)), -1),
    ),
    (
        (1, ((1, 1, 1), (1, 0, 0), (1, 0, 0)), 2),
        (2, ((1, 1, 1), (0, 1, 0)), -1),
        (0, ((1, 1, 1), (1, 0, 0), (1, 0, 0)), -1),
    ),
)

# Slots 1..3 in every four-example window.  Slot 0 is one complete canonical
# profile.  Therefore every cyclic window of length EXAMPLES_NEEDED contains
# a canonical anchor plus all three broad teaching profiles.
_GENERAL_PROFILES = (
    (3, 5, "ascending", "varied", "overlap", "varied"),
    (4, 5, "descending", "uniform", "disjoint", "centered"),
    (3, 6, "mixed", "varied", "disjoint", "varied"),
)

_MASK_BANK = (
    ((1,),),
    ((1, 1),),
    ((1, 1, 1),),
    ((1, 1, 1, 1),),
    ((1, 0), (1, 1)),
    ((1, 1), (1, 1)),
    ((1, 0, 1), (1, 1, 1)),
    ((1, 1, 1), (0, 1, 0)),
    ((1, 0, 0, 1), (1, 1, 1, 1)),
    ((1, 1, 1, 1), (0, 1, 1, 0)),
    ((1, 0), (1, 0), (1, 1)),
    ((1, 1, 1), (1, 0, 0), (1, 0, 0)),
    ((1, 1, 0), (0, 1, 1), (0, 0, 1)),
    ((1, 0, 1), (1, 1, 1), (0, 1, 0)),
    ((1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 1, 1)),
    ((1, 1, 1, 1), (1, 0, 0, 0), (1, 1, 1, 0), (0, 0, 1, 1)),
)


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components_of_color(grid, color: int):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[tuple[int, int], ...]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(tuple(sorted(cells)))
    return components


def _is_connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _DIRS4:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == cells


def _frame_records(grid):
    """Parse exact maroon rectangle components and their key/figure roles."""
    records = []
    for component in _components_of_color(grid, 9):
        r0 = min(r for r, _ in component)
        c0 = min(c for _, c in component)
        r1 = max(r for r, _ in component)
        c1 = max(c for _, c in component)
        perimeter = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if set(component) != perimeter:
            continue
        key_cells = []
        if r0 > 0:
            key_cells = [
                (r0 - 1, c, grid[r0 - 1][c])
                for c in range(c0, c1 + 1)
                if grid[r0 - 1][c] not in (0, 9)
            ]
        figure_cells = [
            (r, c, grid[r][c])
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] != 0
        ]
        mask = None
        if figure_cells:
            fr0 = min(r for r, _, _ in figure_cells)
            fc0 = min(c for _, c, _ in figure_cells)
            fr1 = max(r for r, _, _ in figure_cells)
            fc1 = max(c for _, c, _ in figure_cells)
            mask = tuple(
                tuple(1 if grid[r][c] != 0 else 0 for c in range(fc0, fc1 + 1))
                for r in range(fr0, fr1 + 1)
            )
        records.append({
            "bbox": (r0, c0, r1, c1),
            "perimeter": perimeter,
            "keys": key_cells,
            "figure_cells": figure_cells,
            "figure_colors": {value for _, _, value in figure_cells},
            "mask": mask,
        })
    return sorted(records, key=lambda record: record["bbox"][:2])


def _key_order(records) -> str | None:
    if not records or any(len(record["keys"]) != 1 for record in records):
        return None
    values = [record["keys"][0][2] for record in records]
    if len(set(values)) != len(values):
        return None
    if values == sorted(values):
        return "ascending"
    if values == sorted(values, reverse=True):
        return "descending"
    return "mixed"


def canonical_profile_signature(grid):
    """Return the complete linked official-profile signature, or ``None``.

    Colors are quotiented only by key rank.  Figure/key equality is retained,
    while figure translation inside a frame is omitted because the authority
    tight-crops it away.
    """
    if _grid_errors(grid):
        return None
    records = _frame_records(grid)
    if len(records) != 3 or any(len(record["keys"]) != 1 for record in records):
        return None
    key_values = [record["keys"][0][2] for record in records]
    if len(set(key_values)) != 3:
        return None
    rank = {value: index for index, value in enumerate(sorted(key_values))}
    frame_signatures = []
    for record in records:
        if len(record["figure_colors"]) != 1 or record["mask"] is None:
            return None
        r0, c0, r1, c1 = record["bbox"]
        key_r, key_c, key_value = record["keys"][0]
        figure_color = next(iter(record["figure_colors"]))
        frame_signatures.append((
            (r0, c0, r1, c1),
            key_c - c0,
            rank[key_value],
            record["mask"],
            rank.get(figure_color, -1),
        ))
    return len(grid), len(grid[0]), tuple(frame_signatures)


def _signature_from_profile(profile):
    frames = []
    for index, (key_rank, mask, figure_relation) in enumerate(profile):
        c0 = 1 + 6 * index
        frames.append(((2, c0, 6, c0 + 4), 2, key_rank, mask, figure_relation))
    return 9, 18, tuple(frames)


_CANONICAL_SIGNATURES = frozenset(
    _signature_from_profile(profile) for profile in _CANONICAL_PROFILES
)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding scenes in the teaching grammar."""
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not (9 <= h <= 12 and 17 <= w <= 30):
        errors.append(f"dimensions {h}x{w} outside generator envelope 9..12 x 17..30")

    color9_components = _components_of_color(grid, 9)
    records = _frame_records(grid)
    if len(color9_components) != len(records):
        errors.append("every color-9 component must be one complete rectangle perimeter")
    if not 3 <= len(records) <= 4:
        errors.append(f"expected 3..4 frames, found {len(records)}")
    if not records:
        return errors

    bboxes = [record["bbox"] for record in records]
    sizes = {(r1 - r0 + 1, c1 - c0 + 1) for r0, c0, r1, c1 in bboxes}
    if len(sizes) != 1:
        errors.append("all frames must share one size")
    elif next(iter(sizes))[0] != next(iter(sizes))[1] or next(iter(sizes))[0] not in (5, 6):
        errors.append(f"frames must be common 5x5 or 6x6 squares, found {sorted(sizes)}")
    if len({(r0, r1) for r0, _, r1, _ in bboxes}) != 1:
        errors.append("frames must share one horizontal row")
    for left, right in zip(records, records[1:]):
        if left["bbox"][3] + 1 >= right["bbox"][1]:
            errors.append("neighboring frames need at least one blank separator column")
            break

    key_values = []
    allowed_nonzero: set[tuple[int, int]] = set()
    for index, record in enumerate(records):
        allowed_nonzero.update(record["perimeter"])
        if len(record["keys"]) != 1:
            errors.append(f"frame {index} has {len(record['keys'])} keys; expected exactly one")
        else:
            kr, kc, kv = record["keys"][0]
            allowed_nonzero.add((kr, kc))
            key_values.append(kv)
        if not record["figure_cells"]:
            errors.append(f"frame {index} has no figure")
            continue
        allowed_nonzero.update((r, c) for r, c, _ in record["figure_cells"])
        if len(record["figure_colors"]) != 1:
            errors.append(f"frame {index} figure must be monochrome")
        cells = {(r, c) for r, c, _ in record["figure_cells"]}
        if not _is_connected(cells):
            errors.append(f"frame {index} figure must be 4-connected")
    if len(key_values) != len(set(key_values)):
        errors.append("key colors must be pairwise distinct")

    stray = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0 and (r, c) not in allowed_nonzero
    ]
    if stray:
        errors.append(f"found {len(stray)} nonzero cell(s) outside frame/key/figure roles")
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    signature = canonical_profile_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        return ["scene is lawful but not one complete linked official profile"]
    return []


def observe_overrides(grid) -> dict[str, object]:
    """Recover every exact semantic axis from the returned grid."""
    if _grid_errors(grid):
        return {}
    records = _frame_records(grid)
    if not records or any(len(record["keys"]) != 1 for record in records):
        return {}
    sizes = {record["bbox"][2] - record["bbox"][0] + 1 for record in records}
    heights = {
        len(record["mask"]) for record in records if record["mask"] is not None
    }
    key_colors = {record["keys"][0][2] for record in records}
    figure_colors = set().union(*(record["figure_colors"] for record in records))
    centered = True
    for record in records:
        r0, c0, r1, c1 = record["bbox"]
        key_offset = record["keys"][0][1] - c0
        if key_offset != (c1 - c0 + 1) // 2:
            centered = False
            break
    return {
        "n_frames": len(records),
        "frame_size": next(iter(sizes)) if len(sizes) == 1 else -1,
        "key_order": _key_order(records) or "invalid",
        "figure_height_pattern": "uniform" if len(heights) == 1 else "varied",
        "color_relation": "overlap" if key_colors & figure_colors else "disjoint",
        "key_position": "centered" if centered else "varied",
    }


def _crop_figure(grid, record):
    cells = record["figure_cells"]
    r0 = min(r for r, _, _ in cells)
    c0 = min(c for _, c, _ in cells)
    r1 = max(r for r, _, _ in cells)
    c1 = max(c for _, c, _ in cells)
    return [
        [grid[r][c] if grid[r][c] != 9 else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _interior(grid, record):
    r0, c0, r1, c1 = record["bbox"]
    return [row[c0 + 1:c1] for row in grid[r0 + 1:r1]]


def _pack(pieces, *, vertical: str = "center"):
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = full_grid(height, width, 0)
    left = 0
    for piece in pieces:
        if vertical == "center":
            top = (height - len(piece)) // 2
        elif vertical == "bottom":
            top = height - len(piece)
        else:
            top = 0
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value != 0:
                    out[top + r][left + c] = value
        left += len(piece[0]) + 1
    return out


def rule_mirror(grid):
    """Python spelling of the selected Racket rule for semantic evidence."""
    records = _frame_records(grid)
    ordered = sorted(records, key=lambda record: record["keys"][0][2])
    return _pack([_crop_figure(grid, record) for record in ordered])


def _rival_reading_order(grid):
    records = _frame_records(grid)
    return _pack([_crop_figure(grid, record) for record in records])


def _rival_uncropped_interiors(grid):
    records = sorted(_frame_records(grid), key=lambda record: record["keys"][0][2])
    return _pack([_interior(grid, record) for record in records])


def _rival_top_aligned(grid):
    records = sorted(_frame_records(grid), key=lambda record: record["keys"][0][2])
    return _pack([_crop_figure(grid, record) for record in records], vertical="top")


def _rival_sort_by_figure_color(grid):
    records = sorted(
        _frame_records(grid),
        key=lambda record: min(record["figure_colors"]),
    )
    return _pack([_crop_figure(grid, record) for record in records])


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "reading_order": _rival_reading_order,
    "uncropped_interiors": _rival_uncropped_interiors,
    "top_aligned": _rival_top_aligned,
    "sort_by_figure_color": _rival_sort_by_figure_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_reordering(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != _rival_reading_order(grid)


def _witness_tight_crop(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != _rival_uncropped_interiors(grid)


def _witness_vertical_center(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != _rival_top_aligned(grid)


def _witness_figure_color_independence(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != _rival_sort_by_figure_color(grid)


def _witness_role_color_overlap(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid).get("color_relation") == "overlap"


def _witness_varied_key_position(grid) -> bool:
    return not self_check(grid) and observe_overrides(grid).get("key_position") == "varied"


SEMANTIC_WITNESSES = {
    "key_order_changes_visual_order": _witness_reordering,
    "tight_crop_changes_output_extent": _witness_tight_crop,
    "vertical_centering_changes_rows": _witness_vertical_center,
    "figure_color_does_not_choose_order": _witness_figure_color_independence,
}
WITNESS_RIVALS = {
    "key_order_changes_visual_order": ["reading_order"],
    "tight_crop_changes_output_extent": ["uncropped_interiors"],
    "vertical_centering_changes_rows": ["top_aligned"],
    "figure_color_does_not_choose_order": ["sort_by_figure_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible rival survives all demos."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration pair is required"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return [f"demo {index} is not an input/output pair"]
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output does not match the selected rule")
    if not isinstance(query, dict) or "input" not in query:
        return reasons + ["query is not an input pair"]
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")
        return reasons
    expected = rule_mirror(query["input"])
    if "output" in query and query["output"] != expected:
        reasons.append("query output does not match the selected rule")
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != expected:
            reasons.append(
                f"competing rule '{name}' fits every demo but changes the query answer"
            )
    return reasons


def _validate_call(sample_index, difficulty, overrides):
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    for name in ("n_frames", "frame_size"):
        if name in overrides and (
            isinstance(overrides[name], bool) or not isinstance(overrides[name], int)
        ):
            raise ValueError(f"{name} override must be an integer")
    allowed = {
        "key_order": {"ascending", "descending", "mixed"},
        "figure_height_pattern": {"uniform", "varied"},
        "color_relation": {"disjoint", "overlap"},
        "key_position": {"centered", "varied"},
    }
    for name, values in allowed.items():
        if name in overrides and overrides[name] not in values:
            raise ValueError(f"{name} override must be one of {sorted(values)}")


def _consume_axes(ctx, values):
    n_frames, frame_size, key_order, height_pattern, color_relation, key_position = values
    return (
        ctx.draw_int("n_frames", n_frames, n_frames),
        ctx.draw_int("frame_size", frame_size, frame_size),
        ctx.draw_choice("key_order", (key_order,)),
        ctx.draw_choice("figure_height_pattern", (height_pattern,)),
        ctx.draw_choice("color_relation", (color_relation,)),
        ctx.draw_choice("key_position", (key_position,)),
    )


def _profile_axes(profile):
    ranks = [spec[0] for spec in profile]
    heights = {len(spec[1]) for spec in profile}
    return (
        3,
        5,
        "ascending" if ranks == sorted(ranks) else "descending" if ranks == sorted(ranks, reverse=True) else "mixed",
        "uniform" if len(heights) == 1 else "varied",
        "overlap" if any(spec[2] >= 0 for spec in profile) else "disjoint",
        "centered",
    )


def _draw_frame(grid, r0, c0, size):
    r1, c1 = r0 + size - 1, c0 + size - 1
    for c in range(c0, c1 + 1):
        grid[r0][c] = 9
        grid[r1][c] = 9
    for r in range(r0, r1 + 1):
        grid[r][c0] = 9
        grid[r][c1] = 9


def _draw_canonical_profile(profile, rng):
    grid = full_grid(9, 18, 0)
    sorted_keys = sorted(rng.sample(range(1, 9), 3))
    nonkeys = [color for color in range(1, 9) if color not in sorted_keys]
    rng.shuffle(nonkeys)
    nonkey_index = 0
    for index, (key_rank, mask, figure_relation) in enumerate(profile):
        c0 = 1 + 6 * index
        _draw_frame(grid, 2, c0, 5)
        key_color = sorted_keys[key_rank]
        grid[1][c0 + 2] = key_color
        if figure_relation >= 0:
            figure_color = sorted_keys[figure_relation]
        else:
            figure_color = nonkeys[nonkey_index]
            nonkey_index += 1
        mh, mw = len(mask), len(mask[0])
        top = 3 + rng.randint(0, 3 - mh)
        left = c0 + 1 + rng.randint(0, 3 - mw)
        for r, row in enumerate(mask):
            for c, value in enumerate(row):
                if value:
                    grid[top + r][left + c] = figure_color
    return grid


def _mixed_ranks(n):
    if n == 3:
        return [1, 2, 0]
    return [1, 3, 0, 2]


def _shape_for_height(height, inner_size, index, rng):
    candidates = [
        mask for mask in _MASK_BANK
        if len(mask) == height and len(mask[0]) <= inner_size
    ]
    if not candidates:
        raise ValueError(f"no figure mask for height={height}, inner={inner_size}")
    return candidates[(rng.randrange(len(candidates)) + index) % len(candidates)]


def _draw_general(values, rng, difficulty):
    n_frames, frame_size, key_order, height_pattern, color_relation, key_position = values
    inner_size = frame_size - 2
    if height_pattern == "uniform":
        heights = [2] * n_frames
    else:
        heights = [1, inner_size] + [2 + (index % max(1, inner_size - 2)) for index in range(n_frames - 2)]
    masks = [_shape_for_height(height, inner_size, index, rng) for index, height in enumerate(heights)]

    key_pool = rng.sample(range(1, 9), n_frames)
    sorted_keys = sorted(key_pool)
    if key_order == "ascending":
        ranks = list(range(n_frames))
    elif key_order == "descending":
        ranks = list(reversed(range(n_frames)))
    else:
        ranks = _mixed_ranks(n_frames)
    key_colors = [sorted_keys[rank] for rank in ranks]

    if color_relation == "overlap":
        figure_colors = key_colors[1:] + key_colors[:1]
    else:
        remaining = [color for color in range(1, 9) if color not in key_colors]
        rng.shuffle(remaining)
        figure_colors = remaining[:n_frames]
        # Make the figure-color ranking visibly independent of key ranking.
        if figure_colors == sorted(figure_colors, key=lambda value: value):
            figure_colors = figure_colors[1:] + figure_colors[:1]

    # Difficulty changes only lawful canvas placement: the rule and every
    # observable semantic axis stay fixed, while the three curriculum bands
    # no longer collapse to byte-identical examples.
    r0 = 2 + {"medium": 1, "hard": 2}.get(difficulty, 0)
    gap_choices = [1, 2]
    if n_frames == 4 and frame_size == 6:
        gap_choices = [1]
    gap = gap_choices[rng.randrange(len(gap_choices))]
    left_margin = rng.randint(0, 1)
    right_margin = rng.randint(0, 1)
    width = left_margin + n_frames * frame_size + (n_frames - 1) * gap + right_margin
    height = r0 + frame_size + 2
    grid = full_grid(height, width, 0)

    for index in range(n_frames):
        c0 = left_margin + index * (frame_size + gap)
        _draw_frame(grid, r0, c0, frame_size)
        center_offset = frame_size // 2
        if key_position == "centered":
            key_offset = center_offset
        else:
            varied_offsets = [0, frame_size - 1, 1, frame_size - 2]
            key_offset = varied_offsets[index % len(varied_offsets)]
        grid[r0 - 1][c0 + key_offset] = key_colors[index]

        mask = masks[index]
        mh, mw = len(mask), len(mask[0])
        top = r0 + 1 + rng.randint(0, inner_size - mh)
        left = c0 + 1 + rng.randint(0, inner_size - mw)
        for mr, row in enumerate(mask):
            for mc, value in enumerate(row):
                if value:
                    grid[top + mr][left + mc] = figure_colors[index]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the Racket oracle owns output."""
    _validate_call(sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("scene_layout")

    canonical_profile = None
    if not overrides and sample_index % EXAMPLES_NEEDED == 0:
        canonical_profile = _CANONICAL_PROFILES[
            ctx.draw_rng("canonical_profile").randrange(len(_CANONICAL_PROFILES))
        ]
        selected = _profile_axes(canonical_profile)
    else:
        slot = sample_index % EXAMPLES_NEEDED
        base = list(_GENERAL_PROFILES[(slot - 1) % len(_GENERAL_PROFILES)])
        names = (
            "n_frames",
            "frame_size",
            "key_order",
            "figure_height_pattern",
            "color_relation",
            "key_position",
        )
        selected = tuple(overrides.get(name, value) for name, value in zip(names, base))

    selected = _consume_axes(ctx, selected)
    if canonical_profile is not None:
        grid = _draw_canonical_profile(canonical_profile, rng)
    else:
        grid = _draw_general(selected, rng, difficulty)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid instance: {errors}")
    observed = observe_overrides(grid)
    for name, requested in zip(AXES, selected):
        if observed.get(name) != requested:
            raise ValueError(
                f"constructed axis mismatch for {name}: requested {requested!r}, observed {observed.get(name)!r}"
            )
    return [row[:] for row in grid]


def mutation_fixtures():
    """Named task-local impostors that structural self_check must reject."""
    base = generate(
        991,
        5,
        difficulty="medium",
        n_frames=3,
        frame_size=5,
        key_order="mixed",
        figure_height_pattern="varied",
        color_relation="overlap",
        key_position="varied",
    )
    records = _frame_records(base)

    broken_frame = deepcopy(base)
    r0, c0, _, _ = records[0]["bbox"]
    broken_frame[r0][c0 + 1] = 0

    missing_key = deepcopy(base)
    kr, kc, _ = records[0]["keys"][0]
    missing_key[kr][kc] = 0

    duplicate_key = deepcopy(base)
    _, _, first_key = records[0]["keys"][0]
    kr, kc, _ = records[1]["keys"][0]
    duplicate_key[kr][kc] = first_key

    two_figure_colors = deepcopy(base)
    multi = next(record for record in records if len(record["figure_cells"]) >= 2)
    fr, fc, old_color = multi["figure_cells"][0]
    replacement = next(color for color in range(1, 9) if color != old_color)
    two_figure_colors[fr][fc] = replacement

    stray_marker = deepcopy(base)
    placed = False
    occupied = {
        (r, c)
        for record in records
        for r, c in record["perimeter"]
    }
    for record in records:
        occupied.update((r, c) for r, c, _ in record["keys"])
        occupied.update((r, c) for r, c, _ in record["figure_cells"])
    for r, row in enumerate(stray_marker):
        for c, value in enumerate(row):
            if value == 0 and (r, c) not in occupied:
                stray_marker[r][c] = 8
                placed = True
                break
        if placed:
            break

    disconnected_figure = deepcopy(base)
    record = records[1]
    r0, c0, r1, c1 = record["bbox"]
    figure_color = next(iter(record["figure_colors"]))
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            if disconnected_figure[r][c] == 0:
                disconnected_figure[r][c] = figure_color
                if not _is_connected({
                    (rr, cc)
                    for rr in range(r0 + 1, r1)
                    for cc in range(c0 + 1, c1)
                    if disconnected_figure[rr][cc] == figure_color
                }):
                    break
                disconnected_figure[r][c] = 0
        else:
            continue
        break

    return [
        ("broken_frame_perimeter", broken_frame),
        ("missing_key", missing_key),
        ("duplicate_key_color", duplicate_key),
        ("two_figure_colors", two_figure_colors),
        ("stray_nonzero_outside_roles", stray_marker),
        ("disconnected_figure", disconnected_figure),
    ]

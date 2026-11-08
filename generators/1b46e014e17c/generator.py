"""Generator for 9b:hard_63 — Boolean gallery from two framed templates.

The left and right color-9 hollow frames contain binary source templates A and
B.  Each nonzero cell in the bottom row is an operation code, read left to
right with duplicates preserved: 4=OR, 5=AND, 6=A-minus-B, 7=XOR.  The source
masks are independently cropped, centered on a common canvas, combined, then
each result is tightly cropped, painted with its own code, and packed into a
one-column-gapped horizontal gallery.

The ordinary schedule alternates an all-four-operations discriminator with a
canonical-profile scene.  Consequently every two-demo sliding window contains
one example that identifies all code branches and refutes union-only,
B-minus-A, top-left/raw-coordinate alignment, and sort/deduplicate shortcuts.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1b46e014e17c"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"  # canonical 6x6-frame grammar + exact axes + semantic schedule
RULE_HASH = "bd6e91262627"

SUMMARY = (
    "Read the two hollow color-9 frames from left to right as templates A and B. "
    "Crop each occupied interior mask, center them on a common canvas, then read "
    "the bottom-row codes in positional order (duplicates included): 4=OR, "
    "5=AND, 6=A-minus-B, 7=XOR. Paint and tightly crop each result with its code "
    "and hstack the panels with one zero column between them."
)

INVARIANTS = [
    "background is 0 and all non-background cells belong to two frames or the bottom code row",
    "exactly two same-size hollow color-9 square frames occur at distinct columns",
    "each frame interior is a nonempty monochrome binary template and the two source colors differ",
    "the bottom row contains three or four codes from {4,5,6,7}; positional order and duplicates matter",
    "ordinary draws make OR, AND, A-minus-B, and XOR nonempty and morphologically distinct",
    "every two-example schedule window includes an unsorted all-four-code discriminator",
]

_CODE_PROFILES = (
    "three_unique",
    "three_with_repeat",
    "four_all",
    "four_with_repeat",
    "four_heavy_repeat",
)
_SOURCE_PALETTES = ("canonical", "alternate")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled 10..12 with canonical 10-row anchors",
        "valid": "10..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled 18..20 with canonical 18-column anchors",
        "valid": "18..20",
    },
    "frame_inner_size": {
        "type": "int",
        "default": "scheduled 3..5 with canonical 4x4 interiors",
        "valid": "3..5",
    },
    "code_profile": {
        "type": "str",
        "default": "alternating four_all and canonical three/four-code profiles",
        "valid": "|".join(_CODE_PROFILES),
    },
    "source_palette": {
        "type": "str",
        "default": "mostly canonical colors 2/3, sometimes alternate 1/8",
        "valid": "|".join(_SOURCE_PALETTES),
    },
}

# Every Cartesian combination is constructible in the declared dimensions.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Even residues are all-four-operation anchors.  Every length-two sliding
# window therefore contains one complete code-map discriminator.
_PROFILE_DEFAULTS = (
    ("all_ops_anchor", 10, 18, 4, "four_all", "canonical"),
    ("canonical_repeat_three", 10, 18, 4, "three_with_repeat", "canonical"),
    ("all_ops_small_generalization", 11, 19, 3, "four_all", "alternate"),
    ("canonical_three_unique", 10, 18, 4, "three_unique", "canonical"),
    ("all_ops_large_generalization", 12, 20, 5, "four_all", "canonical"),
    ("canonical_repeat_four", 10, 18, 4, "four_with_repeat", "canonical"),
    ("all_ops_offset_generalization", 11, 18, 4, "four_all", "alternate"),
    ("canonical_heavy_repeat_four", 10, 18, 4, "four_heavy_repeat", "canonical"),
)
SCHEDULE_PROFILES = tuple(row[0] for row in _PROFILE_DEFAULTS)
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.45


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic curriculum profile for this sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _profile_defaults(sample_index: int) -> tuple[int, int, int, str, str]:
    row = _PROFILE_DEFAULTS[int(sample_index) % len(_PROFILE_DEFAULTS)]
    return row[1], row[2], row[3], row[4], row[5]


def _scheduled_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _scheduled_choice(
    ctx,
    overrides,
    label: str,
    default: str,
    choices: Sequence[str],
) -> str:
    options = choices if label in overrides and overrides[label] is not None else (default,)
    return str(ctx.draw_choice(label, options))


def _components_of_color(grid: Sequence[Sequence[int]], color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            component: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(component)
    return components


def _frame_info(grid: Sequence[Sequence[int]], component: Sequence[tuple[int, int]]):
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return None
    border = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    if set(component) != border:
        return None

    mask: list[list[int]] = []
    values: list[int] = []
    support: set[tuple[int, int]] = set()
    for r in range(r0 + 1, r1):
        row: list[int] = []
        for c in range(c0 + 1, c1):
            value = grid[r][c]
            if value == 9:
                return None
            hit = value != 0
            row.append(1 if hit else 0)
            if hit:
                support.add((r - r0 - 1, c - c0 - 1))
                values.append(value)
        mask.append(row)
    return {
        "r0": r0,
        "r1": r1,
        "c0": c0,
        "c1": c1,
        "inner_h": r1 - r0 - 1,
        "inner_w": c1 - c0 - 1,
        "mask": mask,
        "support": support,
        "values": values,
        "border": border,
    }


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty sequence of rows"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be nonempty sequences"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return {"errors": [f"cell ({r},{c}) is not an ARC color 0..9: {value!r}"]}

    height = len(grid)
    frame_candidates = [
        _frame_info(grid, component) for component in _components_of_color(grid, 9)
    ]
    frames = sorted(
        [frame for frame in frame_candidates if frame is not None],
        key=lambda frame: frame["c0"],
    )
    if len(frames) != 2:
        errors.append(f"expected exactly two hollow color-9 frames, found {len(frames)}")

    codes = [value for value in grid[-1] if value in (4, 5, 6, 7)]
    bottom_nonzero = [value for value in grid[-1] if value != 0]
    if bottom_nonzero != codes:
        errors.append("every nonzero bottom-row cell must be an operation code in {4,5,6,7}")
    if not (2 <= len(codes) <= 4):
        errors.append(f"expected two to four bottom-row codes, found {len(codes)}")

    if len(frames) == 2:
        dims = {(frame["inner_h"], frame["inner_w"]) for frame in frames}
        if len(dims) != 1:
            errors.append("the two frame interiors must have equal dimensions")
        elif next(iter(dims))[0] != next(iter(dims))[1]:
            errors.append("the two frame interiors must be square")
        if frames[0]["c1"] >= frames[1]["c0"]:
            errors.append("the two frames must occupy distinct left-to-right columns")
        if any(frame["r1"] >= height - 1 for frame in frames):
            errors.append("the bottom code row must be separate from both frames")

        source_colors: list[int] = []
        for index, frame in enumerate(frames):
            values = frame["values"]
            if len(values) < 3:
                errors.append(f"frame {index} needs at least three occupied interior cells")
            unique = set(values)
            if len(unique) != 1:
                errors.append(
                    f"frame {index} interior must be monochrome, found {sorted(unique)}"
                )
            elif next(iter(unique)) in (4, 5, 6, 7, 9):
                errors.append(f"frame {index} source color must be separate from code/frame colors")
            else:
                source_colors.append(next(iter(unique)))
        if len(source_colors) == 2 and source_colors[0] == source_colors[1]:
            errors.append("the two framed templates must use different source colors")

        occupied_roles: set[tuple[int, int]] = set()
        for frame in frames:
            occupied_roles.update(frame["border"])
            for dr, dc in frame["support"]:
                occupied_roles.add((frame["r0"] + 1 + dr, frame["c0"] + 1 + dc))
        occupied_roles.update(
            (height - 1, c) for c, value in enumerate(grid[-1]) if value != 0
        )
        stray = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value != 0 and (r, c) not in occupied_roles
        ]
        if stray:
            errors.append(f"found non-role cells outside frames/code row, e.g. {stray[0]}")

        if all(frame["support"] for frame in frames):
            normalized = [_crop_mask(frame["mask"]) for frame in frames]
            if normalized[0] == normalized[1]:
                errors.append("the two templates become identical after tight cropping")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "frames": frames,
        "codes": codes,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical input grammar without imposing schedule-only witnesses."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def _crop_mask(mask: Sequence[Sequence[int]]) -> list[list[int]]:
    cells = [
        (r, c)
        for r, row in enumerate(mask)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [list(row[c0 : c1 + 1]) for row in mask[r0 : r1 + 1]]


def _pad_center(mask: Sequence[Sequence[int]], height: int, width: int) -> list[list[int]]:
    out = full_grid(height, width, 0)
    top = (height - len(mask)) // 2
    left = (width - len(mask[0])) // 2
    for r, row in enumerate(mask):
        for c, value in enumerate(row):
            out[top + r][left + c] = int(value != 0)
    return out


def _pad_top_left(mask: Sequence[Sequence[int]], height: int, width: int) -> list[list[int]]:
    out = full_grid(height, width, 0)
    for r, row in enumerate(mask):
        for c, value in enumerate(row):
            out[r][c] = int(value != 0)
    return out


def _apply_op(a: Sequence[Sequence[int]], b: Sequence[Sequence[int]], code: int) -> list[list[int]]:
    out = full_grid(len(a), len(a[0]), 0)
    for r in range(len(a)):
        for c in range(len(a[0])):
            aa, bb = bool(a[r][c]), bool(b[r][c])
            hit = (
                (code == 4 and (aa or bb))
                or (code == 5 and (aa and bb))
                or (code == 6 and (aa and not bb))
                or (code == 7 and (aa != bb))
            )
            out[r][c] = 1 if hit else 0
    return out


def _paint(mask: Sequence[Sequence[int]], color: int) -> list[list[int]]:
    return [[color if value else 0 for value in row] for row in mask]


def _hstack_center(pieces: Sequence[Sequence[Sequence[int]]]) -> list[list[int]]:
    if not pieces:
        return [[]]
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + len(pieces) - 1
    out = full_grid(height, width, 0)
    left = 0
    for piece in pieces:
        top = (height - len(piece)) // 2
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                out[top + r][left + c] = value
        left += len(piece[0]) + 1
    return out


def _transform(
    grid,
    *,
    alignment: str = "center",
    code_mode: str = "as_read",
    op_override: Callable[[int], int] | None = None,
) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid Boolean-gallery input: " + "; ".join(analysis["errors"]))
    frames = analysis["frames"]
    codes = list(analysis["codes"])
    if code_mode == "sort_unique":
        codes = sorted(set(codes))

    if alignment == "raw":
        a0 = [list(row) for row in frames[0]["mask"]]
        b0 = [list(row) for row in frames[1]["mask"]]
    else:
        a0 = _crop_mask(frames[0]["mask"])
        b0 = _crop_mask(frames[1]["mask"])
    height = max(len(a0), len(b0))
    width = max(len(a0[0]), len(b0[0]))
    if alignment == "top_left" or alignment == "raw":
        a = _pad_top_left(a0, height, width)
        b = _pad_top_left(b0, height, width)
    else:
        a = _pad_center(a0, height, width)
        b = _pad_center(b0, height, width)

    pieces: list[list[list[int]]] = []
    for code in codes:
        op_code = op_override(code) if op_override is not None else code
        result = _crop_mask(_apply_op(a, b, op_code))
        pieces.append(_paint(result, code))
    return _hstack_center(pieces)


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    return _transform(grid)


def _rival_all_union(grid):
    return _transform(grid, op_override=lambda code: 4)


def _rival_reverse_minus(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    frames = analysis["frames"]
    a0 = _crop_mask(frames[0]["mask"])
    b0 = _crop_mask(frames[1]["mask"])
    height = max(len(a0), len(b0))
    width = max(len(a0[0]), len(b0[0]))
    a = _pad_center(a0, height, width)
    b = _pad_center(b0, height, width)
    pieces = []
    for code in analysis["codes"]:
        if code == 6:
            result = _crop_mask(_apply_op(b, a, 6))
        else:
            result = _crop_mask(_apply_op(a, b, code))
        pieces.append(_paint(result, code))
    return _hstack_center(pieces)


def _rival_top_left(grid):
    return _transform(grid, alignment="top_left")


def _rival_raw_coordinates(grid):
    return _transform(grid, alignment="raw")


def _rival_sort_unique(grid):
    return _transform(grid, code_mode="sort_unique")


LESSON_COMPETITORS = {
    "all_codes_are_union": _rival_all_union,
    "code_6_is_B_minus_A": _rival_reverse_minus,
    "top_left_align_cropped_masks": _rival_top_left,
    "align_uncropped_frame_coordinates": _rival_raw_coordinates,
    "sort_and_deduplicate_codes": _rival_sort_unique,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)


def _binary_signature(mask: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value != 0) for value in row) for row in mask)


def _operation_signatures(grid) -> dict[int, tuple[tuple[int, ...], ...]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    a0 = _crop_mask(analysis["frames"][0]["mask"])
    b0 = _crop_mask(analysis["frames"][1]["mask"])
    height = max(len(a0), len(b0))
    width = max(len(a0[0]), len(b0[0]))
    a = _pad_center(a0, height, width)
    b = _pad_center(b0, height, width)
    return {
        code: _binary_signature(_crop_mask(_apply_op(a, b, code)))
        for code in (4, 5, 6, 7)
    }


def _witness_all_four_branches(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"] or set(analysis["codes"]) != {4, 5, 6, 7}:
        return False
    signatures = _operation_signatures(grid)
    return len(signatures) == 4 and len(set(signatures.values())) == 4


def _witness_crop_and_center(grid) -> bool:
    if self_check(grid):
        return False
    expected = rule_mirror(grid)
    return expected != _rival_top_left(grid) and expected != _rival_raw_coordinates(grid)


def _witness_code_sequence(grid) -> bool:
    return not self_check(grid) and rule_mirror(grid) != _rival_sort_unique(grid)


def _witness_directional_minus(grid) -> bool:
    analysis = _analyze(grid)
    return (
        not analysis["errors"]
        and 6 in analysis["codes"]
        and rule_mirror(grid) != _rival_reverse_minus(grid)
    )


SEMANTIC_WITNESSES = {
    "all_four_boolean_branches_are_distinct": _witness_all_four_branches,
    "independent_crop_then_center_is_decisive": _witness_crop_and_center,
    "code_order_and_duplicates_are_decisive": _witness_code_sequence,
    "left_minus_right_is_directional": _witness_directional_minus,
}
WITNESS_RIVALS = {
    "all_four_boolean_branches_are_distinct": ["all_codes_are_union"],
    "independent_crop_then_center_is_decisive": [
        "top_left_align_cropped_masks",
        "align_uncropped_frame_coordinates",
    ],
    "code_order_and_duplicates_are_decisive": ["sort_and_deduplicate_codes"],
    "left_minus_right_is_directional": ["code_6_is_B_minus_A"],
}


def _code_profile(codes: Sequence[int]) -> str:
    distinct = len(set(codes))
    if len(codes) == 3 and distinct == 3:
        return "three_unique"
    if len(codes) == 3 and distinct == 2:
        return "three_with_repeat"
    if len(codes) == 4 and distinct == 4:
        return "four_all"
    if len(codes) == 4 and distinct == 3:
        return "four_with_repeat"
    if len(codes) == 4 and distinct == 2:
        return "four_heavy_repeat"
    return "other"


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    frames = analysis["frames"]
    source_colors = {value for frame in frames for value in frame["values"]}
    if source_colors == {2, 3}:
        palette = "canonical"
    elif source_colors == {1, 8}:
        palette = "alternate"
    else:
        palette = "other"
    inner_sizes = {
        (frame["inner_h"], frame["inner_w"]) for frame in frames
    }
    inner_size = None
    if len(inner_sizes) == 1:
        inner_h, inner_w = next(iter(inner_sizes))
        if inner_h == inner_w:
            inner_size = inner_h
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "frame_inner_size": inner_size,
        "code_profile": _code_profile(analysis["codes"]),
        "source_palette": palette,
    }


def strict_canonical_like(grid) -> list[str]:
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    observed = observe_overrides(grid)
    if (observed["grid_h"], observed["grid_w"]) != (10, 18):
        reasons.append("canonical inputs are 10x18")
    if observed["frame_inner_size"] != 4:
        reasons.append("canonical frames have 4x4 interiors")
    if observed["source_palette"] != "canonical":
        reasons.append("canonical source colors are 2 and 3")
    if observed["code_profile"] == "four_all":
        reasons.append("canonical rows use three distinct codes at most")
    palette_size = len({value for row in grid for value in row})
    if palette_size not in (6, 7):
        reasons.append(f"canonical palette size is 6 or 7, found {palette_size}")
    return reasons


def lesson_identifiable(demos, query) -> list[str]:
    """Require exact demos that collectively refute every named rival."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    refuted = {name: False for name in LESSON_COMPETITORS}
    demonstrated_codes: set[int] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the Boolean-gallery rule")
            continue
        demonstrated_codes.update(_analyze(demo["input"])["codes"])
        for name, rival in LESSON_COMPETITORS.items():
            refuted[name] = refuted[name] or rival(demo["input"]) != expected

    missing_codes = sorted({4, 5, 6, 7} - demonstrated_codes)
    if missing_codes:
        reasons.append(f"demonstrations do not expose code branches {missing_codes}")
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _supports_to_mask(size: int, support: set[tuple[int, int]]) -> list[list[int]]:
    mask = full_grid(size, size, 0)
    for r, c in support:
        mask[r][c] = 1
    return mask


def _supports_are_teaching(
    size: int,
    support_a: set[tuple[int, int]],
    support_b: set[tuple[int, int]],
) -> bool:
    if not support_a or not support_b:
        return False
    a0 = _crop_mask(_supports_to_mask(size, support_a))
    b0 = _crop_mask(_supports_to_mask(size, support_b))
    if a0 == b0:
        return False
    height = max(len(a0), len(b0))
    width = max(len(a0[0]), len(b0[0]))
    a = _pad_center(a0, height, width)
    b = _pad_center(b0, height, width)
    shared = sum(a[r][c] and b[r][c] for r in range(height) for c in range(width))
    a_only = sum(a[r][c] and not b[r][c] for r in range(height) for c in range(width))
    b_only = sum(b[r][c] and not a[r][c] for r in range(height) for c in range(width))
    if not (shared and a_only and b_only):
        return False
    signatures = {
        _binary_signature(_crop_mask(_apply_op(a, b, code)))
        for code in (4, 5, 6, 7)
    }
    if len(signatures) != 4:
        return False
    union_count = sum(a[r][c] or b[r][c] for r in range(height) for c in range(width))
    return union_count < height * width


def _anchor_supports(size: int, rng) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    mid = size // 2
    edge_rows = [0, size - 1]
    edge_cols = [0, size - 1]
    if rng.randrange(2) == 0:
        a_row = rng.choice(edge_rows)
        b_col = rng.choice(edge_cols)
        support_a = {(a_row, c) for c in range(size)}
        support_b = {(r, b_col) for r in range(size)}
    else:
        a_col = rng.choice(edge_cols)
        b_row = rng.choice(edge_rows)
        support_a = {(r, a_col) for r in range(size)}
        support_b = {(b_row, c) for c in range(size)}
    # The complete lines guarantee connected templates, a single shared center
    # after crop+center, private cells on both sides, and a raw-coordinate
    # alignment different from the centered rule because the lines sit on edges.
    assert _supports_are_teaching(size, support_a, support_b)
    # Consume a deterministic bit without altering the proof; it diversifies
    # which operand receives the horizontal versus vertical role.
    if (mid + rng.randrange(2)) % 2:
        return support_b, support_a
    return support_a, support_b


def _connected_support(size: int, count: int, rng) -> set[tuple[int, int]]:
    start = (rng.randrange(size), rng.randrange(size))
    support = {start}
    frontier = {start}
    while len(support) < count:
        candidates = {
            (r + dr, c + dc)
            for r, c in frontier
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if 0 <= r + dr < size and 0 <= c + dc < size and (r + dr, c + dc) not in support
        }
        if not candidates:
            frontier = set(support)
            continue
        chosen = rng.choice(sorted(candidates))
        support.add(chosen)
        frontier.add(chosen)
    return support


def _random_supports(size: int, difficulty, rng) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    cap = min(size * size - 1, {"easy": 5, "medium": 7, "hard": 9}.get(difficulty, 7))
    lo = 3
    for _ in range(512):
        count_a = rng.randint(lo, max(lo, cap))
        count_b = rng.randint(lo, max(lo, cap))
        support_a = _connected_support(size, count_a, rng)
        support_b = _connected_support(size, count_b, rng)
        if _supports_are_teaching(size, support_a, support_b):
            return support_a, support_b
    return _anchor_supports(size, rng)


def _code_sequence(profile: str, rng) -> list[int]:
    if profile == "four_all":
        codes = rng.sample([4, 5, 6, 7], 4)
        if codes == sorted(codes):
            codes = codes[1:] + codes[:1]
        return codes
    if profile == "three_unique":
        codes = rng.sample([4, 5, 6, 7], 3)
        if codes == sorted(codes):
            codes = codes[1:] + codes[:1]
        return codes
    if profile == "three_with_repeat":
        distinct = rng.sample([4, 5, 6, 7], 2)
        codes = distinct + [rng.choice(distinct)]
        rng.shuffle(codes)
        return codes
    if profile == "four_with_repeat":
        distinct = rng.sample([4, 5, 6, 7], 3)
        codes = distinct + [rng.choice(distinct)]
        rng.shuffle(codes)
        return codes
    if profile == "four_heavy_repeat":
        distinct = rng.sample([4, 5, 6, 7], 2)
        repeated = rng.choice(distinct)
        codes = distinct + [repeated, repeated]
        rng.shuffle(codes)
        return codes
    raise ValueError(f"unknown code profile {profile!r}")


def _place_frame(
    grid: list[list[int]],
    r0: int,
    c0: int,
    inner_size: int,
    color: int,
    support: set[tuple[int, int]],
) -> None:
    outer = inner_size + 2
    for c in range(c0, c0 + outer):
        grid[r0][c] = 9
        grid[r0 + outer - 1][c] = 9
    for r in range(r0, r0 + outer):
        grid[r][c0] = 9
        grid[r][c0 + outer - 1] = 9
    for dr, dc in support:
        grid[r0 + 1 + dr][c0 + 1 + dc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_inner, default_codes, default_palette = _profile_defaults(sample_index)
    height = _scheduled_int(ctx, overrides, "grid_h", default_h, 10, 12)
    width = _scheduled_int(ctx, overrides, "grid_w", default_w, 18, 20)
    inner_size = _scheduled_int(ctx, overrides, "frame_inner_size", default_inner, 3, 5)
    code_profile = _scheduled_choice(
        ctx, overrides, "code_profile", default_codes, _CODE_PROFILES
    )
    source_palette = _scheduled_choice(
        ctx, overrides, "source_palette", default_palette, _SOURCE_PALETTES
    )

    outer = inner_size + 2
    if 2 * outer + 1 > width or outer + 2 > height:
        raise ValueError("declared dimensions cannot fit two frames plus a separate code row")

    layout_rng = ctx.draw_rng("layout")
    support_rng = ctx.draw_rng("supports")
    code_rng = ctx.draw_rng("codes")
    if code_profile == "four_all":
        support_a, support_b = _anchor_supports(inner_size, support_rng)
    else:
        support_a, support_b = _random_supports(inner_size, difficulty, support_rng)

    grid = full_grid(height, width, 0)
    spare_cols = width - 2 * outer
    gap = layout_rng.randint(1, spare_cols)
    remaining = spare_cols - gap
    left_margin = layout_rng.randint(0, remaining)
    c0_a = left_margin
    c0_b = c0_a + outer + gap
    max_row = height - outer - 2
    r0_a = layout_rng.randint(0, max_row)
    r0_b = layout_rng.randint(0, max_row)
    colors = (2, 3) if source_palette == "canonical" else (1, 8)
    _place_frame(grid, r0_a, c0_a, inner_size, colors[0], support_a)
    _place_frame(grid, r0_b, c0_b, inner_size, colors[1], support_b)

    codes = _code_sequence(code_profile, code_rng)
    code_cols = sorted(code_rng.sample(range(width), len(codes)))
    for col, code in zip(code_cols, codes):
        grid[-1][col] = code

    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator defect: " + "; ".join(errors))
    if code_profile == "four_all":
        required = [
            name for name, witness in SEMANTIC_WITNESSES.items() if not witness(grid)
        ]
        if required:
            raise RuntimeError(f"all-ops anchor missed semantic witnesses: {required}")
    return grid

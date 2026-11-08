"""Generator for ARC task ``c5f62271ea44`` / source task ``94133066``.

A solid blue rectangular panel contains four distinct logical corner markers:
three non-blue colors and blue itself.  A separate one-color motif inside the panel makes transporting the body
part of the task, rather than merely rearranging the corner code.  Outside the panel,
three colored dots occupy three corners of another rectangle; the absent fourth
corner means blue.  Those four logical key values identify one of the eight D4
symmetries, and the answer is the *entire* panel transformed by that symmetry.

The original generator taught a shortcut: it drew a hollow, nearly empty panel
and four external dots, so generated lessons could be solved by permuting corner
colors rather than transforming the panel body.  This version follows the
canonical three-dot/missing-blue grammar. The seed-keyed teaching schedule
varies transform order between episodes, and geometry includes connected or
fragmented bodies and both compact and canonical-scale external keys.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c5f62271ea44"
TASK_ID = GENERATOR_ID
VERSION = "3.3.0"
RULE_HASH = "74e8392d1794"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 12

SUMMARY = (
    "A zero-background grid contains one solid color-1 rectangular panel. "
    "One cell in from its four corners are four distinct logical markers: "
    "three non-blue colors and blue (1).  The panel also contains a nontrivial "
    "one-color body motif, connected or fragmented.  Outside the panel, exactly three dots "
    "occupy three corners of a second bounding box; the missing fourth corner "
    "is interpreted as blue.  Match that four-corner key signature to the "
    "panel's logical corners and apply the corresponding one of all eight D4 "
    "symmetries to the entire panel, including its body motif."
)

INVARIANTS = [
    "background outside the panel/key is 0",
    "the panel is a solid rectangular color-1 field before marker/motif overlays",
    "the four inner-corner marker values are distinct and exactly one is color 1",
    "exactly one additional non-marker color forms a nontrivial panel-body motif",
    "exactly three nonzero cells lie outside the panel and occupy three corners of one bbox",
    "the missing key-bbox corner is interpreted as color 1, uniquely selecting one D4 transform",
]

SYMMETRIES = (
    "identity",
    "transpose",
    "flip_lr",
    "rot_cw",
    "flip_ud",
    "anti_transpose",
    "rot180",
    "rot_ccw",
)
KEY_SIDES = ("top", "right", "bottom", "left")
BODY_KINDS = ("connected", "fragmented")
KEY_EXTENTS = ("compact", "extended")
PROFILE_KINDS = (
    "canonical_0",
    "canonical_1",
    "canonical_2",
    "canonical_3",
    "generalized",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
SCHEDULE_PROFILES = SYMMETRIES

AXES = {
    "symmetry": {
        "type": "str",
        "default": "seed-keyed twelve-slot teaching schedule",
        "valid": "|".join(SYMMETRIES),
    },
    "profile_kind": {
        "type": "str",
        "default": "rng canonical_0|canonical_1|canonical_2|canonical_3|generalized",
        "valid": "|".join(PROFILE_KINDS),
    },
    "key_side": {
        "type": "str",
        "default": "rng top|right|bottom|left",
        "valid": "|".join(KEY_SIDES),
    },
    "body_kind": {
        "type": "str",
        "default": "rng connected|fragmented",
        "valid": "|".join(BODY_KINDS),
    },
    "key_extent": {
        "type": "str",
        "default": "rng compact|extended",
        "valid": "|".join(KEY_EXTENTS),
    },
}

# Each canonical prior pins the full input shape, panel shape and palette.  The
# palette tuple is (three non-blue logical corner colors, body-motif color).
# These are linked profiles, not independently recombined marginal ranges.
_PROFILE_SPECS = {
    "canonical_0": {
        "grid": (22, 21),
        "panel": (9, 9),
        "colors": (4, 8, 5, 2),
    },
    "canonical_1": {
        "grid": (23, 19),
        "panel": (9, 10),
        "colors": (2, 4, 3, 8),
    },
    "canonical_2": {
        "grid": (22, 25),
        "panel": (12, 10),
        "colors": (2, 3, 4, 5),
    },
    "canonical_3": {
        "grid": (19, 30),
        "panel": (13, 10),
        "colors": (4, 2, 8, 3),
    },
}

_GENERAL_SPECS = (
    {"grid": (20, 24), "panel": (10, 11), "colors": (6, 7, 9, 2)},
    {"grid": (21, 27), "panel": (11, 9), "colors": (3, 6, 9, 7)},
    {"grid": (24, 28), "panel": (10, 13), "colors": (2, 6, 7, 9)},
)

# Corner order is TL, TR, BL, BR.  These signatures are exactly the selected
# Racket oracle's transform table.
_CORNER_ARRANGEMENTS = {
    "identity": lambda q: (q[0], q[1], q[2], q[3]),
    "flip_lr": lambda q: (q[1], q[0], q[3], q[2]),
    "flip_ud": lambda q: (q[2], q[3], q[0], q[1]),
    "rot180": lambda q: (q[3], q[2], q[1], q[0]),
    "transpose": lambda q: (q[0], q[2], q[1], q[3]),
    "anti_transpose": lambda q: (q[3], q[1], q[2], q[0]),
    "rot_cw": lambda q: (q[2], q[0], q[3], q[1]),
    "rot_ccw": lambda q: (q[1], q[3], q[0], q[2]),
}


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty 2D sequence")
    rows: list[list[int]] = []
    width: int | None = None
    for row in grid:
        if not isinstance(row, (list, tuple)):
            raise ValueError("grid row is not a sequence")
        values = list(row)
        if width is None:
            width = len(values)
        if not values or len(values) != width:
            raise ValueError("grid is empty or ragged")
        if any(type(value) is not int or not 0 <= value <= 9 for value in values):
            raise ValueError("grid contains a non-ARC color")
        rows.append(values)
    return rows


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    if not cells:
        raise ValueError("cannot take bbox of empty cells")
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _crop(grid: list[list[int]], box: tuple[int, int, int, int]) -> list[list[int]]:
    r0, c0, r1, c1 = box
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _transform_grid(grid: list[list[int]], symmetry: str) -> list[list[int]]:
    values = [list(row) for row in grid]
    if symmetry == "identity":
        return [row[:] for row in values]
    if symmetry == "flip_lr":
        return [list(reversed(row)) for row in values]
    if symmetry == "flip_ud":
        return [row[:] for row in reversed(values)]
    if symmetry == "rot180":
        return [list(reversed(row)) for row in reversed(values)]
    if symmetry == "transpose":
        return [list(row) for row in zip(*values)]
    if symmetry == "anti_transpose":
        return _transform_grid(_transform_grid(values, "transpose"), "rot180")
    if symmetry == "rot_cw":
        return _transform_grid(_transform_grid(values, "flip_ud"), "transpose")
    if symmetry == "rot_ccw":
        return _transform_grid(_transform_grid(values, "flip_lr"), "transpose")
    raise ValueError(f"unknown symmetry {symmetry!r}")


def _arrangement(symmetry: str, corners: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    try:
        return _CORNER_ARRANGEMENTS[symmetry](corners)
    except KeyError as exc:
        raise ValueError(f"unknown symmetry {symmetry!r}") from exc


def _symmetry_from_signature(
    corners: tuple[int, int, int, int],
    signature: tuple[int, int, int, int],
) -> str | None:
    matches = [name for name in SYMMETRIES if _arrangement(name, corners) == signature]
    return matches[0] if len(matches) == 1 else None


def _neighbors4(r: int, c: int) -> tuple[tuple[int, int], ...]:
    return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for point in _neighbors4(r, c):
            if point in cells and point not in seen:
                seen.add(point)
                queue.append(point)
    return len(seen) == len(cells)


def _grow_body(
    panel_h: int,
    panel_w: int,
    reserved: set[tuple[int, int]],
    count: int,
    rng,
) -> set[tuple[int, int]]:
    candidates = {
        (r, c)
        for r in range(1, panel_h - 1)
        for c in range(1, panel_w - 1)
        if (r, c) not in reserved
    }
    starts = sorted(
        point
        for point in candidates
        if 2 <= point[0] <= panel_h - 3 and 2 <= point[1] <= panel_w - 3
    ) or sorted(candidates)
    if not starts:
        raise ValueError("no available body-motif cell")
    start = starts[rng.randrange(len(starts))]
    body = {start}
    while len(body) < min(count, len(candidates)):
        frontier = sorted(
            point
            for cell in body
            for point in _neighbors4(*cell)
            if point in candidates and point not in body
        )
        if not frontier:
            break
        body.add(frontier[rng.randrange(len(frontier))])
    if len(body) != count:
        raise ValueError(f"could not grow {count} body cells, found {len(body)}")
    return body


def _grow_fragmented_body(panel_h, panel_w, reserved, count, rng):
    """One grown component plus one or two isolated cells; exactly 2 or 3
    four-connected components. Diagonal contact is allowed, as in the source.
    Connectivity is a sampling axis, never a requirement on canonical inputs.
    """
    candidates = sorted(
        (r, c) for r in range(1, panel_h - 1)
        for c in range(1, panel_w - 1) if (r, c) not in reserved
    )
    isolated_count = 1 + rng.randrange(2)
    for _ in range(32):
        islands = set(rng.sample(candidates, isolated_count))
        if any(set(_neighbors4(*cell)) & islands for cell in islands):
            continue
        forbidden = set(reserved) | islands
        for cell in islands:
            forbidden.update(_neighbors4(*cell))
        try:
            body = _grow_body(panel_h, panel_w, forbidden, count - isolated_count, rng)
        except ValueError:
            continue
        return body | islands
    # Bounded constructive fallback: opposing edge islands leave a connected
    # central region of at least 23 cells, enough for every supported count.
    islands = {(1, 2), (panel_h - 2, panel_w - 3)}
    forbidden = set(reserved) | islands
    forbidden.update((r, c) for r, c in candidates
                     if not (2 <= r <= panel_h - 3 and 2 <= c <= panel_w - 3))
    for cell in islands:
        forbidden.update(_neighbors4(*cell))
    return _grow_body(panel_h, panel_w, forbidden, count - 2, rng) | islands


def _classify_key_side(
    panel_box: tuple[int, int, int, int],
    key_box: tuple[int, int, int, int],
) -> str:
    pr0, pc0, pr1, pc1 = panel_box
    kr0, kc0, kr1, kc1 = key_box
    if kr1 < pr0:
        return "top"
    if kc0 > pc1:
        return "right"
    if kr0 > pr1:
        return "bottom"
    if kc1 < pc0:
        return "left"
    return "mixed"


def _classify_profile(grid: list[list[int]]) -> str:
    h, w = len(grid), len(grid[0])
    palette = frozenset(value for row in grid for value in row)
    for name, spec in _PROFILE_SPECS.items():
        expected = frozenset((0, 1, *spec["colors"]))
        if (h, w) == spec["grid"] and palette == expected:
            return name
    return "generalized"


def _analyze(grid: Any) -> dict[str, Any]:
    try:
        values = _coerce_grid(grid)
    except ValueError as exc:
        return {"errors": [str(exc)]}

    h, w = len(values), len(values[0])
    errors: list[str] = []
    one_cells = [(r, c) for r in range(h) for c in range(w) if values[r][c] == 1]
    if not one_cells:
        return {"errors": ["missing color-1 panel"]}
    panel_box = _bbox(one_cells)
    pr0, pc0, pr1, pc1 = panel_box
    panel = _crop(values, panel_box)
    ph, pw = len(panel), len(panel[0])
    if ph < 5 or pw < 5:
        errors.append(f"panel {ph}x{pw} is too small")

    if not errors:
        if any(panel[r][c] == 0 for r in range(ph) for c in range(pw)):
            errors.append("panel bbox contains background-zero holes")
        if any(panel[0][c] != 1 or panel[ph - 1][c] != 1 for c in range(pw)):
            errors.append("panel top/bottom border is not solid color 1")
        if any(panel[r][0] != 1 or panel[r][pw - 1] != 1 for r in range(ph)):
            errors.append("panel left/right border is not solid color 1")

    outside = [
        (r, c, values[r][c])
        for r in range(h)
        for c in range(w)
        if values[r][c] != 0 and not (pr0 <= r <= pr1 and pc0 <= c <= pc1)
    ]
    if len(outside) != 3:
        errors.append(f"expected exactly three nonzero key dots outside panel, found {len(outside)}")

    corners: tuple[int, int, int, int] | None = None
    signature: tuple[int, int, int, int] | None = None
    symmetry: str | None = None
    key_box: tuple[int, int, int, int] | None = None
    marker_colors: set[int] = set()
    texture_color: int | None = None
    body_cells: set[tuple[int, int]] = set()

    if ph >= 3 and pw >= 3:
        corners = (panel[1][1], panel[1][pw - 2], panel[ph - 2][1], panel[ph - 2][pw - 2])
        if len(set(corners)) != 4 or corners.count(1) != 1:
            errors.append(
                f"inner-corner markers must be four distinct values with exactly one blue 1, got {corners}"
            )
        marker_colors = {value for value in corners if value != 1}
        if any(value in (0, 1) for value in marker_colors) or len(marker_colors) != 3:
            errors.append("expected exactly three distinct non-blue marker colors")

        reserved = {(1, 1), (1, pw - 2), (ph - 2, 1), (ph - 2, pw - 2)}
        body_palette = {
            panel[r][c]
            for r in range(1, ph - 1)
            for c in range(1, pw - 1)
            if (r, c) not in reserved and panel[r][c] != 1
        }
        if len(body_palette) != 1:
            errors.append(f"expected exactly one body-motif color, found {sorted(body_palette)}")
        else:
            texture_color = next(iter(body_palette))
            if texture_color in marker_colors or texture_color in (0, 1):
                errors.append("body-motif color must be distinct from all marker colors and blue")
            body_cells = {
                (r, c)
                for r in range(1, ph - 1)
                for c in range(1, pw - 1)
                if panel[r][c] == texture_color and (r, c) not in reserved
            }
            if len(body_cells) < 4:
                errors.append(f"body motif is too small ({len(body_cells)} cells)")

    if len(outside) == 3:
        key_points = [(r, c) for r, c, _ in outside]
        key_box = _bbox(key_points)
        kr0, kc0, kr1, kc1 = key_box
        key_corners = {(kr0, kc0), (kr0, kc1), (kr1, kc0), (kr1, kc1)}
        if kr0 == kr1 or kc0 == kc1:
            errors.append("key dots must span a two-dimensional bounding box")
        if set(key_points) - key_corners:
            errors.append("key dots must lie only at bbox corners")
        key_values = {value for _, _, value in outside}
        if key_values != marker_colors:
            errors.append(
                f"key colors {sorted(key_values)} do not equal panel marker colors {sorted(marker_colors)}"
            )
        if any(value == 1 for _, _, value in outside):
            errors.append("blue key corner must be represented by absence, not a fourth dot")
        mapping = {(r, c): value for r, c, value in outside}
        signature = (
            mapping.get((kr0, kc0), 1),
            mapping.get((kr0, kc1), 1),
            mapping.get((kr1, kc0), 1),
            mapping.get((kr1, kc1), 1),
        )
        if corners is not None:
            symmetry = _symmetry_from_signature(corners, signature)
            if symmetry is None:
                errors.append(
                    f"key signature {signature} does not uniquely select a panel D4 transform"
                )

    palette = frozenset(value for row in values for value in row)
    if corners is not None and texture_color is not None:
        expected_palette = frozenset((0, 1, *marker_colors, texture_color))
        if palette != expected_palette:
            errors.append(
                f"palette {sorted(palette)} does not equal expected {sorted(expected_palette)}"
            )

    return {
        "errors": errors,
        "height": h,
        "width": w,
        "panel_box": panel_box,
        "panel": panel,
        "panel_h": ph,
        "panel_w": pw,
        "corners": corners,
        "marker_colors": frozenset(marker_colors),
        "texture_color": texture_color,
        "body_cells": frozenset(body_cells),
        "outside": tuple(outside),
        "key_box": key_box,
        "signature": signature,
        "symmetry": symmetry,
        "key_side": _classify_key_side(panel_box, key_box) if key_box else None,
        "profile_kind": _classify_profile(values),
        "palette": palette,
    }


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(
        key for key, value in overrides.items() if value is not None and key not in AXES
    )
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")
    if overrides.get("symmetry") is not None and overrides["symmetry"] not in SYMMETRIES:
        raise ValueError(f"symmetry must be one of {SYMMETRIES!r}")
    if overrides.get("profile_kind") is not None and overrides["profile_kind"] not in PROFILE_KINDS:
        raise ValueError(f"profile_kind must be one of {PROFILE_KINDS!r}")
    if overrides.get("key_side") is not None and overrides["key_side"] not in KEY_SIDES:
        raise ValueError(f"key_side must be one of {KEY_SIDES!r}")
    if overrides.get("body_kind") is not None and overrides["body_kind"] not in BODY_KINDS:
        raise ValueError(f"body_kind must be one of {BODY_KINDS!r}")
    if overrides.get("key_extent") is not None and overrides["key_extent"] not in KEY_EXTENTS:
        raise ValueError(f"key_extent must be one of {KEY_EXTENTS!r}")


def _validate_indices(seed: Any, sample_index: Any) -> None:
    """Do not alias booleans, strings or fractional values to integer draws."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def _teaching_order_valid(order: list[str]) -> bool:
    """Every five-pair window remains taught after any one query holdout."""
    swapping = {"transpose", "anti_transpose", "rot_cw", "rot_ccw"}
    quarters = {"rot_cw", "rot_ccw"}
    if len(order) != LESSON_SCHEDULE_PERIOD or set(order) != set(SYMMETRIES):
        return False
    for start in range(len(order)):
        five = [order[(start + j) % len(order)] for j in range(5)]
        if len(set(five)) < 4:
            return False
        if not 2 <= sum(name in swapping for name in five) <= 3:
            return False
        if sum(name in quarters for name in five) < 2:
            return False
    return True


# Q = quarter turn, D = diagonal reflection, O = axis-preserving transform.
# These are the three cyclic representatives of all 36 twelve-slot class
# arrangements with 5 Q, 2 D, 5 O and the five-window quarter/axis constraints.
# Unlike the minimal ten-slot construction, their five-window class counts
# vary: a query's class cannot always be recovered from demonstration counts.
_TEACHING_CLASS_CYCLES = (
    "DOQOQDOQOQOQ",
    "DOQOQODQOQOQ",
    "DQOQODQOQOQO",
)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """A reproducible per-seed cycle, not a corpus-wide answer-by-position code.

    Every cyclic five-pair window includes at least two quarter turns, two of
    each output-axis class, and four distinct transforms. Any single holdout
    leaves at least three distinct demonstration transforms, both axis classes
    and a quarter turn refuting both canonical-fitting rivals. All eight D4
    transforms occur within twelve slots. Difficulty does not change a family's
    schedule. A bounded search randomizes directions and repeated values rather
    than making either quarter-turn direction follow from fixed class counts.
    """
    del difficulty
    _validate_indices(seed, sample_index)
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION, task_id=TASK_ID)
    rng = ctx.draw_rng("teaching_schedule")
    for _ in range(32):
        majority, minority = ("rot_cw", "rot_ccw")
        if rng.randrange(2):
            majority, minority = minority, majority
        quarters = [majority] * 3 + [minority] * 2
        diagonals = ["transpose", "anti_transpose"]
        ordinary = ["identity", "rot180", "flip_lr", "flip_ud"]
        ordinary.append(rng.choice(ordinary))
        for values in (quarters, diagonals, ordinary):
            rng.shuffle(values)
        pools = {"Q": quarters, "D": diagonals, "O": ordinary}
        order = [pools[kind].pop() for kind in rng.choice(_TEACHING_CLASS_CYCLES)]
        if _teaching_order_valid(order):
            break
    else:
        # Independently checked fallback with the same five-window guarantees.
        order = ["transpose", "flip_ud", "rot_cw", "rot180", "rot_ccw",
                 "anti_transpose", "identity", "rot_cw", "flip_lr",
                 "rot_cw", "rot180", "rot_ccw"]
    offset = rng.randrange(LESSON_SCHEDULE_PERIOD)
    return order[(sample_index + offset) % LESSON_SCHEDULE_PERIOD]


def _choice_with_scheduled_default(ctx, overrides: dict[str, Any], name: str, default: str, options: tuple[str, ...]) -> str:
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _spec_for_profile(profile_kind: str, rng) -> dict[str, Any]:
    if profile_kind in _PROFILE_SPECS:
        return dict(_PROFILE_SPECS[profile_kind])
    return dict(_GENERAL_SPECS[rng.randrange(len(_GENERAL_SPECS))])


def _key_span_options(h, w, ph, pw, key_side, key_extent):
    """Feasible spans with a one-cell separator and side-aligned placement.

    Compact keys are 3..5 per dimension. Extended keys reach 6..11 where
    space permits (the largest observed canonical extent is 11); a tight
    separating dimension may stay 3..5. At least one dimension exceeds 5.
    Grid/panel dimensions and palette profiles are not enlarged.
    """
    if key_side in ("top", "bottom"):
        max_r, max_c = h - ph - 1, pw
    else:
        max_r, max_c = ph, w - pw - 1
    cap = 5 if key_extent == "compact" else 11
    max_r, max_c = min(cap, max_r), min(cap, max_c)
    min_r = 6 if key_extent == "extended" and max_r >= 6 else 3
    min_c = 6 if key_extent == "extended" and max_c >= 6 else 3
    return tuple((r, c) for r in range(min_r, max_r + 1)
                 for c in range(min_c, max_c + 1)
                 if key_extent == "compact" or max(r, c) > 5)


def _place_panel_and_key(
    grid: list[list[int]],
    panel: list[list[int]],
    signature: tuple[int, int, int, int],
    key_side: str,
    key_extent: str,
    rng,
) -> None:
    h, w = len(grid), len(grid[0])
    ph, pw = len(panel), len(panel[0])
    options = _key_span_options(h, w, ph, pw, key_side, key_extent)
    if not options:
        raise ValueError(f"profile cannot place {key_extent} {key_side} key")
    span_r, span_c = options[rng.randrange(len(options))]
    # A one-cell separator is sufficient and keeps every canonical profile
    # feasible even for the tight 19x30 / 13x10 profile.
    gap = 1

    if key_side in ("top", "bottom"):
        needed = ph + span_r + gap
        if needed > h:
            raise ValueError(f"profile cannot place {key_side} key in {h} rows")
        if key_side == "top":
            panel_r = rng.randint(span_r + gap, h - ph)
            key_r = rng.randint(0, panel_r - gap - span_r)
        else:
            panel_r = rng.randint(0, h - ph - span_r - gap)
            key_r = rng.randint(panel_r + ph + gap, h - span_r)
        panel_c = rng.randint(0, w - pw)
        # Keep the key horizontally aligned with the panel so its observed
        # side is unambiguous (not also diagonally left/right).
        key_c = panel_c + rng.randint(0, pw - span_c)
    else:
        needed = pw + span_c + gap
        if needed > w:
            raise ValueError(f"profile cannot place {key_side} key in {w} columns")
        if key_side == "left":
            panel_c = rng.randint(span_c + gap, w - pw)
            key_c = rng.randint(0, panel_c - gap - span_c)
        else:
            panel_c = rng.randint(0, w - pw - span_c - gap)
            key_c = rng.randint(panel_c + pw + gap, w - span_c)
        panel_r = rng.randint(0, h - ph)
        # Likewise align a left/right key vertically with the panel.
        key_r = panel_r + rng.randint(0, ph - span_r)

    for r in range(ph):
        for c in range(pw):
            grid[panel_r + r][panel_c + c] = panel[r][c]

    key_positions = (
        (key_r, key_c),
        (key_r, key_c + span_c - 1),
        (key_r + span_r - 1, key_c),
        (key_r + span_r - 1, key_c + span_c - 1),
    )
    for (r, c), value in zip(key_positions, signature):
        if value != 1:  # missing bbox corner represents the logical blue marker
            grid[r][c] = value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_indices(seed, sample_index)
    _validate_call(difficulty, overrides)
    # Construct the family-level schedule context first: the shared override
    # checker observes the last context as the main per-instance provenance.
    scheduled_symmetry = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    symmetry = _choice_with_scheduled_default(
        ctx,
        overrides,
        "symmetry",
        scheduled_symmetry,
        SYMMETRIES,
    )
    profile_kind = ctx.draw_choice("profile_kind", PROFILE_KINDS)
    key_side = ctx.draw_choice("key_side", KEY_SIDES)
    body_kind = ctx.draw_choice("body_kind", BODY_KINDS)
    key_extent = ctx.draw_choice("key_extent", KEY_EXTENTS)
    rng = ctx.draw_rng(f"layout:{difficulty or 'mixed'}")
    spec = _spec_for_profile(profile_kind, rng)
    h, w = spec["grid"]
    ph, pw = spec["panel"]
    marker_base = list(spec["colors"][:3])
    texture_color = int(spec["colors"][3])

    # Vary which logical corner is blue and which non-blue marker occupies each
    # remaining corner; palette and profile stay fixed and observable.
    rng.shuffle(marker_base)
    blue_index = rng.randrange(4)
    logical = []
    marker_iter = iter(marker_base)
    for index in range(4):
        logical.append(1 if index == blue_index else next(marker_iter))
    corners = tuple(logical)

    panel = full_grid(ph, pw, 1)
    marker_positions = ((1, 1), (1, pw - 2), (ph - 2, 1), (ph - 2, pw - 2))
    for (r, c), value in zip(marker_positions, corners):
        panel[r][c] = value

    if difficulty == "easy":
        body_count = 7 + rng.randrange(3)
    elif difficulty == "hard":
        body_count = 14 + rng.randrange(5)
    else:
        body_count = 10 + rng.randrange(4)
    grow = _grow_body if body_kind == "connected" else _grow_fragmented_body
    body = grow(ph, pw, set(marker_positions), body_count, rng)
    for r, c in body:
        panel[r][c] = texture_color

    signature = _arrangement(symmetry, corners)
    grid = full_grid(h, w, 0)
    _place_panel_and_key(grid, panel, signature, key_side, key_extent, rng)
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    observed = _observed_axes(analysis)
    for name, actual in observed.items():
        expected = requested.get(name)
        if expected is not None and expected != actual:
            errors.append(f"meta {name} requested {expected!r}, observed {actual!r}")
    return errors


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe overrides: " + "; ".join(analysis["errors"]))
    return _observed_axes(analysis)


def _observed_axes(analysis):
    r0, c0, r1, c1 = analysis["key_box"]
    return {
        "symmetry": analysis["symmetry"],
        "profile_kind": analysis["profile_kind"],
        "key_side": analysis["key_side"],
        "body_kind": "connected" if _connected(set(analysis["body_cells"])) else "fragmented",
        "key_extent": "extended" if max(r1 - r0 + 1, c1 - c0 + 1) > 5 else "compact",
    }


def strict_canonical_like(grid) -> list[str]:
    """Task-linked input grammar shared by official and generated scenes."""
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    if not (9 <= analysis["panel_h"] <= 13 and 9 <= analysis["panel_w"] <= 13):
        errors.append(
            f"panel {analysis['panel_h']}x{analysis['panel_w']} falls outside the supported canonical-linked envelope"
        )
    if not (19 <= analysis["height"] <= 24 and 19 <= analysis["width"] <= 30):
        errors.append(
            f"grid {analysis['height']}x{analysis['width']} falls outside the supported canonical-linked envelope"
        )
    if not (7 <= len(analysis["body_cells"]) <= 18):
        errors.append(f"body motif area {len(analysis['body_cells'])} falls outside 7..18")
    return errors


def canonical_profile_signature(grid) -> tuple[Any, ...] | None:
    """Complete linked signature used by the worker's strict census."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    return (
        analysis["profile_kind"],
        (analysis["height"], analysis["width"]),
        (analysis["panel_h"], analysis["panel_w"]),
        tuple(sorted(analysis["palette"])),
        analysis["symmetry"],
        analysis["key_side"],
        len(analysis["body_cells"]),
    )


def rule_mirror(grid) -> list[list[int]]:
    """Python mirror for checks only; the selected Racket rule is authoritative."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task scene: " + "; ".join(analysis["errors"]))
    return _transform_grid(analysis["panel"], analysis["symmetry"])


def _rival_always_identity(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task scene")
    return [row[:] for row in analysis["panel"]]


def _rival_corner_only(grid):
    """Orient the corner code but erase the body motif — the old teaching shortcut."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task scene")
    panel = [row[:] for row in analysis["panel"]]
    texture = analysis["texture_color"]
    ph, pw = len(panel), len(panel[0])
    marker_positions = {(1, 1), (1, pw - 2), (ph - 2, 1), (ph - 2, pw - 2)}
    for r in range(1, ph - 1):
        for c in range(1, pw - 1):
            if (r, c) not in marker_positions and panel[r][c] == texture:
                panel[r][c] = 1
    return _transform_grid(panel, analysis["symmetry"])


def _rival_always_flip_ud(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task scene")
    return _transform_grid(analysis["panel"], "flip_ud")


def _rival_blue_corner_reflection(grid):
    """Ignore the non-blue marker identities and choose a reflection only.

    All labeled canonical pairs happen to be reflections. Each source/target
    blue-corner pair selects exactly one of the four reflections, so that
    single corner suffices on the canonical data but fails on nonreflections.
    """
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task scene")
    target_blue = analysis["signature"].index(1)
    for name in ("flip_lr", "flip_ud", "transpose", "anti_transpose"):
        if _arrangement(name, analysis["corners"]).index(1) == target_blue:
            return _transform_grid(analysis["panel"], name)
    raise ValueError("blue corner does not select a reflection")


def _rival_inverse_transform(grid):
    """Read the full key but apply the inferred D4 transformation backwards."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task scene")
    name = analysis["symmetry"]
    inverse = {"rot_cw": "rot_ccw", "rot_ccw": "rot_cw"}.get(name, name)
    return _transform_grid(analysis["panel"], inverse)


def _w_nonidentity(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and analysis["symmetry"] != "identity"


def _w_body_required(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and len(analysis["body_cells"]) >= 7


def _w_not_flip_ud(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and analysis["symmetry"] != "flip_ud"


def _w_nonreflection(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and analysis["symmetry"] in {
        "identity", "rot180", "rot_cw", "rot_ccw"
    }


def _w_quarter_turn(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and analysis["symmetry"] in {"rot_cw", "rot_ccw"}


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "always_identity": _rival_always_identity,
    "corner_code_only": _rival_corner_only,
    "always_flip_ud": _rival_always_flip_ud,
    "blue_corner_reflection": _rival_blue_corner_reflection,
    "inverse_transform": _rival_inverse_transform,
}

SEMANTIC_WITNESSES = {
    "nonidentity_refutes_identity": _w_nonidentity,
    "body_motif_refutes_corner_code_only": _w_body_required,
    "varied_transform_refutes_fixed_flip_ud": _w_not_flip_ud,
    "nonreflection_refutes_blue_corner_reflection": _w_nonreflection,
    "quarter_turn_refutes_inverse_transform": _w_quarter_turn,
}

WITNESS_RIVALS = {
    "nonidentity_refutes_identity": ["always_identity"],
    "body_motif_refutes_corner_code_only": ["corner_code_only"],
    "varied_transform_refutes_fixed_flip_ud": ["always_flip_ud"],
    "nonreflection_refutes_blue_corner_reflection": ["blue_corner_reflection"],
    "quarter_turn_refutes_inverse_transform": ["inverse_transform"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "blue_corner_reflection": _rival_blue_corner_reflection,
    "inverse_transform": _rival_inverse_transform,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo lesson to expose transform choice and body motion."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    analyses: list[dict[str, Any]] = []
    axis_swapping = {"transpose", "anti_transpose", "rot_cw", "rot_ccw"}
    body_motion_seen = False
    blue_reflection_refuted = False
    inverse_transform_refuted = False

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is missing input/output")
            continue
        analysis = _analyze(pair["input"])
        if analysis.get("errors"):
            errors.append(f"demo {index} input is malformed: {analysis['errors'][:2]!r}")
            continue
        expected = rule_mirror(pair["input"])
        try:
            actual = _coerce_grid(pair["output"])
        except ValueError as exc:
            errors.append(f"demo {index} output is malformed: {exc}")
            continue
        if actual != expected:
            errors.append(f"demo {index} output is not the keyed D4 transform of the full panel")
            continue
        if _rival_corner_only(pair["input"]) != actual:
            body_motion_seen = True
        if _rival_blue_corner_reflection(pair["input"]) != actual:
            blue_reflection_refuted = True
        if _rival_inverse_transform(pair["input"]) != actual:
            inverse_transform_refuted = True
        analyses.append(analysis)

    if len(analyses) == len(demos):
        symmetries = {item["symmetry"] for item in analyses}
        if len(symmetries) < 3:
            errors.append("demonstrations expose fewer than three distinct transforms")
        if not any(sym in axis_swapping for sym in symmetries):
            errors.append("demonstrations contain no axis-swapping transform")
        if not any(sym not in axis_swapping for sym in symmetries):
            errors.append("demonstrations contain no axis-preserving transform")
        if all(sym == "identity" for sym in symmetries):
            errors.append("demonstrations do not refute always-identity cropping")
        if not body_motion_seen:
            errors.append("demonstrations do not refute a corner-code-only shortcut")
        if not blue_reflection_refuted:
            errors.append("demonstrations do not refute the blue-corner-only reflection shortcut")
        if not inverse_transform_refuted:
            errors.append("demonstrations do not refute the inverse-transform shortcut")

    if not isinstance(query, dict) or "input" not in query:
        errors.append("query is missing its input")
    else:
        query_analysis = _analyze(query["input"])
        if query_analysis.get("errors"):
            errors.append("query input is malformed")
    return errors

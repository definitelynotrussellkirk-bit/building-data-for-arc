"""Generator for bank 54d03287ae93 task H41 / d68754fb0d84.

A connected color-2 template is accompanied by horizontal control pairs:
transform code 1..8 immediately left of a color-9 anchor.  The output clears
the input and stamps, at every anchor, the code-selected dihedral transform of
the normalized template in color 3.

The five public inputs use five different four/five-cell template bitmaps and
collectively exercise all eight codes.  Their complete answer-bearing profile
retains canvas dimensions, normalized template bitmap, and the linked relative
anchor/code gallery.  Template position is a lawful nuisance because the rule
normalizes it; joint gallery translation is also lawful.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d68754fb0d84"
VERSION = "3.0.0"
TASK_ID = "d68754fb0d84"
RULE_HASH = "edea3d411dc3"

SUMMARY = (
    "A 0-background 11..20 x 13..22 grid contains one connected color-2 "
    "template of 4..7 cells and one to four control pairs. Each pair is a "
    "code 1..8 immediately left of a color-9 anchor. The output is otherwise "
    "empty and stamps the corresponding identity/rotation/reflection of the "
    "normalized template in color 3 at each anchor."
)

INVARIANTS = [
    "exactly one connected 4..7-cell color-2 template is distinct from code-2 cells",
    "one to four color-9 anchors each have a distinct code 1..8 immediately left",
    "the template is encountered before every control pair in reading order",
    "every selected transformed stamp fits in-bounds and stamps are disjoint",
    "no nonzero input cells occur outside the template and control pairs",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 11..20",
        "valid": "11..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 13..22",
        "valid": "13..22",
    },
    "n_anchors": {
        "type": "int",
        "default": "difficulty-aware rng 1..4",
        "valid": "1..4",
    },
    "template_cells": {
        "type": "int",
        "default": "difficulty-aware rng 4..7",
        "valid": "4..7",
    },
}

_VALID_H = (11, 20)
_VALID_W = (13, 22)
_PROFILE_PRIOR = 0.08
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# (h, w, template_shape, template_top, template_left, anchors), where each
# anchor is (row, column_of_9, code).
_PROFILE_SPECS = (
    (
        11,
        14,
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        1,
        1,
        ((1, 8, 1), (5, 8, 2), (7, 3, 5)),
    ),
    (
        12,
        14,
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
        1,
        1,
        ((2, 9, 3), (6, 8, 4), (8, 3, 7)),
    ),
    (
        11,
        13,
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        1,
        1,
        ((2, 8, 6), (6, 7, 8), (7, 2, 1)),
    ),
    (
        12,
        15,
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        1,
        1,
        ((2, 10, 2), (6, 9, 5), (8, 3, 6)),
    ),
    (
        11,
        14,
        ((0, 0), (0, 1), (1, 1), (1, 2)),
        1,
        1,
        ((2, 9, 7), (6, 8, 3), (7, 3, 4)),
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _transform(shape, code):
    """Apply the canonical code map and normalize the transformed bitmap."""
    if code == 1:
        cells = shape
    elif code == 2:
        cells = ((c, -r) for r, c in shape)
    elif code == 3:
        cells = ((-r, -c) for r, c in shape)
    elif code == 4:
        cells = ((-c, r) for r, c in shape)
    elif code == 5:
        cells = ((r, -c) for r, c in shape)
    elif code == 6:
        cells = ((-r, c) for r, c in shape)
    elif code == 7:
        cells = ((c, r) for r, c in shape)
    elif code == 8:
        cells = ((-c, -r) for r, c in shape)
    else:
        raise ValueError(f"transform code {code} outside 1..8")
    return _normalize(cells)


def _polyomino_banks():
    banks = {1: (((0, 0),),)}
    current = {((0, 0),)}
    for size in range(2, 8):
        grown = set()
        for shape in current:
            occupied = set(shape)
            frontier = {
                (r + dr, c + dc)
                for r, c in shape
                for dr, dc in _CARDINAL
                if (r + dr, c + dc) not in occupied
            }
            for cell in frontier:
                grown.add(_normalize((*shape, cell)))
        current = grown
        banks[size] = tuple(sorted(current))
    return banks


_POLYOMINO_BANKS = _polyomino_banks()


def _is_connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARDINAL:
            neighbor = (r + dr, c + dc)
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == cells


def _analyze_scene(grid):
    h, w = len(grid), len(grid[0])
    problems = []
    anchors = []
    pair_cells = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 9:
                continue
            if c == 0 or not 1 <= grid[r][c - 1] <= 8:
                problems.append(
                    f"anchor at {(r, c)} lacks a code 1..8 immediately left"
                )
                continue
            code = grid[r][c - 1]
            anchors.append((r, c, code))
            pair_cells.update(((r, c - 1), (r, c)))

    template_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2 and (r, c) not in pair_cells
    }
    if not template_cells:
        problems.append("no color-2 template remains after excluding code-2 cells")
    elif not _is_connected(template_cells):
        problems.append("color-2 template is not one 4-connected component")

    allowed = pair_cells | template_cells
    outside = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) not in allowed
    ]
    if outside:
        problems.append(f"{len(outside)} nonzero cells lie outside the grammar")

    if template_cells and anchors:
        first_template = min(template_cells)
        if any((r, c - 1) <= first_template for r, c, _ in anchors):
            problems.append("a control pair precedes the template in reading order")
        code_twos = {
            (r, c - 1)
            for r, c, code in anchors
            if code == 2
        }
        if any(
            (r + dr, c + dc) in template_cells
            for r, c in code_twos
            for dr, dc in _CARDINAL
        ):
            problems.append("a code-2 cell touches and merges with the template")

    shape = _normalize(template_cells)
    stamp_cells = []
    for index, (r, c, code) in enumerate(anchors):
        transformed = _transform(shape, code) if shape else ()
        placed = {(r + dr, c + dc) for dr, dc in transformed}
        if any(not (0 <= rr < h and 0 <= cc < w) for rr, cc in placed):
            problems.append(f"anchor {index} selects an out-of-bounds stamp")
        stamp_cells.append(placed)
    for i in range(len(stamp_cells)):
        for j in range(i + 1, len(stamp_cells)):
            if stamp_cells[i] & stamp_cells[j]:
                problems.append(f"stamps {i} and {j} overlap")

    return {
        "anchors": tuple(sorted(anchors)),
        "pair_cells": pair_cells,
        "template_cells": template_cells,
        "shape": shape,
        "stamp_cells": stamp_cells,
        "problems": problems,
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid is empty or not a row sequence"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["grid contains a non-row value"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or not widths or next(iter(widths)) == 0:
        return ["grid is ragged or has empty rows"]
    g = _coerce_grid(grid)
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in g
        for value in row
    ):
        return ["grid contains a non-integer or color outside 0..9"]

    errors = []
    h, w = len(g), len(g[0])
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append(f"grid height {h} outside {_VALID_H[0]}..{_VALID_H[1]}")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append(f"grid width {w} outside {_VALID_W[0]}..{_VALID_W[1]}")
    scene = _analyze_scene(g)
    errors.extend(scene["problems"])
    template_size = len(scene["template_cells"])
    if not 4 <= template_size <= 7:
        errors.append(f"template has {template_size} cells, expected 4..7")
    anchors = scene["anchors"]
    if not 1 <= len(anchors) <= 4:
        errors.append(f"anchor count {len(anchors)} outside 1..4")
    codes = [code for _, _, code in anchors]
    if len(codes) != len(set(codes)):
        errors.append("control codes are not distinct")
    return errors


def _raw_profile_signature(grid):
    scene = _analyze_scene(grid)
    if scene["problems"] or not scene["anchors"] or not scene["shape"]:
        return None
    min_r = min(r for r, _, _ in scene["anchors"])
    min_c = min(c for _, c, _ in scene["anchors"])
    gallery = tuple(
        (r - min_r, c - min_c, code)
        for r, c, code in scene["anchors"]
    )
    return len(grid), len(grid[0]), scene["shape"], gallery


def canonical_profile_signature(grid):
    """Complete answer-bearing profile with only lawful nuisances removed."""
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not all(isinstance(row, (list, tuple)) for row in grid)
        or not grid[0]
        or any(len(row) != len(grid[0]) for row in grid)
    ):
        return None
    g = _coerce_grid(grid)
    if any(type(value) is not int for row in g for value in row):
        return None
    if self_check(g):
        return None
    return _raw_profile_signature(g)


def _canonical_grid_from_profile(profile):
    h, w, shape, tr, tc, anchors = profile
    grid = full_grid(h, w, 0)
    for dr, dc in shape:
        grid[tr + dr][tc + dc] = 2
    for r, c, code in anchors:
        grid[r][c - 1] = code
        grid[r][c] = 9
    return grid


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    canonical_profile_signature(_canonical_grid_from_profile(profile))
    for profile in _PROFILE_SPECS
)


def is_canonical_profile(grid):
    signature = canonical_profile_signature(grid)
    return (
        signature is not None
        and signature in _CANONICAL_PROFILE_SIGNATURES
    )


def observe_overrides(grid):
    """Observe exact semantic axes from the returned grid, never metadata."""
    try:
        g = _coerce_grid(grid)
        scene = _analyze_scene(g)
        return {
            "n_anchors": len(scene["anchors"]),
            "template_cells": len(scene["template_cells"]),
        }
    except (TypeError, ValueError, IndexError):
        return {}


def rule_mirror(grid):
    """Python spelling of the canonical Racket rule on valid inputs."""
    g = _coerce_grid(grid)
    scene = _analyze_scene(g)
    out = full_grid(len(g), len(g[0]), 0)
    for r, c, code in scene["anchors"]:
        for dr, dc in _transform(scene["shape"], code):
            out[r + dr][c + dc] = 3
    return out


@lru_cache(maxsize=None)
def _profile_options(profile):
    """All lawful gallery translations and independent template placements."""
    h, w, shape, _, _, anchors = profile
    gallery_cells = set()
    for r, c, code in anchors:
        gallery_cells.update(((r, c - 1), (r, c)))
        gallery_cells.update(
            (r + dr, c + dc)
            for dr, dc in _transform(shape, code)
        )
    min_r = min(r for r, _ in gallery_cells)
    max_r = max(r for r, _ in gallery_cells)
    min_c = min(c for _, c in gallery_cells)
    max_c = max(c for _, c in gallery_cells)
    options = []
    for shift_r in range(-min_r, h - max_r):
        for shift_c in range(-min_c, w - max_c):
            shifted_anchors = tuple(
                (r + shift_r, c + shift_c, code)
                for r, c, code in anchors
            )
            pair_cells = {
                cell
                for r, c, _ in shifted_anchors
                for cell in ((r, c - 1), (r, c))
            }
            for tr in range(0, h - max(r for r, _ in shape)):
                for tc in range(0, w - max(c for _, c in shape)):
                    template_cells = {
                        (tr + dr, tc + dc)
                        for dr, dc in shape
                    }
                    if template_cells & pair_cells:
                        continue
                    first_template = min(template_cells)
                    if any(
                        (r, c - 1) <= first_template
                        for r, c, _ in shifted_anchors
                    ):
                        continue
                    code_twos = {
                        (r, c - 1)
                        for r, c, code in shifted_anchors
                        if code == 2
                    }
                    if any(
                        (r + dr, c + dc) in template_cells
                        for r, c in code_twos
                        for dr, dc in _CARDINAL
                    ):
                        continue
                    options.append((tr, tc, shifted_anchors))
    return tuple(options)


def _draw_profile(profile, rng):
    h, w, shape, _, _, _ = profile
    options = _profile_options(profile)
    if not options:
        raise ValueError("public profile has no lawful nuisance placement")
    tr, tc, anchors = rng.choice(options)
    grid = full_grid(h, w, 0)
    for dr, dc in shape:
        grid[tr + dr][tc + dc] = 2
    for r, c, code in anchors:
        grid[r][c - 1] = code
        grid[r][c] = 9
    return grid


def _general_template_positions(h, w, shape):
    max_r = max(r for r, _ in shape)
    max_c = max(c for _, c in shape)
    return [
        (r, c)
        for r in range(0, min(4, h - max_r))
        for c in range(0, min(5, w - max_c))
    ]


def _place_general(h, w, shape, codes, rng):
    template_positions = _general_template_positions(h, w, shape)
    rng.shuffle(template_positions)
    transformed = {code: _transform(shape, code) for code in codes}

    for tr, tc in template_positions:
        template_cells = {(tr + r, tc + c) for r, c in shape}
        first_template = min(template_cells)
        candidates = {}
        for code in codes:
            shape_code = transformed[code]
            max_r = max(r for r, _ in shape_code)
            max_c = max(c for _, c in shape_code)
            legal = []
            for r in range(0, h - max_r):
                for c in range(1, w - max_c):
                    pair = {(r, c - 1), (r, c)}
                    if pair & template_cells or (r, c - 1) <= first_template:
                        continue
                    if code == 2 and any(
                        (r + dr, c - 1 + dc) in template_cells
                        for dr, dc in _CARDINAL
                    ):
                        continue
                    stamp = {
                        (r + dr, c + dc)
                        for dr, dc in shape_code
                    }
                    legal.append((r, c, pair, stamp))
            rng.shuffle(legal)
            candidates[code] = legal

        def search(index, used_pairs, used_stamps, placed):
            if index == len(codes):
                return tuple(placed)
            code = codes[index]
            for r, c, pair, stamp in candidates[code]:
                if pair & used_pairs or stamp & used_stamps:
                    continue
                result = search(
                    index + 1,
                    used_pairs | pair,
                    used_stamps | stamp,
                    (*placed, (r, c, code)),
                )
                if result is not None:
                    return result
            return None

        anchors = search(0, set(), set(), ())
        if anchors is not None:
            return tr, tc, anchors
    raise ValueError(
        f"cannot place {len(codes)} transformed stamps on {h}x{w}"
    )


def _draw_general(h, w, n_anchors, template_cells, rng, band):
    bank = _POLYOMINO_BANKS[template_cells]
    if band != "easy":
        asymmetric = tuple(
            shape
            for shape in bank
            if len({_transform(shape, code) for code in range(1, 9)}) == 8
        )
        if asymmetric:
            bank = asymmetric
    shape = rng.choice(bank)
    codes = tuple(rng.sample(range(1, 9), n_anchors))
    tr, tc, anchors = _place_general(h, w, shape, codes, rng)
    grid = full_grid(h, w, 0)
    for dr, dc in shape:
        grid[tr + dr][tc + dc] = 2
    for r, c, code in anchors:
        grid[r][c - 1] = code
        grid[r][c] = 9
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    exact_overrides = {
        label for label in AXES if overrides.get(label) is not None
    }
    profile = None
    if not exact_overrides:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_SPECS))),
            )
            profile = _PROFILE_SPECS[profile_index]

    if overrides.get("grid_h") is not None:
        h = ctx.draw_int("grid_h", *_VALID_H)
    elif profile is not None:
        h = ctx.draw_int("grid_h", profile[0], profile[0])
    else:
        h = ctx.draw_int(
            "grid_h",
            *{
                "easy": (11, 13),
                "medium": (12, 17),
                "hard": (16, 20),
            }[band],
        )

    if overrides.get("grid_w") is not None:
        w = ctx.draw_int("grid_w", *_VALID_W)
    elif profile is not None:
        w = ctx.draw_int("grid_w", profile[1], profile[1])
    else:
        w = ctx.draw_int(
            "grid_w",
            *{
                "easy": (13, 15),
                "medium": (14, 19),
                "hard": (18, 22),
            }[band],
        )

    if overrides.get("n_anchors") is not None:
        n_anchors = ctx.draw_int("n_anchors", 1, 4)
    elif profile is not None:
        n_anchors = ctx.draw_int(
            "n_anchors", len(profile[5]), len(profile[5])
        )
    else:
        n_anchors = ctx.draw_choice(
            "n_anchors",
            {
                "easy": (1, 2),
                "medium": (2, 3),
                "hard": (3, 4),
            }[band],
        )

    if overrides.get("template_cells") is not None:
        template_cells = ctx.draw_int("template_cells", 4, 7)
    elif profile is not None:
        template_cells = ctx.draw_int(
            "template_cells", len(profile[2]), len(profile[2])
        )
    else:
        template_cells = ctx.draw_int(
            "template_cells",
            *{
                "easy": (4, 4),
                "medium": (4, 6),
                "hard": (5, 7),
            }[band],
        )

    rng = ctx.draw_rng("layout")
    if profile is not None:
        grid = _draw_profile(profile, rng)
    else:
        grid = _draw_general(
            h,
            w,
            n_anchors,
            template_cells,
            rng,
            band,
        )
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid

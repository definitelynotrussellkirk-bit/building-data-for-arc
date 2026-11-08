"""Semantic generator for ARC task 03269f74e737.

A full-height maroon column separates a cropped template from a board.  Every
unrotated placement that agrees everywhere except for exactly one required
template cell is repaired with that cell's template color.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "03269f74e737"
VERSION = "4.0.1"
TASK_ID = "03269f74e737"
RULE_HASH = "d65573c288f6"
SUMMARY = (
    "Crop the template left of a maroon divider, scan the right board "
    "without rotations, and fill the sole missing required cell of every "
    "exact one-hole placement."
)
EXAMPLES_NEEDED = 4

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_test_1",
)
GENERAL_PROFILES = (
    "plain",
    "multicolor",
    "complete_copy",
    "two_hole",
    "wrong_color",
    "rotated_copy",
    "foreign_noise",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "rng: 3 linked public topology profiles + 7 generalized profiles",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "Exact observable topology: three public linked layouts, or a "
            "specific generalized matcher boundary."
        ),
    },
}
INVARIANTS = [
    "one full-height maroon(9) divider separates nonempty panels",
    "the left panel contains one connected cropped template",
    "the board contains at least one unrotated exact one-hole match",
    "every returned output visibly repairs all and only those matches",
    "near-miss profiles remain unchanged at their distractor placement",
]

BACKGROUND = 0
DIVIDER = 9
ARC_COLORS = tuple(range(1, 9))
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

# Public profiles store input topology only: canvas dimensions and the
# placement / missing-relative-cell descriptors recovered from the three
# canonical inputs. Outputs are always computed live by rule_mirror().
_PUBLIC_SPECS = {
    "public_train_1": {
        "height": 6,
        "board_width": 7,
        "copies": ((0, 1, 0, 1), (3, 4, 1, 0)),
        "minimum_noise": 1,
    },
    "public_train_2": {
        "height": 7,
        "board_width": 7,
        "copies": ((1, 0, 1, 2), (4, 3, 2, 1)),
        "minimum_noise": 0,
    },
    "public_test_1": {
        "height": 7,
        "board_width": 8,
        "copies": ((0, 2, 1, 0), (3, 0, 0, 1), (4, 5, 2, 1)),
        "minimum_noise": 0,
    },
}
_PLUS_MASK = frozenset(
    {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}
)
_SHAPE_MASKS = (
    frozenset({(0, 0), (1, 0), (2, 0), (2, 1)}),  # L
    frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}),  # T
    frozenset({(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)}),  # stair
    frozenset({(0, 0), (0, 1), (1, 1), (2, 0), (2, 1)}),  # U-ish
    frozenset({(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)}),  # zig
    frozenset({(0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)}),
)


def _copy_grid(grid):
    return [list(row) for row in grid]


def _normalize_cells(cells):
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset(
        (row - min_row, col - min_col) for row, col in cells
    )


def _mask_dimensions(mask):
    return (
        max(row for row, _ in mask) + 1,
        max(col for _, col in mask) + 1,
    )


def _rotate_mask_cw(mask):
    height, _ = _mask_dimensions(mask)
    return _normalize_cells((col, height - 1 - row) for row, col in mask)


def _rotate_template_cw(template):
    mask = frozenset(template)
    height, _ = _mask_dimensions(mask)
    rotated = {
        (col, height - 1 - row): value
        for (row, col), value in template.items()
    }
    min_row = min(row for row, _ in rotated)
    min_col = min(col for _, col in rotated)
    return {
        (row - min_row, col - min_col): value
        for (row, col), value in rotated.items()
    }


def _extract(grid):
    """Fail-closed parser matching the executable split/crop convention."""
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty rectangular matrix"]}
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {"errors": ["grid rows must be lists or tuples"]}
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return {"errors": ["grid must be rectangular and nonempty"]}
    height = len(grid)
    width = next(iter(widths))
    if not (5 <= height <= 30 and 7 <= width <= 30):
        errors.append("grid dimensions must be ARC-legal and fit two panels")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    divider_cols = [
        col
        for col in range(width)
        if all(grid[row][col] == DIVIDER for row in range(height))
    ]
    if len(divider_cols) != 1:
        errors.append(
            f"expected exactly one full-height maroon divider, got {len(divider_cols)}"
        )
        return {"errors": errors}
    divider_col = divider_cols[0]
    if divider_col == 0 or divider_col == width - 1:
        errors.append("divider must leave two nonempty panels")
        return {"errors": errors}
    left = [list(row[:divider_col]) for row in grid]
    board = [list(row[divider_col + 1 :]) for row in grid]
    cells = [
        (row, col, left[row][col])
        for row in range(height)
        for col in range(divider_col)
        if left[row][col] not in (BACKGROUND, DIVIDER)
    ]
    if not cells:
        errors.append("left panel must contain a nonzero template")
        return {"errors": errors}
    min_row = min(row for row, _, _ in cells)
    max_row = max(row for row, _, _ in cells)
    min_col = min(col for _, col, _ in cells)
    max_col = max(col for _, col, _ in cells)
    template_grid = [
        [
            left[row][col]
            for col in range(min_col, max_col + 1)
        ]
        for row in range(min_row, max_row + 1)
    ]
    template = {
        (row, col): value
        for row, values in enumerate(template_grid)
        for col, value in enumerate(values)
        if value != BACKGROUND
    }
    if any(value == DIVIDER for value in template.values()):
        errors.append("template may not contain divider color 9")
    if not _connected(frozenset(template)):
        errors.append("cropped template must be 4-connected")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "divider_col": divider_col,
        "left": left,
        "board": board,
        "template_grid": template_grid,
        "template": template,
        "template_height": len(template_grid),
        "template_width": len(template_grid[0]),
    }


def _connected(mask):
    if not mask:
        return False
    seen = {next(iter(mask))}
    frontier = list(seen)
    while frontier:
        row, col = frontier.pop()
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            other = (row + drow, col + dcol)
            if other in mask and other not in seen:
                seen.add(other)
                frontier.append(other)
    return len(seen) == len(mask)


def _window_signature(board, template, template_height, template_width, row, col):
    missing = []
    wrong = []
    extra = []
    for trow in range(template_height):
        for tcol in range(template_width):
            template_value = template.get((trow, tcol), BACKGROUND)
            board_value = board[row + trow][col + tcol]
            if template_value == BACKGROUND:
                if board_value != BACKGROUND:
                    extra.append((trow, tcol, board_value))
            elif board_value == BACKGROUND:
                missing.append((trow, tcol, template_value))
            elif board_value != template_value:
                wrong.append((trow, tcol, board_value))
    return missing, wrong, extra


def _scan_windows(board, template, holes, wrong=0):
    if not template:
        return []
    template_height, template_width = _mask_dimensions(frozenset(template))
    board_height = len(board)
    board_width = len(board[0])
    matches = []
    if template_height > board_height or template_width > board_width:
        return matches
    for row in range(board_height - template_height + 1):
        for col in range(board_width - template_width + 1):
            missing, wrong_cells, extra = _window_signature(
                board,
                template,
                template_height,
                template_width,
                row,
                col,
            )
            if (
                len(missing) == holes
                and len(wrong_cells) == wrong
                and not extra
            ):
                matches.append(
                    {
                        "row": row,
                        "col": col,
                        "missing": tuple(missing),
                        "wrong": tuple(wrong_cells),
                    }
                )
    return matches


def _repair(board, matches):
    output = _copy_grid(board)
    for match in matches:
        for trow, tcol, value in match["missing"]:
            output[match["row"] + trow][match["col"] + tcol] = value
    return output


def _public_signatures(name):
    spec = _PUBLIC_SPECS[name]
    height = spec["height"]
    width = spec["board_width"]
    signatures = set()
    for flip_rows in (False, True):
        for flip_cols in (False, True):
            transformed = []
            for row, col, missing_row, missing_col in spec["copies"]:
                if flip_rows:
                    row = height - (row + 3)
                    missing_row = 2 - missing_row
                if flip_cols:
                    col = width - (col + 3)
                    missing_col = 2 - missing_col
                transformed.append(
                    (row, col, missing_row, missing_col)
                )
            signatures.add(tuple(sorted(transformed)))
    return frozenset(signatures)


_PUBLIC_SIGNATURES = {
    name: _public_signatures(name) for name in PUBLIC_PROFILES
}


def _match_signature(matches):
    return tuple(
        sorted(
            (
                match["row"],
                match["col"],
                match["missing"][0][0],
                match["missing"][0][1],
            )
            for match in matches
        )
    )


def _classify_profile(facts):
    template = facts["template"]
    template_mask = frozenset(template)
    template_colors = set(template.values())
    matches = facts["matches"]
    if (
        facts["divider_col"] == 3
        and template_mask == _PLUS_MASK
        and len(template_colors) == 1
    ):
        signature = _match_signature(matches)
        for name in PUBLIC_PROFILES:
            spec = _PUBLIC_SPECS[name]
            if (
                facts["height"] == spec["height"]
                and len(facts["board"][0]) == spec["board_width"]
                and signature in _PUBLIC_SIGNATURES[name]
            ):
                return name

    if len(template_colors) > 1:
        return "multicolor"

    board = facts["board"]
    exact = _scan_windows(board, template, 0)
    two_hole = _scan_windows(board, template, 2)
    wrong = _scan_windows(board, template, 0, wrong=1)
    rotated = _rotate_template_cw(template)
    rotated_hits = []
    if frozenset(rotated) != template_mask:
        rotated_hits = _scan_windows(board, rotated, 1)
    if rotated_hits:
        return "rotated_copy"
    if exact:
        return "complete_copy"
    if two_hole:
        return "two_hole"
    if wrong:
        return "wrong_color"
    if any(
        value not in template_colors and value != BACKGROUND
        for row in board
        for value in row
    ):
        return "foreign_noise"
    return "plain"


def _analyze(grid):
    facts = _extract(grid)
    errors = list(facts["errors"])
    if errors or "template" not in facts:
        return {"errors": errors, "facts": None}
    matches = _scan_windows(facts["board"], facts["template"], 1)
    if not matches:
        errors.append("board must contain at least one exact one-hole match")
    output = _repair(facts["board"], matches)
    if output == facts["board"]:
        errors.append("rule must visibly repair the board")
    facts = {
        **facts,
        "matches": matches,
        "match_count": len(matches),
        "output": output,
        "changed_cells": sum(
            left != right
            for before_row, after_row in zip(facts["board"], output)
            for left, right in zip(before_row, after_row)
        ),
    }
    facts["profile"] = _classify_profile(facts)
    facts["family"] = (
        "linked" if facts["profile"] in PUBLIC_PROFILES else "generalized"
    )
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _copy_grid(analysis["facts"]["output"])


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    return analysis["facts"]["family"]


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["facts"]["profile"]}


def _flip_public(left, board, flip_rows, flip_cols):
    if flip_rows:
        left = list(reversed(left))
        board = list(reversed(board))
    if flip_cols:
        left = [list(reversed(row)) for row in left]
        board = [list(reversed(row)) for row in board]
    return left, board


def _compose(left, board):
    return [
        list(left_row) + [DIVIDER] + list(board_row)
        for left_row, board_row in zip(left, board)
    ]


def _paint_copy(board, template, row, col, drop=(), wrong=None):
    dropped = set(drop)
    for (trow, tcol), value in template.items():
        if (trow, tcol) in dropped:
            continue
        board[row + trow][col + tcol] = value
    if wrong is not None:
        trow, tcol, value = wrong
        board[row + trow][col + tcol] = value


def _build_public(profile, rng):
    spec = _PUBLIC_SPECS[profile]
    height = spec["height"]
    board_width = spec["board_width"]
    template_color = rng.choice(ARC_COLORS)
    foreign_colors = [
        color for color in ARC_COLORS if color != template_color
    ]
    template = {position: template_color for position in _PLUS_MASK}
    for _ in range(200):
        left = full_grid(height, 3, BACKGROUND)
        for (row, col), value in template.items():
            left[row][col] = value
        board = full_grid(height, board_width, BACKGROUND)
        occupied_boxes = []
        for row, col, missing_row, missing_col in spec["copies"]:
            _paint_copy(
                board,
                template,
                row,
                col,
                drop=((missing_row, missing_col),),
            )
            occupied_boxes.append((row, col, 3, 3))

        # The first public input proves unrelated foreign singleton cells are
        # legal. Randomized constrained singletons expand nuisance diversity
        # without changing the complete linked placement signature.
        noise_count = rng.randint(spec["minimum_noise"], 6)
        candidates = [
            (row, col)
            for row in range(height)
            for col in range(board_width)
            if board[row][col] == BACKGROUND
            and all(
                not (
                    box_row <= row < box_row + box_height
                    and box_col <= col < box_col + box_width
                )
                for box_row, box_col, box_height, box_width in occupied_boxes
            )
        ]
        rng.shuffle(candidates)
        for row, col in candidates[:noise_count]:
            board[row][col] = rng.choice(foreign_colors)

        flip_rows = bool(rng.randrange(2))
        flip_cols = bool(rng.randrange(2))
        left, board = _flip_public(
            left, board, flip_rows, flip_cols
        )
        grid = _compose(left, board)
        analysis = _analyze(grid)
        if (
            not analysis["errors"]
            and analysis["facts"]["profile"] == profile
        ):
            return grid
    raise RuntimeError(f"could not realize linked profile {profile}")


def _difficulty_shape(rng, band):
    if band == "easy":
        return rng.randint(6, 8), rng.randint(8, 11), 1
    if band == "medium":
        return rng.randint(8, 10), rng.randint(11, 15), 2
    return rng.randint(10, 12), rng.randint(15, 18), 3


def _boxes_separated(row, col, height, width, boxes):
    return all(
        row + height < other_row
        or other_row + other_height < row
        or col + width < other_col
        or other_col + other_width < col
        for other_row, other_col, other_height, other_width in boxes
    )


def _place_object(board, template, rng, boxes, kind, wrong_colors):
    template_height, template_width = _mask_dimensions(
        frozenset(template)
    )
    height = len(board)
    width = len(board[0])
    if template_height > height or template_width > width:
        return False
    for _ in range(200):
        row = rng.randint(0, height - template_height)
        col = rng.randint(0, width - template_width)
        if not _boxes_separated(
            row, col, template_height, template_width, boxes
        ):
            continue
        cells = sorted(template)
        if kind == "one_hole":
            drop = (rng.choice(cells),)
            wrong = None
        elif kind == "two_hole":
            drop = tuple(rng.sample(cells, 2))
            wrong = None
        elif kind == "complete":
            drop = ()
            wrong = None
        elif kind == "wrong_color":
            drop = ()
            trow, tcol = rng.choice(cells)
            wrong = (trow, tcol, rng.choice(wrong_colors))
        else:
            raise ValueError(kind)
        _paint_copy(board, template, row, col, drop=drop, wrong=wrong)
        boxes.append(
            (row, col, template_height, template_width)
        )
        return True
    return False


def _build_general(profile, rng, band):
    for _ in range(300):
        height, board_width, match_count = _difficulty_shape(rng, band)
        if profile == "rotated_copy":
            mask = rng.choice(
                [
                    candidate
                    for candidate in _SHAPE_MASKS
                    if _rotate_mask_cw(candidate) != candidate
                ]
            )
        else:
            mask = rng.choice(_SHAPE_MASKS)
        colors = rng.sample(
            ARC_COLORS, 2 if profile == "multicolor" else 1
        )
        template = {
            position: colors[index % len(colors)]
            for index, position in enumerate(sorted(mask))
        }
        template_height, template_width = _mask_dimensions(mask)
        if template_height > height or template_width > board_width:
            continue
        left_width = min(6, max(3, template_width + rng.randint(0, 2)))
        left = full_grid(height, left_width, BACKGROUND)
        top = rng.randint(0, height - template_height)
        left_col = rng.randint(0, left_width - template_width)
        for (row, col), value in template.items():
            left[top + row][left_col + col] = value
        board = full_grid(height, board_width, BACKGROUND)
        boxes = []
        wrong_colors = [
            color for color in ARC_COLORS if color not in set(colors)
        ]
        ok = all(
            _place_object(
                board,
                template,
                rng,
                boxes,
                "one_hole",
                wrong_colors,
            )
            for _ in range(match_count)
        )
        if not ok:
            continue
        special = {
            "complete_copy": "complete",
            "two_hole": "two_hole",
            "wrong_color": "wrong_color",
        }.get(profile)
        if special and not _place_object(
            board,
            template,
            rng,
            boxes,
            special,
            wrong_colors,
        ):
            continue
        if profile == "rotated_copy":
            rotated = _rotate_template_cw(template)
            if not _place_object(
                board,
                rotated,
                rng,
                boxes,
                "one_hole",
                wrong_colors,
            ):
                continue
        if profile == "foreign_noise":
            candidates = [
                (row, col)
                for row in range(height)
                for col in range(board_width)
                if board[row][col] == BACKGROUND
                and all(
                    not (
                        box_row - 1 <= row <= box_row + box_height
                        and box_col - 1 <= col <= box_col + box_width
                    )
                    for box_row, box_col, box_height, box_width in boxes
                )
            ]
            rng.shuffle(candidates)
            for row, col in candidates[: rng.randint(2, 5)]:
                board[row][col] = rng.choice(wrong_colors)
        grid = _compose(left, board)
        analysis = _analyze(grid)
        if (
            not analysis["errors"]
            and analysis["facts"]["profile"] == profile
            and analysis["facts"]["match_count"] == match_count
        ):
            return grid
    raise RuntimeError(f"could not realize generalized profile {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "scene_profile",
        SCENE_PROFILES,
    )
    band = "medium" if difficulty in (None, "default") else difficulty
    rng = ctx.draw_rng("scene")
    if profile in PUBLIC_PROFILES:
        grid = _build_public(profile, rng)
    else:
        grid = _build_general(profile, rng, band)
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["profile"] != profile:
        raise RuntimeError(
            "internal construction error: "
            + "; ".join(
                analysis["errors"]
                or [
                    f"wanted {profile}, observed "
                    f"{analysis['facts']['profile']}"
                ]
            )
        )
    return grid

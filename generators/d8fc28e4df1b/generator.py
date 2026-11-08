"""Generator for S20_H7 — mark candidate boards with the most rotated matches.

The input contains exactly four horizontal panels separated by one full-height
color-9 column: a narrow 3-column template followed by three wider candidate
boards.  The template is a cropped, asymmetric two-color motif.  A candidate's
score is the number of exact-color occurrences of that motif across its four
90-degree rotations; template zeroes are wildcards, exactly as in the Racket
oracle.  The output oracle emits a 1x3 cyan argmax strip.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d8fc28e4df1b"
VERSION = "3.0.0"
TASK_ID = "d8fc28e4df1b"
RULE_HASH = "335668385f45"
EXPECTED_OUTPUT_CODOMAIN = 7

SUMMARY = (
    "A 3-column two-color template panel is followed by three 7- or 8-column "
    "candidate boards, separated by single full-height maroon columns. Count "
    "exact-color occurrences of the cropped template in all four rotations "
    "inside each candidate (template zeroes are wildcards). Output marks every "
    "candidate tied for the positive maximum in a 1x3 cyan strip."
)

INVARIANTS = [
    "background is 0 and separators are exactly three one-column color-9 walls",
    "panel widths are [3, candidate_w, candidate_w, candidate_w]",
    "the cropped template has 5..7 cells, two colors, and four distinct rotations",
    "all candidate match counts are 0..3 and the positive argmax is nonempty",
]

PALETTE_KINDS = ("classic", "warm", "cool", "novel")
_PALETTE_PAIRS = {
    "classic": (2, 7),
    "warm": (1, 4),
    "cool": (3, 6),
    "novel": (5, 8),
}
WINNER_MASKS = ("100", "110", "010", "101", "001", "011", "111")

AXES = {
    "panel_h": {
        "type": "int",
        "default": "banded 7..8 easy, 7..9 medium, 8..9 hard",
        "valid": "7..9",
    },
    "candidate_w": {
        "type": "int",
        "default": "banded 7 easy, 7..8 medium/hard",
        "valid": "7..8",
    },
    "motif_cells": {
        "type": "int",
        "default": "banded 5..6 easy, 5..7 medium, 6..7 hard",
        "valid": "5..7",
    },
    "max_count": {
        "type": "int",
        "default": "banded 1..2 easy, 2..3 medium/hard",
        "valid": "1..3",
    },
    "winner_mask": {
        "type": "enum",
        "default": "sample_index curriculum over all nonempty 3-bit masks",
        "valid": WINNER_MASKS,
    },
    "palette_kind": {
        "type": "enum",
        "default": "rng classic|warm|cool|novel",
        "valid": PALETTE_KINDS,
    },
}

_CANONICAL_TEMPLATE = (
    (2, 7, 0),
    (2, 2, 2),
    (2, 0, 2),
)
# Complete linked official profiles: height, candidate width, exact count vector.
_CANONICAL_PROFILES = (
    (7, 7, (1, 2, 1)),
    (8, 8, (3, 2, 1)),
    (8, 8, (2, 3, 1)),
)
_CANONICAL_PROFILE_RATE = 2 / len(WINNER_MASKS)


def _rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotations(grid):
    out = []
    current = [row[:] for row in grid]
    for _ in range(4):
        out.append(current)
        current = _rotate(current)
    return out


def _crop_nonzero(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def _split_panels(grid):
    if not grid or not grid[0]:
        return [], []
    h, w = len(grid), len(grid[0])
    separators = [
        c for c in range(w) if all(grid[r][c] == 9 for r in range(h))
    ]
    panels = []
    start = 0
    for c in separators:
        if start < c:
            panels.append([row[start:c] for row in grid])
        start = c + 1
    if start < w:
        panels.append([row[start:w] for row in grid])
    return panels, separators


def _match_locations(board, template):
    matches = []
    for rotation, variant in enumerate(_rotations(template)):
        vh, vw = len(variant), len(variant[0])
        if vh > len(board) or vw > len(board[0]):
            continue
        for r0 in range(len(board) - vh + 1):
            for c0 in range(len(board[0]) - vw + 1):
                if all(
                    value == 0 or board[r0 + r][c0 + c] == value
                    for r, row in enumerate(variant)
                    for c, value in enumerate(row)
                ):
                    matches.append((rotation, r0, c0))
    return matches


def _count_vector(grid):
    panels, _ = _split_panels(grid)
    if len(panels) != 4:
        return ()
    template = _crop_nonzero(panels[0])
    return tuple(len(_match_locations(panel, template)) for panel in panels[1:])


def _winner_mask(counts):
    if len(counts) != 3 or max(counts, default=0) <= 0:
        return "000"
    maximum = max(counts)
    return "".join("1" if count == maximum else "0" for count in counts)


def _palette_kind(template):
    colors = {value for row in template for value in row if value != 0}
    for name, pair in _PALETTE_PAIRS.items():
        if colors == set(pair):
            return name
    return "unknown"


def canonical_profile_signature(grid):
    """Complete linked official-profile signature, or ``None``.

    This couples canvas height, all panel widths, the exact cropped template,
    and the three candidate counts.  Mixing dimensions from one official
    example with another example's count vector therefore does not pass as an
    official profile.
    """
    panels, separators = _split_panels(grid)
    if len(panels) != 4 or len(separators) != 3:
        return None
    widths = tuple(len(panel[0]) for panel in panels)
    counts = _count_vector(grid)
    template = tuple(tuple(row) for row in _crop_nonzero(panels[0]))
    return len(grid), widths, template, counts


def observe_overrides(grid):
    panels, _ = _split_panels(grid)
    if len(panels) != 4:
        return {}
    template = _crop_nonzero(panels[0])
    counts = _count_vector(grid)
    return {
        "panel_h": len(grid),
        "candidate_w": len(panels[1][0]),
        "motif_cells": sum(value != 0 for row in template for value in row),
        "max_count": max(counts, default=0),
        "winner_mask": _winner_mask(counts),
        "palette_kind": _palette_kind(template),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if not 7 <= h <= 9:
        errors.append(f"panel height {h} outside 7..9")
    bad_colors = sorted({v for row in grid for v in row if not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9})
    if bad_colors:
        errors.append(f"invalid ARC colors: {bad_colors}")

    panels, separators = _split_panels(grid)
    if len(separators) != 3:
        errors.append(f"expected exactly 3 full-height color-9 separators, got {len(separators)}")
    if len(panels) != 4:
        errors.append(f"expected exactly 4 panels, got {len(panels)}")
        return errors
    widths = [len(panel[0]) for panel in panels]
    if widths[0] != 3 or widths[1:] not in ([7, 7, 7], [8, 8, 8]):
        errors.append(f"expected panel widths [3,w,w,w] with w in 7..8, got {widths}")
    expected_separators = [3, 4 + widths[1], 5 + 2 * widths[1]]
    if separators != expected_separators:
        errors.append(f"separator positions {separators} != {expected_separators}")

    template = _crop_nonzero(panels[0])
    motif_cells = sum(value != 0 for row in template for value in row)
    if not 5 <= motif_cells <= 7:
        errors.append(f"template has {motif_cells} nonzero cells (expected 5..7)")
    if _palette_kind(template) == "unknown":
        errors.append("template must use exactly one declared two-color palette pair")
    if len({tuple(tuple(row) for row in v) for v in _rotations(template)}) != 4:
        errors.append("template must have four distinct 90-degree rotations")

    counts = _count_vector(grid)
    if len(counts) != 3:
        errors.append("could not compute three candidate match counts")
    else:
        if max(counts, default=0) not in (1, 2, 3):
            errors.append(f"positive maximum match count must be 1..3, got {counts}")
        if _winner_mask(counts) not in WINNER_MASKS:
            errors.append(f"candidate counts do not define a lawful nonempty winner mask: {counts}")
    candidate_densities = []
    for index, panel in enumerate(panels[1:]):
        density = _nonbackground_count(panel)
        candidate_densities.append(density)
        if density == 0:
            errors.append(f"candidate panel {index} is empty")

    # The public examples legitimately make match count and density correlate.
    # Generalized teaching scenes must explicitly break that shortcut.
    if canonical_profile_signature(grid) not in _official_signatures() and len(counts) == 3:
        mask = _winner_mask(counts)
        winners = [candidate_densities[i] for i, bit in enumerate(mask) if bit == "1"]
        losers = [candidate_densities[i] for i, bit in enumerate(mask) if bit == "0"]
        if mask not in WINNER_MASKS:
            pass  # a prior structural error already records the invalid answer state
        elif mask == "111":
            if len(set(candidate_densities)) == 1:
                errors.append("all-winner lesson must vary candidate density to rebut a density shortcut")
        elif not losers or max(losers) <= max(winners):
            errors.append("a losing candidate must be denser than every winner")
    return errors


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    if overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _make_template(rng, motif_cells, colors):
    """Build a connected 3x3 two-color motif with four unique rotations."""
    for _ in range(500):
        cells = {(rng.randrange(3), rng.randrange(3))}
        while len(cells) < motif_cells:
            frontier = []
            for r, c in cells:
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 3 and 0 <= nc < 3 and (nr, nc) not in cells:
                        frontier.append((nr, nc))
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) != motif_cells:
            continue
        if {r for r, _ in cells} != {0, 1, 2} or {c for _, c in cells} != {0, 1, 2}:
            continue
        template = full_grid(3, 3, 0)
        for r, c in cells:
            template[r][c] = colors[0]
        accent = rng.choice(sorted(cells))
        template[accent[0]][accent[1]] = colors[1]
        if len({tuple(tuple(row) for row in v) for v in _rotations(template)}) == 4:
            return template
    raise RuntimeError("failed to construct an asymmetric connected template")


def _place_variant(board, variant, r0, c0):
    for r, row in enumerate(variant):
        for c, value in enumerate(row):
            if value == 0:
                continue
            current = board[r0 + r][c0 + c]
            if current not in (0, value):
                return False
    for r, row in enumerate(variant):
        for c, value in enumerate(row):
            if value:
                board[r0 + r][c0 + c] = value
    return True


def _build_candidate(template, desired_count, panel_h, candidate_w, rng, rotation_offset, distractor_color):
    variants = _rotations(template)
    positions = [
        (0, 0),
        (0, candidate_w - 3),
        (panel_h - 3, 0),
        (panel_h - 3, candidate_w - 3),
        ((panel_h - 3) // 2, (candidate_w - 3) // 2),
    ]
    for attempt in range(600):
        board = full_grid(panel_h, candidate_w, 0)
        order = positions[:]
        rng.shuffle(order)
        ok = True
        for copy_index in range(desired_count):
            rotation = (rotation_offset + copy_index + attempt) % 4
            choices = order[:]
            rng.shuffle(choices)
            placed = False
            for r0, c0 in choices:
                trial = [row[:] for row in board]
                if _place_variant(trial, variants[rotation], r0, c0):
                    board = trial
                    order.remove((r0, c0))
                    placed = True
                    break
            if not placed:
                ok = False
                break
        if not ok or len(_match_locations(board, template)) != desired_count:
            continue

        # Each canonical board carries one wrong-color singleton.  Assigning a
        # different distractor color to each candidate reproduces the official
        # seven-color input palette without creating an exact template match.
        empties = [
            (r, c)
            for r in range(panel_h)
            for c in range(candidate_w)
            if board[r][c] == 0
        ]
        rng.shuffle(empties)
        if not empties:
            continue
        r, c = empties[0]
        board[r][c] = distractor_color
        if len(_match_locations(board, template)) == desired_count:
            return board
    raise RuntimeError(f"failed to construct candidate with exactly {desired_count} matches")



def _nonbackground_count(board):
    return sum(value not in (0, 9) for row in board for value in row)


def _add_wrong_color_cells(board, color, target_total, rng):
    """Raise board density with a color absent from the exact template.

    This cannot create an exact match and gives every non-canonical lesson a
    direct rebuttal to the tempting "choose the densest board" shortcut.
    """
    current = _nonbackground_count(board)
    if current >= target_total:
        return
    empties = [
        (r, c)
        for r in range(len(board))
        for c in range(len(board[0]))
        if board[r][c] == 0
    ]
    rng.shuffle(empties)
    need = target_total - current
    if len(empties) < need:
        raise RuntimeError("not enough empty cells for density distractors")
    for r, c in empties[:need]:
        board[r][c] = color


def _official_signatures():
    return {
        (h, (3, w, w, w), _CANONICAL_TEMPLATE, counts)
        for h, w, counts in _CANONICAL_PROFILES
    }

def _counts_for_mask(mask, maximum, rng):
    counts = []
    loser_values = list(range(maximum))
    for bit in mask:
        if bit == "1":
            counts.append(maximum)
        else:
            counts.append(rng.choice(loser_values))
    if maximum > 1 and mask.count("0") >= 2:
        loser_indexes = [i for i, bit in enumerate(mask) if bit == "0"]
        counts[loser_indexes[0]] = maximum - 1
        counts[loser_indexes[-1]] = 0
    return tuple(counts)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    if band == "easy":
        h_bounds, w_bounds, cells_bounds, count_bounds = (7, 8), (7, 7), (5, 6), (1, 2)
    elif band == "hard":
        h_bounds, w_bounds, cells_bounds, count_bounds = (8, 9), (7, 8), (6, 7), (2, 3)
    else:
        h_bounds, w_bounds, cells_bounds, count_bounds = (7, 9), (7, 8), (5, 7), (2, 3)

    has_override = any(value is not None for value in overrides.values())
    scheduled_mask = WINNER_MASKS[(seed + sample_index) % len(WINNER_MASKS)]
    eligible_profiles = [
        profile for profile in _CANONICAL_PROFILES
        if _winner_mask(profile[2]) == scheduled_mask
    ]
    # The ordinary sample-index curriculum is never hidden by the linked prior:
    # exact official profiles occupy the two schedule slots whose legal outputs
    # are 100 and 010, while the other five slots exercise the remaining masks.
    canonical_draw = not has_override and bool(eligible_profiles)
    if canonical_draw:
        panel_h, candidate_w, counts = rng.choice(eligible_profiles)
        motif_cells = ctx.draw_int("motif_cells", 7, 7)
        maximum = ctx.draw_int("max_count", max(counts), max(counts))
        mask = ctx.draw_choice("winner_mask", [_winner_mask(counts)])
        palette_kind = ctx.draw_choice("palette_kind", ["classic"])
        panel_h = ctx.draw_int("panel_h", panel_h, panel_h)
        candidate_w = ctx.draw_int("candidate_w", candidate_w, candidate_w)
        template = [list(row) for row in _CANONICAL_TEMPLATE]
    else:
        panel_h = _banded_int(ctx, overrides, "panel_h", *h_bounds, 7, 9)
        candidate_w = _banded_int(ctx, overrides, "candidate_w", *w_bounds, 7, 8)
        motif_cells = _banded_int(ctx, overrides, "motif_cells", *cells_bounds, 5, 7)
        maximum = _banded_int(ctx, overrides, "max_count", *count_bounds, 1, 3)
        if overrides.get("winner_mask") is not None:
            mask = ctx.draw_choice("winner_mask", WINNER_MASKS)
        else:
            mask = ctx.draw_choice("winner_mask", [scheduled_mask])
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
        counts = _counts_for_mask(mask, maximum, rng)
        template = _make_template(rng, motif_cells, _PALETTE_PAIRS[palette_kind])

    # All generated widths are at most 30: 3 + 3*candidate_w + 3 separators.
    total_w = 3 + 3 * candidate_w + 3
    grid = full_grid(panel_h, total_w, 0)
    separators = [3, 4 + candidate_w, 5 + 2 * candidate_w]
    for c in separators:
        for r in range(panel_h):
            grid[r][c] = 9

    template_row = rng.randint(0, panel_h - 3)
    for r, row in enumerate(template):
        for c, value in enumerate(row):
            if value:
                grid[template_row + r][c] = value

    template_colors = {value for row in template for value in row if value}
    distractor_colors = [
        color for color in range(1, 9) if color not in template_colors
    ][:3]
    starts = [4, 5 + candidate_w, 6 + 2 * candidate_w]
    boards = []
    for index, desired in enumerate(counts):
        boards.append(_build_candidate(
            template, desired, panel_h, candidate_w, rng,
            rotation_offset=(sample_index + index) % 4,
            distractor_color=distractor_colors[index],
        ))

    # Make density provably anti-predictive while preserving every exact match.
    densities = [_nonbackground_count(board) for board in boards]
    if mask == "111":
        _add_wrong_color_cells(
            boards[0], distractor_colors[0], max(densities) + 1, rng
        )
    else:
        winner_density = max(
            densities[index] for index, bit in enumerate(mask) if bit == "1"
        )
        loser_index = next(index for index, bit in enumerate(mask) if bit == "0")
        _add_wrong_color_cells(
            boards[loser_index], distractor_colors[loser_index],
            winner_density + 1, rng,
        )

    for index, (c0, board) in enumerate(zip(starts, boards)):
        if len(_match_locations(board, template)) != counts[index]:
            raise RuntimeError("density distractors changed an exact match count")
        for r in range(panel_h):
            grid[r][c0:c0 + candidate_w] = board[r]

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"internal generator error: {errors}")
    return grid

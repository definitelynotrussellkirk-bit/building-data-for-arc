"""Generator for ARC task 91714a58 / rule family 061566027b67.

Every public input is a dense 16x16 field using all ten ARC colors.  The
answer keeps only the unique largest same-color solid sub-rectangle at its
original coordinates and clears every other cell to zero.  Three of the
four unique public profiles attach one same-color tab to the winning
rectangle, so selecting the largest object or its bounding box is wrong.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "061566027b67"
TASK_ID = "061566027b67"
VERSION = "3.0.0"
RULE_HASH = "b9b141c6960a"

SUMMARY = (
    "On a dense 16x16 background-0 field using every color, enumerate "
    "same-color solid rectangles and keep only the unique maximum-area "
    "rectangle at its original coordinates. Winner-colored decoys and, "
    "in three demonstrated profiles, one attached same-color tab vanish."
)

INVARIANTS = [
    "the grid is 16x16 with background 0 and palette exactly 0..9",
    "72..102 cells are nonzero, matching the public density envelope",
    "one solid same-color rectangle is the unique maximum-area candidate",
    "the winner has 7..13 same-color cells outside its rectangle",
    "the public clean/tab profile is preserved under global D4 symmetry",
    "same-color noise adjacency outside the winner refutes isolated-dot shortcuts",
]

RECTANGLE_PROFILES = ("2x7_clean", "3x4_tab", "3x3_tab", "2x6_tab")
_PROFILE_SPECS = {
    "2x7_clean": (2, 7, False),
    "3x4_tab": (3, 4, True),
    "3x3_tab": (3, 3, True),
    "2x6_tab": (2, 6, True),
}
_PROFILE_INDEX = {
    name: index for index, name in enumerate(RECTANGLE_PROFILES)
}

AXES = {
    "rectangle_profile": {
        "type": "str",
        "default": "uniform over four published profiles",
        "valid": "2x7_clean|3x4_tab|3x3_tab|2x6_tab",
    },
    "winner_color": {
        "type": "int",
        "default": "uniform 1..9",
        "valid": "1..9",
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))


def _coerce_grid(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or len(grid) != 16:
        return None, ["grid must have exactly 16 rows"]
    coerced = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != 16:
            errors.append(f"row {row_index} must have exactly 16 cells")
            continue
        converted = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        coerced.append(converted)
    if errors:
        return None, errors
    return coerced, []


def _rectangle_analysis(grid):
    """Return the maximum solid rectangles in canonical enumeration order."""
    height = len(grid)
    width = len(grid[0])
    max_area = 0
    maxima = []
    for top in range(height):
        for left in range(width):
            color = grid[top][left]
            if color == 0:
                continue
            common_width = width - left
            for bottom in range(top, height):
                run = 0
                while (
                    run < common_width
                    and grid[bottom][left + run] == color
                ):
                    run += 1
                common_width = run
                if common_width == 0:
                    break
                right = left + common_width - 1
                area = (bottom - top + 1) * common_width
                candidate = (
                    area,
                    top,
                    left,
                    bottom,
                    right,
                    color,
                )
                if area > max_area:
                    max_area = area
                    maxima = [candidate]
                elif area == max_area:
                    maxima.append(candidate)
    return tuple(maxima)


def _best_rect(grid):
    maxima = _rectangle_analysis(grid)
    return maxima[0] if maxima else None


def _winner_cells(rectangle):
    _area, top, left, bottom, right, _color = rectangle
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }


def _cardinal_moat(rectangle):
    cells = _winner_cells(rectangle)
    moat = set()
    for row, col in cells:
        for delta_row, delta_col in _CARDINAL:
            neighbor = row + delta_row, col + delta_col
            if (
                0 <= neighbor[0] < 16
                and 0 <= neighbor[1] < 16
                and neighbor not in cells
            ):
                moat.add(neighbor)
    return moat


def _outside_same_color_adjacencies(grid, rectangle):
    winner = _winner_cells(rectangle)
    pairs = set()
    for row in range(16):
        for col in range(16):
            if (row, col) in winner or grid[row][col] == 0:
                continue
            for delta_row, delta_col in ((1, 0), (0, 1)):
                neighbor = row + delta_row, col + delta_col
                if (
                    0 <= neighbor[0] < 16
                    and 0 <= neighbor[1] < 16
                    and neighbor not in winner
                    and grid[neighbor[0]][neighbor[1]]
                    == grid[row][col]
                ):
                    pairs.add(((row, col), neighbor))
    return pairs


def _profile_name(rectangle, attached_count):
    area, top, left, bottom, right, _color = rectangle
    height = bottom - top + 1
    width = right - left + 1
    short, long = sorted((height, width))
    attached = attached_count == 1
    for name, (profile_short, profile_long, profile_attached) in (
        _PROFILE_SPECS.items()
    ):
        if (
            (short, long) == (profile_short, profile_long)
            and attached == profile_attached
            and area == profile_short * profile_long
        ):
            return name
    return None


def _scene_analysis(grid):
    coerced, errors = _coerce_grid(grid)
    if coerced is None:
        return None, {}, errors

    counts = Counter(value for row in coerced for value in row)
    if set(counts) != set(range(10)):
        errors.append("palette must contain every ARC color 0..9")
    if counts[0] != max(counts.values()):
        errors.append("zero must be a modal background")
    nonzero_count = 256 - counts[0]
    if not 72 <= nonzero_count <= 102:
        errors.append("nonzero cell count must be in public range 72..102")

    maxima = _rectangle_analysis(coerced)
    if not maxima:
        errors.append("scene must contain a nonzero rectangle")
        return coerced, {}, errors
    if len(maxima) != 1:
        errors.append(
            f"maximum solid rectangle must be unique, found {len(maxima)}"
        )
    rectangle = maxima[0]
    area, top, left, bottom, right, color = rectangle
    winner = _winner_cells(rectangle)
    moat = _cardinal_moat(rectangle)
    outside_same = {
        (row, col)
        for row in range(16)
        for col in range(16)
        if (row, col) not in winner and coerced[row][col] == color
    }
    attached = outside_same & moat
    profile_name = _profile_name(rectangle, len(attached))
    if profile_name is None:
        errors.append(
            "winner dimensions and attached-tab role must match a "
            "published profile"
        )
    if not 7 <= len(outside_same) <= 13:
        errors.append(
            "winner color must have 7..13 external decoy cells"
        )
    outside_palette = {
        coerced[row][col]
        for row in range(16)
        for col in range(16)
        if (row, col) not in winner and coerced[row][col] != 0
    }
    if outside_palette != set(range(1, 10)):
        errors.append(
            "noise outside the winner must contain every nonzero color"
        )
    adjacency_pairs = _outside_same_color_adjacencies(
        coerced,
        rectangle,
    )
    if not adjacency_pairs:
        errors.append(
            "noise must contain a same-color adjacency outside the winner"
        )

    features = {
        "rectangle": rectangle,
        "area": area,
        "top": top,
        "left": left,
        "bottom": bottom,
        "right": right,
        "winner_color": color,
        "winner_cells": frozenset(winner),
        "outside_same": frozenset(outside_same),
        "attached": frozenset(attached),
        "rectangle_profile": profile_name,
        "profile_index": (
            _PROFILE_INDEX.get(profile_name)
            if profile_name is not None
            else None
        ),
        "nonzero_count": nonzero_count,
        "adjacency_pairs": frozenset(adjacency_pairs),
    }
    return coerced, features, errors


def self_check(grid, *, difficulty=None, meta=None):
    """Return strict returned-grid curriculum errors."""
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    """Recover every declared semantic axis from a returned grid."""
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "rectangle_profile": features["rectangle_profile"],
        "winner_color": features["winner_color"],
    }


def _render_rule(grid, rectangle):
    _area, top, left, bottom, right, color = rectangle
    output = full_grid(16, 16, 0)
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            output[row][col] = color
    return output


def rule_mirror(grid):
    """Apply an independent Python mirror of the canonical Racket rule."""
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError(
            "invalid largest-rectangle lesson: " + "; ".join(errors)
        )
    return _render_rule(coerced, features["rectangle"])


def canonical_profile_index(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        return None
    return features["profile_index"]


def is_canonical_profile(grid):
    return canonical_profile_index(grid) is not None


def _tab_candidates(top, left, height, width):
    bottom = top + height - 1
    right = left + width - 1
    candidates = (
        (top - 1, left),
        (top - 1, right),
        (bottom + 1, left),
        (bottom + 1, right),
        (top, left - 1),
        (bottom, left - 1),
        (top, right + 1),
        (bottom, right + 1),
    )
    return tuple(
        cell
        for cell in candidates
        if 0 <= cell[0] < 16 and 0 <= cell[1] < 16
    )


def _choose_layout(short, long, attached, rng):
    transposed = bool(rng.randrange(2))
    height, width = (
        (long, short) if transposed else (short, long)
    )
    layouts = []
    for top in range(17 - height):
        for left in range(17 - width):
            tabs = _tab_candidates(top, left, height, width)
            if attached:
                layouts.extend(
                    (top, left, height, width, tab) for tab in tabs
                )
            else:
                layouts.append(
                    (top, left, height, width, None)
                )
    return rng.choice(layouts)


def _random_free_cell(rng, occupied, forbidden=()):
    forbidden = set(forbidden)
    choices = [
        (row, col)
        for row in range(16)
        for col in range(16)
        if (row, col) not in occupied
        and (row, col) not in forbidden
    ]
    if not choices:
        raise ValueError("no free cell remains")
    return rng.choice(choices)


def _place_noise_domino(grid, occupied, winner, rng):
    colors = [
        color for color in range(1, 10) if color != winner
    ]
    candidates = []
    for row in range(16):
        for col in range(16):
            for delta_row, delta_col in ((1, 0), (0, 1)):
                neighbor = row + delta_row, col + delta_col
                if (
                    neighbor[0] < 16
                    and neighbor[1] < 16
                    and (row, col) not in occupied
                    and neighbor not in occupied
                ):
                    candidates.append(((row, col), neighbor))
    first, second = rng.choice(candidates)
    color = rng.choice(colors)
    grid[first[0]][first[1]] = color
    grid[second[0]][second[1]] = color
    occupied.update((first, second))


def _density_range(difficulty):
    return {
        "easy": (72, 82),
        "medium": (82, 92),
        "hard": (92, 102),
        None: (72, 102),
    }[difficulty]


def _draw_scene(profile_name, winner_color, difficulty, rng):
    short, long, attached_mode = _PROFILE_SPECS[profile_name]
    for _attempt in range(120):
        top, left, height, width, tab = _choose_layout(
            short,
            long,
            attached_mode,
            rng,
        )
        bottom = top + height - 1
        right = left + width - 1
        rectangle = (
            height * width,
            top,
            left,
            bottom,
            right,
            winner_color,
        )
        winner_cells = _winner_cells(rectangle)
        moat = _cardinal_moat(rectangle)
        grid = full_grid(16, 16, 0)
        for row, col in winner_cells:
            grid[row][col] = winner_color
        occupied = set(winner_cells)
        if tab is not None:
            grid[tab[0]][tab[1]] = winner_color
            occupied.add(tab)

        external_winner_count = rng.randint(7, 13)
        remaining_winner = external_winner_count - int(tab is not None)
        for _index in range(remaining_winner):
            cell = _random_free_cell(
                rng,
                occupied,
                moat,
            )
            grid[cell[0]][cell[1]] = winner_color
            occupied.add(cell)

        # Ensure every other nonzero color appears outside the winner.
        for color in range(1, 10):
            if color == winner_color:
                continue
            cell = _random_free_cell(rng, occupied)
            grid[cell[0]][cell[1]] = color
            occupied.add(cell)

        # Public noise contains same-color runs; force one independent
        # domino so an isolated-dot shortcut cannot fit the curriculum.
        _place_noise_domino(grid, occupied, winner_color, rng)

        density_low, density_high = _density_range(difficulty)
        target_nonzero = rng.randint(density_low, density_high)
        filler_colors = [
            color
            for color in range(1, 10)
            if color != winner_color
        ]
        while len(occupied) < target_nonzero:
            color = rng.choice(filler_colors)
            cell = _random_free_cell(rng, occupied)
            grid[cell[0]][cell[1]] = color
            occupied.add(cell)

        _coerced, features, errors = _scene_analysis(grid)
        if not errors:
            if features["rectangle"] != rectangle:
                raise AssertionError("accepted scene changed intended winner")
            return grid, features
    raise ValueError("could not realize a strict largest-rectangle scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic, fresh, semantically validated input."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_name = ctx.draw_choice(
        "rectangle_profile",
        RECTANGLE_PROFILES,
    )
    winner_color = ctx.draw_int("winner_color", 1, 9)
    grid, features = _draw_scene(
        profile_name,
        winner_color,
        difficulty,
        ctx.draw_rng("scene"),
    )
    observed = {
        "rectangle_profile": features["rectangle_profile"],
        "winner_color": features["winner_color"],
    }
    expected = {
        "rectangle_profile": profile_name,
        "winner_color": winner_color,
    }
    if observed != expected:
        raise AssertionError(
            f"returned axes {observed!r} do not match {expected!r}"
        )
    return grid

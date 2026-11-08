"""Generator for ARC task 0eb83be0298d — mark match-window corners.

A three-column template panel and a search board are separated by one full
color-9 column.  The nonzero template cells define a monochrome 3x3 pattern;
zeroes inside the crop are wildcards.  For every original-orientation match in
the board, the canonical rule paints color 8 at the matched window's
bottom-right corner on an otherwise zero board.

The teaching distribution deliberately includes two kinds of lawful negative
evidence that the old sampler omitted:

* a rotated/reflected same-color near match, so connected components cannot be
  marked without consulting the template; and
* clutter in a wildcard cell of a true match, so template zeroes cannot be
  treated as literal background requirements.

Every generated grid is checked constructively: the requested exact-match set
must be realized exactly and all declared shortcut rivals must disagree with
the canonical Python diagnostic mirror.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0eb83be0298d"
TASK_ID = GENERATOR_ID
RULE_HASH = "4be3f14f70ed"
VERSION = "2.1.0"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4

SUMMARY = (
    "A three-column template panel and a board are separated by color 9. "
    "Find every original-orientation wildcard match of the cropped monochrome "
    "template and mark each matched window's bottom-right corner in color 8. "
    "Generated scenes include same-color orientation decoys and wildcard-slot "
    "clutter; every four-pair lesson also contains two board-only-family "
    "refutations, so the template must actually be used."
)

INVARIANTS = [
    "the sole full-height color-9 divider is column 3",
    "the cropped template is one supported connected monochrome 3x3 shape",
    "the board contains exactly the requested 1..3 original-orientation matches",
    "every board contains a same-color transformed decoy that is not a match",
    "every board contains clutter in a wildcard slot of a true match",
    "every default four-pair schedule window has two board-only-family refutations",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule or difficulty-aware 6..12",
        "valid": "6..12",
    },
    "board_w": {
        "type": "int",
        "default": "canonical-profile schedule or difficulty-aware 7..14",
        "valid": "7..14",
    },
    "shape_id": {
        "type": "int",
        "default": "teaching slots use shape 1; other slots use rng 0..4",
        "valid": "0..4",
    },
    "match_count": {
        "type": "int",
        "default": "easy 1..2, medium 2..3, hard 3",
        "valid": "1..3",
    },
    "template_color": {
        "type": "int",
        "default": "canonical anchors use 6; broad draws use 1..7",
        "valid": "1..7",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# All shapes are connected, asymmetric enough to have a distinct dihedral
# variant, occupy five cells, and span a 3x3 bounding box.  Shape 0 is the
# official template morphology.
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
)
_SHAPE_TO_ID = {shape: index for index, shape in enumerate(_SHAPES)}
SCHEDULE_PROFILES = (
    "canonical_6x11_palette3",
    "canonical_7x11_palette4",
    "canonical_7x12_palette3",
    "broad",
)
MIN_STRICT_FRAC = 1.0


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    seen = {next(iter(remaining))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in remaining and point not in seen:
                seen.add(point)
                queue.append(point)
    return seen == remaining


def _rotate(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((c, -r) for r, c in cells)


def _dihedral_variants(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    base = _normalize(cells)
    variants: set[tuple[tuple[int, int], ...]] = set()
    for reflected in (False, True):
        work = _normalize((r, -c if reflected else c) for r, c in base)
        for _ in range(4):
            variants.add(work)
            work = _rotate(work)
    return tuple(sorted(variants))


def _split_input(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]], int]:
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(dividers) != 1:
        raise ValueError(f"expected one full-height divider, got {dividers}")
    divider = dividers[0]
    if divider == 0 or divider == w - 1:
        raise ValueError("divider must have panels on both sides")
    return [row[:divider] for row in grid], [row[divider + 1:] for row in grid], divider


def _crop_template(panel: list[list[int]]) -> tuple[list[list[int]], tuple[tuple[int, int], ...], int | None]:
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not cells:
        return [], (), None
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    crop = [row[c0:c1 + 1] for row in panel[r0:r1 + 1]]
    colors = {value for row in crop for value in row if value not in (0, 9)}
    color = next(iter(colors)) if len(colors) == 1 else None
    shape = tuple(
        (r, c)
        for r, row in enumerate(crop)
        for c, value in enumerate(row)
        if value not in (0, 9)
    )
    return crop, _normalize(shape), color


def _match_positions(
    board: list[list[int]], shape: Iterable[tuple[int, int]], color: int
) -> list[tuple[int, int]]:
    shape = tuple(shape)
    if not board or not board[0] or not shape:
        return []
    h, w = len(board), len(board[0])
    sh, sw = _dims(shape)
    return [
        (r0, c0)
        for r0 in range(h - sh + 1)
        for c0 in range(w - sw + 1)
        if all(board[r0 + dr][c0 + dc] == color for dr, dc in shape)
    ]


def _stamp(
    board: list[list[int]],
    cells: Iterable[tuple[int, int]],
    top: int,
    left: int,
    color: int,
) -> None:
    for dr, dc in cells:
        if board[top + dr][left + dc] not in (0, color):
            raise ValueError("stamp collision")
    for dr, dc in cells:
        board[top + dr][left + dc] = color


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent diagnostic mirror of the selected Racket rule.

    Generation never calls this function for labels; the repository's Racket
    authority remains canonical.  Focused tests bind this mirror to all public
    canonical pairs.
    """
    panel, board, _ = _split_input(grid)
    _, shape, color = _crop_template(panel)
    if not shape or color is None:
        raise ValueError("template must be nonempty and monochrome")
    sh, sw = _dims(shape)
    out = full_grid(len(board), len(board[0]), 0)
    for r0, c0 in _match_positions(board, shape, color):
        out[r0 + sh - 1][c0 + sw - 1] = 8
    return out


def _literal_zero_matching_rival(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: require wildcard cells in the crop to be literal zeroes."""
    panel, board, _ = _split_input(grid)
    crop, shape, color = _crop_template(panel)
    if not shape or color is None:
        raise ValueError("template must be nonempty and monochrome")
    th, tw = len(crop), len(crop[0])
    out = full_grid(len(board), len(board[0]), 0)
    for r0 in range(len(board) - th + 1):
        for c0 in range(len(board[0]) - tw + 1):
            if all(
                board[r0 + r][c0 + c] == crop[r][c]
                for r in range(th)
                for c in range(tw)
            ):
                out[r0 + th - 1][c0 + tw - 1] = 8
    return out


def _dihedral_matching_rival(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: accept rotations and reflections as matches."""
    panel, board, _ = _split_input(grid)
    _, shape, color = _crop_template(panel)
    if not shape or color is None:
        raise ValueError("template must be nonempty and monochrome")
    out = full_grid(len(board), len(board[0]), 0)
    for variant in _dihedral_variants(shape):
        sh, sw = _dims(variant)
        for r0, c0 in _match_positions(board, variant, color):
            out[r0 + sh - 1][c0 + sw - 1] = 8
    return out


def _component_corner_rival(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule from the retained audit: ignore the template entirely.

    Split the board into same-color four-connected components and mark each
    component bounding box's bottom-right corner.
    """
    _, board, _ = _split_input(grid)
    h, w = len(board), len(board[0])
    out = full_grid(h, w, 0)
    seen: set[tuple[int, int]] = set()
    for start_r in range(h):
        for start_c in range(w):
            color = board[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            component: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and board[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out[max(r for r, _ in component)][max(c for _, c in component)] = 8
    return out



_BOARD_ONLY_VARIANTS: tuple[tuple[tuple[int, int], ...], ...] = tuple(
    dict.fromkeys(
        variant
        for shape in _SHAPES
        for variant in _dihedral_variants(shape)
    )
)


def _board_only_family_rival(grid: list[list[int]]) -> list[list[int]]:
    """Wrong lesson-level rule: infer a repeated known-family motif from the board.

    This deliberately ignores every template-panel cell.  It picks the most
    frequent board color, then the known-family orientation with wildcard
    clutter and the most exact occurrences.  The v2.0 distribution made this
    shortcut highly accurate, especially on hard lessons.
    """
    _, board, _ = _split_input(grid)
    counts = Counter(value for row in board for value in row if value not in (0, 9))
    if not counts:
        return full_grid(len(board), len(board[0]), 0)
    color = max(counts, key=lambda value: (counts[value], -value))
    candidates: list[
        tuple[
            tuple[bool, int, int, int],
            tuple[tuple[int, int], ...],
            list[tuple[int, int]],
        ]
    ] = []
    for index, shape in enumerate(_BOARD_ONLY_VARIANTS):
        matches = _match_positions(board, shape, color)
        if not matches:
            continue
        sh, sw = _dims(shape)
        occupied = set(shape)
        clutter = sum(
            board[r0 + r][c0 + c] != 0
            for r0, c0 in matches
            for r in range(sh)
            for c in range(sw)
            if (r, c) not in occupied
        )
        candidates.append(((clutter > 0, len(matches), clutter, -index), shape, matches))
    if not candidates:
        return full_grid(len(board), len(board[0]), 0)
    _, shape, matches = max(candidates, key=lambda item: item[0])
    sh, sw = _dims(shape)
    out = full_grid(len(board), len(board[0]), 0)
    for r0, c0 in matches:
        out[r0 + sh - 1][c0 + sw - 1] = 8
    return out


def _bbox(anchor: tuple[int, int], h: int = 3, w: int = 3) -> set[tuple[int, int]]:
    r0, c0 = anchor
    return {(r, c) for r in range(r0, r0 + h) for c in range(c0, c0 + w)}


def _select_anchors(h: int, w: int, count: int, rng) -> list[tuple[int, int]] | None:
    candidates = [(r, c) for r in range(h - 2) for c in range(w - 2)]
    rng.shuffle(candidates)

    def search(start: int, chosen: list[tuple[int, int]], occupied: set[tuple[int, int]]):
        if len(chosen) == count:
            return list(chosen)
        remaining_needed = count - len(chosen)
        if len(candidates) - start < remaining_needed:
            return None
        for index in range(start, len(candidates)):
            anchor = candidates[index]
            footprint = _bbox(anchor)
            if footprint & occupied:
                continue
            chosen.append(anchor)
            found = search(index + 1, chosen, occupied | footprint)
            if found is not None:
                return found
            chosen.pop()
        return None

    return search(0, [], set())


def _axis_int(ctx, name: str, lo: int, hi: int, default_lo: int, default_hi: int) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default_lo, default_hi)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _default_dimensions(profile: str, difficulty) -> tuple[tuple[int, int], tuple[int, int]]:
    if profile == "canonical_6x11_palette3":
        return (6, 6), (7, 7)
    if profile == "canonical_7x11_palette4":
        return (7, 7), (7, 7)
    if profile == "canonical_7x12_palette3":
        return (7, 7), (8, 8)
    if difficulty == "easy":
        return (6, 8), (7, 10)
    if difficulty == "hard":
        return (9, 12), (11, 14)
    return (7, 10), (8, 12)


def _default_match_range(difficulty) -> tuple[int, int]:
    if difficulty == "easy":
        return 1, 2
    if difficulty == "hard":
        return 3, 3
    return 2, 3


def _build_scene(
    *,
    h: int,
    board_w: int,
    shape: tuple[tuple[int, int], ...],
    template_color: int,
    match_count: int,
    use_alt_color: bool,
    require_board_only_refutation: bool,
    rng,
) -> tuple[list[list[int]], list[tuple[int, int]], tuple[int, int]]:
    variants = [variant for variant in _dihedral_variants(shape) if variant != shape]
    if not variants:
        raise ValueError("selected shape has no distinct transformed decoy")
    zero_slots = [(r, c) for r in range(3) for c in range(3) if (r, c) not in shape]
    alt_color = next(color for color in range(1, 9) if color != template_color)

    # Repeated constructive attempts are deterministic because every choice is
    # driven by the one keyed layout RNG.  No requested axis is clipped.
    attempt_limit = 2048 if require_board_only_refutation else 320
    for _attempt in range(attempt_limit):
        anchors = _select_anchors(h, board_w, match_count + 1, rng)
        if anchors is None:
            break
        rng.shuffle(anchors)
        positives = anchors[:match_count]
        decoy_anchor = anchors[-1]
        variant_order = list(variants)
        rng.shuffle(variant_order)
        clutter_order = list(zero_slots)
        rng.shuffle(clutter_order)
        positive_order = list(positives)
        rng.shuffle(positive_order)

        for decoy in variant_order:
            for clutter_anchor in positive_order:
                for dr, dc in clutter_order:
                    board = full_grid(h, board_w, 0)
                    for r0, c0 in positives:
                        _stamp(board, shape, r0, c0, template_color)
                    _stamp(board, decoy, decoy_anchor[0], decoy_anchor[1], template_color)
                    rr, cc = clutter_anchor[0] + dr, clutter_anchor[1] + dc
                    if board[rr][cc] != 0:
                        continue
                    board[rr][cc] = alt_color if use_alt_color else template_color
                    if set(_match_positions(board, shape, template_color)) != set(positives):
                        continue

                    template_panel = full_grid(h, 3, 0)
                    template_top = rng.randrange(0, h - 2)
                    _stamp(template_panel, shape, template_top, 0, template_color)
                    grid = [
                        template_panel[r] + [9] + board[r]
                        for r in range(h)
                    ]
                    truth = rule_mirror(grid)
                    if _component_corner_rival(grid) == truth:
                        continue
                    if _literal_zero_matching_rival(grid) == truth:
                        continue
                    if _dihedral_matching_rival(grid) == truth:
                        continue
                    if require_board_only_refutation and _board_only_family_rival(grid) == truth:
                        continue
                    return grid, positives, decoy_anchor
    raise ValueError(
        f"could not construct grid_h={h}, board_w={board_w}, "
        f"match_count={match_count} with required semantic decoys"
        + (" and board-only refutation" if require_board_only_refutation else "")
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    (h_lo, h_hi), (w_lo, w_hi) = _default_dimensions(profile, difficulty)
    h = _axis_int(ctx, "grid_h", 6, 12, h_lo, h_hi)
    board_w = _axis_int(ctx, "board_w", 7, 14, w_lo, w_hi)
    pure_default_draw = not overrides
    board_only_teaching_slot = profile in {
        "canonical_6x11_palette3",
        "canonical_7x12_palette3",
    }
    if ctx.overrides.get("shape_id") is not None:
        shape_id = ctx.draw_int_strict("shape_id", 0, len(_SHAPES) - 1)
    elif pure_default_draw and board_only_teaching_slot:
        # Shape 1 has broad constructive support for a board-only counterexample
        # even in the hard three-match profile.  The other slots retain all five.
        shape_id = ctx.draw_int_strict("shape_id", 1, 1)
    else:
        shape_id = ctx.draw_int_strict("shape_id", 0, len(_SHAPES) - 1)
    m_lo, m_hi = _default_match_range(difficulty)
    match_count = _axis_int(ctx, "match_count", 1, 3, m_lo, m_hi)

    canonical_profile = profile != "broad"
    if ctx.overrides.get("template_color") is not None:
        template_color = ctx.draw_int_strict("template_color", 1, 7)
    elif canonical_profile:
        template_color = ctx.draw_int_strict("template_color", 6, 6)
    else:
        template_color = ctx.draw_int_strict("template_color", 1, 7)

    # The second official profile has four input colors; the other two have
    # three.  Broad draws alternate both lawful palette sizes.
    use_alt_color = (
        profile == "canonical_7x11_palette4"
        or (profile == "broad" and ctx.draw_rng("palette_mode").randrange(2) == 1)
    )
    grid, _, _ = _build_scene(
        h=h,
        board_w=board_w,
        shape=_SHAPES[shape_id],
        template_color=template_color,
        match_count=match_count,
        use_alt_color=use_alt_color,
        require_board_only_refutation=pure_default_draw and board_only_teaching_slot,
        rng=ctx.draw_rng("layout"),
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructed invalid input: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {
        "grid_h": h,
        "board_w": board_w,
        "shape_id": shape_id,
        "match_count": match_count,
        "template_color": template_color,
    }
    if observed != requested:
        raise RuntimeError(f"axis realization drift: requested {requested}, observed {observed}")
    return grid


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    panel, board, _ = _split_input(grid)
    _, shape, color = _crop_template(panel)
    if shape not in _SHAPE_TO_ID or color is None:
        raise ValueError("input does not contain a supported monochrome template")
    return {
        "grid_h": len(grid),
        "board_w": len(board[0]),
        "shape_id": _SHAPE_TO_ID[shape],
        "match_count": len(_match_positions(board, shape, color)),
        "template_color": color,
    }


def semantic_observables(grid: list[list[int]]) -> dict[str, object]:
    panel, board, _ = _split_input(grid)
    crop, shape, color = _crop_template(panel)
    truth = rule_mirror(grid)
    return {
        **observe_overrides(grid),
        "template_bbox": list(_dims(shape)),
        "wildcard_clutter_cells": sum(
            crop[r][c] == 0 and board[r0 + r][c0 + c] != 0
            for r0, c0 in _match_positions(board, shape, color)
            for r in range(len(crop))
            for c in range(len(crop[0]))
        ),
        "component_shortcut_disagrees": _component_corner_rival(grid) != truth,
        "literal_zero_shortcut_disagrees": _literal_zero_matching_rival(grid) != truth,
        "dihedral_shortcut_disagrees": _dihedral_matching_rival(grid) != truth,
        "board_only_family_shortcut_disagrees": _board_only_family_rival(grid) != truth,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid is ragged"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    errors: list[str] = []
    h = len(grid)
    if not 5 <= h <= 16:
        errors.append(f"grid height {h} outside 5..16")
    try:
        panel, board, divider = _split_input([list(row) for row in grid])
    except ValueError as exc:
        return errors + [str(exc)]
    if divider != 3:
        errors.append(f"divider must be column 3, got {divider}")
    if any(grid[r][c] == 9 for r in range(h) for c in range(width) if c != divider):
        errors.append("color 9 appears outside the divider")
    if len(panel[0]) != 3:
        errors.append(f"template panel width must be 3, got {len(panel[0])}")
    if not 7 <= len(board[0]) <= 18:
        errors.append(f"board width {len(board[0])} outside 7..18")

    crop, shape, color = _crop_template(panel)
    if not shape:
        errors.append("template panel has no nonzero object")
        return errors
    colors = {value for row in crop for value in row if value not in (0, 9)}
    if len(colors) != 1 or color is None or color not in range(1, 9):
        errors.append(f"template must be monochrome color 1..8, got {sorted(colors)}")
    if not 3 <= len(shape) <= 7:
        errors.append(f"template has {len(shape)} occupied cells; expected 3..7")
    if not _connected(shape):
        errors.append("template object is not four-connected")
    sh, sw = _dims(shape)
    if sh > 3 or sw > 3:
        errors.append(f"cropped template {sh}x{sw} exceeds 3x3")
    if color is not None:
        hits = _match_positions(board, shape, color)
        if not 1 <= len(hits) <= 8:
            errors.append(f"board has {len(hits)} matches; expected 1..8")
    return errors


def strict_canonical_like(grid):
    errors = list(self_check(grid))
    if errors:
        return errors
    panel, _, _ = _split_input(grid)
    _, shape, _ = _crop_template(panel)
    if shape not in _SHAPE_TO_ID:
        errors.append("template morphology is outside the supported task family")
    return errors


def mutation_fixtures():
    valid = generate(0x0EB83, 0, difficulty="medium")
    fixtures = []

    broken_divider = deepcopy(valid)
    broken_divider[len(broken_divider) // 2][3] = 0
    fixtures.append(("broken_divider", broken_divider))

    empty_template = deepcopy(valid)
    for row in empty_template:
        for c in range(3):
            row[c] = 0
    fixtures.append(("empty_template", empty_template))

    no_matches = deepcopy(valid)
    for row in no_matches:
        for c in range(4, len(row)):
            row[c] = 0
    fixtures.append(("board_without_matches", no_matches))
    return fixtures


def _component_witness(grid):
    return _component_corner_rival(grid) != rule_mirror(grid)


def _literal_zero_witness(grid):
    return _literal_zero_matching_rival(grid) != rule_mirror(grid)


def _dihedral_witness(grid):
    return _dihedral_matching_rival(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "template_required_component_decoy": _component_witness,
    "wildcard_slot_clutter": _literal_zero_witness,
    "original_orientation_only": _dihedral_witness,
}
SEMANTIC_RIVALS = {
    "component_bbox_corner": _component_corner_rival,
    "literal_zero_matching": _literal_zero_matching_rival,
    "dihedral_matching": _dihedral_matching_rival,
}
WITNESS_RIVALS = {
    "template_required_component_decoy": ["component_bbox_corner"],
    "wildcard_slot_clutter": ["literal_zero_matching"],
    "original_orientation_only": ["dihedral_matching"],
}
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "board_only_family_frequency": _board_only_family_rival,
}
# The official labels never place clutter in a template wildcard slot, so the
# plausible but wrong literal-zero interpretation fits every canonical pair.
# Repaired generated scenes refute it constructively on every draw.
CANONICAL_SHORTCUTS = {
    "literal_zero_matching": _literal_zero_matching_rival,
}


def lesson_identifiable(demos, query):
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing input"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demonstration {index} is missing input/output")
            continue
        grammar = strict_canonical_like(pair["input"])
        if grammar:
            reasons.append(f"demonstration {index} is outside the task grammar: {grammar[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demonstration {index} output disagrees with the rule mirror")
    if reasons:
        return sorted(set(reasons))

    query_input = query["input"]
    grammar = strict_canonical_like(query_input)
    if grammar:
        reasons.append(f"query is outside the task grammar: {grammar[0]}")
        return reasons
    query_truth = rule_mirror(query_input)
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
            if survives and rival(query_input) != query_truth:
                reasons.append(f"competitor {name} fits every demonstration and differs on query")
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
    return sorted(set(reasons))

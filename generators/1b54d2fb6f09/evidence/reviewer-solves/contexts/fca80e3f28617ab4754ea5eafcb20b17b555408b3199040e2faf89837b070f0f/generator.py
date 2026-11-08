"""Generator for arc_additional_puzzle_bank_volume17:E113.

Find every 4-connected red (2) component that is a gapless horizontal or
vertical segment. Recolor exactly the two extreme cells of each such segment
to cyan (8). Preserve segment interiors, bent red components, background, and
all non-red distractors.

The generated curriculum makes the rule identifiable rather than merely
executable. Every ordinary draw contains both red orientations, one length-two
boundary case, at least one longer segment with a preserved interior, one bent
red negative control, and one differently colored connected distractor. Four
consecutive samples cover multiple segment counts, multiple distractor colors,
and both straight/non-straight distractor shapes, refuting position-,
color-blind-, count-, minimum-length-, and recolor-all shortcuts.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1b54d2fb6f09"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "c2a92b447e5a"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Find each 4-connected red component that is a gapless horizontal or "
    "vertical segment. Recolor only its two extreme endpoints cyan (8); leave "
    "the red interior unchanged. Bent red components and every non-red object "
    "are distractors and remain unchanged."
)

INVARIANTS = [
    "background is 0 and input colors exclude cyan 8",
    "there is exactly one connected non-red distractor color/object",
    "red components are separated under 4-connectivity",
    "at least one red component is a gapless straight segment of length >=2",
    "ordinary draws contain both straight orientations and an exact length-two segment",
    "ordinary draws contain a longer segment, a bent red control, and a distractor",
]

_DISTRACTOR_COLORS = (1, 3, 4, 5, 6, 7, 9)
_DISTRACTOR_SHAPES = ("line", "corner")
_CANONICAL_SIZES = ((7, 8), (8, 9), (9, 9), (8, 10), (9, 10))
_BAND_SIZES = {
    "easy": ((10, 11), (11, 12)),
    "medium": ((11, 13), (12, 14), (13, 13)),
    "hard": ((14, 16), (16, 17), (17, 18)),
}

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical/band size", "valid": "7..18"},
    "grid_w": {"type": "int", "default": "scheduled canonical/band size", "valid": "8..18"},
    "n_straight": {"type": "int", "default": "cycles 2..4", "valid": "2..4"},
    "distractor_color": {
        "type": "int",
        "default": "cycles across non-0/2/8 colors",
        "valid": "1|3|4|5|6|7|9",
    },
    "distractor_shape": {
        "type": "str",
        "default": "alternates line/corner",
        "valid": "line|corner",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
SCHEDULE_PROFILES = (0, 1, 2, 3)

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    del seed, difficulty
    return sample_index % 4


def _scheduled_size(seed: int, sample_index: int, band: str) -> tuple[int, int]:
    profile = schedule_profile(seed, sample_index, band)
    if profile in (0, 2):
        return _CANONICAL_SIZES[(seed + sample_index // 2) % len(_CANONICAL_SIZES)]
    options = _BAND_SIZES[band]
    return options[(seed + sample_index) % len(options)]


def _draw_int_axis(ctx, overrides: dict[str, Any], name: str, lo: int, hi: int, default: int) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def _draw_choice_axis(ctx, overrides: dict[str, Any], name: str, options: tuple[Any, ...], default: Any):
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _translate(shape: Iterable[tuple[int, int]], r0: int, c0: int) -> tuple[tuple[int, int], ...]:
    return tuple(sorted((r0 + r, c0 + c) for r, c in shape))


def _normalize(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(shape)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_transforms(shape: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    forms: list[tuple[tuple[int, int], ...]] = []
    current = _normalize(shape)
    for _ in range(4):
        for form in (current, _normalize((r, -c) for r, c in current)):
            if form not in forms:
                forms.append(form)
        current = _normalize((c, -r) for r, c in current)
    return tuple(forms)


def _placed_forms(h: int, w: int, forms: Iterable[tuple[tuple[int, int], ...]]):
    candidates: list[tuple[tuple[int, int], ...]] = []
    for form in forms:
        fh = max(r for r, _ in form) + 1
        fw = max(c for _, c in form) + 1
        for r0 in range(h - fh + 1):
            for c0 in range(w - fw + 1):
                candidates.append(_translate(form, r0, c0))
    return candidates


def _straight_candidates(
    h: int,
    w: int,
    orientation: str,
    min_length: int,
    max_length: int = 6,
):
    candidates: list[tuple[tuple[int, int], ...]] = []
    if orientation == "horizontal":
        for length in range(min_length, min(max_length, 6, w) + 1):
            for r in range(h):
                for c in range(w - length + 1):
                    candidates.append(tuple((r, c + i) for i in range(length)))
    else:
        for length in range(min_length, min(max_length, 6, h) + 1):
            for r in range(h - length + 1):
                for c in range(w):
                    candidates.append(tuple((r + i, c) for i in range(length)))
    return candidates


def _separate_from(cells: Iterable[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    cells = tuple(cells)
    if any(cell in occupied for cell in cells):
        return False
    return all(
        (r + dr, c + dc) not in occupied
        for r, c in cells
        for dr, dc in _CARDINAL
    )


def _choose_red_components(h: int, w: int, n_straight: int, rng):
    # A four-cell L is the negative control: it is red and connected, but not a
    # straight segment, so the endpoint rule must leave it untouched.
    bent_forms = _shape_transforms(((0, 0), (1, 0), (2, 0), (2, 1)))
    bent_candidates = _placed_forms(h, w, bent_forms)
    rng.shuffle(bent_candidates)

    first_orientation = "horizontal" if rng.getrandbits(1) else "vertical"
    orientations = [
        first_orientation if i % 2 == 0 else ("vertical" if first_orientation == "horizontal" else "horizontal")
        for i in range(n_straight)
    ]
    slot_candidates: list[list[tuple[tuple[int, int], ...]]] = [bent_candidates]
    for index, orientation in enumerate(orientations):
        if index == 0:
            # The authority applies at length two, so every ordinary example
            # carries this canonical-fitting boundary witness.
            candidates = _straight_candidates(h, w, orientation, 2, 2)
        elif index == 1:
            # Retain a visible red interior so recolor-all remains falsifiable.
            candidates = _straight_candidates(h, w, orientation, 4)
        else:
            candidates = _straight_candidates(h, w, orientation, 3)
        rng.shuffle(candidates)
        slot_candidates.append(candidates)

    chosen: list[tuple[tuple[int, int], ...]] = []
    occupied: set[tuple[int, int]] = set()

    def search(slot: int) -> bool:
        if slot == len(slot_candidates):
            return True
        for cells in slot_candidates[slot]:
            if not _separate_from(cells, occupied):
                continue
            chosen.append(cells)
            occupied.update(cells)
            if search(slot + 1):
                return True
            chosen.pop()
            occupied.difference_update(cells)
        return False

    if not search(0):
        raise ValueError(
            f"unable to place {n_straight} separated straight components plus bent control in {h}x{w}"
        )
    return chosen[0], chosen[1:]


def _choose_distractor(h: int, w: int, shape_name: str, occupied: set[tuple[int, int]], rng):
    if shape_name == "line":
        base = ((0, 0), (0, 1), (0, 2))
    else:
        base = ((0, 0), (1, 0), (1, 1))
    candidates = _placed_forms(h, w, _shape_transforms(base))
    rng.shuffle(candidates)
    for cells in candidates:
        if not any(cell in occupied for cell in cells):
            return cells
    raise ValueError(f"unable to place {shape_name} distractor in {h}x{w}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    default_h, default_w = _scheduled_size(seed, sample_index, band)
    h = _draw_int_axis(ctx, overrides, "grid_h", 7, 18, default_h)
    w = _draw_int_axis(ctx, overrides, "grid_w", 8, 18, default_w)
    n_straight = _draw_int_axis(
        ctx, overrides, "n_straight", 2, 4, 2 + sample_index % 3
    )
    default_color = _DISTRACTOR_COLORS[sample_index % len(_DISTRACTOR_COLORS)]
    distractor_color = _draw_choice_axis(
        ctx, overrides, "distractor_color", _DISTRACTOR_COLORS, default_color
    )
    default_shape = _DISTRACTOR_SHAPES[sample_index % len(_DISTRACTOR_SHAPES)]
    distractor_shape = _draw_choice_axis(
        ctx, overrides, "distractor_shape", _DISTRACTOR_SHAPES, default_shape
    )

    placement_rng = ctx.draw_rng("placement")
    bent, straights = _choose_red_components(h, w, n_straight, placement_rng)
    red_cells = set(bent)
    for cells in straights:
        red_cells.update(cells)
    distractor = _choose_distractor(
        h, w, distractor_shape, red_cells, placement_rng
    )

    grid = full_grid(h, w, 0)
    for r, c in red_cells:
        grid[r][c] = 2
    for r, c in distractor:
        grid[r][c] = distractor_color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError(f"internal generator invariant failed: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_straight": n_straight,
        "distractor_color": distractor_color,
        "distractor_shape": distractor_shape,
    }
    if observed != expected:
        raise AssertionError(f"observer mismatch: expected {expected}, got {observed}")
    return grid


def _components(grid: Any, color: int) -> list[tuple[tuple[int, int], ...]]:
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    components: list[tuple[tuple[int, int], ...]] = []
    while remaining:
        start = min(remaining)
        queue = deque([start])
        remaining.remove(start)
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    queue.append(nxt)
        components.append(tuple(sorted(cells)))
    return components


def _straight_info(cells: Iterable[tuple[int, int]]):
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    if len(set(rows)) == 1 and len(cells) == max(cols) - min(cols) + 1:
        r = rows[0]
        return "horizontal", ((r, min(cols)), (r, max(cols)))
    if len(set(cols)) == 1 and len(cells) == max(rows) - min(rows) + 1:
        c = cols[0]
        return "vertical", ((min(rows), c), (max(rows), c))
    return None, ()


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return info, ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return info, ["grid rows must be non-empty"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return info, ["grid must be rectangular"]
    if not (7 <= h <= 18 and 8 <= w <= 18):
        errors.append(f"grid dimensions {h}x{w} outside 7..18 by 8..18")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        errors.append("grid contains a non-ARC color")
        return info, errors

    palette = {value for row in grid for value in row}
    if 0 not in palette:
        errors.append("background color 0 is absent")
    if 8 in palette:
        errors.append("cyan 8 belongs only in the output, not the input")
    distractor_colors = sorted(palette - {0, 2})
    if len(distractor_colors) != 1:
        errors.append(
            f"expected exactly one non-red distractor color, got {distractor_colors}"
        )
    distractor_color = distractor_colors[0] if len(distractor_colors) == 1 else None

    red_components = _components(grid, 2)
    straight_records = []
    bent_records = []
    for cells in red_components:
        if len(cells) < 2:
            errors.append("red singleton components are not lawful")
            continue
        orientation, endpoints = _straight_info(cells)
        if orientation:
            straight_records.append(
                {"cells": cells, "orientation": orientation, "endpoints": endpoints}
            )
        else:
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            if not (3 <= len(cells) <= 7 and len(set(rows)) >= 2 and len(set(cols)) >= 2):
                errors.append(
                    f"non-straight red component has unsupported geometry/size {len(cells)}"
                )
            bent_records.append({"cells": cells})
    if not (1 <= len(straight_records) <= 4):
        errors.append(f"expected 1..4 straight red components, got {len(straight_records)}")
    if len(bent_records) > 1:
        errors.append(f"expected at most one bent red control, got {len(bent_records)}")

    distractor_components = _components(grid, distractor_color) if distractor_color is not None else []
    if len(distractor_components) != 1:
        errors.append(
            f"expected one connected distractor object, got {len(distractor_components)}"
        )
        distractor_shape = None
    else:
        cells = distractor_components[0]
        if not (2 <= len(cells) <= 5):
            errors.append(f"distractor size {len(cells)} outside 2..5")
        orientation, _ = _straight_info(cells)
        distractor_shape = "line" if orientation else "corner"
        if not orientation:
            rows = {r for r, _ in cells}
            cols = {c for _, c in cells}
            if len(rows) < 2 or len(cols) < 2:
                errors.append("non-line distractor must bend across rows and columns")

    info.update(
        {
            "grid_h": h,
            "grid_w": w,
            "palette": tuple(sorted(palette)),
            "red_components": tuple(red_components),
            "straights": tuple(straight_records),
            "bents": tuple(bent_records),
            "n_straight": len(straight_records),
            "distractor_color": distractor_color,
            "distractor_shape": distractor_shape,
            "distractor_components": tuple(distractor_components),
        }
    )
    return info, errors


def observe_overrides(grid: Any) -> dict[str, Any]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return _analyze(grid)[1]


def strict_canonical_like(grid: Any) -> list[str]:
    return _analyze(grid)[1]


def rule_mirror(grid: Any) -> list[list[int]]:
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    for record in info["straights"]:
        for r, c in record["endpoints"]:
            out[r][c] = 8
    return out


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_recolor_all_straight_red(grid):
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    for record in info["straights"]:
        for r, c in record["cells"]:
            out[r][c] = 8
    return out


def _rival_one_endpoint(grid):
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    for record in info["straights"]:
        r, c = min(record["endpoints"])
        out[r][c] = 8
    return out


def _rival_color_blind_straights(grid):
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = rule_mirror(grid)
    color = info["distractor_color"]
    for cells in info["distractor_components"]:
        _, endpoints = _straight_info(cells)
        for r, c in endpoints:
            out[r][c] = 8
    return out


def _rival_degree_endpoints_all_red(grid):
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    for cells in info["red_components"]:
        cell_set = set(cells)
        for r, c in cells:
            degree = sum((r + dr, c + dc) in cell_set for dr, dc in _CARDINAL)
            if degree == 1:
                out[r][c] = 8
    return out


def _rival_orientation_only(grid, allowed: str):
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    for record in info["straights"]:
        if record["orientation"] == allowed:
            for r, c in record["endpoints"]:
                out[r][c] = 8
    return out


def _rival_horizontal_only(grid):
    return _rival_orientation_only(grid, "horizontal")


def _rival_vertical_only(grid):
    return _rival_orientation_only(grid, "vertical")


def _rival_skip_length_two_segments(grid):
    """Canonical-fitting shortcut: transform only straight runs of length >=3."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    for record in info["straights"]:
        if len(record["cells"]) >= 3:
            for r, c in record["endpoints"]:
                out[r][c] = 8
    return out


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "recolor_all_straight_red": _rival_recolor_all_straight_red,
    "one_endpoint_only": _rival_one_endpoint,
    "color_blind_straights": _rival_color_blind_straights,
    "degree_endpoints_all_red": _rival_degree_endpoints_all_red,
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "skip_length_two_segments": _rival_skip_length_two_segments,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Only shortcuts that actually fit every labeled canonical pair belong here.
CANONICAL_SHORTCUTS = {
    "skip_length_two_segments": _rival_skip_length_two_segments,
}


def _witness_both_orientations(grid):
    info, errors = _analyze(grid)
    orientations = {record["orientation"] for record in info.get("straights", ())}
    return not errors and orientations == {"horizontal", "vertical"}


def _witness_bent_red_control(grid):
    info, errors = _analyze(grid)
    return not errors and bool(info["bents"])


def _witness_straight_distractor(grid):
    info, errors = _analyze(grid)
    return not errors and info["distractor_shape"] == "line"


def _witness_red_interior(grid):
    info, errors = _analyze(grid)
    return not errors and any(len(record["cells"]) >= 3 for record in info["straights"])


def _witness_two_endpoints(grid):
    info, errors = _analyze(grid)
    return not errors and bool(info["straights"])


def _witness_length_two_boundary(grid):
    info, errors = _analyze(grid)
    return not errors and any(len(record["cells"]) == 2 for record in info["straights"])


SEMANTIC_WITNESSES = {
    "both_straight_orientations": _witness_both_orientations,
    "bent_red_negative_control": _witness_bent_red_control,
    "straight_nonred_color_control": _witness_straight_distractor,
    "red_interior_preserved": _witness_red_interior,
    "both_endpoints_required": _witness_two_endpoints,
    "length_two_boundary": _witness_length_two_boundary,
}
WITNESS_RIVALS = {
    "both_straight_orientations": ["horizontal_only", "vertical_only"],
    "bent_red_negative_control": ["degree_endpoints_all_red"],
    "straight_nonred_color_control": ["color_blind_straights"],
    "red_interior_preserved": ["recolor_all_straight_red"],
    "both_endpoints_required": ["identity", "one_endpoint_only"],
    "length_two_boundary": ["skip_length_two_segments"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    counts: set[int] = set()
    distractor_colors: set[int] = set()
    orientations: set[str] = set()
    saw_bent = False
    saw_straight_distractor = False
    saw_interior = False
    saw_length_two = False

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyze(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output does not match endpoint-only recoloring")
        counts.add(info["n_straight"])
        distractor_colors.add(info["distractor_color"])
        orientations.update(record["orientation"] for record in info["straights"])
        saw_bent |= bool(info["bents"])
        saw_straight_distractor |= info["distractor_shape"] == "line"
        saw_interior |= any(len(record["cells"]) >= 3 for record in info["straights"])
        saw_length_two |= any(len(record["cells"]) == 2 for record in info["straights"])

    if len(counts) < 2:
        reasons.append(f"demonstrations need multiple straight-component counts, got {sorted(counts)}")
    if len(distractor_colors) < 2:
        reasons.append("demonstrations need at least two distractor colors")
    if orientations != {"horizontal", "vertical"}:
        reasons.append(f"demonstrations need both straight orientations, got {sorted(orientations)}")
    if not saw_bent:
        reasons.append("demonstrations lack a bent red component that must remain unchanged")
    if not saw_straight_distractor:
        reasons.append("demonstrations lack a straight non-red color control")
    if not saw_interior:
        reasons.append("demonstrations lack a red segment interior that must remain red")
    if not saw_length_two:
        reasons.append("demonstrations lack a length-two red segment boundary case")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        _, query_errors = _analyze(query["input"])
        if query_errors:
            reasons.append(f"query malformed: {query_errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match endpoint-only recoloring")
    return reasons

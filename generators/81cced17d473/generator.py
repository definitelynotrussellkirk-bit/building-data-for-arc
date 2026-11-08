"""Generator for selector-guided motif broadcast (task ``81cced17d473``).

The top-left cell selects one color.  Around the unique gray (5) source marker,
only cells of that selected color form the motif; differently colored nearby
cells are decoys.  Copy the selected motif offsets to every magenta (6) anchor.

The four-slot lesson schedule is deliberately adversarial.  It includes
canonical one/two-decoy scenes, a decoy color that is more frequent than the
selected color, and a four-cell motif with a distance-two offset.  Therefore a
four-demo lesson refutes "copy every local cell", "use the modal local color",
"copy only two cells", and "copy only adjacent cells" shortcuts.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Offset = tuple[int, int]

GENERATOR_ID = "81cced17d473"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
# Re-pinned to the comment-preserving selected source by the task-local
# authority-sync patch returned with this repair.
RULE_HASH = "8f04dcabcbe7"

SUMMARY = (
    "Read the selector color from cell (0,0). Around the unique gray (5) "
    "source, keep only cells of that selector color and express their "
    "positions as offsets from the source. Stamp those selected offsets in "
    "the selector color at every magenta (6) anchor; nearby cells of other "
    "colors are decoys and are not copied."
)
INVARIANTS = [
    "background is 0; cell (0,0) is a selector color other than 0, 5, or 6",
    "exactly one gray (5) source has 2..4 selected-color motif cells within radius two",
    "1..3 differently colored decoy cells lie in the same radius-two source neighborhood",
    "exactly 2..3 magenta (6) anchors have clear, in-bounds projected neighborhoods",
    "normal lessons change the grid and preserve selector, source, anchors, and decoys",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SCHEDULE_PROFILES = (
    "single_decoy",
    "split_decoys",
    "modal_decoy",
    "expanded_far",
)
HELPFUL_TEXTURES = SCHEDULE_PROFILES
_TARGET_COLORS = (1, 2, 3, 4, 7, 8, 9)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

# Only controls that are exactly recoverable from the returned grid are public.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 9..12",
        "valid": "9..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 9..12",
        "valid": "9..14",
    },
    "target_color": {
        "type": "color",
        "default": "keyed draw from ARC colors other than 0, 5, and 6",
        "valid": "1..9 (≠5, ≠6)",
    },
    "n_anchors": {
        "type": "int",
        "default": "2 easy; 2..3 medium/default; 3 hard",
        "valid": "2..3",
    },
    "texture": {
        "type": "enum",
        "default": "four-slot lesson schedule",
        "valid": "|".join(SCHEDULE_PROFILES),
    },
}

# Every Cartesian combination of the declared exact axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_BAND_DEFAULTS = {
    None: ((9, 12), (9, 12), (2, 3)),
    "easy": ((9, 10), (9, 10), (2, 2)),
    "medium": ((9, 11), (9, 11), (2, 3)),
    "hard": ((10, 11), (10, 11), (3, 3)),
}

_PROFILE_SPECS = {
    "single_decoy": {
        "motif_count": 2,
        "decoy_count": 1,
        "decoy_colors": 1,
        "require_far": False,
    },
    "split_decoys": {
        "motif_count": 2,
        "decoy_count": 2,
        "decoy_colors": 2,
        "require_far": False,
    },
    "modal_decoy": {
        "motif_count": 2,
        "decoy_count": 3,
        "decoy_colors": 1,
        "require_far": False,
    },
    "expanded_far": {
        "motif_count": 4,
        "decoy_count": 2,
        "decoy_colors": 2,
        "require_far": True,
    },
}

_OFFSETS: tuple[Offset, ...] = tuple(
    (dr, dc)
    for dr in range(-2, 3)
    for dc in range(-2, 3)
    if (dr, dc) != (0, 0)
)
_FAR_OFFSETS: tuple[Offset, ...] = tuple(
    offset for offset in _OFFSETS if max(abs(offset[0]), abs(offset[1])) == 2
)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the exact four-slot semantic schedule profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _normalize_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    cleaned = {key: value for key, value in overrides.items() if value is not None}
    unknown = sorted(set(cleaned) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    return cleaned


def _draw_axis_int(
    ctx: Any,
    overrides: dict[str, Any],
    label: str,
    valid: tuple[int, int],
    default: tuple[int, int],
) -> int:
    bounds = valid if label in overrides else default
    return int(ctx.draw_int(label, *bounds))


def _draw_texture(
    ctx: Any,
    overrides: dict[str, Any],
    scheduled: str,
) -> str:
    options: Sequence[str] = SCHEDULE_PROFILES if "texture" in overrides else (scheduled,)
    return str(ctx.draw_choice("texture", options))


def _pattern_for_profile(
    profile: str,
    target: int,
    rng: Any,
) -> tuple[tuple[Offset, ...], tuple[tuple[Offset, int], ...]]:
    """Draw disjoint motif and decoy offsets for one semantic profile."""
    spec = _PROFILE_SPECS[profile]
    available = list(_OFFSETS)
    motif: list[Offset] = []
    if spec["require_far"]:
        far = rng.choice(_FAR_OFFSETS)
        motif.append(far)
        available.remove(far)
    motif.extend(rng.sample(available, int(spec["motif_count"]) - len(motif)))
    motif_set = set(motif)
    remaining = [offset for offset in _OFFSETS if offset not in motif_set]
    decoy_offsets = rng.sample(remaining, int(spec["decoy_count"]))

    legal_decoys = [color for color in range(1, 10) if color not in {target, 5, 6}]
    decoy_palette = rng.sample(legal_decoys, int(spec["decoy_colors"]))
    if len(decoy_palette) == 1:
        decoy_colors = [decoy_palette[0]] * len(decoy_offsets)
    else:
        decoy_colors = [decoy_palette[i % len(decoy_palette)] for i in range(len(decoy_offsets))]
        rng.shuffle(decoy_colors)
    return tuple(motif), tuple(zip(decoy_offsets, decoy_colors))


def _candidate_anchors(
    height: int,
    width: int,
    pattern_offsets: Sequence[Offset],
    reserved: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    candidates: list[tuple[int, int]] = []
    for row in range(height):
        for col in range(width):
            footprint = {(row, col)} | {
                (row + dr, col + dc) for dr, dc in pattern_offsets
            }
            if any(not (0 <= rr < height and 0 <= cc < width) for rr, cc in footprint):
                continue
            if footprint & reserved:
                continue
            candidates.append((row, col))
    return candidates


def _draw_scene(
    height: int,
    width: int,
    target: int,
    n_anchors: int,
    profile: str,
    rng: Any,
) -> Grid:
    for _attempt in range(160):
        motif, decoys = _pattern_for_profile(profile, target, rng)
        pattern_offsets = tuple(motif) + tuple(offset for offset, _ in decoys)
        source_candidates: list[tuple[int, int]] = []
        for row in range(2, height - 2):
            for col in range(2, width - 2):
                cells = {(row + dr, col + dc) for dr, dc in pattern_offsets}
                if (0, 0) not in cells:
                    source_candidates.append((row, col))
        rng.shuffle(source_candidates)

        for source_row, source_col in source_candidates:
            grid = full_grid(height, width, 0)
            grid[0][0] = target
            grid[source_row][source_col] = 5
            reserved = {(0, 0), (source_row, source_col)}
            collision = False
            for dr, dc in motif:
                row, col = source_row + dr, source_col + dc
                if (row, col) in reserved:
                    collision = True
                    break
                grid[row][col] = target
                reserved.add((row, col))
            if collision:
                continue
            for (dr, dc), color in decoys:
                row, col = source_row + dr, source_col + dc
                if (row, col) in reserved:
                    collision = True
                    break
                grid[row][col] = color
                reserved.add((row, col))
            if collision:
                continue

            anchors: list[tuple[int, int]] = []
            for _ in range(n_anchors):
                candidates = _candidate_anchors(
                    height, width, pattern_offsets, reserved
                )
                if not candidates:
                    break
                anchor = rng.choice(candidates)
                anchors.append(anchor)
                footprint = {anchor} | {
                    (anchor[0] + dr, anchor[1] + dc)
                    for dr, dc in pattern_offsets
                }
                reserved.update(footprint)
                grid[anchor[0]][anchor[1]] = 6
            if len(anchors) == n_anchors:
                return grid

    raise RuntimeError(
        f"could not place {profile} scene on {height}x{width} with {n_anchors} anchors"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, selector-identifying input grid."""
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    cleaned = _normalize_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=cleaned,
    )
    h_default, w_default, anchors_default = _BAND_DEFAULTS[difficulty]
    height = _draw_axis_int(ctx, cleaned, "grid_h", (9, 14), h_default)
    width = _draw_axis_int(ctx, cleaned, "grid_w", (9, 14), w_default)
    target = int(ctx.draw_color("target_color", exclude={0, 5, 6}))
    n_anchors = _draw_axis_int(
        ctx, cleaned, "n_anchors", (2, 3), anchors_default
    )
    texture = _draw_texture(
        ctx,
        cleaned,
        schedule_profile(seed, sample_index, difficulty),
    )
    return _draw_scene(
        height,
        width,
        target,
        n_anchors,
        texture,
        ctx.draw_rng("layout"),
    )


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    facts: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return facts, ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, list) for row in grid):
        return facts, ["every row must be a list"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return facts, ["grid must be rectangular with positive width"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return facts, ["all cells must be integer ARC colors 0..9"]

    height = len(grid)
    target = grid[0][0]
    sources = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    anchors = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 6
    ]
    motif_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == target and (row, col) != (0, 0)
    ]
    decoy_cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in {0, target, 5, 6}
    ]

    source = sources[0] if len(sources) == 1 else None
    motif_offsets: tuple[Offset, ...] = ()
    decoy_offsets: tuple[tuple[int, int, int], ...] = ()
    if source is not None:
        source_row, source_col = source
        motif_offsets = tuple(
            (row - source_row, col - source_col) for row, col in motif_cells
        )
        decoy_offsets = tuple(
            (row - source_row, col - source_col, value)
            for row, col, value in decoy_cells
        )

    facts.update(
        grid_h=height,
        grid_w=width,
        target=target,
        sources=tuple(sources),
        source=source,
        anchors=tuple(anchors),
        motif_cells=tuple(motif_cells),
        motif_offsets=motif_offsets,
        decoy_cells=tuple(decoy_cells),
        decoy_offsets=decoy_offsets,
        decoy_colors=tuple(sorted({value for _, _, value in decoy_cells})),
        palette=tuple(sorted({value for row in grid for value in row})),
    )
    facts["texture"] = _profile_for(facts)
    return facts, errors


def _profile_for(facts: dict[str, Any]) -> str | None:
    motif_count = len(facts.get("motif_offsets", ()))
    decoys = facts.get("decoy_offsets", ())
    decoy_count = len(decoys)
    decoy_color_count = len({value for _, _, value in decoys})
    has_far = any(
        max(abs(dr), abs(dc)) == 2
        for dr, dc in facts.get("motif_offsets", ())
    )
    if motif_count == 2 and decoy_count == 1 and decoy_color_count == 1:
        return "single_decoy"
    if motif_count == 2 and decoy_count == 2 and decoy_color_count == 2:
        return "split_decoys"
    if motif_count == 2 and decoy_count == 3 and decoy_color_count == 1:
        return "modal_decoy"
    if motif_count == 4 and decoy_count == 2 and decoy_color_count == 2 and has_far:
        return "expanded_far"
    return None


def observe_overrides(grid: Any) -> dict[str, Any]:
    """Recover every declared exact axis from one generated scene."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    texture = facts.get("texture")
    if texture is None:
        raise ValueError("cannot observe texture: grid is not a generated profile")
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "target_color": facts["target"],
        "n_anchors": len(facts["anchors"]),
        "texture": texture,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task grammar and reject rule-hiding or colliding scenes."""
    del difficulty
    facts, errors = _analyze(grid)
    if errors:
        return errors

    height, width = facts["grid_h"], facts["grid_w"]
    target = facts["target"]
    if not 9 <= height <= 14 or not 9 <= width <= 14:
        errors.append(f"expected dimensions in 9..14, got {height}x{width}")
    if target not in _TARGET_COLORS:
        errors.append(
            f"cell (0,0) must be a selector color other than 0, 5, or 6; got {target}"
        )
    if len(facts["sources"]) != 1:
        errors.append(f"expected exactly one gray (5) source, got {len(facts['sources'])}")
        return errors
    if not 2 <= len(facts["anchors"]) <= 3:
        errors.append(f"expected 2..3 magenta (6) anchors, got {len(facts['anchors'])}")
    if not 2 <= len(facts["motif_offsets"]) <= 4:
        errors.append(
            f"expected 2..4 selected-color motif cells, got {len(facts['motif_offsets'])}"
        )
    if not 1 <= len(facts["decoy_offsets"]) <= 3:
        errors.append(f"expected 1..3 local decoy cells, got {len(facts['decoy_offsets'])}")
    if not 1 <= len(facts["decoy_colors"]) <= 2:
        errors.append(f"expected 1..2 decoy colors, got {len(facts['decoy_colors'])}")
    if not 5 <= len(facts["palette"]) <= 6:
        errors.append(f"expected a 5..6-color palette including background, got {facts['palette']}")

    source_row, source_col = facts["source"]
    pattern_offsets: list[Offset] = list(facts["motif_offsets"]) + [
        (dr, dc) for dr, dc, _ in facts["decoy_offsets"]
    ]
    if len(set(pattern_offsets)) != len(pattern_offsets):
        errors.append("motif and decoy offsets must be distinct")
    for dr, dc in pattern_offsets:
        if (dr, dc) == (0, 0) or max(abs(dr), abs(dc)) > 2:
            errors.append(
                f"source-neighborhood offset {(dr, dc)} must be nonzero and within radius two"
            )

    # Only selected-color offsets are output-bearing.  Canonical examples may
    # place a decoy offset beyond an anchor edge because the true rule ignores
    # decoys there; rejecting that would make self_check narrower than the
    # authority.  Generated lessons separately keep every decoy projection
    # in-bounds so copy-all rivals receive a clean killing witness.
    projected: set[tuple[int, int]] = set()
    for anchor_row, anchor_col in facts["anchors"]:
        for dr, dc in facts["motif_offsets"]:
            row, col = anchor_row + dr, anchor_col + dc
            if not (0 <= row < height and 0 <= col < width):
                errors.append(
                    f"anchor {(anchor_row, anchor_col)} projects selected offset "
                    f"{(dr, dc)} out of bounds"
                )
                continue
            if grid[row][col] != 0:
                errors.append(
                    f"selected landing {(row, col)} is occupied by color {grid[row][col]}"
                )
            if (row, col) in projected:
                errors.append(f"selected anchor projections overlap at {(row, col)}")
            projected.add((row, col))

    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict) and requested:
            try:
                observed = observe_overrides(grid)
            except ValueError as exc:
                errors.append(str(exc))
            else:
                for axis, expected in requested.items():
                    if axis in AXES and expected is not None and observed.get(axis) != expected:
                        errors.append(
                            f"override {axis}={expected!r} realized as {observed.get(axis)!r}"
                        )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Linked task manifold shared by all canonical inputs and normal draws."""
    return list(self_check(grid))


def _copy_grid(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in grid]


def _stamp_offsets(grid: Any, offsets: Sequence[Offset], color: int) -> Grid:
    facts, errors = _analyze(grid)
    if errors or facts.get("source") is None:
        raise ValueError("invalid selector-broadcast grid")
    output = _copy_grid(grid)
    for anchor_row, anchor_col in facts["anchors"]:
        for dr, dc in offsets:
            row, col = anchor_row + dr, anchor_col + dc
            if 0 <= row < facts["grid_h"] and 0 <= col < facts["grid_w"]:
                output[row][col] = color
    return output


def rule_mirror(grid: Any) -> Grid:
    """Python parity mirror; canonical Racket remains the output authority."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    return _stamp_offsets(grid, facts["motif_offsets"], facts["target"])


def _copy_all_local_colors_rival(grid: Any) -> Grid:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = _copy_grid(grid)
    local = [
        (dr, dc, facts["target"]) for dr, dc in facts["motif_offsets"]
    ] + list(facts["decoy_offsets"])
    for anchor_row, anchor_col in facts["anchors"]:
        for dr, dc, color in local:
            row, col = anchor_row + dr, anchor_col + dc
            if 0 <= row < facts["grid_h"] and 0 <= col < facts["grid_w"]:
                output[row][col] = color
    return output


def _modal_local_color_rival(grid: Any) -> Grid:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    source_row, source_col = facts["source"]
    local_cells = [
        (row, col, facts["target"]) for row, col in facts["motif_cells"]
    ] + list(facts["decoy_cells"])
    counts = Counter(color for _, _, color in local_cells)
    first_position = {
        color: min((row, col) for row, col, value in local_cells if value == color)
        for color in counts
    }
    chosen = min(
        counts,
        key=lambda color: (-counts[color], first_position[color], color),
    )
    offsets = [
        (row - source_row, col - source_col)
        for row, col, color in local_cells
        if color == chosen
    ]
    return _stamp_offsets(grid, offsets, chosen)


def _first_two_selected_rival(grid: Any) -> Grid:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    offsets = sorted(facts["motif_offsets"])[:2]
    return _stamp_offsets(grid, offsets, facts["target"])


def _adjacent_selected_rival(grid: Any) -> Grid:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    offsets = [
        (dr, dc)
        for dr, dc in facts["motif_offsets"]
        if max(abs(dr), abs(dc)) <= 1
    ]
    return _stamp_offsets(grid, offsets, facts["target"])


def _profile_witness(name: str) -> Callable[[Any], bool]:
    def predicate(grid: Any) -> bool:
        facts, errors = _analyze(grid)
        return not errors and facts.get("texture") == name

    return predicate


SEMANTIC_RIVALS = {
    "copy_all_local_colors": _copy_all_local_colors_rival,
    "modal_local_color": _modal_local_color_rival,
    "first_two_selected": _first_two_selected_rival,
    "adjacent_selected": _adjacent_selected_rival,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
# Both shortcuts fit all five canonical pairs but disagree on scheduled
# generated witnesses, so canonical examples alone cannot falsify them.
CANONICAL_SHORTCUTS = {
    "modal_local_color": _modal_local_color_rival,
    "first_two_selected": _first_two_selected_rival,
}
SEMANTIC_WITNESSES = {
    profile: _profile_witness(profile) for profile in SCHEDULE_PROFILES
}
WITNESS_RIVALS = {
    "single_decoy": ["copy_all_local_colors"],
    "split_decoys": ["copy_all_local_colors"],
    "modal_decoy": ["copy_all_local_colors", "modal_local_color"],
    "expanded_far": [
        "copy_all_local_colors",
        "first_two_selected",
        "adjacent_selected",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo window to cover all profiles and kill rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    profiles: set[str] = set()
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        valid_demos.append(pair)
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the selector-broadcast rule")
        facts, errors = _analyze(pair["input"])
        if not errors and facts.get("texture"):
            profiles.add(str(facts["texture"]))
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the selector-broadcast rule")

    missing = set(SCHEDULE_PROFILES) - profiles
    if missing:
        reasons.append(f"demonstrations miss scheduled profile(s): {sorted(missing)}")

    for name, competitor in LESSON_COMPETITORS.items():
        if not valid_demos:
            break
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in valid_demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons

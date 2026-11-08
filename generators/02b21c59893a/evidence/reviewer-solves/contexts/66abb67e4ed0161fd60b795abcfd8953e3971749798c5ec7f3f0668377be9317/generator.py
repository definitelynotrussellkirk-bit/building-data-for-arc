"""Generator for ARC task 02b21c59893a — transfer payload between anchors.

The selected rule uses the single blue (1) cell as the source anchor and the
last red (2) cell in row-major order as the destination anchor.  Every other
nonzero cell is payload.  On a fresh zero canvas, retain the destination red
cell and translate each payload cell by ``destination - source``; translated
cells outside the canvas are clipped and payload colours are preserved.

A five-role schedule makes the source, last-red, and clipping semantics
redundantly observable.  Every five consecutive pairs contain two multi-red
witnesses and two partial-clipping witnesses; every role also refutes origin
and payload-bounding-box source shortcuts.  Consequently every four-demo
rotation of a five-pair lesson retains a counterexample to every declared rival.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "02b21c59893a"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "ba8a3944ecbc"

CANONICAL_ANCHOR = "canonical_anchor"
OFFSET_ANCHOR = "offset_anchor"
LAST_RED = "last_red"
LAST_RED_CLIP = "last_red_clip"
CLIP_MULTICOLOR = "clip_multicolor"
SCENE_PROFILES = (
    CANONICAL_ANCHOR,
    OFFSET_ANCHOR,
    LAST_RED,
    LAST_RED_CLIP,
    CLIP_MULTICOLOR,
)
SCHEDULE_PROFILES = SCENE_PROFILES

SUMMARY = (
    "A zero-background grid has one blue source anchor, one or two red anchors, "
    "and a multicolour payload. Use the last red in row-major order as the "
    "destination, copy each payload offset from blue to that red on a fresh "
    "canvas, preserve payload colours, and clip translated cells at the edge."
)

INVARIANTS = [
    "exactly one blue source anchor and one or two red anchors",
    "the last red in row-major order is the destination",
    "payload contains 2..8 cells and at least two colours from 3..9",
    "at least one translated payload cell remains in bounds",
    "partial-clipping roles lose some but not all translated payload cells",
]

COUNTER_HYPOTHESES = [
    "use the global origin as source",
    "use the payload bounding-box top-left as source",
    "use the first red rather than the last red",
    "discard the whole payload whenever any translated cell clips",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "five-role semantic schedule",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "Exact observable teaching role: two one-red canonical anchors, "
            "a two-red last-anchor scene, a two-red partial-clip scene, or a "
            "difficulty-scaled one-red partial-clip scene."
        ),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_PAYLOAD_COLORS = (3, 4, 5, 6, 7, 8, 9)
_BASE_OFFSETS = {
    3: ((-1, 0), (0, 1), (1, 1)),
    4: ((-1, 0), (0, 1), (1, 1), (1, 2)),
    5: ((-1, 0), (0, 1), (1, 1), (1, 2), (-1, 2)),
    6: ((-1, 0), (0, 1), (1, 1), (1, 2), (-1, 2), (2, 0)),
}
_CANONICAL_PROFILE_TUPLES = {
    (8, 9, 6),
    (9, 10, 7),
    (7, 11, 5),
    (9, 11, 7),
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the semantic role for one position in the five-pair cycle."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override key(s): " + ", ".join(unknown))
    profile = overrides.get("scene_profile")
    if profile is not None and (type(profile) is not str or profile not in SCENE_PROFILES):
        raise ValueError(f"scene_profile must be one of {SCENE_PROFILES}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, strict, semantically scheduled input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_profile = schedule_profile(seed, sample_index, difficulty)
    options = SCENE_PROFILES if "scene_profile" in overrides else (default_profile,)
    profile = ctx.draw_choice("scene_profile", options)
    rng = ctx.draw_rng(f"profile:{profile}")
    height, width, payload_cells, payload_colours, red_count, clipping = _profile_spec(
        profile, difficulty, rng
    )
    grid = _draw_scene(
        rng,
        height=height,
        width=width,
        payload_cells=payload_cells,
        payload_colours=payload_colours,
        red_count=red_count,
        clipping=clipping,
        required_rivals=_profile_rivals(profile),
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {"scene_profile": profile}
    if observed != requested:
        raise AssertionError(f"internal axis drift: requested={requested}, observed={observed}")
    return grid


def _profile_spec(profile: str, difficulty: Any, rng) -> tuple[int, int, int, int, int, bool]:
    if profile == CANONICAL_ANCHOR:
        return 8, 9, 3, 3, 1, False
    if profile == OFFSET_ANCHOR:
        return 9, 10, 4, 4, 1, False
    if profile == LAST_RED:
        return 7, 11, 4, 2, 2, False
    if profile == LAST_RED_CLIP:
        return 9, 11, 4, 4, 2, True
    if profile == CLIP_MULTICOLOR:
        shapes = {
            "easy": ((8, 12), (9, 13)),
            "medium": ((10, 12), (10, 13), (11, 14)),
            "hard": ((11, 15), (12, 16), (13, 17)),
            None: ((9, 12), (10, 13), (11, 14)),
        }[difficulty]
        height, width = shapes[rng.randrange(len(shapes))]
        payload_cells = rng.choice((4, 5, 6))
        payload_colours = rng.randint(2, min(4, payload_cells))
        return height, width, payload_cells, payload_colours, 1, True
    raise AssertionError(f"unknown scene profile: {profile!r}")


def _profile_rivals(profile: str) -> tuple[str, ...]:
    names = ["always_origin", "payload_bbox_origin"]
    if profile in (LAST_RED, LAST_RED_CLIP):
        names.append("first_red")
    if profile in (LAST_RED_CLIP, CLIP_MULTICOLOR):
        names.append("all_or_nothing_clip")
    return tuple(names)


def _d4_offsets(count: int) -> list[tuple[tuple[int, int], ...]]:
    base = _BASE_OFFSETS[count]
    result: set[tuple[tuple[int, int], ...]] = set()
    for reflected in (False, True):
        for turns in range(4):
            transformed = []
            for row, col in base:
                if reflected:
                    col = -col
                for _ in range(turns):
                    row, col = col, -row
                transformed.append((row, col))
            result.add(tuple(sorted(transformed)))
    return sorted(result)


def _draw_scene(
    rng,
    *,
    height: int,
    width: int,
    payload_cells: int,
    payload_colours: int,
    red_count: int,
    clipping: bool,
    required_rivals: tuple[str, ...],
) -> list[list[int]]:
    transforms = _d4_offsets(payload_cells)
    rng.shuffle(transforms)
    for offsets in transforms:
        source_candidates = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if (row, col) != (0, 0)
            and all(0 <= row + dr < height and 0 <= col + dc < width for dr, dc in offsets)
        ]
        rng.shuffle(source_candidates)
        for source in source_candidates:
            payload_positions = {(source[0] + dr, source[1] + dc) for dr, dc in offsets}
            occupied = payload_positions | {source}
            destination_candidates = []
            for destination in (
                (row, col) for row in range(height) for col in range(width)
            ):
                if destination in occupied:
                    continue
                moved = [
                    (destination[0] + dr, destination[1] + dc) for dr, dc in offsets
                ]
                inside = sum(0 <= row < height and 0 <= col < width for row, col in moved)
                if clipping:
                    if not (0 < inside < len(moved)):
                        continue
                elif inside != len(moved):
                    continue
                if red_count == 2 and not any(
                    (row, col) < destination and (row, col) not in occupied
                    for row in range(height)
                    for col in range(width)
                ):
                    continue
                destination_candidates.append(destination)
            rng.shuffle(destination_candidates)
            for destination in destination_candidates:
                early_red = None
                if red_count == 2:
                    early_candidates = [
                        (row, col)
                        for row in range(height)
                        for col in range(width)
                        if (row, col) < destination
                        and (row, col) not in occupied
                        and (row, col) != destination
                    ]
                    rng.shuffle(early_candidates)
                    if not early_candidates:
                        continue
                    early_red = early_candidates[0]

                colours = rng.sample(_PAYLOAD_COLORS, payload_colours)
                assignments = list(colours)
                assignments.extend(
                    colours[rng.randrange(len(colours))]
                    for _ in range(payload_cells - len(colours))
                )
                rng.shuffle(assignments)
                grid = full_grid(height, width, 0)
                for (dr, dc), colour in zip(offsets, assignments):
                    grid[source[0] + dr][source[1] + dc] = colour
                grid[source[0]][source[1]] = 1
                if early_red is not None:
                    grid[early_red[0]][early_red[1]] = 2
                grid[destination[0]][destination[1]] = 2

                expected = _solve(grid)
                if all(_rival_by_name(name)(deepcopy(grid)) != expected for name in required_rivals):
                    return grid
    raise ValueError(
        f"could not construct profile shape={(height, width)} payload={payload_cells} "
        f"reds={red_count} clipping={clipping}"
    )


def _rectangular_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, list) or not grid:
        return 0, 0, ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return len(grid), 0, ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return len(grid), width, ["grid cells must be integer colours 0..9"]
    return len(grid), width, []


def _features(grid: Any) -> tuple[int, int, tuple[int, int], list[tuple[int, int]], list[tuple[int, int, int]]]:
    height, width, errors = _rectangular_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    blues: list[tuple[int, int]] = []
    reds: list[tuple[int, int]] = []
    payload: list[tuple[int, int, int]] = []
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 1:
                blues.append((row, col))
            elif value == 2:
                reds.append((row, col))
            elif value != 0:
                payload.append((row, col, value))
    if len(blues) != 1:
        raise ValueError(f"expected exactly one blue anchor, found {len(blues)}")
    if not reds:
        raise ValueError("expected at least one red anchor")
    if not payload:
        raise ValueError("expected nonempty payload")
    return height, width, blues[0], reds, payload


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed inputs and rule-hiding anchor/payload degeneracies."""
    del meta
    errors: list[str] = []
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append("difficulty must be None, 'easy', 'medium', or 'hard'")
    height, width, shape_errors = _rectangular_grid(grid)
    if shape_errors:
        return errors + shape_errors
    if not (5 <= height <= 30 and 5 <= width <= 30):
        errors.append(f"grid dimensions {(height, width)} must each be in 5..30")

    blues: list[tuple[int, int]] = []
    reds: list[tuple[int, int]] = []
    payload: list[tuple[int, int, int]] = []
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 1:
                blues.append((row, col))
            elif value == 2:
                reds.append((row, col))
            elif value != 0:
                payload.append((row, col, value))
    if len(blues) != 1:
        errors.append(f"expected exactly one blue(1) source anchor, found {len(blues)}")
    if not (1 <= len(reds) <= 2):
        errors.append(f"expected one or two red(2) anchors, found {len(reds)}")
    if not (2 <= len(payload) <= 8):
        errors.append(f"expected 2..8 payload cells, found {len(payload)}")
    payload_palette = {value for _, _, value in payload}
    if len(payload_palette) < 2:
        errors.append(f"payload must use at least two colours, found {sorted(payload_palette)}")
    if errors:
        return errors

    source = blues[0]
    destination = reds[-1]
    inside = sum(
        0 <= destination[0] + row - source[0] < height
        and 0 <= destination[1] + col - source[1] < width
        for row, col, _ in payload
    )
    if inside == 0:
        errors.append("translation clips every payload cell")
    return errors


def strict_canonical_like(grid):
    """The broad reference-lawful task domain; [] means strict acceptance."""
    return self_check(grid)


def _clipped_count(grid: Any) -> int:
    height, width, source, reds, payload = _features(grid)
    destination = reds[-1]
    return sum(
        not (
            0 <= destination[0] + row - source[0] < height
            and 0 <= destination[1] + col - source[1] < width
        )
        for row, col, _ in payload
    )


def _profile_from_grid(grid: Any) -> str:
    height, width, _, reds, _ = _features(grid)
    palette = len({value for row in grid for value in row})
    clipped = _clipped_count(grid)
    signature = (height, width, palette, len(reds), clipped > 0)
    if signature == (8, 9, 6, 1, False):
        return CANONICAL_ANCHOR
    if signature == (9, 10, 7, 1, False):
        return OFFSET_ANCHOR
    if signature == (7, 11, 5, 2, False):
        return LAST_RED
    if signature == (9, 11, 7, 2, True):
        return LAST_RED_CLIP
    if len(reds) == 1 and clipped > 0 and (height, width, palette) not in _CANONICAL_PROFILE_TUPLES:
        return CLIP_MULTICOLOR
    raise ValueError(
        "grid is outside declared profiles: "
        f"shape={(height, width)} palette={palette} reds={len(reds)} clipped={clipped}"
    )


def observe_overrides(grid):
    """Recover the exact public axis from returned pixels alone."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    return {"scene_profile": _profile_from_grid(grid)}


def _translated_output(
    grid: Any,
    *,
    source: tuple[int, int],
    destination: tuple[int, int],
    all_or_nothing: bool = False,
) -> list[list[int]]:
    height, width, _, _, payload = _features(grid)
    moved = [
        (destination[0] + row - source[0], destination[1] + col - source[1], value)
        for row, col, value in payload
    ]
    out = full_grid(height, width, 0)
    out[destination[0]][destination[1]] = 2
    if all_or_nothing and any(not (0 <= row < height and 0 <= col < width) for row, col, _ in moved):
        return out
    for row, col, value in moved:
        if 0 <= row < height and 0 <= col < width:
            out[row][col] = value
    return out


def _solve(grid: Any) -> list[list[int]]:
    _, _, source, reds, _ = _features(grid)
    return _translated_output(grid, source=source, destination=reds[-1])


def _always_origin_rival(grid: Any) -> list[list[int]]:
    _, _, _, reds, _ = _features(grid)
    return _translated_output(grid, source=(0, 0), destination=reds[-1])


def _payload_bbox_rival(grid: Any) -> list[list[int]]:
    _, _, _, reds, payload = _features(grid)
    source = (min(row for row, _, _ in payload), min(col for _, col, _ in payload))
    return _translated_output(grid, source=source, destination=reds[-1])


def _first_red_rival(grid: Any) -> list[list[int]]:
    _, _, source, reds, _ = _features(grid)
    return _translated_output(grid, source=source, destination=reds[0])


def _all_or_nothing_clip_rival(grid: Any) -> list[list[int]]:
    _, _, source, reds, _ = _features(grid)
    return _translated_output(
        grid, source=source, destination=reds[-1], all_or_nothing=True
    )


def _rival_by_name(name: str) -> Callable[[Any], list[list[int]]]:
    return {
        "always_origin": _always_origin_rival,
        "payload_bbox_origin": _payload_bbox_rival,
        "first_red": _first_red_rival,
        "all_or_nothing_clip": _all_or_nothing_clip_rival,
    }[name]


def _differs_from(rival: Callable[[Any], Any], grid: Any) -> bool:
    try:
        return rival(deepcopy(grid)) != _solve(deepcopy(grid))
    except Exception:
        return False


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "always_origin": _always_origin_rival,
    "payload_bbox_origin": _payload_bbox_rival,
    "first_red": _first_red_rival,
    "all_or_nothing_clip": _all_or_nothing_clip_rival,
}
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "blue_not_origin": lambda grid: _differs_from(_always_origin_rival, grid),
    "blue_not_payload_bbox": lambda grid: _differs_from(_payload_bbox_rival, grid),
    "last_red_not_first": lambda grid: _differs_from(_first_red_rival, grid),
    "partial_clipping": lambda grid: _differs_from(_all_or_nothing_clip_rival, grid),
}
WITNESS_RIVALS = {
    "blue_not_origin": ["always_origin"],
    "blue_not_payload_bbox": ["payload_bbox_origin"],
    "last_red_not_first": ["first_red"],
    "partial_clipping": ["all_or_nothing_clip"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], Any]] = {}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when demonstrations do not determine the selected rule."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        try:
            expected = _solve(pair["input"])
        except Exception as exc:
            reasons.append(f"pair {index} input is invalid: {type(exc).__name__}: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with anchor translation")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(deepcopy(pair["input"])) == pair["output"] for pair in demos
            )
            differs_query = rival(deepcopy(query["input"])) != query["output"]
        except Exception as exc:
            reasons.append(f"rival {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and differs_query:
            reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons

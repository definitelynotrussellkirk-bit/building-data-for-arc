"""Generator for H89 / ARC task 03e706065642.

Three horizontally aligned hollow color-1 frames each contain one monochrome
motif.  Crop each motif to its binary bounding box and classify it by reflection
symmetry:

* 0 — neither left/right nor up/down symmetry
* 1 — left/right symmetry only
* 2 — up/down symmetry only
* 3 — both symmetries

The answer is the 3x3 equality matrix of those *classes*: cells are 2 when the
row and column motifs have the same class, otherwise 0.

The default five-example curriculum deliberately includes vertical-only motifs,
which are absent from the canonical examples.  This makes the strongest
canonical-fitting shortcut (collapsing class 2 into class 0) falsifiable even if
any one example is held out as the query.
"""
from __future__ import annotations

from functools import lru_cache
from numbers import Real
from typing import Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "03e706065642"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "ae585f1eb109"

SUMMARY = (
    "Three horizontal hollow color-1 frames contain monochrome motifs. "
    "Classify each binary-cropped motif as asymmetric, left/right-only, "
    "up/down-only, or symmetric on both axes; output their 3x3 class-equality "
    "matrix using 2 for equal and 0 for unequal."
)

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 5
MIN_STRICT_FRAC = 1.0
# Bell number B3: all-same, all-distinct, and one pair in each of 3 positions.
EXPECTED_OUTPUT_CODOMAIN = 5

INVARIANTS = [
    "background is 0 and every frame border is color 1",
    "exactly three equal square frames are horizontally aligned and disjoint",
    "each frame contains one nonempty monochrome motif",
    "motif symmetry is computed after binary bounding-box normalization",
    "same-class teaching pairs use non-identical exact shapes",
]

FRAME_SIZES = (5, 6, 7, 8)
LAYOUTS = ("pair", "all_same", "all_distinct")
TEXTURES = ("same_color", "mixed_colors")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES = TEXTURES
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[object, ...], ...] = ()

AXES = {
    "frame_n": {
        "type": "int",
        "default": "difficulty-biased 5..8; recurrent canonical-size 6",
        "valid": "5..8",
        "doc": "Outer side length of each square frame.",
    },
    "layout": {
        "type": "enum",
        "default": "five-slot semantic curriculum",
        "valid": "pair|all_same|all_distinct",
        "doc": "Equality pattern of the three symmetry classes.",
    },
    "texture": {
        "type": "enum",
        "default": "same_color|mixed_colors curriculum",
        "valid": "same_color|mixed_colors",
        "doc": "Whether motif color is shared or distinct across panels.",
    },
}

# The first three slots are pinned because they are the smallest witnesses for
# each pair position and explicitly exercise class 2 (up/down-only).
_SCHEDULE_CLASSES = (
    (2, 2, 0),
    (1, 3, 1),
    (0, 2, 2),
    (0, 1, 2),
    None,  # all-same; the concrete class is seeded to widen coverage
)
_SCHEDULE_LAYOUTS = ("pair", "pair", "pair", "all_distinct", "all_same")
_SCHEDULE_TEXTURES = (
    "same_color",
    "mixed_colors",
    "same_color",
    "same_color",
    "mixed_colors",
)


def _is_rectangular_grid(grid: object) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and all(isinstance(row, list) and bool(row) for row in grid)
        and all(len(row) == len(grid[0]) for row in grid)
    )


def _sym_class(cells: Iterable[tuple[int, int]]) -> tuple[int, frozenset[tuple[int, int]]]:
    """Return (class, bbox-normalized shape) for a nonempty binary motif."""
    materialized = list(cells)
    if not materialized:
        raise ValueError("symmetry class requires a nonempty motif")
    mr = min(r for r, _ in materialized)
    mc = min(c for _, c in materialized)
    norm = frozenset((r - mr, c - mc) for r, c in materialized)
    hh = max(r for r, _ in norm) + 1
    ww = max(c for _, c in norm) + 1
    lr = frozenset((r, ww - 1 - c) for r, c in norm) == norm
    ud = frozenset((hh - 1 - r, c) for r, c in norm) == norm
    return (1 if lr else 0) + (2 if ud else 0), norm


def _shape_key(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return tuple(sorted(shape))


def _equal_matrix(values: Sequence[object]) -> list[list[int]]:
    return [[2 if left == right else 0 for right in values] for left in values]


@lru_cache(maxsize=1)
def _fallback_motifs() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    """Enumerate a deterministic 3x3 bank for rare constructive misses."""
    cells = [(r, c) for r in range(3) for c in range(3)]
    pools: dict[int, list[tuple[tuple[int, int], ...]]] = {0: [], 1: [], 2: [], 3: []}
    seen: dict[int, set[tuple[tuple[int, int], ...]]] = {0: set(), 1: set(), 2: set(), 3: set()}
    for mask in range(1, 1 << len(cells)):
        count = mask.bit_count()
        if count < 3 or count == 9:
            continue
        selected = [cell for bit, cell in enumerate(cells) if mask & (1 << bit)]
        cls, norm = _sym_class(selected)
        key = _shape_key(norm)
        if key not in seen[cls]:
            seen[cls].add(key)
            pools[cls].append(key)
    for cls in pools:
        pools[cls].sort(key=lambda shape: (len(shape), shape))
    return {cls: tuple(shapes) for cls, shapes in pools.items()}


def _expanded_seed(
    seed_cells: Iterable[tuple[int, int]],
    height: int,
    width: int,
    want_class: int,
) -> set[tuple[int, int]]:
    cells = set(seed_cells)
    if want_class in (1, 3):
        cells |= {(r, width - 1 - c) for r, c in tuple(cells)}
    if want_class in (2, 3):
        cells |= {(height - 1 - r, c) for r, c in tuple(cells)}
    if want_class == 3:
        cells |= {(height - 1 - r, width - 1 - c) for r, c in tuple(cells)}
    return cells


def _random_motif(
    rng,
    want_class: int,
    inner: int,
    forbidden: set[tuple[tuple[int, int], ...]],
) -> tuple[tuple[int, int], ...]:
    """Construct an unused motif of exactly ``want_class`` within the interior."""
    if want_class not in (0, 1, 2, 3):
        raise ValueError(f"invalid symmetry class {want_class!r}")
    if inner < 3:
        raise ValueError(f"frame interior {inner} is too small")

    prefer_large = inner >= 5
    for attempt in range(800):
        if prefer_large and attempt < 600:
            height = rng.randint(4, inner)
            width = rng.randint(4, inner)
        else:
            height = rng.randint(2, inner)
            width = rng.randint(2, inner)
        all_cells = [(r, c) for r in range(height) for c in range(width)]
        max_seed = min(8, max(3, len(all_cells) - 1))
        seed_count = rng.randint(2, max_seed)
        rng.shuffle(all_cells)
        cells = _expanded_seed(all_cells[:seed_count], height, width, want_class)
        if len(cells) < 3 or len(cells) >= height * width:
            continue
        cls, norm = _sym_class(cells)
        key = _shape_key(norm)
        if cls != want_class or key in forbidden:
            continue
        if prefer_large and max(max(r for r, _ in key), max(c for _, c in key)) < 3:
            continue
        return key

    candidates = [shape for shape in _fallback_motifs()[want_class] if shape not in forbidden]
    if not candidates:
        raise RuntimeError(f"could not construct a new motif for symmetry class {want_class}")
    return candidates[rng.randrange(len(candidates))]


def _find_frames(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    """Find square color-1 borders that contain at least one motif pixel."""
    if not _is_rectangular_grid(grid):
        return []
    h, w = len(grid), len(grid[0])
    frames: list[tuple[int, int, int]] = []
    for fn in FRAME_SIZES:
        if fn > h or fn > w:
            continue
        for ar in range(h - fn + 1):
            for ac in range(w - fn + 1):
                if not all(grid[ar][c] == 1 for c in range(ac, ac + fn)):
                    continue
                if not all(grid[ar + fn - 1][c] == 1 for c in range(ac, ac + fn)):
                    continue
                if not all(grid[r][ac] == 1 for r in range(ar, ar + fn)):
                    continue
                if not all(grid[r][ac + fn - 1] == 1 for r in range(ar, ar + fn)):
                    continue
                if any(
                    grid[r][c] not in (0, 1)
                    for r in range(ar + 1, ar + fn - 1)
                    for c in range(ac + 1, ac + fn - 1)
                ):
                    frames.append((ar, ac, fn))
    return sorted(frames)


def analyze_grid(grid: list[list[int]]) -> dict[str, object]:
    """Recover the exact semantic axes and motif features without mutation."""
    if not _is_rectangular_grid(grid):
        raise ValueError("grid must be a nonempty rectangular list of lists")
    frames = _find_frames(grid)
    if len(frames) != 3:
        raise ValueError(f"expected exactly 3 frames, found {len(frames)}")

    classes: list[int] = []
    shapes: list[tuple[tuple[int, int], ...]] = []
    colors: list[int] = []
    for ar, ac, fn in frames:
        motif_entries = [
            (r - ar - 1, c - ac - 1, grid[r][c])
            for r in range(ar + 1, ar + fn - 1)
            for c in range(ac + 1, ac + fn - 1)
            if grid[r][c] not in (0, 1)
        ]
        if not motif_entries:
            raise ValueError("each frame must contain a nonempty motif")
        motif_colors = {value for _, _, value in motif_entries}
        if len(motif_colors) != 1:
            raise ValueError("each motif must be monochrome")
        cls, norm = _sym_class((r, c) for r, c, _ in motif_entries)
        classes.append(cls)
        shapes.append(_shape_key(norm))
        colors.append(next(iter(motif_colors)))

    distinct_classes = len(set(classes))
    if distinct_classes == 1:
        layout = "all_same"
    elif distinct_classes == 2:
        layout = "pair"
    elif distinct_classes == 3:
        layout = "all_distinct"
    else:  # impossible for three panels, kept explicit for defensive clarity
        raise ValueError(f"invalid class pattern {classes}")

    if len(set(colors)) == 1:
        texture = "same_color"
    elif len(set(colors)) == 3:
        texture = "mixed_colors"
    else:
        texture = "partial_color_repeat"

    return {
        "frames": tuple(frames),
        "frame_n": frames[0][2],
        "classes": tuple(classes),
        "shapes": tuple(shapes),
        "colors": tuple(colors),
        "layout": layout,
        "texture": texture,
    }


def observe_overrides(grid: list[list[int]]) -> dict[str, object]:
    """Expose exact returned-grid values for every declared axis."""
    analysis = analyze_grid(grid)
    return {
        "frame_n": analysis["frame_n"],
        "layout": analysis["layout"],
        "texture": analysis["texture"],
    }


def self_check(grid: list[list[int]], *, difficulty=None, meta=None) -> list[str]:
    """Executable semantic and structural contract for canonical and generated inputs."""
    del difficulty, meta
    errors: list[str] = []
    if not _is_rectangular_grid(grid):
        return ["grid must be a nonempty rectangular list of lists"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("all cells must be integer ARC colors 0..9")

    frames = _find_frames(grid)
    if len(frames) != 3:
        return errors + [f"expected exactly 3 hollow color-1 frames, found {len(frames)}"]
    if len({ar for ar, _, _ in frames}) != 1:
        errors.append(f"frames must be horizontally aligned: {frames}")
    if len({fn for _, _, fn in frames}) != 1:
        errors.append(f"frames must have one size: {frames}")
    intervals = [(ac, ac + fn - 1) for _, ac, fn in frames]
    if any(intervals[i][1] >= intervals[i + 1][0] for i in range(2)):
        errors.append(f"frames must be disjoint and ordered: {frames}")

    covered: set[tuple[int, int]] = set()
    for ar, ac, fn in frames:
        covered.update(
            (r, c)
            for r in range(ar, ar + fn)
            for c in range(ac, ac + fn)
        )
        if any(
            grid[r][c] == 1
            for r in range(ar + 1, ar + fn - 1)
            for c in range(ac + 1, ac + fn - 1)
        ):
            errors.append("frame interiors may not contain color 1")
    if any(
        grid[r][c] != 0 and (r, c) not in covered
        for r in range(len(grid))
        for c in range(len(grid[0]))
    ):
        errors.append("nonzero cells may occur only inside the three frame rectangles")

    try:
        analysis = analyze_grid(grid)
    except ValueError as exc:
        return errors + [str(exc)]

    classes = analysis["classes"]
    shapes = analysis["shapes"]
    colors = analysis["colors"]
    if analysis["texture"] not in TEXTURES:
        errors.append(f"motif colors must be all shared or all distinct, found {colors}")

    class_count = len(set(classes))
    if class_count == 1:
        # Canonical all-same has two exact shapes (one is repeated), so this is
        # the strongest invariant shared by both authority and generated data.
        if len(set(shapes)) < 2:
            errors.append("all-same-class examples must use at least two exact shapes")
    elif class_count == 2:
        for cls in set(classes):
            idxs = [i for i, got in enumerate(classes) if got == cls]
            if len(idxs) == 2 and shapes[idxs[0]] == shapes[idxs[1]]:
                errors.append("same-class teaching pairs must use different exact shapes")
    elif class_count != 3:
        errors.append(f"classes must form pair, all-same, or all-distinct layout: {classes}")
    return errors


def strict_canonical_like(grid: list[list[int]], *, difficulty=None, meta=None) -> list[str]:
    """Strict semantic gate shared by canonical and generated distributions."""
    return self_check(grid, difficulty=difficulty, meta=meta)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned Racket rule authority."""
    return _equal_matrix(analyze_grid(grid)["classes"])


def _collapse_ud_with_none(grid: list[list[int]]) -> list[list[int]]:
    classes = analyze_grid(grid)["classes"]
    return _equal_matrix(tuple(0 if cls == 2 else cls for cls in classes))


def _exact_shape_equality(grid: list[list[int]]) -> list[list[int]]:
    return _equal_matrix(analyze_grid(grid)["shapes"])


def _motif_color_equality(grid: list[list[int]]) -> list[list[int]]:
    return _equal_matrix(analyze_grid(grid)["colors"])


SEMANTIC_RIVALS = {
    "collapse_ud_with_none": _collapse_ud_with_none,
    "exact_shape_equality": _exact_shape_equality,
    "motif_color_equality": _motif_color_equality,
}
CANONICAL_SHORTCUTS = {"collapse_ud_with_none": _collapse_ud_with_none}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness_for(name: str, grid: list[list[int]]) -> bool:
    return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    name: (lambda grid, rival_name=name: _witness_for(rival_name, grid))
    for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos: Sequence[dict], query: dict | None = None) -> list[str]:
    """Return reasons a four-demo lesson fails to identify the intended rule."""
    errors: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        errors.append(f"need at least {EXAMPLES_NEEDED} demonstrations, found {len(demos)}")

    pairs = list(demos)
    if query is not None:
        pairs.append(query)
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {index} must contain input and output")
            continue
        structural = self_check(pair["input"])
        errors.extend(f"pair {index}: {message}" for message in structural)
        if not structural and rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"pair {index}: output does not match the pinned rule")

    if errors:
        return errors
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"demonstrations do not falsify rival: {name}")
    return errors


def _difficulty_name(difficulty: object) -> str:
    if difficulty is None:
        return "medium"
    if isinstance(difficulty, str):
        if difficulty not in ("easy", "medium", "hard"):
            raise ValueError(f"difficulty must be easy, medium, or hard; got {difficulty!r}")
        return difficulty
    if isinstance(difficulty, Real) and not isinstance(difficulty, bool):
        value = float(difficulty)
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"difficulty numeric value must lie in [0, 1], got {difficulty!r}")
        return "easy" if value < 1 / 3 else ("medium" if value < 2 / 3 else "hard")
    raise ValueError(f"difficulty must be easy, medium, hard, or a number in [0, 1]; got {difficulty!r}")


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")
    frame_n = overrides.get("frame_n")
    if frame_n is not None and (type(frame_n) is not int or frame_n not in FRAME_SIZES):
        raise ValueError(f"frame_n override must be one of {FRAME_SIZES}, got {frame_n!r}")
    layout = overrides.get("layout")
    if layout is not None and layout not in LAYOUTS:
        raise ValueError(f"layout override must be one of {LAYOUTS}, got {layout!r}")
    texture = overrides.get("texture")
    if texture is not None and texture not in TEXTURES:
        raise ValueError(f"texture override must be one of {TEXTURES}, got {texture!r}")


def _classes_for_layout(layout: str, slot: int, rng, *, explicit: bool) -> tuple[int, int, int]:
    if not explicit:
        scheduled = _SCHEDULE_CLASSES[slot]
        if scheduled is not None:
            return scheduled
        same = rng.choice((0, 1, 2, 3))
        return (same, same, same)

    if layout == "pair":
        pair_positions = ((0, 1), (0, 2), (1, 2))
        repeated = (2, 1, 2)[slot % 3]
        outsider_options = [cls for cls in (0, 1, 2, 3) if cls != repeated]
        outsider = rng.choice(outsider_options)
        classes = [outsider, outsider, outsider]
        for position in pair_positions[slot % 3]:
            classes[position] = repeated
        return tuple(classes)  # type: ignore[return-value]
    if layout == "all_distinct":
        third = rng.choice((1, 3))
        classes = [0, 2, third]
        rng.shuffle(classes)
        return tuple(classes)  # type: ignore[return-value]
    same = rng.choice((0, 1, 2, 3))
    return (same, same, same)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic input grid; every declared override is exact."""
    _validate_overrides(overrides)
    band = _difficulty_name(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = sample_index % LESSON_SCHEDULE_PERIOD

    frame_overridden = overrides.get("frame_n") is not None
    layout_overridden = overrides.get("layout") is not None
    texture_overridden = overrides.get("texture") is not None
    canonical_profile = slot == 0 and not frame_overridden and not texture_overridden

    if canonical_profile:
        frame_options = (6,)
    else:
        frame_options = {
            "easy": (5, 5, 5, 6, 6, 7, 8),
            "medium": (5, 6, 6, 7, 7, 8),
            "hard": (5, 6, 7, 7, 8, 8, 8),
        }[band]
    frame_n = ctx.draw_choice("frame_n", FRAME_SIZES if frame_overridden else frame_options)

    default_layout = _SCHEDULE_LAYOUTS[slot]
    layout = ctx.draw_choice("layout", LAYOUTS if layout_overridden else (default_layout,))
    default_texture = _SCHEDULE_TEXTURES[slot]
    texture = ctx.draw_choice("texture", TEXTURES if texture_overridden else (default_texture,))

    if canonical_profile:
        top, bottom, left, right, gap = 2, 1, 1, 0, 2
    else:
        top = bottom = left = right = 1
        gap = ctx.draw_int("gap", 1, 3)
        while frame_n * 3 + gap * 2 + left + right > 30:
            gap -= 1
    height = top + frame_n + bottom
    width = left + 3 * frame_n + 2 * gap + right
    grid = full_grid(height, width, 0)
    anchors = [(top, left + index * (frame_n + gap)) for index in range(3)]
    for ar, ac in anchors:
        draw_frame(grid, ar, ac, ar + frame_n - 1, ac + frame_n - 1, 1)

    rng = ctx.draw_rng("semantic_content")
    classes = _classes_for_layout(layout, slot, rng, explicit=layout_overridden)
    if len(set(classes)) != {"pair": 2, "all_same": 1, "all_distinct": 3}[layout]:
        raise RuntimeError(f"internal layout/class mismatch: {layout} -> {classes}")

    inner = frame_n - 2
    motifs: list[tuple[tuple[int, int], ...]] = []
    used_by_class: dict[int, set[tuple[tuple[int, int], ...]]] = {0: set(), 1: set(), 2: set(), 3: set()}
    for cls in classes:
        motif = _random_motif(rng, cls, inner, used_by_class[cls])
        used_by_class[cls].add(motif)
        motifs.append(motif)

    palette = (2, 3, 4, 5, 6, 7, 8, 9)
    if texture == "same_color":
        color = rng.choice(palette)
        colors = (color, color, color)
    else:
        colors = tuple(rng.sample(palette, 3))

    for (ar, ac), motif, color in zip(anchors, motifs, colors):
        motif_h = max(r for r, _ in motif) + 1
        motif_w = max(c for _, c in motif) + 1
        dr = rng.randint(0, inner - motif_h)
        dc = rng.randint(0, inner - motif_w)
        for r, c in motif:
            grid[ar + 1 + dr + r][ac + 1 + dc + c] = color

    failures = self_check(grid, difficulty=difficulty)
    if failures:
        raise RuntimeError("generated invalid grid: " + "; ".join(failures))
    return grid

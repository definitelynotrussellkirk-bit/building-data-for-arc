"""Semantic generator for ARC task 1f85a75f / 5dedfc297cf5.

The input is a background-0 canvas with many same-colour 4-connected objects.
Exactly one object is largest by cell count.  The answer is the rectangular
crop of the ORIGINAL input at that object's bounding box, preserving the
object colour and every background hole/indentation inside the box.

A five-slot lesson schedule deliberately includes:
  0. an exact canonical linked profile (30x30, canonical palette/component
     count, target D4 morphology, and distractor morphology histogram),
  1. a smaller object with a larger bounding-box area,
  2. a same-colour target decoy plus a rarer-colour object, and
  3. an off-centre, late-reading-order irregular target.

Those controls rebut largest-bbox-area, least-frequent-colour, first/centre
position, fixed-size, and solid-bbox shortcuts.  Slots 0 and 4 are canonical
anchors; every five consecutive samples contain all controls, so
EXAMPLES_NEEDED=5 lessons remain identifiable at every sliding-window start.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.selfcheck import components as _components

GENERATOR_ID = "5dedfc297cf5"
TASK_ID = "5dedfc297cf5"
VERSION = "2.0.0"
RULE_HASH = "f0032bdd6779"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "Find same-colour 4-connected foreground objects, select the unique object "
    "with the greatest CELL COUNT, and return the crop of the ORIGINAL input "
    "at that object's bounding box. Preserve its colour and any background "
    "holes. Generated lessons include exact canonical noisy-field profiles and "
    "counterexamples to bbox-area, colour-frequency, fixed-position, fixed-size, "
    "and solid-bbox shortcuts."
)

INVARIANTS = [
    "background is 0",
    "foreground objects are same-colour 4-connected components",
    "one foreground object is uniquely largest by cell count",
    "the selected crop contains background, so shape preservation is visible",
    "no distractor cell lies inside the selected object's bounding box",
    "ordinary five-sample lessons contain all shortcut-rebutting controls",
]

# Only exact, returned-grid-observable controls are declared as public axes.
# Target morphology, colours, object counts, and placement still vary, but they
# are curriculum internals rather than caller promises.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 12..30; scheduled canonical slot is 30",
        "valid": "12..30",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 12..30; scheduled canonical slot is 30",
        "valid": "12..30",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

# Exact target morphologies from the two training pairs and held-out test pair.
_CANONICAL_TARGETS = (
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    (
        (0, 0), (0, 1),
        (1, 0), (1, 1), (1, 2),
        (2, 0),         (2, 2),
        (3, 0), (3, 1), (3, 2),
                (4, 1), (4, 2),
    ),
    (
                (0, 1), (0, 2), (0, 3),
        (1, 0), (1, 1),         (1, 3),
        (2, 0), (2, 1),         (2, 3),
                (3, 1), (3, 2), (3, 3),
    ),
)

# The canonical linked profiles are not independent marginals.  Palette size,
# component count, target morphology, and distractor morphology co-occur.
_CANONICAL_PROFILE_SPECS = (
    {
        "palette_size": 3,
        "target": _CANONICAL_TARGETS[0],
        "distractor_signatures": Counter({(1, 1, 1): 29, (2, 1, 2): 2, (2, 2, 1): 5}),
    },
    {
        "palette_size": 4,
        "target": _CANONICAL_TARGETS[1],
        "distractor_signatures": Counter({(1, 1, 1): 80, (2, 1, 2): 3, (2, 2, 1): 3}),
    },
    {
        "palette_size": 5,
        "target": _CANONICAL_TARGETS[2],
        "distractor_signatures": Counter({
            (1, 1, 1): 98,
            (2, 1, 2): 4,
            (2, 2, 1): 7,
            (3, 1, 3): 1,
            (3, 3, 1): 1,
            (4, 2, 3): 1,
        }),
    },
)

# Generalized targets are connected, span their bbox, and leave visible zeros.
_GENERAL_TARGETS = (
    # 3x3 hollow frame, 8 cells
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    # 4x4 U-like object, 10 cells
    ((0, 0), (0, 3), (1, 0), (1, 3), (2, 0), (2, 3),
     (3, 0), (3, 1), (3, 2), (3, 3)),
    # 3x5 irregular object, 9 cells
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
     (1, 0), (2, 0), (2, 1), (2, 2)),
    # 4x4 irregular ring fragment, 11 cells
    ((0, 0), (0, 1), (0, 2), (0, 3),
     (1, 0),                 (1, 3),
     (2, 0),         (2, 2), (2, 3),
     (3, 0),                 (3, 3)),
)

# Explicit larger-bbox-but-smaller-cell-count rival object: 7 cells in 4x4.
_BBOX_DECOY = (
    (0, 0),
    (1, 0), (1, 1),
            (2, 1), (2, 2),
                    (3, 2), (3, 3),
)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0, c0, _, _ = _bbox(cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _d4(shape: Iterable[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    raw = []
    for r, c in shape:
        if code == 1:
            raw.append((c, -r))
        elif code == 2:
            raw.append((-r, -c))
        elif code == 3:
            raw.append((-c, r))
        elif code == 4:
            raw.append((r, -c))
        elif code == 5:
            raw.append((-r, c))
        elif code == 6:
            raw.append((c, r))
        elif code == 7:
            raw.append((-c, -r))
        else:
            raw.append((r, c))
    return _normalize(raw)


def _d4_signature(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_d4(shape, code) for code in range(8))


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    r0, c0, r1, c1 = _bbox(shape)
    return r1 - r0 + 1, c1 - c0 + 1


def _shape_signature(shape: Iterable[tuple[int, int]]) -> tuple[int, int, int]:
    shape = tuple(shape)
    h, w = _shape_dims(shape)
    return len(shape), h, w


def _crop(grid, bbox):
    r0, c0, r1, c1 = bbox
    return [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]


def _largest_object(grid):
    comps = _components(grid)
    if not comps:
        return None
    return min(comps, key=lambda obj: (-len(obj["cells"]), obj["bbox"][0], obj["bbox"][1]))


def rule_mirror(grid):
    largest = _largest_object(grid)
    if largest is None:
        raise ValueError("no foreground object")
    return _crop(grid, largest["bbox"])


def observe_overrides(grid) -> dict[str, int]:
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return int(sample_index) % 5


SCHEDULE_PROFILES = (0, 1, 2, 3, 4)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    unknown = sorted(
        key for key, value in overrides.items()
        if value is not None and key not in AXES
    )
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")


def _draw_axis_int(ctx, overrides, name, band_lo, band_hi):
    if overrides.get(name) is not None:
        return ctx.draw_int(name, 12, 30)
    return ctx.draw_int(name, band_lo, band_hi)


def _paint(grid, shape, top, left, color):
    for r, c in shape:
        grid[top + r][left + c] = color


def _translated(shape, top, left):
    return tuple((top + r, left + c) for r, c in shape)


def _inside_bbox(cells, bbox):
    r0, c0, r1, c1 = bbox
    return any(r0 <= r <= r1 and c0 <= c <= c1 for r, c in cells)


def _available_component_colors(grid, cells, colors):
    h, w = len(grid), len(grid[0])
    cellset = set(cells)
    blocked = set()
    for r, c in cells:
        for dr, dc in _DIRS4:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in cellset:
                continue
            if grid[nr][nc] != 0:
                blocked.add(grid[nr][nc])
    return [color for color in colors if color not in blocked]


def _place_component(
    grid,
    shape,
    colors,
    rng,
    *,
    forbidden_bbox=None,
    fixed_color=None,
    require_moat=False,
    attempts=1400,
):
    h, w = len(grid), len(grid[0])
    sh, sw = _shape_dims(shape)
    if sh > h or sw > w:
        return None
    for _ in range(attempts):
        top = rng.randint(0, h - sh)
        left = rng.randint(0, w - sw)
        cells = _translated(shape, top, left)
        if any(grid[r][c] != 0 for r, c in cells):
            continue
        if forbidden_bbox is not None and _inside_bbox(cells, forbidden_bbox):
            continue
        if require_moat:
            cellset = set(cells)
            if any(
                0 <= r + dr < h
                and 0 <= c + dc < w
                and (r + dr, c + dc) not in cellset
                and grid[r + dr][c + dc] != 0
                for r, c in cells
                for dr, dc in _DIRS8
            ):
                continue
        available = _available_component_colors(grid, cells, colors)
        if fixed_color is not None:
            if fixed_color not in available:
                continue
            color = fixed_color
        else:
            if not available:
                continue
            color = rng.choice(available)
        _paint(grid, shape, top, left, color)
        return cells, color
    return None


def _shapes_from_signature_counter(counter):
    shapes = []
    for signature, count in sorted(counter.items(), reverse=True):
        size, height, width = signature
        if (size, height, width) == (1, 1, 1):
            shape = ((0, 0),)
        elif size == 2 and height == 1 and width == 2:
            shape = ((0, 0), (0, 1))
        elif size == 2 and height == 2 and width == 1:
            shape = ((0, 0), (1, 0))
        elif size == 3 and height == 1 and width == 3:
            shape = ((0, 0), (0, 1), (0, 2))
        elif size == 3 and height == 3 and width == 1:
            shape = ((0, 0), (1, 0), (2, 0))
        elif (size, height, width) == (4, 2, 3):
            shape = ((0, 0), (0, 1), (0, 2), (1, 1))
        else:
            raise ValueError(f"unsupported canonical distractor signature {signature}")
        shapes.extend([shape] * count)
    return shapes


def _draw_canonical_profile(ctx, sample_index):
    # Even fixed canonical anchors record exact dimension provenance so every
    # declared observable axis is auditable on every default draw.
    h = ctx.draw_int("grid_h", 30, 30)
    w = ctx.draw_int("grid_w", 30, 30)
    profile_rng = ctx.draw_rng("canonical_profile")
    profile_index = profile_rng.randrange(len(_CANONICAL_PROFILE_SPECS))
    spec = _CANONICAL_PROFILE_SPECS[profile_index]
    colors = ctx.draw_distinct_colors(
        "canonical_colors", n=spec["palette_size"] - 1, exclude={0}
    )
    target_color = colors[0]
    distractor_colors = colors[1:]
    transform_code = ctx.draw_rng("canonical_target_transform").randrange(8)
    target_shape = _d4(spec["target"], transform_code)
    th, tw = _shape_dims(target_shape)
    distractor_shapes = _shapes_from_signature_counter(spec["distractor_signatures"])

    for attempt in range(48):
        rng = ctx.draw_rng(f"canonical_layout_{attempt}")
        grid = [[0 for _ in range(w)] for _ in range(h)]
        top = rng.randint(0, h - th)
        left = rng.randint(0, w - tw)
        _paint(grid, target_shape, top, left, target_color)
        target_bbox = (top, left, top + th - 1, left + tw - 1)
        ok = True
        # Larger distractors first; shuffled within equal signatures.
        ordered = list(distractor_shapes)
        rng.shuffle(ordered)
        ordered.sort(key=lambda shape: (-len(shape), -_shape_dims(shape)[0], -_shape_dims(shape)[1]))
        for shape in ordered:
            if _place_component(
                grid,
                shape,
                distractor_colors,
                rng,
                forbidden_bbox=target_bbox,
                require_moat=False,
                attempts=1800,
            ) is None:
                ok = False
                break
        if ok and not self_check(grid) and not strict_canonical_like(grid):
            return grid
    raise RuntimeError(
        f"could not construct canonical linked profile {profile_index} for sample {sample_index}"
    )


def _reading_rank(grid, target):
    ordered = sorted(_components(grid), key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))
    target_key = (target["color"], frozenset(target["cells"]))
    for index, obj in enumerate(ordered):
        if (obj["color"], frozenset(obj["cells"])) == target_key:
            return index, len(ordered)
    return None


def _densify_noisy_field(
    grid,
    *,
    target_bbox,
    target_rank,
    distractor_colors,
    rng,
    desired_components,
    favored_color=None,
    favored_margin=0,
):
    """Add canonical-style one-cell objects without merging equal colours.

    Adjacent DIFFERENT colours remain separate same-colour components, so a
    small canvas can still carry the high object-count texture of the official
    examples.  Position filtering preserves the deliberate first/last target
    witnesses used by the lesson schedule.
    """
    h, w = len(grid), len(grid[0])
    target_origin = (target_bbox[0], target_bbox[1])
    candidates = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or _inside_bbox(((r, c),), target_bbox):
                continue
            if target_rank == "first" and (r, c) < target_origin:
                continue
            if target_rank == "last" and (r, c) > target_origin:
                continue
            candidates.append((r, c))
    rng.shuffle(candidates)

    color_cells = Counter(
        value for row in grid for value in row if value in distractor_colors
    )
    for r, c in candidates:
        if len(_components(grid)) >= desired_components:
            return True
        neighbor_colors = {
            grid[r + dr][c + dc]
            for dr, dc in _DIRS4
            if 0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] != 0
        }
        available = [color for color in distractor_colors if color not in neighbor_colors]
        if not available:
            continue
        color = min(
            available,
            key=lambda value: (
                color_cells[value] - (favored_margin if value == favored_color else 0),
                value,
            ),
        )
        grid[r][c] = color
        color_cells[color] += 1
    return len(_components(grid)) >= desired_components


def _draw_general(ctx, sample_index, difficulty, overrides):
    band = difficulty or "medium"
    ranges = {
        "easy": ((12, 18), (12, 18)),
        "medium": ((18, 25), (18, 25)),
        "hard": ((24, 30), (24, 30)),
    }
    (h_lo, h_hi), (w_lo, w_hi) = ranges[band]
    h = _draw_axis_int(ctx, overrides, "grid_h", h_lo, h_hi)
    w = _draw_axis_int(ctx, overrides, "grid_w", w_lo, w_hi)
    slot = int(sample_index) % 5
    branch = ("general_anchor", "bbox_decoy", "repeated_color", "late_irregular", "general_anchor")[slot]

    palette_n = 4 if branch != "late_irregular" else 5
    colors = ctx.draw_distinct_colors("general_colors", n=palette_n - 1, exclude={0})
    target_color = colors[0]
    d4_code = ctx.draw_rng("general_target_transform").randrange(8)

    if branch == "bbox_decoy":
        target_shape = _d4(_GENERAL_TARGETS[0], d4_code)  # 8 cells, 3x3 bbox
        decoys = [(_BBOX_DECOY, colors[1]), (((0, 0), (0, 1)), colors[2]), (((0, 0),), colors[1])]
        target_rank = "first"
    elif branch == "repeated_color":
        target_shape = _d4(_GENERAL_TARGETS[1], d4_code)  # 10 cells
        decoys = [
            (((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)), target_color),
            (((0, 0),), colors[1]),
            (((0, 0), (0, 1), (1, 0), (1, 1)), colors[2]),
        ]
        target_rank = "middle"
    elif branch == "late_irregular":
        target_shape = _d4(_GENERAL_TARGETS[2], d4_code)  # 9 cells, non-square
        decoys = [
            (((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)), colors[1]),
            (((0, 0), (0, 1), (1, 1), (2, 1), (2, 0)), colors[2]),
            (((0, 0), (0, 1), (1, 0), (1, 1)), colors[3]),
        ]
        target_rank = "last"
    else:
        target_shape = _d4(_GENERAL_TARGETS[3], d4_code)  # 11 cells
        decoys = [
            (((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)), colors[1]),
            (((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)), colors[2]),
            (((0, 0), (0, 1), (1, 0), (1, 1)), colors[1]),
        ]
        target_rank = "middle"

    th, tw = _shape_dims(target_shape)
    for attempt in range(160):
        rng = ctx.draw_rng(f"general_layout_{branch}_{attempt}")
        grid = [[0 for _ in range(w)] for _ in range(h)]
        if target_rank == "first":
            top = rng.randint(0, max(0, min(2, h - th)))
            left = rng.randint(0, max(0, min(2, w - tw)))
        elif target_rank == "last":
            top = rng.randint(max(0, h - th - 2), h - th)
            left = rng.randint(max(0, w - tw - 2), w - tw)
        else:
            top_lo = max(0, (h - th) // 3)
            top_hi = min(h - th, max(top_lo, 2 * (h - th) // 3))
            left_lo = max(0, (w - tw) // 3)
            left_hi = min(w - tw, max(left_lo, 2 * (w - tw) // 3))
            top = rng.randint(top_lo, top_hi)
            left = rng.randint(left_lo, left_hi)
        _paint(grid, target_shape, top, left, target_color)
        target_bbox = (top, left, top + th - 1, left + tw - 1)

        ok = True
        for shape, color in decoys:
            transformed = _d4(shape, rng.randrange(8))
            if _place_component(
                grid,
                transformed,
                (color,),
                rng,
                fixed_color=color,
                forbidden_bbox=target_bbox,
                require_moat=True,
                attempts=700,
            ) is None:
                ok = False
                break
        if not ok:
            continue
        desired_components = max(30, min(75, (h * w) // 4))
        if not _densify_noisy_field(
            grid,
            target_bbox=target_bbox,
            target_rank=target_rank,
            distractor_colors=(tuple(colors) if branch == "repeated_color" else tuple(colors[1:])),
            rng=rng,
            desired_components=desired_components,
            favored_color=(target_color if branch == "repeated_color" else None),
            favored_margin=(6 if branch == "repeated_color" else 0),
        ):
            continue
        target = _largest_object(grid)
        if target is None:
            continue
        rank = _reading_rank(grid, target)
        if target_rank == "first" and rank and rank[0] != 0:
            continue
        if target_rank == "last" and rank and rank[0] != rank[1] - 1:
            continue
        if target_rank == "middle" and rank and rank[0] in (0, rank[1] - 1):
            continue
        if not self_check(grid):
            return grid
    raise RuntimeError(f"could not construct branch={branch} in {h}x{w}")


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
    explicit = any(value is not None for value in overrides.values())
    if int(sample_index) % 5 in (0, 4) and not explicit:
        # Canonical anchor remains present in every difficulty band.
        return _draw_canonical_profile(ctx, sample_index)
    return _draw_general(ctx, sample_index, difficulty, overrides)


def _analysis(grid):
    errors = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"], "components": []}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular and non-empty"], "components": []}
    h = len(grid)
    if not (1 <= h <= 30 and 1 <= width <= 30):
        errors.append(f"grid outside ARC bounds: {h}x{width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return {"errors": errors, "components": []}

    comps = _components(grid)
    if len(comps) < 2:
        errors.append("expected at least two foreground objects")
        return {"errors": errors, "components": comps}
    sizes = sorted((len(obj["cells"]) for obj in comps), reverse=True)
    if sizes[0] == sizes[1]:
        errors.append("largest object must be unique by cell count")
    largest = _largest_object(grid)
    if largest is None:
        return {"errors": errors, "components": comps}
    if len(largest["cells"]) < 6:
        errors.append("largest object is too small to teach selection and cropping")
    r0, c0, r1, c1 = largest["bbox"]
    bbox_area = (r1 - r0 + 1) * (c1 - c0 + 1)
    if bbox_area <= len(largest["cells"]):
        errors.append("selected crop must contain background; solid bboxes hide shape preservation")
    if (r1 - r0 + 1, c1 - c0 + 1) == (h, width):
        errors.append("selected bbox must reduce the input canvas")
    largest_key = (largest["color"], frozenset(largest["cells"]))
    for obj in comps:
        key = (obj["color"], frozenset(obj["cells"]))
        if key == largest_key:
            continue
        if any(r0 <= r <= r1 and c0 <= c <= c1 for r, c in obj["cells"]):
            errors.append("a distractor lies inside the selected object's bounding box")
            break
    if len({obj["color"] for obj in comps}) < 2:
        errors.append("need at least two foreground colours to rebut colour-only selection")
    return {
        "errors": errors,
        "components": comps,
        "largest": largest,
        "component_sizes": sizes,
        "palette_size": len({value for row in grid for value in row}),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def _distractor_signature_counter(comps, largest):
    largest_key = (largest["color"], frozenset(largest["cells"]))
    counter = Counter()
    for obj in comps:
        if (obj["color"], frozenset(obj["cells"])) == largest_key:
            continue
        r0, c0, r1, c1 = obj["bbox"]
        counter[(len(obj["cells"]), r1 - r0 + 1, c1 - c0 + 1)] += 1
    return counter


def strict_canonical_like(grid):
    """Exact linked canonical manifold, quotiented only by D4 and colour names."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [f"teaching grammar: {analysis['errors'][0]}"]
    reasons = []
    if (len(grid), len(grid[0])) != (30, 30):
        return ["canonical canvas is 30x30"]
    largest = analysis["largest"]
    target_signature = _d4_signature(_normalize(largest["cells"]))
    distractors = _distractor_signature_counter(analysis["components"], largest)
    observed = (
        analysis["palette_size"],
        len(analysis["components"]),
        target_signature,
        distractors,
    )
    for spec in _CANONICAL_PROFILE_SPECS:
        expected_components = 1 + sum(spec["distractor_signatures"].values())
        expected = (
            spec["palette_size"],
            expected_components,
            _d4_signature(spec["target"]),
            spec["distractor_signatures"],
        )
        if observed == expected:
            return []
    reasons.append(
        "linked palette/component-count/target-D4/distractor-morphology profile is not canonical"
    )
    return reasons


def _bbox_area(obj):
    r0, c0, r1, c1 = obj["bbox"]
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _answer_from_object(grid, obj):
    return _crop(grid, obj["bbox"])


def _largest_bbox_area_answer(grid):
    comps = _components(grid)
    obj = min(comps, key=lambda item: (-_bbox_area(item), item["bbox"][0], item["bbox"][1]))
    return _answer_from_object(grid, obj)


def _least_frequent_color_answer(grid):
    comps = _components(grid)
    totals = Counter()
    for obj in comps:
        totals[obj["color"]] += len(obj["cells"])
    color = min(totals, key=lambda value: (totals[value], value))
    choices = [obj for obj in comps if obj["color"] == color]
    obj = min(choices, key=lambda item: (-len(item["cells"]), item["bbox"][0], item["bbox"][1]))
    return _answer_from_object(grid, obj)


def _first_object_answer(grid):
    obj = min(_components(grid), key=lambda item: (item["bbox"][0], item["bbox"][1]))
    return _answer_from_object(grid, obj)


def _center_object_answer(grid):
    h, w = len(grid), len(grid[0])
    def distance(obj):
        r0, c0, r1, c1 = obj["bbox"]
        return (abs((r0 + r1) - (h - 1)) + abs((c0 + c1) - (w - 1)), r0, c0)
    return _answer_from_object(grid, min(_components(grid), key=distance))


def _solid_largest_bbox_answer(grid):
    largest = _largest_object(grid)
    r0, c0, r1, c1 = largest["bbox"]
    return [[largest["color"] for _ in range(c0, c1 + 1)] for _ in range(r0, r1 + 1)]


SEMANTIC_RIVALS = {
    "largest_bounding_box_area": _largest_bbox_area_answer,
    "least_frequent_foreground_color": _least_frequent_color_answer,
    "first_object_in_reading_order": _first_object_answer,
    "object_nearest_canvas_center": _center_object_answer,
    "solid_fill_of_largest_bbox": _solid_largest_bbox_answer,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "largest_bounding_box_area": _largest_bbox_area_answer,
    "least_frequent_foreground_color": _least_frequent_color_answer,
}


def _refutes(rival_name):
    rival = SEMANTIC_RIVALS[rival_name]
    def predicate(grid):
        try:
            return rival(grid) != rule_mirror(grid)
        except Exception:
            return False
    return predicate


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "smaller_object_has_larger_bbox": _refutes("largest_bounding_box_area"),
    "target_colour_is_not_rarest": _refutes("least_frequent_foreground_color"),
    "target_is_not_first": _refutes("first_object_in_reading_order"),
    "target_is_not_nearest_center": _refutes("object_nearest_canvas_center"),
    "target_crop_contains_background": _refutes("solid_fill_of_largest_bbox"),
}
WITNESS_RIVALS = {
    "smaller_object_has_larger_bbox": ["largest_bounding_box_area"],
    "target_colour_is_not_rarest": ["least_frequent_foreground_color"],
    "target_is_not_first": ["first_object_in_reading_order"],
    "target_is_not_nearest_center": ["object_nearest_canvas_center"],
    "target_crop_contains_background": ["solid_fill_of_largest_bbox"],
}


def lesson_identifiable(demos, query):
    reasons = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with largest-object crop")

    if self_check(query["input"]):
        reasons.append("query input violates the teaching grammar")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with largest-object crop")

    for name, rival in LESSON_COMPETITORS.items():
        survives = True
        for pair in demos:
            try:
                if rival(pair["input"]) != pair["output"]:
                    survives = False
                    break
            except Exception:
                survives = False
                break
        if survives:
            reasons.append(f"rival rule {name!r} still fits every demonstration")
    return reasons

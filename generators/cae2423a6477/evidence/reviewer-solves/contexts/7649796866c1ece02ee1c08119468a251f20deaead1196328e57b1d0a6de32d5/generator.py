"""Generator for ARC task ``cae2423a6477`` (Ring Selector).

The authoritative rule is intentionally narrow: among the 4-connected green
(color 3) objects, recolor an object orange (color 7) exactly when its cells
are the complete border of its own rectangular bounding box.  Other green
objects remain green, including large open outlines, non-rectangular closed
loops, and branched objects that merely surround a rectangular hole.

The generator schedules three complementary scene profiles in every
three-example lesson.  The latter two are explicit counterexamples to the
strongest rules that fit all public demonstrations:

* ``large_open`` refutes size/bounding-box threshold rules.
* ``hollow_irregular`` contains two complementary hollow decoys: a stepped
  simple loop and a rectangular ring with an outward nub.  Together they
  refute "recolor every object with a hole", "recolor every closed,
  unbranched loop", and "recolor every object with a rectangular hole".
"""
from __future__ import annotations

from collections import deque
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "cae2423a6477"
TASK_ID = "cae2423a6477"
VERSION = "3.1.0"
RULE_HASH = "1f6f97325987"

SUMMARY = (
    "Green objects on black: recolor only complete rectangular frames from 3 "
    "to 7. Every three-example schedule includes a canonical small scene, a "
    "large open non-frame, and complementary hollow decoys, so size, bbox, "
    "generic-hole, closed-loop, and rectangular-hole shortcuts are falsified."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

SCENE_PROFILES = (
    "canonical_small",
    "large_open",
    "hollow_irregular",
)
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "sample_index mod 3 schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}

# Declaring the empty set opts into the strict override-rejection policy while
# documenting that the one-axis matrix has no legitimate incompatibilities.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple = ()

INVARIANTS = [
    "background is 0 and every foreground cell is color 3",
    "at least one exact rectangular frame and one non-frame object are present",
    "foreground objects have a one-cell (including diagonal) moat",
    "only exact rectangular frames are recolored by the authoritative rule",
    "the hollow profile contains both a stepped simple loop and a nubbed ring",
    "the scene_profile override is exactly recoverable from the returned grid",
]

# Fixed dimensions make malformed row insertion/deletion detectable while still
# spanning the exact public shapes and progressively larger adversarial scenes.
_PROFILE_DIMS = {
    "canonical_small": {
        "easy": (9, 10),
        "medium": (12, 11),
        "hard": (13, 12),
    },
    "large_open": {
        "easy": (12, 13),
        "medium": (15, 15),
        "hard": (18, 18),
    },
    "hollow_irregular": {
        "easy": (12, 12),
        "medium": (15, 16),
        "hard": (18, 19),
    },
}
_SUPPORTED_DIMS = {
    dims for profile_dims in _PROFILE_DIMS.values() for dims in profile_dims.values()
}
_CANONICAL_DIMS = set(_PROFILE_DIMS["canonical_small"].values())

Coord = tuple[int, int]
Grid = list[list[int]]
Shape = set[Coord]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the semantic branch used by the default lesson schedule.

    ``seed`` and ``difficulty`` are accepted to match the gate contract; the
    residue schedule deliberately depends only on the sequential sample index,
    so every consecutive three examples cover the complete profile space.
    """

    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _difficulty_band(difficulty) -> str:
    if difficulty == "easy":
        return "easy"
    if difficulty == "hard":
        return "hard"
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        if float(difficulty) <= 0.33:
            return "easy"
        if float(difficulty) >= 0.67:
            return "hard"
    return "medium"


def _normalize(cells: Iterable[Coord]) -> Shape:
    cells = set(cells)
    if not cells:
        raise ValueError("shape may not be empty")
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return {(r - min_r, c - min_c) for r, c in cells}


def _shape_dims(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _rect_frame(height: int, width: int) -> Shape:
    if height < 3 or width < 3:
        raise ValueError("a frame needs height and width >= 3")
    return {
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in {0, height - 1} or c in {0, width - 1}
    }


def _broken_frame(height: int, width: int, rng) -> Shape:
    """Large connected border with a single opening and therefore no hole."""

    cells = _rect_frame(height, width)
    side = rng.randrange(4)
    if side == 0:
        cells.remove((0, rng.randint(1, width - 2)))
    elif side == 1:
        cells.remove((height - 1, rng.randint(1, width - 2)))
    elif side == 2:
        cells.remove((rng.randint(1, height - 2), 0))
    else:
        cells.remove((rng.randint(1, height - 2), width - 1))
    return cells


def _hollow_irregular(height: int, width: int, rng) -> Shape:
    """A one-cell-wide non-rectangular loop with one enclosed hole.

    Every cell has exactly two 4-neighbors, so this is a direct counterexample
    to the plausible shortcut "recolor any closed unbranched loop".  The
    shoulder position, reflection, and rotation vary without changing that
    topology.
    """

    if height < 4 or width < 5:
        raise ValueError("an irregular loop needs height >= 4 and width >= 5")

    shoulder = rng.randint(2, width - 3)
    cells = {
        *((0, c) for c in range(shoulder + 1)),
        *((1, c) for c in range(shoulder, width)),
        *((r, width - 1) for r in range(1, height)),
        *((height - 1, c) for c in range(width)),
        *((r, 0) for r in range(height)),
    }

    if rng.randrange(2):
        cells = {(r, width - 1 - c) for r, c in cells}
    for _ in range(rng.randrange(4)):
        current_height, _ = _shape_dims(cells)
        cells = {(c, current_height - 1 - r) for r, c in cells}
    return _normalize(cells)


def _nubbed_rectangular_hole(height: int, width: int, rng) -> Shape:
    """A closed rectangular ring with one outward branch cell.

    The enclosed background remains a rectangle, but the foreground object is
    not the exact border of its own bounding box.  This separates the target
    rule from the tempting shortcut "recolor any object with a rectangular
    hole".
    """

    cells = _rect_frame(height, width)
    side = rng.randrange(4)
    if side == 0:
        cells.add((-1, rng.randint(1, width - 2)))
    elif side == 1:
        cells.add((height, rng.randint(1, width - 2)))
    elif side == 2:
        cells.add((rng.randint(1, height - 2), -1))
    else:
        cells.add((rng.randint(1, height - 2), width))
    return _normalize(cells)


_SMALL_DECOYS: tuple[frozenset[Coord], ...] = (
    frozenset({(0, 0), (0, 1)}),
    frozenset({(0, 0), (1, 0), (1, 1)}),
    frozenset({(0, 0), (0, 1), (1, 0), (1, 1)}),
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2)}),
    frozenset({(0, 0), (1, 0), (2, 0), (2, 1)}),
)


def _can_place(grid: Grid, shape: Shape, top: int, left: int) -> bool:
    h, w = len(grid), len(grid[0])
    absolute = {(top + r, left + c) for r, c in shape}
    if any(not (0 <= r < h and 0 <= c < w) for r, c in absolute):
        return False
    for r, c in absolute:
        for nr in range(max(0, r - 1), min(h, r + 2)):
            for nc in range(max(0, c - 1), min(w, c + 2)):
                if grid[nr][nc] != 0:
                    return False
    return True


def _place_shape(grid: Grid, shape: Shape, rng) -> bool:
    h, w = len(grid), len(grid[0])
    sh, sw = _shape_dims(shape)
    candidates = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    rng.shuffle(candidates)
    for top, left in candidates:
        if not _can_place(grid, shape, top, left):
            continue
        for r, c in shape:
            grid[top + r][left + c] = 3
        return True
    return False


def _render_shapes(height: int, width: int, shapes: list[Shape], rng) -> Grid:
    # Large shapes first avoids painting a tiny object into the only viable
    # region for an adversarial ring. Restarts are deterministic because they
    # consume the same keyed RNG stream.
    shapes = sorted(shapes, key=lambda s: (_shape_dims(s)[0] * _shape_dims(s)[1], len(s)), reverse=True)
    for _ in range(40):
        grid = [[0 for _ in range(width)] for _ in range(height)]
        if all(_place_shape(grid, shape, rng) for shape in shapes):
            return grid
    raise RuntimeError(
        f"could not place {len(shapes)} isolated objects in {height}x{width} grid"
    )


def _scene_shapes(profile: str, band: str, rng) -> list[Shape]:
    shapes: list[Shape] = []
    if profile == "canonical_small":
        frame_options = ((3, 3), (3, 4), (4, 3))
        frame_count = 2 if band == "hard" else 1 + (rng.randrange(4) == 0)
        for _ in range(frame_count):
            shapes.append(_rect_frame(*rng.choice(frame_options)))
        shapes.append(set(rng.choice(_SMALL_DECOYS)))
        return shapes

    frame_count = 2 if band == "hard" and rng.randrange(2) == 0 else 1
    max_dim = {"easy": 4, "medium": 5, "hard": 6}[band]
    for _ in range(frame_count):
        shapes.append(_rect_frame(rng.randint(3, max_dim), rng.randint(3, max_dim)))

    if profile == "large_open":
        shapes.append(
            _broken_frame(
                rng.randint(4, max(4, max_dim)),
                rng.randint(4, max(4, max_dim + 1)),
                rng,
            )
        )
    elif profile == "hollow_irregular":
        shapes.append(
            _hollow_irregular(
                rng.randint(4, max(4, max_dim)),
                rng.randint(5, max(5, max_dim + 1)),
                rng,
            )
        )
        shapes.append(
            _nubbed_rectangular_hole(
                rng.randint(3, max(3, max_dim)),
                rng.randint(3, max(3, max_dim)),
                rng,
            )
        )
    else:  # defensive: draw_choice already validates this
        raise ValueError(f"unknown scene profile {profile!r}")

    if band != "easy" and rng.randrange(3) == 0:
        shapes.append(set(rng.choice(_SMALL_DECOYS)))
    return shapes


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    effective = dict(overrides)
    if effective.get("scene_profile") is None:
        effective["scene_profile"] = schedule_profile(seed, sample_index, difficulty)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    band = _difficulty_band(difficulty)
    height, width = _PROFILE_DIMS[profile][band]
    rng = ctx.draw_rng("layout")
    return _render_shapes(height, width, _scene_shapes(profile, band, rng), rng)


def _validate_grid(grid) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["every grid row must be a non-empty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        errors.append("grid rows must have equal width")
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append("grid values must be integers")
                return errors
    return errors


def _components(grid: Grid, color: int = 3) -> list[Shape]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    components: list[Shape] = []
    while unseen:
        start = next(iter(unseen))
        unseen.remove(start)
        component = {start}
        queue = [start]
        while queue:
            r, c = queue.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    component.add((nr, nc))
                    queue.append((nr, nc))
        components.append(component)
    return components


def _bbox(cells: Shape) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _is_rect_outline(cells: Shape) -> bool:
    r1, c1, r2, c2 = _bbox(cells)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    if height < 3 or width < 3:
        return False
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in {r1, r2} or c in {c1, c2}
    }
    return cells == border


def _enclosed_holes(cells: Shape) -> list[Shape]:
    """Return background components enclosed inside the object's bounding box."""

    r1, c1, r2, c2 = _bbox(cells)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    occupied = {(r - r1, c - c1) for r, c in cells}
    background = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in occupied
    }
    exterior: set[Coord] = set()
    queue: deque[Coord] = deque(
        (r, c)
        for r, c in background
        if r in {0, height - 1} or c in {0, width - 1}
    )
    exterior.update(queue)
    while queue:
        r, c = queue.popleft()
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (nr, nc) in background and (nr, nc) not in exterior:
                exterior.add((nr, nc))
                queue.append((nr, nc))

    remaining = background - exterior
    holes: list[Shape] = []
    while remaining:
        start = remaining.pop()
        hole = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in remaining:
                    remaining.remove((nr, nc))
                    hole.add((nr, nc))
                    queue.append((nr, nc))
        holes.append(hole)
    return holes


def _hole_count(cells: Shape) -> int:
    """Count background components enclosed inside the object's bounding box."""

    return len(_enclosed_holes(cells))


def _has_rectangular_hole(cells: Shape) -> bool:
    """Whether at least one enclosed background component fills its own bbox."""

    for hole in _enclosed_holes(cells):
        r1, c1, r2, c2 = _bbox(hole)
        rectangle = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
        }
        if hole == rectangle:
            return True
    return False


def _is_small_decoy(cells: Shape) -> bool:
    """Match the canonical negative-object family without accepting row noise.

    The public examples use a domino, a 2x2 block, or a short bent object.
    A 3/4-cell straight line is deliberately excluded: copying a populated
    boundary row into another row otherwise manufactures a second "valid"
    distractor while destroying the source object.
    """

    if not 2 <= len(cells) <= 4 or _hole_count(cells):
        return False
    r1, c1, r2, c2 = _bbox(cells)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    return len(cells) == 2 or (height >= 2 and width >= 2)


def _is_broken_frame(cells: Shape) -> bool:
    """Exactly one missing non-corner cell from a rectangular border."""

    r1, c1, r2, c2 = _bbox(cells)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    if height < 4 or width < 4:
        return False
    border = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in {r1, r2} or c in {c1, c2}
    }
    missing = border - cells
    if len(missing) != 1 or not cells < border:
        return False
    (r, c), = missing
    return r not in {r1, r2} or c not in {c1, c2}


def _is_closed_unbranched_loop(cells: Shape) -> bool:
    """Whether a one-cell-wide object forms a closed 4-neighbor cycle."""

    if _hole_count(cells) == 0:
        return False
    neighbors = ((1, 0), (-1, 0), (0, 1), (0, -1))
    return all(
        sum((r + dr, c + dc) in cells for dr, dc in neighbors) == 2
        for r, c in cells
    )


def _is_hollow_irregular(cells: Shape) -> bool:
    """A non-rectangular, closed, unbranched loop with exactly one hole."""

    return (
        not _is_rect_outline(cells)
        and _hole_count(cells) == 1
        and _is_closed_unbranched_loop(cells)
    )


def _is_nubbed_rectangular_hole(cells: Shape) -> bool:
    """Whether removing one outward leaf exposes an exact rectangular frame."""

    if _is_rect_outline(cells) or not _has_rectangular_hole(cells):
        return False
    neighbors = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for cell in cells:
        r, c = cell
        if sum((r + dr, c + dc) in cells for dr, dc in neighbors) != 1:
            continue
        if _is_rect_outline(cells - {cell}):
            return True
    return False


def analyze_grid(grid: Grid) -> dict:
    errors = _validate_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    components = []
    for cells in _components(grid):
        r1, c1, r2, c2 = _bbox(cells)
        exact = _is_rect_outline(cells)
        holes = _hole_count(cells)
        closed_unbranched_loop = _is_closed_unbranched_loop(cells)
        rectangular_hole = _has_rectangular_hole(cells)
        components.append(
            {
                "cells": frozenset(cells),
                "size": len(cells),
                "bbox": (r1, c1, r2, c2),
                "height": r2 - r1 + 1,
                "width": c2 - c1 + 1,
                "exact_frame": exact,
                "hole_count": holes,
                "closed_unbranched_loop": closed_unbranched_loop,
                "rectangular_hole": rectangular_hole,
            }
        )

    exact = [item for item in components if item["exact_frame"]]
    nonframes = [item for item in components if not item["exact_frame"]]
    hollow_nonframes = [item for item in nonframes if item["hole_count"] > 0]
    large_nonframes = [
        item
        for item in nonframes
        if item["size"] >= 8 and item["height"] >= 3 and item["width"] >= 3
    ]

    small_decoys = [item for item in nonframes if _is_small_decoy(set(item["cells"]))]
    broken_frames = [item for item in nonframes if _is_broken_frame(set(item["cells"]))]
    hollow_irregulars = [
        item for item in nonframes if _is_hollow_irregular(set(item["cells"]))
    ]
    nubbed_rectangular_holes = [
        item
        for item in nonframes
        if _is_nubbed_rectangular_hole(set(item["cells"]))
    ]
    closed_unbranched_nonframes = [
        item for item in nonframes if item["closed_unbranched_loop"]
    ]
    rectangular_hole_nonframes = [
        item for item in nonframes if item["rectangular_hole"]
    ]

    profile = None
    if exact and nonframes:
        if (
            len(hollow_irregulars) == 1
            and len(nubbed_rectangular_holes) == 1
            and len(hollow_irregulars)
            + len(nubbed_rectangular_holes)
            + len(small_decoys)
            == len(nonframes)
        ):
            profile = "hollow_irregular"
        elif (
            len(broken_frames) == 1
            and len(broken_frames) + len(small_decoys) == len(nonframes)
        ):
            profile = "large_open"
        elif len(nonframes) == 1 and len(small_decoys) == 1:
            profile = "canonical_small"

    return {
        "height": len(grid),
        "width": len(grid[0]),
        "components": components,
        "component_count": len(components),
        "exact_frame_count": len(exact),
        "nonframe_count": len(nonframes),
        "hollow_nonframe_count": len(hollow_nonframes),
        "large_nonframe_count": len(large_nonframes),
        "small_decoy_count": len(small_decoys),
        "broken_frame_count": len(broken_frames),
        "hollow_irregular_count": len(hollow_irregulars),
        "nubbed_rectangular_hole_count": len(nubbed_rectangular_holes),
        "closed_unbranched_nonframe_count": len(closed_unbranched_nonframes),
        "rectangular_hole_nonframe_count": len(rectangular_hole_nonframes),
        "scene_profile": profile,
    }


def observe_overrides(grid: Grid) -> dict[str, str]:
    profile = analyze_grid(grid)["scene_profile"]
    if profile is None:
        raise ValueError("grid does not realize any declared scene_profile")
    return {"scene_profile": profile}


def _components_have_diagonal_moat(components: list[dict]) -> bool:
    for index, left in enumerate(components):
        for right in components[index + 1 :]:
            for r, c in left["cells"]:
                if any(abs(r - rr) <= 1 and abs(c - cc) <= 1 for rr, cc in right["cells"]):
                    return False
    return True


def self_check(grid: Grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    errors = _validate_grid(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if (height, width) not in _SUPPORTED_DIMS:
        errors.append(f"unsupported grid dimensions {height}x{width}")

    colors = {value for row in grid for value in row}
    unexpected = sorted(colors - {0, 3})
    if unexpected:
        errors.append(f"unexpected colors {unexpected}; expected only 0 and 3")
    if 0 not in colors:
        errors.append("background color 0 is absent")
    if 3 not in colors:
        errors.append("foreground color 3 is absent")
    if unexpected or 3 not in colors:
        return errors

    analysis = analyze_grid(grid)
    if analysis["exact_frame_count"] < 1:
        errors.append("no exact rectangular frame (positive branch absent)")
    if analysis["nonframe_count"] < 1:
        errors.append("no non-frame object (negative branch absent)")
    if analysis["scene_profile"] is None:
        errors.append("object mix does not match a declared semantic profile")
    if not _components_have_diagonal_moat(analysis["components"]):
        errors.append("foreground objects touch diagonally; one-cell moat is absent")

    transformed = rule_mirror(grid)
    if transformed == grid:
        errors.append("authoritative rule would make no change")
    if not any(3 in row for row in transformed):
        errors.append("authoritative rule leaves no green negative-branch cells")

    requested = None
    if isinstance(meta, dict):
        requested = meta.get("scene_profile")
        if requested is None and isinstance(meta.get("overrides"), dict):
            requested = meta["overrides"].get("scene_profile")
    if requested is not None and analysis["scene_profile"] != requested:
        errors.append(
            f"scene_profile requested {requested!r}, observed {analysis['scene_profile']!r}"
        )
    return errors


def strict_canonical_like(grid: Grid) -> list[str]:
    """Recognize the narrow public-demo envelope, not every valid generated row."""

    reasons = self_check(grid)
    if reasons:
        return reasons
    analysis = analyze_grid(grid)
    if (analysis["height"], analysis["width"]) not in _CANONICAL_DIMS:
        reasons.append("dimensions outside the three public-demo signatures")
    if analysis["scene_profile"] != "canonical_small":
        reasons.append("contains an adversarial non-canonical decoy")
    if not 1 <= analysis["exact_frame_count"] <= 2:
        reasons.append("canonical examples contain one or two exact frames")
    if not 2 <= analysis["component_count"] <= 3:
        reasons.append("canonical examples contain two or three objects")
    for item in analysis["components"]:
        if item["exact_frame"] and (item["height"], item["width"]) not in {
            (3, 3),
            (3, 4),
            (4, 3),
        }:
            reasons.append("frame geometry exceeds the public-demo envelope")
            break
    return reasons


def _paint_matching(grid: Grid, predicate: Callable[[dict], bool]) -> Grid:
    out = [list(row) for row in grid]
    for cells in _components(grid):
        r1, c1, r2, c2 = _bbox(cells)
        item = {
            "cells": cells,
            "size": len(cells),
            "height": r2 - r1 + 1,
            "width": c2 - c1 + 1,
            "exact_frame": _is_rect_outline(cells),
            "hole_count": _hole_count(cells),
            "closed_unbranched_loop": _is_closed_unbranched_loop(cells),
            "rectangular_hole": _has_rectangular_hole(cells),
        }
        if predicate(item):
            for r, c in cells:
                out[r][c] = 7
    return out


def rule_mirror(grid: Grid) -> Grid:
    return _paint_matching(grid, lambda item: item["exact_frame"])


def _rival_any_object_with_hole(grid: Grid) -> Grid:
    return _paint_matching(grid, lambda item: item["hole_count"] > 0)


def _rival_size_at_least_8(grid: Grid) -> Grid:
    return _paint_matching(grid, lambda item: item["size"] >= 8)


def _rival_bbox_at_least_3x3(grid: Grid) -> Grid:
    return _paint_matching(grid, lambda item: item["height"] >= 3 and item["width"] >= 3)


def _rival_closed_unbranched_loop(grid: Grid) -> Grid:
    return _paint_matching(grid, lambda item: item["closed_unbranched_loop"])


def _rival_rectangular_hole(grid: Grid) -> Grid:
    return _paint_matching(grid, lambda item: item["rectangular_hole"])


SEMANTIC_RIVALS = {
    "any_object_with_hole": _rival_any_object_with_hole,
    "size_at_least_8": _rival_size_at_least_8,
    "bbox_at_least_3x3": _rival_bbox_at_least_3x3,
    "closed_unbranched_loop": _rival_closed_unbranched_loop,
    "rectangular_hole": _rival_rectangular_hole,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _is_profile(profile: str) -> Callable[[Grid], bool]:
    def predicate(grid: Grid) -> bool:
        try:
            return observe_overrides(grid)["scene_profile"] == profile
        except (TypeError, ValueError):
            return False

    return predicate


SEMANTIC_WITNESSES = {
    "canonical_small_branch": _is_profile("canonical_small"),
    "large_open_counterexample": _is_profile("large_open"),
    "hollow_irregular_counterexample": _is_profile("hollow_irregular"),
}
BRANCH_WITNESSES = {"canonical_small_branch"}
WITNESS_RIVALS = {
    "large_open_counterexample": ["size_at_least_8", "bbox_at_least_3x3"],
    "hollow_irregular_counterexample": [
        "any_object_with_hole",
        "closed_unbranched_loop",
        "rectangular_hole",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when the demonstrations leave a declared rival alive."""

    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the authoritative rule")

    if isinstance(query, dict) and "input" in query and "output" in query:
        if rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the authoritative rule")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(demo["input"]) == demo["output"] for demo in demos)
        except Exception as exc:  # defensive: report a local contract defect loudly
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons

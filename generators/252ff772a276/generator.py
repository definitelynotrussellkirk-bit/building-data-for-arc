"""Semantic generator for ARC task 252ff772a276.

Find every independent rectangular color-1 outline, count color-2 seeds in
each interior, and select the frame by descending seed count with topmost then
leftmost tie-breaking.  Crop that frame and fill its remaining interior zeros
with green 3, preserving the border and seeds.

Three linked public profiles retain every complete published frame descriptor
tuple.  General profiles expose two/three-frame ranking, both tie directions,
size/count conflicts, malformed-frame filtering, and outside seed distractors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "252ff772a276"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "40bcdf750b85"
SUMMARY = (
    "Select the rectangular 1-frame with most interior 2-seeds, tie-break "
    "topmost then leftmost, crop it, and fill interior zeros with color 3."
)

INVARIANTS = [
    "two or three independent rectangular color-1 outline components",
    "every valid frame is at least 3x3 and contains at least one color-2 seed",
    "ranking is seed count, then top row, then left column",
    "only interior zeros of the chosen crop become color 3",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_test_1",
)
GENERAL_PROFILES = (
    "two_distinct",
    "three_distinct",
    "vertical_tie",
    "horizontal_tie",
    "small_winner",
    "broken_distractor",
    "outside_seed_distractor",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng; three linked public profiles in ten",
        "valid": "|".join(SCENE_PROFILES),
    }
}


# (canvas_h, canvas_w, ((r1, c1, frame_h, frame_w, seed_count), ...))
_PUBLIC_SPECS = {
    "public_train_1": (
        12, 14, ((1, 1, 4, 5, 1), (6, 7, 5, 6, 3))
    ),
    "public_train_2": (
        13, 15, ((1, 2, 5, 5, 2), (7, 8, 4, 5, 1))
    ),
    "public_test_1": (
        14, 16, ((1, 1, 5, 6, 3), (2, 10, 3, 4, 1), (7, 9, 5, 5, 2))
    ),
}


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for neighbor in (
                    (cr - 1, cc),
                    (cr + 1, cc),
                    (cr, cc - 1),
                    (cr, cc + 1),
                ):
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(cells)
    return components


def _frame_from_component(grid, cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    r1, r2 = min(rows), max(rows)
    c1, c2 = min(cols), max(cols)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    if height < 3 or width < 3:
        return None
    border = {
        (row, col)
        for row in range(r1, r2 + 1)
        for col in range(c1, c2 + 1)
        if row in (r1, r2) or col in (c1, c2)
    }
    if set(cells) != border:
        return None
    seed_cells = [
        (row, col)
        for row in range(r1 + 1, r2)
        for col in range(c1 + 1, c2)
        if grid[row][col] == 2
    ]
    return {
        "r1": r1,
        "c1": c1,
        "r2": r2,
        "c2": c2,
        "height": height,
        "width": width,
        "area": height * width,
        "seed_cells": seed_cells,
        "seed_count": len(seed_cells),
    }


def _extract(grid):
    valid = []
    invalid = []
    for component in _components(grid, 1):
        frame = _frame_from_component(grid, component)
        if frame is None:
            invalid.append(component)
        else:
            valid.append(frame)
    valid.sort(key=lambda frame: (frame["r1"], frame["c1"]))
    inside_seeds = {
        cell for frame in valid for cell in frame["seed_cells"]
    }
    all_seeds = {
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 2
    }
    outside_seeds = sorted(all_seeds - inside_seeds)
    chosen = min(
        valid,
        key=lambda frame: (-frame["seed_count"], frame["r1"], frame["c1"]),
    ) if valid else None
    return {
        "frames": valid,
        "invalid_one_components": invalid,
        "outside_seeds": outside_seeds,
        "chosen": chosen,
    }


def _relation_matrix(frames):
    relations = []
    for index, left in enumerate(frames):
        for right in frames[index + 1:]:
            relations.append((
                -1 if left["r1"] < right["r1"] else 0 if left["r1"] == right["r1"] else 1,
                -1 if left["c1"] < right["c1"] else 0 if left["c1"] == right["c1"] else 1,
            ))
    return tuple(relations)


def _linked_signature(grid):
    extracted = _extract(grid)
    if extracted["invalid_one_components"] or extracted["outside_seeds"]:
        return None
    frames = extracted["frames"]
    return (
        len(grid),
        len(grid[0]),
        tuple((f["height"], f["width"], f["seed_count"]) for f in frames),
        _relation_matrix(frames),
        frames.index(extracted["chosen"]) if extracted["chosen"] in frames else None,
    )


def _blank(height, width):
    return [[0 for _ in range(width)] for _ in range(height)]


def _draw_frame(grid, r1, c1, height, width):
    r2, c2 = r1 + height - 1, c1 + width - 1
    for col in range(c1, c2 + 1):
        grid[r1][col] = grid[r2][col] = 1
    for row in range(r1, r2 + 1):
        grid[row][c1] = grid[row][c2] = 1


def _seed_frame(grid, rng, spec):
    r1, c1, height, width, seed_count = spec
    _draw_frame(grid, r1, c1, height, width)
    interior = [
        (row, col)
        for row in range(r1 + 1, r1 + height - 1)
        for col in range(c1 + 1, c1 + width - 1)
    ]
    if len(interior) < seed_count:
        raise ValueError("frame interior cannot hold requested seeds")
    rng.shuffle(interior)
    for row, col in interior[:seed_count]:
        grid[row][col] = 2


def _grid_from_specs(rng, height, width, specs):
    grid = _blank(height, width)
    for spec in specs:
        _seed_frame(grid, rng, spec)
    return grid


_PUBLIC_SIGNATURES = {}
for _profile, (_height, _width, _specs) in _PUBLIC_SPECS.items():
    _ordered_specs = sorted(_specs, key=lambda spec: (spec[0], spec[1]))
    _relations = []
    for _index, _left in enumerate(_ordered_specs):
        for _right in _ordered_specs[_index + 1:]:
            _relations.append((
                -1 if _left[0] < _right[0] else 0 if _left[0] == _right[0] else 1,
                -1 if _left[1] < _right[1] else 0 if _left[1] == _right[1] else 1,
            ))
    _chosen_index = min(
        range(len(_ordered_specs)),
        key=lambda index: (
            -_ordered_specs[index][4],
            _ordered_specs[index][0],
            _ordered_specs[index][1],
        ),
    )
    _signature = (
        _height,
        _width,
        tuple((spec[2], spec[3], spec[4]) for spec in _ordered_specs),
        tuple(_relations),
        _chosen_index,
    )
    if _signature in _PUBLIC_SIGNATURES:
        raise RuntimeError("public profile signatures collide")
    _PUBLIC_SIGNATURES[_signature] = _profile


def canonical_profile_signature(grid):
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
        or any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid)
    ):
        return None
    try:
        return _PUBLIC_SIGNATURES.get(_linked_signature(grid))
    except (IndexError, TypeError, ValueError):
        return None


def _bbox_moat_overlap(first, second, moat=1):
    ar1, ac1, ar2, ac2 = first
    br1, bc1, br2, bc2 = second
    return not (
        ar2 + moat < br1
        or br2 + moat < ar1
        or ac2 + moat < bc1
        or bc2 + moat < ac1
    )


def _analysis(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["empty grid"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["empty grid"]}
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["ragged grid"]}
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1, 2):
                errors.append("input cells must be integer colors 0, 1, or 2")
                break
        if errors:
            break
    if errors:
        return {"errors": errors, "height": height, "width": width, "scene_profile": None}

    extracted = _extract(grid)
    frames = extracted["frames"]
    invalid = extracted["invalid_one_components"]
    outside = extracted["outside_seeds"]
    if len(frames) not in (2, 3):
        errors.append(f"expected 2 or 3 valid frames, got {len(frames)}")
    if any(frame["seed_count"] < 1 for frame in frames):
        errors.append("every valid frame needs at least one interior seed")
    for index, first in enumerate(frames):
        first_box = (first["r1"], first["c1"], first["r2"], first["c2"])
        for second in frames[index + 1:]:
            second_box = (second["r1"], second["c1"], second["r2"], second["c2"])
            if _bbox_moat_overlap(first_box, second_box, moat=1):
                errors.append("valid frames overlap or lack a one-cell moat")

    profile = canonical_profile_signature(grid) if not errors else None
    if not errors and profile is None:
        counts = [frame["seed_count"] for frame in frames]
        maximum = max(counts)
        tied = [frame for frame in frames if frame["seed_count"] == maximum]
        chosen = extracted["chosen"]
        if invalid:
            profile = "broken_distractor"
        elif outside:
            profile = "outside_seed_distractor"
        elif len(tied) > 1:
            profile = (
                "horizontal_tie"
                if len({frame["r1"] for frame in tied}) == 1
                else "vertical_tie"
            )
        elif len(frames) == 3:
            if len(set(counts)) != 3:
                errors.append("three_distinct requires three different seed counts")
            else:
                profile = "three_distinct"
        elif chosen["area"] < min(
            frame["area"] for frame in frames if frame is not chosen
        ):
            profile = "small_winner"
        else:
            profile = "two_distinct"
    if invalid and profile != "broken_distractor" and not errors:
        errors.append("unexpected malformed color-1 component")
    if profile == "broken_distractor" and len(invalid) != 1 and not errors:
        errors.append(f"broken_distractor needs exactly one malformed component, got {len(invalid)}")
    if outside and profile != "outside_seed_distractor" and not errors:
        errors.append("unexpected color-2 seed outside frame interiors")
    if profile not in SCENE_PROFILES and not errors:
        errors.append(f"unrecognized scene profile {profile!r}")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "frames": frames,
        "invalid_one_components": invalid,
        "outside_seeds": outside,
        "chosen": extracted["chosen"],
        "scene_profile": profile,
    }


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    """Independent Python transcription of the canonical Racket rule."""
    extracted = _extract(grid)
    chosen = extracted["chosen"]
    if chosen is None:
        raise ValueError("rule requires at least one rectangular color-1 frame")
    crop = [
        list(grid[row][chosen["c1"]: chosen["c2"] + 1])
        for row in range(chosen["r1"], chosen["r2"] + 1)
    ]
    for row in range(1, len(crop) - 1):
        for col in range(1, len(crop[0]) - 1):
            if crop[row][col] == 0:
                crop[row][col] = 3
    return crop


def _difficulty_dimensions(rng, difficulty):
    if difficulty == "easy":
        return rng.randint(16, 19), rng.randint(19, 23)
    if difficulty == "hard":
        return rng.randint(25, 30), rng.randint(27, 30)
    return rng.randint(20, 25), rng.randint(23, 28)


def _random_specs(rng, height, width, descriptors, *, same_row=False):
    """Place (frame_h, frame_w, seeds) descriptors with a one-cell moat."""
    for _ in range(500):
        specs = []
        boxes = []
        common_row = None
        if same_row:
            maximum_h = max(item[0] for item in descriptors)
            common_row = rng.randint(1, height - maximum_h - 1)
        for frame_h, frame_w, seed_count in descriptors:
            placed = False
            for _ in range(200):
                r1 = common_row if common_row is not None else rng.randint(1, height - frame_h - 1)
                c1 = rng.randint(1, width - frame_w - 1)
                box = (r1, c1, r1 + frame_h - 1, c1 + frame_w - 1)
                if any(_bbox_moat_overlap(box, old, moat=1) for old in boxes):
                    continue
                specs.append((r1, c1, frame_h, frame_w, seed_count))
                boxes.append(box)
                placed = True
                break
            if not placed:
                break
        if len(specs) == len(descriptors):
            return specs
    raise RuntimeError("could not place separated frames")


def _add_broken_distractor(grid, rng):
    height, width = len(grid), len(grid[0])
    occupied = {(row, col) for row in range(height) for col in range(width) if grid[row][col]}
    for _ in range(500):
        row = rng.randint(1, height - 3)
        col = rng.randint(1, width - 3)
        cells = {(row, col), (row + 1, col), (row + 1, col + 1)}
        moat = {
            (rr, cc)
            for rr in range(row - 1, row + 3)
            for cc in range(col - 1, col + 3)
        }
        if not (moat & occupied):
            for rr, cc in cells:
                grid[rr][cc] = 1
            return
    raise RuntimeError("could not place broken frame distractor")


def _add_outside_seeds(grid, rng):
    frames = _extract(grid)["frames"]
    def inside_frame(row, col):
        return any(
            frame["r1"] < row < frame["r2"]
            and frame["c1"] < col < frame["c2"]
            for frame in frames
        )
    zeros = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 0 and not inside_frame(row, col)
    ]
    rng.shuffle(zeros)
    for row, col in zeros[:rng.randint(1, 3)]:
        grid[row][col] = 2


def _general_grid(rng, difficulty, profile):
    height, width = _difficulty_dimensions(rng, difficulty)
    if profile == "two_distinct":
        descriptors = ((5, 6, 1), (6, 7, 3))
        specs = _random_specs(rng, height, width, descriptors)
    elif profile == "three_distinct":
        descriptors = ((4, 5, 1), (5, 6, 2), (6, 7, 3))
        specs = _random_specs(rng, height, width, descriptors)
    elif profile == "vertical_tie":
        descriptors = ((4, 6, 3), (6, 5, 3))
        specs = _random_specs(rng, height, width, descriptors)
        if specs[0][0] == specs[1][0]:
            specs[1] = (min(height - specs[1][2] - 1, specs[1][0] + 1), *specs[1][1:])
            first_box = (specs[0][0], specs[0][1], specs[0][0] + specs[0][2] - 1, specs[0][1] + specs[0][3] - 1)
            second_box = (specs[1][0], specs[1][1], specs[1][0] + specs[1][2] - 1, specs[1][1] + specs[1][3] - 1)
            if _bbox_moat_overlap(first_box, second_box, moat=1):
                return _general_grid(rng, difficulty, profile)
    elif profile == "horizontal_tie":
        descriptors = ((4, 5, 3), (5, 6, 3))
        specs = _random_specs(rng, height, width, descriptors, same_row=True)
    elif profile == "small_winner":
        descriptors = ((3, 5, 3), (7, 8, 1))
        specs = _random_specs(rng, height, width, descriptors)
    else:
        descriptors = ((5, 6, 1), (6, 7, 3))
        specs = _random_specs(rng, height, width, descriptors)
    grid = _grid_from_specs(rng, height, width, specs)
    if profile == "broken_distractor":
        _add_broken_distractor(grid, rng)
    elif profile == "outside_seed_distractor":
        _add_outside_seeds(grid, rng)
    info = _analysis(grid)
    if info["errors"] or info["scene_profile"] != profile:
        return _general_grid(rng, difficulty, profile)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = context.draw_choice("scene_profile", list(SCENE_PROFILES))
    rng = context.draw_rng("scene")
    if profile in PUBLIC_PROFILES:
        height, width, specs = _PUBLIC_SPECS[profile]
        grid = _grid_from_specs(rng, height, width, specs)
    else:
        grid = _general_grid(rng, difficulty, profile)
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile} -> {observed}")
    return [row[:] for row in grid]


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed grids and nearest frame/ranking/profile impostors."""
    info = _analysis(grid)
    errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested:
            errors.append(
                f"requested scene_profile {requested}, observed {info['scene_profile']}"
            )
    if not errors:
        output = rule_mirror(grid)
        chosen = info["chosen"]
        if (len(output), len(output[0])) != (chosen["height"], chosen["width"]):
            errors.append("rule mirror emitted the wrong crop dimensions")
        if any(value != 1 for value in output[0] + output[-1]):
            errors.append("rule mirror failed to preserve horizontal border")
        for row in range(1, len(output) - 1):
            if output[row][0] != 1 or output[row][-1] != 1:
                errors.append("rule mirror failed to preserve vertical border")
                break
            if any(value not in (2, 3) for value in output[row][1:-1]):
                errors.append("chosen interior must contain only preserved seeds and green fill")
                break
    return errors

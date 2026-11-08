"""Task-specific generator for ecd1f88fc6d3: coded directed colour rays.

Direction-marker colours 1/2/3/4 mean up/down/left/right.  A marker fires only
when the cell immediately behind it contains a seed colour 5..9.  The output is
a fresh zero grid: each firing paints the seed cell, marker cell, and every cell
from there to the boundary with the seed colour.  Non-triggering markers vanish,
and a ray does not stop when it crosses another input marker.

The four scheduled scene profiles form a small, explicit curriculum with
randomized nonintersecting emitter positions:

* ``canonical_small`` reproduces the canonical right+down pairing on 7x7.
* ``canonical_medium`` reproduces the canonical up+left pairing on 8x8.
* ``canonical_distractor`` reproduces the 9x9 test's isolated marker and a
  non-triggering colour that an active ray must overwrite.
* ``direction_sweep`` exercises all four direction codes in one lawful scene.

Distractor scenes also include a wrong-side code adjacent to a seed. Geometry
alone therefore cannot replace the numerical direction code.

All profiles fit every declared 7..9 boundary override.  Their direction sets
and distractor counts are intentionally observable, so ``scene_profile`` is an
honest exact override rather than hidden metadata.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ecd1f88fc6d3"
TASK_ID = GENERATOR_ID
VERSION = "5.0.0"
RULE_HASH = "16da73149c81"

SUMMARY = (
    "A 0-background grid contains adjacent seed+direction emitter pairs. "
    "Codes 1/2/3/4 point up/down/left/right; when the cell behind a code is a "
    "colour 5..9, that seed colour is painted from the seed through the code "
    "to the boundary on a fresh output grid. Isolated markers disappear and "
    "rays pass through unrelated input markers."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

INVARIANTS = [
    "input dimensions are 7..9 in both axes and the background is 0",
    "every active emitter is a colour 5..9 immediately behind a code 1..4",
    "the output starts blank and contains only full seed-to-boundary rays",
    "non-triggering code/colour distractors vanish unless overwritten by a ray",
    "all four direction meanings occur in the scheduled curriculum",
    "active rays never intersect, so overwrite precedence is not taught",
    "every scheduled distractor scene refutes geometry-only direction inference",
]

# direction name -> (code value, ray delta)
DIRS: dict[str, tuple[int, tuple[int, int]]] = {
    "up": (1, (-1, 0)),
    "down": (2, (1, 0)),
    "left": (3, (0, -1)),
    "right": (4, (0, 1)),
}
CODE_TO_DIRECTION = {code: (name, delta) for name, (code, delta) in DIRS.items()}
COLORS = (5, 6, 7, 8, 9)

SCHEDULE_PROFILES = (
    "canonical_small",
    "canonical_medium",
    "canonical_distractor",
    "direction_sweep",
)
# Every length-3 sliding window contains a distractor counterexample while the
# first three residues retain the exact 7x7, 8x8, 9x9 canonical profiles.
_CURRICULUM_SEQUENCE = (
    "canonical_small",
    "canonical_medium",
    "canonical_distractor",
    "direction_sweep",
    "canonical_small",
    "canonical_distractor",
)

_PROFILE_DEFAULT_SIZE = {
    "canonical_small": (7, 7),
    "canonical_medium": (8, 8),
    "canonical_distractor": (9, 9),
    "direction_sweep": (9, 9),
}
_PROFILE_PALETTE_SIZE = {
    "canonical_small": 5,
    "canonical_medium": 5,
    "canonical_distractor": 7,
    "direction_sweep": 9,
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled 7|8|9|9",
        "valid": "7..9",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled 7|8|9|9",
        "valid": "7..9",
    },
    "scene_profile": {
        "type": "str",
        "default": "six-residue curriculum (see schedule_profile)",
        "valid": "canonical_small|canonical_medium|canonical_distractor|direction_sweep",
    },
}

# Profile names retain the public dimension/palette/direction signatures, not
# fixed spatial coordinates. Position is nuisance variation, not an override.
_PROFILE_DIRECTIONS: dict[str, tuple[str, ...]] = {
    "canonical_small": ("right", "down"),
    "canonical_medium": ("up", "left"),
    "canonical_distractor": ("up", "left"),
    "direction_sweep": ("up", "down", "left", "right"),
}
_LAYOUT_ATTEMPTS = 128


def _sample_layout(rng, profile: str, h: int, w: int, palette: list[int]):
    """Bounded constructive sampling; no fixed-template fallback.

    Enumerate legal seed positions, then choose nonintersecting full rays.
    Rebuild when a greedy placement cannot complete. A distractor is placed
    on an existing ray; a wrong-side code is placed outside every active ray
    next to a seed. This latter code must have no seed to its left (code 4).
    """
    directions = _PROFILE_DIRECTIONS[profile]
    options = {}
    for direction in directions:
        _, (dr, dc) = DIRS[direction]
        minimum = 3 if profile == "canonical_distractor" and direction == "up" else 2
        options[direction] = [
            (r, c, _ray_cells(r, c, (dr, dc), h, w))
            for r in range(h) for c in range(w)
            if 0 <= r + dr < h and 0 <= c + dc < w
            and len(_ray_cells(r, c, (dr, dc), h, w)) >= minimum
        ]
    for _ in range(_LAYOUT_ATTEMPTS):
        grid = full_grid(h, w, 0)
        occupied: set[tuple[int, int]] = set()
        emitters = []
        # Sampling emitter order avoids always reserving the up/right ray first.
        order = list(enumerate(directions))
        rng.shuffle(order)
        for index, direction in order:
            candidates = [item for item in options[direction]
                          if not occupied.intersection(item[2])]
            if not candidates:
                break
            r, c, ray = rng.choice(candidates)
            _place_emitter(grid, direction, (r, c), palette[index])
            occupied.update(ray)
            emitters.append((r, c, ray))
        if len(emitters) != len(directions):
            continue
        if profile != "canonical_distractor":
            return grid

        colour_cells = [cell for _, _, ray in emitters for cell in ray[2:]
                        if grid[cell[0]][cell[1]] == 0]
        if not colour_cells:
            continue
        r, c = rng.choice(colour_cells)
        grid[r][c] = palette[-1]
        seed_cells = [(sr, sc) for sr, sc, _ in emitters] + [(r, c)]
        wrong_side = set()
        for sr, sc in seed_cells:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = sr + dr, sc + dc
                if (0 <= rr < h and 0 <= cc < w
                        and (rr, cc) not in occupied
                        and grid[rr][cc] == 0
                        and (cc == 0 or grid[rr][cc - 1] not in COLORS)):
                    wrong_side.add((rr, cc))
        if not wrong_side:
            continue
        # Sorting makes replay independent of set iteration order/hash seed.
        rr, cc = rng.choice(sorted(wrong_side))
        grid[rr][cc] = DIRS["right"][0]
        return grid
    raise RuntimeError(
        f"could not construct {profile} on {h}x{w} in {_LAYOUT_ATTEMPTS} attempts"
    )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic curriculum residue used by the semantic gate."""
    del seed
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return _CURRICULUM_SEQUENCE[int(sample_index) % len(_CURRICULUM_SEQUENCE)]


def _validate_override_names(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")


def _draw_default_int(ctx, overrides: dict[str, Any], label: str,
                      default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_default_choice(ctx, overrides: dict[str, Any], label: str,
                         default: str, options: tuple[str, ...]) -> str:
    if label in overrides and overrides[label] is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (default,)))


def _place_emitter(grid: list[list[int]], direction: str, seed: tuple[int, int],
                   colour: int) -> None:
    code, (dr, dc) = DIRS[direction]
    sr, sc = seed
    grid[sr][sc] = colour
    grid[sr + dr][sc + dc] = code


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, task-lawful input grid."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    _validate_override_names(overrides)
    # Match GenCtx: a known key with None means no override, not literal None.
    overrides = {name: value for name, value in overrides.items() if value is not None}

    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    default_profile = str(overrides.get("scene_profile", scheduled_profile))
    if default_profile not in SCHEDULE_PROFILES:
        raise ValueError(f"unknown scene_profile: {default_profile!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _draw_default_choice(
        ctx, overrides, "scene_profile", scheduled_profile, SCHEDULE_PROFILES
    )
    default_h, default_w = _PROFILE_DEFAULT_SIZE[profile]
    h = _draw_default_int(ctx, overrides, "grid_h", default_h, 7, 9)
    w = _draw_default_int(ctx, overrides, "grid_w", default_w, 7, 9)

    layout_rng = ctx.draw_rng(f"layout:{difficulty or 'all'}:{profile}")
    colour_count = len(_PROFILE_DIRECTIONS[profile]) + (
        1 if profile == "canonical_distractor" else 0
    )
    palette = list(
        ctx.draw_distinct_colors(
            "emitter_palette", n=colour_count, exclude={0, 1, 2, 3, 4}
        )
    )
    layout_rng.shuffle(palette)
    grid = _sample_layout(layout_rng, profile, h, w, palette)

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise AssertionError("generated invalid directed-ray input: " + "; ".join(errors))
    return grid


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["input must be a non-empty list of rows"]
    if any(not isinstance(row, list) for row in grid):
        return ["every row must be a list"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["input must be a non-empty rectangular grid"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["cells must be integer ARC colours 0..9"]
    return []


def _ray_cells(seed_r: int, seed_c: int, delta: tuple[int, int],
               h: int, w: int) -> list[tuple[int, int]]:
    dr, dc = delta
    cells: list[tuple[int, int]] = []
    r, c = seed_r, seed_c
    while 0 <= r < h and 0 <= c < w:
        cells.append((r, c))
        r += dr
        c += dc
    return cells


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _basic_grid_errors(grid)
    if errors:
        return {
            "errors": errors,
            "emitters": [],
            "untriggered_markers": [],
            "scene_profile": None,
        }

    h, w = len(grid), len(grid[0])
    emitters: list[dict[str, Any]] = []
    active_marker_cells: set[tuple[int, int]] = set()
    for r in range(h):
        for c in range(w):
            code = grid[r][c]
            if code not in CODE_TO_DIRECTION:
                continue
            direction, (dr, dc) = CODE_TO_DIRECTION[code]
            seed_r, seed_c = r - dr, c - dc
            if not (0 <= seed_r < h and 0 <= seed_c < w):
                continue
            colour = grid[seed_r][seed_c]
            if colour not in COLORS:
                continue
            ray = _ray_cells(seed_r, seed_c, (dr, dc), h, w)
            emitters.append({
                "direction": direction,
                "code": code,
                "code_cell": (r, c),
                "seed_cell": (seed_r, seed_c),
                "colour": colour,
                "ray": ray,
            })
            active_marker_cells.add((r, c))
            active_marker_cells.add((seed_r, seed_c))

    marker_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    untriggered = sorted(marker_cells - active_marker_cells)
    direction_names = sorted(item["direction"] for item in emitters)
    profile: str | None = None
    if len(emitters) == 2 and not untriggered and direction_names == ["down", "right"]:
        profile = "canonical_small"
    elif len(emitters) == 2 and not untriggered and direction_names == ["left", "up"]:
        profile = "canonical_medium"
    elif (len(emitters) == 2 and len(untriggered) == 2
          and direction_names == ["left", "up"]):
        profile = "canonical_distractor"
    elif (len(emitters) == 4 and not untriggered
          and direction_names == ["down", "left", "right", "up"]):
        profile = "direction_sweep"

    return {
        "errors": [],
        "height": h,
        "width": w,
        "emitters": emitters,
        "untriggered_markers": untriggered,
        "scene_profile": profile,
        "palette_size": len({value for row in grid for value in row}),
    }


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned grid."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(facts["errors"]))
    if facts["scene_profile"] is None:
        raise ValueError("grid does not match a declared scene_profile")
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "scene_profile": facts["scene_profile"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the generated/canonical input grammar and exact overrides."""
    del difficulty
    facts = _analyze(grid)
    errors = list(facts["errors"])
    if errors:
        return errors

    h, w = facts["height"], facts["width"]
    if not 7 <= h <= 9 or not 7 <= w <= 9:
        errors.append(f"grid dimensions must each be 7..9, got {h}x{w}")
    profile = facts["scene_profile"]
    if profile is None:
        errors.append("marker arrangement does not match a declared lawful scene profile")
        return errors
    expected_palette = _PROFILE_PALETTE_SIZE[profile]
    if facts["palette_size"] != expected_palette:
        errors.append(
            f"{profile} must use palette size {expected_palette}, "
            f"got {facts['palette_size']}"
        )

    # Active emitter marker cells must be pairwise distinct; otherwise one cell
    # silently participates in multiple rules and the profile signature lies.
    active_cells = [
        cell
        for emitter in facts["emitters"]
        for cell in (emitter["seed_cell"], emitter["code_cell"])
    ]
    if len(active_cells) != len(set(active_cells)):
        errors.append("active emitters must not share seed or code cells")

    ray_sets = [set(emitter["ray"]) for emitter in facts["emitters"]]
    if any(left & right for index, left in enumerate(ray_sets)
           for right in ray_sets[index + 1:]):
        errors.append("active rays must not intersect (overwrite precedence is excluded)")

    if profile == "canonical_distractor":
        output = rule_mirror(grid)
        overwritten = [
            (r, c) for r, c in facts["untriggered_markers"]
            if output[r][c] not in (0, grid[r][c])
        ]
        vanished = [
            (r, c) for r, c in facts["untriggered_markers"]
            if output[r][c] == 0
        ]
        if not overwritten:
            errors.append("distractor profile needs a marker overwritten by a ray")
        if not vanished:
            errors.append("distractor profile needs an isolated marker that vanishes")

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = {name: candidate[name] for name in AXES
                         if name in candidate and candidate[name] is not None}
    if requested:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if observed[name] != value:
                errors.append(
                    f"override {name}={value!r} realized as {observed[name]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All generated profiles and all three public inputs are lawful."""
    return self_check(grid)


def _paint_rays(grid, *, start_at_code: bool = False,
                use_code_colour: bool = False,
                stop_at_marker: bool = False) -> list[list[int]]:
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    # Match the canonical Racket program's row-major code scan and overwrite
    # order exactly.
    for r in range(h):
        for c in range(w):
            code = grid[r][c]
            info = CODE_TO_DIRECTION.get(code)
            if info is None:
                continue
            _, (dr, dc) = info
            seed_r, seed_c = r - dr, c - dc
            if not (0 <= seed_r < h and 0 <= seed_c < w):
                continue
            colour = grid[seed_r][seed_c]
            if colour not in COLORS:
                continue
            paint = code if use_code_colour else colour
            rr, cc = (r, c) if start_at_code else (seed_r, seed_c)
            first = True
            while 0 <= rr < h and 0 <= cc < w:
                if (stop_at_marker and not first and (rr, cc) != (r, c)
                        and grid[rr][cc] != 0):
                    break
                output[rr][cc] = paint
                first = False
                rr += dr
                cc += dc
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror; the canonical Racket program is authority."""
    return _paint_rays(grid)


def _rival_omit_seed(grid) -> list[list[int]]:
    return _paint_rays(grid, start_at_code=True)


def _rival_use_code_colour(grid) -> list[list[int]]:
    return _paint_rays(grid, use_code_colour=True)


def _rival_preserve_untriggered(grid) -> list[list[int]]:
    output = rule_mirror(grid)
    for r, c in _analyze(grid)["untriggered_markers"]:
        output[r][c] = grid[r][c]
    return output


def _rival_stop_at_marker(grid) -> list[list[int]]:
    return _paint_rays(grid, stop_at_marker=True)


def _rival_ignore_direction_codes(grid) -> list[list[int]]:
    """Wrong but canonically plausible: infer direction only from adjacency."""
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for r in range(h):
        for c in range(w):
            if grid[r][c] not in (1, 2, 3, 4):
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                sr, sc = r - dr, c - dc
                if not (0 <= sr < h and 0 <= sc < w and grid[sr][sc] in COLORS):
                    continue
                rr, cc = sr, sc
                while 0 <= rr < h and 0 <= cc < w:
                    output[rr][cc] = grid[sr][sc]
                    rr += dr
                    cc += dc
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "omit_seed_cell": _rival_omit_seed,
    "paint_with_direction_code": _rival_use_code_colour,
    "preserve_untriggered_markers": _rival_preserve_untriggered,
    "stop_ray_at_input_marker": _rival_stop_at_marker,
    "ignore_direction_codes": _rival_ignore_direction_codes,
}

# The curriculum schedule guarantees that every three-demo window includes a
# distractor scene, so all five declared alternatives are actually refuted by
# every generated lesson rather than merely named by isolated witnesses.
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _has_direction(grid, direction: str) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and any(
        item["direction"] == direction for item in facts["emitters"]
    )


def _has_untriggered_markers(grid) -> bool:
    facts = _analyze(grid)
    return not facts["errors"] and bool(facts["untriggered_markers"])


def _ray_crosses_input_marker(grid) -> bool:
    facts = _analyze(grid)
    if facts["errors"]:
        return False
    active_cells = {
        cell
        for emitter in facts["emitters"]
        for cell in (emitter["seed_cell"], emitter["code_cell"])
    }
    for emitter in facts["emitters"]:
        for r, c in emitter["ray"]:
            if (r, c) not in active_cells and grid[r][c] != 0:
                return True
    return False


def _has_wrong_side_marker(grid) -> bool:
    facts = _analyze(grid)
    if facts["errors"]:
        return False
    h, w = facts["height"], facts["width"]
    output = rule_mirror(grid)
    return any(
        grid[r][c] in (1, 2, 3, 4) and output[r][c] == 0
        and any(0 <= r + dr < h and 0 <= c + dc < w
                and grid[r + dr][c + dc] in COLORS
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
        for r, c in facts["untriggered_markers"]
    )


def _lawful_with_emitter(grid) -> bool:
    facts = _analyze(grid)
    return not self_check(grid) and bool(facts["emitters"])


SEMANTIC_WITNESSES = {
    "direction_up": lambda grid: _has_direction(grid, "up"),
    "direction_down": lambda grid: _has_direction(grid, "down"),
    "direction_left": lambda grid: _has_direction(grid, "left"),
    "direction_right": lambda grid: _has_direction(grid, "right"),
    "ray_includes_seed": _lawful_with_emitter,
    "uses_seed_colour": _lawful_with_emitter,
    "untriggered_markers_vanish": _has_untriggered_markers,
    "ray_crosses_input_marker": _ray_crosses_input_marker,
    "wrong_side_marker_ignored": _has_wrong_side_marker,
}
BRANCH_WITNESSES = {
    "direction_up",
    "direction_down",
    "direction_left",
    "direction_right",
}
WITNESS_RIVALS = {
    "ray_includes_seed": ["omit_seed_cell"],
    "uses_seed_colour": ["paint_with_direction_code"],
    "untriggered_markers_vanish": ["preserve_untriggered_markers"],
    "ray_crosses_input_marker": ["stop_ray_at_input_marker"],
    "wrong_side_marker_ignored": ["ignore_direction_codes"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Name any declared rival that fits every demo but changes the query."""
    if not demos:
        return ["lesson has no demonstrations"]
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} fits every demo but changes the query answer"
            )
    return reasons

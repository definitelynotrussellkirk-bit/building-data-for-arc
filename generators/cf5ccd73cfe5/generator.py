"""Generator for 6b9890af.

Rule: find the hollow rectangular frame and the separate marker.  Repeat each
marker row and column independently so the marker's bounding box fills the
frame interior, preserving the frame as the output border.

The ordinary distribution deliberately includes non-square markers, unequal
height/width scales, sparse connected and disconnected markers, four placement
orientations, and several palette families.  Exact dimension and semantic
axis overrides are honored when jointly feasible and rejected loudly when a
combination cannot fit.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cf5ccd73cfe5"
VERSION = "3.1.0"
TASK_ID = "cf5ccd73cfe5"
RULE_HASH = "50b927c3200b"  # whitespace-normalized canonical program_solution
SUMMARY = (
    "Scale a separate marker's binary shape independently in height and width "
    "to fill a hollow rectangular frame interior."
)

INVARIANTS = [
    "background is color 0",
    "exactly one hollow rectangular frame is present",
    "exactly one non-frame marker color is present outside the frame",
    "frame interior dimensions are integer multiples of marker bbox dimensions",
    "ordinary draws keep marker and frame spatially separate",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
PALETTES = {
    "warm": (2, 3, 4, 6, 7, 9),
    "cool": (1, 5, 8),
    "broad": tuple(range(1, 10)),
    "primary": (1, 2, 4),
}
DEGENERATE_TEXTURES = ("no_frame", "no_marker", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS
CANONICAL_PROFILES = ((19, 22), (18, 21), (21, 24), (24, 26))
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("rich_a", "rich_b", "canonical_anchor", "broad")
MIN_STRICT_FRAC = 0.20

AXES = {
    "grid_h": {
        "type": "int",
        "default": "rng exact after semantic-layout feasibility",
        "valid": "8..26",
    },
    "grid_w": {
        "type": "int",
        "default": "rng exact after semantic-layout feasibility",
        "valid": "8..26",
    },
    "marker_h": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "marker_w": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "scale_h": {"type": "int", "default": "difficulty-aware 1..4", "valid": "1..4"},
    "scale_w": {"type": "int", "default": "difficulty-aware 1..4", "valid": "1..4"},
    "palette_kind": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(PALETTE_KINDS),
    },
}


def _record_exact_axis(ctx, label: str, value: int, lo: int, hi: int) -> int:
    """Record a jointly selected exact axis in the same provenance map as draws.

    The semantic dimensions are chosen together so unrelated random draws cannot
    defeat a valid boundary request. Record the feasible choice through the
    public strict draw API using its selected singleton interval.
    """
    if not lo <= value <= hi:
        raise ValueError(f"selected {label} outside [{lo}, {hi}]")
    return ctx.draw_int_strict(label, value, value)


def _marker(rng, mh: int, mw: int) -> list[tuple[int, int]]:
    """Return a marker with exact bbox ``mh x mw``.

    Whenever the bbox has more than two cells, ordinary shapes are non-solid so
    the input contains evidence against the shortcut "fill the whole frame".
    Both connected and disconnected patterns remain possible because the Racket
    rule consumes the complete non-frame cell set rather than one component.
    """
    area = mh * mw
    if area <= 2:
        return [(r, c) for r in range(mh) for c in range(mw)]

    for _ in range(300):
        cells = [
            (r, c)
            for r in range(mh)
            for c in range(mw)
            if rng.random() < 0.58
        ]
        if not cells or len(cells) == area:
            continue
        rows = {r for r, _ in cells}
        cols = {c for _, c in cells}
        if {0, mh - 1} <= rows and {0, mw - 1} <= cols:
            return cells

    # Sparse, exact-bbox fallback.  Duplicate corners collapse naturally for a
    # one-dimensional bbox.
    return sorted({(0, 0), (mh - 1, mw - 1)})


def _frame_candidates(grid: list[list[int]]) -> list[dict]:
    h, w = len(grid), len(grid[0])
    candidates = []
    for color in sorted({v for row in grid for v in row if v != 0}):
        cells = {
            (r, c)
            for r in range(h)
            for c in range(w)
            if grid[r][c] == color
        }
        r1 = min(r for r, _ in cells)
        r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        c2 = max(c for _, c in cells)
        if r2 - r1 < 3 or c2 - c1 < 3:
            continue
        perimeter = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)
        }
        if cells == perimeter:
            candidates.append(
                {
                    "color": color,
                    "bbox": (r1, c1, r2, c2),
                    "height": r2 - r1 + 1,
                    "width": c2 - c1 + 1,
                }
            )
    return candidates


def _analyze(grid) -> tuple[dict | None, list[str]]:
    """Parse the task grammar used by ``self_check`` and override evidence."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return None, ["empty grid"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return None, ["ragged grid"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None, ["cell value out of 0-9"]

    nonzero = {value for row in grid for value in row if value != 0}
    if len(nonzero) != 2:
        return None, [f"expected exactly two nonzero colors, found {len(nonzero)}"]

    frames = _frame_candidates(grid)
    if len(frames) != 1:
        return None, [f"expected exactly one hollow rectangular frame, found {len(frames)}"]
    frame = frames[0]
    frame_color = frame["color"]
    marker_colors = nonzero - {frame_color}
    if len(marker_colors) != 1:
        return None, ["could not identify one marker color distinct from the frame"]
    marker_color = next(iter(marker_colors))
    marker_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == marker_color
    ]
    if not marker_cells:
        return None, ["marker is empty"]

    mr1 = min(r for r, _ in marker_cells)
    mr2 = max(r for r, _ in marker_cells)
    mc1 = min(c for _, c in marker_cells)
    mc2 = max(c for _, c in marker_cells)
    marker_h = mr2 - mr1 + 1
    marker_w = mc2 - mc1 + 1
    fr1, fc1, fr2, fc2 = frame["bbox"]
    if any(fr1 <= r <= fr2 and fc1 <= c <= fc2 for r, c in marker_cells):
        return None, ["marker overlaps the frame bounding box"]

    interior_h = frame["height"] - 2
    interior_w = frame["width"] - 2
    if interior_h % marker_h or interior_w % marker_w:
        return None, [
            "frame interior dimensions are not integer multiples of marker bbox dimensions"
        ]
    scale_h = interior_h // marker_h
    scale_w = interior_w // marker_w
    if scale_h < 1 or scale_w < 1:
        return None, ["non-positive marker scale"]

    return {
        "grid_h": len(grid),
        "grid_w": width,
        "frame_color": frame_color,
        "marker_color": marker_color,
        "frame_bbox": frame["bbox"],
        "frame_h": frame["height"],
        "frame_w": frame["width"],
        "marker_bbox": (mr1, mc1, mr2, mc2),
        "marker_h": marker_h,
        "marker_w": marker_w,
        "marker_cells": len(marker_cells),
        "scale_h": scale_h,
        "scale_w": scale_w,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes outside the exact frame-plus-marker teaching grammar."""
    _facts, errors = _analyze(grid)
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact semantic axis from a returned grid."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        key: facts[key]
        for key in ("grid_h", "grid_w", "marker_h", "marker_w", "scale_h", "scale_w")
    }


def _effective_overrides(overrides: dict) -> tuple[dict, str | None]:
    unknown = set(overrides) - (set(AXES) | {"texture"})
    if unknown:
        raise ValueError(f"unknown override keys: {sorted(unknown)}")
    for name, bounds in (
        ("grid_h", (8, 26)), ("grid_w", (8, 26)),
        ("marker_h", (1, 3)), ("marker_w", (1, 3)),
        ("scale_h", (1, 4)), ("scale_w", (1, 4)),
    ):
        value = overrides.get(name)
        if value is not None:
            if type(value) is not int:
                raise ValueError(f"{name} override must be an integer, not {type(value).__name__}")
            if not bounds[0] <= value <= bounds[1]:
                raise ValueError(f"{name} override {value} outside {bounds}")
    effective = dict(overrides)
    texture = effective.pop("texture", None)
    if texture is None:
        return effective, None
    if texture in DEGENERATE_TEXTURES:
        return effective, texture
    if texture not in HELPFUL_TEXTURES:
        raise ValueError(f"unknown texture {texture!r}")
    explicit_palette = effective.get("palette_kind")
    if explicit_palette is not None and explicit_palette != texture:
        raise ValueError(
            f"texture={texture!r} conflicts with palette_kind={explicit_palette!r}"
        )
    effective["palette_kind"] = texture
    return effective, None


def _semantic_candidates(difficulty: str | None, overrides: dict) -> list[tuple[int, int, int, int, str, int, int]]:
    requested_h = overrides.get("grid_h")
    requested_w = overrides.get("grid_w")
    for name, value in (("grid_h", requested_h), ("grid_w", requested_w)):
        if value is not None and not 8 <= int(value) <= 26:
            raise ValueError(f"{name} override {value} outside [8, 26]")

    candidates = []
    for mh in range(1, 4):
        if overrides.get("marker_h") is not None and mh != int(overrides["marker_h"]):
            continue
        for mw in range(1, 4):
            if overrides.get("marker_w") is not None and mw != int(overrides["marker_w"]):
                continue
            # The 1x1 marker makes every output a solid fill and does not teach
            # shape scaling; reject that jointly incompatible axis tuple.
            if mh == mw == 1:
                continue
            # Ordinary draws avoid the only other forced-solid bbox sizes.
            if not any(overrides.get(name) is not None for name in ("marker_h", "marker_w")):
                if mh * mw <= 2:
                    continue
            for sh in range(1, 5):
                if overrides.get("scale_h") is not None and sh != int(overrides["scale_h"]):
                    continue
                if mh * sh < 2:
                    continue
                if difficulty == "easy" and overrides.get("scale_h") is None and sh > 2:
                    continue
                if difficulty == "hard" and overrides.get("scale_h") is None and sh < 2:
                    continue
                for sw in range(1, 5):
                    if overrides.get("scale_w") is not None and sw != int(overrides["scale_w"]):
                        continue
                    if mw * sw < 2:
                        continue
                    if difficulty == "easy" and overrides.get("scale_w") is None and sw > 2:
                        continue
                    if difficulty == "hard" and overrides.get("scale_w") is None and sw < 2:
                        continue

                    frame_h = mh * sh + 2
                    frame_w = mw * sw + 2
                    layouts = (
                        ("below", frame_h + 1 + mh, max(frame_w, mw)),
                        ("right", max(frame_h, mh), frame_w + 1 + mw),
                    )
                    for layout, min_h, min_w in layouts:
                        if max(8, min_h) > 26 or max(8, min_w) > 26:
                            continue
                        if requested_h is not None and int(requested_h) < max(8, min_h):
                            continue
                        if requested_w is not None and int(requested_w) < max(8, min_w):
                            continue
                        candidates.append((mh, mw, sh, sw, layout, min_h, min_w))
    return candidates


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    effective, degenerate = _effective_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    rng = ctx.draw_rng("layout")
    if degenerate is not None:
        return _draw_from_degenerate(degenerate, rng)

    unconstrained = not any(value is not None for value in effective.values())
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    rich = unconstrained and phase in (0, 1)
    anchor = unconstrained and phase == 2
    palette_options = tuple(kind for kind in PALETTE_KINDS if 2 in PALETTES[kind]) if anchor else PALETTE_KINDS
    palette_kind = ctx.draw_choice("palette_kind", palette_options)
    candidates = _semantic_candidates(difficulty, effective)
    if not candidates:
        exact = {key: effective[key] for key in AXES if effective.get(key) is not None}
        raise ValueError(f"incompatible exact override combination: {exact}")

    # Two rich pairs in every four-index window keep at least one witness in
    # every three-demo query rotation. Exact overrides disable this schedule.
    scheduled = candidates
    if rich:
        scheduled = [candidate for candidate in candidates
                     if candidate[0] > 1 and candidate[1] > 1
                     and candidate[0] != candidate[1]
                     and candidate[2] != candidate[3]
                     and candidate[0] * candidate[2] != candidate[1] * candidate[3]
                     and _rich_marker_choices(*candidate[:4])]
    elif anchor:
        scheduled = [
            candidate
            for candidate in candidates
            if candidate[0] == candidate[1] == 3 and candidate[2] == candidate[3]
        ]
    if not scheduled:
        raise RuntimeError("ordinary lesson schedule has no feasible semantic tuple")

    semantic_rng = ctx.draw_rng("semantic_spec")
    mh, mw, sh, sw, layout, min_h, min_w = semantic_rng.choice(scheduled)
    _record_exact_axis(ctx, "marker_h", mh, 1, 3)
    _record_exact_axis(ctx, "marker_w", mw, 1, 3)
    _record_exact_axis(ctx, "scale_h", sh, 1, 4)
    _record_exact_axis(ctx, "scale_w", sw, 1, 4)

    if unconstrained and phase in (0, 2):
        profiles = [(h, w) for h, w in CANONICAL_PROFILES if h >= min_h and w >= min_w]
        h, w = ctx.draw_rng("canonical_profile").choice(profiles)
        _record_exact_axis(ctx, "grid_h", h, 8, 26)
        _record_exact_axis(ctx, "grid_w", w, 8, 26)
    else:
        h = ctx.draw_int_strict("grid_h", max(8, min_h), 26)
        w = ctx.draw_int_strict("grid_w", max(8, min_w), 26)
    frame_h = mh * sh + 2
    frame_w = mw * sw + 2
    marker = (_rich_marker(ctx.draw_rng("marker_shape"), mh, mw, sh, sw)
              if rich else _marker(ctx.draw_rng("marker_shape"), mh, mw))

    palette = PALETTES[palette_kind]
    if len(palette) < 2:
        raise ValueError(f"palette {palette_kind!r} has fewer than two colors")
    colors_rng = ctx.draw_rng("colors")
    if anchor:
        frame_color = 2
        marker_color = colors_rng.choice([color for color in palette if color != 2])
    elif rich:
        frame_color = colors_rng.choice([color for color in palette if color != 2])
        marker_color = colors_rng.choice([color for color in palette if color != frame_color])
    else:
        frame_color, marker_color = colors_rng.sample(list(palette), 2)

    grid = full_grid(h, w, 0)
    if layout == "below":
        total_h = frame_h + 1 + mh
        block_r = rng.randint(0, h - total_h)
        fr = block_r
        mr = block_r + frame_h + 1
        fc = rng.randint(0, w - frame_w)
        mc = rng.randint(0, w - mw)
    else:
        total_w = frame_w + 1 + mw
        block_c = rng.randint(0, w - total_w)
        fc = block_c
        mc = block_c + frame_w + 1
        fr = rng.randint(0, h - frame_h)
        mr = rng.randint(0, h - mh)

    for c in range(fc, fc + frame_w):
        grid[fr][c] = frame_color
        grid[fr + frame_h - 1][c] = frame_color
    for r in range(fr, fr + frame_h):
        grid[r][fc] = frame_color
        grid[r][fc + frame_w - 1] = frame_color
    for dr, dc in marker:
        grid[mr + dr][mc + dc] = marker_color

    # Reflect the complete scene, not just its marker, to include all four
    # relative placement directions while preserving every exact size control.
    orientation_rng = ctx.draw_rng("scene_orientation")
    if orientation_rng.randrange(2):
        grid = grid[::-1]
    if orientation_rng.randrange(2):
        grid = [row[::-1] for row in grid]

    errors = self_check(grid, difficulty=difficulty)
    if errors:  # fail closed rather than returning a malformed lesson
        raise RuntimeError("internal generator invariant failure: " + "; ".join(errors))
    return grid


def _components8(cells):
    remaining = set(cells)
    components = []
    while remaining:
        first = min(remaining)
        pending, component = [first], {first}
        remaining.remove(first)
        while pending:
            r, c = pending.pop()
            neighbors = {(r + dr, c + dc) for dr in (-1, 0, 1)
                         for dc in (-1, 0, 1)} & remaining
            remaining.difference_update(neighbors)
            component.update(neighbors)
            pending.extend(sorted(neighbors))
        components.append(component)
    return sorted(components, key=lambda part: (-len(part), sorted(part)))


def _render_pattern(cells, mh, mw, ih, iw, frame_color, marker_color, *, mode="intended"):
    """Authoring mirror/rivals only; exported labels still come from Racket."""
    if mode == "square_output":
        iw = ih
    if mode == "red_border":
        frame_color = 2
    if mode == "largest_component8":
        cells = _components8(cells)[0]
        r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
        cells = {(r - r0, c - c0) for r, c in cells}
        mh, mw = max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1
    out = full_grid(ih + 2, iw + 2, frame_color)
    for r in range(ih):
        for c in range(iw):
            if mode == "fixed_3x3":
                source = (r * 3 // ih, c * 3 // iw)
            elif mode == "uniform_height_scale":
                source = (r // max(1, ih // mh), c // max(1, ih // mh))
            else:
                source = (r * mh // ih, c * mw // iw)
            out[r + 1][c + 1] = marker_color if source in cells else 0
    return out


@lru_cache(maxsize=64)
def _rich_marker_choices(mh, mw, sh, sw):
    # Rich markers have only six possible cells, so exhaustively retain the
    # exact-bbox masks that refute every canonical-compatible shortcut.
    choices = []
    for bits in range(1, (1 << (mh * mw)) - 1):
        cells = {(r, c) for r in range(mh) for c in range(mw)
                 if bits & (1 << (r * mw + c))}
        if ({r for r, _ in cells} >= {0, mh - 1}
                and {c for _, c in cells} >= {0, mw - 1}):
            orientations = (
                cells,
                {(mh - 1 - r, c) for r, c in cells},
                {(r, mw - 1 - c) for r, c in cells},
                {(mh - 1 - r, mw - 1 - c) for r, c in cells},
            )
            if all(_render_pattern(shape, mh, mw, mh * sh, mw * sw, 1, 3, mode=name)
                   != _render_pattern(shape, mh, mw, mh * sh, mw * sw, 1, 3)
                   for shape in orientations for name in CANONICAL_SHORTCUTS):
                choices.append(tuple(sorted(cells)))
    return tuple(choices)


def _rich_marker(rng, mh, mw, sh, sw):
    choices = _rich_marker_choices(mh, mw, sh, sw)
    if not choices:
        raise RuntimeError("no marker refutes the declared canonical shortcuts")
    return list(rng.choice(choices))


def _predict(grid, mode="intended"):
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    r0, c0, _r1, _c1 = facts["marker_bbox"]
    cells = {(r - r0, c - c0) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value == facts["marker_color"]}
    return _render_pattern(cells, facts["marker_h"], facts["marker_w"],
                           facts["frame_h"] - 2, facts["frame_w"] - 2,
                           facts["frame_color"], facts["marker_color"], mode=mode)


def _intended_output(grid):
    return _predict(grid)


def _red_border(grid):
    return _predict(grid, "red_border")


def _fixed_3x3(grid):
    return _predict(grid, "fixed_3x3")


def _uniform_height_scale(grid):
    return _predict(grid, "uniform_height_scale")


def _square_output(grid):
    return _predict(grid, "square_output")


def _largest_component8(grid):
    return _predict(grid, "largest_component8")


CANONICAL_SHORTCUTS = {
    "red_border": _red_border,
    "fixed_3x3": _fixed_3x3,
    "uniform_height_scale": _uniform_height_scale,
    "square_output": _square_output,
    "largest_component8": _largest_component8,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)


def _witness(rival):
    def predicate(grid):
        return not self_check(grid) and rival(grid) != _intended_output(grid)
    return predicate


SEMANTIC_WITNESSES = {name: _witness(rival) for name, rival in SEMANTIC_RIVALS.items()}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_WITNESSES}


def strict_canonical_like(grid):
    facts, errors = _analyze(grid)
    if errors:
        return errors
    reasons = []
    if facts["frame_color"] != 2:
        reasons.append("canonical frame is red")
    if (facts["marker_h"], facts["marker_w"]) != (3, 3):
        reasons.append("canonical marker bbox is 3x3")
    if facts["scale_h"] != facts["scale_w"]:
        reasons.append("canonical scales are equal")
    return reasons


def lesson_identifiable(demos, query):
    """Finite declared-rival diagnostic, not a universal uniqueness proof."""
    return [name + " fits demonstrations but disagrees on query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _draw_from_degenerate(name, rng):
    """Intentionally invalid negative probes; structural self_check rejects all."""
    grid = full_grid(15, 15, 0)
    if name == "no_frame":
        for dr, dc in ((0, 0), (0, 1), (1, 0)):
            grid[8 + dr][3 + dc] = 2
        return grid
    if name == "no_marker":
        for r in range(1, 7):
            grid[r][1] = 1
            grid[r][6] = 1
        for c in range(1, 7):
            grid[1][c] = 1
            grid[6][c] = 1
        return grid
    if name == "full_grid":
        return full_grid(15, 15, 1)
    raise ValueError(f"unknown degenerate texture {name!r}")

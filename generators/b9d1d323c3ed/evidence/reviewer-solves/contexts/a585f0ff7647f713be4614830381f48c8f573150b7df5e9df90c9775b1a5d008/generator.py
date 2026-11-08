"""Generator for ARC task b9d1d323c3ed (original ARC 28bf18c6).

Rule: find the bounding box of the single non-background object, crop it, and
concatenate that crop with itself horizontally.

The curriculum alternates an exact canonical-scale profile with a variable-bbox
profile.  Any four consecutive examples therefore retain a variable-bbox
counterexample under every one-query rotation, refuting the strongest canonical
shortcut: "the crop is always 3x3".
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b9d1d323c3ed"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8d4993ada3e1"

SUMMARY = (
    "A zero-background 8..18 by 8..18 grid contains one nonzero color. "
    "The occupied cells span a non-solid bounding box. Crop that box and "
    "concatenate the crop with itself horizontally. Even sample indices use "
    "the canonical 8x8 / 3x3 scale; odd indices use a non-3x3 bounding box so "
    "lessons explicitly refute a fixed-3x3 shortcut."
)

INVARIANTS = [
    "background is color 0",
    "exactly one non-background color is present",
    "the non-background bounding box is at least 2x2 and contains background",
    "the output is the bounding-box crop repeated twice horizontally",
    "generated output height and width are both smaller than the input",
]

FG_LAYOUTS = ("scattered", "blob", "diagonal", "frame", "row", "col", "checker")
BBOX_SIZE_KINDS = ("small", "medium", "large")
BBOX_POSITION_BIASES = ("spread", "center", "edge")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 8 or keyed 8..18",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 8 or keyed 8..18",
        "valid": "8..18",
    },
    "fg_color": {
        "type": "color",
        "default": "keyed 1..9",
        "valid": "1..9",
    },
    "bbox_size_kind": {
        "type": "str",
        "default": "scheduled medium or keyed small|large",
        "valid": "|".join(BBOX_SIZE_KINDS),
    },
    "bbox_position_bias": {
        "type": "str",
        "default": "keyed spread|center|edge",
        "valid": "|".join(BBOX_POSITION_BIASES),
    },
    "fg_layout": {
        "type": "str",
        "default": "keyed helpful layout",
        "valid": "|".join(FG_LAYOUTS),
    },
}

# Every Cartesian combination of documented overrides is constructively valid.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = ("canonical_core", "variable_bbox")
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.35


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Stable two-profile curriculum; independent of seed and difficulty."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    for name in ("grid_h", "grid_w", "fg_color"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise ValueError(f"{name} must be an integer, not {type(overrides[name]).__name__}")

    for name in ("bbox_size_kind", "bbox_position_bias", "fg_layout"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not str:
            raise ValueError(f"{name} must be a string, not {type(overrides[name]).__name__}")

    if "grid_h" in overrides and overrides["grid_h"] is not None and not 8 <= overrides["grid_h"] <= 18:
        raise ValueError("grid_h must be in 8..18")
    if "grid_w" in overrides and overrides["grid_w"] is not None and not 8 <= overrides["grid_w"] <= 18:
        raise ValueError("grid_w must be in 8..18")
    if "fg_color" in overrides and overrides["fg_color"] is not None and not 1 <= overrides["fg_color"] <= 9:
        raise ValueError("fg_color must be in 1..9")
    if "bbox_size_kind" in overrides and overrides["bbox_size_kind"] is not None \
            and overrides["bbox_size_kind"] not in BBOX_SIZE_KINDS:
        raise ValueError(f"bbox_size_kind must be one of {BBOX_SIZE_KINDS}")
    if "bbox_position_bias" in overrides and overrides["bbox_position_bias"] is not None \
            and overrides["bbox_position_bias"] not in BBOX_POSITION_BIASES:
        raise ValueError(f"bbox_position_bias must be one of {BBOX_POSITION_BIASES}")
    if "fg_layout" in overrides and overrides["fg_layout"] is not None \
            and overrides["fg_layout"] not in FG_LAYOUTS:
        raise ValueError(f"fg_layout must be one of {FG_LAYOUTS}")


def _draw_axis_choice(ctx, label: str, domain: Iterable[Any], default_options: Iterable[Any]):
    """Use a scheduled default without narrowing the explicit override domain."""
    domain_values = tuple(domain)
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, domain_values)
    return ctx.draw_choice(label, tuple(default_options))


def _broad_dimension_options(difficulty: Any) -> tuple[int, ...]:
    domain = tuple(range(8, 19))
    if difficulty == "easy":
        favored = tuple(range(8, 12))
    elif difficulty == "hard":
        favored = tuple(range(14, 19))
    else:
        favored = tuple(range(10, 16))
    # Retain the whole domain while giving difficulty a distributional effect.
    return domain + favored + favored


def _bbox_size(h: int, w: int, kind: str) -> tuple[int, int]:
    max_h = h - 1
    max_w = (w - 1) // 2
    if kind == "small":
        return 2, 2
    if kind == "medium":
        return min(3, max_h), min(3, max_w)
    if kind == "large":
        return max_h, max_w
    raise ValueError(f"unknown bbox_size_kind {kind!r}")


def _bbox_position(ctx, h: int, w: int, bh: int, bw: int, bias: str) -> tuple[int, int]:
    max_r = h - bh
    max_c = w - bw
    if bias == "center":
        return max_r // 2, max_c // 2
    rng = ctx.draw_rng("bbox_position")
    if bias == "edge":
        return rng.choice((0, max_r)), rng.choice((0, max_c))
    if bias != "spread":
        raise ValueError(f"unknown bbox_position_bias {bias!r}")

    center = (max_r // 2, max_c // 2)
    corners = {(0, 0), (0, max_c), (max_r, 0), (max_r, max_c)}
    candidates = [
        (r, c)
        for r in range(max_r + 1)
        for c in range(max_c + 1)
        if (r, c) != center and (r, c) not in corners
    ]
    if not candidates:
        candidates = [(r, c) for r in range(max_r + 1) for c in range(max_c + 1)]
    return rng.choice(candidates)


def _pattern_cells(layout: str, bh: int, bw: int, rng) -> set[tuple[int, int]]:
    anchors = {(0, 0), (bh - 1, bw - 1)}
    cells: set[tuple[int, int]] = set(anchors)

    if layout == "scattered":
        for r in range(bh):
            for c in range(bw):
                if rng.random() < 0.38:
                    cells.add((r, c))
    elif layout == "blob":
        center_r, center_c = (bh - 1) / 2, (bw - 1) / 2
        radius = max(1.0, (bh + bw) / 4.0)
        cells.update(
            (r, c)
            for r in range(bh)
            for c in range(bw)
            if abs(r - center_r) + abs(c - center_c) <= radius
        )
    elif layout == "diagonal":
        cells.update((k, k) for k in range(min(bh, bw)))
    elif layout == "frame":
        cells.update((r, c) for r in range(bh) for c in range(bw)
                     if r in (0, bh - 1) or c in (0, bw - 1))
    elif layout == "row":
        target = rng.randrange(bh)
        cells.update((target, c) for c in range(bw))
    elif layout == "col":
        target = rng.randrange(bw)
        cells.update((r, target) for r in range(bh))
    elif layout == "checker":
        cells.update((r, c) for r in range(bh) for c in range(bw) if (r + c) % 2 == 0)
    else:
        raise ValueError(f"unknown fg_layout {layout!r}")

    # Keep the transform visible even in 2x2/frame cases while preserving the
    # two diagonal anchors that span the requested box.
    if len(cells) == bh * bw:
        removable = sorted(set((r, c) for r in range(bh) for c in range(bw)) - anchors)
        if not removable:
            raise RuntimeError("constructive bbox has no removable non-anchor cell")
        cells.remove(removable[0])
    return cells


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    dimension_domain = tuple(range(8, 19))
    if profile == "canonical_core":
        h = _draw_axis_choice(ctx, "grid_h", dimension_domain, (8,))
        w = _draw_axis_choice(ctx, "grid_w", dimension_domain, (8,))
        size_kind = _draw_axis_choice(ctx, "bbox_size_kind", BBOX_SIZE_KINDS, ("medium",))
    else:
        broad = _broad_dimension_options(difficulty)
        h = _draw_axis_choice(ctx, "grid_h", dimension_domain, broad)
        w = _draw_axis_choice(ctx, "grid_w", dimension_domain, broad)
        size_kind = _draw_axis_choice(ctx, "bbox_size_kind", BBOX_SIZE_KINDS, ("small", "large"))

    fg_color = ctx.draw_color("fg_color", exclude={0})
    layout = ctx.draw_choice("fg_layout", FG_LAYOUTS)
    bias = ctx.draw_choice("bbox_position_bias", BBOX_POSITION_BIASES)
    bh, bw = _bbox_size(h, w, size_kind)
    rr, rc = _bbox_position(ctx, h, w, bh, bw, bias)

    grid = full_grid(h, w, 0)
    cells = _pattern_cells(layout, bh, bw, ctx.draw_rng("fg_pattern"))
    for local_r, local_c in cells:
        grid[rr + local_r][rc + local_c] = fg_color
    return grid


def _basic_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["expected a nonempty grid sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["expected nonempty row sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    values = [list(row) for row in grid]
    bad = [value for row in values for value in row
           if type(value) is not int or not 0 <= value <= 9]
    if bad:
        return None, ["cells must be integer ARC colors 0..9 (bool is not a color)"]
    return values, []


def _analyze(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    values, errors = _basic_grid(grid)
    if errors:
        return None, errors
    assert values is not None
    h, w = len(values), len(values[0])
    nonzero = [(r, c, value) for r, row in enumerate(values) for c, value in enumerate(row) if value != 0]
    if not nonzero:
        return None, ["grid has no non-background cells"]
    colors = {value for _, _, value in nonzero}
    if len(colors) != 1:
        return None, [f"expected one non-background color, found {sorted(colors)}"]
    rows = [r for r, _, _ in nonzero]
    cols = [c for _, c, _ in nonzero]
    r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
    crop = [row[c1:c2 + 1] for row in values[r1:r2 + 1]]
    return {
        "grid": values,
        "h": h,
        "w": w,
        "color": next(iter(colors)),
        "bbox": (r1, r2, c1, c2),
        "bh": r2 - r1 + 1,
        "bw": c2 - c1 + 1,
        "crop": crop,
        "nonzero_count": len(nonzero),
    }, []


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    info, errors = _analyze(grid)
    if errors:
        return errors
    assert info is not None
    findings: list[str] = []
    h, w, bh, bw = info["h"], info["w"], info["bh"], info["bw"]
    if not (8 <= h <= 18 and 8 <= w <= 18):
        findings.append(f"grid shape {h}x{w} is outside generated domain 8..18")
    if bh < 2 or bw < 2:
        findings.append(f"bbox {bh}x{bw} must be at least 2x2")
    if bh >= h or 2 * bw >= w:
        findings.append("bbox must make both output dimensions smaller than the input")
    if info["nonzero_count"] < 2:
        findings.append("bbox needs at least two non-background cells")
    if not any(value == 0 for row in info["crop"] for value in row):
        findings.append("bbox is fully filled, making horizontal repetition invisible")
    return findings


def observe_overrides(grid):
    """Recover all exact semantic axes required by the override contract."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    assert info is not None
    return {"grid_h": info["h"], "grid_w": info["w"], "fg_color": info["color"]}


def strict_canonical_like(grid):
    findings = list(self_check(grid))
    if findings:
        return findings
    info, _ = _analyze(grid)
    assert info is not None
    if (info["h"], info["w"]) != (8, 8):
        findings.append("canonical inputs are 8x8")
    if (info["bh"], info["bw"]) != (3, 3):
        findings.append("canonical non-background bbox is 3x3")
    return findings


def _intended_output(grid):
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    assert info is not None
    return [row + row for row in info["crop"]]


def _fixed_3x3_crop(grid):
    """RIVAL, not authority: assumes the demonstrated bbox is always 3x3."""
    info, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    assert info is not None
    values = info["grid"]
    r1, _, c1, _ = info["bbox"]
    h, w = info["h"], info["w"]
    crop = [
        [values[r][c] if 0 <= r < h and 0 <= c < w else 0
         for c in range(c1, c1 + 3)]
        for r in range(r1, r1 + 3)
    ]
    return [row + row for row in crop]


def _has_variable_bbox(grid) -> bool:
    info, errors = _analyze(grid)
    return not errors and (info["bh"], info["bw"]) != (3, 3)


def lesson_identifiable(demos, query):
    del query
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["lesson has no demonstrations"]
    findings = []
    refuted = False
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            findings.append(f"demo {index} is not an input/output pair")
            continue
        try:
            intended = _intended_output(pair["input"])
            rival = _fixed_3x3_crop(pair["input"])
        except ValueError as exc:
            findings.append(f"demo {index} is invalid: {exc}")
            continue
        if pair["output"] != intended:
            findings.append(f"demo {index} output does not match crop-and-repeat rule")
        if pair["output"] != rival:
            refuted = True
    if not refuted:
        findings.append("demonstrations do not refute the fixed-3x3 crop shortcut")
    return findings


SEMANTIC_WITNESSES = {"variable_bbox": _has_variable_bbox}
SEMANTIC_RIVALS = {"fixed_3x3_crop": _fixed_3x3_crop}
WITNESS_RIVALS = {"variable_bbox": ["fixed_3x3_crop"]}
CANONICAL_SHORTCUTS = {"fixed_3x3_crop": _fixed_3x3_crop}
LESSON_COMPETITORS = {"fixed_3x3_crop": _fixed_3x3_crop}

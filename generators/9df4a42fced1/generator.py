"""Generator for ``medium_p06`` — reduce seeded frames to center labels.

For every hollow rectangular frame, read the one differently colored seed in
its interior.  The output is a fresh zero-background grid containing one cell
at the frame's floor-center, colored like that seed.

The official examples put every seed at the center already, so they are also
consistent with the shortcut "erase the borders and keep the seed cells".
This generator preserves a large official-profile branch, but every sequential
lesson also contains off-center seeds that force the relocation rule.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9df4a42fced1"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "a101da2468b2"

SUMMARY = (
    "A zero-background grid contains one to three hollow rectangular frames. "
    "Each frame has exactly one differently colored seed strictly inside it. "
    "On a fresh zero-background canvas, replace each frame by one cell at its "
    "floor-center, using that frame's seed color."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.35

INVARIANTS = [
    "background is 0",
    "one to three complete hollow rectangular frames, each at least 5x5",
    "frame interiors are disjoint and each contains exactly one nonzero seed",
    "all frame and seed colors are distinct, and every seed differs from its frame",
    "every three-demo lesson includes both two- and three-frame scenes; ordinary scenes also include off-center seeds and an even frame dimension",
]

HELPFUL_TEXTURES = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_seeds", "multi_seeds")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 11..20 with scheduled official profiles",
        "valid": "11..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 11..22 with scheduled official profiles",
        "valid": "11..22",
    },
    "n_frames": {
        "type": "int",
        "default": "usually 2, scheduled 3-frame lessons",
        "valid": "1..3",
    },
}

_CANONICAL_PROFILES = ((11, 11), (12, 12), (12, 13), (13, 13))
_PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 7, 9, 1, 3, 6, 5, 8),
    "cool": (8, 6, 5, 1, 9, 3, 2, 4, 7),
    "varied": (9, 7, 5, 3, 1, 8, 6, 4, 2),
}


def _band(difficulty) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_axis_int(
    ctx, label: str, valid: tuple[int, int], ordinary: tuple[int, int]
) -> int:
    """Honor the full declared boundary whenever that axis is overridden."""
    bounds = valid if label in ctx.overrides else ordinary
    return ctx.draw_int(label, *bounds)


def _draw_frame(grid, box: tuple[int, int, int, int], color: int) -> None:
    r1, c1, r2, c2 = box
    for c in range(c1, c2 + 1):
        grid[r1][c] = color
        grid[r2][c] = color
    for r in range(r1, r2 + 1):
        grid[r][c1] = color
        grid[r][c2] = color


def _canonical_boxes(h: int, w: int) -> list[tuple[int, int, int, int]]:
    """Official-profile layouts, including both touching and separated pairs."""
    templates = {
        (11, 11): [(1, 1, 5, 5), (5, 6, 9, 10)],
        (12, 12): [(2, 1, 6, 5), (4, 7, 8, 11)],
        (12, 13): [(1, 1, 5, 5), (4, 6, 10, 12)],
        (13, 13): [(1, 2, 7, 8), (8, 8, 12, 12)],
    }
    return list(templates[(h, w)])


def _box_in_region(
    region: tuple[int, int, int, int], rng, *, prefer_even: bool = False
) -> tuple[int, int, int, int]:
    r1, c1, r2, c2 = region
    max_h = min(7, r2 - r1 + 1)
    max_w = min(7, c2 - c1 + 1)
    if max_h < 5 or max_w < 5:
        raise ValueError(f"region {region} cannot hold a 5x5 frame")
    hs = list(range(5, max_h + 1))
    ws = list(range(5, max_w + 1))
    if prefer_even and 6 in hs:
        fh = 6
    else:
        fh = rng.choice(hs)
    if prefer_even and 6 in ws and fh != 6:
        fw = 6
    else:
        fw = rng.choice(ws)
    top = rng.randint(r1, r2 - fh + 1)
    left = rng.randint(c1, c2 - fw + 1)
    return top, left, top + fh - 1, left + fw - 1


def _ordinary_boxes(
    h: int, w: int, n_frames: int, sample_index: int, rng
) -> list[tuple[int, int, int, int]]:
    """Build exact-count layouts with both touching and separated branches."""
    touching = sample_index % 4 in (1, 2)
    prefer_even = sample_index % 4 in (1, 3)

    if n_frames == 1:
        return [_box_in_region((0, 0, h - 1, w - 1), rng, prefer_even=prefer_even)]

    if n_frames == 2:
        horizontal = (sample_index // 2) % 2 == 0
        if horizontal:
            if touching:
                # Two 5-wide-or-larger regions whose borders are cardinally adjacent.
                left_w = min(7, max(5, w // 2))
                right_start = left_w
                if w - right_start < 5:
                    left_w = w - 5
                    right_start = left_w
                regions = [(0, 0, h - 1, left_w - 1), (0, right_start, h - 1, w - 1)]
            else:
                split = w // 2
                regions = [(0, 0, h - 1, split - 1), (0, split + 1, h - 1, w - 1)]
        else:
            if touching:
                top_h = min(7, max(5, h // 2))
                bottom_start = top_h
                if h - bottom_start < 5:
                    top_h = h - 5
                    bottom_start = top_h
                regions = [(0, 0, top_h - 1, w - 1), (bottom_start, 0, h - 1, w - 1)]
            else:
                split = h // 2
                regions = [(0, 0, split - 1, w - 1), (split + 1, 0, h - 1, w - 1)]
        return [
            _box_in_region(region, rng, prefer_even=prefer_even and i == 0)
            for i, region in enumerate(regions)
        ]

    if n_frames == 3:
        if touching:
            # Three exact 5x5 frames in an L; each adjacent pair remains a
            # separate color object, matching the canonical "touching frames"
            # cue class without overlap.
            top = rng.randint(0, h - 11)
            left = rng.randint(0, w - 10)
            return [
                (top, left, top + 5, left + 4),
                (top, left + 5, top + 4, left + 9),
                (top + 6, left, top + 10, left + 4),
            ]
        # One-cell row/column moats at the minimum 11x11 boundary.
        return [
            _box_in_region(
                (0, 0, h // 2 - 1, w // 2 - 1), rng, prefer_even=True
            ),
            _box_in_region((0, w // 2 + 1, h // 2 - 1, w - 1), rng),
            _box_in_region((h // 2 + 1, 0, h - 1, w // 2 - 1), rng),
        ]

    raise ValueError(f"unsupported n_frames={n_frames}")


def _draw_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(11, 11, 0)
    if name == "no_frames":
        grid[3][3] = 5
        grid[7][7] = 6
        return grid
    _draw_frame(grid, (2, 2, 8, 8), 4)
    if name == "no_seeds":
        return grid
    if name == "multi_seeds":
        grid[3][3] = 5
        grid[7][7] = 6
        return grid
    raise ValueError(f"unknown degenerate texture: {name!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - (set(AXES) | {"texture"})
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    texture_override = overrides.get("texture")
    if texture_override in DEGENERATE_TEXTURES:
        if len(overrides) != 1:
            raise ValueError("degenerate texture cannot be combined with other overrides")
        return _draw_degenerate(texture_override)
    if texture_override is not None and texture_override not in HELPFUL_TEXTURES:
        raise ValueError(f"unknown texture: {texture_override!r}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    # Six-step lesson schedule: C2, O2, O3, C2, C2, O3.  Every
    # three consecutive demonstrations therefore include both frame-count
    # regimes, while half of all draws retain an exact official profile.
    canonical_prior = not overrides and sample_index % 6 in (0, 3, 4)
    if canonical_prior:
        profile_rng = ctx.draw_rng("canonical_profile")
        h, w = profile_rng.choice(_CANONICAL_PROFILES)
        h = ctx.draw_int("grid_h", h, h)
        w = ctx.draw_int("grid_w", w, w)
        n_frames = ctx.draw_int("n_frames", 2, 2)
        texture = ctx.draw_choice("texture", ("default",))
        boxes = _canonical_boxes(h, w)
    else:
        ranges = {
            "easy": ((11, 13), (11, 14)),
            "medium": ((11, 16), (12, 18)),
            "hard": ((14, 20), (16, 22)),
        }
        h_range, w_range = ranges[band]
        if "n_frames" in overrides:
            n_frames = ctx.draw_int("n_frames", 1, 3)
        else:
            scheduled = 3 if sample_index % 6 in (2, 5) else 2
            n_frames = ctx.draw_int("n_frames", scheduled, scheduled)
        # A separated three-frame lesson needs one half-region at least six
        # cells wide/tall to exhibit floor-vs-ceil center placement.  Preserve
        # exact 11-cell overrides, but keep ordinary draws identifiable.
        if (
            n_frames == 3
            and sample_index % 4 not in (1, 2)
            and "grid_h" not in overrides
        ):
            h_range = (max(12, h_range[0]), h_range[1])
        h = _draw_axis_int(ctx, "grid_h", (11, 20), h_range)
        w = _draw_axis_int(ctx, "grid_w", (11, 22), w_range)
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
        boxes = _ordinary_boxes(h, w, n_frames, sample_index, ctx.draw_rng("layout"))

    palette_rng = ctx.draw_rng("palette")
    order = list(_PALETTES[texture])
    palette_rng.shuffle(order)
    colors = order[: 2 * n_frames]
    if len(colors) != 2 * n_frames or len(set(colors)) != 2 * n_frames:
        raise RuntimeError("palette construction did not produce distinct colors")

    grid = full_grid(h, w, 0)
    seed_rng = ctx.draw_rng("seeds")
    for index, (box, frame_color, seed_color) in enumerate(
        zip(boxes, colors[::2], colors[1::2])
    ):
        _draw_frame(grid, box, frame_color)
        r1, c1, r2, c2 = box
        center = ((r1 + r2) // 2, (c1 + c2) // 2)
        interior = [
            (r, c)
            for r in range(r1 + 1, r2)
            for c in range(c1 + 1, c2)
        ]
        if canonical_prior:
            seed_pos = center
        else:
            off_center = [p for p in interior if p != center]
            if not off_center:
                raise RuntimeError("frame has no off-center interior cell")
            # Different frames use independently rotated choices, ensuring the
            # shortcut-rebutting cue is not tied to one fixed corner.
            seed_pos = off_center[(seed_rng.randrange(len(off_center)) + index) % len(off_center)]
        grid[seed_pos[0]][seed_pos[1]] = seed_color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise RuntimeError(f"internal generator defect: {errors}")
    return grid


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[set[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            component: set[tuple[int, int]] = set()
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                component.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(component)
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = list(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _border(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def _analyze(grid) -> dict:
    errors: list[str] = []
    result = {"errors": errors, "frames": [], "loose": []}
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be nonempty")
        return result
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        errors.append("rows must be nonempty")
        return result
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return result
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be ARC colors 0..9")
        return result

    colors = sorted({value for row in grid for value in row if value != 0})
    frame_cells: set[tuple[int, int]] = set()
    frames: list[dict] = []
    for color in colors:
        for component in _components(grid, color):
            box = _bbox(component)
            r1, c1, r2, c2 = box
            border = _border(box)
            if component == border and r2 - r1 + 1 >= 5 and c2 - c1 + 1 >= 5:
                frames.append(
                    {
                        "color": color,
                        "bbox": box,
                        "border": border,
                        "center": ((r1 + r2) // 2, (c1 + c2) // 2),
                        "seeds": [],
                    }
                )
                frame_cells.update(border)

    if not 1 <= len(frames) <= 3:
        errors.append(f"expected 1..3 complete frames, found {len(frames)}")

    interiors: list[set[tuple[int, int]]] = []
    for frame in frames:
        r1, c1, r2, c2 = frame["bbox"]
        inside = {(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)}
        if any(inside & other for other in interiors):
            errors.append("frame interiors overlap")
        interiors.append(inside)
        seeds = [
            (r, c, grid[r][c])
            for r, c in sorted(inside)
            if grid[r][c] != 0 and grid[r][c] != frame["color"]
        ]
        frame["seeds"] = seeds
        if len(seeds) != 1:
            errors.append(
                f"frame {frame['bbox']} has {len(seeds)} interior seeds, expected 1"
            )

    result["frames"] = frames

    accounted = set(frame_cells)
    for frame in frames:
        accounted.update((r, c) for r, c, _ in frame["seeds"])
    loose = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) not in accounted
    ]
    result["loose"] = loose
    if loose:
        errors.append(f"found {len(loose)} non-frame/non-seed cells")

    used_colors = [frame["color"] for frame in frames]
    used_colors.extend(seed[2] for frame in frames for seed in frame["seeds"])
    if len(used_colors) != len(set(used_colors)):
        errors.append("frame and seed colors must be globally distinct")

    return result


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed frames, missing/extra seeds, noise, and color-role leaks."""
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from the returned grid."""
    analysis = _analyze(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(analysis["frames"]),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror used only for tests and rival analysis."""
    out = full_grid(len(grid), len(grid[0]), 0)
    analysis = _analyze(grid)
    for frame in analysis["frames"]:
        if len(frame["seeds"]) != 1:
            continue
        r, c = frame["center"]
        out[r][c] = frame["seeds"][0][2]
    return out


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    analysis = _analyze(grid)
    profile = (len(grid), len(grid[0]))
    if profile not in _CANONICAL_PROFILES:
        reasons.append(f"dimensions {profile[0]}x{profile[1]} are not official")
    if len(analysis["frames"]) != 2:
        reasons.append("official examples have exactly two frames")
    if len({value for row in grid for value in row}) != 5:
        reasons.append("official examples use background plus four role colors")
    for frame in analysis["frames"]:
        r1, c1, r2, c2 = frame["bbox"]
        if (r2 - r1 + 1, c2 - c1 + 1) not in ((5, 5), (7, 7)):
            reasons.append("official frames are 5x5 or 7x7 squares")
            break
        if frame["seeds"] and frame["seeds"][0][:2] != frame["center"]:
            reasons.append("official seeds are already at frame centers")
            break
    return reasons


def _has_centered_seed(grid) -> bool:
    return any(
        frame["seeds"] and frame["seeds"][0][:2] == frame["center"]
        for frame in _analyze(grid)["frames"]
    )


def _has_off_center_seed(grid) -> bool:
    return any(
        frame["seeds"] and frame["seeds"][0][:2] != frame["center"]
        for frame in _analyze(grid)["frames"]
    )


def _has_even_frame_dimension(grid) -> bool:
    for frame in _analyze(grid)["frames"]:
        r1, c1, r2, c2 = frame["bbox"]
        if (r2 - r1 + 1) % 2 == 0 or (c2 - c1 + 1) % 2 == 0:
            return True
    return False


def _frames_touch(grid) -> bool:
    frames = _analyze(grid)["frames"]
    for i, left in enumerate(frames):
        for right in frames[i + 1 :]:
            if any(
                abs(r1 - r2) + abs(c1 - c2) == 1
                for r1, c1 in left["border"]
                for r2, c2 in right["border"]
            ):
                return True
    return False


def _frames_separated(grid) -> bool:
    frames = _analyze(grid)["frames"]
    return len(frames) >= 2 and not _frames_touch(grid)


def _different_frame_sizes(grid) -> bool:
    sizes = []
    for frame in _analyze(grid)["frames"]:
        r1, c1, r2, c2 = frame["bbox"]
        sizes.append((r2 - r1 + 1, c2 - c1 + 1))
    return len(set(sizes)) >= 2


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "centered_seed_official_branch": _has_centered_seed,
    "off_center_seed_refutes_keep_seed_positions": _has_off_center_seed,
    "even_frame_floor_center": _has_even_frame_dimension,
    "touching_frames": _frames_touch,
    "separated_frames": _frames_separated,
    "three_frame_scene": lambda grid: len(_analyze(grid)["frames"]) == 3,
    "different_frame_sizes": _different_frame_sizes,
}


def _keep_seed_positions(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    for frame in _analyze(grid)["frames"]:
        for r, c, color in frame["seeds"]:
            out[r][c] = color
    return out


def _frame_color_centers(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    for frame in _analyze(grid)["frames"]:
        r, c = frame["center"]
        out[r][c] = frame["color"]
    return out


def _ceil_frame_centers(grid):
    """Plausible rival that rounds half-cell frame centers upward."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for frame in _analyze(grid)["frames"]:
        if not frame["seeds"]:
            continue
        r1, c1, r2, c2 = frame["bbox"]
        out[(r1 + r2 + 1) // 2][(c1 + c2 + 1) // 2] = frame["seeds"][0][2]
    return out


def _first_frame_only(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    frames = sorted(_analyze(grid)["frames"], key=lambda frame: frame["bbox"])
    if frames and frames[0]["seeds"]:
        r, c = frames[0]["center"]
        out[r][c] = frames[0]["seeds"][0][2]
    return out


def _one_global_center_per_seed(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    frames = _analyze(grid)["frames"]
    if frames:
        r, c = (len(grid) - 1) // 2, (len(grid[0]) - 1) // 2
        out[r][c] = frames[0]["seeds"][0][2]
    return out


def _two_frame_only(grid):
    """Plausible extrapolation that silently ignores a third frame."""
    out = full_grid(len(grid), len(grid[0]), 0)
    frames = sorted(_analyze(grid)["frames"], key=lambda frame: frame["bbox"])[:2]
    for frame in frames:
        if not frame["seeds"]:
            continue
        r, c = frame["center"]
        out[r][c] = frame["seeds"][0][2]
    return out


def _fixed_first_seed_color(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    frames = sorted(_analyze(grid)["frames"], key=lambda frame: frame["bbox"])
    if not frames or not frames[0]["seeds"]:
        return out
    color = frames[0]["seeds"][0][2]
    for frame in frames:
        r, c = frame["center"]
        out[r][c] = color
    return out


_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": lambda grid: [list(row) for row in grid],
    "erase_frames_keep_seed_positions": _keep_seed_positions,
    "use_frame_colors_at_centers": _frame_color_centers,
    "ceil_frame_centers": _ceil_frame_centers,
    "keep_only_first_frame": _first_frame_only,
    "two_frame_only": _two_frame_only,
    "collapse_to_global_center": _one_global_center_per_seed,
    "use_one_seed_color_for_all_centers": _fixed_first_seed_color,
}

# Public semantic contract: every named witness is paired with at least one
# executable rival that must disagree whenever the witness fires.  The
# canonical shortcut is deliberately retained because every official seed is
# already centered; generated off-center scenes are what falsify it.
SEMANTIC_RIVALS = dict(_RIVALS)
LESSON_COMPETITORS = dict(_RIVALS)
CANONICAL_SHORTCUTS = {
    "erase_frames_keep_seed_positions": _keep_seed_positions,
}
WITNESS_RIVALS = {
    "centered_seed_official_branch": ["use_frame_colors_at_centers"],
    "off_center_seed_refutes_keep_seed_positions": [
        "erase_frames_keep_seed_positions"
    ],
    "even_frame_floor_center": ["ceil_frame_centers"],
    "touching_frames": ["collapse_to_global_center"],
    "separated_frames": ["collapse_to_global_center"],
    "three_frame_scene": ["keep_only_first_frame", "two_frame_only"],
    "different_frame_sizes": ["use_one_seed_color_for_all_centers"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a plausible shortcut fits demos but changes query."""
    reasons: list[str] = []
    for name, rival in _RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"rival {name!r} fits every demonstration but changes query"
                )
    return reasons

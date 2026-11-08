"""Generator for ``cast_the_keyed_ray_inside_each_frame``.

Each separate cyan (8) rectangular frame contains exactly one direction key,
one magenta (6) emitter, and one orange (7) blocker.  The key mapping is the
canonical one: 1=up, 2=right, 3=down, 4=left.  The Racket oracle keeps the
frame contents and casts a magenta ray from each emitter in its keyed direction
until the next step would hit the blocker or the frame wall.

The ordinary curriculum uses two independent frames.  A four-sample schedule
covers every key, wall and blocker termination, positive and zero-length
blocked rays, and several spatial arrangements.  Canonical-sized 7x7-frame
scenes are sampled often enough to keep the real 15x17/15x18/16x18 profiles in
support.  Python constructs inputs only; the Racket rule remains the sole
output authority.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7d09ccad28c8"
VERSION = "3.0.0"
TASK_ID = "7d09ccad28c8"
RULE_HASH = "850aa5ef55c4"
SUMMARY = (
    "One or two separate hollow cyan(8) frames on a 0 background.  Each frame "
    "contains exactly one key (1=up, 2=right, 3=down, 4=left), one magenta(6) "
    "emitter, and one orange(7) blocker.  Cast a magenta ray from each emitter "
    "in the keyed direction until a blocker or the frame wall."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0 and every nonzero cell belongs to exactly one frame scene",
    "there are one or two separate hollow square color-8 frames of size 6..8",
    "each frame has exactly one key in 1..4, one emitter 6, and one blocker 7",
    "the key is not adjacent to the emitter and never lies on the emitted ray",
    "at least one frame adds a positive-length ray, so ordinary lessons are non-identity",
]

# These are deliberate malformed diagnostics.  They are never sampled on the
# ordinary path and self_check must reject every one.
DEGENERATE_TEXTURES = ("no_frame", "no_emitter", "no_key", "broken_frame")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical prior or difficulty-aware feasible profile",
        "valid": "13..18",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical prior or difficulty-aware feasible profile",
        "valid": "15..22",
    },
    "n_frames": {
        "type": "int",
        "default": "2",
        "valid": "1..2",
    },
    "frame_size": {
        "type": "int",
        "default": "6 easy, 7 medium/canonical, 8 hard",
        "valid": "6..8",
    },
    "n_blocked_rays": {
        "type": "int",
        "default": "four-sample schedule over 0, 1, and 2",
        "valid": "0..2",
    },
}

_DIRECTIONS = {
    1: (-1, 0),
    2: (0, 1),
    3: (1, 0),
    4: (0, -1),
}
_CANONICAL_DIMS = ((15, 17), (15, 18), (16, 18))


def _is_arc_grid(grid) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and isinstance(grid[0], list)
        and bool(grid[0])
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _color_components(grid, color):
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    stack.append(nxt)
        components.append(cells)
    return components


def _rect_border(box):
    r1, c1, r2, c2 = box
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def _frame_boxes(grid):
    boxes = []
    for cells in _color_components(grid, 8):
        r1 = min(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        r2 = max(r for r, _ in cells)
        c2 = max(c for _, c in cells)
        box = (r1, c1, r2, c2)
        if cells != _rect_border(box):
            return []
        boxes.append(box)
    return sorted(boxes)


def _inside(box):
    r1, c1, r2, c2 = box
    return [
        (r, c)
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
    ]


def _path_to_wall(emitter, direction, box):
    r1, c1, r2, c2 = box
    dr, dc = direction
    r, c = emitter[0] + dr, emitter[1] + dc
    path = []
    while r1 < r < r2 and c1 < c < c2:
        path.append((r, c))
        r += dr
        c += dc
    return path


def _frame_scene(grid, box):
    cells = _inside(box)
    emitters = [(r, c) for r, c in cells if grid[r][c] == 6]
    keys = [(r, c, grid[r][c]) for r, c in cells if grid[r][c] in _DIRECTIONS]
    blockers = [(r, c) for r, c in cells if grid[r][c] == 7]
    if len(emitters) != 1 or len(keys) != 1 or len(blockers) != 1:
        return None
    emitter = emitters[0]
    key = keys[0]
    blocker = blockers[0]
    path = _path_to_wall(emitter, _DIRECTIONS[key[2]], box)
    blocked = blocker in path
    stop_index = path.index(blocker) if blocked else len(path)
    paint_path = path[:stop_index]
    return {
        "emitter": emitter,
        "key": key,
        "blocker": blocker,
        "path": path,
        "paint_path": paint_path,
        "blocked": blocked,
    }


def observe_overrides(grid):
    """Recover every declared exact semantic axis from the returned grid."""
    if not _is_arc_grid(grid):
        return {}
    boxes = _frame_boxes(grid)
    if not boxes:
        return {
            "grid_h": len(grid),
            "grid_w": len(grid[0]),
            "n_frames": 0,
            "n_blocked_rays": 0,
        }
    sizes = {r2 - r1 + 1 for r1, c1, r2, c2 in boxes}
    blocked = 0
    for box in boxes:
        scene = _frame_scene(grid, box)
        if scene and scene["blocked"]:
            blocked += 1
    observed = {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(boxes),
        "n_blocked_rays": blocked,
    }
    if len(sizes) == 1:
        observed["frame_size"] = next(iter(sizes))
    return observed


def _valid_scenes(grid):
    """All frame scenes when the grid parses cleanly, else None (pure)."""
    if not _is_arc_grid(grid):
        return None
    boxes = _frame_boxes(grid)
    if not boxes:
        return None
    scenes = []
    for box in boxes:
        scene = _frame_scene(grid, box)
        if scene is None:
            return None
        scenes.append(scene)
    return scenes


def strict_canonical_like(grid):
    """Semantic-gate hook: is this grid canonical-like for THIS task?

    Canonical instances are two separate hollow 7x7 cyan frames on one of the
    canonical canvases (15x17, 15x18, 16x18), each holding exactly one key,
    one magenta emitter, and one orange blocker with a lawful keyed ray.
    Returns [] for a lawful canonical-like instance, else reasons.  Pure.
    """
    errors = self_check(grid)
    if errors:
        return errors
    reasons = []
    h, w = len(grid), len(grid[0])
    if (h, w) not in _CANONICAL_DIMS:
        reasons.append(
            f"dimensions {h}x{w} not in canonical profiles {_CANONICAL_DIMS}"
        )
    boxes = _frame_boxes(grid)
    if len(boxes) != 2:
        reasons.append(f"canonical scenes have two frames, found {len(boxes)}")
    for index, (r1, c1, r2, c2) in enumerate(boxes):
        if r2 - r1 + 1 != 7:
            reasons.append(
                f"frame {index} is {r2 - r1 + 1}x{c2 - c1 + 1}; canonical frames are 7x7"
            )
    return reasons


def _witness_key(key_value):
    def predicate(grid):
        scenes = _valid_scenes(grid)
        if not scenes:
            return False
        return any(
            scene["key"][2] == key_value and scene["paint_path"]
            for scene in scenes
        )

    return predicate


def _witness_stops_at_blocker(grid):
    scenes = _valid_scenes(grid)
    if not scenes:
        return False
    return any(scene["blocked"] and scene["paint_path"] for scene in scenes)


def _witness_stops_at_wall(grid):
    scenes = _valid_scenes(grid)
    if not scenes:
        return False
    return any((not scene["blocked"]) and scene["paint_path"] for scene in scenes)


def _witness_zero_length_ray(grid):
    scenes = _valid_scenes(grid)
    if not scenes:
        return False
    return any(scene["blocked"] and not scene["paint_path"] for scene in scenes)


# Semantic-gate hook: every branch the curriculum must actually demonstrate.
# key_* fire only on a POSITIVE painted ray in that keyed direction — a key
# whose ray never paints teaches nothing about the mapping (the pre-repair
# defect: wrong key->direction documentation plus one blocker-free frame).
SEMANTIC_WITNESSES = {
    "key_up": _witness_key(1),
    "key_right": _witness_key(2),
    "key_down": _witness_key(3),
    "key_left": _witness_key(4),
    "stops_at_blocker": _witness_stops_at_blocker,
    "stops_at_wall": _witness_stops_at_wall,
    "zero_length_ray": _witness_zero_length_ray,
}


def lesson_identifiable(demos, query):
    """Semantic-gate hook: do the demos pin down the query's answer?

    Competing rules a lesson must exclude: a different key->direction mapping
    for any key the query relies on, a blocker-ignoring ray (always runs to
    the wall), and a wall-shy ray (never reaches the wall).  Pure.
    """
    reasons = []
    query_scenes = _valid_scenes(query.get("input"))
    if query_scenes is None:
        return ["query input is not a lawful frame scene"]
    demo_scenes = []
    for index, demo in enumerate(demos):
        scenes = _valid_scenes(demo.get("input"))
        if scenes is None:
            reasons.append(f"demo {index} input is not a lawful frame scene")
            continue
        demo_scenes.extend(scenes)
    if reasons:
        return reasons

    demo_positive_keys = {
        scene["key"][2] for scene in demo_scenes if scene["paint_path"]
    }
    demo_has_blocker_stop = any(scene["blocked"] for scene in demo_scenes)
    demo_has_wall_stop = any(
        (not scene["blocked"]) and scene["paint_path"] for scene in demo_scenes
    )
    for scene in query_scenes:
        key_value = scene["key"][2]
        if scene["paint_path"] and key_value not in demo_positive_keys:
            reasons.append(
                f"query needs key {key_value} but no demo shows a positive "
                f"ray for that key (competing mapping survives)"
            )
        if scene["blocked"] and not demo_has_blocker_stop:
            reasons.append(
                "query ray stops at a blocker but no demo witnesses blocker "
                "termination (blocker-ignoring rule survives)"
            )
        if (not scene["blocked"]) and scene["paint_path"] and not demo_has_wall_stop:
            reasons.append(
                "query ray runs to the wall but no demo witnesses wall "
                "termination (wall-shy rule survives)"
            )
    return sorted(set(reasons))


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the full frame/key/emitter/blocker teaching grammar."""
    if not _is_arc_grid(grid):
        return ["grid must be a nonempty rectangular ARC grid"]
    h, w = len(grid), len(grid[0])
    errors = []
    if not (13 <= h <= 18 and 15 <= w <= 22):
        errors.append(f"grid dimensions {h}x{w} outside 13..18 by 15..22")
    palette = {value for row in grid for value in row}
    if not palette <= {0, 1, 2, 3, 4, 6, 7, 8}:
        errors.append(f"unexpected colors: {sorted(palette - {0, 1, 2, 3, 4, 6, 7, 8})}")
        return errors
    if 0 not in palette:
        errors.append("background color 0 is missing")

    boxes = _frame_boxes(grid)
    if not (1 <= len(boxes) <= 2):
        errors.append(f"expected one or two hollow rectangular color-8 frames, found {len(boxes)}")
        return errors

    claimed = set()
    total_paintable = 0
    for index, box in enumerate(boxes):
        r1, c1, r2, c2 = box
        fh, fw = r2 - r1 + 1, c2 - c1 + 1
        if fh != fw or not (6 <= fh <= 8):
            errors.append(f"frame {index} must be square with size 6..8, got {fh}x{fw}")
        claimed.update(_rect_border(box))
        claimed.update(_inside(box))
        scene = _frame_scene(grid, box)
        if scene is None:
            inside = _inside(box)
            n_emitters = sum(grid[r][c] == 6 for r, c in inside)
            n_keys = sum(grid[r][c] in _DIRECTIONS for r, c in inside)
            n_blockers = sum(grid[r][c] == 7 for r, c in inside)
            errors.append(
                f"frame {index} needs exactly one emitter/key/blocker; "
                f"found {n_emitters}/{n_keys}/{n_blockers}"
            )
            continue
        er, ec = scene["emitter"]
        kr, kc, _ = scene["key"]
        if max(abs(er - kr), abs(ec - kc)) <= 1:
            errors.append(f"frame {index} key is adjacent to the emitter")
        if (kr, kc) in scene["path"]:
            errors.append(f"frame {index} key lies on the emitted ray")
        bad_path = [
            (r, c, grid[r][c])
            for r, c in scene["paint_path"]
            if grid[r][c] != 0
        ]
        if bad_path:
            errors.append(f"frame {index} ray crosses non-background cells before stopping: {bad_path}")
        total_paintable += len(scene["paint_path"])

    outside = [
        (r, c, grid[r][c])
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) not in claimed
    ]
    if outside:
        errors.append(f"nonzero cells outside frame scenes: {outside[:4]}")
    if total_paintable < 1:
        errors.append("all rays are zero-length; ordinary lesson would be an identity")
    return errors


def _boxes_separated(a, b):
    ar1, ac1, ar2, ac2 = a
    br1, bc1, br2, bc2 = b
    return (
        ar2 + 2 <= br1
        or br2 + 2 <= ar1
        or ac2 + 2 <= bc1
        or bc2 + 2 <= ac1
    )


def _dimension_candidates(n_frames, frame_size):
    candidates = []
    for h in range(13, 19):
        for w in range(15, 23):
            if n_frames == 1:
                feasible = h >= frame_size + 2 and w >= frame_size + 2
            else:
                feasible = (
                    (h >= frame_size + 2 and w >= 2 * frame_size + 3)
                    or (h >= 2 * frame_size + 3 and w >= frame_size + 2)
                )
            if feasible:
                candidates.append((h, w))
    return candidates


def _placement_candidates(h, w, frame_size, n_frames):
    boxes = [
        (r, c, r + frame_size - 1, c + frame_size - 1)
        for r in range(1, h - frame_size)
        for c in range(1, w - frame_size)
    ]
    if n_frames == 1:
        return [(box,) for box in boxes]
    return [
        pair
        for pair in combinations(boxes, 2)
        if _boxes_separated(pair[0], pair[1])
    ]


def _paint_border(grid, box):
    for r, c in _rect_border(box):
        grid[r][c] = 8


def _place_frame_contents(grid, box, key_value, blocked, zero_length, rng):
    direction = _DIRECTIONS[key_value]
    interior = _inside(box)
    candidates = []
    for emitter in interior:
        path = _path_to_wall(emitter, direction, box)
        if not path:
            continue
        if blocked:
            if zero_length:
                stop_indices = [0]
            else:
                stop_indices = list(range(1, len(path)))
            for stop_index in stop_indices:
                blocker = path[stop_index]
                forbidden = {emitter, blocker, *path}
                keys = [
                    p
                    for p in interior
                    if p not in forbidden
                    and max(abs(p[0] - emitter[0]), abs(p[1] - emitter[1])) > 1
                ]
                for key in keys:
                    candidates.append((emitter, key, blocker))
        else:
            path_set = set(path)
            blockers = [p for p in interior if p != emitter and p not in path_set]
            for blocker in blockers:
                forbidden = {emitter, blocker, *path}
                keys = [
                    p
                    for p in interior
                    if p not in forbidden
                    and max(abs(p[0] - emitter[0]), abs(p[1] - emitter[1])) > 1
                ]
                for key in keys:
                    candidates.append((emitter, key, blocker))
    if not candidates:
        raise ValueError(
            f"no lawful contents for frame={box}, key={key_value}, "
            f"blocked={blocked}, zero_length={zero_length}"
        )
    emitter, key, blocker = rng.choice(candidates)
    grid[emitter[0]][emitter[1]] = 6
    grid[key[0]][key[1]] = key_value
    grid[blocker[0]][blocker[1]] = 7


def _draw_degenerate(name):
    grid = full_grid(15, 17, 0)
    box = (2, 3, 8, 9)
    if name != "no_frame":
        _paint_border(grid, box)
    if name != "no_emitter":
        grid[5][6] = 6
    if name != "no_key":
        grid[3][4] = 2
    grid[5][8] = 7
    if name == "broken_frame":
        grid[2][6] = 0
    return grid


def mutation_fixtures():
    base = full_grid(15, 17, 0)
    box = (2, 3, 8, 9)
    _paint_border(base, box)
    base[5][6] = 6
    base[3][4] = 2
    base[5][8] = 7

    missing_key = [row[:] for row in base]
    missing_key[3][4] = 0

    duplicate_emitter = [row[:] for row in base]
    duplicate_emitter[6][5] = 6

    broken_frame = [row[:] for row in base]
    broken_frame[2][6] = 0

    outside_noise = [row[:] for row in base]
    outside_noise[12][13] = 7

    key_on_ray = [row[:] for row in base]
    key_on_ray[3][4] = 0
    key_on_ray[5][7] = 2
    key_on_ray[5][8] = 7

    return [
        ("missing_key", missing_key),
        ("duplicate_emitter", duplicate_emitter),
        ("broken_frame", broken_frame),
        ("outside_noise", outside_noise),
        ("key_on_ray", key_on_ray),
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"unsupported override(s): {sorted(unknown)}")
    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(
                f"unknown texture {texture!r}; valid degenerates: {DEGENERATE_TEXTURES}"
            )
        extra = sorted(
            key for key, value in overrides.items()
            if key != "texture" and value is not None
        )
        if extra:
            raise ValueError(
                f"degenerate texture {texture!r} is a fixed diagnostic and "
                f"cannot be combined with {extra}"
            )
        return _draw_degenerate(texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = sample_index % EXAMPLES_NEEDED

    n_frames = (
        ctx.draw_int("n_frames", 1, 2)
        if overrides.get("n_frames") is not None
        else ctx.draw_int("n_frames", 2, 2)
    )

    canonical_prior = (
        n_frames == 2
        and not any(
            overrides.get(name) is not None
            for name in ("grid_h", "grid_w", "frame_size")
        )
        and ctx.draw_rng("canonical_prior").random() < 0.45
    )
    explicit_h = overrides.get("grid_h")
    explicit_w = overrides.get("grid_w")
    if overrides.get("frame_size") is not None:
        frame_size = ctx.draw_int("frame_size", 6, 8)
    else:
        desired_size = (
            7
            if canonical_prior or difficulty in (None, "medium")
            else (6 if difficulty == "easy" else 8)
        )
        feasible_sizes = []
        for candidate_size in range(6, 9):
            size_dims = _dimension_candidates(n_frames, candidate_size)
            if explicit_h is not None:
                size_dims = [pair for pair in size_dims if pair[0] == int(explicit_h)]
            if explicit_w is not None:
                size_dims = [pair for pair in size_dims if pair[1] == int(explicit_w)]
            if size_dims:
                feasible_sizes.append(candidate_size)
        if not feasible_sizes:
            raise ValueError(
                f"no feasible frame size for n_frames={n_frames}, "
                f"grid_h={explicit_h}, grid_w={explicit_w}"
            )
        desired_size = min(feasible_sizes, key=lambda value: (abs(value - desired_size), value))
        frame_size = ctx.draw_int("frame_size", desired_size, desired_size)

    candidates = _dimension_candidates(n_frames, frame_size)
    if explicit_h is not None:
        explicit_h = int(explicit_h)
        if not 13 <= explicit_h <= 18:
            raise ValueError(f"grid_h override {explicit_h} outside 13..18")
        candidates = [pair for pair in candidates if pair[0] == explicit_h]
    if explicit_w is not None:
        explicit_w = int(explicit_w)
        if not 15 <= explicit_w <= 22:
            raise ValueError(f"grid_w override {explicit_w} outside 15..22")
        candidates = [pair for pair in candidates if pair[1] == explicit_w]
    if not candidates:
        raise ValueError(
            f"no feasible canvas for n_frames={n_frames}, frame_size={frame_size}, "
            f"grid_h={explicit_h}, grid_w={explicit_w}"
        )

    if canonical_prior:
        canonical = [pair for pair in _CANONICAL_DIMS if pair in candidates]
        chosen_h, chosen_w = ctx.draw_choice("dimension_profile", canonical)
    else:
        if explicit_h is None and explicit_w is None:
            if difficulty == "easy":
                preferred = [pair for pair in candidates if pair[0] <= 15 and pair[1] <= 18]
            elif difficulty == "hard":
                preferred = [pair for pair in candidates if pair[0] >= 15 and pair[1] >= 19]
            else:
                preferred = [pair for pair in candidates if 14 <= pair[0] <= 17 and 17 <= pair[1] <= 20]
            if preferred:
                candidates = preferred
        chosen_h, chosen_w = ctx.draw_choice("dimension_profile", candidates)
    h = ctx.draw_int("grid_h", chosen_h, chosen_h)
    w = ctx.draw_int("grid_w", chosen_w, chosen_w)

    if overrides.get("n_blocked_rays") is not None:
        requested_blocked = int(overrides["n_blocked_rays"])
        if not 0 <= requested_blocked <= 2:
            raise ValueError(
                f"n_blocked_rays override {requested_blocked} outside 0..2"
            )
        if requested_blocked > n_frames:
            raise ValueError(
                f"n_blocked_rays={requested_blocked} exceeds n_frames={n_frames}"
            )
        n_blocked = ctx.draw_int(
            "n_blocked_rays", requested_blocked, requested_blocked
        )
    else:
        scheduled = (2, 1, 0, 2)[profile]
        scheduled = min(scheduled, n_frames)
        n_blocked = ctx.draw_int("n_blocked_rays", scheduled, scheduled)

    placements = _placement_candidates(h, w, frame_size, n_frames)
    if not placements:
        raise ValueError(
            f"dimension planner produced no placements for {h}x{w}, "
            f"frame_size={frame_size}, n_frames={n_frames}"
        )
    boxes = ctx.draw_rng("frame_placement").choice(placements)
    boxes = tuple(sorted(boxes))

    # Pair schedule covers all four keys in any four consecutive lesson
    # demonstrations.  Seed rotation changes the literal colors without
    # destroying that coverage property.
    direction_pairs = ((1, 2), (3, 4), (2, 3), (4, 1))
    rotation = int(seed) % 4
    directions = [
        ((value - 1 + rotation) % 4) + 1
        for value in direction_pairs[profile]
    ][:n_frames]

    grid = full_grid(h, w, 0)
    for box in boxes:
        _paint_border(grid, box)

    # The first profile includes the canonical zero-length blocker branch,
    # but only when another frame has a positive ray.  Every other blocked ray
    # leaves at least one paintable cell before its blocker.
    zero_length_index = 0 if profile == 0 and n_blocked >= 2 else None
    content_rng = ctx.draw_rng("frame_contents")
    for index, (box, key_value) in enumerate(zip(boxes, directions)):
        blocked = index < n_blocked
        zero_length = blocked and index == zero_length_index
        _place_frame_contents(
            grid,
            box,
            key_value,
            blocked,
            zero_length,
            content_rng,
        )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"internal generator invariant failure: {errors}")
    return grid

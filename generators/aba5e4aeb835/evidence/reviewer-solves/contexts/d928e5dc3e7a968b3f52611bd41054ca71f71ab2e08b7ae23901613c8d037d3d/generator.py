r"""Constructive inputs for Mirror Laser Trace, bank hard_p01.

The unchanged Racket authority starts at color 2, reflects at 3 (/) and
4 (\), stops at 5, and paints original zero cells with 8. This module
constructs inputs only. Its Python tracer supports validation and explicitly
named rivals; labels must still be executed through the Racket authority.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aba5e4aeb835"
TASK_ID = GENERATOR_ID
RULE_HASH = "17ecf3938e04"
VERSION = "2.0.0"
SUMMARY = (
    "A unique border 2 launches a beam through interior / (3) and \\ (4) "
    "mirrors. Paint traversed zeros 8, preserving objects; stop at a wall 5 "
    "or exit. Four scheduled profiles teach walls, long routes and repeated "
    "mirror orientations, with occluded and off-path distractors."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
INVARIANTS = [
    "rectangular 8..18 by 8..20 integer grid containing only 0,2,3,4,5",
    "exactly one color-2 source on a noncorner border cell",
    "2..9 interior mirrors (3 or 4); 0..4 walls, including lawful border walls",
    "the source reaches at least two distinct mirrors and paints at least one zero",
    "normal samples follow 2..5 reflections; 0..4 extra mirrors are off-path or hidden behind a wall",
]
AXES = {
    "grid_h": {"type": "int", "default": "9 in core; 8..18 in broad", "valid": "8..18"},
    "grid_w": {"type": "int", "default": "12 in core; 8..20 in broad", "valid": "8..20"},
    "path_turns": {"type": "int", "default": "scheduled 2..5", "valid": "2..5"},
    "n_distractors": {"type": "int", "default": "0 in exit core, 1 behind active wall; 0..4 in broad", "valid": "0..4"},
    "n_walls": {"type": "int", "default": "scheduled 0..4", "valid": "0..4"},
    "source_side": {"type": "str", "default": "uniform four sides", "valid": "top|right|bottom|left"},
    "wall_stop": {"type": "int", "default": "1 in wall profile, 0 otherwise", "valid": "0..1"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [{"n_walls": 0, "wall_stop": 1}]
SCHEDULE_PROFILES = ("canonical_exit", "active_wall", "long_route", "repeated_mirrors")
_SIDES = ("top", "right", "bottom", "left")


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive unoverridden draws contain all teaching profiles."""
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_int(ctx, label, lo, hi, default):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _trace(grid, *, max_reflections=None, alternating=False,
           ignore_mirrors=False, ignore_walls=False, swap_mirrors=False):
    """Bounded input analysis; original pixels, incoming-direction cycle states.

    Optional deviations implement explicit incorrect competitors, never labels.
    The walk is the ordered entered-cell sequence; mirrors records visits.
    """
    h, w = len(grid), len(grid[0]) if grid else 0
    starts = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    result = {"source": starts[0] if starts else None, "painted": set(),
              "walk": [], "mirrors": [], "termination": "no_source"}
    if not starts:
        return result
    r, c = starts[0]
    dr, dc = ((0, 1) if c == 0 else (0, -1) if c == w - 1
              else (1, 0) if r == 0 else (-1, 0))
    visited = set()
    previous_mirror = None
    while True:
        r, c = r + dr, c + dc
        if not (0 <= r < h and 0 <= c < w):
            result["termination"] = "exit"
            break
        value = grid[r][c]
        if value == 5 and not ignore_walls:
            result["termination"] = "wall"
            break
        state = (r, c, dr, dc)
        if state in visited:
            result["termination"] = "cycle"
            break
        visited.add(state)
        result["walk"].append((r, c, dr, dc, value))
        if value == 0:
            result["painted"].add((r, c))
        elif value in (3, 4):
            result["mirrors"].append((r, c, value, dr, dc))
            if max_reflections is not None and len(result["mirrors"]) > max_reflections:
                result["termination"] = "rival_reflection_limit"
                break
            if alternating and value == previous_mirror:
                result["termination"] = "rival_repeated_mirror"
                break
            previous_mirror = value
            if not ignore_mirrors:
                mirror = 7 - value if swap_mirrors else value
                dr, dc = (-dc, -dr) if mirror == 3 else (dc, dr)
        elif value == 2 or (value == 5 and ignore_walls):
            continue
        else:
            result["termination"] = "unsupported_color"
            break
    return result


def _trace_output(grid, **deviations):
    out = [list(row) for row in grid]
    for r, c in _trace(grid, **deviations)["painted"]:
        out[r][c] = 8
    return out


def _orient(grid, side, reflected):
    if reflected:
        grid = [[7 - v if v in (3, 4) else v for v in reversed(row)] for row in grid]
    for _ in range(_SIDES.index(side)):
        grid = [[7 - v if v in (3, 4) else v for v in row]
                for row in zip(*grid[::-1])]
    return grid


def _route_grid(h, w, turns, shape, rng, *, reserve_hidden_mirror=False):
    """Embed three route topologies using independently drawn spacings.

    The route reserves an empty initial cell and at least two cells before
    each final exit. The fold crosses an earlier empty segment; the stair
    repeats a mirror orientation; weave mixes both equal and unequal turns.
    """
    # A hidden mirror needs a free interior cell after the wall. Reserve that
    # exit margin constructively, including the smallest 8x8 exact override.
    row_slots = range(2, h - 3) if reserve_hidden_mirror else range(2, h - 2)
    col_slots = range(2, w - 3) if reserve_hidden_mirror else range(1, w - 2)
    low, middle, high = sorted(rng.sample(row_slots, 3))
    a, b, c = sorted(rng.sample(col_slots, 3))
    if shape == "fold":
        points = [(middle, a), (middle, c), (low, c), (low, b), (high, b)]
        mirrors = (4, 3, 4, 3, 4)
    elif shape == "stair":
        points = [(low, a), (low, b), (middle, b), (middle, c), (high, c)]
        mirrors = (4, 4, 4, 4, 4)
    else:
        points = [(middle, a), (middle, b), (low, b), (low, c), (high, c)]
        mirrors = (4, 3, 3, 4, 4)
    grid = full_grid(h, w, 0)
    grid[0][a] = 2
    for (r, c), value in zip(points[:turns], mirrors[:turns]):
        grid[r][c] = value
    return grid


def _active_wall_candidates(trace, h, w, *, require_hidden_mirror=False):
    walk = trace["walk"]
    last_mirror = max(i for i, item in enumerate(walk) if item[4] in (3, 4))
    prefix = {(r, c) for r, c, *_ in walk[:last_mirror + 1]}
    tail = [(r, c) for r, c, _, _, value in walk[last_mirror + 1:] if value == 0]
    # Do not cut an earlier segment. Require a later, previously unpainted
    # zero so ignoring the wall changes the visible answer.
    choices = []
    for i, point in enumerate(tail):
        later = [p for p in tail[i + 1:] if p not in prefix and p != point]
        hidden = [p for p in later if 0 < p[0] < h - 1 and 0 < p[1] < w - 1]
        if point not in prefix and later and (hidden or not require_hidden_mirror):
            choices.append((point, hidden))
    return choices


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and ((name == "source_side" and type(value) is not str)
                                  or (name != "source_side" and type(value) is not int)):
            raise ValueError(f"invalid type for {name}: {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    core = profile in ("canonical_exit", "active_wall")
    favored = {"easy": (8, 9, 10), "medium": (10, 12, 14), "hard": (14, 16, 18)}.get(difficulty, ())
    h_default = 9 if core else ctx.draw_rng("height_default").choice(list(range(8, 19)) + list(favored) * 3)
    w_default = 12 if core else ctx.draw_rng("width_default").choice(list(range(8, 21)) + list(favored) * 3)
    h = _scheduled_int(ctx, "grid_h", 8, 18, h_default)
    w = _scheduled_int(ctx, "grid_w", 8, 20, w_default)
    turn_default = {"canonical_exit": 2, "active_wall": 3, "long_route": 5,
                    "repeated_mirrors": 4}[profile]
    turns = _scheduled_int(ctx, "path_turns", 2, 5, turn_default)
    distractor_default = (1 if profile == "active_wall" else 0 if core
                          else ctx.draw_rng("distractor_default").randint(0, 4))
    distractors = _scheduled_int(ctx, "n_distractors", 0, 4, distractor_default)
    wall_default = 1 if core else ctx.draw_rng("wall_default").randint(0, 4)
    if overrides.get("wall_stop") == 1:
        wall_default = max(1, wall_default)
    walls = _scheduled_int(ctx, "n_walls", 0, 4, wall_default)
    stop_default = int(profile == "active_wall" and walls > 0)
    wall_stop = _scheduled_int(ctx, "wall_stop", 0, 1, stop_default)
    if wall_stop and not walls:
        raise ValueError("incompatible n_walls=0 and wall_stop=1")
    side = ctx.draw_choice("source_side", _SIDES)
    shape = ("stair" if profile == "repeated_mirrors" else "fold" if core
             else ctx.draw_rng("route_shape").choice(("fold", "weave")))
    # Odd quarter turns transpose dimensions before construction.
    bh, bw = (w, h) if _SIDES.index(side) % 2 else (h, w)
    hidden_mirror = bool(wall_stop and distractors)
    grid = _orient(_route_grid(bh, bw, turns, shape, ctx.draw_rng("route_coordinates"),
                              reserve_hidden_mirror=hidden_mirror),
                   side, ctx.draw_rng("chirality").choice((False, True)))
    trace = _trace(grid)
    protected = {(r, c) for r, c, *_ in trace["walk"]} | {trace["source"]}
    placement_rng = ctx.draw_rng("off_path_objects")
    mirror_slots = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
                    if grid[r][c] == 0 and (r, c) not in protected]
    for r, c in placement_rng.sample(mirror_slots, distractors - int(hidden_mirror)):
        grid[r][c] = placement_rng.choice((3, 4))
    if wall_stop:
        candidates = _active_wall_candidates(trace, h, w, require_hidden_mirror=hidden_mirror)
        if not candidates:
            raise RuntimeError("constructed route has no observable terminal-wall placement")
        (r, c), hidden_slots = ctx.draw_rng("terminal_wall").choice(candidates)
        grid[r][c] = 5
        if hidden_mirror:
            r, c = ctx.draw_rng("hidden_mirror").choice(hidden_slots)
            grid[r][c] = ctx.draw_rng("hidden_mirror_kind").choice((3, 4))
    wall_slots = [(r, c) for r in range(h) for c in range(w)
                  if grid[r][c] == 0 and (r, c) not in protected]
    for r, c in placement_rng.sample(wall_slots, walls - wall_stop):
        grid[r][c] = 5
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or v not in (0, 2, 3, 4, 5) for row in grid for v in row):
        return ["input colors must be integers in 0,2,3,4,5"]
    if not (8 <= h <= 18 and 8 <= w <= 20):
        return ["grid outside declared 8..18 by 8..20 domain"]
    sources = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    if len(sources) != 1:
        return ["expected exactly one color-2 source"]
    r, c = sources[0]
    if not ((r in (0, h - 1)) ^ (c in (0, w - 1))):
        return ["source must occupy a noncorner border cell"]
    mirrors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v in (3, 4)]
    errors = []
    if not 2 <= len(mirrors) <= 9:
        errors.append("expected 2..9 mirrors")
    if any(r in (0, h - 1) or c in (0, w - 1) for r, c in mirrors):
        errors.append("mirrors must be interior")
    if sum(v == 5 for row in grid for v in row) > 4:
        errors.append("expected at most four walls")
    trace = _trace(grid)
    if len({(r, c) for r, c, *_ in trace["mirrors"]}) < 2:
        errors.append("beam must reach at least two distinct mirrors")
    if not trace["painted"]:
        errors.append("beam must paint at least one original zero")
    return errors


def strict_canonical_like(grid):
    """Canonical semantics and declared domain; geometry need not match a template."""
    return self_check(grid)


def observe_overrides(grid):
    trace = _trace(grid)
    r, c = trace["source"]
    h, w = len(grid), len(grid[0])
    side = "left" if c == 0 else "right" if c == w - 1 else "top" if r == 0 else "bottom"
    mirror_count = sum(v in (3, 4) for row in grid for v in row)
    visited_mirrors = {(r, c) for r, c, *_ in trace["mirrors"]}
    return {"grid_h": h, "grid_w": w, "path_turns": len(trace["mirrors"]),
            "n_distractors": mirror_count - len(visited_mirrors),
            "n_walls": sum(v == 5 for row in grid for v in row),
            "source_side": side, "wall_stop": int(trace["termination"] == "wall")}


def _max_three_reflections(grid):
    return _trace_output(grid, max_reflections=3)


def _alternating_mirrors(grid):
    return _trace_output(grid, alternating=True)


def _ignore_mirrors(grid):
    return _trace_output(grid, ignore_mirrors=True)


def _ignore_walls(grid):
    return _trace_output(grid, ignore_walls=True)


def _swap_mirrors(grid):
    return _trace_output(grid, swap_mirrors=True)


def _wall_after_last_mirror_only(grid):
    """Rival: honor a wall only if ignoring walls reaches no further mirror."""
    actual = _trace(grid)
    through_wall = _trace(grid, ignore_walls=True)
    if len(through_wall["mirrors"]) > len(actual["mirrors"]):
        return _trace_output(grid, ignore_walls=True)
    return _trace_output(grid)


def _long_route_witness(grid):
    return _max_three_reflections(grid) != _trace_output(grid)


def _repeated_mirror_witness(grid):
    return _alternating_mirrors(grid) != _trace_output(grid)


def _active_wall_witness(grid):
    return _ignore_walls(grid) != _trace_output(grid)


def _reflection_witness(grid):
    return _ignore_mirrors(grid) != _trace_output(grid)


def _mirror_handedness_witness(grid):
    return _swap_mirrors(grid) != _trace_output(grid)


def _occluded_mirror_witness(grid):
    return _wall_after_last_mirror_only(grid) != _trace_output(grid)


SEMANTIC_RIVALS = {
    "max_three_reflections": _max_three_reflections,
    "alternating_mirrors": _alternating_mirrors,
    "ignore_mirrors": _ignore_mirrors,
    "ignore_walls": _ignore_walls,
    "swap_mirrors": _swap_mirrors,
    "wall_after_last_mirror_only": _wall_after_last_mirror_only,
}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name]
                       for name in ("max_three_reflections", "alternating_mirrors",
                                    "wall_after_last_mirror_only")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "long_route": _long_route_witness,
    "repeated_mirror": _repeated_mirror_witness,
    "active_wall": _active_wall_witness,
    "reflection": _reflection_witness,
    "mirror_handedness": _mirror_handedness_witness,
    "occluded_mirror": _occluded_mirror_witness,
}
WITNESS_RIVALS = {
    "long_route": ["max_three_reflections"],
    "repeated_mirror": ["alternating_mirrors"],
    "active_wall": ["ignore_walls"],
    "reflection": ["ignore_mirrors"],
    "mirror_handedness": ["swap_mirrors"],
    "occluded_mirror": ["wall_after_last_mirror_only"],
}


def lesson_identifiable(demos, query):
    """Finite-rival teaching contract, not a claim of universal induction.

    All declared competitors must be refuted by an actual demonstration.
    Query answers are not used to decide whether a lesson is identifiable.
    """
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one visible demonstration is required"]
    if any(not isinstance(pair, dict) or "input" not in pair or "output" not in pair
           for pair in demos):
        return ["demonstrations must contain input and output"]
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not refute {name}")
    return reasons

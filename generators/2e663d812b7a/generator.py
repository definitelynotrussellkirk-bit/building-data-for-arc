"""Inputs for 9356391f: a positional key drives clipped Chebyshev rings.

The canonical Racket rule remains the label authority. Internal zeros, repeated
colors, the gray separator, and partial rings are meaningful. The alternating
curriculum supplies an informative top-clipped example in every three demos;
the other draws cover complete rings, other edges, rectangles and simpler keys.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2e663d812b7a"
TASK_ID = GENERATOR_ID
VERSION = "1.3.0"
RULE_HASH = "f67ec6a58878"
# The exact key_len=1 override is lawful and intentionally changes no pixels.
# Ordinary curriculum keys have length >=2 and still teach nonidentity rules.
ALLOW_IDENTITY_OUTPUT = True
SUMMARY = "Positional row-0 key, gray separator, and one lower seed for clipped square rings."
INVARIANTS = [
    "row 0 begins with a nonzero key; internal zeros and repeated colors retain their positions",
    "row 1 is a full color-5 separator; lower background is color 0",
    "exactly one lower seed has the first key color",
    "keys use 1..6 distinct colors other than 0 and 5 and end in a nonzero entry",
    "all exact overrides are reconstructed from returned pixels; contradictions are rejected",
]
AXES = {
    "grid_h": {"type": "int", "default": "scheduled 16, 30 or rng 9..30", "valid": "9..30"},
    "grid_w": {"type": "int", "default": "scheduled 16, 30 or rng 9..30", "valid": "9..30"},
    "key_len": {"type": "int", "default": "curriculum 2..10", "valid": "1..10"},
    "palette_size": {"type": "int", "default": "four or feasible rng", "valid": "1..6"},
    "zero_rings": {"type": "int", "default": "one or feasible rng", "valid": "0..8"},
    "seed_r": {"type": "int", "default": "top witness or rng", "valid": "2..h-1"},
    "seed_c": {"type": "int", "default": "interior witness or rng", "valid": "0..w-1"},
}
# Precise conflicts carry their actual axes on the exception. No blanket pair
# declaration hides an accidental failure of an otherwise feasible tuple.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("rich_top", "varied")
# The ring witness still alternates. The full default size mixture repeats
# every ten draws: three canonical anchors, two 30x30, four large, one small.
LESSON_SCHEDULE_PERIOD = 10
_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


class IncompatibleOverrides(ValueError):
    def __init__(self, message, axes):
        super().__init__(message)
        self.incompatible_axes = tuple(axes)


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[(int(seed) + int(sample_index)) % 2]


def _reject(message, overrides, *axes):
    raise IncompatibleOverrides(message, [name for name in axes if name in overrides])


def _draw(ctx, name, lo, hi, preferred=()):
    """An override uses the full feasible domain; defaults use keyed preferences."""
    if name in ctx.overrides:
        return ctx.draw_int(name, lo, hi)
    choices = [value for value in preferred if lo <= value <= hi]
    return ctx.draw_choice(name, choices or tuple(range(lo, hi + 1)))


def _key(ctx, length, palette_size, zero_rings, rich):
    colors = ctx.draw_distinct_colors("key_colors", n=palette_size, exclude={0, 5})
    interior = list(range(1, length - 1))
    late = list(range(3, length - 1))
    gap_slots = late if rich and len(late) >= zero_rings else interior
    zeros = set(ctx.draw_rng("zero_positions").sample(gap_slots, zero_rings))
    positions = [c for c in range(length) if c not in zeros]
    result = [0] * length
    remaining = list(positions)
    unused = list(colors)
    if rich and palette_size >= 2 and len(positions) > palette_size and {0, 1, 2}.issubset(positions):
        result[0], result[1], result[2] = colors[0], colors[1], colors[1]
        remaining = [c for c in positions if c not in (0, 1, 2)]
        unused = list(colors[2:])
    # Every chosen palette color is realized before filling repeated slots.
    shuffled = list(remaining)
    ctx.draw_rng("color_positions").shuffle(shuffled)
    for c, color in zip(shuffled, unused):
        result[c] = color
    rng = ctx.draw_rng("repeated_colors")
    for c in positions:
        if result[c] == 0:
            result[c] = rng.choice(colors)
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer, not a coerced scalar")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty is not None and (type(difficulty) is not str
                                   or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    overrides = {name: value for name, value in overrides.items() if value is not None}
    for name, value in overrides.items():
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    limits = {"grid_h": (9, 30), "grid_w": (9, 30), "key_len": (1, 10),
              "palette_size": (1, 6), "zero_rings": (0, 8),
              "seed_r": (2, 29), "seed_c": (0, 29)}
    for name, value in overrides.items():
        lo, hi = limits[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rich = schedule_profile(seed, sample_index, difficulty) == "rich_top"
    mode = "rich" if rich else ctx.draw_choice("layout_mode", ("complete", "complete", "edge", "free"))
    pinned_palette = overrides.get("palette_size", 1)
    pinned_zeros = overrides.get("zero_rings", 0)
    min_key = max(pinned_palette + pinned_zeros, pinned_zeros + 2 if pinned_zeros else 1)
    if min_key > 10:
        _reject("palette_size plus zero_rings cannot fit a key of length <=10", overrides,
                "palette_size", "zero_rings")
    if overrides.get("key_len", 10) < min_key:
        _reject("key_len cannot contain the requested palette and internal zero rings", overrides,
                "key_len", "palette_size", "zero_rings")
    min_h = max(9, overrides.get("seed_r", 2) + 1)
    min_w = max(9, overrides.get("seed_c", 0) + 1, overrides.get("key_len", min_key))
    if overrides.get("grid_h", 30) < min_h:
        _reject("seed_r lies outside grid_h", overrides, "grid_h", "seed_r")
    if overrides.get("grid_w", 30) < min_w:
        _reject("grid_w cannot fit the requested key or seed_c", overrides,
                "grid_w", "key_len", "palette_size", "zero_rings", "seed_c")
    size_slot = (seed + sample_index) % LESSON_SCHEDULE_PERIOD
    if rich:
        h_choices = w_choices = (16,) if size_slot in (0, 2, 4) else (30,)
    elif size_slot == 9:
        h_choices = w_choices = tuple(range(9, 19))
    else:
        # Both axes still honor exact overrides. One unpinned preferred side
        # is large; the other varies independently to include rectangles.
        long_axis = ctx.draw_choice("long_axis", ("height", "width"))
        h_choices = tuple(range(21, 31)) if long_axis == "height" else tuple(range(9, 31))
        w_choices = tuple(range(21, 31)) if long_axis == "width" else tuple(range(9, 31))
    h = _draw(ctx, "grid_h", min_h, 30, h_choices)
    w = _draw(ctx, "grid_w", min_w, 30, w_choices)
    max_key = min(10, w)
    if min_key > max_key:
        _reject("requested key content cannot fit grid_w", overrides,
                "grid_w", "palette_size", "zero_rings")
    full_key_limit = min((h - 3) // 2, (w - 1) // 2) + 1
    if rich:
        favored_keys = (6, 6, 7) if difficulty == "easy" else ((7, 8, 8) if difficulty == "hard" else (6, 7, 8))
    elif mode == "complete":
        largest = 10 if max(h, w) > 20 else 6
        favored_keys = tuple(range(max(2, min_key), min(largest, full_key_limit, max_key) + 1))
    else:
        smallest, largest = (6, 10) if max(h, w) > 20 else (2, 8)
        favored_keys = tuple(range(max(smallest, min_key), min(largest, max_key) + 1))
    length = _draw(ctx, "key_len", min_key, max_key, favored_keys)
    max_zeros = min(8, max(0, length - 2), length - pinned_palette)
    if pinned_zeros > max_zeros:
        _reject("zero_rings cannot fit the key endpoints and palette", overrides,
                "zero_rings", "key_len", "palette_size")
    gaps = _draw(ctx, "zero_rings", 0, max_zeros, (1,) if rich else (0, 0, 1, 2))
    palette = _draw(ctx, "palette_size", 1, min(6, length - gaps), (4,) if rich else (2, 3, 4, 4))
    key = _key(ctx, length, palette, gaps, rich)
    if rich:
        r_choices, c_choices = (3,), tuple(range(4, w - 4))
    elif mode == "complete" and length <= full_key_limit:
        r_choices = tuple(range(length + 1, h - length + 1))
        c_choices = tuple(range(length - 1, w - length + 1))
    elif mode == "edge":
        edge = ctx.draw_choice("edge", ("top", "bottom", "left", "right"))
        r_choices = (2, 3) if edge == "top" else ((h - 2, h - 1) if edge == "bottom" else ())
        c_choices = (0, 1) if edge == "left" else ((w - 2, w - 1) if edge == "right" else ())
    else:
        r_choices, c_choices = (), ()
    sr = _draw(ctx, "seed_r", 2, h - 1, r_choices)
    sc = _draw(ctx, "seed_c", 0, w - 1, c_choices)
    grid = full_grid(h, w, 0)
    grid[0][:length] = key
    grid[1] = [5] * w
    grid[sr][sc] = key[0]
    return grid


def _parts(grid):
    last = max(c for c, value in enumerate(grid[0]) if value != 0)
    seed = [(r, c) for r in range(2, len(grid)) for c, value in enumerate(grid[r]) if value != 0]
    if len(seed) != 1:
        raise ValueError("expected exactly one lower seed")
    return grid[0][:last + 1], seed[0]


def observe_overrides(grid):
    key, (sr, sc) = _parts(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "key_len": len(key),
            "palette_size": len(set(key) - {0}), "zero_rings": key.count(0),
            "seed_r": sr, "seed_c": sc}


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the input grammar, independently of claimed metadata."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer colors 0..9 (not booleans)"]
    if not 9 <= len(grid) <= 30 or not 9 <= width <= 30:
        return ["grid dimensions must be in the declared 9..30 domain"]
    errors = []
    if grid[1] != [5] * width:
        errors.append("row 1 must be the full color-5 separator")
    if grid[0][0] not in _COLORS:
        errors.append("key must start with a nonzero, nonseparator color")
    if 5 in grid[0]:
        errors.append("input key cannot use separator color 5")
    try:
        key, (sr, sc) = _parts(grid)
    except ValueError as exc:
        return errors + [str(exc)]
    if not 1 <= len(key) <= min(10, width):
        errors.append("key length must be in 1..min(10,width)")
    if len(set(key) - {0}) > 6:
        errors.append("key palette must have at most six nonzero colors")
    if grid[sr][sc] != key[0]:
        errors.append("seed color must match key[0]")
    return errors


def strict_canonical_like(grid):
    """Task grammar, allowing its declared sizes and clipping rather than replaying examples."""
    return self_check(grid)


# Authoring-only rivals. Racket remains the label authority.
def _semantic_parts(grid):
    """Parse this task's domain; internal zero and repeated key entries are legal."""
    if not isinstance(grid, (list, tuple)) or len(grid) < 3:
        raise ValueError("grid needs a key row, separator row, and lower canvas")
    if (not isinstance(grid[0], (list, tuple)) or not grid[0]
            or any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0])
                   for row in grid)):
        raise ValueError("grid must be nonempty and rectangular")
    if any(type(color) is not int or not 0 <= color <= 9
           for row in grid for color in row):
        raise ValueError("grid colors must be integers in 0..9")
    h, w = len(grid), len(grid[0])
    if any(color != 5 for color in grid[1]):
        raise ValueError("row 1 must be a full color-5 separator")
    if grid[0][0] in (0, 5):
        raise ValueError("row 0 must start with a nonzero, non-separator key color")
    if 5 in grid[0]:
        raise ValueError("input key colors must exclude separator color 5")
    key_len = max(c + 1 for c, color in enumerate(grid[0]) if color != 0)
    key = list(grid[0][:key_len])
    seeds = [(r, c) for r in range(2, h) for c in range(w) if grid[r][c] != 0]
    if len(seeds) != 1:
        raise ValueError("lower canvas must contain exactly one nonzero seed")
    seed_r, seed_c = seeds[0]
    if grid[seed_r][seed_c] != key[0]:
        raise ValueError("seed color must match the first key entry")
    complete_radius = min(seed_r - 2, h - 1 - seed_r, seed_c, w - 1 - seed_c)
    return h, w, key, seed_r, seed_c, complete_radius


def _semantic_model(grid, *, marker_mode="canonical", key_mode="canonical",
                    metric="chebyshev", complete_only=False):
    """Independent, local audit model, with explicit plausible rival switches.

    This is never called by generate() to label a sample. The semantic gate
    checks its distinguishing claims against the selected Racket authority.
    """
    h, w, original_key, seed_r, seed_c, complete_radius = _semantic_parts(grid)
    out = [list(row) for row in grid]
    marker_radius = complete_radius
    if marker_mode == "top_is_row_zero":
        marker_radius = min(seed_r, h - 1 - seed_r, seed_c, w - 1 - seed_c)
    elif marker_mode == "bottom_only":
        marker_radius = h - 1 - seed_r
    if marker_mode != "leave_header_unchanged":
        for c in range(marker_radius + 1, len(original_key)):
            if marker_mode == "last_only" and c != len(original_key) - 1:
                continue
            if original_key[c] != 0 or marker_mode == "gray_active_zeros":
                out[0][c] = 5
    body_key = original_key
    if key_mode == "drop_zero_keys":
        body_key = [color for color in original_key if color != 0]
    elif key_mode == "deduplicate_key":
        body_key = []
        for color in original_key:
            if color not in body_key:
                body_key.append(color)
    elif key_mode == "use_marked_key":
        body_key = out[0][:len(original_key)]
    for r in range(2, h):
        for c in range(w):
            if metric == "manhattan":
                distance = abs(r - seed_r) + abs(c - seed_c)
            else:
                distance = max(abs(r - seed_r), abs(c - seed_c))
            if (distance < len(body_key)
                    and (not complete_only or distance <= complete_radius)):
                out[r][c] = body_key[distance]
    return out


def _semantic_top_is_row_zero(grid):
    return _semantic_model(grid, marker_mode="top_is_row_zero")


def _semantic_bottom_only(grid):
    return _semantic_model(grid, marker_mode="bottom_only")


def _semantic_last_only(grid):
    return _semantic_model(grid, marker_mode="last_only")


def _semantic_gray_active_zeros(grid):
    return _semantic_model(grid, marker_mode="gray_active_zeros")


def _semantic_drop_zero_keys(grid):
    return _semantic_model(grid, key_mode="drop_zero_keys")


def _semantic_deduplicate_key(grid):
    return _semantic_model(grid, key_mode="deduplicate_key")


def _semantic_manhattan_distance(grid):
    return _semantic_model(grid, metric="manhattan")


def _semantic_leave_header_unchanged(grid):
    return _semantic_model(grid, marker_mode="leave_header_unchanged")


def _semantic_use_marked_key(grid):
    return _semantic_model(grid, key_mode="use_marked_key")


def _semantic_complete_rings_only(grid):
    return _semantic_model(grid, complete_only=True)


SEMANTIC_RIVALS = {
    "top_is_row_zero": _semantic_top_is_row_zero,
    "bottom_only": _semantic_bottom_only,
    "last_only": _semantic_last_only,
    "gray_active_zeros": _semantic_gray_active_zeros,
    "drop_zero_keys": _semantic_drop_zero_keys,
    "deduplicate_key": _semantic_deduplicate_key,
    "manhattan_distance": _semantic_manhattan_distance,
    "leave_header_unchanged": _semantic_leave_header_unchanged,
    "use_marked_key": _semantic_use_marked_key,
    "complete_rings_only": _semantic_complete_rings_only,
}

# These four rivals fit all six stored canonical pairs (three unique pairs).
# Their obligations therefore require generated, Racket-verified witnesses.
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("top_is_row_zero", "bottom_only", "last_only", "gray_active_zeros")
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _semantic_refutes(grid, rival_name):
    if strict_canonical_like(grid):
        return False
    return _semantic_model(grid) != SEMANTIC_RIVALS[rival_name](grid)


SEMANTIC_WITNESSES = {
    "distinguishes_" + name: (lambda grid, name=name: _semantic_refutes(grid, name))
    for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {
    "distinguishes_" + name: [name] for name in SEMANTIC_RIVALS
}


def lesson_identifiable(demos, query):
    """Report a demo-fitting declared rival only when it changes the query.

    Answer-equivalent survivors are lawful for the current lesson. This is
    finite evidence against named rivals, not proof against all possible rules.
    Declarations are looked up on every call so added competitors are audited.
    """
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["lesson needs at least one demonstration"]
    pairs = list(demos) + [query]
    if any(not isinstance(pair, dict) or "input" not in pair or "output" not in pair
           for pair in pairs):
        return ["demonstrations and query must contain input and authoritative output"]
    competitors = dict(LESSON_COMPETITORS)
    for name, rival in CANONICAL_SHORTCUTS.items():
        competitors.setdefault(name, rival)
    if not competitors:
        return ["no declared lesson competitors are available"]
    reasons = []
    for name, rival in sorted(competitors.items()):
        fits_demos = all(
            rival([list(row) for row in demo["input"]]) == demo["output"]
            for demo in demos
        )
        if (fits_demos
                and rival([list(row) for row in query["input"]]) != query["output"]):
            reasons.append("query-changing rival " + name + " fits every demonstration")
    return reasons

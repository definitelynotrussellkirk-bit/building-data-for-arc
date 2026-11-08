"""Semantic generator for ARC task bf53d21ff9fc (source 182e5d0f).

For every gray marker, the canonical rule follows the first adjacent green
route using cardinal-neighbor priority.  It clears the traversed route to the
orange background, leaves the final route cell green, moves gray to the
penultimate route cell, and clears the marker's original position.  Markers
without an adjacent route and all zero/dormant-route distractors are preserved.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "bf53d21ff9fc"
TASK_ID = "bf53d21ff9fc"
VERSION = "3.1.0"
RULE_HASH = "29e5cb809c58"
SUMMARY = "Move each active gray marker to the penultimate cell of its adjacent green route while preserving inactive markers, endpoint green, zeros, and unrelated cells."
INVARIANTS = [
    "calibrated grids use orange 7 as background plus green 3 routes, gray 5 markers, and zero endpoint caps",
    "one through four gray markers may be present and at least one has an adjacent route of length two or more",
    "active routes are simple nonbranching cardinal paths and are mutually disjoint",
    "inactive gray markers and dormant green route components remain unchanged",
    "each active trail is cleared except for a gray penultimate cell and green final cell",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = ("single_active", "multi_active", "mixed_markers", "dormant_routes")
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four complete official route scenes plus four labeled active/inactive/dormant contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

CARDINAL_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))

_PUBLIC_ROWS = {
    "public_1": (
        "030777777777", "733333333333", "777777777775", "777777777777",
        "777777777777", "077777777777", "337777777777", "037777777770",
        "737777777733", "737777777730", "737777777737", "775777777537",
    ),
    "public_2": (
        "777777777", "077777777", "333777777", "073777777", "773777777",
        "773777777", "773777777", "773777777", "773577777",
    ),
    "public_3": (
        "5370307777777", "7377333337777", "7377777777775", "7377777777777",
        "0377777777777", "3377777777777", "0777777777777", "7777777777777",
        "7777777777777", "7777777777777", "0777777777775", "3377773333377",
        "0357703077777",
    ),
    "public_4": (
        "73577777770307", "73777777777333", "73777777777775", "73777777777777",
        "73777777777777", "03777777777777", "33777777777777", "07777777777777",
        "77777777777777", "77777777777777", "07777777777777", "33777777777777",
        "03777777773377", "77577777703075",
    ),
}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_EXACT = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["input must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["input must contain one through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _positions(grid, color):
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]


def _trace(grid, marker):
    """Exact original-grid route trace used by the canonical program."""
    height, width = len(grid), len(grid[0])
    marker_row, marker_col = marker
    start_delta = next(
        (
            (row_delta, col_delta)
            for row_delta, col_delta in CARDINAL_DELTAS
            if 0 <= marker_row + row_delta < height
            and 0 <= marker_col + col_delta < width
            and grid[marker_row + row_delta][marker_col + col_delta] == 3
        ),
        None,
    )
    if start_delta is None:
        return []
    current = (marker_row + start_delta[0], marker_col + start_delta[1])
    previous = marker
    trail = [current]
    for _ in range(max(height, width)):
        next_delta = next(
            (
                (row_delta, col_delta)
                for row_delta, col_delta in CARDINAL_DELTAS
                if 0 <= current[0] + row_delta < height
                and 0 <= current[1] + col_delta < width
                and grid[current[0] + row_delta][current[1] + col_delta] == 3
                and (current[0] + row_delta, current[1] + col_delta) != previous
            ),
            None,
        )
        if next_delta is not None:
            following = (current[0] + next_delta[0], current[1] + next_delta[1])
            previous, current = current, following
            trail.append(following)
    return trail


def rule_mirror(grid):
    """Broad, input-pure mirror of the canonical multi-marker Racket rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for marker in _positions(grid, 5):
        trail = _trace(grid, marker)
        if len(trail) < 2:
            continue
        for row, col in trail:
            output[row][col] = 7
        last_row, last_col = trail[-1]
        second_row, second_col = trail[-2]
        output[last_row][last_col] = 3
        output[second_row][second_col] = 5
        output[marker[0]][marker[1]] = 7
    return output


def _rival_endpoint_landing(grid):
    """Wrong rule: move gray onto the final route cell instead of penultimate."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for marker in _positions(grid, 5):
        trail = _trace(grid, marker)
        if len(trail) < 2:
            continue
        for row, col in trail:
            output[row][col] = 7
        last_row, last_col = trail[-1]
        output[last_row][last_col] = 5
        output[marker[0]][marker[1]] = 7
    return output


def _rival_preserve_route(grid):
    """Wrong rule: relocate gray but leave the traversed green route in place."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for marker in _positions(grid, 5):
        trail = _trace(grid, marker)
        if len(trail) < 2:
            continue
        second_row, second_col = trail[-2]
        output[second_row][second_col] = 5
        output[marker[0]][marker[1]] = 7
    return output


def _green_components(grid):
    height, width = len(grid), len(grid[0])
    green = set(_positions(grid, 3))
    components = []
    while green:
        start = min(green)
        green.remove(start)
        stack = [start]
        cells = []
        while stack:
            row, col = stack.pop()
            cells.append((row, col))
            for row_delta, col_delta in CARDINAL_DELTAS:
                neighbor = (row + row_delta, col + col_delta)
                if neighbor in green:
                    green.remove(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(cells)))
    return components


def _foreground_signature(grid):
    cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 7
    ]
    if not cells:
        return ()
    row0 = min(row for row, _, _ in cells)
    col0 = min(col for _, col, _ in cells)
    return tuple(sorted((row - row0, col - col0, value) for row, col, value in cells))


def _normalize_colored(cells):
    row0 = min(row for row, _, _ in cells)
    col0 = min(col for _, col, _ in cells)
    return tuple(sorted((row - row0, col - col0, value) for row, col, value in cells))


def _d4_colored_variants(signature):
    variants = set()
    base = tuple(signature)
    for mirrored in (False, True):
        transformed = tuple(
            (row, -col, value) if mirrored else (row, col, value)
            for row, col, value in base
        )
        for _ in range(4):
            variants.add(_normalize_colored(transformed))
            transformed = tuple((col, -row, value) for row, col, value in transformed)
    return tuple(sorted(variants))


_PUBLIC_FAMILY_KEYS = {
    min(_d4_colored_variants(_foreground_signature(grid))): profile
    for profile, grid in _PUBLIC_INPUTS.items()
}


def _public_family(grid):
    signature = _foreground_signature(grid)
    if not signature:
        return None
    return _PUBLIC_FAMILY_KEYS.get(min(_d4_colored_variants(signature)))


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    height, width = len(grid), len(grid[0])
    if not 7 <= height <= 30 or not 7 <= width <= 30:
        errors.append("calibrated canvas dimensions must be seven through thirty")
    palette = {value for row in grid for value in row}
    if not palette <= {0, 3, 5, 7} or not {0, 3, 5, 7} <= palette:
        errors.append("calibrated palette must contain exactly zero, green 3, gray 5, and orange 7")
    markers = _positions(grid, 5)
    if not 1 <= len(markers) <= 4:
        errors.append(f"expected one through four gray markers, got {len(markers)}")
    traces = {marker: _trace(grid, marker) for marker in markers}
    active = [marker for marker in markers if len(traces[marker]) >= 2]
    adjacent_short = [marker for marker in markers if len(traces[marker]) == 1]
    inactive = [marker for marker in markers if not traces[marker]]
    if not active:
        errors.append("at least one gray marker must have a route of length two or more")
    if adjacent_short:
        errors.append("a calibrated active marker may not point to a one-cell route")
    used = set()
    for marker in active:
        trail = traces[marker]
        if len(set(trail)) != len(trail):
            errors.append("active routes must not cycle under canonical priority traversal")
        if used.intersection(trail):
            errors.append("active routes must be mutually disjoint")
        used.update(trail)
    green_components = _green_components(grid)
    component_by_cell = {
        cell: component for component in green_components for cell in component
    }
    active_components = set()
    for marker in active:
        trail = traces[marker]
        component = component_by_cell.get(trail[0], ())
        if set(component) != set(trail):
            errors.append("each active route must be one complete simple green component")
        active_components.add(component)
        for index, cell in enumerate(trail):
            degree = sum(
                (cell[0] + row_delta, cell[1] + col_delta) in component
                for row_delta, col_delta in CARDINAL_DELTAS
            )
            expected_degree = 1 if index in (0, len(trail) - 1) else 2
            if degree != expected_degree:
                errors.append("active routes must be nonbranching cardinal paths")
                break
    dormant = [component for component in green_components if component not in active_components]
    exact = None
    try:
        exact = _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        pass
    public = exact or _public_family(grid)
    if public is not None:
        profile = public
    elif len(active) == 1 and not inactive and not dormant:
        profile = "single_active"
    elif len(active) >= 2 and not inactive and not dormant:
        profile = "multi_active"
    elif active and inactive:
        profile = "mixed_markers"
    elif active and not inactive and dormant:
        profile = "dormant_routes"
    else:
        profile = None
    if profile is None and not errors:
        errors.append("unsupported calibrated active/inactive/dormant route signature")
    output = rule_mirror(grid) if markers else None
    if output == [list(row) for row in grid]:
        errors.append("calibrated lesson must contain a visibly active marker")
    return {
        "errors": errors,
        "scene_profile": profile if not errors else None,
        "facts": {
            "markers": tuple(markers),
            "active_markers": tuple(active),
            "inactive_markers": tuple(inactive),
            "traces": traces,
            "active_lengths": tuple(len(traces[marker]) for marker in active),
            "green_components": tuple(green_components),
            "dormant_components": tuple(dormant),
            "zero_count": len(_positions(grid, 0)),
            "palette": tuple(sorted(palette)),
        },
        "output": output,
    }


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    profile = analysis["scene_profile"]
    return profile if profile in PUBLIC_PROFILES and not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def strict_canonical_like(grid):
    """Accept the calibrated route-scene manifold shared by authority and generator."""
    return list(self_check(grid))


def _facts_if_valid(grid):
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis["facts"]


def _witness_penultimate_not_endpoint(grid):
    facts = _facts_if_valid(grid)
    return bool(facts and any(length >= 2 for length in facts["active_lengths"]))


def _witness_route_is_consumed(grid):
    facts = _facts_if_valid(grid)
    return bool(facts and any(length >= 3 for length in facts["active_lengths"]))


def _witness_multiple_active_markers(grid):
    facts = _facts_if_valid(grid)
    return bool(facts and len(facts["active_markers"]) >= 2)


def _witness_inactive_marker_preserved(grid):
    facts = _facts_if_valid(grid)
    return bool(facts and facts["inactive_markers"])


def _witness_dormant_route_preserved(grid):
    facts = _facts_if_valid(grid)
    return bool(facts and facts["dormant_components"])


SEMANTIC_RIVALS = {
    "endpoint_landing": _rival_endpoint_landing,
    "preserve_route": _rival_preserve_route,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "penultimate_not_endpoint": _witness_penultimate_not_endpoint,
    "route_is_consumed": _witness_route_is_consumed,
    "multiple_active_markers": _witness_multiple_active_markers,
    "inactive_marker_preserved": _witness_inactive_marker_preserved,
    "dormant_route_preserved": _witness_dormant_route_preserved,
}
WITNESS_RIVALS = {
    "penultimate_not_endpoint": ["endpoint_landing"],
    "route_is_consumed": ["preserve_route"],
}
BRANCH_WITNESSES = (
    "multiple_active_markers",
    "inactive_marker_preserved",
    "dormant_route_preserved",
)


def lesson_identifiable(demos, query):
    """Require valid exact demonstrations to refute every query-changing rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    query_errors = self_check(query["input"])
    if query_errors:
        return [f"query input is invalid: {query_errors[0]}"]

    reasons = []
    refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the exact route transformation")
            continue
        for name, rival in SEMANTIC_RIVALS.items():
            if rival(demo["input"]) != expected:
                refuted[name] = True

    expected_query = rule_mirror(query["input"])
    for name, was_refuted in refuted.items():
        if not was_refuted and SEMANTIC_RIVALS[name](query["input"]) != expected_query:
            reasons.append(f"demonstrations do not refute query-disagreeing rival {name}")
    return reasons


def _transform_colored(cells, rng):
    transformed = tuple(cells)
    for _ in range(rng.randrange(4)):
        transformed = tuple((col, -row, value) for row, col, value in transformed)
    if rng.random() < 0.5:
        transformed = tuple((row, -col, value) for row, col, value in transformed)
    return _normalize_colored(transformed)


def _limits(difficulty):
    if difficulty == "easy":
        return 10, 20
    if difficulty == "hard":
        return 16, 24
    return 12, 20


def _embed_public(profile, difficulty, rng):
    signature = _foreground_signature(_PUBLIC_INPUTS[profile])
    transformed = _transform_colored(signature, rng)
    motif_height = max(row for row, _, _ in transformed) + 1
    motif_width = max(col for _, col, _ in transformed) + 1
    low, high = _limits(difficulty)
    if motif_height > high or motif_width > high:
        high = max(high, motif_height, motif_width)
    height = rng.randint(max(low, motif_height), high)
    width = rng.randint(max(low, motif_width), high)
    row0 = rng.randint(0, height - motif_height)
    col0 = rng.randint(0, width - motif_width)
    grid = [[7] * width for _ in range(height)]
    for row, col, value in transformed:
        grid[row0 + row][col0 + col] = value
    return grid


def _route_tokens(length, bent, rng, *, active):
    if bent and length >= 5:
        first_length = rng.randint(3, length - 2)
        second_length = length - first_length + 1
        path = [(0, col) for col in range(first_length)]
        path.extend((row, first_length - 1) for row in range(1, second_length))
    else:
        path = [(0, col) for col in range(length)]
    marker = (0, -1)
    previous, endpoint = path[-2], path[-1]
    direction = (endpoint[0] - previous[0], endpoint[1] - previous[1])
    perpendicular = (-direction[1], direction[0])
    caps = (
        (endpoint[0] + perpendicular[0], endpoint[1] + perpendicular[1]),
        (endpoint[0] - perpendicular[0], endpoint[1] - perpendicular[1]),
    )
    tokens = [(row, col, 3) for row, col in path]
    tokens.extend((row, col, 0) for row, col in caps)
    if active:
        tokens.append((marker[0], marker[1], 5))
    rotations = rng.randrange(4)
    for _ in range(rotations):
        path = [(col, -row) for row, col in path]
        tokens = [(col, -row, value) for row, col, value in tokens]
    if rng.random() < 0.5:
        path = [(row, -col) for row, col in path]
        tokens = [(row, -col, value) for row, col, value in tokens]
    row0 = min(row for row, _, _ in tokens)
    col0 = min(col for _, col, _ in tokens)
    tokens = [(row - row0, col - col0, value) for row, col, value in tokens]
    path = [(row - row0, col - col0) for row, col in path]
    return tuple(tokens), tuple(path)


def _can_place(grid, tokens, path, active):
    height, width = len(grid), len(grid[0])
    token_cells = {(row, col) for row, col, _ in tokens}
    if len(token_cells) != len(tokens):
        return False
    if any(not (0 <= row < height and 0 <= col < width) for row, col in token_cells):
        return False
    if any(grid[row][col] != 7 for row, col in token_cells):
        return False
    existing_green = set(_positions(grid, 3))
    path_set = set(path)
    if any(
        (row + row_delta, col + col_delta) in existing_green
        for row, col in path_set
        for row_delta, col_delta in CARDINAL_DELTAS
    ):
        return False
    if active:
        marker = next((row, col) for row, col, value in tokens if value == 5)
        green_neighbors = {
            (marker[0] + row_delta, marker[1] + col_delta)
            for row_delta, col_delta in CARDINAL_DELTAS
            if (marker[0] + row_delta, marker[1] + col_delta) in path_set
        }
        if green_neighbors != {path[0]}:
            return False
    return True


def _place_route(grid, length, bent, active, rng):
    for _ in range(400):
        base_tokens, base_path = _route_tokens(length, bent, rng, active=active)
        motif_height = max(row for row, _, _ in base_tokens) + 1
        motif_width = max(col for _, col, _ in base_tokens) + 1
        if motif_height > len(grid) or motif_width > len(grid[0]):
            continue
        row0 = rng.randint(0, len(grid) - motif_height)
        col0 = rng.randint(0, len(grid[0]) - motif_width)
        tokens = tuple((row + row0, col + col0, value) for row, col, value in base_tokens)
        path = tuple((row + row0, col + col0) for row, col in base_path)
        if not _can_place(grid, tokens, path, active):
            continue
        for row, col, value in tokens:
            grid[row][col] = value
        return True
    return False


def _place_inactive_marker(grid, rng):
    greens = set(_positions(grid, 3))
    for _ in range(500):
        row, col = rng.randrange(len(grid)), rng.randrange(len(grid[0]))
        if grid[row][col] != 7:
            continue
        if any(
            (row + row_delta, col + col_delta) in greens
            for row_delta, col_delta in CARDINAL_DELTAS
        ):
            continue
        grid[row][col] = 5
        return True
    return False


def _general_counts(profile, difficulty, rng):
    if profile == "single_active":
        return 1, 0, 0
    if profile == "multi_active":
        return (2 if difficulty == "easy" else rng.randint(2, 3) if difficulty != "hard" else rng.randint(3, 4)), 0, 0
    if profile == "mixed_markers":
        active = 1 if difficulty == "easy" else rng.randint(1, 2)
        inactive = 1 if difficulty != "hard" else rng.randint(1, 2)
        dormant = 1 if difficulty == "hard" and rng.random() < 0.5 else 0
        return active, inactive, dormant
    if profile == "dormant_routes":
        return (1 if difficulty == "easy" else rng.randint(1, 2)), 0, (1 if difficulty != "hard" else rng.randint(1, 2))
    raise ValueError(f"unknown generalized profile: {profile!r}")


def _length_range(difficulty, route_count):
    if difficulty == "easy":
        return 4, 6
    if difficulty == "hard":
        return (6, 10 if route_count >= 3 else 12)
    return 5, 9


def _default_profile_choices(sample_index):
    """Choose canonical-scale anchors before drawing the keyed profile axis."""
    if sample_index % 4 == 0:
        return list(GENERAL_PROFILES)
    return list(PUBLIC_PROFILES) * 3 + list(GENERAL_PROFILES) * 2


def _anchor_canvas_size(profile, difficulty, sample_index):
    options = {
        "single_active": (9, 12, 13, 14),
        "multi_active": (12, 13, 14) if difficulty != "hard" else (14,),
        "mixed_markers": (9, 12, 13, 14) if difficulty != "hard" else (12, 13, 14),
        "dormant_routes": (12, 13, 14) if difficulty != "hard" else (14,),
    }[profile]
    return options[(sample_index // 4) % len(options)]


def _random_general(profile, difficulty, rng, *, canvas_size=None):
    low, high = _limits(difficulty)
    for _ in range(300):
        if canvas_size is None:
            height, width = rng.randint(low, high), rng.randint(low, high)
        else:
            height, width = canvas_size
        grid = [[7] * width for _ in range(height)]
        active_count, inactive_count, dormant_count = _general_counts(profile, difficulty, rng)
        route_count = active_count + dormant_count
        length_low, length_high = _length_range(difficulty, route_count)
        success = True
        for _ in range(active_count):
            length = rng.randint(length_low, length_high)
            if not _place_route(grid, length, rng.random() < 0.65, True, rng):
                success = False
                break
        if not success:
            continue
        for _ in range(dormant_count):
            length = rng.randint(max(3, length_low - 1), length_high)
            if not _place_route(grid, length, rng.random() < 0.65, False, rng):
                success = False
                break
        if not success:
            continue
        for _ in range(inactive_count):
            if not _place_inactive_marker(grid, rng):
                success = False
                break
        if not success:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct route lesson {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_options = (
        list(SCENE_PROFILES)
        if overrides.get("scene_profile") is not None
        else _default_profile_choices(sample_index)
    )
    profile = ctx.draw_choice("scene_profile", profile_options)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES and overrides.get("scene_profile") is not None:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    rng = ctx.draw_rng("scene")
    if overrides.get("scene_profile") is None and sample_index % 4 == 0:
        anchor_size = _anchor_canvas_size(profile, difficulty, sample_index)
        grid = _random_general(
            profile,
            difficulty,
            rng,
            canvas_size=(anchor_size, anchor_size),
        )
    else:
        grid = (
            _embed_public(profile, difficulty, rng)
            if profile in PUBLIC_PROFILES
            else _random_general(profile, difficulty, rng)
        )
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid route lesson: " + "; ".join(errors))
    return grid

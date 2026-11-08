"""Semantic generator for ARC task 59a7762bc6da.

Treat gray 5 cells as 8-connected components on an orange 7 background.
Recolor an entire component cyan 8 exactly when it contains three or more
cells in a straight down-right or down-left diagonal run.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "59a7762bc6da"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "108478b11257"
SUMMARY = "Recolor every gray 8-connected component containing a diagonal run of length at least three."
INVARIANTS = [
    "inputs use only orange 7 and gray 5",
    "gray cells are interpreted as 8-connected components",
    "a component changes wholly to cyan 8 iff its maximum straight diagonal run is at least three",
    "every lesson contains both a recolored component and an unchanged gray component",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_train_3", "public_test_1")
GENERAL_PROFILES = (
    "single_down_right", "single_down_left", "bidirectional_x", "long_diagonal",
    "branched_positive", "edge_positive", "mixed_component_sizes", "multiple_positive",
    "negative_singletons", "negative_orthogonal_runs", "near_miss_diagonal",
    "dense_negative_component",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "uniform rng over four public and twelve semantic lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_INPUTS = {
    "public_train_1": (
        "57575775", "57557757", "57777557", "57775757", "57777757", "55577777",
    ),
    "public_train_2": ("77757", "75577", "55777", "77755"),
    "public_train_3": (
        "77775577577", "55775577755", "55777575775", "55777777777",
        "55777557775", "77777757757", "75755757577", "77775757777",
        "57777777775", "55775757577", "75577575757", "75557777777",
    ),
    "public_test_1": (
        "7557777755557757777", "7757777777755577577", "7757757575777775577",
        "5775777557777575757", "7775757775777777755", "7575777777577777755",
        "7557577777777755775", "7777775577755777757", "7757755755775577777",
        "7777775577577777577", "5777777777575777755", "7555777757777777757",
        "7577777755777757755", "7557775755755575777", "7777755757777755575",
        "7777775577777757777",
    ),
}
_PUBLIC_SIGNATURES = {
    tuple(tuple(int(cell) for cell in row) for row in rows): profile
    for profile, rows in _PUBLIC_INPUTS.items()
}

_DR3 = ((0, 0), (1, 1), (2, 2))
_DL3 = ((0, 2), (1, 1), (2, 0))
_X = ((0, 0), (1, 1), (2, 2), (0, 2), (2, 0))
_LONG = ((0, 0), (1, 1), (2, 2), (3, 3), (4, 4))
_BRANCHED = ((0, 0), (1, 1), (2, 2), (0, 1), (0, 2), (1, 2))
_BLOCK2 = ((0, 0), (0, 1), (1, 0), (1, 1))
_PAIR = ((0, 0), (0, 1))
_SINGLE = ((0, 0),)
_HORIZONTAL = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4))
_VERTICAL = ((0, 0), (1, 0), (2, 0), (3, 0))
_NEAR_MISS = ((0, 0), (1, 1), (2, 1), (3, 2))
_DENSE_NEGATIVE = tuple((r, c) for r in range(2) for c in range(4))


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have non-empty rows"], 0, 0
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"], h, w
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or value not in (5, 7):
                return ["input cells must be integer colors 5 or 7"], h, w
    return [], h, w


def _components8(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            component = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        neighbor = (rr + dr, cc + dc)
                        if (0 <= neighbor[0] < h and 0 <= neighbor[1] < w
                                and grid[neighbor[0]][neighbor[1]] == 5
                                and neighbor not in seen):
                            seen.add(neighbor)
                            stack.append(neighbor)
            result.append(tuple(sorted(component)))
    return tuple(result)


def _diagonal_features(component):
    cells = set(component)
    best = 1
    qualifying = set()
    for r, c in cells:
        for dr, dc in ((1, 1), (1, -1)):
            if (r - dr, c - dc) in cells:
                continue
            length = 1
            while (r + length * dr, c + length * dc) in cells:
                length += 1
            best = max(best, length)
            if length >= 3:
                qualifying.add((dr, dc))
    return best, frozenset(qualifying)


def _bbox(component):
    rows = [cell[0] for cell in component]
    cols = [cell[1] for cell in component]
    return min(rows), min(cols), max(rows), max(cols)


def _touches_edge(component, h, w):
    return any(r in (0, h - 1) or c in (0, w - 1) for r, c in component)


def _classify(info):
    positive = info["positive_components"]
    negative = info["negative_components"]
    h, w = info["height"], info["width"]
    if any(_touches_edge(component, h, w) for component in positive):
        return "edge_positive"
    if len(positive) >= 2:
        return "multiple_positive"
    component = positive[0]
    maxdiag, directions = _diagonal_features(component)
    if len(directions) == 2:
        return "bidirectional_x"
    if maxdiag >= 5:
        return "long_diagonal"
    if len(component) >= 6:
        return "branched_positive"
    negative_sizes = {len(item) for item in negative}
    if len(negative) >= 4 and all(len(item) == 1 for item in negative):
        return "negative_singletons"
    for item in negative:
        r0, c0, r1, c1 = _bbox(item)
        if len(item) >= 8 and r1 - r0 + 1 == 2:
            return "dense_negative_component"
    for item in negative:
        r0, c0, r1, c1 = _bbox(item)
        if len(item) >= 4 and (r0 == r1 or c0 == c1):
            return "negative_orthogonal_runs"
    for item in negative:
        r0, c0, r1, c1 = _bbox(item)
        if len(item) == 4 and (r1 - r0 + 1, c1 - c0 + 1) in ((4, 3), (3, 4)):
            return "near_miss_diagonal"
    if {1, 2, 4}.issubset(negative_sizes):
        return "mixed_component_sizes"
    return "single_down_right" if (1, 1) in directions else "single_down_left"


def _analysis(grid):
    errors, h, w = _validate_grid(grid)
    result = {"errors": errors, "height": h, "width": w, "scene_profile": None}
    if errors:
        return result
    components = _components8(grid)
    positive = tuple(component for component in components if _diagonal_features(component)[0] >= 3)
    negative = tuple(component for component in components if _diagonal_features(component)[0] < 3)
    if not positive:
        errors.append("at least one gray component must contain a diagonal run of length three")
    if not negative:
        errors.append("at least one gray component must remain unchanged as a negative witness")
    output = [list(row) for row in grid]
    for component in positive:
        for r, c in component:
            output[r][c] = 8
    signature = tuple(tuple(row) for row in grid)
    profile = _PUBLIC_SIGNATURES.get(signature)
    if profile is None and not errors:
        profile = _classify(result | {
            "components": components,
            "positive_components": positive,
            "negative_components": negative,
        })
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared diagonal-component lesson")
    result.update({
        "components": components,
        "positive_components": positive,
        "negative_components": negative,
        "positive_count": len(positive),
        "negative_count": len(negative),
        "component_sizes": tuple(sorted(len(item) for item in components)),
        "max_diagonal": max((_diagonal_features(item)[0] for item in components), default=0),
        "output": output,
        "scene_profile": profile,
        "errors": errors,
    })
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid)
    profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _dimensions(rng, band):
    bounds = {
        "easy": ((8, 10), (9, 12)),
        "medium": ((9, 11), (10, 13)),
        "hard": ((10, 12), (12, 14)),
    }
    (h1, h2), (w1, w2) = bounds[band]
    return rng.randint(h1, h2), rng.randint(w1, w2)


def _try_place(grid, template, rng, *, edge=None):
    h, w = len(grid), len(grid[0])
    max_r = max(r for r, _ in template)
    max_c = max(c for _, c in template)
    candidates = [(r0, c0) for r0 in range(h - max_r) for c0 in range(w - max_c)]
    if edge is True:
        candidates = [
            (r0, c0) for r0, c0 in candidates
            if any(r0 + r in (0, h - 1) or c0 + c in (0, w - 1) for r, c in template)
        ]
    elif edge is False:
        candidates = [
            (r0, c0) for r0, c0 in candidates
            if all(r0 + r not in (0, h - 1) and c0 + c not in (0, w - 1) for r, c in template)
        ]
    rng.shuffle(candidates)
    for r0, c0 in candidates:
        cells = {(r0 + r, c0 + c) for r, c in template}
        if any(grid[rr][cc] == 5 for r, c in cells
               for rr in range(max(0, r - 1), min(h, r + 2))
               for cc in range(max(0, c - 1), min(w, c + 2))):
            continue
        for r, c in cells:
            grid[r][c] = 5
        return True
    return False


def _templates(profile, rng):
    if profile == "single_down_right":
        return [(_DR3, False)], [_BLOCK2]
    if profile == "single_down_left":
        return [(_DL3, False)], [_BLOCK2]
    if profile == "bidirectional_x":
        return [(_X, False)], [_PAIR]
    if profile == "long_diagonal":
        return [(_LONG, False)], [_BLOCK2]
    if profile == "branched_positive":
        return [(_BRANCHED, False)], [_BLOCK2]
    if profile == "edge_positive":
        return [(_DR3, True)], [_BLOCK2]
    if profile == "mixed_component_sizes":
        return [(_DR3, False)], [_BLOCK2, _PAIR, _SINGLE]
    if profile == "multiple_positive":
        return [(_DR3, False), (_DL3, False)], [_BLOCK2]
    if profile == "negative_singletons":
        return [(_DR3, False)], [_SINGLE, _SINGLE, _SINGLE, _SINGLE]
    if profile == "negative_orthogonal_runs":
        return [(_DR3, False)], [rng.choice((_HORIZONTAL, _VERTICAL))]
    if profile == "near_miss_diagonal":
        return [(_DR3, False)], [_NEAR_MISS]
    if profile == "dense_negative_component":
        return [(_DR3, False)], [_DENSE_NEGATIVE]
    raise ValueError(f"unknown scene_profile: {profile!r}")


def _general_grid(rng, profile, band):
    for _ in range(40):
        h, w = _dimensions(rng, band)
        grid = [[7 for _ in range(w)] for _ in range(h)]
        positives, negatives = _templates(profile, rng)
        if (all(_try_place(grid, template, rng, edge=edge) for template, edge in positives)
                and all(_try_place(grid, template, rng) for template in negatives)):
            return grid
    raise RuntimeError(f"could not place separated components for {profile!r}")


def _public_grid(profile):
    return [[int(cell) for cell in row] for row in _PUBLIC_INPUTS[profile]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                      difficulty=difficulty, overrides=overrides)
    profile = context.draw_choice("scene_profile", list(SCENE_PROFILES))
    rng = context.draw_rng("layout")
    grid = _public_grid(profile) if profile in PUBLIC_PROFILES else _general_grid(rng, profile, _band(difficulty))
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile!r} -> {observed!r}")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
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
            errors.append(f"requested scene_profile {requested}, observed {info['scene_profile']}")
    return errors

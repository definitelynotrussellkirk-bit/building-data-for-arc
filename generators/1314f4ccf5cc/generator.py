"""Semantic generator for ARC task 1314f4ccf5cc.

Dense zero/gray fields hide one or more 8-connected yellow fragments.  Each
fragment is exactly the yellow subset of one (possibly edge-clipped) plus.
The oracle keeps yellow evidence and recolors only the gray cells completing
those plus footprints to red; unrelated gray noise remains gray.
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterable

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "1314f4ccf5cc"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "645d868e16fc"
SUMMARY = (
    "Find every incomplete yellow fragment of a cardinal plus and recolor only "
    "the gray cells that complete that plus; dense unrelated gray noise stays gray."
)

INVARIANTS = [
    "the palette is exactly a subset of background 0, yellow 4, and gray 5",
    "every 8-connected yellow object is the yellow subset of exactly one plus footprint",
    "each target plus has at least two yellow cells and at least one gray missing cell",
    "at least one gray distractor lies outside all target-plus missing cells",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_train_4",
    "public_test_1",
)
GENERAL_PROFILES = (
    "general_sparse",
    "general_dense",
    "general_edge",
    "general_center_missing",
    "general_single_missing",
    "general_mixed",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
EXAMPLES_NEEDED = 4

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "uniform linked public/general semantic profiles",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PLUS = ((-1, 0), (0, -1), (0, 0), (0, 1), (1, 0))
_FULL_FOOTPRINT = tuple(sorted(_PLUS))

# Complete linked signatures extracted from all four train inputs and the held-out
# test input.  They contain no literal grids or outputs: only dimensions, total
# gray count, and each target's edge class plus yellow offsets relative to its
# plus center.  Public-profile draws randomize target positions and every noise
# coordinate while preserving the demonstrated joint morphology.
_PUBLIC_PROFILE_SPECS = {
    "public_train_1": {
        "dims": (14, 15),
        "gray_count": 88,
        "targets": (
            ("top", ((0, 1), (1, 0))),
            ("interior", ((-1, 0), (0, -1), (0, 0), (1, 0))),
            ("interior", ((-1, 0), (0, -1), (0, 1))),
            ("interior", ((0, -1), (0, 1), (1, 0))),
        ),
    },
    "public_train_2": {
        "dims": (18, 16),
        "gray_count": 127,
        "targets": (
            ("interior", ((0, -1), (1, 0))),
            ("interior", ((-1, 0), (0, 1), (1, 0))),
            ("interior", ((0, -1), (0, 1), (1, 0))),
            ("interior", ((-1, 0), (0, 1))),
            ("interior", ((-1, 0), (0, -1), (0, 1))),
            ("interior", ((0, -1), (0, 1), (1, 0))),
        ),
    },
    "public_train_3": {
        "dims": (14, 15),
        "gray_count": 86,
        "targets": (
            ("interior", ((0, 1), (1, 0))),
            ("interior", ((0, -1), (0, 0))),
            ("interior", ((0, 1), (1, 0))),
            ("interior", ((0, -1), (1, 0))),
        ),
    },
    "public_train_4": {
        "dims": (18, 19),
        "gray_count": 142,
        "targets": (
            ("interior", ((-1, 0), (0, -1), (0, 1), (1, 0))),
            ("interior", ((-1, 0), (0, 0), (0, 1), (1, 0))),
            ("interior", ((0, 1), (1, 0))),
            ("interior", ((-1, 0), (0, 0), (0, 1), (1, 0))),
        ),
    },
    "public_test_1": {
        "dims": (19, 19),
        "gray_count": 187,
        "targets": (
            ("top", ((0, 1), (1, 0))),
            ("interior", ((0, -1), (1, 0))),
            ("interior", ((0, 1), (1, 0))),
            ("interior", ((-1, 0), (0, -1), (0, 0))),
            ("interior", ((-1, 0), (0, -1), (0, 1), (1, 0))),
            ("interior", ((-1, 0), (0, 1), (1, 0))),
            ("interior", ((-1, 0), (0, 1), (1, 0))),
        ),
    },
}


def _rectangular_grid(grid) -> tuple[int, int] | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _footprint(center: tuple[int, int], height: int, width: int):
    row, col = center
    return {
        (row + dr, col + dc)
        for dr, dc in _PLUS
        if 0 <= row + dr < height and 0 <= col + dc < width
    }


def _relative(cells: Iterable[tuple[int, int]], center: tuple[int, int]):
    row, col = center
    return tuple(sorted((r - row, c - col) for r, c in cells))


def _yellow_components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 4
    }
    components = []
    while remaining:
        start = min(remaining)
        stack = [start]
        remaining.remove(start)
        component = {start}
        while stack:
            row, col = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    neighbor = (row + dr, col + dc)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        component.add(neighbor)
                        stack.append(neighbor)
        components.append(component)
    return components


def _candidate_centers(grid, yellow_object):
    height, width = len(grid), len(grid[0])
    candidates = []
    for row in range(height):
        for col in range(width):
            footprint = _footprint((row, col), height, width)
            yellow = {cell for cell in footprint if grid[cell[0]][cell[1]] == 4}
            gray = {cell for cell in footprint if grid[cell[0]][cell[1]] == 5}
            if (
                yellow == yellow_object
                and gray
                and all(grid[r][c] in (4, 5) for r, c in footprint)
            ):
                candidates.append(
                    {
                        "center": (row, col),
                        "footprint": footprint,
                        "yellow": yellow,
                        "missing": gray,
                    }
                )
    return candidates


def _edge_class(center, height, width):
    row, col = center
    if row == 0:
        return "top"
    if row == height - 1:
        return "bottom"
    if col == 0:
        return "left"
    if col == width - 1:
        return "right"
    return "interior"


def _analysis(grid):
    shape = _rectangular_grid(grid)
    if shape is None:
        return {"errors": ["grid must be nonempty and rectangular"], "targets": []}
    height, width = shape
    errors = []
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be integer ARC colors 0..9")
                break
            if value not in (0, 4, 5):
                errors.append(f"input palette must be a subset of 0/4/5, got {value}")
                break
        if errors:
            break

    targets = []
    if not errors:
        components = _yellow_components(grid)
        if not components:
            errors.append("expected at least one yellow fragment")
        for component in components:
            candidates = _candidate_centers(grid, component)
            if len(candidates) != 1:
                errors.append(
                    "each yellow object must identify exactly one incomplete plus; "
                    f"found {len(candidates)} candidates for {sorted(component)}"
                )
                continue
            candidate = candidates[0]
            center = candidate["center"]
            targets.append(
                {
                    **candidate,
                    "edge": _edge_class(center, height, width),
                    "yellow_rel": _relative(candidate["yellow"], center),
                    "footprint_rel": _relative(candidate["footprint"], center),
                    "missing_rel": _relative(candidate["missing"], center),
                }
            )

    target_missing = set().union(*(target["missing"] for target in targets)) if targets else set()
    all_gray = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5
    }
    stray_gray = all_gray - target_missing
    if targets and not stray_gray:
        errors.append("need at least one gray distractor outside target pluses")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "yellow_count": sum(value == 4 for row in grid for value in row),
        "gray_count": len(all_gray),
        "gray_fraction": len(all_gray) / max(1, height * width - sum(value == 4 for row in grid for value in row)),
        "targets": sorted(targets, key=lambda item: item["center"]),
        "target_count": len(targets),
        "edge_target_count": sum(target["edge"] != "interior" for target in targets),
        "center_missing_count": sum((0, 0) not in target["yellow_rel"] for target in targets),
        "stray_gray_count": len(stray_gray),
    }


def semantic_signature(grid):
    info = _analysis(grid)
    if info["errors"]:
        return None
    target_signature = tuple(
        sorted(
            (
                target["footprint_rel"],
                target["yellow_rel"],
            )
            for target in info["targets"]
        )
    )
    return (
        info["height"],
        info["width"],
        info["yellow_count"],
        info["gray_count"],
        target_signature,
    )


def _public_signature(spec):
    height, width = spec["dims"]
    targets = []
    yellow_count = 0
    for edge, yellow_rel in spec["targets"]:
        footprint_rel = {
            "interior": _FULL_FOOTPRINT,
            "top": tuple(sorted(rel for rel in _PLUS if rel != (-1, 0))),
            "bottom": tuple(sorted(rel for rel in _PLUS if rel != (1, 0))),
            "left": tuple(sorted(rel for rel in _PLUS if rel != (0, -1))),
            "right": tuple(sorted(rel for rel in _PLUS if rel != (0, 1))),
        }[edge]
        yellow_rel = tuple(sorted(yellow_rel))
        yellow_count += len(yellow_rel)
        targets.append((footprint_rel, yellow_rel))
    return height, width, yellow_count, spec["gray_count"], tuple(sorted(targets))


_PUBLIC_SIGNATURES = {
    _public_signature(spec): profile
    for profile, spec in _PUBLIC_PROFILE_SPECS.items()
}
if len(_PUBLIC_SIGNATURES) != len(PUBLIC_PROFILES):
    raise RuntimeError("public profile signatures collide")


def canonical_profile_signature(grid):
    signature = semantic_signature(grid)
    return _PUBLIC_SIGNATURES.get(signature)


def scene_profile_signature(grid):
    public = canonical_profile_signature(grid)
    if public is not None:
        return public
    info = _analysis(grid)
    if info["errors"]:
        return None
    if info["edge_target_count"]:
        return "general_edge"
    if info["gray_fraction"] < 0.32:
        return "general_sparse"
    if info["gray_fraction"] > 0.60:
        return "general_dense"
    if info["center_missing_count"] == info["target_count"]:
        return "general_center_missing"
    if all(
        len(target["missing"]) == 1 and (0, 0) in target["yellow_rel"]
        for target in info["targets"]
    ):
        return "general_single_missing"
    return "general_mixed"


def observe_overrides(grid):
    profile = scene_profile_signature(grid)
    if profile is None:
        info = _analysis(grid)
        raise ValueError("; ".join(info["errors"]) or "unrecognized scene profile")
    return {"scene_profile": profile}


def rule_mirror(grid):
    """Independent Python transcription of the canonical Racket oracle."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    output = [list(row) for row in grid]
    for target in info["targets"]:
        for row, col in target["missing"]:
            output[row][col] = 2
    return output


def _available_footprint(edge):
    return {
        "interior": set(_PLUS),
        "top": set(_PLUS) - {(-1, 0)},
        "bottom": set(_PLUS) - {(1, 0)},
        "left": set(_PLUS) - {(0, -1)},
        "right": set(_PLUS) - {(0, 1)},
    }[edge]


def _is_connected_8(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for other in cells - seen:
            if max(abs(row - other[0]), abs(col - other[1])) <= 1:
                seen.add(other)
                stack.append(other)
    return seen == cells


def _patterns(edge, *, center_policy="either", missing_count=None):
    footprint = _available_footprint(edge)
    patterns = []
    for size in range(2, len(footprint)):
        if missing_count is not None and len(footprint) - size != missing_count:
            continue
        for subset in combinations(sorted(footprint), size):
            subset = set(subset)
            if not _is_connected_8(subset):
                continue
            if center_policy == "present" and (0, 0) not in subset:
                continue
            if center_policy == "missing" and (0, 0) in subset:
                continue
            patterns.append(tuple(sorted(subset)))
    return patterns


def _center_candidates(edge, height, width):
    if edge == "top":
        return [(0, col) for col in range(1, width - 1)]
    if edge == "bottom":
        return [(height - 1, col) for col in range(1, width - 1)]
    if edge == "left":
        return [(row, 0) for row in range(1, height - 1)]
    if edge == "right":
        return [(row, width - 1) for row in range(1, height - 1)]
    return [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]


def _place_centers(rng, height, width, target_specs):
    for _ in range(160):
        centers = []
        ok = True
        for edge, _yellow_rel in target_specs:
            candidates = _center_candidates(edge, height, width)
            rng.shuffle(candidates)
            center = next(
                (
                    candidate
                    for candidate in candidates
                    if all(
                        max(abs(candidate[0] - old[0]), abs(candidate[1] - old[1])) >= 4
                        for old in centers
                    )
                ),
                None,
            )
            if center is None:
                ok = False
                break
            centers.append(center)
        if ok:
            return centers
    raise ValueError("unable to place separated plus fragments in requested profile")


def _guard_cells(height, width, targets):
    all_yellow = set().union(*(target["yellow"] for target in targets))
    forced_gray = set().union(*(target["missing"] for target in targets))
    guards = set()
    for target in targets:
        intended = target["center"]
        for row in range(height):
            for col in range(width):
                center = (row, col)
                if center == intended:
                    continue
                footprint = _footprint(center, height, width)
                if footprint & all_yellow != target["yellow"]:
                    continue
                choices = sorted(footprint - all_yellow - forced_gray)
                if not choices:
                    raise ValueError("target fragment has an unavoidable second plus interpretation")
                guards.add(choices[0])
    return guards


def _build_grid(rng, height, width, target_specs, gray_count):
    centers = _place_centers(rng, height, width, target_specs)
    targets = []
    all_yellow = set()
    for center, (edge, yellow_rel) in zip(centers, target_specs, strict=True):
        if _edge_class(center, height, width) != edge:
            raise ValueError("internal edge placement mismatch")
        footprint = _footprint(center, height, width)
        yellow = {(center[0] + dr, center[1] + dc) for dr, dc in yellow_rel}
        if not yellow <= footprint:
            raise ValueError("target yellow pattern leaves its clipped plus footprint")
        if all_yellow & yellow:
            raise ValueError("target yellow fragments overlap")
        all_yellow.update(yellow)
        targets.append(
            {
                "center": center,
                "yellow": yellow,
                "missing": footprint - yellow,
            }
        )

    forced_gray = set().union(*(target["missing"] for target in targets))
    guards = _guard_cells(height, width, targets)
    if guards & (all_yellow | forced_gray):
        raise ValueError("interpretation guard collides with a target footprint")

    all_cells = {(row, col) for row in range(height) for col in range(width)}
    available_gray = all_cells - all_yellow - guards
    if gray_count < len(forced_gray) + 1:
        raise ValueError("gray density leaves no distractor outside target pluses")
    if gray_count > len(available_gray) - 1:
        raise ValueError("gray density leaves no background-zero witness")
    extras = list(available_gray - forced_gray)
    rng.shuffle(extras)
    gray = forced_gray | set(extras[: gray_count - len(forced_gray)])

    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in gray:
        grid[row][col] = 5
    for row, col in all_yellow:
        grid[row][col] = 4
    return grid


def _general_specs(rng, profile, count):
    edges = ["interior"] * count
    if profile == "general_edge":
        edges[0] = rng.choice(("top", "bottom", "left", "right"))
    specs = []
    for index, edge in enumerate(edges):
        if profile == "general_center_missing":
            options = _patterns(edge, center_policy="missing")
        elif profile == "general_single_missing":
            options = _patterns(edge, center_policy="present", missing_count=1)
        elif profile in {"general_sparse", "general_dense"}:
            policy = "missing" if index == 0 else "present" if index == 1 else "either"
            options = _patterns(edge, center_policy=policy)
        elif profile == "general_mixed":
            policy = "missing" if index == 0 else "present" if index == 1 else "either"
            options = _patterns(edge, center_policy=policy)
            if index == 1:
                options = [pattern for pattern in options if len(_available_footprint(edge)) - len(pattern) >= 2]
        else:  # general_edge
            policy = "missing" if index == 0 else "present" if index == 1 else "either"
            options = _patterns(edge, center_policy=policy)
        if not options:
            raise ValueError(f"no lawful fragment patterns for {profile}/{edge}")
        specs.append((edge, rng.choice(options)))
    return tuple(specs)


def _general_dimensions(rng, difficulty):
    if difficulty == "easy":
        return rng.randint(10, 14), rng.randint(10, 15), rng.randint(2, 3)
    if difficulty == "hard":
        return rng.randint(20, 28), rng.randint(20, 28), rng.randint(6, 9)
    return rng.randint(15, 21), rng.randint(15, 22), rng.randint(4, 6)


def _gray_count_for_profile(rng, profile, height, width, yellow_count, missing_count):
    if profile == "general_sparse":
        fraction = rng.uniform(0.18, 0.28)
    elif profile == "general_dense":
        fraction = rng.uniform(0.66, 0.74)
    else:
        fraction = rng.uniform(0.40, 0.54)
    count = round(fraction * (height * width - yellow_count))
    return max(missing_count + 2, min(count, height * width - yellow_count - 2))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    rng = ctx.draw_rng("construction")

    for _ in range(200):
        if profile in PUBLIC_PROFILES:
            spec = _PUBLIC_PROFILE_SPECS[profile]
            height, width = spec["dims"]
            target_specs = spec["targets"]
            gray_count = spec["gray_count"]
        else:
            height, width, target_count = _general_dimensions(rng, difficulty)
            target_specs = _general_specs(rng, profile, target_count)
            yellow_count = sum(len(yellow) for _edge, yellow in target_specs)
            missing_count = sum(len(_available_footprint(edge)) - len(yellow) for edge, yellow in target_specs)
            gray_count = _gray_count_for_profile(
                rng,
                profile,
                height,
                width,
                yellow_count,
                missing_count,
            )
        try:
            grid = _build_grid(rng, height, width, target_specs, gray_count)
        except ValueError:
            continue
        if scene_profile_signature(grid) == profile and not self_check(grid, difficulty=difficulty):
            return grid
    raise ValueError(f"unable to construct valid scene_profile={profile!r}")


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid)
    errors = list(info["errors"])
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append(f"unknown difficulty {difficulty!r}")
    if errors:
        return errors
    profile = scene_profile_signature(grid)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match any declared semantic scene profile")
    output = rule_mirror(grid)
    if output == [list(row) for row in grid]:
        errors.append("oracle must recolor at least one target gray cell")
    if any(value not in range(10) for row in output for value in row):
        errors.append("oracle output leaves ARC palette 0..9")
    return errors

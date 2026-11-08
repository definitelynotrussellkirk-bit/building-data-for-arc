"""Semantic generator for ARC task 2a6aac780e6d.

A row is filled only when it contains exactly two nonzero cells, those cells
have the same color, and at least one zero lies between them.  Other rows are
left unchanged.  The generated curriculum includes positive rows plus explicit
single-endpoint, mismatched-endpoint, and extra-marker guards so a solver cannot
learn the weaker shortcut "connect any two colored cells".
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "2a6aac780e6d"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "4f90f10302a9"
SUMMARY = (
    "Fill every row that has exactly two separated, same-color nonzero "
    "endpoints; preserve blank and nonqualifying rows."
)
INVARIANTS = [
    "background is 0 and every generated grid is rectangular",
    "every normal scene contains at least one qualifying same-color endpoint row",
    "qualifying endpoints have at least one zero between them",
    "single, mismatched, and crowded guard rows remain nonqualifying",
    "the linked row-branch census identifies one declared scene profile",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_test_1",
)
GENERAL_PROFILES = (
    "one_gap_fill",
    "long_fill",
    "edge_fill",
    "two_distinct_fills",
    "two_shared_color_fills",
    "many_fills",
    "mismatch_guard",
    "single_guard",
    "crowded_guard",
    "all_guards",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public anchors and linked semantic branch profiles",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "Exact observable curriculum profile. General profiles are recovered "
            "from the linked counts of qualifying, mismatched, single, and crowded "
            "rows, with endpoint-gap/color relations distinguishing positive-only "
            "profiles."
        ),
    }
}

_PUBLIC_ROWS = {
    "public_train_1": (
        "0000000",
        "0200002",
        "0000000",
        "0030030",
        "0000000",
    ),
    "public_train_2": (
        "00000000",
        "00600006",
        "02000203",
        "00000000",
        "40000004",
    ),
    "public_test_1": (
        "000000000",
        "070000007",
        "000000000",
        "002000200",
        "300000003",
    ),
}
_PUBLIC_INPUTS = {
    name: tuple(tuple(int(value) for value in row) for row in rows)
    for name, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_SIGNATURES = {grid: name for name, grid in _PUBLIC_INPUTS.items()}
_COLORS = tuple(range(1, 10))


def _basic_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors 0..9"]
    return []


def _row_record(row_index, row):
    nonzero = [(col, value) for col, value in enumerate(row) if value != 0]
    record = {"row": row_index, "nonzero": tuple(nonzero), "kind": "blank"}
    if not nonzero:
        return record
    if len(nonzero) == 1:
        record["kind"] = "single"
        return record
    if len(nonzero) >= 3:
        record["kind"] = "crowded"
        return record

    (left, left_color), (right, right_color) = nonzero
    record.update(
        {
            "left": left,
            "right": right,
            "left_color": left_color,
            "right_color": right_color,
            "gap": right - left - 1,
        }
    )
    if left_color != right_color:
        record["kind"] = "mismatch"
    elif right == left + 1:
        record["kind"] = "adjacent_same"
    else:
        record["kind"] = "qualifying"
        record["color"] = left_color
    return record


def _infer_general_profile(records, width):
    positives = [record for record in records if record["kind"] == "qualifying"]
    mismatches = [record for record in records if record["kind"] == "mismatch"]
    singles = [record for record in records if record["kind"] == "single"]
    crowded = [record for record in records if record["kind"] == "crowded"]
    counts = (len(positives), len(mismatches), len(singles), len(crowded))

    if counts == (1, 0, 0, 0):
        positive = positives[0]
        if positive["left"] == 0 and positive["right"] == width - 1:
            return "edge_fill"
        if positive["gap"] == 1:
            return "one_gap_fill"
        if positive["gap"] >= 2:
            return "long_fill"
    if counts == (2, 0, 0, 0):
        colors = {record["color"] for record in positives}
        return "two_shared_color_fills" if len(colors) == 1 else "two_distinct_fills"
    if counts[0] >= 3 and counts[1:] == (0, 0, 0):
        return "many_fills"
    if counts == (1, 1, 0, 0):
        return "mismatch_guard"
    if counts == (1, 0, 1, 0):
        return "single_guard"
    if counts == (1, 0, 0, 1):
        return "crowded_guard"
    if counts == (2, 1, 1, 1):
        return "all_guards"
    return None


def _analysis(grid):
    errors = _basic_errors(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    if not (5 <= height <= 14 and 7 <= width <= 18):
        errors.append(f"dimensions {height}x{width} outside 5..14 by 7..18")
        return result

    records = tuple(_row_record(index, row) for index, row in enumerate(grid))
    adjacent = [record for record in records if record["kind"] == "adjacent_same"]
    positives = [record for record in records if record["kind"] == "qualifying"]
    if adjacent:
        errors.append("adjacent same-color pair creates a no-change pseudo-positive row")
    if not positives:
        errors.append("scene has no qualifying same-color endpoint row")

    signature = tuple(tuple(row) for row in grid)
    profile = _PUBLIC_SIGNATURES.get(signature)
    if profile is None and not errors:
        profile = _infer_general_profile(records, width)
    if profile not in SCENE_PROFILES:
        errors.append("linked semantic row census does not match a declared scene profile")

    result.update(
        {
            "height": height,
            "width": width,
            "records": records,
            "qualifying": tuple(positives),
            "mismatches": tuple(
                record for record in records if record["kind"] == "mismatch"
            ),
            "singles": tuple(record for record in records if record["kind"] == "single"),
            "crowded": tuple(record for record in records if record["kind"] == "crowded"),
            "blank_rows": sum(record["kind"] == "blank" for record in records),
            "scene_profile": profile,
            "errors": errors,
        }
    )
    return result


def canonical_profile_signature(grid):
    """Return the exact public profile name, otherwise ``None``."""
    if _basic_errors(grid):
        return None
    return _PUBLIC_SIGNATURES.get(tuple(tuple(row) for row in grid))


def observe_overrides(grid):
    """Recover the exact declared semantic-axis value from a returned grid."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    """Broad test-only mirror of the canonical Racket rule.

    Generation never uses this function to produce labels; the Racket oracle
    remains output authority.  Keeping this mirror broader than ``self_check``
    lets tests distinguish oracle-valid recombinations from this generator's
    deliberately calibrated curriculum profiles.
    """
    errors = _basic_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        nonzero = [(col, value) for col, value in enumerate(row) if value != 0]
        if len(nonzero) != 2 or nonzero[0][1] != nonzero[1][1]:
            continue
        left, color = nonzero[0]
        right = nonzero[1][0]
        if all(row[col] == 0 for col in range(left + 1, right)):
            for col in range(left, right + 1):
                output[row_index][col] = color
    return output


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _dimensions(rng, band, required_rows):
    bounds = {
        "easy": ((5, 7), (7, 10)),
        "medium": ((7, 10), (9, 14)),
        "hard": ((10, 14), (13, 18)),
    }
    (height_lo, height_hi), (width_lo, width_hi) = bounds[band]
    height = rng.randint(max(required_rows, height_lo), height_hi)
    width = rng.randint(width_lo, width_hi)
    return height, width


def _endpoint_pair(rng, width, mode):
    if mode == "edge":
        return 0, width - 1
    if mode == "one_gap":
        left = rng.randrange(width - 2)
        return left, left + 2
    minimum_distance = 3 if mode == "long" else 2
    pairs = [
        (left, right)
        for left in range(width)
        for right in range(left + minimum_distance, width)
        if mode != "long" or not (left == 0 and right == width - 1)
    ]
    return rng.choice(pairs)


def _paint_spec(row, spec, rng):
    kind = spec[0]
    width = len(row)
    if kind == "fill":
        _, color, mode = spec
        left, right = _endpoint_pair(rng, width, mode)
        row[left] = color
        row[right] = color
        return
    if kind == "mismatch":
        _, left_color, right_color = spec
        left, right = _endpoint_pair(rng, width, "varied")
        row[left] = left_color
        row[right] = right_color
        return
    if kind == "single":
        _, color = spec
        row[rng.randrange(width)] = color
        return
    if kind == "crowded":
        _, repeated_color, extra_color = spec
        columns = sorted(rng.sample(range(width), 3))
        same_pair = rng.choice(((0, 1), (0, 2), (1, 2)))
        values = [extra_color, extra_color, extra_color]
        values[same_pair[0]] = repeated_color
        values[same_pair[1]] = repeated_color
        for column, value in zip(columns, values):
            row[column] = value
        return
    raise ValueError(f"unknown row spec: {spec!r}")


def _specs_for_profile(profile, rng, band):
    if profile == "one_gap_fill":
        return [("fill", rng.choice(_COLORS), "one_gap")]
    if profile == "long_fill":
        return [("fill", rng.choice(_COLORS), "long")]
    if profile == "edge_fill":
        return [("fill", rng.choice(_COLORS), "edge")]
    if profile == "two_distinct_fills":
        first, second = rng.sample(_COLORS, 2)
        return [("fill", first, "varied"), ("fill", second, "varied")]
    if profile == "two_shared_color_fills":
        color = rng.choice(_COLORS)
        return [("fill", color, "varied"), ("fill", color, "varied")]
    if profile == "many_fills":
        count = 4 if band == "hard" else 3
        palette = rng.sample(_COLORS, 3)
        return [
            ("fill", palette[index % len(palette)], "varied")
            for index in range(count)
        ]
    if profile == "mismatch_guard":
        fill_color, left_color, right_color = rng.sample(_COLORS, 3)
        return [
            ("fill", fill_color, "varied"),
            ("mismatch", left_color, right_color),
        ]
    if profile == "single_guard":
        fill_color, marker_color = rng.sample(_COLORS, 2)
        return [("fill", fill_color, "varied"), ("single", marker_color)]
    if profile == "crowded_guard":
        fill_color, repeated_color, extra_color = rng.sample(_COLORS, 3)
        return [
            ("fill", fill_color, "varied"),
            ("crowded", repeated_color, extra_color),
        ]
    if profile == "all_guards":
        colors = rng.sample(_COLORS, 7)
        return [
            ("fill", colors[0], "varied"),
            ("fill", colors[1], "varied"),
            ("mismatch", colors[2], colors[3]),
            ("single", colors[4]),
            ("crowded", colors[5], colors[6]),
        ]
    raise ValueError(f"unknown general profile: {profile!r}")


def _general_scene(rng, profile, band):
    specs = _specs_for_profile(profile, rng, band)
    height, width = _dimensions(rng, band, len(specs))
    grid = [[0] * width for _ in range(height)]
    rows = sorted(rng.sample(range(height), len(specs)))
    rng.shuffle(specs)
    for row_index, spec in zip(rows, specs):
        _paint_spec(grid[row_index], spec, rng)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    weighted_profiles = list(PUBLIC_PROFILES) + [
        profile for profile in GENERAL_PROFILES for _ in range(4)
    ]
    profile = ctx.draw_choice("scene_profile", weighted_profiles)
    if profile in PUBLIC_PROFILES:
        return [list(row) for row in _PUBLIC_INPUTS[profile]]

    grid = _general_scene(ctx.draw_rng("layout"), profile, band)
    info = _analysis(grid)
    if info["errors"] or info["scene_profile"] != profile:
        raise ValueError(
            f"internal scene construction mismatch for {profile!r}: "
            f"observed={info['scene_profile']!r}, errors={info['errors']}"
        )
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete linked curriculum profile, not just one good row."""
    return list(_analysis(grid)["errors"])

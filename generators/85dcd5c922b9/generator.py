"""Semantic generator for 85dcd5c922b9 — right-pack each row independently.

For every row, keep the nonzero cells in their original left-to-right order
and slide that ordered sequence flush against the RIGHT edge.  Rows never
exchange cells and zero remains background.

The canonical task uses globally unique colored tokens, 3–4 rows, widths
6–8, and palette sizes 6–9 (including background).  Normal draws preserve
that grammar and cycle through three exact canonical profiles by
``sample_index % 3``.  The profile cycle is intentionally *not* an override
axis: it is a curriculum schedule, so every 3-demo sliding window contains the
query's own size profile.  The only public overrides are exact properties that
can be recovered from the returned grid.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "85dcd5c922b9"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "6ab6552b1d13"

SUMMARY = (
    "Within each row, preserve the left-to-right order of all nonzero cells "
    "and move that sequence flush to the row's right edge; rows are handled "
    "independently and zero remains background."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

INVARIANTS = [
    "grid profile matches one observed canonical (height, width, palette-size) profile",
    "all nonzero colors are globally unique tokens, as in every canonical pair",
    "at least two rows are active and at least two rows contain two or more tokens",
    "no active row is fully filled",
    "at least one row visibly changes when its nonzero tokens are right-packed",
    "ordinary draws contain both ascending and descending token-order witnesses",
]

# Exact canonical profiles observed across the four authoritative train/test pairs.
CANONICAL_PROFILES = frozenset({
    (3, 6, 6),
    (3, 6, 7),
    (3, 8, 8),
    (4, 7, 9),
})

# Normal draws use three profiles in a period-3 curriculum.  The omitted
# (3,6,6) profile is still accepted by self_check/strict_canonical_like and is
# covered by the real canonical test input; the three scheduled profiles give
# every ordinary 3-demo window a same-profile predecessor for its query.
PROFILE_CYCLE = (
    (3, 6, 7),
    (3, 8, 8),
    (4, 7, 9),
)

AXES = {
    "first_row_load": {
        "type": "int",
        "default": "rng 2..3",
        "valid": "2..3",
    },
    "blank_row": {
        "type": "str",
        "default": "rng none|last",
        "valid": "none|last",
    },
}

# These legacy names are intentionally empty.  Identity/empty/full scenes are
# negative fixtures now, never legal training textures or public overrides.
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    """Normalize a candidate ARC grid without mutating the caller's object."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    converted: list[list[int]] = []
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        out_row: list[int] = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                out_row.append(0)
            else:
                out_row.append(int(value))
        converted.append(out_row)
    if errors:
        return None, errors
    return converted, []


def _right_pack_row(row: Sequence[int]) -> list[int]:
    values = [int(value) for value in row if value != 0]
    return [0] * (len(row) - len(values)) + values


def rule_mirror(grid: Any) -> list[list[int]]:
    """Test-only Python mirror; canonical Racket remains the output authority."""
    converted, errors = _coerce_grid(grid)
    if errors or converted is None:
        raise ValueError("; ".join(errors))
    return [_right_pack_row(row) for row in converted]


def _analysis(grid: Any) -> dict[str, Any]:
    converted, errors = _coerce_grid(grid)
    result: dict[str, Any] = {
        "errors": list(errors),
        "grid": converted,
        "grid_h": None,
        "grid_w": None,
        "palette_size": None,
        "nonzero_counts": Counter(),
        "active_rows": (),
        "row_counts": (),
        "row_sequences": (),
        "output": None,
        "changed": False,
        "profile": None,
        "full_rows": (),
        "shift_vectors": (),
    }
    if errors or converted is None:
        return result

    h, w = len(converted), len(converted[0])
    palette = {value for row in converted for value in row}
    nonzero_counts = Counter(value for row in converted for value in row if value != 0)
    active_rows = tuple(index for index, row in enumerate(converted) if any(row))
    row_sequences = tuple(tuple(value for value in row if value != 0) for row in converted)
    row_counts = tuple(len(values) for values in row_sequences)
    output = [_right_pack_row(row) for row in converted]
    full_rows = tuple(index for index, row in enumerate(converted) if all(value != 0 for value in row))

    shift_vectors: list[tuple[int, ...]] = []
    for row in converted:
        cols = [index for index, value in enumerate(row) if value != 0]
        k = len(cols)
        if not k:
            shift_vectors.append(())
            continue
        start = w - k
        shift_vectors.append(tuple((start + i) - col for i, col in enumerate(cols)))

    result.update(
        {
            "grid_h": h,
            "grid_w": w,
            "palette_size": len(palette),
            "nonzero_counts": nonzero_counts,
            "active_rows": active_rows,
            "row_counts": row_counts,
            "row_sequences": row_sequences,
            "output": output,
            "changed": output != converted,
            "profile": (h, w, len(palette)),
            "full_rows": full_rows,
            "shift_vectors": tuple(shift_vectors),
        }
    )
    return result


def observe_overrides(grid: Any) -> dict[str, int | str | None]:
    """Recover every exact public axis from a returned generated grid."""
    facts = _analysis(grid)
    if facts["errors"] or facts["grid"] is None:
        return {"first_row_load": None, "blank_row": None}
    rows = facts["grid"]
    return {
        "first_row_load": facts["row_counts"][0],
        "blank_row": "last" if not any(rows[-1]) else "none",
    }


def _allocate_row_counts(
    *, total_tokens: int, height: int, width: int, first_row_load: int, blank_row: str
) -> list[int]:
    active_count = height - (1 if blank_row == "last" else 0)
    if active_count < 2:
        raise ValueError("generated grammar requires at least two active rows")

    counts = [0] * height
    counts[0] = first_row_load
    for row in range(1, active_count):
        counts[row] = 1
    # A second multi-token row makes row-locality and order preservation visible.
    counts[1] += 1

    remaining = total_tokens - sum(counts)
    if remaining < 0:
        raise ValueError("profile/override combination cannot fit required row witnesses")

    # Keep row 0 exact for the public axis.  Fill later rows deterministically,
    # favoring row 1 but never making a row full.
    order = list(range(1, active_count))
    cursor = 0
    while remaining:
        row = order[cursor % len(order)]
        if counts[row] < width - 1:
            counts[row] += 1
            remaining -= 1
        cursor += 1
        if cursor > 10_000:
            raise RuntimeError("could not allocate token counts")
    return counts


def _place_columns(width: int, count: int, *, row_index: int, difficulty: Any, rng) -> list[int]:
    """Choose sparse columns; row 0 always contains unequal move distances."""
    if count <= 0:
        return []
    if count >= width:
        raise ValueError("active rows must retain at least one zero cell")

    if row_index == 0:
        if count == 2:
            candidates = {
                "easy": [0, 2],
                "medium": [1, max(3, width - 3)],
                "hard": [0, width - 2],
            }
        else:  # public axis caps row 0 at three tokens
            candidates = {
                "easy": [0, 2, 3],
                "medium": [0, 2, width - 2],
                "hard": [1, width - 3, width - 1],
            }
        cols = sorted(dict.fromkeys(candidates.get(str(difficulty), candidates["medium"])))
        if len(cols) == count and all(0 <= col < width for col in cols):
            return cols

    # Other rows vary freely but never start already right-packed.  Retry until
    # there is at least one internal gap when the row has multiple tokens.
    for _ in range(128):
        pool = list(range(width))
        cols = sorted(rng.sample(pool, count))
        right_packed = cols == list(range(width - count, width))
        has_gap = count < 2 or any(b - a > 1 for a, b in zip(cols, cols[1:]))
        if not right_packed and has_gap:
            return cols
    # Deterministic fallback: pack left, then open one gap if possible.
    cols = list(range(count))
    if count >= 2 and count < width - 1:
        cols[-1] += 1
    return cols


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    first_row_load = ctx.draw_int_strict("first_row_load", 2, 3)
    blank_row = ctx.draw_choice("blank_row", ("none", "last"))

    # Curriculum schedule: profile repeats after exactly EXAMPLES_NEEDED draws.
    h, w, total_palette = PROFILE_CYCLE[sample_index % len(PROFILE_CYCLE)]
    total_tokens = total_palette - 1
    colors = sorted(ctx.draw_distinct_colors("palette", n=total_tokens, exclude={0}))
    counts = _allocate_row_counts(
        total_tokens=total_tokens,
        height=h,
        width=w,
        first_row_load=first_row_load,
        blank_row=blank_row,
    )

    # Row 0 is numerically ascending, row 1 descending.  Since colors are all
    # unique, these two rows jointly kill both sort-ascending and sort-descending
    # shortcuts while also killing reversal.
    row_colors: list[list[int]] = [[] for _ in range(h)]
    cursor = 0
    for row_index, count in enumerate(counts):
        if not count:
            continue
        chunk = colors[cursor : cursor + count]
        cursor += count
        if row_index == 1:
            chunk = list(reversed(chunk))
        row_colors[row_index] = list(chunk)
    if cursor != len(colors):
        raise RuntimeError("token allocation did not consume the selected palette")

    grid = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    for row_index, values in enumerate(row_colors):
        if not values:
            continue
        cols = _place_columns(
            w,
            len(values),
            row_index=row_index,
            difficulty=difficulty,
            rng=rng,
        )
        for col, value in zip(cols, values):
            grid[row_index][col] = value
    return grid


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Structural grammar shared by generated and authoritative canonical inputs."""
    facts = _analysis(grid)
    errors = list(facts["errors"])
    if errors:
        return errors

    if facts["profile"] not in CANONICAL_PROFILES:
        errors.append(
            f"profile {facts['profile']} is outside canonical profiles {sorted(CANONICAL_PROFILES)}"
        )
    if any(count != 1 for count in facts["nonzero_counts"].values()):
        errors.append("every nonzero color must occur exactly once")
    if len(facts["active_rows"]) < 2:
        errors.append("at least two rows must contain nonzero tokens")
    if sum(count >= 2 for count in facts["row_counts"]) < 2:
        errors.append("at least two rows must contain two or more nonzero tokens")
    if facts["full_rows"]:
        errors.append(f"active rows may not be fully filled: {facts['full_rows']}")
    if not facts["changed"]:
        errors.append("right-packing must visibly change at least one row")

    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis in AXES:
                if axis in requested and observed.get(axis) != requested[axis]:
                    errors.append(
                        f"override {axis}={requested[axis]!r} realized as {observed.get(axis)!r}"
                    )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Task-linked canonical-manifold predicate used by the semantic gate."""
    return self_check(grid)


def _has_unequal_shift_witness(grid: Any) -> bool:
    facts = _analysis(grid)
    return any(len(shifts) >= 2 and len(set(shifts)) >= 2 for shifts in facts["shift_vectors"])


def _has_ascending_and_descending_rows(grid: Any) -> bool:
    facts = _analysis(grid)
    sequences = [list(seq) for seq in facts["row_sequences"] if len(seq) >= 2]
    has_ascending = any(seq == sorted(seq) and seq != sorted(seq, reverse=True) for seq in sequences)
    has_descending = any(seq == sorted(seq, reverse=True) and seq != sorted(seq) for seq in sequences)
    return has_ascending and has_descending


def _row_locality_visible(grid: Any) -> bool:
    facts = _analysis(grid)
    if facts["errors"] or facts["output"] is None or not facts["changed"]:
        return False
    active = [index for index, count in enumerate(facts["row_counts"]) if count]
    if len(active) < 2:
        return False
    for row in active:
        before = sorted(value for value in facts["grid"][row] if value)
        after = sorted(value for value in facts["output"][row] if value)
        if before != after:
            return False
    return True


SEMANTIC_WITNESSES = {
    "visible_right_compaction": lambda grid: not _analysis(grid)["errors"] and _analysis(grid)["changed"],
    "unequal_move_distances": _has_unequal_shift_witness,
    "ascending_and_descending_order_controls": _has_ascending_and_descending_rows,
    "row_locality_preserved": _row_locality_visible,
}


def _left_pack(grid: Any) -> list[list[int]]:
    converted, errors = _coerce_grid(grid)
    if errors or converted is None:
        raise ValueError("; ".join(errors))
    out = []
    for row in converted:
        values = [value for value in row if value]
        out.append(values + [0] * (len(row) - len(values)))
    return out


def _reverse_right_pack(grid: Any) -> list[list[int]]:
    converted, errors = _coerce_grid(grid)
    if errors or converted is None:
        raise ValueError("; ".join(errors))
    out = []
    for row in converted:
        values = [value for value in row if value][::-1]
        out.append([0] * (len(row) - len(values)) + values)
    return out


def _sorted_right_pack(grid: Any, *, reverse: bool) -> list[list[int]]:
    converted, errors = _coerce_grid(grid)
    if errors or converted is None:
        raise ValueError("; ".join(errors))
    out = []
    for row in converted:
        values = sorted((value for value in row if value), reverse=reverse)
        out.append([0] * (len(row) - len(values)) + values)
    return out


def _one_step_right(grid: Any) -> list[list[int]]:
    """Plausible fixed-translation rival: shift each row one cell right."""
    converted, errors = _coerce_grid(grid)
    if errors or converted is None:
        raise ValueError("; ".join(errors))
    out: list[list[int]] = []
    for row in converted:
        out.append([0] + list(row[:-1]))
    return out


def _profile(grid: Any) -> tuple[int, int, int] | None:
    facts = _analysis(grid)
    return None if facts["errors"] else facts["profile"]


def lesson_identifiable(demos: Sequence[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Reject lessons where a plausible rival still predicts a different query."""
    if len(demos) < 2:
        return ["at least two demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_profile = _profile(query["input"])
    demo_profiles = {_profile(demo.get("input")) for demo in demos if isinstance(demo, dict)}
    if query_profile not in demo_profiles:
        reasons.append(
            f"query profile {query_profile} is absent from demonstration profiles {sorted(demo_profiles, key=str)}"
        )

    rivals = {
        "left_pack": _left_pack,
        "reverse_order": _reverse_right_pack,
        "sort_ascending": lambda grid: _sorted_right_pack(grid, reverse=False),
        "sort_descending": lambda grid: _sorted_right_pack(grid, reverse=True),
        "fixed_one_step_right": _one_step_right,
    }
    official_query = query.get("output")
    if official_query is None:
        official_query = rule_mirror(query["input"])

    for name, rival in rivals.items():
        fits_all = True
        for demo in demos:
            if not isinstance(demo, dict) or "input" not in demo:
                return ["every demonstration must contain an input grid"]
            official = demo.get("output")
            if official is None:
                official = rule_mirror(demo["input"])
            if rival(demo["input"]) != official:
                fits_all = False
                break
        if fits_all and rival(query["input"]) != official_query:
            reasons.append(f"plausible rival {name!r} fits every demo but changes the query answer")
    return reasons


# Named wrong-rule competitors make every semantic witness falsifiable instead
# of merely descriptive.  The gate checks that a claimed rival actually
# disagrees whenever its witness fires.
SEMANTIC_RIVALS = {
    "identity": lambda grid: [list(row) for row in grid],
    "left_pack": _left_pack,
    "reverse_order": _reverse_right_pack,
    "sort_ascending": lambda grid: _sorted_right_pack(grid, reverse=False),
    "sort_descending": lambda grid: _sorted_right_pack(grid, reverse=True),
    "fixed_one_step_right": _one_step_right,
}

WITNESS_RIVALS = {
    "visible_right_compaction": ["identity"],
    "unequal_move_distances": ["fixed_one_step_right"],
    "ascending_and_descending_order_controls": [
        "reverse_order",
        "sort_ascending",
        "sort_descending",
    ],
    "row_locality_preserved": ["identity"],
}

LESSON_COMPETITORS = {
    name: rival
    for name, rival in SEMANTIC_RIVALS.items()
    if name != "identity"
}


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local malformed scenes that the structural checker must reject."""
    blank = full_grid(3, 6, 0)

    duplicate_color = [
        [1, 0, 2, 0, 0, 0],
        [3, 0, 1, 4, 0, 0],
        [5, 0, 6, 0, 0, 0],
    ]

    already_right_packed = [
        [0, 0, 0, 0, 1, 2],
        [0, 0, 0, 3, 4, 5],
        [0, 0, 0, 0, 0, 6],
    ]

    only_one_multirow = [
        [1, 0, 2, 0, 3, 0],
        [0, 0, 0, 4, 0, 0],
        [5, 0, 0, 0, 0, 0],
    ]

    out_of_profile = [
        [1, 0, 2, 0, 3],
        [4, 0, 5, 0, 6],
        [0, 0, 0, 0, 0],
    ]

    return [
        ("all_background", blank),
        ("duplicate_nonzero_token", duplicate_color),
        ("already_right_packed_identity", already_right_packed),
        ("wrong_canonical_profile", out_of_profile),
        ("insufficient_multirow_structure", only_one_multirow),
    ]

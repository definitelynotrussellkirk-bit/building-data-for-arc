"""Generator for v2_meta_puzzles:H4 — mirror objects across sparse gray markers.

The two gray (5) cells occupy one column and jointly identify a vertical
reflection axis.  Every non-{0, 5} cell is preserved and copied to its mirror
position across that column.  A source object may touch the axis; axis cells
map to themselves while the remainder of the object is completed on the other
side.
"""
from __future__ import annotations

from collections import deque
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "158efba9f453"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "41cef903ecd8"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background grid contains exactly two isolated gray (5) cells in the "
    "same column; together they mark a sparse vertical mirror axis. One to "
    "three connected, distinctly colored motifs occupy only one source side, "
    "although a motif may touch the axis itself. Preserve the markers and all "
    "source cells, then add each non-{0,5} cell at column 2*axis-c with the "
    "same row and color. The result completes vertical symmetry around the "
    "marker column."
)

INVARIANTS = [
    "background is color 0",
    "exactly two isolated color-5 cells share one column and mark the axis",
    "one to three distinct-color connected motifs occupy one source side",
    "axis-touching motif cells are lawful but at least one motif cell is off-axis",
    "every mirrored destination is in bounds and blank in the input",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-anchored schedule with 7..12 variation",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-anchored schedule with 9..15 variation",
        "valid": "9..15",
    },
    "n_motifs": {
        "type": "int",
        "default": "canonical-anchored schedule, mostly 2 with 1/3 witnesses",
        "valid": "1..3",
    },
    "source_side": {
        "type": "enum",
        "default": "sample schedule left|right",
        "valid": "left|right",
    },
    "axis_zone": {
        "type": "enum",
        "default": "sample schedule left|center|right",
        "valid": "left|center|right",
    },
    "axis_overlap": {
        "type": "bool",
        "default": "sample schedule false|true",
        "valid": "false|true",
    },
    "marker_profile": {
        "type": "enum",
        "default": "sample schedule outer|inset|mixed",
        "valid": "outer|inset|mixed",
    },
}

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_SOURCE_SIDES = ("left", "right")
_AXIS_ZONES = ("left", "center", "right")
_MARKER_PROFILES = ("outer", "inset", "mixed")

# Shapes use (row_delta, distance_from_axis). Distance zero is an axis cell;
# positive distances extend into the selected source side.
_OVERLAP_SHAPES = (
    ((0, 0), (0, 1)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (1, 1)),
)
_OFF_AXIS_SHAPES = (
    ((0, 1), (1, 1)),
    ((0, 1), (0, 2)),
    ((0, 1), (1, 1), (1, 2)),
    ((0, 1), (1, 1), (2, 1)),
    ((0, 1), (0, 2), (1, 2)),
)


def _axis_zone(axis: int, width: int) -> str:
    """Classify an interior column into stable left/center/right thirds."""
    if 3 * axis < width - 1:
        return "left"
    if 3 * axis > 2 * (width - 1):
        return "right"
    return "center"


def _draw_scheduled_choice(ctx, label, options, scheduled, overrides):
    """Use a lesson schedule by default, while accepting every exact override."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _draw_scheduled_int(ctx, label, lo, hi, scheduled, overrides):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def _validate_generate_call(seed, sample_index, difficulty, overrides) -> None:
    """Reject scalar coercions before schedule arithmetic or keyed draws."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    for name in ("grid_h", "grid_w", "n_motifs"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
    for name in ("source_side", "axis_zone", "marker_profile"):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise TypeError(f"{name} override must be a string")
    value = overrides.get("axis_overlap")
    if value is not None and type(value) is not bool:
        raise TypeError("axis_overlap override must be a boolean")


def _scheduled_dimensions(difficulty, sample_index: int) -> tuple[int, int]:
    """Keep most ordinary draws on the two canonical size profiles.

    One slot per four-step cycle deliberately leaves the canonical sizes so a
    fixed-size solver is not sufficient. The profiles differ by difficulty, so
    the difficulty knob is observably live without changing task semantics.
    """
    profiles = {
        "easy": ((8, 11), (8, 11), (8, 11), (7, 9)),
        "medium": ((9, 13), (9, 13), (8, 11), (10, 15)),
        "hard": ((9, 13), (9, 13), (9, 13), (12, 15)),
        None: ((8, 11), (9, 13), (9, 13), (10, 15)),
    }
    return profiles[difficulty][sample_index % 4]


def _marker_rows(height: int, profile: str, rng) -> tuple[int, int]:
    if profile == "outer":
        return 0, height - 1
    if profile == "inset":
        return 1, height - 2
    if profile == "mixed":
        return (0, height - 2) if rng.randrange(2) == 0 else (1, height - 1)
    raise ValueError(f"unknown marker_profile: {profile!r}")


def _candidate_axis_columns(width: int, zone: str) -> list[int]:
    columns = [c for c in range(2, width - 2) if _axis_zone(c, width) == zone]
    if not columns:
        raise ValueError(f"no interior axis column for width={width}, zone={zone!r}")
    return columns


def _cells_for_shape(
    shape: tuple[tuple[int, int], ...],
    row0: int,
    axis: int,
    source_side: str,
) -> tuple[tuple[int, int], ...]:
    sign = -1 if source_side == "left" else 1
    return tuple((row0 + dr, axis + sign * distance) for dr, distance in shape)


def _four_neighbors(cell: tuple[int, int]):
    r, c = cell
    yield r - 1, c
    yield r + 1, c
    yield r, c - 1
    yield r, c + 1


def _place_motifs(
    grid: list[list[int]],
    *,
    axis: int,
    source_side: str,
    colors: tuple[int, ...],
    axis_overlap: bool,
    rng,
) -> bool:
    """Backtrack over small connected templates with one-cell object separation."""
    height, width = len(grid), len(grid[0])
    marker_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    }
    occupied = set(marker_cells)
    placements: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    side_span = min(axis, width - 1 - axis)

    def recurse(index: int) -> bool:
        if index == len(colors):
            return True
        needs_overlap = axis_overlap and index == 0
        shapes = list(_OVERLAP_SHAPES if needs_overlap else _OFF_AXIS_SHAPES)
        shapes = [s for s in shapes if max(distance for _, distance in s) <= side_span]
        rng.shuffle(shapes)
        for shape in shapes:
            shape_h = max(dr for dr, _ in shape) + 1
            rows = list(range(0, height - shape_h + 1))
            rng.shuffle(rows)
            for row0 in rows:
                cells = _cells_for_shape(shape, row0, axis, source_side)
                cell_set = set(cells)
                if len(cell_set) != len(cells):
                    continue
                if any(not (0 <= r < height and 0 <= c < width) for r, c in cells):
                    continue
                if any(cell in occupied for cell in cells):
                    continue
                # Distinct colored motifs and sparse markers remain separate
                # 4-connected objects. Neighbors within this motif are allowed.
                if any(
                    neighbor in occupied
                    for cell in cells
                    for neighbor in _four_neighbors(cell)
                    if neighbor not in cell_set
                ):
                    continue
                occupied.update(cells)
                placements.append((colors[index], cells))
                if recurse(index + 1):
                    return True
                placements.pop()
                occupied.difference_update(cells)
        return False

    if not recurse(0):
        return False
    for color, cells in placements:
        for r, c in cells:
            grid[r][c] = color
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_generate_call(seed, sample_index, difficulty, overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled_h, scheduled_w = _scheduled_dimensions(difficulty, sample_index)
    height = _draw_scheduled_int(
        ctx, "grid_h", 7, 12, scheduled_h, overrides
    )
    width = _draw_scheduled_int(
        ctx, "grid_w", 9, 15, scheduled_w, overrides
    )
    motif_schedule = (2, 2, 1, 2, 2, 3)
    n_motifs = _draw_scheduled_int(
        ctx, "n_motifs", 1, 3, motif_schedule[sample_index % len(motif_schedule)], overrides
    )
    source_side = _draw_scheduled_choice(
        ctx,
        "source_side",
        _SOURCE_SIDES,
        _SOURCE_SIDES[sample_index % len(_SOURCE_SIDES)],
        overrides,
    )
    axis_zone = _draw_scheduled_choice(
        ctx,
        "axis_zone",
        _AXIS_ZONES,
        _AXIS_ZONES[sample_index % len(_AXIS_ZONES)],
        overrides,
    )
    axis_overlap = _draw_scheduled_choice(
        ctx,
        "axis_overlap",
        (False, True),
        bool(sample_index % 2),
        overrides,
    )
    marker_profile = _draw_scheduled_choice(
        ctx,
        "marker_profile",
        _MARKER_PROFILES,
        _MARKER_PROFILES[sample_index % len(_MARKER_PROFILES)],
        overrides,
    )

    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")
    columns = _candidate_axis_columns(width, axis_zone)
    axis = layout_rng.choice(columns)
    marker_r1, marker_r2 = _marker_rows(height, marker_profile, layout_rng)
    colors = tuple(palette_rng.sample(_COLORS, n_motifs))

    grid = full_grid(height, width, 0)
    grid[marker_r1][axis] = 5
    grid[marker_r2][axis] = 5
    if not _place_motifs(
        grid,
        axis=axis,
        source_side=source_side,
        colors=colors,
        axis_overlap=axis_overlap,
        rng=layout_rng,
    ):
        raise ValueError(
            "could not place sparse-axis motifs for "
            f"{height=} {width=} {n_motifs=} {source_side=} "
            f"{axis_zone=} {axis_overlap=} {marker_profile=}"
        )

    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_motifs": n_motifs,
        "source_side": source_side,
        "axis_zone": axis_zone,
        "axis_overlap": axis_overlap,
        "marker_profile": marker_profile,
    }
    if observed != expected:
        raise RuntimeError(f"constructed grid does not realize keyed axes: {expected} -> {observed}")
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructed invalid grid: {errors}")
    return [row[:] for row in grid]


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        cell = queue.popleft()
        for neighbor in _four_neighbors(cell):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == cells


def _structural_info(grid) -> tuple[dict[str, object] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return None, ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return None, ["grid is ragged or has zero width"]
    height = len(grid)
    if not (5 <= height <= 30 and 7 <= width <= 30):
        errors.append(f"grid dimensions outside task grammar: {height}x{width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None, errors + ["grid contains a non-integer or color outside 0..9"]
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 is absent")

    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    if len(markers) != 2:
        return None, errors + [f"expected exactly two color-5 markers, got {len(markers)}"]
    marker_rows = sorted(r for r, _ in markers)
    marker_cols = {c for _, c in markers}
    if len(marker_cols) != 1:
        errors.append("the two color-5 markers must share one column")
        return None, errors
    axis = next(iter(marker_cols))
    if marker_rows[1] - marker_rows[0] < 2:
        errors.append("the two axis markers must be separated by at least one row")

    motif_by_color: dict[int, set[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 5):
                motif_by_color.setdefault(value, set()).add((r, c))
    if not (1 <= len(motif_by_color) <= 4):
        errors.append(
            f"expected 1..4 non-marker motif colors, got {len(motif_by_color)}"
        )
    for color, cells in sorted(motif_by_color.items()):
        if not _connected(cells):
            errors.append(f"motif color {color} is not one 4-connected object")

    left = {(r, c) for cells in motif_by_color.values() for r, c in cells if c < axis}
    right = {(r, c) for cells in motif_by_color.values() for r, c in cells if c > axis}
    if left and right:
        errors.append("motif cells occupy both sides of the sparse axis")
    if not left and not right:
        errors.append("no off-axis motif cell; the transformation would be identity")
    source_side = "left" if left else "right" if right else None

    for marker in markers:
        for neighbor in _four_neighbors(marker):
            r, c = neighbor
            if 0 <= r < height and 0 <= c < width and grid[r][c] not in (0, 5):
                errors.append("a motif touches an axis marker")
                break

    for cells in motif_by_color.values():
        for r, c in cells:
            mirror_c = 2 * axis - c
            if not 0 <= mirror_c < width:
                errors.append(f"cell {(r, c)} mirrors out of bounds to column {mirror_c}")
                continue
            if c != axis and grid[r][mirror_c] != 0:
                errors.append(
                    f"mirror destination {(r, mirror_c)} is already occupied in the input"
                )

    if marker_rows == [0, height - 1]:
        marker_profile = "outer"
    elif marker_rows == [1, height - 2]:
        marker_profile = "inset"
    elif (marker_rows[0] in (0, 1)) and (marker_rows[1] in (height - 2, height - 1)):
        marker_profile = "mixed"
    else:
        marker_profile = "other"

    info = {
        "grid_h": height,
        "grid_w": width,
        "axis": axis,
        "axis_zone": _axis_zone(axis, width),
        "marker_profile": marker_profile,
        "n_motifs": len(motif_by_color),
        "source_side": source_side,
        "axis_overlap": any(c == axis for cells in motif_by_color.values() for _, c in cells),
        "motif_colors": tuple(sorted(motif_by_color)),
    }
    return info, errors


def observe_overrides(grid) -> dict[str, object]:
    info, errors = _structural_info(grid)
    if info is None or errors:
        raise ValueError("; ".join(errors) or "could not inspect grid")
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the two-marker lesson grammar and exact requested axes."""
    info, errors = _structural_info(grid)
    if info is None:
        return errors
    if info["marker_profile"] not in _MARKER_PROFILES:
        errors.append(
            "marker rows do not form an outer, inset, or mixed sparse-axis profile"
        )

    requested = None
    if isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        requested = meta["overrides"]
    if requested:
        unknown = set(requested) - set(AXES)
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        if not errors:
            observed = {name: info[name] for name in AXES}
            for axis, expected in requested.items():
                if observed.get(axis) != expected:
                    errors.append(
                        f"requested {axis}={expected!r}, observed {observed.get(axis)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """This generator intentionally keeps every ordinary draw on-task."""
    return self_check(grid)


def rule_mirror(grid) -> list[list[int]]:
    """Python parity mirror used only by focused tests and semantic probes."""
    info, errors = _structural_info(grid)
    if info is None or errors:
        raise ValueError("; ".join(errors) or "invalid grid")
    axis = int(info["axis"])
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 5):
                out[r][2 * axis - c] = value
    return out


def _candidate_mirror(
    grid,
    *,
    axis: int,
    color_predicate: Callable[[int], bool] | None = None,
) -> list[list[int]] | None:
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 5):
                continue
            if color_predicate is not None and not color_predicate(value):
                continue
            mirror_c = 2 * axis - c
            if not 0 <= mirror_c < len(row):
                return None
            out[r][mirror_c] = value
    return out


def _candidate_horizontal(grid) -> list[list[int]] | None:
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    if len(markers) != 2:
        return None
    axis_r = markers[0][0]
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 5):
                continue
            mirror_r = 2 * axis_r - r
            if not 0 <= mirror_r < len(grid):
                return None
            out[mirror_r][c] = value
    return out


def _candidate_skip_axis_touching(grid, axis: int) -> list[list[int]] | None:
    touching = {
        value
        for row in grid
        for c, value in enumerate(row)
        if c == axis and value not in (0, 5)
    }
    return _candidate_mirror(grid, axis=axis, color_predicate=lambda value: value not in touching)


def _candidate_left_source_only(grid) -> list[list[int]]:
    """Canonical-fitting rival: reflect left sources, ignore right sources."""
    info, errors = _structural_info(grid)
    if info is None or errors:
        raise ValueError("; ".join(errors) or "invalid grid")
    if info["source_side"] == "left":
        return rule_mirror(grid)
    return [row[:] for row in grid]


CANONICAL_SHORTCUTS = {
    "left_source_only": _candidate_left_source_only,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)


def _candidate_rules(grid) -> dict[str, list[list[int]] | None]:
    info, errors = _structural_info(grid)
    if info is None or errors:
        return {}
    axis = int(info["axis"])
    colors = tuple(info["motif_colors"])
    center_axis = len(grid[0]) // 2
    return {
        "identity": [row[:] for row in grid],
        "left_source_only": _candidate_left_source_only(grid),
        "grid_center_axis": _candidate_mirror(grid, axis=center_axis),
        "only_lowest_color": _candidate_mirror(
            grid, axis=axis, color_predicate=lambda value: value == colors[0]
        ),
        "only_highest_color": _candidate_mirror(
            grid, axis=axis, color_predicate=lambda value: value == colors[-1]
        ),
        "skip_axis_touching_object": _candidate_skip_axis_touching(grid, axis),
        "horizontal_from_first_marker": _candidate_horizontal(grid),
    }


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a plausible shortcut survives with a new query answer."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["lesson has no demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query lacks input/output"]

    candidate_names = set(_candidate_rules(demos[0]["input"]))
    for demo in demos:
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return ["a demonstration lacks input/output"]
        candidates = _candidate_rules(demo["input"])
        candidate_names &= {
            name for name, output in candidates.items() if output is not None and output == demo["output"]
        }
    query_candidates = _candidate_rules(query["input"])
    for name in sorted(candidate_names):
        candidate_output = query_candidates.get(name)
        if candidate_output is not None and candidate_output != query["output"]:
            reasons.append(f"shortcut {name!r} fits every demo but changes the query answer")
    return reasons


def _obs(grid, key):
    try:
        return observe_overrides(grid).get(key)
    except ValueError:
        return None


DISTRIBUTION_WITNESSES = {
    "source_left": lambda grid: _obs(grid, "source_side") == "left",
    "source_right": lambda grid: _obs(grid, "source_side") == "right",
    "axis_overlap": lambda grid: _obs(grid, "axis_overlap") is True,
    "off_axis_only": lambda grid: _obs(grid, "axis_overlap") is False,
    "axis_zone_left": lambda grid: _obs(grid, "axis_zone") == "left",
    "axis_zone_center": lambda grid: _obs(grid, "axis_zone") == "center",
    "axis_zone_right": lambda grid: _obs(grid, "axis_zone") == "right",
    "marker_outer": lambda grid: _obs(grid, "marker_profile") == "outer",
    "marker_inset": lambda grid: _obs(grid, "marker_profile") == "inset",
    "marker_mixed": lambda grid: _obs(grid, "marker_profile") == "mixed",
    "one_motif": lambda grid: _obs(grid, "n_motifs") == 1,
    "two_motifs": lambda grid: _obs(grid, "n_motifs") == 2,
    "three_motifs": lambda grid: _obs(grid, "n_motifs") == 3,
}

# Semantic witnesses are reserved for executable counterexamples to a named
# rival. Other observable coverage axes remain available above without being
# misreported as evidence against a shortcut.
SEMANTIC_WITNESSES = {
    "source_right": DISTRIBUTION_WITNESSES["source_right"],
}
WITNESS_RIVALS = {
    "source_right": ["left_source_only"],
}

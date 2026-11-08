"""Generator for ARC rule family 4f065093e631 (source task 890034e9).

A dense 21x21 scene contains one largest monochrome rectangular
frame whose interior is zero.  Exactly one other same-sized rectangle has an
all-zero interior.  Copy the source frame color onto that second rectangle's
border, preserving the rest of the scene.

The four scene profiles preserve every demonstrated frame dimension and its
balanced-versus-primary-dense noise regime.  Frame color, base colors, source
and target positions, and the individual noise cells remain nuisance
variables.

Even sample indices retain the four-color canonical scene. Odd indices add a
disjoint smaller frame in a fresh fifth color, so choosing a frame merely by
its color's rarity is insufficient. The largest-frame copy rule is unchanged.
An independent low/interior/high source-color rank cycle prevents numerical
palette extrema from becoming an unchallenged condition on applying the rule.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "4f065093e631"
TASK_ID = "4f065093e631"
VERSION = "3.1.0"
RULE_HASH = "6d3fbf3d14b4"

SUMMARY = (
    "Find the largest nonzero monochrome rectangular frame with an all-zero "
    "interior. Find the other same-sized all-zero interior slot in row-major "
    "order and paint that slot's border with the frame color."
)

INVARIANTS = [
    "the canvas is exactly 21x21 with four colors, or five with the scheduled decoy",
    "the frame color occurs only on the complete source-frame border",
    "the source frame is the unique largest zero-interior monochrome frame",
    "exactly two same-sized zero interiors identify source and target slots",
    "the source and target rectangles are disjoint",
    "the two non-role colors form dense noise in the demonstrated count envelope",
    "a fifth color, when present, occurs exactly eight times on one disjoint 3x3 frame",
]

SCENE_PROFILES = (
    "frame_4x5_balanced",
    "frame_5x4_primary_dense",
    "frame_5x6_balanced",
    "frame_7x4_primary_dense",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "uniform complete demonstrated frame/noise profile",
        "valid": (
            "frame_4x5_balanced|frame_5x4_primary_dense|"
            "frame_5x6_balanced|frame_7x4_primary_dense"
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 6
_SOURCE_COLOR_RANKS = ("low", "interior", "high")
SCHEDULE_PROFILES = tuple(
    f"{'rare_color_decoy' if index % 2 else 'canonical_anchor'}_source_"
    f"{_SOURCE_COLOR_RANKS[index % 3]}"
    for index in range(LESSON_SCHEDULE_PERIOD)
)

_HEIGHT = 21
_WIDTH = 21

_PROFILE_DIMS = {
    "frame_4x5_balanced": (4, 5),
    "frame_5x4_primary_dense": (5, 4),
    "frame_5x6_balanced": (5, 6),
    "frame_7x4_primary_dense": (7, 4),
}

_PROFILE_COUNTS = {
    # zero, less-frequent base color.  The other base-color count is derived
    # after reserving the source-frame border.
    "frame_4x5_balanced": (179, 96),
    "frame_5x4_primary_dense": (127, 42),
    "frame_5x6_balanced": (148, 84),
    "frame_7x4_primary_dense": (122, 36),
}

_PROFILE_COUNT_BOUNDS = {
    "frame_4x5_balanced": ((165, 185), (75, 100)),
    "frame_5x4_primary_dense": ((120, 140), (32, 55)),
    "frame_5x6_balanced": ((135, 160), (68, 100)),
    "frame_7x4_primary_dense": ((113, 140), (32, 55)),
}

_PROFILE_BY_DIMS = {
    dimensions: profile
    for profile, dimensions in _PROFILE_DIMS.items()
}

_PROFILE_INDEX = {
    profile: index for index, profile in enumerate(SCENE_PROFILES)
}

# Public inputs are retained only as a never-partial fallback.  Outputs are not
# embedded: rule_mirror always derives the answer from the returned input.
_FALLBACK_ROWS = {
    "frame_4x5_balanced": (
        "303433330334030434400",
        "330033340044430033403",
        "444343030043033430030",
        "044430333030300003433",
        "330433000030444303000",
        "030030030300033334303",
        "030034034044003400033",
        "033304434303334030333",
        "404343440040000303300",
        "004000034434000400433",
        "300888884303304404444",
        "330800083000040330433",
        "000800083303343040300",
        "304888880303003330430",
        "400003040030033340403",
        "004300030034004003434",
        "440030344343404403434",
        "343300003034000333303",
        "000003033403334040340",
        "333040430003003300430",
        "043330443434043440040",
    ),
    "frame_5x4_primary_dense": (
        "081101111010101111111",
        "110811101000111101111",
        "100100222211111811110",
        "011111200211111118101",
        "111110200210011010110",
        "100001200218111110111",
        "001101222210100118008",
        "018001100110111181100",
        "111881110081111181001",
        "810111108110111100101",
        "801111100111101181181",
        "111810118101110111101",
        "108118011111110108111",
        "118111010011081010118",
        "111111008100118118101",
        "888111181100110111101",
        "110180081100111101010",
        "188111111111011100110",
        "118010110111111010011",
        "110081010000111080000",
        "100100100111101108180",
    ),
    "frame_5x6_balanced": (
        "003032020332222222233",
        "322032022222222322032",
        "330300322223222230032",
        "223244444430320222003",
        "332040000420220230220",
        "322240000403223223320",
        "202040000420002220222",
        "020244444422020200222",
        "202220202032330200022",
        "023030232220200022320",
        "302020022033230330030",
        "230322222000020203002",
        "322020220322223022222",
        "333202020322200322322",
        "002223200232030223220",
        "222223233320000200230",
        "222230033200000022320",
        "203222323330000020023",
        "220000000323223002200",
        "030222000222230200032",
        "232220032032022230022",
    ),
    "frame_7x4_primary_dense": (
        "021011110010120111012",
        "111021210111101110211",
        "111022111110111011211",
        "221111111110111201111",
        "021011221101100101112",
        "100110111110100110020",
        "011000110110100110111",
        "111221012211200101112",
        "101010021110000111010",
        "010011011111111101101",
        "011101011110111101111",
        "011100101011111001110",
        "010011111111100211111",
        "133331202110100100111",
        "230031010101111111110",
        "130031120111021110111",
        "130031200012111210101",
        "130031101010101111111",
        "030031020111101102111",
        "133331111111111100110",
        "111210101011111101111",
    ),
}

_FALLBACK_ROLE_COLORS = {
    "frame_4x5_balanced": (8, 3, 4),
    "frame_5x4_primary_dense": (2, 1, 8),
    "frame_5x6_balanced": (4, 2, 3),
    "frame_7x4_primary_dense": (3, 1, 2),
}


def _coerce_arc_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    if len(grid) > 30 or width > 30:
        return None, ["grid dimensions must not exceed 30x30"]
    errors = []
    coerced = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        coerced.append(converted)
    if errors:
        return None, errors
    return coerced, []


def _prefix_for_value(grid, value):
    height = len(grid)
    width = len(grid[0])
    table = [
        [0 for _col in range(width + 1)]
        for _row in range(height + 1)
    ]
    for row in range(height):
        running = 0
        for col in range(width):
            running += grid[row][col] == value
            table[row + 1][col + 1] = (
                table[row][col + 1] + running
            )
    return table


def _rect_count(table, top, left, bottom, right):
    """Count a value in the half-open rectangle."""
    return (
        table[bottom][right]
        - table[top][right]
        - table[bottom][left]
        + table[top][left]
    )


def _horizontal_runs(grid):
    height = len(grid)
    width = len(grid[0])
    runs = [
        [1 for _col in range(width)]
        for _row in range(height)
    ]
    for row in range(height):
        for col in range(width - 2, -1, -1):
            if grid[row][col] == grid[row][col + 1]:
                runs[row][col] = runs[row][col + 1] + 1
    return runs


def _find_frames(grid):
    """Return every nonzero monochrome frame with an all-zero interior."""
    height = len(grid)
    width = len(grid[0])
    colors = sorted({
        value for row in grid for value in row if value != 0
    })
    prefixes = {
        color: _prefix_for_value(grid, color)
        for color in (0, *colors)
    }
    runs = _horizontal_runs(grid)
    frames = []
    for top in range(height - 2):
        for left in range(width - 2):
            color = grid[top][left]
            if color == 0:
                continue
            maximum_width = min(runs[top][left], width - left)
            for frame_width in range(3, maximum_width + 1):
                right = left + frame_width - 1
                for bottom in range(top + 2, height):
                    if (
                        grid[bottom][left] != color
                        or runs[bottom][left] < frame_width
                    ):
                        continue
                    frame_height = bottom - top + 1
                    interior_area = (
                        (frame_height - 2) * (frame_width - 2)
                    )
                    if _rect_count(
                        prefixes[0],
                        top + 1,
                        left + 1,
                        bottom,
                        right,
                    ) != interior_area:
                        continue
                    border_area = (
                        2 * frame_height + 2 * frame_width - 4
                    )
                    if _rect_count(
                        prefixes[color],
                        top,
                        left,
                        bottom + 1,
                        right + 1,
                    ) == border_area:
                        frames.append((
                            color,
                            top,
                            left,
                            bottom,
                            right,
                            frame_height * frame_width,
                        ))
    return frames


def _zero_slots(grid, frame_height, frame_width):
    height = len(grid)
    width = len(grid[0])
    zeros = _prefix_for_value(grid, 0)
    interior_area = (frame_height - 2) * (frame_width - 2)
    return tuple(
        (
            top,
            left,
            top + frame_height - 1,
            left + frame_width - 1,
        )
        for top in range(height - frame_height + 1)
        for left in range(width - frame_width + 1)
        if _rect_count(
            zeros,
            top + 1,
            left + 1,
            top + frame_height - 1,
            left + frame_width - 1,
        ) == interior_area
    )


def _disjoint(first, second):
    return (
        first[2] < second[0]
        or second[2] < first[0]
        or first[3] < second[1]
        or second[3] < first[1]
    )


def _border_cells(box):
    top, left, bottom, right = box
    return tuple(
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    )


def _interior_cells(box):
    top, left, bottom, right = box
    return tuple(
        (row, col)
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
    )


def _semantic_signature(grid):
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return None
    if len(coerced) != _HEIGHT or len(coerced[0]) != _WIDTH:
        return None
    counts = Counter(value for row in coerced for value in row)
    if len(counts) not in (4, 5) or 0 not in counts:
        return None

    frames = _find_frames(coerced)
    if not frames:
        return None
    frames.sort(key=lambda frame: frame[-1], reverse=True)
    best = frames[0]
    if len(frames) > 1 and frames[1][-1] >= best[-1]:
        return None
    color, top, left, bottom, right, _area = best
    frame_height = bottom - top + 1
    frame_width = right - left + 1
    profile = _PROFILE_BY_DIMS.get((frame_height, frame_width))
    if profile is None:
        return None
    border_count = 2 * frame_height + 2 * frame_width - 4
    if counts[color] != border_count:
        return None

    source = (top, left, bottom, right)
    slots = _zero_slots(coerced, frame_height, frame_width)
    if len(slots) != 2 or source not in slots:
        return None
    target = next(slot for slot in slots if slot != source)
    if not _disjoint(source, target):
        return None

    decoy_color = None
    if len(counts) == 5:
        candidates = [
            value for value, count in counts.items()
            if value not in (0, color) and count == 8
        ]
        if len(candidates) != 1:
            return None
        decoy_color = candidates[0]
        decoy_frames = [frame for frame in frames if frame[0] == decoy_color]
        if len(decoy_frames) != 1:
            return None
        _, dt, dl, db, dr, _ = decoy_frames[0]
        decoy = (dt, dl, db, dr)
        if db - dt != 2 or dr - dl != 2:
            return None
        if not _disjoint(decoy, source) or not _disjoint(decoy, target):
            return None

    base_counts = sorted(
        count
        for value, count in counts.items()
        if value not in (0, color, decoy_color)
    )
    if not (
        100 <= counts[0] <= 200
        and 30 <= base_counts[0] <= 110
        and 140 <= base_counts[1] <= 280
    ):
        return None
    return {"scene_profile": profile}


def canonical_profile_index(grid):
    """Return the linked demonstrated profile index, if calibrated."""
    signature = _semantic_signature(grid)
    if signature is None:
        return None
    return _PROFILE_INDEX[signature["scene_profile"]]


def observe_overrides(grid):
    """Recover every declared exact axis from a valid returned grid."""
    signature = _semantic_signature(grid)
    return {} if signature is None else dict(signature)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if (
        "scene_profile" in overrides
        and overrides["scene_profile"] not in SCENE_PROFILES
    ):
        raise ValueError("unknown scene_profile")


def _profile_options():
    return sum(
        ((profile,) * 25 for profile in SCENE_PROFILES),
        (),
    )


def _density_counts(profile, difficulty, rng):
    canonical_zero, canonical_secondary = _PROFILE_COUNTS[profile]
    zero_bounds, secondary_bounds = _PROFILE_COUNT_BOUNDS[profile]
    spread = {
        "easy": 3,
        "hard": 12,
    }.get(difficulty, 7)
    zero_count = rng.randint(
        max(zero_bounds[0], canonical_zero - spread),
        min(zero_bounds[1], canonical_zero + spread),
    )
    secondary_count = rng.randint(
        max(
            secondary_bounds[0],
            canonical_secondary - spread,
        ),
        min(
            secondary_bounds[1],
            canonical_secondary + spread,
        ),
    )
    frame_height, frame_width = _PROFILE_DIMS[profile]
    frame_count = 2 * frame_height + 2 * frame_width - 4
    primary_count = (
        _HEIGHT * _WIDTH
        - frame_count
        - zero_count
        - secondary_count
    )
    if not (
        100 <= zero_count <= 200
        and 30 <= secondary_count <= 110
        and 140 <= primary_count <= 280
    ):
        raise AssertionError("density calibration escaped its envelope")
    return zero_count, primary_count, secondary_count


def _boxes(frame_height, frame_width):
    return tuple(
        (
            top,
            left,
            top + frame_height - 1,
            left + frame_width - 1,
        )
        for top in range(_HEIGHT - frame_height + 1)
        for left in range(_WIDTH - frame_width + 1)
    )


def _try_random_scene(
    profile,
    frame_color,
    primary_color,
    secondary_color,
    counts,
    rng,
    *,
    attempts,
):
    frame_height, frame_width = _PROFILE_DIMS[profile]
    candidates = _boxes(frame_height, frame_width)
    zero_count, primary_count, secondary_count = counts
    for _attempt in range(attempts):
        source = rng.choice(candidates)
        target = rng.choice(tuple(
            box for box in candidates if _disjoint(source, box)
        ))
        source_border = set(_border_cells(source))
        fixed_zeros = set(_interior_cells(source))
        fixed_zeros.update(_interior_cells(target))
        fillable = [
            (row, col)
            for row in range(_HEIGHT)
            for col in range(_WIDTH)
            if (row, col) not in source_border
            and (row, col) not in fixed_zeros
        ]
        values = (
            [0] * (zero_count - len(fixed_zeros))
            + [primary_color] * primary_count
            + [secondary_color] * secondary_count
        )
        if len(values) != len(fillable):
            raise AssertionError("scene count accounting is inconsistent")
        rng.shuffle(values)
        grid = [
            [0 for _col in range(_WIDTH)]
            for _row in range(_HEIGHT)
        ]
        for row, col in source_border:
            grid[row][col] = frame_color
        for (row, col), value in zip(fillable, values):
            grid[row][col] = value
        if _semantic_signature(grid) == {"scene_profile": profile}:
            return grid
    return None


def _fallback_scene(
    profile,
    frame_color,
    primary_color,
    secondary_color,
):
    source_frame, source_primary, source_secondary = (
        _FALLBACK_ROLE_COLORS[profile]
    )
    color_map = {
        0: 0,
        source_frame: frame_color,
        source_primary: primary_color,
        source_secondary: secondary_color,
    }
    grid = [
        [color_map[int(value)] for value in row]
        for row in _FALLBACK_ROWS[profile]
    ]
    if _semantic_signature(grid) != {"scene_profile": profile}:
        raise AssertionError("fallback lost the requested scene profile")
    return grid


def _add_rare_color_decoy(grid, profile, decoy_color, rng):
    """Place one disjoint 3x3 frame by a bounded shuffled location search.

    Cheap count checks precede geometry checks. Exhausting the finite candidate
    set is explicit failure: an odd-index teaching case never becomes an anchor.
    """
    counts = Counter(value for row in grid for value in row)
    if len(counts) != 4 or _semantic_signature(grid) != {"scene_profile": profile}:
        raise ValueError("decoy placement needs a valid four-color anchor")
    if type(decoy_color) is not int or not 1 <= decoy_color <= 9 or decoy_color in counts:
        raise ValueError("decoy color must be a fresh nonzero ARC color")
    frame = max(_find_frames(grid), key=lambda item: item[-1])
    source_color, top, left, bottom, right, _area = frame
    source = (top, left, bottom, right)
    target = next(
        slot for slot in _zero_slots(grid, bottom - top + 1, right - left + 1)
        if slot != source
    )
    secondary, primary = sorted(
        (color for color in counts if color not in (0, source_color)),
        key=lambda color: counts[color],
    )
    zero_bounds, secondary_bounds = _PROFILE_COUNT_BOUNDS[profile]
    candidates = [
        box for box in _boxes(3, 3)
        if _disjoint(box, source) and _disjoint(box, target)
    ]
    rng.shuffle(candidates)
    for box in candidates:
        dt, dl, db, dr = box
        proposed_counts = counts.copy()
        proposed_counts.subtract(
            grid[row][col]
            for row in range(dt, db + 1)
            for col in range(dl, dr + 1)
        )
        proposed_counts.update({decoy_color: 8, 0: 1})
        if not (
            zero_bounds[0] <= proposed_counts[0] <= zero_bounds[1]
            and secondary_bounds[0] <= proposed_counts[secondary] <= secondary_bounds[1]
            and 140 <= proposed_counts[primary] <= 280
        ):
            continue
        candidate = [row[:] for row in grid]
        for row, col in _border_cells(box):
            candidate[row][col] = decoy_color
        candidate[dt + 1][dl + 1] = 0
        if _semantic_signature(candidate) == {"scene_profile": profile}:
            return candidate
    raise RuntimeError(f"no lawful disjoint rare-color decoy location for {profile}")


def _recolor_source_rank(grid, source_color, sample_index, rng):
    """Permute the existing palette while independently scheduling source rank."""
    palette = sorted({value for row in grid for value in row if value != 0})
    rank = sample_index % 3
    selected = (palette[0] if rank == 0 else palette[-1] if rank == 2
                else rng.choice(palette[1:-1]))
    originals = [color for color in palette if color != source_color]
    replacements = [color for color in palette if color != selected]
    rng.shuffle(replacements)
    mapping = {0: 0, source_color: selected}
    mapping.update(zip(originals, replacements))
    return [[mapping[value] for value in row] for row in grid]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", _profile_options())
    frame_color, primary_color, secondary_color = (
        ctx.draw_distinct_colors(
            "role_colors",
            n=3,
            exclude={0},
        )
    )
    counts = _density_counts(
        profile,
        difficulty,
        ctx.draw_rng("density"),
    )
    grid = _try_random_scene(
        profile,
        frame_color,
        primary_color,
        secondary_color,
        counts,
        ctx.draw_rng("scene"),
        attempts=192,
    )
    if grid is None:
        grid = _fallback_scene(
            profile,
            frame_color,
            primary_color,
            secondary_color,
        )
    if sample_index % 2:
        decoy_rng = ctx.draw_rng("rare_color_decoy")
        decoy_color = decoy_rng.choice(tuple(
            color for color in range(1, 10)
            if color not in (frame_color, primary_color, secondary_color)
        ))
        grid = _add_rare_color_decoy(grid, profile, decoy_color, decoy_rng)
    grid = _recolor_source_rank(
        grid, frame_color, sample_index, ctx.draw_rng("source_color_rank"),
    )
    if observe_overrides(grid) != {"scene_profile": profile}:
        raise AssertionError("constructed scene lost its exact axis")
    return grid


def rule_mirror(grid):
    """Broad Python mirror of the canonical largest-frame copy rule."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    frames = _find_frames(coerced)
    if not frames:
        raise ValueError("grid has no zero-interior monochrome frame")
    # Racket enumerates color/top/bottom/left/right ascending, conses each
    # candidate, then stably sorts by area. Preserve that reverse-enumeration
    # tie order even outside the production domain's unique-largest frames.
    frames.sort(
        key=lambda frame: (frame[5], frame[0], frame[1], frame[3], frame[2], frame[4]),
        reverse=True,
    )
    color, top, left, bottom, right, _area = frames[0]
    frame_height = bottom - top + 1
    frame_width = right - left + 1
    target = next(
        (
            slot
            for slot in _zero_slots(
                coerced,
                frame_height,
                frame_width,
            )
            if (slot[0], slot[1]) != (top, left)
        ),
        None,
    )
    if target is None:
        raise ValueError("grid has no second same-sized zero interior")
    output = [row[:] for row in coerced]
    for row, col in _border_cells(target):
        output[row][col] = color
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept calibrated anchors and their complete scheduled decoy extension."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if _semantic_signature(coerced) is None:
        return [
            "grid must be one complete 21x21 calibrated four-color anchor "
            "or five-color scene with one disjoint fresh-color 3x3 decoy; the "
            "frame/noise profile with a unique largest source frame and "
            "exactly one disjoint same-size zero-interior target"
        ]
    if rule_mirror(coerced) == coerced:
        return ["the copied target border must change the grid"]
    return []


def strict_canonical_like(grid):
    """The original four-color calibrated manifold supplies canonical support."""
    if _semantic_signature(grid) is None:
        return ["not a complete calibrated frame scene"]
    if len({value for row in grid for value in row}) != 4:
        return ["the scheduled fifth-color decoy is outside the canonical palette size"]
    return []


def schedule_profile(seed, sample_index, difficulty=None):
    """The independent parity and source-rank schedules repeat modulo six."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _rarest_color_bbox(grid):
    """Plausible shortcut: infer the source from color rarity and its bounds."""
    coerced, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    counts = Counter(value for row in coerced for value in row if value != 0)
    if not counts:
        return [row[:] for row in coerced]
    color = min(counts, key=lambda value: (counts[value], value))
    cells = [(row, col) for row, values in enumerate(coerced)
             for col, value in enumerate(values) if value == color]
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    bottom = max(row for row, _ in cells)
    right = max(col for _, col in cells)
    output = [row[:] for row in coerced]
    if bottom - top < 2 or right - left < 2:
        return output
    target = next((
        slot for slot in _zero_slots(coerced, bottom - top + 1, right - left + 1)
        if slot != (top, left, bottom, right)
    ), None)
    if target is not None:
        for row, col in _border_cells(target):
            output[row][col] = color
    return output


def _identity_rival(grid):
    return [list(row) for row in grid]


def _numeric_color_only(grid, highest):
    """Apply intended updates only when their output color is a numeric extreme."""
    output = rule_mirror(grid)
    colors = sorted({value for row in grid for value in row if value != 0})
    selected = colors[-1 if highest else 0]
    return [
        [value if value == selected else grid[row][col]
         for col, value in enumerate(values)]
        for row, values in enumerate(output)
    ]


def _first_color_only(grid):
    return _numeric_color_only(grid, False)


def _last_color_only(grid):
    return _numeric_color_only(grid, True)


def _has_rare_color_decoy(grid):
    return (
        _semantic_signature(grid) is not None
        and len({value for row in grid for value in row}) == 5
    )


def _has_interior_source_color(grid):
    if _semantic_signature(grid) is None:
        return False
    counts = Counter(value for row in grid for value in row)
    source_color = next(color for color, count in counts.items()
                        if color != 0 and count in (14, 18))
    palette = sorted(color for color in counts if color != 0)
    return palette[0] < source_color < palette[-1]


CANONICAL_SHORTCUTS = {"rarest_color_bbox": _rarest_color_bbox}
SEMANTIC_RIVALS = {
    "rarest_color_bbox": _rarest_color_bbox,
    "identity": _identity_rival,
    "first_color_only": _first_color_only,
    "last_color_only": _last_color_only,
}
SEMANTIC_WITNESSES = {
    "rare_color_decoy": _has_rare_color_decoy,
    "interior_source_color": _has_interior_source_color,
}
WITNESS_RIVALS = {
    "rare_color_decoy": ("rarest_color_bbox",),
    "interior_source_color": ("first_color_only", "last_color_only"),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Check the supplied labels against the declared finite rival family.

    This hook does not claim uniqueness against every possible alternate rule.
    Official lesson checks independently score these rivals with Racket labels.
    """
    if not demos:
        return ["at least one labeled demonstration is required"]
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons

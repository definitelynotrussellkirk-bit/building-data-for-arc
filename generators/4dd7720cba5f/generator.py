"""Generate framed tile arrays completed by same-color motif sharing.

Each input is an array of 5x5 monochrome frames separated by one-cell
zero rows and columns.  One or more frames of a color may contain partial
central motifs.  The transformation unions all same-color motif offsets and
copies that union into every frame of the color, leaving other colors alone.
"""

from __future__ import annotations

from collections import defaultdict
import copy
from typing import NamedTuple

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "4dd7720cba5f"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "d947d085ded3"
SUMMARY = (
    "Split the zero-separated grid into 5x5 framed tiles, union all "
    "interior motif offsets carried by each color, and copy that union "
    "into every frame of that same color."
)
INVARIANTS = [
    "one-cell all-zero rows and columns separate complete 5x5 frames",
    "each tile contains only zero and its nonzero frame color",
    "every nonempty source fragment is a 1..5-cell central 8-connected motif",
    "declared union profiles split one motif across multiple same-color tiles",
    "at least one repeated color gains a motif offset, so the output changes",
]
EXPECTED_OUTPUT_CODOMAIN = 1_000_000

Grid = list[list[int]]
TILE_SIZE = 5
STRIDE = TILE_SIZE + 1
COLORS = tuple(range(1, 9))


class SceneSpec(NamedTuple):
    rows: int
    cols: int
    multiplicities: tuple[int, ...]
    active_repeated_sources: tuple[tuple[int, int], ...]
    active_unique_motif_sizes: tuple[int, ...]
    public: bool
    fragmented_repeated_sources: tuple[
        tuple[int, int, tuple[int, ...]], ...
    ] = ()

    @property
    def active_repeated_multiplicities(self) -> tuple[int, ...]:
        return tuple(
            sorted(
                tuple(
                    multiplicity
                    for multiplicity, _ in self.active_repeated_sources
                )
                + tuple(
                    multiplicity
                    for multiplicity, _, _
                    in self.fragmented_repeated_sources
                ),
                reverse=True,
            )
        )

    @property
    def active_unique(self) -> int:
        return len(self.active_unique_motif_sizes)


SCENE_SPECS = {
    # Complete linked layout/color-multiplicity profiles from the four
    # demonstrations and the visible held-out input.
    "public_2x3_21111": SceneSpec(
        2, 3, (2, 1, 1, 1, 1), ((2, 5),), (), True
    ),
    "public_3x3_32211": SceneSpec(
        3, 3, (3, 2, 2, 1, 1), ((3, 3), (2, 1)), (3,), True
    ),
    "public_3x3_3222": SceneSpec(
        3,
        3,
        (3, 2, 2, 2),
        ((3, 5), (2, 3), (2, 3), (2, 1)),
        (),
        True,
    ),
    "public_4x3_4221111": SceneSpec(
        4,
        3,
        (4, 2, 2, 1, 1, 1, 1),
        ((4, 4), (2, 3), (2, 2)),
        (1, 3, 4),
        True,
    ),
    "public_4x4_5322211": SceneSpec(
        4,
        4,
        (5, 3, 2, 2, 2, 1, 1),
        ((5, 4), (3, 3), (2, 3), (2, 3)),
        (3,),
        True,
    ),
    # Lawful extrapolations preserve the demonstrated 5x5 frame grammar
    # while transposing a rectangular layout or recombining observed group
    # cardinalities.
    "transpose_3x2_21111": SceneSpec(
        3, 2, (2, 1, 1, 1, 1), ((2, 5),), (), False
    ),
    "extrap_3x3_222111": SceneSpec(
        3,
        3,
        (2, 2, 2, 1, 1, 1),
        ((2, 5), (2, 3), (2, 1)),
        (3,),
        False,
    ),
    "transpose_3x4_4221111": SceneSpec(
        3,
        4,
        (4, 2, 2, 1, 1, 1, 1),
        ((4, 4), (2, 3), (2, 2)),
        (1, 3, 4),
        False,
    ),
    "extrap_4x4_4332211": SceneSpec(
        4,
        4,
        (4, 3, 3, 2, 2, 1, 1),
        ((4, 4), (3, 3), (3, 3), (2, 3)),
        (3,),
        False,
    ),
    # Source-bound counterexamples for the canonical-ambiguous shortcut
    # "copy only the first source tile".  Each tuple is
    # (same-color multiplicity, union size, per-source fragment sizes).
    "union_2x3_21111": SceneSpec(
        2,
        3,
        (2, 1, 1, 1, 1),
        (),
        (),
        False,
        ((2, 3, (2, 2)),),
    ),
    "union_3x3_32211": SceneSpec(
        3,
        3,
        (3, 2, 2, 1, 1),
        ((2, 1),),
        (3,),
        False,
        ((3, 4, (3, 2)),),
    ),
    "union_4x3_4221111": SceneSpec(
        4,
        3,
        (4, 2, 2, 1, 1, 1, 1),
        ((2, 3), (2, 2)),
        (1, 3, 4),
        False,
        ((4, 5, (3, 3)),),
    ),
}
SCENE_PROFILES = tuple(SCENE_SPECS)
PUBLIC_PROFILES = tuple(
    name for name, spec in SCENE_SPECS.items() if spec.public
)

_STANDARD_PROFILE_WEIGHTS = {
    "easy": (
        ("public_2x3_21111",) * 4
        + ("transpose_3x2_21111",) * 4
    ),
    "medium": (
        ("public_3x3_32211",) * 2
        + ("public_3x3_3222",) * 2
        + ("extrap_3x3_222111",) * 4
    ),
    "hard": (
        ("public_4x3_4221111",) * 2
        + ("public_4x4_5322211",) * 2
        + ("transpose_3x4_4221111",) * 2
        + ("extrap_4x4_4332211",) * 2
    ),
    "all": tuple(
        profile
        for profile, spec in SCENE_SPECS.items()
        if not spec.fragmented_repeated_sources
    ),
}

_UNION_PROFILE_WEIGHTS = {
    "easy": ("union_2x3_21111",),
    "medium": ("union_3x3_32211",),
    "hard": ("union_4x3_4221111",),
    "all": (
        "union_2x3_21111",
        "union_3x3_32211",
        "union_4x3_4221111",
    ),
}
SCHEDULE_PROFILES = ("standard", "multi_source_union")
EXAMPLES_NEEDED = 3

_PROFILE_BY_KEY = {
    (
        spec.rows,
        spec.cols,
        spec.multiplicities,
        tuple(sorted(spec.active_repeated_sources, reverse=True)),
        tuple(sorted(spec.fragmented_repeated_sources, reverse=True)),
        tuple(sorted(spec.active_unique_motif_sizes)),
    ): name
    for name, spec in SCENE_SPECS.items()
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted framed-tile profile",
        "valid": (
            "public_2x3_21111|public_3x3_32211|public_3x3_3222|"
            "public_4x3_4221111|public_4x4_5322211|"
            "transpose_3x2_21111|extrap_3x3_222111|"
            "transpose_3x4_4221111|extrap_4x4_4332211|"
            "union_2x3_21111|union_3x3_32211|union_4x3_4221111"
        ),
    },
}


def _band(difficulty) -> str:
    if difficulty in {"easy", "medium", "hard"}:
        return str(difficulty)
    if difficulty is None:
        return "all"
    raise ValueError(f"invalid difficulty: {difficulty!r}")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Name the three-draw curriculum slot used by default generation."""
    del seed
    _band(difficulty)
    return (
        "multi_source_union"
        if int(sample_index) % EXAMPLES_NEEDED == 0
        else "standard"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic framed-tile union-completion input."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    band = _band(difficulty)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("scene_profile") is not None:
        profile_options = SCENE_PROFILES
    elif schedule_profile(seed, sample_index, difficulty) == "multi_source_union":
        profile_options = _UNION_PROFILE_WEIGHTS[band]
    else:
        profile_options = _STANDARD_PROFILE_WEIGHTS[band]
    profile = ctx.draw_choice("scene_profile", profile_options)
    rng = ctx.draw_rng(f"framed_tile_scene_{band}")
    grid = _construct_scene(SCENE_SPECS[profile], rng)

    analysis = _analyze(grid)
    if analysis["profile"] != profile:
        raise RuntimeError(
            f"constructed {profile!r}, observed {analysis['profile']!r}"
        )
    if solve_python(grid) == grid:
        raise RuntimeError(f"constructed identity profile {profile!r}")
    return grid


def solve_python(grid: Grid) -> Grid:
    """Mirror the canonical separator-band and same-color offset union."""
    height, width = _validate_rectangular_grid(grid)
    zero_rows = {
        row
        for row in range(height)
        if all(grid[row][col] == 0 for col in range(width))
    }
    zero_cols = {
        col
        for col in range(width)
        if all(grid[row][col] == 0 for row in range(height))
    }
    row_bands = _bands(height, zero_rows)
    col_bands = _bands(width, zero_cols)
    tiles = [
        (row_band, col_band, grid[row_band[0]][col_band[0]])
        for row_band in row_bands
        for col_band in col_bands
        if grid[row_band[0]][col_band[0]] != 0
    ]

    output = copy.deepcopy(grid)
    for row_band, col_band, color in tiles:
        row_start, row_end = row_band
        col_start, col_end = col_band
        for dr in range(row_end - row_start + 1):
            for dc in range(col_end - col_start + 1):
                if _has_offset(
                    grid,
                    tiles,
                    color,
                    dr,
                    dc,
                    height,
                    width,
                ):
                    output[row_start + dr][col_start + dc] = color
    return output


def self_check(grid, *, difficulty=None, meta=None):
    """Recognize the complete returned-grid grammar independently."""
    try:
        analysis = _analyze(grid)
        solved = solve_python(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    if solved == grid:
        return ["at least one repeated color must receive a nonempty motif"]
    if analysis["active_repeated"] < 1:
        return ["no active repeated-color source group"]
    return []


def observe_overrides(grid):
    """Recover the exact declared scene profile from a returned grid."""
    try:
        return {"scene_profile": _analyze(grid)["profile"]}
    except (TypeError, ValueError):
        return {}


def canonical_profile_index(grid):
    """Return the linked public-profile index, or ``None``."""
    try:
        profile = _analyze(grid)["profile"]
    except (TypeError, ValueError):
        return None
    return (
        PUBLIC_PROFILES.index(profile)
        if profile in PUBLIC_PROFILES
        else None
    )


def _construct_scene(spec: SceneSpec, rng) -> Grid:
    """Construct a profile without random-placement failure paths."""
    labels = [
        label
        for label, multiplicity in enumerate(spec.multiplicities)
        for _ in range(multiplicity)
    ]
    rng.shuffle(labels)
    colors = rng.sample(COLORS, len(spec.multiplicities))
    positions: dict[int, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        positions[label].append(index)

    repeated_by_multiplicity: dict[int, list[int]] = defaultdict(list)
    unique = []
    for label, indexes in positions.items():
        if len(indexes) == 1:
            unique.append(label)
        else:
            repeated_by_multiplicity[len(indexes)].append(label)
    required_repeated: dict[int, list[tuple[str, object]]] = defaultdict(list)
    for multiplicity, motif_size in spec.active_repeated_sources:
        required_repeated[multiplicity].append(("single", motif_size))
    for multiplicity, union_size, source_sizes in (
        spec.fragmented_repeated_sources
    ):
        required_repeated[multiplicity].append(
            ("fragmented", (union_size, source_sizes))
        )

    source_motifs: dict[int, dict[int, set[tuple[int, int]]]] = {}
    for multiplicity, requirements in required_repeated.items():
        candidates = repeated_by_multiplicity[multiplicity]
        labels_for_sources = rng.sample(candidates, len(requirements))
        shuffled_requirements = list(requirements)
        rng.shuffle(shuffled_requirements)
        for label, (kind, payload) in zip(
            labels_for_sources, shuffled_requirements
        ):
            if kind == "single":
                motif = _make_motif(rng, int(payload))
                source_index = rng.choice(positions[label])
                source_motifs[label] = {source_index: motif}
            else:
                union_size, source_sizes = payload
                fragments = _make_fragmented_motifs(
                    rng,
                    int(union_size),
                    tuple(source_sizes),
                )
                source_indexes = rng.sample(
                    positions[label], len(fragments)
                )
                source_motifs[label] = dict(
                    zip(source_indexes, fragments)
                )

    unique_labels = rng.sample(
        unique, len(spec.active_unique_motif_sizes)
    )
    unique_sizes = list(spec.active_unique_motif_sizes)
    rng.shuffle(unique_sizes)
    for label, motif_size in zip(unique_labels, unique_sizes):
        source_index = positions[label][0]
        source_motifs[label] = {
            source_index: _make_motif(rng, motif_size)
        }

    grid = full_grid(
        STRIDE * spec.rows + 1,
        STRIDE * spec.cols + 1,
        0,
    )
    for index, label in enumerate(labels):
        tile_row, tile_col = divmod(index, spec.cols)
        row_start = 1 + STRIDE * tile_row
        col_start = 1 + STRIDE * tile_col
        color = colors[label]
        _paint_frame(grid, row_start, col_start, color)
        motif = source_motifs.get(label, {}).get(index)
        if motif:
            for dr, dc in motif:
                grid[row_start + dr][col_start + dc] = color
    return grid


def _paint_frame(
    grid: Grid,
    row_start: int,
    col_start: int,
    color: int,
) -> None:
    for offset in range(TILE_SIZE):
        grid[row_start][col_start + offset] = color
        grid[row_start + TILE_SIZE - 1][col_start + offset] = color
        grid[row_start + offset][col_start] = color
        grid[row_start + offset][col_start + TILE_SIZE - 1] = color


def _make_motif(rng, target_size: int) -> set[tuple[int, int]]:
    """Grow a fresh 8-connected 3x3 motif around its center."""
    if not 1 <= target_size <= 5:
        raise ValueError("motif size must be in 1..5")
    cells = {(2, 2)}
    while len(cells) < target_size:
        candidates = {
            (row + dr, col + dc)
            for row, col in cells
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr, dc) != (0, 0)
            and 1 <= row + dr <= 3
            and 1 <= col + dc <= 3
        } - cells
        cells.add(rng.choice(sorted(candidates)))
    return cells


def _make_fragmented_motifs(
    rng,
    union_size: int,
    source_sizes: tuple[int, ...],
) -> list[set[tuple[int, int]]]:
    """Partition a central motif into proper source fragments.

    Fragments share only the center, so their union is identifiable from the
    grid and every fragment remains 8-connected.
    """
    if len(source_sizes) < 2:
        raise ValueError("fragmented motifs need at least two sources")
    if any(size < 2 for size in source_sizes):
        raise ValueError("fragmented source sizes must be at least 2")
    if sum(size - 1 for size in source_sizes) != union_size - 1:
        raise ValueError(
            "fragment sizes must partition the non-center union cells"
        )
    union = _make_motif(rng, union_size)
    extras = sorted(union - {(2, 2)})
    rng.shuffle(extras)
    fragments: list[set[tuple[int, int]]] = []
    offset = 0
    for size in source_sizes:
        count = size - 1
        fragments.append({(2, 2), *extras[offset: offset + count]})
        offset += count
    return fragments


def _analyze(grid: Grid) -> dict:
    """Extract final-grid frame, source, and linked-profile semantics."""
    height, width = _validate_rectangular_grid(grid)
    if any(value < 0 or value > 8 for row in grid for value in row):
        raise ValueError("cells must use canonical colors 0..8")

    zero_rows = {
        row
        for row in range(height)
        if all(grid[row][col] == 0 for col in range(width))
    }
    zero_cols = {
        col
        for col in range(width)
        if all(grid[row][col] == 0 for row in range(height))
    }
    row_bands = _bands(height, zero_rows)
    col_bands = _bands(width, zero_cols)
    if not row_bands or not col_bands:
        raise ValueError("expected nonempty zero-separated tile bands")
    if any(
        end - start + 1 != TILE_SIZE
        for start, end in row_bands + col_bands
    ):
        raise ValueError("every tile band must be exactly 5 cells wide")
    if zero_rows != set(range(0, height, STRIDE)):
        raise ValueError("zero separator rows must be one cell wide")
    if zero_cols != set(range(0, width, STRIDE)):
        raise ValueError("zero separator columns must be one cell wide")
    if (
        height != STRIDE * len(row_bands) + 1
        or width != STRIDE * len(col_bands) + 1
    ):
        raise ValueError("grid dimensions do not match its tile layout")

    tile_colors: list[int] = []
    motifs: list[set[tuple[int, int]]] = []
    for row_start, row_end in row_bands:
        for col_start, col_end in col_bands:
            color = grid[row_start][col_start]
            if color not in COLORS:
                raise ValueError("every tile needs a nonzero frame color")
            motif: set[tuple[int, int]] = set()
            for row in range(row_start, row_end + 1):
                for col in range(col_start, col_end + 1):
                    value = grid[row][col]
                    if value not in (0, color):
                        raise ValueError(
                            "a tile may contain only zero and its frame color"
                        )
                    on_border = (
                        row in (row_start, row_end)
                        or col in (col_start, col_end)
                    )
                    if on_border and value != color:
                        raise ValueError("every tile needs a complete frame")
                    if not on_border and value == color:
                        motif.add(
                            (row - row_start, col - col_start)
                        )
            if motif:
                if not 1 <= len(motif) <= 5:
                    raise ValueError("source motifs must contain 1..5 cells")
                if (2, 2) not in motif:
                    raise ValueError("source motifs must include the center")
                if not _connected8(motif):
                    raise ValueError("source motifs must be 8-connected")
            tile_colors.append(color)
            motifs.append(motif)

    groups: dict[int, list[int]] = defaultdict(list)
    for index, color in enumerate(tile_colors):
        groups[color].append(index)

    multiplicities = tuple(
        sorted(
            (len(indexes) for indexes in groups.values()),
            reverse=True,
        )
    )
    active_repeated_sources = tuple(
        sorted(
            (
                (len(indexes), len(next(
                    motifs[index]
                    for index in indexes
                    if motifs[index]
                )))
                for indexes in groups.values()
                if len(indexes) > 1
                and sum(bool(motifs[index]) for index in indexes) == 1
            ),
            reverse=True,
        )
    )
    fragmented_repeated_sources = tuple(
        sorted(
            (
                (
                    len(indexes),
                    len(set().union(*(
                        motifs[index]
                        for index in indexes
                        if motifs[index]
                    ))),
                    tuple(
                        sorted(
                            (
                                len(motifs[index])
                                for index in indexes
                                if motifs[index]
                            ),
                            reverse=True,
                        )
                    ),
                )
                for indexes in groups.values()
                if len(indexes) > 1
                and sum(bool(motifs[index]) for index in indexes) > 1
            ),
            reverse=True,
        )
    )
    active_unique_motif_sizes = tuple(
        sorted(
            len(motifs[indexes[0]])
            for indexes in groups.values()
            if len(indexes) == 1 and bool(motifs[indexes[0]])
        )
    )
    profile = _PROFILE_BY_KEY.get(
        (
            len(row_bands),
            len(col_bands),
            multiplicities,
            active_repeated_sources,
            fragmented_repeated_sources,
            active_unique_motif_sizes,
        )
    )
    if profile is None:
        raise ValueError(
            "tile layout, color multiplicities, and source roles do not "
            "match a profile"
        )
    active_repeated = (
        len(active_repeated_sources)
        + len(fragmented_repeated_sources)
    )
    if active_repeated < 1:
        raise ValueError("at least one repeated color needs a source motif")

    return {
        "profile": profile,
        "tile_colors": tuple(tile_colors),
        "motif_sizes": tuple(
            sorted(len(motif) for motif in motifs if motif)
        ),
        "active_repeated": active_repeated,
        "active_repeated_multiplicities": tuple(
            sorted(
                (
                    tuple(
                        multiplicity
                        for multiplicity, _ in active_repeated_sources
                    )
                    + tuple(
                        multiplicity
                        for multiplicity, _, _
                        in fragmented_repeated_sources
                    )
                ),
                reverse=True,
            )
        ),
        "active_repeated_sources": active_repeated_sources,
        "fragmented_repeated_sources": fragmented_repeated_sources,
        "active_unique": len(active_unique_motif_sizes),
        "active_unique_motif_sizes": active_unique_motif_sizes,
    }


def _validate_rectangular_grid(grid: Grid) -> tuple[int, int]:
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        raise ValueError("grid must be a nonempty list of rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        not isinstance(value, int) or isinstance(value, bool)
        for row in grid
        for value in row
    ):
        raise ValueError("grid cells must be integers")
    return len(grid), width


def _bands(
    total: int,
    separators: set[int],
) -> list[tuple[int, int]]:
    bands: list[tuple[int, int]] = []
    start = 0
    while start < total:
        if start in separators:
            start += 1
            continue
        end = start
        while end + 1 < total and end + 1 not in separators:
            end += 1
        bands.append((start, end))
        start = end + 1
    return bands


def _has_offset(
    grid: Grid,
    tiles,
    color: int,
    dr: int,
    dc: int,
    height: int,
    width: int,
) -> bool:
    for row_band, col_band, source_color in tiles:
        if source_color != color:
            continue
        row = row_band[0] + dr
        col = col_band[0] + dc
        if (
            0 <= row < height
            and 0 <= col < width
            and grid[row][col] == color
        ):
            return True
    return False


def _connected8(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return True
    seen = {next(iter(cells))}
    frontier = list(seen)
    while frontier:
        row, col = frontier.pop()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                point = (row + dr, col + dc)
                if point in cells and point not in seen:
                    seen.add(point)
                    frontier.append(point)
    return seen == cells


def _semantic_tiles(
    grid: Grid,
) -> list[tuple[int, int, int, set[tuple[int, int]]]]:
    """Return row-major tile starts, colors, and interior motif offsets."""
    height, width = _validate_rectangular_grid(grid)
    zero_rows = {
        row
        for row in range(height)
        if all(grid[row][col] == 0 for col in range(width))
    }
    zero_cols = {
        col
        for col in range(width)
        if all(grid[row][col] == 0 for row in range(height))
    }
    records = []
    for row_start, row_end in _bands(height, zero_rows):
        for col_start, col_end in _bands(width, zero_cols):
            color = grid[row_start][col_start]
            motif = {
                (row - row_start, col - col_start)
                for row in range(row_start + 1, row_end)
                for col in range(col_start + 1, col_end)
                if grid[row][col] == color
            }
            records.append((row_start, col_start, color, motif))
    return records


def _first_source_only(grid: Grid) -> Grid:
    """Plausible wrong rule: copy only the first motif seen per color."""
    try:
        records = _semantic_tiles(grid)
    except (TypeError, ValueError):
        return copy.deepcopy(grid)
    first: dict[int, set[tuple[int, int]]] = {}
    for _, _, color, motif in records:
        if motif and color not in first:
            first[color] = motif
    output = copy.deepcopy(grid)
    for row_start, col_start, color, _ in records:
        for dr, dc in first.get(color, set()):
            output[row_start + dr][col_start + dc] = color
    return output


def _blank_targets_only(grid: Grid) -> Grid:
    """Plausible wrong rule: fill blank peers but never merge sources."""
    try:
        records = _semantic_tiles(grid)
    except (TypeError, ValueError):
        return copy.deepcopy(grid)
    unions: dict[int, set[tuple[int, int]]] = defaultdict(set)
    for _, _, color, motif in records:
        unions[color].update(motif)
    output = copy.deepcopy(grid)
    for row_start, col_start, color, motif in records:
        if motif:
            continue
        for dr, dc in unions[color]:
            output[row_start + dr][col_start + dc] = color
    return output


def _multi_source_union_required(grid: Grid) -> bool:
    try:
        return bool(_analyze(grid)["fragmented_repeated_sources"])
    except (TypeError, ValueError):
        return False


def strict_canonical_like(grid: Grid) -> list[str]:
    """Task-domain validator used by the semantic curriculum gate."""
    return self_check(grid)


SEMANTIC_RIVALS = {
    "first_source_only": _first_source_only,
    "blank_targets_only": _blank_targets_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "multi_source_union_required": _multi_source_union_required,
}
WITNESS_RIVALS = {
    "multi_source_union_required": [
        "first_source_only",
        "blank_targets_only",
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demos leave a declared answer-changing rival."""
    query_grid = query.get("input") if isinstance(query, dict) else query
    try:
        expected = solve_python(query_grid)
    except (TypeError, ValueError) as exc:
        return [f"query is outside the framed-tile domain: {exc}"]

    reasons = []
    for index, pair in enumerate(demos):
        try:
            answer = solve_python(pair["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demonstration {index} is invalid: {exc}")
            continue
        if answer != pair.get("output"):
            reasons.append(
                f"demonstration {index} disagrees with union semantics"
            )

    for name, rival in LESSON_COMPETITORS.items():
        if all(
            rival(pair["input"]) == pair.get("output")
            for pair in demos
        ) and rival(query_grid) != expected:
            reasons.append(
                f"unresolved answer-changing competitor: {name}"
            )
    return reasons

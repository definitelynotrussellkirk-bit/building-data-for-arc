"""Generate dense noisy fields containing yellow-centered colored pluses."""

from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "b57f299dcdb3"
TASK_ID = "b57f299dcdb3"
VERSION = "3.0.0"
RULE_HASH = "793f1a180fe5"
SUMMARY = (
    "Find every yellow-centered plus whose four petals share one "
    "nonzero, non-background color; output the most frequent petal "
    "color as a 1x1 grid."
)
EXPECTED_OUTPUT_CODOMAIN = 8

PUBLIC_PROFILES = (
    "public_dense_six",
    "public_dense_four",
    "public_dense_three",
    "public_dense_five",
)
EXTRAPOLATION_PROFILES = ("synthetic_texture",)
SCENE_PROFILES = PUBLIC_PROFILES + EXTRAPOLATION_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng across complete linked and synthetic profiles",
        "valid": "|".join(SCENE_PROFILES),
    },
}

INVARIANTS = [
    "a unique nonzero non-yellow modal color is the dense field background",
    "20-35% of cells form a fragmented zero texture over that field",
    "every yellow cell is an interior plus center with four equal petals",
    "there are 3-6 pluses: one petal color occurs twice and every other once",
    "the returned 1x1 answer is the unique twice-occurring petal color",
]

_TRANSFORMS = (
    "identity",
    "horizontal_flip",
    "vertical_flip",
    "rotate_180",
)
_ROLE_VALUES = (2, 3, 5, 6, 7, 8, 9)
_LEGAL_PALETTE = (1, 2, 3, 5, 6, 7, 8, 9)
_WEIGHTED_PROFILES = {
    band: PUBLIC_PROFILES + (("synthetic_texture",) * 12)
    for band in ("easy", "medium", "hard")
}


def _decode(*encoded):
    width = len(encoded[0])
    if any(len(row) != width for row in encoded):
        raise RuntimeError("public profile encoding must be rectangular")
    return [[int(value) for value in row] for row in encoded]


_PUBLIC_ROLE_GRIDS = {
    "public_dense_six": _decode(
        "0201101101010011010300",
        "0101100101120051010110",
        "0001110101010011060110",
        "0117111211111111111011",
        "1351102421111011116017",
        "1111101211111101164611",
        "1001110101016011016100",
        "1111101111111011111110",
        "1601210101010011110160",
        "1112421112113111111111",
        "0101210116011101000120",
        "1111111111111511111111",
        "0001710100005451010100",
        "0001110111100511011105",
        "1101111111111111111111",
        "1011113111111111117111",
        "0001134301010011074700",
        "1110103111110111007111",
        "0001110101010115010100",
        "1610111110111211111111",
        "0001110101010011010170",
        "0001110300160011010100",
    ),
    "public_dense_four": _decode(
        "011121001301021031011001",
        "351011311131111111011002",
        "111111111111111111121101",
        "111132111111115111242112",
        "011152001001011001121111",
        "121545011111111113111111",
        "011151001101011031313001",
        "031301003102011001101115",
        "111111111011111111211111",
        "111113111111111211111111",
        "011101001101010001011001",
        "011111111111111111111131",
        "011501001001011001511001",
        "111111211111111111001001",
        "121111111311011311121111",
        "011131001101051001111115",
        "011101001101011001011001",
        "110111111310111111111111",
        "111311111111311111001001",
        "013431001101011001111111",
        "110311211112111111111111",
        "001111011201001001011051",
        "001111011102001101011001",
        "120111121111311511111111",
        "121111111111125451211211",
        "001101212131002511011001",
    ),
    "public_dense_three": _decode(
        "0011110101010011010110",
        "0010110011010011010110",
        "1111111101111112111101",
        "1011110111011024211111",
        "0111111111111012111111",
        "1111311111111111111111",
        "0013430011010011010100",
        "1101310011110111111110",
        "1111111111111111111111",
        "1111110001111101111111",
        "0011110111010011010110",
        "1111111111111111111111",
        "0011110111310011010010",
        "0001110113430011010110",
        "1111111110311111011111",
        "0001111111111111111111",
        "0010110111010011010110",
        "1111111111111111111111",
        "0011110111010011010010",
        "1011111011111111011111",
    ),
    "public_dense_five": _decode(
        "0011010102010011010010",
        "0011113111010011020110",
        "1151111111111111111101",
        "1545111011010311161151",
        "1151112111211150111111",
        "1111101100111101111111",
        "0011110111013011010110",
        "1110111311110111101111",
        "2110113431111111111111",
        "1110111313111111211003",
        "0006110111010012420110",
        "1111111011105111211016",
        "0011110111010011010100",
        "0015113102010011010110",
        "1111111111111111101111",
        "1111111111111001011151",
        "0231110110010311050010",
        "1111110310111111111111",
        "0011110115010011010110",
        "1111011111120111111121",
        "1111611111011113111111",
        "0006460110010001015100",
        "0011610111010011010110",
        "3111101101115101111001",
        "1111112111154511011111",
        "0011110016015011012110",
        "1100111111111111111011",
    ),
}

_PUBLIC_ORIGINAL_PALETTES = {
    "public_dense_six": (2, 3, 8, 6, 1, 7),
    "public_dense_four": (8, 3, 1, 2),
    "public_dense_three": (5, 3, 8),
    "public_dense_five": (9, 6, 3, 2, 1),
}


def _transform(grid, name):
    if name == "identity":
        return [row[:] for row in grid]
    if name == "horizontal_flip":
        return [list(reversed(row)) for row in grid]
    if name == "vertical_flip":
        return [row[:] for row in reversed(grid)]
    if name == "rotate_180":
        return [list(reversed(row)) for row in reversed(grid)]
    raise KeyError(name)


def _mode(grid):
    counts = Counter(value for row in grid for value in row)
    return max(counts, key=counts.get)


def _role_signature(grid):
    background = _mode(grid)
    masks = {}
    for color in {
        value
        for row in grid
        for value in row
        if value not in (0, 4, background)
    }:
        masks[color] = tuple(
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        )
    ordered = sorted(masks, key=masks.get)
    roles = {0: 0, 4: 4, background: 1}
    roles.update({
        color: _ROLE_VALUES[index]
        for index, color in enumerate(ordered)
    })
    return tuple(
        tuple(roles[value] for value in row)
        for row in grid
    )


_PUBLIC_LOOKUP = {
    _role_signature(grid): profile
    for profile, grid in _PUBLIC_ROLE_GRIDS.items()
}


def _canonical_answer_profile(grid):
    for transform in _TRANSFORMS:
        profile = _PUBLIC_LOOKUP.get(
            _role_signature(_transform(grid, transform))
        )
        if profile is not None:
            return profile
    return None


def _plus_centers(grid, background):
    centers = []
    height = len(grid)
    width = len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 4:
                continue
            petals = (
                grid[row - 1][col],
                grid[row + 1][col],
                grid[row][col - 1],
                grid[row][col + 1],
            )
            if (
                len(set(petals)) == 1
                and petals[0] not in (0, 4, background)
            ):
                centers.append((row, col, petals[0]))
    return centers


def solve_python(grid):
    """Input-pure mirror of the authoritative Racket plus census."""
    background = _mode(grid)
    petals = [
        color for _, _, color in _plus_centers(grid, background)
    ]
    if not petals:
        return [[0]]
    counts = Counter(petals)
    winner = max(counts, key=counts.get)
    return [[winner]]


def _component_sizes(grid, color):
    height = len(grid)
    width = len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    sizes = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        size = 1
        while stack:
            row, col = stack.pop()
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + drow, col + dcol)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
                    size += 1
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _analyze(grid):
    reasons = []
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        return {"strict": False, "reasons": ["empty_or_non_grid"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"strict": False, "reasons": ["ragged"]}
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"strict": False, "reasons": ["invalid_arc_value"]}

    height = len(grid)
    if not 20 <= height <= 27 or not 22 <= width <= 24:
        reasons.append("dimension_range")
    values = [value for row in grid for value in row]
    counts = Counter(values)
    max_count = max(counts.values())
    modes = [
        color for color, count in counts.items() if count == max_count
    ]
    background = modes[0]
    if len(modes) != 1:
        reasons.append("nonunique_mode")
    if background in (0, 4):
        reasons.append("invalid_background")

    area = height * width
    zero_fraction = counts[0] / area
    background_fraction = counts[background] / area
    if not 0.18 <= zero_fraction <= 0.35:
        reasons.append("zero_fraction")
    if not 0.50 <= background_fraction <= 0.80:
        reasons.append("background_fraction")
    if not 5 <= len(counts) <= 8:
        reasons.append("color_count")

    centers = _plus_centers(grid, background)
    if counts[4] != len(centers):
        reasons.append("invalid_yellow_center")
    if not 3 <= len(centers) <= 6:
        reasons.append("plus_count")
    petal_counts = Counter(color for _, _, color in centers)
    winners = [
        color for color, count in petal_counts.items() if count == 2
    ]
    if len(winners) != 1:
        reasons.append("winner_multiplicity")
    if any(count not in (1, 2) for count in petal_counts.values()):
        reasons.append("petal_frequency_shape")
    if sum(count == 2 for count in petal_counts.values()) != 1:
        reasons.append("strict_winner")
    if any(color in (0, 4, background) for color in petal_counts):
        reasons.append("invalid_petal_role")

    zero_components = _component_sizes(grid, 0) if 0 in counts else []
    background_components = (
        _component_sizes(grid, background) if background in counts else []
    )
    if len(zero_components) < 20:
        reasons.append("insufficient_zero_texture")
    largest_background_fraction = (
        background_components[0] / counts[background]
        if background_components and counts[background]
        else 0.0
    )
    if largest_background_fraction < 0.75:
        reasons.append("fragmented_background")

    answer_profile = _canonical_answer_profile(grid)
    scene_profile = answer_profile or "synthetic_texture"
    return {
        "strict": not reasons,
        "reasons": sorted(set(reasons)),
        "height": height,
        "width": width,
        "background": background,
        "background_fraction": background_fraction,
        "zero_fraction": zero_fraction,
        "color_count": len(counts),
        "plus_count": len(centers),
        "petal_color_count": len(petal_counts),
        "winner": winners[0] if len(winners) == 1 else None,
        "zero_component_count": len(zero_components),
        "largest_background_fraction": largest_background_fraction,
        "canonical_answer_profile": answer_profile,
        "scene_profile": scene_profile,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the complete dense-field lesson from the returned grid."""
    return _analyze(grid)["reasons"]


def observe_overrides(grid):
    """Recover the declared semantic control from the returned grid."""
    analysis = _analyze(grid)
    if not analysis["strict"]:
        raise ValueError(f"cannot observe invalid grid: {analysis['reasons']}")
    return {"scene_profile": analysis["scene_profile"]}


def _recolor_public(profile, palette):
    roles = sorted(
        {
            value
            for row in _PUBLIC_ROLE_GRIDS[profile]
            for value in row
            if value not in (0, 4)
        }
    )
    mapping = {0: 0, 4: 4}
    mapping.update(dict(zip(roles, palette)))
    return [
        [mapping[value] for value in row]
        for row in _PUBLIC_ROLE_GRIDS[profile]
    ]


def _public_grid(profile, palette_rng, transform_rng):
    role_count = len(_PUBLIC_ORIGINAL_PALETTES[profile])
    palette = tuple(palette_rng.sample(_LEGAL_PALETTE, role_count))
    transform = transform_rng.choice(_TRANSFORMS)
    if (
        transform == "identity"
        and palette == _PUBLIC_ORIGINAL_PALETTES[profile]
    ):
        transform = "horizontal_flip"
    return _transform(_recolor_public(profile, palette), transform)


def _band_parameters(band, rng):
    if band == "easy":
        return rng.randint(20, 22), 22, rng.randint(3, 4), 0.04, (0, 3)
    if band == "hard":
        return (
            rng.randint(25, 27),
            rng.randint(22, 24),
            rng.randint(5, 6),
            0.11,
            (5, 10),
        )
    return (
        rng.randint(22, 25),
        rng.randint(22, 24),
        rng.randint(4, 5),
        0.075,
        (2, 7),
    )


def _choose_centers(height, width, count, rng):
    candidates = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    rng.shuffle(candidates)
    centers = []
    for candidate in candidates:
        if all(
            max(
                abs(candidate[0] - row),
                abs(candidate[1] - col),
            )
            >= 4
            for row, col in centers
        ):
            centers.append(candidate)
            if len(centers) == count:
                return centers
    raise RuntimeError("could not place separated plus centers")


def _synthetic_candidate(band, rng):
    height, width, plus_count, jitter, noise_range = _band_parameters(
        band, rng
    )
    colors = rng.sample(_LEGAL_PALETTE, plus_count)
    background = colors[0]
    winner = colors[1]
    losers = colors[2:]
    petal_colors = [winner, winner, *losers]
    rng.shuffle(petal_colors)

    zero_probability = rng.uniform(0.19, 0.27)
    tile = [
        [rng.random() < zero_probability for _ in range(6)]
        for _ in range(6)
    ]
    grid = [
        [
            0
            if tile[row % 6][col % 6] ^ (rng.random() < jitter)
            else background
            for col in range(width)
        ]
        for row in range(height)
    ]

    noise_colors = list(dict.fromkeys(petal_colors))
    available = [
        (row, col)
        for row in range(height)
        for col in range(width)
    ]
    rng.shuffle(available)
    noise_lo, noise_hi = noise_range
    cursor = 0
    for color in noise_colors:
        for _ in range(rng.randint(noise_lo, noise_hi)):
            row, col = available[cursor]
            cursor += 1
            grid[row][col] = color

    centers = _choose_centers(height, width, plus_count, rng)
    for (row, col), color in zip(centers, petal_colors):
        grid[row][col] = 4
        grid[row - 1][col] = color
        grid[row + 1][col] = color
        grid[row][col - 1] = color
        grid[row][col + 1] = color
    return grid


def _synthetic_grid(band, rng):
    for _ in range(256):
        grid = _synthetic_candidate(band, rng)
        analysis = _analyze(grid)
        if (
            analysis["strict"]
            and analysis["scene_profile"] == "synthetic_texture"
        ):
            return grid
    raise RuntimeError("failed to construct a strict synthetic texture")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in _WEIGHTED_PROFILES else "medium"
    profile = ctx.draw_choice(
        "scene_profile",
        _WEIGHTED_PROFILES[band],
    )
    if profile in PUBLIC_PROFILES:
        grid = _public_grid(
            profile,
            ctx.draw_rng("public_palette"),
            ctx.draw_rng("public_transform"),
        )
    elif profile == "synthetic_texture":
        grid = _synthetic_grid(band, ctx.draw_rng("synthetic_scene"))
    else:
        raise RuntimeError(f"unhandled scene profile {profile!r}")

    analysis = _analyze(grid)
    if not analysis["strict"] or analysis["scene_profile"] != profile:
        raise RuntimeError(
            f"internal generation contract failed: {analysis['reasons']}"
        )
    return grid

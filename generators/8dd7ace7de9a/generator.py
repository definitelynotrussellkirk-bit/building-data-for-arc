"""Canonical-scale generator for periodic-tile recovery with color-6 noise.

The selected rule searches row periods and then column periods in ascending
order.  It ignores magenta (6), requires every tile residue to retain at least
one non-noise representative, and reconstructs the first fitting tile.  This
sampler therefore constructs a certified fundamental period, preserves a clean
representative for every residue class, and places an exact count of noise
without replacement.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "8dd7ace7de9a"
TASK_ID = GENERATOR_ID
RULE_HASH = "0f05e4e27969"
VERSION = "2.1.0"
SUMMARY = (
    "Recover the smallest periodic tile consistent with all non-magenta cells, "
    "then replace magenta (6) noise by repeating that tile across the grid."
)

INVARIANTS = [
    "grid size is 12..16 by 12..19, covering every canonical size profile",
    "the clean tile has an exact fundamental period 2..4 in each dimension",
    "the clean tile uses 2..4 colors and never uses magenta (6)",
    "1..64 distinct cells are replaced by magenta noise",
    "every tile residue retains a clean representative, so recovery is total",
    "every three consecutive default draws include a noisy top-left tile anchor",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-scale schedule", "valid": "12..16"},
    "grid_w": {"type": "int", "default": "canonical-scale schedule", "valid": "12..19"},
    "period_r": {"type": "int", "default": "three-profile teaching schedule", "valid": "2..4"},
    "period_c": {"type": "int", "default": "three-profile teaching schedule", "valid": "2..4"},
    "palette_size": {"type": "int", "default": "2 on canonical anchors; 2..4 otherwise", "valid": "2..4"},
    "noise_count": {"type": "int", "default": "difficulty-weighted exact count", "valid": "1..64"},
    "clean_anchor": {
        "type": "bool",
        "default": "three-profile teaching schedule",
        "valid": "true|false",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Three consecutive sample indexes contain all profiles. Profile 2 is an
# explicit counterexample to both canonical-compatible shortcuts below.
SCHEDULE_PROFILES = (0, 1, 2)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_INT_DOMAINS = {
    "grid_h": (12, 16),
    "grid_w": (12, 19),
    "period_r": (2, 4),
    "period_c": (2, 4),
    "palette_size": (2, 4),
    "noise_count": (1, 64),
}
_DIFFICULTIES = (None, "easy", "medium", "hard")
_CANONICAL_SCALE_PROFILES = {
    0: (12, 12),
    1: (15, 19),
    2: (16, 16),
}
_PERIOD_PROFILES = {
    0: (3, 3),
    1: (2, 2),
    2: (4, 3),
}
_NOISE_OPTIONS = {
    None: tuple(range(30, 53)),
    "easy": tuple(range(18, 35)),
    "medium": tuple(range(30, 53)),
    "hard": tuple(range(45, 65)),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Semantic lesson profile; every three consecutive draws cover all three."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def anchor_schedule(seed: int, sample_index: int, difficulty=None) -> bool:
    """Keep two clean anchors and one noisy anchor in every three-draw window."""
    return schedule_profile(seed, sample_index, difficulty) != 2


def _scale_profile(sample_index: int) -> int:
    """Independent four-step scale schedule; profile 3 breaks axis lockstep."""
    return int(sample_index) % 4


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name == "clean_anchor":
            if type(value) is not bool:
                raise TypeError(
                    f"clean_anchor must be bool, not {type(value).__name__}"
                )
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be int, not {type(value).__name__}")
        lo, hi = _INT_DOMAINS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_int_axis(ctx, name: str, lo: int, hi: int, defaults: Sequence[int]) -> int:
    """Draw an exact integer axis while retaining a deterministic curriculum."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    options = tuple(int(value) for value in defaults)
    if not options or any(not lo <= value <= hi for value in options):
        raise RuntimeError(f"invalid default options for {name}: {options!r}")
    return int(ctx.draw_choice(name, options))


def _draw_bool_axis(ctx, name: str, default: bool) -> bool:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return bool(ctx.draw_choice(name, (False, True)))
    return bool(ctx.draw_choice(name, (bool(default),)))


def _build_tile(ctx, pr: int, pc: int, palette_size: int) -> list[list[int]]:
    palette = ctx.draw_distinct_colors("palette", n=palette_size, exclude={6})
    tile = [[palette[0] for _ in range(pc)] for _ in range(pr)]

    # A unique color at (0,0), with every other cell a different color, is a
    # constructive period certificate: for every q < pr, (0,0) conflicts with
    # (q,0), and for every q < pc it conflicts with (0,q). Those first-row and
    # first-column certificate cells are kept clean by _noise_positions().
    tile[0][0] = palette[1]
    if palette_size > 2:
        candidates = [
            (r, c)
            for r in range(pr)
            for c in range(pc)
            if (r, c) != (0, 0)
        ]
        positions = ctx.draw_rng("extra_palette_positions").sample(
            candidates, palette_size - 2
        )
        for color, (r, c) in zip(palette[2:], positions, strict=True):
            tile[r][c] = color
    return tile


def _periodic_grid(h: int, w: int, tile: list[list[int]]) -> list[list[int]]:
    pr, pc = len(tile), len(tile[0])
    return [[tile[r % pr][c % pc] for c in range(w)] for r in range(h)]


def _residue_positions(h: int, w: int, pr: int, pc: int, tr: int, tc: int):
    return [
        (r, c)
        for r in range(tr, h, pr)
        for c in range(tc, w, pc)
    ]


def _noise_positions(
    ctx,
    *,
    h: int,
    w: int,
    pr: int,
    pc: int,
    noise_count: int,
    clean_anchor: bool,
) -> list[tuple[int, int]]:
    """Choose exact distinct noise cells while preserving recovery witnesses."""
    protected: set[tuple[int, int]] = set()
    for tr in range(pr):
        for tc in range(pc):
            if clean_anchor or tr == 0 or tc == 0:
                # The first row/column are the fundamental-period certificate.
                protected.add((tr, tc))
            else:
                # Interior anchor cells may be noise, but retain another clean
                # representative of their residue outside the first tile.
                choices = [
                    point
                    for point in _residue_positions(h, w, pr, pc, tr, tc)
                    if not (point[0] < pr and point[1] < pc)
                ]
                if not choices:
                    raise RuntimeError("no off-anchor representative for tile residue")
                protected.add(choices[0])

    forced: list[tuple[int, int]] = []
    if not clean_anchor:
        # Interior by construction (periods are >=2), so no certificate is
        # erased. This makes clean_anchor=False observable even at noise_count=1.
        forced = [(pr - 1, pc - 1)]
        if forced[0] in protected:
            raise RuntimeError("forced anchor noise collided with a protected cell")

    candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in protected and (r, c) not in forced
    ]
    remaining = noise_count - len(forced)
    if remaining < 0 or remaining > len(candidates):
        raise ValueError(
            f"noise_count={noise_count} cannot preserve all {pr * pc} tile residues"
        )
    return forced + ctx.draw_rng("noise_positions").sample(candidates, remaining)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _DIFFICULTIES:
        raise ValueError(
            f"unsupported difficulty {difficulty!r}; expected easy, medium, hard, or None"
        )
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    semantic_profile = schedule_profile(seed, sample_index, difficulty)
    scale_profile = _scale_profile(sample_index)
    if scale_profile in _CANONICAL_SCALE_PROFILES:
        default_h, default_w = _CANONICAL_SCALE_PROFILES[scale_profile]
        h_options = (default_h,)
        w_options = (default_w,)
        palette_options = (2,)
    else:
        # Reuse height 12 with several widths so grid_h/grid_w are not aliases;
        # this broad branch stays inside the canonical envelope.
        h_options = (12,)
        w_options = (13, 14, 15, 17, 18)
        palette_options = (2, 3, 4)

    h = _draw_int_axis(ctx, "grid_h", 12, 16, h_options)
    w = _draw_int_axis(ctx, "grid_w", 12, 19, w_options)
    default_pr, default_pc = _PERIOD_PROFILES[semantic_profile]
    pr = _draw_int_axis(ctx, "period_r", 2, 4, (default_pr,))
    pc = _draw_int_axis(ctx, "period_c", 2, 4, (default_pc,))
    palette_size = _draw_int_axis(ctx, "palette_size", 2, 4, palette_options)
    noise_count = _draw_int_axis(
        ctx, "noise_count", 1, 64, _NOISE_OPTIONS[difficulty]
    )
    clean_anchor = _draw_bool_axis(
        ctx,
        "clean_anchor",
        anchor_schedule(seed, sample_index, difficulty),
    )

    tile = _build_tile(ctx, pr, pc, palette_size)
    grid = _periodic_grid(h, w, tile)
    for r, c in _noise_positions(
        ctx,
        h=h,
        w=w,
        pr=pr,
        pc=pc,
        noise_count=noise_count,
        clean_anchor=clean_anchor,
    ):
        grid[r][c] = 6

    requested = {
        "grid_h": h,
        "grid_w": w,
        "period_r": pr,
        "period_c": pc,
        "palette_size": palette_size,
        "noise_count": noise_count,
        "clean_anchor": clean_anchor,
    }
    observed = observe_overrides(grid)
    if observed != requested:
        raise RuntimeError(
            f"constructive generator drifted: requested {requested}, observed {observed}"
        )
    return grid


def _grid_shape(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty sequence")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty sequences")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    return len(grid), width


def _recover_details(
    grid,
    *,
    noise: int = 6,
    square_only: bool = False,
    max_period: int | None = None,
):
    """Return (reconstructed_grid, pr, pc), or None when no tile is found."""
    h, w = _grid_shape(grid)
    max_pr = min(h // 2, max_period if max_period is not None else h // 2)
    max_pc = min(w // 2, max_period if max_period is not None else w // 2)
    for pr in range(1, max_pr + 1):
        pc_values: Iterable[int]
        if square_only:
            pc_values = (pr,) if pr <= max_pc else ()
        else:
            pc_values = range(1, max_pc + 1)
        for pc in pc_values:
            tile: dict[tuple[int, int], int] = {}
            consistent = True
            for r, row in enumerate(grid):
                for c, value in enumerate(row):
                    if value == noise:
                        continue
                    key = (r % pr, c % pc)
                    if key not in tile:
                        tile[key] = value
                    elif tile[key] != value:
                        consistent = False
                        break
                if not consistent:
                    break
            if not consistent or len(tile) != pr * pc:
                continue
            output = [
                [tile[(r % pr, c % pc)] for c in range(w)]
                for r in range(h)
            ]
            return output, pr, pc
    return None


def _recover(grid, noise=6):
    """Compatibility helper: recovered grid or None."""
    details = _recover_details(grid, noise=noise)
    return None if details is None else details[0]


def _zero_grid_like(grid) -> list[list[int]]:
    h, w = _grid_shape(grid)
    return [[0 for _ in range(w)] for _ in range(h)]


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the selected Racket rule for focused tests."""
    details = _recover_details(grid)
    return _zero_grid_like(grid) if details is None else details[0]


def observe_overrides(grid) -> dict[str, int | bool]:
    """Recover every advertised exact axis from returned pixels."""
    details = _recover_details(grid)
    if details is None:
        raise ValueError("grid has no recoverable periodic tile")
    output, pr, pc = details
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "period_r": pr,
        "period_c": pc,
        "palette_size": len({value for row in output for value in row}),
        "noise_count": sum(value == 6 for row in grid for value in row),
        "clean_anchor": all(
            grid[r][c] != 6 for r in range(pr) for c in range(pc)
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    try:
        h, w = _grid_shape(grid)
    except ValueError as exc:
        return [str(exc)]

    errors: list[str] = []
    if not 12 <= h <= 16:
        errors.append(f"grid height {h} outside 12..16")
    if not 12 <= w <= 19:
        errors.append(f"grid width {w} outside 12..19")
    noise_count = sum(value == 6 for row in grid for value in row)
    if not 1 <= noise_count <= 64:
        errors.append(f"noise_count={noise_count} outside 1..64")

    details = _recover_details(grid)
    if details is None:
        errors.append("no recoverable periodic tile")
        return errors
    output, pr, pc = details
    if not 2 <= pr <= 4:
        errors.append(f"recovered row period {pr} outside 2..4")
    if not 2 <= pc <= 4:
        errors.append(f"recovered column period {pc} outside 2..4")
    palette = {value for row in output for value in row}
    if 6 in palette:
        errors.append("recovered tile illegally contains noise color 6")
    if not 2 <= len(palette) <= 4:
        errors.append(f"recovered palette size {len(palette)} outside 2..4")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 6 and value != output[r][c]:
                errors.append("non-noise cell disagrees with recovered tile")
                return errors
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _constrained_rule(grid, *, square_only=False, max_period=None):
    details = _recover_details(
        grid, square_only=square_only, max_period=max_period
    )
    return _zero_grid_like(grid) if details is None else details[0]


def _square_period_only(grid):
    """Rival: incorrectly assumes the row and column periods are equal."""
    return _constrained_rule(grid, square_only=True)


def _periods_at_most_three(grid):
    """Rival: incorrectly searches only periods 1..3 in each dimension."""
    return _constrained_rule(grid, max_period=3)


def _literal_top_left_tile(grid):
    """Rival: infer the periods, but copy values only from the first tile."""
    details = _recover_details(grid)
    if details is None:
        return _zero_grid_like(grid)
    _, pr, pc = details
    h, w = _grid_shape(grid)
    tile = [row[:pc] for row in grid[:pr]]
    return [[tile[r % pr][c % pc] for c in range(w)] for r in range(h)]


def _requires_non_square_search(grid) -> bool:
    details = _recover_details(grid)
    return bool(
        details is not None
        and details[1] != details[2]
        and _square_period_only(grid) != details[0]
    )


def _requires_period_four(grid) -> bool:
    details = _recover_details(grid)
    return bool(
        details is not None
        and 4 in details[1:]
        and _periods_at_most_three(grid) != details[0]
    )


def _requires_anchor_recovery(grid) -> bool:
    details = _recover_details(grid)
    return bool(
        details is not None
        and _literal_top_left_tile(grid) != details[0]
    )


SEMANTIC_WITNESSES = {
    "non_square_period_required": _requires_non_square_search,
    "period_four_required": _requires_period_four,
    "anchor_recovery_required": _requires_anchor_recovery,
}
SEMANTIC_RIVALS = {
    "square_period_only": _square_period_only,
    "periods_at_most_three": _periods_at_most_three,
    "literal_top_left_tile": _literal_top_left_tile,
}
WITNESS_RIVALS = {
    "non_square_period_required": ["square_period_only"],
    "period_four_required": ["periods_at_most_three"],
    "anchor_recovery_required": ["literal_top_left_tile"],
}
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in ("square_period_only", "periods_at_most_three")
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demos to refute every declared canonical-compatible rival."""
    del query
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(demo["input"]) == demo["output"]
                for demo in demos
            )
        except Exception as exc:  # counted as an identification failure, not hidden
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"demos do not refute competitor {name!r}")
    return reasons

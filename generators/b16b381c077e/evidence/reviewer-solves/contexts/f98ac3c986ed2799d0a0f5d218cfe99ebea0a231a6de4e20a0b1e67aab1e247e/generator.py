"""Generator for arc_puzzle_bank_seventeenth21:H113.

Each input contains three square panels A, B, and C separated by two solid
non-background columns.  B is exactly one non-identity dihedral transform of A;
the canonical rule infers that transform and applies it to C.

The generator deliberately makes A asymmetric, makes the transform visible on
C, keeps the answer out of all three input panels, uses a separator color that
is absent from the panels, and schedules all seven non-identity D8 transforms
across every seven consecutive sample indices.  A three-mode palette schedule
covers the canonical one-panel-color object grammar as well as lawful
second-color distractor variants without fragmenting the panels.  These
constraints prevent ambiguous cues, hidden/no-op transformations,
fixed-transform shortcuts, and separator/background conflation while retaining
the canonical 3x3 and 4x4 cases and lawful 5x5/6x6 extensions.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b16b381c077e"
TASK_ID = "b16b381c077e"
VERSION = "4.0.0"
RULE_HASH = "c828867c1661"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "Three square panels A, B, C are separated by two solid non-background "
    "columns. B is one uniquely identifiable non-identity D8 transform of A; "
    "apply that same transform to C. Generated C panels make the transform "
    "visible and never contain the answer already."
)

INVARIANTS = [
    "background is 0 and the two divider columns share one nonzero color absent from all panels",
    "rows equal panel side n in 3..6 and columns equal 3*n+2",
    "exactly one D8 transform maps panel A to panel B, and it is not identity",
    "panel C is nonempty and nonsolid; applying the inferred transform changes C",
    "the transformed C answer is not already present as A, B, or C",
    "ordinary draws cover one- and two-panel-color scenes and all seven non-identity transforms on a seven-sample schedule",
]

_TRANSFORM_KINDS = (
    "rot90",
    "rot180",
    "rot270",
    "flip_h",
    "flip_v",
    "transpose",
    "anti_transpose",
)
_ALL_KINDS = ("id",) + _TRANSFORM_KINDS

AXES = {
    "panel": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "3..6",
        "doc": "Square panel side; exact overrides remain valid in every difficulty band.",
    },
    "kind": {
        "type": "str",
        "default": "seven-sample non-identity D8 schedule",
        "valid": "|".join(_TRANSFORM_KINDS),
        "doc": "Unique transform from A to B; identity is intentionally excluded.",
    },
    "divider_color": {
        "type": "color",
        "default": "keyed nonzero color",
        "valid": "1..9",
        "doc": "Solid separator color, always absent from A/B/C.",
    },
}


def _rot90(panel):
    n = len(panel)
    return [[panel[n - 1 - c][r] for c in range(n)] for r in range(n)]


def _rot180(panel):
    n = len(panel)
    return [
        [panel[n - 1 - r][n - 1 - c] for c in range(n)]
        for r in range(n)
    ]


def _rot270(panel):
    n = len(panel)
    return [[panel[c][n - 1 - r] for c in range(n)] for r in range(n)]


def _flip_h(panel):
    return [list(reversed(row)) for row in panel]


def _flip_v(panel):
    return [list(row) for row in reversed(panel)]


def _transpose(panel):
    n = len(panel)
    return [[panel[c][r] for c in range(n)] for r in range(n)]


def _anti_transpose(panel):
    n = len(panel)
    return [
        [panel[n - 1 - c][n - 1 - r] for c in range(n)]
        for r in range(n)
    ]


def _copy_panel(panel):
    return [list(row) for row in panel]


def _apply(panel, kind):
    transforms = {
        "id": _copy_panel,
        "rot90": _rot90,
        "rot180": _rot180,
        "rot270": _rot270,
        "flip_h": _flip_h,
        "flip_v": _flip_v,
        "transpose": _transpose,
        "anti_transpose": _anti_transpose,
    }
    try:
        transform = transforms[kind]
    except KeyError as exc:
        raise ValueError(f"unknown transform kind: {kind!r}") from exc
    return transform(panel)


def _matching_kinds(panel_a, panel_b):
    return [kind for kind in _ALL_KINDS if _apply(panel_a, kind) == panel_b]


def _has_trivial_stabilizer(panel):
    return _matching_kinds(panel, panel) == ["id"]


def _grow_connected_region(rng, n, available, size):
    """Grow one 4-connected region inside ``available`` or return None."""
    if size < 1 or len(available) < size:
        return None
    start = rng.choice(sorted(available))
    region = {start}
    frontier = set()

    def add_neighbors(cell):
        row, col = cell
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (row + dr, col + dc)
            if (
                0 <= nxt[0] < n
                and 0 <= nxt[1] < n
                and nxt in available
                and nxt not in region
            ):
                frontier.add(nxt)

    add_neighbors(start)
    while len(region) < size:
        if not frontier:
            return None
        cell = rng.choice(sorted(frontier))
        frontier.remove(cell)
        region.add(cell)
        add_neighbors(cell)
    return region


def _random_asymmetric_panel(rng, n, palette, *, density_bounds):
    """Return one or two connected color regions plus background, without D8 symmetry.

    Canonical inputs contain a handful of coherent objects rather than dozens of
    isolated texture pixels.  Connected per-color regions preserve that object
    grammar while random growth still provides broad asymmetric shapes.
    """
    if len(palette) not in (1, 2):
        raise ValueError("panel palette must contain one or two colors")
    lo, hi = density_bounds
    cells = {(row, col) for row in range(n) for col in range(n)}
    for _ in range(512):
        density = rng.uniform(lo, hi)
        min_total = 2 if len(palette) == 1 else 4
        total = max(min_total, min(n * n - 2, round(n * n * density)))
        background_size = n * n - total

        if len(palette) == 1:
            # Keep zero strictly modal, matching every canonical input.
            total = min(total, (n * n - 1) // 2)
            region = _grow_connected_region(rng, n, cells, total)
            regions = (region,)
        else:
            # Keep zero strictly more frequent than either panel color so the
            # background remains modal under generic object diagnostics.
            first_lo = max(2, total - (background_size - 1))
            first_hi = min(total - 2, background_size - 1)
            if first_lo > first_hi:
                continue
            first_size = rng.randint(first_lo, first_hi)
            second_size = total - first_size
            first = _grow_connected_region(rng, n, cells, first_size)
            if first is None:
                continue
            second = _grow_connected_region(rng, n, cells - first, second_size)
            regions = (first, second)

        if any(region is None for region in regions):
            continue
        panel = [[0] * n for _ in range(n)]
        for color, region in zip(palette, regions):
            for row, col in region:
                panel[row][col] = color
        if not _has_trivial_stabilizer(panel):
            continue
        return panel
    raise RuntimeError(
        f"could not construct an asymmetric {n}x{n} panel after 512 attempts"
    )


def _scheduled_kind(seed, sample_index):
    """Cycle through all non-identity transforms with a stable per-seed offset."""
    offset_rng = stable_rng(seed, f"{TASK_ID}|kind-schedule", VERSION)
    offset = offset_rng.randrange(len(_TRANSFORM_KINDS))
    return _TRANSFORM_KINDS[(offset + sample_index) % len(_TRANSFORM_KINDS)]


def _assemble(panels, divider_color):
    n = len(panels[0])
    grid = full_grid(n, 3 * n + 2, divider_color)
    for panel_index, panel in enumerate(panels):
        left = panel_index * (n + 1)
        for row in range(n):
            for col in range(n):
                grid[row][left + col] = panel[row][col]
    return grid


def _split(grid):
    n = len(grid)
    return [
        [
            [grid[row][panel_index * (n + 1) + col] for col in range(n)]
            for row in range(n)
        ]
        for panel_index in range(3)
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unsupported override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # draw_int_diff keeps the ordinary bands meaningfully different while every
    # exact boundary override 3..6 remains legal in every band.
    n = ctx.draw_int_diff("panel", 3, 6)
    divider_color = ctx.draw_color("divider_color", exclude={0})
    palette = ctx.draw_distinct_colors(
        "panel_palette", n=2, exclude={0, divider_color}
    )

    if overrides.get("kind") is not None:
        kind = ctx.draw_choice("kind", _TRANSFORM_KINDS)
    else:
        # Record the scheduled value through GenCtx so default draw provenance
        # and observe_overrides can be compared exactly by the v6 contract.
        kind = ctx.draw_choice("kind", (_scheduled_kind(seed, sample_index),))

    density_bounds = {
        "easy": (0.28, 0.48),
        "medium": (0.34, 0.56),
        "hard": (0.42, 0.60),
    }.get(difficulty, (0.30, 0.68))

    # Cycle through canonical-like one-color panels and lawful two-color
    # distractor variants.  This yields object-count support 5..7 and palette
    # support 3..4 instead of a single over-fragmented template.
    palette_mode = sample_index % 3
    palette_a = palette[:1] if palette_mode in (0, 1) else palette
    palette_c = palette[:1] if palette_mode in (0, 2) else palette

    panel_a = _random_asymmetric_panel(
        ctx.draw_rng("panel_a"), n, palette_a, density_bounds=density_bounds
    )
    panel_b = _apply(panel_a, kind)

    panel_c_rng = ctx.draw_rng("panel_c")
    for _ in range(512):
        panel_c = _random_asymmetric_panel(
            panel_c_rng, n, palette_c, density_bounds=density_bounds
        )
        answer = _apply(panel_c, kind)
        if panel_c in (panel_a, panel_b):
            continue
        if answer in (panel_a, panel_b, panel_c):
            continue
        break
    else:
        raise RuntimeError("could not construct a non-embedded transformed query panel")

    return _assemble((panel_a, panel_b, panel_c), divider_color)


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty rectangular list"], "facts": None}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["grid must be a nonempty rectangular list"], "facts": None}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"], "facts": None}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["cells must be integer ARC colors 0..9"], "facts": None}

    n = len(grid)
    if not 3 <= n <= 6:
        errors.append("panel side must lie in 3..6")
    if width != 3 * n + 2:
        errors.append(f"cols {width} != 3*rows+2 ({3 * n + 2})")
        return {"errors": errors, "facts": None}

    divider_left = [grid[row][n] for row in range(n)]
    divider_right = [grid[row][2 * n + 1] for row in range(n)]
    if len(set(divider_left)) != 1 or divider_left != divider_right:
        errors.append("divider columns must be identical solid colors")
        divider_color = None
    else:
        divider_color = divider_left[0]
        if divider_color == 0:
            errors.append("divider color must be non-background")

    panel_a, panel_b, panel_c = _split(grid)
    panel_values = {
        value
        for panel in (panel_a, panel_b, panel_c)
        for row in panel
        for value in row
    }
    if divider_color is not None and divider_color in panel_values:
        errors.append("divider color must be absent from all panels")

    matching = _matching_kinds(panel_a, panel_b)
    if len(matching) != 1:
        errors.append(
            f"panel A->B transform must be unique; found {len(matching)} matches"
        )
        kind = matching[0] if matching else None
    else:
        kind = matching[0]
        if kind == "id":
            errors.append("identity A->B transform is a rule-hiding instance")

    count_c = sum(value != 0 for row in panel_c for value in row)
    if count_c == 0:
        errors.append("panel C must be nonempty")
    if count_c == n * n:
        errors.append("panel C must be nonsolid")

    answer = _apply(panel_c, kind) if kind is not None else None
    if answer == panel_c:
        errors.append("the inferred transform is invisible on panel C")
    if answer is not None and answer in (panel_a, panel_b):
        errors.append("the query answer is already embedded in panel A or B")

    facts = {
        "panel": n,
        "kind": kind,
        "divider_color": divider_color,
        "matching_kinds": matching,
        "panel_a": panel_a,
        "panel_b": panel_b,
        "panel_c": panel_c,
        "answer": answer,
    }
    return {"errors": errors, "facts": facts}


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["facts"] is None:
        raise ValueError("cannot observe overrides from malformed grid")
    facts = analysis["facts"]
    return {
        "panel": facts["panel"],
        "kind": facts["kind"],
        "divider_color": facts["divider_color"],
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Return structural/semantic violations; an empty list means acceptance."""
    return list(_analyze(grid)["errors"])

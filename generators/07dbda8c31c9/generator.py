"""Generator for arc_additional_puzzles_21_set5:E32.

Rule: count every red (2) cell.  Return a one-row red bar whose width is that
cell count.

The three-step default schedule is deliberately contrastive:

* ``plain`` places pairwise non-adjacent red cells on a black background;
* ``decoy_colors`` adds non-red nonzero cells that must not affect the count;
* ``blob`` joins all red cells into one component so cells, not objects, count.

Every normal three-demonstration episode therefore refutes both common shortcut
rules before the query is shown.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "07dbda8c31c9"
VERSION = "4.0.0"  # exact observable axes + branch-complete lesson schedule
TASK_ID = "07dbda8c31c9"
RULE_HASH = "bd0e3c33843a"
EXPECTED_OUTPUT_CODOMAIN = 27

SUMMARY = (
    "Count every red (2) cell, independent of position or connectivity, and "
    "output one row of exactly that many red cells.  A three-example lesson "
    "always includes isolated reds, ignored non-red decoys, and one connected "
    "red blob, so neither nonzero-count nor object-count shortcuts fit."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input is a rectangular 4..12 by 4..30 ARC grid",
    "there are 2..28 red cells and black remains the unique modal color",
    "plain scenes contain only pairwise non-adjacent red cells",
    "decoy_colors scenes contain isolated reds plus at least two non-red nonzero cells",
    "blob scenes contain one connected non-rectangular 2-D red component",
    "the Racket output is a 1 x red-count bar filled with red (2)",
]

TEXTURES = ("plain", "decoy_colors", "blob")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty profile", "valid": "4..12"},
    "grid_w": {"type": "int", "default": "difficulty profile", "valid": "4..30"},
    "n_red": {"type": "int", "default": "difficulty profile", "valid": "2..28"},
    "texture": {
        "type": "str",
        "default": "sample_index schedule plain|decoy_colors|blob",
        "valid": "plain|decoy_colors|blob",
        "doc": (
            "plain: isolated red cells; decoy_colors: isolated reds plus "
            "ignored non-red cells; blob: one connected red component"
        ),
    },
}

_DIFFICULTY_DOMAINS = {
    "easy": (range(5, 8), range(5, 9), range(2, 7)),
    "medium": (range(6, 11), range(7, 16), range(4, 15)),
    "hard": (range(8, 13), range(12, 31), range(10, 29)),
    None: (range(5, 13), range(5, 31), range(2, 29)),
}
_DECOY_COLORS = (1, 3, 4, 5, 6, 7, 8, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _is_rectangular_grid(grid) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and isinstance(grid[0], list)
        and bool(grid[0])
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    )


def _red_cells(grid) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    }


def _component_count(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in _CARDINAL:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def _reds_are_isolated(cells: set[tuple[int, int]]) -> bool:
    return all(
        (r + dr, c + dc) not in cells
        for r, c in cells
        for dr, dc in _CARDINAL
    )


def _infer_texture(grid) -> str:
    red = _red_cells(grid)
    decoys = sum(value not in (0, 2) for row in grid for value in row)
    if decoys:
        if decoys < 2:
            raise ValueError("decoy texture needs at least two non-red nonzero cells")
        if not _reds_are_isolated(red):
            raise ValueError("decoy texture must keep red cells pairwise non-adjacent")
        return "decoy_colors"
    if _reds_are_isolated(red):
        return "plain"
    if len(red) >= 3 and _component_count(red) == 1 and _blob_is_teaching_shape(red):
        return "blob"
    raise ValueError(
        "red topology is neither pairwise-isolated plain nor one connected blob"
    )


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned input grid."""
    if not _is_rectangular_grid(grid):
        raise ValueError("expected a non-empty rectangular grid")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_red": len(_red_cells(grid)),
        "texture": _infer_texture(grid),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject inputs outside the contrastive count-red teaching grammar."""
    del difficulty, meta
    errors: list[str] = []
    if not _is_rectangular_grid(grid):
        return ["expected a non-empty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if not (4 <= h <= 12 and 4 <= w <= 30):
        errors.append(f"grid dimensions {h}x{w} are outside 4..12 by 4..30")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors
    red_count = sum(value == 2 for row in grid for value in row)
    if not (2 <= red_count <= 28):
        errors.append(f"red-cell count {red_count} is outside 2..28")
    if red_count > w:
        errors.append("red-cell count exceeds input width, changing the canonical shrink relation")
    counts = {value: sum(cell == value for row in grid for cell in row) for value in range(10)}
    if counts[0] <= max(counts[value] for value in range(1, 10)):
        errors.append("black must remain the unique modal background color")
    if errors:
        return errors
    try:
        texture = _infer_texture(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if texture == "decoy_colors":
        decoy_colors = {value for row in grid for value in row if value not in (0, 2)}
        if not decoy_colors:
            errors.append("decoy_colors scene has no non-red decoy palette")
    return errors


def _independent_capacity(h: int, w: int) -> int:
    return (h * w + 1) // 2


def _feasible(h: int, w: int, n_red: int, texture: str) -> bool:
    area = h * w
    if not (4 <= h <= 12 and 4 <= w <= 30 and 2 <= n_red <= 28):
        return False
    if n_red > w:
        return False
    if texture == "plain":
        return n_red <= _independent_capacity(h, w) and area > 2 * n_red
    if texture == "decoy_colors":
        return n_red <= _independent_capacity(h, w) and area > 2 * n_red + 2
    if texture == "blob":
        return 3 <= n_red and area > 2 * n_red
    return False


def _record_exact_int(ctx, label: str, value: int, explicit: bool) -> int:
    bounds = {"grid_h": (4, 12), "grid_w": (4, 30), "n_red": (2, 28)}
    low, high = bounds[label]
    return ctx.draw_int(label, low, high) if explicit else ctx.draw_int(label, value, value)


def _choose_axes(ctx, seed: int, sample_index: int, difficulty, overrides):
    explicit = {name for name in AXES if overrides.get(name) is not None}
    requested_h = int(overrides["grid_h"]) if "grid_h" in explicit else None
    requested_w = int(overrides["grid_w"]) if "grid_w" in explicit else None
    requested_n = int(overrides["n_red"]) if "n_red" in explicit else None
    requested_texture = overrides.get("texture") if "texture" in explicit else None
    if requested_texture is not None and requested_texture not in TEXTURES:
        raise ValueError(f"unsupported texture override: {requested_texture!r}")

    scheduled = TEXTURES[sample_index % EXAMPLES_NEEDED]
    # The ordinary lesson stream traverses the full finite answer alphabet.
    # `run_one` emits six consecutive sample indices per episode; the factor 6
    # makes the standard diversity probe cover all 28 counts deterministically.
    if difficulty is None:
        # Six consecutive sample indices per episode make the standard
        # no-difficulty diversity probe traverse all 27 legal counts.
        default_n = 2 + ((int(seed) * 6 + sample_index) % EXPECTED_OUTPUT_CODOMAIN)
    else:
        profile_counts = tuple(_DIFFICULTY_DOMAINS[difficulty][2])
        default_n = ctx.draw_rng("default_n_profile").choice(profile_counts)
    if (requested_texture or scheduled) == "blob" and default_n < 3:
        default_n = 3
    lock_default_n = not explicit or explicit == {"texture"}
    texture_order = (
        (requested_texture,)
        if requested_texture is not None
        else (scheduled,) + tuple(t for t in TEXTURES if t != scheduled)
    )
    pref_h, pref_w, pref_n = _DIFFICULTY_DOMAINS[difficulty]
    rng = ctx.draw_rng("axis_profile")
    chosen = None
    for texture in texture_order:
        triples = [
            (h, w, n)
            for h in range(4, 13)
            for w in range(4, 31)
            for n in range(2, 29)
            if (requested_h is None or h == requested_h)
            and (requested_w is None or w == requested_w)
            and (requested_n is None or n == requested_n)
            and (not lock_default_n or n == default_n)
            and _feasible(h, w, n, texture)
        ]
        if not triples:
            continue
        preferred = [
            triple
            for triple in triples
            if ("grid_h" in explicit or triple[0] in pref_h)
            and ("grid_w" in explicit or triple[1] in pref_w)
            and ("n_red" in explicit or triple[2] in pref_n)
        ]
        chosen = rng.choice(preferred or triples)
        chosen_texture = texture
        break
    if chosen is None:
        requested = {name: overrides[name] for name in sorted(explicit)}
        raise ValueError(f"incompatible exact axes for count-red grammar: {requested}")

    if "texture" in explicit:
        texture = ctx.draw_choice("texture", TEXTURES)
    else:
        texture = ctx.draw_choice("texture", (chosen_texture,))
    h = _record_exact_int(ctx, "grid_h", chosen[0], "grid_h" in explicit)
    w = _record_exact_int(ctx, "grid_w", chosen[1], "grid_w" in explicit)
    n_red = _record_exact_int(ctx, "n_red", chosen[2], "n_red" in explicit)
    if (h, w, n_red, texture) != (*chosen, chosen_texture):
        raise RuntimeError("axis recording diverged from the selected feasible profile")
    return h, w, n_red, texture


def _isolated_positions(h: int, w: int, n_red: int, rng):
    parity_classes = [
        [(r, c) for r in range(h) for c in range(w) if (r + c) % 2 == parity]
        for parity in (0, 1)
    ]
    legal = [cells for cells in parity_classes if len(cells) >= n_red]
    if not legal:
        raise ValueError("requested red count does not fit as isolated cells")
    cells = rng.choice(legal)
    return rng.sample(cells, n_red)


def _blob_is_teaching_shape(cells: set[tuple[int, int]]) -> bool:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    height = max(rows) - min(rows) + 1
    width = max(cols) - min(cols) + 1
    return height >= 2 and width >= 2 and len(cells) < height * width


def _connected_blob(h: int, w: int, n_red: int, rng):
    for _attempt in range(128):
        start = (rng.randrange(h), rng.randrange(w))
        cells = {start}
        frontier = {
            (start[0] + dr, start[1] + dc)
            for dr, dc in _CARDINAL
            if 0 <= start[0] + dr < h and 0 <= start[1] + dc < w
        }
        while len(cells) < n_red:
            choices = sorted(frontier)
            if not choices:
                break
            cell = rng.choice(choices)
            frontier.remove(cell)
            cells.add(cell)
            r, c = cell
            frontier.update(
                (r + dr, c + dc)
                for dr, dc in _CARDINAL
                if 0 <= r + dr < h
                and 0 <= c + dc < w
                and (r + dr, c + dc) not in cells
            )
        if len(cells) == n_red and _blob_is_teaching_shape(cells):
            return cells
    raise RuntimeError("could not construct a connected non-rectangular 2-D blob")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _DIFFICULTY_DOMAINS:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unsupported override(s): {unknown}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, n_red, texture = _choose_axes(ctx, seed, sample_index, difficulty, overrides)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)

    if texture in ("plain", "decoy_colors"):
        red_cells = _isolated_positions(h, w, n_red, rng)
    else:
        red_cells = sorted(_connected_blob(h, w, n_red, rng))
    for r, c in red_cells:
        grid[r][c] = 2

    if texture == "decoy_colors":
        free = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0]
        rng.shuffle(free)
        max_decoys = min(6, len(free), h * w - 2 * n_red - 1)
        decoy_count = rng.randint(2, max_decoys)
        for index, (r, c) in enumerate(free[:decoy_count]):
            if index < 2:
                grid[r][c] = _DECOY_COLORS[index]
            else:
                grid[r][c] = rng.choice(_DECOY_COLORS)

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal generator invariant failed: {errors[0]}")
    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "n_red": n_red, "texture": texture}
    if observed != expected:
        raise RuntimeError(f"axis observability mismatch: expected {expected}, got {observed}")
    return grid

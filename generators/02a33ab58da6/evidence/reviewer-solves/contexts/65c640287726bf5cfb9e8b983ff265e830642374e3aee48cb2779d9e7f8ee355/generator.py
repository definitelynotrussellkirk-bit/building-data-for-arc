"""Semantic multi-motif generator for ARC task 230f2e48 / 02a33ab58da6.

Each motif is a straight gray-red-black-red ray.  The red tail beyond black
rotates at the black pivot, in the perpendicular direction toward the canvas
center.  Scenes may contain several independent motifs.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "02a33ab58da6"
VERSION = "4.1.0"
TASK_ID = "02a33ab58da6"
RULE_HASH = "74c9a82b96dc"
SUMMARY = (
    "One to eight independent gray-red-black-red rays lie on a color-7 field. "
    "For every ray, the red tail beyond its black pivot rotates perpendicular "
    "toward the grid center while retaining its length."
)
INVARIANTS = [
    "the palette is exactly field 7, red 2, gray endpoint 5, and black pivot 0",
    "each gray endpoint has exactly one straight red-bar / black-pivot / red-tail ray",
    "every gray endpoint and black pivot belongs to one motif and no stray red cells exist",
    "the old tail and its center-directed rotated destination are in bounds and disjoint",
    "normal generated scenes always contain at least one motif and visibly transform",
]
EXAMPLES_NEEDED = 3
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng public|generalized",
        "valid": "public|generalized",
        "doc": "Complete official feature profile or broader lawful scene.",
    },
}

FIELD = 7
RED = 2
GRAY = 5
PIVOT = 0
_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_D4 = (
    (1, 0, 0, 1),
    (-1, 0, 0, 1),
    (1, 0, 0, -1),
    (-1, 0, 0, -1),
    (0, 1, 1, 0),
    (0, -1, 1, 0),
    (0, 1, -1, 0),
    (0, -1, -1, 0),
)

# (canvas size, ((source direction, center-directed turn, bar length, tail length), ...))
# Absolute positions are lawful nuisance variation; every linked motif tuple and
# the scene-level dimensions/count are retained together.
_PUBLIC_PROFILES = (
    (10, (
        ((1, 0), (0, 1), 2, 4),
        ((1, 0), (0, -1), 4, 1),
    )),
    (8, (
        ((0, 1), (1, 0), 2, 2),
    )),
    (12, (
        ((0, -1), (1, 0), 1, 1),
        ((0, 1), (-1, 0), 2, 2),
        ((0, -1), (-1, 0), 2, 5),
    )),
    (16, (
        ((1, 0), (0, -1), 2, 2),
        ((0, 1), (1, 0), 2, 2),
        ((0, 1), (-1, 0), 0, 1),
        ((-1, 0), (0, 1), 7, 3),
        ((-1, 0), (0, 1), 4, 1),
        ((-1, 0), (0, 1), 1, 2),
        ((0, -1), (-1, 0), 0, 1),
    )),
)


def _copy_grid(grid):
    return [list(row) for row in grid]


def _transform_vector(vector, matrix):
    dr, dc = vector
    a, b, c, d = matrix
    return a * dr + b * dc, c * dr + d * dc


def _turn_toward_center(direction, pivot, height, width):
    dr, dc = direction
    row, col = pivot
    if dc != 0:
        return (1, 0) if row < height // 2 else (-1, 0)
    return (0, 1) if col < width // 2 else (0, -1)


def _cells_for_spec(height, width, pivot, direction, turn, bar_len, tail_len):
    row, col = pivot
    dr, dc = direction
    tr, tc = turn
    gray = row - dr * (bar_len + 1), col - dc * (bar_len + 1)
    bar = {(row - dr * index, col - dc * index) for index in range(1, bar_len + 1)}
    old_tail = {(row + dr * index, col + dc * index) for index in range(1, tail_len + 1)}
    new_tail = {(row + tr * index, col + tc * index) for index in range(1, tail_len + 1)}
    source = {gray, pivot} | bar | old_tail
    reserved = source | new_tail
    if any(not (0 <= r < height and 0 <= c < width) for r, c in reserved):
        return None
    if len(reserved) != len(source) + len(new_tail):
        return None
    return {
        "gray": gray,
        "pivot": pivot,
        "bar": bar,
        "old_tail": old_tail,
        "new_tail": new_tail,
        "source": source,
        "reserved": reserved,
    }


def _build_scene(rng, height, width, specs):
    """Pack exact motif specifications without source/output collisions."""
    ordered = list(specs)
    rng.shuffle(ordered)
    occupied = set()
    placed = []
    for direction, requested_turn, bar_len, tail_len in ordered:
        found = None
        for _ in range(1200):
            pivot = rng.randrange(height), rng.randrange(width)
            turn = _turn_toward_center(direction, pivot, height, width)
            if requested_turn is not None and turn != requested_turn:
                continue
            cells = _cells_for_spec(
                height, width, pivot, direction, turn, bar_len, tail_len
            )
            if cells is None or cells["reserved"] & occupied:
                continue
            found = cells, direction, turn, bar_len, tail_len
            break
        if found is None:
            return None
        cells, direction, turn, bar_len, tail_len = found
        occupied.update(cells["reserved"])
        placed.append((cells, direction, turn, bar_len, tail_len))

    grid = full_grid(height, width, FIELD)
    for cells, _, _, _, _ in placed:
        gray_row, gray_col = cells["gray"]
        pivot_row, pivot_col = cells["pivot"]
        grid[gray_row][gray_col] = GRAY
        grid[pivot_row][pivot_col] = PIVOT
        for row, col in cells["bar"] | cells["old_tail"]:
            grid[row][col] = RED
    return grid


def _build_single_motif_ranked(height, width, spec, rank):
    """Select one of a single motif's finite legal placements by exact rank."""
    direction, requested_turn, bar_len, tail_len = spec
    candidates = []
    for row in range(height):
        for col in range(width):
            pivot = row, col
            turn = _turn_toward_center(direction, pivot, height, width)
            if turn != requested_turn:
                continue
            cells = _cells_for_spec(
                height, width, pivot, direction, turn, bar_len, tail_len
            )
            if cells is not None:
                candidates.append(cells)
    if not candidates:
        return None
    cells = candidates[rank % len(candidates)]
    grid = full_grid(height, width, FIELD)
    gray_row, gray_col = cells["gray"]
    pivot_row, pivot_col = cells["pivot"]
    grid[gray_row][gray_col] = GRAY
    grid[pivot_row][pivot_col] = PIVOT
    for row, col in cells["bar"] | cells["old_tail"]:
        grid[row][col] = RED
    return grid


@lru_cache(maxsize=8)
def _two_motif_variants(height, width, specs):
    """Enumerate the finite collision-free layouts of a two-motif profile."""
    candidate_sets = []
    for direction, requested_turn, bar_len, tail_len in specs:
        candidates = []
        for row in range(height):
            for col in range(width):
                pivot = row, col
                turn = _turn_toward_center(direction, pivot, height, width)
                if turn != requested_turn:
                    continue
                cells = _cells_for_spec(
                    height, width, pivot, direction, turn, bar_len, tail_len
                )
                if cells is not None:
                    candidates.append(cells)
        candidate_sets.append(candidates)

    expected_shape = sorted(
        (direction, bar_len, tail_len)
        for direction, _, bar_len, tail_len in specs
    )
    variants = []
    for first_cells, second_cells in product(*candidate_sets):
        if first_cells["reserved"] & second_cells["reserved"]:
            continue
        grid = full_grid(height, width, FIELD)
        for cells in (first_cells, second_cells):
            gray_row, gray_col = cells["gray"]
            pivot_row, pivot_col = cells["pivot"]
            grid[gray_row][gray_col] = GRAY
            grid[pivot_row][pivot_col] = PIVOT
            for row, col in cells["bar"] | cells["old_tail"]:
                grid[row][col] = RED
        analysis = _analyze(grid)
        observed_shape = sorted(
            (move["direction"], move["bar_len"], move["tail_len"])
            for move in analysis["facts"]["moves"]
        )
        if not analysis["errors"] and observed_shape == expected_shape:
            variants.append(tuple(tuple(row) for row in grid))
    return tuple(variants)


def _build_two_motif_ranked(height, width, specs, rank):
    variants = _two_motif_variants(height, width, tuple(specs))
    if not variants:
        return None
    return [list(row) for row in variants[rank % len(variants)]]


def _build_multi_motif_ranked(height, width, specs, rank):
    """Use a disjoint mixed-radix block for a stable multi-motif layout rank."""
    candidate_sets = []
    for direction, requested_turn, bar_len, tail_len in specs:
        candidates = []
        for row in range(height):
            for col in range(width):
                pivot = row, col
                turn = _turn_toward_center(direction, pivot, height, width)
                if turn != requested_turn:
                    continue
                cells = _cells_for_spec(
                    height, width, pivot, direction, turn, bar_len, tail_len
                )
                if cells is not None:
                    candidates.append(cells)
        candidate_sets.append(candidates)

    total = 1
    for candidates in candidate_sets:
        total *= len(candidates)
    lane_count = min(512, total)
    lane = rank % lane_count
    expected_shape = sorted(
        (direction, bar_len, tail_len)
        for direction, _, bar_len, tail_len in specs
    )
    for flat_index in range(lane, total, lane_count):
        remainder = flat_index
        chosen = []
        for candidates in reversed(candidate_sets):
            chosen.append(candidates[remainder % len(candidates)])
            remainder //= len(candidates)
        chosen.reverse()
        occupied = set()
        collision = False
        for cells in chosen:
            if cells["reserved"] & occupied:
                collision = True
                break
            occupied.update(cells["reserved"])
        if collision:
            continue
        grid = full_grid(height, width, FIELD)
        for cells in chosen:
            gray_row, gray_col = cells["gray"]
            pivot_row, pivot_col = cells["pivot"]
            grid[gray_row][gray_col] = GRAY
            grid[pivot_row][pivot_col] = PIVOT
            for row, col in cells["bar"] | cells["old_tail"]:
                grid[row][col] = RED
        analysis = _analyze(grid)
        observed_shape = sorted(
            (move["direction"], move["bar_len"], move["tail_len"])
            for move in analysis["facts"]["moves"]
        )
        if not analysis["errors"] and observed_shape == expected_shape:
            return grid
    return None


def _scan_moves(grid):
    height, width = len(grid), len(grid[0])
    moves = []
    for gray_row in range(height):
        for gray_col in range(width):
            if grid[gray_row][gray_col] != GRAY:
                continue
            for dr, dc in _DIRECTIONS:
                pivots = []
                for distance in range(1, height + width):
                    row = gray_row + dr * distance
                    col = gray_col + dc * distance
                    if 0 <= row < height and 0 <= col < width and grid[row][col] == PIVOT:
                        pivots.append(distance)
                if not pivots:
                    continue
                pivot_step = pivots[0]
                if any(
                    grid[gray_row + dr * step][gray_col + dc * step] != RED
                    for step in range(1, pivot_step)
                ):
                    continue
                pivot = gray_row + dr * pivot_step, gray_col + dc * pivot_step
                tail_len = 0
                while True:
                    row = pivot[0] + dr * (tail_len + 1)
                    col = pivot[1] + dc * (tail_len + 1)
                    if 0 <= row < height and 0 <= col < width and grid[row][col] == RED:
                        tail_len += 1
                    else:
                        break
                if tail_len == 0:
                    continue
                turn = _turn_toward_center((dr, dc), pivot, height, width)
                moves.append({
                    "gray": (gray_row, gray_col),
                    "direction": (dr, dc),
                    "pivot": pivot,
                    "turn": turn,
                    "bar_len": pivot_step - 1,
                    "tail_len": tail_len,
                })
    return moves


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
           for row in grid for value in row):
        return {"errors": ["cells must be integer ARC colors 0..9"], "facts": None}
    height = len(grid)
    if not (8 <= height <= 24 and 8 <= width <= 24):
        errors.append("dimensions must lie in 8..24")
    palette = {value for row in grid for value in row}
    if palette != {PIVOT, RED, GRAY, FIELD}:
        errors.append("palette must be exactly {0,2,5,7}")
    if sum(value == FIELD for row in grid for value in row) <= height * width / 2:
        errors.append("color 7 must be the modal field")

    moves = _scan_moves(grid)
    gray_cells = {(row, col) for row in range(height) for col in range(width)
                  if grid[row][col] == GRAY}
    pivot_cells = {(row, col) for row in range(height) for col in range(width)
                   if grid[row][col] == PIVOT}
    red_cells = {(row, col) for row in range(height) for col in range(width)
                 if grid[row][col] == RED}
    if not (1 <= len(moves) <= 8):
        errors.append("scene must contain one to eight valid motifs")
    if len(moves) != len(gray_cells) or {move["gray"] for move in moves} != gray_cells:
        errors.append("each gray endpoint must define exactly one motif")
    if len(moves) != len(pivot_cells) or {move["pivot"] for move in moves} != pivot_cells:
        errors.append("each black pivot must belong to exactly one motif")

    expected_red = set()
    destinations = set()
    for move in moves:
        dr, dc = move["direction"]
        tr, tc = move["turn"]
        gray_row, gray_col = move["gray"]
        pivot_row, pivot_col = move["pivot"]
        if not (0 <= move["bar_len"] <= 7):
            errors.append("bar length must lie in 0..7")
        if not (1 <= move["tail_len"] <= 6):
            errors.append("tail length must lie in 1..6")
        for step in range(1, move["bar_len"] + 1):
            expected_red.add((gray_row + dr * step, gray_col + dc * step))
        for step in range(1, move["tail_len"] + 1):
            expected_red.add((pivot_row + dr * step, pivot_col + dc * step))
            destination = pivot_row + tr * step, pivot_col + tc * step
            if not (0 <= destination[0] < height and 0 <= destination[1] < width):
                errors.append("rotated tail leaves the grid")
            elif grid[destination[0]][destination[1]] != FIELD:
                errors.append("rotated tail destination must be clear field")
            destinations.add(destination)
    if expected_red != red_cells:
        errors.append("red cells must belong exactly to motif bars and old tails")
    if len(destinations) != sum(move["tail_len"] for move in moves):
        errors.append("rotated tails may not collide")

    output = _copy_grid(grid)
    for move in moves:
        pivot_row, pivot_col = move["pivot"]
        dr, dc = move["direction"]
        for step in range(1, move["tail_len"] + 1):
            output[pivot_row + dr * step][pivot_col + dc * step] = FIELD
    for move in moves:
        pivot_row, pivot_col = move["pivot"]
        tr, tc = move["turn"]
        for step in range(1, move["tail_len"] + 1):
            row = pivot_row + tr * step
            col = pivot_col + tc * step
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = RED
    if output == [list(row) for row in grid]:
        errors.append("rule must visibly move at least one tail")
    facts = {
        "height": height,
        "width": width,
        "motif_count": len(moves),
        "moves": moves,
        "output": output,
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return analysis["facts"]["output"]


def _scene_signature_from_facts(facts):
    motifs = tuple(sorted(
        (
            move["direction"], move["turn"],
            move["bar_len"], move["tail_len"],
        )
        for move in facts["moves"]
    ))
    return facts["height"], facts["width"], motifs


def _public_signatures():
    signatures = set()
    for size, specs in _PUBLIC_PROFILES:
        for matrix in _D4:
            transformed = tuple(sorted(
                (
                    _transform_vector(direction, matrix),
                    _transform_vector(turn, matrix),
                    bar_len,
                    tail_len,
                )
                for direction, turn, bar_len, tail_len in specs
            ))
            signatures.add((size, size, transformed))
    return frozenset(signatures)


_PUBLIC_SIGNATURES = _public_signatures()


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    return (
        "public"
        if _scene_signature_from_facts(analysis["facts"]) in _PUBLIC_SIGNATURES
        else "generalized"
    )


def observe_overrides(grid):
    signature = canonical_profile_signature(grid)
    if signature == "invalid":
        return {}
    return {"scene_family": signature}


def _public_specs(rng, seed, sample_index, band_index):
    # The 8x8 one-motif profile has exactly 96 D4+placement variants.  Schedule
    # it sparsely and rank those variants explicitly so long telemetry sweeps do
    # not waste valid draws on birthday-collision duplicates.
    if sample_index % 32 == 0:
        profile_index = 1
        within_band = (sample_index // 32 + seed) % 32
        matrix_index = within_band % len(_D4)
        placement_rank = band_index * 4 + within_band // len(_D4)
    elif sample_index % 4 == 1:
        profile_index = 0
        within_band = (sample_index // 4 + 2 * seed) % 250
        matrix_index = within_band % len(_D4)
        placement_rank = band_index * 32 + within_band // len(_D4)
    elif sample_index % 2 == 0:
        profile_index = 2
        occurrence = band_index * 500 + sample_index // 2
        matrix_index = occurrence % len(_D4)
        placement_rank = occurrence // len(_D4)
    else:
        profile_index = 3
        matrix_index = rng.randrange(len(_D4))
        placement_rank = None
    size, specs = _PUBLIC_PROFILES[profile_index]
    matrix = _D4[matrix_index]
    transformed = [
        (
            _transform_vector(direction, matrix),
            _transform_vector(turn, matrix),
            bar_len,
            tail_len,
        )
        for direction, turn, bar_len, tail_len in specs
    ]
    return size, size, transformed, placement_rank


def _generalized_specs(rng, difficulty):
    if difficulty == "easy":
        height, width = rng.randint(8, 12), rng.randint(8, 12)
        count = rng.randint(1, 3)
        max_bar, max_tail = 4, 3
    elif difficulty == "hard":
        height, width = rng.randint(16, 24), rng.randint(16, 24)
        count = rng.randint(4, 8)
        max_bar, max_tail = 7, 6
    else:
        height, width = rng.randint(11, 18), rng.randint(11, 18)
        count = rng.randint(2, 5)
        max_bar, max_tail = 6, 5
    specs = [
        (rng.choice(_DIRECTIONS), None, rng.randint(0, max_bar), rng.randint(1, max_tail))
        for _ in range(count)
    ]
    return height, width, specs


_DIFFICULTIES = {None, "default", "easy", "medium", "hard"}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = ctx.draw_choice(
        "scene_family", ("public", "generalized", "generalized", "generalized")
    )
    rng = ctx.draw_rng("scene")
    band = "medium" if difficulty in (None, "default") else difficulty
    band_index = {"easy": 0, "medium": 1, "hard": 2}[band]
    for _ in range(300):
        if family == "public":
            height, width, specs, placement_rank = _public_specs(
                rng, seed, sample_index, band_index
            )
        else:
            height, width, specs = _generalized_specs(rng, band)
            placement_rank = None
        if placement_rank is not None:
            if len(specs) == 1:
                grid = _build_single_motif_ranked(
                    height, width, specs[0], placement_rank
                )
            elif len(specs) == 2:
                grid = _build_two_motif_ranked(
                    height, width, specs, placement_rank
                )
            else:
                grid = _build_multi_motif_ranked(
                    height, width, specs, placement_rank
                )
        else:
            grid = _build_scene(rng, height, width, specs)
        if grid is None:
            continue
        analysis = _analyze(grid)
        if analysis["errors"]:
            continue
        expected_shape = sorted(
            (direction, bar_len, tail_len)
            for direction, _, bar_len, tail_len in specs
        )
        observed_shape = sorted(
            (move["direction"], move["bar_len"], move["tail_len"])
            for move in analysis["facts"]["moves"]
        )
        if observed_shape != expected_shape:
            continue
        if canonical_profile_signature(grid) != family:
            continue
        return grid
    raise RuntimeError(f"could not construct a valid {family} scene")

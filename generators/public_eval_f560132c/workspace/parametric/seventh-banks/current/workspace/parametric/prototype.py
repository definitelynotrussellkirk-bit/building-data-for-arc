"""Jigsaw-square reconstruction and source-independent lesson sampler.

The official task supplies disconnected polyomino pieces.  One piece contains a
small palette square.  Its zero palette cell (when present) is still physical
piece material.  The palette-bearing piece fixes the output orientation: it is
not rotated and occupies the output's top-left.  Other pieces may rotate by
quarter turns; reflections are forbidden.
"""
from __future__ import annotations

from collections import Counter
import copy
from functools import lru_cache
import hashlib
import math
import random
from typing import Any, Iterable

SETTINGS = ('pack_only', 'highlight_hub')
INTERNAL_SETTINGS = SETTINGS + ('highlight_largest', 'highlight_key')
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def checked_grid(value: Any) -> list[list[int]]:
    if (type(value) is not list or not 1 <= len(value) <= 30 or
            any(type(row) is not list for row in value) or
            not 1 <= len(value[0]) <= 30 or
            any(len(row) != len(value[0]) or
                any(type(v) is not int or not 0 <= v <= 9 for v in row)
                for row in value)):
        raise ValueError('Expected a rectangular integer-color grid, dimensions 1..30')
    return [[int(v) for v in row] for row in value]


def validate_request(seed: Any, demos: Any, queries: Any) -> None:
    for value, lo, hi, name in (
        (seed, 0, 2**63 - 1, 'seed'),
        (demos, 2, 6, 'demos'),
        (queries, 1, 4, 'queries'),
    ):
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')


def _components4(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result: list[list[tuple[int, int]]] = []
    while unseen:
        seed = min(unseen)
        unseen.remove(seed)
        stack = [seed]
        cells: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in CARDINAL:
                q = (r + dr, c + dc)
                if q in unseen:
                    unseen.remove(q)
                    stack.append(q)
        result.append(sorted(cells))
    return result


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        raise ValueError('Empty piece')
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotations(shape: tuple[tuple[int, int], ...]) -> tuple[tuple[tuple[int, int], ...], ...]:
    current = set(shape)
    result: list[tuple[tuple[int, int], ...]] = []
    for _ in range(4):
        normalized = _normalize(current)
        if normalized not in result:
            result.append(normalized)
        current = {(c, -r) for r, c in current}
    return tuple(result)


def _palette(grid: list[list[int]], components: list[list[tuple[int, int]]]):
    count = len(components)
    n = math.isqrt(count)
    if n not in (2, 3) or n * n != count:
        raise ValueError('Expected exactly four or nine disconnected pieces')
    ranked = sorted(
        components,
        key=lambda cells: (-len({grid[r][c] for r, c in cells}), min(cells)),
    )
    key = ranked[0]
    if len({grid[r][c] for r, c in key}) < n * n - 1:
        raise ValueError('No unique multicolor palette-bearing piece')
    key_set = set(key)
    counts = Counter(grid[r][c] for r, c in key)
    scaffold = max(counts, key=lambda value: (counts[value], -value))
    h, w = len(grid), len(grid[0])
    candidates = []
    for r0 in range(h - n + 1):
        for c0 in range(w - n + 1):
            values = [grid[r0 + r][c0 + c] for r in range(n) for c in range(n)]
            if len(set(values)) != n * n or sum(v != 0 for v in values) < n * n - 1:
                continue
            nonzero = {(r0 + r, c0 + c) for r in range(n) for c in range(n)
                       if grid[r0 + r][c0 + c] != 0}
            if not nonzero <= key_set:
                continue
            candidates.append((sum(v == scaffold for v in values), r0, c0, values))
    if not candidates:
        raise ValueError('No embedded distinct palette square')
    candidates.sort()
    best = candidates[0]
    if len(candidates) > 1 and candidates[1][0] == best[0] and candidates[1][1:3] == best[1:3]:
        raise ValueError('Ambiguous palette')
    _, r0, c0, values = best
    palette = tuple(tuple(values[r*n:(r+1)*n]) for r in range(n))
    key_shape = set(key) | {(r0 + r, c0 + c) for r in range(n) for c in range(n)}
    other = [cells for cells in components if set(cells) != key_set]
    pieces = (_normalize(key_shape),) + tuple(_normalize(cells) for cells in other)
    return n, palette, pieces, scaffold, (r0, c0)


def _pack(pieces: tuple[tuple[tuple[int, int], ...], ...]):
    area = sum(map(len, pieces))
    side = math.isqrt(area)
    if side * side != area or not 1 <= side <= 30:
        raise ValueError('Piece areas do not form a square')
    key = frozenset(pieces[0])
    if max(r for r, _ in key) >= side or max(c for _, c in key) >= side:
        raise ValueError('Palette piece does not fit at the top-left')
    full = tuple((r, c) for r in range(side) for c in range(side))
    occupied0 = set(key)
    placements: dict[int, list[tuple[int, int, int, frozenset[tuple[int, int]]]]] = {}
    for piece_id, shape in enumerate(pieces[1:], 1):
        rows = []
        for rotation, oriented in enumerate(_rotations(shape)):
            ph = max(r for r, _ in oriented) + 1
            pw = max(c for _, c in oriented) + 1
            for dr in range(side - ph + 1):
                for dc in range(side - pw + 1):
                    cells = frozenset((r + dr, c + dc) for r, c in oriented)
                    if not cells & occupied0:
                        rows.append((rotation, dr, dc, cells))
        placements[piece_id] = rows
    solution: dict[int, tuple[int, int, int, frozenset[tuple[int, int]]]] = {
        0: (0, 0, 0, key)
    }

    def search(occupied: set[tuple[int, int]], remaining: frozenset[int]):
        if not remaining:
            return dict(solution) if len(occupied) == side * side else None
        target = next((cell for cell in full if cell not in occupied), None)
        if target is None:
            return None
        options = []
        for piece_id in sorted(remaining):
            for row in placements[piece_id]:
                if target in row[3] and not row[3] & occupied:
                    options.append((piece_id, *row))
        for piece_id, rotation, dr, dc, cells in options:
            solution[piece_id] = (rotation, dr, dc, cells)
            found = search(occupied | set(cells), remaining - {piece_id})
            if found is not None:
                return found
            del solution[piece_id]
        return None

    found = search(occupied0, frozenset(range(1, len(pieces))))
    if found is None:
        raise ValueError('Pieces cannot exactly tile the square')
    owner = [[-1] * side for _ in range(side)]
    for piece_id, (_, _, _, cells) in found.items():
        for r, c in cells:
            if owner[r][c] != -1:
                raise ValueError('Overlapping packing')
            owner[r][c] = piece_id
    if any(v < 0 for row in owner for v in row):
        raise ValueError('Packing leaves a gap')
    return side, found, owner


def _positions(n: int, owner: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    side = len(owner)
    if n == 2:
        ids = ((owner[0][0], owner[0][-1]), (owner[-1][0], owner[-1][-1]))
    else:
        ids_list: list[list[int | None]] = [[None] * 3 for _ in range(3)]
        ids_list[0][0], ids_list[0][2] = owner[0][0], owner[0][-1]
        ids_list[2][0], ids_list[2][2] = owner[-1][0], owner[-1][-1]
        corners = {ids_list[0][0], ids_list[0][2], ids_list[2][0], ids_list[2][2]}
        def side_piece(values):
            choices = []
            for value in values:
                if value not in corners and value not in choices:
                    choices.append(value)
            if len(choices) != 1:
                raise ValueError('Each side must expose exactly one non-corner piece')
            return choices[0]
        ids_list[0][1] = side_piece(owner[0])
        ids_list[2][1] = side_piece(owner[-1])
        ids_list[1][0] = side_piece([row[0] for row in owner])
        ids_list[1][2] = side_piece([row[-1] for row in owner])
        used = {v for row in ids_list for v in row if v is not None}
        remaining = set(range(9)) - used
        if len(remaining) != 1:
            raise ValueError('Expected one interior piece')
        ids_list[1][1] = remaining.pop()
        ids = tuple(tuple(int(v) for v in row) for row in ids_list)
    flat = [v for row in ids for v in row]
    if len(set(flat)) != n * n or set(flat) != set(range(n * n)):
        raise ValueError('Palette positions do not identify every piece once')
    return ids


def _adjacency(owner: list[list[int]]) -> tuple[frozenset[int], ...]:
    count = max(max(row) for row in owner) + 1
    neighbors = [set() for _ in range(count)]
    h, w = len(owner), len(owner[0])
    for r in range(h):
        for c in range(w):
            for dr, dc in ((1, 0), (0, 1)):
                rr, cc = r + dr, c + dc
                if rr < h and cc < w and owner[r][c] != owner[rr][cc]:
                    a, b = owner[r][c], owner[rr][cc]
                    neighbors[a].add(b); neighbors[b].add(a)
    return tuple(frozenset(x) for x in neighbors)


def _decode_uncached(grid_tuple: tuple[tuple[int, ...], ...]) -> dict[str, Any]:
    g = [list(row) for row in grid_tuple]
    components = _components4(g)
    n, palette, pieces, scaffold, palette_origin = _palette(g, components)
    side, placements, owner = _pack(pieces)
    positions = _positions(n, owner)
    adjacency = _adjacency(owner)
    degrees = [len(x) for x in adjacency]
    max_degree = max(degrees)
    hubs = [i for i, value in enumerate(degrees) if value == max_degree]
    areas = [len(p) for p in pieces]
    largest = max(range(len(areas)), key=lambda i: (areas[i], -i))
    return {
        'grid': g, 'n': n, 'palette': palette, 'pieces': pieces,
        'scaffold': scaffold, 'palette_origin': palette_origin, 'side': side,
        'placements': placements, 'owner': owner, 'positions': positions,
        'adjacency': adjacency, 'degrees': tuple(degrees),
        'hub_piece': hubs[0], 'hub_is_unique': len(hubs) == 1,
        'largest_piece': largest, 'areas': tuple(areas),
    }


@lru_cache(maxsize=4096)
def _decode_cached(grid_tuple: tuple[tuple[int, ...], ...]) -> dict[str, Any]:
    # Exact-cover recovery is the dominant cost and is independent of the
    # finish rule. Cache it once per visible input so selected rules and
    # semantic rivals reuse the same decoded intermediate.
    return _decode_uncached(grid_tuple)


def _decode_data(grid: Any) -> dict[str, Any]:
    g = checked_grid(grid)
    return _decode_cached(tuple(tuple(row) for row in g))


def decode(grid: Any) -> dict[str, Any]:
    # The public helper historically returned mutable containers. Preserve
    # that contract while keeping the internal cached value mutation-safe.
    return copy.deepcopy(_decode_data(grid))


def _solve_uncached(grid_tuple: tuple[tuple[int, ...], ...], finish_rule: str):
    data = _decode_cached(grid_tuple)
    if finish_rule not in INTERNAL_SETTINGS:
        raise ValueError('Unknown finish_rule')
    piece_color = {}
    for r in range(data['n']):
        for c in range(data['n']):
            piece_color[data['positions'][r][c]] = data['palette'][r][c]
    if finish_rule == 'highlight_hub':
        if not data['hub_is_unique']:
            raise ValueError('Highlight setting requires a unique adjacency hub')
        piece_color[data['hub_piece']] = 1
    elif finish_rule == 'highlight_largest':
        piece_color[data['largest_piece']] = 1
    elif finish_rule == 'highlight_key':
        piece_color[0] = 1
    output = [[piece_color[data['owner'][r][c]] for c in range(data['side'])]
              for r in range(data['side'])]
    return tuple(tuple(row) for row in output)


@lru_cache(maxsize=4096)
def _solve_cached(grid_tuple: tuple[tuple[int, ...], ...], finish_rule: str):
    return _solve_uncached(grid_tuple, finish_rule)


def solve(grid: Any, finish_rule: str = 'pack_only') -> list[list[int]]:
    g = checked_grid(grid)
    return [list(row) for row in _solve_cached(tuple(tuple(row) for row in g), finish_rule)]


def self_check(grid: Any) -> list[str]:
    try:
        data = _decode_data(grid)
    except (TypeError, ValueError, IndexError) as exc:
        return [str(exc)]
    errors = []
    if data['positions'][0][0] != 0:
        errors.append('palette-bearing piece must occupy the top-left position')
    return errors


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in CARDINAL:
            q = (r + dr, c + dc)
            if q in cells and q not in seen:
                seen.add(q); stack.append(q)
    return seen == cells


def _partition(side: int, rng: random.Random, n: int = 3):
    if n != 3 or side < 12:
        raise ValueError('Authoring sampler currently uses 3x3 piece layouts')
    a = max(5, (2 * side + 4) // 5)
    b = max(a + 4, (2 * side + 2) // 3)
    if b >= side - 3:
        b = side - 4
    cuts = (0, a, b, side)
    owner = [[0] * side for _ in range(side)]
    for r in range(side):
        rr = next(i for i in range(3) if cuts[i] <= r < cuts[i+1])
        for c in range(side):
            cc = next(i for i in range(3) if cuts[i] <= c < cuts[i+1])
            owner[r][c] = rr * 3 + cc
    palette_cells = {(1 + r, 1 + c) for r in range(3) for c in range(3)}
    protected = set(palette_cells)
    # Preserve the entire outer boundary so side-order interpretation is exact.
    protected |= {(0, c) for c in range(side)} | {(side-1, c) for c in range(side)}
    protected |= {(r, 0) for r in range(side)} | {(r, side-1) for r in range(side)}
    for _ in range(side * side * 3):
        r = rng.randrange(1, side - 1); c = rng.randrange(1, side - 1)
        if (r, c) in protected:
            continue
        dr, dc = rng.choice(CARDINAL)
        rr, cc = r + dr, c + dc
        src, dst = owner[r][c], owner[rr][cc]
        if src == dst:
            continue
        # Keep transfers local to neighboring logical cells; this stabilizes the
        # 3x3 topology while still creating irregular interlocking shapes.
        sr, sc, drg, dcg = src // 3, src % 3, dst // 3, dst % 3
        if abs(sr - drg) + abs(sc - dcg) != 1:
            continue
        source_cells = {(x, y) for x in range(side) for y in range(side) if owner[x][y] == src}
        if len(source_cells) <= 10:
            continue
        remaining = source_cells - {(r, c)}
        if not _connected(remaining):
            continue
        owner[r][c] = dst
    return owner, palette_cells


def _piece_shapes(owner: list[list[int]]):
    count = max(max(row) for row in owner) + 1
    return [set((r, c) for r, row in enumerate(owner) for c, v in enumerate(row) if v == i)
            for i in range(count)]


def _place_input(piece_shapes, palette, palette_cells, canvas_h, canvas_w, rng):
    full_shapes = [_normalize(shape) for shape in piece_shapes]
    colored: list[tuple[tuple[tuple[int, int], ...], dict[tuple[int, int], int]]] = []
    palette_origin = (1, 1)
    palette_map = {(palette_origin[0] + r, palette_origin[1] + c): palette[r][c]
                   for r in range(3) for c in range(3)}
    key_values = {cell: palette_map.get(cell, 1) for cell in full_shapes[0]}
    colored.append((full_shapes[0], key_values))
    source_colors = list(range(2, 10)); rng.shuffle(source_colors)
    for i, shape in enumerate(full_shapes[1:], 1):
        turns = rng.randrange(4)
        oriented = _rotations(shape)[turns % len(_rotations(shape))]
        color = source_colors[(i - 1) % len(source_colors)]
        colored.append((oriented, {cell: color for cell in oriented}))
    order = list(range(len(colored)))
    # Place larger bounding boxes first, but randomize equal sizes.
    rng.shuffle(order)
    order.sort(key=lambda i: -len(colored[i][0]))
    occupied_footprint: set[tuple[int, int]] = set()
    placements: dict[int, tuple[int, int]] = {}
    for i in order:
        shape = colored[i][0]
        ph = max(r for r, _ in shape) + 1; pw = max(c for _, c in shape) + 1
        choices = [(r, c) for r in range(canvas_h - ph + 1) for c in range(canvas_w - pw + 1)]
        rng.shuffle(choices)
        for r0, c0 in choices:
            footprint = {(r0 + r, c0 + c) for r, c in shape}
            halo = footprint | {(r + dr, c + dc) for r, c in footprint
                                for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                                if (dr or dc) and 0 <= r + dr < canvas_h and 0 <= c + dc < canvas_w}
            if footprint & occupied_footprint or any(q in occupied_footprint for q in halo - footprint):
                continue
            placements[i] = (r0, c0)
            occupied_footprint |= footprint
            break
        else:
            raise ValueError('Could not scatter all pieces')
    grid = [[0] * canvas_w for _ in range(canvas_h)]
    for i, (shape, values) in enumerate(colored):
        r0, c0 = placements[i]
        for r, c in shape:
            grid[r0 + r][c0 + c] = values[(r, c)]
    return grid


def _rng(seed: int, index: int, query: bool, attempt: int):
    tag = f'f560132c-v1|{seed}|{index}|{int(query)}|{attempt}'
    return random.Random(int.from_bytes(hashlib.sha256(tag.encode()).digest(), 'big'))


@lru_cache(maxsize=1024)
def _scene_tuple(seed: int, index: int, query: bool):
    if type(seed) is not int or not 0 <= seed < 2**63 or type(index) is not int or index < 0:
        raise ValueError('Invalid seed/index')
    if query:
        dims = ((23, 22, 15), (26, 24, 15), (29, 28, 18), (30, 30, 18))
        canvas_h, canvas_w, side = dims[index % 4]
    else:
        side = (15, 18, 15, 18, 15, 18)[index % 6]
        canvas_h = canvas_w = 24 if side == 15 else 27
    for attempt in range(200):
        rng = _rng(seed, index, query, attempt)
        owner, palette_cells = _partition(side, rng)
        shapes = _piece_shapes(owner)
        adjacency = _adjacency(owner)
        degrees = [len(x) for x in adjacency]
        hubs = [i for i, v in enumerate(degrees) if v == max(degrees)]
        areas = [len(s) for s in shapes]
        largest = max(range(9), key=lambda i: (areas[i], -i))
        if len(hubs) != 1 or hubs[0] == largest:
            continue
        palette_values = [0, 2, 3, 4, 5, 6, 7, 8, 9]
        rng.shuffle(palette_values)
        palette = tuple(tuple(palette_values[r*3:(r+1)*3]) for r in range(3))
        try:
            grid = _place_input(shapes, palette, palette_cells, canvas_h, canvas_w, rng)
            decoded = decode(grid)
            if decoded['hub_piece'] == decoded['largest_piece'] or not decoded['hub_is_unique']:
                continue
            # The exact-cover rule must recover the intended palette-positioned tiling.
            expected = [[palette[owner[r][c]//3][owner[r][c]%3] for c in range(side)] for r in range(side)]
            if solve(grid, 'pack_only') != expected:
                continue
            if solve(grid, 'highlight_hub') == solve(grid, 'highlight_largest'):
                continue
            return tuple(tuple(row) for row in grid)
        except ValueError:
            continue
    raise RuntimeError('Could not construct an identifiable jigsaw scene')


def scene(seed: int, index: int, *, query: bool = False, rng: random.Random | None = None) -> list[list[int]]:
    # The optional RNG parameter is accepted by the production entry point, but
    # source-stable episode construction intentionally derives its own stream.
    del rng
    return [list(row) for row in _scene_tuple(seed, index, query)]

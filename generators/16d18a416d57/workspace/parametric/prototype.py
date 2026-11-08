"""Opt-in parametric family for ARC task 16d18a416d57.

The default preserves the canonical largest-blue-object rule byte-for-byte.  The
alternate first finds that same largest object, uses its measured size as an
input-dependent key, then recolors the unique blue component whose size is three
smaller.
"""
from __future__ import annotations

CANONICAL_PROGRAM = "(rule! (let ((dummy 0)) (define (e8b-list< a b) (cond ((empty? a) #f) ((< (first a) (first b)) #t) ((> (first a) (first b)) #f) (else (e8b-list< (rest a) (rest b))))) (let ((largest (first (sort (filter (lambda (obj) (= (obj-color obj) 1)) (objects g 0)) (lambda (a b) (or (> (obj-size a) (obj-size b)) (and (= (obj-size a) (obj-size b)) (e8b-list< (obj-bbox a) (obj-bbox b))))))))) (paint-cells g (obj-cells largest) 7))))"

PARTNER_PROGRAM = "(rule! (let ((dummy 0)) (define (e8b-list< a b) (cond ((empty? a) #f) ((< (first a) (first b)) #t) ((> (first a) (first b)) #f) (else (e8b-list< (rest a) (rest b))))) (let* ((blue (filter (lambda (obj) (= (obj-color obj) 1)) (objects g 0))) (largest (first (sort blue (lambda (a b) (or (> (obj-size a) (obj-size b)) (and (= (obj-size a) (obj-size b)) (e8b-list< (obj-bbox a) (obj-bbox b)))))))) (key-size (obj-size largest)) (partner-size (- key-size 3)) (partner (first (filter (lambda (obj) (= (obj-size obj) partner-size)) blue)))) (paint-cells (paint-cells g (obj-cells largest) 7) (obj-cells partner) 2))))"

MODES = frozenset({"canonical", "size_keyed_partner"})


def validate_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    return {"mode": mode}


def rule_text(mode: str) -> str:
    if mode == "canonical":
        return CANONICAL_PROGRAM
    if mode == "size_keyed_partner":
        return PARTNER_PROGRAM
    raise ValueError(f"unknown mode {mode!r}")

from random import Random

_BASE_SHAPES = {
    2: ((0, 0), (0, 1)),
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (0, 1), (1, 0), (1, 1)),
    5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    7: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
}

_DEMO_SPECS = (
    (8, 10, 5),
    (9, 11, 7),
    (10, 12, 6),
    (14, 16, 5),
    (20, 22, 7),
    (26, 28, 6),
)
_QUERY_SPECS = (
    (12, 14, 6),
    (18, 21, 5),
    (24, 26, 7),
    (30, 30, 6),
)


def _normalize(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _variant(shape, rng: Random):
    cells = tuple(shape)
    if rng.randrange(2):
        cells = tuple((row, -col) for row, col in cells)
    for _ in range(rng.randrange(4)):
        cells = tuple((col, -row) for row, col in cells)
    return _normalize(cells)


def _components_4(grid, color=1):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (r + dr, c + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and grid[nxt[0]][nxt[1]] == color
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(tuple(sorted(cells)))
    return sorted(components, key=min)


def _input_grid(seed: int, kind: str, index: int, spec):
    height, width, largest_size = spec
    # Split and pair identity are mixed without depending on Python's randomized hash.
    salt = 0xD3 if kind == "demo" else 0x71
    rng = Random(seed * 1_000_003 + index * 97_409 + salt)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    sizes = [2, 3, 4, largest_size]
    rng.shuffle(sizes)
    anchors = ((0, 0), (0, width - 3), (height - 3, 0), (height - 3, width - 3))
    for size, (top, left) in zip(sizes, anchors):
        for row, col in _variant(_BASE_SHAPES[size], rng):
            grid[top + row][left + col] = 1

    # Neutral distractors exercise color filtering and make the 30x30 case a real
    # canvas stress rather than a padded four-object corner toy.  They are fully
    # preserved by both settings.
    phase = (seed + index * 13 + salt) % 17
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 and (row * 11 + col * 7 + phase) % 17 == 0:
                grid[row][col] = 8
    for row, col in (
        (0, width // 2),
        (height - 1, width // 2),
        (height // 2, 0),
        (height // 2, width - 1),
    ):
        if grid[row][col] == 0:
            grid[row][col] = 8
    return grid


def apply_mode(grid, mode: str):
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    components = _components_4(grid, 1)
    if len(components) != 4:
        raise ValueError("expected exactly four blue components")
    largest_size = max(map(len, components))
    largest = [component for component in components if len(component) == largest_size]
    if len(largest) != 1 or largest_size not in {5, 6, 7}:
        raise ValueError("expected one largest blue component of size 5, 6, or 7")
    out = [list(row) for row in grid]
    for row, col in largest[0]:
        out[row][col] = 7
    if mode == "size_keyed_partner":
        partner_size = largest_size - 3
        partners = [component for component in components if len(component) == partner_size]
        if len(partners) != 1:
            raise ValueError("expected one size-keyed partner component")
        for row, col in partners[0]:
            out[row][col] = 2
    return out


def _pair(seed: int, kind: str, index: int, spec, mode: str):
    grid = _input_grid(seed, kind, index, spec)
    return {"input": grid, "output": apply_mode(grid, mode)}


def generate_episode(seed: int, *, mode: str, demos: int, queries: int):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2**63-1")
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be exactly four")

    train = [_pair(seed, "demo", index, _DEMO_SPECS[index], mode) for index in range(demos)]
    test = [_pair(seed, "query", index, spec, mode) for index, spec in enumerate(_QUERY_SPECS)]
    return {"train": train, "test": test, "program_solution": rule_text(mode)}

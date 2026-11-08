"""Four stable packing directions over the canonical rectangular ARC domain.

Python outputs are label claims. Native qualification and audit.py execute the
matching protected Racket programs independently before retaining evidence.
"""
from __future__ import annotations

from pathlib import Path
import random

TASK_ID = '2a43e4f3a796'
VERSION = 'parametric-gravity-1.0.0'
DIRECTIONS = ('down', 'up', 'left', 'right')
DEFAULT = 'down'


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in {low}..{high}')


def _direction(direction):
    if type(direction) is not str or direction not in DIRECTIONS:
        raise ValueError('gravity must be down, up, left, or right')
    return direction


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError('grid must have 1..30 rows and columns')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError('grid must be rectangular with exact integer colors 0..9')


def transform(grid, direction=DEFAULT):
    """Stable line filtering and packing; no color-dependent ordering or barriers."""
    validate_grid(grid)
    _direction(direction)
    vertical = direction in ('down', 'up')
    lines = list(zip(*grid)) if vertical else grid
    packed = []
    for line in lines:
        values = [value for value in line if value != 0]
        padding = [0] * (len(line) - len(values))
        packed.append(padding + values if direction in ('down', 'right') else values + padding)
    return [list(row) for row in zip(*packed)] if vertical else packed


def program(direction=DEFAULT):
    """Return a complete native rule! program, with the default preserved exactly."""
    _direction(direction)
    if direction == DEFAULT:
        return Path(__file__).with_name('canonical.rkt').read_text()
    vertical = direction in ('down', 'up')
    lines = '(apply map list g)' if vertical else 'g'
    combined = '(append padding values)' if direction in ('down', 'right') else '(append values padding)'
    output = '(apply map list packed)' if vertical else 'packed'
    return f'''(rule! (lambda (g)
  (let* ((lines {lines})
         (packed
          (for/list ((line (in-list lines)))
            (let* ((values (filter (lambda (v) (not (= v 0))) line))
                   (padding (make-list (- (length line) (length values)) 0)))
              {combined}))))
    {output})))
'''


def _rng(seed, profile):
    return random.Random(f'{VERSION}:{seed}:{profile}')


def _cross(height, width, rng, *, dense):
    """Shared-gap row/column witnesses work in every gravity direction.

    The gray cells on both sides of the gap must move. The a,b,a prefix
    distinguishes stable order from reversal and either numerical sort. Both
    ends remain occupied, so translating a rigid line cannot remove its gap.
    """
    dominant, accent = rng.sample([c for c in range(1, 10) if c != 5], 2)
    grid = [[dominant if dense else 0 for _ in range(width)] for _ in range(height)]
    row = rng.randint(4, height - 4)
    col = rng.randint(4, width - 4)

    def strand(length, gap):
        line = [dominant] * length
        line[1] = accent
        line[gap - 1] = line[gap + 1] = 5
        line[gap] = 0
        return line

    grid[row] = strand(width, col)
    for r, value in enumerate(strand(height, row)):
        grid[r][col] = value
    return grid


def _scattered(height, width, rng, *, density):
    grid = [[rng.randrange(1, 10) if rng.random() < density else 0
             for _ in range(width)] for _ in range(height)]
    # Real foreground contacts all four boundaries; large grids are not pads
    # around a small repeated puzzle. Interior colors and gaps are independent.
    for r, c in ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)):
        grid[r][c] = rng.randrange(1, 10)
    return grid


def _skinny(rng, *, vertical):
    values = [rng.randrange(1, 10) if rng.random() < 0.55 else 0 for _ in range(30)]
    a, b = rng.sample([c for c in range(1, 10) if c != 5], 2)
    for index, value in {0: a, 1: b, 2: a, 9: 5, 10: 0, 11: 5, 20: 0, 29: a}.items():
        values[index] = value
    return [[value] for value in values] if vertical else [values]


def generate_inputs(seed, demos=3, queries=4):
    """Construct fixed independent prefixes; each admitted request has exact counts."""
    _integer('seed', seed, 0, 2**63 - 1)
    _integer('demos', demos, 2, 6)
    _integer('queries', queries, 1, 4)
    demonstrations = [
        _cross(9, 11, _rng(seed, 'dense-demo'), dense=True),
        _cross(13, 15, _rng(seed, 'sparse-demo'), dense=False),
        _scattered(7, 8, _rng(seed, 'free-demo-0'), density=0.4),
        _scattered(10, 12, _rng(seed, 'free-demo-1'), density=0.7),
        _scattered(16, 18, _rng(seed, 'free-demo-2'), density=0.2),
        _scattered(23, 25, _rng(seed, 'free-demo-3'), density=0.55),
    ]
    # Empty lines are lawful. Their absence from the constructive cross must
    # not imply a rule that invents foreground in an otherwise blank line.
    demonstrations[2][0] = [0] * 8
    for row in demonstrations[2]:
        row[-1] = 0
    tests = [
        _scattered(30, 30, _rng(seed, 'query-0'), density=0.62),
        _scattered(19, 27, _rng(seed, 'query-1'), density=0.18),
        _skinny(_rng(seed, 'query-2'), vertical=False),
        _skinny(_rng(seed, 'query-3'), vertical=True),
    ]
    # All ten profile shapes differ, proving within-episode input distinctness
    # constructively. No retries, duplicate fallbacks, or short returns occur.
    result = demonstrations[:demos] + tests[:queries]
    for grid in result:
        validate_grid(grid)
    return result

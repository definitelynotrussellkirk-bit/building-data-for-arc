"""Centered-bar grammar, independent Python oracle, and setting-blind sampler."""
from __future__ import annotations
from functools import lru_cache
import hashlib
import random

BACKGROUND, BASELINE = 8, 6
COLORS = (0, 1, 2, 3, 4, 5, 7, 9)


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def grid_check(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('Expected a 1..30 rectangular grid')
    if any(type(row) is not list or len(row) != len(grid[0]) or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError('Expected exact color integers and equal row lengths')


def paint(height, width, axis, bars, lengths=None):
    out = [[BASELINE if r == axis else BACKGROUND for _ in range(width)] for r in range(height)]
    for (left, right, color, old), length in zip(bars, lengths if lengths is not None else [b[3] for b in bars]):
        for r in range(axis - length // 2, axis - length // 2 + length):
            if not 0 <= r < height:
                raise ValueError('Bar does not fit the baseline')
            for c in range(left, right):
                out[r][c] = color
    return out


def analyze(grid):
    grid_check(grid)
    axes = [r for r, row in enumerate(grid) if BASELINE in row]
    if len(axes) != 1:
        raise ValueError('Exactly one magenta baseline row is required')
    axis = axes[0]; row = grid[axis]; bars = []; c = 0
    while c < len(row):
        color = row[c]
        if color == BACKGROUND:
            raise ValueError('Baseline cannot contain background gaps')
        if color == BASELINE:
            c += 1; continue
        start = c
        while c < len(row) and row[c] == color:
            c += 1
        occupied = [r for r, line in enumerate(grid) if line[start] == color]
        length = len(occupied)
        if min(occupied) != axis - length // 2 or max(occupied) != axis - length // 2 + length - 1:
            raise ValueError('Bars must be solid baseline-centered rectangles')
        bars.append((start, c, color, length))
    if not bars or paint(len(grid), len(row), axis, bars) != grid:
        raise ValueError('Off-axis noise, holes, or malformed bars')
    return axis, bars


def solve(grid, order):
    axis, bars = analyze(grid)
    lengths = sorted((b[3] for b in bars), reverse=order == 'descending')
    return paint(len(grid), len(grid[0]), axis, bars, lengths)


def rng_for(seed, stream):
    return random.Random(int.from_bytes(hashlib.sha256(f'bars-v1:{seed}:{stream}'.encode()).digest(), 'big'))


def sample_grid(seed, stream, profile):
    height, width, count = profile
    rng = rng_for(seed, stream)
    # The asymmetric vertical padding defeats a hardcoded mid-row baseline.
    axis = height // 2 if height % 2 == 0 else height // 2 - rng.randrange(2)
    if stream == 'train:0':
        axis = height // 2 - 1  # Teach the observed baseline, never infer it from canvas midpoint.
    max_length = min(2 * axis + 1, 2 * (height - axis))
    for attempt in range(256):
        widths = [1] * count
        occupied_width = min(width - count + 1, 3 * count - 1)
        while sum(widths) < occupied_width:
            choices = [i for i, v in enumerate(widths) if v < 4]
            widths[rng.choice(choices)] += 1
        gaps = [1] * (count - 1)
        slack = width - sum(widths) - sum(gaps)
        if height == 30:
            margins = [0, 0]
            for _ in range(slack): gaps[rng.randrange(len(gaps))] += 1
        else:
            spaces = [0] + gaps + [0]
            for _ in range(slack): spaces[rng.randrange(len(spaces))] += 1
            margins, gaps = [spaces[0], spaces[-1]], spaces[1:-1]
        if count == 8:
            lengths = [1, 6, 9, 14, 20, 20, 25, max_length]
        else:
            lengths = [rng.randint(1, max_length) for _ in range(count)]
            lengths[1] = lengths[0]  # Multiplicity is intentional, not a deduplicated rank.
            lengths[-1] = max_length
        rng.shuffle(lengths)
        if len(set(lengths)) < 2 or lengths in (sorted(lengths), sorted(lengths, reverse=True)):
            continue
        palette = rng.sample(COLORS, min(count, len(COLORS)))
        if count >= 5:
            palette[-1] = palette[0]  # Same color, distinct bar; never adjacent.
        bars = []; left = margins[0]
        for i in range(count):
            bars.append((left, left + widths[i], palette[i], lengths[i]))
            left += widths[i] + (gaps[i] if i < len(gaps) else 0)
        grid = paint(height, width, axis, bars)
        if height == 30 and sum(v != BACKGROUND for row in grid for v in row) < 250:
            continue
        return grid
    raise ValueError('Unable to construct a varied legal bar scene')


@lru_cache(maxsize=128)
def bank(seed):
    profiles = [(17,21,5),(30,30,8),(15,19,4),(21,25,6),(25,28,7),(11,15,3)]
    trains = [sample_grid(seed, f'train:{i}', p) for i,p in enumerate(profiles)]
    queries = [sample_grid(seed, f'query:{i}', p) for i,p in enumerate([(13,18,4),(19,23,5),(25,27,7),(30,30,8)])]
    rng_for(seed, 'presentation').shuffle(queries)
    return trains, queries

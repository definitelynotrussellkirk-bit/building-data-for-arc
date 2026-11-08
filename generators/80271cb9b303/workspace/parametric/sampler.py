"""Deterministic, label-free input banks for row-prefix continuation.

The first three training grids are constructive teaching templates.  All
variation preserves the left-to-right observed prefixes: only color
permutations and vertical reflections are applied to those templates.
"""

from __future__ import annotations

import hashlib
import json
import random


MAX_SEED = 2**63 - 1
MAX_DUPLICATE_ATTEMPTS = 64
_RNG_DOMAIN = "80271cb9b303-native-input-banks-v1"

# Each row specification is (row_index, primitive_motif, rightmost_nonzero).
_TEACHING_TEMPLATES = (
    (
        7,
        20,
        (
            (0, (0, 1, 2, 3), 5),
            (2, (1, 2, 3), 4),
            (4, (4, 5, 0), 4),
            (6, (6,), 3),
        ),
    ),
    (
        9,
        27,
        (
            (1, (1, 0, 2, 3, 4), 8),
            (3, (0, 1, 2, 3, 4, 5), 8),
            (6, (6, 7, 0, 8), 7),
            (8, (8, 9), 4),
        ),
    ),
    (
        11,
        30,
        (
            (0, (0, 1, 0, 2, 3, 4, 5), 10),
            (2, (1, 2, 3, 4, 0, 5, 6, 7), 9),
            (5, (1, 0, 2), 3),
            (7, (4, 0, 0, 5), 7),
            (10, (0, 6), 5),
        ),
    ),
)


def _local_rng(seed: int, split: str, slot: int, retry: int) -> random.Random:
    material = f"{_RNG_DOMAIN}|{seed}|{split}|{slot}|{retry}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _minimal_period(row: list[int], right: int) -> int:
    """Use the canonical finite-prefix test, including every observed zero."""
    for period in range(1, right + 2):
        if all(row[column] == row[column % period] for column in range(right + 1)):
            return period
    raise AssertionError("the complete observed prefix is always a period")


def _prefix_row(width: int, motif: tuple[int, ...], right: int) -> list[int]:
    if not motif or not 0 <= right < width - 1:
        raise ValueError("a row requires an observed prefix and a blank suffix")
    row = [motif[column % len(motif)] if column <= right else 0 for column in range(width)]
    actual_right = max((column for column, color in enumerate(row) if color), default=-1)
    if actual_right != right:
        raise ValueError("the specified right edge must be a nonzero cell")
    if _minimal_period(row, right) != len(motif):
        raise ValueError("the observed prefix does not identify the specified primitive period")
    return row


def _grid_from_rows(
    height: int,
    width: int,
    row_specs: tuple[tuple[int, tuple[int, ...], int], ...],
    rng: random.Random,
) -> list[list[int]]:
    grid = [[0] * width for _ in range(height)]
    occupied_rows: set[int] = set()
    for row_index, motif, right in row_specs:
        if not 0 <= row_index < height or row_index in occupied_rows:
            raise ValueError("row specifications must occupy distinct in-bounds rows")
        occupied_rows.add(row_index)
        grid[row_index] = _prefix_row(width, motif, right)

    palette = list(range(1, 10))
    rng.shuffle(palette)
    mapping = [0] + palette
    grid = [[mapping[color] for color in row] for row in grid]
    if rng.randrange(2):
        grid.reverse()
    return grid


def _marker_motif(period: int, mode: int, rng: random.Random) -> tuple[int, ...]:
    """Make a dense primitive motif with one unique marker and at most one zero.

    Seeing marker 1 at both marker_index and marker_index + period rules out
    every shorter finite-prefix period.  Other positions exclude that marker.
    """
    if period < 3:
        raise ValueError("random marker motifs require period at least three")
    marker_index = 1 if mode % 4 == 0 else 0
    motif = [rng.randrange(2, 10) for _ in range(period)]
    motif[marker_index] = 1
    if mode % 4 == 0:
        motif[0] = 0
    elif mode % 4 == 1:
        motif[-1] = 0
    elif mode % 4 == 2:
        motif[period // 2] = 0
    return tuple(motif)


def _query_profile(profile: int, rng: random.Random) -> list[list[int]]:
    if profile == 0:
        return _grid_from_rows(1, 9, ((0, (1, 2, 3), 4),), rng)
    if profile == 1:
        return _grid_from_rows(
            5,
            15,
            (
                (2, (0, 0, 1, 0), 6),
                (3, (2, 1, 1, 0), 9),
                (4, (2, 2, 1, 3), 9),
            ),
            rng,
        )
    if profile == 2:
        height, width = 16, 26
        active_rows = sorted([0, height - 1] + rng.sample(range(1, height - 1), 6))
        periods = list(range(3, 11))
        rng.shuffle(periods)
        specs = []
        for index, (row_index, period) in enumerate(zip(active_rows, periods)):
            motif = _marker_motif(period, index, rng)
            marker_index = motif.index(1)
            # Show the marker twice and leave more than one motif length blank.
            low = period + max(marker_index, 1)
            high = min(2 * period + 2, width - period - 2)
            candidates = [right for right in range(low, high + 1) if motif[right % period]]
            if not candidates:
                raise AssertionError("the dense query motif must have an admissible right edge")
            specs.append((row_index, motif, rng.choice(candidates)))
        return _grid_from_rows(height, width, tuple(specs), rng)
    if profile == 3:
        height = width = 30
        blank_rows = set(rng.sample(range(1, height - 1), 2))
        active_rows = [row for row in range(height) if row not in blank_rows]
        periods = [3 + index % 8 for index in range(len(active_rows))]
        rng.shuffle(periods)
        specs = []
        for index, (row_index, period) in enumerate(zip(active_rows, periods)):
            motif = _marker_motif(period, index, rng)
            candidates = [right for right in range(17, 24) if motif[right % period]]
            if not candidates:
                raise AssertionError("the dense stress motif must have an admissible right edge")
            # The first active row reaches column 22 or 23, rather than adding
            # empty columns solely to obtain the 30-column shape.
            right = max(candidates) if index == 0 else rng.choice(candidates)
            specs.append((row_index, motif, right))
        grid = _grid_from_rows(height, width, tuple(specs), rng)
        if sum(color != 0 for row in grid for color in row) < 200:
            raise AssertionError("the stress input must contain at least 200 occupied cells")
        return grid
    raise ValueError("unknown query profile")


def _validate_grid(grid: list[list[int]]) -> None:
    if not 1 <= len(grid) <= 30 or not 1 <= len(grid[0]) <= 30:
        raise AssertionError("bank grids must have dimensions in 1..30")
    width = len(grid[0])
    active = 0
    for row in grid:
        if len(row) != width or any(type(color) is not int or not 0 <= color <= 9 for color in row):
            raise AssertionError("bank grids must be rectangular ARC grids")
        right = max((column for column, color in enumerate(row) if color), default=-1)
        if right == -1:
            continue
        active += 1
        period = _minimal_period(row, right)
        if right < period or right >= width - 1:
            raise AssertionError("active rows must show a repeated residue and a blank suffix")
        if not any(row[column % period] for column in range(right + 1, width)):
            raise AssertionError("an active row must expose at least one continuation cell")
    if not active:
        raise AssertionError("bank grids must contain an active row")


def input_banks(seed: int) -> dict[str, list[list[list[int]]]]:
    """Return all six training inputs and four queries before any caller slicing.

    RNG streams are local to (seed, split, slot, retry).  The only retry is a
    bounded check against duplicate input grids across the complete bank.
    No setting, output label, or global random state participates in sampling.
    """
    if type(seed) is not int:
        raise TypeError("seed must be an integer, excluding bool")
    if not 0 <= seed <= MAX_SEED:
        raise ValueError("seed must be in 0..2**63-1")

    banks: dict[str, list[list[list[int]]]] = {"train": [], "test": []}
    seen: set[str] = set()
    for split, count in (("train", 6), ("test", 4)):
        for slot in range(count):
            for retry in range(MAX_DUPLICATE_ATTEMPTS):
                rng = _local_rng(seed, split, slot, retry)
                if split == "train" and slot < 3:
                    height, width, specs = _TEACHING_TEMPLATES[slot]
                    grid = _grid_from_rows(height, width, specs, rng)
                else:
                    profile = slot - 3 if split == "train" else slot
                    grid = _query_profile(profile, rng)
                _validate_grid(grid)
                identity = json.dumps(grid, separators=(",", ":"))
                if identity not in seen:
                    seen.add(identity)
                    banks[split].append(grid)
                    break
            else:
                raise RuntimeError(f"could not construct a unique {split} input at slot {slot} in 64 attempts")
    return banks

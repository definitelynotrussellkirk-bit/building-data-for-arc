"""Constructive, label-free banks for fixed and density-derived cyclic scans.

Every input includes the empty signature, every solo section, and every pair
of sections.  The shared layout is Hx19: four width-four panels separated by
three full-height color-3 columns.  No family module or labeler is imported.
"""

from __future__ import annotations

from collections import Counter
import hashlib
from itertools import permutations
import json
import random


MAX_SEED = 2**63 - 1
MAX_ATTEMPTS = 64
_DOMAIN = "9000d0ea6484-native-input-bank-v1"
_COLORS = (1, 2, 4, 5, 6, 7, 8, 9)
_STARTS = (0, 5, 10, 15)
_TIE_ORDER = (2, 3, 0, 1)
_MANDATORY = (0, 1, 2, 4, 8, 3, 5, 9, 6, 10, 12)
_CYCLIC_ORDERS = frozenset(
    tuple((start + direction * offset) % 4 for offset in range(4))
    for start in range(4) for direction in (1, -1)
)
_CANONICAL_COLOR_RANK = {9: 0, 4: 1, 8: 2, 5: 3}

# Cell values below are section-membership masks, not ARC colors.  Each panel
# touches all four rows and columns, but its true occupied-cell count differs.
# Four-neighbor component counts are [1,4,3,4], while cell counts are [9,4,7,6].
_D0 = (
    (2, 9, 13, 5),
    (12, 3, 0, 1),
    (1, 5, 6, 9),
    (8, 5, 4, 10),
)

_TRAIN_PROFILES = (
    ("unique_extremes_geometric_guards", 4, (9, 4, 7, 6)),
    ("tie_max_23_min_01", 4, (5, 5, 9, 9)),
    ("tie_max_13_min_02", 4, (5, 9, 5, 9)),
    ("mandatory_remaining_anchor_guard", 5, (7, 10, 6, 4)),
    ("moderate_partial_max_tie", 9, (20, 12, 20, 14)),
    ("tall_partial_min_tie", 12, (25, 30, 17, 17)),
)
_TEST_PROFILES = (
    ("minimum_complete_witness", 3, (4, 5, 4, 5)),
    ("moderate_unique_extremes", 7, (20, 13, 16, 8)),
    ("tall_unique_extremes", 18, (28, 44, 32, 36)),
    ("full_height_dense_stress", 30, (90, 70, 95, 80)),
)


def _palette_ok(colors: tuple[int, ...]) -> bool:
    numeric = tuple(sorted(range(4), key=lambda index: colors[index]))
    fixed = tuple(sorted(range(4), key=lambda index: (
        _CANONICAL_COLOR_RANK.get(colors[index], 100 + colors[index]), colors[index])))
    # The reverse numeric ordering is also noncyclic because the cyclic-order
    # set is closed under reversal.  Complete pair signatures expose each order.
    return numeric not in _CYCLIC_ORDERS and fixed not in _CYCLIC_ORDERS


_PALETTES = tuple(colors for colors in permutations(_COLORS, 4) if _palette_ok(colors))
_D0_PALETTES = tuple(
    colors for colors in _PALETTES
    if min(range(4), key=lambda index: colors[index]) in (2, 3)
    and max(range(4), key=lambda index: colors[index]) in (2, 3)
)


def _rng(seed: int, split: str, slot: int, retry: int) -> random.Random:
    raw = f"{_DOMAIN}|{seed}|{split}|{slot}|{retry}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _square_symmetry(rows: list[list[int]], transform: int) -> list[list[int]]:
    if transform >= 4:
        rows = [list(reversed(row)) for row in rows]
    for _ in range(transform % 4):
        rows = [list(row) for row in zip(*reversed(rows))]
    return rows


def _counted_masks(height: int, counts: tuple[int, ...], rng: random.Random,
                   *, full_boundary_cells: bool) -> list[int]:
    extras = [15, 15] if full_boundary_cells else []
    remaining = 4 * height - len(_MANDATORY) - len(extras)
    if remaining < 0:
        raise ValueError("height is too small for the complete witness set")
    random_masks = [0] * remaining
    for section, count in enumerate(counts):
        needed = count - 4 - len(extras)
        if not 0 <= needed <= remaining:
            raise ValueError("requested counts cannot coexist with the complete witness set")
        for position in rng.sample(range(remaining), needed):
            random_masks[position] |= 1 << section
    return [*_MANDATORY, *extras, *random_masks]


def _arrange(masks: list[int], height: int, rng: random.Random,
             *, full_boundary_cells: bool) -> list[list[int]]:
    masks = list(masks)
    fixed: dict[int, int] = {}
    if full_boundary_cells:
        for position in (0, 4 * height - 1):
            masks.remove(15)
            fixed[position] = 15
    nonempty = [mask for mask in masks if mask]
    empty_count = len(masks) - len(nonempty)
    rng.shuffle(nonempty)

    # Reserve genuine content in every aligned row and column.  This changes
    # positions only; the exact input-derived section counts remain unchanged.
    for column in range(4):
        if not any(position % 4 == column for position in fixed):
            fixed[4 * (column % height) + column] = nonempty.pop()
    for row in range(height):
        if not any(position // 4 == row for position in fixed):
            fixed[4 * row + rng.randrange(4)] = nonempty.pop()
    remaining = nonempty + [0] * empty_count
    rng.shuffle(remaining)
    flat = []
    for position in range(4 * height):
        flat.append(fixed[position] if position in fixed else remaining.pop())
    if remaining:
        raise AssertionError("layout did not consume exactly the specified masks")
    return [flat[4 * row:4 * row + 4] for row in range(height)]


def _components(rows: list[list[int]], section: int) -> int:
    unseen = {(r, c) for r, row in enumerate(rows) for c, mask in enumerate(row)
              if mask & (1 << section)}
    count = 0
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        count += 1
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
    return count


def _extreme(values: list[int], largest: bool) -> int:
    target = (max if largest else min)(values)
    return next(section for section in _TIE_ORDER if values[section] == target)


def _describe_masks(rows: list[list[int]], colors: tuple[int, ...]) -> dict:
    height = len(rows)
    flat = [mask for row in rows for mask in row]
    counts = [sum(bool(mask & (1 << section)) for mask in flat) for section in range(4)]
    occupied_rows = [sum(any(mask & (1 << section) for mask in row) for row in rows)
                     for section in range(4)]
    occupied_columns = [sum(any(rows[r][c] & (1 << section) for r in range(height)) for c in range(4))
                        for section in range(4)]
    bbox_areas = []
    for section in range(4):
        cells = [(r, c) for r, row in enumerate(rows) for c, mask in enumerate(row)
                 if mask & (1 << section)]
        bbox_areas.append((max(r for r, c in cells) - min(r for r, c in cells) + 1)
                         * (max(c for r, c in cells) - min(c for r, c in cells) + 1))
    return {
        "input_shape": [height, 19], "output_shape": [height, 4],
        "section_colors": list(colors), "section_counts": counts,
        "occupied_rows": occupied_rows, "occupied_columns": occupied_columns,
        "bbox_areas": bbox_areas, "components4": [_components(rows, section) for section in range(4)],
        "densest_section": _extreme(counts, True), "sparsest_section": _extreme(counts, False),
        "signature_histogram": {str(mask): count for mask, count in sorted(Counter(flat).items())},
        "nonzero_input_cells": sum(counts) + 3 * height,
        "nonzero_output_cells": sum(bool(mask) for mask in flat),
        "active_aligned_rows": sum(any(row) for row in rows),
        "boundary_contacts_without_dividers": {
            "top": any(rows[0]), "bottom": any(rows[-1]),
            "left": any(row[0] & 1 for row in rows),
            "right": any(row[3] & 8 for row in rows)},
    }


def _render(rows: list[list[int]], colors: tuple[int, ...]) -> list[list[int]]:
    grid = [[0] * 19 for _ in rows]
    for r, masks in enumerate(rows):
        for divider in (4, 9, 14):
            grid[r][divider] = 3
        for c, mask in enumerate(masks):
            for section, start in enumerate(_STARTS):
                if mask & (1 << section):
                    grid[r][start + c] = colors[section]
    return grid


def _candidate(seed: int, split: str, slot: int, retry: int):
    rng = _rng(seed, split, slot, retry)
    profiles = _TRAIN_PROFILES if split == "train" else _TEST_PROFILES
    name, height, target_counts = profiles[slot]
    full_boundary = split == "test" and slot == 3
    if split == "train" and slot == 0:
        transform = rng.randrange(8)
        rows = _square_symmetry([list(row) for row in _D0], transform)
        palette = rng.choice(_D0_PALETTES)
    else:
        transform = None
        masks = _counted_masks(height, target_counts, rng, full_boundary_cells=full_boundary)
        rows = _arrange(masks, height, rng, full_boundary_cells=full_boundary)
        palette = rng.choice(_PALETTES)
    spec = _describe_masks(rows, palette)
    if spec["section_counts"] != list(target_counts):
        raise AssertionError("constructed section counts differ from the profile")
    if not set(_MANDATORY) <= {mask for row in rows for mask in row}:
        raise AssertionError("the complete local witness set was lost")
    if spec["active_aligned_rows"] != height:
        raise AssertionError("each sampled row must contain actual panel content")
    if split == "train" and slot == 0:
        if (spec["occupied_rows"] != [4] * 4 or spec["occupied_columns"] != [4] * 4
                or spec["bbox_areas"] != [16] * 4 or spec["components4"] != [1, 4, 3, 4]):
            raise AssertionError("D0 lost a constructive geometry guard")
    grid = _render(rows, palette)
    spec.update({"profile_id": name, "seed": seed, "split": split,
                 "slot": slot, "retry": retry, "aligned_d4_transform": transform,
                 "input_sha256": hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()})
    if split == "train" and slot < 4:
        spec["minimum_complete_density_demonstrations"] = 4
    if split == "train" and slot == 3:
        spec["teaching_guard"] = (
            "The first three inputs do not select section1 as densest or section3 as sparsest. "
            "This fourth input selects both, refuting omission of those candidates. "
            "Retaining it as a held-out query also reproduces the three-demo support gap."
        )
    return grid, spec


def build_bank(seed: int) -> dict:
    """Return six train grids, four test grids, and input-only private specs.

    The full bank is constructed before callers slice it.  Each candidate has
    its own stable local RNG; the sole bounded retry avoids duplicate inputs.
    No setting, output label, global RNG state, or family import is involved.
    """
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer, excluding bool")
    if not 0 <= seed <= MAX_SEED:
        raise ValueError("seed must be in 0..2**63-1")
    result = {"train": [], "test": [], "specs": {"train": [], "test": []}}
    seen = set()
    for split, count in (("train", 6), ("test", 4)):
        for slot in range(count):
            for retry in range(MAX_ATTEMPTS):
                grid, spec = _candidate(seed, split, slot, retry)
                if spec["input_sha256"] not in seen:
                    seen.add(spec["input_sha256"])
                    result[split].append(grid)
                    result["specs"][split].append(spec)
                    break
            else:
                raise RuntimeError(f"could not construct a distinct {split} input at slot {slot} in 64 attempts")
    return result

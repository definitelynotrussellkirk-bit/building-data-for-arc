"""Native parametric family for db89dc496d45.

The default is the exact canonical largest-component crop.  The alternate keeps
that first inference as Step A, measures the winning component's input-dependent
cell count, then uses that count to select a different disconnected color before
cropping its union.  Every scene also contains a unique key+1 decoy so a protected
Racket counterfactual can show that the intermediate is causally necessary.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from pathlib import Path
from random import Random

_HERE = Path(__file__).resolve().parent
CANONICAL_PROGRAM = (_HERE / "canonical.rkt").read_text(encoding="utf-8")
SIZE_RELAY_PROGRAM = (_HERE / "largest_size_relay.rkt").read_text(encoding="utf-8")
WRONG_INTERMEDIATE_PROGRAM = (
    _HERE / "wrong_intermediate_plus_one.rkt"
).read_text(encoding="utf-8")

MODES = frozenset({"largest_component", "largest_size_relay"})

# The first two demonstrations deliberately put the relay at count ranks 2 and
# 4.  Thus no fixed frequency-rank selector can explain the minimum lesson.
_DEMO_SPECS = (
    (14, 16, 7, "rank2"),
    (20, 20, 10, "rank4"),
    (18, 20, 8, "rank3"),
    (22, 24, 11, "rank2"),
    (25, 27, 9, "rank4"),
    (28, 28, 12, "rank3"),
)
_QUERY_SPECS = (
    (18, 20, 9, "rank3"),
    (21, 23, 7, "rank4"),
    (26, 28, 11, "rank2"),
    (30, 30, 12, "stress"),
)

# A connected perimeter walk.  Prefixes 7..12 preserve interior zeros in their
# bounding boxes, so the canonical crop retains nontrivial shape information.
_PERIMETER_PATH = (
    (0, 0), (1, 0), (2, 0), (3, 0),
    (3, 1), (3, 2), (3, 3), (2, 3),
    (1, 3), (0, 3), (0, 2), (0, 1),
    (1, 1), (1, 2), (2, 2), (2, 1),
)


def validate_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    return {"mode": mode}


def rule_text(mode: str) -> str:
    if mode == "largest_component":
        return CANONICAL_PROGRAM
    if mode == "largest_size_relay":
        return SIZE_RELAY_PROGRAM
    raise ValueError(f"unknown mode {mode!r}")


def _normalize(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _shape(size: int, rng: Random):
    if type(size) is not int or not 1 <= size <= 12:
        raise ValueError(f"component size must be 1..12, got {size!r}")
    cells = tuple(_PERIMETER_PATH[:size])
    if rng.randrange(2):
        cells = tuple((row, -col) for row, col in cells)
    for _ in range(rng.randrange(4)):
        cells = tuple((col, -row) for row, col in cells)
    return _normalize(cells)


def _axis_positions(length: int):
    if length < 4:
        raise ValueError("canvas axis must be at least four cells")
    count = (length + 1) // 5
    if count < 2:
        count = 2
    positions = [index * 5 for index in range(count)]
    positions[-1] = length - 4
    if any(b - a < 5 for a, b in zip(positions, positions[1:])):
        raise ValueError(f"cannot place separated 4-cell regions on axis {length}")
    return positions


def _slots(height: int, width: int):
    return [
        (top, left)
        for top in _axis_positions(height)
        for left in _axis_positions(width)
    ]


def _split_total(total: int, max_part: int, *, minimum_parts: int = 1):
    parts = max(minimum_parts, (total + max_part - 1) // max_part)
    if parts > total:
        raise ValueError("cannot split total into positive parts")
    base, remainder = divmod(total, parts)
    result = [base + (index < remainder) for index in range(parts)]
    if not result or min(result) < 1 or max(result) > max_part:
        raise ValueError((total, max_part, minimum_parts, result))
    return result


def _profile_totals(key: int, profile: str):
    if profile == "rank2":
        return key - 1, key - 3
    if profile == "rank4":
        return key + 3, key + 2
    if profile == "rank3":
        return key + 3, key - 1
    if profile == "stress":
        return 3 * key - 1, 2 * key - 2
    raise ValueError(f"unknown profile {profile!r}")


def _choose_colors(seed: int, ordinal: int, profile: str):
    """Choose five colors while constructively varying numeric shortcuts."""
    rng = Random(seed * 1_000_003 + ordinal * 104_729 + 0xC0104)
    colors = list(range(1, 10))
    source = rng.choice(colors)
    non_source = [color for color in colors if color != source]

    if profile == "rank2":
        relay = min(non_source)
    elif profile in {"rank4", "stress"}:
        relay = max(non_source)
    else:
        middle = [color for color in non_source if min(non_source) < color < max(non_source)]
        relay = rng.choice(middle)

    candidates = [color for color in non_source if color != relay]
    rng.shuffle(candidates)
    decoy, extra_a, extra_b = candidates[:3]
    return source, relay, decoy, extra_a, extra_b


def _components_4(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for start_r in range(height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = row + dr, col + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append((color, cells))
    return result


def _crop_original(grid, cells):
    r0 = min(row for row, _ in cells)
    r1 = max(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    c1 = max(col for _, col in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _crop_color_mask(grid, color: int):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    if not cells:
        return [[0]]
    r0 = min(row for row, _ in cells)
    r1 = max(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    c1 = max(col for _, col in cells)
    return [
        [color if grid[row][col] == color else 0 for col in range(c0, c1 + 1)]
        for row in range(r0, r1 + 1)
    ]


def analyze(grid):
    components = _components_4(grid)
    if len(components) < 2:
        raise ValueError("expected multiple nonzero components")
    largest_size = max(len(cells) for _, cells in components)
    largest = [item for item in components if len(item[1]) == largest_size]
    if len(largest) != 1:
        raise ValueError("expected a unique largest component")
    source_color, source_cells = largest[0]
    counts = Counter(value for row in grid for value in row if value)
    relay_colors = [
        color
        for color, count in counts.items()
        if color != source_color and count == largest_size
    ]
    if len(relay_colors) != 1:
        raise ValueError("expected one non-source color keyed by largest size")
    plus_one = [
        color
        for color, count in counts.items()
        if color != source_color and count == largest_size + 1
    ]
    if len(plus_one) != 1:
        raise ValueError("expected one non-source key+1 decoy")
    return {
        "components": components,
        "source_color": source_color,
        "source_cells": source_cells,
        "key": largest_size,
        "relay_color": relay_colors[0],
        "wrong_color": plus_one[0],
        "counts": counts,
    }


def apply_mode(grid, mode: str):
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    info = analyze(grid)
    if mode == "largest_component":
        return _crop_original(grid, info["source_cells"])
    return _crop_color_mask(grid, info["relay_color"])


def apply_wrong_intermediate(grid):
    return _crop_color_mask(grid, analyze(grid)["wrong_color"])


def _role_parts(seed: int, ordinal: int, key: int, profile: str):
    source, relay, decoy, extra_a, extra_b = _choose_colors(seed, ordinal, profile)
    source_fragment = 1 + ((seed + ordinal) & 1)
    extra_a_total, extra_b_total = _profile_totals(key, profile)
    max_part = key - 2
    relay_parts = _split_total(
        key, max_part, minimum_parts=3 if profile in {"rank3", "stress"} else 2
    )
    decoy_parts = _split_total(key + 1, max_part, minimum_parts=2)
    extra_a_parts = _split_total(extra_a_total, max_part)
    extra_b_parts = _split_total(extra_b_total, max_part)
    return {
        "colors": {
            "source": source,
            "relay": relay,
            "decoy": decoy,
            "extra_a": extra_a,
            "extra_b": extra_b,
        },
        "parts": {
            "source": [key],
            "source_fragment": [source_fragment],
            "relay": relay_parts,
            "decoy": decoy_parts,
            "extra_a": extra_a_parts,
            "extra_b": extra_b_parts,
        },
    }


def _distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _take_farthest(available, origin):
    return max(available, key=lambda slot: (_distance(slot, origin), slot))


def _allocate_role_slots(slots, part_counts, rng: Random, *, stress: bool):
    available = list(slots)
    assignments = {name: [] for name in part_counts}

    def take(slot):
        available.remove(slot)
        return slot

    if stress:
        relay_slots = [min(available), max(available)]
        for slot in relay_slots[: part_counts["relay"]]:
            assignments["relay"].append(take(slot))
        while len(assignments["relay"]) < part_counts["relay"]:
            assignments["relay"].append(take(_take_farthest(available, relay_slots[-1])))
        center = min(
            available,
            key=lambda slot: (
                abs(slot[0] - max(s[0] for s in slots) / 2)
                + abs(slot[1] - max(s[1] for s in slots) / 2),
                slot,
            ),
        )
        assignments["source"].append(take(center))
    else:
        rng.shuffle(available)
        assignments["source"].append(take(available[0]))
        first = take(available[0])
        assignments["relay"].append(first)
        if part_counts["relay"] > 1:
            assignments["relay"].append(take(_take_farthest(available, first)))
        while len(assignments["relay"]) < part_counts["relay"]:
            assignments["relay"].append(take(available[0]))

    source_slot = assignments["source"][0]
    assignments["source_fragment"].append(take(_take_farthest(available, source_slot)))

    if part_counts["decoy"]:
        first = take(available[0])
        assignments["decoy"].append(first)
        while len(assignments["decoy"]) < part_counts["decoy"]:
            assignments["decoy"].append(take(_take_farthest(available, first)))

    for name in ("extra_a", "extra_b"):
        rng.shuffle(available)
        while len(assignments[name]) < part_counts[name]:
            assignments[name].append(take(available[0]))
    return assignments


def _paint_shape(grid, slot, shape, color, rng: Random):
    height, width = len(grid), len(grid[0])
    top, left = slot
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    max_top = height - 4
    max_left = width - 4
    if top == 0:
        row_shift = 0
    elif top == max_top:
        row_shift = 4 - shape_h
    else:
        row_shift = rng.randrange(5 - shape_h)
    if left == 0:
        col_shift = 0
    elif left == max_left:
        col_shift = 4 - shape_w
    else:
        col_shift = rng.randrange(5 - shape_w)
    for dr, dc in shape:
        row = top + row_shift + dr
        col = left + col_shift + dc
        if grid[row][col] != 0:
            raise RuntimeError("constructive slot overlap")
        grid[row][col] = color


def _build_input(seed: int, kind: str, index: int, spec):
    height, width, key, profile = spec
    ordinal = index if kind == "demo" else len(_DEMO_SPECS) + index
    rng = Random(seed * 2_000_003 + ordinal * 130_363 + 0x5A17E)
    roles = _role_parts(seed, ordinal, key, profile)
    part_counts = {name: len(parts) for name, parts in roles["parts"].items()}
    slots = _slots(height, width)
    if sum(part_counts.values()) > len(slots):
        raise ValueError((spec, part_counts, len(slots)))
    role_slots = _allocate_role_slots(
        slots, part_counts, rng, stress=(profile == "stress")
    )
    grid = [[0 for _ in range(width)] for _ in range(height)]

    for role in ("source", "source_fragment", "relay", "decoy", "extra_a", "extra_b"):
        color_role = "source" if role == "source_fragment" else role
        color = roles["colors"][color_role]
        for size, slot in zip(roles["parts"][role], role_slots[role], strict=True):
            _paint_shape(grid, slot, _shape(size, rng), color, rng)

    info = analyze(grid)
    if info["key"] != key:
        raise RuntimeError((key, info["key"]))
    expected_colors = roles["colors"]
    if info["source_color"] != expected_colors["source"]:
        raise RuntimeError("source color drift")
    if info["relay_color"] != expected_colors["relay"]:
        raise RuntimeError("relay color drift")
    if info["wrong_color"] != expected_colors["decoy"]:
        raise RuntimeError("decoy color drift")
    return grid


def _pair(seed: int, kind: str, index: int, spec, mode: str):
    grid = _build_input(seed, kind, index, spec)
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

    train = [
        _pair(seed, "demo", index, _DEMO_SPECS[index], mode)
        for index in range(demos)
    ]
    test = [
        _pair(seed, "query", index, spec, mode)
        for index, spec in enumerate(_QUERY_SPECS)
    ]
    return {
        "train": deepcopy(train),
        "test": deepcopy(test),
        "program_solution": rule_text(mode),
    }

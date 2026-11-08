"""Task-local translated-motif lessons; Racket supplies the authoritative labels.

Python labels are claims for the native worker to verify, never an admission.
The production generator and canonical reference are not changed here.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import random

SETTINGS = ("linear", "bounce")
HOME = Path(__file__).resolve().parent


def _integer(value, name, low, high):
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"edge"}:
        raise ValueError("settings must contain exactly the edge parameter")
    if type(settings["edge"]) is not str or settings["edge"] not in SETTINGS:
        raise ValueError("edge must be linear or bounce")
    return settings["edge"]


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(c) is not int or not 0 <= c <= 9 for c in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def detect(grid):
    """The canonical smallest-period/translation detector, including fallback."""
    grid = _grid(grid)
    height, width = len(grid), len(grid[0])
    first = next((c for c, value in enumerate(grid[0]) if value), None)
    for period in range(1, height):
        later = next((c for c, value in enumerate(grid[period]) if value), None)
        if first is None or later is None:
            continue
        shift = later - first
        if all(grid[r][c] == grid[r + period][c + shift]
               if 0 <= c + shift < width else grid[r][c] == 0
               for r in range(height - period) for c in range(width)):
            return period, shift
    return height, 0


def describe(grid):
    """Private input-derived intermediate used by continuation and audits."""
    grid = _grid(grid)
    period, shift = detect(grid)
    occupied = [c for row in grid[:period] for c, value in enumerate(row) if value]
    left, right = (min(occupied), max(occupied)) if occupied else (0, 0)
    width = len(grid[0])
    span = width - (right - left + 1)
    distance = span - left if shift > 0 else left
    return {"height": len(grid), "width": width, "period": period,
            "shift": shift, "left": left, "right": right, "span": span,
            "first_reflection_block": (distance // abs(shift) + 1 if shift else None)}


def _fold(position, span):
    if span == 0:
        return 0
    phase = position % (2 * span)
    return min(phase, 2 * span - phase)


def solve(grid, mode="linear"):
    """Python claim implementation. Native qualification independently executes Racket."""
    if type(mode) is not str or mode not in SETTINGS:
        raise ValueError("mode must be linear or bounce")
    facts = describe(grid)
    width, period, shift = facts["width"], facts["period"], facts["shift"]
    output = [[0] * width for _ in range(width)]
    for r, row in enumerate(output):
        offset = (r // period) * shift
        if mode == "bounce":
            offset = _fold(facts["left"] + offset, facts["span"]) - facts["left"]
        for c in range(width):
            source = c - offset
            if 0 <= source < width:
                row[c] = grid[r % period][source]
    return output


def program(settings):
    mode = _setting(settings)
    name = "canonical.rkt" if mode == "linear" else "bounce.rkt"
    return (HOME / name).read_text(encoding="utf-8")


def _rng(seed, split, index, attempt):
    digest = hashlib.sha256(f"3031e2ee53d1-edge-v1|{seed}|{split}|{index}|{attempt}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _motif(period, size, shift, rng):
    """Different row lengths expose phase; later rows own the forward extreme."""
    full = set(range(size))
    if period == 1:
        rows = [full]
    else:
        front = size - 1 if shift >= 0 else 0
        rows = [full - {front}, full]
        if period == 3:
            rows.append(full - {0, size - 1})
    # Coherent repeated fragments, not unrelated label-breaking noise. These
    # gaps vary topology while retaining the same shared period and drift.
    if size >= 9 and rng.randrange(3) == 0:
        gap = size // 2
        rows = [row - {gap} for row in rows]
    return rows


def _draw(seed, split, index, attempt=0):
    rng = _rng(seed, split, index, attempt)
    sign = rng.choice((-1, 1))
    dense = split == "test" and index == 3
    if split == "train":
        profiles = (
            # A partial period makes restarting phase at the input boundary
            # observably wrong even in the minimum two-demo lesson.
            (rng.choice((12, 16, 20)), 2, 2, 5),
            (rng.choice((13, 19, 25)), 3, 1, rng.choice((6, 7))),
            (rng.choice((11, 17, 23)), 1, 0, rng.choice((4, 5))),
            (rng.choice((12, 16, 20)), 1, 1, 4),
            (rng.choice((13, 19, 25)), 2, 1, rng.choice((4, 5))),
            (rng.choice((11, 17, 23)), 3, 1, rng.choice((6, 7))),
        )
        width, period, magnitude, height = profiles[index]
        # Both signs are taught even at the minimum demonstration count.
        sign = 1 if (seed % 2 == 0) == (index % 2 == 0) else -1
    else:
        profiles = (
            (rng.choice((10, 14)), 1, 1, 4),
            (rng.choice((18, 22)), 2, 2, rng.choice((6, 7))),
            (26, 3, 0 if seed % 4 == 0 else 1, rng.choice((9, 10))),
            (30, 3, 2, 18),
        )
        width, period, magnitude, height = profiles[index]
    shift = sign * magnitude
    if dense:
        size = rng.randint(17, 19)
        span = width - size
        margin = rng.randint(1, 3)
        anchor = margin if sign > 0 else span - margin
        distance = span - anchor if sign > 0 else anchor
        height = (distance // magnitude + 1) * period
    elif magnitude == 0:
        size = rng.randint(max(2, period + 1), max(3, width // 2))
        anchor = rng.randint(0, width - size)
    else:
        last_seen = (height - 1) // period
        last_output = (width - 1) // period
        min_distance = last_seen * magnitude
        # Odd distance at speed 2 guarantees visible overshoot, not exact-hit-only
        # lessons on which clamping could masquerade as reflection.
        reserve = min_distance + (1 if magnitude == 2 else 0)
        max_size = min(width - reserve, max(period + 2, 2 * width // 3))
        min_size = max(period + 2, magnitude + 1)
        size = rng.randint(min_size, max_size)
        span = width - size
        max_distance = min(span, last_output * magnitude - 1)
        distances = [d for d in range(min_distance, max_distance + 1)
                     if magnitude != 2 or d % 2 == 1]
        if not distances:
            raise AssertionError("constructive reflection profile has no lawful anchor")
        distance = rng.choice(distances)
        anchor = span - distance if sign > 0 else distance
    masks = _motif(period, size, shift, rng)
    color = rng.randint(1, 9)
    grid = [[0] * width for _ in range(height)]
    for r, row in enumerate(grid):
        offset = anchor + (r // period) * shift
        # Full envelope, not merely the occupied last phase, must fit before
        # reflection. This also protects partially observed final periods.
        if not 0 <= offset <= width - size:
            raise AssertionError("visible prefix crosses a full-motif boundary")
        for c in masks[r % period]:
            row[c + offset] = color
    if detect(grid) != (period, shift):
        raise AssertionError("constructed motif does not expose the intended primitive period")
    return grid


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    mode = _setting(settings)
    episode = {"train": [], "test": [], "program_solution": program(settings),
               "settings": dict(settings), "seed": seed}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            for attempt in range(16):
                grid = _draw(seed, split, index, attempt)
                identity = tuple(tuple(row) for row in grid)
                if identity not in seen:
                    break
            else:
                raise ValueError("bounded unique-input construction exhausted")
            seen.add(identity)
            output = solve(grid, mode)
            if output[:len(grid)] != grid:
                raise AssertionError("continuation rewrote its observed prefix")
            episode[split].append({"input": grid, "output": output})
    # A direct finite-family assertion, not a claim of universal uniqueness.
    rivals = [candidate for candidate in SETTINGS
              if all(solve(pair["input"], candidate) == pair["output"]
                     for pair in episode["train"])]
    if rivals != [mode]:
        raise ValueError("constructive demonstrations fail to identify the edge setting")
    return episode


def public_challenge(episode, query_index=0):
    """One model-visible turn; future inputs/counts/settings remain private."""
    _integer(query_index, "query_index", 0, len(episode["test"]) - 1)
    return {"train": [{"input": deepcopy(_grid(pair["input"])),
                       "output": deepcopy(_grid(pair["output"]))}
                      for pair in episode["train"]],
            "test": [{"input": deepcopy(_grid(episode["test"][query_index]["input"]))}]}


def _public_support():
    # Resolve the helper in this checkout (or its staged runtime), never an
    # unrelated same-named module already present in another adapter's cache.
    for parent in HOME.parents:
        for candidate in (parent / "shared/runtime/reviewer_support.py",
                          parent / "reviewer_support.py"):
            if candidate.is_file():
                spec = importlib.util.spec_from_file_location("_3031_public_support", candidate)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
    raise FileNotFoundError("same-checkout reviewer_support.py not found")


def public_id(challenge):
    return _public_support().public_challenge_id(challenge)

"""Task-local boundary-mode prototype for ARC task 56072bfdb820.

The production generator and canonical authority remain pinned to clipping.
This bounded prototype selects exactly one episode-level parameter:
``boundary_mode`` is either ``clip`` (canonical/default) or ``wrap``.  The
input grammar is unchanged.  Only proposed color-5/color-8 diamonds that fall
outside the 3x3 meta-grid are handled differently.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from itertools import combinations
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root

TASK_ID = "56072bfdb820"
PROTOTYPE_VERSION = "1.0.0"
STATUS = "proposed task-local prototype; not production-approved"
ROOT = find_root(__file__)
PARAMETERS = {
    "boundary_mode": {
        "allowed": ("clip", "wrap"),
        "default": "clip",
        "selected_once_per_episode": True,
    }
}

_DIAMOND = ((0, 1), (1, 0), (1, 2), (2, 1))
_TILES = tuple((row, col) for row in range(3) for col in range(3))
_PAIRS = tuple(combinations(_TILES, 2))
_AUTO = object()

# This block occurs exactly once in the pinned canonical authority.  Requiring
# an exact match makes a future canonical edit fail closed rather than silently
# producing a variant of a different rule.
_CLIP_ITEMS_BLOCK = """(items (append symbols
                                       (filter (lambda (e)
                                                 (and
                                                   (>= (first e) 0)
                                                   (< (first e) 3)
                                                   (>= (second e) 0)
                                                   (< (second e) 3)))
                                               extras)))"""
_WRAP_ITEMS_BLOCK = """(items (append symbols
                                       (map (lambda (e)
                                              (list (modulo (first e) 3)
                                                    (modulo (second e) 3)
                                                    (third e)))
                                            extras)))"""


def _validate_mode(boundary_mode: str) -> None:
    if type(boundary_mode) is not str or boundary_mode not in PARAMETERS["boundary_mode"]["allowed"]:
        raise ValueError("boundary_mode must be exactly 'clip' or 'wrap'")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be a Python int")


def canonical_record(*, root: Path | str = ROOT) -> dict[str, Any]:
    """Return the single canonical ledger row for this task."""
    matches = []
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                matches.append(record)
    if not matches:
        raise ValueError(f"missing canonical record for {TASK_ID}")
    programs = {record.get("program_solution") for record in matches}
    if len(programs) != 1:
        raise ValueError(
            f"canonical variants disagree on program authority for {TASK_ID}"
        )
    return next(
        (record for record in matches if record.get("content_hash") == TASK_ID),
        matches[0],
    )


def racket_program(boundary_mode: str = "clip", *, root: Path | str = ROOT) -> str:
    """Materialize the exact program for one declared parameter setting."""
    _validate_mode(boundary_mode)
    canonical = canonical_record(root=root)["program_solution"]
    if canonical.count(_CLIP_ITEMS_BLOCK) != 1:
        raise ValueError("canonical clipping anchor changed; prototype requires review")
    if boundary_mode == "clip":
        return canonical
    return canonical.replace(_CLIP_ITEMS_BLOCK, _WRAP_ITEMS_BLOCK, 1)


def choose_boundary_mode(seed: int) -> str:
    """Select one hidden setting deterministically, exactly once per episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:boundary_mode".encode()).digest()
    allowed = PARAMETERS["boundary_mode"]["allowed"]
    return allowed[digest[0] % len(allowed)]


def _base_grid() -> list[list[int]]:
    grid = [[7] * 11 for _ in range(11)]
    for row in (3, 7):
        grid[row] = [6] * 11
    for col in (3, 7):
        for row in range(11):
            grid[row][col] = 6
    return grid


def _put_diamond(grid: list[list[int]], tile: tuple[int, int], color: int) -> None:
    row0, col0 = tile[0] * 4, tile[1] * 4
    for dr, dc in _DIAMOND:
        grid[row0 + dr][col0 + dc] = color


def input_for_pair(pair_index: int) -> list[list[int]]:
    if type(pair_index) is not int or not 0 <= pair_index < len(_PAIRS):
        raise ValueError("pair_index must be an integer in 0..35")
    grid = _base_grid()
    for tile in _PAIRS[pair_index]:
        _put_diamond(grid, tile, 2)
    return grid


def _raw_extras(pair: tuple[tuple[int, int], tuple[int, int]]) -> tuple[tuple[int, int, int], ...]:
    (r1, c1), (r2, c2) = pair
    if c1 == c2:
        row, col = min(r1, r2) - 1, c1
        return ((row, col - 1, 5), (row, col + 1, 8))
    if r1 == r2:
        row, col = r1, min(c1, c2) - 1
        return ((row - 1, col, 8), (row + 1, col, 5))
    if c2 < c1:
        return ((r2, c2 - 1, 8), (r2 + 1, c2, 5))
    return ((r2, c2 + 1, 8), (r2 + 1, c2, 5))


def _symbols(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    if (
        not isinstance(grid, list)
        or len(grid) != 11
        or any(not isinstance(row, list) or len(row) != 11 for row in grid)
    ):
        raise ValueError("grid must be an 11x11 list of lists")
    symbols: list[tuple[int, int, int]] = []
    for tile_row, tile_col in _TILES:
        row0, col0 = tile_row * 4, tile_col * 4
        values = [
            grid[row0 + dr][col0 + dc]
            for dr in range(3)
            for dc in range(3)
            if grid[row0 + dr][col0 + dc] not in (6, 7)
        ]
        if values:
            symbols.append((tile_row, tile_col, values[0]))
    return symbols


def apply_python(grid: list[list[int]], boundary_mode: str = "clip") -> list[list[int]]:
    """Independent Python mirror of the materialized two-setting rule family."""
    _validate_mode(boundary_mode)
    symbols = _symbols(grid)
    if any(color != 2 for _, _, color in symbols):
        return [[7] * 16 for _ in range(16)]
    twos = tuple((row, col) for row, col, color in symbols if color == 2)
    if len(twos) != 2:
        raise ValueError(f"expected exactly two color-2 symbols, got {len(twos)}")

    raw = _raw_extras((twos[0], twos[1]))
    if boundary_mode == "clip":
        extras = tuple(
            item for item in raw
            if 0 <= item[0] < 3 and 0 <= item[1] < 3
        )
    else:
        extras = tuple((row % 3, col % 3, color) for row, col, color in raw)

    # The Racket authority appends extras after observed symbols and uses
    # find-first, so observed color-2 diamonds win any wrapped collision.
    lookup: dict[tuple[int, int], int] = {}
    for row, col, color in (*symbols, *extras):
        lookup.setdefault((row, col), color)

    output = _base_grid()
    for tile, color in lookup.items():
        _put_diamond(output, tile, color)
    return output


def _distinguishing_pair_indices() -> tuple[int, ...]:
    return tuple(
        index for index in range(len(_PAIRS))
        if apply_python(input_for_pair(index), "clip")
        != apply_python(input_for_pair(index), "wrap")
    )


def _episode_indices(seed: int, count: int) -> tuple[int, ...]:
    candidates = _distinguishing_pair_indices()
    if len(candidates) < count:
        raise ValueError("not enough boundary-distinguishing pair placements")
    digest = hashlib.sha256(f"{TASK_ID}:{PROTOTYPE_VERSION}:{seed}:pairs".encode()).digest()
    offset = int.from_bytes(digest[:8], "big") % len(candidates)
    rotated = candidates[offset:] + candidates[:offset]
    return tuple(rotated[:count])


def generate_episode(
    seed: int,
    *,
    boundary_mode: str | object = _AUTO,
    root: Path | str = ROOT,
    train_count: int = 3,
    query_count: int = 1,
) -> dict[str, Any]:
    """Build one complete private episode with one fixed hidden parameter."""
    _validate_seed(seed)
    if boundary_mode is _AUTO:
        selected = choose_boundary_mode(seed)
    else:
        _validate_mode(boundary_mode)
        selected = boundary_mode
    if type(train_count) is not int or train_count < 1:
        raise ValueError("train_count must be a positive integer")
    if type(query_count) is not int or query_count < 1:
        raise ValueError("query_count must be a positive integer")

    indices = _episode_indices(seed, train_count + query_count)
    rows = []
    for pair_index in indices:
        grid = input_for_pair(pair_index)
        rows.append({
            "input": grid,
            "output": apply_python(grid, selected),
            "pair_index": pair_index,
        })

    return {
        "schema": "56072bfdb820-boundary-mode-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter_draw_count": 1,
        "parameter": {"boundary_mode": selected},
        "program": racket_program(selected, root=root),
        "train": rows[:train_count],
        "test": rows[train_count:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return model-visible demonstrations and inputs, masking all query labels."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }

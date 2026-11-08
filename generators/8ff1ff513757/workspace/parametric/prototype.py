"""Parametric family for row compression with a post-compression contact relay.

The canonical setting removes all-zero rows.  The alternative first performs
that exact compression, then recolors every nonzero cell that has a vertical
nonzero neighbor in the compressed intermediate.  Because source rows are
separated by blank rows, those contacts are created by step A.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Callable

TASK_ID = "8ff1ff513757"
PARAMETER = "finish"
SETTINGS = ("compress_only", "mark_vertical_contacts")
DEFAULT = {PARAMETER: SETTINGS[0]}
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1

_HOME = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    SETTINGS[0]: _HOME / "canonical.rkt",
    SETTINGS[1]: _HOME / "mark_vertical_contacts.rkt",
}

# height, width, active-row count, density fraction
_TRAIN_PROFILES = (
    (8, 8, 3, 0.50),
    (10, 12, 4, 0.50),
    (12, 15, 5, 0.47),
    (16, 18, 6, 0.50),
    (20, 22, 5, 0.55),
    (24, 26, 6, 0.56),
)
_QUERY_PROFILES = (
    (9, 11, 3, 0.55),
    (15, 20, 4, 0.55),
    (24, 28, 5, 0.56),
    (30, 30, 6, 0.56),
)


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _finish(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return value


def program(settings: dict[str, Any]) -> str:
    return _PROGRAM_FILES[_finish(settings)].read_text(encoding="utf-8")


def _grid(value: Any) -> tuple[int, int]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(value[0])
    if len(value) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact ARC colors")
    return len(value), width


def compress_rows(grid: list[list[int]]) -> list[list[int]]:
    _, width = _grid(grid)
    kept = [list(row) for row in grid if any(value != 0 for value in row)]
    return kept or [[0] * width]


def vertical_contact_cells(grid: list[list[int]]) -> set[tuple[int, int]]:
    height, width = _grid(grid)
    return {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
        and (
            (row > 0 and grid[row - 1][col] != 0)
            or (row + 1 < height and grid[row + 1][col] != 0)
        )
    }


def solve(grid: list[list[int]], settings: Any) -> list[list[int]]:
    finish = _finish(settings)
    compact = compress_rows(grid)
    if finish == SETTINGS[0]:
        return compact
    contacts = vertical_contact_cells(compact)
    return [
        [9 if (row, col) in contacts else value for col, value in enumerate(values)]
        for row, values in enumerate(compact)
    ]


def skip_a_solve(grid: list[list[int]]) -> list[list[int]]:
    """Counterfactual: run step B on the uncompressed source grid."""
    _grid(grid)
    contacts = vertical_contact_cells(grid)
    return [
        [9 if (row, col) in contacts else value for col, value in enumerate(values)]
        for row, values in enumerate(grid)
    ]


def changed_cells(left: list[list[int]], right: list[list[int]]) -> int:
    if _grid(left) != _grid(right):
        raise ValueError("grids must have the same shape")
    return sum(
        left[row][col] != right[row][col]
        for row in range(len(left))
        for col in range(len(left[0]))
    )


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|row-contact-input-v1|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _active_rows(height: int, count: int, rng: random.Random) -> list[int]:
    # Constructively retain at least one blank row between active rows while
    # spreading them across the full source height.
    if height < 2 * count:
        raise ValueError("profile cannot separate active rows")
    anchors = [round((index + 1) * (height - 1) / (count + 1)) for index in range(count)]
    rows: list[int] = []
    for index, anchor in enumerate(anchors):
        low = 0 if index == 0 else rows[-1] + 2
        high = height - 1 - 2 * (count - index - 1)
        jitter = rng.choice((-1, 0, 1))
        rows.append(max(low, min(high, anchor + jitter)))
    if any(b <= a + 1 for a, b in zip(rows, rows[1:])):
        raise RuntimeError("active-row construction lost blank separators")
    return rows


def _row_masks(width: int, count: int, density: float, rng: random.Random) -> list[set[int]]:
    target = max(4, min(width - 1, round(width * density)))
    mid = width // 2
    core = {max(0, mid - 1), mid}
    witness = 1
    if witness in core:
        raise ValueError("profile width cannot reserve the gapped-repeat witness column")
    masks: list[set[int]] = []
    for row_index in range(count):
        mask = set(core)
        # Reserve one column on alternating compacted rows.  It is repeated,
        # but every occupied witness cell has blank compacted-row neighbors,
        # which constructively refutes "mark every repeated column".
        forbidden = {witness} if row_index % 2 else set()
        if row_index % 2 == 0:
            mask.add(witness)
        # Boundary and offset structure make the 30x30 case substantive.
        if row_index == 0:
            mask.add(0)
        if row_index == count - 1:
            mask.add(width - 1)
        candidates = [col for col in range(width) if col not in mask and col not in forbidden]
        rng.shuffle(candidates)
        mask.update(candidates[: max(0, target - len(mask))])
        masks.append(mask)
    # Keep masks visibly distinct while preserving the shared vertical core
    # and the alternating witness invariant.
    for index in range(1, len(masks)):
        if masks[index] == masks[0]:
            protected = core | ({witness} if index % 2 == 0 else set())
            removable = next(col for col in sorted(masks[index]) if col not in protected)
            masks[index].remove(removable)
            forbidden = {witness} if index % 2 else set()
            replacement = next(
                col for col in range(width)
                if col not in masks[index] and col not in forbidden
            )
            masks[index].add(replacement)
    return masks


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer("seed", seed, 0, MAX_SEED)
    if split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")
    profiles = _TRAIN_PROFILES if split == "train" else _QUERY_PROFILES
    _integer("index", index, 0, len(profiles) - 1)
    height, width, count, density = profiles[index]
    rng = _rng(seed, split, index)
    rows = _active_rows(height, count, rng)
    masks = _row_masks(width, count, density, rng)
    palette = list(range(1, 9))
    rng.shuffle(palette)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row_index, (row, mask) in enumerate(zip(rows, masks, strict=True)):
        colors = palette[row_index % len(palette):] + palette[: row_index % len(palette)]
        for offset, col in enumerate(sorted(mask)):
            grid[row][col] = colors[(offset + row_index) % len(colors)]
    compact = compress_rows(grid)
    if not vertical_contact_cells(compact):
        raise RuntimeError("constructed input lacks post-compression contacts")
    if vertical_contact_cells(grid):
        raise RuntimeError("source rows unexpectedly have vertical contacts")
    return grid


def _horizontal_contacts(compact: list[list[int]]) -> list[list[int]]:
    height, width = _grid(compact)
    marked = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if compact[r][c] != 0
        and ((c > 0 and compact[r][c - 1] != 0) or (c + 1 < width and compact[r][c + 1] != 0))
    }
    return [[9 if (r, c) in marked else value for c, value in enumerate(row)] for r, row in enumerate(compact)]


def _repeated_columns(compact: list[list[int]]) -> list[list[int]]:
    _, width = _grid(compact)
    repeated = {
        c for c in range(width)
        if sum(row[c] != 0 for row in compact) >= 2
    }
    return [[9 if value != 0 and c in repeated else value for c, value in enumerate(row)] for row in compact]


def _upper_contacts(compact: list[list[int]]) -> list[list[int]]:
    height, width = _grid(compact)
    marked = {
        (r, c)
        for r in range(height - 1)
        for c in range(width)
        if compact[r][c] != 0 and compact[r + 1][c] != 0
    }
    return [[9 if (r, c) in marked else value for c, value in enumerate(row)] for r, row in enumerate(compact)]


def _all_nonzero(compact: list[list[int]]) -> list[list[int]]:
    return [[9 if value != 0 else 0 for value in row] for row in compact]


def rival_outputs(grid: list[list[int]], settings: Any) -> dict[str, list[list[int]]]:
    finish = _finish(settings)
    compact = compress_rows(grid)
    selected = solve(grid, settings)
    outputs = {
        "other_setting": solve(grid, {PARAMETER: SETTINGS[1] if finish == SETTINGS[0] else SETTINGS[0]}),
        "horizontal_contacts": _horizontal_contacts(compact),
        "repeated_columns": _repeated_columns(compact),
        "upper_contacts_only": _upper_contacts(compact),
        "mark_all_nonzero": _all_nonzero(compact),
    }
    return outputs


def teaching_check(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = episode.get("settings")
    _finish(settings)
    train = episode.get("train")
    if type(train) is not list or len(train) < MIN_DEMOS:
        raise ValueError("episode needs at least two demonstrations")
    names = set()
    per_demo: list[dict[str, list[list[int]]]] = []
    for pair in train:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("demonstrations require input/output grids")
        expected = solve(pair["input"], settings)
        if pair["output"] != expected:
            raise ValueError("demonstration label differs from selected rule")
        outputs = rival_outputs(pair["input"], settings)
        names.update(outputs)
        per_demo.append(outputs)
    surviving = sorted(
        name
        for name in names
        if all(outputs.get(name) == pair["output"] for outputs, pair in zip(per_demo, train))
    )
    return {
        "status": "identified" if not surviving else "ambiguous",
        "surviving_rivals": surviving,
        "demonstrations": len(train),
        "used_query_answers": False,
        "limits": "Finite named rivals fitted to demonstrations only; not universal uniqueness.",
    }


def dependency_trace(grid: list[list[int]], settings: Any) -> dict[str, Any]:
    finish = _finish(settings)
    compact = compress_rows(grid)
    contacts = vertical_contact_cells(compact)
    return {
        "setting": {PARAMETER: finish},
        "step_a": "remove every all-zero row",
        "intermediate": {"rows": len(compact), "cols": len(compact[0]), "grid": compact},
        "step_b": "recolor nonzero cells with vertical nonzero contact to 9",
        "vertical_contact_cells": len(contacts),
        "why_b_depends_on_a": "blank-row removal makes formerly separated nonempty rows adjacent, creating the vertical contacts consumed by step B",
    }


def generate(seed: int, settings: Any, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer("seed", seed, 0, MAX_SEED)
    _finish(settings)
    _integer("demos", demos, MIN_DEMOS, MAX_DEMOS)
    _integer("queries", queries, MIN_QUERIES, MAX_QUERIES)
    train = [
        {"input": (grid := sample_input(seed, "train", index)), "output": solve(grid, settings)}
        for index in range(demos)
    ]
    test = [
        {"input": (grid := sample_input(seed, "test", index)), "output": solve(grid, settings)}
        for index in range(queries)
    ]
    fingerprints = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(fingerprints) != len(set(fingerprints)):
        raise RuntimeError("constructed episode contains duplicate inputs")
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": deepcopy(settings),
        "train": train,
        "test": test,
        "program_solution": program(settings),
        "sampling": {"draws": demos + queries, "duplicate_rejections": 0},
    }
    certificate = teaching_check(episode)
    if certificate["surviving_rivals"]:
        raise RuntimeError("constructed demonstrations leave declared rivals alive: " + ", ".join(certificate["surviving_rivals"]))
    episode["teaching"] = certificate
    return episode


def public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    if type(episode) is not dict or type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    test = episode["test"]
    _integer("query_index", query_index, 0, len(test) - 1)
    try:
        query = {"input": deepcopy(test[query_index]["input"])}
        if query_index == 0:
            train = [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])} for pair in episode["train"]]
            return {"train": train, "test": [query]}
        return {"test": [query]}
    except (KeyError, TypeError) as error:
        raise ValueError("episode pairs require valid grids") from error


__all__ = [
    "DEFAULT", "SETTINGS", "changed_cells", "compress_rows", "dependency_trace",
    "generate", "program", "public_turn", "rival_outputs", "sample_input",
    "skip_a_solve", "solve", "teaching_check", "vertical_contact_cells",
]

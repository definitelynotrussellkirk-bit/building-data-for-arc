"""Native modal-frequency scale family for ``2dacb90452ce``.

``fixed_two`` is the byte-exact canonical 2x upscale. ``modal_parity`` first
finds the unique modal color and counts its cells, then uses factor three for an
odd count and factor two for an even count.  The inputs are independent of the
private setting; the first two demonstrations deliberately reverse simple
size/palette shortcuts while exposing opposite modal-count parity.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable


TASK_ID = "2dacb90452ce"
PARAMETER = "scale_policy"
SETTINGS = ("fixed_two", "modal_parity")
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1

_HOME = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    "fixed_two": _HOME / "canonical.rkt",
    "modal_parity": _HOME / "modal_parity.rkt",
}

# height, width, palette size, exact unique-modal count.  The first profile is
# small/even-featured with odd modal count; the second is large/odd-featured
# with even modal count.  Size, area and palette shortcuts therefore predict
# the reverse of the intended conditional policy.
_TRAIN_PROFILES = (
    (4, 4, 4, 7),
    (7, 7, 5, 20),
    (3, 3, 3, 5),
    (6, 6, 3, 16),
    (7, 7, 5, 21),
    (8, 8, 5, 30),
)
_QUERY_PROFILES = (
    (6, 6, 5, 15),
    (7, 7, 5, 20),
    (9, 9, 6, 32),
    (10, 10, 7, 41),
)


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return value


def program(settings: dict[str, Any]) -> str:
    return _PROGRAM_FILES[_validate_settings(settings)].read_text(encoding="utf-8")


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact ARC colors")
    return len(grid), width


def modal_summary(grid: list[list[int]]) -> dict[str, int]:
    _validate_grid(grid)
    counts = Counter(value for row in grid for value in row)
    maximum = max(counts.values())
    modes = [color for color, count in counts.items() if count == maximum]
    if len(modes) != 1:
        raise ValueError("modal_parity requires a unique modal color")
    return {"color": modes[0], "count": maximum}


def scale_factor(grid: list[list[int]], policy: str) -> int:
    if type(policy) is not str or policy not in SETTINGS:
        raise ValueError(f"policy must be one of {SETTINGS!r}")
    if policy == "fixed_two":
        return 2
    return 3 if modal_summary(grid)["count"] % 2 else 2


def _upscale(grid: list[list[int]], factor: int) -> list[list[int]]:
    _validate_grid(grid)
    if type(factor) is not int or factor not in (2, 3):
        raise ValueError("factor must be 2 or 3")
    height, width = len(grid), len(grid[0])
    if height * factor > 30 or width * factor > 30:
        raise ValueError("upscaled output would exceed 30x30")
    return [
        [value for value in row for _ in range(factor)]
        for row in grid
        for _ in range(factor)
    ]


def apply_rule(grid: list[list[int]], policy: str) -> list[list[int]]:
    return _upscale(grid, scale_factor(grid, policy))


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|modal-parity-v1|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _TRAIN_PROFILES if split == "train" else _QUERY_PROFILES
    height, width, palette_size, modal_count = profiles[index]
    rng = _rng(seed, split, index)
    palette = list(range(10))
    rng.shuffle(palette)
    palette = palette[:palette_size]
    modal_color = palette[0]
    others = palette[1:]
    remaining = height * width - modal_count
    if modal_count <= 0 or not others or remaining < len(others):
        raise RuntimeError("invalid modal-profile construction")
    values = [modal_color] * modal_count
    values.extend(others[i % len(others)] for i in range(remaining))
    rng.shuffle(values)
    # Keep a boundary-spanning modal trace and a nonmodal corner so the large
    # query contains real structure rather than padded noise.
    for position in (0, width - 1, (height - 1) * width, height * width - 1):
        try:
            modal_position = values.index(modal_color)
        except ValueError as exc:
            raise RuntimeError("modal color disappeared") from exc
        values[position], values[modal_position] = values[modal_position], values[position]
    # Restore one nonmodal cell at the bottom-right while retaining the count.
    nonmodal_position = next(i for i, value in enumerate(values) if value != modal_color)
    values[-1], values[nonmodal_position] = values[nonmodal_position], values[-1]
    grid = [values[row * width : (row + 1) * width] for row in range(height)]
    summary = modal_summary(grid)
    if summary != {"color": modal_color, "count": modal_count}:
        raise RuntimeError(f"constructed modal summary {summary!r} differs from profile")
    return grid


def _factor_output(grid: list[list[int]], factor: int) -> list[list[int]]:
    return _upscale(grid, factor)


def _feature_policies(grid: list[list[int]]) -> dict[str, int]:
    height, width = _validate_grid(grid)
    colors = len({value for row in grid for value in row})
    return {
        "fixed_two": 2,
        "fixed_three": 3,
        "odd_height": 3 if height % 2 else 2,
        "odd_width": 3 if width % 2 else 2,
        "odd_area": 3 if (height * width) % 2 else 2,
        "odd_palette": 3 if colors % 2 else 2,
        "large_grid": 3 if max(height, width) >= 7 else 2,
        "many_colors": 3 if colors >= 5 else 2,
        "modal_parity": scale_factor(grid, "modal_parity"),
    }


def rival_outputs(grid: list[list[int]], chosen: str) -> dict[str, list[list[int]]]:
    if chosen not in SETTINGS:
        raise ValueError(f"chosen must be one of {SETTINGS!r}")
    target_name = "fixed_two" if chosen == "fixed_two" else "modal_parity"
    return {
        name: _factor_output(grid, factor)
        for name, factor in _feature_policies(grid).items()
        if name != target_name
    }


def surviving_rivals(train: list[dict[str, Any]], chosen: str) -> list[str]:
    if type(train) is not list or not train:
        raise ValueError("train must be a nonempty list")
    names = set(rival_outputs(train[0]["input"], chosen))
    return sorted(
        name
        for name in names
        if all(rival_outputs(pair["input"], chosen)[name] == pair["output"] for pair in train)
    )


def _pair(grid: list[list[int]], policy: str) -> dict[str, list[list[int]]]:
    return {"input": deepcopy(grid), "output": apply_rule(grid, policy)}


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    if type(queries) is not int:
        raise TypeError("queries must be an exact integer; bool is forbidden")
    if queries != QUERY_COUNT:
        raise ValueError(f"queries must be exactly {QUERY_COUNT}")
    policy = _validate_settings(settings)

    train = [_pair(_sample_input(seed, "train", index), policy) for index in range(demos)]
    test = [_pair(_sample_input(seed, "test", index), policy) for index in range(QUERY_COUNT)]
    inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in [*train, *test]]
    if len(inputs) != len(set(inputs)):
        raise RuntimeError("all demonstration and query inputs must be distinct")
    survivors = surviving_rivals(train, policy)
    if survivors:
        raise RuntimeError(f"visible demonstrations leave declared rivals alive: {survivors}")
    return {"train": train, "test": test, "program_solution": program(settings)}

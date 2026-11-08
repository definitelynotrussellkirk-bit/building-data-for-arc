#!/usr/bin/env python3
"""Task-local prototype varying clockwise vs counterclockwise corner copying.

The production catalog remains unchanged.  This module builds complete private
training episodes and answer-masked public challenges for an explicitly chosen
(or deterministically selected) direction.  The canonical clockwise Racket
program is returned byte-for-byte as the default setting.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
for ancestor in HERE.parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        if str(runtime) not in sys.path:
            sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        if str(ancestor) not in sys.path:
            sys.path.insert(0, str(ancestor))
        break

from reviewer_support import (  # noqa: E402
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "61c0bcd32328"
PROTOTYPE_VERSION = "proposed-corner-direction-v1"
ALLOWED_DIRECTIONS = ("clockwise", "counterclockwise")
SETTINGS = ALLOWED_DIRECTIONS
DEFAULT_DIRECTION = "clockwise"
DEFAULT_N_TRAIN = 3
DEFAULT_N_TEST = 4
CANONICAL_EXACT_SHA256 = (
    "0dc3328fe8ad885a19f7c620a4d641ffc733e8cc641a331d01b3e88410c5f64e"
)
CANONICAL_NORMALIZED_SHA256 = (
    "e3835c9a174e5fd8b8be9b2c3a7bd754629ce5f5197d6e25d7be704d40d32692"
)

_CLOCKWISE_DR = """(dr (cond
                                                                     ((eq? corner 'tl) 0)
                                                                     ((eq? corner 'tr) (- h 1 r2))
                                                                     ((eq? corner 'br) 0)
                                                                     ((eq? corner 'bl) (- 0 r1))))"""
_CLOCKWISE_DC = """(dc (cond
                                                                     ((eq? corner 'tl) (- w 1 c2))
                                                                     ((eq? corner 'tr) 0)
                                                                     ((eq? corner 'br) (- 0 c1))
                                                                     ((eq? corner 'bl) 0)))"""
_COUNTERCLOCKWISE_DR = """(dr (cond
                                                                     ((eq? corner 'tl) (- h 1 r2))
                                                                     ((eq? corner 'tr) 0)
                                                                     ((eq? corner 'br) (- 0 r1))
                                                                     ((eq? corner 'bl) 0)))"""
_COUNTERCLOCKWISE_DC = """(dc (cond
                                                                     ((eq? corner 'tl) 0)
                                                                     ((eq? corner 'tr) (- 0 c1))
                                                                     ((eq? corner 'br) 0)
                                                                     ((eq? corner 'bl) (- w 1 c2))))"""

_BANDS = ("easy", "medium", "hard")
_PROFILES = ("single_tl", "single_tr", "single_br", "single_bl")


def _validate_direction(direction: str) -> str:
    if direction not in ALLOWED_DIRECTIONS:
        raise ValueError(
            f"direction must be one of {ALLOWED_DIRECTIONS}, got {direction!r}"
        )
    return direction


def _validate_seed(seed: int) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be an exact nonnegative integer")
    return seed


def _validate_count(name: str, value: int) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be an exact positive integer")
    return value


def _normalized_source(source: str) -> str:
    return " ".join(source.split())


@lru_cache(maxsize=1)
def canonical_source() -> str:
    """Return the one canonical Racket source, pinned by exact SHA-256."""
    root = find_root(__file__)
    sources: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source.strip():
                    raise ValueError(f"canonical row for {TASK_ID} lacks a program")
                sources.add(source)
    if len(sources) != 1:
        raise ValueError(
            f"expected one canonical program for {TASK_ID}, found {len(sources)}"
        )
    source = next(iter(sources))
    exact = hashlib.sha256(source.encode()).hexdigest()
    normalized = hashlib.sha256(_normalized_source(source).encode()).hexdigest()
    if exact != CANONICAL_EXACT_SHA256:
        raise ValueError(f"canonical exact source hash changed: {exact}")
    if normalized != CANONICAL_NORMALIZED_SHA256:
        raise ValueError(f"canonical normalized source hash changed: {normalized}")
    return source


def program_for(direction: str = DEFAULT_DIRECTION) -> str:
    """Return executable Racket for one bounded direction setting."""
    direction = _validate_direction(direction)
    source = canonical_source()
    if direction == DEFAULT_DIRECTION:
        return source
    if source.count(_CLOCKWISE_DR) != 1 or source.count(_CLOCKWISE_DC) != 1:
        raise ValueError("canonical direction fragments are not uniquely identifiable")
    transformed = source.replace(_CLOCKWISE_DR, _COUNTERCLOCKWISE_DR, 1)
    transformed = transformed.replace(_CLOCKWISE_DC, _COUNTERCLOCKWISE_DC, 1)
    if transformed == source:
        raise ValueError("counterclockwise program transformation made no change")
    return transformed


def normalized_program_hash(direction: str = DEFAULT_DIRECTION) -> str:
    return hashlib.sha256(_normalized_source(program_for(direction)).encode()).hexdigest()


def exact_program_hash(direction: str = DEFAULT_DIRECTION) -> str:
    return hashlib.sha256(program_for(direction).encode()).hexdigest()


def grid_hash(grid: Any) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _validate_grid(grid: Any) -> list[list[int]]:
    normalized = normalize_grid(grid)
    # normalize_grid intentionally accepts digit strings; this public API does not.
    if type(grid) is not list or any(type(row) is not list for row in grid):
        raise ValueError("grid must be a list of list rows")
    if any(type(value) is not int for row in grid for value in row):
        raise ValueError("grid cells must be exact integers")
    return normalized


def _background(grid: list[list[int]]) -> int:
    frequencies = Counter(value for row in grid for value in row if value != 0)
    if not frequencies:
        raise ValueError("a dominant nonzero background is required")
    return frequencies.most_common(1)[0][0]


def _components(grid: list[list[int]], background: int) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != background
    }
    components: list[dict[str, Any]] = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        cells = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        components.append(
            {
                "cells": frozenset(cells),
                "color": color,
                "bbox": (
                    min(row for row, _ in cells),
                    min(col for _, col in cells),
                    max(row for row, _ in cells),
                    max(col for _, col in cells),
                ),
            }
        )
    return components


def _corner(component: dict[str, Any], height: int, width: int) -> str | None:
    row1, col1, row2, col2 = component["bbox"]
    if row1 == 0 and col1 == 0:
        return "tl"
    if row1 == 0 and col2 == width - 1:
        return "tr"
    if row2 == height - 1 and col2 == width - 1:
        return "br"
    if row2 == height - 1 and col1 == 0:
        return "bl"
    return None


def _translation(
    corner: str,
    bbox: tuple[int, int, int, int],
    height: int,
    width: int,
    direction: str,
) -> tuple[int, int]:
    row1, col1, row2, col2 = bbox
    if direction == "clockwise":
        return {
            "tl": (0, width - 1 - col2),
            "tr": (height - 1 - row2, 0),
            "br": (0, -col1),
            "bl": (-row1, 0),
        }[corner]
    return {
        "tl": (height - 1 - row2, 0),
        "tr": (0, -col1),
        "br": (-row1, 0),
        "bl": (0, width - 1 - col2),
    }[corner]


def solve(
    grid: list[list[int]],
    *,
    direction: str = DEFAULT_DIRECTION,
) -> list[list[int]]:
    """Independent Python mirror for clockwise or counterclockwise copying."""
    direction = _validate_direction(direction)
    normalized = _validate_grid(grid)
    height, width = len(normalized), len(normalized[0])
    output = deepcopy(normalized)
    background = _background(normalized)
    for component in _components(normalized, background):
        corner = _corner(component, height, width)
        if corner is None:
            continue
        delta_row, delta_col = _translation(
            corner, component["bbox"], height, width, direction
        )
        for row, col in component["cells"]:
            new_row, new_col = row + delta_row, col + delta_col
            if 0 <= new_row < height and 0 <= new_col < width:
                output[new_row][new_col] = component["color"]
    return output


def select_direction(seed: int) -> str:
    seed = _validate_seed(seed)
    digest = hashlib.sha256(
        f"{TASK_ID}|corner-direction|{PROTOTYPE_VERSION}|{seed}".encode()
    ).digest()
    return SETTINGS[digest[0] % len(SETTINGS)]


def _input_seed(seed: int, sample_index: int) -> int:
    digest = hashlib.sha256(
        f"{TASK_ID}|direction-input|{PROTOTYPE_VERSION}|{seed}|{sample_index}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big") & 0x7FFFFFFF


@lru_cache(maxsize=1)
def selected_generator():
    """Load the selected generator, including the packet task-test mirror layout.

    The isolated task-test runner deliberately copies both an execution layout
    and a repository mirror.  Earlier tests may have loaded ``puzzle_generators``
    from the mirror before this prototype is imported; the general helper then
    correctly rejects mixing dependency trees.  In that one manifest-backed
    case, load the byte-identical repository mirror against its already-cached
    dependencies after checking both hashes and origins.
    """
    root = find_root(__file__)
    try:
        return load_selected_generator(TASK_ID, root=root)
    except ImportError as error:
        if "belongs to another source tree" not in str(error):
            raise
        manifest_path = root / "RUNTIME_MANIFEST.json"
        source_path = root / "generators" / TASK_ID / "generator.py"
        package_root = (root / "shared" / "runtime" / "puzzle_generators").resolve()
        if not manifest_path.is_file() or not source_path.is_file() or not package_root.is_dir():
            raise

        for name, module in tuple(sys.modules.items()):
            if name != "puzzle_generators" and not name.startswith("puzzle_generators."):
                continue
            origins = list(getattr(module, "__path__", []))
            origin = getattr(module, "__file__", None)
            if origin:
                origins.append(origin)
            if not origins or any(
                not Path(value).resolve().is_relative_to(package_root)
                for value in origins
            ):
                raise

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        library_path = f"generators/{TASK_ID}/generator.py"
        rows = [
            row for row in manifest.get("files", [])
            if row.get("library_path") == library_path
        ]
        expected_hashes = {row.get("sha256") for row in rows}
        body = source_path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if len(expected_hashes) != 1 or digest not in expected_hashes:
            raise ImportError(
                "task-test repository mirror does not match the selected manifest"
            ) from error

        name = f"_parametric_mirror_{TASK_ID}_{digest}"
        spec = importlib.util.spec_from_file_location(name, source_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot import task-test mirror {source_path}") from error
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            exec(compile(body, str(source_path), "exec"), module.__dict__)
        except BaseException:
            sys.modules.pop(name, None)
            raise
        return module, source_path, digest


def generate_episode(
    seed: int,
    *,
    direction: str | None = None,
    n_train: int = DEFAULT_N_TRAIN,
    n_test: int = DEFAULT_N_TEST,
) -> dict[str, Any]:
    """Build one full episode whose hidden direction stays fixed throughout."""
    seed = _validate_seed(seed)
    n_train = _validate_count("n_train", n_train)
    n_test = _validate_count("n_test", n_test)
    selected = select_direction(seed) if direction is None else _validate_direction(direction)
    generator, source_path, source_sha256 = selected_generator()

    total = n_train + n_test
    accepted: list[dict[str, Any]] = []
    seen_inputs: set[str] = set()
    max_attempts = max(256, total * 64)
    for sample_index in range(max_attempts):
        profile = _PROFILES[sample_index % len(_PROFILES)]
        difficulty = _BANDS[sample_index % len(_BANDS)]
        input_seed = _input_seed(seed, sample_index)
        grid = generator.generate(
            input_seed,
            sample_index,
            difficulty=difficulty,
            scene_profile=profile,
        )
        if generator.self_check(grid):
            continue
        input_sha256 = grid_hash(grid)
        if input_sha256 in seen_inputs:
            continue
        clockwise = solve(grid, direction="clockwise")
        counterclockwise = solve(grid, direction="counterclockwise")
        if clockwise == counterclockwise:
            continue
        outputs = {
            "clockwise": clockwise,
            "counterclockwise": counterclockwise,
        }
        seen_inputs.add(input_sha256)
        accepted.append(
            {
                "input": grid,
                "output": outputs[selected],
                "meta": {
                    "sample_index": sample_index,
                    "input_seed": input_seed,
                    "difficulty": difficulty,
                    "scene_profile": profile,
                    "input_sha256": input_sha256,
                    "output_sha256_by_direction": {
                        key: grid_hash(value) for key, value in outputs.items()
                    },
                },
            }
        )
        if len(accepted) == total:
            break
    if len(accepted) != total:
        raise RuntimeError(
            f"could not sample {total} distinct direction-sensitive inputs "
            f"within {max_attempts} attempts"
        )

    program = program_for(selected)
    root = find_root(__file__)
    return {
        "train": accepted[:n_train],
        "test": accepted[n_train:],
        "parameters": {"direction": selected},
        "program": program,
        "meta": {
            "prototype": True,
            "status": "proposed_not_selected",
            "task_id": TASK_ID,
            "version": PROTOTYPE_VERSION,
            "seed": seed,
            "selection_scope": "once_per_complete_episode",
            "canonical_default": {"direction": DEFAULT_DIRECTION},
            "allowed_directions": list(ALLOWED_DIRECTIONS),
            "n_train": n_train,
            "n_test": n_test,
            "input_constraint": (
                "every retained input has one declared corner profile and "
                "different clockwise/counterclockwise outputs"
            ),
            "generator_path": str(Path(source_path).relative_to(root)),
            "generator_sha256": source_sha256,
            "canonical_exact_sha256": CANONICAL_EXACT_SHA256,
            "canonical_normalized_sha256": CANONICAL_NORMALIZED_SHA256,
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "normalized_program_sha256": normalized_program_hash(selected),
            "accepted_sample_indices": [
                pair["meta"]["sample_index"] for pair in accepted
            ],
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Keep demonstrations and query inputs while removing private answers."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(public_challenge(episode))


def public_filename(episode: dict[str, Any]) -> str:
    return f"challenge-{public_id(episode)}.json"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--direction", choices=ALLOWED_DIRECTIONS)
    parser.add_argument("--train", type=int, default=DEFAULT_N_TRAIN)
    parser.add_argument("--test", type=int, default=DEFAULT_N_TEST)
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    episode = generate_episode(
        args.seed,
        direction=args.direction,
        n_train=args.train,
        n_test=args.test,
    )
    if args.public:
        data = public_bytes(episode)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_bytes(data)
        else:
            sys.stdout.buffer.write(data)
    else:
        text = json.dumps(episode, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

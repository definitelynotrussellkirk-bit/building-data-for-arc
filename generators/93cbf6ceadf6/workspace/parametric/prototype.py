#!/usr/bin/env python3
"""Native odd-shape selection × output-transform family for 93cbf6ceadf6.

The visible scene sampler is independent of the episode-fixed transform.  Every
scene has exactly three separated objects: a translation-identical pair and one
odd normalized shape.  Pair and odd controls share area and bounding-box size,
while the selected odd shape is asymmetric under the three declared output
transforms.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "93cbf6ceadf6"
ROOT = find_root(__file__)
ALLOWED_TRANSFORMS = ("identity", "rotate_cw", "flip_lr")
DEFAULT_TRANSFORM = "identity"
DEFAULT_DEMOS = 2
DEFAULT_QUERIES = 4
PROTOTYPE_VERSION = "1.0.0"

_PAINT_EXPRESSION = "(paint-cells (empty-grid sh sw 0) offs color)"
BASE, BASE_SOURCE, BASE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _validate_transform(value: str) -> None:
    if type(value) is not str or value not in ALLOWED_TRANSFORMS:
        raise ValueError(
            f"output_transform must be one of {ALLOWED_TRANSFORMS}, got {value!r}"
        )


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def canonical_source(*, root: Path = ROOT) -> str:
    sources: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source.strip():
                    raise ValueError(
                        f"canonical record for {TASK_ID} has no program_solution"
                    )
                sources.append(source)
    if not sources:
        raise ValueError(f"no canonical record found for {TASK_ID}")
    if len(set(sources)) != 1:
        raise ValueError(f"canonical variants for {TASK_ID} disagree")
    return sources[0]


def program_for(
    output_transform: str = DEFAULT_TRANSFORM,
    *,
    root: Path = ROOT,
) -> str:
    """Materialize one exact rule; identity preserves canonical bytes."""
    _validate_transform(output_transform)
    source = canonical_source(root=root)
    if output_transform == DEFAULT_TRANSFORM:
        return source
    if source.count(_PAINT_EXPRESSION) != 1:
        raise ValueError("canonical source no longer matches the guarded paint template")
    operator = "rotate-cw" if output_transform == "rotate_cw" else "flip-lr"
    return source.replace(_PAINT_EXPRESSION, f"({operator} {_PAINT_EXPRESSION})")


def _dimensions(seed: int, sample_index: int, total: int) -> tuple[int, int, int, bool]:
    if sample_index == total - 1:
        return 30, 30, 2, True
    digest = hashlib.sha256(
        f"{TASK_ID}:dimensions:{seed}:{sample_index}:{total}".encode()
    ).digest()
    scale = 2 if sample_index % 4 == 2 else 1
    if scale == 2:
        height = 23 + digest[0] % 5
        width = 23 + digest[1] % 5
    else:
        height = 13 + digest[0] % 9
        width = 13 + digest[1] % 9
    return height, width, scale, False


def sample_inputs(seed: int, total: int) -> list[list[list[int]]]:
    _validate_seed(seed)
    if type(total) is not int or not 6 <= total <= 10:
        raise ValueError("total must be an exact integer in 6..10")

    grids: list[list[list[int]]] = []
    keys: set[str] = set()
    for sample_index in range(total):
        height, width, scale, span_edges = _dimensions(seed, sample_index, total)
        for attempt in range(64):
            scene_index = sample_index * 257 + attempt
            grid = BASE.build_scene(
                seed,
                scene_index,
                height=height,
                width=width,
                scale=scale,
                span_edges=span_edges,
            )
            key = json.dumps(grid, separators=(",", ":"))
            if key not in keys:
                keys.add(key)
                grids.append(grid)
                break
        else:
            raise RuntimeError("could not construct a distinct visible input")
    return grids


def _rotate_cw_grid(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr_grid(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def python_output(
    grid: list[list[int]],
    *,
    output_transform: str = DEFAULT_TRANSFORM,
) -> list[list[int]]:
    """A = select/normalize odd object; B = apply episode-fixed transform."""
    _validate_transform(output_transform)
    intermediate = BASE._odd_output(grid)
    if output_transform == "identity":
        return [row[:] for row in intermediate]
    if output_transform == "rotate_cw":
        return _rotate_cw_grid(intermediate)
    return _flip_lr_grid(intermediate)


def generate_claims(
    seed: int,
    *,
    output_transform: str,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    root: Path = ROOT,
) -> dict:
    _validate_seed(seed)
    _validate_transform(output_transform)
    _validate_counts(demos, queries)
    grids = sample_inputs(seed, demos + queries)
    pairs = [
        {
            "input": [row[:] for row in grid],
            "output": python_output(grid, output_transform=output_transform),
        }
        for grid in grids
    ]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(output_transform, root=root),
    }

"""Tensorization for padded ARC-native model episodes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import torch


Grid = Sequence[Sequence[int]]


class ArcRoles:
    TRAIN_INPUT = 0
    TRAIN_OUTPUT = 1
    QUERY_INPUT = 2
    TARGET_OUTPUT = 3
    CANDIDATE_OUTPUT = 4
    ERROR_MASK = 5
    FEATURE_TOKEN = 6
    RESERVED = 7


DEMO_SLOT_BASE = 0
QUERY_SLOT_BASE = 10
NO_SLOT = 23


@dataclass(frozen=True)
class EpisodeLayout:
    num_tokens: int
    target_start: int | None
    query_start: int


def validate_grid(grid: Grid, *, canvas_size: int, num_arc_colors: int) -> tuple[int, int]:
    if not grid:
        raise ValueError("grid has no rows")
    height = len(grid)
    width = len(grid[0])
    if width == 0:
        raise ValueError("grid has no columns")
    if height > canvas_size or width > canvas_size:
        raise ValueError(f"grid {height}x{width} exceeds canvas {canvas_size}x{canvas_size}")
    for r, row in enumerate(grid):
        if len(row) != width:
            raise ValueError(f"ragged grid at row {r}: {len(row)} != {width}")
        for c, value in enumerate(row):
            value = int(value)
            if value < 0 or value >= num_arc_colors:
                raise ValueError(f"cell ({r}, {c}) has invalid color {value}")
    return height, width


def pad_grid(
    grid: Grid,
    *,
    canvas_size: int = 30,
    num_arc_colors: int = 10,
    null_color_id: int = 10,
) -> torch.Tensor:
    height, width = validate_grid(
        grid,
        canvas_size=canvas_size,
        num_arc_colors=num_arc_colors,
    )
    out = torch.full((canvas_size, canvas_size), null_color_id, dtype=torch.long)
    for r in range(height):
        for c in range(width):
            out[r, c] = int(grid[r][c])
    return out


def real_cell_mask(height: int, width: int, *, canvas_size: int = 30) -> torch.Tensor:
    mask = torch.zeros((canvas_size, canvas_size), dtype=torch.bool)
    mask[:height, :width] = True
    return mask


def _position_ids(canvas_size: int) -> torch.Tensor:
    return torch.arange(canvas_size * canvas_size, dtype=torch.long)


def _append_grid(
    rows: dict[str, list[torch.Tensor]],
    grid: Grid,
    *,
    role: int,
    slot: int,
    canvas_size: int,
    num_arc_colors: int,
    null_color_id: int,
    candidate_id: int = 0,
    labels_grid: Grid | None = None,
) -> tuple[int, int]:
    height, width = validate_grid(
        grid,
        canvas_size=canvas_size,
        num_arc_colors=num_arc_colors,
    )
    cell_ids = pad_grid(
        grid,
        canvas_size=canvas_size,
        num_arc_colors=num_arc_colors,
        null_color_id=null_color_id,
    ).reshape(-1)
    n = canvas_size * canvas_size
    rows["cell_ids"].append(cell_ids)
    rows["position_ids"].append(_position_ids(canvas_size))
    rows["role_ids"].append(torch.full((n,), role, dtype=torch.long))
    rows["slot_ids"].append(torch.full((n,), slot, dtype=torch.long))
    rows["candidate_ids"].append(torch.full((n,), candidate_id, dtype=torch.long))
    rows["attention_mask"].append(torch.ones((n,), dtype=torch.bool))
    rows["pool_mask"].append(torch.full((n,), role == ArcRoles.QUERY_INPUT, dtype=torch.bool))

    labels = torch.full((canvas_size, canvas_size), -100, dtype=torch.long)
    if labels_grid is not None:
        label_h, label_w = validate_grid(
            labels_grid,
            canvas_size=canvas_size,
            num_arc_colors=num_arc_colors,
        )
        for r in range(label_h):
            for c in range(label_w):
                labels[r, c] = int(labels_grid[r][c])
    rows["labels"].append(labels.reshape(-1))
    return height, width


def build_episode_tensors(
    demo_pairs: Iterable[dict],
    query_input: Grid,
    *,
    query_output: Grid | None = None,
    canvas_size: int = 30,
    num_arc_colors: int = 10,
    null_color_id: int = 10,
    include_target_placeholder: bool = True,
) -> dict[str, torch.Tensor]:
    """Build one dense full-attention episode.

    Layout:

    - each demo contributes 900 train-input cells then 900 train-output cells
    - query input contributes 900 cells
    - optional target placeholder contributes 900 NULL cells and carries labels
    """
    rows: dict[str, list[torch.Tensor]] = {
        "cell_ids": [],
        "position_ids": [],
        "role_ids": [],
        "slot_ids": [],
        "candidate_ids": [],
        "attention_mask": [],
        "pool_mask": [],
        "labels": [],
    }

    demo_list = list(demo_pairs)
    if len(demo_list) > 10:
        raise ValueError("demo_pairs exceeds supported DEMO_SLOT_1..10")
    for i, pair in enumerate(demo_list):
        slot = DEMO_SLOT_BASE + i
        _append_grid(
            rows,
            pair["input"],
            role=ArcRoles.TRAIN_INPUT,
            slot=slot,
            canvas_size=canvas_size,
            num_arc_colors=num_arc_colors,
            null_color_id=null_color_id,
        )
        _append_grid(
            rows,
            pair["output"],
            role=ArcRoles.TRAIN_OUTPUT,
            slot=slot,
            canvas_size=canvas_size,
            num_arc_colors=num_arc_colors,
            null_color_id=null_color_id,
        )

    query_start = sum(part.numel() for part in rows["cell_ids"])
    query_h, query_w = _append_grid(
        rows,
        query_input,
        role=ArcRoles.QUERY_INPUT,
        slot=QUERY_SLOT_BASE,
        canvas_size=canvas_size,
        num_arc_colors=num_arc_colors,
        null_color_id=null_color_id,
    )
    del query_h, query_w

    height_labels = None
    width_labels = None
    target_start = None
    if include_target_placeholder:
        target_start = sum(part.numel() for part in rows["cell_ids"])
        blank = [[null_color_id for _ in range(canvas_size)] for _ in range(canvas_size)]
        if query_output is not None:
            out_h, out_w = validate_grid(
                query_output,
                canvas_size=canvas_size,
                num_arc_colors=num_arc_colors,
            )
            height_labels = torch.tensor(out_h - 1, dtype=torch.long)
            width_labels = torch.tensor(out_w - 1, dtype=torch.long)
        _append_grid(
            rows,
            blank,
            role=ArcRoles.TARGET_OUTPUT,
            slot=QUERY_SLOT_BASE,
            canvas_size=canvas_size,
            num_arc_colors=num_arc_colors + 1,
            null_color_id=null_color_id,
            labels_grid=query_output,
        )

    result = {key: torch.cat(value, dim=0) for key, value in rows.items()}
    result["layout"] = EpisodeLayout(
        num_tokens=int(result["cell_ids"].numel()),
        target_start=target_start,
        query_start=query_start,
    )
    if height_labels is not None and width_labels is not None:
        result["height_labels"] = height_labels
        result["width_labels"] = width_labels
    return result


def collate_episode_tensors(rows: list[dict[str, torch.Tensor]]) -> dict[str, torch.Tensor]:
    if not rows:
        raise ValueError("empty batch")
    keys = [
        "cell_ids",
        "position_ids",
        "role_ids",
        "slot_ids",
        "candidate_ids",
        "attention_mask",
        "pool_mask",
        "labels",
    ]
    batch = {key: torch.stack([row[key] for row in rows], dim=0) for key in keys}
    if "height_labels" in rows[0] and "width_labels" in rows[0]:
        batch["height_labels"] = torch.stack([row["height_labels"] for row in rows], dim=0)
        batch["width_labels"] = torch.stack([row["width_labels"] for row in rows], dim=0)
    return batch


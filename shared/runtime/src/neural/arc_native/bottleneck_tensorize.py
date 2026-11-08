"""Board-level tensorization for ARC bottleneck models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import torch

from .tensorize import Grid, pad_grid, real_cell_mask, validate_grid


class BottleneckBoardRoles:
    DEMO_INPUT = 0
    DEMO_OUTPUT = 1
    QUERY_INPUT = 2
    CANDIDATE_OUTPUT = 3


GRID_FEATURE_IGNORE_INDEX = -100
GRID_FEATURE_NAMES = (
    "nonzero",
    "neighbor4_nonzero",
    "neighbor8_nonzero",
    "neighbor4_same_color",
    "neighbor8_same_color",
    "top_edge",
    "bottom_edge",
    "left_edge",
    "right_edge",
    "component_size_bucket",
)
GRID_FEATURE_VOCAB_SIZES = (2, 5, 9, 5, 9, 2, 2, 2, 2, 8)


@dataclass(frozen=True)
class BottleneckEpisodeLayout:
    context_pairs: int
    max_context_pairs: int
    query_pairs: int
    max_query_pairs: int
    canvas_size: int


def _blank_grid(*, canvas_size: int, null_color_id: int) -> torch.Tensor:
    return torch.full((canvas_size, canvas_size), null_color_id, dtype=torch.long)


def _component_size_bucket(size: int) -> int:
    if size <= 0:
        return 0
    if size == 1:
        return 1
    if size == 2:
        return 2
    if size <= 4:
        return 3
    if size <= 8:
        return 4
    if size <= 16:
        return 5
    if size <= 32:
        return 6
    return 7


def grid_feature_channels(
    padded: torch.Tensor,
    mask: torch.Tensor,
    *,
    null_color_id: int = 10,
) -> torch.Tensor:
    """Compute deterministic per-cell ARC helper channels.

    The channels intentionally avoid generator metadata. They expose local
    geometry the model would otherwise have to rediscover from raw colors:
    colorless occupancy, 4/8-neighborhood structure, edge contacts, and an
    occupancy-component size bucket.
    """
    if padded.shape != mask.shape:
        raise ValueError(f"padded/mask shape mismatch: {padded.shape} vs {mask.shape}")

    height, width = padded.shape
    feature_count = len(GRID_FEATURE_NAMES)
    features = torch.zeros((height, width, feature_count), dtype=torch.long)
    values = [[int(padded[r, c]) for c in range(width)] for r in range(height)]
    valid = [[bool(mask[r, c]) for c in range(width)] for r in range(height)]
    nonzero = [
        [valid[r][c] and values[r][c] != 0 and values[r][c] != null_color_id for c in range(width)]
        for r in range(height)
    ]
    valid_rows = [r for r in range(height) if any(valid[r])]
    valid_cols = [c for c in range(width) if any(valid[r][c] for r in range(height))]
    top = valid_rows[0] if valid_rows else 0
    bottom = valid_rows[-1] if valid_rows else -1
    left = valid_cols[0] if valid_cols else 0
    right = valid_cols[-1] if valid_cols else -1
    deltas4 = ((-1, 0), (0, -1), (0, 1), (1, 0))
    deltas8 = (
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (0, -1),
        (0, 1),
        (1, -1),
        (1, 0),
        (1, 1),
    )

    for r in range(height):
        for c in range(width):
            if not valid[r][c]:
                continue
            center = values[r][c]
            center_nonzero = nonzero[r][c]
            n4 = 0
            n8 = 0
            same4 = 0
            same8 = 0
            for dr, dc in deltas8:
                rr = r + dr
                cc = c + dc
                if rr < 0 or rr >= height or cc < 0 or cc >= width:
                    continue
                if not valid[rr][cc] or not nonzero[rr][cc]:
                    continue
                n8 += 1
                if center_nonzero and values[rr][cc] == center:
                    same8 += 1
                if (dr, dc) in deltas4:
                    n4 += 1
                    if center_nonzero and values[rr][cc] == center:
                        same4 += 1
            features[r, c, 0] = int(center_nonzero)
            features[r, c, 1] = n4
            features[r, c, 2] = n8
            features[r, c, 3] = same4
            features[r, c, 4] = same8
            features[r, c, 5] = int(r == top)
            features[r, c, 6] = int(r == bottom)
            features[r, c, 7] = int(c == left)
            features[r, c, 8] = int(c == right)

    visited = [[False for _ in range(width)] for _ in range(height)]
    for r in range(height):
        for c in range(width):
            if visited[r][c] or not nonzero[r][c]:
                continue
            stack = [(r, c)]
            cells: list[tuple[int, int]] = []
            visited[r][c] = True
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in deltas4:
                    nr = rr + dr
                    nc = cc + dc
                    if nr < 0 or nr >= height or nc < 0 or nc >= width:
                        continue
                    if visited[nr][nc] or not nonzero[nr][nc]:
                        continue
                    visited[nr][nc] = True
                    stack.append((nr, nc))
            bucket = _component_size_bucket(len(cells))
            for rr, cc in cells:
                features[rr, cc, 9] = bucket

    return features.reshape(height * width, feature_count)


def _padded_grid_and_mask(
    grid: Grid,
    *,
    canvas_size: int,
    num_arc_colors: int,
    null_color_id: int,
) -> tuple[torch.Tensor, torch.Tensor, int, int]:
    height, width = validate_grid(
        grid,
        canvas_size=canvas_size,
        num_arc_colors=num_arc_colors,
    )
    padded = pad_grid(
        grid,
        canvas_size=canvas_size,
        num_arc_colors=num_arc_colors,
        null_color_id=null_color_id,
    )
    mask = real_cell_mask(height, width, canvas_size=canvas_size)
    return padded, mask, height, width


def _target_labels(
    query_input: Grid,
    query_output: Grid,
    *,
    canvas_size: int,
    num_arc_colors: int,
    null_color_id: int,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    in_h, in_w = validate_grid(
        query_input,
        canvas_size=canvas_size,
        num_arc_colors=num_arc_colors,
    )
    out_h, out_w = validate_grid(
        query_output,
        canvas_size=canvas_size,
        num_arc_colors=num_arc_colors,
    )

    labels = torch.full((canvas_size, canvas_size), -100, dtype=torch.long)
    changed = torch.full((canvas_size, canvas_size), -100, dtype=torch.long)
    target_mask = real_cell_mask(out_h, out_w, canvas_size=canvas_size)
    padded_output = pad_grid(
        query_output,
        canvas_size=canvas_size,
        num_arc_colors=num_arc_colors,
        null_color_id=null_color_id,
    )
    feature_labels = grid_feature_channels(
        padded_output,
        target_mask,
        null_color_id=null_color_id,
    )
    feature_labels = feature_labels.clone()
    feature_labels[~target_mask.reshape(-1)] = GRID_FEATURE_IGNORE_INDEX

    for r in range(out_h):
        for c in range(out_w):
            out_value = int(query_output[r][c])
            labels[r, c] = out_value
            if r < in_h and c < in_w:
                changed[r, c] = int(int(query_input[r][c]) != out_value)
            else:
                changed[r, c] = 1

    height_label = torch.tensor(out_h - 1, dtype=torch.long)
    width_label = torch.tensor(out_w - 1, dtype=torch.long)
    return labels.reshape(-1), changed.reshape(-1), height_label, width_label, feature_labels


def build_bottleneck_episode_tensors(
    demo_pairs: Iterable[dict],
    query_input: Grid | None = None,
    *,
    query_output: Grid | None = None,
    query_pairs: Iterable[dict] | None = None,
    canvas_size: int = 30,
    num_arc_colors: int = 10,
    null_color_id: int = 10,
    max_context_pairs: int = 5,
    max_query_pairs: int = 1,
    pair_consistency_label: int | None = None,
) -> dict[str, torch.Tensor]:
    """Build board-level tensors for an ARC episode.

    The dense baseline emits one 10,800-token sequence. This layout keeps each
    board as a separate padded 900-cell array so the model can encode boards
    independently before rule aggregation.
    """
    demo_list = list(demo_pairs)
    if query_pairs is not None:
        query_list = list(query_pairs)
    else:
        if query_input is None or query_output is None:
            raise ValueError("query_input/query_output are required when query_pairs is not provided")
        query_list = [{"input": query_input, "output": query_output}]
    if len(demo_list) > max_context_pairs:
        raise ValueError(f"demo_pairs={len(demo_list)} exceeds max_context_pairs={max_context_pairs}")
    if len(query_list) > max_query_pairs:
        raise ValueError(f"query_pairs={len(query_list)} exceeds max_query_pairs={max_query_pairs}")
    if max_query_pairs < 1:
        raise ValueError("max_query_pairs must be >= 1")
    if pair_consistency_label is None:
        pair_consistency_label = max_context_pairs
    if not 0 <= pair_consistency_label <= max_context_pairs:
        raise ValueError(
            f"pair_consistency_label={pair_consistency_label} outside 0..{max_context_pairs}"
        )

    demo_input_ids: list[torch.Tensor] = []
    demo_output_ids: list[torch.Tensor] = []
    demo_input_masks: list[torch.Tensor] = []
    demo_output_masks: list[torch.Tensor] = []
    demo_input_features: list[torch.Tensor] = []
    demo_output_features: list[torch.Tensor] = []
    pair_mask: list[bool] = []

    for pair in demo_list:
        inp, inp_mask, _, _ = _padded_grid_and_mask(
            pair["input"],
            canvas_size=canvas_size,
            num_arc_colors=num_arc_colors,
            null_color_id=null_color_id,
        )
        out, out_mask, _, _ = _padded_grid_and_mask(
            pair["output"],
            canvas_size=canvas_size,
            num_arc_colors=num_arc_colors,
            null_color_id=null_color_id,
        )
        demo_input_ids.append(inp.reshape(-1))
        demo_output_ids.append(out.reshape(-1))
        demo_input_masks.append(inp_mask.reshape(-1))
        demo_output_masks.append(out_mask.reshape(-1))
        demo_input_features.append(grid_feature_channels(inp, inp_mask, null_color_id=null_color_id))
        demo_output_features.append(grid_feature_channels(out, out_mask, null_color_id=null_color_id))
        pair_mask.append(True)

    while len(demo_input_ids) < max_context_pairs:
        blank = _blank_grid(canvas_size=canvas_size, null_color_id=null_color_id)
        blank_mask = torch.zeros((canvas_size, canvas_size), dtype=torch.bool)
        blank_features = torch.zeros(
            (canvas_size * canvas_size, len(GRID_FEATURE_NAMES)),
            dtype=torch.long,
        )
        demo_input_ids.append(blank.reshape(-1))
        demo_output_ids.append(blank.reshape(-1).clone())
        demo_input_masks.append(blank_mask.reshape(-1))
        demo_output_masks.append(blank_mask.reshape(-1).clone())
        demo_input_features.append(blank_features)
        demo_output_features.append(blank_features.clone())
        pair_mask.append(False)

    query_input_ids: list[torch.Tensor] = []
    query_input_masks: list[torch.Tensor] = []
    query_input_features: list[torch.Tensor] = []
    labels_list: list[torch.Tensor] = []
    changed_labels_list: list[torch.Tensor] = []
    feature_labels_list: list[torch.Tensor] = []
    height_labels: list[torch.Tensor] = []
    width_labels: list[torch.Tensor] = []
    query_mask_slots: list[bool] = []

    for query_pair in query_list:
        query_ids, query_mask, _, _ = _padded_grid_and_mask(
            query_pair["input"],
            canvas_size=canvas_size,
            num_arc_colors=num_arc_colors,
            null_color_id=null_color_id,
        )
        query_features = grid_feature_channels(query_ids, query_mask, null_color_id=null_color_id)
        labels, changed_labels, height_label, width_label, feature_labels = _target_labels(
            query_pair["input"],
            query_pair["output"],
            canvas_size=canvas_size,
            num_arc_colors=num_arc_colors,
            null_color_id=null_color_id,
        )
        query_input_ids.append(query_ids.reshape(-1))
        query_input_masks.append(query_mask.reshape(-1))
        query_input_features.append(query_features)
        labels_list.append(labels)
        changed_labels_list.append(changed_labels)
        feature_labels_list.append(feature_labels)
        height_labels.append(height_label)
        width_labels.append(width_label)
        query_mask_slots.append(True)

    while len(query_input_ids) < max_query_pairs:
        blank = _blank_grid(canvas_size=canvas_size, null_color_id=null_color_id)
        blank_mask = torch.zeros((canvas_size, canvas_size), dtype=torch.bool)
        blank_features = torch.zeros(
            (canvas_size * canvas_size, len(GRID_FEATURE_NAMES)),
            dtype=torch.long,
        )
        inactive_labels = torch.full((canvas_size * canvas_size,), -100, dtype=torch.long)
        inactive_features = torch.full(
            (canvas_size * canvas_size, len(GRID_FEATURE_NAMES)),
            GRID_FEATURE_IGNORE_INDEX,
            dtype=torch.long,
        )
        query_input_ids.append(blank.reshape(-1))
        query_input_masks.append(blank_mask.reshape(-1))
        query_input_features.append(blank_features)
        labels_list.append(inactive_labels)
        changed_labels_list.append(inactive_labels.clone())
        feature_labels_list.append(inactive_features)
        height_labels.append(torch.tensor(-100, dtype=torch.long))
        width_labels.append(torch.tensor(-100, dtype=torch.long))
        query_mask_slots.append(False)

    query_ids_tensor = torch.stack(query_input_ids, dim=0)
    query_mask_tensor = torch.stack(query_input_masks, dim=0)
    query_features_tensor = torch.stack(query_input_features, dim=0)
    labels_tensor = torch.stack(labels_list, dim=0)
    changed_tensor = torch.stack(changed_labels_list, dim=0)
    feature_labels_tensor = torch.stack(feature_labels_list, dim=0)
    height_tensor = torch.stack(height_labels, dim=0)
    width_tensor = torch.stack(width_labels, dim=0)
    query_slot_mask = torch.tensor(query_mask_slots, dtype=torch.bool)

    if max_query_pairs == 1:
        query_ids_out = query_ids_tensor[0]
        query_mask_out = query_mask_tensor[0]
        query_features_out = query_features_tensor[0]
        labels_out = labels_tensor[0]
        changed_out = changed_tensor[0]
        feature_labels_out = feature_labels_tensor[0]
        height_out = height_tensor[0]
        width_out = width_tensor[0]
        query_slot_mask_out = query_slot_mask[0]
    else:
        query_ids_out = query_ids_tensor
        query_mask_out = query_mask_tensor
        query_features_out = query_features_tensor
        labels_out = labels_tensor
        changed_out = changed_tensor
        feature_labels_out = feature_labels_tensor
        height_out = height_tensor
        width_out = width_tensor
        query_slot_mask_out = query_slot_mask

    return {
        "demo_input_ids": torch.stack(demo_input_ids, dim=0),
        "demo_output_ids": torch.stack(demo_output_ids, dim=0),
        "demo_input_masks": torch.stack(demo_input_masks, dim=0),
        "demo_output_masks": torch.stack(demo_output_masks, dim=0),
        "demo_input_features": torch.stack(demo_input_features, dim=0),
        "demo_output_features": torch.stack(demo_output_features, dim=0),
        "pair_mask": torch.tensor(pair_mask, dtype=torch.bool),
        "query_input_ids": query_ids_out,
        "query_input_mask": query_mask_out,
        "query_input_features": query_features_out,
        "query_mask": query_slot_mask_out,
        "labels": labels_out,
        "changed_labels": changed_out,
        "feature_labels": feature_labels_out,
        "height_labels": height_out,
        "width_labels": width_out,
        "pair_consistency_labels": torch.tensor(pair_consistency_label, dtype=torch.long),
        "layout": BottleneckEpisodeLayout(
            context_pairs=len(demo_list),
            max_context_pairs=max_context_pairs,
            query_pairs=len(query_list),
            max_query_pairs=max_query_pairs,
            canvas_size=canvas_size,
        ),
    }


def collate_bottleneck_episode_tensors(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("empty batch")
    keys = [
        "demo_input_ids",
        "demo_output_ids",
        "demo_input_masks",
        "demo_output_masks",
        "demo_input_features",
        "demo_output_features",
        "pair_mask",
        "query_input_ids",
        "query_input_mask",
        "query_input_features",
        "query_mask",
        "labels",
        "changed_labels",
        "feature_labels",
        "height_labels",
        "width_labels",
        "pair_consistency_labels",
    ]
    batch: dict[str, Any] = {key: torch.stack([row[key] for row in rows], dim=0) for key in keys}
    recovery_keys = (
        "previous_answer_ids",
        "previous_answer_mask",
        "refinement_step",
    )
    recovery_rows = ["previous_answer_ids" in row for row in rows]
    if any(recovery_rows) and not all(recovery_rows):
        raise ValueError("cannot mix ordinary and Recovery rows in one batch")
    if all(recovery_rows):
        for key in recovery_keys:
            batch[key] = torch.stack([row[key] for row in rows], dim=0)
    for key in ("task_id", "source", "difficulty"):
        batch[key] = [str(row.get(key, "")) for row in rows]
    if all(recovery_rows):
        for key in ("recovery_thread_id", "recovery_parent_event_id"):
            batch[key] = [str(row.get(key, "")) for row in rows]
    for key in (
        "seed",
        "episode_index",
        "query_index",
        "query_count",
        "demo_count",
        "row_index",
    ):
        batch[key] = torch.tensor([int(row.get(key, -1)) for row in rows], dtype=torch.long)
    return batch

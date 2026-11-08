"""JSONL dataset reader for ARC bottleneck episodes."""

from __future__ import annotations

import gzip
import json
import random
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

import torch
from torch.utils.data import IterableDataset, get_worker_info

from .bottleneck_tensorize import (
    _padded_grid_and_mask,
    build_bottleneck_episode_tensors,
)
from .dataset import expand_jsonl_paths


def bottleneck_row_to_tensors(
    row: dict,
    *,
    canvas_size: int = 30,
    max_context_pairs: int = 5,
    max_query_pairs: int = 1,
    shuffle_demo_pairs: bool = False,
    color_permutation_prob: float = 0.0,
    pair_corruption_prob: float = 0.0,
    min_context_pairs_for_pair_corruption: int = 3,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    """Convert an ARC-native or grid-only episode row into bottleneck tensors."""
    query_pairs = _row_query_pairs(row)
    if not query_pairs:
        raise ValueError("bottleneck training requires at least one query")
    if any("output" not in query for query in query_pairs):
        raise ValueError("bottleneck training requires query output labels")
    rng = rng or random
    query_pairs = deepcopy(query_pairs)
    demo_pairs = deepcopy(list(row.get("demo_pairs", row.get("train", []))))
    if not demo_pairs:
        raise ValueError("bottleneck training requires at least one demonstration pair")
    if color_permutation_prob > 0 and rng.random() < color_permutation_prob:
        color_map = _random_color_permutation(rng)
        demo_pairs = _permute_demo_pairs(demo_pairs, color_map)
        for query in query_pairs:
            query["input"] = _permute_grid(query["input"], color_map)
            query["output"] = _permute_grid(query["output"], color_map)
    if shuffle_demo_pairs:
        rng.shuffle(demo_pairs)
    demo_pairs, pair_consistency_label = maybe_corrupt_demo_pair(
        demo_pairs,
        max_context_pairs=max_context_pairs,
        probability=pair_corruption_prob,
        min_context_pairs=min_context_pairs_for_pair_corruption,
        rng=rng,
    )
    tensors: dict[str, Any] = build_bottleneck_episode_tensors(
        demo_pairs,
        query_pairs=query_pairs,
        canvas_size=canvas_size,
        max_context_pairs=max_context_pairs,
        max_query_pairs=max_query_pairs,
        pair_consistency_label=pair_consistency_label,
    )
    tensors["task_id"] = str(row.get("task_id", "unknown"))
    tensors["source"] = str(row.get("source", ""))
    tensors["difficulty"] = str(row.get("difficulty", ""))
    tensors["seed"] = int(row.get("seed", -1))
    tensors["episode_index"] = int(row.get("episode_index", -1))
    tensors["query_index"] = int(row.get("query_index", -1))
    tensors["query_count"] = int(row.get("query_count", len(query_pairs)))
    tensors["demo_count"] = int(row.get("demo_count", len(demo_pairs)))
    _attach_recovery_tensors(
        tensors,
        row,
        query_count=len(query_pairs),
        canvas_size=canvas_size,
        max_query_pairs=max_query_pairs,
    )
    return tensors


def _attach_recovery_tensors(
    tensors: dict[str, Any],
    row: dict,
    *,
    query_count: int,
    canvas_size: int,
    max_query_pairs: int,
    num_arc_colors: int = 10,
    null_color_id: int = 10,
) -> None:
    """Attach explicit prior-grid inputs for lineage Recovery rows."""

    previous_answers = row.get("previous_answers")
    if previous_answers is None and "previous_answer" in row:
        previous_answers = [row["previous_answer"]]
    if previous_answers is None:
        return
    if not isinstance(previous_answers, list) or len(previous_answers) != query_count:
        raise ValueError("previous_answers must contain one grid per query")

    refinement_steps = row.get("refinement_steps")
    if refinement_steps is None and "refinement_step" in row:
        refinement_steps = [row["refinement_step"]]
    if not isinstance(refinement_steps, list) or len(refinement_steps) != query_count:
        raise ValueError("refinement_steps must contain one value per query")
    if any(int(step) < 1 for step in refinement_steps):
        raise ValueError("Recovery refinement_steps must be positive")

    answer_ids = []
    answer_masks = []
    steps = []
    for answer, step in zip(previous_answers, refinement_steps):
        padded, mask, _, _ = _padded_grid_and_mask(
            answer,
            canvas_size=canvas_size,
            num_arc_colors=num_arc_colors,
            null_color_id=null_color_id,
        )
        answer_ids.append(padded.reshape(-1))
        answer_masks.append(mask.reshape(-1))
        steps.append(int(step))

    while len(answer_ids) < max_query_pairs:
        answer_ids.append(
            torch.full(
                (canvas_size * canvas_size,),
                null_color_id,
                dtype=torch.long,
            )
        )
        answer_masks.append(
            torch.zeros((canvas_size * canvas_size,), dtype=torch.bool)
        )
        steps.append(0)

    answer_ids_tensor = torch.stack(answer_ids)
    answer_masks_tensor = torch.stack(answer_masks)
    steps_tensor = torch.tensor(steps, dtype=torch.long)
    if max_query_pairs == 1:
        answer_ids_tensor = answer_ids_tensor[0]
        answer_masks_tensor = answer_masks_tensor[0]
        steps_tensor = steps_tensor[0]
    tensors["previous_answer_ids"] = answer_ids_tensor
    tensors["previous_answer_mask"] = answer_masks_tensor
    tensors["refinement_step"] = steps_tensor
    tensors["recovery_thread_id"] = str(row.get("recovery_thread_id", ""))
    tensors["recovery_parent_event_id"] = str(
        row.get("recovery_parent_event_id", "")
    )


def _row_query_pairs(row: dict) -> list[dict]:
    """Return labeled query/test pairs from old and contest-style rows."""
    if "queries" in row:
        return list(row["queries"])
    if "query_pairs" in row:
        return list(row["query_pairs"])
    if "test" in row:
        tests = deepcopy(list(row["test"]))
        solutions = row.get("solutions")
        if solutions is not None:
            if len(tests) != len(solutions):
                raise ValueError("test/solutions length mismatch")
            for query, solution in zip(tests, solutions):
                query["output"] = deepcopy(solution)
        return tests
    if "query" in row:
        return [row["query"]]
    return []


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _random_color_permutation(rng: random.Random, *, num_arc_colors: int = 10) -> dict[int, int]:
    """Return an ARC color permutation with background color 0 fixed."""
    colors = list(range(1, num_arc_colors))
    shuffled = list(colors)
    rng.shuffle(shuffled)
    mapping = {0: 0}
    mapping.update({color: shuffled[idx] for idx, color in enumerate(colors)})
    return mapping


def _permute_grid(grid: list[list[int]], color_map: dict[int, int]) -> list[list[int]]:
    return [[color_map.get(int(value), int(value)) for value in row] for row in grid]


def _permute_demo_pairs(demo_pairs: list[dict], color_map: dict[int, int]) -> list[dict]:
    out: list[dict] = []
    for pair in demo_pairs:
        out.append(
            {
                **pair,
                "input": _permute_grid(pair["input"], color_map),
                "output": _permute_grid(pair["output"], color_map),
            }
        )
    return out


def _perturb_grid(grid: list[list[int]], rng: random.Random, *, num_arc_colors: int = 10) -> list[list[int]]:
    corrupted = _copy_grid(grid)
    if not corrupted or not corrupted[0]:
        return corrupted
    height = len(corrupted)
    width = len(corrupted[0])
    area = height * width
    edits = rng.randint(1, max(1, min(5, area // 8)))
    for _ in range(edits):
        r = rng.randrange(height)
        c = rng.randrange(width)
        old = int(corrupted[r][c])
        choices = [color for color in range(num_arc_colors) if color != old]
        corrupted[r][c] = rng.choice(choices)
    return corrupted


def maybe_corrupt_demo_pair(
    demo_pairs: list[dict],
    *,
    max_context_pairs: int,
    probability: float,
    min_context_pairs: int,
    rng: random.Random,
) -> tuple[list[dict], int]:
    """Optionally make one demo pair inconsistent and return its class label.

    Class `max_context_pairs` means "all context pairs are consistent"; classes
    `0..max_context_pairs-1` point to the corrupted pair slot. This gives the
    rule pathway a direct high-gradient objective: identify whether the demos
    agree, and which input/output pair does not belong.
    """
    clean_label = max_context_pairs
    if probability <= 0 or len(demo_pairs) < min_context_pairs or rng.random() >= probability:
        return demo_pairs, clean_label

    corrupt_idx = rng.randrange(len(demo_pairs))
    corrupted_pairs = deepcopy(demo_pairs)
    source_outputs = [
        pair["output"]
        for idx, pair in enumerate(demo_pairs)
        if idx != corrupt_idx and "output" in pair
    ]
    if source_outputs and rng.random() < 0.5:
        replacement = _copy_grid(rng.choice(source_outputs))
    else:
        replacement = _copy_grid(corrupted_pairs[corrupt_idx]["output"])
    corrupted_pairs[corrupt_idx]["output"] = _perturb_grid(replacement, rng)
    return corrupted_pairs, corrupt_idx


class ArcBottleneckJsonlDataset(IterableDataset):
    """Streaming JSONL dataset for board-level bottleneck episodes."""

    def __init__(
        self,
        paths: list[str | Path],
        *,
        canvas_size: int = 30,
        max_context_pairs: int = 5,
        max_query_pairs: int = 1,
        repeat: bool = False,
        shuffle_buffer: int = 0,
        seed: int = 0,
        rank: int = 0,
        world_size: int = 1,
        shuffle_demo_pairs: bool = False,
        color_permutation_prob: float = 0.0,
        pair_corruption_prob: float = 0.0,
        min_context_pairs_for_pair_corruption: int = 3,
        task_filter: Any = None,
        start_row: int = 0,
        stop_row: int | None = None,
    ) -> None:
        if start_row < 0:
            raise ValueError("start_row must be non-negative")
        if stop_row is not None and stop_row <= start_row:
            raise ValueError("stop_row must be greater than start_row")
        self.paths = expand_jsonl_paths(paths)
        self.canvas_size = canvas_size
        self.max_context_pairs = max_context_pairs
        self.max_query_pairs = max_query_pairs
        self.repeat = repeat
        self.shuffle_buffer = shuffle_buffer
        self.seed = seed
        self.rank = rank
        self.world_size = world_size
        self.shuffle_demo_pairs = shuffle_demo_pairs
        self.color_permutation_prob = color_permutation_prob
        self.pair_corruption_prob = pair_corruption_prob
        self.min_context_pairs_for_pair_corruption = min_context_pairs_for_pair_corruption
        # Optional callable task_id -> bool; rows whose task_id returns False
        # are skipped before tensorization (held-out-generator splits).
        self.task_filter = task_filter
        self.start_row = start_row
        self.stop_row = stop_row

    def _rows_once(self, *, rank: int, world_size: int, rng: random.Random) -> Iterable[dict]:
        row_index = 0
        for path in self.paths:
            opener = gzip.open if path.suffix == ".gz" else open
            with opener(path, "rt", encoding="utf-8") as f:
                for line in f:
                    if self.stop_row is not None and row_index >= self.stop_row:
                        return
                    if row_index < self.start_row:
                        row_index += 1
                        continue
                    if row_index % world_size == rank:
                        row = json.loads(line)
                        if self.task_filter is not None and not self.task_filter(
                            str(row.get("task_id", "unknown"))
                        ):
                            row_index += 1
                            continue
                        tensors = bottleneck_row_to_tensors(
                            row,
                            canvas_size=self.canvas_size,
                            max_context_pairs=self.max_context_pairs,
                            max_query_pairs=self.max_query_pairs,
                            shuffle_demo_pairs=self.shuffle_demo_pairs,
                            color_permutation_prob=self.color_permutation_prob,
                            pair_corruption_prob=self.pair_corruption_prob,
                            min_context_pairs_for_pair_corruption=self.min_context_pairs_for_pair_corruption,
                            rng=rng,
                        )
                        tensors["row_index"] = row_index
                        yield tensors
                    row_index += 1

    def __iter__(self) -> Iterable[dict]:
        worker = get_worker_info()
        rank = self.rank
        world_size = self.world_size
        if worker is not None:
            rank = self.rank * worker.num_workers + worker.id
            world_size = self.world_size * worker.num_workers

        rng = random.Random(self.seed + rank)
        while True:
            rows = self._rows_once(rank=rank, world_size=world_size, rng=rng)
            if self.shuffle_buffer <= 1:
                yielded = False
                for row in rows:
                    yielded = True
                    yield row
                if not yielded or not self.repeat:
                    return
                continue

            buffer: list[dict] = []
            for row in rows:
                if len(buffer) < self.shuffle_buffer:
                    buffer.append(row)
                    continue
                j = rng.randrange(len(buffer))
                yield buffer[j]
                buffer[j] = row
            rng.shuffle(buffer)
            for row in buffer:
                yield row
            if not self.repeat:
                return

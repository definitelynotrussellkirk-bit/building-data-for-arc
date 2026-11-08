"""Dataset utilities for the dense episode model.

Two pieces:

- A deterministic held-out-generator split. Random pair holdout is too
  easy — with 3,889 rule families and unbounded fresh inputs, the honest
  generalization metric is exact-match on generators the model NEVER
  trained on. The split hashes task_id, so it is stable across runs,
  machines, and shard layouts, and train/eval can stream the same JSONL
  files with complementary filters.
- A collate that upgrades bottleneck batches to the 28-channel episode
  feature set. Runs inside dataloader workers, never in model forward.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import torch

from .bottleneck_tensorize import collate_bottleneck_episode_tensors
from .episode_features import add_episode_features_to_batch

DEFAULT_HOLDOUT_SALT = "generator-holdout-v1"


def load_primitive_lookup(path: str | Path) -> tuple[int, dict[str, list[int]]]:
    """Load the primitive-set supervision artifact built by
    scripts/build_primitive_vocab.py. Returns (vocab_size, task_id->indices)."""
    data = json.loads(Path(path).read_text())
    return len(data["primitives"]), data["task_primitives"]


def task_in_holdout(
    task_id: str,
    holdout_percent: float,
    *,
    salt: str = DEFAULT_HOLDOUT_SALT,
) -> bool:
    """Deterministically assign a task_id to the held-out-generator set.

    Hash-based so the assignment is independent of shard order and
    identical everywhere. holdout_percent is in [0, 100].
    """
    digest = hashlib.md5(f"{salt}:{task_id}".encode()).hexdigest()
    bucket = int(digest[:8], 16) % 10_000
    return bucket < holdout_percent * 100


def make_holdout_task_filter(
    holdout_percent: float,
    mode: str,
    *,
    salt: str = DEFAULT_HOLDOUT_SALT,
) -> Callable[[str], bool] | None:
    """Build a task_filter for ArcBottleneckJsonlDataset.

    mode="train" keeps only tasks OUTSIDE the holdout; mode="eval" keeps
    only tasks INSIDE it. Returns None when holdout_percent <= 0.
    """
    if holdout_percent <= 0:
        return None
    if mode == "train":
        return lambda task_id: not task_in_holdout(task_id, holdout_percent, salt=salt)
    if mode == "eval":
        return lambda task_id: task_in_holdout(task_id, holdout_percent, salt=salt)
    raise ValueError(f"unknown holdout mode: {mode}")


def collate_episode_batch(
    rows: list[dict[str, Any]],
    *,
    primitive_lookup: dict[str, list[int]] | None = None,
    primitive_vocab_size: int = 0,
) -> dict[str, Any]:
    """Collate bottleneck rows and replace features with the episode set.

    With a primitive lookup (B1 supervision), adds multi-hot
    `primitive_labels` (b, vocab) and `primitive_labels_mask` (b,) — rows
    whose task_id has no entry are masked out of the loss, not zero-labeled.
    Use functools.partial to bind the lookup for DataLoader workers.
    """
    batch = add_episode_features_to_batch(collate_bottleneck_episode_tensors(rows))
    if primitive_lookup is not None and primitive_vocab_size > 0:
        task_ids = batch.get("task_id") or [str(row.get("task_id", "")) for row in rows]
        labels = torch.zeros((len(rows), primitive_vocab_size), dtype=torch.float32)
        label_mask = torch.zeros(len(rows), dtype=torch.bool)
        for idx, task_id in enumerate(task_ids):
            indices = primitive_lookup.get(str(task_id))
            if indices:
                labels[idx, indices] = 1.0
                label_mask[idx] = True
        batch["primitive_labels"] = labels
        batch["primitive_labels_mask"] = label_mask
    return batch


__all__ = [
    "DEFAULT_HOLDOUT_SALT",
    "collate_episode_batch",
    "load_primitive_lookup",
    "make_holdout_task_filter",
    "task_in_holdout",
]

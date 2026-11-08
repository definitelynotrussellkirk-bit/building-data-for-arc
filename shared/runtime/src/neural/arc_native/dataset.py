"""JSONL dataset reader for ARC-native episodes."""

from __future__ import annotations

import glob
import json
import random
from pathlib import Path
from typing import Iterable

from torch.utils.data import IterableDataset, get_worker_info

from .tensorize import build_episode_tensors


def expand_jsonl_paths(patterns: list[str | Path]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        text = str(pattern)
        matched = [Path(p) for p in glob.glob(text)]
        paths.extend(matched if matched else [Path(text)])
    paths = sorted(path for path in paths if path.exists())
    if not paths:
        raise FileNotFoundError(f"no JSONL files matched {patterns}")
    return paths


def episode_row_to_tensors(
    row: dict,
    *,
    canvas_size: int = 30,
    include_target_placeholder: bool = True,
) -> dict:
    """Convert one `arc_native_episode_v1` row into model tensors."""
    query = row["query"]
    return build_episode_tensors(
        row["demo_pairs"],
        query["input"],
        query_output=query.get("output"),
        canvas_size=canvas_size,
        include_target_placeholder=include_target_placeholder,
    )


class ArcNativeJsonlDataset(IterableDataset):
    """Streaming JSONL dataset for generated ARC-native episodes."""

    def __init__(
        self,
        paths: list[str | Path],
        *,
        canvas_size: int = 30,
        repeat: bool = False,
        shuffle_buffer: int = 0,
        seed: int = 0,
        rank: int = 0,
        world_size: int = 1,
    ) -> None:
        self.paths = expand_jsonl_paths(paths)
        self.canvas_size = canvas_size
        self.repeat = repeat
        self.shuffle_buffer = shuffle_buffer
        self.seed = seed
        self.rank = rank
        self.world_size = world_size

    def _rows_once(self, *, rank: int, world_size: int) -> Iterable[dict]:
        row_index = 0
        for path in self.paths:
            with path.open() as f:
                for line in f:
                    if row_index % world_size == rank:
                        row = json.loads(line)
                        yield episode_row_to_tensors(
                            row,
                            canvas_size=self.canvas_size,
                            include_target_placeholder=True,
                        )
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
            rows = self._rows_once(rank=rank, world_size=world_size)
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

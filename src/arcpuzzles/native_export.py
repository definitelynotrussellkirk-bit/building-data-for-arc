"""Native grid rows and optional CPU tensors from the pinned local serializers."""
from __future__ import annotations

import ast
from dataclasses import asdict, is_dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


def native_rows(episode: dict[str, Any], builder: Path, *, grouped: bool) -> list[dict[str, Any]]:
    """Use the four pure legacy row helpers without running its CLI discovery."""
    names = {"shape", "color_set", "build_row", "build_grouped_query_row"}
    tree = ast.parse(builder.read_text())
    definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if len(definitions) != len(names) or {n.name for n in definitions} != names:
        raise ValueError("Pinned native builder lacks the required pure row helpers")
    namespace: dict[str, Any] = {"Any": Any}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(builder), "exec"), namespace)
    common = {"source": "arcpuzzles", "task_id": episode["task_id"], "seed": episode["seed"],
              "difficulty": episode.get("provenance", {}).get("difficulty", episode.get("difficulty")),
              "episode_index": episode.get("sample_index", 0),
              "demo_pairs": episode["train"]}
    if grouped:
        return [namespace["build_grouped_query_row"](**common, query_pairs=episode["test"])]
    return [namespace["build_row"](**common, query_index=i, query_pair=pair)
            for i, pair in enumerate(episode["test"])]


def tensorize_rows(rows: list[dict[str, Any]], root: Path, *, kind: str,
                   canvas_size: int, n_train: int, n_test: int, grouped: bool) -> dict[str, dict]:
    """Write private safetensors, keeping query labels apart from context tensors.

    Called in a prepared library worker. The imported tensorizers are copied
    local source, not a model-training checkout. No tensor is placed on a GPU.
    """
    import torch
    from safetensors.torch import save_file
    from src.neural.arc_native.dataset import episode_row_to_tensors
    from src.neural.arc_native.bottleneck_dataset import bottleneck_row_to_tensors

    artifacts = {}
    for row in rows:
        if kind == "native":
            values = episode_row_to_tensors(row, canvas_size=canvas_size)
        elif kind == "bottleneck":
            values = bottleneck_row_to_tensors(row, canvas_size=canvas_size,
                                               max_context_pairs=n_train,
                                               max_query_pairs=n_test if grouped else 1)
        else:
            raise ValueError(f"Unknown tensor layout: {kind}")
        tensors = {name: value.detach().cpu().contiguous().clone() for name, value in values.items()
                   if isinstance(value, torch.Tensor)}
        metadata = {name: asdict(value) if is_dataclass(value) else value
                    for name, value in values.items() if not isinstance(value, torch.Tensor)}
        name = f"tensor-{row['episode_id']}-q{row['query_index']}.private.safetensors"
        path = root / name
        save_file(tensors, str(path), metadata={"arcpuzzles": json.dumps({
            "schema": "arcpuzzles-private-tensors-v1", "episode_id": row["episode_id"],
            "query_index": row["query_index"], "layout": kind}, sort_keys=True)})
        identity = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
        row["tensor_artifact"] = {"file": name, **identity, "layout": kind, "canvas_size": canvas_size,
                                  "metadata": metadata,
                                  "tensors": {key: {"shape": list(t.shape), "dtype": str(t.dtype)}
                                              for key, t in tensors.items()}}
        artifacts[name] = identity
    return artifacts

"""Strict task-local transport for already verified native episodes.

``controller/`` retains all masked query inputs for the controller, normally
four. Give an actor exactly one file from ``onequery/``. Neither visible format
contains settings, seeds, programs, query labels, turn indices, or count hints.
This module validates transport; protected reference execution is the caller's
responsibility and is never inferred from metadata supplied to this writer.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "8de1c257a9c7"


def _grid(value: Any) -> list[list[int]]:
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return [list(row) for row in value]


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def public_challenge_bytes(challenge: dict[str, Any]) -> bytes:
    """Use the shared public serializer's exact, newline-terminated convention.

    This small portable projection intentionally validates only visible grids.
    Unknown fields, including malformed private values, cannot affect its bytes.
    Full private validation belongs to ``write_batch``.
    """
    if type(challenge) is not dict:
        raise ValueError("challenge must contain nonempty train/test lists")
    train, test = challenge.get("train"), challenge.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("challenge must contain nonempty train/test lists")
    try:
        if any(type(pair) is not dict for pair in train + test):
            raise ValueError("visible pairs must be objects")
        public = {
            "train": [{"input": _grid(pair["input"]), "output": _grid(pair["output"])}
                      for pair in train],
            "test": [{"input": _grid(pair["input"])} for pair in test],
        }
    except (KeyError, TypeError) as error:
        raise ValueError("visible pairs require inputs and demonstration outputs") from error
    return _json_bytes(public)


def public_challenge_id(challenge: dict[str, Any]) -> str:
    """Hash only the exact bytes an actor or controller can see."""
    return hashlib.sha256(public_challenge_bytes(challenge)).hexdigest()


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    """Copy current demonstrations plus one masked query, ignoring every future.

    This function deliberately does not validate or serialize other query pairs,
    their count, query labels, or private fields. Selecting a turn does not add
    answer history; the caller owns that sequencing decision.
    """
    if type(query_index) is not int or query_index < 0:
        raise ValueError("query_index must be a nonnegative exact integer")
    if type(episode) is not dict or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    queries = episode["test"]
    if query_index >= len(queries):
        raise ValueError("query_index is outside the query list")
    projection = {"train": episode.get("train"), "test": [queries[query_index]]}
    return json.loads(public_challenge_bytes(projection))


def _finite_json(value: Any) -> None:
    """Reject private values JSON would silently coerce or fail to preserve."""
    kind = type(value)
    if kind in {str, int, bool, type(None)}:
        return
    if kind is float and math.isfinite(value):
        return
    if kind is list:
        for item in value:
            _finite_json(item)
        return
    if kind is dict and all(type(key) is str for key in value):
        for item in value.values():
            _finite_json(item)
        return
    raise ValueError("private metadata must use finite JSON values and string object keys")


def _private_episode(value: Any) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError("an episode must be an object")
    _finite_json(value)
    episode = json.loads(_json_bytes(value))
    inputs: set[bytes] = set()
    for split, low, high in (("train", 2, 6), ("test", 1, 4)):
        pairs = episode.get(split)
        if type(pairs) is not list or not low <= len(pairs) <= high:
            raise ValueError(f"{split} must contain {low}..{high} pairs")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("every private demonstration and query needs input and output grids")
            input_bytes = _json_bytes(_grid(pair["input"]))
            _grid(pair["output"])
            if input_bytes in inputs:
                raise ValueError("duplicate input: all demonstration and query inputs must be distinct")
            inputs.add(input_bytes)
    if "task_id" in episode and episode["task_id"] != TASK_ID:
        raise ValueError("episode task_id does not match this task-local exporter")
    return episode


def _verify_sources(source_sha256: dict[str, str]) -> None:
    if type(source_sha256) is not dict or not source_sha256:
        raise ValueError("source_sha256 must be a nonempty object")
    for name, expected in source_sha256.items():
        if (type(name) is not str or "\\" in name or not name
                or PurePosixPath(name).is_absolute()
                or any(part in {"", ".", ".."} for part in name.split("/"))
                or type(expected) is not str or not re.fullmatch(r"[0-9a-f]{64}", expected)):
            raise ValueError("source binding needs repository-relative paths and SHA-256 values")
        path = REPO / name
        if (not path.is_file() or path.resolve() != path
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
            raise ValueError(f"source binding changed or is unavailable: {name}")


def write_batch(
    episodes: Iterable[dict[str, Any]],
    out_dir: str | Path,
    *,
    source_sha256: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Publish a deterministic, source-bound batch after complete preflight.

    Counts are independently bounded to 2..6 demonstrations and 1..4 queries.
    Every grid and private label must be strict, all inputs within an episode
    must differ, and controller or single-turn payloads may not repeat across
    a batch. Matched inputs across settings remain lawful when demonstrations
    differ. The full supplied episode survives under ``private/metadata.jsonl``.

    A fresh destination is reserved without overwriting any existing path.
    Each staged file moves atomically; the completion manifest moves last.
    Exceptions clean only the destination reserved by this call and its staging.
    The manifest and metadata are controller material, never actor payloads.
    """
    destination = Path(out_dir)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    own_source = HERE / "export.py"
    binding = {own_source.relative_to(REPO).as_posix(): hashlib.sha256(own_source.read_bytes()).hexdigest()}
    if source_sha256 is not None:
        if type(source_sha256) is not dict:
            raise ValueError("source_sha256 must be an object")
        binding.update(source_sha256)
    _verify_sources(binding)

    controllers: dict[str, bytes] = {}
    turns: dict[str, bytes] = {}
    metadata: dict[str, bytes] = {}
    for value in episodes:
        episode = _private_episode(value)
        controller_bytes = public_challenge_bytes(episode)
        public_id = hashlib.sha256(controller_bytes).hexdigest()
        if public_id in controllers:
            raise ValueError("duplicate public controller payload")
        controllers[public_id] = controller_bytes
        ordered_turn_ids = []
        for query_index in range(len(episode["test"])):
            turn_bytes = public_challenge_bytes(public_turn(episode, query_index))
            turn_id = hashlib.sha256(turn_bytes).hexdigest()
            if turn_id in turns:
                raise ValueError("duplicate single-query public payload")
            turns[turn_id] = turn_bytes
            ordered_turn_ids.append(turn_id)
        metadata[public_id] = _json_bytes({
            "public_id": public_id, "turn_ids": ordered_turn_ids, "episode": episode,
        })
    if not controllers:
        raise ValueError("episodes must contain at least one episode")

    controller_ids, turn_ids = sorted(controllers), sorted(turns)
    payloads = {
        **{f"controller/{key}.json": controllers[key] for key in controller_ids},
        **{f"onequery/{key}.json": turns[key] for key in turn_ids},
        "private/metadata.jsonl": b"".join(metadata[key] for key in controller_ids),
    }
    manifest = {
        "schema": "arcpuzzles-task-parametric-export-v1",
        "status": "complete",
        "task_id": TASK_ID,
        "training_admitted": False,
        "controller_ids": controller_ids,
        "turn_ids": turn_ids,
        "source_sha256": dict(sorted(binding.items())),
        "files": {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                  for name, data in sorted(payloads.items())},
        "actor_delivery": "one onequery/<id>.json file per turn; manifest and controller files stay private",
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    reserved = False
    try:
        with tempfile.TemporaryDirectory(prefix=f".{destination.name}-", dir=destination.parent) as temporary:
            stage = Path(temporary)
            for name, data in payloads.items():
                path = stage / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            _verify_sources(binding)
            (stage / "manifest.json").write_bytes(_json_bytes(manifest))
            destination.mkdir(exist_ok=False)
            reserved = True
            for name in ("controller", "onequery", "private"):
                os.replace(stage / name, destination / name)
            _verify_sources(binding)
            os.replace(stage / "manifest.json", destination / "manifest.json")
    except BaseException:
        if reserved:
            shutil.rmtree(destination)
        raise
    return {
        "public_ids": controller_ids,
        "controller_ids": controller_ids,
        "turn_ids": turn_ids,
        "metadata_path": str(destination / "private/metadata.jsonl"),
        "manifest_path": str(destination / "manifest.json"),
        "manifest_sha256": hashlib.sha256(_json_bytes(manifest)).hexdigest(),
    }

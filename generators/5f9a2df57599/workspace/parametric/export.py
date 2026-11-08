"""Strict, task-local transport of already verified native wall episodes.

Only a single ``turns/<sha256>.json`` file is actor-visible. Masked containers
holding every query input are private controller data. This writer validates
syntax and separation; protected reference execution belongs to its caller.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PROMOTION_PATH = HERE / "promotion.json"


def _public_serializer():
    """Load the exact helper in this checkout, independent of import caches."""
    source = REPO / "shared/runtime/reviewer_support.py"
    if source.is_symlink() or source.resolve() != source:
        raise ValueError("public serialization must use the same checkout")
    spec = importlib.util.spec_from_file_location("_walls_export_public_support", source)
    if spec is None or spec.loader is None:
        raise ValueError("same-checkout public serializer is unavailable")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module.public_challenge_bytes


public_challenge_bytes = _public_serializer()


def _json_bytes(value: Any) -> bytes:
    """Reject lossy or non-JSON private values before reserving a destination."""
    def validate(item):
        kind = type(item)
        if kind is dict:
            if any(type(key) is not str for key in item):
                raise ValueError("JSON object keys must be strings")
            for child in item.values():
                validate(child)
        elif kind is list:
            for child in item:
                validate(child)
        elif kind is float:
            if not math.isfinite(item):
                raise ValueError("private metadata must contain finite JSON values")
        elif kind not in (str, int, bool, type(None)):
            raise ValueError("private metadata must contain JSON-native values")

    try:
        validate(value)
        return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    except (RecursionError, UnicodeError) as error:
        raise ValueError("private metadata must be finite UTF-8 JSON") from error


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    """Detach demonstrations and exactly one input, without reading future data.

    The index is a private selector and never appears in the returned bytes.
    Hidden labels, metadata and the number of future queries cannot influence
    this view. Sequencing and answer history remain the consumer's concern.
    """
    if type(query_index) is not int or query_index < 0:
        raise ValueError("query_index must be a nonnegative exact integer")
    if type(episode) is not dict or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    if query_index >= len(episode["test"]):
        raise ValueError("query_index is outside the episode")
    return json.loads(public_challenge_bytes({
        "train": episode.get("train"), "test": [episode["test"][query_index]],
    }))


def controller_payload(episode: dict[str, Any]) -> dict[str, Any]:
    """Detach all masked query inputs for private controller storage only."""
    return json.loads(public_challenge_bytes(episode))


def _validate_episode(episode: dict[str, Any], limits: dict[str, list[int]]) -> None:
    if type(episode) is not dict:
        raise ValueError("episode must be a JSON object")
    for split, name in (("train", "demos"), ("test", "queries")):
        pairs = episode.get(split)
        lower, upper = limits[name]
        if type(pairs) is not list or not lower <= len(pairs) <= upper:
            raise ValueError(f"episode requires {lower}..{upper} {name}")
        if any(type(pair) is not dict or not {"input", "output"} <= set(pair) for pair in pairs):
            raise ValueError("every private pair requires input and output grids")
    pairs = episode["train"] + episode["test"]
    # Treat every label as a demonstration only inside validation. The shared
    # serializer enforces exact integer colors and rectangular 1..30 grids.
    public_challenge_bytes({"train": pairs, "test": episode["test"][:1]})
    inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
    if len(inputs) != len(set(inputs)):
        raise ValueError("all demonstration and query inputs must be distinct")


def write_batch(
    episodes: Iterable[dict[str, Any]],
    out_dir: str | Path,
    *,
    private_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preflight all bytes, exclusively reserve a fresh directory, publish last.

    Each actor file's name hashes exactly its visible serialized bytes. The
    complete episode and ordered turn mapping stay in private metadata; the
    all-query container lives beneath ``private/controllers``. Duplicate input
    grids within an episode, duplicate visible payloads across the batch, bad
    private labels and lossy metadata fail before destination creation.

    A write failure leaves an incomplete reserved directory without a complete
    manifest. Subsequent calls refuse that directory rather than overwrite it.
    """
    destination = Path(out_dir)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    if any(parent.is_symlink() for parent in destination.absolute().parents):
        raise ValueError("export destination must not have symlink ancestors")
    limits = json.loads(PROMOTION_PATH.read_bytes())["limits"]
    controllers: dict[str, bytes] = {}
    turns: dict[str, bytes] = {}
    metadata: dict[str, bytes] = {}
    for episode in episodes:
        _validate_episode(episode, limits)
        payload = public_challenge_bytes(episode)
        identifier = hashlib.sha256(payload).hexdigest()
        if identifier in controllers:
            raise ValueError("duplicate controller challenge payload")
        controllers[identifier] = payload
        turn_ids = []
        for index in range(len(episode["test"])):
            turn_bytes = public_challenge_bytes(public_turn(episode, index))
            turn_id = hashlib.sha256(turn_bytes).hexdigest()
            if turn_id in turns:
                raise ValueError("duplicate single-query challenge payload")
            turns[turn_id] = turn_bytes
            turn_ids.append(turn_id)
        metadata[identifier] = _json_bytes({
            "controller_id": identifier, "turn_ids": turn_ids, "episode": episode,
        })
    if not controllers:
        raise ValueError("episodes must contain at least one episode")
    controller_ids, turn_ids = sorted(controllers), sorted(turns)
    files = {
        **{f"private/controllers/{key}.json": controllers[key] for key in controller_ids},
        **{f"turns/{key}.json": turns[key] for key in turn_ids},
        "private/metadata.jsonl": b"".join(metadata[key] for key in controller_ids),
    }
    if private_context is not None:
        files["private/context.json"] = _json_bytes(private_context)
    manifest = {
        "schema": "arcpuzzles-native-wall-export-v1",
        "complete": True,
        "native_acceptance": "owner_pending",
        "training_admitted": False,
        "episodes": len(controllers),
        "turns": len(turns),
        "files": {name: hashlib.sha256(body).hexdigest() for name, body in sorted(files.items())},
        "visibility": "Only one turns/<id>.json payload is actor-visible; every other file is private controller data.",
        "reference_labels_checked_by_writer": False,
    }
    manifest_bytes = _json_bytes(manifest)

    # mkdir(exist_ok=False) is the atomic reservation, including concurrent
    # attempts and dangling symlinks; preflight never implies ownership.
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    for name, body in sorted(files.items()):
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.write_bytes(body)
    pending = destination / "manifest.pending"
    pending.write_bytes(manifest_bytes)
    pending.replace(destination / "manifest.json")
    return {
        "controller_ids": controller_ids,
        "turn_ids": turn_ids,
        "metadata_path": str(destination / "private/metadata.jsonl"),
        "manifest_path": str(destination / "manifest.json"),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    }

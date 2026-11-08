"""Task-local public/private export for verified parametric episodes.

Reference execution belongs to the caller. This module only validates visible
grid syntax and transports already-verified labels; it never runs Racket.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[4]
RUNTIME = REPO / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import public_challenge_bytes, public_challenge_id


def _validate_episode(episode: dict[str, Any]) -> None:
    """Validate the private lesson before publishing any of its visible views.

    This transport check does not validate rule semantics. In particular,
    syntactically valid private labels still require reference execution.
    """
    if not isinstance(episode, dict):
        raise ValueError("episode must contain train/test lists")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("episode must contain 2..6 demonstrations")
    if type(test) is not list or not 1 <= len(test) <= 4:
        raise ValueError("episode must contain 1..4 queries")
    # Reusing the public grid validator for the combined pair list also
    # validates every private query output without exposing those labels.
    public_challenge_bytes({"train": train + test, "test": test[:1]})
    inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in train + test]
    if len(inputs) != len(set(inputs)):
        raise ValueError("all demonstration and query inputs must be distinct")


def public_turn(episode: dict[str, Any], query_index: int = 0) -> dict[str, Any]:
    """Return the current demonstrations and exactly one masked query.

    No future query is inspected, and neither query labels nor private metadata
    can affect this projection. The result shares no mutable grids with the
    stored episode. Sequencing and answer history remain the caller's concern.
    """
    if type(query_index) is not int or query_index < 0:
        raise ValueError("query_index must be a nonnegative exact integer")
    if not isinstance(episode, dict) or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    queries = episode["test"]
    if query_index >= len(queries):
        raise ValueError("query_index is outside the episode query list")
    projection = {"train": episode.get("train"), "test": [queries[query_index]]}
    return json.loads(public_challenge_bytes(projection))


def write_batch(episodes: Iterable[dict[str, Any]], out_dir: str | Path) -> dict[str, Any]:
    """Write a deterministic batch to a fresh directory after complete preflight.

    ``public/<id>.json`` stores all query inputs for controller use. Each
    ``turns/<id>.json`` contains only the demonstrations and one current query;
    give actors that single payload rather than a directory or batch index.
    ``private/metadata.jsonl`` preserves each full episode and its ordered turn
    IDs. Public filenames are SHA-256 identifiers of the shared canonical
    visible bytes, and all files/metadata rows are ordered by those identifiers.

    Duplicate controller or single-query payloads, invalid public or private
    grids, repeated inputs, invalid counts, and non-JSON private metadata fail
    before any destination is created. Existing destinations are never
    overwritten. A hash inventory is published last; an interrupted write has
    no completed manifest. Admission callers materialize four distinct queries.
    """
    public_payloads: dict[str, bytes] = {}
    turn_payloads: dict[str, bytes] = {}
    metadata_lines: dict[str, str] = {}
    for episode in episodes:
        _validate_episode(episode)
        payload = public_challenge_bytes(episode)
        identifier = public_challenge_id(episode)
        if identifier in public_payloads:
            raise ValueError("duplicate public challenge payload")
        public_payloads[identifier] = payload
        ordered_turn_ids = []
        for query_index in range(len(episode["test"])):
            visible = public_turn(episode, query_index)
            turn_payload = public_challenge_bytes(visible)
            turn_id = public_challenge_id(visible)
            if turn_id in turn_payloads:
                raise ValueError("duplicate single-query public challenge payload")
            turn_payloads[turn_id] = turn_payload
            ordered_turn_ids.append(turn_id)
        metadata_lines[identifier] = json.dumps(
            {"public_id": identifier, "turn_ids": ordered_turn_ids, "episode": episode},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ) + "\n"
    if not public_payloads:
        raise ValueError("episodes must contain at least one episode")

    public_ids = sorted(public_payloads)
    turn_ids = sorted(turn_payloads)
    files = {
        **{f"public/{identifier}.json": public_payloads[identifier] for identifier in public_ids},
        **{f"turns/{identifier}.json": turn_payloads[identifier] for identifier in turn_ids},
        "private/metadata.jsonl": "".join(metadata_lines[identifier] for identifier in public_ids).encode("utf-8"),
    }
    manifest = {
        "schema": "arcpuzzles-task-local-example-export-v1",
        "complete": True,
        "native_acceptance": "owner_pending",
        "training_admitted": False,
        "episodes": len(public_ids),
        "turns": len(turn_ids),
        "files": {name: hashlib.sha256(body).hexdigest() for name, body in sorted(files.items())},
        "visibility": "Give the actor exactly one turns/<id>.json payload; all other files are controller-private.",
    }
    manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=False)
    for name, body in sorted(files.items()):
        path = destination / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(body)
    pending = destination / "manifest.pending"
    pending.write_bytes(manifest_bytes)
    pending.rename(destination / "manifest.json")
    metadata_path = destination / "private/metadata.jsonl"
    return {
        "public_ids": public_ids,
        "turn_ids": turn_ids,
        "metadata_path": str(metadata_path),
        "manifest_path": str(destination / "manifest.json"),
    }

"""Task-local public/private export for verified parametric episodes.

Reference execution belongs to the caller. This module only validates visible
grid syntax and transports already-verified labels; it never runs Racket.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[4]
RUNTIME = REPO / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import public_challenge_bytes, public_challenge_id


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

    Duplicate controller payloads or single-query payloads, invalid visible
    grids, and non-JSON private metadata fail before any destination is created.
    Existing destinations are never overwritten. The writer supports a
    nonempty query list; admission callers materialize four distinct queries.
    """
    public_payloads: dict[str, bytes] = {}
    turn_payloads: dict[str, bytes] = {}
    metadata_lines: dict[str, str] = {}
    for episode in episodes:
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

    destination = Path(out_dir)
    destination.mkdir(parents=True, exist_ok=False)
    public_ids = sorted(public_payloads)
    turn_ids = sorted(turn_payloads)
    for name, payloads in (("public", public_payloads), ("turns", turn_payloads)):
        directory = destination / name
        directory.mkdir()
        for identifier in sorted(payloads):
            (directory / f"{identifier}.json").write_bytes(payloads[identifier])
    private = destination / "private"
    private.mkdir()
    metadata_path = private / "metadata.jsonl"
    metadata_path.write_text(
        "".join(metadata_lines[identifier] for identifier in public_ids),
        encoding="utf-8",
    )
    return {
        "public_ids": public_ids,
        "turn_ids": turn_ids,
        "metadata_path": str(metadata_path),
    }

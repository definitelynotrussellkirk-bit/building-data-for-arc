"""Public projections for the task-local parametric authoring workspace.

The caller chooses the query to reveal. This helper exposes no episode counts,
labels, settings, or progress metadata and does not manage turn sequencing.
"""
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import public_challenge_bytes, public_challenge_id


def public_turn(episode: dict, query_index: int = 0) -> dict:
    """Return independent visible grids for demos and one selected query.

    Only visible content is validated: private query labels and unrevealed
    queries have no effect on the returned challenge or its content identifier.
    """
    if type(query_index) is not int or query_index < 0:
        raise ValueError("query_index must be a nonnegative exact integer")
    if not isinstance(episode, dict) or type(episode.get("test")) is not list:
        raise ValueError("episode must contain train/test lists")
    queries = episode["test"]
    if query_index >= len(queries):
        raise ValueError("query_index is outside the episode query list")
    try:
        selected = {
            "train": episode["train"],
            "test": [{"input": queries[query_index]["input"]}],
        }
    except (KeyError, TypeError) as error:
        raise ValueError("episode requires demos and a selected query input") from error
    # The shared serializer validates the visible grid grammar, strips private
    # pair fields, and provides an alias-free copy when decoded again.
    return json.loads(public_challenge_bytes(selected))


def write_public_turns(episodes, output_dir, query_index: int = 0) -> list[str]:
    """Write one public turn per episode to a fresh directory; return sorted IDs.

    All projections and duplicate checks finish before the directory is created.
    Filenames are SHA-256 IDs of the exact public bytes, with no private map or
    episode ordinal. Duplicate visible challenges are rejected even when their
    private metadata differs.
    """
    payloads = {}
    for episode in episodes:
        visible = public_turn(episode, query_index=query_index)
        payload = public_challenge_bytes(visible)
        identifier = public_challenge_id(visible)
        if identifier in payloads:
            raise ValueError("duplicate public challenge")
        payloads[identifier] = payload
    if not payloads:
        raise ValueError("episodes must contain at least one episode")

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=False)
    identifiers = sorted(payloads)
    for identifier in identifiers:
        (destination / f"{identifier}.json").write_bytes(payloads[identifier])
    return identifiers

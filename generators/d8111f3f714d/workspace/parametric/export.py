"""Write reviewed branch episodes with one actor-visible query per file.

This writer verifies format and publication boundaries, not reference semantics.
Only ``turns/`` is actor-visible; controllers and full episodes remain private.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from reviewer_support import public_challenge_bytes


SCHEMA = "arcpuzzles-native-branch-export-v1"


def json_bytes(value):
    try:
        return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("Private metadata must be finite serializable JSON") from error


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("Grid dimensions must be within 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("Grids must be rectangular with exact integer colors 0..9")
    return grid


def validate_episode(episode):
    """Validate every private label as well as the visible demonstration data."""
    if type(episode) is not dict:
        raise ValueError("Episode must be a JSON object")
    if type(episode.get("program_solution")) is not str or not episode["program_solution"].strip():
        raise ValueError("Episode must retain its private program_solution")
    seen = set()
    for split, minimum, maximum in (("train", 2, 6), ("test", 1, 4)):
        pairs = episode.get(split)
        if type(pairs) is not list or not minimum <= len(pairs) <= maximum:
            raise ValueError(f"{split} count must be within {minimum}..{maximum}")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("Every pair needs input and private output grids")
            source, answer = _grid(pair["input"]), _grid(pair["output"])
            if (len(source), len(source[0])) != (len(answer), len(answer[0])):
                raise ValueError("Branch outputs must have the same dimensions as inputs")
            fingerprint = json_bytes(source)
            if fingerprint in seen:
                raise ValueError("duplicate demonstration or query input")
            seen.add(fingerprint)
    # Round-trip the complete episode, preserving its JSON representation privately.
    return json.loads(json_bytes(episode))


def turn_bytes(episode, query_index):
    """Project one current query; omit query count, order and private metadata."""
    checked = validate_episode(episode)
    if type(query_index) is not int or not 0 <= query_index < len(checked["test"]):
        raise ValueError("query_index must be an exact integer naming an existing query")
    return public_challenge_bytes({"train": checked["train"],
                                   "test": [checked["test"][query_index]]})


def _write_new(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)


def write_episodes(episodes, out, *, context=None):
    """Validate the whole batch, reserve a fresh directory, publish manifest last.

    A failed write leaves no complete manifest. No existing destination is
    overwritten, including a dangling symlink or a concurrent reservation.
    """
    destination = Path(out)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    if type(episodes) is not list or not episodes:
        raise ValueError("A nonempty episode list is required")
    if context is None:
        context = {}
    if type(context) is not dict:
        raise ValueError("Private context must be a JSON object")
    context_raw = json_bytes(context)
    payloads, rows, controller_ids, actor_ids = {}, [], set(), set()
    digest = lambda raw: hashlib.sha256(raw).hexdigest()
    for episode in episodes:
        checked = validate_episode(episode)
        controller_raw = public_challenge_bytes(checked)
        controller_id = digest(controller_raw)
        if controller_id in controller_ids:
            raise ValueError("duplicate visible controller payload")
        controller_ids.add(controller_id)
        payloads[f"private/controllers/{controller_id}.json"] = controller_raw
        turns = []
        for pair in checked["test"]:
            raw = public_challenge_bytes({"train": checked["train"], "test": [pair]})
            identifier = digest(raw)
            if identifier in actor_ids:
                raise ValueError("duplicate visible actor payload")
            actor_ids.add(identifier)
            payloads[f"turns/{identifier}.json"] = raw
            turns.append(identifier)
        rows.append({"controller_id": controller_id, "turn_ids": turns, "episode": checked})
    rows.sort(key=lambda row: row["controller_id"])
    payloads["private/metadata.jsonl"] = b"".join(json_bytes(row) for row in rows)
    payloads["private/context.json"] = context_raw
    manifest = {
        "schema": SCHEMA, "complete": True, "native_acceptance": "owner_pending",
        "training_admitted": False, "episode_count": len(rows),
        "actor_visible_directory": "turns", "controller_directory": "private/controllers",
        "private_metadata": "private/metadata.jsonl", "private_context": "private/context.json",
        "controller_ids": sorted(controller_ids), "turn_ids": sorted(actor_ids),
        "files": {name: digest(raw) for name, raw in sorted(payloads.items())},
        "limits": "Format and publication checks only. Turn sequencing belongs to the consuming controller; this writer does not execute reference rules or accept source.",
    }
    manifest_raw = json_bytes(manifest)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()  # Atomic reservation; deliberately no exist_ok.
    for name, raw in sorted(payloads.items()):
        _write_new(destination / name, raw)
    _write_new(destination / "manifest.json", manifest_raw)
    return deepcopy(manifest)

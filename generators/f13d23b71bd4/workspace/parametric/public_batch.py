"""Visible-content-only public projection and deterministic batch writer.

Private seed, settings, rule source, and query labels never enter artifact bytes,
identifiers, filenames, or physical emission order.  The complete batch is
planned and duplicate-checked before the output directory is created.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import public_challenge_bytes, public_challenge_id

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_f13_public_family", _HERE / "family.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent parametric family")
_FAMILY = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_FAMILY)


def public_artifact(episode: Any, query_index: Any) -> dict[str, Any]:
    """Return one immutable public artifact derived only from visible fields."""
    challenge = _FAMILY.public_turn(episode, query_index)
    body = public_challenge_bytes(challenge)
    identifier = public_challenge_id(challenge)
    return {
        "id": identifier,
        "filename": f"challenge-{identifier}.json",
        "bytes": body,
    }


def plan_public_batch(requests: Iterable[tuple[Any, Any]]) -> list[dict[str, Any]]:
    """Build and sort the whole visible batch, rejecting duplicate IDs first."""
    planned = [public_artifact(episode, query_index) for episode, query_index in requests]
    identifiers = [item["id"] for item in planned]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate visible public challenge id")
    return sorted(planned, key=lambda item: item["filename"])


def write_public_batch(directory: str | Path, requests: Iterable[tuple[Any, Any]]) -> dict[str, Any]:
    """Write a prevalidated batch in visible-filename order without overwrites."""
    planned = plan_public_batch(requests)
    destination = Path(directory)
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    for item in planned:
        (destination / item["filename"]).write_bytes(item["bytes"])
    return {
        "count": len(planned),
        "filenames": [item["filename"] for item in planned],
        "identity_basis": "public_challenge_bytes",
        "emission_order": "visible_filename_sorted",
    }

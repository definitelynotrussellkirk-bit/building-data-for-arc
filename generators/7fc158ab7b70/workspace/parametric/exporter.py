"""Content-addressed exports for the task-local parameterized scaling family.

Call ``export_episode(out, episode)`` with the same output root for every
episode. Give a solver exactly one returned ``turns`` file at a time.
``public_archive`` exposes all query inputs and is controller-only. The return
value and ``private`` files are controller metadata; they must not accompany a
solver turn. Only canonical public bytes determine public paths and identities.

This module validates and separates an existing episode. It does not execute
its reference rule, establish label correctness, or confer native acceptance.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


def _load_support():
    """Load only a helper physically inside this checkout or copied runtime."""
    for parent in Path(__file__).resolve().parents:
        for relative in ("shared/runtime/reviewer_support.py", "reviewer_support.py"):
            path = parent / relative
            if not path.is_file():
                continue
            if not path.resolve().is_relative_to(parent.resolve()):
                raise ImportError("reviewer_support must not escape its own tree")
            spec = importlib.util.spec_from_file_location("scaling_export_support", path)
            if spec is None or spec.loader is None:
                raise ImportError(f"cannot load public export helpers from {path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise ImportError("no reviewer_support.py in this exporter's own tree")


SUPPORT = _load_support()


def _pairs(episode):
    if type(episode) is not dict or type(episode.get("pairs")) is not dict:
        raise ValueError("episode must be a dict containing a pairs dict")
    pairs = episode["pairs"]
    if any(type(pairs.get(split)) is not list or not pairs[split]
           for split in ("train", "test")):
        raise ValueError("episode pairs must contain nonempty train/test lists")
    return pairs


def public_challenge(episode):
    """Return a validated deep copy of the full controller-facing challenge."""
    return json.loads(SUPPORT.public_challenge_bytes(_pairs(episode)))


def public_turn(episode, index=0):
    """Return only demonstrations and one query; no index/count or future data."""
    pairs = _pairs(episode)
    if type(index) is not int or not 0 <= index < len(pairs["test"]):
        raise ValueError("index must be an integer identifying an existing query")
    # Validate only visible material here: private labels, annotations, and
    # future query contents cannot affect the bytes of the current turn.
    return json.loads(SUPPORT.public_challenge_bytes(
        {"train": pairs["train"], "test": [pairs["test"][index]]}))


def public_first_turn(episode):
    return public_turn(episode, 0)


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _public_blob(folder, challenge):
    raw = SUPPORT.public_challenge_bytes(challenge)
    identity = SUPPORT.public_challenge_id(challenge)
    if identity != _sha(raw):
        raise ValueError("public identity must hash exactly the exported public bytes")
    return {"path": f"{folder}/{identity}.json", "sha256": identity, "bytes": len(raw)}, raw


def _directory(path):
    if path.is_symlink():
        raise ValueError(f"export directory must not be a symlink: {path}")
    path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise ValueError(f"export directory is not a directory: {path}")


def _write_content(out, entry, raw):
    """Reuse exact content; never overwrite or follow an existing symlink."""
    path = out / entry["path"]
    if path.is_symlink():
        raise ValueError(f"export file must not be a symlink: {path}")
    try:
        with path.open("xb") as handle:
            handle.write(raw)
    except FileExistsError:
        if not path.is_file() or path.is_symlink() or path.read_bytes() != raw:
            raise FileExistsError(f"existing export differs from its content identity: {path}")


def export_episode(out, episode):
    """Export one existing episode; return private metadata with relative paths.

    Multiple episodes may share ``out``. Identical public payloads reuse the
    same paths even when settings, provenance, or query answers differ. Full
    private payloads have separate content identities, so changed provenance
    cannot silently replace an earlier private episode. No episode field is
    interpolated into a path.
    """
    # Build all payloads before creating directories. Invalid visible grids or
    # non-JSON private metadata therefore produce no partial public export.
    challenge = public_challenge(episode)
    archive, archive_raw = _public_blob("public_archive", challenge)
    turn_blobs = [_public_blob("turns", public_turn(episode, index))
                  for index in range(len(challenge["test"]))]
    turns = [entry for entry, _ in turn_blobs]
    public_id = archive["sha256"]
    turn_ids = [entry["sha256"] for entry in turns]
    private_raw = _json_bytes({
        "schema": "arcpuzzles-parametric-private-export-v1",
        "visibility": "controller_only",
        "episode": episode,
        "public_id": public_id,
        "public_archive": archive,
        "turn_ids": turn_ids,
        "turns": turns,
    })
    private_id = _sha(private_raw)
    private = {"path": f"private/{private_id}.json", "sha256": private_id,
               "bytes": len(private_raw)}
    out = Path(out).absolute()
    # Reject symlinks anywhere in the selected output path, and in each
    # managed directory, before any payload write can cross that boundary.
    if any(path.is_symlink() for path in (out, *out.parents)):
        raise ValueError("export output path must not contain symlinks")
    _directory(out)
    for folder in ("public_archive", "turns", "private"):
        _directory(out / folder)
    for entry, raw in [(archive, archive_raw), *turn_blobs, (private, private_raw)]:
        _write_content(out, entry, raw)
    return {"public_id": public_id, "public_archive": dict(archive),
            "turn_ids": list(turn_ids), "turns": [dict(entry) for entry in turns],
            "private": dict(private)}

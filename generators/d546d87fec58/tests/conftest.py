"""Portable-runtime compatibility for the retained legacy fixture.

The source-bound task-test runtime stores pinned authority data at ``data/``.
The immutable legacy fixture predates that layout and resolves the same files
under ``generators/<task>/data``.  During portable task-test runs only, expose
an ephemeral relative symlink to the already-copied runtime snapshot.  No
source checkout or authority file is modified.
"""
from __future__ import annotations

import os
from pathlib import Path


_TASK_ID = "d546d87fec58"


def pytest_sessionstart(session) -> None:  # noqa: ARG001 - pytest hook signature
    home = os.environ.get("ARCPUZZLES_HOME")
    if not home:
        return

    runtime = Path(home).resolve()
    authority = runtime / "data"
    legacy = runtime / "generators" / _TASK_ID / "data"
    if not (authority / "canonical" / "puzzles.jsonl").is_file():
        raise RuntimeError(f"Portable authority snapshot is missing: {authority}")
    if legacy.exists() or legacy.is_symlink():
        if legacy.resolve() != authority:
            raise RuntimeError(f"Unexpected legacy data path: {legacy}")
        return

    legacy.parent.mkdir(parents=True, exist_ok=True)
    relative_target = os.path.relpath(authority, start=legacy.parent)
    legacy.symlink_to(relative_target, target_is_directory=True)

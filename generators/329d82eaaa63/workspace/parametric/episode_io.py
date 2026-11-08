"""Strict sequential public/private bundle writer for a complete episode.

Every public file contains all demonstrations and exactly one query input.  It
contains no seed, setting, reference program, answer, query index, or total-count
hint.  Private records bind those controller-side fields to the public hash.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from reviewer_support import public_challenge_bytes

SCHEMA = "arcpuzzles-sequential-public-private-v1"


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid must be rectangular with exact ARC integers 0..9")
    return value


def _episode(value):
    if not isinstance(value, dict):
        raise ValueError("episode must be an object")
    if type(value.get("task_id")) is not str or type(value.get("seed")) is not int:
        raise ValueError("episode needs task_id and exact integer seed")
    if not isinstance(value.get("settings"), dict) or type(value.get("program_solution")) is not str:
        raise ValueError("episode needs private settings and program_solution")
    normalized = {}
    for split in ("train", "test"):
        pairs = value.get(split)
        if type(pairs) is not list or not pairs:
            raise ValueError(f"episode needs nonempty {split} pairs")
        rows = []
        for pair in pairs:
            if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
                raise ValueError("each pair needs input and output")
            rows.append({"input": _grid(pair["input"]), "output": _grid(pair["output"])})
        normalized[split] = rows
    inputs = [json.dumps(pair["input"], separators=(",", ":"))
              for pairs in normalized.values() for pair in pairs]
    if len(inputs) != len(set(inputs)):
        raise ValueError("episode inputs must be distinct")
    return normalized


def _safe_member(root, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in str(relative):
        raise ValueError("unsafe bundle member path")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("bundle member escapes destination")
    return resolved


def write_bundle(episodes, destination):
    if type(episodes) is not list or not episodes:
        raise ValueError("episodes must be a nonempty list")
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    public_files = {}
    private_rows = []
    episode_keys = set()
    for episode in episodes:
        normalized = _episode(episode)
        episode_key = hashlib.sha256(_raw({
            "task_id": episode["task_id"],
            "seed": episode["seed"],
            "settings": episode["settings"],
            "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest(),
        })).hexdigest()
        if episode_key in episode_keys:
            # Same private episode necessarily repeats every visible turn.
            raise ValueError("duplicate visible challenge")
        episode_keys.add(episode_key)
        for pair in normalized["test"]:
            visible = {"train": normalized["train"], "test": [{"input": pair["input"]}]}
            raw = public_challenge_bytes(visible)
            public_id = hashlib.sha256(raw).hexdigest()
            if public_id in public_files:
                raise ValueError("duplicate visible challenge")
            public_files[public_id] = raw
            private_rows.append({
                "id": public_id,
                "episode": episode_key,
                "task_id": episode["task_id"],
                "seed": episode["seed"],
                "settings": episode["settings"],
                "program": episode["program_solution"],
                "answer": pair["output"],
            })

    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent))
    try:
        public_dir = temporary / "public"
        public_dir.mkdir()
        file_rows = []
        for public_id, raw in sorted(public_files.items()):
            relative = f"public/{public_id}.json"
            path = temporary / relative
            path.write_bytes(raw)
            file_rows.append({"path": relative, "bytes": len(raw), "sha256": public_id})
        private_raw = b"".join(_raw(row) for row in sorted(private_rows, key=lambda row: row["id"]))
        (temporary / "private.jsonl").write_bytes(private_raw)
        file_rows.append({
            "path": "private.jsonl",
            "bytes": len(private_raw),
            "sha256": hashlib.sha256(private_raw).hexdigest(),
        })
        manifest = {
            "schema": SCHEMA,
            "episodes": len(episodes),
            "public_challenges": len(public_files),
            "files": sorted(file_rows, key=lambda row: row["path"]),
        }
        manifest_raw = _raw(manifest)
        (temporary / "manifest.json").write_bytes(manifest_raw)
        os.rename(temporary, destination)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {
        "schema": SCHEMA,
        "episodes": len(episodes),
        "public_challenges": len(public_files),
        "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
    }


def verify_bundle(destination):
    destination = Path(destination)
    manifest_path = destination / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("missing manifest")
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    if manifest.get("schema") != SCHEMA:
        raise ValueError("unexpected bundle schema")
    rows = manifest.get("files")
    if type(rows) is not list or not rows:
        raise ValueError("manifest files are missing")
    expected_paths = {"manifest.json"}
    public_ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}:
            raise ValueError("malformed manifest file row")
        path = _safe_member(destination, row["path"])
        if not path.is_file():
            raise ValueError("manifest member is missing")
        raw = path.read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("bundle member hash mismatch")
        expected_paths.add(row["path"])
        if row["path"].startswith("public/"):
            name = Path(row["path"]).stem
            if name != row["sha256"]:
                raise ValueError("public filename/hash mismatch")
            value = json.loads(raw)
            if set(value) != {"train", "test"} or len(value["test"]) != 1 or set(value["test"][0]) != {"input"}:
                raise ValueError("public challenge leaks private fields")
            if public_challenge_bytes(value) != raw:
                raise ValueError("public challenge bytes are not canonical")
            public_ids.add(name)
    actual_paths = {path.relative_to(destination).as_posix()
                    for path in destination.rglob("*") if path.is_file()}
    if actual_paths != expected_paths:
        raise ValueError("bundle has unmanifested or missing files")
    private_rows = [json.loads(line) for line in (destination / "private.jsonl").read_text().splitlines()]
    if {row.get("id") for row in private_rows} != public_ids or len(private_rows) != len(public_ids):
        raise ValueError("private/public ID coverage mismatch")
    if manifest.get("public_challenges") != len(public_ids):
        raise ValueError("public challenge count mismatch")
    episodes = {row.get("episode") for row in private_rows}
    if manifest.get("episodes") != len(episodes):
        raise ValueError("episode count mismatch")
    return {
        "schema": SCHEMA,
        "episodes": manifest["episodes"],
        "public_challenges": manifest["public_challenges"],
        "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
    }

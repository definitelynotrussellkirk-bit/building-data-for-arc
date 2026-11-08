#!/usr/bin/env python3
"""Publish qualified examples as one-query public turns plus private labels.

This is an authoring exporter, not a training controller or acceptance command.
It reuses the native source/execution binding check and existing public-byte
projection.  Labels must already have been executed by native qualification.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
_path = Path(__file__).with_name("prototype.py")
_name = "_room_export_" + hashlib.sha256(str(_path).encode()).hexdigest()
_spec = importlib.util.spec_from_file_location(_name, _path)
_prototype = importlib.util.module_from_spec(_spec)
sys.modules[_name] = _prototype
_spec.loader.exec_module(_prototype)


def build_payloads(episodes):
    """Pure projection. Caller must establish qualification before publication."""
    from reviewer_support import public_challenge_bytes, public_challenge_id
    public, private = {}, []
    for episode in episodes:
        ids = []
        for query_index in range(len(episode["test"])):
            turn = _prototype.public_turn(episode, query_index)
            raw = public_challenge_bytes(turn)
            name = public_challenge_id(turn) + ".json"
            if name in public:
                raise ValueError("duplicate visible public turn")
            public[name] = raw
            ids.append(name[:-5])
        private.append({**copy.deepcopy(episode), "reference": "qualified_authoring",
                        "public_turn_ids": ids, "training_admitted": False})
    return dict(sorted(public.items())), sorted(private, key=lambda e: e["public_turn_ids"][0])


def export_qualified(qualification, out):
    from arcpuzzles.review_witness import _qualified
    qualification, out = Path(qualification), Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(f"choose a new output directory: {out}")
    report, execution = _qualified(ROOT, qualification)
    public, private = build_payloads(execution["episodes"])
    private_raw = b"".join((json.dumps(row, sort_keys=True, allow_nan=False)+"\n").encode()
                           for row in private)
    manifest = {
        "schema": "arcpuzzles-room-scope-authoring-export-v1",
        "task_id": report["task_id"], "qualification_sha256": hashlib.sha256(qualification.read_bytes()).hexdigest(),
        "source_binding": report["source_binding"], "racket": execution["racket"],
        "episodes": len(private), "public_turns": len(public),
        "queries_per_episode": [len(e["test"]) for e in private],
        "public": [{"path": "public/"+name, "sha256": hashlib.sha256(raw).hexdigest()}
                   for name, raw in public.items()],
        "private": {"path": "private.jsonl", "sha256": hashlib.sha256(private_raw).hexdigest()},
        "owner_acceptance": "pending", "training_admitted": False,
        "projection": "Give the model one selected public turn only; all labels, ordering and remaining queries stay controller-side."
    }
    (out / "public").mkdir(parents=True, exist_ok=False)
    for name, raw in public.items():
        (out / "public" / name).write_bytes(raw)
    (out / "private.jsonl").write_bytes(private_raw)
    # Publication marker is last; a partial write is never a complete export.
    (out / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2)+"\n")
    return {"episodes": len(private), "public_turns": len(public),
            "manifest": str(out / "manifest.json"), "training_admitted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(export_qualified(args.qualification, args.out), sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Execute the current d5a059b0f3a6 prototype writer and check public bytes/IDs."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from reviewer_support import (
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "d5a059b0f3a6"
EXPECTED_GENERATOR_SHA256 = "8276303d89c43e360a4990344a3ccf04a0321e0b490aaa4300c36e3d0c86975d"
SEED = 20261023


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    base = root / "generators" / TASK_ID / "workspace" / "parametric"
    prototype_path = base / "prototype.py"
    verify_path = base / "verify.py"
    prototype = _load("d5_parametric_audit_prototype", prototype_path)
    verifier = _load("d5_parametric_audit_verifier", verify_path)
    _generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    if generator_sha256 != EXPECTED_GENERATOR_SHA256:
        raise RuntimeError(
            f"source drift: expected {EXPECTED_GENERATOR_SHA256}, got {generator_sha256}"
        )

    episodes = {
        setting: prototype.build_episode(
            SEED,
            setting=setting,
            n_train=prototype.DEFAULT_N_TRAIN,
            n_test=prototype.DEFAULT_N_TEST,
        )
        for setting in prototype.ALLOWED_SETTINGS
    }
    programs = {
        setting: prototype.program_for(setting)
        for setting in prototype.ALLOWED_SETTINGS
    }

    out_path = args.out.resolve()
    retained_public = out_path.parent / "public"
    if retained_public.exists():
        shutil.rmtree(retained_public)
    retained_public.mkdir(parents=True)

    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="d5-public-writer-audit-") as temp:
        artifact_dir = Path(temp) / "artifacts"
        verifier._materialize(
            artifact_dir=artifact_dir,
            seed=SEED,
            prototype=prototype,
            programs=programs,
            episodes=episodes,
            generator_sha256=generator_sha256,
        )
        for source in sorted((artifact_dir / "public" / "challenges").glob("*.json")):
            destination = retained_public / source.name
            shutil.copyfile(source, destination)
            raw = destination.read_bytes()
            challenge = json.loads(raw)
            canonical = public_challenge_bytes(challenge)
            visible_id = destination.stem.removeprefix("challenge-")
            expected_id = public_challenge_id(challenge)
            rows.append(
                {
                    "path": str(destination.relative_to(root.parent.resolve())),
                    "filename": destination.name,
                    "visible_id": visible_id,
                    "visible_id_hex_length": len(visible_id),
                    "saved_sha256": hashlib.sha256(raw).hexdigest(),
                    "canonical_bytes_sha256": hashlib.sha256(canonical).hexdigest(),
                    "expected_full_public_id": expected_id,
                    "filename_matches_saved_bytes": visible_id == hashlib.sha256(raw).hexdigest(),
                    "filename_matches_canonical_public_id": visible_id == expected_id,
                    "saved_bytes_are_canonical": raw == canonical,
                    "demonstrations": len(challenge["train"]),
                    "queries": len(challenge["test"]),
                }
            )

    finding_reproduced = len(rows) == len(prototype.ALLOWED_SETTINGS) and all(
        row["visible_id_hex_length"] == 16
        and not row["filename_matches_saved_bytes"]
        and not row["filename_matches_canonical_public_id"]
        and not row["saved_bytes_are_canonical"]
        for row in rows
    )
    report = {
        "schema": "arcpuzzles-bounded-audit-probe-v1",
        "status": "finding" if finding_reproduced else "not_reproduced",
        "task_id": TASK_ID,
        "finding": "prototype_public_export_nonconformance",
        "generator_path": str(generator_path),
        "generator_sha256": generator_sha256,
        "prototype_path": str(prototype_path.relative_to(root)),
        "prototype_sha256": _sha256(prototype_path),
        "writer_path": str(verify_path.relative_to(root)),
        "writer_sha256": _sha256(verify_path),
        "seed": SEED,
        "rows": rows,
        "summary": {
            "public_files": len(rows),
            "truncated_identifiers": sum(row["visible_id_hex_length"] != 64 for row in rows),
            "noncanonical_saved_bytes": sum(not row["saved_bytes_are_canonical"] for row in rows),
            "incorrect_saved_byte_ids": sum(not row["filename_matches_saved_bytes"] for row in rows),
        },
        "impact": (
            "The current unapproved task-local writer advertises content-derived public IDs "
            "but writes pretty-printed bytes under 16-hex names. It therefore fails the shared "
            "exact-saved-byte/full-SHA-256 contract required before promotion or deduplication."
        ),
        "scope": (
            "public export conformance for the task-local prototype only; production generator "
            "and canonical labels were not changed or re-audited"
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["summary"], "out": str(args.out)}, sort_keys=True))
    return 0 if finding_reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())

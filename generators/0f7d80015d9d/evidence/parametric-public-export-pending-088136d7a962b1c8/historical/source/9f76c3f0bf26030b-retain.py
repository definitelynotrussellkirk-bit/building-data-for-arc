#!/usr/bin/env python3
"""Retain a compact, source-bound snapshot from a successful verifier run.

The full private execution trace stays under ``WORK/checks/parametric``. This
utility copies only opaque public episodes, their exact Racket programs, and a
compact private verification summary into the selected task workspace, then
writes the discovery manifest consumed by the parametric-priority index.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
for dependency in (REPO, REPO / "shared" / "runtime"):
    text = str(dependency)
    if text not in sys.path:
        sys.path.insert(0, text)

from reviewer_support import load_selected_generator, public_challenge_id  # noqa: E402

TASK_ID = "0f7d80015d9d"
ASSIGNMENT_ID = "review-088136d7a962b1c8"


def _sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _reset(path: Path, *, overwrite: bool) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"retained output already exists: {path}; use --overwrite")
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    path.mkdir(parents=True, exist_ok=True)


def _copy_checked(source: Path, destination: Path, expected: dict[str, Any]) -> None:
    raw = source.read_bytes()
    if len(raw) != expected["bytes"] or _sha_bytes(raw) != expected["sha256"]:
        raise ValueError(f"verification artifact hash mismatch: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)


def _inventory(paths: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(paths):
        relative = path.relative_to(REPO).as_posix()
        rows.append({"path": relative, "sha256": _sha_file(path), "bytes": path.stat().st_size})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checks-dir", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    checks = Path(args.checks_dir).resolve()
    checks_manifest_path = checks / "manifest.json"
    checked = json.loads(checks_manifest_path.read_text(encoding="utf-8"))
    if checked.get("schema") != "0f7d80015d9d-parametric-verification-v1" or checked.get("status") != "passed":
        raise ValueError("checks directory is not a successful task verifier output")
    if checked.get("task_id") != TASK_ID or checked.get("counts", {}).get("episodes") != 4:
        raise ValueError("checks directory does not contain the expected four-setting task evidence")
    if checked.get("counts", {}).get("query_pairs_per_episode") != 4:
        raise ValueError("retained evidence requires four queries per episode")

    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=REPO)
    if checked.get("generator_sha256") != generator_sha:
        raise ValueError("verification output is stale relative to the selected generator")

    examples_dir = HERE / "examples"
    racket_dir = HERE / "racket"
    evidence_dir = HERE / "evidence"
    reported_dir = evidence_dir / "reviewer-reported"
    _reset(examples_dir, overwrite=args.overwrite)
    _reset(racket_dir, overwrite=args.overwrite)
    _reset(reported_dir, overwrite=args.overwrite)
    manifest_path = evidence_dir / "manifest.json"
    if manifest_path.exists():
        if not args.overwrite:
            raise FileExistsError(f"retained manifest exists: {manifest_path}; use --overwrite")
        manifest_path.unlink()

    retained_episodes = []
    for episode in checked["episodes"]:
        public_id = episode["public_id"]
        if not isinstance(public_id, str) or len(public_id) != 64:
            raise ValueError(f"invalid opaque public ID: {public_id!r}")
        source_dir = checks / public_id
        public_source = source_dir / "public.json"
        rule_source = source_dir / "rule.rkt"
        public_target = examples_dir / f"{public_id}.json"
        rule_target = racket_dir / f"{public_id}.rkt"
        _copy_checked(public_source, public_target, episode["files"]["public.json"])
        _copy_checked(rule_source, rule_target, episode["files"]["rule.rkt"])
        public = json.loads(public_target.read_text(encoding="utf-8"))
        if public_challenge_id(public) != public_id:
            raise ValueError(f"public filename is not derived from visible bytes: {public_id}")
        if len(public.get("train", [])) != 3 or len(public.get("test", [])) != 4:
            raise ValueError(f"retained episode has wrong demo/query counts: {public_id}")
        if any(set(pair) != {"input"} for pair in public["test"]):
            raise ValueError(f"retained public query leaks a label: {public_id}")
        retained_episodes.append(
            {
                "public_id": public_id,
                "setting": episode["setting"],
                "setting_key": episode["setting_key"],
                "demonstration_survivors": episode["demonstration_survivors"],
                "train_count": episode["train_count"],
                "query_count": episode["query_count"],
                "public_sha256": _sha_file(public_target),
                "racket_sha256": _sha_file(rule_target),
            }
        )

    runtime = checked.get("racket_runtime", {})
    summary = {
        "schema": "0f7d80015d9d-retained-parametric-evidence-v1",
        "status": "passed",
        "scope": "proposed task-local prototype; not canonical approval or training admission",
        "assignment_id": ASSIGNMENT_ID,
        "task_id": TASK_ID,
        "generator_sha256": generator_sha,
        "canonical_rule_hash": generator.RULE_HASH,
        "canonical_program_sha256": checked["canonical_program_sha256"],
        "checks_manifest_sha256": _sha_file(checks_manifest_path),
        "command": {
            "cwd": "repo",
            "argv": [
                "python3",
                "generators/0f7d80015d9d/workspace/parametric/verify.py",
                "--all-settings",
                "--output-dir",
                "../checks/parametric",
                "--overwrite",
            ],
        },
        "counts": checked["counts"],
        "parameters": checked["parameterization"],
        "prototype_source_sha256": checked["prototype_source_sha256"],
        "episodes": sorted(retained_episodes, key=lambda row: row["public_id"]),
        "racket_runtime": {
            key: runtime.get(key)
            for key in (
                "schema",
                "backend",
                "binary_sha256",
                "bridge_sha256",
                "prelude_sha256",
                "candidate_symbol_policy_sha256",
                "protected",
                "deterministic",
                "security_canary",
            )
        },
        "limitations": checked["limitations"],
    }
    summary_path = reported_dir / "verification-summary.json"
    _write_json(summary_path, summary)

    test_path = REPO / "generators" / TASK_ID / "tests" / "test_parametric_stamp_rule.py"
    retained_files = [
        HERE / "README.md",
        HERE / "prototype.py",
        HERE / "verify.py",
        HERE / "retain.py",
        HERE / "check_retained.py",
        test_path,
        summary_path,
        *examples_dir.glob("*.json"),
        *racket_dir.glob("*.rkt"),
    ]
    manifest = {
        "schema": "arcpuzzles-parametric-prototype-evidence-v1",
        "task_id": TASK_ID,
        "generator_sha256": generator_sha,
        "canonical_rule_hash": generator.RULE_HASH,
        "parameters": {
            "midpoint_side": ["right", "left"],
            "stamp_relation": ["opposite", "same"],
        },
        "default_setting": {"midpoint_side": "right", "stamp_relation": "opposite"},
        "episode_counts": {"demonstrations": 3, "queries": 4, "settings": 4},
        "production_parametric_api": False,
        "public_identifier_status": "opaque_visible_bytes_v1",
        "variant_approved": False,
        "verification_status": "reviewer_reported",
        "return_id": ASSIGNMENT_ID + ":v0001",
        "scope": (
            "Four proposed episode-fixed stamp-rule settings; exact Racket labels, four opaque public episodes, "
            "and demonstration-only identifiability are retained. Canonical production and approval remain unchanged."
        ),
        "files": _inventory(retained_files),
    }
    _write_json(manifest_path, manifest)
    print(
        json.dumps(
            {
                "status": "retained",
                "manifest": str(manifest_path),
                "files": len(manifest["files"]),
                "episodes": len(retained_episodes),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

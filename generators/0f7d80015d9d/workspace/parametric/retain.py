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
import string
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
for dependency in (REPO, REPO / "shared" / "runtime"):
    text = str(dependency)
    if text not in sys.path:
        sys.path.insert(0, text)

from reviewer_support import (  # noqa: E402
    load_selected_generator,
    public_challenge_bytes,
)

TASK_ID = "0f7d80015d9d"
ASSIGNMENT_ID = "review-6535e31bbdf64206"


def _sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_reported_summary(
    path: Path,
    value: dict[str, Any],
    *,
    overwrite: bool = False,
) -> None:
    """Replace only the current summary, preserving sibling review evidence."""
    path = Path(path)
    _require_resettable(path, overwrite=overwrite)
    _write_json(path, value)


def verification_command(checked: dict[str, Any]) -> dict[str, Any]:
    """Normalize the verifier's recorded invocation for a portable receipt."""
    argv = checked.get("argv")
    if (
        not isinstance(argv, list)
        or not argv
        or any(not isinstance(argument, str) or not argument for argument in argv)
    ):
        raise ValueError("verification manifest has no usable argv")
    normalized = list(argv)
    if normalized[0] != "python3":
        normalized.insert(0, "python3")
    return {"cwd": "repo", "argv": normalized}


def _require_resettable(path: Path, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"retained output already exists: {path}; use --overwrite")


def _reset(path: Path, *, overwrite: bool) -> None:
    _require_resettable(path, overwrite=overwrite)
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    path.mkdir(parents=True, exist_ok=True)


def _read_checked(source: Path, expected: dict[str, Any]) -> bytes:
    if not source.is_file() or source.is_symlink():
        raise ValueError(f"verification artifact is missing or symlinked: {source}")
    raw = source.read_bytes()
    expected_bytes = expected.get("bytes")
    expected_sha = expected.get("sha256")
    if (
        not isinstance(expected_bytes, int)
        or isinstance(expected_bytes, bool)
        or not isinstance(expected_sha, str)
        or len(raw) != expected_bytes
        or _sha_bytes(raw) != expected_sha
    ):
        raise ValueError(f"verification artifact hash mismatch: {source}")
    return raw


def _inventory(paths: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(paths):
        relative = path.relative_to(REPO).as_posix()
        rows.append(
            {
                "path": relative,
                "sha256": _sha_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return rows


def retain_verified_batch(
    *,
    checks_dir: Path,
    checked: dict[str, Any],
    examples_dir: Path,
    racket_dir: Path,
    overwrite: bool = False,
) -> list[dict[str, Any]]:
    """Preflight a verifier batch completely, then retain it in public-ID order."""
    checks_dir = Path(checks_dir).resolve()
    examples_dir = Path(examples_dir)
    racket_dir = Path(racket_dir)
    if examples_dir.resolve() == racket_dir.resolve():
        raise ValueError("examples and Racket destinations must be distinct")

    episodes = checked.get("episodes")
    if not isinstance(episodes, list) or not episodes:
        raise ValueError("verification manifest has no episode rows")

    planned: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_payloads: set[bytes] = set()
    required_files = {"public.json", "private.json", "rule.rkt"}
    for episode in episodes:
        if not isinstance(episode, dict):
            raise ValueError("verification episode row is not an object")
        public_id = episode.get("public_id")
        if (
            not isinstance(public_id, str)
            or len(public_id) != 64
            or public_id != public_id.lower()
            or any(character not in string.hexdigits.lower() for character in public_id)
        ):
            raise ValueError(f"invalid opaque public ID: {public_id!r}")
        if public_id in seen_ids:
            raise ValueError(f"duplicate public ID in verification manifest: {public_id}")
        seen_ids.add(public_id)

        files = episode.get("files")
        if not isinstance(files, dict) or set(files) != required_files:
            raise ValueError(f"verification file inventory differs for {public_id}")
        source_dir = checks_dir / public_id
        raw_files = {
            name: _read_checked(source_dir / name, files[name])
            for name in sorted(required_files)
        }
        public_raw = raw_files["public.json"]
        if public_raw in seen_payloads:
            raise ValueError(f"duplicate public payload in verification manifest: {public_id}")
        seen_payloads.add(public_raw)
        if _sha_bytes(public_raw) != public_id:
            raise ValueError(f"public raw bytes do not hash to opaque ID: {public_id}")
        try:
            public = json.loads(public_raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"public challenge is not canonical JSON: {public_id}") from exc
        if public_raw != public_challenge_bytes(public):
            raise ValueError(f"public challenge bytes are not canonical: {public_id}")
        if len(public.get("train", [])) != 3 or len(public.get("test", [])) != 4:
            raise ValueError(f"retained episode has wrong demo/query counts: {public_id}")
        if any(set(pair) != {"input"} for pair in public["test"]):
            raise ValueError(f"retained public query leaks a label: {public_id}")

        planned.append(
            {
                "public_id": public_id,
                "public_bytes": public_raw,
                "racket_bytes": raw_files["rule.rkt"],
                "setting": episode["setting"],
                "setting_key": episode["setting_key"],
                "demonstration_survivors": episode["demonstration_survivors"],
                "train_count": episode["train_count"],
                "query_count": episode["query_count"],
            }
        )

    planned.sort(key=lambda row: row["public_id"])
    _require_resettable(examples_dir, overwrite=overwrite)
    _require_resettable(racket_dir, overwrite=overwrite)
    _reset(examples_dir, overwrite=overwrite)
    _reset(racket_dir, overwrite=overwrite)

    retained: list[dict[str, Any]] = []
    for row in planned:
        public_id = row["public_id"]
        public_target = examples_dir / f"{public_id}.json"
        rule_target = racket_dir / f"{public_id}.rkt"
        public_target.write_bytes(row["public_bytes"])
        rule_target.write_bytes(row["racket_bytes"])
        retained.append(
            {
                "public_id": public_id,
                "setting": row["setting"],
                "setting_key": row["setting_key"],
                "demonstration_survivors": row["demonstration_survivors"],
                "train_count": row["train_count"],
                "query_count": row["query_count"],
                "public_sha256": _sha_bytes(row["public_bytes"]),
                "racket_sha256": _sha_bytes(row["racket_bytes"]),
            }
        )
    return retained


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checks-dir", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    checks = Path(args.checks_dir).resolve()
    checks_manifest_path = checks / "manifest.json"
    checked = json.loads(checks_manifest_path.read_text(encoding="utf-8"))
    if (
        checked.get("schema") != "0f7d80015d9d-parametric-verification-v1"
        or checked.get("status") != "passed"
    ):
        raise ValueError("checks directory is not a successful task verifier output")
    if (
        checked.get("task_id") != TASK_ID
        or checked.get("counts", {}).get("episodes") != 4
    ):
        raise ValueError(
            "checks directory does not contain the expected four-setting task evidence"
        )
    if checked.get("counts", {}).get("query_pairs_per_episode") != 4:
        raise ValueError("retained evidence requires four queries per episode")

    generator, _generator_path, generator_sha = load_selected_generator(
        TASK_ID, root=REPO
    )
    if checked.get("generator_sha256") != generator_sha:
        raise ValueError("verification output is stale relative to the selected generator")

    examples_dir = HERE / "examples"
    racket_dir = HERE / "racket"
    evidence_dir = HERE / "evidence"
    reported_dir = evidence_dir / "reviewer-reported"
    summary_path = reported_dir / "verification-summary.json"
    manifest_path = evidence_dir / "manifest.json"
    _require_resettable(summary_path, overwrite=args.overwrite)
    _require_resettable(manifest_path, overwrite=args.overwrite)

    retained_episodes = retain_verified_batch(
        checks_dir=checks,
        checked=checked,
        examples_dir=examples_dir,
        racket_dir=racket_dir,
        overwrite=args.overwrite,
    )
    if manifest_path.exists():
        manifest_path.unlink()

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
        "command": verification_command(checked),
        "counts": checked["counts"],
        "parameters": checked["parameterization"],
        "prototype_source_sha256": checked["prototype_source_sha256"],
        "episodes": retained_episodes,
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
    write_reported_summary(summary_path, summary, overwrite=args.overwrite)

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
        "default_setting": {
            "midpoint_side": "right",
            "stamp_relation": "opposite",
        },
        "episode_counts": {"demonstrations": 3, "queries": 4, "settings": 4},
        "production_parametric_api": False,
        "public_identifier_status": "opaque_visible_bytes_v1",
        "variant_approved": False,
        "verification_status": "reviewer_reported",
        "return_id": ASSIGNMENT_ID + ":v0001",
        "scope": (
            "Four proposed episode-fixed stamp-rule settings; exact Racket labels, "
            "four opaque public episodes, and demonstration-only identifiability "
            "are retained. Canonical production and approval remain unchanged."
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

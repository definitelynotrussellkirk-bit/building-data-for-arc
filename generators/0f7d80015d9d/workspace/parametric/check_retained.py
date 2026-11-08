#!/usr/bin/env python3
"""Verify the retained source-bound parametric snapshot outside staged tests.

The portable ``task_tests`` stage intentionally excludes directories named
``evidence``. This checker therefore runs against the owner checkout and proves
that the discovery manifest, opaque public episodes, exact Racket files, and
source bindings are current.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
for dependency in (REPO, REPO / "shared" / "runtime"):
    text = str(dependency)
    if text not in sys.path:
        sys.path.insert(0, text)

from reviewer_support import public_challenge_bytes  # noqa: E402

TASK_ID = "0f7d80015d9d"
RULE_HASH = "9744dc525afc"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_canonical_public(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        public = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"retained public challenge is not JSON: {path.name}") from exc
    if raw != public_challenge_bytes(public):
        raise ValueError(
            f"retained public challenge bytes are not canonical: {path.name}"
        )
    if hashlib.sha256(raw).hexdigest() != path.stem:
        raise ValueError(
            f"retained public challenge does not hash to filename: {path.name}"
        )
    return public


def check() -> dict[str, Any]:
    home = REPO / "generators" / TASK_ID
    evidence_root = HERE / "evidence"
    manifest_path = evidence_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    generator_path = home / "generator.py"
    if manifest.get("task_id") != TASK_ID:
        raise ValueError("retained manifest task ID differs")
    if manifest.get("generator_sha256") != _sha(generator_path):
        raise ValueError("retained manifest is stale relative to generator.py")
    if manifest.get("canonical_rule_hash") != RULE_HASH:
        raise ValueError("retained manifest canonical rule hash differs")
    if manifest.get("verification_status") != "reviewer_reported":
        raise ValueError("retained manifest lacks reviewer-reported status")
    if manifest.get("variant_approved") is not False or manifest.get("production_parametric_api") is not False:
        raise ValueError("retained prototype incorrectly claims approval or production API")
    expected_parameters = {
        "midpoint_side": ["right", "left"],
        "stamp_relation": ["opposite", "same"],
    }
    if manifest.get("parameters") != expected_parameters:
        raise ValueError("retained parameter declaration differs")

    declared: dict[str, dict[str, Any]] = {}
    for item in manifest.get("files", []):
        relative = item.get("path")
        if not isinstance(relative, str) or relative in declared:
            raise ValueError(f"invalid or repeated retained path: {relative!r}")
        path = REPO / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"retained file is missing or symlinked: {relative}")
        if item.get("sha256") != _sha(path) or item.get("bytes") != path.stat().st_size:
            raise ValueError(f"retained file hash/size differs: {relative}")
        declared[relative] = item

    examples = sorted((HERE / "examples").glob("*.json"))
    rules = sorted((HERE / "racket").glob("*.rkt"))
    if len(examples) != 4 or len(rules) != 4:
        raise ValueError("retained snapshot must have four public episodes and four rules")
    if {path.stem for path in examples} != {path.stem for path in rules}:
        raise ValueError("retained public/rule opaque IDs differ")
    private_tokens = ("opposite", "same", "midpoint", "left", "right")
    if any(token in path.name for path in examples + rules for token in private_tokens):
        raise ValueError("retained public/rule filename leaks private setting semantics")

    public_ids = []
    for path in examples:
        public = _load_canonical_public(path)
        if len(public.get("train", [])) != 3 or len(public.get("test", [])) != 4:
            raise ValueError(f"retained demo/query counts differ: {path.name}")
        if any(set(pair) != {"input"} for pair in public["test"]):
            raise ValueError(f"retained query leaks an output or metadata: {path.name}")
        public_ids.append(path.stem)

    summary_path = evidence_root / "reviewer-reported" / "verification-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    expected_counts = {
        "episodes": 4,
        "query_pairs_per_episode": 4,
        "racket_executions": 112,
        "settings_available": 4,
        "train_pairs_per_episode": 3,
    }
    if summary.get("counts") != expected_counts:
        raise ValueError("retained protected-execution counts differ")
    if sorted(row.get("public_id") for row in summary.get("episodes", [])) != sorted(public_ids):
        raise ValueError("retained private summary/public IDs differ")
    if any(len(row.get("demonstration_survivors", [])) != 1 for row in summary["episodes"]):
        raise ValueError("retained demonstrations do not uniquely identify every setting")

    return {
        "schema": "0f7d80015d9d-retained-parametric-check-v1",
        "status": "passed",
        "task_id": TASK_ID,
        "generator_sha256": _sha(generator_path),
        "manifest_sha256": _sha(manifest_path),
        "declared_files": len(declared),
        "public_ids": sorted(public_ids),
        "counts": expected_counts,
        "public_filenames_opaque": True,
        "variants_approved": False,
        "production_parametric_api": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    args = parser.parse_args()
    result = check()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    print(json.dumps({"status": result["status"], "declared_files": result["declared_files"], "out": args.out}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

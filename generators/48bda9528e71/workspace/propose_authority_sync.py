#!/usr/bin/env python3
"""Build or verify the OPTIONAL, hash-bound authority-formatting proposal.

This task-local tool never writes to the repository's authority files. A
maintainer may select the generated patch separately from the generator repair.
Only the two selected target_code JSON strings change; archival raw_code and
the canonical ledger stay untouched.

From the repository root:
  python3 generators/48bda9528e71/workspace/propose_authority_sync.py build \
    --repo . --out ../checks/authority-proposal/generated
  python3 generators/48bda9528e71/workspace/propose_authority_sync.py check \
    --repo . --state original
  git apply --check ../checks/authority-proposal/generated/authority-sync.patch
  # Apply only after this separate shared-file proposal has been selected:
  git apply ../checks/authority-proposal/generated/authority-sync.patch
  python3 generators/48bda9528e71/workspace/propose_authority_sync.py check \
    --repo . --state patched

The checker is specific to the inspected source hashes. Refusals require new
review of changed sources; do not refresh constants merely to bypass a guard.
"""

from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import json
from pathlib import Path
import sys


TASK_ID = "48bda9528e71"
CANONICAL_SOURCE_SHA256 = (
    "cbaac000ae7b97165d8b2427d8fc2bc87387647706d8a68e87b1d2f5ff95c4db"
)
NORMALIZED_SOURCE_SHA256 = (
    "b9f9e9bda3f360c20aa772dfedc3adc436e725f5f33659fc056cee0312ee293f"
)
FILES = {
    "shared/data/base/solutions/augmented/aa62e3f4__9e325a53a30a.json": {
        "original": "7f8f5689dd21adc62d9967f989d1cac8ec8dbb6c47748e1459a1a186b2b1507d",
        "patched": "9424291396cfce2787f04fc4540991a04c68b736e7b67d09afacd4ef0e1c6120",
    },
    "shared/data/base/solutions/training/aa62e3f4__48bda9528e71.json": {
        "original": "70a478937368320747b59fdfb42b65becc7fc925bd0ea12456bcb2e9279686c0",
        "patched": "db18cdf3f8a694b0460c15fb8241f35afee992925aaf900ea0d4aa72a2d02516",
    },
}


def digest(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def replace_target(text: str, old: str, new: str) -> str:
    """Replace one encoded string, preserving every surrounding file byte."""
    needle = '"target_code": ' + json.dumps(old)
    require(text.count(needle) == 1, "target_code encoding is not unique/expected")
    return text.replace(needle, '"target_code": ' + json.dumps(new), 1)


def proposal(repo: Path, state: str) -> tuple[str, dict]:
    canonical_path = repo / "shared/data/canonical/puzzles.jsonl"
    canonical_bytes = canonical_path.read_bytes()
    sources = []
    for number, line in enumerate(canonical_bytes.splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            sources.append((number, row["program_solution"]))
    require(len(sources) == 2, "expected exactly two canonical task records")
    require(
        {digest(source) for _, source in sources} == {CANONICAL_SOURCE_SHA256},
        "canonical task source changed",
    )
    canonical = sources[0][1]
    compact = " ".join(canonical.split())
    require(digest(compact) == NORMALIZED_SOURCE_SHA256, "normalized rule changed")
    # For these inspected bytes, whitespace cannot occur inside a string,
    # escaped symbol, character literal or comment. This is not a generic
    # claim that split/join establishes Racket equivalence for other sources.
    require(
        all(marker not in canonical for marker in ('"', ";", "|", "#\\")),
        "unsupported Racket lexical construct in canonical source",
    )
    catalog_path = repo / "catalog/authority_files.json"
    catalog_bytes = catalog_path.read_bytes()
    catalog = json.loads(catalog_bytes)
    selected_paths = {"shared/" + path for path, task in catalog.items() if task == TASK_ID}
    require(selected_paths == set(FILES), "catalog authority set changed")

    patch_parts = []
    file_records = []
    for relative, hashes in FILES.items():
        blob = (repo / relative).read_bytes()
        require(digest(blob) == hashes[state], f"{relative}: {state} file SHA-256 mismatch")
        text = blob.decode("utf-8")
        row = json.loads(text)
        require(row.get("task_id") == TASK_ID, f"{relative}: task identity mismatch")
        target = row["racket_target"]
        require(target["raw_code"] == compact, f"{relative}: archival source changed")
        require(
            target["target_code"] == (compact if state == "original" else canonical),
            f"{relative}: selected source does not match expected state",
        )
        original = text if state == "original" else replace_target(text, canonical, compact)
        patched = replace_target(original, compact, canonical)
        require(digest(original) == hashes["original"], f"{relative}: original reconstruction mismatch")
        require(digest(patched) == hashes["patched"], f"{relative}: patched reconstruction mismatch")
        expected = copy.deepcopy(json.loads(original))
        expected["racket_target"]["target_code"] = canonical
        require(json.loads(patched) == expected, f"{relative}: unrelated JSON field changed")
        patch_parts.append(f"diff --git a/{relative} b/{relative}\n")
        patch_parts.extend(difflib.unified_diff(
            original.splitlines(keepends=True), patched.splitlines(keepends=True),
            fromfile=f"a/{relative}", tofile=f"b/{relative}", n=3,
        ))
        file_records.append({
            "path": relative,
            "original_sha256": hashes["original"],
            "patched_sha256": hashes["patched"],
            "original_bytes": len(original.encode("utf-8")),
            "patched_bytes": len(patched.encode("utf-8")),
            "changed_json_pointers": ["/racket_target/target_code"],
            "archival_raw_code_unchanged": True,
        })
    patch = "".join(patch_parts)
    manifest = {
        "schema_version": 1,
        "task_id": TASK_ID,
        "status": "optional_shared_authority_formatting_proposal",
        "patch_path_base": "repository root (shared/ paths)",
        "patch_sha256": digest(patch),
        "canonical_ledger_sha256_at_inspection": digest(canonical_bytes),
        "catalog_sha256_at_inspection": digest(catalog_bytes),
        "canonical_lines_at_inspection": [number for number, _ in sources],
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "original_selected_and_archival_source_sha256": NORMALIZED_SOURCE_SHA256,
        "whitespace_normalized_source_sha256_before_and_after": NORMALIZED_SOURCE_SHA256,
        "comment_stripped_normalized_source_sha256_before_and_after": NORMALIZED_SOURCE_SHA256,
        "normalized_rule_hash_12_before_and_after": NORMALIZED_SOURCE_SHA256[:12],
        "canonical_ledger_unchanged_by_patch": True,
        "archival_raw_code_unchanged_by_patch": True,
        "active_authority_count": 4,
        "active_exact_text_groups_before": 2,
        "active_exact_text_groups_after": 1,
        "archival_authority_count": 2,
        "expected_checker_audit_status_after": "selected_synchronized_archival_divergent",
        "expected_checker_payload_status_after": "SELECTED_SYNC_ARCHIVAL_DIVERGENT",
        "proof_scope": "Inspected source bytes differ only in inter-token whitespace; execution is checked separately by the authority_sync stage.",
        "files": file_records,
    }
    return patch, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "check"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, help="new output directory (build only)")
    parser.add_argument("--state", choices=("original", "patched"), default="original")
    args = parser.parse_args()
    try:
        require(args.action != "build" or args.state == "original", "build requires original sources")
        require((args.out is not None) == (args.action == "build"), "--out is required only for build")
        patch, manifest = proposal(args.repo.resolve(), args.state)
        if args.action == "build":
            args.out.mkdir(parents=True, exist_ok=False)
            (args.out / "authority-sync.patch").write_text(patch, encoding="utf-8")
            (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": "PASS", "action": args.action, "verified_state": args.state,
            "task_id": TASK_ID, "file_count": len(FILES),
            "patch_sha256": manifest["patch_sha256"],
            "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
            "normalized_rule_hash_12": NORMALIZED_SOURCE_SHA256[:12],
            "repository_files_written": 0,
        }, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

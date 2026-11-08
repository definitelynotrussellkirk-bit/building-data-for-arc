#!/usr/bin/env python3
"""Task-bound manual selected-authority synchronizer for 83ca9df09514.

The shared ``authority-sync`` command intentionally refuses this repair because
canonical and selected programs use different primitive tokens.  This helper is
narrower and safer than an ad-hoc JSON edit: it is pinned to the reviewed old
source, changes only ``/racket_target/target_code`` in the two catalog-selected
files, preserves ``raw_code`` byte-for-byte, emits a diff/receipt, and refuses
unknown source state.

Why manual review is justified here:
* the assignment marks ``requires_racket_patch`` and
  ``shared_authority_write_allowed`` true;
* canonical ``program_solution`` is the declared authority;
* the old selected and canonical sources both solve all five canonical pairs in
  the retained authority-sync execution-parity check;
* the token changes are reviewed primitive aliases/wrappers (``cell-at``/``at``,
  ``grid-from-fn``/``cellmap``, ``length(filter ...)``/``count-if``, and boolean
  spelling), not a new task rule.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any

TASK_ID = "83ca9df09514"
REPO = Path(__file__).resolve().parents[3]
CANONICAL_LEDGER = REPO / "shared/data/canonical/puzzles.jsonl"
AUTHORITY_FILES = (
    REPO / "shared/data/base/solutions/augmented/82819916__965db239566b.json",
    REPO / "shared/data/base/solutions/training/82819916__83ca9df09514.json",
)
EXPECTED_OLD_TARGET_SHA256 = "c270b2721111e8bcaa68db4eccc6ece2a56f7c5df4f43172fc9e44e4e86513fb"
EXPECTED_CANONICAL_SHA256 = "cae56e2f8161ccd2fd21aa8b0d4e0b51318d3e114e626ea9097fab7c2602af87"
EXPECTED_OLD_FILE_SHA256 = {
    "shared/data/base/solutions/augmented/82819916__965db239566b.json":
        "6779137bf6a855232fc0ee2c3022167cf7861b101c25d44d0546c56e019c0d54",
    "shared/data/base/solutions/training/82819916__83ca9df09514.json":
        "f05df25299ac1a8e7d593bb2ee23b7da55c41eaf12c8fa6e7835c564e077fd23",
}


def _sha(blob: bytes | str) -> str:
    if isinstance(blob, str):
        blob = blob.encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _decode(text: str) -> dict[str, Any]:
    value = json.loads(text, object_pairs_hook=_object)
    if not isinstance(value, dict):
        raise ValueError("authority document must be a JSON object")
    return value


def patch_document(text: str, *, expected_old: str, canonical: str) -> str:
    """Replace exactly one encoded target_code and prove no other JSON field changed."""
    before = _decode(text)
    target = before.get("racket_target")
    if not isinstance(target, dict):
        raise ValueError("missing racket_target object")
    if target.get("target_code") != expected_old:
        raise ValueError("selected target_code does not match reviewed old source")
    raw_before = target.get("raw_code")

    pattern = r'"target_code"\s*:\s*("(?:\\.|[^"\\])*")'
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one target_code encoding, found {len(matches)}")
    encoded = matches[0].group(1)
    if json.loads(encoded) != expected_old:
        raise ValueError("target_code encoding does not decode to reviewed old source")

    start, end = matches[0].span(1)
    patched = text[:start] + json.dumps(canonical) + text[end:]
    after = _decode(patched)
    expected = deepcopy(before)
    expected["racket_target"]["target_code"] = canonical
    if after != expected:
        raise ValueError("patch changed fields other than /racket_target/target_code")
    if after["racket_target"].get("raw_code") != raw_before:
        raise ValueError("archival raw_code changed")
    return patched


def _canonical_source() -> tuple[str, list[int]]:
    sources: list[tuple[int, str]] = []
    with CANONICAL_LEDGER.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source.strip():
                    raise ValueError(f"canonical row {line_number} has no program_solution")
                sources.append((line_number, source))
    if not sources or len({source for _, source in sources}) != 1:
        raise ValueError("canonical rows do not carry one exact program_solution")
    source = sources[0][1]
    if _sha(source) != EXPECTED_CANONICAL_SHA256:
        raise ValueError("canonical source hash changed since manual review")
    return source, [line for line, _ in sources]


def _unified_diff(relative: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
            n=3,
        )
    )


def build_plan() -> dict[str, Any]:
    canonical, canonical_lines = _canonical_source()
    files = []
    combined_diff = []
    for path in AUTHORITY_FILES:
        relative = path.relative_to(REPO).as_posix()
        blob = path.read_bytes()
        text = blob.decode("utf-8")
        row = _decode(text)
        if row.get("task_id") != TASK_ID:
            raise ValueError(f"{relative}: task identity mismatch")
        target = row.get("racket_target")
        if not isinstance(target, dict):
            raise ValueError(f"{relative}: missing racket_target")
        old = target.get("target_code")
        raw = target.get("raw_code")
        if not isinstance(old, str) or not isinstance(raw, str):
            raise ValueError(f"{relative}: source fields must be strings")
        raw_sha = _sha(raw)
        old_sha = _sha(old)

        if old == canonical:
            patched = text
            status = "already_synchronized"
        else:
            expected_blob = EXPECTED_OLD_FILE_SHA256[relative]
            if _sha(blob) != expected_blob:
                raise ValueError(f"{relative}: file bytes changed since review")
            if old_sha != EXPECTED_OLD_TARGET_SHA256:
                raise ValueError(f"{relative}: selected source changed since review")
            if raw_sha != EXPECTED_OLD_TARGET_SHA256:
                raise ValueError(f"{relative}: archival raw source changed since review")
            patched = patch_document(text, expected_old=old, canonical=canonical)
            status = "planned"
            combined_diff.append(_unified_diff(relative, text, patched))

        patched_row = _decode(patched)
        if patched_row["racket_target"]["raw_code"] != raw:
            raise ValueError(f"{relative}: plan does not preserve raw_code")
        files.append(
            {
                "path": relative,
                "status": status,
                "old_file_sha256": _sha(blob),
                "new_file_sha256": _sha(patched),
                "old_target_sha256": old_sha,
                "new_target_sha256": _sha(canonical),
                "raw_code_sha256_before": raw_sha,
                "raw_code_sha256_after": _sha(patched_row["racket_target"]["raw_code"]),
                "changed_json_pointers": [] if patched == text else ["/racket_target/target_code"],
                "patched_text": patched,
            }
        )

    patch = "".join(combined_diff)
    public_files = [{k: v for k, v in item.items() if k != "patched_text"} for item in files]
    return {
        "schema": "83ca9df09514-manual-authority-sync-v1",
        "task_id": TASK_ID,
        "status": "proposal" if patch else "already_synchronized",
        "applied": False,
        "canonical_lines": canonical_lines,
        "canonical_source_sha256": _sha(canonical),
        "canonical_rule_hash": _sha(" ".join(canonical.split()))[:12],
        "review_basis": {
            "shared_authority_write_allowed": True,
            "requires_racket_patch": True,
            "canonical_pair_execution_parity": "PASS 5/5 for both exact source texts",
            "retained_evidence": "checks/after-v1/checks/83ca9df09514_after_authority_sync.json",
            "shared_tool_refusal": "different primitive tokens require manual review",
        },
        "files": public_files,
        "patch": patch,
        "patch_sha256": _sha(patch),
        "_private_files": files,
    }


def _atomic_replace(path: Path, body: bytes) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    fd, name = tempfile.mkstemp(prefix=".83ca9df09514-authority-", dir=path.parent)
    staged = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def apply_plan(plan: dict[str, Any]) -> dict[str, Any]:
    private = plan.get("_private_files", [])
    changed = [item for item in private if item["changed_json_pointers"]]
    if not changed:
        receipt = {k: v for k, v in plan.items() if k != "_private_files"}
        receipt.update(status="already_synchronized", applied=False)
        return receipt

    # Rebuild immediately before the first write.  This is a task-local one-shot
    # repair, so any drift aborts rather than attempting a merge.
    fresh = build_plan()
    comparable = lambda p: {k: v for k, v in p.items() if k != "_private_files"}
    if comparable(fresh) != comparable(plan):
        raise ValueError("authority plan became stale before apply")

    originals: dict[Path, bytes] = {}
    written: list[Path] = []
    try:
        for item in changed:
            path = REPO / item["path"]
            current = path.read_bytes()
            if _sha(current) != item["old_file_sha256"]:
                raise ValueError(f"{item['path']}: bytes changed before apply")
            originals[path] = current
            _atomic_replace(path, item["patched_text"].encode("utf-8"))
            written.append(path)
            if _sha(path.read_bytes()) != item["new_file_sha256"]:
                raise ValueError(f"{item['path']}: post-write hash mismatch")
    except BaseException:
        for path in reversed(written):
            _atomic_replace(path, originals[path])
        raise

    receipt = comparable(plan)
    receipt.update(status="applied", applied=True)
    return receipt


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="apply the reviewed task-bound plan")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).with_name("manual_authority_sync_plan.json"),
        help="plan/receipt JSON path",
    )
    parser.add_argument(
        "--diff-out",
        type=Path,
        default=Path(__file__).with_name("manual_authority_sync.diff"),
        help="human-reviewable unified diff path",
    )
    args = parser.parse_args(argv)

    plan = build_plan()
    public = {k: v for k, v in plan.items() if k != "_private_files"}
    args.diff_out.write_text(public["patch"], encoding="utf-8")
    result = apply_plan(plan) if args.apply else public
    _write_json(args.out, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

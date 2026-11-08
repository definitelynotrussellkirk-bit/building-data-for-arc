"""Source-bound exact-text synchronization for dbecc530afd0 selected copies.

The generic helper currently rejects these files because each JSON document has
both a nested and a top-level ``target_code`` key.  This tool understands those
explicit JSON pointers, accepts formatting-only token identity, preserves both
``raw_code`` copies, and emits a decoded-delta/hash receipt.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

from arcpuzzles.authority_sync import _tokens
from reviewer_support import canonical_path, find_root

TASK_ID = "dbecc530afd0"
SELECTED_FILES = (
    "shared/data/base/solutions/training/af902bf9__dbecc530afd0.json",
    "shared/data/base/solutions/augmented/af902bf9__2c4d5cd6123c.json",
)
TARGET_POINTERS = ("/racket_target/target_code", "/target_code")
RAW_POINTERS = ("/racket_target/raw_code", "/raw_code")
_TARGET_LINE = re.compile(
    r'^(?P<prefix>\s*"target_code"\s*:\s*)'
    r'(?P<encoded>"(?:\\.|[^"\\])*")(?P<suffix>,?\s*)$',
    re.MULTILINE,
)


def _sha(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _canonical(root: Path) -> tuple[str, list[int], str]:
    ledger = canonical_path(root)
    sources: list[tuple[int, str]] = []
    with ledger.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if not isinstance(source, str) or not source:
                    raise ValueError("canonical program_solution must be nonempty text")
                sources.append((line_number, source))
    unique = {source for _, source in sources}
    if not sources or len(unique) != 1:
        raise ValueError(
            f"expected one unique canonical source; got {len(sources)} rows / "
            f"{len(unique)} exact sources"
        )
    return sources[0][1], [line for line, _ in sources], _sha(ledger.read_bytes())


def _pointer_get(value, pointer: str):
    current = value
    for component in pointer.strip("/").split("/"):
        current = current[component]
    return current


def _pointer_set(value, pointer: str, replacement) -> None:
    components = pointer.strip("/").split("/")
    current = value
    for component in components[:-1]:
        current = current[component]
    current[components[-1]] = replacement


def _decoded_differences(before, after, pointer="") -> list[str]:
    if type(before) is not type(after):
        return [pointer or "/"]
    if isinstance(before, dict):
        if before.keys() != after.keys():
            return [pointer or "/"]
        result: list[str] = []
        for key in before:
            escaped = key.replace("~", "~0").replace("/", "~1")
            result.extend(
                _decoded_differences(before[key], after[key], f"{pointer}/{escaped}")
            )
        return result
    if isinstance(before, list):
        if len(before) != len(after):
            return [pointer or "/"]
        result: list[str] = []
        for index, (left, right) in enumerate(zip(before, after)):
            result.extend(_decoded_differences(left, right, f"{pointer}/{index}"))
        return result
    return [] if before == after else [pointer or "/"]


def _patch_target_lines(text: str, old: str, new: str) -> str:
    matches = list(_TARGET_LINE.finditer(text))
    if len(matches) != 2:
        raise ValueError(f"expected exactly two target_code lines, found {len(matches)}")
    for match in matches:
        if json.loads(match.group("encoded")) != old:
            raise ValueError("target_code line does not decode to the selected source")
    encoded = json.dumps(new, ensure_ascii=False)
    return _TARGET_LINE.sub(
        lambda match: match.group("prefix") + encoded + match.group("suffix"),
        text,
    )


def _inspect_file(root: Path, relative: str, canonical: str) -> dict:
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError(f"selected authority path escapes workspace: {relative}")
    blob = path.read_bytes()
    text = blob.decode("utf-8")
    row = json.loads(text)
    if row.get("task_id") != TASK_ID:
        raise ValueError(f"{relative}: selected task identity mismatch")
    targets = [_pointer_get(row, pointer) for pointer in TARGET_POINTERS]
    raws = [_pointer_get(row, pointer) for pointer in RAW_POINTERS]
    if any(not isinstance(value, str) or not value for value in targets + raws):
        raise ValueError(f"{relative}: authority fields must be nonempty strings")
    if targets[0] != targets[1]:
        raise ValueError(f"{relative}: nested/top-level target_code disagree")
    if raws[0] != raws[1]:
        raise ValueError(f"{relative}: nested/top-level raw_code disagree")
    if _tokens(targets[0]) != _tokens(canonical):
        raise ValueError(f"{relative}: selected target tokens differ from canonical")
    return {
        "path": path,
        "relative": relative,
        "blob": blob,
        "text": text,
        "row": row,
        "target_before": targets[0],
        "raw_before": raws[0],
        "already_exact": all(value == canonical for value in targets),
    }


def inspect(root: Path | None = None) -> dict:
    root = find_root(__file__) if root is None else Path(root).resolve()
    canonical, lines, ledger_sha = _canonical(root)
    files = [_inspect_file(root, relative, canonical) for relative in SELECTED_FILES]
    return {
        "root": root,
        "canonical": canonical,
        "canonical_lines": lines,
        "canonical_ledger_sha256": ledger_sha,
        "files": files,
        "synchronized": all(item["already_exact"] for item in files),
    }


def _replace_atomically(path: Path, blob: bytes) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    fd, name = tempfile.mkstemp(prefix=".manual-authority-sync-", dir=path.parent)
    staged = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(blob)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def apply(receipt_path: Path, *, root: Path | None = None) -> dict:
    state = inspect(root)
    if state["synchronized"]:
        raise ValueError("selected authority copies are already exact-canonical")
    canonical = state["canonical"]
    prepared: list[dict] = []
    for item in state["files"]:
        before = item["row"]
        expected = copy.deepcopy(before)
        for pointer in TARGET_POINTERS:
            _pointer_set(expected, pointer, canonical)
        patched_text = _patch_target_lines(item["text"], item["target_before"], canonical)
        after = json.loads(patched_text)
        differences = _decoded_differences(before, after)
        if differences != list(TARGET_POINTERS):
            raise ValueError(
                f"{item['relative']}: unexpected decoded deltas {differences!r}"
            )
        if after != expected:
            raise ValueError(f"{item['relative']}: patch changed unrelated decoded data")
        for pointer in RAW_POINTERS:
            if _pointer_get(after, pointer) != _pointer_get(before, pointer):
                raise ValueError(f"{item['relative']}: archival {pointer} changed")
        prepared.append(
            {
                **item,
                "after": after,
                "patched_blob": patched_text.encode("utf-8"),
                "differences": differences,
            }
        )

    written: list[dict] = []
    try:
        for item in prepared:
            _replace_atomically(item["path"], item["patched_blob"])
            written.append(item)
    except BaseException:
        for item in reversed(written):
            if item["path"].read_bytes() == item["patched_blob"]:
                _replace_atomically(item["path"], item["blob"])
        raise

    verified = inspect(state["root"])
    if not verified["synchronized"]:
        raise RuntimeError("post-write selected authority verification failed")

    receipt = {
        "schema": "dbecc530afd0-manual-authority-sync-v1",
        "task_id": TASK_ID,
        "status": "applied_and_verified",
        "scope": "selected task-bound copies only; canonical ledger unchanged",
        "tool": {
            "path": str(Path(__file__).resolve().relative_to(state["root"])),
            "sha256": _sha(Path(__file__).read_bytes()),
            "argv": [sys.executable, *sys.argv],
        },
        "canonical": {
            "ledger": str(canonical_path(state["root"]).relative_to(state["root"])),
            "ledger_sha256": state["canonical_ledger_sha256"],
            "line_numbers": state["canonical_lines"],
            "exact_sha256": _sha(canonical),
            "normalized_rule_hash_12": _sha(" ".join(canonical.split()))[:12],
        },
        "files": [],
        "claims": {
            "restricted_racket_tokens_identical_before": True,
            "changed_json_pointers_only": list(TARGET_POINTERS),
            "both_raw_code_copies_unchanged": True,
            "all_unrelated_decoded_values_unchanged": True,
            "both_target_code_copies_exact_canonical_after": True,
        },
        "generic_helper_limitation": (
            "arcpuzzles authority-sync uses a whole-text regex requiring one "
            "target_code key, but each selected JSON intentionally carries nested "
            "and top-level target_code copies."
        ),
    }
    for item in prepared:
        current = json.loads(item["path"].read_text(encoding="utf-8"))
        receipt["files"].append(
            {
                "path": item["relative"],
                "file_sha256_before": _sha(item["blob"]),
                "file_sha256_after": _sha(item["path"].read_bytes()),
                "target_exact_sha256_before": _sha(item["target_before"]),
                "target_exact_sha256_after": _sha(canonical),
                "raw_exact_sha256_before": _sha(item["raw_before"]),
                "raw_exact_sha256_after": _sha(_pointer_get(current, RAW_POINTERS[0])),
                "changed_json_pointers": item["differences"],
                "raw_code_unchanged": _pointer_get(current, RAW_POINTERS[0]) == item["raw_before"],
                "unrelated_decoded_values_unchanged": True,
            }
        )

    receipt_path = Path(receipt_path).resolve()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipt


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="exit 0 only when exact-synchronized")
    mode.add_argument("--apply", action="store_true", help="apply the two-pointer formatting-only repair")
    parser.add_argument("--receipt", type=Path, help="required with --apply")
    args = parser.parse_args(argv)

    if args.apply:
        if args.receipt is None:
            parser.error("--apply requires --receipt")
        receipt = apply(args.receipt)
        print(json.dumps({"status": receipt["status"], "receipt": str(args.receipt)}, sort_keys=True))
        return 0

    state = inspect()
    summary = {
        "task_id": TASK_ID,
        "status": "synchronized" if state["synchronized"] else "needs_sync",
        "canonical_exact_sha256": _sha(state["canonical"]),
        "files": [
            {
                "path": item["relative"],
                "already_exact": item["already_exact"],
                "target_exact_sha256": _sha(item["target_before"]),
                "raw_exact_sha256": _sha(item["raw_before"]),
            }
            for item in state["files"]
        ],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if state["synchronized"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

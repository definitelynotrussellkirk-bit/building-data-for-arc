#!/usr/bin/env python3
"""Report exact and normalized agreement across every Racket task authority."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE_SOLUTIONS = ROOT / "data/base/solutions"

# Roles that carry the ACTIVE task rule. Everything else (today only
# archival_or_executable_raw) is preserved source whose text may lawfully
# diverge when its role is stated and execution parity is proved.
ACTIVE_ROLES = {"canonical_program_solution", "selected_task_rule"}


def _patch_target_paths(patch_text: str) -> list[str]:
    """Repo-relative paths a git-format patch writes (`+++ b/<path>` lines)."""
    paths = []
    for line in patch_text.splitlines():
        if line.startswith("+++ b/"):
            paths.append(line[len("+++ b/"):].strip())
    return paths


class StagedTree:
    """Audit a proposed task-scoped patch WITHOUT mutating the shared ledger
    (adopted 2026-07-29, EWF-002059/002064).

    Copies the canonical ledger, every base-solution file carrying one of the
    audited task_ids, and every patch-touched file into a temp tree; applies
    the patch there with `patch -p1`; then points this module's CANONICAL /
    BASE_SOLUTIONS globals at the staged copies for the duration. A patch
    that does not apply cleanly aborts LOUDLY — a staged audit of a
    half-applied patch would certify the wrong tree.
    """

    def __init__(self, patch_path: Path, task_ids: list[str]) -> None:
        self.patch_path = patch_path
        self.task_ids = set(task_ids)
        self._saved: tuple[Path, Path] | None = None
        self.tmp: Path | None = None

    def __enter__(self) -> "StagedTree":
        import shutil
        import subprocess
        import tempfile

        global CANONICAL, BASE_SOLUTIONS
        self.tmp = Path(tempfile.mkdtemp(prefix="authority-sync-staged-"))
        patch_text = self.patch_path.read_text(encoding="utf-8")
        wanted = set(_patch_target_paths(patch_text))
        staged_canonical = self.tmp / "data/canonical/puzzles.jsonl"
        staged_canonical.parent.mkdir(parents=True, exist_ok=True)
        if CANONICAL.exists():
            shutil.copy2(CANONICAL, staged_canonical)
        copied = 1
        for path in sorted(BASE_SOLUTIONS.rglob("*.json")):
            rel = str(path.relative_to(ROOT))
            take = rel in wanted
            if not take:
                try:
                    row = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                take = row.get("task_id") in self.task_ids
            if take:
                dest = self.tmp / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dest)
                copied += 1
        for rel in wanted:
            src = ROOT / rel
            dest = self.tmp / rel
            if src.exists() and not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                copied += 1
        result = subprocess.run(
            ["patch", "-p1", "-s", "-d", str(self.tmp)],
            input=patch_text, capture_output=True, text=True,
        )
        if result.returncode != 0:
            shutil.rmtree(self.tmp, ignore_errors=True)
            raise SystemExit(
                f"LOUD: --patch {self.patch_path} does not apply cleanly to "
                f"the staged tree (exit {result.returncode}):\n"
                f"{result.stdout}{result.stderr}"
            )
        self._saved = (CANONICAL, BASE_SOLUTIONS)
        CANONICAL = staged_canonical
        BASE_SOLUTIONS = self.tmp / "data/base/solutions"
        print(f"staged audit: {copied} file(s) copied, patch applied at {self.tmp}")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        import shutil

        global CANONICAL, BASE_SOLUTIONS
        if self._saved is not None:
            CANONICAL, BASE_SOLUTIONS = self._saved
        if self.tmp is not None:
            shutil.rmtree(self.tmp, ignore_errors=True)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def strip_racket_comments(source: str) -> str:
    """Remove semicolon line comments while preserving quoted semicolons."""
    output: list[str] = []
    in_string = False
    escaped = False
    for line in source.splitlines():
        kept: list[str] = []
        for char in line:
            if escaped:
                kept.append(char)
                escaped = False
                continue
            if in_string and char == "\\":
                kept.append(char)
                escaped = True
                continue
            if char == '"':
                in_string = not in_string
                kept.append(char)
                continue
            if char == ";" and not in_string:
                break
            kept.append(char)
        output.append("".join(kept))
    return "\n".join(output)


def source_digests(source: str) -> dict[str, Any]:
    whitespace_normalized = " ".join(source.split())
    comment_stripped = " ".join(strip_racket_comments(source).split())
    return {
        "chars": len(source),
        "exact_sha256": _sha256(source),
        "whitespace_normalized_sha256": _sha256(whitespace_normalized),
        "comment_stripped_normalized_sha256": _sha256(comment_stripped),
        "rule_hash_12": _sha256(whitespace_normalized)[:12],
    }


def _canonical_sources(task_id: str) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    if not CANONICAL.exists():
        return sources
    with CANONICAL.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != task_id:
                continue
            source = row.get("program_solution")
            if isinstance(source, str) and source.strip():
                sources.append(
                    {
                        "location": (
                            f"data/canonical/puzzles.jsonl:{line_number}"
                        ),
                        "field": "program_solution",
                        "role": "canonical_program_solution",
                        "canonicalization_status": "canonical",
                        "source": source,
                    }
                )
    return sources


def _base_sources(task_id: str) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for path in sorted(BASE_SOLUTIONS.rglob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if row.get("task_id") != task_id:
            continue
        target = row.get("racket_target")
        if not isinstance(target, dict):
            continue
        try:
            location = str(path.relative_to(ROOT))
        except ValueError:
            location = str(path)
        for field in ("raw_code", "target_code"):
            source = target.get(field)
            if isinstance(source, str) and source.strip():
                sources.append(
                    {
                        "location": location,
                        "field": field,
                        "role": (
                            "selected_task_rule"
                            if field == "target_code"
                            else "archival_or_executable_raw"
                        ),
                        "canonicalization_status": str(
                            target.get("canonicalization_status") or ""
                        ),
                        "code_form": str(target.get("code_form") or ""),
                        "target_status": str(
                            target.get("target_status") or ""
                        ),
                        "source": source,
                    }
                )
    return sources


def audit_task(task_id: str) -> dict[str, Any]:
    authorities = _canonical_sources(task_id) + _base_sources(task_id)
    rows = [
        {
            "location": authority["location"],
            "field": authority["field"],
            "role": authority["role"],
            "canonicalization_status": authority[
                "canonicalization_status"
            ],
            **(
                {
                    "code_form": authority.get("code_form", ""),
                    "target_status": authority.get("target_status", ""),
                }
                if authority["field"] != "program_solution"
                else {}
            ),
            **source_digests(authority["source"]),
        }
        for authority in authorities
    ]
    digest_keys = (
        "exact_sha256",
        "whitespace_normalized_sha256",
        "comment_stripped_normalized_sha256",
    )
    groups: dict[str, dict[str, list[str]]] = {}
    selected_groups: dict[str, dict[str, list[str]]] = {}
    for key in digest_keys:
        grouped: dict[str, list[str]] = defaultdict(list)
        selected_grouped: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            label = f"{row['location']}#{row['field']}"
            grouped[str(row[key])].append(label)
            if row["role"] in ACTIVE_ROLES:
                selected_grouped[str(row[key])].append(label)
        groups[key] = dict(sorted(grouped.items()))
        selected_groups[key] = dict(sorted(selected_grouped.items()))
    selected_rows = [row for row in rows if row["role"] in ACTIVE_ROLES]
    archival_rows = [row for row in rows if row["role"] not in ACTIVE_ROLES]
    selected_exact = {
        str(row["exact_sha256"]) for row in selected_rows
    }
    archival_divergent = [
        f"{row['location']}#{row['field']}"
        for row in archival_rows
        if str(row["exact_sha256"]) not in selected_exact
    ]
    if not rows:
        status = "no_authority"
    elif all(len(grouped) == 1 for grouped in groups.values()):
        status = "synchronized"
    elif selected_rows and all(
        len(grouped) == 1 for grouped in selected_groups.values()
    ):
        status = "selected_synchronized_archival_divergent"
    else:
        status = "diagnostic_divergence"
    return {
        "task_id": task_id,
        "authority_count": len(rows),
        "authorities": rows,
        "group_counts": {
            key: len(value) for key, value in groups.items()
        },
        "groups": groups,
        "selected_group_counts": {
            key: len(value) for key, value in selected_groups.items()
        },
        "selected_groups": selected_groups,
        "selected_authority_count": len(selected_rows),
        "archival_authority_count": len(archival_rows),
        "archival_divergent": archival_divergent,
        "status": status,
        "selected_sync_remediation": {
            "applied": False,
            "copy_from": "canonical program_solution",
            "copy_to": "selected racket_target.target_code",
            "preserve": "archival racket_target.raw_code",
            "needed": len(selected_groups["exact_sha256"]) > 1,
            "proposal_argv": ["arcpuzzles", "authority-sync", task_id, "--selected-only"],
            "scope": "Non-applying suggestion only. The proposal command refuses ambiguous canonical or non-formatting edits.",
            "verify_argv": [["arcpuzzles", "check", task_id, "--stage", stage,
                             "--out", "NEW_" + stage.upper() + "_DIRECTORY"]
                            for stage in ("authority_sync", "rule_smoke")],
        },
    }


def verify_execution_parity(audit: dict[str, Any]) -> dict[str, Any]:
    """Execute every distinct authority text on the canonical pairs.

    Returns per-distinct-source pass counts via the Racket bridge so a
    textually divergent archival source can prove (or fail) execution
    equivalence with the selected rule. LOUD: any source that errors or
    misses a pair is reported, never swallowed.
    """
    import sys

    # This tool also reads authority text directly from shared/data in a source
    # checkout. Execution needs the copied runtime layout; otherwise missing
    # scripts imports were recorded as zero-scoring, semantically wrong rules.
    required = ("scripts/coder_synth_verify.py", "scripts/comment_solutions.py",
                "arc_repl/racket_bridge.py", "puzzle_generators/rule_wrap.py")
    missing = [name for name in required if not (ROOT / name).is_file()]
    if missing:
        return {
            "status": "INFRASTRUCTURE_ERROR", "executed": False,
            "reason": "prepared_runtime_required", "sources": [],
            "missing_runtime_files": missing,
            "error": "Execution parity requires a prepared runtime; no authority text was scored.",
            "supported_command": ["arcpuzzles", "check", audit["task_id"],
                                  "--stage", "authority_sync", "--out", "NEW_OUTPUT_DIRECTORY"],
        }

    sys.path.insert(0, str(ROOT / "scripts"))
    from coder_synth_verify import ProgramVerifier  # noqa: PLC0415

    task_id = audit["task_id"]
    train = test = None
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == task_id:
                train, test = row["train"], row["test"]
                break
    if train is None:
        return {"status": "NO_CANONICAL_PAIRS", "sources": []}

    sources: dict[str, dict[str, Any]] = {}
    for authority in audit["authorities"]:
        sources.setdefault(
            str(authority["exact_sha256"]),
            {
                "locations": [],
                "roles": set(),
            },
        )["locations"].append(
            f"{authority['location']}#{authority['field']}"
        )
        sources[str(authority["exact_sha256"])]["roles"].add(
            authority["role"]
        )

    verifier = ProgramVerifier()
    results = []
    all_pass = True
    texts = _authority_texts(task_id)
    for digest, meta in sorted(sources.items()):
        source = texts.get(digest)
        if source is None:
            results.append(
                {
                    "exact_sha256": digest,
                    "locations": meta["locations"],
                    "error": "source text not recoverable",
                }
            )
            all_pass = False
            continue
        # ProgramVerifier requires the text to start with an s-expression;
        # leading comment/blank lines are semantically inert, so drop them.
        lines = source.splitlines()
        while lines and (
            not lines[0].strip() or lines[0].lstrip().startswith(";")
        ):
            lines.pop(0)
        score = verifier.score("\n".join(lines), train, test)
        passed = bool(
            score.get("train_pass") == score.get("train_total")
            and score.get("test_pass") == score.get("test_total")
            and not score.get("error")
        )
        all_pass = all_pass and passed
        results.append(
            {
                "exact_sha256": digest,
                "locations": meta["locations"],
                "roles": sorted(meta["roles"]),
                "score": score,
                "solves_all_canonical_pairs": passed,
            }
        )
    return {
        "status": "PASS" if all_pass else "FAIL",
        "sources": results,
    }


def _authority_texts(task_id: str) -> dict[str, str]:
    return {
        source_digests(authority["source"])["exact_sha256"]: authority[
            "source"
        ]
        for authority in _canonical_sources(task_id) + _base_sources(task_id)
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_ids", nargs="+")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--require-exact-sync", action="store_true")
    parser.add_argument(
        "--require-selected-exact-sync",
        action="store_true",
        help=(
            "require one exact-text group across ACTIVE authorities only "
            "(canonical program_solution + selected target_code); a "
            "role-stated archival raw_code may diverge without failing"
        ),
    )
    parser.add_argument(
        "--require-whitespace-normalized-sync", action="store_true"
    )
    parser.add_argument(
        "--require-comment-stripped-sync", action="store_true"
    )
    parser.add_argument(
        "--verify-execution-parity",
        action="store_true",
        help=(
            "execute every distinct authority text on the canonical "
            "train/test pairs via the Racket bridge; a divergent archival "
            "source must solve all pairs or the audit FAILs"
        ),
    )
    parser.add_argument(
        "--patch",
        type=Path,
        help=(
            "audit a proposed task-scoped source patch applied to a STAGED "
            "temp copy of the ledgers — the shared tree is never mutated. "
            "Task-local workers use this to prove atomic sync for a "
            "patches/racket__<task_id>.patch return."
        ),
    )
    args = parser.parse_args()

    if args.patch:
        if not args.patch.exists():
            raise SystemExit(f"LOUD: --patch {args.patch} does not exist")
        with StagedTree(args.patch, list(args.task_ids)):
            return _run_audits(args)
    return _run_audits(args)


def _run_audits(args) -> int:
    audits = [audit_task(task_id) for task_id in args.task_ids]
    failures: list[str] = []
    for audit in audits:
        counts = audit["group_counts"]
        selected_counts = audit["selected_group_counts"]
        print(
            f"{audit['task_id']}: {audit['authority_count']} authorities; "
            f"exact={counts['exact_sha256']} group(s), "
            "whitespace-normalized="
            f"{counts['whitespace_normalized_sha256']} group(s), "
            "comment-stripped="
            f"{counts['comment_stripped_normalized_sha256']} group(s); "
            f"selected-exact={selected_counts['exact_sha256']} group(s) "
            f"over {audit['selected_authority_count']} active; "
            f"archival-divergent={len(audit['archival_divergent'])}; "
            f"status={audit['status']}"
        )
        if audit["selected_sync_remediation"]["needed"]:
            import shlex
            print("  Selected target_code should match canonical program_solution; preserve archival raw_code.")
            print("  Non-applying proposal: " + shlex.join(audit["selected_sync_remediation"]["proposal_argv"]))
        if args.verify_execution_parity:
            parity = verify_execution_parity(audit)
            audit["execution_parity"] = parity
            print(
                f"  execution-parity: {parity['status']} over "
                f"{len(parity['sources'])} distinct source text(s)"
            )
            if parity.get("supported_command"):
                import shlex
                print(f"  {parity['error']}")
                print("  Use: " + shlex.join(parity["supported_command"]))
            if parity["status"] != "PASS":
                failures.append(
                    f"{audit['task_id']}: execution parity {parity['status']}"
                )
        if audit["status"] == "no_authority":
            failures.append(f"{audit['task_id']}: no authority")
        if args.require_exact_sync and counts["exact_sha256"] != 1:
            failures.append(f"{audit['task_id']}: exact text diverges")
        if (
            args.require_selected_exact_sync
            and selected_counts["exact_sha256"] != 1
        ):
            failures.append(
                f"{audit['task_id']}: ACTIVE authorities (canonical + "
                "selected target_code) diverge in exact text"
            )
        if (
            args.require_whitespace_normalized_sync
            and counts["whitespace_normalized_sha256"] != 1
        ):
            failures.append(
                f"{audit['task_id']}: whitespace-normalized source diverges"
            )
        if (
            args.require_comment_stripped_sync
            and counts["comment_stripped_normalized_sha256"] != 1
        ):
            failures.append(
                f"{audit['task_id']}: comment-stripped source diverges"
            )

    diagnostic_divergence = any(
        audit["status"] == "diagnostic_divergence"
        for audit in audits
    )
    archival_only_divergence = any(
        audit["status"] == "selected_synchronized_archival_divergent"
        for audit in audits
    )
    payload = {
        "schema_version": 2,
        "audits": audits,
        "failures": failures,
        "status": (
            "FAIL"
            if failures
            else "DIAGNOSTIC_DIVERGENCE"
            if diagnostic_divergence
            else "SELECTED_SYNC_ARCHIVAL_DIVERGENT"
            if archival_only_divergence
            else "PASS"
        ),
    }
    if args.json_out:
        path = (
            args.json_out
            if args.json_out.is_absolute()
            else ROOT / args.json_out
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    for failure in failures:
        print(f"ERROR: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

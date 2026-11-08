#!/usr/bin/env python3
"""Compute the source identity used by the per-generator battery receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import ast
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _generator_path(root: Path, task_id: str) -> tuple[Path, str]:
    if task_id.startswith("generic_"):
        family, separator, generator = task_id[len("generic_"):].rpartition("_")
        if not separator or not family or not generator.startswith("gen"):
            raise ValueError(
                "generic task id must look like generic_<family>_genN: "
                f"{task_id}"
            )
        return (
            root / "puzzle_generators/generic/concepts" / family / f"{generator}.py",
            "generic",
        )
    return root / "puzzle_generators/per_puzzle" / task_id / "generator.py", "per_puzzle"


def _embedded_program(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "PROGRAM" for target in targets):
                value = ast.literal_eval(node.value)
                if isinstance(value, str) and value.strip():
                    return value
    raise ValueError(f"generic generator has no literal PROGRAM: {path}")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _authority_entries(
    root: Path, task_id: str, generator: Path, kind: str
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if kind == "generic":
        entries.append({
            "location": str(generator.relative_to(root)),
            "field": "PROGRAM",
            "role": "embedded_generic_program",
            "source": _embedded_program(generator),
        })
        return entries
    canonical = root / "data/canonical/puzzles.jsonl"
    if canonical.exists():
        occurrence = 0
        for line in canonical.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != task_id:
                continue
            source = row.get("program_solution")
            if isinstance(source, str):
                entries.append(
                    {
                        "location": "data/canonical/puzzles.jsonl",
                        "occurrence": occurrence,
                        "role": "canonical_program_solution",
                        "source": source,
                    }
                )
                occurrence += 1

    base = root / "data/base/solutions"
    if base.exists():
        for path in sorted(base.rglob("*.json")):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if row.get("task_id") != task_id:
                continue
            target = row.get("racket_target")
            if not isinstance(target, dict):
                continue
            location = str(path.relative_to(root))
            role_metadata = {
                "canonicalization_status": target.get("canonicalization_status"),
                "code_form": target.get("code_form"),
                "target_status": target.get("target_status"),
            }
            for field, role in (
                ("target_code", "selected_task_rule"),
                ("raw_code", "archival_or_executable_raw"),
            ):
                source = target.get(field)
                if isinstance(source, str):
                    entries.append(
                        {
                            "location": location,
                            "field": field,
                            "role": role,
                            "role_metadata": role_metadata,
                            "source": source,
                        }
                    )
    return entries


def compute_subject(root: Path, task_id: str) -> dict[str, str]:
    generator, kind = _generator_path(root, task_id)
    if not generator.is_file():
        raise FileNotFoundError(f"generator not found: {generator}")
    generator_file_sha256 = _sha256_bytes(generator.read_bytes())
    authority_payload = json.dumps(
        _authority_entries(root, task_id, generator, kind),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    authority_set_sha256 = _sha256_bytes(authority_payload)
    subject_payload = json.dumps(
        {
            "generator_file_sha256": generator_file_sha256,
            "authority_set_sha256": authority_set_sha256,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return {
        "generator_file_sha256": generator_file_sha256,
        "authority_set_sha256": authority_set_sha256,
        "battery_subject_sha16": _sha256_bytes(subject_payload)[:16],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--tsv", action="store_true")
    args = parser.parse_args()
    result = compute_subject(args.root.resolve(), args.task_id)
    if args.tsv:
        print(
            result["generator_file_sha256"],
            result["authority_set_sha256"],
            result["battery_subject_sha16"],
            sep="\t",
        )
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

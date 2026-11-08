"""Source-bound, portable generator review assignment contracts."""
from __future__ import annotations

import json
from pathlib import Path
import random
import re

from .catalog import Catalog, jsonl, local_path, sha256


def load_question(review_root: Path, question_id: str | None, seed: int) -> dict | None:
    paths = sorted((review_root / "questions").glob("*.json"))
    if question_id is not None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", question_id):
            raise ValueError("Invalid question ID")
        paths = [review_root / "questions" / f"{question_id}.json"]
    if not paths:
        return None
    path = random.Random(seed).choice(paths)
    value = json.loads(path.read_text())
    if (value.get("schema") != "arcpuzzles-review-question-v1" or value.get("id") != path.stem
            or not isinstance(value.get("version"), int) or value["version"] < 1
            or not value.get("owner") or not value.get("text")):
        raise ValueError(f"Invalid review question: {path}")
    return {**value, "sha256": sha256(path)}


def load_cohort(catalog: Catalog, receipt_path: Path) -> tuple[set[str], dict]:
    receipt_path = receipt_path.resolve()
    receipt = json.loads(receipt_path.read_text())
    if receipt.get("schema") != "verified-unapproved-official-generator-review-v1":
        raise ValueError("Invalid cohort receipt schema")
    rows_path = receipt_path.parent / "rows.jsonl"
    if sha256(rows_path) != receipt.get("rows_sha256"):
        raise ValueError("Review cohort rows hash changed")
    for relative, expected in receipt.get("source_sha256", {}).items():
        source = local_path(catalog.root, relative)
        if not source.is_file() or sha256(source) != expected:
            raise ValueError(f"Review cohort source changed: {relative}")
    ids = set()
    for row in jsonl(rows_path):
        tid = row.get("generator_id")
        if not tid or tid in ids:
            raise ValueError("Duplicate or missing review cohort generator")
        current = catalog.describe(tid)
        if current["generator_sha256"] != row.get("generator_sha256"):
            raise ValueError(f"Review cohort generator changed: {tid}")
        if row.get("canonical_rule_hash") != current["rule_hash"] and "canonical_rule_hash" in row:
            raise ValueError(f"Review cohort rule changed: {tid}")
        ids.add(tid)
    return ids, {"receipt_sha256": sha256(receipt_path), "rows_sha256": sha256(rows_path),
                 "size": len(ids), "receipt_path": str(receipt_path)}


def build_contract(catalog: Catalog, record: dict, workspace: Path,
                   question: dict | None) -> dict:
    row = catalog.describe(record["task_id"])
    if row["generator_sha256"] != record["generator_sha256"] or row["rule_hash"] != record["rule_hash"]:
        raise RuntimeError("Generator or rule changed while preparing review; retry")
    generator_path = local_path(workspace, row["runtime_generator"])
    if sha256(generator_path) != row["generator_sha256"]:
        raise RuntimeError("Generator changed in review workspace; retry")
    manifest = json.loads((workspace / "RUNTIME_MANIFEST.json").read_text())
    authorities = [f for f in manifest["files"] if f["runtime_path"].startswith("data/base/solutions/")]
    return {"schema": "arcpuzzles-review-assignment-v1", "assignment_id": record["id"],
            "task_id": row["id"],
            "generator": {"library_path": row["generator"], "runtime_path": row["runtime_generator"],
                          "sha256": row["generator_sha256"]},
            "rule": {"task_id": row.get("rule_task_id", row["id"]), "rule_hash": row["rule_hash"],
                     "library_path": "shared/data/canonical/puzzles.jsonl",
                     "runtime_path": "data/canonical/puzzles.jsonl",
                     "sha256": sha256(catalog.root / "shared/data/canonical/puzzles.jsonl")},
            "base_authorities": authorities,
            "runtime_manifest_sha256": sha256(workspace / "RUNTIME_MANIFEST.json"),
            "question": question,
            "cohort": ({key: record["cohort"][key] for key in
                        ("receipt_sha256", "rows_sha256", "size", "eligible_count")}
                       if record.get("cohort") else None)}

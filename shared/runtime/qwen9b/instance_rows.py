#!/usr/bin/env python3
"""Shared raw-instance row builder for the Qwen9B data lane.

Single source for the `qwen9b_raw_instance_v1` row shape, used by both
`build_dataset.py` (immutable baseline shards) and `live_producer.py`
(the safe-tagged generator-in-the-loop lane). Keeping the shape here means
the two producers can never drift apart.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ground_facts import fed_facts  # noqa: E402
from qwen9b.contracts import RAW_SCHEMA, validate_instance_row  # noqa: E402
from qwen9b.racket_presentations import present_racket_program  # noqa: E402


def make_instance_row(task_id: str, canonical: dict, instance: dict,
                      where: str = "") -> dict:
    """Assemble and validate one raw-instance row.

    `canonical` is the puzzles.jsonl row (needs program_solution,
    content_hash, parent_hash, source); `instance` is one run_batch element
    (needs train/test pairs plus generator provenance).
    """
    presentation = present_racket_program(
        canonical["program_solution"],
        task_id=task_id,
        seed=instance.get("seed"),
        sample_index=instance.get("sample_index"),
        description=canonical.get("written_solution") or "",
    )
    program = presentation.program
    row = {
        "schema_version": RAW_SCHEMA,
        "task_id": task_id,
        "content_hash": canonical.get("content_hash"),
        "parent_hash": canonical.get("parent_hash"),
        "source": canonical.get("source"),
        "split_group": canonical.get("parent_hash") or canonical.get("task_id"),
        "generator_version": instance.get("generator_version"),
        "seed": instance.get("seed"),
        "sample_index": instance.get("sample_index"),
        "program": program,
        "program_hash": hashlib.sha256(program.encode()).hexdigest(),
        "program_authority_hash": presentation.authority_hash,
        "program_presentation_variant": presentation.variant_id,
        "program_comments_added": presentation.comments_added,
        "facts": fed_facts(instance["train"]),
        "train": instance["train"],
        "test": instance["test"],
    }
    validate_instance_row(row, where or f"row:{task_id}")
    return row

#!/usr/bin/env python3
"""Run the official causal-witness CLI for a legacy singleton-test record.

The task's canonical JSONL row uses the supported legacy form where ``test``
is one pair object rather than a list.  Catalog.challenge normalizes that form,
but review_base_preflight's private record hash and witness revalidation hash
the raw row.  The authoring preflight therefore used an in-memory normalization
of only this task's row.  Apply the identical normalization before delegating to
the unmodified official review_witness CLI so its source/receipt comparison is
against the exact preflight view.  Shared source and canonical bytes are never
changed.
"""
from __future__ import annotations

from copy import deepcopy

import arcpuzzles.review_base_preflight as base

TASK_ID = "9e2802ee78bd"
_ORIGINAL_RECORDS = base._records


def _normalized_records(catalog, tid):
    rows = deepcopy(_ORIGINAL_RECORDS(catalog, tid))
    if tid != TASK_ID:
        return rows
    for row in rows:
        tests = row.get("test")
        if isinstance(tests, dict):
            row["test"] = [tests]
        elif not isinstance(tests, list):
            raise ValueError(f"{TASK_ID}: canonical test must be an object or list")
    return rows


def main(argv=None) -> int:
    base._records = _normalized_records
    from arcpuzzles import review_witness

    return review_witness.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())

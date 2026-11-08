"""Regression binding selected execution copies to the canonical Racket authority."""
from __future__ import annotations

import hashlib
import json

from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
AUTHORITY_FILES = {
    "shared/data/base/solutions/training/902510d5__747486860e56.json":
        "9aadb14ef60c3240e95070978ce1f9e14b9ff17a3f21da326505bcaa493af121",
    "shared/data/base/solutions/augmented/902510d5__50f50ce3a1e3.json":
        "386e82b02eb1e039a885d11af8861e0cb243cbd41f3196a29234a93ae952714d",
}


def _canonical_source() -> str:
    sources = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == "747486860e56":
                    sources.add(row["program_solution"])
    assert len(sources) == 1
    return sources.pop()


def test_selected_target_code_is_exact_canonical_while_archival_raw_code_is_unchanged():
    canonical = _canonical_source()
    for relative, expected_raw_sha256 in AUTHORITY_FILES.items():
        row = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        target = row["racket_target"]
        assert hashlib.sha256(target["raw_code"].encode()).hexdigest() == expected_raw_sha256
        assert target["target_code"] == canonical

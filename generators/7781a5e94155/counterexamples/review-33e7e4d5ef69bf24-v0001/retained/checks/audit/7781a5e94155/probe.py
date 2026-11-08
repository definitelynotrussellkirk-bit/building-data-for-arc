from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator

TASK_ID = "7781a5e94155"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit" / TASK_ID


def pixel_adjacency(grid: list[list[int]]) -> list[list[int]]:
    pixels = sorted(
        ((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0),
        key=lambda rc: (rc[1], rc[0]),
    )
    return [
        [
            5 if i == j else 7 if abs(r1 - r2) + abs(c1 - c2) == 1 else 0
            for j, (r2, c2) in enumerate(pixels)
        ]
        for i, (r1, c1) in enumerate(pixels)
    ]


def main() -> int:
    gen, source, source_sha = load_selected_generator(TASK_ID, root=ROOT)
    racket = json.loads((OUT / "racket.json").read_text())
    generated = gen.generate(0, 0, difficulty="medium")
    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)[0]["input"]
    generated_rival = pixel_adjacency(generated)
    canonical_rival = pixel_adjacency(canonical)
    generated_official = racket["results"][0]["output"]
    canonical_official = racket["results"][1]["output"]

    report = {
        "schema": "arcpuzzles-audit-case-v1",
        "task_id": TASK_ID,
        "finding": "single-pixel-only generator makes a pixel-as-object shortcut exact and rejects canonical multi-cell objects",
        "generator_path": str(source.relative_to(ROOT)),
        "generator_sha256": source_sha,
        "rule_hash": racket["executed_rule_hash"],
        "replay": {"seed": 0, "sample_index": 0, "difficulty": "medium", "overrides": {}},
        "generated_input": generated,
        "generated_self_check": gen.self_check(generated),
        "generated_racket_output": generated_official,
        "generated_rival_output": generated_rival,
        "generated_rival_matches": generated_rival == generated_official,
        "canonical_pair": {"variant": 0, "split": "train", "pair_index": 0},
        "canonical_input": canonical,
        "canonical_self_check": gen.self_check(canonical),
        "canonical_racket_output": canonical_official,
        "canonical_rival_output": canonical_rival,
        "canonical_rival_matches": canonical_rival == canonical_official,
        "rival": "treat every nonzero pixel as its own object, sort pixels by (column,row), and emit pixel-cardinal adjacency",
        "domain_note": "The generated case is in the documented default domain. The canonical case is authoritative task data but is rejected because each monochrome object contains multiple cells.",
        "authority_evidence": "checks/audit/7781a5e94155/racket.json",
        "audit_check_evidence": "checks/audit/7781a5e94155-combined/",
    }
    assert report["generator_sha256"] == "c545db1edf02cbed2b4c7671eaae76c60cdcd14ab9083a62f41c7f7b8797fbbe"
    assert report["generated_self_check"] == []
    assert report["generated_rival_matches"] is True
    assert report["canonical_self_check"]
    assert report["canonical_rival_matches"] is False
    body = json.dumps(report, indent=2, sort_keys=True) + "\n"
    (OUT / "case.json").write_text(body)
    print(body, end="")
    print("case_sha256", hashlib.sha256(body.encode()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

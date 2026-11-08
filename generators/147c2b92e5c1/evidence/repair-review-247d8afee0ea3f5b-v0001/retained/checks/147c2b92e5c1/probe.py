#!/usr/bin/env python3
"""One fixed, source-pinned learnability probe; no production mutation.

From packet: WORK/.venv/bin/python review.py run python3 ../checks/147c2b92e5c1/probe.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator
from arcpuzzles.parametric_worker import _real_evaluator

TASK = "147c2b92e5c1"
EXPECTED = "658485dcaa05e19b78869e77afa0da15170000fbb0aa09a65a5f13fad82607a0"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK, root=root)
    assert digest == EXPECTED, (digest, EXPECTED)
    ledger = root / "shared/data/canonical/puzzles.jsonl"
    records = [json.loads(line) for line in ledger.read_text().splitlines()]
    rows = [row for row in records if row.get("task_id") == TASK]
    assert len(rows) == 1
    canonical = rows[0]["program_solution"]
    original = "((= code 5) (flip-lr grid)) ((= code 6) (flip-ud grid))"
    swapped = "((= code 5) (flip-ud grid)) ((= code 6) (flip-lr grid))"
    assert canonical.count(original) == 1
    rival = canonical.replace(original, swapped)
    grids = [gen.generate(0, index, difficulty="easy") for index in range(5)]
    codes = [gen.observe_overrides(grid)["transform_code"] for grid in grids]
    assert codes == [1, 2, 3, 4, 5]
    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    try:
        canonical_outputs = [apply(canonical, grid) for grid in grids]
        rival_outputs = [apply(rival, grid) for grid in grids]
    finally:
        bridge.close()
    matches = [a == b for a, b in zip(canonical_outputs, rival_outputs)]
    lesson = [{"input": grid, "output": output}
              for grid, output in zip(grids, canonical_outputs)]
    hook = gen.lesson_identifiable(lesson[:4], lesson[4])
    report = {
        "schema": "bounded-peer-learnability-probe-v1",
        "task_id": TASK,
        "status": "peer_review_unverified_proposal",
        "finding": "unseen_flip_code_swap_fits_four_demos_and_differs_query",
        "bindings": {
            "generator_path": str(source.relative_to(root)),
            "generator_sha256": digest,
            "rule_hash": gen.RULE_HASH,
            "probe_sha256": sha(Path(__file__).read_bytes()),
            "canonical_ledger_path": str(ledger.relative_to(root)),
            "canonical_ledger_sha256": sha(ledger.read_bytes()),
            "canonical_program_sha256": sha(canonical.encode()),
            "rival_program_sha256": sha(rival.encode()),
            "runtime_identity": identity,
        },
        "scope": {"lessons": 1, "rivals": 1, "seed": 0, "difficulty": "easy",
                  "sample_indices": list(range(5)), "demo_indices": [0, 1, 2, 3],
                  "query_index": 4, "overrides": {}, "transform_codes": codes},
        "rival": {"name": "swap_flip_codes_5_and_6",
                  "description": "Select the unique one-hole object, use the canonical rotations for codes 1..4, map 5 to up-down flip and 6 to left-right flip, then scale 2x.",
                  "racket_program": rival},
        "canonical_program": canonical,
        "labels_source": "Both canonical and rival outputs executed by protected Racket backend.",
        "pairs": [{"sample_index": index, "role": "demo" if index < 4 else "query",
                   "transform_code": codes[index], "input": grids[index],
                   "canonical_output": canonical_outputs[index],
                   "rival_output": rival_outputs[index], "match": matches[index],
                   "self_check": gen.self_check(grids[index])} for index in range(5)],
        "result": {"demo_matches": matches[:4], "query_matches": matches[4],
                   "lesson_identifiable_reasons": hook,
                   "found": all(matches[:4]) and not matches[4]},
        "limitations": [
            "One default-generated easy lesson and one fixed rival; no full battery or acceptance decision.",
            "Finding concerns learning the code mapping from visible grids alone. An explicitly supplied code legend would resolve this ambiguity.",
            "Production generator, canonical authority, catalog, and approval records remain unchanged."
        ],
        "reproduce": "WORK/.venv/bin/python review.py run python3 ../checks/147c2b92e5c1/probe.py",
    }
    assert report["result"]["found"], report["result"]
    assert not hook, hook
    assert all(not row["self_check"] for row in report["pairs"])
    target = Path(__file__).with_name("probe-result.json")
    target.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"path": str(target), "sha256": sha(target.read_bytes()),
                      "generator_sha256": digest, "result": report["result"]}))


if __name__ == "__main__":
    main()

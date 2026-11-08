"""Reproduce the current-source ambiguity in generic_demo_transfer_gen1.

Run from the packet root with:
  python3 review.py run python3 ../checks/audit/generic_demo_transfer_gen1/reproduce_ambiguity.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import find_root, load_selected_generator

TASK_ID = "generic_demo_transfer_gen1"
SEED = 10
DIFFICULTY = "easy"
PAIR_INDEX = 1
HERE = Path(__file__).resolve().parent


def inner(grid, box):
    r1, c1, r2, c2 = box
    return [row[c1 + 1:c2] for row in grid[r1 + 1:r2]]


def locate_scene(module, grid):
    boxes = module._detect_boxes(grid)
    hole = next(
        box for box in boxes
        if all(value == 0 for row in inner(grid, box) for value in row)
    )
    others = [box for box in boxes if box != hole]

    def dist2(box):
        dr = (box[0] + box[2]) - (hole[0] + hole[2])
        dc = (box[1] + box[3]) - (hole[1] + hole[3])
        return dr * dr + dc * dc

    query = min(others, key=dist2)
    demos = [box for box in others if box != query]
    return boxes, hole, query, demos


def main() -> None:
    root = find_root(Path.cwd())
    module, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    task = module.generate_task(SEED, difficulty=DIFFICULTY)
    pair = task["train"][PAIR_INDEX]
    grid = pair["input"]
    boxes, hole, query, demos = locate_scene(module, grid)
    X = inner(grid, demos[0])
    Y = inner(grid, demos[1])
    Z = inner(grid, query)
    mx, my = module._mask(X), module._mask(Y)
    hits = [
        index
        for index, transform in enumerate(module._LIB)
        if transform(mx) == my or transform(my) == mx
    ]
    nonzero = [value for row in Z for value in row if value]
    qcol = max(set(nonzero), key=lambda value: (nonzero.count(value), -value))
    candidate_outputs = {
        str(index): module._apply_f(index, module._mask(Z), qcol)
        for index in hits
    }
    distinct_candidates = {
        json.dumps(value, sort_keys=True, separators=(",", ":"))
        for value in candidate_outputs.values()
    }
    assert hits == [2, 3], hits
    assert len(distinct_candidates) == 2, candidate_outputs
    assert module._unique_f(mx, my, hits[0]), "current _unique_f should reproduce acceptance"

    evidence = {
        "schema": "generic-demo-transfer-ambiguity-reproduction-v1",
        "task_id": TASK_ID,
        "generator_version": module.VERSION,
        "generator_source": str(source.relative_to(root)),
        "generator_sha256": source_sha256,
        "rule_hash": getattr(module, "RULE_HASH", None),
        "program_sha256": hashlib.sha256(module.PROGRAM.encode()).hexdigest(),
        "seed": SEED,
        "difficulty": DIFFICULTY,
        "split": "train",
        "pair_index": PAIR_INDEX,
        "documented_domain": "emitted directly by generate_task; no hand construction or filtering",
        "validator_status": "generator accepted and emitted the pair",
        "boxes": boxes,
        "hole": hole,
        "query": query,
        "demos": demos,
        "X": X,
        "Y": Y,
        "Z": Z,
        "hits": hits,
        "candidate_outputs": candidate_outputs,
        "selected_output": pair["output"],
        "failure": (
            "Two library transforms fit the visible demonstration in the allowed "
            "bidirectional test but produce different query answers. _unique_f "
            "accepts the intended transform when it is merely hits[0], rather than "
            "requiring len(hits) == 1."
        ),
        "command": [
            "python3", "review.py", "run", "python3",
            "../checks/audit/generic_demo_transfer_gen1/reproduce_ambiguity.py",
        ],
        "cwd": "packet_root",
    }
    out = HERE / "ambiguity-current.json"
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": "REPRODUCED",
        "generator_sha256": source_sha256,
        "hits": hits,
        "candidate_outputs_distinct": len(distinct_candidates),
        "evidence": str(out),
    }, indent=2))


if __name__ == "__main__":
    main()

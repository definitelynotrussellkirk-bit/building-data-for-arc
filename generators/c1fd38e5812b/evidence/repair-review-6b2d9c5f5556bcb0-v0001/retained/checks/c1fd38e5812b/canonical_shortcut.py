"""Replay the independent-axis shortcut against canonical demos and one lawful input."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK = "c1fd38e5812b"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    root = find_root(__file__)
    home = root / "generators" / TASK / "workspace/parametric"
    path = home / "audit_native.py"
    spec = importlib.util.spec_from_file_location("_compression_question_audit", path)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    selected = Catalog(root).get(TASK)
    programs = {v["program_solution"] for v in selected["variants"]}
    if len(programs) != 1:
        raise ValueError("Expected one canonical authority")
    intended = next(iter(programs))
    rival = audit.rival_program({"view": "compressed"}, "coupled_cols")
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines() if line.strip()]
    variants = [r for r in rows if r.get("task_id") == TASK]
    vi = next(i for i, row in enumerate(variants) if row.get("source") == "training")
    demos = [p for p in canonical_pairs(TASK, root=root, variant=vi) if p["split"] == "train"]
    logical = [[0, 1], [2, 2], [3, 3], [0, 1], [2, 2], [3, 3]]
    row_spans, col_spans = [2] * 6, [4, 8]
    grid = audit.expand(logical, row_spans, col_spans)
    generator, source_path, source_sha = load_selected_generator(TASK, root=root)
    errors = generator.self_check(grid)
    if errors:
        raise ValueError(f"Retained witness is not accepted by unchanged production validator: {errors}")
    executed = []
    with _local_imports(root / "shared/runtime", home):
        apply, identity, bridge = _real_evaluator(root / "shared/runtime")
        try:
            for pair in demos:
                reference, alternative = apply(intended, pair["input"]), apply(rival, pair["input"])
                assert reference == pair["output"] == alternative
                executed.append({**pair, "rival_output": alternative})
            reference, alternative = apply(intended, grid), apply(rival, grid)
            assert reference == logical and reference != alternative
            assert alternative == audit.rival_reference(grid, {"view": "compressed"}, "coupled_cols")
        finally:
            bridge.close()
    report = {
        "schema": "c1fd38e5812b-canonical-shortcut-replay-v1", "task_id": TASK,
        "status": "reproduced", "source_sha256": source_sha,
        "canonical_rule_hash": Catalog(root).describe(TASK)["rule_hash"],
        "declared_module_pin": generator.RULE_HASH,
        "canonical_program_sha256": hashlib.sha256(intended.encode()).hexdigest(),
        "rival_program_sha256": hashlib.sha256(rival.encode()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "programs": {"canonical": intended, "coupled_columns": rival},
        "canonical_train": executed, "fits_every_canonical_demonstration": True,
        "fit_frozen_before_witness": True,
        "witness": {"input": grid, "output": reference, "rival_output": alternative,
                    "logical_grid": logical, "row_spans": row_spans, "col_spans": col_spans,
                    "self_check_errors": errors, "seed": None, "sample_index": None,
                    "kind": "handcrafted accepted-domain witness; no production draw claimed"},
        "racket": identity, "racket_evaluations": 2 * len(demos) + 2,
        "scope": "Fresh protected replay of all four canonical training demonstrations and one exact inherited mixed-axis witness; no new production census or production repair.",
        "training_admitted": False, "visibility": "controller_private",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "canonical_demos": len(demos),
                      "racket_evaluations": report["racket_evaluations"], "out": str(args.out)}))


if __name__ == "__main__":
    main()

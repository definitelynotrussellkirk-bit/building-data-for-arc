"""Verify the retained scale-map ambiguity with the actual Racket runtime."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.generic.concepts.extraction import _program_body

ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators" / "generic_resize_gen3" / "generator.py"
AMBIGUITY = Path(__file__).with_name("ambiguity.json")
OUT = Path(__file__).with_name("racket-parity.json")


def load_module():
    spec = importlib.util.spec_from_file_location("audit_generic_resize_gen3_racket", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main():
    retained = json.loads(AMBIGUITY.read_text())
    finding = retained["finding"]
    module = load_module()
    task = module.generate_task(finding["seed"], difficulty=finding["difficulty"])
    intended_body = _program_body(task["program"])
    rows = " ".join(str(x) for x in finding["true_row_scales"])
    alt_cols = " ".join(str(x) for x in finding["alternative_col_scales"])
    alternate_body = f"(scale-map g (list {rows}) (list {alt_cols}))"

    bridge = RacketBridge()
    records = []
    for split in ("train", "test"):
        for index, pair in enumerate(task[split]):
            bridge.define_grid("g", pair["input"])
            intended = bridge.eval_text(intended_body)
            bridge.define_grid("g", pair["input"])
            alternate = bridge.eval_text(alternate_body)
            records.append({
                "split": split,
                "index": index,
                "intended_matches_stored": intended == pair["output"],
                "alternate_matches_stored": alternate == pair["output"],
                "intended_sha256": hashlib.sha256(json.dumps(intended, separators=(",", ":")).encode()).hexdigest(),
                "alternate_sha256": hashlib.sha256(json.dumps(alternate, separators=(",", ":")).encode()).hexdigest(),
            })

    result = {
        "schema": "generic-resize-gen3-racket-ambiguity-v1",
        "task_id": "generic_resize_gen3",
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "seed": finding["seed"],
        "difficulty": finding["difficulty"],
        "intended_program": task["program"],
        "alternate_body": alternate_body,
        "records": records,
        "all_intended_match": all(row["intended_matches_stored"] for row in records),
        "alternate_fits_all_train": all(row["alternate_matches_stored"] for row in records if row["split"] == "train"),
        "alternate_differs_on_test": any(not row["alternate_matches_stored"] for row in records if row["split"] == "test"),
        "replay": {
            "cwd": "repo",
            "argv": ["python3", "../checks/audit/generic_resize_gen3/verify_racket.py"],
        },
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not (result["all_intended_match"] and result["alternate_fits_all_train"] and result["alternate_differs_on_test"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Reproduce one retained canonical-demo learnability witness in protected Racket."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from puzzle_generators import runner

ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
TASK = "c1b540a1d7b0"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_sha(value) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def main() -> None:
    canonical_path = ROOT / "shared/data/canonical/puzzles.jsonl"
    row = next(json.loads(line) for line in canonical_path.read_text().splitlines()
               if json.loads(line).get("task_id") == TASK)
    source_path = ROOT / f"generators/{TASK}/generator.py"
    program = row["program_solution"]
    replacements = (
        ("(define (add-arm a b da db)", "(define (add-arm a b da db ks)"),
        ("(for ((k (list 0 1 2)))", "(for ((k ks))"),
        ("(add-arm a b (car (first nb)) (cdr (first nb)))",
         "(add-arm a b (car (first nb)) (cdr (first nb)) (list 0 1 2))"),
        ("(add-arm a b (car chosen) (cdr chosen))",
         "(add-arm a b (car chosen) (cdr chosen) (list 0 1 2 3 4))"),
    )
    rival = program
    for old, new in replacements:
        assert rival.count(old) == 1, old
        rival = rival.replace(old, new)
    (OUT / "rival.rkt").write_text(rival + "\n")
    pairs = []
    for split in ("train", "test"):
        split_pairs = row[split]
        if isinstance(split_pairs, dict):
            split_pairs = [split_pairs]
        for index, pair in enumerate(split_pairs):
            pairs.append((split, index, pair))
    outputs = {}
    runtime_identities = {}
    for name, code in (("canonical", program), ("rival", rival)):
        bridge, fn = runner._open_bridge_with_rule(runner.wrap_rule(code))
        try:
            runtime_identities[name] = bridge.runtime_identity
            assert runtime_identities[name]["protected"] is True
            outputs[name] = [runner._apply_rule(bridge, fn, pair["input"])
                             for _, _, pair in pairs]
        finally:
            bridge.close()
    cases = []
    for (split, index, pair), actual, alternative in zip(
            pairs, outputs["canonical"], outputs["rival"]):
        assert actual == pair["output"], (split, index, "canonical label mismatch")
        changes = [{"row": r, "column": c, "canonical": value,
                    "rival": alternative[r][c]}
                   for r, line in enumerate(actual) for c, value in enumerate(line)
                   if value != alternative[r][c]]
        cases.append({"split": split, "pair_index": index,
                      "input_sha256": json_sha(pair["input"]),
                      "canonical_output_sha256": json_sha(actual),
                      "rival_output_sha256": json_sha(alternative),
                      "rival_matches_label": alternative == pair["output"],
                      "changed_cells": changes,
                      **({"input": pair["input"], "canonical_output": actual,
                          "rival_output": alternative} if changes else {})})
    assert sum(c["split"] == "train" and c["rival_matches_label"] for c in cases) == 3
    assert sum(c["split"] == "test" and bool(c["changed_cells"]) for c in cases) == 1
    result = {
        "schema": "arcpuzzles-peer-learnability-probe-v1",
        "task_id": TASK,
        "status": "retained_ambiguity_reproduced",
        "source_binding": {"path": str(source_path.relative_to(ROOT)),
                           "sha256": sha(source_path.read_bytes()),
                           "rule_hash": sha(" ".join(program.split()).encode())[:12]},
        "canonical_program_sha256": sha(program.encode()),
        "canonical_row_sha256": json_sha(row),
        "canonical_data_path": str(canonical_path.relative_to(ROOT)),
        "rival_program_sha256": sha(rival.encode()),
        "probe_sha256": sha(Path(__file__).read_bytes()),
        "rival_definition": {"tip_arm_length": 3, "bridge_arm_length": 5,
                             "direction_tie_break": ["up", "left", "down", "right"],
                             "only_semantic_difference": "bridge arm offsets 0..2 become 0..4"},
        "demonstrations_fit": 3,
        "held_out_queries_changed": 1,
        "pairs": cases,
        "racket": runtime_identities,
        "scope": "Reproduced the existing bridge-length rival on the single canonical row: 3 demos and 1 query, 8 protected Racket evaluations. No generator edit, population census, new sampling or parametric qualification.",
        "remaining_limits": ["Only one pre-existing rival was tested.",
                             "This demonstrates underidentification from these visible demonstrations, not that the alternative is the intended rule.",
                             "No repair or acceptance is claimed; the official-template replay audit was not rechecked."],
    }
    (OUT / "ambiguity.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "demonstrations_fit": 3,
                      "held_out_queries_changed": 1, "query_changes": cases[-1]["changed_cells"],
                      "source_binding": result["source_binding"]}, sort_keys=True))


if __name__ == "__main__":
    main()

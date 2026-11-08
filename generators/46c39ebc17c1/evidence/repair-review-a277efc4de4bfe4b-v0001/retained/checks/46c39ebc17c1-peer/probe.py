"""Bounded direct research sampler: source-color omission lesson counterexample."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from reviewer_support import canonical_path, load_selected_generator
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

TASK = "46c39ebc17c1"
SEED = 1

def digest(data):
    return hashlib.sha256(data).hexdigest()

def save(name, data):
    (HERE / name).write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")

def main():
    generator, source_path, source_hash = load_selected_generator(TASK, root=ROOT)
    programs = set()
    with canonical_path(ROOT).open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    reference = programs.pop()
    old = "(when\n                               solid"
    new = "(when\n                               (and solid (!= color 3))"
    assert reference.count(old) == 1
    rival = reference.replace(old, new, 1)
    assert digest(re.sub(r"\s+", " ", reference).strip().encode())[:12] == generator.RULE_HASH
    (HERE / "reference.rkt").write_text(reference)
    (HERE / "rival.rkt").write_text(rival)
    grids = [generator.generate(SEED, i, difficulty="easy") for i in range(5)]
    assert all(generator.self_check(grid) == [] for grid in grids)
    outputs, evaluations = [], 0
    with _local_imports(ROOT / "shared/runtime", source_path.parent):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            for index, grid in enumerate(grids):
                actual = _grid(apply(reference, grid))
                alternate = _grid(apply(rival, grid))
                evaluations += 2
                assert actual == generator.solve_python(grid)
                facts = generator._analyze(grid)
                outputs.append({"sample_index": index, "input": grid,
                                "output": actual, "rival_output": alternate,
                                "fits": actual == alternate,
                                "background_color_3_count": facts["background_counts"][3],
                                "rectangle_colors": [r["color"] for r in
                                    facts["rectangles"]]})
        finally:
            bridge.close()
    finding = all(pair["fits"] for pair in outputs[:4]) and not outputs[4]["fits"]
    changes = [[r, c] for r, row in enumerate(outputs[4]["output"])
               for c, value in enumerate(row) if value != outputs[4]["rival_output"][r][c]]
    assert finding, "Pinned bounded lesson no longer exhibits the retained finding"
    episode = {"train": [{"input": p["input"], "output": p["output"]} for p in outputs[:4]],
               "test": [{"input": outputs[4]["input"], "output": outputs[4]["output"]}],
               "rival_query_output": outputs[4]["rival_output"],
               "query_disagreement_cells": changes}
    save("counterexample.json", episode)
    save("evaluations.json", outputs)
    summary = {"schema": "bounded-peer-learnability-probe-v1", "task_id": TASK,
        "status": "counterexample_confirmed", "source_path": str(source_path.relative_to(ROOT)),
        "source_sha256": source_hash, "rule_hash": generator.RULE_HASH,
        "reference_program_sha256": digest(reference.encode()),
        "rival_program_sha256": digest(rival.encode()), "runtime_identity": identity,
        "sampling": "direct research sampler; no normal export or approval change",
        "seed": SEED, "difficulty": "easy", "demo_indices": [0, 1, 2, 3], "query_index": 4,
        "exploratory_seeds": [0, 1], "exploratory_grids": 10,
        "reference_evaluations": 5, "rival_evaluations": 5, "evaluation_count": evaluations,
        "demos_fit": sum(p["fits"] for p in outputs[:4]),
        "query_disagreement_cell_count": len(changes),
        "rival_description": "Treat color 3 as fixed background; recolor qualifying solid rectangles of other colors yellow. Implemented by excluding color-3 rectangles from the canonical geometry scan.",
        "finding": "Color 3 occurs only in dense unchanged background in all four natural easy demonstrations; the next query requires recoloring a color-3 rectangle. The fixed-background-3 hypothesis fits all demonstrations and differs on query.",
        "role_evidence": [{"sample_index": p["sample_index"],
                           "rectangle_colors": p["rectangle_colors"],
                           "background_color_3_count": p["background_color_3_count"]} for p in outputs],
        "recommendation": "Consider lesson-level coverage of source colors or a declared palette-restriction rival; no source repair attempted.",
        "limitations": ["One naturally generated five-pair easy lesson replayed; two seeds inspected for input-only profile/color facts.",
            "Finite rival ambiguity is not proof that a human cannot infer the intended rule.",
            "The fixed-background-color rival is a bounded role-based hypothesis, not a universal defect or a claim of general learner failure.",
            "No broad battery, parametric gate, acceptance change, or training admission performed."]}
    save("summary.json", summary)
    print(json.dumps({k: summary[k] for k in ("status", "seed", "demos_fit", "evaluation_count", "query_disagreement_cell_count")}))

if __name__ == "__main__":
    main()

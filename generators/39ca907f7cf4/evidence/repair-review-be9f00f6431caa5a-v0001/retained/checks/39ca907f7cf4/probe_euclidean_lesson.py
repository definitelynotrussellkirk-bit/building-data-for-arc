"""Replay one retained Manhattan/Euclidean teaching counterexample, privately."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import canonical_path, load_selected_generator


TASK_ID = "39ca907f7cf4"
EXPECTED_SOURCE = "6b6678b2dbe5cb1934cf16757f4575e30cba3d7c6f3b20f8b59a81a049977e8a"
RETAINED = (
    f"generators/{TASK_ID}/counterexamples/review-744c58f59a7bb8e9-v0001/"
    f"retained/checks/audit/{TASK_ID}/counterexample.json"
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    root = Path.cwd().resolve()
    gen, source, source_sha = load_selected_generator(TASK_ID, root=root)
    assert source_sha == EXPECTED_SOURCE, "reassess the witness after source drift"
    retained_path = root / RETAINED
    retained_bytes = retained_path.read_bytes()
    retained = json.loads(retained_bytes)
    assert retained["generator_sha256"] == source_sha
    grids = [gen.generate(4, i, difficulty="medium") for i in range(4)]
    assert grids == retained["inputs"], "the retained production draw no longer reproduces"
    assert all(gen.self_check(grid) == [] for grid in grids)

    programs = set()
    with canonical_path(root).open() as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.add(row["program_solution"])
    assert len(programs) == 1
    canonical = programs.pop()
    old = "(define (manhattan a b) (+ (abs (- (first a) (first b))) (abs (- (second a) (second b)))))"
    new = "(define (manhattan a b) (+ (* (- (first a) (first b)) (- (first a) (first b))) (* (- (second a) (second b)) (- (second a) (second b)))))"
    assert canonical.count(old) == 1, "canonical metric changed; review the rival construction"
    rival = canonical.replace(old, new).replace("manhattan", "euclidean-squared")
    with _local_imports(root / "shared/runtime", root / "shared/runtime"):
        apply, identity, bridge = _real_evaluator(root / "shared/runtime")
        try:
            labels = [_grid(apply(canonical, grid)) for grid in grids]
            alternatives = [_grid(apply(rival, grid)) for grid in grids]
        finally:
            bridge.close()
    assert labels == retained["actual_racket_outputs"]
    assert alternatives == retained["rival_outputs"]
    demos = [{"input": grid, "output": output} for grid, output in zip(grids[:3], labels[:3])]
    query = {"input": grids[3]}
    guard_findings = gen.lesson_identifiable(demos, query)
    demo_matches = [actual == alternate for actual, alternate in zip(labels[:3], alternatives[:3])]
    query_differs = labels[3] != alternatives[3]
    assert all(demo_matches) and query_differs
    assert guard_findings == [], "the known teaching guard has now been repaired"

    # A bounded lesson-selection proposal uses the same already-executed pairs.
    # It does not claim to repair the production sampler or its broader support.
    proposal_indices = [0, 1, 3]
    proposal_demos = [{"input": grids[i], "output": labels[i]} for i in proposal_indices]
    proposal_survives = all(labels[i] == alternatives[i] for i in proposal_indices)
    proposal_guard = gen.lesson_identifiable(proposal_demos, {"input": grids[2]})
    assert not proposal_survives and proposal_guard == []

    distances = []
    for grid in grids:
        analysis = gen._analyze(grid)
        mr, mc = analysis["marker_cell"]
        distances.append([
            {"color": obj["color"],
             "nearest_manhattan": min(abs(mr-r) + abs(mc-c) for r, c in obj["cells"]),
             "nearest_euclidean_squared": min((mr-r)**2 + (mc-c)**2 for r, c in obj["cells"])}
            for obj in analysis["candidates"]
        ])
    assert sha(source.read_bytes()) == source_sha
    result = {
        "schema": "arcpuzzles-peer-teaching-probe-v1",
        "task_id": TASK_ID,
        "finding": "confirmed_existing_unresolved_teaching_ambiguity",
        "source_binding": {"generator": source.relative_to(root).as_posix(),
                           "generator_sha256": source_sha, "rule_hash": gen.RULE_HASH,
                           "canonical_program_sha256": sha(canonical.encode()),
                           "probe_sha256": sha(Path(__file__).read_bytes())},
        "retained_witness": {"path": RETAINED, "sha256": sha(retained_bytes),
                             "inputs_reproduced": True},
        "seed": 4, "difficulty": "medium", "sample_indices": [0, 1, 2, 3],
        "racket": identity, "racket_evaluations": 8,
        "programs": {"canonical": canonical, "nearest_euclidean_cell": rival},
        "inputs": grids, "canonical_outputs": labels, "rival_outputs": alternatives,
        "candidate_distances": distances,
        "validator_findings": [gen.self_check(grid) for grid in grids],
        "demo_rival_matches": demo_matches, "query_rival_differs": query_differs,
        "current_lesson_identifiable_findings": guard_findings,
        "rival_declared": "nearest_euclidean_cell" in gen.LESSON_COMPETITORS,
        "bounded_lesson_selection_proposal": {
            "demo_sample_indices": proposal_indices, "query_sample_index": 2,
            "euclidean_rival_survives_demonstrations": proposal_survives,
            "current_named_rival_guard_findings": proposal_guard,
            "label_basis": "the same eight protected Racket executions above",
            "status": "validated_for_this_lesson_only_not_applied_to_production",
        },
        "limits": [
            "One retained legal four-input production lesson and one explicit metric rival only.",
            "Canonical-pair rival fit and the separate middle-reading-order finding remain inherited evidence, not re-executed here.",
            "No generator repair, broad support census, battery, approval, acceptance or training admission.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"finding": result["finding"], "generator_sha256": source_sha,
                      "racket_evaluations": 8, "demo_rival_matches": demo_matches,
                      "query_rival_differs": query_differs,
                      "current_lesson_identifiable_findings": guard_findings,
                      "bounded_proposal_eliminates_euclidean_rival": not proposal_survives,
                      "evidence": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()

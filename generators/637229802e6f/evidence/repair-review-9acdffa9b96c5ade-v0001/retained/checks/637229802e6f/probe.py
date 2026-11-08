"""One bounded, source-bound peer probe; labels come from protected Racket."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root, load_selected_generator
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator


TASK_ID = "637229802e6f"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
RIVAL = """(rule!
 (let* ((mr (first (filter
                    (lambda (r) (> (count-where (lambda (v) (= v 2))
                                                (list-ref g r)) 0))
                    (range h))))
        (mc (first (filter (lambda (c) (= (at g mr c) 2)) (range w)))))
   (grid-from-fn h w
     (lambda (r c)
       (if (and (<= mr r) (< r (+ mr 2))
                (<= mc c) (< c (+ mc 2))) 2 6)))))"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "marker-anchor-boundary.json")
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("Use a fresh --out path to preserve the earlier source-bound case")
    canonical = next(
        json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
        if json.loads(line)["task_id"] == TASK_ID
    )["program_solution"]
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, runtime):
        gen, source, source_hash = load_selected_generator(TASK_ID, root=ROOT)
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            materialized = []
            for index in range(5):
                grid = gen.generate(0, index, difficulty="easy")
                assert not gen.self_check(grid)
                expected = apply(canonical, grid)
                alternate = apply(RIVAL, grid)
                assert expected == gen.rule_mirror(grid)
                materialized.append({
                    "sample_index": index,
                    "observed_axes": gen.observe_overrides(grid),
                    "input": grid,
                    "output": expected,
                    "rival_output": alternate,
                })
        finally:
            bridge.close()

    demos = materialized[1:4]
    query = materialized[4]
    reasons = gen.lesson_identifiable(demos, query)
    assert all("marker_as_" in reason for reason in reasons)
    assert all(pair["output"] == pair["rival_output"] for pair in demos)
    assert query["output"] != query["rival_output"]
    assert all(pair["output"] == pair["rival_output"] for pair in materialized[:4])
    report = {
        "task_id": TASK_ID,
        "outcome": "rejected_teaching_gap" if reasons else "confirmed_teaching_gap",
        "generator_source": str(source.relative_to(ROOT)),
        "generator_sha256": source_hash,
        "canonical_program": canonical,
        "canonical_program_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "canonical_normalized_rule_hash": gen.RULE_HASH,
        "rival_program": RIVAL,
        "rival_program_sha256": hashlib.sha256(RIVAL.encode()).hexdigest(),
        "rival_description": "Paint a 2x2 red block with the marker as its top-left corner, clipping to the 4x4 grid; paint the other cells magenta.",
        "racket": identity,
        "seed": 0,
        "difficulty": "easy",
        "demonstrations": demos,
        "query": query,
        "declared_lesson_identifiable_reasons": reasons,
        "rival_fits_all_demonstrations": True,
        "rival_disagrees_on_query": True,
        "aligned_control": {
            "sample_indices": [0, 1, 2, 3],
            "all_outputs_match_rival": True,
            "extra_pair": materialized[0],
        },
        "execution_count": 10,
        "scope": "One seed, easy difficulty, five consecutive input draws, one additional total rival. This does not claim all production lessons are ambiguous or universal rule identifiability.",
        "repair_direction": "Teach multiple local marker slots within the demonstrations before a query changes slot, and include marker-anchored rectangle rivals in lesson checks; preserve three demonstrations and the canonical output rule.",
    }
    output = args.out
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"task_id": TASK_ID, "outcome": report["outcome"],
                      "generator_sha256": source_hash, "racket_evaluations": 10,
                      "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""One bounded, source-bound accepted-grammar elbow-order ambiguity probe.

Run through review.py run from this packet. Four scheduled demonstrations and
one manually constructed strict-accepted query are labeled with protected Racket.
The query is not claimed to belong to the current generator's output support.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


ROOT = Path.cwd()
TASK = "b5c887448ed9"
HOME = ROOT / "generators" / TASK
RUNTIME = ROOT / "shared/runtime"
OUT = Path(__file__).with_name("second_endpoint_probe.json")


def main():
    task = Catalog(".").get(TASK)
    program = task["variants"][0]["program_solution"]
    assert {v["program_solution"] for v in task["variants"]} == {program}
    needle = "(in-list (e8b-colors-reading g))"
    replacement = "(in-list (sort (e8b-colors-reading g) (lambda (a b) (e8b-list< (second (sort (find-color g a) e8b-list<)) (second (sort (find-color g b) e8b-list<))))))"
    assert program.count(needle) == 1
    rival = program.replace(needle, replacement)
    with _local_imports(RUNTIME, HOME):
        spec = importlib.util.spec_from_file_location("reviewed_elbows", HOME / "generator.py")
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        demos = [gen.generate(17, i, difficulty="medium") for i in range(4)]
        query = [[0] * 8 for _ in range(7)]
        for color, cells in ((1, ((0, 0), (6, 4))), (2, ((2, 7), (4, 1)))):
            for r, c in cells:
                query[r][c] = color
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            cases = []
            for i, grid in enumerate(demos + [query]):
                actual = _grid(apply(program, _grid(grid)))
                predicted = _grid(apply(rival, _grid(grid)))
                cases.append({
                    "kind": "demo" if i < 4 else "query",
                    "demo_sample_index": i if i < 4 else None,
                    "input": grid,
                    "canonical_output": actual,
                    "rival_output": predicted,
                    "strict_errors": gen.strict_canonical_like(grid),
                    "python_mirror_matches_racket": gen._predict(grid) == actual,
                    "rival_matches": predicted == actual,
                    "differences": [{"row": r, "col": c, "canonical": actual[r][c], "rival": predicted[r][c]}
                                    for r in range(len(grid)) for c in range(len(grid[0]))
                                    if actual[r][c] != predicted[r][c]],
                })
        finally:
            bridge.close()
        lesson = [{"input": row["input"], "output": row["canonical_output"]} for row in cases]
        reasons = gen.lesson_identifiable(lesson[:4], lesson[4])
        report = {
            "task_id": TASK,
            "generator_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(),
            "rule_hash": task["rule_hash"],
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "rival_program_sha256": hashlib.sha256(rival.encode()).hexdigest(),
            "rival_program": rival,
            "rival_description": "Paint ordered elbows by row-major order of the second endpoint, rather than the first endpoint.",
            "demo_recipe": {"seed": 17, "sample_indices": [0, 1, 2, 3], "difficulty": "medium"},
            "query_origin": "hand-constructed within strict_canonical_like; not a claimed generator output",
            "racket": identity,
            "racket_evaluations": 10,
            "cases": cases,
            "lesson_identifiable_reasons": reasons,
            "finding_confirmed": all(not row["strict_errors"] and row["python_mirror_matches_racket"] for row in cases)
                and all(row["rival_matches"] for row in cases[:4]) and not cases[4]["rival_matches"] and not reasons,
            "limits": "One four-demo lesson and one accepted-grammar custom query. No claim of a generated-query counterexample, exhaustive support coverage, native qualification, parametric verification, or failed canonical output. Production generator unchanged.",
        }
        OUT.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"finding_confirmed": report["finding_confirmed"], "generator_sha256": report["generator_sha256"], "differences": cases[4]["differences"], "out": str(OUT)}))
        return 0 if report["finding_confirmed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

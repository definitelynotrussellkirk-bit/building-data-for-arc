"""Replay the unchanged prototype's seed-zero lesson against a size-only rule."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

ROOT = Path.cwd().resolve()
HOME = ROOT / "generators/5f9a2df57599/workspace/parametric"
OUT = ROOT.parent / "checks/5f9a2df57599/legacy-shortcut.json"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    assert not OUT.exists(), "Retained replay output must be new"
    proto = load("legacy_wall_prototype", HOME / "prototype.py")
    assert hashlib.sha256((HOME / "prototype.py").read_bytes()).hexdigest() == "5117dffb6b5b9adab9197838271916fa2725b949d2df48739ff871689836024d"
    gate = load("legacy_wall_gate", HOME / "check_wall_teaching.py")
    demos, queries, production = proto._generate_inputs(0, 3, 4, root=ROOT)
    inputs = demos + queries
    records, episodes = [], []
    with _local_imports(ROOT / "shared/runtime", HOME):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            for policy in proto.SIDE_POLICIES:
                intended = proto.materialize_program(policy, root=ROOT)
                side = "#t" if policy == "canvas_edges" else "(and (> c1 0) (< c2 (- w 1)))"
                rival = f"""(rule! (lambda (g)
  (let ((h (rows g)) (w (cols g)))
    (paint-objects-by g (objects g 5)
      (lambda (obj) (with-bbox obj (r1 c1 r2 c2)
        (and (= (obj-color obj) 0) (<= (+ 1 (- r2 r1)) 4)
             (<= (+ 1 (- c2 c1)) 4) (> r1 0) (< r2 (- h 1))
             {side} (not (and (= c1 0) (= c2 0) (> r2 r1))) 4)))))))"""
                labeled, wrong, fits = [], [], []
                for index, row in enumerate(inputs):
                    grid = row["input"]
                    output = _grid(apply(intended, grid))
                    assert output == proto.python_apply(grid, policy)
                    counterfactual = _grid(apply(rival, grid))
                    expected = [line[:] for line in grid]
                    for cells in gate._components(grid):
                        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
                        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
                        eligible = (r1-r0+1 <= 4 and c1-c0+1 <= 4 and r0 > 0 and r1 < len(grid)-1
                            and not (c0 == c1 == 0 and r1 > r0)
                            and (policy == "canvas_edges" or 0 < c0 <= c1 < len(grid[0])-1))
                        if eligible:
                            for r, c in cells:
                                expected[r][c] = 4
                    assert counterfactual == expected
                    labeled.append({"input": grid, "output": output})
                    wrong.append(counterfactual)
                    fits.append(counterfactual == output)
                    records.append({"settings": {"side_boundary_policy": policy}, "pair_index": index,
                        "input": grid, "output": output, "rival_output": counterfactual,
                        "intended_program_sha256": hashlib.sha256(intended.encode()).hexdigest(),
                        "rival_program_sha256": hashlib.sha256(rival.encode()).hexdigest(), "rival_matches": fits[-1]})
                episodes.append({"seed": 0, "settings": {"side_boundary_policy": policy},
                    "train": labeled[:3], "test": labeled[3:], "program_solution": intended,
                    "rival_program": rival, "rival_demo_fits": fits[:3], "rival_query_fits": fits[3:],
                    "gate": gate.check_episode({"train": labeled[:3]})})
        finally:
            bridge.close()
    report = {"schema": "legacy-wall-shortcut-replay-v1", "task_id": "5f9a2df57599",
        "scope": "Two seed-zero unchanged-prototype lessons, three demos and four queries. A policy-aware size rule skips every gray-wall predicate. Bounded distribution shortcut, not wrong intended labels or an all-seed claim.",
        "racket": identity, "evaluations": 28, "intended_evaluations": 14, "rival_evaluations": 14,
        "production": production, "generator_requests": {"train": demos, "test": queries},
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [HOME / "prototype.py", HOME / "check_wall_teaching.py", ROOT / production["path"]]},
        "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "episodes": episodes, "executions": records, "training_admitted": False}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"path": str(OUT), "evaluations": report["evaluations"],
        "fits": [{"policy": ep["settings"], "demos": ep["rival_demo_fits"], "queries": ep["rival_query_fits"], "gate": ep["gate"]["status"]} for ep in episodes]}, indent=2))


if __name__ == "__main__":
    main()

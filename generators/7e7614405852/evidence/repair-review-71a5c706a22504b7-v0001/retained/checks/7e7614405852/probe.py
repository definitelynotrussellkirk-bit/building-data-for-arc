"""One bounded, protected-Racket lesson probe for an undeclared length-four rival."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _real_evaluator


TASK = "7e7614405852"
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "generators" / TASK / "generator.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location("_peer_7e7614405852_generator", SOURCE)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    catalog = Catalog(ROOT)
    row = catalog.describe(TASK)
    authority = row.get("rule_task_id", TASK)
    canonical_programs = {v["program_solution"] for v in catalog._variants()[authority]}
    assert len(canonical_programs) == 1
    canonical = next(iter(canonical_programs))
    needle = "(= (+ 1 (- cc c)) 3)"
    assert canonical.count(needle) == 1
    rival = canonical.replace(needle, "(or (= (+ 1 (- cc c)) 3) (= (+ 1 (- cc c)) 4))")

    # This is a search for one lesson, not a sampler census. All four calls
    # are ordinary generation, without difficulty or structural overrides.
    indices = (0, 1, 3, 2)
    selected = None
    seeds_examined = 0
    for seed in range(32):
        seeds_examined += 1
        grids = [generator.generate(seed, index) for index in indices]
        axes = [generator.observe_overrides(grid) for grid in grids]
        if all(item["n_len4"] == 0 for item in axes[:3]) and axes[3]["n_len4"] > 0:
            selected = seed, grids, axes
            break
    base = {
        "task_id": TASK,
        "scope": "One extra rival and one bounded lesson; not exhaustive identifiability or a measured rate.",
        "prior_audit": "Existing side-border orientation finding was read; this probes a separate length-four rival.",
        "source_binding": {
            "generator_sha256": sha(SOURCE),
            "rule_hash": row["rule_hash"],
            "rule_task_id": authority,
            "canonical_program_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "rival_program_sha256": hashlib.sha256(rival.encode()).hexdigest(),
            "probe_sha256": sha(Path(__file__)),
            "parametric_worker_sha256": sha(ROOT / "src/arcpuzzles/parametric_worker.py"),
        },
        "search": {"seed_range": [0, 31], "seeds_examined": seeds_examined,
                   "sample_indices": list(indices), "difficulty": None, "overrides": {}},
        "canonical_program": canonical,
        "rival_program": rival,
        "rival_meaning": "Recolor the second cell of maximal horizontal nonzero monochromatic runs of length three or four; leave other lengths unchanged.",
        "argv": sys.argv,
        "cwd": str(ROOT),
    }
    if selected is None:
        result = {**base, "status": "bounded_no_finding", "protected_execution": False}
    else:
        seed, grids, axes = selected
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            canonical_outputs = [apply(canonical, grid) for grid in grids]
            rival_outputs = [apply(rival, grid) for grid in grids]
        finally:
            bridge.close()
        pairs = [{"input": grid, "output": output}
                 for grid, output in zip(grids, canonical_outputs)]
        fits = all(left == right for left, right in zip(canonical_outputs[:3], rival_outputs[:3]))
        differences = [{"row": r, "col": c, "canonical": canonical_outputs[3][r][c],
                        "rival": rival_outputs[3][r][c]}
                       for r in range(len(grids[3])) for c in range(len(grids[3][0]))
                       if canonical_outputs[3][r][c] != rival_outputs[3][r][c]]
        hook = generator.lesson_identifiable(pairs[:3], pairs[3])
        assert identity["protected"] is True and identity["backend"] == "racket"
        assert fits and differences and hook == []
        assert all(generator.self_check(grid) == [] for grid in grids)
        assert len({json.dumps(grid) for grid in grids}) == 4
        result = {**base, "status": "finding", "seed": seed, "runtime": identity,
                  "protected_execution": True, "racket_evaluations": 8,
                  "rival_fits_all_demos": fits, "query_differences": differences,
                  "lesson_identifiable_reasons": hook, "observed_axes": axes,
                  "public_challenge": {"train": pairs[:3], "test": [{"input": grids[3]}]},
                  "private_query_output": canonical_outputs[3],
                  "rival_outputs": rival_outputs,
                  "validators": [generator.self_check(grid) for grid in grids],
                  "declared_rivals_refuted_by_demos": {
                      name: any(fn(pair["input"]) != pair["output"] for pair in pairs[:3])
                      for name, fn in generator.LESSON_COMPETITORS.items()}}
    (OUT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "seeds_examined": seeds_examined,
                      "seed": result.get("seed"), "differences": result.get("query_differences"),
                      "generator_sha256": base["source_binding"]["generator_sha256"]}))


if __name__ == "__main__":
    main()

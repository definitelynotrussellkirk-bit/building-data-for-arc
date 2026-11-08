"""Bounded visible-demo check for the existing leading-gap-only rival.

Run from WORK/repo via the outer review.py launcher. Searches at most 512
deterministic four-call episodes and then replays only the first witness using
the protected Racket authority. This is not a production lesson census.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path.cwd().resolve()
RUNTIME = ROOT / "shared/runtime"
TASK = "ba9d8eb0cd5a"
HOME = ROOT / "generators" / TASK
OUT = ROOT.parent / "checks" / TASK / "visible-demo-witness.json"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

RIVAL = '''(rule!
 (let ((packed (gravity g "left")))
  (grid-from-fn (rows g) (cols g)
   (lambda (r c)
    (if (= (at g r 0) 0) (at packed r c) (at g r c))))))'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packed(grid):
    result = []
    for row in grid:
        values = [value for value in row if value]
        result.append(values + [0] * (len(row) - len(values)))
    return result


def rival(grid):
    return [out if row[0] == 0 else list(row)
            for row, out in zip(grid, packed(grid))]


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    bound = {"generator.py": sha(HOME / "generator.py"),
             "probe.py": sha(Path(__file__).resolve()),
             "canonical/puzzles.jsonl": sha(ROOT / "shared/data/canonical/puzzles.jsonl")}
    assert bound["generator.py"] == "2e8eff2841fb77f8c50326cb0f5b871f5f4f93dc290cc961248adeac8ca7cf94"
    report = {
        "schema": "ba9d8eb0cd5a-visible-demo-probe-v1", "task_id": TASK,
        "source_sha256": bound, "status": "running",
        "rival": "Compact only rows whose first cell is zero; leave anchored rows unchanged.",
        "rival_program": RIVAL,
        "rival_program_sha256": hashlib.sha256(RIVAL.encode()).hexdigest(),
        "search": {"maximum_candidate_episodes": 512, "difficulty": "easy",
                   "seed_start": 810000, "sample_indices": [0, 1, 2, 3],
                   "generated_grids": 0, "candidate_episodes": 0},
        "racket_evaluations": 0, "cases": [],
        "limits": "One deliberately searched episode assembled from unmodified public generate calls. This does not replay the shared production lesson assembler, estimate prevalence, prove all lessons ambiguous, or assert owner acceptance. No production changes or full battery.",
        "training_admitted": False,
    }
    bridge = None
    try:
        with _local_imports(RUNTIME, HOME):
            spec = importlib.util.spec_from_file_location("peer_ba9_generator", HOME / "generator.py")
            gen = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gen)
            witness = None
            for seed in range(810000, 810512):
                report["search"]["candidate_episodes"] += 1
                grids = []
                for index in range(4):
                    grid = gen.generate(seed, index, difficulty="easy")
                    report["search"]["generated_grids"] += 1
                    assert gen.self_check(grid, difficulty="easy") == []
                    grids.append(grid)
                    if index < 3 and rival(grid) != packed(grid):
                        break
                if len(grids) == 4 and rival(grids[3]) != packed(grids[3]):
                    witness = (seed, grids)
                    break
            if witness is None:
                report["status"] = "bounded_no_finding"
            else:
                seed, grids = witness
                task = Catalog(ROOT).get(TASK)
                programs = {variant["program_solution"] for variant in task["variants"]}
                assert len(programs) == 1
                program = programs.pop()
                report["canonical_program"] = program
                report["canonical_program_sha256"] = hashlib.sha256(program.encode()).hexdigest()
                report["canonical_rule_hash"] = task["rule_hash"]
                apply, identity, bridge = _real_evaluator(RUNTIME)
                report["racket"] = identity
                for index, grid in enumerate(grids):
                    authority = _grid(apply(program, _grid(grid)))
                    wrong = _grid(apply(RIVAL, _grid(grid)))
                    report["racket_evaluations"] += 2
                    assert authority == packed(grid)
                    assert wrong == rival(grid)
                    assert (authority == wrong) == (index < 3)
                    report["cases"].append({
                        "role": "demo" if index < 3 else "query",
                        "seed": seed, "sample_index": index, "difficulty": "easy",
                        "input": grid, "authority_output": authority,
                        "rival_output": wrong, "rival_matches_authority": authority == wrong,
                        "self_check": [], "declared_sort_rival_refuted": gen.SEMANTIC_RIVALS["sort_then_pack"](grid) != authority,
                        "differences": [{"row": r, "column": c, "authority": value, "rival": wrong[r][c]}
                                        for r, row in enumerate(authority) for c, value in enumerate(row)
                                        if value != wrong[r][c]],
                    })
                assert sha(HOME / "generator.py") == bound["generator.py"]
                report["status"] = "verified_visible_demo_ambiguity"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        if bridge is not None:
            bridge.close()
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "search": report["search"],
                      "racket_evaluations": report["racket_evaluations"], "error": report.get("error"),
                      "output": str(OUT)}))
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())

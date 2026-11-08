#!/usr/bin/env python3
"""Findings-only audits for the packet's immutable, separately drawn targets."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
TARGETS = {
    "40dea3d45f2a": "66a5167f7c5d62e2494f579ab3c261f0aa06e24b0ed246390b47c1c7ed8f9c68",
    "e4cb0224ca42": "5073b90d0c44b4ab4f4517bbfb528fdf5ad64a551a572d03484be4669d80f6b8",
}


def load(tid):
    path = REPO / "generators" / tid / "generator.py"
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != TARGETS[tid]:
        raise ValueError(f"audit source drift for {tid}: {actual}")
    spec = importlib.util.spec_from_file_location("audit_"+tid, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def count_rule(grid):
    starts = ((0, 0), (0, 5), (5, 0), (5, 5))
    counts = [sum(grid[r0+r][c0+c] != 0 for r in range(4) for c in range(4)) for r0, c0 in starts]
    return [[8 if a == b else 0 for b in counts] for a in counts]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(REPO / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    rules = {x["task_id"]: x["program_solution"] for x in map(json.loads, (REPO / "shared/data/canonical/puzzles.jsonl").open()) if x["task_id"] in TARGETS}
    result = {"schema": "findings-only-audit-v1", "source_hashes": TARGETS,
              "audit_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "modified_audit_sources": False, "targets": {}}
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-audit-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(REPO), stage, task_ids=list(TARGETS))
        result["runtime_layout"] = str(stage)
        sys.path.insert(0, str(stage))
        from puzzle_generators import runner
        from puzzle_generators.base import set_ctx_observer
        tid = "40dea3d45f2a"
        module = load(tid)
        bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(rules[tid]))
        try:
            stats = Counter()
            mismatches = []
            unique = set()
            for seed in range(128):
                grid = module.generate(seed, 0, difficulty="medium")
                output = runner._apply_rule(bridge, name, grid)
                stats["grids"] += 1
                stats["count_only_exact_matches"] += output == count_rule(grid)
                unique.add(json.dumps(grid))
                if output != count_rule(grid):
                    mismatches.append({"seed": seed, "input": grid, "racket": output, "count_only": count_rule(grid)})
            counterexample = [[0]*9 for _ in range(9)]
            shapes = [[(0,0), (1,0), (2,0)], [(0,0), (1,0), (1,1)],
                      [(0,0), (0,1), (0,2)], [(0,0), (0,1), (1,0)]]
            for color, ((r0, c0), shape) in enumerate(zip(((0,0),(0,5),(5,0),(5,5)),shapes), 1):
                for r, c in shape:
                    counterexample[r0+r][c0+c] = color
            truth = runner._apply_rule(bridge, name, counterexample)
            result["targets"][tid] = {
                "classification": "reproduced_count_shortcut_and_false_domain_rejection",
                "sampling": {"seed_first":0,"seed_last":127,"sample_index":0,"difficulty":"medium"},
                "counts":dict(stats), "unique_inputs":len(unique), "mismatches":mismatches,
                "counterexample": {"input":counterexample, "racket_output":truth,
                                   "count_only_output":count_rule(counterexample),
                                   "self_check":module.self_check(counterexample)},
                "rule_sha256": hashlib.sha256(rules[tid].encode()).hexdigest(),
            }
            assert truth != count_rule(counterexample)
        finally:
            bridge.shutdown()
        tid = "e4cb0224ca42"
        module = load(tid)
        per_band, witnesses, unique = {}, [], set()
        for band in ("easy", "medium", "hard"):
            stats = Counter()
            for seed in range(256):
                contexts = []
                set_ctx_observer(contexts.append)
                try:
                    grid = module.generate(seed, 0, difficulty=band)
                finally:
                    set_ctx_observer(None)
                requested = contexts[-1].axis_value("n_rects")
                realized = len({v for row in grid for v in row if v})
                errors = module.self_check(grid, difficulty=band)
                stats["grids"] += 1
                stats[f"requested_{requested}"] += 1
                stats[f"realized_{realized}"] += 1
                stats["underfilled"] += realized < requested
                stats["validator_accepts_underfill"] += realized < requested and not errors
                unique.add(json.dumps(grid))
                if realized < requested and len([w for w in witnesses if w["difficulty"] == band]) < 8:
                    witnesses.append({"seed":seed,"sample_index":0,"difficulty":band,
                                      "requested":requested,"realized":realized,"self_check":errors,"input":grid})
            per_band[band] = dict(stats)
        bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(rules[tid]))
        try:
            for item in witnesses:
                item["racket_output"] = runner._apply_rule(bridge, name, item["input"])
        finally:
            bridge.shutdown()
        result["targets"][tid] = {
            "classification":"reproduced_silent_underfill",
            "sampling":{"seed_first":0,"seed_last":255,"sample_index":0,"bands":["easy","medium","hard"]},
            "per_band":per_band,"unique_inputs":len(unique),"witnesses":witnesses,
            "rule_sha256":hashlib.sha256(rules[tid].encode()).hexdigest(),
        }
    args.out.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({tid:{k:v for k,v in item.items() if k in ("classification","counts","per_band","unique_inputs")} for tid,item in result["targets"].items()},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

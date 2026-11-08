"""Bounded sampler reliability/coverage probe; its labels remain Python claims."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def key(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=24)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 64 or args.out.exists():
        raise ValueError("use 1..64 seeds and a fresh output path")
    root = Path.cwd().resolve()
    home = root / "generators/5f9a2df57599/workspace/parametric"
    family = load("wall_sampler_family", home / "native_family.py")
    audit = load("wall_sampler_audit", home / "audit_native.py")
    gate = load("wall_sampler_gate", home / "check_wall_teaching.py")
    sources = [home / name for name in ["native_family.py", "adapter.py", "promotion.json", "prototype.py", "audit_native.py", "check_wall_teaching.py"]]
    before = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    inputs, pairs, queries, shapes, geometries = set(), set(), set(), set(), set()
    large, records, failures = [], [], []
    requests = 0
    began = time.monotonic()
    for seed in range(args.seeds):
        baseline = None
        for policy in ["canvas_edges", "gray_walls"]:
            settings = {"side_boundary_policy": policy}
            for demos, count in [(6, 4), (2, 1), (3, 4)]:
                requests += 1
                try:
                    episode = family.generate(seed, settings, demos, count)
                    assert len(episode["train"]) == demos and len(episode["test"]) == count
                    assert episode["program_solution"] == family.program(settings)
                    all_pairs = episode["train"] + episode["test"]
                    assert len({key(pair["input"]) for pair in all_pairs}) == len(all_pairs)
                    assert gate.check_episode({"train": episode["train"][:2]})["status"] == "passed"
                    if demos == 6:
                        full = episode
                        these_inputs = [pair["input"] for pair in all_pairs]
                        if baseline is None:
                            baseline = these_inputs
                        else:
                            assert these_inputs == baseline, "settings alter inputs"
                        for split in ["train", "test"]:
                            for index, pair in enumerate(episode[split]):
                                grid = pair["input"]
                                assert pair["output"] == audit.reference(grid, policy)
                                inputs.add(key(grid)); pairs.add(key(pair))
                                if split == "test":
                                    queries.add(key(grid))
                                h, w = len(grid), len(grid[0])
                                shapes.add((h, w))
                                facts = audit.facts(grid, policy)
                                for region in facts:
                                    r0, c0, _, _ = region["bbox"]
                                    geometries.add(tuple(sorted((r-r0, c-c0) for r, c in region["cells"])))
                                if split == "test" and (h, w) == (30, 30):
                                    large.append({"seed": seed, "policy": policy, "query_index": index,
                                        "zero_cells": sum(v == 0 for row in grid for v in row),
                                        "painted_cells": sum(v == 4 for row in pair["output"] for v in row),
                                        "components": len(facts), "eligible_components": sum(r["eligible"] for r in facts),
                                        "zero_boundary_cells": sum(grid[r][c] == 0 for r in range(h) for c in range(w) if r in (0,h-1) or c in (0,w-1))})
                        meta = episode.get("meta", {})
                        fixtures = {}
                        for split, profiles in meta.get("fixtures", {}).items():
                            fixtures[split] = []
                            for profile in profiles:
                                facts = profile["facts"]
                                fixtures[split].append({
                                    **{name: profile[name] for name in ["index", "profile", "attempts", "backbone", "input_sha256"]},
                                    "shape": facts["shape"], "gray_cells": facts["gray_cells"],
                                    "component_count": facts["component_count"],
                                    "eligible_counts": facts["eligible_counts"], "painted_cells": facts["painted_cells"],
                                    "top_row_sha256": key(facts["top_row"]),
                                })
                        records.append({"seed": seed, "policy": policy,
                            "sampler": meta.get("sampler", {}), "fixtures": fixtures})
                    else:
                        assert episode["train"] == full["train"][:demos], "demo prefix drift"
                        assert episode["test"] == full["test"][:count], "query prefix drift"
                except Exception as exc:
                    failures.append({"seed": seed, "policy": policy, "demos": demos, "queries": count,
                        "error": f"{type(exc).__name__}: {exc}"})
    assert all(hashlib.sha256((root/path).read_bytes()).hexdigest() == value for path, value in before.items()), "source changed during probe"
    report = {"schema": "wall-native-sampler-probe-v1", "task_id": "5f9a2df57599",
        "status": "passed" if not failures else "failed", "requests": requests,
        "successes": requests-len(failures), "failures": failures, "seeds": list(range(args.seeds)),
        "settings": ["canvas_edges", "gray_walls"], "request_counts": [[6,4],[2,1],[3,4]],
        "distinct_inputs": len(inputs), "distinct_claim_labeled_pairs": len(pairs),
        "distinct_query_inputs": len(queries), "distinct_component_geometries": len(geometries),
        "shapes": [list(shape) for shape in sorted(shapes)], "large_queries": large,
        "source_sha256": before, "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seconds": time.monotonic()-began,
        "scope": "Pure-Python claim-label/reference parity, coverage, deterministic prefix and matched-input probe. No Racket calls or model training; native labels are separate evidence.",
        "generation_records": records}
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in ["status", "requests", "successes", "failures", "distinct_inputs", "distinct_query_inputs", "distinct_component_geometries", "seconds"]}, indent=2))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())

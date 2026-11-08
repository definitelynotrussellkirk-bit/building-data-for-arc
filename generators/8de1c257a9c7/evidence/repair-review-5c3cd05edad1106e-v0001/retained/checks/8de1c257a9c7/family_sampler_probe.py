"""Bounded current-source sampler/count-prefix census; labels are Python claims."""
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path.cwd().resolve()
TASK = "8de1c257a9c7"
HOME = ROOT / "generators" / TASK / "workspace/parametric"
CHECKS = ROOT.parent / "checks" / TASK


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def bbox(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    return [min(r for r, c in points), min(c for r, c in points),
            max(r for r, c in points), max(c for r, c in points)] if points else None


def main():
    family = load("sampler_family", HOME / "prototype.py")
    gate = load("sampler_geometry_gate", HOME / "check_geometry_gate.py")
    sources = {name: hashlib.sha256((HOME / name).read_bytes()).hexdigest()
               for name in ("prototype.py", "adapter.py", "canonical.rkt", "check_geometry_gate.py")}
    sources["sampler_probe.py"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    all_inputs, all_pairs, query_inputs, geometries = set(), set(), set(), set()
    by_count = defaultdict(set)
    shapes, red_counts, cyan_counts = set(), set(), set()
    rows, failures = [], []
    request_count = passed = 0
    max_shape_attempts = max_layout_attempts = 0
    start = time.perf_counter()
    for seed in range(24):
        matched_bank = None
        for setting in ("identity", "mirror_horizontal"):
            settings = {"stamp_transform": setting}
            try:
                base = None
                for demos, queries in ((6, 4), (2, 1), (3, 4)):
                    request_count += 1
                    episode = family.generate(seed, settings, demos=demos, queries=queries)
                    assert len(episode["train"]) == demos and len(episode["test"]) == queries
                    assert episode["program_solution"] == family.program(settings)
                    pairs = episode["train"] + episode["test"]
                    assert len({digest(p["input"]) for p in pairs}) == len(pairs)
                    assert gate.check_episode({"train": episode["train"][:2]})["status"] == "passed"
                    if base is None:
                        base = episode
                    else:
                        assert episode["train"] == base["train"][:demos]
                        assert episode["test"] == base["test"][:queries]
                    passed += 1
                bank = [p["input"] for p in base["train"] + base["test"]]
                if matched_bank is None:
                    matched_bank = bank
                else:
                    assert bank == matched_bank
                for index, pair in enumerate(base["train"] + base["test"]):
                    grid = pair["input"]
                    assert family.self_check(grid) == []
                    assert family.reference(grid, settings) == pair["output"]
                    fact = family.facts(grid)
                    key = digest(grid)
                    all_inputs.add(key)
                    all_pairs.add(digest(pair))
                    if index >= 6:
                        query_inputs.add(key)
                    geometry = digest(fact["shape_offsets"])
                    geometries.add(geometry)
                    by_count[fact["cyan_count"]].add(geometry)
                    shapes.add((fact["h"], fact["w"]))
                    red_counts.add(len(fact["reds"]))
                    cyan_counts.add(fact["cyan_count"])
                dense = base["test"][3]
                assert (len(dense["input"]), len(dense["input"][0])) == (30, 30)
                profiles = base.get("meta", {}).get("generation", {}).get("profiles", [])
                max_shape_attempts = max([max_shape_attempts] + [p.get("shape_attempts", 0) for p in profiles])
                max_layout_attempts = max([max_layout_attempts] + [p.get("layout_attempts", 0) for p in profiles])
                rows.append({"seed": seed, "settings": settings,
                             "query_shapes": [[len(p["input"]), len(p["input"][0])] for p in base["test"]],
                             "dense_input_foreground": sum(v != 0 for row in dense["input"] for v in row),
                             "dense_output_foreground": sum(v != 0 for row in dense["output"] for v in row),
                             "dense_input_bbox": bbox(dense["input"]), "dense_output_bbox": bbox(dense["output"]),
                             "dense_input_sha256": digest(dense["input"]),
                             "generation": base.get("meta", {}).get("generation", {})})
            except Exception as error:
                failures.append({"seed": seed, "settings": settings,
                                 "error": type(error).__name__ + ": " + str(error)})
    for name, expected in sources.items():
        path = Path(__file__) if name == "sampler_probe.py" else HOME / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    report = {
        "schema": "stamp-native-sampler-census-v1", "status": "passed" if not failures and passed == 144 else "failed",
        "scope": "24 fixed seeds, two settings, three independent count requests each. All labels here are Python claims; protected execution is recorded separately.",
        "request_count": request_count, "passed": passed, "failures": failures,
        "elapsed_seconds": time.perf_counter() - start, "source_sha256": sources,
        "unique_inputs": len(all_inputs), "unique_claim_labeled_pairs": len(all_pairs),
        "unique_query_inputs": len(query_inputs), "distinct_source_geometries": len(geometries),
        "distinct_geometries_by_cyan_count": {str(k): len(v) for k, v in sorted(by_count.items())},
        "shapes": [list(s) for s in sorted(shapes)], "red_counts": sorted(red_counts), "cyan_counts": sorted(cyan_counts),
        "max_observed_shape_attempts": max_shape_attempts, "max_observed_layout_attempts": max_layout_attempts,
        "episodes": rows, "native_reference_evaluations": 0,
    }
    path = CHECKS / "family-sampler-final.json"
    with path.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({k: report[k] for k in ("status", "request_count", "passed", "unique_inputs",
                     "unique_query_inputs", "distinct_source_geometries", "failures", "elapsed_seconds")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

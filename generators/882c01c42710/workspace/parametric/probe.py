"""Bounded structural self-audit for the 882c01c42710 family."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("probe_882_impl", HERE / "prototype.py")
impl = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(impl)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for seed in (0, 17):
        for mode in impl.MODES:
            for demos in range(2, 7):
                episode = impl.generate(seed, {"mode": mode}, demos, 4)
                inputs = [p["input"] for p in episode["train"] + episode["test"]]
                other = next(x for x in impl.MODES if x != mode)
                rows.append({
                    "seed": seed,
                    "mode": mode,
                    "demos": demos,
                    "queries": 4,
                    "unique_inputs": len({json.dumps(g, separators=(",", ":")) for g in inputs}),
                    "distinguishing_demos": sum(
                        p["output"] != impl.python_oracle(p["input"], {"mode": other})
                        for p in episode["train"]),
                    "query_sizes": [[len(p["input"]), len(p["input"][0])] for p in episode["test"]],
                    "last_output_nonzero": sum(v != 0 for row in episode["test"][-1]["output"] for v in row),
                })
    if any(r["unique_inputs"] != r["demos"] + 4 or not r["distinguishing_demos"]
           or r["query_sizes"][-1] != [30, 30] or r["last_output_nonzero"] < 59 for r in rows):
        raise SystemExit("probe invariant failed")
    sources = {}
    for path in sorted(HERE.rglob("*")):
        if path.is_file() and "evidence" not in path.parts and "__pycache__" not in path.parts:
            sources[str(path.relative_to(HERE))] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {"schema": "arcpuzzles-882c01c42710-parametric-probe-v1",
              "status": "passed", "rows": rows, "sources": sources,
              "limits": "Finite seeds 0/17, both settings, demo counts 2..6, four fixed query profiles."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": "passed", "cases": len(rows), "out": str(args.out)}))


if __name__ == "__main__":
    main()

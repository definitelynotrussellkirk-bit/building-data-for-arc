"""Bounded deterministic authoring audit for the 151f4dc0c08f family."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_audit_151f", HERE / "prototype.py")
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load prototype")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def run() -> dict:
    episodes = pairs = transitive = diagonal = thirty = 0
    for seed in range(16):
        for setting in P.SETTINGS:
            for demos in range(2, 7):
                episode = P.generate(seed, {P.PARAMETER: setting}, demos=demos, queries=4)
                episodes += 1
                for pair in episode["train"] + episode["test"]:
                    pairs += 1
                    info = P.analyze(pair["input"])
                    transitive += int(info["anchor_component"] != info["anchor_direct_neighborhood"])
                    positions = info["positions"]
                    diagonal += int(any(
                        a[0] != b[0] and a[1] != b[1]
                        and abs(a[0] - b[0]) == abs(a[1] - b[1])
                        for i, a in enumerate(positions) for b in positions[i + 1:]
                    ))
                    thirty += int(len(pair["input"]) == 30 and len(pair["input"][0]) == 30)
                rival = next(v for v in P.SETTINGS if v != setting)
                if not any(P.apply_python(x["input"], rival) != x["output"] for x in episode["train"]):
                    raise AssertionError("declared rival survived")
                if setting == "anchor_component" and not any(
                    P.apply_wrong_direct_neighbors(x["input"]) != x["output"] for x in episode["train"]
                ):
                    raise AssertionError("direct-neighbor shortcut survived")
    return {
        "schema": "151f4dc0c08f-parametric-audit-v1",
        "status": "passed",
        "seeds": 16,
        "demo_counts": [2, 3, 4, 5, 6],
        "queries": 4,
        "episodes": episodes,
        "pairs": pairs,
        "transitive_cases": transitive,
        "diagonal_cases": diagonal,
        "thirty_by_thirty_cases": thirty,
        "source_sha256": hashlib.sha256((HERE / "prototype.py").read_bytes()).hexdigest(),
        "limits": "Finite authored bank and declared rivals; not universal uniqueness or learning evidence."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))

if __name__ == "__main__":
    main()

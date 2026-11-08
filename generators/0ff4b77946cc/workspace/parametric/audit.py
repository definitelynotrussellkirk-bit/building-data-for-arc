"""Bounded deterministic authoring audit for the 0ff4b77946cc family."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


P = _load("_audit_0ff_parametric", HERE / "prototype.py")
G = _load("_audit_0ff_generator", HERE.parents[1] / "generator.py")


def run() -> dict:
    episodes = pairs = wide = tall = thirty = 0
    for seed in range(16):
        for setting in P.SETTINGS:
            for demos in range(2, 7):
                episode = P.generate(seed, {P.PARAMETER: setting}, demos=demos, queries=4)
                episodes += 1
                orientations = {
                    P.analyze(pair["input"])["largest_orientation"]
                    for pair in episode["train"][:2]
                }
                if orientations != {"wide_or_square", "tall"}:
                    raise AssertionError("minimum lesson lost an orientation branch")
                for pair in episode["train"] + episode["test"]:
                    pairs += 1
                    if G.self_check(pair["input"]):
                        raise AssertionError("authored input failed native self_check")
                    info = P.analyze(pair["input"])
                    wide += int(info["largest_orientation"] == "wide_or_square")
                    tall += int(info["largest_orientation"] == "tall")
                    thirty += int(len(pair["input"]) == 30 and len(pair["input"][0]) == 30)
                    if pair["output"] != P.apply_python(pair["input"], setting):
                        raise AssertionError("stored label differs from Python reference")
                rival = next(value for value in P.SETTINGS if value != setting)
                if not any(P.apply_python(x["input"], rival) != x["output"] for x in episode["train"]):
                    raise AssertionError("declared rival survived")
                if setting == "largest_orientation" and not any(
                    P.analyze(x["input"])["largest_orientation"] == "tall"
                    and P.apply_python(x["input"], "size_desc") != x["output"]
                    for x in episode["train"]
                ):
                    raise AssertionError("always-descending shortcut survived")
    return {
        "schema": "0ff4b77946cc-parametric-audit-v1",
        "status": "passed",
        "seeds": 16,
        "demo_counts": [2, 3, 4, 5, 6],
        "queries": 4,
        "episodes": episodes,
        "pairs": pairs,
        "wide_or_square_cases": wide,
        "tall_cases": tall,
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

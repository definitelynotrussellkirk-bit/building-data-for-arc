"""Bounded protected-Racket label and finite-rival teaching audit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def assess_predictions(expected_train, expected_test, rival_train, rival_test):
    if (not expected_train or not expected_test
            or len(expected_train) != len(rival_train)
            or len(expected_test) != len(rival_test)):
        raise ValueError("each rival must predict every demonstration and query")
    demo_matches = [left == right for left, right in zip(expected_train, rival_train)]
    query_disagreements = [index for index, (left, right)
                           in enumerate(zip(expected_test, rival_test)) if left != right]
    survives = all(demo_matches)
    return {
        "demo_matches": demo_matches,
        "survives_demonstrations": survives,
        "query_disagreements": query_disagreements,
        "harmful_survivor": survives and bool(query_disagreements),
    }


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(output: Path, *, seeds=(0, 17), demo_counts=(2, 3, 6)):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    home = Path(__file__).resolve().parent
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    prototype = _load(home / "prototype.py", "_row_corridor_audit_prototype")
    source_names = ("adapter.py", "prototype.py", "canonical.rkt", "promotion.json", "audit.py")
    source_hashes = {name: hashlib.sha256((home / name).read_bytes()).hexdigest()
                     for name in source_names}

    cache, wrapped, checks, witnesses = {}, {}, [], {}
    bridge = RacketBridge(timeout=20)
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        bridge.close()
        raise ValueError("audit requires the protected Racket backend")

    def execute(program, grid):
        key = (hashlib.sha256(program.encode()).hexdigest(),
               json.dumps(grid, separators=(",", ":")))
        if key not in cache:
            if program not in wrapped:
                wrapped[program] = wrap_rule(program)
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            value = bridge.eval_text(f"({wrapped[program]} {literal})")
            if (type(value) is not list or len(value) != len(grid)
                    or any(type(row) is not list or len(row) != len(grid[0])
                           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                           for row in value)):
                raise ValueError("Racket program returned an invalid ARC grid")
            cache[key] = value
        return cache[key]

    try:
        for seed in seeds:
            for demos in demo_counts:
                for settings in prototype.SETTINGS:
                    episode = prototype.generate(seed, settings, demos, 4)
                    intended = prototype.program(settings)
                    labels = {
                        split: [execute(intended, pair["input"]) for pair in episode[split]]
                        for split in ("train", "test")
                    }
                    for split in labels:
                        if labels[split] != [pair["output"] for pair in episode[split]]:
                            raise ValueError("Python label claim differs from protected Racket")

                    rivals = {}
                    for name, rival_program in prototype.rival_programs(settings).items():
                        predictions = {
                            split: [execute(rival_program, pair["input"])
                                    for pair in episode[split]]
                            for split in ("train", "test")
                        }
                        verdict = assess_predictions(
                            labels["train"], labels["test"],
                            predictions["train"], predictions["test"],
                        )
                        rivals[name] = verdict
                        witness_key = json.dumps(settings, sort_keys=True) + "/" + name
                        if witness_key not in witnesses and not verdict["survives_demonstrations"]:
                            index = verdict["demo_matches"].index(False)
                            witnesses[witness_key] = {
                                "seed": seed,
                                "demos": demos,
                                "demo_index": index,
                                "settings": settings,
                                "input": episode["train"][index]["input"],
                                "program": intended,
                                "output": labels["train"][index],
                                "rival_program": rival_program,
                                "rival_output": predictions["train"][index],
                            }
                    checks.append({
                        "seed": seed,
                        "settings": settings,
                        "demos": demos,
                        "queries": 4,
                        "rivals": rivals,
                        "input_metrics": {
                            split: [prototype.analyze(pair["input"]) for pair in episode[split]]
                            for split in ("train", "test")
                        },
                    })
    finally:
        bridge.close()

    current_hashes = {name: hashlib.sha256((home / name).read_bytes()).hexdigest()
                      for name in source_names}
    if source_hashes != current_hashes:
        raise ValueError("audited source changed during execution")
    harmful = [
        {"seed": row["seed"], "settings": row["settings"], "demos": row["demos"],
         "rival": name, "query_disagreements": verdict["query_disagreements"]}
        for row in checks
        for name, verdict in row["rivals"].items()
        if verdict["harmful_survivor"]
    ]
    report = {
        "schema": "628b4a2c24c1-finite-teaching-audit-v1",
        "status": "passed" if not harmful else "failed",
        "source_sha256": source_hashes,
        "racket": {key: value for key, value in identity.items()
                   if key.endswith("sha256") or key in ("schema", "backend", "protected")},
        "episodes": len(checks),
        "racket_evaluations": len(cache),
        "harmful_survivors": harmful,
        "checks": checks,
        "scope": "Two seeds, demo counts 2/3/6 and eight named rivals; no universal uniqueness or training admission.",
        "training_admitted": False,
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "witnesses.json").write_text(
        json.dumps({"source_sha256": source_hashes, "cases": witnesses},
                   separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", action="append", type=int)
    parser.add_argument("--demos", action="append", type=int)
    args = parser.parse_args()
    report = run(args.out, seeds=tuple(args.seed or (0, 17)),
                 demo_counts=tuple(args.demos or (2, 3, 6)))
    print(json.dumps({key: report[key] for key in
                      ("status", "episodes", "racket_evaluations", "harmful_survivors")},
                     indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

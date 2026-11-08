#!/usr/bin/env python3
"""Find an actual four-consecutive-draw lesson ambiguous under declared rivals.

All searched inputs are labeled by the selected canonical Racket program.
The bounded search stops at its first witness; no failed window is fabricated.
Only the winning four grids and predictions are retained in the JSON receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
TASK = "cf5ccd73cfe5"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs, canonical_path, normalize_grid


def sha(body):
    return hashlib.sha256(body).hexdigest()


def load_source(path):
    path = Path(path).resolve()
    body = path.read_bytes()
    spec = importlib.util.spec_from_file_location("lesson_probe_" + sha(body), path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module, {"path": str(path), "sha256": sha(body)}


def selected_rule():
    sources = set()
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK and row.get("program_solution"):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError("expected one exact selected canonical program")
    return sources.pop()


def execute(bridge, callable_text, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({callable_text} {literal})"))


def ambiguous_rivals(pairs, rivals, query_position):
    """Return names fitting every demo but disagreeing on the held-out query."""
    predictions = {name: [rival(pair["input"]) for pair in pairs]
                   for name, rival in rivals.items()}
    return {
        name: outputs[query_position]
        for name, outputs in predictions.items()
        if all(outputs[i] == pair["output"] for i, pair in enumerate(pairs)
               if i != query_position)
        and outputs[query_position] != pairs[query_position]["output"]
    }


def search(gen, rivals, bridge, callable_text, *, seed_start, seeds, starts, bands):
    counts = {"generated_inputs": 0, "reference_executions": 0,
              "consecutive_windows": 0, "query_rotations_scored": 0}
    for band in bands:
        for seed in range(seed_start, seed_start + seeds):
            pairs = []
            for index in range(starts + 3):
                grid = gen.generate(seed, index, difficulty=band)
                counts["generated_inputs"] += 1
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    raise ValueError(f"self_check rejected {seed}/{index}/{band}: {errors}")
                output = execute(bridge, callable_text, grid)
                counts["reference_executions"] += 1
                pairs.append({"sample_index": index, "input": grid, "output": output})
                if len(pairs) < 4:
                    continue
                window = pairs[-4:]
                counts["consecutive_windows"] += 1
                # Ordinary three-demo/last-query order first, then other holdouts.
                for qi in (3, 0, 1, 2):
                    counts["query_rotations_scored"] += 1
                    survivors = ambiguous_rivals(window, rivals, qi)
                    if not survivors:
                        continue
                    demo_indices = [p["sample_index"] for i, p in enumerate(window) if i != qi]
                    public = {"train": [{"input": p["input"], "output": p["output"]}
                                        for i, p in enumerate(window) if i != qi],
                              "test": [{"input": window[qi]["input"]}]}
                    return {
                        "seed": seed, "difficulty": band,
                        "start_sample_index": window[0]["sample_index"],
                        "consecutive_sample_indices": [p["sample_index"] for p in window],
                        "query_position": qi, "query_sample_index": window[qi]["sample_index"],
                        "demo_sample_indices": demo_indices,
                        "ordering": "production_last_query" if qi == 3 else "held_out_rotation",
                        "public_challenge": public,
                        "private_query_output": window[qi]["output"],
                        "surviving_rival_predictions": survivors,
                        "label_authority": "selected canonical Racket execution",
                    }, counts
    return None, counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator-source", type=Path, required=True)
    parser.add_argument("--expected-generator-sha256")
    parser.add_argument("--rival-source", type=Path, default=ROOT / "generators" / TASK / "generator.py")
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--starts", type=int, default=8)
    parser.add_argument("--bands", nargs="+", choices=("easy", "medium", "hard"),
                        default=("easy", "medium", "hard"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seeds < 1 or args.starts < 1:
        parser.error("--seeds and --starts must be positive")
    if args.out.exists():
        parser.error("--out must be new")
    gen, generator_binding = load_source(args.generator_source)
    if args.expected_generator_sha256 and generator_binding["sha256"] != args.expected_generator_sha256:
        parser.error("generator source hash does not match --expected-generator-sha256")
    rival_module, rival_binding = load_source(args.rival_source)
    rivals = rival_module.CANONICAL_SHORTCUTS
    if not isinstance(rivals, dict) or not rivals or not all(callable(r) for r in rivals.values()):
        raise ValueError("rival source must declare nonempty callable CANONICAL_SHORTCUTS")
    rule = selected_rule()
    receipt = {
        "schema": "cf5ccd73cfe5-consecutive-lesson-probe-v1", "task_id": TASK,
        "status": "ERROR", "generator_source": generator_binding, "rival_source": rival_binding,
        "probe_sha256": sha(Path(__file__).read_bytes()),
        "rule_source_sha256": sha(rule.encode()),
        "rule_hash": sha(" ".join(rule.split()).encode())[:12],
        "command": shlex.join([sys.executable, *sys.argv]),
        "cwd": str(Path.cwd()), "rivals": sorted(rivals),
        "search": {"seed_start": args.seed_start, "seed_count": args.seeds,
                   "consecutive_window_starts": list(range(args.starts)), "bands": list(args.bands),
                   "query_position_order": [3, 0, 1, 2], "stop_at_first_witness": True,
                   "overrides": {}, "sampler": "direct consecutive generate(seed,index,difficulty) calls"},
        "limits": ["Finite bounded search against the declared canonical-fitting rivals only.",
                   "No-witness status does not establish universal identifiability.",
                   "Receipt contains private query labels; expose only public_challenge to a solver."],
    }
    try:
        canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
        for pair in canonical:
            for name, rival in rivals.items():
                if rival(pair["input"]) != pair["output"]:
                    raise ValueError(f"{name} does not fit all labeled canonical pairs")
        receipt["canonical_rival_validation"] = {"pairs": len(canonical), "all_fit": True}
        if "scripts" not in sys.modules:
            scripts = types.ModuleType("scripts")
            scripts.__path__ = [str(ROOT / "shared/tools")]
            sys.modules["scripts"] = scripts
        from puzzle_generators.rule_wrap import wrap_rule
        from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
        callable_text = wrap_rule(rule)
        receipt["rule_callable_sha256"] = sha(callable_text.encode())
        receipt["runtime"] = racket_runtime_status()
        with RacketBridge() as bridge:
            witness, counts = search(
                gen, rivals, bridge, callable_text, seed_start=args.seed_start,
                seeds=args.seeds, starts=args.starts, bands=args.bands,
            )
        receipt.update(status="AMBIGUOUS" if witness else "NO_WITNESS_WITHIN_BOUNDS",
                       witness=witness, counts=counts)
    except Exception as exc:
        receipt["error"] = {"type": type(exc).__name__, "message": str(exc)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"], "out": str(args.out),
                      "counts": receipt.get("counts"), "error": receipt.get("error")}, sort_keys=True))
    return 2 if receipt["status"] == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())

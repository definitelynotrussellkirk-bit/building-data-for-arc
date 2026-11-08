#!/usr/bin/env python3
"""Fast Python-only curriculum sweep for future edits to this family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SETTINGS = (
    {"second_source": "header"},
    {"second_source": "post_first_marker"},
)


def load_adapter():
    path = HERE / "adapter.py"
    body = path.read_bytes()
    name = "_dcc5_sweep_" + hashlib.sha256(str(path).encode() + body).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sweep(seed_count: int):
    if type(seed_count) is not int or not 1 <= seed_count <= 4096:
        raise ValueError("seed_count must be an exact integer in 1..4096")
    adapter = load_adapter()
    failures = []
    episodes = 0
    command_pairs = set()
    marker_transitions = set()
    shapes = set()
    public_inputs = set()
    for seed in range(seed_count):
        for demos in range(2, 7):
            matched = None
            for settings in SETTINGS:
                episode = adapter.generate(seed, settings, demos, 4)
                episodes += 1
                inputs = [packed(pair["input"]) for pair in episode["train"] + episode["test"]]
                if len(inputs) != len(set(inputs)):
                    failures.append({"kind": "duplicate_input", "seed": seed,
                                     "demos": demos, "settings": settings})
                if matched is None:
                    matched = inputs
                elif matched != inputs:
                    failures.append({"kind": "setting_input_mismatch", "seed": seed,
                                     "demos": demos, "settings": settings})
                report = adapter.lesson_report(episode, settings)
                if report["demonstration_survivors"] or report["surviving_query_disagreements"]:
                    failures.append({"kind": "teaching_failure", "seed": seed,
                                     "demos": demos, "settings": settings, "report": report})
                one = adapter.generate(seed, settings, demos, 1)
                if one["train"] != episode["train"] or one["test"][0] != episode["test"][0]:
                    failures.append({"kind": "prefix_failure", "seed": seed,
                                     "demos": demos, "settings": settings})
                large = episode["test"][3]["input"]
                if (len(large), len(large[0])) != (30, 30):
                    failures.append({"kind": "missing_large_query", "seed": seed,
                                     "demos": demos, "settings": settings})
                for pair in episode["train"] + episode["test"]:
                    scene = adapter.analyze(pair["input"])
                    first = adapter._MODULE._transform(scene["motif"], scene["cmd1"])
                    command_pairs.add((scene["cmd1"], scene["cmd2"]))
                    marker_transitions.add((adapter._MODULE._corner_name(scene["motif"]),
                                            adapter._MODULE._corner_name(first)))
                    shapes.add((len(pair["input"]), len(pair["input"][0]),
                                len(scene["motif"]), len(scene["motif"][0])))
                    public_inputs.add(packed(pair["input"]))
    return {
        "schema": "dcc5f8961845-python-sweep-v1",
        "status": "passed" if not failures else "failed",
        "seed_count": seed_count,
        "episode_count": episodes,
        "failed_findings": len(failures),
        "failures": failures,
        "coverage": {
            "command_pairs": [list(pair) for pair in sorted(command_pairs)],
            "command_pair_count": len(command_pairs),
            "marker_transitions": [list(pair) for pair in sorted(marker_transitions)],
            "shape_profiles": [list(shape) for shape in sorted(shapes)],
            "distinct_input_count": len(public_inputs),
        },
        "finite_claim": "Python mirrors and the named rival set only; Racket is checked separately.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = sweep(args.seeds)
    body = json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body, encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "status", "seed_count", "episode_count", "failed_findings"
    )}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Bounded, source-bound authoring evidence for the separate prototype."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import time

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root

import prototype as p


def sha256_bytes(body):
    return hashlib.sha256(body).hexdigest()


def digest(value):
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def artifact_manifest(directory):
    """Hash the declared payloads only; the enclosing report cannot hash itself."""
    names = ("canonical-equality.private.json", "challenges.public.jsonl", "episodes.private.jsonl",
             "programs.private.json", "witness.private.json")
    result = []
    for name in names:
        body = (Path(directory) / name).read_bytes()
        result.append({"path": name, "sha256": sha256_bytes(body), "bytes": len(body)})
    return result


def verify_geometry(grid, output, setting):
    """Independent bbox check of executed labels, never a label source."""
    period, phase = setting
    expected = [row[:] for row in grid]
    for rectangle in p.validate_scene(grid):
        top, left = rectangle["top"], rectangle["left"]
        for r in range(top + 1, top + rectangle["height"] - 1):
            for c in range(left + 1, left + rectangle["width"] - 1):
                if ((r - top - 1) + (c - left - 1)) % period == phase:
                    expected[r][c] = 0
    if output != expected:
        raise AssertionError("Racket label disagrees with local-coordinate geometry")


def lawful_witness():
    grid = [[0] * 14 for _ in range(12)]
    for r in range(1, 6):
        for c in range(2, 7):
            grid[r][c] = 8
    return grid


def run_probe(output, seed_count):
    if type(seed_count) is not int or not 1 <= seed_count <= 50:
        raise ValueError("seed_count must be 1..50")
    root = find_root(__file__)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    source_files = {"prototype.py": Path(p.__file__), "probe.py": Path(__file__)}
    sources = {name: {"path": str(path.resolve().relative_to(root)),
                      "sha256": sha256_bytes(path.read_bytes())}
               for name, path in source_files.items()}
    program_rows = [{"parameters": dict(zip(("period", "phase"), setting)),
                     "program": p.racket_program(*setting),
                     "program_sha256": sha256_bytes(p.racket_program(*setting).encode())}
                    for setting in p.SETTINGS]
    canonical = p.canonical_program(root)
    programs = {"settings": program_rows, "canonical_setting": list(p.CANONICAL),
                "canonical_source": canonical,
                "canonical_source_sha256": sha256_bytes(canonical.encode()),
                "canonical_executed_expression": p.executable_expression(canonical),
                "canonical_executed_expression_sha256": sha256_bytes(p.executable_expression(canonical).encode())}
    write_json(output / "programs.private.json", programs)
    witness = lawful_witness()
    canonical_pairs = canonical_pairs_for_probe(root)
    settings_counts = {f"{period}:{phase}": 0 for period, phase in p.SETTINGS}
    fixed_seeds = (0, 7, 19)
    plans = [(seed, setting) for setting in p.SETTINGS for seed in fixed_seeds]
    plans += [(seed, None) for seed in range(seed_count)]
    probe_rows = []
    public_rows = []
    private_rows = []
    baseline_rng = random.getstate()
    with RacketBridge(timeout=15) as bridge:
        runtime_binary = Path(bridge.racket_binary)
        runtime = {"racket_binary": str(runtime_binary),
                   "racket_binary_sha256": sha256_bytes(runtime_binary.read_bytes()),
                   "bridge_api": "RacketBridge.define_grid/eval_text/context manager"}
        inputs = [pair["input"] for pair in canonical_pairs]
        original_outputs = p.execute_racket(canonical, inputs, bridge=bridge)
        proposed_outputs = p.execute_racket(p.racket_program(*p.CANONICAL), inputs, bridge=bridge)
        if not original_outputs == proposed_outputs == [pair["output"] for pair in canonical_pairs]:
            raise AssertionError("canonical setting equality failed")
        canonical_receipt = {"status": "passed", "labeled_pairs": len(canonical_pairs),
                             "unique_inputs": len({digest(grid) for grid in inputs}),
                             "pairs": [{**pair, "canonical_executed_output": original,
                                        "prototype_executed_output": proposed}
                                       for pair, original, proposed in zip(canonical_pairs, original_outputs, proposed_outputs)]}
        write_json(output / "canonical-equality.private.json", canonical_receipt)
        witness_outputs = []
        for setting in p.SETTINGS:
            result = p.execute_racket(p.racket_program(*setting), [witness], bridge=bridge)[0]
            verify_geometry(witness, result, setting)
            witness_outputs.append({"parameters": dict(zip(("period", "phase"), setting)),
                                    "output": result, "output_sha256": digest(result)})
        if len({row["output_sha256"] for row in witness_outputs}) != len(p.SETTINGS):
            raise AssertionError("lawful witness does not distinguish all settings")
        write_json(output / "witness.private.json", {"input": witness, "outputs": witness_outputs,
                                                     "all_five_pairwise_distinct": True})
        for ordinal, (seed, explicit) in enumerate(plans):
            episode = p.generate_episode(seed, setting=explicit, bridge=bridge)
            repeat = p.generate_episode(seed, setting=explicit, bridge=bridge)
            if repeat != episode:
                raise AssertionError("same seed and controls did not reproduce the full episode")
            if random.getstate() != baseline_rng:
                raise AssertionError("prototype changed global random state")
            setting = p.validate_setting(**episode["parameters"])
            settings_counts[f"{setting[0]}:{setting[1]}"] += 1
            for pair in episode["train"] + episode["test"]:
                verify_geometry(pair["input"], pair["output"], setting)
            public = p.public_challenge(episode)
            if (set(public) != {"train", "test"}
                    or any(set(pair) != {"input", "output"} for pair in public["train"])
                    or any(set(pair) != {"input"} for pair in public["test"])):
                raise AssertionError("public challenge has hidden metadata or query labels")
            row = {"ordinal": ordinal, "seed": seed, "parameters": episode["parameters"],
                   "selection": episode["selection"], "episode_sha256": digest(episode),
                   "public_sha256": digest(public), "reproduced": True,
                   "parameter_rivals": episode["parameter_rivals"]}
            probe_rows.append(row)
            public_rows.append(public)
            private_rows.append(episode)
    for name, path in source_files.items():
        if sha256_bytes(path.read_bytes()) != sources[name]["sha256"]:
            raise RuntimeError("prototype source changed during this probe")
    for filename, rows in (("episodes.private.jsonl", private_rows), ("challenges.public.jsonl", public_rows)):
        (output / filename).write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
    import arc_repl.racket_bridge as bridge_module
    bridge_path = Path(bridge_module.__file__).resolve()
    prelude = bridge_path.parent / "racket_prelude/arc-prelude.rkt"
    runtime["bridge_sha256"] = sha256_bytes(bridge_path.read_bytes())
    runtime["prelude_sha256"] = sha256_bytes(prelude.read_bytes())
    report = {"schema": "rectangle-parametric-probe-v1", "status": "prototype_passed_bounded_probe",
              "task_id": p.TASK_ID, "sources": sources, "runtime": runtime,
              "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
              "settings": [list(setting) for setting in p.SETTINGS],
              "canonical_setting": list(p.CANONICAL), "seeded_range": [0, seed_count - 1],
              "explicit_seeds_per_setting": list(fixed_seeds), "episodes": len(plans),
              "labeled_pairs": sum(len(row["train"]) + len(row["test"]) for row in private_rows),
              "repeated_episodes": len(plans), "setting_counts": settings_counts,
              "parameter_rival_checks": 4 * len(plans), "ambiguous_episodes": 0,
              "geometry_mismatches": 0, "global_rng_unchanged": True,
              "canonical_labeled_pairs": len(canonical_pairs),
              "canonical_unique_inputs": canonical_receipt["unique_inputs"],
              "episode_results": probe_rows, "elapsed_seconds": round(time.monotonic() - started, 3),
              "limitations": ["Separate authoring prototype; no production API, approval, or training admission.",
                              "Finite seeds and the four alternative declared parameter settings only.",
                              "Episode order is intentional: the first demo contains the identifying witness; no query-rotation guarantee.",
                              "Input sampler uses 14..24 grids, 1..4 distinct-color solid rectangles, and one-cell zone separation; lawful domain is 10..24.",
                              "No claim against other transformation families or all possible teaching ambiguities."]}
    report["artifacts"] = artifact_manifest(output)
    write_json(output / "report.json", report)
    return report


def canonical_pairs_for_probe(root):
    return canonical_pairs(p.TASK_ID, root=root, labeled_only=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="new evidence directory; existing paths are refused")
    parser.add_argument("--seed-count", type=int, default=20, help="seeded episodes at consecutive seeds starting 0 (1..50)")
    args = parser.parse_args(argv)
    report = run_probe(args.out, args.seed_count)
    print(json.dumps({key: report[key] for key in ("status", "episodes", "labeled_pairs", "parameter_rival_checks",
                                                  "ambiguous_episodes", "canonical_labeled_pairs", "canonical_unique_inputs")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

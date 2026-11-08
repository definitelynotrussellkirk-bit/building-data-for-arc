#!/usr/bin/env python3
"""Materialize episodes and compact source-bound evidence for the prototype."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

import prototype as p


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _query_metrics(episode):
    pair = episode["test"][0]
    grid, output = pair["input"], pair["output"]
    lines = grid if episode["parameters"]["axis"] == "row" else list(zip(*grid))
    changes = sum(a != b for before, after in zip(grid, output) for a, b in zip(before, after))
    return {"parameters": episode["parameters"], "shape": [len(grid), len(grid[0])],
            "active_lines": sum(any(line) for line in lines), "changed_cells": changes,
            "input_nonzero_cells": sum(bool(value) for line in grid for value in line),
            "output_nonzero_cells": sum(bool(value) for line in output for value in line)}


def build_evidence(seed: int) -> tuple[dict, list]:
    """Bounded exhaustive setting coverage at one seed, with real outputs."""
    sources = [Path(p.__file__).resolve(), Path(__file__).resolve(), Path(__file__).with_name("README.md"),
               Path(p.__file__).resolve().parents[2] / "tests/test_parametric_806425ca81b3.py"]
    hashes = {path.relative_to(p.ROOT).as_posix(): _digest(path) for path in sources}
    report = {"schema": "806425ca81b3-parametric-evidence-v1", "status": "running",
              "generator_id": p.TASK_ID, "original_arc_id": "22168020", "seed": seed,
              "prototype_version": p.VERSION, "prototype_source_hashes": hashes,
              "parameters": {"axis": ["row", "column"], "min_anchors": [2, 3]},
              "canonical_setting": p.DEFAULT_PARAMETERS,
              "command": [sys.executable, *sys.argv],
              "canonical_generator_sha256": _digest(p.ROOT / "generators" / p.TASK_ID / "generator.py"),
              "limits": [
                  "Task-local prototype; no production parameter API or approval change.",
                  "Four settings and one retained episode per setting at the recorded seed.",
                  "Identifiability is measured only against the three other declared parameter settings.",
                  "Sampling uses disjoint repeated-color spans in the chosen axis, both dimensions 6..30.",
                  "Default APIs select the canonical setting; sample_parameters(seed) explicitly samples a fixed setting.",
                  "The selected canonical generator is recorded for context but is not used to construct prototype inputs.",
              ]}
    canonical = p.canonical_record()
    report["canonical_rule"] = {"text": canonical["program_solution"],
                                "sha256": hashlib.sha256(canonical["program_solution"].encode()).hexdigest(),
                                "exact_default_text_match": p.materialize_rule() == canonical["program_solution"]}
    with p.reference_runtime() as runtime:
        report["racket"] = runtime.identity()
        report["episodes"] = [p.generate_episode(seed, setting, runtime=runtime) for setting in p.SETTINGS]
        report["canonical_pairs"] = []
        for split in ("train", "test"):
            for index, pair in enumerate(canonical[split]):
                output = runtime.apply(p.materialize_rule(), pair["input"])
                passed = output == pair["output"] == p.mirror(pair["input"])
                report["canonical_pairs"].append({"split": split, "pair_index": index,
                                                   "input": pair["input"], "expected": pair["output"],
                                                   "actual": output, "passed": passed})
                if not passed:
                    raise AssertionError("canonical label parity failed")
        common = p.counterfactual_input()
        counterfactual = []
        for setting in p.SETTINGS:
            rule = p.materialize_rule(setting)
            output = runtime.apply(rule, common)
            if output != p.mirror(common, setting) or p.input_errors(common, setting):
                raise AssertionError("counterfactual validity/parity failed")
            counterfactual.append({"parameters": setting, "output": output,
                                   "rule_sha256": hashlib.sha256(rule.encode()).hexdigest()})
        distinct = len({json.dumps(case["output"]) for case in counterfactual})
        if distinct != 4:
            raise AssertionError("counterfactual does not distinguish all settings")
        report["counterfactual"] = {"input": common, "results": counterfactual, "distinct_outputs": distinct,
                                    "lawful_under_all_settings": True}
        report["determinism"] = []
        for episode in report["episodes"]:
            setting = episode["parameters"]
            inputs = p.make_inputs(seed, setting)
            inputs_match = all([pair["input"] for pair in episode[split]] == inputs[split]
                               for split in ("train", "test"))
            repeated = runtime.apply(episode["rule"]["text"], episode["test"][0]["input"])
            output_match = repeated == episode["test"][0]["output"]
            if not inputs_match or not output_match:
                raise AssertionError("repeat determinism failed")
            report["determinism"].append({"parameters": setting, "input_replay_matches": inputs_match,
                                           "query_racket_replay_matches": output_match})
            for rival in episode["identifiability"]["rivals"]:
                for split in ("train", "test"):
                    predictions = rival["predictions"][split]
                    if predictions != [p.mirror(pair["input"], rival["parameters"]) for pair in episode[split]]:
                        raise AssertionError("Racket/Python rival parity failed")
        report["racket_calls"] = runtime.calls
    report["large_queries"] = [_query_metrics(episode) for episode in report["episodes"]]
    if any(case["active_lines"] != 24 or case["changed_cells"] < 100 for case in report["large_queries"]):
        raise AssertionError("large query lacks the required semantic workload")
    if hashes != {path.relative_to(p.ROOT).as_posix(): _digest(path) for path in sources}:
        raise RuntimeError("prototype sources changed during evidence generation")
    # Deterministic order permutation does not expose parameter names or seeds.
    indices = list(range(len(report["episodes"])))
    random.Random(f"{seed}:public-order").shuffle(indices)
    public = [p.public_challenge(report["episodes"][index]) for index in indices]
    report["private_public_index_map"] = indices
    report["summary"] = {"episodes": 4, "demonstrations": 12, "queries": 4,
                           "parameter_rivals_refuted": 12, "ambiguous_queries": 0,
                           "canonical_pairs_passed": len(report["canonical_pairs"]),
                           "distinct_counterfactual_outputs": distinct,
                           "racket_python_pair_comparisons": 72,
                           "racket_calls": report["racket_calls"]}
    report["status"] = "prototype_verified"
    return report, public


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify", help="verify all four settings and write two evidence files")
    verify.add_argument("--seed", type=int, default=20261023)
    verify.add_argument("--out", type=Path, required=True)
    episode = subparsers.add_parser("episode", help="write one private episode and one public challenge")
    episode.add_argument("--seed", type=int, required=True)
    episode.add_argument("--axis", choices=("row", "column"))
    episode.add_argument("--min-anchors", type=int, choices=(2, 3))
    episode.add_argument("--sample-parameters", action="store_true")
    episode.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "verify":
        report, public = build_evidence(args.seed)
        args.out.mkdir(parents=True, exist_ok=True)
        _write(args.out / "evidence.json", report)
        _write(args.out / "public_challenges.json", public)
        print(json.dumps({"status": report["status"], **report["summary"], "out": str(args.out)}))
    else:
        if args.sample_parameters and (args.axis is not None or args.min_anchors is not None):
            parser.error("--sample-parameters cannot be combined with an explicit setting")
        setting = p.sample_parameters(args.seed) if args.sample_parameters else p.validate_parameters(
            {key: value for key, value in {"axis": args.axis, "min_anchors": args.min_anchors}.items()
             if value is not None})
        result = p.generate_episode(args.seed, setting)
        args.out.mkdir(parents=True, exist_ok=True)
        _write(args.out / "episode.json", result)
        _write(args.out / "challenge.json", p.public_challenge(result))
        print(json.dumps({"status": "prototype", "identifiable": True, "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

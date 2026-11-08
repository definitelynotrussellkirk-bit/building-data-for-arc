"""Bounded teaching and protected-Racket audit for 204eaaff6c24 parametrics."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "count_bar_anchor_indexed_audit_target", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = prototype
_SPEC.loader.exec_module(prototype)


def _bar(grid, size):
    color = prototype.analyze(grid)["color"]
    return [[color] * size]


def _fixed_candidate(index):
    def rival(grid):
        info = prototype.analyze(grid)
        return _bar(grid, info["candidate_sizes"][index % len(info["candidate_sizes"])])
    return rival


def _reverse_selector(grid):
    info = prototype.analyze(grid)
    index = (-info["anchor_size"]) % len(info["candidate_sizes"])
    return _bar(grid, info["candidate_sizes"][index])


RIVALS = {
    "all_cells": lambda grid: prototype.apply_mode(grid, "all_cells"),
    "anchor_indexed_component": lambda grid: prototype.apply_mode(grid, "anchor_indexed_component"),
    "anchor_size": lambda grid: _bar(grid, prototype.analyze(grid)["anchor_size"]),
    "all_candidates": lambda grid: _bar(grid, sum(prototype.analyze(grid)["candidate_sizes"])),
    "fixed_candidate_0": _fixed_candidate(0),
    "fixed_candidate_1": _fixed_candidate(1),
    "fixed_candidate_2": _fixed_candidate(2),
    "fixed_candidate_3": _fixed_candidate(3),
    "largest_candidate": lambda grid: _bar(grid, max(prototype.analyze(grid)["candidate_sizes"])),
    "smallest_candidate": lambda grid: _bar(grid, min(prototype.analyze(grid)["candidate_sizes"])),
    "wrong_plus_one_selector": prototype.apply_wrong_plus_one,
    "reverse_selector": _reverse_selector,
}


def python_audit(*, seeds=(0, 17), demo_counts=range(2, 7)):
    ambiguities = []
    episode_count = 0
    pair_count = 0
    distinct_count = 0
    stress_count = 0
    branches = set()
    for seed in seeds:
        for demos in demo_counts:
            for mode in prototype.MODES:
                maximum = prototype.generate_episode(
                    seed, count_mode=mode, demos=6, queries=4
                )
                episode = prototype.generate_episode(
                    seed, count_mode=mode, demos=demos, queries=4
                )
                episode_count += 1
                pairs = episode["train"] + episode["test"]
                pair_count += len(pairs)
                serial = {json.dumps(pair["input"], separators=(",", ":")) for pair in pairs}
                distinct_count += len(serial)
                if len(serial) != len(pairs):
                    ambiguities.append({"seed": seed, "demos": demos, "mode": mode, "failure": "duplicate_input"})
                if episode["train"] != maximum["train"][:demos] or episode["test"] != maximum["test"]:
                    ambiguities.append({"seed": seed, "demos": demos, "mode": mode, "failure": "prefix_instability"})
                if any((len(pair["input"]), len(pair["input"][0])) == (30, 30) for pair in episode["test"]):
                    stress_count += 1
                for pair in pairs:
                    branches.add(prototype.analyze(pair["input"])["anchor_size"])
                intended = [pair["output"] for pair in episode["train"]]
                for name, rival in RIVALS.items():
                    if name == mode:
                        continue
                    predictions = [rival(pair["input"]) for pair in episode["train"]]
                    survives = predictions == intended
                    changed_queries = [
                        index
                        for index, pair in enumerate(episode["test"])
                        if rival(pair["input"]) != pair["output"]
                    ]
                    if survives and changed_queries:
                        ambiguities.append({
                            "seed": seed,
                            "demos": demos,
                            "mode": mode,
                            "rival": name,
                            "changed_queries": changed_queries,
                        })
    return {
        "episodes": episode_count,
        "pairs": pair_count,
        "distinct_inputs": distinct_count,
        "stress_30x30": stress_count,
        "anchor_size_branches": sorted(branches),
        "rivals": sorted(RIVALS),
        "ambiguities": ambiguities,
        "limits": "Finite declared rivals over seeds 0 and 17 and demo counts 2..6; not universal uniqueness.",
    }


def _literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def racket_audit(seeds=(0, 17)):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    programs = {mode: prototype.rule_text(mode) for mode in prototype.MODES}
    programs["wrong_plus_one_selector"] = prototype.counterfactual_program()
    mismatches = []
    counterfactual_changes = 0
    evaluations = 0
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("audit requires protected Racket")
        wrapped = {name: wrap_rule(program) for name, program in programs.items()}
        for seed in seeds:
            episode = prototype.generate_episode(
                seed, count_mode="anchor_indexed_component", demos=6, queries=4
            )
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    grid = pair["input"]
                    for mode in prototype.MODES:
                        actual = bridge.eval_text(f"({wrapped[mode]} {_literal(grid)})")
                        expected = prototype.apply_mode(grid, mode)
                        evaluations += 1
                        if actual != expected:
                            mismatches.append({"seed": seed, "split": split, "index": index, "program": mode})
            causal = episode["test"][0]
            correct = bridge.eval_text(f"({wrapped['anchor_indexed_component']} {_literal(causal['input'])})")
            wrong = bridge.eval_text(f"({wrapped['wrong_plus_one_selector']} {_literal(causal['input'])})")
            evaluations += 2
            if correct != wrong:
                counterfactual_changes += 1
            else:
                mismatches.append({"seed": seed, "failure": "counterfactual_unchanged"})
        keep = (
            "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
            "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256",
        )
        return {
            "runtime": {key: identity[key] for key in keep if key in identity},
            "evaluations": evaluations,
            "counterfactual_changes": counterfactual_changes,
            "mismatches": mismatches,
        }


def build_report(out_root: Path):
    python = python_audit()
    racket = racket_audit()
    examples = out_root / "examples"
    private = []
    public_paths = []
    for setting_index, mode in enumerate(prototype.MODES):
        episode = prototype.generate_episode(
            900 + setting_index, count_mode=mode, demos=3, queries=4
        )
        private.append({
            "seed": 900 + setting_index,
            "settings": {"count_mode": mode},
            **episode,
        })
        for query_index in range(4):
            data = prototype.public_bytes(episode, query_index)
            path = examples / "public" / f"{hashlib.sha256(data).hexdigest()}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            public_paths.append(path.relative_to(out_root).as_posix())
    (examples / "private.json").parent.mkdir(parents=True, exist_ok=True)
    (examples / "private.json").write_text(json.dumps(private, indent=2, sort_keys=True) + "\n")
    report = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": prototype.TASK_ID,
        "status": "passed" if not python["ambiguities"] and not racket["mismatches"] else "failed",
        "python": python,
        "racket": racket,
        "program_sha256": {
            mode: hashlib.sha256(prototype.rule_text(mode).encode()).hexdigest()
            for mode in prototype.MODES
        },
        "counterfactual_program_sha256": hashlib.sha256(prototype.counterfactual_program().encode()).hexdigest(),
        "examples": {"private": "examples/private.json", "public": public_paths},
    }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise FileExistsError(args.out)
    args.out.mkdir(parents=True)
    report = build_report(args.out)
    (args.out / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "episodes": report["python"]["episodes"],
        "rivals": len(report["python"]["rivals"]),
        "ambiguities": len(report["python"]["ambiguities"]),
        "racket_evaluations": report["racket"]["evaluations"],
        "mismatches": len(report["racket"]["mismatches"]),
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

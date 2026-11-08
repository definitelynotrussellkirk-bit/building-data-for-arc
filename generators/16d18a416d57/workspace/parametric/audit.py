"""Bounded teaching and protected-Racket audit for the parametric family.

The Python pass asks whether a declared shortcut can fit every visible
Demonstration yet disagree on a query.  The optional CLI pass also re-executes
all distinct setting/input combinations from the maximal episode through the
same protected Racket bridge used by native qualification.
"""
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
    "largest_blue_size_keyed_partner_audit_target", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent parametric prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _paint_partner(grid, selector):
    components = prototype._components_4(grid, 1)
    largest = max(components, key=len)
    out = deepcopy(grid)
    for row, col in largest:
        out[row][col] = 7
    partner = selector(components, largest)
    if partner is not None:
        for row, col in partner:
            out[row][col] = 2
    return out


def _by_size(size):
    def select(components, _largest):
        hits = [component for component in components if len(component) == size]
        return hits[0] if len(hits) == 1 else None
    return select


def _second_largest(components, largest):
    return max((component for component in components if component != largest), key=len)


def _smallest(components, _largest):
    return min(components, key=len)


def _largest_minus_2(components, largest):
    hits = [component for component in components if len(component) == len(largest) - 2]
    return hits[0] if len(hits) == 1 else None


RIVALS = {
    "canonical_only": lambda grid: prototype.apply_mode(grid, "canonical"),
    "fixed_size_2_partner": lambda grid: _paint_partner(grid, _by_size(2)),
    "fixed_size_3_partner": lambda grid: _paint_partner(grid, _by_size(3)),
    "fixed_size_4_partner": lambda grid: _paint_partner(grid, _by_size(4)),
    "second_largest_partner": lambda grid: _paint_partner(grid, _second_largest),
    "smallest_partner": lambda grid: _paint_partner(grid, _smallest),
    "largest_minus_2_partner": lambda grid: _paint_partner(grid, _largest_minus_2),
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
            for mode in ("canonical", "size_keyed_partner"):
                episode = prototype.generate_episode(seed, mode=mode, demos=demos, queries=4)
                episode_count += 1
                pairs = episode["train"] + episode["test"]
                pair_count += len(pairs)
                inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
                if len(inputs) != len(set(inputs)):
                    raise ValueError(f"duplicate visible input in seed={seed}, demos={demos}, mode={mode}")
                distinct_count += len(set(inputs))
                stress_count += sum(
                    len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                    for pair in episode["test"]
                )
                branches.update(
                    max(map(len, prototype._components_4(pair["input"], 1)))
                    for pair in episode["train"]
                )

                for name, rival in RIVALS.items():
                    fits = all(rival(pair["input"]) == pair["output"] for pair in episode["train"])
                    changed_queries = [
                        index
                        for index, pair in enumerate(episode["test"])
                        if rival(pair["input"]) != pair["output"]
                    ]
                    if fits and changed_queries:
                        ambiguities.append(
                            {
                                "seed": seed,
                                "demos": demos,
                                "mode": mode,
                                "rival": name,
                                "changed_queries": changed_queries,
                            }
                        )

    return {
        "episodes": episode_count,
        "pairs": pair_count,
        "distinct_inputs": distinct_count,
        "stress_30x30": stress_count,
        "largest_size_branches": sorted(branches),
        "rivals": sorted(RIVALS),
        "ambiguities": ambiguities,
        "limits": "Finite declared rivals over seeds 0 and 17 and demo counts 2..6; not universal uniqueness.",
    }


def _racket_audit(seeds=(0, 17)):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    wrapped = {}
    mismatches = []
    evaluations = 0
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("audit requires a protected Racket backend")
        for seed in seeds:
            for mode in ("canonical", "size_keyed_partner"):
                episode = prototype.generate_episode(seed, mode=mode, demos=6, queries=4)
                program = prototype.rule_text(mode)
                wrapped.setdefault(program, wrap_rule(program))
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        literal = "'(" + " ".join(
                            "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
                        ) + ")"
                        actual = bridge.eval_text(f"({wrapped[program]} {literal})")
                        evaluations += 1
                        if actual != pair["output"]:
                            mismatches.append(
                                {"seed": seed, "mode": mode, "split": split, "index": index}
                            )
        keep = (
            "schema",
            "backend",
            "protected",
            "binary_sha256",
            "prelude_sha256",
            "bridge_sha256",
            "boot_script_sha256",
            "candidate_symbol_policy_sha256",
        )
        return {
            "runtime": {key: identity[key] for key in keep if key in identity},
            "evaluations": evaluations,
            "mismatches": mismatches,
        }
    finally:
        bridge.close()


def build_report():
    report = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": "16d18a416d57",
        "python": python_audit(),
        "racket": _racket_audit(),
        "program_sha256": {
            mode: hashlib.sha256(prototype.rule_text(mode).encode()).hexdigest()
            for mode in ("canonical", "size_keyed_partner")
        },
    }
    report["status"] = (
        "passed"
        if not report["python"]["ambiguities"] and not report["racket"]["mismatches"]
        else "failed"
    )
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": report["status"],
        "episodes": report["python"]["episodes"],
        "racket_evaluations": report["racket"]["evaluations"],
        "ambiguities": len(report["python"]["ambiguities"]),
        "mismatches": len(report["racket"]["mismatches"]),
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

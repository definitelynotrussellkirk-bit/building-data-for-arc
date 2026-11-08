"""Finite lesson audit and protected-Racket replay for b5b012cd97d9.

This is deliberately a bounded certificate, not a claim of universal rule
uniqueness.  It checks the declared fixed/reversed/spurious-axis shortcuts on
fresh deterministic episodes and replays both intended rules and every rival
through the packet's protected Racket runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Callable


_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_b5b012cd97d9_audit_prototype", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent parametric prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = prototype
_SPEC.loader.exec_module(prototype)

_FINAL = "(if big-above packed (rotate-180 packed))"
_VERTICAL_BLOCK = """(big-row-center2 (+ (first big-box) (third big-box)))
                  (small-row-center2 (+ (first small-box) (third small-box)))
                  (big-above (< big-row-center2 small-row-center2))"""
_HORIZONTAL_BLOCK = """(big-col-center2 (+ (second big-box) (fourth big-box)))
                  (small-col-center2 (+ (second small-box) (fourth small-box)))
                  (big-above (< big-col-center2 small-col-center2))"""


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"expected exactly one source fragment, found {source.count(old)}")
    return source.replace(old, new, 1)


def racket_programs() -> dict[str, str]:
    """Return exact intended programs plus source-derived executable rivals."""
    canonical = prototype.program({"placement": "canonical"})
    vertical = prototype.program({"placement": "preserve_vertical"})
    programs = {
        "canonical": canonical,
        "preserve_vertical": vertical,
        "always_below": _replace_once(vertical, _FINAL, "(rotate-180 packed)"),
        "reverse_vertical": _replace_once(
            vertical, _FINAL, "(if big-above (rotate-180 packed) packed)"
        ),
        "horizontal_proxy": _replace_once(vertical, _VERTICAL_BLOCK, _HORIZONTAL_BLOCK),
    }
    if len(set(programs.values())) != len(programs):
        raise ValueError("audit programs must be source-distinct")
    return programs


def _rivals(placement: str) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    return prototype.declared_rivals(placement)


def python_audit(*, seeds=(0, 17), demo_counts=range(2, 7)) -> dict[str, object]:
    ambiguities: list[dict[str, object]] = []
    episodes = 0
    pairs = 0
    stress = 0
    branches: set[bool] = set()
    rival_checks = 0

    for seed in seeds:
        for demos in demo_counts:
            for placement in prototype.PLACEMENTS:
                episode = prototype.generate(seed, {"placement": placement}, demos, 4)
                episodes += 1
                all_pairs = episode["train"] + episode["test"]
                pairs += len(all_pairs)
                serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in all_pairs]
                if len(serialized) != len(set(serialized)):
                    raise ValueError(
                        f"duplicate input seed={seed} demos={demos} placement={placement}"
                    )
                stress += sum(
                    len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                    for pair in episode["test"]
                )
                branches.update(
                    bool(prototype.analyze(pair["input"])["big_above"])
                    for pair in all_pairs
                )
                intended_demos = [pair["output"] for pair in episode["train"]]
                intended_queries = [pair["output"] for pair in episode["test"]]
                for name, rival in _rivals(placement).items():
                    rival_checks += 1
                    rival_demos = [rival(pair["input"]) for pair in episode["train"]]
                    rival_queries = [rival(pair["input"]) for pair in episode["test"]]
                    if rival_demos == intended_demos and rival_queries != intended_queries:
                        ambiguities.append(
                            {
                                "seed": seed,
                                "demos": demos,
                                "placement": placement,
                                "rival": name,
                                "changed_queries": [
                                    index
                                    for index, (actual, expected) in enumerate(
                                        zip(rival_queries, intended_queries)
                                    )
                                    if actual != expected
                                ],
                            }
                        )

    return {
        "episodes": episodes,
        "pairs": pairs,
        "rival_checks": rival_checks,
        "stress_30x30": stress,
        "vertical_branches": sorted(branches),
        "ambiguities": ambiguities,
        "limits": (
            "Finite declared rivals over the supplied seeds and demo counts; "
            "not a universal identifiability proof."
        ),
    }


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def _python_rival(name: str) -> Callable[[list[list[int]]], list[list[int]]]:
    mapping = {
        "canonical": prototype._canonical_pack,
        "preserve_vertical": lambda grid: prototype.solve_python(grid, "preserve_vertical"),
        "always_below": prototype._always_below,
        "reverse_vertical": prototype._reverse_vertical,
        "horizontal_proxy": prototype._horizontal_proxy,
    }
    return mapping[name]


def racket_audit(*, seeds=(0, 17)) -> dict[str, object]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    programs = racket_programs()
    wrapped = {name: wrap_rule(source) for name, source in programs.items()}
    intended_mismatches: list[dict[str, object]] = []
    rival_mismatches: list[dict[str, object]] = []
    ambiguities: list[dict[str, object]] = []
    rival_results: list[dict[str, object]] = []
    evaluations = 0

    with RacketBridge(max_calls_before_restart=64) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("audit requires the protected Racket backend")

        for seed in seeds:
            for placement in prototype.PLACEMENTS:
                episode = prototype.generate(seed, {"placement": placement}, 2, 4)
                pairs = episode["train"] + episode["test"]
                intended_name = placement
                for flat_index, pair in enumerate(pairs):
                    actual = bridge.eval_text(
                        f"({wrapped[intended_name]} {_grid_literal(pair['input'])})"
                    )
                    evaluations += 1
                    if actual != pair["output"]:
                        intended_mismatches.append(
                            {
                                "seed": seed,
                                "placement": placement,
                                "split": "train" if flat_index < 2 else "test",
                                "index": flat_index if flat_index < 2 else flat_index - 2,
                            }
                        )

                for rival_name, rival_python in _rivals(placement).items():
                    demo_matches: list[bool] = []
                    query_matches: list[bool] = []
                    for flat_index, pair in enumerate(pairs):
                        actual = bridge.eval_text(
                            f"({wrapped[rival_name]} {_grid_literal(pair['input'])})"
                        )
                        evaluations += 1
                        expected_rival = rival_python(pair["input"])
                        if actual != expected_rival:
                            rival_mismatches.append(
                                {
                                    "seed": seed,
                                    "placement": placement,
                                    "rival": rival_name,
                                    "split": "train" if flat_index < 2 else "test",
                                    "index": flat_index if flat_index < 2 else flat_index - 2,
                                }
                            )
                        match = actual == pair["output"]
                        if flat_index < 2:
                            demo_matches.append(match)
                        else:
                            query_matches.append(match)
                    result = {
                        "seed": seed,
                        "placement": placement,
                        "rival": rival_name,
                        "demo_matches": demo_matches,
                        "query_matches": query_matches,
                    }
                    rival_results.append(result)
                    if all(demo_matches) and not all(query_matches):
                        ambiguities.append(result)

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
        runtime = {key: identity[key] for key in keep if key in identity}

    return {
        "runtime": runtime,
        "evaluations": evaluations,
        "intended_mismatches": intended_mismatches,
        "rival_program_mismatches": rival_mismatches,
        "ambiguities": ambiguities,
        "rival_results": rival_results,
    }


def build_report() -> dict[str, object]:
    programs = racket_programs()
    report: dict[str, object] = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": prototype.TASK_ID,
        "python": python_audit(),
        "racket": racket_audit(),
        "program_sha256": {
            name: hashlib.sha256(source.encode("utf-8")).hexdigest()
            for name, source in programs.items()
        },
    }
    report["status"] = (
        "passed"
        if not report["python"]["ambiguities"]
        and not report["racket"]["intended_mismatches"]
        and not report["racket"]["rival_program_mismatches"]
        and not report["racket"]["ambiguities"]
        else "failed"
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = build_report()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "status": report["status"],
        "python_episodes": report["python"]["episodes"],
        "python_rival_checks": report["python"]["rival_checks"],
        "racket_evaluations": report["racket"]["evaluations"],
        "ambiguities": len(report["python"]["ambiguities"]) + len(report["racket"]["ambiguities"]),
        "mismatches": len(report["racket"]["intended_mismatches"])
        + len(report["racket"]["rival_program_mismatches"]),
        "out": str(args.out),
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

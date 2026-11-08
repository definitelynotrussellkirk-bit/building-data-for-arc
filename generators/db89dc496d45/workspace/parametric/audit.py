"""Finite teaching, protected-Racket, and causal audit for db89dc496d45.

This checks only the declared shortcut family over a bounded seed range.  It is
not a proof of unique induction.  The protected Racket pass independently
replays labels and compares the admitted alternate with a key+1 counterfactual.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "_db89dc496d45_size_relay_audit_target", _HERE / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load adjacent prototype")
prototype = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = prototype
_SPEC.loader.exec_module(prototype)


def _ranked_non_source(grid):
    info = prototype.analyze(grid)
    counts = info["counts"]
    return sorted(
        (color for color in counts if color != info["source_color"]),
        key=lambda color: (-counts[color], color),
    )


def _color_output(grid, color):
    return prototype._crop_color_mask(grid, color) if color is not None else [[0]]


def _fixed_rank(grid, rank):
    ranked = _ranked_non_source(grid)
    return _color_output(grid, ranked[rank - 1] if len(ranked) >= rank else None)


def _most_frequent_non_source(grid):
    return _fixed_rank(grid, 1)


def _least_frequent_non_source(grid):
    ranked = _ranked_non_source(grid)
    return _color_output(grid, ranked[-1] if ranked else None)


def _first_numeric_non_source(grid):
    info = prototype.analyze(grid)
    colors = sorted(color for color in info["counts"] if color != info["source_color"])
    return _color_output(grid, colors[0] if colors else None)


def _last_numeric_non_source(grid):
    info = prototype.analyze(grid)
    colors = sorted(color for color in info["counts"] if color != info["source_color"])
    return _color_output(grid, colors[-1] if colors else None)


def _source_color_envelope(grid):
    return _color_output(grid, prototype.analyze(grid)["source_color"])


def _other_setting(grid, true_mode):
    other = (
        "largest_size_relay"
        if true_mode == "largest_component"
        else "largest_component"
    )
    return prototype.apply_mode(grid, other)


def _wrong_intermediate(grid, _true_mode):
    return prototype.apply_wrong_intermediate(grid)


def _unary(candidate):
    return lambda grid, _mode: candidate(grid)


RIVALS = {
    "other_setting": _other_setting,
    "wrong_intermediate_plus_one": _wrong_intermediate,
    "source_color_envelope": _unary(_source_color_envelope),
    "most_frequent_non_source": _unary(_most_frequent_non_source),
    "least_frequent_non_source": _unary(_least_frequent_non_source),
    "fixed_rank_1": lambda grid, _mode: _fixed_rank(grid, 1),
    "fixed_rank_2": lambda grid, _mode: _fixed_rank(grid, 2),
    "fixed_rank_3": lambda grid, _mode: _fixed_rank(grid, 3),
    "fixed_rank_4": lambda grid, _mode: _fixed_rank(grid, 4),
    "first_numeric_non_source": _unary(_first_numeric_non_source),
    "last_numeric_non_source": _unary(_last_numeric_non_source),
}


def python_audit(*, seeds=range(64), demo_counts=range(2, 7)):
    ambiguities = []
    episode_count = 0
    pair_count = 0
    distinct_count = 0
    stress_count = 0
    relay_ranks = set()
    keys = set()
    relay_colors = set()
    source_colors = set()

    for seed in seeds:
        for demos in demo_counts:
            for mode in ("largest_component", "largest_size_relay"):
                episode = prototype.generate_episode(
                    seed, mode=mode, demos=demos, queries=4
                )
                episode_count += 1
                pairs = episode["train"] + episode["test"]
                pair_count += len(pairs)
                visible = [
                    json.dumps(pair["input"], separators=(",", ":"))
                    for pair in pairs
                ]
                if len(visible) != len(set(visible)):
                    raise ValueError(
                        f"duplicate input seed={seed} demos={demos} mode={mode}"
                    )
                distinct_count += len(set(visible))
                stress_count += sum(
                    len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                    for pair in episode["test"]
                )

                for pair in pairs:
                    info = prototype.analyze(pair["input"])
                    ranked = _ranked_non_source(pair["input"])
                    relay_ranks.add(ranked.index(info["relay_color"]) + 1)
                    keys.add(info["key"])
                    relay_colors.add(info["relay_color"])
                    source_colors.add(info["source_color"])

                for name, rival in RIVALS.items():
                    fits = all(
                        rival(pair["input"], mode) == pair["output"]
                        for pair in episode["train"]
                    )
                    changed_queries = [
                        index
                        for index, pair in enumerate(episode["test"])
                        if rival(pair["input"], mode) != pair["output"]
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
        "relay_ranks": relay_ranks,
        "keys": keys,
        "relay_colors": relay_colors,
        "source_colors": source_colors,
        "rivals": sorted(RIVALS),
        "ambiguities": ambiguities,
        "limits": (
            "Finite declared rivals over the requested seeds and demo counts; "
            "not universal uniqueness."
        ),
    }


def python_causal_witness(*, seed=17):
    episode = prototype.generate_episode(
        seed, mode="largest_size_relay", demos=2, queries=4
    )
    grid = episode["test"][3]["input"]
    info = prototype.analyze(grid)
    correct = prototype.apply_mode(grid, "largest_size_relay")
    wrong = prototype.apply_wrong_intermediate(grid)
    return {
        "seed": seed,
        "split": "test",
        "index": 3,
        "setting": {"mode": "largest_size_relay"},
        "step_a": "find the unique largest 4-connected monochromatic component",
        "intermediate": "its cell count",
        "key": info["key"],
        "wrong_key": info["key"] + 1,
        "step_b": "select the non-source color whose global count equals the key and crop its union",
        "correct_color": info["relay_color"],
        "wrong_color": info["wrong_color"],
        "input": grid,
        "correct_output": correct,
        "wrong_output": wrong,
        "correct_program_sha256": hashlib.sha256(
            prototype.SIZE_RELAY_PROGRAM.encode()
        ).hexdigest(),
        "wrong_program_sha256": hashlib.sha256(
            prototype.WRONG_INTERMEDIATE_PROGRAM.encode()
        ).hexdigest(),
    }


def _grid_literal(grid):
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def racket_audit(*, seeds=(0, 17)):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    wrapped = {}
    mismatches = []
    evaluations = 0
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("audit requires protected Racket")

        for seed in seeds:
            for mode in ("largest_component", "largest_size_relay"):
                episode = prototype.generate_episode(
                    seed, mode=mode, demos=6, queries=4
                )
                program = prototype.rule_text(mode)
                wrapped.setdefault(program, wrap_rule(program))
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        actual = bridge.eval_text(
                            f"({wrapped[program]} {_grid_literal(pair['input'])})"
                        )
                        evaluations += 1
                        if actual != pair["output"]:
                            mismatches.append(
                                {
                                    "seed": seed,
                                    "mode": mode,
                                    "split": split,
                                    "index": index,
                                    "expected": pair["output"],
                                    "actual": actual,
                                }
                            )

        witness = python_causal_witness(seed=17)
        correct_wrapped = wrap_rule(prototype.SIZE_RELAY_PROGRAM)
        wrong_wrapped = wrap_rule(prototype.WRONG_INTERMEDIATE_PROGRAM)
        correct_actual = bridge.eval_text(
            f"({correct_wrapped} {_grid_literal(witness['input'])})"
        )
        wrong_actual = bridge.eval_text(
            f"({wrong_wrapped} {_grid_literal(witness['input'])})"
        )
        evaluations += 2
        causal = {
            **witness,
            "correct_racket_output": correct_actual,
            "wrong_racket_output": wrong_actual,
            "correct_matches_claim": correct_actual == witness["correct_output"],
            "wrong_matches_claim": wrong_actual == witness["wrong_output"],
            "final_outputs_differ": correct_actual != wrong_actual,
        }

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
            "causal_witness": causal,
        }
    finally:
        bridge.close()


def _jsonable_python(report):
    return {
        **report,
        "relay_ranks": sorted(report["relay_ranks"]),
        "keys": sorted(report["keys"]),
        "relay_colors": sorted(report["relay_colors"]),
        "source_colors": sorted(report["source_colors"]),
    }


def build_report(*, seed_count=64):
    python_report = python_audit(seeds=range(seed_count), demo_counts=range(2, 7))
    racket_report = racket_audit()
    causal = racket_report["causal_witness"]
    status = (
        "passed"
        if not python_report["ambiguities"]
        and not racket_report["mismatches"]
        and causal["correct_matches_claim"]
        and causal["wrong_matches_claim"]
        and causal["final_outputs_differ"]
        else "failed"
    )
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": "db89dc496d45",
        "status": status,
        "python": _jsonable_python(python_report),
        "racket": racket_report,
        "program_sha256": {
            "largest_component": hashlib.sha256(
                prototype.CANONICAL_PROGRAM.encode()
            ).hexdigest(),
            "largest_size_relay": hashlib.sha256(
                prototype.SIZE_RELAY_PROGRAM.encode()
            ).hexdigest(),
            "wrong_intermediate_plus_one": hashlib.sha256(
                prototype.WRONG_INTERMEDIATE_PROGRAM.encode()
            ).hexdigest(),
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-count", type=int, default=64)
    args = parser.parse_args(argv)
    if not 1 <= args.seed_count <= 4096:
        parser.error("--seed-count must be 1..4096")
    report = build_report(seed_count=args.seed_count)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes": report["python"]["episodes"],
                "pairs": report["python"]["pairs"],
                "ambiguities": len(report["python"]["ambiguities"]),
                "racket_evaluations": report["racket"]["evaluations"],
                "racket_mismatches": len(report["racket"]["mismatches"]),
                "causal_outputs_differ": report["racket"]["causal_witness"][
                    "final_outputs_differ"
                ],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

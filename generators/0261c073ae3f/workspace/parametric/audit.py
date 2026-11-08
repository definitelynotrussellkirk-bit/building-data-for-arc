"""Bounded authoring audit for the normalized-panel Boolean family.

The audit covers deterministic matched inputs, prefix stability, finite
semantic rivals, protected-Racket execution, a wrong-intermediate ablation,
and the unchanged base sampler.  It does not grant owner acceptance or
training admission.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
HOME = HERE.parent.parent
ROOT = HOME.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared" / "runtime")]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


P = _load(HERE / "prototype.py", "_0261_authoring_audit_prototype")
A = _load(HERE / "adapter.py", "_0261_authoring_audit_adapter")
G = _load(HOME / "generator.py", "_0261_authoring_audit_generator")


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def run(out: Path, seeds: int) -> dict[str, Any]:
    if type(seeds) is not int or not 1 <= seeds <= 256:
        raise ValueError("seeds must be an exact integer in 1..256")
    if out.exists():
        raise ValueError("output directory must be new")
    out.mkdir(parents=True)

    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    failures: list[dict[str, Any]] = []
    distinct_inputs: set[str] = set()
    episodes = 0
    pair_instances = 0
    teaching_checks = 0
    matched_input_checks = 0
    prefix_checks = 0
    max_query_checks = 0

    for seed in range(seeds):
        full = {
            op: A.generate(seed, {"boolean_op": op}, 6, 4)
            for op in P.BOOLEAN_OPS
        }
        xor_inputs = [
            pair["input"]
            for split in ("train", "test")
            for pair in full["xor"][split]
        ]
        or_inputs = [
            pair["input"]
            for split in ("train", "test")
            for pair in full["or"][split]
        ]
        if xor_inputs != or_inputs:
            failures.append({"seed": seed, "kind": "settings_not_matched"})
        matched_input_checks += 1
        if len({_digest(grid) for grid in xor_inputs}) != 10:
            failures.append({"seed": seed, "kind": "duplicate_inputs"})
        distinct_inputs.update(_digest(grid) for grid in xor_inputs)

        for op in P.BOOLEAN_OPS:
            for demos in (2, 3, 6):
                episode = A.generate(seed, {"boolean_op": op}, demos, 4)
                episodes += 1
                pair_instances += demos + 4
                survivors = P.teaching_survivors(episode["train"])
                if survivors != [op]:
                    failures.append(
                        {
                            "seed": seed,
                            "boolean_op": op,
                            "demos": demos,
                            "kind": "teaching_survivors",
                            "survivors": survivors,
                        }
                    )
                teaching_checks += 1
                if episode["train"] != full[op]["train"][:demos]:
                    failures.append({"seed": seed, "boolean_op": op, "kind": "demo_prefix"})
                if A.generate(seed, {"boolean_op": op}, demos, 1)["test"] != full[op]["test"][:1]:
                    failures.append({"seed": seed, "boolean_op": op, "kind": "query_prefix"})
                prefix_checks += 2

            max_grid = full[op]["test"][3]["input"]
            if (len(max_grid), len(max_grid[0])) != (30, 30):
                failures.append({"seed": seed, "boolean_op": op, "kind": "missing_30x30"})
            if sum(value != 0 for row in max_grid for value in row) < 420:
                failures.append({"seed": seed, "boolean_op": op, "kind": "insubstantial_30x30"})
            output = full[op]["test"][3]["output"]
            if len(output) < 24 or len(output[0]) < 12:
                failures.append({"seed": seed, "boolean_op": op, "kind": "small_stress_output"})
            max_query_checks += 1

    bridge = RacketBridge(timeout=30, max_calls_before_restart=64)
    protected_evaluations = 0
    counterfactual_checks = 0
    execution_rows: list[dict[str, Any]] = []
    try:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            failures.append({"kind": "unprotected_runtime", "runtime": identity})
        for seed in range(seeds):
            for op in P.BOOLEAN_OPS:
                episode = A.generate(seed, {"boolean_op": op}, 2, 4)
                program = A.program({"boolean_op": op})
                wrapped = wrap_rule(program)
                for split, index in (("train", 0), ("test", 3)):
                    pair = episode[split][index]
                    got = bridge.eval_text(f"({wrapped} {_literal(pair['input'])})")
                    protected_evaluations += 1
                    if got != pair["output"]:
                        failures.append(
                            {"seed": seed, "boolean_op": op, "split": split, "index": index, "kind": "racket_label_mismatch"}
                        )
                    execution_rows.append(
                        {
                            "seed": seed,
                            "boolean_op": op,
                            "split": split,
                            "index": index,
                            "input_sha256": _digest(pair["input"]),
                            "output_sha256": _digest(got),
                            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                        }
                    )

            pair = A.generate(seed, {"boolean_op": "or"}, 2, 4)["train"][0]
            wrong = (HERE / "counterfactual_raw_or.rkt").read_text(encoding="utf-8")
            wrong_output = bridge.eval_text(f"({wrap_rule(wrong)} {_literal(pair['input'])})")
            protected_evaluations += 1
            counterfactual_checks += 1
            if wrong_output == pair["output"]:
                failures.append({"seed": seed, "kind": "counterfactual_did_not_change"})
    finally:
        bridge.close()

    separator_profiles: set[tuple[int, int, int]] = set()
    normalized_shapes: set[tuple[int, int]] = set()
    mixed_left_panels = 0
    base_samples = 128
    for sample_index in range(base_samples):
        grid = G.generate(65537, sample_index)
        errors = G.self_check(grid)
        if errors:
            failures.append({"sample_index": sample_index, "kind": "base_self_check", "errors": errors})
            continue
        sep = next(c for c in range(len(grid[0])) if all(row[c] == 5 for row in grid))
        separator_profiles.add((len(grid), len(grid[0]), sep))
        output = P.solve(grid, "xor")
        normalized_shapes.add((len(output), len(output[0])))
        left_colors = {row[c] for row in grid for c in range(sep) if row[c] not in (0, 5)}
        mixed_left_panels += int(len(left_colors) > 1)
    if len(separator_profiles) < 8:
        failures.append({"kind": "base_separator_diversity", "count": len(separator_profiles)})
    if len(normalized_shapes) < 3:
        failures.append({"kind": "base_shape_diversity", "count": len(normalized_shapes)})
    if mixed_left_panels == 0:
        failures.append({"kind": "base_missing_mixed_color_panel"})

    report: dict[str, Any] = {
        "schema": "0261c073ae3f-parametric-authoring-audit-v1",
        "status": "passed" if not failures else "failed",
        "seed_count": seeds,
        "settings": list(P.BOOLEAN_OPS),
        "demo_counts": [2, 3, 6],
        "episodes": episodes,
        "pair_instances": pair_instances,
        "distinct_inputs": len(distinct_inputs),
        "teaching_checks": teaching_checks,
        "matched_input_checks": matched_input_checks,
        "prefix_checks": prefix_checks,
        "max_query_checks": max_query_checks,
        "protected_racket_evaluations": protected_evaluations,
        "counterfactual_checks": counterfactual_checks,
        "base_samples": base_samples,
        "base_separator_profiles": len(separator_profiles),
        "base_normalized_shapes": len(normalized_shapes),
        "base_mixed_left_panels": mixed_left_panels,
        "racket": identity,
        "failures": failures,
        "source_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(HERE.iterdir())
            if path.is_file() and path.suffix in {".py", ".rkt", ".json"}
        },
        "limits": "Finite authored-rival audit; no owner acceptance or training admission.",
    }
    (out / "execution.json").write_text(json.dumps(execution_rows, indent=2, sort_keys=True) + "\n")
    (out / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=32)
    args = parser.parse_args()
    report = run(args.out, args.seeds)
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "seed_count",
                    "episodes",
                    "distinct_inputs",
                    "protected_racket_evaluations",
                    "counterfactual_checks",
                    "base_separator_profiles",
                    "base_normalized_shapes",
                    "base_mixed_left_panels",
                )
            },
            sort_keys=True,
        )
    )
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

"""Bounded authoring audit for the crop/swap post-transform family.

This checks deterministic matched inputs, prefix stability, finite teaching
rivals, protected-Racket label execution, the wrong-intermediate causal
ablation, and the repaired base sampler.  It is evidence for review only;
it never grants owner acceptance or training admission.
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


P = _load(HERE / "prototype.py", "_f22_authoring_audit_prototype")
A = _load(HERE / "adapter.py", "_f22_authoring_audit_adapter")
G = _load(HOME / "generator.py", "_f22_authoring_audit_generator")


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _inner_facts(grid: list[list[int]]) -> tuple[bool, bool]:
    cells = [
        (r, c, grid[r][c])
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] != 0
    ]
    r0, r1 = min(r for r, _, _ in cells), max(r for r, _, _ in cells)
    c0, c1 = min(c for _, c, _ in cells), max(c for _, c, _ in cells)
    outer = grid[r0][c0]
    inner = {(r - r0, c - c0) for r, c, value in cells if value != outer}
    ir0, ir1 = min(r for r, _ in inner), max(r for r, _ in inner)
    ic0, ic1 = min(c for _, c in inner), max(c for _, c in inner)
    solid = len(inner) == (ir1 - ir0 + 1) * (ic1 - ic0 + 1)
    centered = ir0 + ir1 == r1 - r0 and ic0 + ic1 == c1 - c0
    return solid, centered


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
            mode: A.generate(seed, {"post_transform": mode}, 6, 4)
            for mode in P.TRANSFORMS
        }
        left_inputs = [
            pair["input"]
            for split in ("train", "test")
            for pair in full["as_is"][split]
        ]
        right_inputs = [
            pair["input"]
            for split in ("train", "test")
            for pair in full["rotate_cw"][split]
        ]
        if left_inputs != right_inputs:
            failures.append({"seed": seed, "kind": "settings_not_matched"})
        matched_input_checks += 1
        if len({_digest(grid) for grid in left_inputs}) != 10:
            failures.append({"seed": seed, "kind": "duplicate_inputs"})
        distinct_inputs.update(_digest(grid) for grid in left_inputs)

        for mode in P.TRANSFORMS:
            for demos in (2, 3, 6):
                episode = A.generate(seed, {"post_transform": mode}, demos, 4)
                episodes += 1
                pair_instances += demos + 4
                survivors = P.teaching_survivors(episode["train"])
                if survivors != [mode]:
                    failures.append(
                        {
                            "seed": seed,
                            "mode": mode,
                            "demos": demos,
                            "kind": "teaching_survivors",
                            "survivors": survivors,
                        }
                    )
                teaching_checks += 1
                if episode["train"] != full[mode]["train"][:demos]:
                    failures.append({"seed": seed, "mode": mode, "kind": "demo_prefix"})
                if A.generate(seed, {"post_transform": mode}, demos, 1)["test"] != full[mode]["test"][:1]:
                    failures.append({"seed": seed, "mode": mode, "kind": "query_prefix"})
                prefix_checks += 2

            max_grid = full[mode]["test"][3]["input"]
            if (len(max_grid), len(max_grid[0])) != (30, 30):
                failures.append({"seed": seed, "mode": mode, "kind": "missing_30x30"})
            if sum(value != 0 for row in max_grid for value in row) < 500:
                failures.append({"seed": seed, "mode": mode, "kind": "insubstantial_30x30"})
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
            for mode in P.TRANSFORMS:
                episode = A.generate(seed, {"post_transform": mode}, 2, 4)
                program = A.program({"post_transform": mode})
                wrapped = wrap_rule(program)
                for split, index in (("train", 0), ("test", 3)):
                    pair = episode[split][index]
                    got = bridge.eval_text(f"({wrapped} {_literal(pair['input'])})")
                    protected_evaluations += 1
                    if got != pair["output"]:
                        failures.append(
                            {"seed": seed, "mode": mode, "split": split, "index": index, "kind": "racket_label_mismatch"}
                        )
                    execution_rows.append(
                        {
                            "seed": seed,
                            "mode": mode,
                            "split": split,
                            "index": index,
                            "input_sha256": _digest(pair["input"]),
                            "output_sha256": _digest(got),
                            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                        }
                    )

            pair = A.generate(seed, {"post_transform": "rotate_cw"}, 2, 4)["train"][0]
            wrong = (HERE / "counterfactual_crop_rotate.rkt").read_text(encoding="utf-8")
            wrong_output = bridge.eval_text(
                f"({wrap_rule(wrong)} {_literal(pair['input'])})"
            )
            protected_evaluations += 1
            counterfactual_checks += 1
            if wrong_output == pair["output"]:
                failures.append({"seed": seed, "kind": "counterfactual_did_not_change"})
    finally:
        bridge.close()

    topology_counts = {
        "solid": 0,
        "non_solid": 0,
        "centered": 0,
        "off_center": 0,
    }
    for sample_index in range(128):
        grid = G.generate(104729, sample_index)
        errors = G.self_check(grid)
        if errors:
            failures.append({"sample_index": sample_index, "kind": "base_self_check", "errors": errors})
            continue
        solid, centered = _inner_facts(grid)
        topology_counts["solid" if solid else "non_solid"] += 1
        topology_counts["centered" if centered else "off_center"] += 1
    if not all(topology_counts.values()):
        failures.append({"kind": "base_topology_missing", "counts": topology_counts})

    report: dict[str, Any] = {
        "schema": "f22baf82ea81-parametric-authoring-audit-v1",
        "status": "passed" if not failures else "failed",
        "seed_count": seeds,
        "settings": list(P.TRANSFORMS),
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
        "base_topology_samples": 128,
        "base_topology_counts": topology_counts,
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
                    "base_topology_counts",
                )
            },
            sort_keys=True,
        )
    )
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

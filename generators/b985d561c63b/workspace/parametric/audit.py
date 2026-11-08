#!/usr/bin/env python3
"""Bounded Racket-backed teaching audit for the b985d561c63b family.

This tool is intentionally finite.  It checks exact selected labels through the
protected Racket bridge, probes a compact bank of plausible fixed/cue shortcuts
against demonstrations only, retains one causal counterexample, and verifies the
public/private projection boundary.  It grants no owner acceptance.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
_PROTOTYPE_PATH = HERE / "prototype.py"
_SPEC = importlib.util.spec_from_file_location(
    "_b985d561c63b_parametric_audit_prototype", _PROTOTYPE_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load {_PROTOTYPE_PATH}")
P = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = P
_SPEC.loader.exec_module(P)


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _grid_sha(grid: Any) -> str:
    return _sha_text(json.dumps(grid, sort_keys=True, separators=(",", ":")))


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _corner_variants(grid: Any) -> dict[str, list[list[int]]]:
    derived = P.hole_corner_intermediate(grid)["corner"]
    row_only = "top_left" if derived.startswith("top") else "bottom_left"
    col_only = "top_left" if derived.endswith("left") else "top_right"
    opposite = {
        "top_left": "bottom_right",
        "top_right": "bottom_left",
        "bottom_left": "top_right",
        "bottom_right": "top_left",
    }[derived]
    return {
        "row_only": P.apply_python(
            grid, stamp_anchor="hole_corner", corner_override=row_only
        ),
        "column_only": P.apply_python(
            grid, stamp_anchor="hole_corner", corner_override=col_only
        ),
        "opposite_corner": P.apply_python(
            grid, stamp_anchor="hole_corner", corner_override=opposite
        ),
    }


def _projection_check(episode: dict[str, Any]) -> dict[str, Any]:
    public = P.public_challenge(episode)
    original_id = P.public_id(episode)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"stamp_anchor": "private-mutated"}
    changed["program_solution"] = "private-mutated"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    changed_id = P.public_id(changed)
    visible = json.dumps(public, sort_keys=True)
    return {
        "public_id": original_id,
        "private_mutation_id": changed_id,
        "stable_under_private_mutation": original_id == changed_id,
        "public_keys": sorted(public),
        "demo_pair_keys": sorted(public["train"][0]),
        "query_pair_keys": sorted(public["test"][0]),
        "private_setting_absent": episode["settings"]["stamp_anchor"] not in visible,
    }


def _rival_rows(
    bridge: Any,
    episode: dict[str, Any],
    chosen: str,
) -> tuple[list[dict[str, Any]], int]:
    pairs = episode["train"] + episode["test"]
    demos = len(episode["train"])
    labels = [pair["output"] for pair in pairs]
    evaluations = 0

    racket_programs = {
        "declared_top_left": P.program_for("top_left"),
        "declared_hole_corner": P.program_for("hole_corner"),
        "fixed_top_left": P.fixed_anchor_program("top_left"),
        "fixed_top_right": P.fixed_anchor_program("top_right"),
        "fixed_bottom_left": P.fixed_anchor_program("bottom_left"),
        "fixed_bottom_right": P.fixed_anchor_program("bottom_right"),
    }
    predictions: dict[str, list[list[list[int]]]] = {}
    for name, source in racket_programs.items():
        predictions[name] = [
            P.execute_rule(source, pair["input"], bridge=bridge) for pair in pairs
        ]
        evaluations += len(pairs)

    python_names = ("row_only", "column_only", "opposite_corner")
    for name in python_names:
        predictions[name] = [_corner_variants(pair["input"])[name] for pair in pairs]
    predictions["nonzero_only"] = [
        P.apply_python(
            pair["input"],
            stamp_anchor=chosen,
            copy_template_zeros=False,
        )
        for pair in pairs
    ]

    intended_names = {
        "top_left": {"declared_top_left", "fixed_top_left"},
        "hole_corner": {"declared_hole_corner"},
    }[chosen]
    rows: list[dict[str, Any]] = []
    for name, outputs in predictions.items():
        demo_mismatches = [
            index for index in range(demos) if outputs[index] != labels[index]
        ]
        query_mismatches = [
            index
            for index in range(len(pairs) - demos)
            if outputs[demos + index] != labels[demos + index]
        ]
        intended_equivalent = name in intended_names
        rows.append(
            {
                "name": name,
                "authority": "protected_racket" if name in racket_programs else "python_hypothesis",
                "program_sha256": (
                    _sha_text(racket_programs[name]) if name in racket_programs else None
                ),
                "intended_equivalent": intended_equivalent,
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
                "fits_all_demonstrations": not demo_mismatches,
                "ambiguous_wrong_rival": (
                    not intended_equivalent and not demo_mismatches and bool(query_mismatches)
                ),
            }
        )
    return rows, evaluations


def run_audit(*, seeds: tuple[int, ...] = (0, 17), out: Path) -> dict[str, Any]:
    if type(seeds) is not tuple or not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be a nonempty tuple of distinct exact integers")
    for seed in seeds:
        P._validate_seed(seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)

    jobs: list[dict[str, Any]] = []
    ambiguous = 0
    selected_evaluations = 0
    rival_evaluations = 0
    minimal_case: dict[str, Any] | None = None
    with P.RacketBridge(max_calls_before_restart=128) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("audit requires a protected Racket backend")
        for seed in seeds:
            for chosen in P.ALLOWED_STAMP_ANCHORS:
                episode = P.generate_episode(
                    seed,
                    stamp_anchor=chosen,
                    demos=2,
                    queries=4,
                )
                source = episode["program_solution"]
                all_pairs = episode["train"] + episode["test"]
                actual = [
                    P.execute_rule(source, pair["input"], bridge=bridge)
                    for pair in all_pairs
                ]
                selected_evaluations += len(all_pairs)
                if actual != [pair["output"] for pair in all_pairs]:
                    raise AssertionError("Python claim differs from protected Racket label")
                rivals, count = _rival_rows(bridge, episode, chosen)
                rival_evaluations += count
                ambiguous += sum(row["ambiguous_wrong_rival"] for row in rivals)
                projection = _projection_check(episode)
                if not all(
                    (
                        projection["stable_under_private_mutation"],
                        projection["private_setting_absent"],
                        projection["demo_pair_keys"] == ["input", "output"],
                        projection["query_pair_keys"] == ["input"],
                    )
                ):
                    raise AssertionError("public/private projection check failed")
                jobs.append(
                    {
                        "seed": seed,
                        "settings": episode["settings"],
                        "program_sha256": _sha_text(source),
                        "input_sha256": [_grid_sha(pair["input"]) for pair in all_pairs],
                        "output_sha256": [_grid_sha(pair["output"]) for pair in all_pairs],
                        "intermediate_values": [
                            P.hole_corner_intermediate(pair["input"])["corner"]
                            for pair in all_pairs
                        ],
                        "rivals": rivals,
                        "projection": projection,
                    }
                )

                if minimal_case is None and chosen == "hole_corner":
                    pair = episode["train"][0]
                    wrong = P.fixed_anchor_program("bottom_left")
                    wrong_output = P.execute_rule(wrong, pair["input"], bridge=bridge)
                    selected_evaluations += 1
                    if wrong_output == pair["output"]:
                        raise AssertionError("selected causal counterexample does not change output")
                    minimal_case = {
                        "schema": "arcpuzzles-parametric-minimal-counterexample-v1",
                        "task_id": P.TASK_ID,
                        "settings": episode["settings"],
                        "input": pair["input"],
                        "actual_output": pair["output"],
                        "wrong_intermediate_output": wrong_output,
                        "program": source,
                        "program_sha256": _sha_text(source),
                        "counterfactual_program": wrong,
                        "counterfactual_program_sha256": _sha_text(wrong),
                        "intermediate_value": P.hole_corner_intermediate(pair["input"])["corner"],
                        "wrong_intermediate_value": "bottom_left",
                        "ablation": "wrong_intermediate",
                        "qualified_selector": {"seed": seed, "split": "train", "pair_index": 0},
                        "racket": {"backend": "racket", "protected": True},
                    }

    if minimal_case is None:
        raise AssertionError("no alternate-setting counterexample was retained")
    stress = P.input_features(
        P.generate_episode(seeds[0], stamp_anchor="hole_corner", demos=2, queries=4)["test"][3]["input"]
    )
    report = {
        "schema": "arcpuzzles-parametric-self-review-v1",
        "task_id": P.TASK_ID,
        "prototype_version": P.VERSION,
        "status": "passed" if ambiguous == 0 else "ambiguous",
        "settings": list(P.ALLOWED_STAMP_ANCHORS),
        "seeds": list(seeds),
        "counts": {
            "jobs": len(jobs),
            "demonstrations_per_job": 2,
            "queries_per_job": 4,
            "selected_racket_evaluations": selected_evaluations,
            "rival_racket_evaluations": rival_evaluations,
            "ambiguous_wrong_rivals": ambiguous,
        },
        "canonical_source_sha256": P.CANONICAL_SHA256,
        "alternate_source_sha256": _sha_text(P.program_for("hole_corner")),
        "prototype_sha256": _sha_bytes(_PROTOTYPE_PATH.read_bytes()),
        "adapter_sha256": _sha_bytes((HERE / "adapter.py").read_bytes()),
        "promotion_sha256": _sha_bytes((HERE / "promotion.json").read_bytes()),
        "racket": {
            key: identity[key]
            for key in (
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            )
            if key in identity
        },
        "stress_30x30": stress,
        "jobs": jobs,
        "minimal_counterexample": "minimal-counterexample.json",
        "limits": [
            "finite rival bank; no universal uniqueness claim",
            "Python-only shortcut predictions are compared to protected-Racket labels",
            "reviewer audit does not perform owner acceptance or training admission",
        ],
    }
    _write(out / "minimal-counterexample.json", minimal_case)
    _write(out / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run_audit(seeds=tuple(args.seeds or (0, 17)), out=args.out)
    print(
        json.dumps(
            {
                "status": report["status"],
                "jobs": report["counts"]["jobs"],
                "ambiguous_wrong_rivals": report["counts"]["ambiguous_wrong_rivals"],
                "report": str((args.out / "report.json").resolve()),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

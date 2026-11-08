#!/usr/bin/env python3
"""Reproduce canonical-fitting shortcut rivals and a generated disagreement.

Run from the repository through the packet wrapper, for example::

    python3 run_with_racket.py python3 \
      generators/4c93dc1552b3/workspace/probe_shortcuts.py \
      --out-dir ../checks/generator-shortcut

The report uses retained canonical labels for canonical-fit checks and the
selected generator's independent Python mirror for generated candidates.  Use
``arcpuzzles apply`` on the emitted ``input.json`` for hash-bound Racket label
authority; this script deliberately does not import a private Racket runner.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "4c93dc1552b3"
RIVAL_NAME = "all_solid_rectangles_any_color"
ROOT = find_root(__file__)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(payload)


def load_generator():
    candidates = (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    source = next((path for path in candidates if path.is_file()), None)
    if source is None:
        raise FileNotFoundError(f"selected generator {TASK_ID} not found under {ROOT}")
    spec = importlib.util.spec_from_file_location("shortcut_probe_generator", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def _declared_rivals(gen) -> dict[str, Callable[[list[list[int]]], list[list[int]]]]:
    rivals = getattr(gen, "CANONICAL_SHORTCUTS", None)
    if not isinstance(rivals, dict) or not rivals:
        raise TypeError("generator.CANONICAL_SHORTCUTS must be a nonempty mapping")
    for name, predictor in rivals.items():
        if not isinstance(name, str) or not callable(predictor):
            raise TypeError("canonical shortcut names must map to callables")
    return dict(rivals)


def _canonical_scores(gen) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    scores: dict[str, dict[str, Any]] = {}
    for name, predictor in _declared_rivals(gen).items():
        fit_cases: list[dict[str, Any]] = []
        refuted_cases: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for pair in pairs:
            identity = {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
            }
            try:
                prediction = predictor(copy.deepcopy(pair["input"]))
            except Exception as exc:  # evidence should retain rival failures
                errors.append({**identity, "error": f"{type(exc).__name__}: {exc}"})
                continue
            record = {**identity, "input_sha256": _json_hash(pair["input"])}
            if prediction == pair["output"]:
                fit_cases.append(record)
            else:
                refuted_cases.append(record)
        scores[name] = {
            "fit_count": len(fit_cases),
            "refuted_count": len(refuted_cases),
            "error_count": len(errors),
            "fits_all": len(fit_cases) == len(pairs) and not refuted_cases and not errors,
            "fit_cases": fit_cases,
            "refuted_cases": refuted_cases,
            "errors": errors,
        }
    return pairs, scores


def _diff_cells(
    grid: list[list[int]],
    intended: list[list[int]],
    rival: list[list[int]],
) -> list[dict[str, int]]:
    result = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if intended[row][col] != rival[row][col]:
                result.append(
                    {
                        "row": row,
                        "col": col,
                        "input_color": grid[row][col],
                        "intended_color": intended[row][col],
                        "rival_color": rival[row][col],
                    }
                )
    return result


def _find_generated_witness(gen, *, seed_limit: int) -> dict[str, Any]:
    rival = _declared_rivals(gen)[RIVAL_NAME]
    for profile in gen.SCENE_PROFILES:
        band = gen._PROFILE_BY_NAME[profile][0]
        for seed in range(seed_limit):
            sample_index = seed * 17 + 3
            grid = gen.generate(
                seed,
                sample_index,
                difficulty=band,
                scene_profile=profile,
            )
            intended = gen.rule_mirror(copy.deepcopy(grid))
            prediction = rival(copy.deepcopy(grid))
            differing = _diff_cells(grid, intended, prediction)
            if not differing:
                continue
            return {
                "rival": RIVAL_NAME,
                "seed": seed,
                "sample_index": sample_index,
                "difficulty": band,
                "overrides": {"scene_profile": profile},
                "input": grid,
                "intended_output": intended,
                "rival_output": prediction,
                "differing_cells": differing,
                "input_sha256": _json_hash(grid),
                "intended_output_sha256": _json_hash(intended),
                "rival_output_sha256": _json_hash(prediction),
                "generator_membership": {
                    "self_check_errors": gen.self_check(
                        copy.deepcopy(grid),
                        difficulty=band,
                        meta={"overrides": {"scene_profile": profile}},
                    ),
                    "teaching_check_errors": gen.teaching_check(
                        copy.deepcopy(grid),
                        difficulty=band,
                        meta={"overrides": {"scene_profile": profile}},
                    ),
                    "strict_canonical_like_errors": gen.strict_canonical_like(
                        copy.deepcopy(grid)
                    ),
                    "observed_overrides": gen.observe_overrides(copy.deepcopy(grid)),
                },
            }
    raise AssertionError(
        f"no generated {RIVAL_NAME!r} disagreement found in seeds [0, {seed_limit})"
    )


def _rule_binding(gen) -> dict[str, Any]:
    matching = []
    ledger = canonical_path(ROOT)
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            program = row["program_solution"]
            normalized = " ".join(program.split())
            full_hash = _sha256_bytes(normalized.encode("utf-8"))
            matching.append(
                {
                    "variant": len(matching),
                    "normalized_rule_sha256": full_hash,
                    "rule_hash": full_hash[:12],
                }
            )
    return {
        "canonical_ledger": str(ledger.relative_to(ROOT)),
        "canonical_bindings": matching,
        "generator_rule_hash": gen.RULE_HASH,
        "pin_matches_all": bool(matching)
        and all(item["rule_hash"] == gen.RULE_HASH for item in matching),
    }


def build_report(*, seed_limit: int = 256) -> dict[str, Any]:
    if seed_limit < 1:
        raise ValueError("seed_limit must be positive")
    gen, source = load_generator()
    canonical, canonical_scores = _canonical_scores(gen)
    witness = _find_generated_witness(gen, seed_limit=seed_limit)
    return {
        "schema": "4c93dc1552b3-shortcut-probe-v1",
        "task_id": TASK_ID,
        "source": {
            "generator_path": str(source.relative_to(ROOT)),
            "generator_sha256": _sha256_bytes(source.read_bytes()),
            "generator_version": gen.VERSION,
            "probe_path": str(Path(__file__).resolve().relative_to(ROOT)),
            "probe_sha256": _sha256_bytes(Path(__file__).read_bytes()),
            **_rule_binding(gen),
        },
        "label_authority": {
            "canonical_pairs": "retained canonical labels",
            "generated_intended_output": "generator.rule_mirror; verify emitted input with public arcpuzzles apply",
            "generated_racket_executed_by_this_script": False,
        },
        "canonical_pair_count": len(canonical),
        "canonical_rivals": canonical_scores,
        "selected_witness": witness,
        "conclusion": (
            "The color-agnostic solid-rectangle rival fits every canonical pair, "
            "but the selected generator emits a lawful solid non-blue rectangle "
            "whose corners the rival recolors and the intended rule preserves."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--seed-limit", type=int, default=256)
    args = parser.parse_args()
    report = build_report(seed_limit=args.seed_limit)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "python_report.json"
    input_path = out_dir / "input.json"
    for path in (report_path, input_path):
        if path.exists():
            parser.error(f"refusing to overwrite existing evidence: {path}")
    input_path.write_text(
        json.dumps(report["selected_witness"]["input"], indent=2) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(report_path),
        "input": str(input_path),
        "canonical_pair_count": report["canonical_pair_count"],
        "selected_rival": report["selected_witness"]["rival"],
        "differing_cell_count": len(report["selected_witness"]["differing_cells"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()

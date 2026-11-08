#!/usr/bin/env python3
"""Fast source-bound lesson/rotation census for db95939a5dd0.

The shared semantic gate remains the authority-backed check: it executes the
canonical Racket rule and verifies witness/rival disagreement.  This utility is
for larger schedule coverage after that gate is green; it labels generated
inputs with the selected generator's independently canonical-tested Python
mirror and scores every declared competitor plus every query rotation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


TASK_ID = "db95939a5dd0"
BANDS = ("easy", "medium", "hard")


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _lesson_seed(task_id: str, band: str, index: int) -> int:
    text = f"lesson-census:v1:{task_id}:{band}:{index}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)


def _score(gen: Any, demos: list[dict], query: dict) -> dict:
    reasons = list(gen.lesson_identifiable(demos, query))
    survivors = []
    ambiguous = []
    errors = []
    for name, solve in sorted(gen.LESSON_COMPETITORS.items()):
        try:
            fits = all(solve(pair["input"]) == pair["output"] for pair in demos)
            if fits:
                survivors.append(name)
                if solve(query["input"]) != query["output"]:
                    ambiguous.append(name)
        except Exception as exc:  # evidence must keep failures visible
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    return {
        "ambiguous": ambiguous,
        "survivors": survivors,
        "hook_reasons": reasons,
        "errors": errors,
    }


def run_census(
    gen: Any,
    *,
    per_band: int = 100,
    bands: Iterable[str] = BANDS,
) -> dict:
    if type(per_band) is not int or per_band < 1:
        raise ValueError("per_band must be a positive integer")
    bands = tuple(bands)
    if not bands or any(band not in BANDS for band in bands):
        raise ValueError(f"bands must be a non-empty subset of {BANDS}")

    source_path = Path(gen.__file__).resolve()
    report = {
        "schema": "db95939a5dd0-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "examples_needed": gen.EXAMPLES_NEEDED,
        "lesson_schedule_period": gen.LESSON_SCHEDULE_PERIOD,
        "bands": list(bands),
        "per_band": per_band,
        "label_authority": (
            "generator._rule_output; canonical parity is separately established "
            "by canonical-pair tests and the Racket-backed semantic gate"
        ),
        "summary": {
            "lessons": 0,
            "pairs": 0,
            "rotations": 0,
            "ambiguous": 0,
            "hook_warnings": 0,
            "errors": 0,
            "witness_pairs": 0,
            "unique_inputs": 0,
        },
        "per_band_summary": {},
        "counterexamples": [],
        "limits": [
            "Finite declared-rival census, not universal identifiability proof.",
            "Uses the selected Python mirror for labels; Racket parity is checked separately.",
            "Each lesson uses four consecutive sample indices and the shared census seed recipe.",
        ],
    }
    unique_inputs: set[str] = set()

    for band in bands:
        band_summary = {
            "lessons": 0,
            "pairs": 0,
            "rotations": 0,
            "ambiguous": 0,
            "hook_warnings": 0,
            "errors": 0,
            "witness_pairs": 0,
        }
        for index in range(per_band):
            seed = _lesson_seed(TASK_ID, band, index)
            pairs = []
            materialization_errors = []
            for sample_index in range(index, index + gen.EXAMPLES_NEEDED + 1):
                try:
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    self_errors = list(gen.self_check(grid, difficulty=band))
                    if self_errors:
                        raise ValueError("self_check: " + "; ".join(self_errors))
                    pair = {"input": grid, "output": gen._rule_output(grid)}
                    pairs.append(pair)
                    unique_inputs.add(_digest(grid))
                    if gen._has_opposite_role_color_reuse(grid):
                        band_summary["witness_pairs"] += 1
                except Exception as exc:
                    materialization_errors.append(
                        f"sample_index={sample_index}: {type(exc).__name__}: {exc}"
                    )
            if materialization_errors or len(pairs) != gen.EXAMPLES_NEEDED + 1:
                band_summary["errors"] += 1
                report["counterexamples"].append(
                    {
                        "band": band,
                        "index": index,
                        "seed": seed,
                        "kind": "materialization_error",
                        "details": materialization_errors,
                    }
                )
                continue

            band_summary["lessons"] += 1
            band_summary["pairs"] += len(pairs)
            production = _score(gen, pairs[: gen.EXAMPLES_NEEDED], pairs[-1])
            if production["ambiguous"]:
                band_summary["ambiguous"] += 1
            if production["hook_reasons"]:
                band_summary["hook_warnings"] += 1
            if production["errors"]:
                band_summary["errors"] += 1
            if any(production.values()):
                if production["ambiguous"] or production["hook_reasons"] or production["errors"]:
                    report["counterexamples"].append(
                        {
                            "band": band,
                            "index": index,
                            "seed": seed,
                            "kind": "production",
                            **production,
                        }
                    )

            for held_out, query in enumerate(pairs):
                demos = [pair for i, pair in enumerate(pairs) if i != held_out]
                score = _score(gen, demos, query)
                band_summary["rotations"] += 1
                if score["ambiguous"]:
                    band_summary["ambiguous"] += 1
                if score["hook_reasons"]:
                    band_summary["hook_warnings"] += 1
                if score["errors"]:
                    band_summary["errors"] += 1
                if score["ambiguous"] or score["hook_reasons"] or score["errors"]:
                    report["counterexamples"].append(
                        {
                            "band": band,
                            "index": index,
                            "seed": seed,
                            "kind": "rotation",
                            "held_out": held_out,
                            **score,
                        }
                    )

        report["per_band_summary"][band] = band_summary
        for key in (
            "lessons",
            "pairs",
            "rotations",
            "ambiguous",
            "hook_warnings",
            "errors",
            "witness_pairs",
        ):
            report["summary"][key] += band_summary[key]

    report["summary"]["unique_inputs"] = len(unique_inputs)
    report["status"] = (
        "pass"
        if not report["summary"]["ambiguous"]
        and not report["summary"]["hook_warnings"]
        and not report["summary"]["errors"]
        else "fail"
    )
    return report


def _load_generator():
    import sys

    repo = Path(__file__).resolve().parents[3]
    for path in (repo, repo / "shared" / "runtime"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    from reviewer_support import load_selected_generator

    module, _source_path, _source_sha = load_selected_generator(TASK_ID, root=repo)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(f"refusing to overwrite {args.out}")
    report = run_census(_load_generator(), per_band=args.per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))
    print(f"status={report['status']} out={args.out}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

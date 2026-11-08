#!/usr/bin/env python3
"""Fast source-bound probe for c5a69e7cd8c8's lesson and override contract.

This authoring probe is deliberately cheaper than the shared Racket-backed
``lesson-census``.  It checks every cyclic start in the finite schedule, every
held-out query position, all rivals declared by the selected generator, each
witness-to-rival claim, and the complete advertised canvas/opening/depth/lateral
cross-product.  Labels come from the task's independent Python review mirror;
use the shared census for authoritative Racket-labelled evidence.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

HERE = Path(__file__).resolve()
for ancestor in HERE.parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "c5a69e7cd8c8"
BANDS = ("easy", "medium", "hard")


def _load_generator(root: Path):
    candidates = (
        root / "generators" / TASK_ID / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    source = next((path for path in candidates if path.is_file()), None)
    if source is None:
        raise FileNotFoundError(f"no generator.py for {TASK_ID} under {root}")
    spec = importlib.util.spec_from_file_location(
        f"probe_generator_{TASK_ID}", source
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, source


def _digest_grid(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _pair(gen, grid) -> dict[str, Any]:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def audit(
    *,
    seeds: Iterable[int] = (12317, 12319, 12323),
    starts: int | None = None,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Return a deterministic JSON-serializable contract report."""
    root_path = Path(root).resolve() if root is not None else find_root(HERE)
    gen, source = _load_generator(root_path)
    seed_values = tuple(int(seed) for seed in seeds)
    if not seed_values:
        raise ValueError("at least one seed is required")
    if starts is None:
        starts = int(gen.LESSON_SCHEDULE_PERIOD)
    if starts < 1:
        raise ValueError("starts must be positive")

    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    canonical = canonical_pairs(TASK_ID, root=root_path, labeled_only=True)
    shortcut_failures: list[dict[str, Any]] = []
    for rival_name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in canonical:
            before = deepcopy(pair["input"])
            try:
                predicted = rival(pair["input"])
            except Exception as exc:  # reported, never swallowed
                shortcut_failures.append(
                    {
                        "rival": rival_name,
                        "split": pair.get("split"),
                        "pair_index": pair.get("pair_index"),
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            if predicted != pair["output"]:
                shortcut_failures.append(
                    {
                        "rival": rival_name,
                        "split": pair.get("split"),
                        "pair_index": pair.get("pair_index"),
                        "error": "does_not_fit_canonical_pair",
                    }
                )
            if pair["input"] != before:
                shortcut_failures.append(
                    {
                        "rival": rival_name,
                        "split": pair.get("split"),
                        "pair_index": pair.get("pair_index"),
                        "error": "mutated_input",
                    }
                )

    ambiguities: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    generated: list[list[list[int]]] = []
    competitor_disagreements = {name: 0 for name in gen.LESSON_COMPETITORS}
    windows = 0
    rotations = 0
    for band in BANDS:
        for seed in seed_values:
            for start in range(starts):
                lesson = []
                for offset in range(int(gen.EXAMPLES_NEEDED) + 1):
                    grid = gen.generate(seed, start + offset, difficulty=band)
                    findings = gen.self_check(grid, difficulty=band)
                    if findings:
                        ambiguities.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "offset": offset,
                                "kind": "self_check",
                                "reasons": list(findings),
                            }
                        )
                    pair = _pair(gen, grid)
                    lesson.append(pair)
                    generated.append(grid)
                    unique_inputs.add(_digest_grid(grid))
                    for name, rival in gen.LESSON_COMPETITORS.items():
                        if rival(grid) != pair["output"]:
                            competitor_disagreements[name] += 1
                windows += 1
                for query_index, query in enumerate(lesson):
                    demos = [
                        pair for index, pair in enumerate(lesson)
                        if index != query_index
                    ]
                    rotations += 1
                    independent = []
                    for name, rival in gen.LESSON_COMPETITORS.items():
                        fits = all(
                            rival(pair["input"]) == pair["output"]
                            for pair in demos
                        )
                        changes_query = rival(query["input"]) != query["output"]
                        if fits and changes_query:
                            independent.append(name)
                    hook_reasons = list(gen.lesson_identifiable(demos, query))
                    if independent or hook_reasons:
                        ambiguities.append(
                            {
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "kind": "lesson_ambiguity",
                                "independent_survivors": independent,
                                "hook_reasons": hook_reasons,
                            }
                        )

    witness_claim_failures: list[dict[str, Any]] = []
    witness_firings: dict[str, int] = {}
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        firing = [grid for grid in generated if witness(grid)]
        witness_firings[witness_name] = len(firing)
        claimed = list(getattr(gen, "WITNESS_RIVALS", {}).get(witness_name, ()))
        if not firing:
            witness_claim_failures.append(
                {"witness": witness_name, "error": "never_fired"}
            )
        if not claimed:
            witness_claim_failures.append(
                {"witness": witness_name, "error": "no_declared_rivals"}
            )
        for rival_name in claimed:
            rival = gen.SEMANTIC_RIVALS.get(rival_name)
            if rival is None:
                witness_claim_failures.append(
                    {
                        "witness": witness_name,
                        "rival": rival_name,
                        "error": "unknown_rival",
                    }
                )
                continue
            if firing and not any(
                rival(grid) != gen.rule_mirror(grid) for grid in firing
            ):
                witness_claim_failures.append(
                    {
                        "witness": witness_name,
                        "rival": rival_name,
                        "error": "no_disagreement_on_firing_grid",
                    }
                )

    depth_lo, depth_hi = (
        int(part) for part in gen.AXES["support_depth"]["valid"].split("..")
    )
    geometric_failures: list[dict[str, Any]] = []
    geometric_cases = 0
    for canvas in gen.CANVAS_DIMS:
        for opening in gen.OPENINGS:
            for depth in range(depth_lo, depth_hi + 1):
                for lateral in gen.LATERALS:
                    geometric_cases += 1
                    overrides = {
                        "canvas": canvas,
                        "opening": opening,
                        "support_depth": depth,
                        "palette": "6_9",
                        "anchor": "middle",
                        "lateral": lateral,
                        "n_extras": 0,
                    }
                    try:
                        grid = gen.generate(
                            44_001,
                            geometric_cases,
                            difficulty="medium",
                            **overrides,
                        )
                        findings = gen.self_check(grid, difficulty="medium")
                        observed = gen.observe_overrides(grid)
                    except Exception as exc:
                        geometric_failures.append(
                            {
                                "overrides": overrides,
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )
                        continue
                    mismatches = {
                        name: {"requested": value, "observed": observed.get(name)}
                        for name, value in overrides.items()
                        if observed.get(name) != value
                    }
                    if findings or mismatches:
                        geometric_failures.append(
                            {
                                "overrides": overrides,
                                "self_check": list(findings),
                                "mismatches": mismatches,
                            }
                        )

    never_refuted = sorted(
        name for name, count in competitor_disagreements.items() if count == 0
    )
    status = "PASS" if not any(
        (shortcut_failures, ambiguities, witness_claim_failures,
         geometric_failures, never_refuted)
    ) else "FAIL"
    return {
        "schema": "c5a69e7cd8c8-curriculum-contract-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": source_hash,
        "rule_hash": gen.RULE_HASH,
        "examples_needed": gen.EXAMPLES_NEEDED,
        "bands": list(BANDS),
        "seeds": list(seed_values),
        "starts_per_seed_band": starts,
        "windows_checked": windows,
        "rotations_checked": rotations,
        "unique_inputs": len(unique_inputs),
        "canonical_pairs": len(canonical),
        "canonical_shortcuts": sorted(gen.CANONICAL_SHORTCUTS),
        "canonical_shortcut_failures": shortcut_failures,
        "competitors": sorted(gen.LESSON_COMPETITORS),
        "competitor_disagreements": competitor_disagreements,
        "competitors_never_refuted": never_refuted,
        "witness_firings": witness_firings,
        "witness_claim_failures": witness_claim_failures,
        "ambiguities": ambiguities,
        "geometric_contract_cases": geometric_cases,
        "geometric_failures": geometric_failures,
        "status": status,
        "limitations": [
            "Generated labels use the independent Python review mirror, not Racket.",
            "Only declared rivals are tested; undeclared hypotheses remain unknown.",
            "Finite seeds do not prove behavior outside the advertised finite schedule.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[12317, 12319, 12323])
    parser.add_argument("--starts", type=int)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = audit(seeds=args.seeds, starts=args.starts)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(text, end="")
    else:
        if args.out.exists():
            parser.error("--out must name a new file; preserve earlier evidence")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

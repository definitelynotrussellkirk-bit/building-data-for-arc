#!/usr/bin/env python3
"""Finite authoring audit of yellow-ring predicate contrasts; never a solve tool."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "7494855fa379"


def own_support():
    # Bootstrap from this file's tree, independent of cwd or predecessor paths.
    for parent in Path(__file__).resolve().parents:
        for relative in ("reviewer_support.py", "shared/runtime/reviewer_support.py"):
            helper = parent / relative
            if helper.is_file():
                sys.path.insert(0, str(helper.parent))
                if (parent / "src/arcpuzzles").is_dir():
                    sys.path.insert(0, str(parent / "src"))
                from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid
                return canonical_pairs, canonical_path, find_root, normalize_grid
    raise FileNotFoundError("No reviewer_support in this probe's library/runtime tree")


canonical_pairs, canonical_path, find_root, normalize_grid = own_support()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def predicate_rule(grid, mode="exact"):
    """Independent Python mirror / simple rivals, using simultaneous updates."""
    out = deepcopy(grid)
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            ring = [grid[r + dr][c + dc] for dr in (-1, 0, 1)
                    for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]
            if grid[r][c] != 0 and mode != "overwrite_nonzero_center":
                continue
            if mode == "orthogonal_only":
                fires = all(grid[r + dr][c + dc] == 4
                            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
            elif mode == "seven_of_eight":
                fires = ring.count(4) >= 7
            elif mode == "any_color_ring":
                fires = ring[0] != 0 and len(set(ring)) == 1
            else:
                fires = ring == [4] * 8
            if fires:
                out[r][c] = 6
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator-path", type=Path, help="explicit source snapshot; default own selected generator")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 17])
    parser.add_argument("--sample-start", type=int, default=0)
    parser.add_argument("--sample-stop", type=int, default=12, help="exclusive sample index")
    parser.add_argument("--bands", nargs="+", choices=("easy", "medium", "hard"), default=["easy", "medium", "hard"])
    parser.add_argument("--verify-racket", action="store_true", help="public Catalog.apply on retained first witnesses")
    parser.add_argument("--racket-timeout", type=float, default=120)
    parser.add_argument("--require-observed", action="store_true", help="exit 1 if a canonical-fitting rival lacks a witness in any requested band")
    parser.add_argument("--out", type=Path, required=True, help="new report JSON; refuses overwrite")
    args = parser.parse_args()
    if not 0 <= args.sample_start < args.sample_stop or args.racket_timeout <= 0:
        parser.error("require 0 <= sample-start < sample-stop and positive racket-timeout")
    if args.out.exists():
        parser.error("output already exists; choose a new path")
    root = find_root(__file__)
    selected = root / "generators" / TASK_ID / "generator.py"
    if not selected.is_file():
        selected = root / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
    source = (args.generator_path or selected).resolve()
    source_hash = file_hash(source)
    spec = importlib.util.spec_from_file_location("predicate_probe_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    errors, rivals = [], {}
    for mode in ("orthogonal_only", "seven_of_eight", "any_color_ring", "overwrite_nonzero_center"):
        rivals[f"simple:{mode}"] = lambda grid, mode=mode: predicate_rule(grid, mode)
    for attribute in ("LESSON_COMPETITORS", "SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS"):
        declaration = getattr(gen, attribute, None)
        if declaration is None:
            continue
        if not isinstance(declaration, dict):
            errors.append(f"{attribute}: expected dict of named callables")
            continue
        for name, fn in declaration.items():
            if not isinstance(name, str) or not callable(fn):
                errors.append(f"{attribute}:{name}: expected string name and callable")
            else:
                rivals[f"{attribute}:{name}"] = fn
    scored = {}
    for name, fn in rivals.items():
        mismatches, failures = [], []
        for pair in pairs:
            identity = {key: pair[key] for key in ("variant", "split", "pair_index")}
            try:
                if normalize_grid(fn(deepcopy(pair["input"]))) != pair["output"]:
                    mismatches.append(identity)
            except Exception as exc:
                failures.append({**identity, "error": str(exc)})
        scored[name] = {"canonical_fit": None if failures else not mismatches,
                        "canonical_refutations": mismatches, "canonical_errors": failures,
                        "by_band": {band: {"draws_scored": 0, "refutations": 0, "errors": 0,
                                           "first_witness_sha256": None} for band in args.bands}}
        errors.extend(f"{name}: canonical: {failure}" for failure in failures)
    mirror_matches = all(predicate_rule(pair["input"]) == pair["output"] for pair in pairs)
    if not mirror_matches:
        errors.append("Python mirror disagrees with a retained canonical label")
    witnesses, draws = {}, []
    for band in args.bands:
        for seed in args.seeds:
            for index in range(args.sample_start, args.sample_stop):
                identity = {"difficulty": band, "seed": seed, "sample_index": index}
                try:
                    grid = normalize_grid(gen.generate(seed, index, difficulty=band))
                except Exception as exc:
                    errors.append({**identity, "generation_error": str(exc)})
                    continue
                sha = digest(grid)
                draws.append({**identity, "input_sha256": sha})
                expected = predicate_rule(grid)
                for name, fn in rivals.items():
                    row = scored[name]["by_band"][band]
                    try:
                        prediction = normalize_grid(fn(deepcopy(grid)))
                    except Exception as exc:
                        row["errors"] += 1
                        errors.append({**identity, "rival": name, "error": str(exc)})
                        continue
                    row["draws_scored"] += 1
                    if prediction != expected:
                        row["refutations"] += 1
                        if row["first_witness_sha256"] is None:
                            row["first_witness_sha256"] = sha
                            witnesses.setdefault(sha, {**identity, "input": grid,
                                "python_mirror_output": expected, "rivals": []})["rivals"].append(name)
    gaps = []
    for name, rival in scored.items():
        for band, row in rival["by_band"].items():
            row["status"] = "observed_refutation_python_mirror" if row["refutations"] else "unknown_gap"
            if rival["canonical_fit"] is True and not row["refutations"]:
                gaps.append({"rival": name, "difficulty": band, "status": "unknown_gap"})
    authority = {"status": "not_requested", "note": "All production counts compare to a Python mirror, not executed Racket labels."}
    if args.verify_racket:
        if not (root / "catalog/puzzles.jsonl").is_file():
            authority = {"status": "skipped_unknown", "reason": "Copied runtime has no public Catalog library; no libraries fetched."}
        elif witnesses:
            try:
                from arcpuzzles import Catalog
                ordered = list(witnesses)
                applied = Catalog(root).apply(TASK_ID, [witnesses[sha]["input"] for sha in ordered], timeout=args.racket_timeout)
                agreement = True
                for sha, result in zip(ordered, applied["results"], strict=True):
                    witness = witnesses[sha]
                    witness["racket_result"] = result
                    witness["racket_matches_python_mirror"] = result["output"] == witness["python_mirror_output"]
                    agreement &= witness["racket_matches_python_mirror"]
                authority = {"status": "selected_witnesses_executed" if agreement else "mirror_disagreement",
                             "apply_receipt": {key: value for key, value in applied.items() if key != "results"}}
                if not agreement:
                    errors.append("Selected Racket witness labels disagree with Python mirror")
            except Exception as exc:
                authority = {"status": "execution_error", "error": str(exc)}
                errors.append(f"Racket verification: {exc}")
        else:
            authority = {"status": "no_observed_witnesses", "note": "No inputs executed; production support remains unknown."}
    if file_hash(source) != source_hash:
        errors.append("Generator source changed during probe; rerun on stable bytes")
    report = {"schema": "yellow-ring-predicate-witness-probe-v1", "task_id": TASK_ID,
              "source": {"generator_path": str(source), "generator_sha256": source_hash,
                         "probe_sha256": file_hash(Path(__file__)), "root": str(root),
                         "canonical_path": str(canonical_path(root)), "canonical_pairs_sha256": digest(pairs)},
              "settings": {"seeds": args.seeds, "bands": args.bands, "sample_start": args.sample_start,
                           "sample_stop_exclusive": args.sample_stop, "require_observed": args.require_observed,
                           "verify_racket": args.verify_racket, "racket_timeout": args.racket_timeout},
              "canonical_labeled_pairs": len(pairs), "python_mirror_matches_canonical_labels": mirror_matches,
              "rivals": scored, "draws": draws, "first_witnesses": witnesses, "required_witness_gaps": gaps,
              "authority": authority, "errors": errors,
              "status": "error" if errors else "unknown_gaps" if gaps else "finite_witness_support_observed",
              "limits": "Finite samples and named rivals only; gaps may reflect rare support or an intentional curriculum. Witness counts use the independent Python mirror; only retained racket_result labels were executed. No universal proof, approval, lesson identifiability claim, or training admission."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(args.out), "status": report["status"], "draws": len(draws),
                      "required_gaps": len(gaps), "retained_witnesses": len(witnesses), "authority": authority["status"]}))
    return 2 if errors else 1 if args.require_observed and gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())

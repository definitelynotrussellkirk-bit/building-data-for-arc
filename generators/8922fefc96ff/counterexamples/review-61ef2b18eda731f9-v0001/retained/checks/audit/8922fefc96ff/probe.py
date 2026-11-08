#!/usr/bin/env python3
"""Reproduce the occupied-span shortcut for audit target 8922fefc96ff."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("audit_generator_8922", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_mirror(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        hits = [c for c, value in enumerate(row) if value == 7]
        if len(hits) == 2 and all(row[c] == 0 for c in range(hits[0] + 1, hits[1])):
            for c in range(hits[0], hits[1] + 1):
                out[r][c] = 7
    return out


def unconditional_two_endpoint_rival(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        hits = [c for c, value in enumerate(row) if value == 7]
        if len(hits) == 2:
            for c in range(hits[0], hits[1] + 1):
                out[r][c] = 7
    return out


def blocked_rows(grid):
    rows = []
    for r, row in enumerate(grid):
        hits = [c for c, value in enumerate(row) if value == 7]
        if len(hits) == 2 and any(row[c] != 0 for c in range(hits[0] + 1, hits[1])):
            rows.append({
                "row": r,
                "endpoints": hits,
                "interior": row[hits[0] + 1:hits[1]],
            })
    return rows


def grid_hash(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def differing_cells(a, b):
    if len(a) != len(b) or any(len(x) != len(y) for x, y in zip(a, b)):
        return None
    return sum(x != y for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--per-band", type=int, default=300)
    args = parser.parse_args()
    root = args.root.resolve()
    out_dir = Path(__file__).resolve().parent
    generator_path = root / "repo/generators/8922fefc96ff/generator.py"
    gen = load_module(generator_path)
    episode = json.loads((out_dir / "episode.jsonl").read_text().splitlines()[0])

    exact_pairs = episode["train"] + episode["test"]
    exact = []
    for i, pair in enumerate(exact_pairs):
        grid = pair["input"]
        canonical = canonical_mirror(grid)
        rival = unconditional_two_endpoint_rival(grid)
        if canonical != pair["output"]:
            raise AssertionError(f"Python canonical mirror mismatch at pair {i}")
        exact.append({
            "split": "train" if i < len(episode["train"]) else "test",
            "pair_index": i if i < len(episode["train"]) else i - len(episode["train"]),
            "sample_index": episode["sample_indices"][i],
            "self_check": gen.self_check(grid, difficulty="hard"),
            "blocked_rows": blocked_rows(grid),
            "input_sha256": grid_hash(grid),
            "actual_output_sha256": grid_hash(pair["output"]),
            "rival_output_sha256": grid_hash(rival),
            "rival_matches_actual": rival == pair["output"],
            "differing_cells": differing_cells(rival, pair["output"]),
        })
    if not all(row["rival_matches_actual"] for row in exact[:4]):
        raise AssertionError("occupied-span rival must fit all four retained demonstrations")
    if exact[4]["rival_matches_actual"]:
        raise AssertionError("occupied-span rival must fail the retained query")
    if any(row["self_check"] for row in exact):
        raise AssertionError("retained inputs must pass self_check")

    query_grid = episode["test"][0]["input"]
    (out_dir / "input.json").write_text(json.dumps(query_grid, indent=2) + "\n")
    (out_dir / "rival-output.json").write_text(
        json.dumps(unconditional_two_endpoint_rival(query_grid), indent=2) + "\n"
    )

    degenerate = gen.generate(0, 0, difficulty="medium", texture="span_already_filled")
    degenerate_check = {
        "override": {"texture": "span_already_filled"},
        "self_check": gen.self_check(degenerate, difficulty="medium"),
        "blocked_rows": blocked_rows(degenerate),
        "canonical_and_rival_differ": canonical_mirror(degenerate) != unconditional_two_endpoint_rival(degenerate),
        "input_sha256": grid_hash(degenerate),
    }
    if degenerate_check["self_check"] or not degenerate_check["canonical_and_rival_differ"]:
        raise AssertionError("declared occupied-span texture must be an accepted witness")

    bands = {}
    total_survivors = 0
    total_wrong_queries = 0
    total_blocked_pairs = 0
    for band in ("easy", "medium", "hard"):
        survivors = wrong_queries = equivalent_queries = blocked_pairs = 0
        blocked_row_counts = Counter()
        for seed in range(args.per_band):
            rows = []
            for sample_index in range(5):
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    raise AssertionError((band, seed, sample_index, errors))
                blocked = blocked_rows(grid)
                blocked_pairs += bool(blocked)
                blocked_row_counts[len(blocked)] += 1
                actual = canonical_mirror(grid)
                rival = unconditional_two_endpoint_rival(grid)
                rows.append(actual == rival)
            demos_fit = all(rows[:4])
            if demos_fit:
                survivors += 1
                if rows[4]:
                    equivalent_queries += 1
                else:
                    wrong_queries += 1
        bands[band] = {
            "lessons": args.per_band,
            "demonstrations_per_lesson": 4,
            "queries_per_lesson": 1,
            "pair_draws": args.per_band * 5,
            "pairs_with_blocked_two-endpoint_rows": blocked_pairs,
            "blocked_row_count_histogram": dict(sorted(blocked_row_counts.items())),
            "rival_survives_all_demonstrations": survivors,
            "surviving_rival_wrong_on_query": wrong_queries,
            "surviving_rival_equivalent_on_query": equivalent_queries,
        }
        total_survivors += survivors
        total_wrong_queries += wrong_queries
        total_blocked_pairs += blocked_pairs

    report = {
        "schema": "arc-audit-occupied-span-shortcut-v1",
        "task_id": "8922fefc96ff",
        "finding": (
            "The plausible rival 'fill every row containing exactly two orange cells' "
            "fits ordinary easy and medium output support because those bands never emit "
            "an occupied interior. Hard sampling can emit the decisive branch, but it is "
            "not lesson-scheduled, so four demonstrations can all miss it before a query uses it."
        ),
        "generator": {
            "version": getattr(gen, "VERSION", None),
            "sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
            "declared_rule_hash": getattr(gen, "RULE_HASH", None),
            "examples_needed": getattr(gen, "EXAMPLES_NEEDED", None),
        },
        "retained_production_lesson": {
            "generation": {
                "seed": episode["seed"],
                "difficulty": episode["provenance"]["difficulty"],
                "sample_indices": episode["sample_indices"],
                "overrides": episode["provenance"]["overrides"],
                "train": len(episode["train"]),
                "test": len(episode["test"]),
            },
            "pair_checks": exact,
            "rival_fits_demos": True,
            "rival_fails_query": True,
            "lesson_check": episode["lesson_check"],
            "executed_rule_hash": episode["executed_rule_hash"],
        },
        "declared_texture_witness": degenerate_check,
        "diagnostic_census": {
            "label_source": "independent Python transcription of the canonical row predicate; exact retained lesson is separately Racket-labelled",
            "per_band": args.per_band,
            "total_lessons": args.per_band * 3,
            "total_pair_draws": args.per_band * 3 * 5,
            "pairs_with_blocked_two_endpoint_rows": total_blocked_pairs,
            "rival_survives_all_demonstrations": total_survivors,
            "surviving_rival_wrong_on_query": total_wrong_queries,
            "bands": bands,
        },
        "rival": {
            "name": "unconditional exactly-two-endpoint fill",
            "definition": (
                "For every row containing exactly two orange cells, paint the inclusive "
                "span orange without checking whether the interior is black."
            ),
        },
        "scope": (
            "The census is finite. The retained seed-22 hard episode was materialized "
            "by the supported generator with canonical Racket labels, and its query is "
            "independently checked with canonical Racket apply. No audit-target source was changed."
        ),
    }

    racket_path = out_dir / "racket.json"
    if racket_path.exists():
        receipt = json.loads(racket_path.read_text())
        results = receipt.get("results", [])
        if len(results) != 1 or results[0].get("error") is not None:
            raise AssertionError("unexpected Racket apply receipt")
        racket_output = results[0]["output"]
        expected = episode["test"][0]["output"]
        rival = unconditional_two_endpoint_rival(query_grid)
        if racket_output != expected:
            raise AssertionError("Racket output does not match generated query label")
        if racket_output == rival:
            raise AssertionError("Racket output unexpectedly matches rival")
        report["racket_verification"] = {
            "status": "passed",
            "command": [
                "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
                "8922fefc96ff", "--input", "../checks/audit/8922fefc96ff/input.json",
                "--out", "../checks/audit/8922fefc96ff/racket.json",
            ],
            "cwd": "packet_root",
            "exit_code": 0,
            "executed_rule_hash": receipt.get("executed_rule_hash"),
            "rule_hash_matches_catalog": receipt.get("rule_hash_matches_catalog"),
            "input_sha256": results[0].get("input_sha256"),
            "output_sha256": results[0].get("output_sha256"),
            "matches_generated_label": True,
            "differs_from_rival": True,
        }

    (out_dir / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "exact_demo_matches": [r["rival_matches_actual"] for r in exact[:4]],
        "query_matches": exact[4]["rival_matches_actual"],
        "query_blocked_rows": len(exact[4]["blocked_rows"]),
        "census_lessons": args.per_band * 3,
        "blocked_pairs": total_blocked_pairs,
        "survivors": total_survivors,
        "wrong_queries": total_wrong_queries,
        "racket_verified": "racket_verification" in report,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

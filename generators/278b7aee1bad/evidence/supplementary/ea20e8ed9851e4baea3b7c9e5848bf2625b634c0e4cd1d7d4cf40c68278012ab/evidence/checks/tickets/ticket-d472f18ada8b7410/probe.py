#!/usr/bin/env python3
"""One bounded canonical-fitting shortcut probe for generator 278b7aee1bad."""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import random

from arcpuzzles.catalog import Catalog
from arcpuzzles.runtime import apply_rule

TICKET_ID = "ticket-d472f18ada8b7410"
TASK_ID = "278b7aee1bad"
PROBE_SEED = "77028d173c2134edc6afd293b5202bc5ff623a6ebc7fa4b9b65438f5417ca868"
PINNED_GENERATOR_SHA256 = "bbc421bc61cbde919359452e033509ceb3ee81cd6788e3fb0be938f88507f35e"
PINNED_RULE_HASH = "99a84b189ddf"
ROOT = Path.cwd()
WORK = ROOT.parent
OUT = WORK / "checks" / "tickets" / TICKET_ID
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
SOLUTION_PATH = ROOT / "shared" / "data" / "base" / "solutions" / "banks" / "64addfdad75c" / "H152__278b7aee1bad.json"
MAX_CANDIDATES = 2048


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_sha(grid: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location("ticket_278_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def spans(grid: list[list[int]]) -> list[dict]:
    points: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                points[value].append((r, c))
    result = []
    for color in sorted(points):
        pts = points[color]
        if len(pts) != 2:
            raise ValueError(f"color {color} occurs {len(pts)} times")
        a, b = pts
        if a[0] == b[0]:
            orientation = "h"
            cells = [(a[0], c) for c in range(min(a[1], b[1]), max(a[1], b[1]) + 1)]
        elif a[1] == b[1]:
            orientation = "v"
            cells = [(r, a[1]) for r in range(min(a[0], b[0]), max(a[0], b[0]) + 1)]
        else:
            raise ValueError(f"color {color} endpoints are not aligned: {a}, {b}")
        result.append({"color": color, "a": list(a), "b": list(b), "orientation": orientation,
                       "cells": [list(cell) for cell in cells]})
    return result


def outputs(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]], list[dict]]:
    info = spans(grid)
    h, w = len(grid), len(grid[0])
    coverage: dict[tuple[int, int], list[str]] = defaultdict(list)
    for span in info:
        for cell in span["cells"]:
            coverage[tuple(cell)].append(span["orientation"])
    intended = [[0 for _ in range(w)] for _ in range(h)]
    rival = [[0 for _ in range(w)] for _ in range(h)]
    for (r, c), orientations in coverage.items():
        n = len(orientations)
        value = 8 if n == 2 else 9 if n >= 3 else 0
        intended[r][c] = value
        # Plausible shortcut: output only genuine horizontal/vertical crossing cells,
        # ignoring collinear overlaps between parallel spans.
        if "h" in orientations and "v" in orientations:
            rival[r][c] = value
    return intended, rival, info


def domain_facts(grid: list[list[int]], module) -> dict:
    info = spans(grid)
    orientations = Counter(span["orientation"] for span in info)
    intended, _, _ = outputs(grid)
    return {
        "shape": [len(grid), len(grid[0])],
        "colors": [span["color"] for span in info],
        "pair_count": len(info),
        "orientation_counts": dict(sorted(orientations.items())),
        "all_pairs_aligned": True,
        "mixed_orientations": set(orientations) == {"h", "v"},
        "has_overlap": any(value in {8, 9} for row in intended for value in row),
        "self_check_errors": module.self_check(grid),
    }


def canonical_fit(solution: dict) -> dict:
    pairs = list(solution["visible_context"]["train"])
    for item, expected in zip(solution["visible_context"]["test_inputs"], solution["verification"]["expected_test_outputs"], strict=True):
        pairs.append({"input": item["input"], "output": expected})
    rows = []
    for index, pair in enumerate(pairs):
        intended, rival, _ = outputs(pair["input"])
        rows.append({
            "index": index,
            "expected_sha256": grid_sha(pair["output"]),
            "independent_intended_matches_expected": intended == pair["output"],
            "rival_matches_expected": rival == pair["output"],
        })
    return {"pair_count": len(rows), "all_fit": all(row["rival_matches_expected"] for row in rows), "pairs": rows}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source_sha = sha(GENERATOR_PATH)
    if source_sha != PINNED_GENERATOR_SHA256:
        raise SystemExit(f"pinned generator changed: {source_sha}")
    module = load_generator()
    solution = json.loads(SOLUTION_PATH.read_text(encoding="utf-8"))
    canonical = canonical_fit(solution)
    if not canonical["all_fit"]:
        raise SystemExit("the proposed rival does not fit every canonical pair")

    rng = random.Random(int(PROBE_SEED, 16))
    difficulties = ("easy", "medium", "hard")
    witness = None
    for candidate_index in range(MAX_CANDIDATES):
        difficulty = difficulties[candidate_index % len(difficulties)]
        seed = rng.randrange(0, 2**31)
        sample_index = rng.randrange(0, 100_000)
        grid = module.generate(seed, sample_index, difficulty=difficulty)
        try:
            intended, rival, info = outputs(grid)
        except ValueError:
            continue
        facts = domain_facts(grid, module)
        disagreements = []
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if intended[r][c] != rival[r][c]:
                    disagreements.append({"row": r, "col": c, "intended": intended[r][c], "rival": rival[r][c]})
        if (not facts["self_check_errors"] and facts["mixed_orientations"] and facts["has_overlap"]
                and disagreements and any(item["intended"] in {8, 9} and item["rival"] == 0 for item in disagreements)):
            witness = {
                "candidate_index": candidate_index,
                "seed": seed,
                "sample_index": sample_index,
                "difficulty": difficulty,
                "overrides": {},
                "input": grid,
                "input_sha256": grid_sha(grid),
                "spans": info,
                "domain": facts,
                "independent_intended_output": intended,
                "rival_output": rival,
                "disagreements": disagreements,
            }
            break
    if witness is None:
        raise SystemExit(f"bounded unknown: no separating generated witness in {MAX_CANDIDATES} candidates")

    racket = apply_rule(Catalog(), TASK_ID, [witness["input"]], check_generator_domain=True, timeout=30)
    if racket["generator_sha256"] != PINNED_GENERATOR_SHA256:
        raise SystemExit("runtime generator hash drift")
    if racket["executed_rule_hash"] != PINNED_RULE_HASH or not racket["rule_hash_matches_catalog"]:
        raise SystemExit("runtime rule hash drift")
    result_row = racket["results"][0]
    if result_row["error"] is not None:
        raise SystemExit(f"Racket apply failed: {result_row['error']}")
    if result_row["output"] != witness["independent_intended_output"]:
        raise SystemExit("independent intended output disagrees with Racket")

    final_source_sha = sha(GENERATOR_PATH)
    if final_source_sha != source_sha:
        raise SystemExit("generator changed during probe")
    (OUT / "input.json").write_text(json.dumps({"input": witness["input"]}, indent=2) + "\n", encoding="utf-8")
    (OUT / "racket.json").write_text(json.dumps(racket, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = {
        "schema": "arcpuzzles-adversarial-witness-v1",
        "ticket_id": TICKET_ID,
        "consumer": "target_current_audit",
        "status": "completed",
        "source_binding": {
            "task_id": TASK_ID,
            "generator_path": f"generators/{TASK_ID}/generator.py",
            "generator_sha256": source_sha,
            "rule_hash": PINNED_RULE_HASH,
            "source_unchanged_at_finalize": True,
        },
        "probe": {
            "seed": PROBE_SEED,
            "max_candidates": MAX_CANDIDATES,
            "candidates_examined": witness["candidate_index"] + 1,
            "search_space": "ticket-seeded seed/sample_index pairs, difficulty cycling easy/medium/hard, no overrides",
        },
        "rival": {
            "name": "perpendicular_crossings_only",
            "definition": "Count span multiplicity only at cells covered by at least one horizontal and one vertical span; ignore overlap cells covered solely by parallel collinear spans.",
            "plausibility": "The visible canonical task presents outputs at horizontal/vertical intersections and contains no collinear parallel-overlap output corridor.",
            "canonical_fit": canonical,
        },
        "witness": witness,
        "racket": {
            "receipt_path": f"checks/tickets/{TICKET_ID}/racket.json",
            "executed_rule_hash": racket["executed_rule_hash"],
            "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
            "generator_sha256": racket["generator_sha256"],
            "output_sha256": result_row["output_sha256"],
            "generator_domain_errors": result_row.get("generator_domain_errors"),
            "matches_independent_intended": True,
            "differs_from_rival": result_row["output"] != witness["rival_output"],
        },
        "bounded_conclusion": "The shortcut fits all five canonical input/output pairs but is not universal for the pinned generator: one unchanged generated input lawfully contains a parallel-span overlap corridor that Racket labels and the rival omits. This probe does not estimate how often complete lessons expose the distinction and does not reclassify existing unresolved audits.",
        "limits": [
            "one ticket-seeded finite search and one Racket apply call",
            "no peer battery, lesson census, or frequency estimate",
            "no source edit or automatic safety/approval change",
        ],
    }
    (OUT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = f"""# Bounded adversarial witness for `{TASK_ID}`

Pinned generator SHA-256 `{source_sha}` and rule hash `{PINNED_RULE_HASH}` matched.

The plausible **perpendicular-crossings-only** rival fits all {canonical['pair_count']} canonical pairs. It treats overlap output as occurring only where a horizontal and vertical span cross, so it ignores cells covered by two parallel collinear spans.

The ticket-seeded search examined {witness['candidate_index'] + 1} unchanged generator draws and found a lawful separating input at difficulty `{witness['difficulty']}`, seed `{witness['seed']}`, sample index `{witness['sample_index']}`. `self_check` returned no errors. The canonical Racket output matched the independent span-count implementation and differed from the rival at {len(witness['disagreements'])} cell(s).

This is a completed source-bound witness, not a no-issue safety record: it proves the generator can emit a refutation, but does not measure whether assembled lessons reliably include one. Existing unresolved audits remain unresolved.
"""
    (OUT / "report.md").write_text(report, encoding="utf-8")
    print(json.dumps({"ticket_id": TICKET_ID, "status": "completed", "candidates_examined": witness["candidate_index"] + 1,
                      "witness_input_sha256": witness["input_sha256"], "disagreement_cells": len(witness["disagreements"])}, sort_keys=True))


if __name__ == "__main__":
    main()

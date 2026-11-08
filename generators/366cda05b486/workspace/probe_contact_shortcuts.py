#!/usr/bin/env python3
"""Bounded, source-bound shortcut probe for task 366cda05b486.

From any working directory, supply the checkout's shared/runtime on PYTHONPATH:
  TMPDIR=/path/to/tmp PYTHONPATH=/path/to/repo/shared/runtime \
    python /path/to/this/probe_contact_shortcuts.py --out /new/report.json
The packet's run_with_racket.py wrapper may also be used, but this probe itself
does not execute Racket. Outputs are the selected module's Python mirror; the
report records that limitation. Shared lesson-census remains the production
materialization/rotation tool. This script checks individual draws, one retained
four-pair counterexample, and three hand-made boundary witnesses only.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import types


TASK_ID = "366cda05b486"
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
EIGHT = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c)


def islands(grid, deltas=CARDINAL):
    """Independent foreground components: input colors do not split an island."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue, cells = deque([start]), {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in deltas:
                nxt = r + dr, c + dc
                if nxt in unseen:
                    unseen.remove(nxt)
                    cells.add(nxt)
                    queue.append(nxt)
        result.append(cells)
    return result


def crop(cells):
    if not cells:
        return [[0]]
    top, left = min(r for r, _ in cells), min(c for _, c in cells)
    bottom, right = max(r for r, _ in cells), max(c for _, c in cells)
    return [[8 if (r, c) in cells else 0 for c in range(left, right + 1)]
            for r in range(top, bottom + 1)]


def largest_island(grid):
    """Keep largest cardinal foreground island, breaking ties by top-left."""
    parts = islands(grid)
    return crop(min(parts, key=lambda cells: (-len(cells), min(cells))) if parts else set())


def noncyan_island(grid):
    """Keep largest island containing no cyan; top-left breaks ties.

    This rule ignores blue. It is intentionally total even when no candidate
    exists, so its disagreement remains visible on cyan-in-selected inputs.
    """
    candidates = [part for part in islands(grid) if all(grid[r][c] != 8 for r, c in part)]
    return crop(min(candidates, key=lambda cells: (-len(cells), min(cells)))
                if candidates else set())


def blue_eight_connected(grid):
    """Keep the 8-connected foreground island containing the first blue cell."""
    blue = next(((r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                 if value == 1), None)
    return crop(next((part for part in islands(grid, EIGHT) if blue in part), set()))


RIVALS = {"largest_island": largest_island, "noncyan_island": noncyan_island,
          "blue_eight_connected": blue_eight_connected}


def inspect(module, grid, **identity):
    reference = module.expected_output(grid)
    predictions = {name: rival(grid) for name, rival in RIVALS.items()}
    return {**identity, "input": grid, "python_mirror_output": reference,
            "self_check": module.self_check(grid),
            "predictions": predictions,
            "rival_matches": {name: output == reference for name, output in predictions.items()}}


def load_selected(path):
    # Execute the exact bytes hashed here, even if another worker edits the file
    # after this point. No source snapshot or source mutation is needed.
    source = path.read_bytes()
    module = types.ModuleType("contact_shortcuts_selected")
    module.__file__ = str(path)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module, hashlib.sha256(source).hexdigest()


def canonical_evidence(module, generator):
    from reviewer_support import canonical_pairs, find_root

    pairs = canonical_pairs(TASK_ID, root=find_root(generator))
    records = [inspect(module, pair["input"], split=pair["split"],
                       pair_index=pair["pair_index"]) for pair in pairs]
    for record, pair in zip(records, pairs):
        record["canonical_output"] = pair["output"]
        record["mirror_matches_canonical"] = record["python_mirror_output"] == pair["output"]
    train = [pair for pair in pairs if pair["split"] == "train"]
    boundaries = []
    if len(train) >= 2:
        for label, pair, old, new in (("cyan_in_selected", train[0], 3, 8),
                                      ("repeated_color_across_clusters", train[1], 7, 3)):
            grid = [[new if value == old else value for value in row] for row in pair["input"]]
            boundaries.append(inspect(module, grid, witness=label,
                                      construction=f"canonical train{pair['pair_index']} color{old}->{new}"))
    boundaries.append(inspect(module, [[1, 3, 0, 0, 0], [0, 3, 4, 0, 0], [0, 0, 0, 8, 7]],
                              witness="diagonal_only_cluster_contact"))
    return records, boundaries


def retained_lesson(module):
    pairs = []
    for index in (23, 24, 25, 26):
        try:
            pairs.append(inspect(module, module.generate(2, index, difficulty="easy"),
                                 seed=2, sample_index=index, difficulty="easy"))
        except Exception as exc:
            pairs.append({"seed": 2, "sample_index": index, "difficulty": "easy",
                          "error": f"{type(exc).__name__}: {exc}"})
    valid = all("rival_matches" in pair for pair in pairs)
    return {"name": "old_easy_largest_island_counterexample", "demonstration_indices": [23, 24, 25],
            "query_index": 26, "pairs": pairs,
            "largest_fits_demos_changes_query": valid and all(
                pair["rival_matches"]["largest_island"] for pair in pairs[:3])
                and not pairs[3]["rival_matches"]["largest_island"]}


def declared_contract(module, canonical, sampled):
    """Score the module's actual declarations separately from fixed probes."""
    namespaces, errors = {}, []
    for namespace in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        if not hasattr(module, namespace):
            namespaces[namespace] = {"status": "missing", "rivals": {}}
            continue
        declared = getattr(module, namespace)
        if not isinstance(declared, dict):
            errors.append(f"{namespace} must be a dict")
            namespaces[namespace] = {"status": "invalid", "rivals": {}}
            continue
        results = {}
        for name, rival in declared.items():
            if not isinstance(name, str) or not callable(rival):
                errors.append(f"{namespace} has an invalid name/callable declaration: {name!r}")
                continue
            result = {"canonical_matches": 0, "canonical_disagrees": 0,
                      "canonical_errors": [], "canonical_pair_count": len(canonical),
                      "sampled": {band: {"matches": 0, "disagrees": 0, "errors": []}
                                  for band in ("easy", "medium", "hard")},
                      "first_sampled_disagreement": None}
            for pair in canonical:
                try:
                    prediction = rival(pair["input"])
                    matches = prediction == pair["canonical_output"]
                    result["canonical_matches" if matches else "canonical_disagrees"] += 1
                    if not matches and "first_canonical_disagreement" not in result:
                        result["first_canonical_disagreement"] = {
                            "split": pair["split"], "pair_index": pair["pair_index"],
                            "input": pair["input"], "canonical_output": pair["canonical_output"],
                            "prediction": prediction}
                except Exception as exc:
                    result["canonical_errors"].append({"split": pair["split"],
                        "pair_index": pair["pair_index"], "error": f"{type(exc).__name__}: {exc}"})
            result["fits_all_canonical_pairs"] = (
                result["canonical_matches"] == len(canonical)
                and not result["canonical_errors"])
            if namespace == "CANONICAL_SHORTCUTS" and not result["fits_all_canonical_pairs"]:
                errors.append(f"claimed canonical shortcut {name} does not fit all {len(canonical)} pairs")
            for pair in sampled:
                band = result["sampled"][pair["difficulty"]]
                try:
                    prediction = rival(pair["input"])
                    matches = prediction == pair["python_mirror_output"]
                    band["matches" if matches else "disagrees"] += 1
                    if not matches and result["first_sampled_disagreement"] is None:
                        result["first_sampled_disagreement"] = {
                            "seed": pair["seed"], "sample_index": pair["sample_index"],
                            "difficulty": pair["difficulty"], "input": pair["input"],
                            "python_mirror_output": pair["python_mirror_output"], "prediction": prediction}
                except Exception as exc:
                    band["errors"].append({"seed": pair["seed"], "sample_index": pair["sample_index"],
                                           "error": f"{type(exc).__name__}: {exc}"})
                    errors.append(f"{namespace}.{name} raised on {pair['difficulty']} seed{pair['seed']}")
            results[name] = result
        namespaces[namespace] = {"status": "declared", "rivals": results}
    present = any(section["status"] == "declared" and section["rivals"]
                  for section in namespaces.values())
    return {"status": "failed" if errors else "scored" if present else "missing",
            "namespaces": namespaces, "errors": errors,
            "label_sources": {"canonical": "stored canonical pair labels",
                              "sampled": "selected generator.expected_output Python mirror"},
            "scope": "Actual selected module declarations, independent of this tool's fixed three rivals. Missing declarations are reported, never synthesized."}


def run(module, generator, source_hash, seeds):
    census, sampled = {}, []
    for band in ("easy", "medium", "hard"):
        counts = {name: {"matches": 0, "disagrees": 0} for name in RIVALS}
        first_disagreements, errors = {}, []
        for seed in range(seeds):
            try:
                grid = module.generate(seed, seed, difficulty=band)
                record = inspect(module, grid, seed=seed, sample_index=seed, difficulty=band)
                sampled.append(record)
            except Exception as exc:
                errors.append({"seed": seed, "sample_index": seed,
                               "error": f"{type(exc).__name__}: {exc}"})
                continue
            for name, matches in record["rival_matches"].items():
                counts[name]["matches" if matches else "disagrees"] += 1
                if not matches:
                    first_disagreements.setdefault(name, record)
        census[band] = {"requested_draws": seeds, "rival_counts": counts,
                        "first_disagreements": first_disagreements, "errors": errors}
    canonical, boundaries = canonical_evidence(module, generator)
    contract = declared_contract(module, canonical, sampled)
    errors = [f"{band}: generation/inspection error" for band, data in census.items() if data["errors"]]
    errors.extend(contract["errors"])
    if any(not pair["mirror_matches_canonical"] for pair in canonical):
        errors.append("Python mirror disagrees with stored canonical labels")
    return {"schema": "366cda05b486-contact-shortcut-probe-v1", "task_id": TASK_ID,
            "status": "failed" if errors else "passed", "errors": errors,
            "generator_path": str(generator), "generator_sha256": source_hash,
            "generator_version": getattr(module, "VERSION", None),
            "declared_rule_hash": getattr(module, "RULE_HASH", None),
            "label_source": "selected generator.expected_output Python mirror; no Racket execution",
            "rival_source": str(Path(__file__).resolve()),
            "rival_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "independent_probe_rivals": {"names": list(RIVALS),
                "source": "fixed independent color-blind implementations in this tool",
                "results_section": "census; canonical_pairs.rival_matches; boundary_witnesses",
                "scope": "These three probes do not substitute for the module's declared contract."},
            "declared_contract": contract,
            "scope": "Finite individual-draw sample, one retained direct four-pair lesson, canonical pairs and three boundary witnesses; does not prove universal support or lesson identifiability.",
            "census": census, "canonical_pairs": canonical,
            "retained_lesson": retained_lesson(module), "boundary_witnesses": boundaries}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=Path(__file__).resolve().parent.parent / "generator.py")
    parser.add_argument("--out", required=True, type=Path, help="new JSON file; existing outputs are refused")
    parser.add_argument("--seeds", type=int, default=30, help="draws per band, bounded to 1..100")
    args = parser.parse_args()
    if not 1 <= args.seeds <= 100:
        parser.error("--seeds must be within 1..100")
    if args.out.exists():
        parser.error("--out must name a new file")
    generator = args.generator.resolve()
    module, source_hash = load_selected(generator)
    report = run(module, generator, source_hash, args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"out": str(args.out.resolve()), "generator_sha256": source_hash,
                      "status": report["status"], "errors": report["errors"],
                      "declared_contract_status": report["declared_contract"]["status"],
                      "retained_lesson_ambiguous": report["retained_lesson"]["largest_fits_demos_changes_query"],
                      "census": {band: data["rival_counts"] for band, data in report["census"].items()}}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

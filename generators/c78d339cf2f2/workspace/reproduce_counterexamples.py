"""Authoring-only perimeter-rank witnesses; never import in the blind solve lane.

Run through WORK/run_with_racket.py with --out and optionally --witness-dir.
The selected Racket authority labels exactly two generated inputs. Canonical
comparisons use the five supplied labels and do not re-execute those inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve()
# Bootstrap only an ancestor's local helper; do not depend on caller cwd.
for parent in SCRIPT.parents:
    helper_root = next((p for p in (parent, parent / "shared/runtime")
                        if (p / "reviewer_support.py").is_file()), None)
    if helper_root is not None:
        sys.path.insert(0, str(helper_root))
        break
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "c78d339cf2f2"
ROOT = find_root(SCRIPT)
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))
RIVALS = ("area", "bbox_perimeter", "bbox_area", "row_major", "column_major",
          "descending", "reverse_ties")


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def json_sha(value):
    return sha_bytes(json.dumps(value, separators=(",", ":"), sort_keys=True).encode())


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def components(grid):
    """Independent row-major flood fill across every nonzero input color."""
    height, width = len(grid), len(grid[0])
    seen, bodies = set(), []
    for r in range(height):
        for c in range(width):
            if not grid[r][c] or (r, c) in seen:
                continue
            seen.add((r, c))
            queue, body = [(r, c)], {(r, c)}
            for rr, cc in queue:
                for dr, dc in DIRS:
                    point = rr + dr, cc + dc
                    if (0 <= point[0] < height and 0 <= point[1] < width
                            and grid[point[0]][point[1]] and point not in seen):
                        seen.add(point)
                        body.add(point)
                        queue.append(point)
            bodies.append(tuple(sorted(body)))
    return bodies


def measurements(body):
    cells = set(body)
    height = max(r for r, c in cells) - min(r for r, c in cells) + 1
    width = max(c for r, c in cells) - min(c for r, c in cells) + 1
    shared_edges = sum((r + dr, c + dc) in cells for r, c in cells
                       for dr, dc in ((1, 0), (0, 1)))
    return {"perimeter": 4 * len(cells) - 2 * shared_edges, "area": len(cells),
            "bbox_perimeter": 2 * (height + width), "bbox_area": height * width}


def prediction(grid, name="perimeter"):
    bodies = components(grid)
    assert len(bodies) == 3, "This task's witness inputs must have three components"
    facts = [measurements(body) for body in bodies]
    if name == "row_major":
        order = list(range(3))
    elif name == "column_major":
        order = sorted(range(3), key=lambda i: min((c, r) for r, c in bodies[i]))
    elif name == "descending":
        order = sorted(range(3), key=lambda i: -facts[i]["perimeter"])
    elif name == "reverse_ties":
        order = sorted(range(3), key=lambda i: (facts[i]["perimeter"], -i))
    else:
        order = sorted(range(3), key=lambda i: facts[i][name])
    output = [[0] * len(grid[0]) for _ in grid]
    for index, color in zip(order, (2, 3, 4), strict=True):
        for r, c in bodies[index]:
            output[r][c] = color
    return output


def compare(grid, output, module):
    assert prediction(grid) == output, "Independent edge metric disagrees with authority"
    result = {}
    for name in RIVALS:
        predicted = prediction(grid, name)
        assert module.SEMANTIC_RIVALS[name](grid) == predicted, name
        changes = [[r, c, color, predicted[r][c]] for r, row in enumerate(output)
                   for c, color in enumerate(row) if color != predicted[r][c]]
        result[name] = {"fits": not changes, "prediction_sha256": json_sha(predicted),
                        "changed_coordinates_r_c_authority_rival": changes}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--witness-dir", type=Path,
                        default=ROOT / "generators" / TASK / "counterexamples/generated_rank_witnesses")
    args = parser.parse_args()
    module, source, source_hash = load_selected_generator(TASK, root=ROOT)
    assert set(module.SEMANTIC_RIVALS) == set(RIVALS), "Update probe for a changed rival inventory"
    calls = [{"seed": 23, "sample_index": i, "difficulty": "medium", "overrides": {}}
             for i in (0, 1)]
    grids = [module.generate(23, i, difficulty="medium") for i in (0, 1)]
    provided = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(provided) == 5
    canonical = []
    for pair in provided:
        comparisons = compare(pair["input"], pair["output"], module)
        canonical.append({key: pair[key] for key in ("variant", "split", "pair_index")} |
                         {"input_sha256": json_sha(pair["input"]),
                          "provided_output_sha256": json_sha(pair["output"]), "rivals": comparisons})
    fits = {name: sum(pair["rivals"][name]["fits"] for pair in canonical) for name in RIVALS}
    assert {name for name, count in fits.items() if count == 5} == {"area", "bbox_perimeter"}

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles.catalog import Catalog
    authority = Catalog(ROOT).apply(TASK, grids, reference="canonical", timeout=90,
                                    check_generator_domain=True)
    assert authority["rule_hash_matches_catalog"] and authority["executed_rule_hash"] == module.RULE_HASH
    assert authority["generator_sha256"] == source_hash
    labeled = authority.pop("results")
    assert len(labeled) == 2 and all(item["output"] is not None for item in labeled)
    witnesses, references = [], []
    for index, (grid, labeled_pair) in enumerate(zip(grids, labeled, strict=True)):
        output = labeled_pair["output"]
        comparisons = compare(grid, output, module)
        assert all(not comparisons[name]["fits"] for name in RIVALS if name != "reverse_ties")
        assert comparisons["reverse_ties"]["fits"] == bool(index)
        assert not module.self_check(grid, difficulty="medium")
        mode = "tied" if index == 0 else "distinct"
        bodies = components(grid)
        assert len({measurements(body)["perimeter"] for body in bodies}) == (2 if index == 0 else 3)
        witness = {"schema": "arc-perimeter-rank-counterexample-v1", "task_id": TASK,
                   "authoring_only": True, "generate_call": calls[index], "profile": mode,
                   "generator_sha256": source_hash, "rule_hash": module.RULE_HASH,
                   "rule_text_sha256": authority["rule_text_sha256"], "input": grid, "output": output,
                   "components_row_major": [{"cells": body, **measurements(body)} for body in bodies],
                   "rivals": comparisons}
        path = args.witness_dir.resolve() / f"seed23_index{index}_{mode}.json"
        witnesses.append((path, witness))
        references.append({"path": str(path.relative_to(ROOT)), "profile": mode,
                           "rivals_refuted": [name for name in RIVALS if not comparisons[name]["fits"]]})
    assert sha_bytes(source.read_bytes()) == source_hash, "Selected source changed during the probe"
    for (path, witness), reference in zip(witnesses, references, strict=True):
        write_json(path, witness)
        reference["sha256"] = sha_bytes(path.read_bytes())
    report = {"schema": "arc-perimeter-counterexample-reproduction-v1", "task_id": TASK,
              "authoring_only": True, "execution": {"argv": sys.orig_argv, "cwd": os.getcwd(),
                  "python": sys.executable, "script_sha256": sha_bytes(SCRIPT.read_bytes())},
              "source": {"path": str(source.relative_to(ROOT)), "sha256": source_hash,
                  "version": module.VERSION, "rule_hash": module.RULE_HASH, "source_changed": False},
              "scope": {"generated_draws": 2, "real_racket_labels": 2,
                  "provided_canonical_labels_checked": 5, "independent_rivals": len(RIVALS)},
              "authority_receipt": authority, "witnesses": references,
              "canonical": {"ledger": str(canonical_path(ROOT).relative_to(ROOT)),
                  "population_sha256": json_sha(provided), "label_source": "provided canonical labels",
                  "rival_fit_counts_of_5": fits, "pairs": canonical}}
    write_json(args.out.resolve(), report)
    print(json.dumps({"source_sha256": source_hash, "rule_hash": module.RULE_HASH,
                      "scope": report["scope"], "canonical_fit_counts": fits,
                      "witnesses": references, "evidence": str(args.out.resolve())}, indent=2))


if __name__ == "__main__":
    main()

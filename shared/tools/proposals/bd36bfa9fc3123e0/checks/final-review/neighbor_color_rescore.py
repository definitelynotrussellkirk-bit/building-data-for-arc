#!/usr/bin/env python3
"""Rescore retained ARC census labels against the neighboring-color rival.

This does not import the generator, replay Racket, or create training labels.
The authoritative outputs are the saved census/canonical outputs. An independent
component graph is used only to predict the rival and cross-check those labels.
"""
import argparse
import hashlib
import json
from pathlib import Path


TASK = "9f05dcdedf35"
RULE_SOURCE_SHA256 = "85fa63b64c3c9990f028cd6895fcf1b7e168d83ca7c7d4291e8fb343dcc9493e"
CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def graph(grid):
    h, w = len(grid), len(grid[0])
    owner, colors, cells = {}, [], []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in owner:
                continue
            ident = len(colors)
            color = grid[r][c]
            colors.append(color)
            component = set()
            stack = [(r, c)]
            owner[r, c] = ident
            while stack:
                rr, cc = stack.pop()
                component.add((rr, cc))
                for dr, dc in CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in owner
                            and grid[nr][nc] == color):
                        owner[nr, nc] = ident
                        stack.append((nr, nc))
            cells.append(component)
    neighbors = [set() for _ in colors]
    for (r, c), ident in owner.items():
        for dr, dc in CARDINAL:
            other = owner.get((r + dr, c + dc))
            if other is not None and other != ident:
                neighbors[ident].add(other)
    return colors, cells, neighbors


def predict(grid, *, by_color):
    colors, cells, neighbors = graph(grid)
    out = [list(row) for row in grid]
    for ident, adjacent in enumerate(neighbors):
        degree = len({colors[n] for n in adjacent}) if by_color else len(adjacent)
        if degree == 1:
            for r, c in cells[ident]:
                out[r][c] = 8
    return out


def binding(data, raw, path):
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
            **{name: data[name] for name in (
                "task_id", "generator_sha256", "rule_source_sha256", "rule_callable_sha256",
                "controller_sha256", "runtime_manifest_sha256")}}


def canonical_fit(path):
    with path.open() as stream:
        for raw in stream:
            if TASK not in raw:
                continue
            row = json.loads(raw)
            if row.get("task_id") == TASK:
                break
        else:
            raise ValueError("selected canonical task was not found")
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    pairs = [("train", i, pair) for i, pair in enumerate(row["train"])]
    pairs += [("test", i, pair) for i, pair in enumerate(tests)]
    fit = []
    for split, index, pair in pairs:
        assert predict(pair["input"], by_color=False) == pair["output"]
        fit.append({"split": split, "pair_index": index,
                    "input_sha256": digest(pair["input"]),
                    "output_sha256": digest(pair["output"]),
                    "rival_matches": predict(pair["input"], by_color=True) == pair["output"]})
    return {"source_path": str(path), "selected_row_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "pairs": len(fit), "fits": sum(item["rival_matches"] for item in fit), "pair_results": fit}


def rescore(path, expected_generator):
    raw = path.read_bytes()
    data = json.loads(raw)
    assert data["schema"] == "arcpuzzles-lesson-census-v1"
    assert data["task_id"] == TASK
    assert data["generator_sha256"] == expected_generator
    assert data["rule_source_sha256"] == RULE_SOURCE_SHA256
    assert data["execution"]["exit_code"] == 0 and data["execution"]["timed_out"] is False
    assert data["errors"] == [] and data["sampler"]["n_queries"] == 1
    source = binding(data, raw, path)
    counts = {band: {"lessons": 0, "pairs": 0, "all_four_fit": 0,
                     "production_ambiguous": 0, "rotations": 0, "rotations_ambiguous": 0,
                     "rival_mismatching_pairs": 0} for band in data["sampler"]["bands"]}
    production, rotations = [], []
    first_production = first_rotation = None
    for row in data["lessons"]:
        assert digest(row["instance"]) == row["instance_sha256"]
        pairs = row["instance"]["train"] + row["instance"]["test"]
        predictions = [predict(pair["input"], by_color=True) for pair in pairs]
        mismatches = [prediction != pair["output"] for pair, prediction in zip(pairs, predictions, strict=True)]
        for pair in pairs:
            assert predict(pair["input"], by_color=False) == pair["output"]
        counts[row["band"]]["lessons"] += 1
        counts[row["band"]]["pairs"] += len(pairs)
        counts[row["band"]]["all_four_fit"] += int(not any(mismatches))
        counts[row["band"]]["rival_mismatching_pairs"] += sum(mismatches)
        observations = [("production", len(pairs) - 1, list(range(len(pairs) - 1)))]
        observations += [("rotation", item["query_index"], item["train_indices"]) for item in row["rotations"]]
        for kind, query, train in observations:
            if kind == "rotation":
                counts[row["band"]]["rotations"] += 1
            if any(mismatches[index] for index in train) or not mismatches[query]:
                continue
            actual = pairs[query]["output"]
            prediction = predictions[query]
            record = {"kind": kind, "band": row["band"], "lesson_index": row["index"],
                      "seed": row["seed"], "sample_index": row["sample_index"],
                      "instance_sha256": row["instance_sha256"], "query_index": query,
                      "train_indices": train, "pair_mismatches": mismatches,
                      "query_input_sha256": digest(pairs[query]["input"]),
                      "query_reference_output_sha256": digest(actual),
                      "query_rival_output_sha256": digest(prediction),
                      "differing_coordinates": [[r, c] for r, line in enumerate(actual)
                                                for c, value in enumerate(line) if value != prediction[r][c]]}
            witness = {"schema": "arc-neighbor-color-teaching-counterexample-v1", "source": source,
                       "rival": "Recolor each monochrome 4-connected component iff its cardinal neighbors use exactly one distinct color.",
                       "labels": "Retained actual Racket census labels; Racket was not rerun by this rescore.",
                       **record, "instance": row["instance"], "rival_outputs": predictions}
            if kind == "production":
                counts[row["band"]]["production_ambiguous"] += 1
                production.append(record)
                first_production = first_production or witness
            else:
                counts[row["band"]]["rotations_ambiguous"] += 1
                rotations.append(record)
                first_rotation = first_rotation or witness
    totals = {key: sum(row[key] for row in counts.values()) for key in next(iter(counts.values()))}
    assert totals["lessons"] == data["summary"]["materialized"]
    assert totals["rotations"] == data["summary"]["rotations"]
    return {"source": source, "per_band": counts, "totals": totals,
            "production_ambiguities": production, "rotation_ambiguities": rotations}, first_production, first_rotation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--expected-generator-sha256", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--census", default="checks/lesson-census-final.json")
    parser.add_argument("--schedule", default="checks/schedule-census-final.json")
    args = parser.parse_args()
    root = args.work_root.resolve()
    main_result, production, rotation = rescore(root / args.census, args.expected_generator_sha256)
    schedule, _, _ = rescore(root / args.schedule, args.expected_generator_sha256)
    report = {"schema": "arc-neighbor-color-final-review-v1", "status": "teaching_defect" if main_result["totals"]["production_ambiguous"] or main_result["totals"]["rotations_ambiguous"] else "no_ambiguity_found",
              "task_id": TASK, "generator_sha256": args.expected_generator_sha256,
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "scope": "One undeclared rival, finite retained labels, no generator or Racket replay; no universal induction claim.",
              "canonical_fit": canonical_fit(root / "repo/shared/data/canonical/puzzles.jsonl"),
              "production_census": main_result, "fixed_seed_schedule_census": schedule}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    files = {"rescore.json": report}
    if production is not None:
        files["first-production-counterexample.json"] = production
    if rotation is not None:
        files["first-rotation-counterexample.json"] = rotation
    for name, value in files.items():
        with (args.out_dir / name).open("x") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
    print(json.dumps({"status": report["status"], "canonical_fits": report["canonical_fit"]["fits"],
                      "canonical_pairs": report["canonical_fit"]["pairs"],
                      "production_census": main_result["totals"], "schedule_census": schedule["totals"],
                      "out_dir": str(args.out_dir)}, sort_keys=True))


if __name__ == "__main__":
    main()

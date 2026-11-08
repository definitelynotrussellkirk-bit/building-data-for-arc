"""Bounded authoring diagnostics for the selected generator and declared rivals.

Run from repo with PYTHONPATH=src:shared/runtime, or through run_with_racket.py.
Generated labels use the Python mirror only. This does not execute Racket or
establish correctness for an unknown query. Canonical labels are authoring data.
The four-pair windows start at every index 0..N-1, without wrapping the finite
sample corpus; every position is held out as the query in turn.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "d2b3402dde86"
BANDS = ("easy", "medium", "hard")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_selected():
    root = find_root(__file__)
    paths = (root / "generators" / TASK_ID / "generator.py",
             root / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py")
    path = next((p for p in paths if p.is_file()), None)
    if path is None:
        raise FileNotFoundError("selected task generator not found")
    spec = importlib.util.spec_from_file_location("selected_distribution_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return root, path, module


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def shape(grid):
    return f"{len(grid)}x{len(grid[0])}"


def observable_box(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    top, left = min(r for r, _ in cells), min(c for _, c in cells)
    bottom, right = max(r for r, _ in cells), max(c for _, c in cells)
    return top, left, bottom - top + 1, right - left + 1


def evaluate(rival, grid):
    try:
        return rival(grid), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def fit_report(rivals, pairs):
    report = {}
    for name, rival in sorted(rivals.items()):
        predictions = [evaluate(rival, pair["input"]) for pair in pairs]
        all_indices = [i for i, pair in enumerate(pairs)]
        train_indices = [i for i, pair in enumerate(pairs) if pair["split"] == "train"]
        def fits(indices):
            return bool(indices) and all(predictions[i][1] is None and
                                         predictions[i][0] == pairs[i]["output"] for i in indices)
        report[name] = {
            "all_pair_fit": fits(all_indices), "train_demo_fit": fits(train_indices),
            "matching_pairs": sum(error is None and prediction == pair["output"]
                                  for (prediction, error), pair in zip(predictions, pairs)),
            "errors": [{"pair_index": i, "error": error}
                       for i, (_, error) in enumerate(predictions) if error],
        }
    return report


def probe(samples_per_band, window_starts, seed):
    root, path, generator = load_selected()
    ledger = canonical_path(root)
    canonical = canonical_pairs(TASK_ID, root=root)
    declarations = {"canonical_shortcuts": generator.CANONICAL_SHORTCUTS,
                    "lesson_competitors": generator.LESSON_COMPETITORS}
    fit = {group: fit_report(rivals, canonical) for group, rivals in declarations.items()}
    rule_rows = [json.loads(line) for line in ledger.read_text().splitlines()
                 if line.strip() and json.loads(line).get("task_id") == TASK_ID]
    hashes = {hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
              for row in rule_rows}
    failures = []
    failure_count = 0
    def fail(message):
        nonlocal failure_count
        failure_count += 1
        if len(failures) < 100:
            failures.append(message)
    if hashes != {generator.RULE_HASH}:
        fail("declared generator RULE_HASH does not match selected canonical rule")
    mirror_matches = 0
    for index, pair in enumerate(canonical):
        prediction, error = evaluate(generator.rule_mirror, pair["input"])
        if error or prediction != pair["output"]:
            fail(f"canonical mirror disagreement at pair {index}: {error or 'different output'}")
        else:
            mirror_matches += 1
    report = {
        "schema": "d2b3402dde86-distribution-probe-v1", "task_id": TASK_ID,
        "label_basis": "python_rule_mirror_diagnostic_only",
        "limitations": ["No Racket execution in this probe.",
                        "Named rivals only; does not certify all possible hypotheses.",
                        "All canonical outputs are authoring data; no unknown query is solved."],
        "source": {"generator_path": path.relative_to(root).as_posix(),
                   "generator_sha256": digest(path), "rule_hash": generator.RULE_HASH,
                   "canonical_rule_hashes": sorted(hashes), "canonical_sha256": digest(ledger),
                   "canonical_rule_exact_sha256": sorted({hashlib.sha256(
                       row["program_solution"].encode()).hexdigest() for row in rule_rows})},
        "parameters": {"seed": seed, "samples_per_band": samples_per_band,
                       "window_starts": window_starts, "demonstration_count": 3,
                       "query_policy": "all four holdouts of each consecutive four-pair window"},
        "declarations": {group: sorted(rivals) for group, rivals in declarations.items()},
        "canonical": {"all_pair_count": len(canonical),
                      "train_demo_count": sum(p["split"] == "train" for p in canonical),
                      "mirror_matching_pairs": mirror_matches, "rival_fit": fit},
        "bands": {}, "windows": {}, "witnesses": {},
    }
    witness_candidates = {f"{group}/{name}": (rival, None)
                          for group, rivals in declarations.items() for name, rival in rivals.items()
                          if fit[group][name]["all_pair_fit"]}
    all_accepted = set()
    for band in BANDS:
        cache = []
        for index in range(max(samples_per_band, window_starts + 3)):
            try:
                grid = generator.generate(seed, index, difficulty=band)
                errors = generator.self_check(grid, difficulty=band)
                if errors:
                    raise ValueError("; ".join(errors))
                answer = generator.rule_mirror(grid)
                cache.append({"input": grid, "output": answer})
                all_accepted.add(frozen(grid))
                for key, (rival, best) in list(witness_candidates.items()):
                    prediction, error = evaluate(rival, grid)
                    if error is None and prediction != answer:
                        rank = (len(grid) * len(grid[0]), sum(bool(v) for row in grid for v in row),
                                band, index)
                        if best is None or rank < best[0]:
                            witness_candidates[key] = (rival, (rank, {
                                "band": band, "sample_index": index, "seed": seed,
                                "input": grid, "mirror_output": answer, "rival_output": prediction,
                                "label_basis": "python_rule_mirror_diagnostic_only"}))
            except Exception as exc:
                cache.append(None)
                fail(f"{band} sample {index}: {type(exc).__name__}: {exc}")
        inputs, outputs, extents, positions, palettes, palette_sizes = (Counter() for _ in range(6))
        accepted = strict = blank_top = blank_left = 0
        unique = set()
        for pair in cache[:samples_per_band]:
            if pair is None:
                continue
            grid, answer = pair["input"], pair["output"]
            accepted += 1
            unique.add(frozen(grid))
            inputs[shape(grid)] += 1
            outputs[shape(answer)] += 1
            top, left, height, width = observable_box(grid)
            extents[f"{height}x{width}"] += 1
            positions[f"r{top}_c{left}"] += 1
            palette = sorted({value for row in grid for value in row if value})
            palettes[",".join(map(str, palette))] += 1
            palette_sizes[str(len(palette))] += 1
            strict += not generator.strict_canonical_like(grid)
            blank_top += not any(answer[0])
            blank_left += not any(row[0] for row in answer)
        report["bands"][band] = {
            "sample_indices": [0, samples_per_band - 1], "draw_count": samples_per_band,
            "accepted_count": accepted, "unique_accepted_inputs": len(unique),
            "input_shapes": dict(sorted(inputs.items())), "output_shapes": dict(sorted(outputs.items())),
            "observable_extents": dict(sorted(extents.items())),
            "observable_positions": dict(sorted(positions.items())),
            "foreground_palettes": dict(sorted(palettes.items())),
            "foreground_palette_sizes": dict(sorted(palette_sizes.items())),
            "strict_count": strict, "strict_fraction": strict / accepted if accepted else None,
            "blank_output_top_count": blank_top, "blank_output_left_count": blank_left,
        }
        holdouts = []
        ambiguity_count = window_errors = 0
        predictions = {name: [evaluate(rival, pair["input"]) if pair else (None, "input rejected")
                              for pair in cache]
                       for name, rival in generator.LESSON_COMPETITORS.items()}
        for start in range(window_starts):
            indices = list(range(start, start + 4))
            for query_position in range(4):
                query_index = indices[query_position]
                demo_indices = [index for index in indices if index != query_index]
                survivors, ambiguities, errors = [], [], []
                if any(cache[index] is None for index in indices):
                    errors.append("window contains rejected input")
                else:
                    for name in sorted(predictions):
                        relevant_errors = [predictions[name][index][1] for index in indices
                                           if predictions[name][index][1]]
                        if relevant_errors:
                            errors.append(f"{name}: {relevant_errors[0]}")
                            continue
                        if all(predictions[name][index][0] == cache[index]["output"]
                               for index in demo_indices):
                            survivors.append(name)
                            if predictions[name][query_index][0] != cache[query_index]["output"]:
                                ambiguities.append(name)
                    try:
                        contract_errors = generator.lesson_identifiable(
                            [cache[index] for index in demo_indices], cache[query_index])
                        errors.extend(contract_errors)
                    except Exception as exc:
                        errors.append(f"lesson_identifiable: {type(exc).__name__}: {exc}")
                if ambiguities or errors:
                    fail(f"{band} start {start} query position {query_position}: "
                         f"ambiguities={ambiguities}; errors={errors}")
                ambiguity_count += bool(ambiguities)
                window_errors += bool(errors)
                holdouts.append({"start": start, "query_position": query_position,
                                 "query_sample_index": query_index, "demo_sample_indices": demo_indices,
                                 "surviving_rivals": survivors, "differing_query_rivals": ambiguities,
                                 "errors": errors})
        report["windows"][band] = {"starts": list(range(window_starts)),
            "window_count": window_starts, "holdout_count": len(holdouts),
            "ambiguity_count": ambiguity_count, "error_holdout_count": window_errors,
            "production_holdout_count": window_starts,
            "production_ambiguity_count": sum(bool(h["differing_query_rivals"]) for h in holdouts
                                              if h["query_position"] == 3),
            "holdouts": holdouts}
    report["witnesses"] = {key: best[1] if best else None
                           for key, (_, best) in sorted(witness_candidates.items())}
    report["witness_policy"] = "smallest observed accepted canvas, then nonzero count, band and index"
    report["accepted_unique_inputs_across_distribution_and_window_draws"] = len(all_accepted)
    report["total_draws_including_window_support"] = 3 * max(samples_per_band, window_starts + 3)
    report["failures"] = failures
    report["failure_count"] = failure_count
    report["failures_truncated"] = failure_count > len(failures)
    report["status"] = "FAIL" if failure_count else "PASS"
    return report


def bounded_count(maximum):
    def parse(value):
        try:
            number = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"count must be between 1 and {maximum}") from exc
        if not 1 <= number <= maximum:
            raise argparse.ArgumentTypeError(f"count must be between 1 and {maximum}")
        return number
    return parse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-band", type=bounded_count(2048), default=128)
    parser.add_argument("--window-starts", type=bounded_count(256), default=40)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    report = probe(args.samples_per_band, args.window_starts, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.out.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError:
        parser.error(f"output already exists: {args.out}")
    print(f"{report['status']}: {report['failure_count']} failure(s); {args.out}")
    return int(report["status"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())

"""Find and Racket-verify a bounded numeric-color-rank teaching counterexample."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

TASK_ID = "ffd3a33c5687"


def sha(value: bytes | str) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def grid_hash(grid) -> str:
    return sha(json.dumps(grid, separators=(",", ":")))


def numeric_rank_output(grid, direction):
    """Complete mirror pairs using min/max nonzero color; preserve the axis."""
    out = copy.deepcopy(grid)
    choose = min if direction == "minimum" else max
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            occupied = [value for value in (row[left_col], row[right_col]) if value]
            value = choose(occupied) if occupied else 0
            out[row_index][left_col] = out[row_index][right_col] = value
    return out


def conflicts(grid):
    width = len(grid[0])
    return [{"row": r, "left_col": c, "right_col": width - 1 - c,
             "left_color": row[c], "right_color": row[width - 1 - c]}
            for r, row in enumerate(grid) for c in range(width // 2)
            if row[c] and row[width - 1 - c] and row[c] != row[width - 1 - c]]


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def bootstrap(repo):
    sys.path.insert(0, str(repo / "shared/runtime"))
    sys.path.insert(0, str(repo / "src"))
    from reviewer_support import canonical_pairs, load_selected_generator
    mod, source, source_hash = load_selected_generator(TASK_ID, root=repo)
    rows = [json.loads(line) for line in (repo / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
            if json.loads(line).get("task_id") == TASK_ID]
    rules = {row["program_solution"] for row in rows}
    assert len(rules) == 1
    rule = rules.pop()
    return mod, source, source_hash, rule, canonical_pairs(TASK_ID, root=repo, labeled_only=True)


def search(repo, outdir):
    mod, source, source_hash, rule, canonical = bootstrap(repo)
    directions = ["minimum", "maximum"]
    assert all(all(numeric_rank_output(pair["input"], d) == pair["output"] for pair in canonical) for d in directions)
    cache, examined = {}, 0
    candidate = None
    for seed in range(20):
        for band in ("easy", "medium", "hard"):
            for start in range(5):
                examined += 1
                pairs = []
                for index in range(start, start + 4):
                    key = seed, band, index
                    if key not in cache:
                        grid = mod.generate(seed, index, difficulty=band)
                        assert mod.self_check(grid) == []
                        cache[key] = {"input": grid, "output": mod.rule_mirror(grid)}
                    pairs.append(cache[key])
                for direction in directions:
                    fits = [numeric_rank_output(pair["input"], direction) == pair["output"] for pair in pairs]
                    if fits == [True, True, True, False]:
                        candidate = {"seed": seed, "difficulty": band, "sample_indices": list(range(start, start + 4)),
                                     "overrides": {}, "rival_direction": direction, "pairs": pairs,
                                     "conflicts": [conflicts(pair["input"]) for pair in pairs],
                                     "mirror_agreement": fits,
                                     "declared_lesson_hook_reasons": mod.lesson_identifiable(pairs[:3], pairs[3])}
                        break
                if candidate:
                    break
            if candidate:
                break
        if candidate:
            break
    assert sha(source.read_bytes()) == source_hash
    report = {"task_id": TASK_ID, "generator_sha256": source_hash, "rule_text_sha256": sha(rule),
              "rule_hash": sha(" ".join(rule.split()))[:12], "candidate_search": {
                  "seed_bounds": [0, 19], "bands": ["easy", "medium", "hard"], "start_bounds": [0, 4],
                  "examined_lesson_candidates": examined, "generated_positions": len(cache),
                  "stopping_policy": "Stop at the first min/max rival fitting three demos but changing query"},
              "candidate": candidate, "canonical_pairs": canonical,
              "declared_rivals": list(mod.LESSON_COMPETITORS),
              "label_scope": "Candidate search uses Python mirror; verify phase requires actual public Racket execution",
              "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()), "exit_code": 0 if candidate else 1}
    save(outdir / "candidate.json", report)
    if candidate is None:
        raise SystemExit("No witness in the bounded search")
    save(outdir / "input.json", {"inputs": [pair["input"] for pair in candidate["pairs"] + canonical]})
    (outdir / "canonical-rule.rkt").write_text(rule)
    print(json.dumps({"seed": candidate["seed"], "difficulty": candidate["difficulty"],
                      "sample_indices": candidate["sample_indices"], "direction": candidate["rival_direction"],
                      "conflicts": candidate["conflicts"], "searched": report["candidate_search"],
                      "hook": candidate["declared_lesson_hook_reasons"]}, indent=2))


def verify(repo, outdir):
    mod, source, source_hash, rule, canonical = bootstrap(repo)
    prepared = json.loads((outdir / "candidate.json").read_text())
    assert source_hash == prepared["generator_sha256"]
    assert sha(rule) == prepared["rule_text_sha256"]
    candidate = prepared["candidate"]
    inputs = json.loads((outdir / "input.json").read_text())["inputs"]
    receipt_reused = (outdir / "racket.json").is_file()
    if receipt_reused:
        receipt = json.loads((outdir / "racket.json").read_text())
    else:
        from arcpuzzles import Catalog
        receipt = Catalog(repo).apply(TASK_ID, inputs, reference="canonical", timeout=120,
                                     check_generator_domain=True)
        receipt["command"] = [sys.executable, *sys.argv]
        receipt["cwd"] = str(Path.cwd())
        save(outdir / "racket.json", receipt)
    assert receipt["generator_sha256"] == source_hash
    assert receipt["reference"] == "canonical"
    # The worker hashes wrapped callable text in rule_text_sha256. Its
    # executed_rule_hash instead binds the normalized canonical source.
    assert receipt["executed_rule_hash"] == prepared["rule_hash"]
    assert receipt["rule_hash_matches_catalog"]
    assert [row["input"] for row in receipt["results"]] == inputs
    assert all(row["valid_output"] and row["error"] is None for row in receipt["results"])
    assert all(row["generator_domain"] == {"status": "valid", "errors": []} for row in receipt["results"])
    pairs = [{"input": row["input"], "output": row["output"]} for row in receipt["results"][:4]]
    direction = candidate["rival_direction"]
    rival_outputs = [numeric_rank_output(pair["input"], direction) for pair in pairs]
    fits = [prediction == pair["output"] for prediction, pair in zip(rival_outputs, pairs)]
    assert fits == [True, True, True, False]
    assert all(mod.self_check(pair["input"]) == [] for pair in pairs)
    assert all(pair["input"] != pair["output"] for pair in pairs)
    assert len({grid_hash(pair["input"]) for pair in pairs}) == 4
    canonical_results = receipt["results"][4:]
    assert len(canonical_results) == len(canonical)
    assert all(row["output"] == pair["output"] for row, pair in zip(canonical_results, canonical))
    canonical_fit = {name: sum(numeric_rank_output(row["input"], name) == row["output"] for row in canonical_results)
                     for name in ("minimum", "maximum")}
    query, rival_query = pairs[3]["output"], rival_outputs[3]
    diff = [{"row": r, "column": c, "racket": value, "rival": rival_query[r][c]}
            for r, row in enumerate(query) for c, value in enumerate(row) if value != rival_query[r][c]]
    declared = {name: {"demo_matches": sum(fn(pair["input"]) == pair["output"] for pair in pairs[:3]),
                       "query_matches": fn(pairs[3]["input"]) == pairs[3]["output"]}
                for name, fn in mod.LESSON_COMPETITORS.items()}
    hook = mod.lesson_identifiable(pairs[:3], pairs[3])
    assert hook == []
    assert sha(source.read_bytes()) == source_hash
    finding = {"finding_id": "A1-NUMERIC-RANK", "task_id": TASK_ID, "status": "reproduced_teaching_ambiguity",
               "generator_sha256": source_hash, "rule_hash": receipt["executed_rule_hash"],
               "canonical_source_sha256": sha(rule), "executed_callable_sha256": receipt["rule_text_sha256"], "seed": candidate["seed"],
               "difficulty": candidate["difficulty"], "sample_indices": candidate["sample_indices"],
               "overrides": {}, "demonstration_count": 3, "query_index": 3,
               "rival": direction + "_nonzero_color", "pairs": pairs, "rival_outputs": rival_outputs,
               "demo_matches": sum(fits[:3]), "query_matches": fits[3], "query_differences": diff,
               "conflicts": candidate["conflicts"], "canonical_labeled_pairs": len(canonical_results),
               "canonical_rival_fits": canonical_fit, "declared_rival_scores": declared,
               "lesson_identifiable_reasons": hook,
               "generator_domain_errors": [mod.self_check(pair["input"]) for pair in pairs],
               "unique_generated_inputs": 4, "results_in_actual_racket_receipt": len(receipt["results"]),
               "racket_receipt_reused": receipt_reused,
               "racket_receipt_sha256": sha((outdir / "racket.json").read_bytes()),
               "source_unchanged_during_probe": True,
               "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()), "exit_code": 0,
               "limits": "One exact default-generated consecutive lesson. No prevalence estimate, exhaustive induction claim, or canonical-label defect. Query is freshly generated authoring data, not a hidden solve label."}
    save(outdir / "finding.json", finding)
    print(json.dumps({k: v for k, v in finding.items() if k not in ("pairs", "rival_outputs")}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("search", "verify"))
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (search if args.phase == "search" else verify)(args.repo.resolve(), args.out_dir.resolve())


if __name__ == "__main__":
    main()

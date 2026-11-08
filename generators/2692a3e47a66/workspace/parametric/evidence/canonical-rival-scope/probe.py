#!/usr/bin/env python3
"""Read-only canonical-rival scope probe using saved Racket labels.
No generator draws, Racket execution, tests, or repository edits are performed.
"""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys

def sha_file(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()

def sha_json(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()

def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

def difference(left, right):
    assert len(left) == len(right)
    assert all(len(a) == len(b) for a, b in zip(left, right))
    return sum(a != b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root, evidence, out = args.repo.resolve(), args.evidence.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root / "shared/runtime"))
    import reviewer_support
    from reviewer_support import canonical_pairs, canonical_path, load_selected_generator, normalize_grid
    task_id = "2692a3e47a66"
    generator, generator_path, generator_sha = load_selected_generator(task_id, root=root)
    report_path = evidence / "private/report.json"
    report = json.loads(report_path.read_text())
    assert generator_sha == report["source_identity"]["canonical_generator.py"]["sha256"]
    canonical_saved_path = evidence / "private/canonical_default.json"
    canonical_saved = json.loads(canonical_saved_path.read_text())
    canonical = canonical_pairs(task_id, root=root)
    assert len(canonical) == len(canonical_saved["pairs"]) == 5
    rule_sha = canonical_saved["program_sha256"]
    trace_path = evidence / "private/racket_trace.jsonl"
    trace = [json.loads(line) for line in trace_path.read_text().splitlines() if line.strip()]
    trace_labels = {
        (item["input_sha256"], item["output_sha256"], item["rule_sha256"]): item
        for item in trace if item["status"] == "completed"
    }
    sources = {
        "generator": {"path": str(generator_path), "sha256": generator_sha},
        "reviewer_support": {"path": reviewer_support.__file__, "sha256": sha_file(reviewer_support.__file__)},
        "probe": {"path": str(Path(__file__).resolve()), "sha256": sha_file(__file__)},
        "canonical_ledger": {"path": str(canonical_path(root)), "sha256": sha_file(canonical_path(root))},
        "retained_report": {"path": str(report_path), "sha256": sha_file(report_path)},
        "retained_trace": {"path": str(trace_path), "sha256": sha_file(trace_path)},
        "retained_canonical": {"path": str(canonical_saved_path), "sha256": sha_file(canonical_saved_path)},
    }
    for name, identity in report["source_identity"].items():
        current = root / identity["path"]
        assert sha_file(current) == identity["sha256"], name
        sources[name] = {"path": str(current), "sha256": identity["sha256"]}
    declarations = {}
    candidates = {}
    for declaration in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        values = getattr(generator, declaration)
        assert isinstance(values, dict) and values
        declarations[declaration] = list(values)
        for name, function in values.items():
            if name in candidates:
                assert function is candidates[name]
            candidates[name] = function
    rival_sources = {}
    for name, function in candidates.items():
        source = inspect.getsource(function)
        rival_sources[name] = {
            "callable_name": function.__name__,
            "module_source_sha256": generator_sha,
            "function_source": source,
            "function_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "declarations": [d for d, names in declarations.items() if name in names],
        }
    canonical_results = []
    direct_predictions = 0
    for pair, retained in zip(canonical, canonical_saved["pairs"]):
        for key in ("input", "output", "variant", "split", "pair_index"):
            assert pair[key] == retained[key]
        assert retained["actual"] == pair["output"]
        trace_row = trace_labels[(sha_json(pair["input"]), sha_json(pair["output"]), rule_sha)]
        rival_results = {}
        for name, function in candidates.items():
            actual = normalize_grid(function(deepcopy(pair["input"])))
            direct_predictions += 1
            rival_results[name] = {
                "output": actual, "output_sha256": sha_json(actual),
                "matches_reference": actual == pair["output"],
                "difference_cells": difference(actual, pair["output"]),
            }
        canonical_results.append({
            **pair, "retained_racket_attempt_index": trace_row["attempt_index"],
            "rivals": rival_results,
        })
    canonical_fit = {
        name: all(pair["rivals"][name]["matches_reference"] for pair in canonical_results)
        for name in candidates
    }
    episodes = []
    observed_failures = []
    production_failures = []
    for entry in report["episodes"]:
        if entry["settings"] != {"min_repeat": 2, "step_blocks": 1}:
            continue
        episode_path = evidence / entry["private"]
        episode = json.loads(episode_path.read_text())
        assert episode["settings"] == entry["settings"]
        pairs = episode["pairs"]
        assert len(pairs) == 7 and episode["accepted"]
        assert [p["output"] for p in pairs] == episode["predictions"]["m2_s1"]
        source_key = f"default_episode_{entry['index']:03}"
        sources[source_key] = {"path": str(episode_path), "sha256": sha_file(episode_path)}
        public_path = evidence / entry["public"]
        public = json.loads(public_path.read_text())
        assert public == {"train": pairs[:6], "test": [{"input": pairs[6]["input"]}]}
        sources[source_key + "_public"] = {"path": str(public_path), "sha256": sha_file(public_path)}
        predictions = {name: [] for name in candidates}
        facts = []
        for index, pair in enumerate(pairs):
            assert not generator.self_check(pair["input"])
            key = sha_json(pair["input"]), sha_json(pair["output"]), rule_sha
            trace_row = trace_labels[key]
            grid = pair["input"]
            corner_colors = [grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1]]
            facts.append({
                "pair_index": index,
                "shape": [len(grid), len(grid[0])],
                "corner_colors_tl_tr_bl_br": corner_colors,
                "multiplicities": sorted(Counter(corner_colors).values()),
                "input_sha256": key[0], "reference_output_sha256": key[1],
                "retained_racket_attempt_index": trace_row["attempt_index"],
            })
            for name, function in candidates.items():
                predictions[name].append(normalize_grid(function(deepcopy(grid))))
                direct_predictions += 1
        prediction_records = {
            name: [{"pair_index": i, "output": actual, "output_sha256": sha_json(actual),
                    "matches_reference": actual == pairs[i]["output"],
                    "difference_cells": difference(actual, pairs[i]["output"])}
                   for i, actual in enumerate(outputs)]
            for name, outputs in predictions.items()
        }
        holdouts = []
        for query_index in range(7):
            train_indices = [i for i in range(7) if i != query_index]
            rival_results = {}
            surviving_wrong = []
            for name, outputs in predictions.items():
                refuted_by = [i for i in train_indices if outputs[i] != pairs[i]["output"]]
                query_matches = outputs[query_index] == pairs[query_index]["output"]
                rival_results[name] = {
                    "fits_all_five_canonical_pairs": canonical_fit[name],
                    "fits_all_visible_demonstrations": not refuted_by,
                    "refuted_by_pair_indices": refuted_by,
                    "query_output": outputs[query_index],
                    "query_output_sha256": sha_json(outputs[query_index]),
                    "query_matches_reference": query_matches,
                    "query_difference_cells": difference(outputs[query_index], pairs[query_index]["output"]),
                }
                if canonical_fit[name] and not refuted_by and not query_matches:
                    surviving_wrong.append(name)
                    finding = {"episode_index": entry["index"], "seed": entry["seed"],
                               "query_index": query_index, "rival": name,
                               "difference_cells": difference(outputs[query_index], pairs[query_index]["output"])}
                    observed_failures.append(finding)
                    if query_index == 6:
                        production_failures.append(finding)
            holdouts.append({
                "query_index": query_index, "is_ordered_production_query": query_index == 6,
                "visible_train_pair_indices": train_indices,
                "visible_lesson": {"train": [pairs[i] for i in train_indices],
                                   "test": [{"input": pairs[query_index]["input"]}]},
                "reference_query_output": pairs[query_index]["output"],
                "rivals": rival_results,
                "canonical_fitting_surviving_wrong_rivals": surviving_wrong,
            })
        episodes.append({
            "episode_index": entry["index"], "seed": episode["seed"],
            "settings": episode["settings"], "production_query_index": 6,
            "pairs": pairs, "pair_facts": facts, "rival_predictions": prediction_records,
            "holdouts": holdouts, "retained_public_path": str(public_path),
        })
    assert episodes
    details = {
        "task_id": task_id, "sources": sources, "declarations": declarations,
        "canonical_rule_program_sha256": rule_sha,
        "rival_sources": rival_sources, "canonical_pairs": canonical_results,
        "episodes": episodes, "racket_executions_performed": 0,
        "direct_python_rival_predictions": direct_predictions,
        "procedure": "Load actual declared callables via public load_selected_generator; read canonical pairs via public canonical_pairs; compare predictions to retained exact Racket labels and trace hashes; reuse predictions across all seven holdouts. No relabeling or sampler draw.",
    }
    details_path = out / "details.json"
    dump(details_path, details)
    summary = {
        "task_id": task_id, "status": "known_rotation_scope_limit_observed" if observed_failures else "no_limit_observed_in_checked_default_episodes",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "command_argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "TMPDIR": os.environ.get("TMPDIR"),
        "default_episodes_checked": len(episodes), "canonical_pairs_checked": len(canonical),
        "unique_declared_rivals_checked": len(candidates),
        "declarations": declarations, "canonical_fit_all_five": canonical_fit,
        "query_placements_checked": 7 * len(episodes),
        "rival_placement_comparisons": 7 * len(episodes) * len(candidates),
        "direct_python_rival_predictions": direct_predictions,
        "racket_executions_performed": 0,
        "ordered_production_surviving_wrong_rivals": production_failures,
        "all_holdout_surviving_wrong_rivals": observed_failures,
        "ordered_production_refutes_all_declared_rivals": all(
            not rival["fits_all_visible_demonstrations"]
            for episode in episodes for holdout in episode["holdouts"]
            if holdout["is_ordered_production_query"]
            for rival in holdout["rivals"].values()
        ),
        "details_sha256": sha_file(details_path),
        "source_hashes": {key: value["sha256"] for key, value in sources.items()},
        "scope": "The prototype's 49 earlier successful holdout checks concern its six parameter settings only. This saved default-episode probe separately checks both actual canonical-fitting rivals. Preserve each public episode's six demonstrations and its designated seventh query; do not infer arbitrary query-rotation robustness against canonical rivals.",
        "repository_sources_modified": False,
    }
    dump(out / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True))

if __name__ == "__main__":
    main()

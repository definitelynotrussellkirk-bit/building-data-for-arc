#!/usr/bin/env python3
"""Assess saved public-CLI canonical episodes against live declared competitors.

From the packet's outer root, generate labels with the public Racket path:

    WORK/.venv/bin/python review.py run ../.venv/bin/python -m arcpuzzles \
        generate 3977ec54e4a0 --count 1 --seed 17 --test 4 --allow-unapproved \
        --out ../checks/four-query/episode.jsonl
    WORK/.venv/bin/python review.py run ../.venv/bin/python \
        generators/3977ec54e4a0/workspace/canonical_episode_probe.py \
        ../checks/four-query/episode.jsonl \
        --out ../checks/four-query/episode-probe.json

The assessment uses only ``train`` pairs to fit rivals; each ``test`` answer
is used solely to evaluate that query. It does not relabel grids or re-execute
Racket. Its evidence is bound to the saved episode, current generator bytes,
and executed canonical rule hash. This finite competitor family does not prove
universal identifiability. Output paths must be new.

For a separate one-query episode, ``--test 1 --rotate-query`` also holds out
each labeled pair once. This diagnostic deliberately changes the demo/query
assignment and reports ``rotation_status`` independently; the normal production
verdict and exit status still use only the original ``train`` demonstrations.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys


TASK_ID = "3977ec54e4a0"


def _grid_hash(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _validate_grid(grid, location: str) -> None:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError(f"{location} must be a nonempty integer grid")
    width = len(grid[0])
    if any(
        not isinstance(row, list) or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError(f"{location} must be a rectangular grid of integers 0..9")


def assess_episode(episode, competitors):
    """Score a finite rival family without borrowing any query labels as demos."""
    pairs = []
    inputs = {}
    for split in ("train", "test"):
        if not isinstance(episode.get(split), list) or not episode[split]:
            raise ValueError(f"{split} must contain at least one labeled pair")
        for index, pair in enumerate(episode[split]):
            location = f"{split}[{index}]"
            for field in ("input", "output"):
                if not isinstance(pair, dict) or field not in pair:
                    raise ValueError(f"{location} is missing {field}")
                _validate_grid(pair[field], f"{location}.{field}")
            digest = _grid_hash(pair["input"])
            inputs.setdefault(digest, []).append(location)
            pairs.append({
                "split": split, "pair_index": index,
                "input_sha256": digest, "output_sha256": _grid_hash(pair["output"]),
                "shape": [len(pair["input"]), len(pair["input"][0])],
            })

    rivals = {}
    for name, solve in sorted(competitors.items()):
        mismatches = []
        errors = []
        for index, pair in enumerate(episode["train"]):
            try:
                predicted = solve(copy.deepcopy(pair["input"]))
                _validate_grid(predicted, f"rival {name} prediction")
                if predicted != pair["output"]:
                    mismatches.append(index)
            except Exception as exc:
                errors.append({"demo_index": index, "error": f"{type(exc).__name__}: {exc}"})
        rivals[name] = {
            "demo_fit": "error" if errors else "refuted" if mismatches else "fits",
            "mismatching_demo_indices": mismatches,
            "errors": errors,
        }

    queries = []
    for index, pair in enumerate(episode["test"]):
        query = {
            "query_index": index,
            "input_sha256": _grid_hash(pair["input"]),
            "demonstration_indices": list(range(len(episode["train"]))),
            "refuted_by_demos": [], "agreeing_rivals": [],
            "ambiguous_rivals": [], "error_rivals": [], "errors": [],
        }
        for name, solve in sorted(competitors.items()):
            fit = rivals[name]["demo_fit"]
            if fit == "refuted":
                query["refuted_by_demos"].append(name)
            elif fit == "error":
                query["error_rivals"].append(name)
            else:
                try:
                    predicted = solve(copy.deepcopy(pair["input"]))
                    _validate_grid(predicted, f"rival {name} prediction")
                    key = "agreeing_rivals" if predicted == pair["output"] else "ambiguous_rivals"
                    query[key].append(name)
                except Exception as exc:
                    query["error_rivals"].append(name)
                    query["errors"].append({"rival": name, "error": f"{type(exc).__name__}: {exc}"})
        query["status"] = (
            "NO_CONTRACT" if not rivals else
            "FAIL" if query["ambiguous_rivals"] or query["error_rivals"] else "PASS"
        )
        queries.append(query)

    duplicates = [
        {"input_sha256": digest, "locations": locations}
        for digest, locations in sorted(inputs.items()) if len(locations) > 1
    ]
    return {
        "train_count": len(episode["train"]), "query_count": len(episode["test"]),
        "unique_input_count": len(inputs), "duplicate_inputs": duplicates,
        "pairs": pairs, "rivals": rivals, "queries": queries,
        "query_answers_used_as_demonstrations": False,
        "status": "NO_CONTRACT" if not rivals else "FAIL" if duplicates or any(
            query["status"] != "PASS" for query in queries
        ) else "PASS",
    }


def binding_errors(episode, source_hash, rule_hash, expected_train=3, expected_test=4):
    """Reject stale authority/source bindings and silently shortened episodes."""
    provenance = episode.get("provenance", {})
    errors = []
    if episode.get("task_id") != TASK_ID:
        errors.append("episode task ID does not match this selected generator")
    if provenance.get("generator_sha256") != source_hash:
        errors.append("episode generator source hash differs from the live selected source")
    if episode.get("executed_rule_hash") != rule_hash or provenance.get("rule_hash") != rule_hash:
        errors.append("episode executed rule hash differs from the declared canonical rule")
    if provenance.get("reference") != "canonical":
        errors.append("episode does not declare canonical reference execution")
    if len(episode.get("train", [])) != expected_train:
        errors.append(f"demonstration count differs from requested {expected_train}")
    if len(episode.get("test", [])) != expected_test:
        errors.append(f"query count differs from requested {expected_test}")
    return errors


def assess_rotations(episode, competitors):
    """Diagnose every holdout of one 3+1 bundle, separate from production."""
    if len(episode.get("test", [])) != 1:
        raise ValueError("rotation diagnostics require exactly one query in a separate episode")
    pairs = episode["train"] + episode["test"]
    rotations = []
    for query_index, pair in enumerate(pairs):
        train_indices = [index for index in range(len(pairs)) if index != query_index]
        assessment = assess_episode(
            {"train": [pairs[index] for index in train_indices], "test": [pair]},
            competitors,
        )
        rotations.append({
            "held_out_pair_index": query_index,
            "train_pair_indices": train_indices,
            "status": assessment["status"], "assessment": assessment,
        })
    return rotations


def _load_selected():
    for parent in Path(__file__).resolve().parents:
        for runtime in (parent / "shared/runtime", parent):
            if (runtime / "reviewer_support.py").is_file():
                sys.path.insert(0, str(runtime))
                from reviewer_support import find_root, load_selected_generator
                return load_selected_generator(TASK_ID, root=find_root(__file__))
    raise RuntimeError("cannot locate this checkout's reviewer_support runtime")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episodes", type=Path, nargs="+", help="saved public-generation JSONL files")
    parser.add_argument("--train", type=int, default=3, help="required demonstrations per episode")
    parser.add_argument("--test", type=int, default=4, help="required queries per episode")
    parser.add_argument("--rotate-query", action="store_true", help="separate diagnostic; requires --test 1")
    parser.add_argument("--out", type=Path, help="new JSON report; stdout if omitted")
    args = parser.parse_args(argv)
    if args.train < 1 or args.test < 1:
        parser.error("--train and --test must be positive")
    if args.rotate_query and args.test != 1:
        parser.error("--rotate-query requires --test 1 on a separate one-query episode")
    if args.out is not None and args.out.exists():
        parser.error(f"output already exists: {args.out}")

    generator, source, source_hash = _load_selected()
    competitors = dict(generator.LESSON_COMPETITORS)
    reports = []
    for path in args.episodes:
        raw = path.read_bytes()
        file_hash = hashlib.sha256(raw).hexdigest()
        for line_number, line in enumerate(raw.decode().splitlines(), 1):
            if not line.strip():
                continue
            episode = json.loads(line)
            report = assess_episode(episode, competitors)
            errors = binding_errors(episode, source_hash, generator.RULE_HASH, args.train, args.test)
            for split in ("train", "test"):
                for index, pair in enumerate(episode[split]):
                    for reason in generator.self_check(copy.deepcopy(pair["input"])):
                        errors.append(f"{split}[{index}] domain: {reason}")
            report.update({
                "episode_file": str(path), "episode_file_sha256": file_hash,
                "line_number": line_number, "episode_index": episode.get("episode_index"),
                "seed": episode.get("seed"), "sample_indices": episode.get("sample_indices"),
                "recorded_lesson_check": episode.get("lesson_check"),
                "executed_rule_hash": episode.get("executed_rule_hash"),
                "binding_and_domain_errors": errors,
            })
            if errors:
                report["status"] = "FAIL"
            report["production_status"] = report["status"]
            if args.rotate_query:
                report["rotations"] = assess_rotations(episode, competitors)
                report["rotation_status"] = "PASS" if all(
                    item["status"] == "PASS" for item in report["rotations"]
                ) else "FAIL"
            else:
                report["rotation_status"] = "NOT_REQUESTED"
            reports.append(report)

    report = {
        "schema": "arc.canonical-episode-probe.v1", "task_id": TASK_ID,
        "generator_source": str(source), "generator_sha256": source_hash,
        "generator_version": generator.VERSION, "rule_hash": generator.RULE_HASH,
        "declared_competitors": sorted(competitors),
        "expected_counts": {"train": args.train, "test": args.test},
        "label_basis": "Saved public-generation Racket labels; this probe does not re-execute Racket.",
        "scope_limit": "Finite declared competitors only; no universal identifiability claim.",
        "episodes": reports,
        "status": "PASS" if reports and all(item["status"] == "PASS" for item in reports) else "FAIL",
        "rotation_policy": "diagnostic",
        "rotation_status": "NOT_REQUESTED" if not args.rotate_query else
            "PASS" if reports and all(item["rotation_status"] == "PASS" for item in reports) else "FAIL",
    }
    report["production_status"] = report["status"]
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(rendered, end="")
    else:
        with args.out.open("x", encoding="utf-8") as handle:
            handle.write(rendered)
        print(json.dumps({
            "production_status": report["production_status"],
            "rotation_status": report["rotation_status"],
            "episodes": len(reports), "out": str(args.out),
        }))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

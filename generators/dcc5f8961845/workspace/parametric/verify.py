#!/usr/bin/env python3
"""Bounded protected-Racket verification, teaching audit, and public projection."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "dcc5f8961845"
HEADER = {"second_source": "header"}
MARKER = {"second_source": "post_first_marker"}
SETTINGS = (HEADER, MARKER)


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False, ensure_ascii=False) + "\n").encode()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def load_adapter():
    path = HERE / "adapter.py"
    body = path.read_bytes()
    name = "_dcc5_verify_" + digest(str(path).encode() + body)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


def source_hashes():
    sources = [HERE.parents[1] / "generator.py", HERE.parents[1] / "tests/test_generator_dcc5f8961845.py",
               HERE.parents[1] / "tests/test_parametric.py"]
    sources += [path for path in sorted(HERE.iterdir())
                if path.is_file() and path.suffix in {".py", ".rkt", ".json", ".md"}]
    return {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in sources}


def content_summary(grid, adapter):
    scene = adapter.analyze(grid)
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                if value != 0 and r >= 2]
    return {
        "shape": [len(grid), len(grid[0])],
        "motif_shape": [len(scene["motif"]), len(scene["motif"][0])],
        "commands": [scene["cmd1"], scene["cmd2"]],
        "marker_corner_before_first": adapter._MODULE._corner_name(scene["motif"]),
        "marker_corner_after_first": adapter._MODULE._corner_name(
            adapter._MODULE._transform(scene["motif"], scene["cmd1"])
        ),
        "nonzero_motif_cells": len(occupied),
        "density": len(occupied) / (len(scene["motif"]) * len(scene["motif"][0])),
        "touches": {
            "left": any(c == 0 for _, c in occupied),
            "right": any(c == len(grid[0]) - 1 for _, c in occupied),
            "bottom": any(r == len(grid) - 1 for r, _ in occupied),
        },
        "quadrants": sorted({(2 * r // len(grid)) * 2 + (2 * c // len(grid[0]))
                             for r, c in occupied}),
    }


def verify(output: Path, *, seeds: list[int], demos: int, queries: int):
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
    from reviewer_support import public_challenge_bytes, public_challenge_id

    if output.exists():
        raise FileExistsError(f"refusing existing output: {output}")
    if (type(demos) is not int or not 2 <= demos <= 6
            or type(queries) is not int or not 1 <= queries <= 4):
        raise ValueError("supported counts are 2..6 demonstrations and 1..4 queries")
    if (type(seeds) is not list or not 1 <= len(seeds) <= 16
            or len(set(seeds)) != len(seeds)
            or any(type(seed) is not int or not 0 <= seed < 2**63 for seed in seeds)):
        raise ValueError("use 1..16 distinct exact integer seeds")
    output.mkdir(parents=True)
    adapter = load_adapter()
    initial = source_hashes()
    failures = []
    episodes = []
    public_rows = []
    matched_inputs = {}
    evaluations = 0
    bridge = None
    runtime = ROOT / "shared/runtime"

    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            def execute(program, grid, context):
                nonlocal evaluations
                evaluations += 1
                try:
                    return _grid(apply(program, copy.deepcopy(grid)))
                except Exception as exc:
                    failures.append({"kind": "racket_error", "context": context,
                                     "error": f"{type(exc).__name__}: {exc}"})
                    return None

            for seed in seeds:
                for settings in SETTINGS:
                    episode = adapter.generate(seed, copy.deepcopy(settings), demos, queries)
                    selected = adapter.program(copy.deepcopy(settings))
                    splits = {name: [{"input": _grid(pair["input"]), "output": _grid(pair["output"])}
                                     for pair in episode[name]]
                              for name in ("train", "test")}
                    serialized = [raw(pair["input"]) for name in ("train", "test") for pair in splits[name]]
                    if len(serialized) != len(set(serialized)):
                        failures.append({"kind": "duplicate_input", "seed": seed, "settings": settings})
                    prior = matched_inputs.setdefault(seed, serialized)
                    if prior != serialized:
                        failures.append({"kind": "setting_input_mismatch", "seed": seed, "settings": settings})

                    selected_outputs = []
                    for split in ("train", "test"):
                        for index, pair in enumerate(splits[split]):
                            got = execute(selected, pair["input"], {
                                "seed": seed, "settings": settings, "split": split,
                                "pair": index, "program": "selected",
                            })
                            selected_outputs.append(got)
                            if got != pair["output"]:
                                failures.append({"kind": "selected_label_mismatch", "seed": seed,
                                                 "settings": settings, "split": split, "pair": index})

                    other = MARKER if settings == HEADER else HEADER
                    candidates = {"other_setting": adapter.program(copy.deepcopy(other))}
                    candidates.update(adapter.rival_programs(copy.deepcopy(settings)))
                    survivors = []
                    candidate_rows = []
                    for name, candidate in candidates.items():
                        outputs = [execute(candidate, pair["input"], {
                            "seed": seed, "settings": settings, "split": "train",
                            "pair": index, "program": name,
                        }) for index, pair in enumerate(splits["train"])]
                        fits = all(got == pair["output"] for got, pair in zip(outputs, splits["train"]))
                        if fits:
                            survivors.append(name)
                        candidate_rows.append({"name": name, "program_sha256": digest(candidate.encode()),
                                               "fits_demonstrations": fits, "outputs": outputs})
                    query_disagreements = []
                    for name in survivors:
                        candidate = candidates[name]
                        outputs = [execute(candidate, pair["input"], {
                            "seed": seed, "settings": settings, "split": "test",
                            "pair": index, "program": name,
                        }) for index, pair in enumerate(splits["test"])]
                        if any(got != pair["output"] for got, pair in zip(outputs, splits["test"])):
                            query_disagreements.append(name)
                    if survivors:
                        failures.append({"kind": "rival_survived_demonstrations", "seed": seed,
                                         "settings": settings, "survivors": survivors,
                                         "query_disagreements": query_disagreements})

                    public = {"train": splits["train"],
                              "test": [{"input": pair["input"]} for pair in splits["test"]]}
                    public_body = public_challenge_bytes(public)
                    public_id = public_challenge_id(public)
                    first = adapter.generate(seed, copy.deepcopy(settings), demos, 1)
                    first_equal = public_challenge_bytes(first) == public_challenge_bytes(
                        {"train": splits["train"], "test": splits["test"][:1]}
                    )
                    if not first_equal:
                        failures.append({"kind": "first_turn_mismatch", "seed": seed, "settings": settings})
                    if settings["second_source"].encode() in public_body or selected.encode() in public_body:
                        failures.append({"kind": "private_field_leak", "seed": seed, "settings": settings})
                    coverage = [content_summary(pair["input"], adapter)
                                for name in ("train", "test") for pair in splits[name]]
                    if queries == 4 and not any(row["shape"] == [30, 30] for row in coverage):
                        failures.append({"kind": "missing_30x30_query", "seed": seed, "settings": settings})
                    mirror = adapter.lesson_report({**episode, **splits}, copy.deepcopy(settings))
                    if mirror["demonstration_survivors"] or mirror["surviving_query_disagreements"]:
                        failures.append({"kind": "python_teaching_audit_failed", "seed": seed,
                                         "settings": settings, "report": mirror})
                    episodes.append({
                        "seed": seed,
                        "settings": settings,
                        "public_id": public_id,
                        "program_sha256": digest(selected.encode()),
                        "train": splits["train"],
                        "test": splits["test"],
                        "finite_rivals": candidate_rows,
                        "racket_survivors": survivors,
                        "query_disagreements": query_disagreements,
                        "content_coverage": coverage,
                        "first_turn_equals_single_query": first_equal,
                    })
                    public_rows.append((public_id, public_body))

            witness = adapter.sequential_witness()
            correct = execute(adapter.program(MARKER), witness["input"], {"program": "post_first_marker",
                                                                          "kind": "causal_witness"})
            skip_program = adapter.rival_programs(MARKER)["original_corner_after_first"]
            skipped = execute(skip_program, witness["input"], {"program": "original_corner_after_first",
                                                                "kind": "causal_witness"})
            witness["racket"] = {
                "correct_output": correct,
                "skip_a_output": skipped,
                "outputs_differ": correct != skipped,
                "correct_matches_python": correct == witness["correct_output"],
                "skip_matches_python": skipped == witness["skip_a_output"],
                "skip_program": skip_program,
                "skip_program_sha256": digest(skip_program.encode()),
            }
            if not all((witness["outputs_differ"], witness["racket"]["outputs_differ"],
                        witness["racket"]["correct_matches_python"], witness["racket"]["skip_matches_python"])):
                failures.append({"kind": "causal_witness_failed"})
        finally:
            if bridge is not None:
                bridge.close()

    if source_hashes() != initial:
        failures.append({"kind": "source_changed_during_verification"})
    ids = [public_id for public_id, _ in public_rows]
    if len(ids) != len(set(ids)):
        failures.append({"kind": "duplicate_public_projection"})
    (output / "episodes.private.jsonl").write_bytes(b"".join(raw(row) for row in sorted(episodes, key=lambda x: x["public_id"])))
    (output / "public.jsonl").write_bytes(b"".join(body for _, body in sorted(public_rows)))
    (output / "causal-witness.json").write_bytes(raw(witness))
    report = {
        "schema": "dcc5f8961845-bounded-parametric-verification-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "seeds": seeds,
        "counts": {"demos": demos, "queries": queries},
        "settings": SETTINGS,
        "episode_count": len(episodes),
        "racket_evaluations": evaluations,
        "racket": identity,
        "source_sha256": initial,
        "failed_findings": len(failures),
        "failures": failures,
        "public_ids": sorted(ids),
        "finite_claim": "Only the declared settings and named rival programs were tested.",
        "training_admitted": False,
        "native_qualification": False,
    }
    (output / "self-review.json").write_bytes(raw(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append")
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args(argv)
    result = verify(args.out, seeds=args.seed or [0, 17], demos=args.demos, queries=args.queries)
    print(json.dumps({key: result[key] for key in (
        "status", "episode_count", "racket_evaluations", "failed_findings"
    )}, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

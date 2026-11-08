#!/usr/bin/env python3
"""Export and independently replay bounded quarter-turn prototype evidence."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import traceback

from reviewer_support import canonical_pairs

from prototype import (
    EpisodeBuilder, PARAMETER_VALUES, SamplingExhausted, TASK_ID, digest,
    file_digest, public_challenge, rotation_domain_errors,
)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def source_snapshot(builder):
    paths = [
        builder.generator_path,
        Path(__file__).resolve(),
        Path(__file__).resolve().with_name("prototype.py"),
        Path(__file__).resolve().with_name("README.md"),
        builder.root / f"generators/{TASK_ID}/tests/test_parametric_quarter_turns.py",
    ]
    return [
        {"path": str(path.relative_to(builder.root)), "sha256": file_digest(path),
         "text": path.read_text(encoding="utf-8")}
        for path in paths
    ]


def export_evidence(args):
    destination = args.out.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    invocation = {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
                  "purpose": "bounded proposed parametric evidence"}
    write_json(destination / "invocation.json", invocation)
    episodes = []
    try:
        with EpisodeBuilder() as builder:
            sources = source_snapshot(builder)
            write_json(destination / "private/source-snapshot.json", sources)
            for turns, program in builder.programs.items():
                rule_path = destination / f"private/programs/quarter-turns-{turns}.rkt"
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(program, encoding="utf-8")

            canonical = canonical_pairs(TASK_ID, root=builder.root, labeled_only=True)
            canonical_results = []
            for pair in canonical:
                actual = builder.execute(0, pair["input"])
                if actual != pair["output"]:
                    raise AssertionError("zero-turn program disagrees with a canonical label")
                canonical_results.append({
                    "variant": pair["variant"], "split": pair["split"],
                    "pair_index": pair["pair_index"], "input_sha256": digest(pair["input"]),
                    "output_sha256": digest(actual), "matches_canonical_label": True,
                })

            overrides = {}
            if args.grid_height is not None:
                overrides["grid_h"] = args.grid_height
            if args.grid_width is not None:
                overrides["grid_w"] = args.grid_width
            for seed in args.seeds:
                for turns in args.settings:
                    episode = builder.generate(
                        seed, quarter_turns=turns, demos=args.demos, queries=args.queries,
                        max_attempts=args.max_attempts, input_overrides=overrides,
                    )
                    public = public_challenge(episode)
                    # Opaque content-derived names disclose no hidden parameter,
                    # seed, rule text, query labels, or private source identity.
                    public_name = f"public/challenge-{digest(public)[:20]}.json"
                    if (destination / public_name).exists():
                        raise AssertionError("duplicate public episode content in requested suite")
                    write_json(destination / public_name, public)
                    episode["meta"]["public_path"] = public_name
                    episodes.append(episode)

            witness_input = episodes[0]["train"][0]["input"]
            witness_outputs = {str(turns): builder.execute(turns, witness_input) for turns in PARAMETER_VALUES}
            if len({digest(output) for output in witness_outputs.values()}) < 2:
                raise AssertionError("retained witness does not change under any alternative setting")
            write_json(destination / "private/same-input-witness.json", {
                "input": witness_input, "input_sha256": digest(witness_input),
                "outputs": witness_outputs, "program_sha256": builder.program_hashes,
                "scope": "lawful shared input; exact Racket execution under all four settings",
            })
            write_json(destination / "private/canonical-zero-check.json", canonical_results)
            write_json(destination / "private/episodes.json", episodes)
            builder.ensure_sources_unchanged()
            for source in sources:
                if file_digest(builder.root / source["path"]) != source["sha256"]:
                    raise RuntimeError(f"source changed during evidence collection: {source['path']}")

            summary = {
                "schema": "fa3550d200a0-quarter-turn-prototype-report-v1",
                "status": "proposed_prototype", "complete": True,
                "seeds": args.seeds, "settings": args.settings,
                "demos_per_episode": args.demos, "queries_per_episode": args.queries,
                "episode_count": len(episodes), "canonical_labeled_pairs_checked": len(canonical_results),
                "racket_executions": builder.execution_count,
                "runtime_identity": builder.bridge.runtime_identity,
                "source_binding": builder.source_binding,
                "program_sha256": builder.program_hashes,
                "input_overrides": overrides,
                "input_sizes": sorted({
                    (len(pair["input"]), len(pair["input"][0]))
                    for episode in episodes for pair in episode["train"] + episode["test"]
                }),
                "sampling_rejections": dict(Counter(
                    row["reason"] for episode in episodes
                    for row in episode["meta"]["sampling"]["attempts"]
                    if row["status"] == "rejected"
                )),
                "all_pairs_distinct_within_each_episode": True,
                "demos_alone_identify_each_query_rule": True,
                "query_labels_used_for_demo_selection": False,
                "limitations": [
                    "Only the four declared orientation settings are rival-checked.",
                    "The sampler excludes clipping, target overlap and marker overwrite under every setting.",
                    "Counts and source identities describe this finite run, not all seeds or model difficulty.",
                    "No production interface, canonical authority, approval or training admission is changed.",
                ],
                "invocation": invocation,
            }
            write_json(destination / "report.json", summary)
        files = [
            {"path": str(path.relative_to(destination)), "sha256": file_digest(path),
             "bytes": path.stat().st_size}
            for path in sorted(destination.rglob("*")) if path.is_file()
        ]
        write_json(destination / "manifest.json", {
            "schema": "fa3550d200a0-parametric-evidence-manifest-v1", "files": files,
            "public_paths": [episode["meta"]["public_path"] for episode in episodes],
        })
        print(json.dumps({"status": "complete", "out": str(destination),
                          "episodes": len(episodes), "racket_executions": summary["racket_executions"]}))
        return 0
    except Exception as error:
        failure = {"status": "failed", "error_type": type(error).__name__, "error": str(error),
                   "invocation": invocation, "completed_episode_count": len(episodes),
                   "traceback": traceback.format_exc()}
        if isinstance(error, SamplingExhausted):
            failure["sampling_exhaustion"] = error.record
        write_json(destination / "failure.json", failure)
        if episodes:
            write_json(destination / "private/partial-episodes.json", episodes)
        print(json.dumps(failure), file=sys.stderr)
        return 1


def replay_evidence(source):
    source = source.resolve()
    manifest = json.loads((source / "manifest.json").read_text())
    for member in manifest["files"]:
        relative = Path(member["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("unsafe evidence manifest path")
        path = source / relative
        if path.is_symlink() or not path.resolve().is_relative_to(source):
            raise ValueError("evidence member escapes the evidence tree")
        if file_digest(path) != member["sha256"] or path.stat().st_size != member["bytes"]:
            raise ValueError(f"evidence hash mismatch: {relative}")
    episodes = json.loads((source / "private/episodes.json").read_text())
    checked = []
    with EpisodeBuilder() as builder:
        for episode in episodes:
            meta, turns = episode["meta"], episode["meta"]["quarter_turns"]
            for name, current in builder.source_binding.items():
                if meta["source_binding"][name]["sha256"] != current["sha256"]:
                    raise ValueError(f"evidence is stale against current {name} source")
            recorded_program = (source / f"private/programs/quarter-turns-{turns}.rkt").read_text()
            if not (recorded_program == episode["program"] == builder.programs[turns]):
                raise AssertionError("recorded rule differs from the exact instantiated rule")
            if hashlib.sha256(recorded_program.encode()).hexdigest() != meta["program_sha256"]:
                raise AssertionError("program hash mismatch")
            public = json.loads((source / meta["public_path"]).read_text())
            if public != public_challenge(episode):
                raise AssertionError("public challenge differs from strict privacy projection")
            pairs = episode["train"] + episode["test"]
            if len({digest(pair["input"]) for pair in pairs}) != len(pairs):
                raise AssertionError("repeated input within an episode")
            for pair in pairs:
                if rotation_domain_errors(pair["input"], builder.generator):
                    raise AssertionError("recorded input violates prototype geometry constraints")
            # Recompute the complete hypothesis set using demonstrations only.
            predictions = {
                rival: [builder.execute(rival, pair["input"]) for pair in episode["train"]]
                for rival in PARAMETER_VALUES
            }
            survivors = [rival for rival, outputs in predictions.items()
                         if outputs == [pair["output"] for pair in episode["train"]]]
            if survivors != [turns] or meta["demo_survivors"] != survivors:
                raise AssertionError("demonstrations do not identify the recorded setting")
            for pair in episode["test"]:
                if builder.execute(turns, pair["input"]) != pair["output"]:
                    raise AssertionError("query label differs from exact Racket execution")
            checked.append({"public_path": meta["public_path"], "quarter_turns": turns,
                            "seed": meta["seed"], "demos": len(episode["train"]),
                            "queries": len(episode["test"]), "demo_survivors": survivors})
        builder.ensure_sources_unchanged()
        report = {"status": "replay_passed", "source": str(source), "episodes": checked,
                  "racket_executions": builder.execution_count,
                  "manifest_sha256": file_digest(source / "manifest.json"),
                  "cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]}
    print(json.dumps(report, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument("--out", type=Path, help="new evidence directory")
    destination.add_argument("--replay", type=Path, help="verify hashes and re-execute an existing export")
    parser.add_argument("--seeds", type=int, nargs="+", default=[17])
    parser.add_argument("--settings", type=int, nargs="+", choices=PARAMETER_VALUES,
                        default=list(PARAMETER_VALUES))
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=500)
    parser.add_argument("--grid-height", type=int)
    parser.add_argument("--grid-width", type=int)
    args = parser.parse_args()
    if args.replay is not None:
        return replay_evidence(args.replay)
    if len(set(args.seeds)) != len(args.seeds) or len(set(args.settings)) != len(args.settings):
        parser.error("seeds and settings must each be distinct")
    return export_evidence(args)


if __name__ == "__main__":
    raise SystemExit(main())

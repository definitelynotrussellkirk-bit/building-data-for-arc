#!/usr/bin/env python3
"""Independently verify a one-parameter ARC authoring bundle.

This task-local tool is reusable for another family with the same small manifest
contract. It never trusts an author's rival verdicts. Structural mode checks
source/program/grid hashes and exact public projections. --execute additionally
runs every recorded program on every pair, checks labels, and recomputes teaching
and query-rotation evidence. The manifest is PRIVATE authoring data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def grid_hash(grid):
    return sha256(json.dumps(grid, sort_keys=True, separators=(",", ":")).encode())


def strict_json(raw):
    """Reject duplicate keys instead of silently discarding hidden fields."""
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique_object)


def exact_json(value):
    """Retain JSON scalar types, unlike Python's True == 1 == 1.0."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def valid_grid(grid):
    return (
        isinstance(grid, list) and 1 <= len(grid) <= 30
        and isinstance(grid[0], list) and 1 <= len(grid[0]) <= 30
        and all(isinstance(row, list) and len(row) == len(grid[0])
                and all(type(value) is int and 0 <= value <= 9 for value in row)
                for row in grid)
    )


def local_file(root, relative):
    if not isinstance(relative, str) or "\\" in relative:
        raise ValueError("file path must be a relative POSIX path")
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("file path must stay within the declared root")
    target = root.joinpath(*path.parts)
    if target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("file path escapes the declared root")
    if not target.is_file():
        raise ValueError("file is absent")
    return target


class RacketEvaluator:
    """Execute self-contained rule! lambdas through the protected Racket bridge.

    Deliberately excludes DSL shorthand and free implicit h/w bindings. The
    broader wrap_rule helper imports scripts.comment_solutions, which is absent
    in the direct library layout. Reusing its public wrapper parser is enough
    for this explicit lambda-only evidence contract; unsupported forms fail.
    """

    def __init__(self, timeout=10.0):
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import strip_rule_wrapper
        self.bridge = RacketBridge(timeout=timeout)
        self.strip_rule_wrapper = strip_rule_wrapper
        self.wrapped = {}

    def __enter__(self):
        self.bridge.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.bridge.shutdown()

    def __call__(self, program, grid):
        if program not in self.wrapped:
            body = self.strip_rule_wrapper(program)
            if not body.startswith(("(lambda ", "(lambda\n", "(λ ", "(λ\n")):
                raise ValueError("evidence programs must be self-contained rule! lambdas")
            self.wrapped[program] = body
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.wrapped[program]} {literal})")

    def runtime_identity(self):
        return self.bridge.runtime_identity


def verify_bundle(manifest_path, *, root, evaluator=None,
                  require_identified=False, require_rotations=False):
    """Return a receipt; malformed, incomplete or stale evidence fails closed."""
    manifest_path = Path(manifest_path).resolve()
    root = Path(root).resolve()
    report = {
        "schema": "arc-parametric-independent-verification-v1",
        "verifier_sha256": sha256(Path(__file__).read_bytes()),
        "passed": False, "issues": [], "execution_status": "not_run",
        "executed_pairs": 0, "label_mismatches": 0,
        "production_ambiguities": None, "rotation_ambiguities": None,
        "unidentified_episodes": None, "episodes": [],
        "limits": "Finite saved pairs and declared settings only; no approval or universal identifiability claim.",
    }
    issues = report["issues"]
    try:
        raw = manifest_path.read_bytes()
        manifest = strict_json(raw)
    except (OSError, ValueError) as exc:
        issues.append(f"cannot read manifest: {exc}")
        return report
    report["manifest_sha256"] = sha256(raw)
    if not isinstance(manifest, dict):
        issues.append("manifest must be an object")
        return report
    report["task_id"] = manifest.get("task_id")
    parameter = manifest.get("parameter_name")
    if not isinstance(parameter, str) or not parameter:
        issues.append("parameter_name must name the episode's fixed parameter")
        return report
    sources = manifest.get("source_hashes")
    if not isinstance(sources, dict) or not sources:
        issues.append("source_hashes must bind at least one source file")
    else:
        for relative, expected in sources.items():
            try:
                actual = sha256(local_file(root, relative).read_bytes())
                if actual != expected:
                    issues.append(f"source sha256 mismatch: {relative}")
            except (OSError, ValueError) as exc:
                issues.append(f"source {relative}: {exc}")
    programs = manifest.get("programs")
    if not isinstance(programs, dict) or len(programs) < 2:
        issues.append("programs must declare at least two distinct parameter settings")
        return report
    for setting, program in programs.items():
        if not isinstance(setting, str) or not isinstance(program, dict) or not isinstance(program.get("text"), str):
            issues.append(f"malformed program for setting {setting}")
        elif sha256(program["text"].encode()) != program.get("sha256"):
            issues.append(f"program sha256 mismatch: {setting}")
        if isinstance(program, dict) and "path" in program:
            try:
                rule_raw = local_file(manifest_path.parent, program["path"]).read_bytes()
                if (rule_raw.decode("utf-8") != program.get("text")
                        or sha256(rule_raw) != program.get("sha256")):
                    issues.append(f"program file mismatch: {setting}")
            except (OSError, ValueError) as exc:
                issues.append(f"program file {setting}: {exc}")

    episodes = manifest.get("episodes")
    if not isinstance(episodes, list) or not episodes:
        issues.append("episodes must be a nonempty list")
        return report
    public_expected = {}
    episode_data = []
    seen_episodes = set()
    for episode in episodes:
        if not isinstance(episode, dict):
            issues.append("episode must be an object")
            continue
        episode_id = episode.get("id")
        if not isinstance(episode_id, str) or not episode_id:
            issues.append("episode must have a nonempty id")
            continue
        if episode_id in seen_episodes:
            issues.append(f"duplicate episode id: {episode_id}")
        seen_episodes.add(episode_id)
        parameters = episode.get("parameters", {})
        setting = parameters.get(parameter) if isinstance(parameters, dict) else None
        if not isinstance(setting, str) or setting not in programs:
            issues.append(f"episode {episode_id}: undeclared parameter setting")
        elif "program_sha256" in episode:
            selected_program = programs[setting]
            if (not isinstance(selected_program, dict)
                    or episode["program_sha256"] != selected_program.get("sha256")):
                issues.append(f"episode {episode_id}: program binding sha256 mismatch")
        pairs = episode.get("pairs")
        if not isinstance(pairs, list) or not pairs:
            issues.append(f"episode {episode_id}: pairs must be nonempty")
            continue
        projection = {"train": [], "test": []}
        seen_pairs = set()
        pair_ok = True
        for pair in pairs:
            if not isinstance(pair, dict):
                issues.append(f"episode {episode_id}: pair must be an object")
                pair_ok = False
                continue
            pair_id = pair.get("id")
            if not isinstance(pair_id, str) or not pair_id or pair_id in seen_pairs:
                issues.append(f"episode {episode_id}: missing or duplicate pair id")
                pair_ok = False
            seen_pairs.add(pair_id if isinstance(pair_id, str) else "")
            role = pair.get("role")
            if role not in ("train", "test"):
                issues.append(f"episode {episode_id}: pair role must be train or test")
                pair_ok = False
            for name in ("input", "output"):
                grid = pair.get(name)
                if not valid_grid(grid):
                    issues.append(f"episode {episode_id}/{pair_id}: invalid {name} grid")
                    pair_ok = False
                elif grid_hash(grid) != pair.get(name + "_sha256"):
                    issues.append(f"episode {episode_id}/{pair_id}: {name} sha256 mismatch")
            if isinstance(role, str) and role in projection:
                entry = {"input": pair.get("input")}
                if role == "train":
                    entry["output"] = pair.get("output")
                projection[role].append(entry)
        if not projection["train"] or not projection["test"]:
            issues.append(f"episode {episode_id}: both train and test pairs are required")
        public_expected[episode_id] = projection
        if pair_ok and isinstance(setting, str) and setting in programs:
            episode_data.append((episode_id, setting, pairs))

    public_files = manifest.get("public_challenges")
    seen_public = set()
    if not isinstance(public_files, list) or not public_files:
        issues.append("a public challenge is required for every episode")
    else:
        seen_paths = set()
        for entry in public_files:
            if not isinstance(entry, dict):
                issues.append("public challenge record must be an object")
                continue
            episode_id, relative = entry.get("episode_id"), entry.get("path")
            if not isinstance(episode_id, str) or episode_id not in public_expected:
                issues.append("public challenge references an unknown episode")
                continue
            if episode_id in seen_public or (isinstance(relative, str) and relative in seen_paths):
                issues.append(f"duplicate public challenge: {episode_id}")
            seen_public.add(episode_id)
            seen_paths.add(relative if isinstance(relative, str) else "")
            try:
                public_raw = local_file(manifest_path.parent, relative).read_bytes()
                if sha256(public_raw) != entry.get("sha256"):
                    issues.append(f"public challenge sha256 mismatch: {episode_id}")
                if exact_json(strict_json(public_raw)) != exact_json(public_expected[episode_id]):
                    issues.append(f"public projection mismatch or hidden-data leakage: {episode_id}")
            except (OSError, ValueError) as exc:
                issues.append(f"public challenge {episode_id}: {exc}")
    for episode_id in seen_episodes - seen_public:
        issues.append(f"missing public challenge: {episode_id}")

    if evaluator is None:
        if require_identified or require_rotations:
            issues.append("identifiability requirements need program execution")
        report["passed"] = not issues
        return report
    # Never execute source with a failed structural/hash preflight.
    if issues:
        return report
    report.update(execution_status="completed", production_ambiguities=0,
                  rotation_ambiguities=0, unidentified_episodes=0)
    for episode_id, selected, pairs in episode_data:
        pair_results = {}
        for setting, program in programs.items():
            matches = []
            for pair in pairs:
                try:
                    actual = evaluator(program["text"], pair["input"])
                    report["executed_pairs"] += 1
                    if not valid_grid(actual):
                        raise ValueError("program returned an invalid ARC grid")
                    matches.append(actual == pair["output"])
                except Exception as exc:
                    report["execution_status"] = "failed"
                    issues.append(f"execution {episode_id}/{pair['id']}/{setting}: {type(exc).__name__}: {exc}")
                    matches.append(None)
            pair_results[setting] = matches
        label_mismatches = sum(value is False for value in pair_results[selected])
        report["label_mismatches"] += label_mismatches
        if label_mismatches:
            issues.append(f"episode {episode_id}: {label_mismatches} labels disagree with its fixed parameter")
        train_indexes = [i for i, pair in enumerate(pairs) if pair["role"] == "train"]
        test_indexes = [i for i, pair in enumerate(pairs) if pair["role"] == "test"]
        rivals = {}
        unidentified = []
        for setting, matches in pair_results.items():
            if setting == selected:
                continue
            fits_training = all(matches[i] is True for i in train_indexes)
            production_ambiguous = fits_training and any(matches[i] is False for i in test_indexes)
            rotations = [
                pairs[holdout]["id"] for holdout in range(len(pairs))
                if matches[holdout] is False
                and all(matches[i] is True for i in range(len(pairs)) if i != holdout)
            ]
            if fits_training:
                unidentified.append(setting)
            report["production_ambiguities"] += int(production_ambiguous)
            report["rotation_ambiguities"] += len(rotations)
            rivals[setting] = {"pair_matches": matches, "fits_training": fits_training,
                               "production_ambiguous": production_ambiguous,
                               "ambiguous_rotation_pair_ids": rotations}
        if unidentified:
            report["unidentified_episodes"] += 1
            if require_identified:
                issues.append(f"episode {episode_id}: alternative settings fit all demonstrations: {unidentified}")
        report["episodes"].append({"id": episode_id, "selected_setting": selected,
                                   "train_count": len(train_indexes), "query_count": len(test_indexes),
                                   "rotation_count": len(pairs), "label_mismatches": label_mismatches,
                                   "unrefuted_settings": unidentified, "rivals": rivals})
    if report["production_ambiguities"]:
        issues.append("declared rivals leave a production-query ambiguity")
    if require_rotations and report["rotation_ambiguities"]:
        issues.append("declared rivals leave a query-rotation ambiguity")
    report["passed"] = not issues
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, required=True, help="source root used by source_hashes")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--require-identified", action="store_true")
    parser.add_argument("--require-rotations", action="store_true")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("output already exists; use a fresh receipt path")
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    kwargs = dict(root=args.root, require_identified=args.require_identified,
                  require_rotations=args.require_rotations)
    if args.execute:
        with RacketEvaluator(timeout=args.timeout) as evaluator:
            report = verify_bundle(args.manifest, evaluator=evaluator, **kwargs)
            if report["executed_pairs"]:
                report["runtime_identity"] = evaluator.runtime_identity()
    else:
        report = verify_bundle(args.manifest, **kwargs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({key: report[key] for key in ("passed", "execution_status", "executed_pairs",
                     "label_mismatches", "production_ambiguities", "rotation_ambiguities", "issues")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

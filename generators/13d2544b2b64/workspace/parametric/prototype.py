#!/usr/bin/env python3
"""Proposed task-local crossing-priority episodes for ARC family 13d2544b2b64.

Run through WORK/run_with_racket.py. This is a separate authoring prototype;
the selected generator and canonical Racket authority are never written.
"""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import json
from pathlib import Path
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
for _ancestor in HERE.parents:
    for _relative in ("shared/runtime", "."):
        _runtime = _ancestor / _relative
        if (_runtime / "reviewer_support.py").is_file():
            if str(_runtime) not in sys.path:
                sys.path.insert(0, str(_runtime))
            break
    else:
        continue
    break
else:
    raise RuntimeError("cannot find a local library/runtime beside this prototype")

from reviewer_support import canonical_path, find_root, load_selected_generator

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from episode_tools import (ParameterSpace, RacketRunner, digest_bytes, digest_json,
                           grid_copy, grid_differences, public_challenge,
                           rival_report, validate_seed)


TASK_ID = "13d2544b2b64"
ROOT = find_root(__file__)
PROTOTYPE_VERSION = "1.0.0"
CANONICAL_SHA256 = "a699bbb01d8be15bf86293fdf76bebcf226ebfb019c6968f8917cc74a4f0e0c8"
PRIORITIES = ("horizontal", "vertical")
SPACE = ParameterSpace({"crossing_priority": PRIORITIES}, {"crossing_priority": "horizontal"})
DEMO_PROFILES = ("canonical_controls", "equality_mismatch", "horizontal_precedence", "target_overwrite")
HORIZONTAL_BRANCHES = "((!= h-mark 0) h-mark)\n                                ((!= v-mark 0) v-mark)"
VERTICAL_BRANCHES = "((!= v-mark 0) v-mark)\n                                ((!= h-mark 0) h-mark)"
LIMITATIONS = [
    "Proposed task-local authoring prototype; no production parameter API or variant approval.",
    "Only horizontal and vertical crossing priority are declared; no other rule changes.",
    "Generated episodes use medium difficulty, 8x8 grids, nine 2x2 panels and four demonstrations.",
    "The input sampler uses the selected generator's explicit scene_profile interface.",
    "Rival coverage proves identifiability only against the two declared parameter settings.",
    "Retained seed checks are bounded evidence, not a guarantee over every possible seed or grid.",
    "Public files contain grids only; the private directory and report contain hidden rule information.",
]


@lru_cache(maxsize=1)
def _canonical_record() -> dict:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    if len(rows) != 1:
        raise ValueError(f"expected one exact canonical record for {TASK_ID}, found {len(rows)}")
    source = rows[0]["program_solution"]
    if digest_bytes(source.encode()) != CANONICAL_SHA256:
        raise ValueError("canonical Racket source changed; reassess the prototype before using it")
    return rows[0]


def canonical_record() -> dict:
    return copy.deepcopy(_canonical_record())


def normalize_parameters(parameters=None) -> dict[str, str]:
    return SPACE.normalize(parameters)


def parameters_from_seed(seed: int) -> dict[str, str]:
    return SPACE.choose(seed, namespace=TASK_ID)


def materialize_rule(parameters=None) -> str:
    """Return exact canonical bytes by default; otherwise swap one branch pair."""
    priority = normalize_parameters(parameters)["crossing_priority"]
    source = _canonical_record()["program_solution"]
    if source.count(HORIZONTAL_BRANCHES) != 1:
        raise ValueError("canonical crossing branch anchor is missing or ambiguous")
    if priority == "horizontal":
        return source
    return source.replace(HORIZONTAL_BRANCHES, VERTICAL_BRANCHES, 1)


def source_hashes() -> dict[str, str]:
    _, _, generator_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    return {
        "prototype.py": digest_bytes(Path(__file__).read_bytes()),
        "episode_tools.py": digest_bytes((HERE / "episode_tools.py").read_bytes()),
        "selected_generator.py": generator_sha256,
        "canonical_record": digest_json(_canonical_record()),
        "canonical_racket": CANONICAL_SHA256,
    }


def sample_inputs(seed: int) -> tuple[list, list]:
    """Choose inputs independently of the hidden rule, with a novel crossing query."""
    validate_seed(seed)
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    inputs, specs = [], []
    for index, profile in enumerate(DEMO_PROFILES):
        inputs.append(generator.generate(seed, index, difficulty="medium", scene_profile=profile))
        specs.append({"sample_index": index, "scene_profile": profile})
    for index in range(4, 68):
        query = generator.generate(seed, index, difficulty="medium", scene_profile="horizontal_precedence")
        if query not in inputs:
            inputs.append(query)
            specs.append({"sample_index": index, "scene_profile": "horizontal_precedence"})
            break
    else:
        raise RuntimeError("could not obtain a crossing query distinct from all demonstrations")
    for grid in inputs:
        errors = generator.strict_canonical_like(grid)
        if errors:
            raise ValueError(f"input violates the selected task grammar: {errors}")
    return inputs, specs


def build_episode(seed: int, *, parameters=None, runner: RacketRunner | None = None) -> dict:
    """Choose a rule once, then label every demonstration and query using Racket."""
    validate_seed(seed)
    selected = parameters_from_seed(seed) if parameters is None else normalize_parameters(parameters)
    if runner is None:
        with RacketRunner() as owned:
            return build_episode(seed, parameters=parameters, runner=owned)
    inputs, specs = sample_inputs(seed)
    source = materialize_rule(selected)
    outputs = runner.run(source, inputs)
    pairs = [{"input": grid, "output": output} for grid, output in zip(inputs, outputs)]
    return {
        "schema": "arc-parametric-crossing-episode-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameter_selection": "seeded" if parameters is None else "explicit",
        "parameters": selected,
        "source_hashes": source_hashes(),
        "program": source,
        "program_sha256": digest_bytes(source.encode()),
        "sample_specs": specs,
        "train": pairs[:4],
        "test": pairs[4:],
    }


def check_episode(episode: Any, *, runner: RacketRunner | None = None) -> dict:
    """Replay labels and require the alternate setting to lose on demonstrations."""
    report: dict[str, Any] = {"passed": False, "failures": [], "candidates": {}}
    try:
        if not isinstance(episode, dict):
            raise ValueError("episode must be a mapping")
        validate_seed(episode.get("seed"))
        selected = normalize_parameters(episode["parameters"])
        if episode["parameters"] != selected:
            raise ValueError("episode parameters must explicitly name every parameter")
        priority = selected["crossing_priority"]
        if episode.get("parameter_selection") == "seeded" and selected != parameters_from_seed(episode["seed"]):
            raise ValueError("parameters disagree with the deterministic episode seed")
        if episode.get("parameter_selection") not in ("seeded", "explicit"):
            raise ValueError("unknown parameter selection mode")
        source = materialize_rule(selected)
        if episode.get("program") != source or episode.get("program_sha256") != digest_bytes(source.encode()):
            raise ValueError("program or program hash disagrees with the selected parameters")
        if episode.get("source_hashes") != source_hashes():
            raise ValueError("episode source hashes differ from the current source snapshot")
        demos, queries = episode["train"], episode["test"]
        if not isinstance(demos, list) or len(demos) != 4 or not isinstance(queries, list) or len(queries) != 1:
            raise ValueError("this prototype requires four demonstrations and one query")
        generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
        for index, pair in enumerate(demos + queries):
            grid_copy(pair["input"])
            grid_copy(pair["output"])
            errors = generator.strict_canonical_like(pair["input"])
            if errors:
                raise ValueError(f"pair {index} violates the input grammar: {errors}")
    except (ValueError, TypeError, KeyError) as exc:
        report["failures"].append(str(exc))
        return report
    if runner is None:
        with RacketRunner() as owned:
            return check_episode(episode, runner=owned)
    programs = {setting: materialize_rule({"crossing_priority": setting}) for setting in PRIORITIES}
    candidates = rival_report(demos, queries, programs, runner=runner)
    report["candidates"] = candidates
    chosen = candidates[priority]
    if chosen["demo_mismatch_indices"] or chosen["query_mismatch_indices"]:
        report["failures"].append("selected Racket program disagrees with retained output labels")
    for rival, result in candidates.items():
        if rival == priority:
            continue
        if not result["refuted_by_demonstrations"]:
            report["failures"].append(f"demonstrations do not refute crossing_priority={rival}")
        if not result["query_mismatch_indices"]:
            report["failures"].append(f"query does not witness a difference against crossing_priority={rival}")
    report.update(passed=not report["failures"], selected_priority=priority,
                  demonstrations=len(demos), queries=len(queries),
                  racket_checked_episode_pairs=len(demos) + len(queries))
    return report


def _canonical_check(runner: RacketRunner) -> dict:
    record = canonical_record()
    pairs = []
    for split in ("train", "test"):
        for index, pair in enumerate(record[split]):
            pairs.append({"split": split, "pair_index": index, **pair})
    observed = runner.run(materialize_rule(), [pair["input"] for pair in pairs])
    rows = [{**pair, "actual": actual, "matches": pair["output"] == actual}
            for pair, actual in zip(pairs, observed)]
    return {"matches": sum(row["matches"] for row in rows), "total": len(rows),
            "exact_source_match": materialize_rule() == record["program_solution"], "pairs": rows}


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def write_bundle(destination: str | Path, *, seeds=(0, 5), parameters=None) -> dict:
    """Write a fresh, hash-bound bundle with complete episodes and exact rules."""
    destination = Path(destination)
    seeds = list(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("episode seeds must be nonempty and unique")
    for seed in seeds:
        validate_seed(seed)
    if parameters is not None:
        normalize_parameters(parameters)
    if destination.exists():
        raise FileExistsError(f"output must be a new directory: {destination}")
    with RacketRunner() as runner:
        episodes = [build_episode(seed, parameters=parameters, runner=runner) for seed in seeds]
        checks = [check_episode(episode, runner=runner) for episode in episodes]
        repeated = [build_episode(seed, parameters=parameters, runner=runner) for seed in seeds]
        deterministic = episodes == repeated
        canonical = _canonical_check(runner)
        witness_input = episodes[0]["train"][2]["input"]
        witness_outputs = {setting: runner.run(materialize_rule({"crossing_priority": setting}),
                                               [witness_input])[0] for setting in PRIORITIES}
        witness = {
            "input": witness_input,
            "outputs": witness_outputs,
            "different_cells": grid_differences(witness_outputs["horizontal"], witness_outputs["vertical"]),
            "lawful": True,
            "origin": {"episode_index": 0, "split": "train", "pair_index": 2},
            "program_sha256": {setting: digest_bytes(materialize_rule({"crossing_priority": setting}).encode())
                               for setting in PRIORITIES},
        }
        execution_receipts = list(runner.executions)
        identity = runner.runtime_identity
    passed = (all(check["passed"] for check in checks) and deterministic
              and canonical["matches"] == canonical["total"] and canonical["exact_source_match"]
              and bool(witness["different_cells"]))
    settings = sorted({episode["parameters"]["crossing_priority"] for episode in episodes})
    report = {
        "schema": "arc-parametric-crossing-bundle-v1", "status": "prototype", "passed": passed,
        "task_id": TASK_ID, "prototype_version": PROTOTYPE_VERSION,
        "parameter_schema": {"crossing_priority": {"allowed": list(PRIORITIES), "default": "horizontal"}},
        "source_hashes": source_hashes(), "runtime_identity": identity,
        "settings_observed": settings, "all_declared_settings_observed": set(settings) == set(PRIORITIES),
        "deterministic_replay": deterministic,
        "counts": {"episodes": len(episodes), "demonstrations": 4 * len(episodes),
                   "queries": len(episodes), "pairs": 5 * len(episodes),
                   "racket_rule_evaluations": len(execution_receipts), "canonical_pairs": canonical["total"]},
        "canonical_default": {key: value for key, value in canonical.items() if key != "pairs"},
        "episodes": [{"index": i, "seed": episode["seed"], "parameters": episode["parameters"],
                      "check": check} for i, (episode, check) in enumerate(zip(episodes, checks))],
        "program_sha256": witness["program_sha256"], "limitations": LIMITATIONS,
    }
    if not passed:
        raise RuntimeError("refusing to retain an invalid episode bundle: " + json.dumps(report))
    destination.mkdir(parents=True)
    for i, episode in enumerate(episodes):
        _write_json(destination / f"private/episode-{i:03d}.json", episode)
        _write_json(destination / f"public/challenge-{i:03d}.json", public_challenge(episode))
    for setting in PRIORITIES:
        path = destination / f"private/rules/{setting}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(materialize_rule({"crossing_priority": setting}), encoding="utf-8")
    _write_json(destination / "private/crossing-witness.json", witness)
    _write_json(destination / "private/canonical-default.json", canonical)
    _write_json(destination / "private/execution-receipts.json", execution_receipts)
    _write_json(destination / "report.json", report)
    manifest = {path.relative_to(destination).as_posix(): digest_bytes(path.read_bytes())
                for path in sorted(destination.rglob("*")) if path.is_file()}
    _write_json(destination / "manifest.json", {"schema": "arc-parametric-artifacts-v1", "files": manifest})
    return report


def verify_bundle(destination: str | Path) -> dict:
    """Check file integrity/public separation, then replay all labels and rivals."""
    destination = Path(destination)
    result = {"passed": False, "failures": [], "counts": {"racket_checked_episode_pairs": 0}}
    try:
        manifest = json.loads((destination / "manifest.json").read_text())["files"]
        actual = {p.relative_to(destination).as_posix(): digest_bytes(p.read_bytes())
                  for p in destination.rglob("*") if p.is_file() and p != destination / "manifest.json"}
        if manifest != actual:
            raise ValueError("bundle file hashes or artifact inventory differ from the manifest")
        retained = json.loads((destination / "report.json").read_text())
        episode_rows = retained.get("episodes")
        if not isinstance(episode_rows, list) or not episode_rows:
            raise ValueError("bundle must list at least one retained episode")
        if any(not isinstance(item, dict) or type(item.get("index")) is not int
               for item in episode_rows):
            raise ValueError("episode inventory requires literal integer indices")
        if [item["index"] for item in episode_rows] != list(range(len(episode_rows))):
            raise ValueError("episode inventory must list each contiguous index exactly once")
        expected_files = {"report.json", "private/crossing-witness.json",
                          "private/canonical-default.json", "private/execution-receipts.json"}
        expected_files.update(f"private/rules/{setting}.rkt" for setting in PRIORITIES)
        for item in episode_rows:
            expected_files.add(f"private/episode-{item['index']:03d}.json")
            expected_files.add(f"public/challenge-{item['index']:03d}.json")
        if set(manifest) != expected_files:
            raise ValueError("artifact inventory does not match all listed public/private episodes")
        for name, expected in {"episodes": len(episode_rows), "demonstrations": 4 * len(episode_rows),
                               "queries": len(episode_rows), "pairs": 5 * len(episode_rows)}.items():
            if retained["counts"].get(name) != expected:
                raise ValueError(f"retained {name} count disagrees with the episode inventory")
        if retained["source_hashes"] != source_hashes():
            raise ValueError("current prototype/generator source differs from the retained report")
        for setting in PRIORITIES:
            if (destination / f"private/rules/{setting}.rkt").read_text() != materialize_rule({"crossing_priority": setting}):
                raise ValueError(f"materialized {setting} program differs from the declared rule")
        episodes = []
        for item in episode_rows:
            i = item["index"]
            episode = json.loads((destination / f"private/episode-{i:03d}.json").read_text())
            public = json.loads((destination / f"public/challenge-{i:03d}.json").read_text())
            if item.get("seed") != episode["seed"] or item.get("parameters") != episode["parameters"]:
                raise ValueError(f"episode {i} metadata differs from the retained report")
            if public != public_challenge(episode):
                raise ValueError(f"public challenge {i} differs from the strict public projection")
            episodes.append(episode)
        with RacketRunner() as runner:
            checks = [check_episode(episode, runner=runner) for episode in episodes]
            canonical = _canonical_check(runner)
            witness = json.loads((destination / "private/crossing-witness.json").read_text())
            for setting in PRIORITIES:
                observed = runner.run(materialize_rule({"crossing_priority": setting}), [witness["input"]])[0]
                if observed != witness["outputs"][setting]:
                    raise ValueError(f"crossing witness output mismatch for {setting}")
            if not grid_differences(witness["outputs"]["horizontal"], witness["outputs"]["vertical"]):
                raise ValueError("crossing witness does not distinguish the declared settings")
            if canonical != json.loads((destination / "private/canonical-default.json").read_text()):
                raise ValueError("retained canonical parity evidence differs from replay")
            result["runtime_identity"] = runner.runtime_identity
            result["counts"].update(episodes=len(episodes), racket_rule_evaluations=len(runner.executions))
        for index, check in enumerate(checks):
            result["failures"].extend(f"episode {index}: {error}" for error in check["failures"])
            result["counts"]["racket_checked_episode_pairs"] += check.get("racket_checked_episode_pairs", 0)
        result["episode_checks"] = checks
        result["canonical_default"] = {key: value for key, value in canonical.items() if key != "pairs"}
        if canonical["matches"] != canonical["total"]:
            result["failures"].append("canonical default parity failed")
        result["passed"] = not result["failures"]
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result["failures"].append(str(exc))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="create a fresh public/private evidence bundle")
    build.add_argument("--out", type=Path, required=True)
    build.add_argument("--seeds", nargs="+", type=int, default=[0, 5])
    build.add_argument("--priority", choices=PRIORITIES, help="pin one rule explicitly; omit for seeded selection")
    verify = commands.add_parser("verify", help="replay a retained bundle with real Racket")
    verify.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            parameters = {"crossing_priority": args.priority} if args.priority is not None else None
            result = write_bundle(args.out, seeds=args.seeds, parameters=parameters)
        else:
            result = verify_bundle(args.directory)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Source-bound Python-mirror diagnostic for every cyclic five-pair lesson.

From the review packet root (the wrapper changes cwd to repo)::

    python3 run_with_racket.py python3 \
      generators/89ab40aedfe4/workspace/probe_schedule.py \
      --seed-start 0 --seeds 10 --out ../checks/schedule-after.json

Use --generator ../checks/independent-review/baseline_generator.py to score
retained source bytes. Canonical data always comes from this script's own tree.
The wrapper may make Racket available, but this probe never executes Racket:
generated labels use rule_mirror and are diagnostic, not Racket certification.
Exit codes: 0 = diagnostic pass, 1 = ambiguity/canonical mismatch, 2 = error.
Existing output paths are refused. Only first failures retain complete grids.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import sys
from types import ModuleType

from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


BANDS = (None, "easy", "medium", "hard")
DECLARATIONS = ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")
DEMONSTRATIONS = 4
PAIR_COUNT = DEMONSTRATIONS + 1


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def grid_hash(grid):
    encoded = json.dumps(grid, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def error_record(exc):
    return {"type": type(exc).__name__, "message": str(exc)}


def add_error(report, stage, exc, **context):
    report["error_count"] += 1
    # Aggregate all errors, but keep repetitive error logs bounded.
    if len(report["errors"]) < 50:
        report["errors"].append({"stage": stage, **context, **error_record(exc)})


def assert_unchanged(path, expected, label):
    actual = file_hash(path)
    if actual != expected:
        raise RuntimeError(f"{label} hash drift: expected {expected}, observed {actual}")


def load_exact_generator(path, report):
    source = path.read_bytes()
    source_hash = hashlib.sha256(source).hexdigest()
    report["provenance"]["generator_path"] = str(path)
    report["provenance"]["generator_sha256"] = source_hash
    name = "schedule_probe_generator_" + source_hash
    module = ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    # Compile the hashed bytes themselves: do not trust a timestamp-based pyc.
    exec(compile(source, str(path), "exec"), module.__dict__)
    assert_unchanged(path, source_hash, "generator during import")
    return module, source_hash


def phase_counter():
    return {"lessons_checked": 0, "demo_fits": 0, "query_disagreements": 0,
            "ambiguities": 0, "errors": 0,
            "first_ambiguous_lesson": None, "first_error_lesson": None}


def declared_rivals(module, report):
    rivals = {}
    for declaration in DECLARATIONS:
        value = getattr(module, declaration, None)
        entry = {"declared_names": [], "valid_names": [], "validation_errors": []}
        report["declarations"][declaration] = entry
        if not isinstance(value, Mapping) or not value:
            exc = ValueError(f"{declaration} must be a nonempty mapping of names to callables")
            entry["validation_errors"].append(str(exc))
            add_error(report, "declaration", exc, declaration=declaration)
            continue
        for name, function in value.items():
            entry["declared_names"].append(name if isinstance(name, str) else repr(name))
            if not isinstance(name, str) or not name or not callable(function):
                exc = ValueError(f"invalid declared rival {name!r}: expected a nonempty name and callable")
                entry["validation_errors"].append(str(exc))
                add_error(report, "declaration", exc, declaration=declaration)
                continue
            key = declaration + "/" + name
            rivals[key] = function
            entry["valid_names"].append(name)
            report["rivals"][key] = {
                "declaration": declaration, "name": name,
                "callable": getattr(function, "__qualname__", repr(function)),
                "production": phase_counter(), "rotation": phase_counter(),
            }
    return rivals


def evaluate(function, grid):
    try:
        return {"output": normalize_grid(function(copy.deepcopy(grid)))}
    except Exception as exc:
        return {"error": error_record(exc)}


def check_canonical(module, rivals, root, report):
    result = {"scope": "all variants, all train pairs and test pairs with labels",
              "helper": "reviewer_support.canonical_pairs(..., labeled_only=True)",
              "usable_pairs": 0, "pairs": [], "mirror": {}, "shortcuts": {}}
    report["canonical"] = result
    pairs = canonical_pairs(module.GENERATOR_ID, root=root, labeled_only=True)
    if not pairs:
        raise ValueError("canonical helpers returned no usable labeled pairs")
    result["usable_pairs"] = len(pairs)
    canonical_functions = {"rule_mirror": module.rule_mirror}
    canonical_functions.update({key: function for key, function in rivals.items()
                                if key.startswith("CANONICAL_SHORTCUTS/")})
    for key in canonical_functions:
        counter = {"checked": 0, "fits": 0, "mismatches": 0, "errors": 0,
                   "first_failure": None, "fits_every_usable_pair": False}
        if key == "rule_mirror":
            result["mirror"] = counter
        else:
            result["shortcuts"][key] = counter
    for pair in pairs:
        identity = {key: pair[key] for key in ("variant", "split", "pair_index")}
        result["pairs"].append({**identity, "input_sha256": grid_hash(pair["input"]),
                                "output_sha256": grid_hash(pair["output"])})
        for key, function in canonical_functions.items():
            counter = result["mirror"] if key == "rule_mirror" else result["shortcuts"][key]
            counter["checked"] += 1
            outcome = evaluate(function, pair["input"])
            if "error" in outcome:
                counter["errors"] += 1
                report["error_count"] += 1
            elif outcome["output"] == pair["output"]:
                counter["fits"] += 1
                continue
            else:
                counter["mismatches"] += 1
            if counter["first_failure"] is None:
                counter["first_failure"] = {
                    **identity, "input": pair["input"], "output": pair["output"],
                    "rival_output": outcome.get("output"), "error": outcome.get("error"),
                }
    for counter in (result["mirror"], *result["shortcuts"].values()):
        counter["fits_every_usable_pair"] = counter["fits"] == len(pairs)
    result["all_declared_shortcuts_fit"] = (
        bool(result["shortcuts"])
        and not report["declarations"]["CANONICAL_SHORTCUTS"]["validation_errors"]
        and all(counter["fits_every_usable_pair"] for counter in result["shortcuts"].values())
    )


def failure_lesson(samples, key, phase, query_position, seed, band, start):
    pairs = []
    for position, sample in enumerate(samples):
        outcome = sample["rival_results"][key]
        pairs.append({"role": "query" if position == query_position else "demo",
                      "position": position, "sample_index": sample["sample_index"],
                      "profile": sample["profile"], "input_sha256": sample["input_sha256"],
                      "input": sample["input"], "output": sample["output"],
                      "rival_output": outcome.get("output"), "rival_error": outcome.get("error")})
    return {"seed": seed, "difficulty": band, "cyclic_start": start, "phase": phase,
            "sample_indices": [sample["sample_index"] for sample in samples],
            "query_position": query_position,
            "query_sample_index": samples[query_position]["sample_index"], "pairs": pairs}


def score_lesson(samples, rivals, report, phase, query_position, seed, band, start):
    total = report["phases"][phase]
    total["lessons_checked"] += 1
    ambiguous = False
    errored = False
    for key in rivals:
        counter = report["rivals"][key][phase]
        counter["lessons_checked"] += 1
        outcomes = [sample["rival_results"][key] for sample in samples]
        if any("error" in outcome for outcome in outcomes):
            counter["errors"] += 1
            total["rival_errors"] += 1
            errored = True
            if counter["first_error_lesson"] is None:
                counter["first_error_lesson"] = failure_lesson(
                    samples, key, phase, query_position, seed, band, start)
            continue
        fits = all(outcome["output"] == sample["output"]
                   for position, (outcome, sample) in enumerate(zip(outcomes, samples))
                   if position != query_position)
        disagrees = outcomes[query_position]["output"] != samples[query_position]["output"]
        counter["demo_fits"] += int(fits)
        counter["query_disagreements"] += int(disagrees)
        if fits and disagrees:
            counter["ambiguities"] += 1
            total["rival_ambiguities"] += 1
            ambiguous = True
            if counter["first_ambiguous_lesson"] is None:
                counter["first_ambiguous_lesson"] = failure_lesson(
                    samples, key, phase, query_position, seed, band, start)
    total["ambiguous_lessons"] += int(ambiguous)
    total["error_lessons"] += int(errored)


def probe(args, report):
    root = find_root(__file__)
    canonical_file = canonical_path(root)
    canonical_hash = file_hash(canonical_file)
    report["provenance"].update({"canonical_root": str(root),
                                 "canonical_path": str(canonical_file),
                                 "canonical_sha256": canonical_hash})
    source_path = args.generator.resolve()
    module, source_hash = load_exact_generator(source_path, report)
    for name in ("GENERATOR_ID", "RULE_HASH"):
        if not isinstance(getattr(module, name, None), str) or not getattr(module, name):
            raise ValueError(f"generator is missing a nonempty {name}")
    report["provenance"].update({"generator_id": module.GENERATOR_ID,
                                 "rule_hash": module.RULE_HASH,
                                 "rule_hash_basis": "generator declaration, not an executed authority hash"})
    if not callable(getattr(module, "generate", None)) or not callable(getattr(module, "rule_mirror", None)):
        raise ValueError("generator must export callable generate and rule_mirror")
    profiles = getattr(module, "SCHEDULE_PROFILES", None)
    if not isinstance(profiles, (tuple, list)) or not profiles or not all(isinstance(p, str) for p in profiles):
        raise ValueError("SCHEDULE_PROFILES must be a nonempty list or tuple of names")
    if not callable(getattr(module, "schedule_profile", None)):
        raise ValueError("generator must export callable schedule_profile")
    rivals = declared_rivals(module, report)
    check_canonical(module, rivals, root, report)
    report["sampling"].update({"schedule_profiles": list(profiles),
                                "cyclic_starts": list(range(len(profiles))),
                                "expected_generate_calls": args.seeds * len(BANDS) * (len(profiles) + 4)})
    base_count = args.seeds * len(BANDS) * len(profiles)
    for phase, multiplier in (("production", 1), ("rotation", PAIR_COUNT)):
        report["phases"][phase] = {
            "lessons_expected": base_count * multiplier, "lessons_checked": 0,
            "ambiguous_lessons": 0, "error_lessons": 0,
            "rival_ambiguities": 0, "rival_errors": 0,
        }
    unique_inputs = set()
    observed_indices = set()
    for seed in range(args.seed_start, args.seed_start + args.seeds):
        for band in BANDS:
            assert_unchanged(source_path, source_hash, "generator")
            cache = {}
            for index in range(len(profiles) + DEMONSTRATIONS):
                report["sampling"]["generate_calls_attempted"] += 1
                observation = {"seed": seed, "difficulty": band, "sample_index": index}
                try:
                    # Raw directed calls only: no production sampler, rejection,
                    # lesson_identifiable filtering, or profile overrides.
                    grid = normalize_grid(module.generate(seed, index, difficulty=band))
                    label = normalize_grid(module.rule_mirror(copy.deepcopy(grid)))
                    profile = module.schedule_profile(seed, index, difficulty=band)
                    if profile not in profiles:
                        raise ValueError(f"schedule_profile returned undeclared profile {profile!r}")
                    observed_indices.add(index)
                    input_hash = grid_hash(grid)
                    unique_inputs.add(input_hash)
                    observation.update({"profile": profile, "input_sha256": input_hash,
                                        "output_sha256": grid_hash(label)})
                    cache[index] = {**observation, "input": grid, "output": label,
                                    "rival_results": {key: evaluate(function, grid)
                                                      for key, function in rivals.items()}}
                    for key, outcome in cache[index]["rival_results"].items():
                        if "error" in outcome:
                            report["error_count"] += 1
                    report["sampling"]["generate_calls_succeeded"] += 1
                except Exception as exc:
                    observation["error"] = error_record(exc)
                    add_error(report, "generate_or_mirror", exc, seed=seed,
                              difficulty=band, sample_index=index)
                report["sampling"]["observations"].append(observation)
            for start in range(len(profiles)):
                indices = list(range(start, start + PAIR_COUNT))
                if not all(index in cache for index in indices):
                    report["sampling"]["unscorable_windows"] += 1
                    continue
                samples = [cache[index] for index in indices]
                score_lesson(samples, rivals, report, "production", 4, seed, band, start)
                for query_position in range(PAIR_COUNT):
                    score_lesson(samples, rivals, report, "rotation", query_position, seed, band, start)
    report["sampling"]["observed_sample_indices"] = sorted(observed_indices)
    report["sampling"]["unique_input_count"] = len(unique_inputs)
    report["sampling"]["unique_input_sha256"] = sorted(unique_inputs)
    assert_unchanged(source_path, source_hash, "generator at completion")
    assert_unchanged(canonical_file, canonical_hash, "canonical ledger at completion")
    report["provenance"]["source_hashes_unchanged"] = True
    report["execution_complete"] = True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--generator", type=Path, default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--out", type=Path, required=True, help="new JSON file; existing paths fail")
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    # lexists also refuses dangling symlinks instead of following them.
    if args.out.exists() or args.out.is_symlink():
        parser.error(f"output path already exists: {args.out}")
    command = [sys.executable, *sys.argv]
    report = {
        "schema": "cyclic-schedule-python-mirror-diagnostic-v1",
        "verification_scope": "Python-mirror diagnostic; not Racket certification",
        "label_basis": "raw generate(seed, sample_index, difficulty=band), labeled with generator.rule_mirror",
        "ambiguity_definition": "rival fits every demonstration and changes the query output",
        "rotation_definition": "hold out each of five labeled pairs; includes the production query at position 4",
        "counting_note": "rival counts are per declaration; a rival in both declarations is counted twice; ambiguous_lessons counts each lesson once",
        "grid_hash_encoding": "SHA-256 of UTF-8 JSON integer matrix using separators=(',', ':')",
        "provenance": {"probe_path": str(Path(__file__).resolve()), "probe_sha256": file_hash(__file__),
                       "command": command, "shell_command": shlex.join(command), "cwd": str(Path.cwd()),
                       "python_version": sys.version.split()[0],
                       "started_utc": datetime.now(timezone.utc).isoformat(), "source_hashes_unchanged": False},
        "sampling": {"seed_start": args.seed_start, "seeds": args.seeds, "bands": list(BANDS),
                     "demonstrations": DEMONSTRATIONS, "query_count": 1,
                     "generate_calls_attempted": 0, "generate_calls_succeeded": 0,
                     "unscorable_windows": 0, "observed_sample_indices": [], "observations": [],
                     "unique_input_count": 0, "unique_input_sha256": []},
        "declarations": {}, "rivals": {}, "phases": {},
        "execution_complete": False, "error_count": 0, "errors": [],
    }
    try:
        probe(args, report)
    except Exception as exc:
        add_error(report, "execution", exc)
    errors = report["error_count"] > 0 or not report["execution_complete"]
    canonical = report.get("canonical", {})
    failure = (not canonical.get("all_declared_shortcuts_fit", False)
               or not canonical.get("mirror", {}).get("fits_every_usable_pair", False)
               or any(phase["ambiguous_lessons"] for phase in report["phases"].values()))
    report["status"] = "error" if errors else "fail" if failure else "pass"
    report["provenance"]["finished_utc"] = datetime.now(timezone.utc).isoformat()
    encoded = json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    try:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as handle:
            handle.write(encoded)
    except OSError as exc:
        print(f"cannot create new output file: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "verification_scope": report["verification_scope"],
                      "out": str(args.out.resolve()), "bytes": len(encoded.encode()),
                      "generator_sha256": report["provenance"].get("generator_sha256"),
                      "phases": report["phases"], "error_count": report["error_count"]}, sort_keys=True))
    return 2 if errors else 1 if failure else 0


if __name__ == "__main__":
    raise SystemExit(main())

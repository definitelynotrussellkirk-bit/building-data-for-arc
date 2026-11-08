"""Bounded protected-Racket self-audit and strict public/private writer.

Run from the packet's outer directory:
  WORK/.venv/bin/python review.py run python3 \
    generators/2ca60ab198d6/workspace/parametric/audit.py --out ../checks/2ca60ab198d6/audit

public/ and public.jsonl are answer-free controller containers holding all four
query inputs. A model receives only current_query_bytes() for its current turn.
All other files are private authoring evidence. This audit neither qualifies
nor accepts the family and does not implement a sequential controller.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import time

TASK = "2ca60ab198d6"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SELECTIONS = ("rows", "rows_then_columns")
SEEDS = (0, 17, 44)
DEMO_COUNTS = (2, 3, 6)
LIMITS = (
    "Finite declared rivals and seeds only; no universal uniqueness claim. "
    "Every retained reference and rival label is executed through protected Racket. "
    "The serialized export verifier checks structure and projection, not another Racket replay. "
    "First-turn equality checks a projection, not an implemented sequential controller. "
    "No native qualification, owner acceptance, or training admission is granted."
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def load_source(path, name):
    """Compile the exact named local bytes, independent of timestamp pyc reuse."""
    path = Path(path)
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
        raise ValueError("audit imports must be regular same-checkout sources")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


_SUPPORT = load_source(ROOT / "shared/runtime/reviewer_support.py", "_row_audit_support")
public_challenge_bytes = _SUPPORT.public_challenge_bytes
public_challenge_id = _SUPPORT.public_challenge_id


def strict_grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("grids require rectangular 1..30 lists of exact integer colors 0..9")
    return value


def validate_episode(episode, demos=None, queries=None):
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    for split, count in (("train", demos), ("test", queries)):
        pairs = episode.get(split)
        if type(pairs) is not list or not pairs or (count is not None and len(pairs) != count):
            raise ValueError(f"incorrect {split} count")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("private pairs require input and output grids")
            strict_grid(pair["input"])
            strict_grid(pair["output"])
    inputs = [json_bytes(pair["input"]) for pair in episode["train"] + episode["test"]]
    if len(inputs) != len(set(inputs)):
        raise ValueError("all demonstration/query inputs must be distinct")
    return episode


def current_query_bytes(episode, index=0):
    """Visible demos plus one current query, with no future/count/answer fields."""
    if type(index) is not int or not 0 <= index < len(episode["test"]):
        raise ValueError("current query index is out of range")
    return public_challenge_bytes({"train": episode["train"],
                                   "test": [{"input": episode["test"][index]["input"]}]})


def prepare_public(episodes):
    """Preflight the complete batch before creating any destination."""
    if type(episodes) is not list or not episodes:
        raise ValueError("a nonempty episode batch is required")
    rows, seen = [], set()
    for episode in episodes:
        validate_episode(episode)
        raw = public_challenge_bytes(episode)
        identifier = public_challenge_id(episode)
        if identifier != digest(raw):
            raise ValueError("public helper identifier and exact bytes disagree")
        if raw in seen:
            raise ValueError("duplicate visible challenge bytes")
        seen.add(raw)
        rows.append((identifier, raw, copy.deepcopy(episode)))
    return sorted(rows, key=lambda row: row[0])


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object field")
        result[key] = value
    return result


def read_json(path):
    def bad_constant(value):
        raise ValueError(f"non-finite JSON constant: {value}")
    return json.loads(Path(path).read_bytes(), object_pairs_hook=_unique_object,
                      parse_constant=bad_constant)


def verify_export(out):
    """Reject byte, projection, type, filename, duplicate, and ordering defects."""
    out = Path(out)
    manifest = read_json(out / "manifest.json")
    expected_members = {"audit.json", "private.json", "public.jsonl", "public"}
    if {p.name for p in out.iterdir()} != expected_members | {"manifest.json"}:
        raise ValueError("unexpected export member")
    if any(p.is_symlink() for p in out.rglob("*")):
        raise ValueError("export symlinks are forbidden")
    private = read_json(out / "private.json")
    rows = prepare_public(private["episodes"])
    if manifest.get("public_order") != [identifier for identifier, _, _ in rows]:
        raise ValueError("manifest public order differs from sorted hash order")
    if any(episode.get("public_id") != identifier for identifier, _, episode in rows):
        raise ValueError("private public identifier differs from visible bytes")
    expected_paths = {f"public/{identifier}.json" for identifier, _, _ in rows}
    if {f"public/{p.name}" for p in (out / "public").iterdir()} != expected_paths:
        raise ValueError("public files must be exactly the hash-named episode projections")
    for identifier, raw, _ in rows:
        path = out / "public" / f"{identifier}.json"
        if not re.fullmatch(r"[0-9a-f]{64}\.json", path.name) or path.read_bytes() != raw:
            raise ValueError("public filename, canonical bytes, or private projection differs")
        value = read_json(path)
        if (type(value) is not dict or set(value) != {"train", "test"}
                or any(set(p) != {"input", "output"} for p in value["train"])
                or any(set(p) != {"input"} for p in value["test"])):
            raise ValueError("public payload contains private fields")
    if (out / "public.jsonl").read_bytes() != b"".join(raw for _, raw, _ in rows):
        raise ValueError("public batch order or bytes differs from sorted hash order")
    expected_files = expected_paths | {"audit.json", "private.json", "public.jsonl"}
    if set(manifest.get("files", {})) != expected_files:
        raise ValueError("manifest file set differs")
    for relative, expected in manifest["files"].items():
        if digest((out / relative).read_bytes()) != expected:
            raise ValueError(f"manifest hash differs: {relative}")
    return {"status": "passed", "public_files": len(rows), "projection_checked": True,
            "reference_labels_replayed": False}


def write_export(out, episodes, evidence):
    """Publish a preflighted, sorted batch into a strictly new directory."""
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(f"refusing existing output: {out}")
    rows = prepare_public(episodes)
    private = copy.deepcopy(evidence)
    private["episodes"] = [dict(episode, public_id=identifier) for identifier, _, episode in rows]
    summary = {key: private[key] for key in ("status", "counts", "racket", "source_hashes", "limits")
               if key in private}
    summary["public_files"] = len(rows)
    files = {f"public/{identifier}.json": raw for identifier, raw, _ in rows}
    files.update({"public.jsonl": b"".join(raw for _, raw, _ in rows),
                  "private.json": json_bytes(private), "audit.json": json_bytes(summary)})
    # Serialize every private field before creating the destination, too.
    manifest = {"files": {name: digest(raw) for name, raw in sorted(files.items())},
                "public_order": [identifier for identifier, _, _ in rows]}
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    for relative, raw in sorted(files.items()):
        (out / relative).write_bytes(raw)
    (out / "manifest.json").write_bytes(json_bytes(manifest))
    return verify_export(out)


def source_hashes():
    paths = [HERE / name for name in ("prototype.py", "adapter.py", "promotion.json", "audit.py")]
    paths += [ROOT / "generators" / TASK / "generator.py",
              ROOT / "shared/data/canonical/puzzles.jsonl",
              ROOT / "shared/runtime/reviewer_support.py",
              ROOT / "shared/runtime/arc_repl/racket_bridge.py",
              ROOT / "shared/runtime/puzzle_generators/rule_wrap.py",
              ROOT / "src/arcpuzzles/parametric_worker.py"]
    paths += sorted((ROOT / "generators" / TASK / "tests").glob("test_*parametric*.py"))
    audit_test = ROOT / "generators" / TASK / "tests/test_audit.py"
    if audit_test.exists():
        paths.append(audit_test)
    return {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in sorted(paths)}


def grid_metrics(grid):
    colors = sorted({cell for row in grid for cell in row})
    selected = [row for row in grid if row[0] == 7]
    return {"shape": [len(grid), len(grid[0])], "colors": colors,
            "selected_rows": len(selected), "selected_columns": selected[0][1:].count(7),
            "nonzero_cells": sum(cell != 0 for row in grid for cell in row),
            "occupied_rows": sum(any(row) for row in grid),
            "occupied_columns": sum(any(row[c] for row in grid) for c in range(len(grid[0])))}


class AuditFailure(ValueError):
    def __init__(self, message, case):
        super().__init__(message)
        self.case = case


def run_audit(timeout=10.0, budget=120.0):
    # Bind imports to this checkout even if another installed arcpuzzles exists.
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    if not Path(sys.modules[_local_imports.__module__].__file__).resolve().is_relative_to(ROOT):
        raise ValueError("parametric worker must come from this checkout")
    before = source_hashes()
    prototype = load_source(HERE / "prototype.py", "_row_audit_prototype")
    adapter = load_source(HERE / "adapter.py", "_row_audit_adapter")
    programs = {s: adapter.program({"selection": s}) for s in SELECTIONS}
    if any(programs[s] != prototype.program({"selection": s}) for s in SELECTIONS):
        raise ValueError("adapter and prototype programs disagree")
    canonical = {row["program_solution"] for row in (
        json.loads(line) for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines())
        if row.get("task_id") == TASK}
    if canonical != {programs["rows"]}:
        raise ValueError("default program differs from exact canonical authority")
    rivals = {s: prototype.rival_programs(s) for s in SELECTIONS}
    registry = {digest(p.encode()): p for p in list(programs.values())
                + [p for group in rivals.values() for p in group.values()]}
    if any(type(p) is not str or not p.strip() for p in registry.values()):
        raise ValueError("reference and rivals need exact nonempty Racket programs")
    result = {"status": "running", "task_id": TASK, "source_hashes": before,
              "command": ["python3", str(Path(__file__).relative_to(ROOT)), *sys.argv[1:]],
              "limits": LIMITS, "programs": registry,
              "reference_programs": {s: digest(p.encode()) for s, p in programs.items()},
              "rival_programs": {s: {name: digest(p.encode()) for name, p in group.items()}
                                 for s, group in rivals.items()},
              "bounds": {"seeds": list(SEEDS), "demo_counts": list(DEMO_COUNTS),
                         "query_counts": [1, 4], "per_call_timeout_seconds": timeout,
                         "audit_time_budget_seconds": budget},
              "checks": [], "failures": [], "boundary_cases": [], "first_turn_checks": []}
    counts = {"jobs_passed": 0, "jobs_failed": 0, "claimed_labels_checked": 0,
              "demo_rival_predictions_checked": 0, "query_conflicts": 0,
              "racket_calls_succeeded": 0, "racket_calls_failed": 0, "racket_cache_hits": 0}
    result["counts"] = counts
    cache, witnesses, retained, input_inventory = {}, {}, [], {}
    matched_inputs, independent_counts = {}, {}
    deadline = time.monotonic() + budget
    with _local_imports(ROOT / "shared/runtime", HERE):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        bridge.timeout = timeout
        result["racket"] = identity

        def execute(program, grid, context):
            key = (program, json_bytes(strict_grid(grid)))
            if key in cache:
                counts["racket_cache_hits"] += 1
                return copy.deepcopy(cache[key])
            if time.monotonic() >= deadline:
                raise AuditFailure("bounded audit time budget exceeded", context)
            try:
                output = strict_grid(apply(program, copy.deepcopy(grid)))
            except Exception as exc:
                counts["racket_calls_failed"] += 1
                raise AuditFailure(f"Racket execution/type failure: {type(exc).__name__}: {exc}",
                                   dict(context, input=grid, program_sha256=digest(program.encode()))) from exc
            counts["racket_calls_succeeded"] += 1
            cache[key] = copy.deepcopy(output)
            return output

        try:
            for selection in SELECTIONS:
                for seed in SEEDS:
                    for demos in DEMO_COUNTS:
                        context = {"settings": {"selection": selection}, "seed": seed,
                                   "demos": demos, "queries": 4}
                        try:
                            episode = validate_episode(adapter.generate(seed, context["settings"], demos, 4), demos, 4)
                            if (episode.get("program_solution") != programs[selection]
                                    or episode.get("settings") != context["settings"]
                                    or type(episode.get("seed")) is not int or episode["seed"] != seed):
                                raise AuditFailure("episode rule or private request metadata differs", context)
                            input_list = [pair["input"] for pair in episode["train"] + episode["test"]]
                            match_key = (seed, demos)
                            if match_key in matched_inputs and matched_inputs[match_key] != input_list:
                                raise AuditFailure("input sampling depends on private setting", context)
                            matched_inputs[match_key] = input_list
                            count_key = (selection, seed)
                            previous = independent_counts.get(count_key)
                            if previous is not None:
                                common = min(len(previous["train"]), demos)
                                if (previous["test"] != episode["test"]
                                        or previous["train"][:common] != episode["train"][:common]):
                                    raise AuditFailure("demo count changes query draws or demonstration prefixes", context)
                            independent_counts[count_key] = episode
                            pair_checks = []
                            for split in ("train", "test"):
                                for index, pair in enumerate(episode[split]):
                                    at = dict(context, split=split, pair_index=index)
                                    errors = prototype.domain_errors(pair["input"])
                                    if errors:
                                        raise AuditFailure("generated input outside admitted grammar", dict(at, errors=errors))
                                    output = execute(programs[selection], pair["input"], at)
                                    if output != pair["output"]:
                                        raise AuditFailure("claimed label disagrees with Racket",
                                                           dict(at, input=pair["input"], claimed=pair["output"], output=output))
                                    counts["claimed_labels_checked"] += 1
                                    inp_id = digest(json_bytes(pair["input"]))
                                    input_inventory[inp_id] = grid_metrics(pair["input"])
                                    pair_checks.append({"split": split, "pair_index": index,
                                                        "input_sha256": inp_id,
                                                        "output_sha256": digest(json_bytes(output)),
                                                        "output_shape": [len(output), len(output[0])]})
                            rejected, surviving, conflicts = {}, [], []
                            for name, program in sorted(rivals[selection].items()):
                                mismatch = []
                                for index, pair in enumerate(episode["train"]):
                                    at = dict(context, split="train", pair_index=index, rival=name)
                                    output = execute(program, pair["input"], at)
                                    counts["demo_rival_predictions_checked"] += 1
                                    if output != pair["output"]:
                                        mismatch.append(index)
                                        witness = dict(at, input=pair["input"], output=pair["output"],
                                                       rival_output=output, program_sha256=digest(programs[selection].encode()),
                                                       rival_program_sha256=digest(program.encode()))
                                        key = (selection, name)
                                        area = len(pair["input"]) * len(pair["input"][0])
                                        old = witnesses.get(key)
                                        if old is None or area < len(old["input"]) * len(old["input"][0]):
                                            witnesses[key] = witness
                                if mismatch:
                                    rejected[name] = mismatch
                                else:
                                    surviving.append(name)
                                    for index, pair in enumerate(episode["test"]):
                                        output = execute(program, pair["input"], dict(context, split="test", pair_index=index, rival=name))
                                        if output != pair["output"]:
                                            conflicts.append({"rival": name, "query_index": index,
                                                              "input": pair["input"], "output": pair["output"],
                                                              "rival_output": output})
                            counts["query_conflicts"] += len(conflicts)
                            check = dict(context, pairs=pair_checks, rejected_by_demo=rejected,
                                         demo_survivors=surviving, query_conflicts=conflicts)
                            result["checks"].append(check)
                            if surviving:
                                raise AuditFailure("visible demonstrations leave a declared rival alive", check)
                            one = validate_episode(adapter.generate(seed, context["settings"], demos, 1), demos, 1)
                            first, only = current_query_bytes(episode), current_query_bytes(one)
                            if first != only or one["train"] != episode["train"] or one["test"] != episode["test"][:1]:
                                raise AuditFailure("first turn changes with requested query count", context)
                            changed = copy.deepcopy(episode)
                            changed.update(seed=seed + 1, settings={"selection": "private-change"}, program_solution="private-change")
                            for pair in changed["test"]:
                                pair["output"] = [[9]]
                            changed["test"][1:4] = [{"input": [[9]], "output": [[9]]}]
                            if current_query_bytes(changed) != first:
                                raise AuditFailure("first turn leaks private or future fields", context)
                            result["first_turn_checks"].append(dict(context, bytes_sha256=digest(first),
                                                                   one_query_equals_four=True,
                                                                   private_and_future_fields_ignored=True))
                            if seed == 0 and demos == 3:
                                retained.append({key: copy.deepcopy(episode[key]) for key in
                                                 ("seed", "settings", "program_solution", "train", "test")})
                            counts["jobs_passed"] += 1
                        except (AuditFailure, ValueError, TypeError, KeyError) as exc:
                            counts["jobs_failed"] += 1
                            result["failures"].append({"message": str(exc),
                                                       "case": getattr(exc, "case", context)})
            # Exercise real count extrema as well as the ordinary 30x30 query.
            for selection in SELECTIONS:
                for name, profile in (("minimum", (6, 7, 3, 2, .35)),
                                      ("maximum", (30, 30, 28, 27, .80))):
                    h, w, nr, nc, density = profile
                    grid = prototype.make_input(0, 501 if name == "minimum" else 502,
                                                height=h, width=w, n_keep=nr,
                                                n_columns=nc, density=density)
                    at = {"settings": {"selection": selection}, "boundary": name}
                    output = execute(programs[selection], grid, at)
                    if output != prototype.interpret(grid, selection):
                        raise AuditFailure("boundary claimed label disagrees with Racket", dict(at, input=grid, output=output))
                    counts["claimed_labels_checked"] += 1
                    result["boundary_cases"].append(dict(at, input=grid, output=output,
                                                        program_sha256=digest(programs[selection].encode()),
                                                        metrics=grid_metrics(grid)))
        except AuditFailure as exc:
            result["failures"].append({"message": str(exc), "case": exc.case})
        finally:
            bridge.close()
    if before != source_hashes():
        result["failures"].append({"message": "audited source changed during execution"})
    result["rival_witnesses"] = [witnesses[key] for key in sorted(witnesses)]
    result["input_diversity"] = {"unique_inputs": len(input_inventory),
        "shapes": sorted({tuple(m["shape"]) for m in input_inventory.values()}),
        "selected_row_counts": sorted({m["selected_rows"] for m in input_inventory.values()}),
        "selected_column_counts": sorted({m["selected_columns"] for m in input_inventory.values()}),
        "input_metrics": input_inventory}
    counts["rival_witnesses"] = len(witnesses)
    counts["retained_episodes"] = len(retained)
    counts["boundary_labels_checked"] = len(result["boundary_cases"])
    result["status"] = "passed" if not result["failures"] and len(retained) == 2 else "failed"
    return retained, result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out", type=Path)
    mode.add_argument("--verify", type=Path)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--budget", type=float, default=120.0)
    args = parser.parse_args(argv)
    try:
        if args.verify:
            print(json.dumps(verify_export(args.verify), sort_keys=True))
            return 0
        if not 1 <= args.timeout <= 30 or not 10 <= args.budget <= 300:
            raise ValueError("timeout must be 1..30 seconds and total budget 10..300 seconds")
        if args.out.exists() or args.out.is_symlink():
            raise FileExistsError(f"refusing existing output: {args.out}")
        episodes, evidence = run_audit(args.timeout, args.budget)
        if evidence["status"] != "passed":
            args.out.mkdir(parents=True, exist_ok=False)
            (args.out / "failure.private.json").write_bytes(json_bytes(evidence))
            print(json.dumps({"status": "failed", "counts": evidence["counts"],
                              "failures": evidence["failures"], "out": str(args.out)}, sort_keys=True))
            return 1
        verification = write_export(args.out, episodes, evidence)
        print(json.dumps({"status": "passed", "counts": evidence["counts"],
                          "export": verification, "out": str(args.out)}, sort_keys=True))
        return 0
    except (ValueError, TypeError, FileExistsError, OSError) as exc:
        print(json.dumps({"status": "failed", "error": type(exc).__name__, "message": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Bounded protected-Racket teaching audit with strict one-query public views.

The serialized verifier checks hashes and projections, not another Racket replay
or authenticity of an entirely rewritten bundle. No acceptance is performed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "80a3c4f25880"
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "src"))
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name + sha(str(path).encode()), path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_support = _module(ROOT / "shared/runtime/reviewer_support.py", "_public_80a3c4f25880_")


class AuditFailure(ValueError):
    def __init__(self, message, **details):
        super().__init__(message)
        self.details = details


def _pairs(episode, demos, queries):
    if not isinstance(episode, dict):
        raise ValueError("episode must be a dictionary")
    result = {}
    for split, count in (("train", demos), ("test", queries)):
        pairs = episode.get(split)
        if type(count) is not int or count < 1 or type(pairs) is not list or len(pairs) != count:
            raise ValueError("episode count differs for " + split)
        result[split] = []
        for pair in pairs:
            if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
                raise ValueError("each private pair needs input/output grids")
            result[split].append({"input": _grid(pair["input"]), "output": _grid(pair["output"])})
    inputs = [raw(p["input"]) for pairs in result.values() for p in pairs]
    if len(set(inputs)) != len(inputs):
        raise ValueError("all demonstration/query inputs must be distinct; duplicate input found")
    return result


def verify_episode(episode, program, execute, *, demos, queries):
    """Reject malformed or unexecuted claimed labels; retain actual outputs."""
    if type(program) is not str or not program.strip() or episode.get("program_solution") != program:
        raise ValueError("episode program_solution differs from the selected program")
    normalized = _pairs(episode, demos, queries)
    for split, pairs in normalized.items():
        for index, pair in enumerate(pairs):
            actual = _grid(execute(program, deepcopy(pair["input"])))
            if actual != pair["output"]:
                raise AuditFailure("claimed label differs from executed Racket output", split=split,
                                   pair_index=index, input=pair["input"],
                                   claimed_output=pair["output"], executed_output=actual,
                                   program=program)
            pair["output"] = actual
    return {**deepcopy(episode), **normalized}


def public_bytes(visible):
    """Do not let the shared projection silently discard a private-field leak."""
    if type(visible) is not dict or set(visible) != {"train", "test"}:
        raise ValueError("public challenge may contain only train and test")
    if type(visible["train"]) is not list or not visible["train"]:
        raise ValueError("public challenge needs visible demonstrations")
    if type(visible["test"]) is not list or len(visible["test"]) != 1:
        raise ValueError("public challenge must show exactly one query input")
    if any(type(p) is not dict or set(p) != {"input", "output"} for p in visible["train"]):
        raise ValueError("public demonstration contains an extra or missing visible field")
    if type(visible["test"][0]) is not dict or set(visible["test"][0]) != {"input"}:
        raise ValueError("public query must contain its input only")
    return _support.public_challenge_bytes(visible)


def verify_public_bytes(payload, identifier):
    visible = json.loads(payload)
    if public_bytes(visible) != payload:
        raise ValueError("public bytes differ from strict canonical projection")
    if (type(identifier) is not str or not re.fullmatch("[0-9a-f]{64}", identifier)
            or _support.public_challenge_id(visible) != identifier or sha(payload) != identifier):
        raise ValueError("public identity/hash does not match exact visible bytes")
    return visible


def _public(episode, index):
    return {"train": deepcopy(episode["train"]),
            "test": [{"input": deepcopy(episode["test"][index]["input"])}]}


def _empty_output(output):
    output = Path(output)
    if output.is_symlink() or (output.exists() and (not output.is_dir() or any(output.iterdir()))):
        raise FileExistsError("Output directory must be new or empty: " + str(output))
    return output


def export_episodes(episodes, output, projector):
    """Export previously executed episodes; this helper does not execute rules."""
    output = _empty_output(output)
    planned = []
    for episode_index, episode in enumerate(episodes):
        _pairs(episode, len(episode["train"]), len(episode["test"]))
        for query_index in range(len(episode["test"])):
            payload = public_bytes(projector(episode, query_index))
            if payload != public_bytes(_public(episode, query_index)):
                raise ValueError("public projection differs from the executed episode")
            identifier = _support.public_challenge_id(json.loads(payload))
            verify_public_bytes(payload, identifier)
            planned.append((identifier, payload, {"public_id": identifier,
                           "episode_index": episode_index, "query_index": query_index}))
    planned.sort(key=lambda item: item[0])
    if len({item[0] for item in planned}) != len(planned):
        raise ValueError("duplicate visible challenge in export")
    private = raw({"schema": "arcpuzzles-task-audit-private-v1", "task_id": TASK,
                   "episodes": episodes, "public_index": [item[2] for item in planned]})
    files = [{"path": f"public/{identifier}.json", "sha256": identifier, "bytes": len(payload)}
             for identifier, payload, _ in planned]
    files.append({"path": "private.json", "sha256": sha(private), "bytes": len(private)})
    manifest = {"schema": "arcpuzzles-task-audit-export-v1", "episodes": len(episodes),
                "public_count": len(planned), "files": files, "training_admitted": False}
    output.mkdir(parents=True, exist_ok=True)
    (output / "public").mkdir()
    for identifier, payload, _ in planned:
        (output / "public" / f"{identifier}.json").write_bytes(payload)
    (output / "private.json").write_bytes(private)
    (output / "export_manifest.json").write_bytes(raw(manifest))
    return verify_export(output)


def verify_export(output):
    output = Path(output)
    manifest = json.loads((output / "export_manifest.json").read_bytes())
    if manifest.get("schema") != "arcpuzzles-task-audit-export-v1":
        raise ValueError("wrong export manifest schema")
    files = manifest.get("files")
    if type(files) is not list or not files:
        raise ValueError("missing serialized file inventory")
    paths = [item["path"] for item in files]
    actual = {"private.json"} | {p.relative_to(output).as_posix() for p in (output / "public").iterdir()}
    if len(paths) != len(set(paths)) or set(paths) != actual:
        raise ValueError("serialized file inventory differs")
    for item in files:
        name = item["path"]
        if name != "private.json" and not re.fullmatch(r"public/[0-9a-f]{64}\.json", name):
            raise ValueError("unsafe serialized path")
        path = output / name
        if path.is_symlink():
            raise ValueError("symlink in serialized export")
        payload = path.read_bytes()
        if len(payload) != item["bytes"] or sha(payload) != item["sha256"]:
            raise ValueError("serialized file bytes/hash differ: " + name)
    private = json.loads((output / "private.json").read_bytes())
    episodes, index = private["episodes"], private["public_index"]
    if len(episodes) != manifest["episodes"] or len(index) != manifest["public_count"]:
        raise ValueError("serialized episode/public counts differ")
    for episode in episodes:
        _pairs(episode, len(episode["train"]), len(episode["test"]))
    ids = [row["public_id"] for row in index]
    if any(type(identifier) is not str or not re.fullmatch("[0-9a-f]{64}", identifier) for identifier in ids):
        raise ValueError("invalid public identity in index")
    if ids != sorted(set(ids)):
        raise ValueError("public identity index is not unique and sorted")
    if set(paths) - {"private.json"} != {f"public/{identifier}.json" for identifier in ids}:
        raise ValueError("public file inventory differs from indexed identities")
    pairs = set()
    for row in index:
        i, q = row["episode_index"], row["query_index"]
        if (type(i) is not int or not 0 <= i < len(episodes) or type(q) is not int
                or not 0 <= q < len(episodes[i]["test"]) or (i, q) in pairs):
            raise ValueError("invalid or duplicate public index position")
        pairs.add((i, q))
        payload = (output / "public" / f"{row['public_id']}.json").read_bytes()
        visible = verify_public_bytes(payload, row["public_id"])
        if public_bytes(visible) != public_bytes(_public(episodes[i], q)):
            raise ValueError("public/private projection differs")
    if pairs != {(i, q) for i, e in enumerate(episodes) for q in range(len(e["test"]))}:
        raise ValueError("public index does not cover every private query")
    return manifest


def _source_hashes():
    paths = {p for p in HERE.rglob("*") if p.is_file() and p.suffix in {".py", ".rkt", ".json"}
             and not {"evidence", "examples", "__pycache__"}.intersection(p.relative_to(HERE).parts)}
    paths.update((HERE.parents[1] / "tests").glob("test_parametric*.py"))
    paths.update(ROOT / name for name in (
        f"generators/{TASK}/generator.py", "src/arcpuzzles/parametric_worker.py",
        "shared/runtime/reviewer_support.py", "shared/runtime/puzzle_generators/rule_wrap.py",
        "shared/tools/comment_solutions.py"))
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(paths)}


def _coverage(descriptions):
    def shapes(field):
        return dict(sorted(Counter("x".join(map(str, row[field])) for row in descriptions).items()))
    grouped = {}
    for row in descriptions:
        key = json.dumps(row["settings"], sort_keys=True)
        group = grouped.setdefault(key, {"selected_rows": [], "tie_examples": 0})
        if row.get("selected_row") is not None:
            group["selected_rows"].append(row["selected_row"])
        group["tie_examples"] += len(row.get("tied_rows", [])) > 1
    return {"keys": sorted({row["key"] for row in descriptions}),
            "input_shapes": shapes("input_shape"), "output_shapes": shapes("output_shape"),
            "max_input_side": max(max(row["input_shape"]) for row in descriptions),
            "exact_30x30_inputs": sum(row["input_shape"] == [30, 30] for row in descriptions),
            "nonzero_input_density_range": [min(row["measured_nonzero_fraction"] for row in descriptions),
                                             max(row["measured_nonzero_fraction"] for row in descriptions)],
            "object_cell_range": [min(row["object_cells"] for row in descriptions),
                                  max(row["object_cells"] for row in descriptions)],
            "settings": grouped, "descriptions": descriptions}


def audit(output, seeds):
    output = _empty_output(output)
    if (not 1 <= len(seeds) <= 2 or len(set(seeds)) != len(seeds)
            or any(type(s) is not int or not 0 <= s <= 2**63 - 1 for s in seeds)):
        raise ValueError("Use one or two distinct integer seeds in 0..2**63-1")
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.parametric_promotion import settings_space
    before = _source_hashes()
    adapter = _module(HERE / "adapter.py", "_audit_adapter_80a3c4f25880_")
    prototype = _module(HERE / "prototype.py", "_audit_prototype_80a3c4f25880_")
    contract = json.loads((HERE / "promotion.json").read_bytes())
    settings = settings_space(contract)
    if len(settings) != 3:
        raise ValueError("This bounded audit requires exactly three declared settings")
    canonical = (HERE / "canonical.rkt").read_bytes()
    catalog = Catalog(ROOT)
    selected = catalog.describe(TASK)
    authority = selected.get("rule_task_id", TASK)
    programs = {v["program_solution"] for v in catalog._variants()[authority]}
    if programs != {canonical.decode()} or adapter.program(contract["default"]).encode() != canonical:
        raise ValueError("Default and canonical.rkt must match the selected canonical authority byte-for-byte")
    binding = {"task_id": TASK, "generator_sha256": before[f"generators/{TASK}/generator.py"],
               "canonical_rule_hash": selected["rule_hash"], "canonical_program_sha256": sha(canonical),
               "source_hashes": before}
    failures, witnesses, episodes, comparisons, descriptions = [], [], [], [], []
    cache, program_sources = {}, {}
    evaluations = cache_hits = 0
    common_inputs = {}
    with _local_imports(ROOT / "shared/runtime", HERE):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        def execute(program, grid):
            nonlocal evaluations, cache_hits
            key = (program, raw(grid))
            program_sources[sha(program.encode())] = program
            if key in cache:
                cache_hits += 1
            else:
                evaluations += 1
                cache[key] = _grid(apply(program, deepcopy(grid)))
            return deepcopy(cache[key])
        try:
            for seed in seeds:
                for setting in settings:
                    try:
                        value = adapter.generate(seed, deepcopy(setting), 3, 4)
                        value.update(seed=seed, settings=deepcopy(setting))
                        episode = verify_episode(value, adapter.program(setting), execute, demos=3, queries=4)
                        inputs = [p["input"] for p in episode["train"] + episode["test"]]
                        if seed in common_inputs and common_inputs[seed] != inputs:
                            raise ValueError("sampler inputs differ across settings")
                        common_inputs[seed] = inputs
                        short = adapter.generate(seed, deepcopy(setting), 3, 1)
                        extended = adapter.generate(seed, deepcopy(setting), 6, 4)
                        _pairs(short, 3, 1)
                        _pairs(extended, 6, 4)
                        if (public_bytes(prototype.public_turn(short, 0)) !=
                                public_bytes(prototype.public_turn(episode, 0))
                                or extended["train"][:3] != episode["train"]
                                or extended["test"] != episode["test"]):
                            raise ValueError("count independence or one-query/four-query first-turn stability failed")
                        episodes.append(episode)
                        for split in ("train", "test"):
                            for index, pair in enumerate(episode[split]):
                                metadata = prototype.describe(pair["input"], setting)
                                grid = pair["input"]
                                descriptions.append({**metadata, "seed": seed, "settings": setting,
                                    "split": split, "index": index, "input_shape": [len(grid), len(grid[0])],
                                    "output_shape": [len(pair["output"]), len(pair["output"][0])],
                                    "measured_nonzero_fraction": sum(v != 0 for r in grid for v in r) / (len(grid) * len(grid[0]))})
                    except Exception as error:
                        failure = {"kind": "episode_failed", "seed": seed, "settings": setting,
                                   "error": f"{type(error).__name__}: {error}"}
                        if isinstance(error, AuditFailure):
                            failure["witness"] = error.details
                        failures.append(failure)

            for episode in episodes:
                setting, seed = episode["settings"], episode["seed"]
                candidates = [("alternate_setting", raw(other).decode().strip(), adapter.program(other))
                              for other in settings if other != setting]
                candidates += [("named_rival", name, program) for name, program in prototype.rivals(setting).items()]
                for kind, name, program in candidates:
                    row = {"seed": seed, "settings": setting, "kind": kind, "name": name,
                           "program_sha256": sha(program.encode()), "backend": "protected_racket"}
                    try:
                        demos = [execute(program, p["input"]) for p in episode["train"]]
                        refuted = [i for i, p in enumerate(episode["train"]) if demos[i] != p["output"]]
                        row.update(demonstration_refutations=refuted, query_mismatches=None,
                                   query_audit="not_needed_refuted_on_demo" if refuted else "executed")
                        if refuted:
                            row["status"] = "refuted_on_demonstrations"
                        else:
                            outputs = [execute(program, p["input"]) for p in episode["test"]]
                            mismatches = [i for i, p in enumerate(episode["test"]) if outputs[i] != p["output"]]
                            row.update(query_mismatches=mismatches,
                                       status="ambiguous_queries" if mismatches else "consistent_on_support")
                            if mismatches or kind == "alternate_setting":
                                failures.append({"kind": "teaching_ambiguity", "seed": seed,
                                                 "settings": setting, "candidate": name, "query_mismatches": mismatches})
                            if mismatches:
                                q = min(mismatches, key=lambda i: len(episode["test"][i]["input"]) * len(episode["test"][i]["input"][0]))
                                witnesses.append({"seed": seed, "settings": setting, "candidate": name,
                                    "train": episode["train"], "query_index": q, "query": episode["test"][q],
                                    "rival_output": outputs[q], "program": episode["program_solution"],
                                    "rival_program": program, "selection": "smallest differing checked query; no cell minimization"})
                    except Exception as error:
                        row.update(status="execution_failed", error=f"{type(error).__name__}: {error}")
                        failures.append({"kind": "rival_execution_failed", **row})
                    comparisons.append(row)
        finally:
            bridge.close()
    if _source_hashes() != before:
        failures.append({"kind": "source_changed_during_audit"})
    export = export_episodes(episodes, output, prototype.public_turn)
    witness_bytes = raw({"schema": "arcpuzzles-task-audit-witnesses-v1", "source_binding": binding,
                         "racket": identity, "witnesses": witnesses})
    (output / "witnesses.json").write_bytes(witness_bytes)
    report = {"schema": "arcpuzzles-parametric-teaching-audit-v1", "status": "failed" if failures else "passed",
              "source_binding": binding, "racket": identity, "seeds": seeds,
              "counts": {"planned_jobs": len(seeds) * len(settings), "executed_episodes": len(episodes),
                         "demonstrations": 3, "queries": 4, "intended_labels_verified": len(episodes) * 7,
                         "racket_evaluations": evaluations, "cache_hits": cache_hits,
                         "candidate_comparisons": len(comparisons), "public_files": export["public_count"]},
              "coverage": _coverage(descriptions) if descriptions else {},
              "rivals": comparisons, "failures": failures, "program_sources": program_sources,
              "export_manifest_sha256": sha((output / "export_manifest.json").read_bytes()),
              "witnesses_sha256": sha(witness_bytes), "training_admitted": False,
              "limits": "One or two seeds, three settings, and finite declared rivals only. All intended labels "
                        "were executed; short/extended requests check count and visibility invariance only. "
                        "Candidates fit demonstrations only; refuted candidates' queries are not executed. "
                        "Execution errors fail the audit. No universal identifiability, native qualification, "
                        "owner acceptance, training admission, or reauthentication of rewritten artifacts."}
    (output / "report.json").write_bytes(raw(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append", help="At most two distinct seeds; default 0 and 17")
    args = parser.parse_args(argv)
    try:
        report = audit(args.out, [0, 17] if args.seed is None else args.seed)
    except Exception as error:
        print(json.dumps({"status": "failed", "error": f"{type(error).__name__}: {error}"}), file=sys.stderr)
        return 1
    print(json.dumps({key: report[key] for key in ("status", "counts", "failures")}, sort_keys=True))
    return int(report["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())

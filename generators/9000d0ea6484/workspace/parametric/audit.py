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
TASK = "9000d0ea6484"
SCREENED_DEMOS = 4
CANONICAL_PAIRS = 7
SETTING_COUNT = 12
SECTION_STARTS = (0, 5, 10, 15)
GAP_RIVALS = {"densest": "ignore_anchor_candidate_1", "sparsest": "ignore_anchor_candidate_3"}
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


_support = _module(ROOT / "shared/runtime/reviewer_support.py", "_public_9000d0ea6484_")


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


def make_teaching_gap(episode, candidate, rival_program, demonstration_outputs, *, episode_index):
    """Retain a prefix ambiguity using already executed labels; never execute here."""
    pairs = _pairs(episode, len(episode["train"]), len(episode["test"]))
    if (type(episode_index) is not int or episode_index < 0
            or len(pairs["train"]) < SCREENED_DEMOS
            or type(demonstration_outputs) is not list
            or len(demonstration_outputs) != SCREENED_DEMOS):
        raise ValueError("teaching gap needs the complete screened demonstration outputs")
    outputs = [_grid(value) for value in demonstration_outputs]
    prefix = SCREENED_DEMOS - 1
    if any(outputs[i] != pairs["train"][i]["output"] for i in range(prefix)):
        raise ValueError("rival does not fit the original demonstration prefix")
    query = pairs["train"][prefix]
    actual, rival = query["output"], outputs[prefix]
    if len(actual) != len(rival) or any(len(a) != len(b) for a, b in zip(actual, rival)):
        raise ValueError("teaching gap outputs must have matching dimensions")
    differences = [{"row": r, "column": c, "intended": a, "rival": b}
                   for r, (row, other) in enumerate(zip(actual, rival))
                   for c, (a, b) in enumerate(zip(row, other)) if a != b]
    if not differences:
        raise ValueError("teaching gap requires an actual query difference")
    return {"private_episode_index": episode_index, "seed": episode["seed"],
            "settings": deepcopy(episode["settings"]), "candidate": candidate,
            "lesson_origin": "author-proposed three-demo prefix; not production or legacy output",
            "original_demo_count": prefix, "query_from_train_index": prefix,
            "original_lesson": {"train": deepcopy(pairs["train"][:prefix]), "test": [deepcopy(query)]},
            "program": episode["program_solution"], "rival_program": rival_program,
            "rival_demonstration_outputs": outputs[:prefix], "rival_query_output": rival,
            "rival_fits_original_demonstrations": True,
            "differences": differences, "changed_cells": len(differences),
            "repaired_demo_count": SCREENED_DEMOS,
            "repaired_demonstration_refutations": [prefix],
            "repaired_queries": deepcopy(pairs["test"]),
            "repaired_queries_are_distinct_from_demonstrations": True,
            "additional_racket_evaluations": 0}


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


def export_episodes(episodes, output, projector, *, teaching_gap=None):
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
    gap_payload = raw(teaching_gap) if teaching_gap is not None else None
    if gap_payload is not None:
        files.append({"path": "teaching-gap.json", "sha256": sha(gap_payload), "bytes": len(gap_payload)})
    manifest = {"schema": "arcpuzzles-task-audit-export-v1", "episodes": len(episodes),
                "public_count": len(planned), "files": files, "training_admitted": False}
    output.mkdir(parents=True, exist_ok=True)
    (output / "public").mkdir()
    for identifier, payload, _ in planned:
        (output / "public" / f"{identifier}.json").write_bytes(payload)
    (output / "private.json").write_bytes(private)
    if gap_payload is not None:
        (output / "teaching-gap.json").write_bytes(gap_payload)
    (output / "export_manifest.json").write_bytes(raw(manifest))
    return verify_export(output)


def verify_export(output):
    output = Path(output)
    manifest = json.loads((output / "export_manifest.json").read_bytes())
    if (type(manifest) is not dict
            or set(manifest) != {"schema", "episodes", "public_count", "files", "training_admitted"}
            or manifest.get("schema") != "arcpuzzles-task-audit-export-v1"):
        raise ValueError("wrong export manifest schema")
    if (any(type(manifest[name]) is not int or manifest[name] < 0
            for name in ("episodes", "public_count"))
            or manifest["training_admitted"] is not False):
        raise ValueError("export manifest needs literal integer counts and no admission")
    files = manifest.get("files")
    if type(files) is not list or not files:
        raise ValueError("missing serialized file inventory")
    if any(type(item) is not dict or set(item) != {"path", "sha256", "bytes"}
           or type(item["path"]) is not str or type(item["bytes"]) is not int
           or item["bytes"] < 0 or type(item["sha256"]) is not str
           or not re.fullmatch("[0-9a-f]{64}", item["sha256"]) for item in files):
        raise ValueError("invalid serialized manifest file schema")
    paths = [item["path"] for item in files]
    actual = {"private.json"} | {p.relative_to(output).as_posix() for p in (output / "public").iterdir()}
    private_names = {"private.json", "teaching-gap.json"}
    if (output / "teaching-gap.json").exists():
        actual.add("teaching-gap.json")
    if len(paths) != len(set(paths)) or set(paths) != actual:
        raise ValueError("serialized file inventory differs")
    for item in files:
        name = item["path"]
        if name not in private_names and not re.fullmatch(r"public/[0-9a-f]{64}\.json", name):
            raise ValueError("unsafe serialized path")
        path = output / name
        if path.is_symlink():
            raise ValueError("symlink in serialized export")
        payload = path.read_bytes()
        if len(payload) != item["bytes"] or sha(payload) != item["sha256"]:
            raise ValueError("serialized file bytes/hash differ: " + name)
    private = json.loads((output / "private.json").read_bytes())
    if (type(private) is not dict
            or set(private) != {"schema", "task_id", "episodes", "public_index"}
            or private.get("schema") != "arcpuzzles-task-audit-private-v1"
            or private.get("task_id") != TASK
            or type(private.get("episodes")) is not list
            or type(private.get("public_index")) is not list):
        raise ValueError("private task/schema envelope differs")
    episodes, index = private["episodes"], private["public_index"]
    if len(episodes) != manifest["episodes"] or len(index) != manifest["public_count"]:
        raise ValueError("serialized episode/public counts differ")
    for episode in episodes:
        _pairs(episode, len(episode["train"]), len(episode["test"]))
    if any(type(row) is not dict or set(row) != {"public_id", "episode_index", "query_index"}
           for row in index):
        raise ValueError("invalid public index schema")
    ids = [row["public_id"] for row in index]
    if any(type(identifier) is not str or not re.fullmatch("[0-9a-f]{64}", identifier) for identifier in ids):
        raise ValueError("invalid public identity in index")
    if ids != sorted(set(ids)):
        raise ValueError("public identity index is not unique and sorted")
    if set(paths) - private_names != {f"public/{identifier}.json" for identifier in ids}:
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
    if "teaching-gap.json" in paths:
        gap = json.loads((output / "teaching-gap.json").read_bytes())
        if (type(gap) is not dict or gap.get("schema") != "arcpuzzles-task-teaching-gap-v1"
                or gap.get("task_id") != TASK or type(gap.get("cases")) is not list):
            raise ValueError("private teaching-gap schema differs")
        for case in gap["cases"]:
            try:
                i = case["private_episode_index"]
                if type(i) is not int or not 0 <= i < len(episodes):
                    raise ValueError("invalid private episode index")
                rebuilt = make_teaching_gap(episodes[i], case["candidate"], case["rival_program"],
                    case["rival_demonstration_outputs"] + [case["rival_query_output"]], episode_index=i)
                if rebuilt != case:
                    raise ValueError("teaching-gap private association differs")
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError("private teaching-gap schema or association differs") from error
    return manifest


def _source_hashes():
    paths = {p for p in HERE.rglob("*") if p.is_file() and p.suffix in {".py", ".rkt", ".json"}
             and not {"evidence", "examples", "__pycache__"}.intersection(p.relative_to(HERE).parts)}
    paths.update((HERE.parents[1] / "tests").glob("test_native*.py"))
    paths.update(ROOT / name for name in (
        f"generators/{TASK}/generator.py", "src/arcpuzzles/parametric_worker.py",
        "shared/runtime/reviewer_support.py", "shared/runtime/puzzle_generators/rule_wrap.py",
        "shared/tools/comment_solutions.py"))
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(paths)}


def screen_candidate(episode, program, execute):
    """Screen only the minimum demo prefix; evaluate queries only for survivors.

    Every screened demo is executed even after an earlier mismatch. An exception
    propagates to the audit as a failure, never a demonstration refutation.
    """
    demonstrations = episode["train"][:SCREENED_DEMOS]
    if len(demonstrations) != SCREENED_DEMOS:
        raise ValueError(f"the minimum teaching screen needs {SCREENED_DEMOS} demonstrations")
    outputs = [_grid(execute(program, deepcopy(pair["input"]))) for pair in demonstrations]
    refuted = [i for i, pair in enumerate(demonstrations) if outputs[i] != pair["output"]]
    result = {"screened_demo_count": SCREENED_DEMOS, "demonstration_refutations": refuted,
              "demonstration_outputs": outputs, "query_mismatches": None,
              "query_audit": "not_needed_refuted_on_demo" if refuted else "executed",
              "status": "refuted_on_demonstrations" if refuted else "consistent_on_support"}
    if not refuted:
        query_outputs = [_grid(execute(program, deepcopy(pair["input"]))) for pair in episode["test"]]
        mismatches = [i for i, pair in enumerate(episode["test"]) if query_outputs[i] != pair["output"]]
        result.update(query_outputs=query_outputs, query_mismatches=mismatches,
                      status="ambiguous_queries" if mismatches else "consistent_on_support")
    return result


def _coverage(descriptions):
    def shapes(field):
        return dict(sorted(Counter("x".join(map(str, row[field])) for row in descriptions).items()))
    def extent(field):
        values = [row[field] for row in descriptions]
        return [min(values), max(values)]
    grouped = Counter(json.dumps(row["settings"], sort_keys=True) for row in descriptions)
    return {"input_shapes": shapes("input_shape"), "output_shapes": shapes("output_shape"),
            "max_input_side": max(max(row["input_shape"]) for row in descriptions),
            "exact_30x19_inputs": sum(row["input_shape"] == [30, 19] for row in descriptions),
            "input_occupied_cells_range": extent("input_occupied_cells"),
            "output_occupied_cells_range": extent("output_occupied_cells"),
            "panel_nonzero_cells_range": extent("panel_nonzero_cells"),
            "nonzero_panel_density_range": extent("measured_panel_nonzero_fraction"),
            "panel_boundary_coverage": {side: sum(row["panel_touches"][side] for row in descriptions)
                                        for side in ("top", "bottom", "left", "right")},
            "panel_content_touching_all_boundaries": sum(all(row["panel_touches"].values())
                                                        for row in descriptions),
            "nonzero_input_density_range": extent("measured_nonzero_fraction"),
            "nonzero_output_density_range": extent("measured_output_nonzero_fraction"),
            "observed_nonzero_colors": sorted({color for row in descriptions for color in row["nonzero_colors"]}),
            "examples_per_setting": dict(sorted(grouped.items())), "descriptions": descriptions}


def check_shared_inputs(episode, memo):
    """Every requested demonstration/query input is shared across policies."""
    seed = episode["seed"]
    inputs = {split: [deepcopy(pair["input"]) for pair in episode[split]]
              for split in ("train", "test")}
    if seed in memo and memo[seed] != inputs:
        raise ValueError("sampler shared inputs differ across settings")
    memo[seed] = inputs


def _canonical_grid(value):
    # Catalog archival pairs use digit-string rows; generated grids stay strict.
    if type(value) is list and value and all(type(row) is str for row in value):
        value = [[int(cell) for cell in row] for row in value]
    return _grid(value)


def _canonical_pairs(variants):
    pairs = []
    seen = set()
    for variant_index, variant in enumerate(variants):
        for split in ("train", "test"):
            values = variant.get(split, [])
            values = [values] if type(values) is dict else values
            if type(values) is not list:
                raise ValueError("canonical pairs must be lists or single pairs")
            for index, pair in enumerate(values):
                normalized = {name: _canonical_grid(pair[name]) for name in ("input", "output")}
                key = raw(normalized)
                if key not in seen:
                    pairs.append({"variant_index": variant_index, "split": split, "index": index,
                                  **normalized})
                    seen.add(key)
    if len(pairs) != CANONICAL_PAIRS:
        raise ValueError(f"This task audit expects {CANONICAL_PAIRS} distinct canonical labeled pairs")
    return pairs


def _request_checks(adapter, family, episode, setting, seed):
    """Check count/prefix visibility without claiming extra Racket labels."""
    requests = ((SCREENED_DEMOS, 1), (SCREENED_DEMOS, 4), (6, 4))
    for demos, queries in requests:
        other = adapter.generate(seed, deepcopy(setting), demos, queries)
        _pairs(other, demos, queries)
        if other.get("program_solution") != episode["program_solution"]:
            raise ValueError("selected program changed with pair counts")
        if (other["train"][:min(SCREENED_DEMOS, demos)] != episode["train"][:min(SCREENED_DEMOS, demos)]
                or other["test"] != episode["test"][:queries]):
            raise ValueError("demonstration/query count prefix independence failed")
        if demos == SCREENED_DEMOS and public_bytes(family.public_turn(other, 0)) != public_bytes(family.public_turn(episode, 0)):
            raise ValueError("one-query/four-query first-turn visibility differs")
    return {"seed": seed, "settings": setting, "requests": [list(v) for v in requests],
            "status": "passed", "extra_labels_replayed": False}


def audit(output, seeds):
    output = _empty_output(output)
    if (not 1 <= len(seeds) <= 2 or len(set(seeds)) != len(seeds)
            or any(type(s) is not int or not 0 <= s <= 2**63 - 1 for s in seeds)):
        raise ValueError("Use one or two distinct integer seeds in 0..2**63-1")
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.parametric_promotion import settings_space
    before = _source_hashes()
    adapter = _module(HERE / "adapter.py", "_audit_adapter_9000d0ea6484_")
    family = _module(HERE / "native_family.py", "_audit_family_9000d0ea6484_")
    contract = json.loads((HERE / "promotion.json").read_bytes())
    settings = settings_space(contract)
    if len(settings) != SETTING_COUNT or contract["limits"] != {"demos": [SCREENED_DEMOS, 6], "queries": [1, 4]}:
        raise ValueError(f"This bounded audit requires {SETTING_COUNT} settings and the declared {SCREENED_DEMOS}..6/1..4 counts")
    canonical = adapter.program(contract["default"]).encode()
    catalog = Catalog(ROOT)
    selected = catalog.describe(TASK)
    authority = selected.get("rule_task_id", TASK)
    variants = catalog.get(authority)["variants"]
    programs = {v["program_solution"] for v in variants}
    canonical_pairs = _canonical_pairs(variants)
    if programs != {canonical.decode()}:
        raise ValueError("Default must match the selected canonical authority byte-for-byte")
    binding = {"task_id": TASK, "rule_task_id": authority, "generator_sha256": before[f"generators/{TASK}/generator.py"],
               "canonical_rule_hash": selected["rule_hash"], "canonical_program_sha256": sha(canonical),
               "source_hashes": before}
    failures, witnesses, episodes, comparisons, descriptions, requests = [], [], [], [], [], []
    teaching_gaps = []
    cache, program_sources = {}, {}
    evaluations = cache_hits = verified_labels = 0
    canonical_replay = []
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
            for pair in canonical_pairs:
                try:
                    actual = _grid(execute(canonical.decode(), pair["input"]))
                    if actual != pair["output"]:
                        raise AuditFailure("canonical label differs from executed Racket output",
                                           **pair, executed_output=actual, program=canonical.decode())
                    canonical_replay.append({**pair, "output": actual, "status": "passed"})
                except Exception as error:
                    failure = {"kind": "canonical_replay_failed", "split": pair["split"],
                               "index": pair["index"], "error": f"{type(error).__name__}: {error}"}
                    if isinstance(error, AuditFailure):
                        failure["witness"] = error.details
                    failures.append(failure)
            for seed in seeds:
                for setting in settings:
                    try:
                        value = adapter.generate(seed, deepcopy(setting), SCREENED_DEMOS, 4)
                        value.update(seed=seed, settings=deepcopy(setting))
                        episode = verify_episode(value, adapter.program(setting), execute, demos=SCREENED_DEMOS, queries=4)
                        verified_labels += SCREENED_DEMOS + 4
                        check_shared_inputs(episode, common_inputs)
                        requests.append(_request_checks(adapter, family, episode, setting, seed))
                        metadata_rows = []
                        for split in ("train", "test"):
                            for index, pair in enumerate(episode[split]):
                                metadata = family.describe(pair["input"], setting)
                                grid, actual_output = pair["input"], pair["output"]
                                input_shape = [len(grid), len(grid[0])]
                                output_shape = [len(actual_output), len(actual_output[0])]
                                if (type(metadata) is not dict
                                        or ("input_shape" in metadata and metadata["input_shape"] != input_shape)
                                        or ("output_shape" in metadata and metadata["output_shape"] != output_shape)):
                                    raise ValueError("description disagrees with executed label/grid dimensions")
                                if input_shape[1] != 19 or output_shape != [input_shape[0], 4]:
                                    raise ValueError("executed family must map Hx19 inputs to Hx4 outputs")
                                panel_counts = [sum(row[start + c] != 0 for row in grid for c in range(4))
                                                for start in SECTION_STARTS]
                                if metadata.get("counts") != panel_counts:
                                    raise ValueError("description disagrees with measured panel counts")
                                panel_points = [(r, start + c) for r, row in enumerate(grid)
                                                for start in SECTION_STARTS for c in range(4)
                                                if row[start + c] != 0]
                                panel_bbox = ([min(r for r, c in panel_points), min(c for r, c in panel_points),
                                               max(r for r, c in panel_points), max(c for r, c in panel_points)]
                                              if panel_points else None)
                                panel_touches = {"top": any(r == 0 for r, c in panel_points),
                                                 "bottom": any(r == input_shape[0] - 1 for r, c in panel_points),
                                                 "left": any(c == 0 for r, c in panel_points),
                                                 "right": any(c == 18 for r, c in panel_points)}
                                occupied = sum(v != 0 for row in grid for v in row)
                                output_occupied = sum(v != 0 for row in actual_output for v in row)
                                metadata_rows.append({"family_description": metadata, "seed": seed, "settings": setting,
                                    "split": split, "index": index, "input_shape": input_shape,
                                    "output_shape": output_shape, "input_occupied_cells": occupied,
                                    "output_occupied_cells": output_occupied,
                                    "measured_panel_counts": panel_counts,
                                    "panel_nonzero_cells": sum(panel_counts),
                                    "measured_panel_nonzero_fraction": sum(panel_counts) / (input_shape[0] * 16),
                                    "panel_content_bbox": panel_bbox, "panel_touches": panel_touches,
                                    "nonzero_colors": sorted({v for row in grid for v in row if v != 0}),
                                    "measured_nonzero_fraction": occupied / (len(grid) * len(grid[0])),
                                    "measured_output_nonzero_fraction": output_occupied
                                        / (len(actual_output) * len(actual_output[0]))})
                        episodes.append(episode)
                        descriptions.extend(metadata_rows)
                    except Exception as error:
                        failure = {"kind": "episode_failed", "seed": seed, "settings": setting,
                                   "error": f"{type(error).__name__}: {error}"}
                        if isinstance(error, AuditFailure):
                            failure["witness"] = error.details
                        failures.append(failure)

            for episode_index, episode in enumerate(episodes):
                setting, seed = episode["settings"], episode["seed"]
                candidates = [("alternate_setting", raw(other).decode().strip(), adapter.program(other))
                              for other in settings if other != setting]
                candidates += [("named_rival", name, program) for name, program in family.rivals(setting).items()]
                for kind, name, program in candidates:
                    row = {"seed": seed, "settings": setting, "kind": kind, "name": name,
                           "program_sha256": sha(program.encode()), "backend": "protected_racket",
                           "screened_demo_count": SCREENED_DEMOS}
                    try:
                        result = screen_candidate(episode, program, execute)
                        outputs = result.pop("query_outputs", None)
                        row.update(result)
                        if not result["demonstration_refutations"]:
                            mismatches = result["query_mismatches"]
                            if mismatches or kind == "alternate_setting":
                                failures.append({"kind": "teaching_ambiguity", "seed": seed, "screened_demo_count": SCREENED_DEMOS,
                                                 "settings": setting, "candidate": name, "query_mismatches": mismatches})
                            if mismatches:
                                q = min(mismatches, key=lambda i: len(episode["test"][i]["input"]) * len(episode["test"][i]["input"][0]))
                                witnesses.append({"seed": seed, "settings": setting, "candidate": name,
                                    "screened_demo_count": SCREENED_DEMOS, "train": episode["train"][:SCREENED_DEMOS],
                                    "query_index": q, "query": episode["test"][q],
                                    "rival_output": outputs[q], "program": episode["program_solution"],
                                    "rival_program": program, "selection": "smallest differing checked query; no cell minimization"})
                    except Exception as error:
                        row.update(status="execution_failed", error=f"{type(error).__name__}: {error}")
                        failures.append({"kind": "rival_execution_failed", **row})
                    if (seed == 0 and setting["scan_direction"] == "forward"
                            and name == GAP_RIVALS.get(setting["start_section"])
                            and row["status"] != "execution_failed"):
                        try:
                            teaching_gaps.append(make_teaching_gap(episode, name, program,
                                row["demonstration_outputs"], episode_index=episode_index))
                        except Exception as error:
                            failures.append({"kind": "teaching_gap_failed", "seed": seed,
                                             "settings": setting, "candidate": name,
                                             "error": f"{type(error).__name__}: {error}"})
                    comparisons.append(row)
        finally:
            bridge.close()
    source_current = _source_hashes() == before
    if not source_current:
        failures.append({"kind": "source_changed_during_audit"})
    expected_gaps = len(GAP_RIVALS) if 0 in seeds else 0
    if len(teaching_gaps) != expected_gaps:
        failures.append({"kind": "teaching_gap_missing", "expected": expected_gaps,
                         "retained": len(teaching_gaps)})
    gap_artifact = {"schema": "arcpuzzles-task-teaching-gap-v1", "task_id": TASK,
                    "source_binding": binding, "racket": identity, "cases": teaching_gaps,
                    "status": "retained" if teaching_gaps else "not_requested" if not expected_gaps else "failed",
                    "scope": "Author-proposed three-demo lessons from the final native bank. The fourth training pair "
                             "is their counterexample query, then the added fourth demonstration. The four ordinary "
                             "queries remain novel. This is not a production or legacy-worker episode.",
                    "repair_cost": {"additional_demonstrations": 1, "required_demonstrations": SCREENED_DEMOS},
                    "additional_racket_evaluations": 0, "training_admitted": False}
    export = export_episodes(episodes, output, family.public_turn, teaching_gap=gap_artifact)
    witness_bytes = raw({"schema": "arcpuzzles-task-audit-witnesses-v1", "source_binding": binding,
                         "racket": identity, "screened_demo_count": SCREENED_DEMOS, "witnesses": witnesses})
    (output / "witnesses.json").write_bytes(witness_bytes)
    report = {"schema": "arcpuzzles-parametric-teaching-audit-v1", "status": "failed" if failures else "passed",
              "source_binding": binding, "source_unchanged_during_audit": source_current,
              "racket": identity, "seeds": seeds, "settings": settings, "screened_demo_count": SCREENED_DEMOS,
              "counts": {"planned_jobs": len(seeds) * len(settings), "executed_episodes": len(episodes),
                         "demonstrations": SCREENED_DEMOS, "screened_demo_count": SCREENED_DEMOS, "queries": 4,
                         "intended_labels_verified": verified_labels,
                         "canonical_labels_verified": len(canonical_replay),
                         "racket_evaluations": evaluations, "cache_hits": cache_hits,
                         "candidate_comparisons": len(comparisons), "public_files": export["public_count"],
                         "teaching_gap_cases": len(teaching_gaps)},
              "coverage": _coverage(descriptions) if descriptions else {}, "request_checks": requests,
              "matched_input_policy": f"all {SCREENED_DEMOS} demonstrations and all four queries across all settings",
              "canonical_replay": canonical_replay,
              "rivals": comparisons, "failures": failures, "program_sources": program_sources,
              "export_manifest_sha256": sha((output / "export_manifest.json").read_bytes()),
              "teaching_gap_path": "teaching-gap.json", "teaching_gap_sha256": sha(raw(gap_artifact)),
              "witnesses_sha256": sha(witness_bytes), "training_admitted": False,
              "limits": f"One or two seeds, {SETTING_COUNT} settings, and finite declared rivals only. All retained intended "
                        f"labels and {CANONICAL_PAIRS} canonical labels were executed; {SCREENED_DEMOS}/6-demo and 1/4-query requests check count and visibility invariance only. "
                        f"Candidates are screened on the first {SCREENED_DEMOS} demonstrations only; later demos are never screening evidence. "
                        "Refuted candidates' queries are not executed. Execution errors fail the audit. No universal "
                        "identifiability, native qualification, owner acceptance, training admission, or reauthentication "
                        "of rewritten artifacts."}
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


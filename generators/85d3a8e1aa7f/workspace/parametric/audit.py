"""Bounded authoring audit and private/public examples for the relay prototype.

Run with the same-checkout review launcher and a new --out directory. This is
authoring evidence; the separate native manifest and qualification remain gates.
Nothing is published until all required checks in this script have succeeded.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "85d3a8e1aa7f"
SEEDS = (0, 17)
DEMOS = 2
QUERIES = 4
LIMITS = (
    "Finite authoring checks on the declared settings and shortcuts only. "
    "Protected Racket labels cover seeds 0 and 17 at two demonstrations and "
    "four queries, plus two explicit edge fixtures. The construction sweep "
    "checks Python requests, not Racket labels. No universal identifiability, "
    "sampling guarantee, measured learning gain, owner acceptance or training "
    "admission is established."
)

sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import public_challenge_bytes, public_challenge_id


class AuditFailure(RuntimeError):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details or {}


def _require(condition, message, **details):
    if not condition:
        raise AuditFailure(message, details)


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _load_adapter():
    path = HERE / "adapter.py"
    body = path.read_bytes()
    name = "_relay_authoring_adapter_" + _sha(body)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    # Compile the exact hashed bytes instead of accepting timestamp-based pyc.
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


def _sources():
    paths = {ROOT / f"generators/{TASK_ID}/generator.py",
             ROOT / "shared/runtime/reviewer_support.py",
             ROOT / "src/arcpuzzles/parametric_worker.py"}
    paths.update(path for path in HERE.rglob("*")
                 if path.is_file() and path.suffix in {".py", ".rkt", ".json"}
                 and not {"evidence", "examples", "__pycache__"}.intersection(
                     path.relative_to(HERE).parts))
    return [{"path": path.relative_to(ROOT).as_posix(),
             "bytes": path.stat().st_size, "sha256": _sha(path.read_bytes())}
            for path in sorted(paths)]


def _episode(adapter, programs, seed, routing, demos, queries):
    value = adapter.generate(seed, {"routing": routing}, demos, queries)
    _require(type(value) is dict and value.get("program_solution") == programs[routing],
             "Generated program differs from the setting's exact program",
             seed=seed, routing=routing)
    result = {"program_solution": value["program_solution"]}
    inputs = []
    for split, count in (("train", demos), ("test", queries)):
        pairs = value.get(split)
        _require(type(pairs) is list and len(pairs) == count,
                 "Requested pair count was not honored", seed=seed,
                 routing=routing, split=split, requested=count)
        normalized = []
        for index, pair in enumerate(pairs):
            _require(type(pair) is dict and {"input", "output"} <= set(pair),
                     "A pair lacks its input or output", split=split, pair_index=index)
            inp, out = _grid(pair["input"]), _grid(pair["output"])
            _require(len(inp) == len(out) and len(inp[0]) == len(out[0]),
                     "This family's outputs must retain the full input dimensions",
                     seed=seed, routing=routing, split=split, pair_index=index)
            inputs.append(_raw(inp))
            normalized.append({"input": inp, "output": out})
        result[split] = normalized
    _require(len(set(inputs)) == len(inputs),
             "Demonstration/query inputs repeat within an episode", seed=seed,
             routing=routing, demos=demos, queries=queries)
    return result


def _input_lists(episode):
    return {split: [pair["input"] for pair in episode[split]]
            for split in ("train", "test")}


def _reliability(adapter, programs):
    failures, successes, saved = [], 0, {}
    matched_settings, prefix_checks = 0, 0
    for seed in range(16):
        episodes = {}
        for demos in (2, 6):
            for queries in (1, 4):
                for routing in adapter.ROUTINGS:
                    request = {"seed": seed, "routing": routing,
                               "demos": demos, "queries": queries}
                    try:
                        episode = _episode(adapter, programs, seed, routing, demos, queries)
                        episodes[routing, demos, queries] = episode
                        successes += 1
                        if seed == 0 and demos == DEMOS and queries == QUERIES:
                            saved[0, routing] = episode
                    except Exception as exc:
                        failures.append({**request, "error": type(exc).__name__,
                                         "message": str(exc)[:500]})
        for demos in (2, 6):
            for queries in (1, 4):
                left = episodes.get(("direct", demos, queries))
                right = episodes.get(("relay", demos, queries))
                if left is not None and right is not None:
                    if _input_lists(left) != _input_lists(right):
                        failures.append({"seed": seed, "demos": demos,
                                         "queries": queries,
                                         "message": "Inputs differ across private settings"})
                    else:
                        matched_settings += 1
        for routing in adapter.ROUTINGS:
            full = episodes.get((routing, 6, 4))
            if full is None:
                continue
            for demos, queries in ((2, 1), (2, 4), (6, 1)):
                small = episodes.get((routing, demos, queries))
                if small is None:
                    continue
                if (small["train"] != full["train"][:demos]
                        or small["test"] != full["test"][:queries]):
                    failures.append({"seed": seed, "routing": routing,
                                     "demos": demos, "queries": queries,
                                     "message": "Count changes alter the shared pair prefix"})
                else:
                    prefix_checks += 1
    report = {"seeds": list(range(16)), "demo_counts": [2, 6],
              "query_counts": [1, 4], "request_count": 128,
              "successful_requests": successes, "failures": failures,
              "matched_input_comparisons": matched_settings,
              "count_prefix_comparisons": prefix_checks,
              "scope": "One call per declared request combination; Python construction, exact grids, counts, distinct inputs and matched prefixes only."}
    _require(not failures and successes == 128, "Bounded request reliability failed",
             request_reliability=report)
    return report, saved


def _edge_fixtures():
    even = [[7] * 30 for _ in range(30)]
    even[15][15] = 0
    even_expected = [[7] * 30 for _ in range(30)]
    for index in range(15, 30):
        even_expected[index][index] = 0
    hit = [[7] * 9 for _ in range(9)]
    for row, col in ((4, 4), (5, 5), (8, 7), (7, 8), (8, 8)):
        hit[row][col] = 1
    for row, col in ((6, 6), (0, 0), (0, 1), (1, 0), (1, 1), (2, 1)):
        hit[row][col] = 2
    hit[7][7] = 3
    hit[3][5] = 3
    direct, relay = [[7] * 9 for _ in range(9)], [[7] * 9 for _ in range(9)]
    for index in range(4, 9):
        direct[index][index] = 1
    for index in range(5):
        relay[index][index] = 2
    return [{"name": "even_center_key_zero_no_eligible_relay", "input": even,
             "expected": {"direct": even_expected, "relay": even_expected},
             "reason": "Independent literal expectation: floor center (15,15), positive centroid ties, zero key and relay fallback paint the BR ray."},
            {"name": "first_hit_key_skip_and_second_centroid", "input": hit,
             "expected": {"direct": direct, "relay": relay},
             "reason": "Independent literal expectation: skip key at (5,5), choose 2 at (6,6) before 3 at (7,7), ignore the wrong-ray decoy, then paint color 2 toward TL."}]


def _protected(adapter, programs, episodes):
    runtime = (ROOT / "shared/runtime").resolve()
    certificates, edge_results = [], []
    program_hashes = {routing: _sha(program.encode())
                      for routing, program in programs.items()}
    rivals = {routing: adapter.rival_programs(routing) for routing in adapter.ROUTINGS}
    for routing, values in rivals.items():
        _require(type(values) is dict and values
                 and all(type(name) is str and name and type(program) is str
                         and program.strip() for name, program in values.items()),
                 "Declared rivals must be named standalone programs", routing=routing)
    rival_hashes = {routing: {name: _sha(program.encode())
                             for name, program in values.items()}
                    for routing, values in rivals.items()}
    evaluations = 0
    cache = {}
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            def execute(program, grid):
                nonlocal evaluations
                key = (program, _raw(grid))
                if key not in cache:
                    evaluations += 1
                    cache[key] = _grid(apply(program, deepcopy(grid)))
                return cache[key]

            for seed in SEEDS:
                for routing in adapter.ROUTINGS:
                    episode = episodes[seed, routing]
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            _require(execute(programs[routing], pair["input"]) == pair["output"],
                                     "Claimed label differs from protected Racket",
                                     seed=seed, routing=routing, split=split, pair_index=index)
                    survivors = [candidate for candidate in adapter.ROUTINGS
                                 if all(execute(programs[candidate], pair["input"]) == pair["output"]
                                        for pair in episode["train"])]
                    _require(survivors == [routing],
                             "Demonstrations fail to identify the chosen finite setting",
                             seed=seed, routing=routing, survivors=survivors)
                    mirrors = [adapter.rival_predictions(pair["input"], routing)
                               for pair in episode["train"]]
                    _require(all(type(mirror) is dict and set(mirror) == set(rivals[routing])
                                 for mirror in mirrors),
                             "Python and Racket rival names differ", seed=seed, routing=routing)
                    rows = []
                    for name, rival in rivals[routing].items():
                        refuted = []
                        for index, pair in enumerate(episode["train"]):
                            actual = execute(rival, pair["input"])
                            expected = _grid(mirrors[index][name])
                            _require(actual == expected,
                                     "Racket rival differs from its Python mirror; no refutation can be counted",
                                     seed=seed, routing=routing, rival=name, demo_index=index)
                            if actual != pair["output"]:
                                refuted.append(index)
                        conflicts = []
                        if not refuted:
                            for index, pair in enumerate(episode["test"]):
                                actual = execute(rival, pair["input"])
                                mirror = _grid(adapter.rival_predictions(pair["input"], routing)[name])
                                _require(actual == mirror,
                                         "Surviving Racket rival differs from its query mirror",
                                         seed=seed, routing=routing, rival=name, query_index=index)
                                if actual != pair["output"]:
                                    conflicts.append(index)
                        _require(not conflicts, "A demonstration-surviving shortcut conflicts on queries",
                                 seed=seed, routing=routing, rival=name, query_indices=conflicts)
                        rows.append({"name": name, "program_sha256": rival_hashes[routing][name],
                                     "mirror_demo_checks": DEMOS, "refuted_by_demo_indices": refuted,
                                     "query_checks": 0 if refuted else QUERIES,
                                     "query_conflicts": conflicts,
                                     "status": "refuted_by_demos" if refuted else "unrefuted_query_agreement"})
                    certificates.append({"seed": seed, "settings": {"routing": routing},
                                         "counts": {"demos": DEMOS, "queries": QUERIES},
                                         "label_count": DEMOS + QUERIES,
                                         "setting_survivors": [{"routing": value} for value in survivors],
                                         "rivals": rows,
                                         "all_declared_shortcuts_refuted_by_demos": all(row["refuted_by_demo_indices"] for row in rows)})
            fixtures = _edge_fixtures()
            for case in fixtures:
                checks = []
                for routing in adapter.ROUTINGS:
                    expected = _grid(case["expected"][routing])
                    _require(execute(programs[routing], case["input"]) == expected,
                             "Protected Racket failed a literal edge fixture",
                             case=case["name"], routing=routing)
                    _require(_grid(adapter.predict(case["input"], routing)) == expected,
                             "Python prediction failed a literal edge fixture",
                             case=case["name"], routing=routing)
                    checks.append({"settings": {"routing": routing},
                                   "program_sha256": program_hashes[routing],
                                   "expected_output_sha256": _sha(_raw(expected)), "matched": True})
                edge_results.append({"name": case["name"], "reason": case["reason"],
                                     "input_sha256": _sha(_raw(case["input"])), "checks": checks})
        finally:
            bridge.close()
    return {"runtime": identity, "racket_evaluations": evaluations,
            "cache_scope": "Identical program bytes and identical grid bytes only, within this run.",
            "program_sha256": program_hashes, "rival_program_sha256": rival_hashes,
            "demo_only_certificates": certificates, "edge_cases": edge_results}, fixtures


def _density(episodes):
    unique = {}
    for (seed, routing), episode in episodes.items():
        for split in ("train", "test"):
            for index, pair in enumerate(episode[split]):
                grid = pair["input"]
                identifier = _sha(_raw(grid))
                if identifier in unique:
                    continue
                height, width = len(grid), len(grid[0])
                points = [(r, c) for r, row in enumerate(grid)
                          for c, value in enumerate(row) if value != 7]
                unique[identifier] = {"seed": seed, "split": split, "pair_index": index,
                    "input_sha256": identifier, "height": height, "width": width,
                    "nonbackground_cells": len(points),
                    "nonbackground_fraction": round(len(points) / (height * width), 6),
                    "occupied_rows": len({r for r, _ in points}),
                    "occupied_columns": len({c for _, c in points}),
                    "nonbackground_bounds": [min(r for r, _ in points), min(c for _, c in points),
                                             max(r for r, _ in points), max(c for _, c in points)],
                    "border_nonbackground_cells": sum(r in (0, height - 1) or c in (0, width - 1)
                                                       for r, c in points)}
    rows = list(unique.values())
    _require(min(row["height"] for row in rows) == 9
             and max(row["height"] for row in rows) == 30
             and all(row["height"] == row["width"] for row in rows),
             "Protected examples must span square inputs from 9 to 30")
    return {"unique_inputs": len(rows), "minimum_side": 9, "maximum_side": 30,
            "minimum_nonbackground_fraction": min(row["nonbackground_fraction"] for row in rows),
            "maximum_nonbackground_fraction": max(row["nonbackground_fraction"] for row in rows),
            "inputs": rows,
            "scope": "Measured visible cell occupancy, not a difficulty or learning-benefit claim."}


def _projection_artifacts(adapter, episodes, programs, source_files):
    artifacts, mappings = {}, []
    invariance_checks = 0
    for routing in adapter.ROUTINGS:
        episode = deepcopy(episodes[0, routing])
        private = {"task_id": TASK_ID, "seed": 0, "settings": {"routing": routing},
                   **episode, "program_sha256": _sha(programs[routing].encode()),
                   "source_files": source_files,
                   "private_intermediates": {split: [adapter.intermediate(pair["input"])
                                                       for pair in episode[split]]
                                             for split in ("train", "test")},
                   "training_admitted": False}
        private_name = f"private/{routing}-seed0.json"
        artifacts[private_name] = _raw(private)
        for index, pair in enumerate(episode["test"]):
            challenge = {**deepcopy(private), "test": [deepcopy(pair)]}
            payload = public_challenge_bytes(challenge)
            identifier = public_challenge_id(challenge)
            _require(identifier == _sha(payload), "Public ID is not the exact visible-byte hash")
            hidden_changed = deepcopy(challenge)
            hidden_changed.update(seed=999, settings={"routing": "hidden-change"},
                                  task_id="hidden-change", program_solution="hidden-change",
                                  program_sha256="hidden-change", private_intermediates={})
            old = hidden_changed["test"][0]["output"][0][0]
            hidden_changed["test"][0]["output"][0][0] = (old + 1) % 10
            _require(public_challenge_bytes(hidden_changed) == payload
                     and public_challenge_id(hidden_changed) == identifier,
                     "Private metadata or query answers affect the public ID")
            del hidden_changed["test"][0]["output"]
            _require(public_challenge_bytes(hidden_changed) == payload,
                     "Removing a query answer changes the visible projection")
            invariance_checks += 1
            visible = json.loads(payload)
            _require(set(visible) == {"train", "test"} and len(visible["test"]) == 1
                     and all(set(row) == {"input", "output"} for row in visible["train"])
                     and set(visible["test"][0]) == {"input"},
                     "Public first-turn projection contains unexpected fields")
            public_name = f"public/{identifier}.json"
            _require(public_name not in artifacts, "Duplicate visible challenge in authored examples")
            artifacts[public_name] = payload
            mappings.append({"private_path": private_name, "query_index": index,
                             "public_path": public_name, "public_sha256": identifier})

    malformed = {"empty": [], "empty_row": [[]], "ragged": [[0], [1, 2]],
                 "boolean": [[True]], "float": [[1.0]], "negative": [[-1]],
                 "color_above_nine": [[10]], "too_tall": [[0] for _ in range(31)],
                 "too_wide": [[0] * 31], "tuple_grid": ((0,),), "tuple_row": [(0,)]}
    rejected = []
    basis = {"train": [{"input": [[0]], "output": [[1]]}], "test": [{"input": [[2]]}]}
    for split, field in (("train", "input"), ("train", "output"), ("test", "input")):
        for name, grid in malformed.items():
            invalid = deepcopy(basis)
            invalid[split][0][field] = deepcopy(grid)
            try:
                public_challenge_bytes(invalid)
            except ValueError:
                rejected.append(f"{split}.{field}:{name}")
            else:
                raise AuditFailure("Malformed visible grid was accepted", {"field": f"{split}.{field}", "case": name})
    return artifacts, {"public_files": len(mappings), "queries_per_public_file": 1,
                       "private_episodes": 2, "queries_per_private_episode": QUERIES,
                       "hidden_field_and_answer_invariance_checks": invariance_checks,
                       "malformed_visible_grid_rejections": rejected,
                       "mapping_is_private": True, "mapping": mappings}


def run(output):
    output = Path(output).absolute()
    _require(not output.exists() and not output.is_symlink(),
             "Choose a new output directory", output=str(output))
    sources = _sources()
    adapter = _load_adapter()
    _require(tuple(adapter.ROUTINGS) == ("direct", "relay"), "Unexpected setting space")
    programs = {routing: adapter.program({"routing": routing}) for routing in adapter.ROUTINGS}
    _require(all(type(program) is str and program.strip() for program in programs.values()),
             "Each setting must provide nonempty Racket source")
    catalog = Catalog(ROOT)
    selected = catalog.describe(TASK_ID)
    authority = selected.get("rule_task_id", TASK_ID)
    canonical = {row.get("program_solution") for row in catalog._variants().get(authority, [])}
    _require(canonical == {programs["direct"]}, "Default source is not the exact canonical program")
    _require(programs["direct"] != programs["relay"], "Routing settings have identical programs")
    reliability, episodes = _reliability(adapter, programs)
    for routing in adapter.ROUTINGS:
        episodes[17, routing] = _episode(adapter, programs, 17, routing, DEMOS, QUERIES)
    for seed in SEEDS:
        _require(_input_lists(episodes[seed, "direct"]) == _input_lists(episodes[seed, "relay"]),
                 "Protected jobs have setting-dependent inputs", seed=seed)
    protected, edge_fixtures = _protected(adapter, programs, episodes)
    density = _density(episodes)
    artifacts, projection = _projection_artifacts(adapter, episodes, programs, sources)
    artifacts["private/edge-fixtures.json"] = _raw(edge_fixtures)
    _require(_sources() == sources
             and all(adapter.program({"routing": routing}) == program
                     for routing, program in programs.items()),
             "Source or program bytes changed during the authoring audit")
    report = {"schema": "arcpuzzles-parametric-author-audit-v1", "status": "passed",
              "task_id": TASK_ID, "rule_task_id": authority,
              "canonical_rule_hash": selected["rule_hash"],
              "canonical_default_exact_bytes": True, "source_files": sources,
              "protected_jobs": 4, "sampled_label_checks": 24, "manual_edge_label_checks": 4,
              "request_reliability": reliability, "protected_execution": protected,
              "input_profiles": density, "public_projection": projection,
              "files": [{"path": name, "bytes": len(payload), "sha256": _sha(payload)}
                        for name, payload in sorted(artifacts.items())],
              "native_qualification": "separate_required_gate", "owner_acceptance": "not_performed",
              "training_admitted": False, "limits": LIMITS}
    artifacts["audit.json"] = _raw(report)
    # The manifest/report is written last; an interrupted publication stays
    # visibly incomplete. No output directory exists before successful checks.
    output.mkdir(parents=True, exist_ok=False)
    for name, payload in artifacts.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(payload)
    return {"status": "passed", "report": str(output / "audit.json"),
            "report_sha256": _sha(artifacts["audit.json"]),
            "protected_jobs": 4, "racket_evaluations": protected["racket_evaluations"],
            "successful_python_requests": reliability["successful_requests"],
            "public_files": projection["public_files"],
            "all_declared_shortcuts_refuted_by_demos": all(
                row["all_declared_shortcuts_refuted_by_demos"]
                for row in protected["demo_only_certificates"]),
            "training_admitted": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new output directory")
    args = parser.parse_args(argv)
    try:
        result = run(args.out)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": type(exc).__name__,
                          "message": str(exc), **getattr(exc, "details", {})},
                         sort_keys=True, allow_nan=False), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

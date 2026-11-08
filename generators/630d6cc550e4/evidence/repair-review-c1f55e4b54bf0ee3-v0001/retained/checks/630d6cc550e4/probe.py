"""Bounded protected-Racket authoring and first-query export probe for MAIN.

Run from this packet's repository through review.py run.  This is private
authoring evidence, not native qualification, acceptance, or training admission.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import canonical_pairs, public_challenge_bytes as visible_bytes


TASK_ID = "630d6cc550e4"
MODES = ("canonical", "inverse", "odd_canonical", "even_canonical")
SEEDS = (0, 17)
QUERY_SHAPES = ((7, 9), (13, 17), (23, 27), (30, 30))
BORDER = ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0), (1, 0))
MINIMUM_ANCHORS = (
    {"name": "three_colors_including_zero", "input": [[0, 1, 2], [2, 7, 0], [1, 0, 2]],
     "forward": [[2, 2, 2], [0, 7, 1], [0, 0, 1]],
     "inverse": [[1, 0, 0], [1, 7, 0], [2, 2, 2]], "odd": True},
    {"name": "eight_colors_including_zero", "input": [[0, 1, 2], [8, 7, 3], [6, 5, 4]],
     "forward": [[2, 8, 4], [5, 7, 1], [0, 3, 6]],
     "inverse": [[6, 3, 0], [1, 7, 5], [4, 8, 2]], "odd": False},
)
sys.dont_write_bytecode = True


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_module(path, role):
    name = f"_authoring_probe_{TASK_ID}_{role}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def pairs_of(episode):
    return episode["train"] + episode["test"]


def validate_episode(episode, settings, demos, queries, expected_program):
    assert isinstance(episode, dict)
    assert episode["program_solution"] == expected_program
    for split, count in (("train", demos), ("test", queries)):
        assert type(episode[split]) is list and len(episode[split]) == count
        for pair in episode[split]:
            assert isinstance(pair, dict) and {"input", "output"} <= set(pair)
            _grid(pair["input"])
            _grid(pair["output"])
    inputs = [raw(pair["input"]) for pair in pairs_of(episode)]
    assert len(set(inputs)) == len(inputs), (settings, "duplicate input")


def stress_metrics(pair):
    grid, output = pair["input"], pair["output"]
    points = [(r, c) for r, row in enumerate(grid)
              for c, color in enumerate(row) if color != 7]
    assert points
    rows = max(r for r, _ in points) - min(r for r, _ in points) + 1
    cols = max(c for _, c in points) - min(c for _, c in points) + 1
    rings = [(r, c) for r in range(len(grid) - 2) for c in range(len(grid[0]) - 2)
             if grid[r + 1][c + 1] == 7
             and all(grid[r + dr][c + dc] != 7 for dr, dc in BORDER)]
    covered = {(r + dr, c + dc) for r, c in rings for dr, dc in BORDER}
    assert len(rings) >= 30 and covered == set(points) and len(covered) == 8 * len(rings)
    assert rows == cols == 30
    changed = (sum(a != b for a_row, b_row in zip(grid, output)
                   for a, b in zip(a_row, b_row))
               if len(grid) == len(output) and len(grid[0]) == len(output[0]) else None)
    return {"shape": [len(grid), len(grid[0])], "background": 7,
            "foreground_cells": len(points), "foreground_span": [rows, cols],
            "complete_rings": len(rings), "colors": sorted({c for row in grid for c in row}),
            "changed_cells": changed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new task-local evidence directory")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    home = root / "generators" / TASK_ID
    parametric = home / "workspace" / "parametric"
    output = args.out.resolve()
    assert output.is_relative_to(parametric / "evidence"), "keep this evidence task-local"
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)

    catalog = Catalog(root)
    selected = catalog.describe(TASK_ID)
    authority = selected.get("rule_task_id", TASK_ID)
    canonical_sources = {row["program_solution"] for row in catalog._variants().get(authority, [])}
    assert len(canonical_sources) == 1
    canonical = canonical_sources.pop()
    paths = [root / selected["generator"], parametric / "prototype.py",
             parametric / "adapter.py", parametric / "promotion.json"]
    source_files = [{"path": path.relative_to(root).as_posix(),
                     "sha256": digest(path.read_bytes())} for path in paths]
    probe_hash = digest(Path(__file__).read_bytes())
    binding = {"task_id": TASK_ID, "rule_task_id": authority,
               "canonical_rule_hash": selected["rule_hash"],
               "canonical_program_sha256": digest(canonical.encode()),
               "files": source_files, "probe_sha256": probe_hash}
    prototype = load_module(parametric / "prototype.py", "prototype")
    adapter = load_module(parametric / "adapter.py", "adapter")
    contract = json.loads((parametric / "promotion.json").read_bytes())
    assert tuple(prototype.MODES) == MODES
    assert contract["parameters"] == {"ring_motion": list(MODES)}
    assert contract["default"] == {"ring_motion": "canonical"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    programs = prototype.candidate_programs()
    assert type(programs) is dict and programs
    declared = {f"setting:{mode}" for mode in MODES}
    assert declared <= set(programs)
    assert set(programs) - declared, "declare the finite extra rivals being checked"
    assert all(type(name) is str and type(program) is str and program.strip()
               for name, program in programs.items())
    program_hashes = {name: digest(program.encode()) for name, program in programs.items()}
    for mode in MODES:
        settings = {"ring_motion": mode}
        assert programs[f"setting:{mode}"] == prototype.program(settings) == adapter.program(settings)
    assert programs["setting:canonical"] == canonical

    execution_cache, python_cache, input_keys = {}, {}, set()
    counters = {"racket_evaluations": 0, "cache_hits": 0, "logical_execution_requests": 0,
                "python_rival_grid_comparisons": 0}
    serialized, lessons, boundaries, official_checks, minimum_checks = [], [], [], [], []
    matched_inputs = {}

    with _local_imports(root / "shared/runtime", parametric):
        apply, runtime, bridge = _real_evaluator(root / "shared/runtime")
        try:
            def execute(program, grid):
                grid = _grid(grid)
                input_hash = digest(raw(grid))
                key = (digest(program.encode()), input_hash)
                counters["logical_execution_requests"] += 1
                input_keys.add(input_hash)
                if key not in execution_cache:
                    execution_cache[key] = _grid(apply(program, grid))
                    counters["racket_evaluations"] += 1
                else:
                    counters["cache_hits"] += 1
                return execution_cache[key]

            def compare_rivals(grid):
                input_hash = digest(raw(grid))
                if input_hash not in python_cache:
                    claims = prototype.rival_outputs(deepcopy(grid))
                    assert type(claims) is dict and set(claims) == set(programs)
                    for name, program in programs.items():
                        assert execute(program, grid) == _grid(claims[name]), (name, input_hash)
                        counters["python_rival_grid_comparisons"] += 1
                    python_cache[input_hash] = claims
                return python_cache[input_hash]

            def verify_teaching(episode, settings):
                mode = settings["ring_motion"]
                for pair in pairs_of(episode):
                    compare_rivals(pair["input"])
                    assert execute(programs[f"setting:{mode}"], pair["input"]) == pair["output"]
                    assert _grid(prototype.apply_rule(deepcopy(pair["input"]), settings)) == pair["output"]
                survivors = [name for name, program in programs.items() if all(
                    execute(program, pair["input"]) == pair["output"] for pair in episode["train"])]
                selected_survivors = sorted(name.removeprefix("setting:") for name in survivors if name in declared)
                extras = sorted(name for name in survivors if name not in declared)
                assert selected_survivors == [mode], (settings, survivors)
                disagreements = {name: [i for i, pair in enumerate(episode["test"])
                                       if execute(programs[name], pair["input"]) != pair["output"]]
                                 for name in survivors}
                assert all(not indices for indices in disagreements.values()), disagreements
                authored = prototype.teaching_certificate(episode, settings)
                assert authored["passed"] is True
                assert sorted(authored["declared_survivors"]) == selected_survivors
                assert sorted(authored["extra_survivors"]) == extras
                return {"passed": True, "fit_split": "train_only",
                        "declared_survivors": selected_survivors, "extra_survivors": extras,
                        "query_disagreement_indices": disagreements,
                        "authored_certificate": authored}

            official = canonical_pairs(authority, root=root, labeled_only=True)
            assert len(official) == 4, "expected all four official labeled pairs"
            for pair in official:
                actual = execute(canonical, pair["input"])
                assert actual == pair["output"]
                official_checks.append({**pair, "racket_output": actual, "matched": True})

            for anchor in MINIMUM_ANCHORS:
                predictions = compare_rivals(anchor["input"])
                expected = {"canonical": anchor["forward"], "inverse": anchor["inverse"],
                            "odd_canonical": anchor["forward"] if anchor["odd"] else anchor["inverse"],
                            "even_canonical": anchor["inverse"] if anchor["odd"] else anchor["forward"]}
                for mode, label in expected.items():
                    assert execute(programs[f"setting:{mode}"], anchor["input"]) == label
                minimum_checks.append({"name": anchor["name"], "input": anchor["input"],
                                       "expected_declared_outputs": expected,
                                       "all_candidate_racket_python_agreements": len(predictions),
                                       "matched": True})

            for mode in MODES:
                settings = {"ring_motion": mode}
                for seed in SEEDS:
                    episode = adapter.generate(seed, settings, 3, 4)
                    validate_episode(episode, settings, 3, 4, programs[f"setting:{mode}"])
                    assert [(len(pair["input"]), len(pair["input"][0]))
                            for pair in episode["test"]] == list(QUERY_SHAPES)
                    teaching = verify_teaching(episode, settings)
                    plan = [pair["input"] for pair in pairs_of(episode)]
                    assert plan == matched_inputs.setdefault((seed, 3, 4), plan)
                    large = stress_metrics(episode["test"][-1])

                    first_only = adapter.generate(seed, settings, 3, 1)
                    validate_episode(first_only, settings, 3, 1, programs[f"setting:{mode}"])
                    assert first_only["train"] == episode["train"]
                    assert first_only["test"] == episode["test"][:1]
                    payload = prototype.public_challenge_bytes(episode)
                    expected_visible = {"train": episode["train"],
                                        "test": [{"input": episode["test"][0]["input"]}]}
                    assert type(payload) is bytes and payload == visible_bytes(expected_visible)
                    assert payload == prototype.public_challenge_bytes(first_only)
                    mutated = deepcopy(episode)
                    mutated.update(seed=-123, settings={"private": "changed"}, program_solution="private changed")
                    for index, pair in enumerate(mutated["test"]):
                        pair["output"] = [[9]]
                        pair["private_future_hint"] = "changed"
                        if index:
                            pair["input"] = [[9]]
                    assert prototype.public_challenge_bytes(mutated) == payload
                    changed_visible = deepcopy(episode)
                    changed_visible["test"][0]["input"][0][0] = (changed_visible["test"][0]["input"][0][0] + 1) % 10
                    assert prototype.public_challenge_bytes(changed_visible) != payload
                    identifier = digest(payload)
                    private = {"episode_id": identifier, "seed": seed, "settings": settings,
                               "episode": episode, "program": programs[f"setting:{mode}"],
                               "teaching": teaching, "racket": runtime, "source_binding": binding}
                    serialized.append((identifier, payload, private))
                    lessons.append({"seed": seed, "settings": settings, "episode_id": identifier,
                                    "demonstrations": 3, "materialized_queries": 4,
                                    "public_queries": 1, "teaching": teaching,
                                    "large_query": large, "private_metadata_invariance": True,
                                    "first_turn_matches_single_query": True,
                                    "private": f"private/{identifier}.json"})

                    largest = adapter.generate(seed, settings, 6, 4)
                    validate_episode(largest, settings, 6, 4, programs[f"setting:{mode}"])
                    assert episode["train"] == largest["train"][:3]
                    assert episode["test"] == largest["test"]
                    for demos, queries in ((2, 1), (2, 4), (6, 1), (6, 4)):
                        smaller = (largest if (demos, queries) == (6, 4)
                                   else adapter.generate(seed, settings, demos, queries))
                        validate_episode(smaller, settings, demos, queries, programs[f"setting:{mode}"])
                        assert smaller["train"] == largest["train"][:demos]
                        assert smaller["test"] == largest["test"][:queries]
                        boundary_teaching = verify_teaching(smaller, settings)
                        boundary_inputs = [pair["input"] for pair in pairs_of(smaller)]
                        assert boundary_inputs == matched_inputs.setdefault((seed, demos, queries), boundary_inputs)
                        boundaries.append({"seed": seed, "settings": settings,
                                           "demos": demos, "queries": queries,
                                           "input_prefixes_preserved": True,
                                           "teaching": boundary_teaching})
        finally:
            bridge.close()

    assert len(lessons) == 8 and len(boundaries) == 32
    assert len({identifier for identifier, _, _ in serialized}) == 8
    assert all(digest((root / row["path"]).read_bytes()) == row["sha256"] for row in source_files)
    assert digest(Path(__file__).read_bytes()) == probe_hash
    execution_rows = [{"program_sha256": program_hash, "input_sha256": input_hash,
                       "output_sha256": digest(raw(result))}
                      for (program_hash, input_hash), result in sorted(execution_cache.items())]
    checks = {
        "schema": "arcpuzzles-parametric-authoring-probe-v1", "task_id": TASK_ID,
        "passed": True, "source_binding": binding, "racket": runtime,
        "observed_counts": {**counters, "qualified_like_lessons": len(lessons),
                            "count_boundary_requests": len(boundaries),
                            "official_pairs": len(official_checks),
                            "minimum_size_semantic_anchors": len(minimum_checks),
                            "candidate_names": len(programs),
                            "unique_programs": len(set(program_hashes.values())),
                            "unique_executed_inputs": len(input_keys)},
        "program_sha256": program_hashes, "programs_path": "private/programs.json",
        "execution_hashes_path": "private/execution-hashes.json",
        "official_parity_path": "private/official-parity.json",
        "minimum_size_path": "private/minimum-size.json",
        "lessons": lessons, "count_boundaries": boundaries,
        "limits": [
            "Finite four-setting, two-seed authoring evidence; no universal identifiability claim.",
            "Candidates are fitted only to demonstrations; query agreement is checked afterward.",
            "Public files expose demonstrations and the first query only; full future queries and labels remain private.",
            "Invalid scalar checks belong to the separate task tests, not this probe.",
            "This probe grants no native qualification, acceptance, approval or training admission.",
        ],
        "training_admitted": False,
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "public").mkdir()
    (output / "private").mkdir()
    for identifier, payload, private in sorted(serialized):
        (output / "public" / f"{identifier}.json").write_bytes(payload)
        (output / "private" / f"{identifier}.json").write_bytes(raw(private))
    (output / "private" / "programs.json").write_bytes(raw(programs))
    (output / "private" / "execution-hashes.json").write_bytes(raw(execution_rows))
    (output / "private" / "official-parity.json").write_bytes(raw(official_checks))
    (output / "private" / "minimum-size.json").write_bytes(raw(minimum_checks))
    checks["files"] = [{"path": path.relative_to(output).as_posix(),
                         "bytes": path.stat().st_size, "sha256": digest(path.read_bytes())}
                        for path in sorted(output.rglob("*")) if path.is_file()]
    (output / "checks.json").write_bytes(raw(checks))
    print(json.dumps({"passed": True, "task_id": TASK_ID,
                      "observed_counts": checks["observed_counts"],
                      "checks": str(output / "checks.json")}, indent=2))


if __name__ == "__main__":
    main()

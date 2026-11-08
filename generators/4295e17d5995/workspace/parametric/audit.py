"""Bounded protected-Racket teaching audit and private/public example writer.

Run through the packet's review.py run wrapper. This checks proposed source;
it does not accept variants or admit training data.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import public_challenge_bytes


TASK_ID = "4295e17d5995"
HERE = Path(__file__).resolve().parent


def public_bytes(episode, query_index=None):
    """Project only visible fields; an indexed turn includes one query input."""
    pairs = episode["test"]
    if query_index is not None:
        if type(query_index) is not int or not 0 <= query_index < len(pairs):
            raise ValueError("query_index must select one existing query")
        pairs = [pairs[query_index]]
    return public_challenge_bytes({"train": episode["train"], "test": pairs})


def _json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def write_examples(episodes, output):
    """Write hash-named public views and one separate controller-owned file."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Choose a new output path: {output}")
    plans = []
    for episode in episodes:
        full = public_bytes(episode)
        first = public_bytes(episode, query_index=0)
        private_episode = deepcopy(episode)
        if "reference" in private_episode:
            private_episode["native_worker_reference"] = private_episode["reference"]
        private_episode["reference"] = "proposed_parametric"
        private_episode["training_admitted"] = False
        plans.append((hashlib.sha256(full).hexdigest(), full,
                      hashlib.sha256(first).hexdigest(), first, private_episode))
    if not plans or len({p[0] for p in plans}) != len(plans):
        raise ValueError("empty batch or duplicate public episode")
    if len({p[2] for p in plans}) != len(plans):
        raise ValueError("duplicate first-turn public episode")
    # Complete validation before creating a destination.
    private = json.dumps([p[4] for p in sorted(plans)], sort_keys=True,
                         indent=2, allow_nan=False) + "\n"
    (output / "public").mkdir(parents=True)
    (output / "first_turn").mkdir()
    for key, full, first_key, first, _ in sorted(plans):
        (output / "public" / f"{key}.json").write_bytes(full)
        (output / "first_turn" / f"{first_key}.json").write_bytes(first)
    (output / "episodes.private.json").write_text(private)
    return {"episodes": len(plans), "public_views": len(plans),
            "first_turn_views": len(plans)}


def _load(name):
    path = HERE / f"{name}.py"
    key = "_wall_audit_" + name + hashlib.sha256(str(path).encode()).hexdigest()[:10]
    spec = importlib.util.spec_from_file_location(key, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_inventory(root):
    return [{"path": p.relative_to(root).as_posix(), "sha256": _sha(p)}
            for p in sorted(HERE.iterdir())
            if p.is_file() and p.suffix in {".py", ".rkt", ".json"}]


def _changed_cells(left, right):
    return sum(a != b for ra, rb in zip(left, right) for a, b in zip(ra, rb))


def run(output):
    """Check both API count edges, finite rival teaching, labels and projection."""
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.parametric_worker import evaluate_contract, _local_imports, _real_evaluator, _grid

    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Choose a new output path: {output}")
    root = HERE.parents[3]
    inventory = _source_inventory(root)
    selected = Catalog(root).describe(TASK_ID)
    contract = json.loads((HERE / "promotion.json").read_bytes())
    adapter, rivals, prototype = _load("adapter"), _load("rivals"), _load("prototype")
    settings = [{"wall_relation": value} for value in ("matching", "opposite")]
    jobs = [{"seed": seed, "settings": setting, "demos": demos, "queries": 4}
            for seed, demos in ((3, 2), (29, 6)) for setting in settings]
    execution = evaluate_contract(root, TASK_ID, contract, jobs)
    execution["acceptance_status"] = "not_accepted"
    execution["native_reference_field_note"] = (
        "The native worker uses the legacy accepted_parametric reference tag during qualification. "
        "It is not an acceptance decision; exported proposal copies are labeled proposed_parametric.")
    report = {
        "schema": "matching-wall-parametric-audit-v1",
        "status": "checking",
        "task_id": TASK_ID,
        "generator_sha256": selected["generator_sha256"],
        "rule_hash": selected["rule_hash"],
        "sources": inventory,
        "scope": "Four bounded episodes: both settings, demo-count edges 2 and 6, four queries; seven executable rivals.",
        "limits": "Finite rival checks and sampled seeds only. No owner acceptance, universal uniqueness, or training admission.",
        "jobs": jobs,
        "native_demo_only_certificates": execution["checks"],
        "native_racket_evaluations": execution["racket_evaluations"],
        "racket": execution["racket"],
        "sampler_draws": [{"seed": seed, "demos": demos, "queries": 4,
                           "attempts": prototype.sample_inputs(seed, demos, 4)["attempts"]}
                          for seed, demos in ((3, 2), (29, 6))],
        "teaching": [],
        "profiles": [],
        "failures": [],
    }
    runtime = root / "shared/runtime"
    evaluations = 0
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            if identity != execution["racket"]:
                raise ValueError("Rival evaluator identity differs from native label evaluator")
            report["rival_racket"] = identity
            for episode, job in zip(execution["episodes"], jobs):
                # Query count and private future inputs cannot influence the first turn.
                single = adapter.generate(job["seed"], job["settings"], job["demos"], 1)
                if public_bytes(single) != public_bytes(episode, query_index=0):
                    raise ValueError("First turn differs between one-query and four-query requests")
                mutated = deepcopy(episode)
                mutated.update(seed=-1, settings={"hidden": "changed"}, program="hidden")
                for pair in mutated["test"]:
                    pair["output"] = [[9]]
                if public_bytes(mutated) != public_bytes(episode):
                    raise ValueError("Private labels or metadata affected public bytes")
                mutated["test"][1:] = [{"input": [[0]], "output": [[1]]}]
                if public_bytes(mutated, query_index=0) != public_bytes(episode, query_index=0):
                    raise ValueError("Future queries affected initial public bytes")

                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        grid = pair["input"]
                        interior = [(r, c) for r, row in enumerate(grid)
                                    for c in range(1, len(row) - 1) if row[c] != 7]
                        report["profiles"].append({
                            "seed": job["seed"], "settings": job["settings"],
                            "split": split, "index": index,
                            "shape": [len(grid), len(grid[0])],
                            "interior_cells": len(interior),
                            "interior_bbox": [min(r for r, _ in interior), min(c for _, c in interior),
                                              max(r for r, _ in interior), max(c for _, c in interior)],
                            "changed_cells": _changed_cells(grid, pair["output"]),
                        })

                for name, program in rivals.programs(job["settings"]).items():
                    demo_outputs = []
                    for pair in episode["train"]:
                        demo_outputs.append(_grid(apply(program, pair["input"])))
                        evaluations += 1
                    mismatch = next((i for i, (actual, pair) in enumerate(zip(demo_outputs, episode["train"]))
                                     if actual != pair["output"]), None)
                    item = {"seed": job["seed"], "settings": job["settings"], "demos": job["demos"],
                            "rival": name, "program": program,
                            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                            "survives_demos": mismatch is None}
                    if mismatch is not None:
                        item["distinguishing_demo"] = {
                            "index": mismatch, **episode["train"][mismatch],
                            "rival_output": demo_outputs[mismatch],
                            "changed_cells": _changed_cells(demo_outputs[mismatch], episode["train"][mismatch]["output"]),
                        }
                    else:
                        disagreements = []
                        for index, pair in enumerate(episode["test"]):
                            rival_output = _grid(apply(program, pair["input"]))
                            evaluations += 1
                            if rival_output != pair["output"]:
                                disagreements.append({"index": index, **pair, "rival_output": rival_output})
                        item["query_disagreements"] = disagreements
                        report["failures"].append({"seed": job["seed"], "settings": job["settings"],
                                                   "rival": name, "query_disagreements": len(disagreements)})
                    report["teaching"].append(item)
        finally:
            bridge.close()
    # Matched input streams make the visible labels, not input construction, teach the parameter.
    for offset in (0, 2):
        left, right = execution["episodes"][offset:offset + 2]
        for split in ("train", "test"):
            if [p["input"] for p in left[split]] != [p["input"] for p in right[split]]:
                raise ValueError("Input stream depends on private setting")
    report.update(
        status="passed" if not report["failures"] else "failed",
        matched_input_streams=True,
        first_turn_equals_single_query=True,
        private_metadata_and_future_query_invariance=True,
        rival_racket_evaluations=evaluations,
        attempted_episodes=len(jobs),
        completed_episodes=len(execution["episodes"]),
        rival_checks=len(report["teaching"]),
        rival_demo_rejections=sum(not row["survives_demos"] for row in report["teaching"]),
    )
    def require_unchanged_source():
        current = Catalog(root).describe(TASK_ID)
        if (_source_inventory(root) != inventory
                or any(current[key] != selected[key] for key in ("generator_sha256", "rule_hash"))):
            raise ValueError("Source changed during audit; rerun after edits finish")

    require_unchanged_source()
    output.mkdir(parents=True)
    _json(output / "execution.json", execution)
    if report["failures"]:
        _json(output / "audit.json", report)
        raise ValueError(f"Demonstration teaching gaps; inspect {output / 'audit.json'}")
    try:
        write_examples(execution["episodes"], output / "examples")
        require_unchanged_source()
    except Exception as error:
        report["status"] = "failed"
        report["failures"].append({"export_error": f"{type(error).__name__}: {error}"})
        _json(output / "audit.json", report)
        raise
    _json(output / "audit.json", report)
    return {key: report[key] for key in (
        "status", "attempted_episodes", "completed_episodes", "rival_checks", "rival_demo_rejections",
        "native_racket_evaluations", "rival_racket_evaluations", "first_turn_equals_single_query")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.out), sort_keys=True))


if __name__ == "__main__":
    main()

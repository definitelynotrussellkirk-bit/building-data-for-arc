from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

TICKET_ID = "ticket-9ac3c5812b351b75"
TICKET_SEED = "cc9d66bd9447da723da53f0d35e903168d720c7dfa6f2fbb1b657d3fd566da8d"
WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
OUT = Path(__file__).resolve().parent
MANIFEST = json.loads((WORK / "PACKET-MANIFEST.json").read_text())


def load_module(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"allocation_{task_id}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def all_grids(pair):
    return [pair["input"], pair["output"]]


def shape(grid):
    return [len(grid), len(grid[0]) if grid else 0]


def summarize_episode(task_id: str, episode: dict, elapsed: float, module) -> dict:
    train = episode.get("train", [])
    test = episode.get("test", [])
    pairs = train + test
    inputs = [pair["input"] for pair in pairs]
    input_bytes = [json.dumps(grid, separators=(",", ":"), sort_keys=True) for grid in inputs]
    grids = [grid for pair in pairs for grid in all_grids(pair)]
    rejections = episode.get("sampling", {}).get("rejections", [])
    reject_reasons = Counter(row.get("reason", "unknown") for row in rejections)
    hook_results = []
    hook = getattr(module, "lesson_identifiable", None)
    if callable(hook):
        for query in test:
            hook_results.append(hook(train, query))
    observed = []
    observe = getattr(module, "observe_overrides", None)
    if callable(observe):
        for pair in pairs:
            try:
                observed.append(observe(pair["input"]))
            except Exception as exc:  # evidence, not a gate
                observed.append({"error": f"{type(exc).__name__}: {exc}"})
    provenance = episode.get("provenance", {})
    return {
        "task_id": task_id,
        "elapsed_seconds": round(elapsed, 6),
        "approved": episode.get("approved"),
        "train_safety": episode.get("train_safety"),
        "generator_sha256": provenance.get("generator_sha256"),
        "catalog_rule_hash": provenance.get("catalog_rule_hash"),
        "executed_rule_hash": episode.get("executed_rule_hash"),
        "train_pairs": len(train),
        "query_pairs": len(test),
        "distinct_pair_inputs": len(set(input_bytes)),
        "distinct_query_inputs": len(set(input_bytes[len(train):])),
        "all_outputs_present": all("output" in pair and pair["output"] is not None for pair in pairs),
        "input_shapes": [shape(pair["input"]) for pair in pairs],
        "output_shapes": [shape(pair["output"]) for pair in pairs],
        "max_side": max((max(shape(grid)) for grid in grids), default=0),
        "has_side_at_least_20": any(max(shape(grid)) >= 20 for grid in grids),
        "sampling_rejections": len(rejections),
        "rejection_reasons": dict(sorted(reject_reasons.items())),
        "declared_axes": sorted(getattr(module, "AXES", {})),
        "examples_needed": getattr(module, "EXAMPLES_NEEDED", None),
        "lesson_hook_present": callable(hook),
        "lesson_hook_query_results": hook_results if callable(hook) else None,
        "lesson_hook_all_clear": (all(not row for row in hook_results) if callable(hook) else None),
        "observed_controls": observed,
    }


def main():
    started = time.monotonic()
    rng = random.Random(int(TICKET_SEED, 16))
    ids = sorted(MANIFEST["generators"])
    sampled = rng.sample(ids, min(3, len(ids)))
    episode_seeds = {task_id: rng.randrange(0, 2**31) for task_id in sampled}

    catalog = {}
    for line in (REPO / "catalog" / "puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        catalog[row["id"]] = row

    records = []
    for task_id in sampled:
        binding = MANIFEST["generators"][task_id]
        source = REPO / binding["generator"]
        source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
        if source_sha != binding["generator_sha256"]:
            raise RuntimeError(f"{task_id}: source hash mismatch")
        module = load_module(task_id)
        if module.RULE_HASH != binding["rule_hash"]:
            raise RuntimeError(f"{task_id}: rule hash mismatch")
        out_path = OUT / f"{task_id}-episode.jsonl"
        if out_path.exists():
            out_path.unlink()
        command = [
            sys.executable, "-m", "arcpuzzles", "generate", task_id,
            "--count", "1",
            "--seed", str(episode_seeds[task_id]),
            "--difficulty", "medium",
            "--train", str(max(3, int(getattr(module, "EXAMPLES_NEEDED", 3)))),
            "--test", "4",
            "--timeout", "30",
            "--out", str(out_path),
        ]
        if not binding["approved"]:
            command.append("--allow-unapproved")
        t0 = time.monotonic()
        completed = subprocess.run(command, cwd=REPO, text=True, capture_output=True, timeout=45)
        elapsed = time.monotonic() - t0
        (OUT / f"{task_id}-command.json").write_text(json.dumps({
            "cwd": str(REPO),
            "command": command,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "elapsed_seconds": round(elapsed, 6),
        }, indent=2) + "\n")
        if completed.returncode != 0:
            raise RuntimeError(f"{task_id}: generation failed: {completed.stderr[-1000:]}")
        rows = [json.loads(line) for line in out_path.read_text().splitlines() if line.strip()]
        if len(rows) != 1:
            raise RuntimeError(f"{task_id}: expected one episode, got {len(rows)}")
        summary = summarize_episode(task_id, rows[0], elapsed, module)
        current = catalog[task_id]
        related = MANIFEST["parametric_priority"]["related_generators"].get(task_id)
        review_index = REPO / "generators" / task_id / "evidence" / "review_index.json"
        summary.update({
            "episode_seed": episode_seeds[task_id],
            "source_sha256_verified": source_sha,
            "manifest_approved": binding["approved"],
            "selection_reasons": MANIFEST["selection"]["reasons"][task_id],
            "catalog": {
                key: current.get(key)
                for key in ("version", "mix_weight", "review_status", "train_safety", "sources", "canonical_rows")
            },
            "parametric_priority": related,
            "review_index_path": str(review_index.relative_to(WORK)) if review_index.exists() else None,
            "review_index_sha256": hashlib.sha256(review_index.read_bytes()).hexdigest() if review_index.exists() else None,
        })
        records.append(summary)

    weights = Counter(row.get("mix_weight") for row in catalog.values())
    normal_ids = MANIFEST["main_draw_policy"]["normal_ids"]
    focus = MANIFEST["main_draw_policy"]["evaluation_focus"]
    result = {
        "schema": "arcpuzzles-bounded-allocation-quality-v1",
        "ticket_id": TICKET_ID,
        "ticket_seed": TICKET_SEED,
        "sample_algorithm": "random.Random(int(seed,16)).sample(sorted(PACKET-MANIFEST generators), 3)",
        "sampled_ids": sampled,
        "episode_seeds": episode_seeds,
        "source_snapshot": {
            "packet_generator_count": len(MANIFEST["generators"]),
            "owner_generator_count": MANIFEST["selection"]["owner_generator_count"],
            "packet_selection_policy": MANIFEST["selection"]["policy"],
            "normal_authoring_pool_count": len(normal_ids),
            "evaluation_focus_probability": focus["probability"],
            "evaluation_focus_eligible_related_generators": focus["eligible_related_generators"],
            "evaluation_focus_scope": focus["scope"],
            "catalog_rows_in_packet": len(catalog),
            "catalog_mix_weight_counts": {str(k): v for k, v in sorted(weights.items(), key=lambda x: str(x[0]))},
            "supplementary_type_weights": MANIFEST["supplementary_ticket_policy"]["weights"],
            "supplementary_weight_basis": MANIFEST["supplementary_ticket_policy"]["weight_basis"],
        },
        "records": records,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "coverage_limits": [
            "three packet records and one medium episode per record; not a corpus estimate",
            "declared lesson hooks test only declared rivals; absence of a hook leaves ambiguity unmeasured",
            "generation elapsed time is a local one-run estimate and excludes downstream tensorization/training",
            "ARC-GEN, RE-ARC and NVARC records are not embedded as equivalent per-task generator records in this packet",
        ],
    }
    (OUT / "probe-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "sampled_ids": sampled,
        "records": [{k: row[k] for k in (
            "task_id", "manifest_approved", "catalog", "train_pairs", "query_pairs",
            "distinct_query_inputs", "sampling_rejections", "max_side",
            "lesson_hook_present", "lesson_hook_all_clear", "elapsed_seconds"
        )} for row in records],
        "elapsed_seconds": result["elapsed_seconds"],
    }, indent=2))


if __name__ == "__main__":
    main()

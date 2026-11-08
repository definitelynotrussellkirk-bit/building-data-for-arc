"""Source-bound allocation-quality probe for ticket-f0ed5197c9504860.

The script performs one bounded executable probe on the pinned primary generator
and records current metadata for the primary plus two ticket-seeded peers.  It
does not edit generator sources, catalog weights, approvals, or draw policies.
"""
from __future__ import annotations

import ast
import hashlib
import json
import random
import re
import time
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator

TICKET_ID = "ticket-f0ed5197c9504860"
TICKET_SEED = "b0bf6f722f351c52d001629057a9d781223868abf00e2f62e2fa3c7bab82fbab"
PRIMARY_ID = "1bfb2ef9ca71"
PINNED_SOURCE_SHA256 = "1040eab6c06ff4c472af885bc51eb8c6ec94c8e33be5b04b246e303a238d275f"
PINNED_RULE_HASH = "a0ec8172be31"
EXPECTED_PEERS = ["27c1546d634f", "28e5fbc279ab"]


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> object:
    return json.loads(path.read_text())


def catalog_rows(path: Path) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows[str(row["id"])] = row
    return rows


def count_tests(task_dir: Path) -> tuple[int, int]:
    files = sorted((task_dir / "tests").glob("test_*.py")) if (task_dir / "tests").is_dir() else []
    functions = 0
    for path in files:
        tree = ast.parse(path.read_text(), filename=str(path))
        functions += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in ast.walk(tree)
        )
    return len(files), functions


def axis_upper_bound(axes: object, name: str) -> int | None:
    if not isinstance(axes, dict) or name not in axes or not isinstance(axes[name], dict):
        return None
    valid = str(axes[name].get("valid", ""))
    match = re.fullmatch(r"\s*(-?\d+)\.\.(-?\d+)\s*", valid)
    return int(match.group(2)) if match else None


def inspect_task(
    *,
    root: Path,
    manifest: dict[str, object],
    catalog: dict[str, dict[str, object]],
    task_id: str,
) -> dict[str, object]:
    module, source_path, source_hash = load_selected_generator(task_id, root=root)
    task_dir = root / "generators" / task_id
    review_path = task_dir / "evidence" / "review_index.json"
    review = read_json(review_path) if review_path.exists() else {}
    catalog_row = catalog[task_id]
    manifest_row = manifest["generators"][task_id]
    test_file_count, test_function_count = count_tests(task_dir)
    axes = getattr(module, "AXES", {})
    max_h = axis_upper_bound(axes, "grid_h")
    max_w = axis_upper_bound(axes, "grid_w")
    priority = manifest.get("parametric_priority", {}).get("related_generators", {}).get(task_id)
    return {
        "task_id": task_id,
        "source_path": str(source_path.relative_to(root)),
        "current_source_sha256": source_hash,
        "manifest_source_sha256": manifest_row.get("generator_sha256"),
        "source_matches_manifest": source_hash == manifest_row.get("generator_sha256"),
        "review_index_source_sha256": review.get("current_source_sha256"),
        "source_matches_review_index": (
            review.get("current_source_sha256") is None
            or source_hash == review.get("current_source_sha256")
        ),
        "rule_hash": getattr(module, "RULE_HASH", manifest_row.get("rule_hash")),
        "manifest_rule_hash": manifest_row.get("rule_hash"),
        "version": getattr(module, "VERSION", None),
        "summary": getattr(module, "SUMMARY", catalog_row.get("summary")),
        "axes": axes,
        "max_declared_grid_h": max_h,
        "max_declared_grid_w": max_w,
        "max_declared_side": max(v for v in (max_h, max_w) if v is not None),
        "examples_needed": getattr(module, "EXAMPLES_NEEDED", None),
        "declared_rivals": sorted(getattr(module, "LESSON_COMPETITORS", {})),
        "approved": catalog_row.get("train_safety") == "reviewed_safe",
        "train_safety": catalog_row.get("train_safety"),
        "review_status": catalog_row.get("review_status"),
        "mix_weight": catalog_row.get("mix_weight"),
        "kind": catalog_row.get("kind"),
        "sources": catalog_row.get("sources", []),
        "selection_reasons": manifest.get("selection", {}).get("reasons", {}).get(task_id, []),
        "unresolved_audits": sum(
            1 for audit in review.get("audits", []) if audit.get("resolution") == "unresolved"
        ),
        "review_decisions": len(review.get("decisions", [])),
        "test_file_count": test_file_count,
        "test_function_count": test_function_count,
        "workspace_files": sorted(
            str(path.relative_to(task_dir))
            for path in (task_dir / "workspace").glob("**/*")
            if path.is_file()
        ) if (task_dir / "workspace").is_dir() else [],
        "parametric_priority_record": priority,
    }


def main() -> None:
    started = time.monotonic()
    out = Path(__file__).resolve().parent
    root = find_root(__file__)
    work = root.parent
    manifest_path = work / "PACKET-MANIFEST.json"
    context_path = work / "TRAINING-CONTEXT.md"
    catalog_path = root / "catalog" / "puzzles.jsonl"
    manifest = read_json(manifest_path)
    assert isinstance(manifest, dict)
    catalog = catalog_rows(catalog_path)

    main_ids = sorted(manifest["main_draw_policy"]["ids"])
    peer_pool = [task_id for task_id in main_ids if task_id != PRIMARY_ID]
    peers = random.Random(int(TICKET_SEED, 16)).sample(peer_pool, 2)
    assert peers == EXPECTED_PEERS, (peers, EXPECTED_PEERS)
    selection = {
        "ticket_id": TICKET_ID,
        "primary": PRIMARY_ID,
        "seed": TICKET_SEED,
        "algorithm": "primary fixed by ticket; random.Random(int(ticket_seed,16)).sample(sorted(main-draw IDs excluding primary),2)",
        "peer_pool_count": len(peer_pool),
        "peer_pool_sha256": sha256_bytes(canonical_bytes(peer_pool)),
        "peer_ids": peers,
    }
    (out / "comparison_selection.json").write_text(json.dumps(selection, indent=2, sort_keys=True) + "\n")

    sampled = [
        inspect_task(root=root, manifest=manifest, catalog=catalog, task_id=task_id)
        for task_id in [PRIMARY_ID, *peers]
    ]
    inspection = {
        "ticket_id": TICKET_ID,
        "packet_manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
        "training_context_sha256": sha256_bytes(context_path.read_bytes()),
        "catalog_sha256": sha256_bytes(catalog_path.read_bytes()),
        "sampled_records": sampled,
        "draw_context": {
            "main_distribution": manifest["main_draw_policy"]["distribution"],
            "main_pool_count": len(main_ids),
            "conditional_probability_each_main": 1 / len(main_ids),
            "main_priority_scope": manifest["main_draw_policy"]["priority_scope"],
            "authoring_focus_probability": manifest["authoring_focus_policy"]["probability"],
            "authoring_focus_anchor_count": len(manifest["authoring_focus_policy"]["anchors"]),
            "authoring_focus_scope": manifest["authoring_focus_policy"]["scope"],
            "authoring_focus_target_selection": manifest["authoring_focus_policy"]["target_selection"],
            "allocation_ticket_weight": manifest["supplementary_ticket_policy"]["weights"]["allocation_quality"],
            "ticket_weight_sum": sum(manifest["supplementary_ticket_policy"]["weights"].values()),
            "ticket_weight_basis": manifest["supplementary_ticket_policy"]["weight_basis"],
            "parametric_selected_tier": manifest["parametric_priority"]["selected_tier"],
            "parametric_selected_tier_count": manifest["parametric_priority"]["counts"][manifest["parametric_priority"]["selected_tier"]],
        },
    }
    (out / "inspection.json").write_text(json.dumps(inspection, indent=2, sort_keys=True) + "\n")

    primary = sampled[0]
    assert primary["current_source_sha256"] == PINNED_SOURCE_SHA256
    assert primary["rule_hash"] == PINNED_RULE_HASH
    assert primary["source_matches_manifest"] and primary["source_matches_review_index"]

    generator, _source_path, source_hash = load_selected_generator(PRIMARY_ID, root=root)
    programs = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(root).read_text().splitlines())
        if row.get("task_id") == PRIMARY_ID
    }
    assert len(programs) == 1
    program = programs.pop()
    normalized_rule_hash = sha256_bytes(" ".join(program.split()).encode())[:12]
    assert normalized_rule_hash == PINNED_RULE_HASH
    callable_text = wrap_rule(program)

    episode_seed = int(hashlib.sha256((TICKET_SEED + ":episode").encode()).hexdigest()[:16], 16)
    grids = [generator.generate(episode_seed, index, difficulty="hard") for index in range(7)]
    validation_errors = [generator.self_check(grid) for grid in grids]
    assert not any(validation_errors), validation_errors
    input_hashes = [sha256_bytes(canonical_bytes(grid)) for grid in grids]
    assert len(set(input_hashes)) == len(input_hashes), "duplicate demo/query inputs"

    bridge_started = time.monotonic()
    bridge = RacketBridge(timeout=15, startup_timeout=45)
    try:
        racket_startup_seconds = time.monotonic() - bridge_started
        bridge.eval_text(f"(define allocation_rule {callable_text})")
        label_started = time.monotonic()
        outputs = []
        for grid in grids:
            bridge.define_grid("allocation_input", grid)
            outputs.append(bridge.eval_text("(allocation_rule allocation_input)"))
        racket_label_seconds = time.monotonic() - label_started
        runtime_identity = bridge.runtime_identity
    finally:
        bridge.close()

    assert all(generator.rule_mirror(grid) == output for grid, output in zip(grids, outputs))
    pairs = [{"input": grid, "output": output} for grid, output in zip(grids, outputs)]
    demos, queries = pairs[:3], pairs[3:]
    rival_demo_fits = {
        name: [rival(demo["input"]) == demo["output"] for demo in demos]
        for name, rival in generator.LESSON_COMPETITORS.items()
    }
    surviving_rivals = [name for name, fits in rival_demo_fits.items() if all(fits)]
    identifiability = [generator.lesson_identifiable(demos, query) for query in queries]
    assert not surviving_rivals, surviving_rivals
    assert not any(identifiability), identifiability

    episode = {
        "task_id": PRIMARY_ID,
        "ticket_id": TICKET_ID,
        "seed": episode_seed,
        "difficulty": "hard",
        "source_sha256": source_hash,
        "rule_hash": normalized_rule_hash,
        "train": demos,
        "test": queries,
    }
    (out / "private_episode.json").write_text(json.dumps(episode, indent=2) + "\n")

    probe = {
        "schema": "arcpuzzles-allocation-quality-probe-v1",
        "ticket_id": TICKET_ID,
        "status": "completed",
        "primary_task_id": PRIMARY_ID,
        "ticket_seed": TICKET_SEED,
        "episode_seed": episode_seed,
        "source_sha256": source_hash,
        "rule_hash": normalized_rule_hash,
        "demo_count": len(demos),
        "query_count": len(queries),
        "all_inputs_distinct": True,
        "input_shapes": [[len(grid), len(grid[0])] for grid in grids],
        "max_observed_side": max(max(len(grid), len(grid[0])) for grid in grids),
        "validation_errors": validation_errors,
        "racket_labels_checked": len(outputs),
        "racket_startup_seconds": round(racket_startup_seconds, 6),
        "racket_label_seconds": round(racket_label_seconds, 6),
        "runtime_identity": runtime_identity,
        "python_racket_parity": True,
        "rival_demo_fits": rival_demo_fits,
        "surviving_named_rivals": surviving_rivals,
        "per_query_identifiability_errors": identifiability,
        "schedule_profiles": [generator.schedule_profile(episode_seed, index, "hard") for index in range(7)],
        "input_sha256": input_hashes,
        "query_output_sha256": [sha256_bytes(canonical_bytes(query["output"])) for query in queries],
        "four_query_label_accounting": {
            "one_episode_labels": 7,
            "four_separate_one_query_episode_labels": 16,
            "label_count_reduction_fraction": 9 / 16,
            "note": "Arithmetic only; not a measured token, wall-time, or model-quality reduction.",
        },
        "scope": "One source-bound seven-input episode for the pinned primary; current metadata inspection for two seed-selected peers. No peer generator execution, corpus census, model job, weight change, or training admission.",
        "elapsed_seconds": round(time.monotonic() - started, 6),
    }
    (out / "probe_result.json").write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": probe["status"],
        "sampled_ids": [row["task_id"] for row in sampled],
        "demo_count": probe["demo_count"],
        "query_count": probe["query_count"],
        "racket_labels_checked": probe["racket_labels_checked"],
        "surviving_named_rivals": probe["surviving_named_rivals"],
        "elapsed_seconds": probe["elapsed_seconds"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()

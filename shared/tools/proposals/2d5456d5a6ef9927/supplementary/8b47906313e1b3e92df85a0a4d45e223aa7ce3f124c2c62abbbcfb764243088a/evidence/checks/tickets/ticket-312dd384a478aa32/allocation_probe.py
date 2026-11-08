"""Bounded allocation-quality probe for ticket-312dd384a478aa32.

Deterministically inspects the pinned primary plus two seed-selected current
records, then executes one seven-grid (3 demo + 4 query) canonical-Racket probe
on the primary's retained fixed-anchor witness window.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import tempfile
import time
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TICKET_ID = "ticket-312dd384a478aa32"
SEED_HEX = "669dfdf13fda8154ea6f58655bd8e0a140897735516b7170a55c29255cdaf055"
PRIMARY = "71d5c4ac6ea3"
EXCLUDED_OFFICIAL_TARGETS = {PRIMARY, "2534c7164e36", "a631936f7715"}
EXPECTED_PRIMARY_SHA = "e70ca9f847fc4919d7cba9fa328eec429f34aea56d6a9fe99facc6a0d5e9c11f"
EXPECTED_RULE_HASH = "ed3afc80127d"
PROBE_SEED = 2
PROBE_START = 49
PROBE_DIFFICULTY = "easy"
DEMO_COUNT = 3
QUERY_COUNT = 4


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def points(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == color
    ]


def solve_stamp(grid: list[list[int]], fixed_origin: tuple[int, int] | None = None) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    anchors = points(grid, 9)
    if not anchors:
        return [[0 for _ in row] for row in grid]
    origin = fixed_origin if fixed_origin is not None else anchors[0]
    offsets = [(row - origin[0], col - origin[1]) for row, col in points(grid, 1)]
    output = [[0 for _ in range(width)] for _ in range(height)]
    for seed_row, seed_col in points(grid, 2):
        for delta_row, delta_col in offsets:
            row, col = seed_row + delta_row, seed_col + delta_col
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = 8
    return output


def source_origins(repo: Path, task_id: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    solution_root = repo / "shared/data/base/solutions"
    for path in sorted(solution_root.rglob(f"*__{task_id}.json")):
        rel = path.relative_to(solution_root)
        parts = rel.parts
        if parts[0] == "banks" and len(parts) >= 3:
            source = f"bank:{parts[1]}"
        else:
            source = parts[0]
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            payload = {}
        records.append(
            {
                "source": source,
                "path": str(path.relative_to(repo)),
                "alias": str(payload.get("source_task_id") or payload.get("task_id") or ""),
            }
        )
    return records


def review_summary(repo: Path, task_id: str) -> dict[str, Any]:
    path = repo / "generators" / task_id / "evidence/review_index.json"
    if not path.exists():
        return {"present": False, "audits": [], "decisions": []}
    payload = json.loads(path.read_text())
    audits = payload.get("audits", [])
    decisions = payload.get("decisions", [])
    return {
        "present": True,
        "path": str(path.relative_to(repo)),
        "sha256": sha256_bytes(path.read_bytes()),
        "current_source_sha256": payload.get("current_source_sha256"),
        "audit_count": len(audits),
        "audit_resolutions": [item.get("resolution") for item in audits],
        "audit_triage_statuses": [
            (item.get("triage") or {}).get("status") for item in audits
        ],
        "audit_verification_statuses": [item.get("verification_status") for item in audits],
        "decision_count": len(decisions),
        "decision_verification_statuses": [
            item.get("verification_status") for item in decisions
        ],
    }


def inspect_record(
    repo: Path,
    manifest: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
    weights: dict[str, float],
    task_id: str,
) -> dict[str, Any]:
    meta = manifest["generators"][task_id]
    source_path = repo / meta["generator"]
    source_text = source_path.read_text()
    tests_dir = source_path.parent / "tests"
    test_files = (
        [str(path.relative_to(repo)) for path in sorted(tests_dir.rglob("test*.py"))]
        if tests_dir.exists()
        else []
    )
    counterexample_files = [
        str(path.relative_to(repo))
        for path in sorted((source_path.parent / "counterexamples").rglob("*"))
        if path.is_file()
    ] if (source_path.parent / "counterexamples").exists() else []
    actual_sha = sha256_bytes(source_path.read_bytes())
    row = catalog[task_id]
    return {
        "task_id": task_id,
        "approved": bool(meta.get("approved")),
        "in_main_authoring_pool": task_id in manifest.get("main_ids", []),
        "selection_reasons": manifest["selection"]["reasons"].get(task_id, []),
        "source_path": str(source_path.relative_to(repo)),
        "manifest_source_sha256": meta.get("generator_sha256"),
        "actual_source_sha256": actual_sha,
        "source_matches_pin": actual_sha == meta.get("generator_sha256"),
        "rule_hash": meta.get("rule_hash"),
        "mix_weight": weights.get(task_id),
        "origins": source_origins(repo, task_id),
        "catalog": {
            "version": row.get("version"),
            "difficulty": row.get("difficulty"),
            "combinatorial_reach": row.get("combinatorial_reach"),
            "reach_score": row.get("reach_score"),
            "diversity_score": row.get("diversity_score"),
            "live_axes": row.get("live_axes", []),
            "locked_axes": row.get("locked_axes", []),
            "axis_cardinality": row.get("axis_cardinality", {}),
            "lint_status": row.get("lint_status"),
            "tech_debt": row.get("tech_debt", []),
            "size_relation": row.get("size_relation"),
            "summary": row.get("summary"),
        },
        "contract_symbols": {
            "RULE_HASH": "RULE_HASH" in source_text,
            "EXAMPLES_NEEDED": "EXAMPLES_NEEDED" in source_text,
            "LESSON_SCHEDULE_PERIOD": "LESSON_SCHEDULE_PERIOD" in source_text,
            "SEMANTIC_RIVALS": "SEMANTIC_RIVALS" in source_text,
            "LESSON_COMPETITORS": "LESSON_COMPETITORS" in source_text,
            "CANONICAL_SHORTCUTS": "CANONICAL_SHORTCUTS" in source_text,
            "lesson_identifiable": "def lesson_identifiable" in source_text,
            "observe_overrides": "def observe_overrides" in source_text,
            "unknown_override_rejection": "unknown override" in source_text,
        },
        "task_tests": test_files,
        "parametric_workspace_present": (source_path.parent / "workspace/parametric").is_dir(),
        "counterexample_file_count": len(counterexample_files),
        "counterexample_files": counterexample_files,
        "review": review_summary(repo, task_id),
    }


def main() -> None:
    out = Path(__file__).resolve().parent
    root = find_root(__file__)
    repo = root
    work = repo.parent
    tempfile.tempdir = str(out)
    os.environ["TMPDIR"] = str(out)
    started = time.monotonic()

    manifest = json.loads((work / "PACKET-MANIFEST.json").read_text())
    weights = json.loads((repo / "shared/data/derived/generator_weights.json").read_text())
    catalog: dict[str, dict[str, Any]] = {}
    for line in (repo / "shared/data/derived/generator_catalog.jsonl").read_text().splitlines():
        row = json.loads(line)
        catalog[row["task_id"]] = row

    eligible = sorted(
        task_id
        for task_id in manifest["generators"]
        if task_id not in EXCLUDED_OFFICIAL_TARGETS
        and (repo / manifest["generators"][task_id]["generator"]).exists()
    )
    peers = random.Random(int(SEED_HEX, 16)).sample(eligible, 2)
    sampled = [PRIMARY, *peers]
    selection = {
        "ticket_id": TICKET_ID,
        "primary": PRIMARY,
        "ticket_seed": SEED_HEX,
        "algorithm": (
            "primary pinned by ticket; peers = random.Random(int(ticket_seed,16)).sample(" 
            "sorted current generator IDs excluding the main target, audit target and primary, 2)"
        ),
        "excluded_official_targets": sorted(EXCLUDED_OFFICIAL_TARGETS),
        "eligible_peer_count": len(eligible),
        "peer_ids": peers,
        "sampled_ids": sampled,
    }
    (out / "comparison_selection.json").write_text(json.dumps(selection, indent=2) + "\n")

    inspected = [inspect_record(repo, manifest, catalog, weights, task_id) for task_id in sampled]
    if not all(row["source_matches_pin"] for row in inspected):
        raise RuntimeError("sampled source drift")
    inspection = {
        "schema": "arcpuzzles-allocation-quality-inspection-v1",
        "ticket_id": TICKET_ID,
        "sampled_records": inspected,
        "pool_summary": {
            "packet_generator_count": len(manifest["generators"]),
            "main_authoring_pool_count": len(manifest.get("main_ids", [])),
            "owner_generator_count": manifest["selection"].get("owner_generator_count"),
            "selection_policy": manifest["selection"].get("policy"),
            "selection_quotas": manifest["selection"].get("quotas"),
            "sampled_selection_reasons": {
                task_id: manifest["selection"]["reasons"].get(task_id, [])
                for task_id in sampled
            },
            "sampled_weights": {task_id: weights.get(task_id) for task_id in sampled},
            "approved_sampled_ids": [row["task_id"] for row in inspected if row["approved"]],
            "unapproved_sampled_ids": [row["task_id"] for row in inspected if not row["approved"]],
        },
        "coverage_gaps": [
            "No ARC-GEN or RE-ARC record was selected by this three-record seed sample; no source-family ranking is inferred for either.",
            "Catalog rows are dated metadata; current source identities and review indexes were checked separately.",
            "No model-learning or mastery experiment was run.",
        ],
        "training_context_sha256": sha256_bytes((work / "TRAINING-CONTEXT.md").read_bytes()),
    }
    (out / "inspection.json").write_text(json.dumps(inspection, indent=2) + "\n")

    report: dict[str, Any] = {
        "schema": "arcpuzzles-allocation-quality-probe-v1",
        "ticket_id": TICKET_ID,
        "task_id": PRIMARY,
        "status": "unknown",
        "probe_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "arguments": {
            "seed": PROBE_SEED,
            "start": PROBE_START,
            "difficulty": PROBE_DIFFICULTY,
            "demo_count": DEMO_COUNT,
            "query_count": QUERY_COUNT,
        },
        "query_answers_used_for_rival_elimination": False,
    }
    try:
        primary_meta = manifest["generators"][PRIMARY]
        if primary_meta["generator_sha256"] != EXPECTED_PRIMARY_SHA:
            raise RuntimeError("ticket/manifest source pin disagreement")
        generator, source_path, source_hash = load_selected_generator(PRIMARY, root=repo)
        if source_hash != EXPECTED_PRIMARY_SHA:
            raise RuntimeError("primary source drift")

        programs = {
            row["program_solution"]
            for row in map(json.loads, canonical_path(repo).read_text().splitlines())
            if row.get("task_id") == primary_meta["rule_task_id"]
        }
        if len(programs) != 1:
            raise RuntimeError(f"expected one canonical program, found {len(programs)}")
        program = programs.pop()
        rule_hash = sha256_bytes(" ".join(program.split()).encode())[:12]
        if rule_hash != EXPECTED_RULE_HASH:
            raise RuntimeError(f"canonical rule drift: {rule_hash}")
        callable_text = wrap_rule(program)
        (out / "canonical_rule.rkt").write_text(program)

        generation_started = time.monotonic()
        grids = [
            generator.generate(
                PROBE_SEED,
                PROBE_START + offset,
                difficulty=PROBE_DIFFICULTY,
            )
            for offset in range(DEMO_COUNT + QUERY_COUNT)
        ]
        validation_errors = [
            generator.self_check(grid, difficulty=PROBE_DIFFICULTY) for grid in grids
        ]
        if any(validation_errors):
            raise RuntimeError(f"source validation failure: {validation_errors}")
        if len({canonical_bytes(grid) for grid in grids}) != len(grids):
            raise RuntimeError("duplicate input in probe lesson")
        anchors = [points(grid, 9)[0] for grid in grids]
        fixed_origin = anchors[0]
        if not all(anchor == fixed_origin for anchor in anchors[:DEMO_COUNT]):
            raise RuntimeError("retained fixed-origin witness no longer has fixed demos")
        report["generation_seconds"] = round(time.monotonic() - generation_started, 6)

        bridge_started = time.monotonic()
        bridge = RacketBridge(timeout=15, startup_timeout=45)
        try:
            report["racket_startup_seconds"] = round(time.monotonic() - bridge_started, 6)
            bridge.eval_text(f"(define allocation_rule {callable_text})")
            label_started = time.monotonic()
            outputs: list[list[list[int]]] = []
            for grid in grids:
                bridge.define_grid("allocation_input", grid)
                outputs.append(bridge.eval_text("(allocation_rule allocation_input)"))
            report["racket_label_seconds"] = round(time.monotonic() - label_started, 6)
            report["runtime_identity"] = bridge.runtime_identity
        finally:
            bridge.close()

        mirrors = [solve_stamp(grid) for grid in grids]
        if mirrors != outputs:
            raise RuntimeError("independent mirror disagrees with canonical Racket labels")
        rivals = [solve_stamp(grid, fixed_origin=fixed_origin) for grid in grids]
        rival_fits = [rival == actual for rival, actual in zip(rivals, outputs)]
        query_diff_cells = [
            sum(
                left != right
                for actual_row, rival_row in zip(actual, rival)
                for left, right in zip(actual_row, rival_row)
            )
            for actual, rival in zip(outputs[DEMO_COUNT:], rivals[DEMO_COUNT:])
        ]
        if not all(rival_fits[:DEMO_COUNT]):
            raise RuntimeError("fixed-origin rival no longer fits all demonstrations")
        if not all(count > 0 for count in query_diff_cells):
            raise RuntimeError("at least one query fails to refute fixed-origin rival")

        pairs = [
            {
                "sample_index": PROBE_START + index,
                "anchor": list(anchors[index]),
                "input": grid,
                "output": output,
                "fixed_origin_rival_output": rival,
                "rival_matches": rival_fits[index],
            }
            for index, (grid, output, rival) in enumerate(zip(grids, outputs, rivals))
        ]
        demos = pairs[:DEMO_COUNT]
        queries = pairs[DEMO_COUNT:]
        private_episode = {
            "task_id": PRIMARY,
            "source_sha256": source_hash,
            "rule_hash": rule_hash,
            "seed": PROBE_SEED,
            "start": PROBE_START,
            "difficulty": PROBE_DIFFICULTY,
            "rival_fixed_origin": list(fixed_origin),
            "train": demos,
            "test": queries,
        }
        (out / "private_episode.json").write_text(json.dumps(private_episode, indent=2) + "\n")

        challenge = {
            "train": [{"input": pair["input"], "output": pair["output"]} for pair in demos],
            "test": [{"input": pair["input"], "output": pair["output"]} for pair in queries],
        }
        public_dir = out / "public"
        public_dir.mkdir(exist_ok=True)
        public_name = public_challenge_id(challenge) + ".json"
        public_path = public_dir / public_name
        public_path.write_bytes(public_challenge_bytes(challenge))

        report.update(
            {
                "status": "completed",
                "source_path": str(source_path.relative_to(repo)),
                "source_sha256": source_hash,
                "rule_hash": rule_hash,
                "canonical_text_sha256": sha256_bytes(program.encode()),
                "callable_text_sha256": sha256_bytes(callable_text.encode()),
                "racket_labels_checked": len(outputs),
                "python_racket_parity": True,
                "all_inputs_distinct": True,
                "validation_errors": validation_errors,
                "demo_sample_indices": list(range(PROBE_START, PROBE_START + DEMO_COUNT)),
                "query_sample_indices": list(
                    range(PROBE_START + DEMO_COUNT, PROBE_START + DEMO_COUNT + QUERY_COUNT)
                ),
                "anchors": [list(anchor) for anchor in anchors],
                "fixed_origin": list(fixed_origin),
                "fixed_origin_rival_demo_fits": rival_fits[:DEMO_COUNT],
                "fixed_origin_rival_query_fits": rival_fits[DEMO_COUNT:],
                "query_differing_cell_counts": query_diff_cells,
                "input_shapes": [[len(grid), len(grid[0])] for grid in grids],
                "input_sha256": [sha256_bytes(canonical_bytes(grid)) for grid in grids],
                "query_output_sha256": [
                    sha256_bytes(canonical_bytes(output)) for output in outputs[DEMO_COUNT:]
                ],
                "public_path": "public/" + public_name,
                "public_sha256": sha256_bytes(public_path.read_bytes()),
                "finding": (
                    "The fixed-origin rival fits all three demonstrations but fails all four "
                    "Racket-labeled queries; the current source therefore lacks a lesson-level "
                    "schedule/qualification guarantee even though individual inputs are valid."
                ),
                "scope": (
                    "One retained seven-input window under seed 2/easy/start 49. This reproduces "
                    "a known source-bound lesson defect; it is not a corpus-wide rate estimate."
                ),
            }
        )
    except Exception as error:
        report.update(
            {
                "status": "blocked",
                "error_type": type(error).__name__,
                "error": str(error),
            }
        )
        raise
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 6)
        (out / "probe_result.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        print(
            json.dumps(
                {
                    key: report.get(key)
                    for key in (
                        "status",
                        "racket_labels_checked",
                        "anchors",
                        "fixed_origin_rival_demo_fits",
                        "fixed_origin_rival_query_fits",
                        "query_differing_cell_counts",
                        "elapsed_seconds",
                        "error",
                    )
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()

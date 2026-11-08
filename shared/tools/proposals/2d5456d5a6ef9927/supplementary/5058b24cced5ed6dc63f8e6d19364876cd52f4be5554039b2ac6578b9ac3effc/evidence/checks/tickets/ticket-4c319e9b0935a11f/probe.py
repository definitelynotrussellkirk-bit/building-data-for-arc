#!/usr/bin/env python3
"""One bounded source-bound allocation-quality probe for ticket-4c319e9b0935a11f.

The executable portion is intentionally limited to the assigned primary source.
It assembles one three-demo/four-query lesson, executes the pinned canonical
Racket rule once over all seven grids, checks an independent Python mirror,
checks deduplication, and measures three plausible lesson rivals.  The two
seeded comparison records are inspected from current packet/catalog evidence;
they are not executed, preserving the one-probe budget.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
import re
import time
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TICKET_ID = "ticket-4c319e9b0935a11f"
TICKET_SEED = "a14b0b2672ab4652b706f73703a4af4a61e04a45c3385577e1dbbdca84aa75ea"
PRIMARY_ID = "5553241d87bf"
PRIMARY_SOURCE_SHA256 = "b5f6ba93ce67123cb4c48e979b323277bdd284e400329a1e4f332a24707fc23d"
PRIMARY_RULE_HASH = "064666b78c2e"
EXPECTED_COMPARISON_IDS = ["7355dc4aa5e5", "6f81e8b8bc90"]
DEMO_PROFILES = ["public_1", "template_with_zero", "multiple_dot_shapes"]
QUERY_PROFILES = [
    "rectangular_cells",
    "cell3_corner_template",
    "cell4_center_template",
    "cell5_edge_template",
]
ROOT = find_root(__file__)
WORK = ROOT.parent
OUT = WORK / "checks" / "tickets" / TICKET_ID
MANIFEST_PATH = WORK / "PACKET-MANIFEST.json"
CATALOG_PATH = ROOT / "catalog" / "puzzles.jsonl"
STARTED = time.perf_counter()


def stable_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(stable_bytes(value))


def write_json(name: str, value: Any) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_catalog() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line in CATALOG_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["id"]] = row
    return rows


def test_function_count(home: Path) -> int:
    count = 0
    tests = home / "tests"
    if not tests.is_dir():
        return 0
    for path in tests.glob("test*.py"):
        count += len(re.findall(r"^\s*def test_", path.read_text(encoding="utf-8"), flags=re.MULTILINE))
    return count


def parametric_files(home: Path) -> list[str]:
    workspace = home / "workspace" / "parametric"
    if not workspace.is_dir():
        return []
    return sorted(str(path.relative_to(home)) for path in workspace.rglob("*") if path.is_file())


def canonical_sources_and_pairs(task_id: str) -> tuple[list[str], list[dict[str, Any]]]:
    sources: list[str] = []
    pairs: list[dict[str, Any]] = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") != task_id:
            continue
        source = row.get("program_solution")
        if isinstance(source, str):
            sources.append(source)
        for split in ("train", "test"):
            for index, pair in enumerate(row.get(split, [])):
                pairs.append({"source": row.get("source"), "split": split, "pair_index": index, **pair})
    return sources, pairs


def source_callable(source: str) -> str:
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise AssertionError("canonical source is not exactly one rule! form")
    callable_source = source[len(prefix) : -1]
    if not callable_source.startswith("(lambda (g)"):
        raise AssertionError("canonical source does not expose lambda over g")
    return callable_source


def grid_literal(grid: Any) -> str:
    normalized = normalize_grid(grid)
    return "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in normalized) + ")"


def execute_many(source: str, grids: list[Any]) -> tuple[list[list[list[int]]], float]:
    expression = f"(map {source_callable(source)} '({' '.join(grid_literal(grid) for grid in grids)}))"
    started = time.perf_counter()
    with RacketBridge(max_calls_before_restart=32) as bridge:
        result = bridge.eval_text(expression)
    elapsed = time.perf_counter() - started
    return [normalize_grid(grid) for grid in result], elapsed


def slot_seed(profile: str, slot: int) -> int:
    digest = hashlib.sha256(f"{TICKET_SEED}:{profile}:{slot}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % (2**63)


def copy_pattern_into(output: list[list[int]], facts: dict[str, Any], targets: list[tuple[int, int]], *, foreground_only: bool = False) -> list[list[int]]:
    pattern = facts["pattern"]
    background = facts["background"]
    for row_index, col_index in targets:
        row0 = facts["row_bounds"][row_index][0]
        col0 = facts["col_bounds"][col_index][0]
        for drow, pattern_row in enumerate(pattern):
            for dcol, value in enumerate(pattern_row):
                if foreground_only and value in (0, background):
                    continue
                output[row0 + drow][col0 + dcol] = value
    return output


def rival_foreground_only(grid: list[list[int]], facts: dict[str, Any]) -> list[list[int]]:
    return copy_pattern_into(copy.deepcopy(grid), facts, list(facts["targets"]), foreground_only=True)


def rival_exactly_one_zero_target(grid: list[list[int]], facts: dict[str, Any]) -> list[list[int]]:
    targets = [target for target in facts["targets"] if facts["dot_counts"][target] == 1]
    return copy_pattern_into(copy.deepcopy(grid), facts, targets)


def rival_stamp_every_non_template_cell(grid: list[list[int]], facts: dict[str, Any]) -> list[list[int]]:
    template = tuple(facts["template_index"])
    targets = [
        (row_index, col_index)
        for row_index in range(len(facts["row_bounds"]))
        for col_index in range(len(facts["col_bounds"]))
        if (row_index, col_index) != template
    ]
    return copy_pattern_into(copy.deepcopy(grid), facts, targets)


manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
catalog = load_catalog()
peer_ids = sorted(set(manifest["generators"]) - {PRIMARY_ID})
selected_peers = random.Random(int(TICKET_SEED, 16)).sample(peer_ids, 2)
assert selected_peers == EXPECTED_COMPARISON_IDS
selected_ids = [PRIMARY_ID, *selected_peers]

selection = {
    "schema": "arcpuzzles-allocation-sample-v1",
    "ticket_id": TICKET_ID,
    "seed": TICKET_SEED,
    "algorithm": "Primary ticket target plus random.Random(int(seed,16)).sample(sorted current packet peer IDs, 2)",
    "eligible_peer_count": len(peer_ids),
    "eligible_peer_universe_sha256": sha256_bytes("\n".join(peer_ids).encode("utf-8")),
    "selected_ids": selected_ids,
    "packet_generator_count": len(manifest["generators"]),
    "owner_generator_count": manifest["selection"]["owner_generator_count"],
}
write_json("selection.json", selection)

inspection_records: list[dict[str, Any]] = []
for task_id in selected_ids:
    packet_row = manifest["generators"][task_id]
    source_path = ROOT / packet_row["generator"]
    source_digest = sha256_bytes(source_path.read_bytes())
    assert source_digest == packet_row["generator_sha256"]
    row = catalog[task_id]
    home = ROOT / "generators" / task_id
    review_index = home / "evidence" / "review_index.json"
    supplementary_current = home / "evidence" / "supplementary-current.json"
    params = parametric_files(home)
    inspection_records.append(
        {
            "task_id": task_id,
            "packet": packet_row,
            "source_path": str(source_path.relative_to(ROOT)),
            "source_sha256_actual": source_digest,
            "source_matches_packet_pin": True,
            "catalog": {
                key: row.get(key)
                for key in (
                    "mix_weight",
                    "train_safety",
                    "review_status",
                    "health",
                    "sources",
                    "version",
                    "semantic_veto",
                    "kind",
                    "summary",
                )
            },
            "packet_selection_reason": manifest["selection"]["reasons"].get(task_id, []),
            "test_function_count": test_function_count(home),
            "has_parametric_workspace": bool(params),
            "parametric_file_count": len(params),
            "parametric_files": params,
            "has_review_index": review_index.is_file(),
            "review_index_sha256": sha256_bytes(review_index.read_bytes()) if review_index.is_file() else None,
            "has_current_supplementary_index": supplementary_current.is_file(),
            "supplementary_index_sha256": sha256_bytes(supplementary_current.read_bytes()) if supplementary_current.is_file() else None,
        }
    )
write_json("inspection.json", {"schema": "arcpuzzles-allocation-inspection-v1", "records": inspection_records})

module, primary_source_path, primary_digest = load_selected_generator(PRIMARY_ID, root=ROOT)
assert primary_digest == PRIMARY_SOURCE_SHA256
assert module.RULE_HASH == PRIMARY_RULE_HASH
assert module.SCENE_PROFILES == module.PUBLIC_PROFILES + module.GENERAL_PROFILES
assert set(DEMO_PROFILES + QUERY_PROFILES).issubset(set(module.SCENE_PROFILES))

program_sources, canonical_pairs = canonical_sources_and_pairs(PRIMARY_ID)
assert program_sources and len(set(program_sources)) == 1
program_source = program_sources[0]
canonical_input_hashes = [sha256_json(pair["input"]) for pair in canonical_pairs]
canonical_occurrences = len(canonical_input_hashes)
canonical_unique_inputs = len(set(canonical_input_hashes))

profiles = DEMO_PROFILES + QUERY_PROFILES
grids: list[list[list[int]]] = []
item_records: list[dict[str, Any]] = []
generation_started = time.perf_counter()
for slot, profile in enumerate(profiles):
    difficulty = None if profile in module.PUBLIC_PROFILES else ("hard" if slot % 2 else "medium")
    seed = slot_seed(profile, slot)
    grid = module.generate(seed, slot, difficulty=difficulty, scene_profile=profile)
    errors = module.self_check(grid, difficulty=difficulty)
    assert errors == []
    observed = module.observe_overrides(grid)
    assert observed == {"scene_profile": profile}
    analysis = module._analysis(grid)
    assert analysis["errors"] == []
    facts = analysis["facts"]
    grids.append(normalize_grid(grid))
    item_records.append(
        {
            "role": "demo" if slot < len(DEMO_PROFILES) else "query",
            "slot": slot if slot < len(DEMO_PROFILES) else slot - len(DEMO_PROFILES),
            "profile": profile,
            "seed": seed,
            "sample_index": slot,
            "difficulty": difficulty,
            "input_sha256": sha256_json(grid),
            "height": len(grid),
            "width": len(grid[0]),
            "background": facts["background"],
            "cell_height": facts["cell_height"],
            "cell_width": facts["cell_width"],
            "logical_rows": len(facts["row_bounds"]),
            "logical_cols": len(facts["col_bounds"]),
            "target_count": len(facts["targets"]),
            "max_dot_count": max(facts["dot_counts"].values()),
            "template_zero_count": len(facts["pattern_zeros"]),
            "self_check_errors": errors,
            "observed_overrides": observed,
        }
    )
generation_seconds = time.perf_counter() - generation_started
assert len({sha256_json(grid) for grid in grids}) == len(grids)

racket_outputs, racket_seconds = execute_many(program_source, grids)
mirror_started = time.perf_counter()
mirror_outputs = [normalize_grid(module.rule_mirror(grid)) for grid in grids]
mirror_seconds = time.perf_counter() - mirror_started
assert racket_outputs == mirror_outputs
assert all(output != grid for grid, output in zip(grids, racket_outputs))
assert len({sha256_json(output) for output in racket_outputs}) == len(racket_outputs)
assert not ({sha256_json(grid) for grid in grids} & {sha256_json(output) for output in racket_outputs})

for item, output in zip(item_records, racket_outputs):
    item["output_sha256"] = sha256_json(output)
    item["changed_cells"] = sum(
        before != after
        for input_row, output_row in zip(grids[item_records.index(item)], output)
        for before, after in zip(input_row, output_row)
    )
    item["changed_fraction"] = round(item["changed_cells"] / (item["height"] * item["width"]), 6)

rivals = {
    "copy_foreground_only": rival_foreground_only,
    "stamp_only_cells_with_exactly_one_zero": rival_exactly_one_zero_target,
    "stamp_every_non_template_cell": rival_stamp_every_non_template_cell,
}
rival_report: dict[str, Any] = {}
for name, competitor in rivals.items():
    comparisons = []
    for index in range(len(DEMO_PROFILES)):
        grid = grids[index]
        facts = module._analysis(grid)["facts"]
        rival_output = normalize_grid(competitor(grid, facts))
        label = racket_outputs[index]
        comparisons.append(
            {
                "demo_index": index,
                "profile": DEMO_PROFILES[index],
                "matches_label": rival_output == label,
                "differing_cells": sum(
                    left != right
                    for left_row, right_row in zip(rival_output, label)
                    for left, right in zip(left_row, right_row)
                ),
            }
        )
    survives = all(row["matches_label"] for row in comparisons)
    assert not survives
    rival_report[name] = {
        "survives_all_demos": survives,
        "first_refuting_demo": next(row["demo_index"] for row in comparisons if not row["matches_label"]),
        "comparisons": comparisons,
    }

private_episode = {
    "schema": "arcpuzzles-source-quality-episode-private-v1",
    "task_id": PRIMARY_ID,
    "source_sha256": primary_digest,
    "rule_hash": PRIMARY_RULE_HASH,
    "program_source_sha256": sha256_bytes(program_source.encode("utf-8")),
    "demos": [
        {"input": grids[index], "output": racket_outputs[index], "metadata": item_records[index]}
        for index in range(len(DEMO_PROFILES))
    ],
    "queries": [
        {
            "input": grids[index],
            "output": racket_outputs[index],
            "metadata": item_records[index],
        }
        for index in range(len(DEMO_PROFILES), len(grids))
    ],
}
public_episode = {
    "schema": "arcpuzzles-source-quality-episode-public-v1",
    "task_id": PRIMARY_ID,
    "demos": [{"input": row["input"], "output": row["output"]} for row in private_episode["demos"]],
    "queries": [{"input": row["input"]} for row in private_episode["queries"]],
}
write_json("episode-private.json", private_episode)
write_json("episode-public.json", public_episode)

probe = {
    "schema": "arcpuzzles-allocation-quality-probe-v1",
    "ticket_id": TICKET_ID,
    "task_id": PRIMARY_ID,
    "source_path": str(primary_source_path.relative_to(ROOT)),
    "source_sha256": primary_digest,
    "rule_hash": PRIMARY_RULE_HASH,
    "program_source_sha256": sha256_bytes(program_source.encode("utf-8")),
    "canonical_evidence": {
        "pair_occurrences": canonical_occurrences,
        "unique_inputs": canonical_unique_inputs,
        "duplicate_occurrences": canonical_occurrences - canonical_unique_inputs,
    },
    "episode": {
        "demo_count": len(DEMO_PROFILES),
        "query_count": len(QUERY_PROFILES),
        "all_inputs_distinct": len({sha256_json(grid) for grid in grids}) == len(grids),
        "all_outputs_distinct": len({sha256_json(output) for output in racket_outputs}) == len(racket_outputs),
        "input_output_collision_count": len({sha256_json(grid) for grid in grids} & {sha256_json(output) for output in racket_outputs}),
        "profiles": profiles,
        "items": item_records,
        "max_side": max(max(len(grid), len(grid[0])) for grid in grids),
        "items_with_side_at_least_20": sum(max(len(grid), len(grid[0])) >= 20 for grid in grids),
    },
    "execution": {
        "racket_rule_applications": len(grids),
        "racket_matches_python_mirror": racket_outputs == mirror_outputs,
        "generation_seconds": round(generation_seconds, 6),
        "racket_seconds": round(racket_seconds, 6),
        "python_mirror_seconds": round(mirror_seconds, 6),
    },
    "lesson_rivals": rival_report,
    "covered_semantics": [
        "whole-template copying including zero/background positions",
        "any positive zero count marks a target",
        "unmarked non-template cells stay unchanged",
        "rectangular and 3/4/5-cell geometry",
        "corner/center/edge template placement across the full episode",
    ],
    "uncovered_semantics": [
        "row-major choice among two or more foreground-bearing template candidates: current generator emits exactly one candidate",
        "arbitrary-program identifiability beyond the three bounded rivals",
        "current export acceptance/throughput: this is one source-bound probe, not an export run",
    ],
    "elapsed_seconds": round(time.perf_counter() - STARTED, 6),
    "limit": "one primary-source episode; comparison records were inspected but not executed",
}
write_json("probe.json", probe)

print(json.dumps({
    "ticket_id": TICKET_ID,
    "selected_ids": selected_ids,
    "source_checks": {row["task_id"]: row["source_matches_packet_pin"] for row in inspection_records},
    "racket_matches_python_mirror": probe["execution"]["racket_matches_python_mirror"],
    "distinct_inputs": len({sha256_json(grid) for grid in grids}),
    "demo_count": len(DEMO_PROFILES),
    "query_count": len(QUERY_PROFILES),
    "rivals_eliminated": sum(not row["survives_all_demos"] for row in rival_report.values()),
    "elapsed_seconds": probe["elapsed_seconds"],
}, indent=2, sort_keys=True))

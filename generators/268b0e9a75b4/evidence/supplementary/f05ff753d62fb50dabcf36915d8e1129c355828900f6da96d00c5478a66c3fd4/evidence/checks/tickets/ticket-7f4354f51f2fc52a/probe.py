from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator

TICKET_ID = "ticket-7f4354f51f2fc52a"
TICKET_PROBE_SEED = "b9adf6fc83c5646dcc1b18d27352b1312aec115ced2bf191d6da8d0764a6de2a"
TASK_ID = "268b0e9a75b4"
EXPECTED_SOURCE_SHA256 = "d2c9358d83f264d38d6c7051dfa371f42fce6f73256a77c85149a329ebf89943"
EXPECTED_RULE_HASH = "210dc0194f51"
EXPECTED_ASSETS_SHA256 = "5c72e70841614a462787a5150a807c8c20b22c1f524eea082c3b0a4760f54109"
EXPECTED_INDEX_SHA256 = "3cf9e8c6e7f37f84489f835329dbec3f4830b5daa86cf0a7b2365fc37ae7c4bf"
EXPECTED_AUDIT_RECORD_SHA256 = "4d9b8f4ba6430ebda91a567fadc77daf44b73249dd2e597d89f371330506bc12"
EXPECTED_RETURN_ID = "review-15ca3f0021971a61:v0001"

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
generator, source, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute_rule(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    bridge.define_grid("g", grid)
    body = program[len("(rule!") : -1].strip()
    return bridge.eval_text(body)


def normalize_grid(value: list[Any]) -> list[list[int]]:
    return [
        [int(cell) for cell in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def global_largest_fallback_rival(grid: list[list[int]]) -> list[list[int]]:
    """Use the intended unique branch; otherwise crop the global largest object."""
    components = generator._components(grid)
    order = generator._color_order(grid)
    counts = {
        color: sum(obj["color"] == color for obj in components)
        for color in order
    }
    unique_colors = [color for color in order if counts[color] == 1]
    if unique_colors:
        chosen = next(obj for obj in components if obj["color"] == unique_colors[0])
    else:
        chosen = max(components, key=lambda obj: obj["size"])
    return generator._crop(grid, chosen)


def differing_cells(left: list[list[int]], right: list[list[int]]) -> list[list[int | None]]:
    height = max(len(left), len(right))
    width = max(
        max((len(row) for row in left), default=0),
        max((len(row) for row in right), default=0),
    )
    result: list[list[int | None]] = []
    for row in range(height):
        for col in range(width):
            lv = left[row][col] if row < len(left) and col < len(left[row]) else None
            rv = right[row][col] if row < len(right) and col < len(right[row]) else None
            if lv != rv:
                result.append([row, col, lv, rv])
    return result


def load_canonical() -> dict[str, Any]:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    if len(rows) != 1:
        raise RuntimeError(f"expected one canonical row, found {len(rows)}")
    return rows[0]


def verify_pinned_identity() -> dict[str, Any]:
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source SHA mismatch: {source_sha256}")
    if getattr(generator, "RULE_HASH", None) != EXPECTED_RULE_HASH:
        raise RuntimeError(f"rule hash mismatch: {getattr(generator, 'RULE_HASH', None)!r}")

    assets_path = ROOT / "generators" / TASK_ID / "counterexamples" / "review-15ca3f0021971a61-v0001" / "audit_assets.json"
    index_path = ROOT / "generators" / TASK_ID / "evidence" / "review_index.json"
    if sha256_file(assets_path) != EXPECTED_ASSETS_SHA256:
        raise RuntimeError("audit assets manifest SHA mismatch")
    if sha256_file(index_path) != EXPECTED_INDEX_SHA256:
        raise RuntimeError("audit index SHA mismatch")

    assets = json.loads(assets_path.read_text(encoding="utf-8"))
    if assets.get("return_id") != EXPECTED_RETURN_ID:
        raise RuntimeError("audit return identity mismatch")
    if assets.get("audited_generator_sha256") != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("asset manifest generator SHA mismatch")
    verified_assets = []
    for item in assets.get("files", []):
        path = ROOT / item["path"]
        actual = sha256_file(path)
        if actual != item["sha256"]:
            raise RuntimeError(f"retained asset SHA mismatch: {item['path']}")
        verified_assets.append({"path": item["path"], "sha256": actual})

    index = json.loads(index_path.read_text(encoding="utf-8"))
    records = [row for row in index.get("audits", []) if row.get("return_id") == EXPECTED_RETURN_ID]
    if len(records) != 1:
        raise RuntimeError(f"expected one pinned audit record, found {len(records)}")
    record = records[0]
    record_sha = hashlib.sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if record_sha != EXPECTED_AUDIT_RECORD_SHA256:
        raise RuntimeError(f"audit record SHA mismatch: {record_sha}")
    if record.get("source_sha256") != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("audit record source SHA mismatch")

    return {
        "source_path": str(source.relative_to(ROOT)),
        "source_sha256": source_sha256,
        "rule_hash": generator.RULE_HASH,
        "assets_manifest_path": str(assets_path.relative_to(ROOT)),
        "assets_manifest_sha256": EXPECTED_ASSETS_SHA256,
        "audit_index_path": str(index_path.relative_to(ROOT)),
        "audit_index_sha256": EXPECTED_INDEX_SHA256,
        "audit_record_sha256": record_sha,
        "verified_retained_assets": verified_assets,
    }


identity = verify_pinned_identity()
canonical = load_canonical()
program = canonical["program_solution"]
program_sha256 = hashlib.sha256(program.encode("utf-8")).hexdigest()

seed = 119
band = "easy"
with RacketBridge() as bridge:
    canonical_checks = []
    public_pairs = [*canonical["train"]]
    test = canonical["test"]
    public_pairs.extend(test if isinstance(test, list) else [test])
    for index, pair in enumerate(public_pairs):
        grid = normalize_grid(pair["input"])
        expected = normalize_grid(pair["output"])
        intended = execute_rule(bridge, program, grid)
        if intended != expected:
            raise RuntimeError(f"canonical Racket mismatch at pair {index}")
        rival = global_largest_fallback_rival(grid)
        canonical_checks.append({
            "pair_index": index,
            "rival_matches": rival == intended,
            "branch": generator._analysis(grid)["branch"],
        })

    lesson = []
    for sample_index in range(4):
        grid = generator.generate(seed, sample_index, difficulty=band)
        findings = generator.self_check(grid)
        if findings:
            raise RuntimeError(f"generated pair {sample_index} failed: {findings}")
        intended = execute_rule(bridge, program, grid)
        mirror = generator.rule_mirror(grid)
        if intended != mirror:
            raise RuntimeError("Python mirror disagrees with canonical Racket")
        rival = global_largest_fallback_rival(grid)
        info = generator._analysis(grid)
        lesson.append({
            "sample_index": sample_index,
            "role": "demo" if sample_index < 3 else "query",
            "scene_profile": info["scene_profile"],
            "branch": info["branch"],
            "object_counts": list(info["object_counts"]),
            "chosen_color": info["chosen_color"],
            "input": grid,
            "intended_output": intended,
            "rival_output": rival,
            "rival_matches": rival == intended,
            "differing_cells": differing_cells(intended, rival),
        })

if not all(row["rival_matches"] for row in canonical_checks):
    raise RuntimeError("rival should fit every canonical pair")
if not all(row["rival_matches"] for row in lesson[:3]):
    raise RuntimeError("rival should fit all three generated demonstrations")
if lesson[3]["rival_matches"]:
    raise RuntimeError("query should distinguish the fallback rules")

retained_path = ROOT / "generators" / TASK_ID / "counterexamples" / "review-15ca3f0021971a61-v0001" / "retained" / "checks" / "audit" / TASK_ID / "teaching_shortcut_probe.json"
retained = json.loads(retained_path.read_text(encoding="utf-8"))
replay_projection = {
    "source_sha256": source_sha256,
    "canonical_program_sha256": program_sha256,
    "seed": seed,
    "difficulty": band,
    "canonical_checks": canonical_checks,
    "lesson": lesson,
}
retained_projection = {key: retained[key] for key in replay_projection}
if replay_projection != retained_projection:
    raise RuntimeError("fresh replay differs from the retained semantic witness")

payload = {
    "schema": "arcpuzzles-ticket-audit-replay-v1",
    "ticket_id": TICKET_ID,
    "ticket_probe_seed": TICKET_PROBE_SEED,
    "task_id": TASK_ID,
    "status": "completed",
    "identity": identity,
    "canonical_program_sha256": program_sha256,
    "replay": {
        "seed": seed,
        "difficulty": band,
        "canonical_pair_count": len(canonical_checks),
        "canonical_all_fit_rival": all(row["rival_matches"] for row in canonical_checks),
        "generated_profiles": [row["scene_profile"] for row in lesson],
        "all_three_demos_fit_rival": all(row["rival_matches"] for row in lesson[:3]),
        "query_distinguishes_rival": not lesson[3]["rival_matches"],
        "query_difference_count": len(lesson[3]["differing_cells"]),
        "fresh_replay_matches_retained_witness": True,
        "canonical_checks": canonical_checks,
        "lesson": lesson,
    },
    "conclusion": (
        "The pinned unresolved audit claim reproduced exactly against the pinned "
        "generator, audit record, retained assets, and canonical Racket program. "
        "This replay does not clear or modify the existing audit."
    ),
}
(HERE / "report.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "ticket_id": TICKET_ID,
    "task_id": TASK_ID,
    "status": payload["status"],
    "source_sha256": source_sha256,
    "canonical_all_fit_rival": payload["replay"]["canonical_all_fit_rival"],
    "all_three_demos_fit_rival": payload["replay"]["all_three_demos_fit_rival"],
    "query_distinguishes_rival": payload["replay"]["query_distinguishes_rival"],
    "fresh_replay_matches_retained_witness": True,
}, indent=2, sort_keys=True))

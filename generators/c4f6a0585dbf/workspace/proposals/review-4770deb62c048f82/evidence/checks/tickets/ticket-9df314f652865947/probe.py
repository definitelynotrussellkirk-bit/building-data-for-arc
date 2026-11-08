from __future__ import annotations

from collections import Counter
import ast
import hashlib
import inspect
import json
from pathlib import Path
import random
import re
import time

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TICKET_ID = "ticket-9df314f652865947"
TICKET_SEED = "844c67a5d177353427e6fb29441d77a7bae84c954785a67f86b34e046f2368cf"
ANCHOR_ID = "df0b5d094b2d"
ANCHOR_SHA256 = "90da7d4462f3fd9038a663532c28cc4262c7178fb1cb826844551c20a132b90e"
HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
PACKET_ROOT = ROOT.parent
MANIFEST_PATH = PACKET_ROOT / "PACKET-MANIFEST.json"


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_path(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def grid_sha(grid) -> str:
    return sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def canonical_program(task_id: str) -> str:
    programs = {
        row["program_solution"]
        for row in jsonl(canonical_path(ROOT))
        if row.get("task_id") == task_id
    }
    if len(programs) != 1:
        raise AssertionError(f"{task_id}: expected one canonical program, found {len(programs)}")
    return programs.pop()


def racket_evaluate(bridge: RacketBridge, source: str, grid):
    body = strip_rule_wrapper(source)
    if body.lstrip().startswith("(lambda"):
        datum = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        value = bridge.eval_text(f"({body} '{datum})")
    else:
        bridge.define_grid("g", grid)
        value = bridge.eval_text(body)
    return normalize_grid(value)


def call_self_check(module, grid, difficulty: str):
    signature = inspect.signature(module.self_check)
    kwargs = {"difficulty": difficulty} if "difficulty" in signature.parameters else {}
    return module.self_check(grid, **kwargs)


def test_function_count(task_dir: Path) -> int:
    total = 0
    for path in sorted((task_dir / "tests").glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        total += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
            for node in ast.walk(tree)
        )
    return total


def recursive_values(value, wanted: set[str], found: dict[str, list]):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in wanted and isinstance(child, (int, float, str, list, dict)):
                found.setdefault(key, []).append(child)
            recursive_values(child, wanted, found)
    elif isinstance(value, list):
        for child in value:
            recursive_values(child, wanted, found)


def retained_counts(task_dir: Path) -> dict:
    found: dict[str, list] = {}
    wanted = {"query_count", "demo_count", "demonstration_count", "queries", "demonstrations"}
    for path in sorted(task_dir.rglob("*.json")):
        if path.stat().st_size > 2_000_000:
            continue
        try:
            recursive_values(json.loads(path.read_text(encoding="utf-8")), wanted, found)
        except (json.JSONDecodeError, UnicodeError):
            continue
    compact = {}
    for key, values in found.items():
        numbers = []
        for value in values:
            if type(value) in {int, float}:
                numbers.append(value)
            elif isinstance(value, list):
                numbers.append(len(value))
        if numbers:
            compact[key] = {"max": max(numbers), "observations": len(numbers)}
    return compact


def audit_summary(task_dir: Path) -> dict:
    path = task_dir / "evidence" / "review_index.json"
    if not path.is_file():
        return {"path": None, "audit_count": 0, "open_count": 0, "records": []}
    value = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for audit in value.get("audits", []):
        text = audit.get("text", "")
        records.append(
            {
                "return_id": audit.get("return_id"),
                "resolution": audit.get("resolution"),
                "source_sha256": audit.get("source_sha256"),
                "verification_status": audit.get("verification_status"),
                "text_excerpt": " ".join(text.split())[:700],
                "mentions_no_defect": "no generator defect found" in text.lower(),
                "mentions_possible_shortcut": "possible teaching shortcut" in text.lower(),
                "reported_racket_pairs": [int(n) for n in re.findall(r"(\d+)/(?:\1) source-bound Racket-labelled generated pairs", text)],
                "reported_query_rotations": [int(n) for n in re.findall(r"all \*\*(\d+) query rotations", text)],
            }
        )
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha_path(path),
        "current_source_sha256": value.get("current_source_sha256"),
        "audit_count": len(records),
        "open_count": sum(row["resolution"] not in {"resolved", "no_issue"} for row in records),
        "records": records,
    }


def source_category(sources: list[str]) -> list[str]:
    categories = []
    for source in sources:
        lower = source.lower()
        if "arc-gen" in lower or "arcgen" in lower:
            categories.append("ARC-GEN")
        elif "re-arc" in lower or "rearc" in lower:
            categories.append("RE-ARC")
        elif source.startswith("bank:"):
            categories.append("bank")
        elif source in {"training", "evaluation", "augmented"}:
            categories.append(source)
        else:
            categories.append("other")
    return sorted(set(categories))


started = time.monotonic()
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
all_ids = sorted(manifest["all_ids"])
sampled_ids = random.Random(int(TICKET_SEED, 16)).sample(all_ids, min(3, len(all_ids)))
assert sampled_ids == ["27a915a2c9b3", "1856980929fe", "28c998e193d9"]

anchor_path = ROOT / manifest["generators"][ANCHOR_ID]["generator"]
assert manifest["generators"][ANCHOR_ID]["generator_sha256"] == ANCHOR_SHA256
assert sha_path(anchor_path) == ANCHOR_SHA256

catalog_rows = {row["id"]: row for row in jsonl(ROOT / "catalog" / "puzzles.jsonl")}
derived_rows = {row["task_id"]: row for row in jsonl(ROOT / "shared" / "data" / "derived" / "generator_catalog.jsonl")}
weights = json.loads((ROOT / "shared" / "data" / "derived" / "generator_weights.json").read_text())

selection_reasons = Counter(
    reason for reasons in manifest["selection"]["reasons"].values() for reason in reasons
)
weight_distribution = Counter(str(value) for value in weights.values())
missing_weight_ids = sorted(task_id for task_id in all_ids if task_id not in weights)
source_counts = Counter()
for task_id in all_ids:
    for category in source_category(catalog_rows[task_id].get("sources", [])):
        source_counts[category] += 1

packet_summary = {
    "packet_generator_count": len(all_ids),
    "owner_generator_count": manifest["selection"]["owner_generator_count"],
    "selection_policy": manifest["selection"]["policy"],
    "selection_reasons": dict(sorted(selection_reasons.items())),
    "selection_quotas": manifest["selection"]["quotas"],
    "main_pool": {
        "main_ids": len(manifest["main_ids"]),
        "normal_ids": len(manifest["main_draw_policy"]["normal_ids"]),
        "approved_main_ids": sum(manifest["generators"][task_id]["approved"] for task_id in manifest["main_ids"]),
    },
    "evaluation_focus": {
        "probability": manifest["main_draw_policy"]["evaluation_focus"]["probability"],
        "provided_tasks": manifest["main_draw_policy"]["evaluation_focus"]["provided_tasks"],
        "mapped_tasks": manifest["main_draw_policy"]["evaluation_focus"]["mapped_tasks"],
        "eligible_related_generators": manifest["main_draw_policy"]["evaluation_focus"]["eligible_related_generators"],
        "anchors": len(manifest["main_draw_policy"]["evaluation_focus"]["anchors"]),
        "fallback": manifest["main_draw_policy"]["evaluation_focus"]["fallback"],
    },
    "dataset_weights": {
        "distribution": dict(sorted(weight_distribution.items())),
        "total_mass": sum(weights.values()),
        "weighted_record_count": len(weights),
        "missing_weight_ids": missing_weight_ids,
        "approved_count": sum(manifest["generators"][task_id]["approved"] for task_id in all_ids),
        "approved_mass": sum(weights.get(task_id, 0.0) for task_id in all_ids if manifest["generators"][task_id]["approved"]),
        "unapproved_positive_weight_count": sum(
            not manifest["generators"][task_id]["approved"] and weights.get(task_id, 0.0) > 0 for task_id in all_ids
        ),
        "note": "Positive mix weight is not authoring-draw eligibility; export separately requires current effective approval.",
    },
    "evidence_pool": {
        "current_parametric_manifests": len(manifest["supplementary_ticket_policy"]["candidates"].get("parameter_queries", [])),
        "open_audit_replay_candidates": len(manifest["supplementary_ticket_policy"]["candidates"].get("audit_replay", [])),
    },
    "source_categories_in_packet": dict(sorted(source_counts.items())),
}

records = []
public_ids = []
racket_label_seconds = []
with RacketBridge() as bridge:
    for task_id in sampled_ids:
        task_dir = ROOT / "generators" / task_id
        manifest_row = manifest["generators"][task_id]
        source_path = ROOT / manifest_row["generator"]
        source_digest = sha_path(source_path)
        assert source_digest == manifest_row["generator_sha256"]
        module, selected_source, selected_digest = load_selected_generator(task_id, root=ROOT)
        assert selected_source == source_path and selected_digest == source_digest
        catalog = catalog_rows[task_id]
        derived = derived_rows.get(task_id, {})
        program = canonical_program(task_id)

        base_seed = int.from_bytes(hashlib.sha256((TICKET_SEED + ":" + task_id).encode()).digest()[:8], "big") % 100_000
        grids = [module.generate(base_seed, index, difficulty="medium") for index in (0, 1)]
        assert grids[0] != grids[1]
        checks = [call_self_check(module, grid, "medium") for grid in grids]
        assert checks == [[], []]
        outputs = []
        timings = []
        for grid in grids:
            label_started = time.monotonic()
            output = racket_evaluate(bridge, program, grid)
            timings.append(time.monotonic() - label_started)
            outputs.append(output)
        racket_label_seconds.extend(timings)
        challenge = {
            "train": [{"input": grids[0], "output": outputs[0]}],
            "test": [{"input": grids[1]}],
        }
        visible = public_challenge_bytes(challenge)
        public_id = public_challenge_id(challenge)
        assert public_id == sha_bytes(visible)
        public_ids.append(public_id)

        review = audit_summary(task_dir)
        param_path = task_dir / "workspace" / "parametric" / "evidence" / "manifest.json"
        param = None
        if param_path.is_file():
            param_value = json.loads(param_path.read_text(encoding="utf-8"))
            param = {
                "path": str(param_path.relative_to(ROOT)),
                "sha256": sha_path(param_path),
                "generator_sha256": param_value.get("generator_sha256"),
                "current": param_value.get("generator_sha256") == source_digest,
            }
        shortcut_path = task_dir / "counterexamples" / "current-shortcut.json"
        records.append(
            {
                "task_id": task_id,
                "identity": {
                    "source_path": str(source_path.relative_to(ROOT)),
                    "source_sha256": source_digest,
                    "manifest_hash_matches": True,
                    "version": getattr(module, "VERSION", None),
                    "rule_hash": getattr(module, "RULE_HASH", None),
                    "rule_text_sha256": sha_bytes(program.encode()),
                },
                "allocation": {
                    "packet_selection_reasons": manifest["selection"]["reasons"].get(task_id, []),
                    "approved": manifest_row["approved"],
                    "in_main_ids": task_id in manifest["main_ids"],
                    "in_normal_main_pool": task_id in manifest["main_draw_policy"]["normal_ids"],
                    "mix_weight": weights.get(task_id),
                },
                "catalog": {
                    "review_status": catalog.get("review_status"),
                    "train_safety": catalog.get("train_safety"),
                    "sources": catalog.get("sources", []),
                    "source_categories": source_category(catalog.get("sources", [])),
                    "summary": catalog.get("summary"),
                    "current_reviewed_hash": catalog.get("reviewed_generator_sha256") == source_digest,
                },
                "derived_catalog": {
                    "cataloged_at": derived.get("cataloged_at"),
                    "version": derived.get("version"),
                    "current_version": getattr(module, "VERSION", None),
                    "version_current": derived.get("version") == getattr(module, "VERSION", None),
                    "lint_status": derived.get("lint_status"),
                    "diversity_score": derived.get("diversity_score"),
                    "combinatorial_reach": derived.get("combinatorial_reach"),
                    "live_axes": derived.get("live_axes", []),
                    "locked_axes": derived.get("locked_axes", []),
                    "tech_debt": derived.get("tech_debt", []),
                    "freshness_warning": "Derived metrics are historical when version_current is false.",
                },
                "current_contract": {
                    "axis_names": sorted(getattr(module, "AXES", {}).keys()),
                    "examples_needed": getattr(module, "EXAMPLES_NEEDED", None),
                    "schedule_profiles": list(getattr(module, "SCHEDULE_PROFILES", ())),
                    "focused_test_functions": test_function_count(task_dir),
                },
                "retained_evidence": {
                    "review_index": review,
                    "parametric_manifest": param,
                    "retained_count_fields": retained_counts(task_dir),
                    "current_shortcut": (
                        {
                            "path": str(shortcut_path.relative_to(ROOT)),
                            "sha256": sha_path(shortcut_path),
                        }
                        if shortcut_path.is_file()
                        else None
                    ),
                },
                "targeted_probe": {
                    "difficulty": "medium",
                    "seed": base_seed,
                    "sample_indices": [0, 1],
                    "self_check": checks,
                    "shapes": [[len(grid), len(grid[0])] for grid in grids],
                    "palettes": [sorted({cell for row in grid for cell in row}) for grid in grids],
                    "input_sha256": [grid_sha(grid) for grid in grids],
                    "output_sha256": [grid_sha(output) for output in outputs],
                    "changed_cells": [
                        sum(a != b for in_row, out_row in zip(grid, output, strict=True) for a, b in zip(in_row, out_row, strict=True))
                        for grid, output in zip(grids, outputs, strict=True)
                    ],
                    "racket_label_seconds": [round(value, 4) for value in timings],
                    "public_shape": {"demonstrations": 1, "queries": 1, "query_answers_excluded": True},
                    "public_bytes": len(visible),
                    "public_id": public_id,
                },
            }
        )

assert len(public_ids) == len(set(public_ids))

sample_observations = {
    "27a915a2c9b3": (
        "Current hash is bound, but the record is coverage-only and not approved; it has no current parametric/four-query manifest. "
        "Its historical derived catalog describes v2.0.0 while source is v4.0.0, so old lint/diversity fields are not current quality evidence."
    ),
    "1856980929fe": (
        "Approved unfinished original with strong repair notes but no current parametric/four-query manifest. "
        "An unresolved source-bound audit retains a five-demo/one-query lesson where an at-most-two-seeds rival survives the demonstrations."
    ),
    "28c998e193d9": (
        "Approved bank-derived coverage record with targeted morphology and no current parametric/four-query manifest. "
        "Its open audit reports no defect after 270 Racket-labelled pairs and 270 query rotations, so triage state and evidence content must be read separately."
    ),
}

base_labels = 10 * 7
paired_variant_labels = 3 * 7
alternative = {
    "kind": "shadow experiment only; preserve current production draw, 10% evaluation focus, approvals, and training boundaries",
    "records": 10,
    "strata": [
        {"count": 1, "stratum": "public-evaluation focus", "reason": "preserves the existing 10% authoring focus"},
        {"count": 4, "stratum": "unfinished approved originals lacking current parameter/four-query evidence", "reason": "high expected teachability gain per source review"},
        {"count": 2, "stratum": "coverage records, source-stratified internal versus bank/external", "reason": "measure source-specific quality rather than infer from provenance"},
        {"count": 2, "stratum": "current open-audit records", "reason": "measure repair/ambiguity cost and avoid silently treating triage as quality"},
        {"count": 1, "stratum": "recent return", "reason": "retain feedback-loop coverage"},
    ],
    "per_record_gate": [
        "Static source-hash, approval, review-index, derived-metric freshness, and existing-evidence screen; zero Racket labels.",
        "For records passing the static screen, retain one 3-demo + 4-distinct-query episode and execute all seven labels in canonical Racket.",
        "Use exact public_challenge_bytes/public_challenge_id and reject duplicate visible challenges before counting a success.",
        "Only the top three unambiguous records receive one paired parameter setting, adding seven labels each; proposals remain non-production.",
    ],
    "label_estimate": {
        "base": base_labels,
        "paired_parameter_top_three": paired_variant_labels,
        "maximum": base_labels + paired_variant_labels,
        "basis": "7 labels = 3 demonstrations + 4 distinct queries per setting; one extra setting for at most three records.",
    },
    "metrics": [
        "source-current, duplicate-free episodes per reviewer minute",
        "rival-refuting distinct query labels per Racket second",
        "fraction with current parameter evidence and four-query supervision",
        "unresolved-audit and stale-derived-metric rates by stratum/source",
    ],
    "stopping_rule": (
        "Stop at ten records. Do not scale the alternative if fewer than 7/10 records yield source-current, duplicate-free, "
        "Racket-verified four-query episodes; if any stratum has zero successes; or if more than 2/10 labels are ambiguous/unverified. "
        "Stop a stratum early after two consecutive source/evidence freshness failures. No audit is auto-cleared."
    ),
    "coverage_gaps": [
        "This packet exposes no source string explicitly labeled ARC-GEN or RE-ARC, so the three-record sample cannot compare those sources.",
        "Three sampled records cannot estimate corpus-wide quality or model loss; high loss is not treated as a defect.",
        "Historical derived catalog metrics are stale for all three sampled current versions.",
        "The targeted probe measures one demo and one query per record for labeling/dedup cost, not full four-query teachability.",
    ],
}

result = {
    "schema": "arcpuzzles-allocation-quality-ticket-v1",
    "ticket_id": TICKET_ID,
    "status": "completed",
    "ticket_seed": TICKET_SEED,
    "sampling_method": "random.Random(int(ticket_seed, 16)).sample(sorted(PACKET_MANIFEST.all_ids), 3)",
    "sampled_ids": sampled_ids,
    "ticket_anchor": {
        "task_id": ANCHOR_ID,
        "source_path": str(anchor_path.relative_to(ROOT)),
        "source_sha256": sha_path(anchor_path),
        "pinned_hash_matches": True,
        "note": "Anchor identity verified separately; the seeded three-record sample is not forced to include it.",
    },
    "dated_context": {
        "path": "TRAINING-CONTEXT.md",
        "sha256": sha_path(PACKET_ROOT / "TRAINING-CONTEXT.md"),
        "scope": "Dated owner context, not a live benchmark or source of current per-record approval.",
    },
    "packet": packet_summary,
    "records": records,
    "sample_observations": sample_observations,
    "probe_cost": {
        "racket_labels": len(racket_label_seconds),
        "racket_seconds": round(sum(racket_label_seconds), 4),
        "mean_racket_seconds_per_label": round(sum(racket_label_seconds) / len(racket_label_seconds), 4),
        "public_challenges": len(public_ids),
        "unique_public_ids": len(set(public_ids)),
        "probe_scope": "Two generated inputs and two canonical labels per sampled record; one visible demo plus one hidden-answer query per public challenge.",
    },
    "alternative_allocation": alternative,
    "conclusion": (
        "The sampled records support spending a bounded shadow allocation on evidence freshness and four-query teachability rather than increasing raw volume. "
        "Current packet selection intentionally emphasizes unfinished approved originals, while mix weights serve export sampling and do not certify quality. "
        "All three sampled records lack current parametric manifests; two retain open audits with materially different content, and all three historical derived catalog rows lag current source versions."
    ),
    "elapsed_seconds": round(time.monotonic() - started, 3),
}

output = HERE.with_name("result.json")
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "sampled_ids": sampled_ids,
    "racket_labels": result["probe_cost"]["racket_labels"],
    "racket_seconds": result["probe_cost"]["racket_seconds"],
    "public_ids_unique": result["probe_cost"]["unique_public_ids"],
    "elapsed_seconds": result["elapsed_seconds"],
}, indent=2, sort_keys=True))

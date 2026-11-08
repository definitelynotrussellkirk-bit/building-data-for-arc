#!/usr/bin/env python3
"""Source-bound lesson probe for ``a6211f2301a7``.

The exact selected generator supplies inputs, validators, and rival/witness
predictions. Correct labels come only from public ``Catalog.apply`` canonical
Racket execution. To keep a 300-lesson audit practical, the probe labels the
minimum declared witness subset needed to test every rival in every lesson;
it still measures all generated inputs for uniqueness and distribution.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "a6211f2301a7"
BANDS = ("easy", "medium", "hard")
STARTS = (0, 1)
RIVAL_REGISTRIES = ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")
CANONICAL_PROFILES = {
    (8, 9, 4), (9, 8, 4), (7, 10, 2), (8, 8, 3), (9, 9, 4)
}


def json_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_grid(value: Any) -> list[list[int]]:
    if isinstance(value, list) and value and all(isinstance(row, str) for row in value):
        value = [[int(cell) for cell in row] for row in value]
    if (
        not isinstance(value, list) or not value
        or any(not isinstance(row, list) or not row for row in value)
        or any(len(row) != len(value[0]) for row in value)
        or any(type(cell) is not int or not 0 <= cell <= 9 for row in value for cell in row)
    ):
        raise ValueError("expected a nonempty rectangular integer-colour grid")
    return [list(row) for row in value]


def load_generator(root: Path):
    runtime = root / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    path = root / "generators" / TASK_ID / "generator.py"
    name = f"{TASK_ID}_distribution_probe_generator"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module, path


def canonical_pairs(catalog) -> list[dict[str, list[list[int]]]]:
    record = catalog.get(TASK_ID)
    pairs = []
    for variant in record.get("variants", []):
        for field in ("train", "test"):
            raw = variant.get(field)
            rows = raw if isinstance(raw, list) else [raw] if isinstance(raw, dict) else []
            for pair in rows:
                if isinstance(pair, dict) and "input" in pair and "output" in pair:
                    pairs.append({
                        "input": normalize_grid(pair["input"]),
                        "output": normalize_grid(pair["output"]),
                    })
    if not pairs:
        raise ValueError("canonical record has no usable input/output pairs")
    return pairs


def declared_contract(module):
    rivals: dict[str, Any] = {}
    rival_sources: dict[str, list[str]] = {}
    for registry_name in RIVAL_REGISTRIES:
        registry = getattr(module, registry_name, None)
        if not isinstance(registry, dict) or not registry:
            raise ValueError(f"{registry_name} must be a nonempty mapping")
        for name, function in registry.items():
            if not isinstance(name, str) or not callable(function):
                raise ValueError(f"{registry_name} has a non-callable entry")
            if name in rivals and rivals[name] is not function:
                raise ValueError(f"rival {name!r} maps to different callables")
            rivals[name] = function
            rival_sources.setdefault(name, []).append(registry_name)

    witnesses = getattr(module, "SEMANTIC_WITNESSES", None)
    links = getattr(module, "WITNESS_RIVALS", None)
    if not isinstance(witnesses, dict) or not witnesses:
        raise ValueError("SEMANTIC_WITNESSES must be a nonempty mapping")
    if any(not isinstance(name, str) or not callable(fn) for name, fn in witnesses.items()):
        raise ValueError("SEMANTIC_WITNESSES has a non-callable entry")
    if not isinstance(links, dict):
        raise ValueError("WITNESS_RIVALS must be a mapping")

    linked: dict[str, list[str]] = {name: [] for name in rivals}
    for witness_name, rival_names in links.items():
        if witness_name not in witnesses or not isinstance(rival_names, list):
            raise ValueError(f"invalid witness link for {witness_name!r}")
        for rival_name in rival_names:
            if rival_name in linked:
                linked[rival_name].append(witness_name)
    return rivals, rival_sources, witnesses, linked


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({cell for row in grid for cell in row})


def run_probe(options: argparse.Namespace) -> dict[str, Any]:
    from arcpuzzles import Catalog

    root = options.library.resolve()
    module, source = load_generator(root)
    generator_hash = file_hash(source)
    probe_path = Path(__file__).resolve()
    catalog = Catalog(root)
    metadata = catalog.describe(TASK_ID)
    if metadata["generator_sha256"] != generator_hash:
        raise RuntimeError("catalog generator hash does not match selected source bytes")

    rivals, rival_sources, witnesses, linked_witnesses = declared_contract(module)
    canonical = canonical_pairs(catalog)
    canonical_results = {}
    for name, rival in rivals.items():
        matches = [rival(pair["input"]) == pair["output"] for pair in canonical]
        canonical_results[name] = {
            "source_registries": rival_sources[name],
            "linked_witnesses": linked_witnesses[name],
            "usable_pairs": len(matches),
            "matching_pairs": sum(matches),
            "fits_all_usable_pairs": all(matches),
        }

    report: dict[str, Any] = {
        "schema": "a6211f2301a7-distribution-probe-v2",
        "task_id": TASK_ID,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_identity": {
            "generator_path": str(source.relative_to(root)),
            "generator_version": getattr(module, "VERSION", None),
            "generator_sha256_start": generator_hash,
            "probe_path": str(probe_path.relative_to(root)),
            "probe_sha256": file_hash(probe_path),
            "catalog_rule_hash": metadata.get("rule_hash"),
            "canonical_ledger_sha256": file_hash(root / "shared/data/canonical/puzzles.jsonl"),
        },
        "parameters": {
            "bands": list(options.bands),
            "curriculum_starts": list(STARTS),
            "lessons_per_start": options.lessons_per_start,
            "lessons_per_band": options.lessons_per_start * len(STARTS),
            "generated_inputs_per_lesson": 4,
            "demonstrations_per_lesson": 3,
            "queries_per_lesson": 1,
            "base_seed": options.seed,
            "max_apply_batch": 64,
            "timeout_seconds_per_apply_batch": options.timeout,
        },
        "sampler": {
            "input_route": "direct exact selected generator.generate",
            "label_route": "public Catalog.apply with canonical Racket reference",
            "policy": (
                "For each band and curriculum start 0 or 1, use an independent seed per "
                "lesson and direct sample indices start..start+3. Measure all four inputs. "
                "For each declared rival, choose the first training input satisfying a linked "
                "declared witness; if no linked witness is available, label all three demos. "
                "Label the union through Catalog.apply in batches of at most 64."
            ),
            "label_scope": (
                "Every lesson/rival claim is backed by at least one source-bound demonstration "
                "label. Unlabeled generated inputs contribute only distribution and uniqueness "
                "measurements, never correctness claims."
            ),
            "domain_limits": (
                "Unforced default draws only: 7..13 padded grids, 2..4 tight boxes, 3..8 "
                "foreground cells, 1..3 colours and 1..3 components. This finite audit does "
                "not cover arbitrary grids, explicit overrides, reordered lessons, fewer than "
                "three demonstrations, or undeclared rivals, and is not universal induction."
            ),
        },
        "canonical_rivals": canonical_results,
        "reference_receipts": [],
        "bands": {},
        "failures": [],
    }

    records: list[dict[str, Any]] = []
    lessons_by_band: dict[str, list[dict[str, Any]]] = {band: [] for band in options.bands}
    label_indices: set[int] = set()

    for band_index, band in enumerate(options.bands):
        for start in STARTS:
            seed_start = options.seed + band_index * 100000 + start * 10000
            for lesson_offset in range(options.lessons_per_start):
                seed = seed_start + lesson_offset
                indices = []
                for position, sample_index in enumerate(range(start, start + 4)):
                    grid = normalize_grid(module.generate(seed, sample_index, difficulty=band))
                    findings = module.self_check(grid)
                    if findings:
                        report["failures"].append({
                            "category": "generated_input_failed_self_check",
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "findings": findings,
                        })
                    row = {
                        "band": band,
                        "curriculum_start": start,
                        "seed": seed,
                        "sample_index": sample_index,
                        "position": position,
                        "grid": grid,
                        "input_sha256": json_hash(grid),
                        "observed": module.observe_overrides(grid),
                    }
                    indices.append(len(records))
                    records.append(row)

                rival_candidates: dict[str, list[int]] = {}
                train_indices = indices[:3]
                for rival_name in rivals:
                    linked = linked_witnesses[rival_name]
                    matching = [
                        index for index in train_indices
                        if any(witnesses[witness](records[index]["grid"]) for witness in linked)
                    ]
                    chosen = matching[:1] if matching else list(train_indices)
                    rival_candidates[rival_name] = chosen
                    label_indices.update(chosen)
                lessons_by_band[band].append({
                    "seed": seed,
                    "curriculum_start": start,
                    "record_indices": indices,
                    "rival_label_indices": rival_candidates,
                })

    # Publicly label only the witness subset that backs lesson-level rival claims.
    ordered_label_indices = sorted(label_indices)
    for offset in range(0, len(ordered_label_indices), 64):
        batch_indices = ordered_label_indices[offset:offset + 64]
        batch = [records[index] for index in batch_indices]
        applied = catalog.apply(
            TASK_ID,
            [row["grid"] for row in batch],
            reference="canonical",
            allow_unapproved=True,
            timeout=options.timeout,
        )
        if len(applied["results"]) != len(batch):
            raise RuntimeError("Catalog.apply returned an incomplete batch")
        if applied.get("generator_sha256") != generator_hash:
            report["failures"].append({
                "category": "apply_generator_hash_mismatch",
                "batch_offset": offset,
                "actual": applied.get("generator_sha256"),
                "expected": generator_hash,
            })
        if not applied.get("rule_hash_matches_catalog"):
            report["failures"].append({
                "category": "apply_rule_hash_mismatch",
                "batch_offset": offset,
                "executed": applied.get("executed_rule_hash"),
                "catalog": applied.get("catalog_rule_hash"),
            })
        error_count = 0
        for index, item in zip(batch_indices, applied["results"], strict=True):
            if item.get("error") is not None or item.get("output") is None:
                error_count += 1
                row = records[index]
                report["failures"].append({
                    "category": "reference_execution_error",
                    "band": row["band"],
                    "seed": row["seed"],
                    "sample_index": row["sample_index"],
                    "error": item.get("error"),
                })
                continue
            records[index]["reference_output"] = normalize_grid(item["output"])
            records[index]["reference_output_sha256"] = (
                item.get("output_sha256") or json_hash(item["output"])
            )
        report["reference_receipts"].append({
            "label_batch_offset": offset,
            "count": len(batch),
            "generator_sha256": applied.get("generator_sha256"),
            "executed_rule_hash": applied.get("executed_rule_hash"),
            "catalog_rule_hash": applied.get("catalog_rule_hash"),
            "rule_hash_matches_catalog": applied.get("rule_hash_matches_catalog"),
            "rule_text_sha256": applied.get("rule_text_sha256"),
            "elapsed_seconds": applied.get("elapsed_seconds"),
            "error_count": error_count,
            "input_sha256": [row["input_sha256"] for row in batch],
            "output_sha256": [records[index].get("reference_output_sha256") for index in batch_indices],
        })

    expected_lessons = options.lessons_per_start * len(STARTS)
    for band in options.bands:
        unique_inputs: set[str] = set()
        orientation_counts: Counter[str] = Counter()
        component_counts: Counter[str] = Counter()
        profile_counts: Counter[tuple[int, int, int]] = Counter()
        lesson_rows = []
        first_disagreement: dict[str, Any] = {}

        for lesson in lessons_by_band[band]:
            current = [records[index] for index in lesson["record_indices"]]
            for row in current:
                unique_inputs.add(row["input_sha256"])
                orientation_counts[row["observed"]["bbox_orientation"]] += 1
                component_counts[str(row["observed"]["component_count"])] += 1
                profile_counts[profile(row["grid"])] += 1

            rival_rows = {}
            for rival_name, rival in rivals.items():
                candidates = [records[index] for index in lesson["rival_label_indices"][rival_name]]
                if any("reference_output" not in row for row in candidates):
                    report["failures"].append({
                        "category": "missing_source_bound_witness_label",
                        "band": band,
                        "seed": lesson["seed"],
                        "rival": rival_name,
                    })
                    disagreements = []
                else:
                    disagreements = [
                        row for row in candidates
                        if rival(row["grid"]) != row["reference_output"]
                    ]
                refuted = bool(disagreements)
                rival_rows[rival_name] = {
                    "candidate_sample_indices": [row["sample_index"] for row in candidates],
                    "source_bound_candidate_count": len(candidates),
                    "source_bound_disagreement_count": len(disagreements),
                    "refuted_by_demonstrations": refuted,
                }
                if disagreements and rival_name not in first_disagreement:
                    row = disagreements[0]
                    predicted = rival(row["grid"])
                    first_disagreement[rival_name] = {
                        "band": band,
                        "seed": row["seed"],
                        "sample_index": row["sample_index"],
                        "input": row["grid"],
                        "reference_output": row["reference_output"],
                        "rival_output": predicted,
                        "input_sha256": row["input_sha256"],
                        "reference_output_sha256": row["reference_output_sha256"],
                        "rival_output_sha256": json_hash(predicted),
                    }
            lesson_rows.append({
                "seed": lesson["seed"],
                "curriculum_start": lesson["curriculum_start"],
                "sample_indices": [row["sample_index"] for row in current],
                "input_sha256": [row["input_sha256"] for row in current],
                "train_orientations": [row["observed"]["bbox_orientation"] for row in current[:3]],
                "rivals": rival_rows,
            })

        rival_summary = {}
        for rival_name in rivals:
            refuted = sum(
                lesson["rivals"][rival_name]["refuted_by_demonstrations"]
                for lesson in lesson_rows
            )
            candidate_count = sum(
                lesson["rivals"][rival_name]["source_bound_candidate_count"]
                for lesson in lesson_rows
            )
            disagreement_count = sum(
                lesson["rivals"][rival_name]["source_bound_disagreement_count"]
                for lesson in lesson_rows
            )
            rival_summary[rival_name] = {
                "lessons_refuted_by_demonstrations": refuted,
                "lesson_denominator": len(lesson_rows),
                "source_bound_candidate_labels": candidate_count,
                "source_bound_disagreements": disagreement_count,
                "first_disagreement": first_disagreement.get(rival_name),
            }
            if refuted != expected_lessons:
                report["failures"].append({
                    "category": "lesson_does_not_refute_declared_rival",
                    "band": band,
                    "rival": rival_name,
                    "refuted": refuted,
                    "denominator": expected_lessons,
                })

        report["bands"][band] = {
            "completed_lessons": len(lesson_rows),
            "expected_lessons": expected_lessons,
            "generated_input_occurrences": len(lesson_rows) * 4,
            "unique_input_hashes": len(unique_inputs),
            "source_bound_labeled_input_occurrences": len({
                index for lesson in lessons_by_band[band]
                for indices in lesson["rival_label_indices"].values() for index in indices
            }),
            "bbox_orientation_occurrences": dict(sorted(orientation_counts.items())),
            "component_count_occurrences": dict(sorted(component_counts.items())),
            "canonical_profile_occurrences": sum(
                count for key, count in profile_counts.items() if key in CANONICAL_PROFILES
            ),
            "canonical_profile_denominator": len(lesson_rows) * 4,
            "rivals": rival_summary,
            "lessons": lesson_rows,
        }
        if len(lesson_rows) != expected_lessons:
            report["failures"].append({
                "category": "band_lesson_denominator",
                "band": band,
                "expected": expected_lessons,
                "actual": len(lesson_rows),
            })

    for rival_name, row in canonical_results.items():
        if not row["fits_all_usable_pairs"]:
            report["failures"].append({
                "category": "declared_rival_does_not_fit_canonical",
                "rival": rival_name,
                **row,
            })

    final_hash = file_hash(source)
    report["source_identity"]["generator_sha256_final"] = final_hash
    report["source_identity"]["source_unchanged"] = final_hash == generator_hash
    if final_hash != generator_hash:
        report["failures"].append({
            "category": "source_changed_during_probe",
            "start": generator_hash,
            "final": final_hash,
        })
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    report["passed"] = not report["failures"]
    report["failure_count"] = len(report["failures"])
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--library", type=Path, default=Path(__file__).resolve().parents[3],
        help="ARCpuzzles repository root",
    )
    parser.add_argument(
        "--lessons-per-start", type=int, default=50,
        help="episodes for starts 0 and 1; default gives 100 lessons per band",
    )
    parser.add_argument("--seed", type=int, default=271828)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--bands", nargs="+", choices=BANDS, default=list(BANDS))
    return parser


def main(argv: list[str] | None = None) -> int:
    options = build_parser().parse_args(argv)
    if options.lessons_per_start < 1:
        raise SystemExit("--lessons-per-start must be positive")
    report = run_probe(options)
    options.out.parent.mkdir(parents=True, exist_ok=True)
    options.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    summary = {
        "passed": report["passed"],
        "failure_count": report["failure_count"],
        "generator_sha256": report["source_identity"]["generator_sha256_final"],
        "bands": {
            band: {
                "lessons": row["completed_lessons"],
                "unique_inputs": row["unique_input_hashes"],
                "source_bound_labels": row["source_bound_labeled_input_occurrences"],
                "rival_refutation": {
                    name: f"{value['lessons_refuted_by_demonstrations']}/{value['lesson_denominator']}"
                    for name, value in row["rivals"].items()
                },
            }
            for band, row in report["bands"].items()
        },
        "report": str(options.out),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

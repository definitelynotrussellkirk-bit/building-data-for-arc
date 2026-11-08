from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

REPO = Path.cwd()
OUT_ROOT = REPO.parent / "checks" / "audit"


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path, hashlib.sha256(path.read_bytes()).hexdigest()


def grid_hash(grid: Any) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def save(task_id: str, payload: dict[str, Any]) -> None:
    out = OUT_ROOT / task_id / "probe.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(out)


def audit_d2() -> None:
    task = "d2f8cb1c91b2"
    gen, path, source_sha = load(task)
    generated = 0
    branch_failures = []
    control_failures = []
    for band in ("easy", "medium", "hard"):
        for transform in gen.GENERATED_TRANSFORMS:
            for palette_size in (3, 4):
                grid = gen.generate(
                    20261020,
                    generated,
                    difficulty=band,
                    transform=transform,
                    palette_size=palette_size,
                )
                generated += 1
                errors = gen.self_check(grid)
                observed = gen.observe_overrides(grid) if not errors else None
                analysis_errors, analysis = gen._analyze_grid(grid)
                if errors or observed != {"transform": transform, "palette_size": palette_size}:
                    control_failures.append(
                        {
                            "band": band,
                            "transform": transform,
                            "palette_size": palette_size,
                            "errors": errors,
                            "observed": observed,
                        }
                    )
                if analysis_errors or analysis is None or any(
                    analysis["stats"].get(name, 0) < 1
                    for name in ("x_only", "y_only", "match", "conflict", "both_zero")
                ):
                    branch_failures.append(
                        {
                            "band": band,
                            "transform": transform,
                            "palette_size": palette_size,
                            "analysis_errors": analysis_errors,
                            "stats": None if analysis is None else analysis["stats"],
                        }
                    )

    rotation_failures = []
    rotations_checked = 0
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(99173, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": gen.reference_output(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                rotations_checked += 1
                if reasons:
                    rotation_failures.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                        }
                    )

    save(
        task,
        {
            "task_id": task,
            "source": str(path.relative_to(REPO)),
            "source_sha256": source_sha,
            "status": "no_issue_found" if not (control_failures or branch_failures or rotation_failures) else "finding",
            "generated_control_cases": generated,
            "control_failures": control_failures,
            "branch_failures": branch_failures,
            "rotations_checked": rotations_checked,
            "rotation_failures": rotation_failures,
            "scope": "All transform/palette override combinations in all bands plus every query rotation for 12 consecutive four-pair windows per band.",
        },
    )


def marked_and_stray_counts(gen, grid):
    reds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    components = gen._blue_components(grid)
    if len(reds) != 1:
        return None, len(components)
    marker = reds[0]
    adjacent = {
        (marker[0] + dr, marker[1] + dc)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
    }
    marked_index = next(
        (i for i, cells in enumerate(components) if adjacent.intersection(cells)),
        None,
    )
    return marked_index, len(components) - (1 if marked_index is not None else 0)


def audit_66() -> None:
    task = "66ba1145a9b7"
    gen, path, source_sha = load(task)
    seed, sample_index, band = 7171, 9, "medium"
    base = gen.generate(seed, sample_index, difficulty=band)
    palette_variants = {
        value: grid_hash(gen.generate(seed, sample_index, difficulty=band, palette_kind=value))
        for value in gen.PALETTE_KINDS
    }
    texture_variants = {
        value: grid_hash(gen.generate(seed, sample_index, difficulty=band, texture=value))
        for value in gen.HELPFUL_TEXTURES
    }

    override_errors = {}
    for name, value in (("grid_h", 5), ("grid_w", 6), ("stray_count", 4)):
        try:
            gen.generate(seed, sample_index, difficulty="easy", **{name: value})
        except Exception as exc:  # exact evidence for advertised values
            override_errors[name] = {"value": value, "type": type(exc).__name__, "message": str(exc)}
        else:
            override_errors[name] = {"value": value, "type": None, "message": None}

    foreign = [list(row) for row in base]
    foreign_cell = next(
        (r, c)
        for r, row in enumerate(foreign)
        for c, value in enumerate(row)
        if value == 0
    )
    foreign[foreign_cell[0]][foreign_cell[1]] = 9
    foreign_errors = gen.self_check(foreign)

    max_strays = -1
    first_out_of_contract = None
    sampled = 0
    for probe_seed in range(40):
        for index in range(20):
            grid = gen.generate(probe_seed, index, difficulty="hard")
            _, strays = marked_and_stray_counts(gen, grid)
            sampled += 1
            max_strays = max(max_strays, strays)
            if strays > 4 and first_out_of_contract is None:
                first_out_of_contract = {
                    "seed": probe_seed,
                    "sample_index": index,
                    "difficulty": "hard",
                    "observed_stray_components": strays,
                    "input_sha256": grid_hash(grid),
                    "self_check": gen.self_check(grid),
                    "grid": grid,
                }

    payload = {
        "task_id": task,
        "source": str(path.relative_to(REPO)),
        "source_sha256": source_sha,
        "status": "reproduced_generator_contract_defects",
        "ignored_palette_kind": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": band,
            "hashes": palette_variants,
            "distinct_hashes": len(set(palette_variants.values())),
        },
        "ignored_helpful_texture_alias": {
            "hashes": texture_variants,
            "distinct_hashes": len(set(texture_variants.values())),
        },
        "advertised_values_rejected_in_easy": override_errors,
        "validator_accepts_foreign_color": {
            "mutated_cell": list(foreign_cell),
            "inserted_color": 9,
            "self_check": foreign_errors,
            "input_sha256": grid_hash(foreign),
            "grid": foreign,
        },
        "default_stray_count_census": {
            "draws": sampled,
            "advertised_max": 4,
            "observed_max": max_strays,
            "first_out_of_contract": first_out_of_contract,
        },
        "scope": "Exact override comparisons, one validator mutation, and 800 hard-band default draws; audited source was not modified.",
    }
    save(task, payload)


audit_d2()
audit_66()

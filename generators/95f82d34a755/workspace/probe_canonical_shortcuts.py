"""Racket-backed probe for canonical-fitting shortcut rules.

Run this authoring tool from ``WORK/repo`` through the packet wrapper::

    python3 review.py run python3 \
      generators/95f82d34a755/workspace/probe_canonical_shortcuts.py \
      --out ../checks/canonical-shortcut-probe

The probe reads the generator's declared ``CANONICAL_SHORTCUTS`` rather than
copying rival implementations.  It proves that each rival fits every usable
canonical pair, applies the canonical Racket rule to all cases needed for a
sliding-window and leave-one-out rotation audits, and retains one exact disagreement witness.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable


TASK_ID = "95f82d34a755"
DEFAULT_DIFFICULTIES: tuple[str | None, ...] = (None, "easy", "medium", "hard")


def cell_differences(
    intended: list[list[int]], rival: list[list[int]]
) -> list[dict[str, Any]]:
    """Return deterministic row-major differences, including shape mismatch."""
    differences: list[dict[str, Any]] = []
    max_rows = max(len(intended), len(rival))
    for row in range(max_rows):
        intended_row = intended[row] if row < len(intended) else []
        rival_row = rival[row] if row < len(rival) else []
        max_columns = max(len(intended_row), len(rival_row))
        for column in range(max_columns):
            intended_value = intended_row[column] if column < len(intended_row) else None
            rival_value = rival_row[column] if column < len(rival_row) else None
            if intended_value != rival_value:
                differences.append(
                    {
                        "row": row,
                        "column": column,
                        "intended": intended_value,
                        "rival": rival_value,
                    }
                )
    return differences


def scheduled_cases(
    *,
    seed: int,
    starts: int,
    window: int,
    difficulties: Iterable[str | None] = DEFAULT_DIFFICULTIES,
) -> list[dict[str, Any]]:
    """Describe the minimum draws covering ``starts`` sliding windows."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(starts) is not int or starts <= 0:
        raise ValueError("starts must be a positive integer")
    if type(window) is not int or window <= 0:
        raise ValueError("window must be a positive integer")
    return [
        {"seed": seed, "difficulty": difficulty, "sample_index": sample_index}
        for difficulty in difficulties
        for sample_index in range(starts + window - 1)
    ]


def _load_environment() -> tuple[Path, Any, Any, Any]:
    try:
        from reviewer_support import canonical_pairs, find_root
    except ModuleNotFoundError as exc:
        if exc.name != "reviewer_support":
            raise
        for ancestor in Path(__file__).resolve().parents:
            runtime = ancestor / "shared" / "runtime"
            if (runtime / "reviewer_support.py").is_file():
                sys.path.insert(0, str(runtime))
                break
        else:
            raise
        from reviewer_support import canonical_pairs, find_root

    root = find_root(__file__)
    try:
        from arcpuzzles import Catalog
    except ModuleNotFoundError as exc:
        if exc.name != "arcpuzzles":
            raise
        sys.path.insert(0, str(root / "src"))
        from arcpuzzles import Catalog

    source = root / "generators" / TASK_ID / "generator.py"
    raw = source.read_bytes()
    spec = importlib.util.spec_from_file_location(
        f"canonical_shortcut_probe_{TASK_ID}", source
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {source}")
    generator = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(source), "exec"), generator.__dict__)
    return root, Catalog(root), canonical_pairs, generator


def _difficulty_key(difficulty: str | None) -> str:
    return "default" if difficulty is None else difficulty


def _case_key(difficulty: str | None, sample_index: int) -> tuple[str | None, int]:
    return difficulty, sample_index


def _window_summaries(
    checked_by_key: dict[tuple[str | None, int], dict[str, Any]],
    shortcut_names: list[str],
    *,
    starts: int,
    window: int,
    difficulties: Iterable[str | None],
) -> list[dict[str, Any]]:
    summaries = []
    for difficulty in difficulties:
        for start in range(starts):
            cases = [checked_by_key[_case_key(difficulty, start + offset)] for offset in range(window)]
            refuted = {
                name: any(not case["shortcuts"][name]["matches_reference"] for case in cases)
                for name in shortcut_names
            }
            summaries.append(
                {
                    "difficulty": _difficulty_key(difficulty),
                    "start": start,
                    "sample_indices": [case["sample_index"] for case in cases],
                    "profiles": [case["scene_profile"] for case in cases],
                    "shapes": [case["shape"] for case in cases],
                    "contains_extended_multi_shared_anchor": any(
                        case["shape"] == [8, 9]
                        and case["scene_profile"] == "multi_shared"
                        for case in cases
                    ),
                    "shortcut_refuted": refuted,
                    "all_reference_outputs_match_mirror": all(
                        case["reference_matches_mirror"] for case in cases
                    ),
                }
            )
    return summaries


def rotation_summaries(
    checked_by_key: dict[tuple[str | None, int], dict[str, Any]],
    shortcut_names: list[str],
    *,
    starts: int,
    window: int,
    difficulties: Iterable[str | None],
) -> list[dict[str, Any]]:
    """Audit every query choice in ``window + 1`` consecutive items."""
    summaries: list[dict[str, Any]] = []
    for difficulty in difficulties:
        for start in range(starts):
            lesson = [
                checked_by_key[_case_key(difficulty, start + offset)]
                for offset in range(window + 1)
            ]
            for query_offset, query in enumerate(lesson):
                demos = [case for offset, case in enumerate(lesson) if offset != query_offset]
                refuted = {
                    name: any(
                        not case["shortcuts"][name]["matches_reference"]
                        for case in demos
                    )
                    for name in shortcut_names
                }
                summaries.append(
                    {
                        "difficulty": _difficulty_key(difficulty),
                        "start": start,
                        "query_offset": query_offset,
                        "query_sample_index": query["sample_index"],
                        "demo_sample_indices": [case["sample_index"] for case in demos],
                        "shortcut_refuted": refuted,
                    }
                )
    return summaries


def run_probe(
    *,
    output: Path,
    seed: int,
    starts: int,
    timeout: int,
    difficulties: tuple[str | None, ...] = DEFAULT_DIFFICULTIES,
) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    root, catalog, canonical_pairs, generator = _load_environment()
    source = root / "generators" / TASK_ID / "generator.py"
    raw = source.read_bytes()
    script_raw = Path(__file__).read_bytes()

    shortcuts = dict(getattr(generator, "CANONICAL_SHORTCUTS", {}))
    if not shortcuts:
        raise RuntimeError("generator declares no CANONICAL_SHORTCUTS")
    shortcut_names = sorted(shortcuts)

    canonical = canonical_pairs(TASK_ID, root=root)
    canonical_fit = {
        name: [shortcut(pair["input"]) == pair["output"] for pair in canonical]
        for name, shortcut in shortcuts.items()
    }

    window = int(generator.EXAMPLES_NEEDED)
    # One extra sliding start supplies the sixth item needed to rotate every
    # query position while retaining five demonstrations.
    descriptors = scheduled_cases(
        seed=seed,
        starts=starts + 1,
        window=window,
        difficulties=difficulties,
    )
    generated = []
    for descriptor in descriptors:
        grid = generator.generate(
            descriptor["seed"],
            descriptor["sample_index"],
            difficulty=descriptor["difficulty"],
        )
        generated.append({**descriptor, "input": grid})

    receipt = catalog.apply(
        TASK_ID,
        [case["input"] for case in generated],
        reference="canonical",
        allow_unapproved=True,
        timeout=timeout,
    )
    (output / "racket.json").write_text(json.dumps(receipt, indent=2) + "\n")

    if len(receipt.get("results", [])) != len(generated):
        raise RuntimeError(
            f"reference returned {len(receipt.get('results', []))} results "
            f"for {len(generated)} inputs"
        )

    checked_cases: list[dict[str, Any]] = []
    checked_by_key: dict[tuple[str | None, int], dict[str, Any]] = {}
    for case, reference_result in zip(generated, receipt["results"], strict=True):
        grid = case["input"]
        intended = reference_result.get("output")
        mirror = generator.rule_mirror(grid)
        reference_error = reference_result.get("error")
        shortcut_checks = {}
        for name, shortcut in shortcuts.items():
            prediction = shortcut(grid)
            differences = (
                cell_differences(intended, prediction) if intended is not None else []
            )
            shortcut_checks[name] = {
                "matches_reference": intended is not None and not differences,
                "difference_count": len(differences),
                "first_differences": differences[:12],
            }
        facts = generator.observe_overrides(grid)
        checked = {
            "difficulty": _difficulty_key(case["difficulty"]),
            "sample_index": case["sample_index"],
            "shape": [len(grid), len(grid[0])],
            "scene_profile": facts["scene_profile"],
            "palette_band": facts["palette_band"],
            "self_check": generator.self_check(grid),
            "reference_error": reference_error,
            "reference_matches_mirror": reference_error is None and intended == mirror,
            "shortcuts": shortcut_checks,
        }
        checked_cases.append(checked)
        checked_by_key[_case_key(case["difficulty"], case["sample_index"])] = checked

    windows = _window_summaries(
        checked_by_key,
        shortcut_names,
        starts=starts,
        window=window,
        difficulties=difficulties,
    )
    rotations = rotation_summaries(
        checked_by_key,
        shortcut_names,
        starts=starts,
        window=window,
        difficulties=difficulties,
    )

    witness_key = _case_key("easy", 3)
    witness_position = next(
        i
        for i, case in enumerate(generated)
        if _case_key(case["difficulty"], case["sample_index"]) == witness_key
    )
    witness_case = generated[witness_position]
    witness_reference = receipt["results"][witness_position]
    witness_intended = witness_reference["output"]
    witness_rivals = {}
    for name, shortcut in shortcuts.items():
        prediction = shortcut(witness_case["input"])
        witness_rivals[name] = {
            "output": prediction,
            "differences": cell_differences(witness_intended, prediction),
        }

    requirements = {
        "all_shortcuts_fit_all_canonical_pairs": bool(canonical)
        and all(all(values) for values in canonical_fit.values()),
        "all_generated_inputs_pass_self_check": all(
            not case["self_check"] for case in checked_cases
        ),
        "all_reference_outputs_match_python_mirror": all(
            case["reference_matches_mirror"] for case in checked_cases
        ),
        "every_window_contains_extended_multi_shared_anchor": all(
            window_summary["contains_extended_multi_shared_anchor"]
            for window_summary in windows
        ),
        "every_window_refutes_every_declared_shortcut": all(
            all(window_summary["shortcut_refuted"].values())
            for window_summary in windows
        ),
        "every_leave_one_out_rotation_refutes_every_declared_shortcut": all(
            all(rotation["shortcut_refuted"].values())
            for rotation in rotations
        ),
        "exact_witness_refutes_every_declared_shortcut": all(
            witness["differences"] for witness in witness_rivals.values()
        ),
    }

    source_hash = hashlib.sha256(raw).hexdigest()
    report = {
        "schema": "canonical_shortcut_probe/1",
        "task_id": TASK_ID,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cwd": str(Path.cwd()),
        "library_root": str(root),
        "argv": ["python3", *sys.argv],
        "generator_version": generator.VERSION,
        "generator_sha256": source_hash,
        "script_sha256": hashlib.sha256(script_raw).hexdigest(),
        "rule_hash": generator.RULE_HASH,
        "reference_generator_sha256": receipt.get("generator_sha256"),
        "source_matches_reference_receipt": receipt.get("generator_sha256")
        in (None, source_hash),
        "rule_hash_matches_catalog": receipt.get("rule_hash_matches_catalog"),
        "seed": seed,
        "starts_per_difficulty": starts,
        "window_size": window,
        "difficulty_bands": [_difficulty_key(value) for value in difficulties],
        "canonical_pair_count": len(canonical),
        "declared_shortcuts": shortcut_names,
        "canonical_fit": canonical_fit,
        "checked_case_count": len(checked_cases),
        "checked_cases": checked_cases,
        "window_count": len(windows),
        "windows": windows,
        "rotation_count": len(rotations),
        "rotations": rotations,
        "exact_witness": {
            "seed": witness_case["seed"],
            "sample_index": witness_case["sample_index"],
            "difficulty": _difficulty_key(witness_case["difficulty"]),
            "input": witness_case["input"],
            "reference_output": witness_intended,
            "reference_error": witness_reference.get("error"),
            "rivals": witness_rivals,
        },
        "requirements": requirements,
    }
    report["passed"] = all(requirements.values()) and report["source_matches_reference_receipt"]
    report["exit_code"] = 0 if report["passed"] else 1
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new report directory")
    parser.add_argument("--seed", type=int, default=20261012)
    parser.add_argument("--starts", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    report = run_probe(
        output=args.out.resolve(),
        seed=args.seed,
        starts=args.starts,
        timeout=args.timeout,
    )
    summary = {
        "task_id": report["task_id"],
        "generator_sha256": report["generator_sha256"],
        "canonical_pairs": report["canonical_pair_count"],
        "shortcuts": report["declared_shortcuts"],
        "checked_cases": report["checked_case_count"],
        "windows": report["window_count"],
        "rotations": report["rotation_count"],
        "requirements": report["requirements"],
        "passed": report["passed"],
        "report": str((args.out.resolve() / "report.json")),
    }
    print(json.dumps(summary, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())

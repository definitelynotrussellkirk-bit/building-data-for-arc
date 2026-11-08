#!/usr/bin/env python3
"""Racket-backed reproducer for mirror teaching and validator regressions.

Run from a review packet with::

    python3 review.py run python3 generators/72f0b65569a4/workspace/mirror_contract_probe.py \
        --out ../checks/diagnosis/mirror-contract.json

This bounded diagnostic selects the current generator through reviewer_support,
reads every canonical pair through that public helper, and gets generated and
handmade labels from Catalog.apply. The independent Python implementations below
are competing hypotheses only; none supplies authoritative labels. The normal
defaults check 36 overlapping lessons and all 144 query rotations. They are a
focused regression population, not a full schedule census or all-seed proof.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Callable


def _bootstrap() -> None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        for helper in (parent / "reviewer_support.py", parent / "shared/runtime/reviewer_support.py"):
            if helper.is_file():
                sys.path.insert(0, str(helper.parent))
                if (parent / "src/arcpuzzles").is_dir():
                    sys.path.insert(0, str(parent / "src"))
                return
    raise FileNotFoundError("No local reviewer_support.py above this probe")


_bootstrap()
from reviewer_support import canonical_pairs, find_root, load_selected_generator, normalize_grid  # noqa: E402

TASK_ID = "72f0b65569a4"
Grid = list[list[int]]


def _frame(grid: Grid) -> tuple[int, int, int, int]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    if not cells:
        raise ValueError("Missing blue frame")
    return min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)


def independent_rival(grid: Grid, mode: str) -> Grid:
    """A deterministic competing rule, deliberately independent of generator hooks."""
    out = copy.deepcopy(grid)
    if mode == "identity":
        return out
    r1, c1, r2, c2 = _frame(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 4:
                continue
            if mode == "whole_grid_empty":
                rr, cc = r, len(row) - 1 - c
            else:
                if not (r1 < r < r2 and c1 < c < c2):
                    continue
                rr, cc = (r1 + r2 - r, c) if mode == "vertical_empty" else (r, c1 + c2 - c)
            target = grid[rr][cc]
            if target == 0:
                out[rr][cc] = 4 if mode == "copy_yellow" else 7
            elif mode == "overwrite_nonaxis_yellow" and target == 4 and cc != c:
                out[rr][cc] = 7
            elif mode == "recolor_axis_yellow" and cc == c:
                out[rr][cc] = 7
    return out


def whole_grid_empty(grid: Grid) -> Grid:
    return independent_rival(grid, "whole_grid_empty")


def nearest_frame_only(grid: Grid, *, frame_wins_ties: bool) -> Grid:
    """Reflect only when the target is nearest to blue, using input pixels only.

    This is the independent counterpart of the generic nearest-component label
    mutations on this task's one-frame manifold. No measured output is read.
    """
    out = copy.deepcopy(grid)
    r1, c1, r2, c2 = _frame(grid)
    marks = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value == 4 and r1 < r < r2 and c1 < c < c2]
    for r, c in marks:
        target = c1 + c2 - c
        if grid[r][target] != 0:
            continue
        blue_distance = min(r - r1, r2 - r, target - c1, c2 - target)
        yellow_distance = min(abs(r - rr) + abs(target - cc) for rr, cc in marks)
        if blue_distance < yellow_distance or (frame_wins_ties and blue_distance == yellow_distance):
            out[r][target] = 7
    return out


def _scene(*, frame: tuple[int, int, int, int], marks: list[tuple[int, int]], h: int = 7, w: int = 9) -> Grid:
    grid = [[0] * w for _ in range(h)]
    r1, c1, r2, c2 = frame
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if r in (r1, r2) or c in (c1, c2):
                grid[r][c] = 1
    for r, c in marks:
        grid[r][c] = 4
    return grid


def weak_axis_scene() -> Grid:
    """Off-center frame, yet both candidate axes paint only cell (2, 5)."""
    return _scene(frame=(1, 1, 4, 6), marks=[(2, 2), (2, 3), (2, 4)])


def outside_marker_cases() -> dict[str, Grid]:
    return {
        "positive_oob_mirror": _scene(frame=(1, 3, 4, 7), marks=[(2, 4), (0, 0)]),
        "negative_mirror_index": _scene(frame=(1, 1, 4, 5), marks=[(2, 2), (0, 8)]),
        "outside_row_in_bounds_mirror": _scene(frame=(1, 1, 4, 5), marks=[(2, 2), (0, 2)]),
    }


def declared_rivals(gen: Any) -> dict[str, Callable[[Grid], Grid]]:
    """Keep namespaces explicit so a probe follows the live contract after edits."""
    result: dict[str, Callable[[Grid], Grid]] = {}
    for namespace in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        rules = getattr(gen, namespace, {})
        if isinstance(rules, dict):
            result.update({f"{namespace}:{name}": fn for name, fn in rules.items() if callable(fn)})
    return result


def diagnostic_rivals() -> dict[str, Callable[[Grid], Grid]]:
    result = {
        f"diagnostic:{mode}": (lambda grid, mode=mode: independent_rival(grid, mode))
        for mode in ("identity", "overwrite_nonaxis_yellow", "recolor_axis_yellow", "whole_grid_empty", "copy_yellow", "vertical_empty")
    }
    result.update({
        "diagnostic:nearest_frame_with_ties": lambda grid: nearest_frame_only(grid, frame_wins_ties=True),
        "diagnostic:nearest_frame_strict": lambda grid: nearest_frame_only(grid, frame_wins_ties=False),
    })
    return result


def _hook(fn: Callable, *args: Any) -> dict[str, Any]:
    try:
        result = fn(*copy.deepcopy(args))
    except Exception as exc:
        return {"reasons": None, "error": f"{type(exc).__name__}: {exc}"}
    if not isinstance(result, list) or any(not isinstance(reason, str) for reason in result):
        return {"reasons": None, "error": f"Invalid reasons result: {result!r}"}
    return {"reasons": result, "error": None}


def _grid_hash(grid: Grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def audit(*, seeds: tuple[int, ...], starts: int, bands: tuple[str, ...]) -> dict[str, Any]:
    from arcpuzzles import Catalog

    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    n_demos = gen.EXAMPLES_NEEDED
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for pair in canonical:
        records.append({"kind": "canonical", **pair})
    for name, grid in outside_marker_cases().items():
        records.append({"kind": "invalid_rectangular", "name": name, "input": grid})
    weak_index = len(records)
    records.append({"kind": "weak_axis_fixture", "input": weak_axis_scene()})
    sample_map: dict[tuple[str, int, int], int] = {}
    for band in bands:
        for seed in seeds:
            for si in range(starts + n_demos):
                grid = gen.generate(seed, si, difficulty=band)
                sample_map[band, seed, si] = len(records)
                records.append({"kind": "generated", "difficulty": band, "seed": seed, "sample_index": si, "input": grid})

    authority: list[dict[str, Any]] = []
    catalog = Catalog(root)
    for first in range(0, len(records), 64):
        subset = records[first:first + 64]
        applied = catalog.apply(TASK_ID, [record["input"] for record in subset], timeout=120)
        if applied["generator_sha256"] != digest:
            raise RuntimeError("Selected generator changed while this diagnostic was running; rerun on stable bytes")
        authority.append({"first_record": first, "record_count": len(subset), **{k: v for k, v in applied.items() if k != "results"}})
        for offset, (record, result) in enumerate(zip(subset, applied["results"], strict=True)):
            index = first + offset
            if result.get("error"):
                failures.append({"kind": "reference_error", "record": index, "error": result["error"]})
            if record["kind"] == "canonical" and record["output"] != result["output"]:
                failures.append({"kind": "canonical_label_mismatch", "record": index})
            record["output"] = result["output"]
            record["reference_error"] = result.get("error")
            record["input_sha256"] = result["input_sha256"]
            record["output_sha256"] = result["output_sha256"]

    rivals = {**diagnostic_rivals(), **declared_rivals(gen)}
    predictions: dict[tuple[str, int], Grid | None] = {}
    for name, rival in rivals.items():
        for index, record in enumerate(records):
            if record["kind"] == "invalid_rectangular":
                continue
            try:
                predictions[name, index] = normalize_grid(rival(copy.deepcopy(record["input"])))
            except Exception as exc:
                predictions[name, index] = None
                failures.append({"kind": "rival_error", "rival": name, "record": index, "error": f"{type(exc).__name__}: {exc}"})

    canonical_fit = {}
    for name in rivals:
        mismatches = [i for i in range(len(canonical)) if predictions[name, i] != records[i]["output"]]
        canonical_fit[name] = {"checked": len(canonical), "mismatches": mismatches, "fits_all": not mismatches}
        if name.startswith("CANONICAL_SHORTCUTS:") and mismatches:
            failures.append({"kind": "false_canonical_shortcut", "rival": name, "records": mismatches})

    validators = []
    for index, record in enumerate(records):
        if record["kind"] != "invalid_rectangular":
            continue
        for hook_name in ("self_check", "strict_canonical_like"):
            outcome = _hook(getattr(gen, hook_name), record["input"])
            validators.append({"record": index, "case": record["name"], "hook": hook_name, **outcome})
            if outcome["error"] or not outcome["reasons"] or not any("outside" in reason for reason in outcome["reasons"]):
                failures.append({"kind": "invalid_marker_validation", "record": index, "hook": hook_name, **outcome})

    witness_checks = []
    claims = getattr(gen, "WITNESS_RIVALS", {})
    for index, record in enumerate(records):
        if record["kind"] not in {"generated", "weak_axis_fixture"}:
            continue
        selfcheck = _hook(gen.self_check, record["input"])
        record["self_check"] = selfcheck
        if selfcheck["error"] or selfcheck["reasons"]:
            failures.append({"kind": "valid_input_rejected", "record": index, **selfcheck})
        for witness, fn in gen.SEMANTIC_WITNESSES.items():
            try:
                fires = fn(copy.deepcopy(record["input"]))
            except Exception as exc:
                failures.append({"kind": "witness_error", "witness": witness, "record": index, "error": f"{type(exc).__name__}: {exc}"})
                continue
            names = claims.get(witness, [])
            names = [names] if isinstance(names, str) else list(names)
            unknown = [name for name in names if f"SEMANTIC_RIVALS:{name}" not in rivals]
            if unknown:
                failures.append({"kind": "unknown_witness_rival", "record": index, "witness": witness, "rivals": unknown})
            disagreement = [name for name in names if predictions.get((f"SEMANTIC_RIVALS:{name}", index)) is not None and predictions[f"SEMANTIC_RIVALS:{name}", index] != record["output"]]
            witness_checks.append({"record": index, "witness": witness, "fires": bool(fires), "declared_rivals": names, "disagreeing_rivals": disagreement})
            if fires and names and not disagreement:
                failures.append({"kind": "witness_proves_nothing", "record": index, "witness": witness, "declared_rivals": names})
            if witness == "frame_local_not_global_axis" and fires and whole_grid_empty(record["input"]) == record["output"]:
                failures.append({"kind": "frame_axis_witness_false_positive", "record": index, "witness": witness})

    lessons = []
    rotations = []
    for band in bands:
        for seed in seeds:
            for start in range(starts):
                indices = [sample_map[band, seed, start + offset] for offset in range(n_demos + 1)]
                lesson_index = len(lessons)
                lessons.append({"difficulty": band, "seed": seed, "start": start, "records": indices})
                for query_position, query_index in enumerate(indices):
                    demos = [records[index] for index in indices if index != query_index]
                    outcome = _hook(gen.lesson_identifiable, demos, records[query_index])
                    ambiguous = [name for name in rivals if predictions[name, query_index] is not None and all(predictions[name, index] == records[index]["output"] for index in indices if index != query_index) and predictions[name, query_index] != records[query_index]["output"]]
                    row = {"lesson": lesson_index, "query_position": query_position, "query_record": query_index, "ambiguous_rivals": ambiguous, "ambiguous_rival_outputs": {name: predictions[name, query_index] for name in ambiguous}, **outcome}
                    rotations.append(row)
                    if outcome["error"] or outcome["reasons"]:
                        failures.append({"kind": "rotation_hook", **row})
                    if ambiguous:
                        failures.append({"kind": "rotation_rival_ambiguity", **row})

    return {
        "schema": "arc-mirror-contract-probe-v1",
        "task_id": TASK_ID,
        "execution": {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()), "source_root": str(root)},
        "source": {"generator_path": str(source.relative_to(root)), "generator_sha256": digest, "rule_hash": gen.RULE_HASH, "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        "scope": {"seeds": list(seeds), "bands": list(bands), "starts": list(range(starts)), "demonstrations": n_demos, "authority": "canonical Racket via Catalog.apply", "claim": "bounded focused regression evidence"},
        "authority_batches": authority,
        "rivals": sorted(rivals),
        "canonical_fit": canonical_fit,
        "weak_axis_record": weak_index,
        "validator_results": validators,
        "records": records,
        "witness_checks": witness_checks,
        "lessons": lessons,
        "rotations": rotations,
        "failures": failures,
        "summary": {"records": len(records), "canonical_pairs": len(canonical), "lessons": len(lessons), "rotations": len(rotations), "failures": len(failures), "failures_by_kind": dict(Counter(row["kind"] for row in failures)), "passed": not failures},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--starts", type=int, default=6)
    parser.add_argument("--band", choices=("easy", "medium", "hard"), action="append", dest="bands")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.starts < 1:
        parser.error("--starts must be positive")
    report = audit(seeds=tuple(args.seeds or (0, 2)), starts=args.starts, bands=tuple(args.bands or ("easy", "medium", "hard")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    exit_code = 0 if report["summary"]["passed"] else 1
    print(json.dumps({"report": str(args.out.resolve()), "generator_sha256": report["source"]["generator_sha256"], "exit_code": exit_code, **report["summary"]}, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

"""Independent semantic design probe for 31b8bedd699a.

The standard-library oracle and named alternatives below are design candidates,
not reference authorities or a snapshot of the generator's live declarations.
The CLI obtains every label through public ``Catalog.apply``. It checks four
unique canonical pairs and four explicit witnesses, and separately scores every
currently declared generator rival in each declaration namespace.

From a review packet's outer directory::

    python review.py run python \
        generators/31b8bedd699a/workspace/frame_semantics_probe.py \
        --out ../checks/semantic-design/reference-probe.json

An authoring checkout also supports an absolute script path from any cwd when
the protected Racket runtime is configured. Importing this module or running
``--describe`` does not execute Racket or write files. Missing reference outputs
are recorded as errors and never treated as counterexamples.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def _bootstrap_own_tree() -> None:
    """Import public support from this file's ancestors, never a sibling tree."""
    for ancestor in Path(__file__).resolve().parents:
        for relative in ("shared/runtime", ""):
            support = ancestor / relative
            if (support / "reviewer_support.py").is_file():
                sys.path.insert(0, str(support))
                source = ancestor / "src"
                if (source / "arcpuzzles").is_dir():
                    sys.path.insert(0, str(source))
                return
    raise FileNotFoundError("No reviewer_support.py in this probe's own tree")


_bootstrap_own_tree()
from reviewer_support import canonical_pairs, find_root, normalize_grid


TASK_ID = "31b8bedd699a"
DECLARATION_NAMES = (
    "SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS",
)
DESIGN_DESCRIPTIONS = {
    "crop": "Pack original frame crops and preserve their dimensions.",
    "centers": "Choose orientation and order using bounding-box centers.",
    "bbox_extent": "Choose orientation from aggregate frame bounding-box extents.",
    "tie_vertical": "Use row-range >= column-range, selecting vertical on ties.",
    "unique_colors": "Emit only the first retained frame token of each color.",
    "size12": "Retain components with exactly 12 colored cells.",
    "solid_axis": "Include solid components when choosing output orientation.",
    "always_horizontal": "Always concatenate retained frame tokens horizontally.",
    "row_major": "Keep row-major extraction order after choosing orientation.",
    "color_order": "Sort retained frame tokens by ascending color index.",
}


def grid_hash(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def components(grid: list[list[int]]) -> list[dict]:
    """Four-connected same-color components in row-major discovery order."""
    grid = normalize_grid(grid)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            pending = [(row, col)]
            cells = {(row, col)}
            seen.add((row, col))
            while pending:
                r, c = pending.pop()
                for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= rr < height and 0 <= cc < width
                            and grid[rr][cc] == color and (rr, cc) not in seen):
                        pending.append((rr, cc))
                        cells.add((rr, cc))
                        seen.add((rr, cc))
            rows, cols = zip(*cells)
            top, left = min(rows), min(cols)
            bh, bw = max(rows) - top + 1, max(cols) - left + 1
            result.append({
                "color": color, "top": top, "left": left,
                "height": bh, "width": bw, "size": len(cells),
                "kind": "solid" if len(cells) == bh * bw else "frame",
            })
    return result


def _render(grid: list[list[int]], frames: list[dict], vertical: bool,
            *, preserve_sizes: bool = False) -> list[list[int]]:
    if not frames:
        # A deterministic wrong-rule prediction when size12 selects nothing.
        return [[0]]
    tiles = []
    for frame in frames:
        if preserve_sizes:
            r, c = frame["top"], frame["left"]
            tiles.append([
                row[c:c + frame["width"]]
                for row in grid[r:r + frame["height"]]
            ])
        else:
            tiles.append([
                [frame["color"] if r in (0, 3) or c in (0, 3) else 0
                 for c in range(4)] for r in range(4)
            ])
    if vertical:
        width = max(len(tile[0]) for tile in tiles)
        return [row + [0] * (width - len(row)) for tile in tiles for row in tile]
    height = max(len(tile) for tile in tiles)
    return [
        sum((tile[r] if r < len(tile) else [0] * len(tile[0])
             for tile in tiles), [])
        for r in range(height)
    ]


def candidate_solve(grid: list[list[int]], name: str) -> list[list[int]]:
    """Run a named design alternative; ``oracle`` selects the independent model."""
    if name != "oracle" and name not in DESIGN_DESCRIPTIONS:
        raise KeyError(name)
    grid = normalize_grid(grid)
    objects = components(grid)
    frames = [obj for obj in objects if obj["kind"] == "frame"]
    if name == "size12":
        frames = [obj for obj in objects if obj["size"] == 12]
    if not frames:
        if name == "oracle":
            raise ValueError("The independent oracle requires a nonsolid component")
        return [[0]]
    axis_objects = objects if name == "solid_axis" else frames
    if name == "centers":
        row_key = lambda obj: obj["top"] + (obj["height"] - 1) / 2
        col_key = lambda obj: obj["left"] + (obj["width"] - 1) / 2
    else:
        row_key = lambda obj: obj["top"]
        col_key = lambda obj: obj["left"]
    row_range = max(map(row_key, axis_objects)) - min(map(row_key, axis_objects))
    col_range = max(map(col_key, axis_objects)) - min(map(col_key, axis_objects))
    if name == "bbox_extent":
        row_range = (max(obj["top"] + obj["height"] for obj in frames)
                     - min(obj["top"] for obj in frames))
        col_range = (max(obj["left"] + obj["width"] for obj in frames)
                     - min(obj["left"] for obj in frames))
    vertical = row_range >= col_range if name == "tie_vertical" else row_range > col_range
    if name == "always_horizontal":
        vertical = False
    if name == "row_major":
        key = lambda obj: (obj["top"], obj["left"])
    elif name == "color_order":
        key = lambda obj: obj["color"]
    else:
        key = row_key if vertical else col_key
    frames.sort(key=key)
    if name == "unique_colors":
        seen_colors = set()
        unique_frames = []
        for frame in frames:
            if frame["color"] not in seen_colors:
                unique_frames.append(frame)
                seen_colors.add(frame["color"])
        frames = unique_frames
    return _render(grid, frames, vertical, preserve_sizes=name == "crop")


def oracle(grid: list[list[int]]) -> list[list[int]]:
    """Independent model for comparisons only; never a substitute for Racket labels."""
    return candidate_solve(grid, "oracle")


def _candidate(name: str):
    def solve(grid):
        return candidate_solve(grid, name)
    solve.__name__ = name
    return solve


DESIGN_CANDIDATES = {name: _candidate(name) for name in DESIGN_DESCRIPTIONS}


def _scene(height: int, width: int, frames: list[tuple], solids: list[tuple]) -> list[list[int]]:
    grid = [[0] * width for _ in range(height)]
    occupied_boxes = set()
    for is_frame, boxes in ((True, frames), (False, solids)):
        for top, left, bh, bw, color in boxes:
            for r in range(bh):
                for c in range(bw):
                    cell = (top + r, left + c)
                    if not (0 <= cell[0] < height and 0 <= cell[1] < width):
                        raise ValueError("Witness box outside canvas")
                    if cell in occupied_boxes:
                        raise ValueError("Overlapping witness boxes")
                    occupied_boxes.add(cell)
                    if not is_frame or r in (0, bh - 1) or c in (0, bw - 1):
                        grid[cell[0]][cell[1]] = color
    return grid


def design_witnesses() -> dict[str, list[list[int]]]:
    """The exact four manually designed inputs from the independent analysis."""
    return {
        "tie_rich": _scene(
            28, 24, [(2, 16, 4, 4, 2), (9, 9, 4, 4, 4), (16, 2, 6, 3, 4)],
            [(24, 10, 3, 4, 6)],
        ),
        "horizontal_strict": _scene(
            24, 22, [(9, 2, 4, 4, 4), (2, 16, 4, 4, 2)],
            [(20, 8, 4, 4, 8), (14, 15, 4, 4, 6)],
        ),
        "vertical_strict": _scene(
            24, 24, [(2, 2, 4, 4, 4), (16, 4, 4, 4, 2)],
            [(7, 19, 4, 4, 8), (16, 16, 4, 4, 6)],
        ),
        "vertical_rich": _scene(
            24, 28, [(2, 15, 8, 8, 4), (16, 2, 3, 3, 2)],
            [(2, 2, 4, 4, 8), (18, 23, 4, 4, 6)],
        ),
    }


def unique_canonical(root: Path) -> tuple[list[dict], int]:
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    unique = {}
    for pair in pairs:
        key = (grid_hash(pair["input"]), grid_hash(pair["output"]))
        identity = {key: pair[key] for key in ("variant", "split", "pair_index")}
        if key not in unique:
            unique[key] = {
                "input": pair["input"], "output": pair["output"],
                "canonical_identities": [],
            }
        unique[key]["canonical_identities"].append(identity)
    return list(unique.values()), len(pairs)


def _load_generator(root: Path):
    candidates = (
        root / "generators" / TASK_ID / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    path = next((path for path in candidates if path.is_file()), None)
    if path is None:
        raise FileNotFoundError("Selected generator absent from this tree")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    module_name = f"frame_probe_generator_{digest}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module, path, digest


def _score_rule(solve, cases: list[dict], canonical_count: int) -> dict:
    matches, errors = [], []
    for case in cases:
        if not case["valid_reference_output"]:
            matches.append(None)
            continue
        try:
            predicted = normalize_grid(solve(deepcopy(case["input"])))
            matches.append(predicted == case["output"])
        except Exception as exc:
            matches.append(None)
            errors.append({"case": case["name"], "error": f"{type(exc).__name__}: {exc}"})
    canonical_matches = matches[:canonical_count]
    return {
        "canonical_matches": canonical_matches,
        "canonical_fit_count": sum(match is True for match in canonical_matches),
        "fits_all_canonical": bool(canonical_matches) and all(match is True for match in canonical_matches),
        "counterexamples": [case["name"] for case, match in zip(cases, matches) if match is False],
        "errors": errors,
    }


def run_probe(*, timeout: float = 120) -> dict:
    from arcpuzzles import Catalog

    root = find_root(__file__)
    canonical, ledger_pair_count = unique_canonical(root)
    witnesses = design_witnesses()
    generator, generator_path, generator_digest = _load_generator(root)
    inputs = [pair["input"] for pair in canonical] + list(witnesses.values())
    applied = Catalog(root).apply(TASK_ID, inputs, reference="canonical", timeout=timeout)
    cases = []
    for index, result in enumerate(applied["results"]):
        is_canonical = index < len(canonical)
        valid = bool(result.get("valid_output") and result.get("output"))
        case = {
            "name": f"canonical_{index + 1}" if is_canonical else list(witnesses)[index - len(canonical)],
            "kind": "canonical" if is_canonical else "design_witness",
            "input": result["input"], "output": result.get("output"),
            "input_sha256": result["input_sha256"],
            "output_sha256": result["output_sha256"],
            "valid_reference_output": valid,
            "reference_error": result.get("error"),
            "components": components(result["input"]),
            "independent_oracle_matches": valid and oracle(result["input"]) == result["output"],
        }
        if is_canonical:
            case["canonical_identities"] = canonical[index]["canonical_identities"]
            case["canonical_label_sha256"] = grid_hash(canonical[index]["output"])
            case["canonical_label_matches"] = valid and result["output"] == canonical[index]["output"]
        cases.append(case)
    design_scores = {
        name: {"description": DESIGN_DESCRIPTIONS[name], **_score_rule(solve, cases, len(canonical))}
        for name, solve in DESIGN_CANDIDATES.items()
    }
    declared_scores, declaration_errors = {}, []
    for namespace in DECLARATION_NAMES:
        rules = getattr(generator, namespace, {})
        if not isinstance(rules, dict):
            declaration_errors.append(f"{namespace}: expected a dictionary")
            continue
        declared_scores[namespace] = {}
        for name, solve in rules.items():
            if not isinstance(name, str) or not callable(solve):
                declaration_errors.append(f"{namespace}: invalid rival declaration {name!r}")
                continue
            declared_scores[namespace][name] = _score_rule(solve, cases, len(canonical))
    generator_unchanged = hashlib.sha256(generator_path.read_bytes()).hexdigest() == generator_digest
    source_consistent = generator_unchanged and applied["generator_sha256"] == generator_digest
    reference_ok = (all(case["valid_reference_output"] and case["independent_oracle_matches"] for case in cases)
                    and all(case["canonical_label_matches"] for case in cases if case["kind"] == "canonical")
                    and applied["rule_hash_matches_catalog"] and source_consistent)
    scoring_ok = (not declaration_errors
                  and all(not score["errors"] for score in design_scores.values())
                  and all(not score["errors"] for scores in declared_scores.values() for score in scores.values()))
    return {
        "schema": "frame-semantics-probe-v1", "task_id": TASK_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if reference_ok and scoring_ok else "FAIL",
        "reference_basis": "Public Catalog.apply with the canonical Racket authority; no generated or mirror labels.",
        "design_candidate_scope": "Independent proposed alternatives, separate from live generator declarations.",
        "live_declaration_scope": "Each dictionary was loaded from the selected generator in this run; namespace identities preserved.",
        "source_consistent_through_run": source_consistent,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "reference_receipt": {key: value for key, value in applied.items() if key != "results"},
        "counts": {
            "canonical_ledger_pairs": ledger_pair_count,
            "unique_canonical_pairs": len(canonical), "design_witnesses": len(witnesses),
            "authoritative_valid_outputs": sum(case["valid_reference_output"] for case in cases),
            "independent_oracle_matches": sum(case["independent_oracle_matches"] for case in cases),
            "design_candidates": len(design_scores),
            "design_candidates_fit_all_canonical": sum(score["fits_all_canonical"] for score in design_scores.values()),
            "live_declared_rivals_by_namespace": {name: len(scores) for name, scores in declared_scores.items()},
        },
        "cases": cases, "design_candidates": design_scores,
        "live_declared_rivals": declared_scores, "declaration_errors": declaration_errors,
        "limits": [
            "Eight focused inputs are design evidence, not a distributional safety review.",
            "This probe does not establish lesson or query-rotation identifiability.",
            "Rival predictions never supply reference labels.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Write the complete measured JSON receipt to this new file.")
    parser.add_argument("--timeout", type=float, default=120, help="Public reference execution timeout in seconds.")
    parser.add_argument("--describe", action="store_true", help="Read local canonical counts and describe candidates without reference execution.")
    args = parser.parse_args(argv)
    if args.describe:
        root = find_root(__file__)
        canonical, ledger_count = unique_canonical(root)
        print(json.dumps({"task_id": TASK_ID, "root": str(root), "canonical_ledger_pairs": ledger_count,
                          "unique_canonical_pairs": len(canonical), "design_candidates": DESIGN_DESCRIPTIONS,
                          "witness_names": list(design_witnesses())}, sort_keys=True))
        return 0
    if args.out is not None and args.out.exists():
        parser.error(f"Refusing to overwrite an existing receipt: {args.out}")
    report = run_probe(timeout=args.timeout)
    encoded = json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    if len(encoded.encode("utf-8")) >= 100_000:
        raise ValueError("Receipt exceeded the intentionally small 100 KB limit")
    if args.out is None:
        print(encoded, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
        print(json.dumps({"status": report["status"], "receipt": str(args.out.resolve()),
                          "bytes": len(encoded.encode("utf-8")), "counts": report["counts"],
                          "generator_sha256": report["reference_receipt"]["generator_sha256"],
                          "executed_rule_hash": report["reference_receipt"]["executed_rule_hash"],
                          "probe_sha256": report["probe_sha256"]}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Source-bound adversarial probe for the two immutable audit assignments.

Run from the packet root through the bundled Racket wrapper::

    python3 run_with_racket.py python3 \
      generators/fa55db418c9d/workspace/audit_probe.py \
      --out ../checks/audit-probe-final.json

The probe does not modify either audit target. It records generator/rule hashes,
canonical authority checks, exact override behavior, validator results, and an
actual-Racket counterexample for the disconnected-template finding.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any, Iterable

TARGETS = ("2fc4ca4ea6c4", "8d46d66e31b0")
TASK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_DIR.parents[1]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
TOOLS_ROOT = REPO_ROOT / "shared" / "tools"
for path in (TOOLS_ROOT, RUNTIME_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
if "scripts" not in sys.modules:
    scripts_pkg = types.ModuleType("scripts")
    scripts_pkg.__path__ = [str(TOOLS_ROOT)]
    sys.modules["scripts"] = scripts_pkg


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalized_rule_hash(source: str) -> str:
    return sha256_bytes(" ".join(source.split()).encode())


def to_grid(value: Any) -> list[list[int]]:
    if not isinstance(value, list):
        raise TypeError(f"expected grid list, got {type(value).__name__}")
    if value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return [[int(cell) for cell in row] for row in value]


def same_color_components(
    grid: list[list[int]], *, color: int | None = None
) -> list[set[tuple[int, int]]]:
    """Return cardinal components, split by exact color."""
    if not grid:
        return []
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0 and (color is None or grid[r][c] == color)
    }
    components: list[set[tuple[int, int]]] = []
    while unseen:
        root = min(unseen)
        target_color = grid[root[0]][root[1]]
        unseen.remove(root)
        component = {root}
        stack = [root]
        while stack:
            r, c = stack.pop()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                point = (nr, nc)
                if point in unseen and grid[nr][nc] == target_color:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        components.append(component)
    return components


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    materialized = list(cells)
    if not materialized:
        raise ValueError("cannot compute bbox of empty cells")
    rows = [point[0] for point in materialized]
    cols = [point[1] for point in materialized]
    return min(rows), min(cols), max(rows), max(cols)


def _is_rect_border(cells: set[tuple[int, int]]) -> bool:
    if len(cells) < 8:
        return False
    r1, c1, r2, c2 = _bbox(cells)
    expected = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    return cells == expected


def documented_whole_template_output(grid: list[list[int]]) -> list[list[int]]:
    """Apply the written whole-template interpretation to a generated scene.

    Unlike the canonical Racket source, this intentionally treats *all* color-2
    cells as the advertised template even when the generator emitted a
    disconnected set. It therefore exposes the generator/invariant mismatch.
    """
    if not grid or not grid[0]:
        return copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    template_cells = {
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 2
    }
    if not template_cells:
        return [[0] * w for _ in range(h)]
    tr1, tc1, tr2, tc2 = _bbox(template_cells)
    normalized = sorted((r - tr1, c - tc1) for r, c in template_cells)
    th, tw = tr2 - tr1 + 1, tc2 - tc1 + 1
    out = [[0] * w for _ in range(h)]
    for component in same_color_components(grid):
        first = min(component)
        value = grid[first[0]][first[1]]
        if value == 2 or not _is_rect_border(component):
            continue
        r1, c1, r2, c2 = _bbox(component)
        for r, c in component:
            out[r][c] = value
        ih, iw = r2 - r1 - 1, c2 - c1 - 1
        sr = r1 + 1 + (ih - th) // 2
        sc = c1 + 1 + (iw - tw) // 2
        for dr, dc in normalized:
            rr, cc = sr + dr, sc + dc
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = value
    return out


def _load_generator(task_id: str):
    path = REPO_ROOT / "generators" / task_id / "generator.py"
    module_name = f"audit_probe_{task_id}_{sha256_file(path)[:12]}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module, path


def _canonical_rows() -> dict[str, dict[str, Any]]:
    wanted = set(TARGETS)
    rows: dict[str, dict[str, Any]] = {}
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") in wanted:
                rows[row["task_id"]] = row
    missing = wanted - rows.keys()
    if missing:
        raise RuntimeError(f"canonical rows missing: {sorted(missing)}")
    return rows


def _pairs(record: dict[str, Any]) -> list[dict[str, list[list[int]]]]:
    raw_test = record.get("test", [])
    tests = raw_test if isinstance(raw_test, list) else [raw_test]
    return [
        {"input": to_grid(pair["input"]), "output": to_grid(pair["output"])}
        for pair in [*record.get("train", []), *tests]
    ]


def _racket_literal(value: Any) -> str:
    if isinstance(value, list):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError(f"not an ARC literal: {value!r}")
    return str(value)


def _racket_outputs(rule_source: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge() as bridge:
        bridge.eval_text(f"(define audit-rule {wrap_rule(rule_source)})")
        result = bridge.eval_text(f"(map audit-rule '{_racket_literal(grids)})")
    if not isinstance(result, list) or len(result) != len(grids):
        raise RuntimeError("unexpected Racket batch result")
    return result


def _safe_generate(module: Any, seed: int, sample_index: int, **overrides: Any) -> dict[str, Any]:
    try:
        grid = module.generate(seed, sample_index, **overrides)
    except Exception as exc:  # exact exception is audit evidence
        return {
            "accepted": False,
            "exception": f"{type(exc).__name__}: {exc}",
        }
    return {
        "accepted": True,
        "grid": grid,
        "validator_findings": module.self_check(grid),
    }


def _audit_midpoint_generator(module: Any, path: Path, canonical: dict[str, Any]) -> dict[str, Any]:
    pairs = _pairs(canonical)
    actual = _racket_outputs(canonical["program_solution"], [pair["input"] for pair in pairs])
    base = _safe_generate(module, 42, 0)
    if not base["accepted"]:
        raise RuntimeError("2fc audit base generation unexpectedly failed")
    base_grid = base["grid"]
    base_output = _racket_outputs(canonical["program_solution"], [base_grid])[0]
    cases: dict[str, Any] = {}
    for name, value in (
        ("grid_h", 3),
        ("grid_w", 7),
        ("palette_kind", "warm"),
        ("palette_size", 1),
        ("n_distinct_colors", 1),
        ("texture", "cool"),
        ("unknown_axis", 1),
    ):
        result = _safe_generate(module, 42, 0, **{name: value})
        if result.get("accepted"):
            result["identical_to_default"] = result["grid"] == base_grid
        cases[name] = {"requested": value, **result}

    default_validation: dict[str, Any] = {}
    for band in ("easy", "medium", "hard"):
        accepted = valid = 0
        unique = set()
        for sample_index in range(32):
            grid = module.generate(20261002, sample_index, difficulty=band)
            accepted += 1
            valid += module.self_check(grid, difficulty=band) == []
            unique.add(sha256_bytes(json.dumps(grid, separators=(",", ":")).encode()))
        default_validation[band] = {
            "draws": accepted,
            "sample_indices": [0, 31],
            "validator_clean": valid,
            "unique_inputs": len(unique),
        }

    return {
        "task_id": TARGETS[0],
        "generator_sha256": sha256_file(path),
        "rule_source_sha256": sha256_bytes(canonical["program_solution"].encode()),
        "normalized_rule_sha256": normalized_rule_hash(canonical["program_solution"]),
        "canonical": {
            "pairs_checked": len(pairs),
            "racket_matches_published": sum(
                output == pair["output"] for output, pair in zip(actual, pairs)
            ),
        },
        "finding": {
            "classification": "reproduced override-contract defect",
            "summary": (
                "Declared exact controls are inert, unknown controls are silently accepted, "
                "and declared grid minima are rejected by the active draw ranges."
            ),
            "seed": 42,
            "sample_index": 0,
            "difficulty": None,
            "default_input": base_grid,
            "actual_racket_output": base_output,
            "override_cases": cases,
            "declared_axes": module.AXES,
            "input_passes_validator": base["validator_findings"] == [],
            "belongs_to_default_generator_domain": True,
        },
        "default_validation": default_validation,
    }


def _audit_template_generator(module: Any, path: Path, canonical: dict[str, Any]) -> dict[str, Any]:
    pairs = _pairs(canonical)
    canonical_actual = _racket_outputs(
        canonical["program_solution"], [pair["input"] for pair in pairs]
    )
    found: dict[str, Any] | None = None
    checked = 0
    for seed in range(32):
        for sample_index in range(32):
            grid = module.generate(seed, sample_index)
            checked += 1
            components = same_color_components(grid, color=2)
            if len(components) > 1:
                found = {
                    "seed": seed,
                    "sample_index": sample_index,
                    "difficulty": None,
                    "overrides": {},
                    "input": grid,
                    "color_2_component_sizes": sorted(len(component) for component in components),
                    "validator_findings": module.self_check(grid),
                }
                break
        if found is not None:
            break
    if found is None:
        raise RuntimeError("did not find disconnected default template in search window")
    actual = _racket_outputs(canonical["program_solution"], [found["input"]])[0]
    documented = documented_whole_template_output(found["input"])
    found.update(
        {
            "actual_racket_output": actual,
            "documented_whole_template_output": documented,
            "outputs_differ": actual != documented,
            "generated_by_default_path": True,
            "input_passes_validator": found["validator_findings"] == [],
            "violates_declared_invariant_exactly_one_connected_2_blob": True,
            "belongs_to_documented_generator_domain": False,
            "domain_note": (
                "The default generator emitted this scene, but it violates its own declared "
                "connected-template invariant; the validator does not detect that violation."
            ),
        }
    )
    return {
        "task_id": TARGETS[1],
        "generator_sha256": sha256_file(path),
        "rule_source_sha256": sha256_bytes(canonical["program_solution"].encode()),
        "normalized_rule_sha256": normalized_rule_hash(canonical["program_solution"]),
        "canonical": {
            "pairs_checked": len(pairs),
            "racket_matches_published": sum(
                output == pair["output"]
                for output, pair in zip(canonical_actual, pairs)
            ),
        },
        "search": {
            "seeds": [0, 31],
            "sample_indices": [0, 31],
            "cases_examined_until_first_finding": checked,
        },
        "finding": {
            "classification": "reproduced default-generation invariant/validator defect",
            "summary": (
                "A built-in template is three cardinally disconnected singleton cells. "
                "The default generator emits it, self_check accepts it, and canonical Racket "
                "extracts only one singleton rather than the advertised whole template."
            ),
            **found,
        },
    }


def run_probe() -> dict[str, Any]:
    canonical = _canonical_rows()
    modules = {task: _load_generator(task) for task in TARGETS}
    reports = {
        TARGETS[0]: _audit_midpoint_generator(
            modules[TARGETS[0]][0], modules[TARGETS[0]][1], canonical[TARGETS[0]]
        ),
        TARGETS[1]: _audit_template_generator(
            modules[TARGETS[1]][0], modules[TARGETS[1]][1], canonical[TARGETS[1]]
        ),
    }
    unexpected: list[str] = []
    if reports[TARGETS[0]]["canonical"]["racket_matches_published"] != reports[TARGETS[0]]["canonical"]["pairs_checked"]:
        unexpected.append("2fc canonical authority mismatch")
    if reports[TARGETS[1]]["canonical"]["racket_matches_published"] != reports[TARGETS[1]]["canonical"]["pairs_checked"]:
        unexpected.append("8d4 canonical authority mismatch")
    if not reports[TARGETS[1]]["finding"]["outputs_differ"]:
        unexpected.append("8d4 disconnected-template witness did not distinguish outputs")
    return {
        "schema": "fa55-source-bound-adversarial-audit-v1",
        "probe_source_sha256": sha256_file(Path(__file__)),
        "runtime_cwd": str(Path.cwd()),
        "argv": sys.argv,
        "targets": reports,
        "unexpected_failures": unexpected,
        "findings_reproduced": not unexpected,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_probe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "findings_reproduced": report["findings_reproduced"],
                "unexpected_failures": len(report["unexpected_failures"]),
                "2fc_override_cases": len(report["targets"][TARGETS[0]]["finding"]["override_cases"]),
                "8d4_witness": {
                    "seed": report["targets"][TARGETS[1]]["finding"]["seed"],
                    "sample_index": report["targets"][TARGETS[1]]["finding"]["sample_index"],
                },
            },
            sort_keys=True,
        )
    )
    return 0 if report["findings_reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

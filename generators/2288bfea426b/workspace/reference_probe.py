"""Independent oracle and reproducible audit for 2288bfea426b.

The Python oracle is supplementary test tooling, never label authority.  Passing
``--racket`` executes the canonical Racket program and fails rather than falling
back when that runtime is unavailable.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "2288bfea426b"

# The public helper is normally injected by the task-test runtime.  The source
# checkout fallback only locates that helper; all data/root resolution still
# goes through reviewer_support rather than a fixed parent depth.
try:
    from reviewer_support import (
        canonical_pairs as _read_canonical_pairs, canonical_path, find_root,
    )
except ModuleNotFoundError:
    for _parent in Path(__file__).resolve().parents:
        _runtime = _parent / "shared/runtime"
        if (_runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(_runtime))
            break
    from reviewer_support import (
        canonical_pairs as _read_canonical_pairs, canonical_path, find_root,
    )

ROOT = Path(find_root(__file__)).resolve()
CODES = (1, 3, 4, 6)
TURNS = {1: 0, 3: 1, 4: 2, 6: 3}
STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _generator_path(path=None):
    if path is not None:
        candidate = Path(path).resolve()
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        return candidate
    for candidate in (
        ROOT / f"generators/{TASK}/generator.py",
        ROOT / f"puzzle_generators/per_puzzle/{TASK}/generator.py",
    ):
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"selected generator {TASK} is absent under {ROOT}")


def load_generator(path=None):
    selected = path or __import__("os").environ.get("GENERATOR_UNDER_TEST")
    generator_path = _generator_path(selected)
    spec = importlib.util.spec_from_file_location("reviewed_generator", generator_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError("canonical task is absent")


def canonical_pairs():
    return _read_canonical_pairs(TASK, root=ROOT)


def normalize(cells):
    cells = tuple(cells)
    if not cells:
        raise ValueError("missing template")
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def rotate(cells, turns):
    result = tuple(cells)
    for _ in range(turns % 4):
        result = tuple((c, -r) for r, c in result)
        result = normalize(result)
    return tuple(sorted(result))


def scene(grid):
    source = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    markers = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value in CODES]
    return normalize(source), markers


def oracle_output(grid, *, rival=None):
    """Independent bounding-box-normalized rotation/stamping implementation."""
    shape, markers = scene(grid)
    h, w = len(grid), len(grid[0])
    if rival == "first_three_markers":
        markers = markers[:3]
    seen = set()
    out = [[0 for _ in range(w)] for _ in range(h)]
    for ar, ac, code in markers:
        if rival == "deduplicate_marker_code" and code in seen:
            continue
        seen.add(code)
        actual = code
        if isinstance(rival, tuple) and rival[0] == "map" and code == rival[1]:
            actual = rival[2]
        for dr, dc in rotate(shape, TURNS[actual]):
            r, c = ar + dr, ac + dc
            if 0 <= r < h and 0 <= c < w:
                out[r][c] = 8
    return out


def observed(grid):
    shape, markers = scene(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_size": len(shape),
        "n_markers": len(markers),
    }


def racket_outputs(grids):
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(json.dumps({"program": program, "grids": grids}))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    outputs=[runner._apply_rule(bridge,name,g) for g in request['grids']]
    print(json.dumps(outputs))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count):
    by_band = {}
    retained = [pair["input"] for pair in canonical_pairs()]
    totals = Counter()
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        shapes, dimensions, inputs, code_sets = set(), set(), set(), set()
        for i in range(count):
            seed, sample_index = 1907 + i, i
            grid = module.generate(seed, sample_index, difficulty=band)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            truth = oracle_output(grid)
            counts["changed"] += truth != grid
            obs = observed(grid)
            shape, markers = scene(grid)
            dimensions.add((obs["grid_h"], obs["grid_w"]))
            shapes.add(shape)
            code_sets.add(tuple(sorted(code for _, _, code in markers)))
            counts["canonical_profile"] += (obs["grid_h"], obs["grid_w"], len({v for row in grid for v in row})) == (13, 13, 5)
            counts["repeated_code"] += len({code for _, _, code in markers}) < len(markers)
            counts["all_four_codes"] += {code for _, _, code in markers} == set(CODES)
            counts["all_four_rotations"] += len({rotate(shape, turn) for turn in range(4)}) == 4
            for name, rival in getattr(module, "SEMANTIC_RIVALS", {}).items():
                counts[f"rival:{name}"] += rival(grid) != truth
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            inputs.add(digest)
            if i < 12:
                retained.append(grid)
        counts.update({
            "distinct_dimensions": len(dimensions),
            "distinct_shapes": len(shapes),
            "distinct_code_multisets": len(code_sets),
            "distinct_inputs": len(inputs),
        })
        by_band[str(band)] = dict(counts)
        totals.update(counts)
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": getattr(module, "VERSION", None),
        "canonical_matches": sum(oracle_output(pair["input"]) == pair["output"] for pair in canonical_pairs()),
        "canonical_self_check_errors": [module.self_check(pair["input"]) for pair in canonical_pairs()],
        "by_band": by_band,
        "totals": dict(totals),
        "sampling_design": "Consecutive sample indices are crossed with all four bands; counts are descriptive, not independent estimates.",
        "warning": "Python oracle is supplementary evidence; request --racket for authority parity.",
    }
    return report, retained


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250, help="samples per difficulty band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    generator_path = _generator_path(args.generator)
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["rule_hash"] = hashlib.sha256(" ".join(canonical()["program_solution"].split()).encode()).hexdigest()[:12]
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        report["canonical_matches"] != len(canonical_pairs())
        or any(report["canonical_self_check_errors"])
        or report["totals"]["self_check_errors"]
        or report["totals"]["nondeterministic"]
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [i for i, (grid, output) in enumerate(zip(grids, outputs)) if oracle_output(grid) != output]
            report["racket"] = {"status": "passed" if not mismatches else "failed", "checked": len(outputs), "mismatches": mismatches}
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:
            report["racket"] = {"status": "unavailable_or_failed", "checked": 0, "error": f"{type(exc).__name__}: {exc}"}
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"version": report["version"], "canonical_matches": report["canonical_matches"], "totals": report["totals"], "racket": report["racket"]}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

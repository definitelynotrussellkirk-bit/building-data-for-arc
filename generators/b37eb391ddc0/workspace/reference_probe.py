#!/usr/bin/env python3
"""Independent replayable audit for generator b37eb391ddc0.

This tool supplements, but never replaces, the canonical Racket authority.  It
checks canonical ownership, exact public profiles, semantic witnesses, declared
rival disagreements, deterministic sampling, exhaustive short lesson rotations,
and (with ``--racket``) real selected-rule parity in a staged runtime.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
TASK_ID = "b37eb391ddc0"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs, canonical_path, find_root  # noqa: E402


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load_generator(path: Path | None = None):
    path = (path or HERE.parents[1] / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    spec.loader.exec_module(module)
    return module, path


def canonical_program(root: Path) -> str:
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return str(row["program_solution"])
    raise KeyError(TASK_ID)


def foreground_object_count(grid) -> int:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            row, col = stack.pop()
            for cell in (
                (row - 1, col), (row + 1, col),
                (row, col - 1), (row, col + 1),
            ):
                if cell in remaining:
                    remaining.remove(cell)
                    stack.append(cell)
    return count


def racket_outputs(grids, root: Path):
    """Require and execute the selected Racket rule; never fall back to Python."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    sys.path.insert(0, str(REPO / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-probe-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(REPO), stage, TASK_ID)
        request = {"program": canonical_program(root), "grids": grids}
        (stage / "probe-request.json").write_text(json.dumps(request))
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path("probe-request.json").read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    outputs=[runner._apply_rule(bridge,name,grid) for grid in request["grids"]]
    print(json.dumps(outputs))
finally:
    shutdown=getattr(bridge,"shutdown",None)
    shutdown() if callable(shutdown) else bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=240)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def pair(module, grid):
    return {"input": copy.deepcopy(grid), "output": module.rule_mirror(grid)}


def audit(module, *, count: int) -> tuple[dict[str, Any], list]:
    root = find_root(HERE)
    canon = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_rows = {
        "count": len(canon),
        "self_check_errors": [module.self_check(p["input"]) for p in canon],
        "strict_errors": [module.strict_canonical_like(p["input"]) for p in canon],
        "mirror_mismatches": [
            index for index, p in enumerate(canon)
            if module.rule_mirror(p["input"]) != p["output"]
        ],
        "shortcut_fits": {
            name: all(rival(p["input"]) == p["output"] for p in canon)
            for name, rival in module.CANONICAL_SHORTCUTS.items()
        },
    }

    by_band: dict[str, Any] = {}
    parity_grids = [p["input"] for p in canon]
    for band_index, band in enumerate(("easy", "medium", "hard")):
        stats = Counter()
        profiles = Counter()
        witnesses = Counter()
        rival_disagreements = Counter()
        inputs, outputs = set(), set()
        object_counts = Counter()
        for index in range(count):
            seed = 90_000 + band_index * 10_000 + index
            sample_index = index * 17 + 5
            grid = module.generate(seed, sample_index, difficulty=band)
            again = module.generate(seed, sample_index, difficulty=band)
            expected = module.rule_mirror(grid)
            stats["samples"] += 1
            stats["nondeterministic"] += grid != again
            stats["self_check_errors"] += bool(module.self_check(grid))
            stats["teaching_check_errors"] += bool(module.teaching_check(grid))
            profile = module.observe_overrides(grid).get("scene_profile")
            profiles[str(profile)] += 1
            object_counts[str(foreground_object_count(grid))] += 1
            for name, predicate in module.SEMANTIC_WITNESSES.items():
                witnesses[name] += bool(predicate(grid))
            for name, rival in module.LESSON_COMPETITORS.items():
                rival_disagreements[name] += rival(grid) != expected
            inputs.add(digest(grid)); outputs.add(digest(expected))
            if index < 8:
                parity_grids.append(grid)
        by_band[band] = {
            **dict(stats),
            "profiles": dict(sorted(profiles.items())),
            "witnesses": dict(sorted(witnesses.items())),
            "rival_disagreements": dict(sorted(rival_disagreements.items())),
            "object_counts": dict(sorted(object_counts.items())),
            "unique_inputs": len(inputs),
            "unique_outputs": len(outputs),
        }

    rotations = Counter()
    examples = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(18):
            rows = [
                pair(module, module.generate(500_000 + band_index, start + offset, difficulty=band))
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            for query_index in range(len(rows)):
                query = rows[query_index]
                demos = [row for index, row in enumerate(rows) if index != query_index]
                reasons = module.lesson_identifiable(demos, query)
                rotations["checked"] += 1
                rotations["hook_failures"] += bool(reasons)
                survivors = [
                    name for name, rival in module.LESSON_COMPETITORS.items()
                    if all(rival(demo["input"]) == demo["output"] for demo in demos)
                    and rival(query["input"]) != query["output"]
                ]
                rotations["ambiguous"] += bool(survivors)
                if (reasons or survivors) and len(examples) < 5:
                    examples.append({
                        "band": band, "start": start, "query_index": query_index,
                        "reasons": reasons, "survivors": survivors,
                    })

    witness = [[2, 3], [0, 2]]
    report = {
        "schema": f"{TASK_ID}-reference-probe-v1",
        "task_id": TASK_ID,
        "version": module.VERSION,
        "rule_hash": module.RULE_HASH,
        "canonical": canonical_rows,
        "by_band": by_band,
        "lesson_rotations": {**dict(rotations), "examples": examples},
        "authority_counterexample": {
            "input": witness,
            "intended_python": module.rule_mirror(witness),
            "isolated_pairs_only": module._rival_isolated_pairs_only(witness),
            "preserve_occupied": module._rival_preserve_occupied(witness),
        },
        "limits": (
            "Finite declared-rival checks do not prove unique induction over all "
            "possible rules. Python parity is supplementary unless --racket passes."
        ),
    }
    parity_grids.insert(len(canon), witness)
    return report, parity_grids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100, help="samples per band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true", help="require selected-rule parity")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")

    module, generator_path = load_generator(args.generator)
    report, grids = audit(module, count=args.count)
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(HERE.read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}

    bad = False
    canonical = report["canonical"]
    bad |= bool(any(canonical["self_check_errors"]))
    bad |= bool(any(canonical["strict_errors"]))
    bad |= bool(canonical["mirror_mismatches"])
    bad |= not all(canonical["shortcut_fits"].values())
    for stats in report["by_band"].values():
        bad |= bool(stats["nondeterministic"])
        bad |= bool(stats["self_check_errors"])
        bad |= bool(stats["teaching_check_errors"])
        bad |= set(stats["profiles"]) != set(module.SCENE_PROFILES)
        bad |= any(value != args.count for value in stats["witnesses"].values())
        bad |= any(value != args.count for value in stats["rival_disagreements"].values())
    bad |= bool(report["lesson_rotations"]["hook_failures"])
    bad |= bool(report["lesson_rotations"]["ambiguous"])

    if args.racket:
        try:
            outputs = racket_outputs(grids, find_root(HERE))
            mismatches = [
                index for index, (grid, output) in enumerate(zip(grids, outputs))
                if module.rule_mirror(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            bad |= bool(mismatches)
            report["authority_counterexample"]["intended_racket"] = outputs[
                len(report["canonical"]["self_check_errors"])
            ]
        except Exception as exc:
            report["racket"] = {
                "status": "unavailable_or_failed", "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            bad = True

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "version": report["version"],
        "canonical": report["canonical"],
        "by_band": report["by_band"],
        "lesson_rotations": report["lesson_rotations"],
        "racket": report["racket"],
    }, indent=2, sort_keys=True))
    return int(bad)


if __name__ == "__main__":
    raise SystemExit(main())

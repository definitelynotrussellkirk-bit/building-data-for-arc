"""Bounded teaching and protected-Racket audit for 7c2b3290ba62.

Rival fitting reads demonstrations only. Query answers are used only to verify
that the selected Racket program labels the retained four controller queries.
The finite rival set is evidence, not a universal identifiability proof.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK = "7c2b3290ba62"
RIVALS = (
    "other_mode",
    "ignore_source",
    "intersect_candidates",
    "single_candidate",
    "reverse_size_roles",
    "left_index_cyan",
    "right_index_cyan",
    "global_two_largest",
    "global_two_smallest",
)


def _load_prototype():
    path = HOME / "prototype.py"
    name = "_arc_7c2b3290ba62_audit_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _empty(n: int) -> list[list[int]]:
    return [[0] * n]


def _role_output(facts: dict[str, Any], pair: tuple[int, int] | None, mode: str) -> list[list[int]]:
    result = _empty(len(facts["candidates"]))
    if pair is None:
        return result
    left, right = pair
    if mode == "pair_cyan":
        result[0][left] = 8
        result[0][right] = 8
    else:
        sizes = facts["candidate_sizes"]
        larger, smaller = (left, right) if sizes[left] >= sizes[right] else (right, left)
        result[0][larger] = 8
        result[0][smaller] = 2
    return result


def _first_pair(facts: dict[str, Any], policy: str) -> tuple[int, int] | None:
    candidates = facts["candidates"]
    source, target = facts["source"], facts["target"]
    pairs = [(left, right) for left in range(len(candidates)) for right in range(left + 1, len(candidates))]
    if policy == "ignore_source":
        return next((p for p in pairs if candidates[p[0]] | candidates[p[1]] == target), None)
    if policy == "intersect_candidates":
        return next((p for p in pairs if source | (candidates[p[0]] & candidates[p[1]]) == target), None)
    if policy == "global_two_largest":
        order = sorted(range(len(candidates)), key=lambda i: (-len(candidates[i]), i))
        return tuple(sorted(order[:2]))
    if policy == "global_two_smallest":
        order = sorted(range(len(candidates)), key=lambda i: (len(candidates[i]), i))
        return tuple(sorted(order[:2]))
    raise ValueError(f"unknown pair policy: {policy}")


def rival_output(grid: list[list[int]], mode: str, rival: str) -> list[list[int]]:
    prototype = _load_prototype()
    if rival not in RIVALS:
        raise ValueError(f"unknown rival: {rival}")
    facts = prototype.analyze(grid)
    selected = facts["good_pairs"][0] if facts["good_pairs"] else None
    if rival == "other_mode":
        other = "size_roles" if mode == "pair_cyan" else "pair_cyan"
        return prototype.solve_python(grid, other)
    if rival in {"ignore_source", "intersect_candidates", "global_two_largest", "global_two_smallest"}:
        return _role_output(facts, _first_pair(facts, rival), mode)
    if rival == "single_candidate":
        result = _empty(len(facts["candidates"]))
        index = next(
            (i for i, candidate in enumerate(facts["candidates"]) if facts["source"] | candidate == facts["target"]),
            None,
        )
        if index is not None:
            result[0][index] = 8
        return result
    if selected is None:
        return _empty(len(facts["candidates"]))
    left, right = selected
    result = _empty(len(facts["candidates"]))
    if rival == "left_index_cyan":
        result[0][left], result[0][right] = 8, 2
    elif rival == "right_index_cyan":
        result[0][left], result[0][right] = 2, 8
    elif rival == "reverse_size_roles":
        sizes = facts["candidate_sizes"]
        larger, smaller = (left, right) if sizes[left] >= sizes[right] else (right, left)
        result[0][larger], result[0][smaller] = 2, 8
    else:
        raise ValueError(f"unhandled rival: {rival}")
    return result


def teaching_audit(seed: int, mode: str, demos: int = 2) -> dict[str, Any]:
    prototype = _load_prototype()
    episode = prototype.generate(seed, {"marker_mode": mode}, demos, 4)
    rejected: dict[str, list[int]] = {}
    survivors: list[str] = []
    for rival in RIVALS:
        mismatches = [
            index
            for index, pair in enumerate(episode["train"])
            if rival_output(pair["input"], mode, rival) != pair["output"]
        ]
        rejected[rival] = mismatches
        if not mismatches:
            survivors.append(rival)
    return {
        "seed": seed,
        "settings": {"marker_mode": mode},
        "demos": demos,
        "queries": 4,
        "query_answers_used": False,
        "rejected_by_demo": rejected,
        "survivors": survivors,
        "scope": "finite named rivals fit to demonstrations only; no universal identifiability claim",
    }


def _sha_json(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(body).hexdigest()


def run(output: Path) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"refusing existing evidence destination: {output}")
    output.mkdir(parents=True)
    prototype = _load_prototype()
    reports = [
        teaching_audit(seed, mode, demos)
        for seed in (0, 17, 31)
        for mode in prototype.MODES
        for demos in (2, 3, 6)
    ]
    if any(report["survivors"] for report in reports):
        bad = [report for report in reports if report["survivors"]]
        raise AssertionError(f"named shortcuts survived: {bad}")

    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    executions: list[dict[str, Any]] = []
    bridge = None
    with _local_imports(ROOT / "shared/runtime", HOME):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            for report in reports:
                seed = report["seed"]
                mode = report["settings"]["marker_mode"]
                demos = report["demos"]
                episode = prototype.generate(seed, {"marker_mode": mode}, demos, 4)
                chosen = episode["program_solution"]
                other_mode = "size_roles" if mode == "pair_cyan" else "pair_cyan"
                other = prototype.program({"marker_mode": other_mode})
                other_rejections = []
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        actual = _grid(apply(chosen, deepcopy(pair["input"])))
                        if actual != pair["output"]:
                            raise AssertionError(f"selected Racket label mismatch: {seed}/{mode}/{demos}/{split}/{index}")
                        executions.append({
                            "seed": seed,
                            "settings": {"marker_mode": mode},
                            "demos": demos,
                            "split": split,
                            "pair_index": index,
                            "shape": [len(pair["input"]), len(pair["input"][0])],
                            "input_sha256": _sha_json(pair["input"]),
                            "output_sha256": _sha_json(actual),
                        })
                for index, pair in enumerate(episode["train"]):
                    if _grid(apply(other, deepcopy(pair["input"]))) != pair["output"]:
                        other_rejections.append(index)
                if not other_rejections:
                    raise AssertionError(f"declared setting rival survived Racket demos: {seed}/{mode}/{demos}")
                report["declared_rival_racket_rejected_by_demo"] = other_rejections
        finally:
            if bridge is not None:
                bridge.close()

    sources = {}
    for name in (
        "prototype.py",
        "adapter.py",
        "promotion.json",
        "canonical.rkt",
        "size_roles.rkt",
        "wrong_size_roles.rkt",
        "audit.py",
    ):
        path = HOME / name
        sources[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        "schema": "7c2b3290ba62-marker-mode-self-review-v1",
        "status": "passed",
        "task_id": TASK,
        "scope": "finite two-setting and eight-shortcut demo audit; selected labels and declared setting rival executed in protected Racket",
        "limits": "No universal uniqueness or measured training-gain claim.",
        "query_answers_used_for_rival_selection": False,
        "sources": sources,
        "runtime": identity,
        "teaching": reports,
        "selected_racket_executions": executions,
        "racket_evaluations": len(executions) + sum(row["demos"] for row in reports),
        "actual_30x29_selected_executions": sum(row["shape"] == [30, 29] for row in executions),
    }
    (output / "self_review.json").write_text(
        json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.out)
    print(json.dumps({
        "status": report["status"],
        "teaching_cases": len(report["teaching"]),
        "racket_evaluations": report["racket_evaluations"],
        "actual_30x29_selected_executions": report["actual_30x29_selected_executions"],
        "report": str(args.out / "self_review.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

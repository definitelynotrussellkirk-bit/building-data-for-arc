#!/usr/bin/env python3
"""Bounded source-bound audit for the hole-area packing parameter family.

Static checks cover count independence, matched inputs, finite teaching rivals,
public projection, and the 30x30 stress profile.  ``run_audit`` additionally
replays the maximal retained episodes and one causal counterfactual through the
live protected Racket bridge, then writes compact evidence for future agents.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
for path in (ROOT / "src", ROOT / "shared" / "runtime"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from arc_repl.racket_bridge import RacketBridge  # noqa: E402
from arcpuzzles import Catalog  # noqa: E402
from puzzle_generators.rule_wrap import wrap_rule  # noqa: E402

TASK_ID = "4e05481a2c21"
COUNT_PROFILES = ((2, 4), (3, 4), (6, 4))


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_arc_4e05481a2c21_self_audit_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path.resolve():
        raise ImportError("prototype import escaped task home")
    return module


P = _load_prototype()


def _compact(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _grid_key(grid: list[list[int]]) -> str:
    return _sha_bytes(_compact(grid))


def _inputs(episode: dict[str, Any], split: str) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode[split]]


def _stress_ok(grid: list[list[int]]) -> bool:
    info = P.analyze(grid)
    boxes = [obj["bbox"] for obj in info["objects"]]
    return (
        len(grid) == len(grid[0]) == 30
        and len(info["objects"]) == 4
        and sum(len(obj["cells"]) for obj in info["objects"]) >= 120
        and any(box[0] == 0 for box in boxes)
        and any(box[2] == 29 for box in boxes)
        and any(box[1] == 0 for box in boxes)
        and any(box[3] == 29 for box in boxes)
    )


def static_report(*, seeds: Iterable[int] = (0, 17)) -> dict[str, Any]:
    seeds = tuple(seeds)
    findings: list[dict[str, Any]] = []
    episodes = 0
    comparisons = 0
    stress = 0
    teaching_rows = []
    public_checks = 0
    distinct_inputs = set()

    for seed in seeds:
        maximal = {
            order: P.generate_episode(seed, pack_order=order, demos=6, queries=4)
            for order in P.PACK_ORDERS
        }
        for order in P.PACK_ORDERS:
            one = P.generate_episode(seed, pack_order=order, demos=3, queries=1)
            four = P.generate_episode(seed, pack_order=order, demos=3, queries=4)
            if P.public_view(one, 0) != P.public_view(four, 0):
                findings.append({"seed": seed, "order": order,
                                 "code": "first_turn_query_count_drift"})
            public_checks += 1
        for demos, queries in COUNT_PROFILES:
            current = {
                order: P.generate_episode(seed, pack_order=order,
                                          demos=demos, queries=queries)
                for order in P.PACK_ORDERS
            }
            episodes += len(current)
            comparisons += 1
            left, right = (current[P.PACK_ORDERS[0]], current[P.PACK_ORDERS[1]])
            if _inputs(left, "train") != _inputs(right, "train") or _inputs(left, "test") != _inputs(right, "test"):
                findings.append({"seed": seed, "demos": demos, "queries": queries,
                                 "code": "settings_changed_inputs"})
            for order, episode in current.items():
                rerun = P.generate_episode(seed, pack_order=order, demos=demos, queries=queries)
                if episode != rerun:
                    findings.append({"seed": seed, "order": order,
                                     "demos": demos, "queries": queries,
                                     "code": "nondeterministic"})
                if (episode["train"] != maximal[order]["train"][:demos]
                        or episode["test"] != maximal[order]["test"][:queries]):
                    findings.append({"seed": seed, "order": order,
                                     "demos": demos, "queries": queries,
                                     "code": "prefix_instability"})
                teaching = P.teaching_check(episode, order)
                teaching_rows.append({"seed": seed, "order": order,
                                      "demos": demos, "queries": queries,
                                      "harmful_survivors": teaching["harmful_survivors"],
                                      "demo_survivors": teaching["demo_survivors"]})
                if teaching["harmful_survivors"]:
                    findings.append({"seed": seed, "order": order,
                                     "demos": demos, "queries": queries,
                                     "code": "query_changing_rival_survived",
                                     "rivals": teaching["harmful_survivors"]})
                if not teaching["settings_disagree_on_demos"]:
                    findings.append({"seed": seed, "order": order,
                                     "demos": demos, "queries": queries,
                                     "code": "settings_not_taught"})
                if queries == 4 and _stress_ok(episode["test"][3]["input"]):
                    stress += 1
                else:
                    findings.append({"seed": seed, "order": order,
                                     "demos": demos, "queries": queries,
                                     "code": "missing_30x30_stress"})
                for split in ("train", "test"):
                    keys = [_grid_key(pair["input"]) for pair in episode[split]]
                    distinct_inputs.update(keys)
                    if len(keys) != len(set(keys)):
                        findings.append({"seed": seed, "order": order,
                                         "demos": demos, "queries": queries,
                                         "split": split, "code": "duplicate_input"})

    return {
        "schema": "arcpuzzles-4e05481a2c21-static-self-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not findings else "failed",
        "scope": "finite declared rivals; seeds and count profiles listed below",
        "limits": "finite rival elimination does not establish universal rule uniqueness",
        "seeds": list(seeds),
        "count_profiles": [list(profile) for profile in COUNT_PROFILES],
        "settings": list(P.PACK_ORDERS),
        "counts": {
            "episodes": episodes,
            "matched_input_comparisons": comparisons,
            "stress_30x30": stress,
            "public_first_turn_checks": public_checks,
            "distinct_input_hashes": len(distinct_inputs),
            "finite_rival_rows": len(teaching_rows),
        },
        "teaching": teaching_rows,
        "findings": findings,
    }


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _execute(bridge: RacketBridge, source: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(f"({wrap_rule(source)} {_literal(grid)})")


def _diff_cells(left: list[list[int]], right: list[list[int]]) -> int:
    if len(left) != len(right) or (left and right and len(left[0]) != len(right[0])):
        return max(sum(map(len, left)), sum(map(len, right)))
    return sum(a != b for ra, rb in zip(left, right, strict=True)
               for a, b in zip(ra, rb, strict=True))


def _source_binding() -> dict[str, Any]:
    catalog = Catalog(ROOT)
    row = catalog.describe(TASK_ID)
    programs = {v["program_solution"] for v in catalog.get(TASK_ID)["variants"]}
    if len(programs) != 1:
        raise ValueError("expected one selected canonical program")
    canonical = next(iter(programs))
    selected = [
        HERE / "prototype.py", HERE / "adapter.py", HERE / "promotion.json",
        HERE / "canonical.rkt", HERE / "hole_area_descending.rkt",
        HERE / "bbox_area_descending.rkt", HERE.parent.parent / "generator.py",
    ]
    return {
        "generator_sha256": row["generator_sha256"],
        "canonical_rule_hash": row["rule_hash"],
        "canonical_program_sha256": _sha_bytes(canonical.encode()),
        "files": [{"path": path.relative_to(ROOT).as_posix(), "sha256": _sha_file(path)}
                  for path in selected],
    }


def run_audit(*, seeds: Iterable[int] = (0, 17)) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    seeds = tuple(seeds)
    static = static_report(seeds=seeds)
    if static["status"] != "passed":
        raise AssertionError(f"static self-audit failed: {static['findings']}")
    cache: dict[tuple[str, str], list[list[int]]] = {}
    calls = 0
    hits = 0
    parity = []
    examples = []
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("protected Racket is required")
        for seed in seeds:
            for order in P.PACK_ORDERS:
                episode = P.generate_episode(seed, pack_order=order, demos=6, queries=4)
                source = P.program_for(order)
                source_hash = _sha_bytes(source.encode())
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        key = source_hash, _grid_key(pair["input"])
                        if key in cache:
                            got = cache[key]
                            hits += 1
                        else:
                            got = _execute(bridge, source, pair["input"])
                            cache[key] = got
                            calls += 1
                        exact = got == pair["output"]
                        parity.append({"seed": seed, "order": order, "split": split,
                                       "index": index, "exact": exact,
                                       "input_sha256": key[1],
                                       "output_sha256": _sha_bytes(_compact(got))})
                        if not exact:
                            raise AssertionError((seed, order, split, index))
                if seed == seeds[0]:
                    examples.append({
                        "seed": seed,
                        "settings": {"pack_order": order},
                        "program_sha256": source_hash,
                        "train": deepcopy(episode["train"][:3]),
                        "test": deepcopy(episode["test"]),
                    })

        witness_episode = P.generate_episode(seeds[0], pack_order="hole_area_descending",
                                             demos=2, queries=4)
        witness_input = witness_episode["train"][0]["input"]
        correct_source = P.program_for("hole_area_descending")
        wrong_source = (HERE / "bbox_area_descending.rkt").read_text(encoding="utf-8")
        correct_output = _execute(bridge, correct_source, witness_input)
        wrong_output = _execute(bridge, wrong_source, witness_input)
        calls += 2
        if correct_output == wrong_output:
            raise AssertionError("causal counterfactual failed to change final output")
        if correct_output != P.solve_python(witness_input, "hole_area_descending"):
            raise AssertionError("correct witness output disagrees with Python mirror")
        if wrong_output != P.solve_python(witness_input, "hole_bbox_area_descending"):
            raise AssertionError("counterfactual witness output disagrees with Python mirror")

    vector = P.derived_area_vector(witness_input)
    correct_order = [row["color"] for row in sorted(vector, key=lambda row: (-row["hole_area"], row["left"]))]
    wrong_order = [row["color"] for row in sorted(vector, key=lambda row: (-row["hole_bbox_area"], row["left"]))]
    witness = {
        "schema": "arcpuzzles-parametric-sequential-witness-v1",
        "task_id": TASK_ID,
        "setting": {"pack_order": "hole_area_descending"},
        "step_a": "extract each object's complete four-connected enclosed-zero union",
        "intermediate": {
            "name": "per-object enclosed-hole cell area vector",
            "values": vector,
            "correct_order_colors": correct_order,
            "counterfactual_bbox_order_colors": wrong_order,
        },
        "step_b": "sort complete extracted patterns by descending derived hole area, tie left-to-right, then pack",
        "why_b_depends_on_a": "the pack order cannot be selected until the input-dependent enclosed cells have been extracted and counted",
        "counterfactual": "replace hole-cell area with the bounding-box area of each extracted union while leaving extraction and packing unchanged",
        "input": witness_input,
        "correct_program_sha256": _sha_bytes(correct_source.encode()),
        "counterfactual_program_sha256": _sha_bytes(wrong_source.encode()),
        "correct_output": correct_output,
        "counterfactual_output": wrong_output,
        "different_cells": _diff_cells(correct_output, wrong_output),
        "protected_racket": True,
    }
    report = {
        "schema": "arcpuzzles-4e05481a2c21-protected-self-audit-v1",
        "task_id": TASK_ID,
        "status": "passed",
        "source_binding": _source_binding(),
        "static": static,
        "racket": identity,
        "counts": {
            "protected_racket_evaluations": calls,
            "cache_hits": hits,
            "parity_rows": len(parity),
            "settings": len(P.PACK_ORDERS),
            "seeds": len(seeds),
            "retained_examples": len(examples),
        },
        "parity": parity,
        "witness_summary": {
            "different_cells": witness["different_cells"],
            "correct_order_colors": correct_order,
            "counterfactual_bbox_order_colors": wrong_order,
        },
        "limits": static["limits"],
    }
    return report, witness, examples


def _write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(data)


def materialize(out: Path, *, seeds: Iterable[int] = (0, 17)) -> dict[str, Any]:
    if out.exists():
        raise FileExistsError(out)
    report, witness, examples = run_audit(seeds=seeds)
    out.mkdir(parents=True)
    _write_new(out / "self-audit.json", _compact(report))
    _write_new(out / "sequential-witness.json", _compact(witness))
    _write_new(out / "private" / "examples.json", _compact({"episodes": examples}))
    for example in examples:
        order = example["settings"]["pack_order"]
        episode = P.generate_episode(example["seed"], pack_order=order, demos=3, queries=4)
        raw = P.public_bytes(episode, 0)
        digest = _sha_bytes(raw)
        _write_new(out / "public" / f"challenge-{digest}.json", raw)
    return {"status": report["status"], **report["counts"],
            "witness_different_cells": witness["different_cells"],
            "out": str(out)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", default="0,17")
    args = parser.parse_args(argv)
    seeds = tuple(int(value) for value in args.seeds.split(",") if value)
    summary = materialize(args.out, seeds=seeds)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

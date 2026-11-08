#!/usr/bin/env python3
"""Replayable finite audit for the native nearest/farthest family.

The default CLI uses the checkout's protected Racket bridge.  ``run_audit``
also accepts an evaluator injection so the orchestration can be unit tested
without replacing the live qualification gate.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from typing import Callable, Iterable

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


HERE = Path(__file__).resolve().parent
TASK_ID = "9971f3a5882c"


def _load_native():
    path = HERE / "native.py"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    name = f"_audit_native_{digest}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _input_key(program: str, grid: list[list[int]]) -> str:
    body = json.dumps(grid, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256((program + "\0" + body).encode("utf-8")).hexdigest()


def _same_inputs(left: dict, right: dict) -> bool:
    return [pair["input"] for pair in left["train"]] == [
        pair["input"] for pair in right["train"]
    ] and [pair["input"] for pair in left["test"]] == [
        pair["input"] for pair in right["test"]
    ]


def _public_payload(episode: dict) -> dict:
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _run(
    output_dir: Path,
    *,
    seeds: tuple[int, ...],
    demo_counts: tuple[int, ...],
    queries: int,
    apply_program: Callable[[str, list[list[int]]], list[list[int]]],
    runtime_identity: dict,
) -> dict:
    native = _load_native()
    output_dir.mkdir(parents=True, exist_ok=True)
    public_dir = output_dir / "public"
    if public_dir.exists():
        shutil.rmtree(public_dir)
    public_dir.mkdir(parents=True)

    cache: dict[str, list[list[int]]] = {}
    cache_hits = 0
    failures: list[str] = []
    job_records: list[dict] = []
    thirty_by_thirty = 0

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    def execute(program: str, grid: list[list[int]]) -> list[list[int]]:
        nonlocal cache_hits
        key = _input_key(program, grid)
        if key in cache:
            cache_hits += 1
            return deepcopy(cache[key])
        result = _grid(apply_program(program, deepcopy(grid)))
        cache[key] = deepcopy(result)
        return result

    declared = {
        setting: native.program({"marker_selection": setting})
        for setting in native.SETTINGS
    }
    rivals = native.plausible_programs()
    require(set(rivals) == set(native.PLAUSIBLE_RIVALS), "Racket rival inventory drifted")
    require(len(set(declared.values())) == len(declared), "declared programs are not distinct")
    require(len(set(rivals.values())) == len(rivals), "plausible rival programs are not distinct")
    require(
        not (set(declared.values()) & set(rivals.values())),
        "a plausible rival duplicates a declared program",
    )

    episodes: dict[tuple[int, int, str], dict] = {}
    for seed in seeds:
        for demos in demo_counts:
            for setting in native.SETTINGS:
                settings = {"marker_selection": setting}
                episode = native.generate(seed, settings, demos, queries)
                episodes[(seed, demos, setting)] = episode

                selected_program = declared[setting]
                claimed_pairs = episode["train"] + episode["test"]
                wrong_claims = sum(
                    execute(selected_program, pair["input"]) != pair["output"]
                    for pair in claimed_pairs
                )
                require(
                    wrong_claims == 0,
                    f"seed={seed} demos={demos} setting={setting}: "
                    f"{wrong_claims} claimed labels disagree with Racket",
                )

                setting_survivors = [
                    candidate
                    for candidate, candidate_program in declared.items()
                    if all(
                        execute(candidate_program, pair["input"]) == pair["output"]
                        for pair in episode["train"]
                    )
                ]
                rival_survivors = [
                    name
                    for name, candidate_program in rivals.items()
                    if all(
                        execute(candidate_program, pair["input"]) == pair["output"]
                        for pair in episode["train"]
                    )
                ]
                require(
                    setting_survivors == [setting],
                    f"seed={seed} demos={demos} setting={setting}: "
                    f"declared survivors={setting_survivors}",
                )
                require(
                    not rival_survivors,
                    f"seed={seed} demos={demos} setting={setting}: "
                    f"plausible survivors={rival_survivors}",
                )

                query_inputs = [
                    json.dumps(pair["input"], separators=(",", ":"))
                    for pair in episode["test"]
                ]
                require(
                    len(query_inputs) == len(set(query_inputs)),
                    f"seed={seed} demos={demos} setting={setting}: duplicate queries",
                )
                thirty_by_thirty += sum(
                    len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                    for pair in episode["test"]
                )

                one = native.generate(seed, settings, demos, 1)
                require(
                    one["train"] == episode["train"]
                    and one["test"][0] == episode["test"][0],
                    f"seed={seed} demos={demos} setting={setting}: query prefix drift",
                )
                require(
                    native.visible_turn(one, 0) == native.visible_turn(episode, 0),
                    f"seed={seed} demos={demos} setting={setting}: first public turn drift",
                )
                visible = json.loads(native.visible_turn(episode, 0))
                require(
                    all(set(pair) == {"input"} for pair in visible["test"]),
                    f"seed={seed} demos={demos} setting={setting}: public query leaked output",
                )

                job_records.append(
                    {
                        "seed": seed,
                        "demos": demos,
                        "queries": queries,
                        "settings": settings,
                        "declared_survivors": setting_survivors,
                        "plausible_rival_survivors": rival_survivors,
                        "claimed_pairs_executed": len(claimed_pairs),
                        "query_shapes": [
                            [len(pair["input"]), len(pair["input"][0])]
                            for pair in episode["test"]
                        ],
                    }
                )

            nearest = episodes[(seed, demos, "nearest")]
            farthest = episodes[(seed, demos, "farthest")]
            require(
                _same_inputs(nearest, farthest),
                f"seed={seed} demos={demos}: inputs depend on private setting",
            )
            require(
                all(
                    left["output"] != right["output"]
                    for split in ("train", "test")
                    for left, right in zip(nearest[split], farthest[split])
                ),
                f"seed={seed} demos={demos}: a pair does not distinguish settings",
            )

        for setting in native.SETTINGS:
            small = native.generate(seed, {"marker_selection": setting}, 2, 1)
            large = native.generate(seed, {"marker_selection": setting}, 6, queries)
            require(
                small["train"] == large["train"][:2]
                and small["test"] == large["test"][:1],
                f"seed={seed} setting={setting}: demo/query streams are not prefix stable",
            )

    public_records = []
    public_seed = seeds[0]
    public_demos = demo_counts[0]
    for setting in native.SETTINGS:
        episode = episodes[(public_seed, public_demos, setting)]
        challenge = _public_payload(episode)
        raw = public_challenge_bytes(challenge)
        challenge_id = public_challenge_id(challenge)
        path = public_dir / f"{challenge_id}.json"
        path.write_bytes(raw)
        parsed = json.loads(raw)
        require(
            all(set(pair) == {"input"} for pair in parsed["test"]),
            f"public file {path.name} leaked query labels",
        )
        require(
            b"program_solution" not in raw and b"marker_selection" not in raw,
            f"public file {path.name} leaked private metadata",
        )
        public_records.append(
            {
                "setting_used_privately": setting,
                "challenge_id": challenge_id,
                "path": f"public/{path.name}",
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )

    witness = native.dependency_witness()
    correct_actual = execute(witness["program"], witness["input"])
    counterfactual_actual = execute(witness["counterfactual_program"], witness["input"])
    require(correct_actual == witness["output"], "causal witness correct program label mismatch")
    require(
        counterfactual_actual == witness["counterfactual_output"],
        "causal witness Python counterfactual disagrees with Racket",
    )
    require(
        correct_actual != counterfactual_actual,
        "causal witness ablation did not change final output",
    )
    audited_case = deepcopy(witness)
    audited_case["output"] = correct_actual
    audited_case["counterfactual_output"] = counterfactual_actual
    audited_case["step_a"] = (
        "Compute the original color-3 lattice bbox/full lines, then classify every "
        "color-6 marker by side relative to that input-dependent bbox."
    )
    audited_case["step_b"] = (
        "Choose the nearest/farthest marker within each classified side, derive "
        "new boundaries, move source boundary lines, extend internal lines, and restore markers."
    )
    _json(output_dir / "audited-case.json", audited_case)
    _json(output_dir / "jobs.json", job_records)

    source_paths = {
        name: HERE / filename
        for name, filename in {
            "adapter": "adapter.py",
            "audit": "audit.py",
            "native": "native.py",
            "nearest_program": "nearest.rkt",
            "promotion": "promotion.json",
        }.items()
    }
    source_hashes = {name: _digest(path) for name, path in source_paths.items()}
    runtime_is_live = runtime_identity.get("backend") == "racket"
    if runtime_is_live:
        require(
            runtime_identity.get("protected") is True,
            "live audit did not use a protected Racket backend",
        )

    summary = {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "status": "pass" if not failures else "fail",
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "queries": queries,
        "settings": list(native.SETTINGS),
        "jobs": len(job_records),
        "declared_programs": {
            setting: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for setting, text in declared.items()
        },
        "plausible_programs": {
            name: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for name, text in rivals.items()
        },
        "racket_evaluations": len(cache),
        "evaluation_cache_hits": cache_hits,
        "thirty_by_thirty_queries": thirty_by_thirty,
        "public_challenges": public_records,
        "causal_witness": {
            "ablation": witness["ablation"],
            "outputs_differ": correct_actual != counterfactual_actual,
            "changed_cells": sum(
                before != after
                for before_row, after_row in zip(correct_actual, counterfactual_actual)
                for before, after in zip(before_row, after_row)
            ),
            "case_path": "audited-case.json",
        },
        "runtime_identity": runtime_identity,
        "source_hashes": source_hashes,
        "failures": failures,
    }
    _json(output_dir / "summary.json", summary)
    if failures:
        raise RuntimeError("self-audit failed: " + "; ".join(failures))
    return summary


def run_audit(
    output_dir: str | Path,
    *,
    seeds: Iterable[int] = (0, 17),
    demo_counts: Iterable[int] = (2, 3, 6),
    queries: int = 4,
    apply_program: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
    runtime_identity: dict | None = None,
) -> dict:
    """Run the finite audit, using protected Racket unless an evaluator is injected."""
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    if not seeds or any(type(seed) is not int or not 0 <= seed <= 2**63 - 1 for seed in seeds):
        raise ValueError("seeds must be nonempty exact integers in 0..2**63-1")
    if not demo_counts or any(type(count) is not int or not 2 <= count <= 6 for count in demo_counts):
        raise ValueError("demo_counts must be nonempty exact integers in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    output = Path(output_dir).resolve()

    if apply_program is not None:
        if runtime_identity is None:
            runtime_identity = {"backend": "injected", "protected": False}
        return _run(
            output,
            seeds=seeds,
            demo_counts=demo_counts,
            queries=queries,
            apply_program=apply_program,
            runtime_identity=deepcopy(runtime_identity),
        )

    root = find_root(__file__)
    runtime = root / "shared" / "runtime"
    with _local_imports(runtime, HERE):
        evaluator, identity, bridge = _real_evaluator(runtime)
        try:
            return _run(
                output,
                seeds=seeds,
                demo_counts=demo_counts,
                queries=queries,
                apply_program=evaluator,
                runtime_identity=identity,
            )
        finally:
            bridge.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="evidence output directory")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 17])
    parser.add_argument("--demos", type=int, nargs="+", default=[2, 3, 6])
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args(argv)
    summary = run_audit(
        args.out,
        seeds=args.seeds,
        demo_counts=args.demos,
        queries=args.queries,
    )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "jobs": summary["jobs"],
                "racket_evaluations": summary["racket_evaluations"],
                "thirty_by_thirty_queries": summary["thirty_by_thirty_queries"],
                "changed_cells": summary["causal_witness"]["changed_cells"],
                "output": str(Path(args.out).resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

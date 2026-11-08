"""Reusable bounded self-audit for 63784d19dd2d's native family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
PROTOTYPE_PATH = HERE / "prototype.py"
_NAME = "parametric_63784d19dd2d_audit_source"


def _load():
    module = sys.modules.get(_NAME)
    if module is not None:
        return module
    spec = importlib.util.spec_from_file_location(_NAME, PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[_NAME] = module
    spec.loader.exec_module(module)
    return module


P = _load()


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _failure(rows: list[dict[str, Any]], kind: str, **details: Any) -> None:
    rows.append({"kind": kind, **details})


def build_audit(
    *,
    seeds: tuple[int, ...] = (0, 17, 31),
    demo_counts: tuple[int, ...] = (2, 3, 6),
    query_counts: tuple[int, ...] = (1, 4),
    execute_racket: bool = True,
) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    survivors: dict[str, dict[str, list[str]]] = {}
    totals = {
        "seeds": len(seeds),
        "requests": 0,
        "episodes": 0,
        "labeled_pairs": 0,
        "matched_input_requests": 0,
        "maximum_width_episodes": 0,
        "racket_evaluations": 0,
    }
    bridge = None
    wrapped: dict[str, str] = {}
    runtime: dict[str, Any] = {"executed": False}
    if execute_racket:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
        runtime = bridge.runtime_identity
        wrapped = {
            name: wrap_rule(P.candidate_program(name))
            for name in P.CANDIDATE_RULES
        }

    def execute(name: str, grid):
        if bridge is None:
            return P.solve_candidate(grid, name)
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        totals["racket_evaluations"] += 1
        return bridge.eval_text(f"({wrapped[name]} {literal})")

    try:
        for seed in seeds:
            base = P.episode_inputs(seed, demos=2, queries=4)
            survivors[str(seed)] = {}
            racket_outputs: dict[str, list[Any]] = {}
            for candidate in P.CANDIDATE_RULES:
                outputs = []
                for grid in base["train"]:
                    output = execute(candidate, grid)
                    expected = P.solve_candidate(grid, candidate)
                    if output != expected:
                        _failure(
                            failures,
                            "racket_candidate_mismatch",
                            seed=seed,
                            candidate=candidate,
                        )
                    outputs.append(output)
                racket_outputs[candidate] = outputs

            for chosen in P.OVERLAP_MODES:
                labels = [P.solve(grid, chosen) for grid in base["train"]]
                names = [
                    candidate
                    for candidate, outputs in racket_outputs.items()
                    if outputs == labels
                ]
                survivors[str(seed)][chosen] = names
                if names != [chosen]:
                    _failure(
                        failures,
                        "finite_rival_survivor",
                        seed=seed,
                        chosen=chosen,
                        survivors=names,
                    )

            if execute_racket:
                for chosen in P.OVERLAP_MODES:
                    episode = P.generate_episode(seed, chosen, demos=6, queries=4)
                    for split in ("train", "test"):
                        for pair_index, pair in enumerate(episode[split]):
                            output = execute(chosen, pair["input"])
                            if output != pair["output"]:
                                _failure(
                                    failures,
                                    "racket_label_mismatch",
                                    seed=seed,
                                    chosen=chosen,
                                    split=split,
                                    pair_index=pair_index,
                                )

            for demos in demo_counts:
                for queries in query_counts:
                    totals["requests"] += 1
                    episodes = {
                        mode: P.generate_episode(seed, mode, demos=demos, queries=queries)
                        for mode in P.OVERLAP_MODES
                    }
                    totals["episodes"] += len(episodes)
                    totals["labeled_pairs"] += len(episodes) * (demos + queries)
                    input_lists = [
                        [
                            pair["input"]
                            for split in ("train", "test")
                            for pair in episode[split]
                        ]
                        for episode in episodes.values()
                    ]
                    if all(inputs == input_lists[0] for inputs in input_lists[1:]):
                        totals["matched_input_requests"] += 1
                    else:
                        _failure(
                            failures,
                            "settings_input_confound",
                            seed=seed,
                            demos=demos,
                            queries=queries,
                        )
                    if len({_freeze(grid) for grid in input_lists[0]}) != demos + queries:
                        _failure(
                            failures,
                            "duplicate_visible_input",
                            seed=seed,
                            demos=demos,
                            queries=queries,
                        )
                    full = P.generate_episode(seed, P.DEFAULT_MODE, demos=6, queries=4)
                    current = episodes[P.DEFAULT_MODE]
                    if current["train"] != full["train"][:demos] or current["test"] != full["test"][:queries]:
                        _failure(
                            failures,
                            "prefix_instability",
                            seed=seed,
                            demos=demos,
                            queries=queries,
                        )
                    one = P.generate_episode(seed, P.DEFAULT_MODE, demos=demos, queries=1)
                    if P.public_view(current, 0) != P.public_view(one, 0):
                        _failure(
                            failures,
                            "first_turn_instability",
                            seed=seed,
                            demos=demos,
                            queries=queries,
                        )
                    public = P.public_view(current, 0)
                    if set(public) != {"train", "test"} or set(public["test"][0]) != {"input"}:
                        _failure(
                            failures,
                            "public_projection_leak",
                            seed=seed,
                            demos=demos,
                            queries=queries,
                        )
                    if queries == 4:
                        for mode, episode in episodes.items():
                            grid = episode["test"][3]["input"]
                            if len(grid) == 9 and len(grid[0]) == 29:
                                totals["maximum_width_episodes"] += 1
                            else:
                                _failure(
                                    failures,
                                    "missing_maximum_width_stress",
                                    seed=seed,
                                    demos=demos,
                                    mode=mode,
                                )
                    for grid in input_lists[0]:
                        facts = P.analyze_input(grid)
                        if facts["errors"]:
                            _failure(
                                failures,
                                "invalid_scene",
                                seed=seed,
                                demos=demos,
                                queries=queries,
                                errors=facts["errors"],
                            )
                        elif not 0 < facts["b_overlap_count"] < facts["transformed_c_size"]:
                            _failure(
                                failures,
                                "non_partial_overlap",
                                seed=seed,
                                demos=demos,
                                queries=queries,
                            )
    finally:
        if bridge is not None:
            bridge.close()

    source_paths = (
        PROTOTYPE_PATH,
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "canonical.rkt",
        HERE / "mark_b_overlap.rkt",
        Path(__file__).resolve(),
    )
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": P.TASK_ID,
        "status": "passed" if not failures else "failed",
        "settings": list(P.OVERLAP_MODES),
        "finite_candidates": list(P.CANDIDATE_RULES),
        "finite_rival_survivors": survivors,
        "totals": totals,
        "racket": runtime,
        "failures": failures,
        "source": {path.name: _sha256(path) for path in source_paths},
        "limits": (
            "Finite authored seeds/count boundaries and declared rivals only; "
            "this is not universal identifiability or measured training gain."
        ),
        "training_admitted": False,
    }


def _write_public_files(output: Path, seeds: tuple[int, ...]) -> list[str]:
    output.mkdir(parents=True, exist_ok=False)
    paths: list[str] = []
    seen: set[str] = set()
    for seed in seeds:
        for mode in P.OVERLAP_MODES:
            episode = P.generate_episode(seed, mode, demos=3, queries=4)
            for query_index in range(4):
                path = P.write_public(episode, output, query_index)
                if path.name in seen:
                    raise RuntimeError(f"duplicate public payload {path.name}")
                seen.add(path.name)
                paths.append(str(path))
    return sorted(paths)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--public-dir")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17, 31])
    parser.add_argument("--no-racket", action="store_true")
    args = parser.parse_args(argv)
    seeds = tuple(args.seeds)
    report = build_audit(seeds=seeds, execute_racket=not args.no_racket)
    if args.public_dir:
        report["public_files"] = _write_public_files(Path(args.public_dir), seeds)
    output = Path(args.out)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "output": str(output),
                "totals": report["totals"],
                "failures": len(report["failures"]),
                "public_files": len(report.get("public_files", [])),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Protected-Racket self-audit and causal witness for 24bb2221ca5c.

The audit is deliberately finite.  It verifies Python label claims against the
same-checkout protected Racket runtime, checks demo-only identification against
all declared settings plus a small set of plausible selectors, validates the
one-query public projection, and records one wrong-intermediate causal case.
"""
from __future__ import annotations

from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable


TASK_ID = "24bb2221ca5c"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
POLICIES = ("all", "largest_hole_area", "most_holes")
RIVAL_NAMES = (
    "identity",
    "largest_bbox_area",
    "first_closed",
    "last_closed",
    "smallest_hole_area",
)
DEPENDENCY = {
    "step_a": (
        "Compute same-color 4-connected components and identify every bbox-local "
        "zero region that cannot reach that component's bbox border."
    ),
    "intermediate": (
        "The input-dependent per-component enclosed regions, total enclosed area, "
        "hole count, color, and bounding box."
    ),
    "step_b": (
        "Rank components by total enclosed area and fill the holes of the unique "
        "maximum-area component."
    ),
    "why_b_depends_on_a": (
        "Step B cannot choose its component until Step A has measured the enclosed "
        "regions. Replacing those measurements with bbox area selects a different "
        "component on the retained case and changes the final grid."
    ),
}


def _load_exact(path: Path, prefix: str):
    source = path.read_bytes()
    name = prefix + hashlib.sha256(str(path).encode() + source).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load exact source {path}")
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


ADAPTER = _load_exact(HERE / "adapter.py", "_24bb_audit_adapter_")
PROTOTYPE = _load_exact(HERE / "prototype.py", "_24bb_audit_prototype_")
RULES = _load_exact(HERE / "rules.py", "_24bb_audit_rules_")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _raw(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _replace_score(expression: str) -> str:
    source = RULES.program({"fill_policy": "largest_hole_area"})
    needle = "(define (score record) (length (second record)))"
    replacement = f"(define (score record) {expression})"
    if source.count(needle) != 1:
        raise ValueError("declared selector score changed or became ambiguous")
    return source.replace(needle, replacement, 1)


def counterfactual_program(name: str) -> str:
    """Materialize one bounded plausible wrong rule from the exact source."""
    if name == "identity":
        source = RULES.canonical_program()
        tail = RULES._CANONICAL_TAIL
        if source.count(tail) != 1 or not source.endswith(tail):
            raise ValueError("canonical final block changed or became ambiguous")
        return source[: -len(tail)] + "    g\n  ))"
    if name == "largest_bbox_area":
        return _replace_score(
            "(let ((bb (obj-bbox (first record)))) "
            "(* (+ 1 (- (third bb) (first bb))) "
            "(+ 1 (- (fourth bb) (second bb)))))"
        )
    if name == "first_closed":
        return _replace_score(
            "(let ((bb (obj-bbox (first record)))) "
            "(- 0 (+ (* 100 (first bb)) (second bb))))"
        )
    if name == "last_closed":
        return _replace_score(
            "(let ((bb (obj-bbox (first record)))) "
            "(+ (* 100 (first bb)) (second bb)))"
        )
    if name == "smallest_hole_area":
        return _replace_score("(- 0 (length (second record)))")
    raise ValueError(f"unknown bounded rival: {name}")


def _validate_options(
    seeds: Iterable[int], demos: int, queries: int, source_binding: dict | None
) -> tuple[int, ...]:
    seeds = tuple(seeds)
    if not seeds or any(type(seed) is not int or not 0 <= seed <= 2**63 - 1 for seed in seeds):
        raise ValueError("seeds must be nonempty exact integers in 0..2**63-1")
    if len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be distinct")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an exact integer in 1..4")
    if source_binding is not None and type(source_binding) is not dict:
        raise ValueError("source_binding must be an object when supplied")
    return seeds


def _public_is_private_free(visible: dict) -> bool:
    if set(visible) != {"train", "test"}:
        return False
    if not isinstance(visible["train"], list) or not isinstance(visible["test"], list):
        return False
    if len(visible["test"]) != 1 or set(visible["test"][0]) != {"input"}:
        return False
    return all(set(pair) == {"input", "output"} for pair in visible["train"])


def build_evidence(
    output: Path,
    *,
    seeds: Iterable[int] = (0, 17),
    demos: int = 3,
    queries: int = 4,
    source_binding: dict | None = None,
) -> dict:
    """Execute the bounded audit and write private replayable evidence."""
    seeds = _validate_options(seeds, demos, queries, source_binding)
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    rules_dir = output / "rules"
    rules_dir.mkdir()

    declared = {
        policy: ADAPTER.program({"fill_policy": policy}) for policy in POLICIES
    }
    rivals = {name: counterfactual_program(name) for name in RIVAL_NAMES}
    if len(set((*declared.values(), *rivals.values()))) != len(declared) + len(rivals):
        raise ValueError("declared and rival programs must be byte-distinct")
    for name, source in {**declared, **rivals}.items():
        (rules_dir / f"{name}.rkt").write_text(source, encoding="utf-8")

    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    failures: list[dict[str, Any]] = []
    private_episodes = []
    certificates = []
    first_turn_count_invariant = True
    private_fields_absent = True
    label_count = 0
    evaluations = 0
    cache: dict[tuple[str, bytes], list[list[int]]] = {}

    with _local_imports(ROOT / "shared/runtime", HERE):
        apply_program, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            def execute(program: str, grid: list[list[int]]) -> list[list[int]]:
                nonlocal evaluations
                key = (program, _raw(grid))
                if key not in cache:
                    cache[key] = _grid(apply_program(program, deepcopy(grid)))
                    evaluations += 1
                return deepcopy(cache[key])

            for seed in seeds:
                for policy in POLICIES:
                    settings = {"fill_policy": policy}
                    episode = ADAPTER.generate(seed, settings, demos, queries)
                    pairs = episode["train"] + episode["test"]
                    actual = [execute(declared[policy], pair["input"]) for pair in pairs]
                    label_count += len(pairs)
                    for pair_index, (observed, pair) in enumerate(zip(actual, pairs)):
                        if observed != pair["output"]:
                            failures.append(
                                {
                                    "kind": "racket_label_mismatch",
                                    "seed": seed,
                                    "settings": settings,
                                    "pair_index": pair_index,
                                }
                            )

                    declared_survivors = []
                    for candidate, program in declared.items():
                        outputs = [
                            execute(program, pair["input"]) for pair in episode["train"]
                        ]
                        if all(
                            observed == pair["output"]
                            for observed, pair in zip(outputs, episode["train"])
                        ):
                            declared_survivors.append(candidate)
                    if declared_survivors != [policy]:
                        failures.append(
                            {
                                "kind": "declared_demo_survivors",
                                "seed": seed,
                                "settings": settings,
                                "survivors": declared_survivors,
                            }
                        )

                    rival_results = []
                    for rival, program in rivals.items():
                        demo_outputs = [
                            execute(program, pair["input"]) for pair in episode["train"]
                        ]
                        survives = all(
                            observed == pair["output"]
                            for observed, pair in zip(demo_outputs, episode["train"])
                        )
                        query_disagreements = []
                        if survives:
                            query_outputs = [
                                execute(program, pair["input"])
                                for pair in episode["test"]
                            ]
                            query_disagreements = [
                                index
                                for index, (observed, pair) in enumerate(
                                    zip(query_outputs, episode["test"])
                                )
                                if observed != pair["output"]
                            ]
                            if query_disagreements:
                                failures.append(
                                    {
                                        "kind": "rival_fits_demos_disagrees_query",
                                        "seed": seed,
                                        "settings": settings,
                                        "rival": rival,
                                        "query_indices": query_disagreements,
                                    }
                                )
                        rival_results.append(
                            {
                                "name": rival,
                                "survives_demos": survives,
                                "query_disagreements": query_disagreements,
                            }
                        )
                    certificates.append(
                        {
                            "seed": seed,
                            "settings": settings,
                            "declared_survivors": declared_survivors,
                            "rivals": rival_results,
                        }
                    )

                    stopped = ADAPTER.generate(seed, settings, demos, 1)
                    visible = PROTOTYPE.public_turn(episode, 0)
                    stopped_visible = PROTOTYPE.public_turn(stopped, 0)
                    first_turn_count_invariant = (
                        first_turn_count_invariant and _raw(visible) == _raw(stopped_visible)
                    )
                    private_fields_absent = (
                        private_fields_absent and _public_is_private_free(visible)
                    )
                    private_episodes.append(
                        {
                            "task_id": TASK_ID,
                            "seed": seed,
                            "settings": settings,
                            **deepcopy(episode),
                            "program_sha256": hashlib.sha256(
                                declared[policy].encode()
                            ).hexdigest(),
                            "racket_labels": actual,
                        }
                    )

            witness_episode = ADAPTER.generate(
                seeds[0], {"fill_policy": "largest_hole_area"}, demos, queries
            )
            witness_input = witness_episode["train"][0]["input"]
            actual_program = declared["largest_hole_area"]
            wrong_program = rivals["largest_bbox_area"]
            actual_output = execute(actual_program, witness_input)
            wrong_output = execute(wrong_program, witness_input)
            if actual_output != witness_episode["train"][0]["output"]:
                raise ValueError("causal witness actual program differs from private label")
            if actual_output == wrong_output:
                raise ValueError("wrong-intermediate witness did not change final output")
            profiles = PROTOTYPE.component_profiles(witness_input)
            closed = [profile for profile in profiles if profile["hole_count"]]
            area_winner = max(closed, key=lambda profile: profile["hole_area"])
            bbox_winner = max(closed, key=lambda profile: profile["bbox_area"])
            if area_winner["component_index"] == bbox_winner["component_index"]:
                raise ValueError("witness intermediate winners unexpectedly coincide")
            witness = {
                "schema": "arcpuzzles-sequential-dependency-witness-v1",
                "source_binding": deepcopy(source_binding)
                if source_binding is not None
                else {"status": "pending_native_qualification"},
                "racket": {"backend": "racket", "protected": True},
                **DEPENDENCY,
                "cases": [
                    {
                        "input": deepcopy(witness_input),
                        "settings": {"fill_policy": "largest_hole_area"},
                        "intermediate_value": {
                            "components": profiles,
                            "largest_hole_area_component": area_winner[
                                "component_index"
                            ],
                            "largest_bbox_component": bbox_winner[
                                "component_index"
                            ],
                        },
                        "program": actual_program,
                        "output": actual_output,
                        "counterfactual_program": wrong_program,
                        "counterfactual_output": wrong_output,
                        "ablation": "wrong_intermediate",
                    }
                ],
                "limits": (
                    "One bounded source-local protected-Racket case; this does not "
                    "prove universal algorithmic depth."
                ),
            }
        finally:
            bridge.close()

    if not first_turn_count_invariant:
        failures.append({"kind": "first_public_turn_depends_on_query_count"})
    if not private_fields_absent:
        failures.append({"kind": "public_projection_leaks_private_fields"})

    _write_json(
        output / "episodes.private.json",
        {
            "schema": "24bb-hole-selection-audit-episodes-v1",
            "private": True,
            "episodes": private_episodes,
            "certificates": certificates,
        },
    )
    _write_json(output / "sequential-dependency.json", witness)
    surviving_rivals = [
        {"seed": certificate["seed"], "settings": certificate["settings"],
         "rival": rival["name"]}
        for certificate in certificates
        for rival in certificate["rivals"]
        if rival["survives_demos"]
    ]
    report = {
        "schema": "24bb-hole-selection-audit-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "seeds": list(seeds),
        "demos": demos,
        "queries": queries,
        "episodes": len(private_episodes),
        "label_count": label_count,
        "racket_evaluations": evaluations,
        "racket": identity,
        "rival_programs": len(rivals),
        "demo_only_certificates": len(certificates),
        "surviving_rivals": surviving_rivals,
        "public_projection": {
            "first_turn_count_invariant": first_turn_count_invariant,
            "private_fields_absent": private_fields_absent,
        },
        "failures": failures,
        "limits": (
            "Finite declared-setting and authored-rival scan over the recorded seeds; "
            "not a uniqueness proof against arbitrary programs."
        ),
    }
    _write_json(output / "summary.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--source-binding", type=Path)
    args = parser.parse_args(argv)
    binding = (
        json.loads(args.source_binding.read_text(encoding="utf-8"))
        if args.source_binding
        else None
    )
    report = build_evidence(
        args.out,
        seeds=tuple(args.seeds or (0, 17)),
        demos=args.demos,
        queries=args.queries,
        source_binding=binding,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "summary": str((args.out / "summary.json").resolve()),
                "racket_evaluations": report["racket_evaluations"],
                "failures": len(report["failures"]),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
